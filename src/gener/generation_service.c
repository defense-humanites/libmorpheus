/* SPDX-License-Identifier: MPL-2.0 */

#include "generation_service.h"

#include <ctype.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <modes.h>

#include "gener_internal.h"
#include "../morphlib/gkstring.proto.h"
#include "../morphlib/runtime_context_internal.h"

struct morpheus_generation_service {
	const morpheus_gener_index *index;
	morpheus_runtime_context *context;
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

static char *
record_keys(const char *source)
{
	char *copy;
	char *cursor;
	size_t length = strlen(source);

	copy = malloc(length + 1);
	if (!copy)
		return NULL;
	memcpy(copy,source,length + 1);
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

static morpheus_generation_status
generate_record(morpheus_generation_service *service, const char *lemma,
                const morpheus_gener_record_view *record,
                morpheus_generation_visitor visitor, void *state,
                size_t *form_count)
{
	gk_word input = { 0 };
	gk_word *forms;
	char *keys;
	size_t form;
	int irregular;
	int mode;

	set_lemma(&input,lemma);
	set_stem(&input,record->stem);
	keys = record_keys(record->keys);
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
		return status;
	}
	if (morpheus_runtime_context_error(service->context) !=
	    MORPHEUS_RUNTIME_ERROR_NONE) {
		morpheus_generation_status status = runtime_status(service->context);
		release_forms(forms);
		release_input(&input);
		return status;
	}
	for (form = 0; workword_of(forms + form)[0]; form++) {
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
	created->index = index;
	*service = created;
	return MORPHEUS_GENERATION_OK;
}

void
morpheus_generation_service_destroy(morpheus_generation_service *service)
{
	if (!service)
		return;
	morpheus_runtime_context_destroy(service->context);
	free(service);
}

morpheus_generation_status
morpheus_generation_service_generate(morpheus_generation_service *service,
                                     const char *canonical_lemma,
                                     morpheus_generation_visitor visitor,
                                     void *state, size_t *form_count)
{
	morpheus_gener_lemma_view lemma;
	morpheus_runtime_context *previous;
	morpheus_generation_status result = MORPHEUS_GENERATION_OK;
	uint64_t block_number;

	if (!service || !canonical_lemma || !*canonical_lemma || !visitor ||
	    !form_count)
		return MORPHEUS_GENERATION_INVALID;
	*form_count = 0;
	switch (morpheus_gener_index_lookup(service->index,canonical_lemma,&lemma)) {
	case MORPHEUS_GENER_INDEX_OK:
		break;
	case MORPHEUS_GENER_INDEX_NOT_FOUND:
		return MORPHEUS_GENERATION_NOT_FOUND;
	default:
		return MORPHEUS_GENERATION_INVALID;
	}
	previous = morpheus_runtime_context_activate(service->context);
	morpheus_runtime_context_set_language(service->context,GREEK);
	morpheus_runtime_context_clear_error(service->context);
	for (block_number = lemma.first_block;
	     block_number != lemma.first_block + lemma.block_count; block_number++) {
		morpheus_gener_block_view block;
		uint64_t record_number;

		if (morpheus_gener_index_block(service->index,block_number,&block) !=
		    MORPHEUS_GENER_INDEX_OK) {
			result = MORPHEUS_GENERATION_INVALID;
			break;
		}
		for (record_number = block.first_record;
		     record_number != block.first_record + block.record_count;
		     record_number++) {
			morpheus_gener_record_view record;

			if (morpheus_gener_index_record(service->index,record_number,
			                                &record) !=
			    MORPHEUS_GENER_INDEX_OK) {
				result = MORPHEUS_GENERATION_INVALID;
				break;
			}
			result = generate_record(service,canonical_lemma,&record,visitor,
			                         state,form_count);
			if (result != MORPHEUS_GENERATION_OK)
				break;
		}
		if (result != MORPHEUS_GENERATION_OK)
			break;
	}
	morpheus_runtime_context_activate(previous);
	return result;
}
