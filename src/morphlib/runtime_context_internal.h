/* SPDX-License-Identifier: MPL-2.0 */

#ifndef MORPHEUS_RUNTIME_CONTEXT_INTERNAL_H
#define MORPHEUS_RUNTIME_CONTEXT_INTERNAL_H

#include <gkstring.h>
#include <endtags.h>
#include <endindex.h>
#include "morphargs.h"

#include "runtime_context.h"

#define MORPHEUS_END_CACHE_SIZE 45
#define MORPHEUS_DERIVATION_BUFFER_COUNT 4
#define MORPHEUS_DERIVATION_CACHE_SIZE 12
#define MORPHEUS_AUGMENT_STEM_COUNT 12
#define MORPHEUS_POSSIBLE_STEM_COUNT 10
#define MORPHEUS_IRREGULAR_FORM_COUNT 3
#define MORPHEUS_BYTE_TABLE_SIZE 256

struct morpheus_runtime_context {
	int language;
	int heap_allocated;
	char *stemlib_path;
	void *public_generation_index;
	void *public_generation_service;
	void (*public_generation_cleanup)(struct morpheus_runtime_context *);
	unsigned char comparison_table[MORPHEUS_BYTE_TABLE_SIZE];
	unsigned char beta_table[MORPHEUS_BYTE_TABLE_SIZE];
	int comparison_table_initialized;
	int beta_table_initialized;
	char *hidden_morphflag_table;
	char *preverb_morphflag_table;
	gk_string *raw_preverb_table;
	int raw_preverb_count;
	int raw_preverb_language;
	gk_string *vowel_contraction_table;
	int vowel_contraction_count;
	int vowel_contraction_language;
	gk_string *consonant_euphony_table;
	int consonant_euphony_count;
	int consonant_euphony_language;
	gk_string *ending_cache[MORPHEUS_END_CACHE_SIZE];
	int ending_cache_current;
	int ending_cache_size;
	int ending_cache_language;
	int ending_cache_initialized;
	int ending_start_match;
	FILE *suffix_table_file;
	int suffix_table_unavailable;
	gk_string *ending_store;
	int ending_store_count;
	int ending_store_max_string;
	endind *dictionary_entry_index;
	endind *compound_verb_index;
	endind *verb_ending_index;
	endind *derivation_ending_index;
	endind *nominal_ending_index;
	endind *verb_stem_index;
	endtags *verb_dictionary_tags;
	endtags *nominal_dictionary_tags;
	endtags *lemma_dictionary_tags;
	int verb_dictionary_tag_count;
	int nominal_dictionary_tag_count;
	int lemma_dictionary_tag_count;
	int dictionary_tag_language;
	int dictionary_tag_hq_mode;
	int dictionary_tags_initialized;
	int dictionary_hq_mode;
	int dictionary_hq_availability_checked;
	int dictionary_hq_available;
	int dictionary_hq_availability_language;
	gk_string *derivation_stem_buffers[MORPHEUS_DERIVATION_BUFFER_COUNT];
	gk_string *derivation_quantity_buffers[MORPHEUS_DERIVATION_BUFFER_COUNT];
	int derivation_buffers_initialized;
	char derivation_cache_stems[MORPHEUS_DERIVATION_CACHE_SIZE]
		[MAXWORDSIZE+1];
	char *derivation_cache_keys[MORPHEUS_DERIVATION_CACHE_SIZE];
	int derivation_cache_index;
	int derivation_cache_language;
	int derivation_cache_initialized;
	int derivation_checked_suffixes;
	int derivation_checked_stems;
	int derivation_real_stems;
	char **compound_head_table;
	int compound_head_count;
	int compound_head_capacity;
	int compound_head_table_initialized;
	char *analysis_print_buffer;
	size_t analysis_print_capacity;
	char analysis_previous_lemma[MAXWORDSIZE];
	char analysis_previous_word[MAXWORDSIZE];
	char analysis_previous_stem[MAXWORDSIZE];
	int analysis_current_number;
	gk_string *analysis_augmented_stems[MORPHEUS_AUGMENT_STEM_COUNT];
	gk_string *analysis_augmented_quantities[MORPHEUS_AUGMENT_STEM_COUNT];
	int analysis_augmented_stems_initialized;
	gk_string *analysis_possible_stems[MORPHEUS_POSSIBLE_STEM_COUNT];
	char *analysis_possible_keys[MORPHEUS_POSSIBLE_STEM_COUNT];
	int analysis_possible_stems_initialized;
	char *analysis_irregular_forms[MORPHEUS_IRREGULAR_FORM_COUNT];
	char *analysis_irregular_keys[MORPHEUS_IRREGULAR_FORM_COUNT];
	int analysis_irregular_buffers_initialized;
	int analysis_crasis_disabled;
	int analysis_quick_enabled;
	Dialect analysis_wanted_dialects;
	int analysis_wanted_dialects_initialized;
	int analysis_total_analyses;
	int analysis_total_lemmas;
	int analysis_storage_error;
	int smarta_greek_table[256];
	int smarta_accent_table[256];
	int smarta_tables_initialized;
	int smarta_current_font;
	int smarta_character_style;
	char *smk_beta_table[257];
	char *smarta_beta_table[257];
	char **active_inverse_conversion_table;
	char inverse_smarta_characters[257];
	int inverse_conversion_tables_initialized;
	int inverse_conversion_from_smk;
	int inverse_conversion_current_font;
	Morph_args *stem_type_arguments;
	Morph_args *derivation_type_arguments;
	Morph_args *domain_arguments;
	const Morph_args **morph_key_table;
	int morph_key_stem_count;
	int morph_key_derivation_count;
	int morph_key_domain_count;
	int morph_key_count;
	int morph_keys_initialized;
	int morph_key_language;
	int files_opened;
	morpheus_runtime_error runtime_error;
	char volume_name[128];
};

int morpheus_runtime_string_append(char *destination, const char *source,
                                   size_t capacity);

morpheus_runtime_context *morpheus_runtime_context_current(void);

#endif
