/* SPDX-License-Identifier: MPL-2.0 */

#include "generation_normalizer.h"

#include <stdlib.h>
#include <string.h>

#include "legacy_values.h"

struct morpheus_normalized_generation_result {
	size_t count;
	size_t capacity;
	size_t skipped_records;
	morpheus_normalized_generation *records;
};

typedef struct {
	morpheus_normalized_generation_result *result;
	size_t limit;
	int limit_exceeded;
	int no_memory;
} collector;

static uint32_t
effective_dialect(const gk_word *form)
{
	uint32_t augment = (uint32_t)(unsigned short)dialect_of(aug1_gstr_of(form));
	uint32_t ending = (uint32_t)(unsigned short)dialect_of(ends_gstr_of(form));
	uint32_t stem = (uint32_t)(unsigned short)dialect_of(stem_gstr_of(form));
	uint32_t dialect = stem & ending;
	uint32_t constraint = (uint32_t)(unsigned short)dialect_of(form);

	/* Match the effective-dialect calculation used by the legacy renderer. */
	if (!dialect)
		dialect =
		    (uint32_t)(unsigned short)dialect_of(prvb_gstr_of(form)) |
		    augment | stem | ending;
	if (augment)
		dialect &= augment;
	if (constraint)
		dialect &= constraint;
	return dialect;
}

static int
copy_text(char *destination, size_t capacity, const char *source)
{
	size_t length = strlen(source);
	size_t copied = length < capacity ? length : capacity - 1;

	memcpy(destination,source,copied);
	destination[copied] = 0;
	return length >= capacity;
}

/*
 * Generated surfaces keep the hyphen that marks the stem boundary in the stem
 * source (a)nqr-w/pwn). It is not part of the form: drop it, as lemma keys
 * already do.
 */
static int
copy_surface(char *destination, size_t capacity, const char *source)
{
	size_t copied = 0;

	for (; *source; source++) {
		if (*source == '-')
			continue;
		if (copied == capacity - 1) {
			destination[copied] = 0;
			return 1;
		}
		destination[copied++] = *source;
	}
	destination[copied] = 0;
	return 0;
}

static int
grow_result(morpheus_normalized_generation_result *result, size_t limit)
{
	size_t capacity = result->capacity ? result->capacity * 2 : 32;
	morpheus_normalized_generation *records;

	if (capacity < result->capacity || capacity > limit)
		capacity = limit;
	if (capacity <= result->capacity ||
	    capacity > SIZE_MAX / sizeof *result->records)
		return 0;
	records = realloc(result->records,capacity * sizeof *result->records);
	if (!records)
		return 0;
	result->records = records;
	result->capacity = capacity;
	return 1;
}

/*
 * The morphology flags of a form, as analysis reports them for the same form
 * (checkgenwds.c): the word's own flags with those of its preverb, stem and
 * ending. The generator leaves stem flags such as irreg_comp on the stem, so
 * reading only the word's flags lost them, and with them the degree of
 * irregular comparatives and superlatives.
 */
static void
effective_morphflags(const gk_word *form, MorphFlags *flags)
{
	const MorphFlags *sources[4];
	size_t source;
	size_t byte;

	sources[0] = morphflags_of(form);
	sources[1] = morphflags_of(prvb_gstr_of(form));
	sources[2] = morphflags_of(stem_gstr_of(form));
	sources[3] = morphflags_of(ends_gstr_of(form));
	memset(flags,0,MORPHFLAG_STORAGE_BYTES);
	for (source = 0; source != 4; source++)
		for (byte = 0; byte != MORPHFLAG_STORAGE_BYTES; byte++)
			flags[byte] |= sources[source][byte];
}

static int
collect_form(const gk_word *form, void *state)
{
	collector *collect = state;
	morpheus_normalized_generation *record;
	word_form info = forminfo_of(form);
	MorphFlags flags[MORPHFLAG_STORAGE_BYTES];

	if (collect->result->count == collect->limit) {
		collect->limit_exceeded = 1;
		return 0;
	}
	if (collect->result->count == collect->result->capacity &&
	    !grow_result(collect->result,collect->limit)) {
		collect->no_memory = 1;
		return 0;
	}
	record = collect->result->records + collect->result->count;
	memset(record,0,sizeof *record);
	record->source_order = (uint64_t)collect->result->count;
	if (copy_surface(record->surface,sizeof record->surface,workword_of(form)))
		record->truncated_fields |= MORPHEUS_TRUNCATED_WORKWORD;
	if (copy_text(record->lemma,sizeof record->lemma,lemma_of(form)))
		record->truncated_fields |= MORPHEUS_TRUNCATED_LEMMA;
	record->part_of_speech =
	    morpheus_public_part_of_speech((uint32_t)stemtype_of(form));
	record->dialect = morpheus_public_dialect(effective_dialect(form));
	record->geographic_region =
	    morpheus_public_region((uint32_t)geogregion_of(form));
	record->person = morpheus_public_person((uint32_t)person_of(info));
	record->number = morpheus_public_number((uint32_t)number_of(info));
	record->gender = morpheus_public_gender((uint32_t)gender_of(info));
	record->grammatical_case =
	    morpheus_public_case((uint32_t)case_of(info));
	record->tense = morpheus_public_tense((uint32_t)tense_of(info));
	record->mood = morpheus_public_mood((uint32_t)mood_of(info));
	record->voice = morpheus_public_voice((uint32_t)voice_of(info));
	effective_morphflags(form,flags);
	record->degree = morpheus_public_degree(
	    (uint32_t)degree_of(info),
	    (morpheus_part_of_speech)record->part_of_speech,flags);
	morpheus_public_morph_flags(record->morph_flags,flags);
	collect->result->count++;
	return 1;
}

