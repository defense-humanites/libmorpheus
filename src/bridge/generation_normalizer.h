/* SPDX-License-Identifier: MPL-2.0 */

#ifndef MORPHEUS_GENERATION_NORMALIZER_H
#define MORPHEUS_GENERATION_NORMALIZER_H

#include <stddef.h>
#include <stdint.h>

#include <morpheus/morpheus.h>

#include "../gener/generation_service.h"

#define MORPHEUS_GENERATION_RESULT_HARD_LIMIT ((size_t)65536)

typedef enum {
	MORPHEUS_GENERATION_NORMALIZE_OK = 0,
	MORPHEUS_GENERATION_NORMALIZE_INVALID = 1,
	MORPHEUS_GENERATION_NORMALIZE_NOT_FOUND = 2,
	MORPHEUS_GENERATION_NORMALIZE_NO_MEMORY = 3,
	MORPHEUS_GENERATION_NORMALIZE_ENGINE_ERROR = 4,
	MORPHEUS_GENERATION_NORMALIZE_LIMIT = 5
} morpheus_generation_normalize_status;

typedef struct {
	char surface[MORPHEUS_TEXT_CAPACITY];
	char lemma[MORPHEUS_TEXT_CAPACITY];
	uint32_t part_of_speech;
	morpheus_dialect dialect;
	morpheus_geographic_region geographic_region;
	morpheus_person person;
	morpheus_number number;
	morpheus_gender gender;
	morpheus_case grammatical_case;
	morpheus_tense tense;
	morpheus_mood mood;
	morpheus_voice voice;
	morpheus_degree degree;
	uint8_t morph_flags[MORPHEUS_MORPH_FLAG_CAPACITY];
	morpheus_truncated_fields truncated_fields;
	uint64_t source_order;
} morpheus_normalized_generation;

typedef struct morpheus_normalized_generation_result
    morpheus_normalized_generation_result;

morpheus_generation_normalize_status morpheus_generation_normalize(
    morpheus_generation_service *service, const char *canonical_lemma,
    size_t result_limit, morpheus_normalized_generation_result **result);
void morpheus_normalized_generation_result_free(
    morpheus_normalized_generation_result *result);
size_t morpheus_normalized_generation_result_count(
    const morpheus_normalized_generation_result *result);
/* Source records the engine could not generate and skipped. */
size_t morpheus_normalized_generation_result_skipped_records(
    const morpheus_normalized_generation_result *result);
const morpheus_normalized_generation *morpheus_normalized_generation_result_at(
    const morpheus_normalized_generation_result *result, size_t index);

/* Defines the total deterministic order used by normalized results. */
int morpheus_normalized_generation_compare(
    const morpheus_normalized_generation *left,
    const morpheus_normalized_generation *right);

#endif
