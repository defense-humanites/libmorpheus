/* SPDX-License-Identifier: MPL-2.0 */

#include "generation_service.h"

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
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
 * generated for a compound, and the keys of a preverb variant after them.
 */
static char *
record_keys(const char *source, const char *preverbs, const char *variant)
{
	char *copy;
	char *cursor;
	size_t length = strlen(source);
	size_t added = preverbs ? strlen(" pb:") + strlen(preverbs) : 0;
	size_t variant_length = variant ? 1 + strlen(variant) : 0;

	copy = malloc(length + added + variant_length + 1);
	if (!copy)
		return NULL;
	memcpy(copy,source,length + 1);
	if (preverbs) {
		memcpy(copy + length," pb:",4);
		memcpy(copy + length + 4,preverbs,strlen(preverbs) + 1);
	}
	if (variant) {
		copy[length + added] = ' ';
		memcpy(copy + length + added + 1,variant,strlen(variant) + 1);
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
 * The raw forms a request has returned, with their readings, so that a
 * preverb variant or the unaugmented pass returns only the forms that its
 * flags change (an apocope pass on a)na/ also yields the forms where nothing
 * is cut).
 */
typedef struct {
	char **slots;
	size_t capacity;
	size_t count;
} surface_set;

static size_t
surface_hash(const char *text)
{
	size_t hash = 2166136261u;

	for (; *text; text++)
		hash = (hash ^ (unsigned char)*text) * 16777619u;
	return hash;
}

static void
surface_set_free(surface_set *set)
{
	size_t slot;

	for (slot = 0; slot != set->capacity; slot++)
		free(set->slots[slot]);
	free(set->slots);
	set->slots = NULL;
	set->capacity = set->count = 0;
}

static int
surface_set_has(const surface_set *set, const char *text)
{
	size_t slot;

	if (!set->capacity)
		return 0;
	for (slot = surface_hash(text) & (set->capacity - 1); set->slots[slot];
	     slot = (slot + 1) & (set->capacity - 1))
		if (!strcmp(set->slots[slot],text))
			return 1;
	return 0;
}

/* Returns 0 when out of memory. */
static int
surface_set_add(surface_set *set, const char *text)
{
	size_t slot;
	size_t length;

	if ((set->count + 1) * 2 > set->capacity) {
		surface_set grown = { 0 };
		size_t old;

		grown.capacity = set->capacity ? set->capacity * 2 : 1024;
		grown.slots = calloc(grown.capacity,sizeof *grown.slots);
		if (!grown.slots)
			return 0;
		for (old = 0; old != set->capacity; old++) {
			char *moved = set->slots[old];

			if (!moved)
				continue;
			for (slot = surface_hash(moved) & (grown.capacity - 1);
			     grown.slots[slot]; slot = (slot + 1) & (grown.capacity - 1))
				;
			grown.slots[slot] = moved;
		}
		grown.count = set->count;
		free(set->slots);
		*set = grown;
	}
	for (slot = surface_hash(text) & (set->capacity - 1); set->slots[slot];
	     slot = (slot + 1) & (set->capacity - 1))
		if (!strcmp(set->slots[slot],text))
			return 1;
	length = strlen(text);
	set->slots[slot] = malloc(length + 1);
	if (!set->slots[slot])
		return 0;
	memcpy(set->slots[slot],text,length + 1);
	set->count++;
	return 1;
}

/* Adds the forms of another set. Returns 0 when out of memory. */
static int
surface_set_merge(surface_set *set, const surface_set *from)
{
	size_t slot;

	for (slot = 0; slot != from->capacity; slot++)
		if (from->slots[slot] && !surface_set_add(set,from->slots[slot]))
			return 0;
	return 1;
}

/* One pass of generation for a requested lemma. */
typedef struct {
	morpheus_generation_service *service;
	const char *lemma;
	/* The compound's preverbs, NULL for the lemma's own records. */
	const char *preverbs;
	/* A preverb variant, or NULL. */
	const morpheus_preverb_variant *variant;
	/* Forms returned so far, when variants are to follow. */
	surface_set *seen;
	/*
	 * The forms of the current variant pass, which join seen when the pass
	 * ends: a variant may give one surface several readings (cune/ballon,
	 * first singular and third plural), and each must reach the visitor.
	 */
	surface_set *added;
	/* The unaugmented pass, alone or combined with a preverb variant. */
	int unaugmented;
	/* Whether the preverb variants are generated. */
	int preverb_variants;
	morpheus_generation_visitor visitor;
	void *state;
	size_t *form_count;
	size_t *skipped_records;
	int *found;
} generation_pass;

/*
 * Analysis reads an unaspirated preverb before a rough breathing (a)pi/keto)
 * as Ionic (checkgenwds.c) and labels the reading Ionic alone, so such a
 * form must allow Ionic; morpheus_generation_form_dialect() then leaves out
 * the forms whose preverb, augment, stem or ending exclude it. Analysis keeps
 * those with every dialect, as AndDialect() returns -1 there.
 */
static int
ionic_form(gk_word *form)
{
	Dialect requested = dialect_of(form);

	set_dialect(form,requested ? (Dialect)(requested & IONIC) : IONIC);
	return dialect_of(form) != 0;
}

int
morpheus_generation_form_dialect(const gk_word *form, unsigned *dialect)
{
	const unsigned named[] = {
		(unsigned short)dialect_of(prvb_gstr_of(form)),
		(unsigned short)dialect_of(aug1_gstr_of(form)),
		(unsigned short)dialect_of(stem_gstr_of(form)),
		(unsigned short)dialect_of(ends_gstr_of(form)),
		(unsigned short)dialect_of(form)
	};
	unsigned result = 0;
	int constrained = 0;
	size_t part;

	for (part = 0; part != sizeof named / sizeof *named; part++) {
		if (!named[part])
			continue;
		result = constrained ? result & named[part] : named[part];
		constrained = 1;
	}
	if (dialect)
		*dialect = result;
	return !constrained || result != 0;
}

/*
 * Gives every part of a form that names dialects the union of them, so that
 * the form takes them all (see generate_record).
 */
static void
join_dialects(gk_word *form)
{
	Dialect joined = (Dialect)(dialect_of(prvb_gstr_of(form)) |
	                           dialect_of(aug1_gstr_of(form)) |
	                           dialect_of(stem_gstr_of(form)) |
	                           dialect_of(ends_gstr_of(form)) |
	                           dialect_of(form));

	if (dialect_of(prvb_gstr_of(form)))
		set_dialect(prvb_gstr_of(form),joined);
	if (dialect_of(aug1_gstr_of(form)))
		set_dialect(aug1_gstr_of(form),joined);
	if (dialect_of(stem_gstr_of(form)))
		set_dialect(stem_gstr_of(form),joined);
	if (dialect_of(ends_gstr_of(form)))
		set_dialect(ends_gstr_of(form),joined);
	if (dialect_of(form))
		set_dialect(form,joined);
}

/*
 * Analysis reads a verb form that lacks the augment of the indicative
 * imperfect, aorist or pluperfect as Homeric or Ionic (checkstring.c,
 * checkgenwds.c): a)/gon, a)gorh/sato, a)po/balon. It requests these
 * dialects for the form, so that an ending of other dialects only does not
 * match, and drops a reading that is not indicative.
 */
#define UNAUGMENTED_KEYS "unaugmented"

static const morpheus_preverb_variant unaugmented_variant = {
	UNAUGMENTED_KEYS, NULL
};

static int
unaugmented_form(gk_word *form)
{
	Dialect requested = dialect_of(form);

	if (mood_of(forminfo_of(form)) != INDICATIVE)
		return 0;
	set_dialect(form,requested ? (Dialect)(requested & (IONIC|EPIC)) :
	                             (Dialect)(IONIC|EPIC));
	return dialect_of(form) != 0;
}

/*
 * Whether a form of a preverb variant is one analysis accepts. The form must
 * begin as one of the table's spellings of the variant does (the augment
 * before a)po/ is h)f-, before a rough breathing: not h)pw/llun), letters
 * compared without breathings, accents or quantities. Analysis accepts an
 * unaspirated preverb in Ionic only (ionic_form), and an augment before the
 * preverb (prevb_augment) only where the verb takes one: the indicative
 * imperfect, aorist and pluperfect, unless the form is unaugmented or
 * iterative (genwd.c checks this for regular stems, not for irregular
 * forms).
 */
static int
variant_form(const morpheus_preverb_variant *variant, gk_word *form)
{
	word_form info = forminfo_of(form);
	gk_string *parts[3];
	size_t part;

	if (variant->prefixes) {
		const char *prefix = variant->prefixes;
		const char *surface = workword_of(form);
		int matched = 0;

		for (; *prefix && !matched; prefix += strlen(prefix) + 1) {
			const char *letter = prefix;
			const char *cursor = surface;

			while (*letter && *cursor) {
				if (*cursor < 'a' || *cursor > 'z') {
					cursor++;
					continue;
				}
				if (*cursor != *letter)
					break;
				cursor++;
				letter++;
			}
			matched = !*letter;
		}
		if (!matched)
			return 0;
	}
	if (strstr(variant->keys,UNAUGMENTED_KEYS) && !unaugmented_form(form))
		return 0;
	if (strstr(variant->keys,"unasp_preverb"))
		return ionic_form(form);
	if (strstr(variant->keys,UNAUGMENTED_KEYS))
		return 1;
	if (!strstr(variant->keys,"prevb_augment"))
		return 1;
	if (mood_of(info) != INDICATIVE ||
	    (tense_of(info) != IMPERF && tense_of(info) != AORIST &&
	     tense_of(info) != PLUPERF))
		return 0;
	parts[0] = stem_gstr_of(form);
	parts[1] = ends_gstr_of(form);
	parts[2] = prvb_gstr_of(form);
	if (has_morphflag(morphflags_of(form),ITERATIVE) ||
	    has_morphflag(morphflags_of(form),UNAUGMENTED))
		return 0;
	for (part = 0; part != 3; part++)
		if (has_morphflag(morphflags_of(parts[part]),ITERATIVE) ||
		    has_morphflag(morphflags_of(parts[part]),UNAUGMENTED))
			return 0;
	return 1;
}

/*
 * A raw form and its reading, as the passes compare them: a variant or an
 * unaugmented form that the flags leave unchanged repeats an earlier form
 * and its reading, while one that only shares its surface is another
 * reading (unaugmented lu=on, an imperfect, beside the participle lu=on).
 */
static void
form_reading(const gk_word *form, char *reading, size_t size)
{
	word_form info = forminfo_of(form);

	snprintf(reading,size,"%s|%x|%x|%x|%x|%x|%x|%x|%x",workword_of(form),
	         (unsigned)tense_of(info),(unsigned)mood_of(info),
	         (unsigned)voice_of(info),(unsigned)person_of(info),
	         (unsigned)number_of(info),(unsigned)case_of(info),
	         (unsigned)gender_of(info),(unsigned)degree_of(info));
}

/*
 * *unusable is set when the record failed before any of its forms reached the
 * visitor, so the caller may skip it without exposing a partial record.
 */
static morpheus_generation_status
generate_record(const generation_pass *pass,
                const morpheus_gener_record_view *record, int *unusable)
{
	morpheus_generation_service *service = pass->service;
	const char *preverbs = pass->preverbs;
	size_t *form_count = pass->form_count;
	gk_word input = { 0 };
	gk_word *forms;
	char *keys;
	size_t form;
	int irregular;
	int mode;
	/*
	 * A record that forces its ending states the form and its dialects
	 * itself: eu)-triain hs_ou,masc,aeolic end:a nom sg is the Aeolic and
	 * epic nominative eu)tri/aina, though the ending table names that ending
	 * epic only. Such a form keeps the dialects of all its parts.
	 */
	int stated = strstr(record->keys,"end:") != NULL;

	set_lemma(&input,pass->lemma);
	set_stem(&input,record->stem);
	keys = record_keys(record->keys,preverbs,
	                   pass->variant ? pass->variant->keys : NULL);
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
		if (pass->variant && !variant_form(pass->variant,forms + form))
			continue;
		if (!morpheus_generation_form_dialect(forms + form,NULL)) {
			if (!stated)
				continue;
			join_dialects(forms + form);
		}
		if (pass->seen) {
			char reading[MAXWORDSIZE + 64];

			form_reading(forms + form,reading,sizeof reading);
			if (pass->variant && surface_set_has(pass->seen,reading))
				continue;
			if (!surface_set_add(pass->variant ? pass->added : pass->seen,
			                     reading)) {
				release_forms(forms);
				release_input(&input);
				return MORPHEUS_GENERATION_NO_MEMORY;
			}
		}
		if (*form_count == SIZE_MAX) {
			release_forms(forms);
			release_input(&input);
			return MORPHEUS_GENERATION_ENGINE_ERROR;
		}
		(*form_count)++;
		if (!pass->visitor(forms + form,pass->state)) {
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
generate_key(const generation_pass *pass, const char *key)
{
	morpheus_generation_service *service = pass->service;
	const char *preverbs = pass->preverbs;
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
	*pass->found = 1;
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
			/*
			 * Only a stem takes or leaves the augment: an irregular
			 * form is spelled out with its own.
			 */
			if (pass->unaugmented &&
			    record.kind != MORPHEUS_GENER_RECORD_VERB_STEM)
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
			result = generate_record(pass,&record,&unusable);
			if (unusable && pass->skipped_records) {
				/* A record the engine cannot generate leaves the others usable. */
				morpheus_runtime_context_clear_error(service->context);
				/* A variant pass reads records the plain pass counted. */
				if (!pass->variant)
					(*pass->skipped_records)++;
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
generate_decomposition(generation_pass *pass,
                       const morpheus_compound_decomposition *decomposition)
{
	char reserved[MAXWORDSIZE + 1];
	morpheus_generation_status result;

	pass->preverbs = decomposition->preverbs;
	result = generate_key(pass,decomposition->lemma);
	if (result != MORPHEUS_GENERATION_OK)
		return result;
	reserved[0] = '-';
	memcpy(reserved + 1,decomposition->lemma,strlen(decomposition->lemma) + 1);
	return generate_key(pass,reserved);
}

/*
 * A compound listed as its own decomposition (a)mfi/-a)mfisbhte/w) adds
 * nothing to the lemma's own records but duplicates.
 */
static int
composes(const morpheus_compound_decomposition *decomposition,
         const char *lemma)
{
	return strcmp(decomposition->lemma,lemma) != 0;
}

/*
 * The variants of a single preverb that analysis accepts (apocope, ἐς for
 * εἰς, the augment before the preverb, psilosis...) are generated after the
 * plain forms, from the same records with the variant's flags; a variant
 * returns only the forms its flags change. A compound of several preverbs
 * has none: the engine applies the flags at either end of the chain, while
 * analysis may find a variant at any preverb.
 */
static morpheus_generation_status
generate_variants(generation_pass *pass,
                  const morpheus_compound_decomposition *decomposition)
{
	const morpheus_preverb_variant *variants = NULL;
	morpheus_generation_status result = MORPHEUS_GENERATION_OK;
	size_t count = 0;
	size_t variant;

	if (strchr(decomposition->preverbs,','))
		return MORPHEUS_GENERATION_OK;
	if (morpheus_compound_preverb_variants(&pass->service->compounds,
	                                       decomposition->preverbs,&variants,
	                                       &count) != MORPHEUS_COMPOUND_OK)
		return MORPHEUS_GENERATION_NO_MEMORY;
	for (variant = 0; variant != count && result == MORPHEUS_GENERATION_OK;
	     variant++) {
		surface_set added = { 0 };

		pass->variant = variants + variant;
		pass->added = &added;
		result = generate_decomposition(pass,decomposition);
		if (result == MORPHEUS_GENERATION_OK &&
		    !surface_set_merge(pass->seen,&added))
			result = MORPHEUS_GENERATION_NO_MEMORY;
		surface_set_free(&added);
	}
	pass->variant = NULL;
	pass->added = NULL;
	return result;
}

/*
 * Ends a pass of the unaugmented forms: its forms join those returned before
 * the next pass compares with them.
 */
static morpheus_generation_status
end_pass(generation_pass *pass, morpheus_generation_status result)
{
	if (result == MORPHEUS_GENERATION_OK &&
	    !surface_set_merge(pass->seen,pass->added))
		result = MORPHEUS_GENERATION_NO_MEMORY;
	surface_set_free(pass->added);
	return result;
}

/*
 * The unaugmented forms of the lemma and of its compounds come last, from
 * their verb stems with the key unaugmented, then those of the preverb
 * variants other than the augment before the preverb (apocope, psilosis:
 * a)pi/kato). Like a variant, the pass returns only the forms and readings
 * that differ from those already returned.
 */
static morpheus_generation_status
generate_unaugmented(generation_pass *pass,
                     const morpheus_compound_decomposition *decompositions,
                     size_t count)
{
	morpheus_generation_status result;
	surface_set added = { 0 };
	size_t item;

	pass->unaugmented = 1;
	pass->variant = &unaugmented_variant;
	pass->added = &added;
	pass->preverbs = NULL;
	result = generate_key(pass,pass->lemma);
	for (item = 0; item != count && result == MORPHEUS_GENERATION_OK; item++)
		if (composes(decompositions + item,pass->lemma))
			result = generate_decomposition(pass,decompositions + item);
	result = end_pass(pass,result);
	for (item = 0; pass->preverb_variants && item != count &&
	               result == MORPHEUS_GENERATION_OK; item++) {
		const morpheus_preverb_variant *variants = NULL;
		size_t variant_count = 0;
		size_t variant;

		if (!composes(decompositions + item,pass->lemma) ||
		    strchr(decompositions[item].preverbs,','))
			continue;
		if (morpheus_compound_preverb_variants(&pass->service->compounds,
		                                       decompositions[item].preverbs,
		                                       &variants,&variant_count) !=
		    MORPHEUS_COMPOUND_OK) {
			result = MORPHEUS_GENERATION_NO_MEMORY;
			break;
		}
		for (variant = 0; variant != variant_count &&
		                  result == MORPHEUS_GENERATION_OK; variant++) {
			char keys[256];
			morpheus_preverb_variant combined;

			if (strstr(variants[variant].keys,"prevb_augment"))
				continue;
			if ((size_t)snprintf(keys,sizeof keys,"%s %s",
			                     variants[variant].keys,UNAUGMENTED_KEYS) >=
			    sizeof keys)
				continue;
			combined.keys = keys;
			combined.prefixes = variants[variant].prefixes;
			pass->variant = &combined;
			result = end_pass(pass,
			                  generate_decomposition(pass,decompositions + item));
		}
	}
	surface_set_free(&added);
	pass->unaugmented = 0;
	pass->variant = NULL;
	pass->added = NULL;
	pass->preverbs = NULL;
	return result;
}

morpheus_generation_status
morpheus_generation_service_generate(morpheus_generation_service *service,
                                     const char *canonical_lemma,
                                     morpheus_generation_visitor visitor,
                                     void *state, size_t *form_count,
                                     size_t *skipped_records)
{
	return morpheus_generation_service_generate_flags(
	    service,canonical_lemma,0,visitor,state,form_count,skipped_records);
}

morpheus_generation_status
morpheus_generation_service_generate_flags(
    morpheus_generation_service *service, const char *canonical_lemma,
    unsigned flags, morpheus_generation_visitor visitor, void *state,
    size_t *form_count, size_t *skipped_records)
{
	morpheus_runtime_context *previous;
	morpheus_generation_status result = MORPHEUS_GENERATION_OK;
	morpheus_compound_decomposition *decompositions = NULL;
	size_t count = 0;
	size_t item;
	surface_set seen = { 0 };
	generation_pass pass = { 0 };
	int found = 0;
	int variants = 0;
	int unaugmented;

	if (!service || !canonical_lemma || !*canonical_lemma || !visitor ||
	    !form_count ||
	    (flags & ~(MORPHEUS_GENERATION_SERVICE_NO_PREVERB_VARIANTS|
	               MORPHEUS_GENERATION_SERVICE_NO_UNAUGMENTED)))
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
	if (morpheus_compound_decompositions(&service->compounds,canonical_lemma,
	                                     &decompositions,&count) !=
	    MORPHEUS_COMPOUND_OK)
		result = MORPHEUS_GENERATION_NO_MEMORY;
	for (item = 0; item != count; item++)
		if (composes(decompositions + item,canonical_lemma) &&
		    !strchr(decompositions[item].preverbs,','))
			variants = 1;
	if (flags & MORPHEUS_GENERATION_SERVICE_NO_PREVERB_VARIANTS)
		variants = 0;
	pass.service = service;
	pass.lemma = canonical_lemma;
	unaugmented = !(flags & MORPHEUS_GENERATION_SERVICE_NO_UNAUGMENTED);
	pass.seen = variants || unaugmented ? &seen : NULL;
	pass.visitor = visitor;
	pass.state = state;
	pass.form_count = form_count;
	pass.skipped_records = skipped_records;
	pass.found = &found;
	pass.preverb_variants = variants;
	if (result == MORPHEUS_GENERATION_OK)
		result = generate_key(&pass,canonical_lemma);
	for (item = 0; item != count && result == MORPHEUS_GENERATION_OK; item++)
		if (composes(decompositions + item,canonical_lemma))
			result = generate_decomposition(&pass,decompositions + item);
	for (item = 0; variants && item != count &&
	               result == MORPHEUS_GENERATION_OK; item++)
		if (composes(decompositions + item,canonical_lemma))
			result = generate_variants(&pass,decompositions + item);
	if (unaugmented && result == MORPHEUS_GENERATION_OK)
		result = generate_unaugmented(&pass,decompositions,count);
	morpheus_runtime_context_activate(previous);
	free(decompositions);
	surface_set_free(&seen);
	if (result == MORPHEUS_GENERATION_OK && !found)
		return MORPHEUS_GENERATION_NOT_FOUND;
	return result;
}
