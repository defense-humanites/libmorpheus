/* SPDX-License-Identifier: MPL-2.0 */

#include "generation_service.h"

#include <ctype.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <modes.h>

#include "gener_internal.h"
#include "generation_compounds.h"
#include "../morphlib/gkstring.proto.h"
#include "../morphlib/runtime_context_internal.h"

struct morpheus_generation_service {
	const morpheus_gener_index *index;
	morpheus_runtime_context *context;
	morpheus_compound_table *compounds;
};

static morpheus_generation_status
runtime_status(const morpheus_runtime_context *context)
{
	switch (morpheus_runtime_context_error(context)) {
	case MORPHEUS_RUNTIME_ERROR_NO_MEMORY:
		return MORPHEUS_GENERATION_NO_MEMORY;
	case MORPHEUS_RUNTIME_ERROR_INTERNAL:
		return MORPHEUS_GENERATION_ENGINE_ERROR;
	default:
		return MORPHEUS_GENERATION_ENGINE_ERROR;
	}
}

static void
release_input(gk_word *input)
{
	free(oddkeys_of(input));
	oddkeys_of(input) = NULL;
	ReleaseGkAnalStorage(input);
}

static void
release_forms(gk_word *forms)
{
	/* Generated forms borrow these pointers from the call-local input. */
	oddkeys_of(forms) = NULL;
	DetachGkAnalStorage(forms);
	FreeGkword(forms);
}

/*
 * The record's keys, with " pb:<preverbs>" appended when the record is
 * generated for a compound.
 */
static char *
record_keys(const char *source, const char *preverbs)
{
	char *copy;
	char *cursor;
	size_t length = strlen(source);
	size_t added = preverbs ? strlen(" pb:") + strlen(preverbs) : 0;

	copy = malloc(length + added + 1);
	if (!copy)
		return NULL;
	memcpy(copy,source,length + 1);
	if (preverbs) {
		memcpy(copy + length," pb:",4);
		memcpy(copy + length + 4,preverbs,strlen(preverbs) + 1);
	}
	cursor = copy;
	while (isspace((unsigned char)*cursor))
		cursor++;
	while (*cursor && !isspace((unsigned char)*cursor)) {
		if (*cursor == ',')
			*cursor = ' ';
		cursor++;
	}
	return copy;
}

/*
 * *unusable is set when the record failed before any of its forms reached the
 * visitor, so the caller may skip it without exposing a partial record.
 */
static morpheus_generation_status
generate_record(morpheus_generation_service *service, const char *lemma,
                const morpheus_gener_record_view *record, const char *preverbs,
                morpheus_generation_visitor visitor, void *state,
                size_t *form_count, int *unusable)
{
	gk_word input = { 0 };
	gk_word *forms;
	char *keys;
	size_t form;
	int irregular;
	int mode;

	set_lemma(&input,lemma);
	set_stem(&input,record->stem);
	keys = record_keys(record->keys,preverbs);
	if (!keys)
		return MORPHEUS_GENERATION_NO_MEMORY;
	irregular = record->kind == MORPHEUS_GENER_RECORD_INDECLINABLE ||
	            record->kind == MORPHEUS_GENER_RECORD_IRREGULAR_VERB;
	mode = record->kind == MORPHEUS_GENER_RECORD_INDECLINABLE ? INDECL : 0;
	forms = irregular
	            ? GenIrregForm(&input,keys,mode)
	            : GenStemForms(&input,keys,0);
	free(keys);
	if (!forms) {
		morpheus_generation_status status = runtime_status(service->context);
		release_input(&input);
		*unusable = status == MORPHEUS_GENERATION_ENGINE_ERROR;
		return status;
	}
	if (morpheus_runtime_context_error(service->context) !=
	    MORPHEUS_RUNTIME_ERROR_NONE) {
		morpheus_generation_status status = runtime_status(service->context);
		release_forms(forms);
		release_input(&input);
		*unusable = status == MORPHEUS_GENERATION_ENGINE_ERROR;
		return status;
	}
	for (form = 0; workword_of(forms + form)[0]; form++) {
		/*
		 * A compound takes verb forms only: some verb records decline
		 * an adjective (:vs:ton os_on comp_only under tei/nw), to which
		 * the engine attaches no preverb.
		 */
		if (preverbs && !(stemtype_of(forms + form) & PPARTMASK))
			continue;
		if (*form_count == SIZE_MAX) {
			release_forms(forms);
			release_input(&input);
			return MORPHEUS_GENERATION_ENGINE_ERROR;
		}
		(*form_count)++;
		if (!visitor(forms + form,state)) {
			release_forms(forms);
			release_input(&input);
			return MORPHEUS_GENERATION_STOPPED;
		}
	}
	release_forms(forms);
	release_input(&input);
	return MORPHEUS_GENERATION_OK;
}

morpheus_generation_status
morpheus_generation_service_create(const morpheus_gener_index *index,
                                   morpheus_generation_service **service)
{
	return morpheus_generation_service_create_at_path(index,NULL,service);
}