static int
compare_u32(uint32_t left, uint32_t right)
{
	return left > right ? 1 : left < right ? -1 : 0;
}

static int
compare_u64(uint64_t left, uint64_t right)
{
	return left > right ? 1 : left < right ? -1 : 0;
}

#define COMPARE_FIELD(field) \
	do { \
		int order = compare_u32(left->field,right->field); \
		if (order) return order; \
	} while (0)

int
morpheus_normalized_generation_compare(
    const morpheus_normalized_generation *left,
    const morpheus_normalized_generation *right)
{
	int order;

	if (!left || !right)
		return left ? 1 : right ? -1 : 0;
	COMPARE_FIELD(part_of_speech);
	COMPARE_FIELD(tense);
	COMPARE_FIELD(voice);
	COMPARE_FIELD(mood);
	COMPARE_FIELD(degree);
	COMPARE_FIELD(number);
	COMPARE_FIELD(person);
	COMPARE_FIELD(grammatical_case);
	COMPARE_FIELD(gender);
	COMPARE_FIELD(dialect);
	COMPARE_FIELD(geographic_region);
	order = strcmp(left->surface,right->surface);
	if (order)
		return order;
	order = strcmp(left->lemma,right->lemma);
	if (order)
		return order;
	order = memcmp(left->morph_flags,right->morph_flags,
	               sizeof left->morph_flags);
	if (order)
		return order;
	return compare_u64(left->source_order,right->source_order);
}

#undef COMPARE_FIELD

static int
compare_records(const void *left, const void *right)
{
	return morpheus_normalized_generation_compare(left,right);
}

static morpheus_generation_normalize_status
service_status(morpheus_generation_status status)
{
	switch (status) {
	case MORPHEUS_GENERATION_OK:
		return MORPHEUS_GENERATION_NORMALIZE_OK;
	case MORPHEUS_GENERATION_NOT_FOUND:
		return MORPHEUS_GENERATION_NORMALIZE_NOT_FOUND;
	case MORPHEUS_GENERATION_NO_MEMORY:
		return MORPHEUS_GENERATION_NORMALIZE_NO_MEMORY;
	case MORPHEUS_GENERATION_INVALID:
		return MORPHEUS_GENERATION_NORMALIZE_INVALID;
	default:
		return MORPHEUS_GENERATION_NORMALIZE_ENGINE_ERROR;
	}
}

morpheus_generation_normalize_status
morpheus_generation_normalize(
    morpheus_generation_service *service, const char *canonical_lemma,
    size_t result_limit, morpheus_normalized_generation_result **result)
{
	morpheus_normalized_generation_result *created;
	morpheus_generation_status generated;
	collector collect;
	size_t generated_count = 0;

	if (!service || !canonical_lemma || !*canonical_lemma || !result ||
	    !result_limit || result_limit > MORPHEUS_GENERATION_RESULT_HARD_LIMIT)
		return MORPHEUS_GENERATION_NORMALIZE_INVALID;
	*result = NULL;
	created = calloc(1,sizeof *created);
	if (!created)
		return MORPHEUS_GENERATION_NORMALIZE_NO_MEMORY;
	collect = (collector){ created, result_limit, 0, 0 };
	generated = morpheus_generation_service_generate(
	    service,canonical_lemma,collect_form,&collect,&generated_count,
	    &created->skipped_records);
	if (collect.limit_exceeded) {
		morpheus_normalized_generation_result_free(created);
		return MORPHEUS_GENERATION_NORMALIZE_LIMIT;
	}
	if (collect.no_memory) {
		morpheus_normalized_generation_result_free(created);
		return MORPHEUS_GENERATION_NORMALIZE_NO_MEMORY;
	}
	if (generated != MORPHEUS_GENERATION_OK) {
		morpheus_generation_normalize_status status =
		    service_status(generated);
		morpheus_normalized_generation_result_free(created);
		return status;
	}
	if (generated_count != created->count) {
		morpheus_normalized_generation_result_free(created);
		return MORPHEUS_GENERATION_NORMALIZE_ENGINE_ERROR;
	}
	if (created->count > 1)
		qsort(created->records,created->count,sizeof *created->records,
		      compare_records);
	*result = created;
	return MORPHEUS_GENERATION_NORMALIZE_OK;
}

void
morpheus_normalized_generation_result_free(
    morpheus_normalized_generation_result *result)
{
	if (!result)
		return;
	free(result->records);
	free(result);
}

size_t
morpheus_normalized_generation_result_count(
    const morpheus_normalized_generation_result *result)
{
	return result ? result->count : 0;
}

size_t
morpheus_normalized_generation_result_skipped_records(
    const morpheus_normalized_generation_result *result)
{
	return result ? result->skipped_records : 0;
}

const morpheus_normalized_generation *
morpheus_normalized_generation_result_at(
    const morpheus_normalized_generation_result *result, size_t index)
{
	return result && index < result->count ? result->records + index : NULL;
}
