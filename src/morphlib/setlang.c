#include "morphlib_internal.h"

static _Thread_local morpheus_runtime_context default_context = { 0, 0 };
static _Thread_local morpheus_runtime_context *active_context;

static void
destroy_end_index(endind *index)
{
	if (!index) return;
	free(endbuffer_of(index));
	free(endeptr_of(index));
	free(index);
}

morpheus_runtime_context *
morpheus_runtime_context_current(void)
{
	return(active_context ? active_context : &default_context);
}

morpheus_runtime_context *
morpheus_runtime_context_create(void)
{
	morpheus_runtime_context *context = calloc(1,sizeof *context);

	if (context) context->heap_allocated = 1;
	return(context);
}

void
morpheus_runtime_context_destroy(morpheus_runtime_context *context)
{
	size_t i;

	if (!context || !context->heap_allocated) return;
	if (active_context == context) active_context = NULL;
	free(context->stemlib_path);
	free(context->hidden_morphflag_table);
	free(context->preverb_morphflag_table);
	if (context->raw_preverb_table)
		FreeGkString(context->raw_preverb_table);
	if (context->vowel_contraction_table)
		FreeGkString(context->vowel_contraction_table);
	if (context->consonant_euphony_table)
		FreeGkString(context->consonant_euphony_table);
	if (context->suffix_table_file)
		fclose(context->suffix_table_file);
	for (i = 0; i < MORPHEUS_INDEX_FILE_CACHE_SIZE; i++) {
		if (context->index_files[i])
			fclose(context->index_files[i]);
		free(context->index_file_paths[i]);
	}
	if (context->ending_store)
		FreeGkString(context->ending_store);
	destroy_end_index(context->dictionary_entry_index);
	destroy_end_index(context->compound_verb_index);
	destroy_end_index(context->verb_ending_index);
	destroy_end_index(context->derivation_ending_index);
	destroy_end_index(context->nominal_ending_index);
	destroy_end_index(context->verb_stem_index);
	for (i = 0; i < MORPHEUS_END_CACHE_SIZE; i++) {
		if (context->ending_cache[i])
			FreeGkString(context->ending_cache[i]);
	}
	free(context->verb_dictionary_tags);
	free(context->nominal_dictionary_tags);
	free(context->lemma_dictionary_tags);
	for (i = 0; i < MORPHEUS_DERIVATION_BUFFER_COUNT; i++) {
		if (context->derivation_stem_buffers[i])
			FreeGkString(context->derivation_stem_buffers[i]);
		if (context->derivation_quantity_buffers[i])
			FreeGkString(context->derivation_quantity_buffers[i]);
	}
	for (i = 0; i < MORPHEUS_DERIVATION_CACHE_SIZE; i++)
		free(context->derivation_cache_keys[i]);
	for (i = 0; i < (size_t)context->compound_head_count; i++)
		free(context->compound_head_table[i]);
	free(context->compound_head_table);
	free(context->analysis_print_buffer);
	for (i = 0; i < MORPHEUS_AUGMENT_STEM_COUNT; i++) {
		if (context->analysis_augmented_stems[i])
			FreeGkString(context->analysis_augmented_stems[i]);
		if (context->analysis_augmented_quantities[i])
			FreeGkString(context->analysis_augmented_quantities[i]);
	}
	for (i = 0; i < MORPHEUS_POSSIBLE_STEM_COUNT; i++) {
		if (context->analysis_possible_stems[i])
			FreeGkString(context->analysis_possible_stems[i]);
		free(context->analysis_possible_keys[i]);
	}
	for (i = 0; i < MORPHEUS_IRREGULAR_FORM_COUNT; i++) {
		free(context->analysis_irregular_forms[i]);
		free(context->analysis_irregular_keys[i]);
	}
	for (i = 0; i < sizeof context->smk_beta_table /
				 sizeof context->smk_beta_table[0]; i++) {
		free(context->smk_beta_table[i]);
		free(context->smarta_beta_table[i]);
	}
	free(context->morph_key_table);
	free(context->stem_type_arguments);
	free(context->derivation_type_arguments);
	free(context->domain_arguments);
	free(context);
}

morpheus_runtime_context *
morpheus_runtime_context_activate(morpheus_runtime_context *context)
{
	morpheus_runtime_context *previous = morpheus_runtime_context_current();

	active_context = context;
	return(previous);
}

void
morpheus_runtime_context_set_language(
	morpheus_runtime_context *context, int language)
{
	if (context) context->language = language;
}

int
morpheus_runtime_context_language(const morpheus_runtime_context *context)
{
	return(context ? context->language : default_context.language);
}

void
morpheus_runtime_context_clear_error(morpheus_runtime_context *context)
{
	if (context) {
		context->runtime_error = MORPHEUS_RUNTIME_ERROR_NONE;
		context->analysis_storage_error = 0;
	}
}

morpheus_runtime_error
morpheus_runtime_context_error(const morpheus_runtime_context *context)
{
	return(context ? context->runtime_error : MORPHEUS_RUNTIME_ERROR_NONE);
}

void
morpheus_runtime_error_record(morpheus_runtime_error error)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();

	if (context->runtime_error == MORPHEUS_RUNTIME_ERROR_NONE)
		context->runtime_error = error;
}

int
morpheus_runtime_string_append(char *destination, const char *source,
			       size_t capacity)
{
	if (Xstrncat(destination,source,capacity)) return(1);
	morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
	return(0);
}

void set_lang(int n)
{
	morpheus_runtime_context_current()->language = n;
}

int cur_lang(void)
{
	return(morpheus_runtime_context_current()->language);
}