morpheus_generation_status
morpheus_generation_service_create_at_path(
    const morpheus_gener_index *index, const char *stemlib_path,
    morpheus_generation_service **service)
{
	morpheus_generation_service *created;
	size_t path_length;

	if (!index || !service)
		return MORPHEUS_GENERATION_INVALID;
	*service = NULL;
	created = calloc(1,sizeof *created);
	if (!created)
		return MORPHEUS_GENERATION_NO_MEMORY;
	created->context = morpheus_runtime_context_create();
	if (!created->context) {
		free(created);
		return MORPHEUS_GENERATION_NO_MEMORY;
	}
	if (stemlib_path) {
		path_length = strlen(stemlib_path);
		created->context->stemlib_path = malloc(path_length + 1);
		if (!created->context->stemlib_path) {
			morpheus_runtime_context_destroy(created->context);
			free(created);
			return MORPHEUS_GENERATION_NO_MEMORY;
		}
		memcpy(created->context->stemlib_path,stemlib_path,path_length + 1);
	}
	/* Unusable records are counted by the caller, not reported on stderr. */
	morpheus_runtime_context_set_diagnostics(created->context,0);
	created->index = index;
	*service = created;
	return MORPHEUS_GENERATION_OK;
}

void
morpheus_generation_service_destroy(morpheus_generation_service *service)
{
	if (!service)
		return;
	morpheus_compound_table_destroy(service->compounds);
	morpheus_runtime_context_destroy(service->context);
	free(service);
}

/*
 * The preverb a record names: the value of its last pb: key, or of its last
 * rpb: key (a preverb that is part of the stem, which analysis ignores).
 */
typedef struct {
	char value[MAXWORDSIZE];
	int root;
} record_preverb;

static int
find_record_preverb(const char *keys, record_preverb *found)
{
	const char *cursor = keys;
	int seen = 0;

	found->value[0] = 0;
	found->root = 0;
	while (*cursor) {
		size_t length;
		size_t prefix = 0;

		cursor += strspn(cursor," \t");
		length = strcspn(cursor," \t");
		if (length > 3 && !strncmp(cursor,"pb:",3))
			prefix = 3;
		else if (length > 4 && !strncmp(cursor,"rpb:",4))
			prefix = 4;
		if (prefix && length - prefix < sizeof found->value) {
			memcpy(found->value,cursor + prefix,length - prefix);
			found->value[length - prefix] = 0;
			found->root = prefix == 4;
			seen = 1;
		}
		cursor += length;
	}
	return seen;
}

/*
 * Whether a record that names its own preverb belongs to the generated
 * lemma, as analysis decides (checkdict.c). A root preverb (rpb:) is part of
 * the lemma's stem: the record belongs to the lemma itself, never to a
 * compound of it. A pb: preverb belongs to the lemma analysis names after
 * it: to the lemma itself when that name is the lemma (a)mfisbhte/w), and
 * otherwise to a compound whose preverbs end with it (the pb:e)pi/ stems of
 * mele/omai to e)pimele/omai).
 */
static morpheus_generation_status
record_belongs(morpheus_generation_service *service, const char *lemma,
               const char *preverbs, const record_preverb *own, int *belongs)
{
	*belongs = 0;
	if (own->root) {
		*belongs = !preverbs;
		return MORPHEUS_GENERATION_OK;
	}
	if (preverbs) {
		size_t length = strlen(preverbs);
		size_t own_length = strlen(own->value);

		*belongs = length >= own_length &&
		           !strcmp(preverbs + length - own_length,own->value);
		return MORPHEUS_GENERATION_OK;
	}
	switch (morpheus_compound_names_lemma(&service->compounds,own->value,lemma,
	                                      belongs)) {
	case MORPHEUS_COMPOUND_OK:
		return MORPHEUS_GENERATION_OK;
	default:
		return MORPHEUS_GENERATION_NO_MEMORY;
	}
}

/*
 * Generates the records of one index key under the requested lemma. With
 * preverbs, only verb records are composed: analysis reads a preverb only
 * before a verb stem, and attributes adjectives such as a)po/dotos to
 * lemmas of their own. *found is set when the key is in the index.
 */
static morpheus_generation_status
generate_key(morpheus_generation_service *service, const char *key,
             const char *lemma, const char *preverbs,
             morpheus_generation_visitor visitor, void *state,
             size_t *form_count, size_t *skipped_records, int *found)
{
	morpheus_gener_lemma_view entry;
	morpheus_generation_status result = MORPHEUS_GENERATION_OK;
	uint64_t block_number;
	/* The lemma the key holds stems of: -dhme/w holds stems of dhme/w. */
	const char *simple_lemma = key[0] == '-' ? key + 1 : key;

	switch (morpheus_gener_index_lookup(service->index,key,&entry)) {
	case MORPHEUS_GENER_INDEX_OK:
		break;
	case MORPHEUS_GENER_INDEX_NOT_FOUND:
		return MORPHEUS_GENERATION_OK;
	default:
		return MORPHEUS_GENERATION_INVALID;
	}
	*found = 1;
	for (block_number = entry.first_block;
	     block_number != entry.first_block + entry.block_count; block_number++) {
		morpheus_gener_block_view block;
		uint64_t record_number;

		if (morpheus_gener_index_block(service->index,block_number,&block) !=
		    MORPHEUS_GENER_INDEX_OK)
			return MORPHEUS_GENERATION_INVALID;
		for (record_number = block.first_record;
		     record_number != block.first_record + block.record_count;
		     record_number++) {
			morpheus_gener_record_view record;
			record_preverb own;
			int unusable = 0;

			if (morpheus_gener_index_record(service->index,record_number,
			                                &record) !=
			    MORPHEUS_GENER_INDEX_OK)
				return MORPHEUS_GENERATION_INVALID;
			if (preverbs &&
			    record.kind != MORPHEUS_GENER_RECORD_VERB_STEM &&
			    record.kind != MORPHEUS_GENER_RECORD_IRREGULAR_VERB)
				continue;
			if (find_record_preverb(record.keys,&own)) {
				int belongs;

				result = record_belongs(service,simple_lemma,preverbs,&own,
				                        &belongs);
				if (result != MORPHEUS_GENERATION_OK)
					return result;
				if (!belongs)
					continue;
			}
			result = generate_record(service,lemma,&record,preverbs,visitor,
			                         state,form_count,&unusable);
			if (unusable && skipped_records) {
				/* A record the engine cannot generate leaves the others usable. */
				morpheus_runtime_context_clear_error(service->context);
				(*skipped_records)++;
				result = MORPHEUS_GENERATION_OK;
				continue;
			}
			if (result != MORPHEUS_GENERATION_OK)
				return result;
		}
	}
	return result;
}

/*
 * A compound is generated from the records of its simple verb, under the
 * simple verb's key and, for stems that analysis accepts only after a
 * preverb, under the same key prefixed with '-' (-dhme/w), which the
 * preparer reserves for them and no request can name.
 */
static morpheus_generation_status
generate_compounds(morpheus_generation_service *service, const char *lemma,
                   morpheus_generation_visitor visitor, void *state,
                   size_t *form_count, size_t *skipped_records, int *found)
{
	morpheus_compound_decomposition *decompositions = NULL;
	morpheus_generation_status result = MORPHEUS_GENERATION_OK;
	size_t count = 0;
	size_t item;

	switch (morpheus_compound_decompositions(&service->compounds,lemma,
	                                         &decompositions,&count)) {
	case MORPHEUS_COMPOUND_OK:
		break;
	default:
		return MORPHEUS_GENERATION_NO_MEMORY;
	}
	for (item = 0; item != count && result == MORPHEUS_GENERATION_OK; item++) {
		char reserved[MAXWORDSIZE + 1];

		/*
		 * A compound listed as its own decomposition (a)mfi/-a)mfisbhte/w)
		 * adds nothing to the lemma's own records but duplicates.
		 */
		if (!strcmp(decompositions[item].lemma,lemma))
			continue;
		result = generate_key(service,decompositions[item].lemma,lemma,
		                      decompositions[item].preverbs,visitor,state,
		                      form_count,skipped_records,found);
		if (result != MORPHEUS_GENERATION_OK)
			break;
		reserved[0] = '-';
		memcpy(reserved + 1,decompositions[item].lemma,
		       strlen(decompositions[item].lemma) + 1);
		result = generate_key(service,reserved,lemma,
		                      decompositions[item].preverbs,visitor,state,
		                      form_count,skipped_records,found);
	}
	free(decompositions);
	return result;
}

morpheus_generation_status
morpheus_generation_service_generate(morpheus_generation_service *service,
                                     const char *canonical_lemma,
                                     morpheus_generation_visitor visitor,
                                     void *state, size_t *form_count,
                                     size_t *skipped_records)
{
	morpheus_runtime_context *previous;
	morpheus_generation_status result;
	int found = 0;

	if (!service || !canonical_lemma || !*canonical_lemma || !visitor ||
	    !form_count)
		return MORPHEUS_GENERATION_INVALID;
	*form_count = 0;
	if (skipped_records)
		*skipped_records = 0;
	/* Keys beginning with '-' hold compound-only stems, not lemmas. */
	if (canonical_lemma[0] == '-')
		return MORPHEUS_GENERATION_NOT_FOUND;
	previous = morpheus_runtime_context_activate(service->context);
	morpheus_runtime_context_set_language(service->context,GREEK);
	morpheus_runtime_context_clear_error(service->context);
	result = generate_key(service,canonical_lemma,canonical_lemma,NULL,visitor,
	                      state,form_count,skipped_records,&found);
	if (result == MORPHEUS_GENERATION_OK)
		result = generate_compounds(service,canonical_lemma,visitor,state,
		                            form_count,skipped_records,&found);
	morpheus_runtime_context_activate(previous);
	if (result == MORPHEUS_GENERATION_OK && !found)
		return MORPHEUS_GENERATION_NOT_FOUND;
	return result;
}
