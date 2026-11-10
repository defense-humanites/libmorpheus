// SPDX-License-Identifier: AGPL-3.0-or-later

#include <stdlib.h>
#include <string.h>

#include "morpheus/morpheus.h"

struct morpheus_runtime_context {
  uint32_t language;
};

struct morpheus_result {
  size_t count;
  morpheus_analysis analyses[2];
  morpheus_truncated_fields truncated[2];
};

struct morpheus_generation_result {
  size_t count;
  size_t skipped;
  morpheus_generation generations[3];
  morpheus_truncated_fields truncated[3];
};

uint32_t morpheus_abi_version(void) { return MORPHEUS_ABI_VERSION; }

size_t morpheus_analysis_size(void) { return sizeof(morpheus_analysis); }

size_t morpheus_generation_size(void) { return sizeof(morpheus_generation); }

const char *morpheus_status_message(morpheus_status status) {
  switch (status) {
    case MORPHEUS_OK: return "success";
    case MORPHEUS_INVALID_ARGUMENT: return "invalid argument";
    case MORPHEUS_ABI_MISMATCH: return "ABI mismatch";
    case MORPHEUS_NO_MEMORY: return "out of memory";
    case MORPHEUS_INPUT_TOO_LONG: return "input too long";
    case MORPHEUS_OUT_OF_RANGE: return "out of range";
    case MORPHEUS_BUFFER_TOO_SMALL: return "buffer too small";
    case MORPHEUS_STEMLIB_ERROR: return "stemlib is unavailable or incomplete";
    default: return "fixture error";
  }
}

morpheus_status morpheus_open_path(
    uint32_t abi_version, const uint8_t *stemlib_path,
    size_t stemlib_path_length, uint32_t language, morpheus_context **context) {
  if (abi_version != MORPHEUS_ABI_VERSION) return MORPHEUS_ABI_MISMATCH;
  if (stemlib_path == NULL || stemlib_path_length == 0u || context == NULL)
    return MORPHEUS_INVALID_ARGUMENT;
  if (stemlib_path_length == strlen("missing-stemlib") &&
      memcmp(stemlib_path, "missing-stemlib", stemlib_path_length) == 0)
    return MORPHEUS_STEMLIB_ERROR;
  morpheus_context *created = calloc(1u, sizeof(*created));
  if (created == NULL) return MORPHEUS_NO_MEMORY;
  created->language = language;
  *context = created;
  return MORPHEUS_OK;
}

void morpheus_close(morpheus_context *context) { free(context); }

static void set_text(char *destination, size_t capacity, const char *text) {
  size_t length = strlen(text);
  if (length >= capacity) length = capacity - 1u;
  memcpy(destination, text, length);
  destination[length] = '\0';
}

static void set_flag(morpheus_analysis *analysis, uint32_t flag) {
  analysis->morph_flags[flag / 8u] |= (uint8_t)(1u << (flag % 8u));
}

static void set_generation_flag(morpheus_generation *generation,
                                uint32_t flag) {
  generation->morph_flags[flag / 8u] |= (uint8_t)(1u << (flag % 8u));
}

morpheus_status morpheus_analyze(
    morpheus_context *context, const uint8_t *beta_code, size_t length,
    morpheus_options options, morpheus_result **result) {
  if (context == NULL || beta_code == NULL || result == NULL)
    return MORPHEUS_INVALID_ARGUMENT;
  if (length == 5u && memcmp(beta_code, "error", 5u) == 0)
    return MORPHEUS_INPUT_TOO_LONG;
  morpheus_result *created = calloc(1u, sizeof(*created));
  if (created == NULL) return MORPHEUS_NO_MEMORY;
  if (length != 5u || memcmp(beta_code, "bi/ou", 5u) != 0) {
    *result = created;
    return MORPHEUS_OK;
  }
  if ((options & MORPHEUS_OPTION_STRICT_CASE) == 0u) {
    free(created);
    return MORPHEUS_INVALID_ARGUMENT;
  }

  created->count = 2u;
  morpheus_analysis *first = &created->analyses[0];
  first->struct_size = sizeof(*first);
  first->part_of_speech = MORPHEUS_PART_OF_SPEECH_NOUN;
  first->dialect = MORPHEUS_DIALECT_EPIC;
  first->person = MORPHEUS_PERSON_NONE;
  first->number = MORPHEUS_NUMBER_SINGULAR;
  first->gender = MORPHEUS_GENDER_MASCULINE;
  first->grammatical_case = MORPHEUS_CASE_NOMINATIVE;
  set_text(first->raw, sizeof(first->raw), "bi/ou:noun masc nom sg epic");
  set_text(first->workword, sizeof(first->workword), "bi/ou");
  set_text(first->lemma, sizeof(first->lemma), "bi/os");
  set_flag(first, MORPHEUS_MORPH_FLAG_LATE);

  morpheus_analysis *second = &created->analyses[1];
  second->struct_size = sizeof(*second);
  second->part_of_speech = MORPHEUS_PART_OF_SPEECH_NOUN;
  second->dialect = MORPHEUS_DIALECT_ATTIC | MORPHEUS_DIALECT_IONIC;
  second->geographic_region = MORPHEUS_REGION_ARGOLID | MORPHEUS_REGION_RHODES;
  second->number = MORPHEUS_NUMBER_DUAL;
  second->gender = MORPHEUS_GENDER_FEMININE | MORPHEUS_GENDER_MASCULINE;
  second->grammatical_case = MORPHEUS_CASE_NOMINATIVE |
                             MORPHEUS_CASE_ACCUSATIVE;
  set_text(second->raw, sizeof(second->raw), "bi/ou:noun dual");
  set_text(second->workword, sizeof(second->workword), "bi/ou");
  set_text(second->lemma, sizeof(second->lemma), "bi/a");
  set_flag(second, MORPHEUS_MORPH_FLAG_RARE);
  created->truncated[1] = MORPHEUS_TRUNCATED_LEMMA;

  *result = created;
  return MORPHEUS_OK;
}

size_t morpheus_result_count(const morpheus_result *result) {
  return result == NULL ? 0u : result->count;
}

morpheus_status morpheus_result_copy(
    const morpheus_result *result, size_t index, void *buffer,
    size_t buffer_size) {
  if (result == NULL || buffer == NULL) return MORPHEUS_INVALID_ARGUMENT;
  if (index >= result->count) return MORPHEUS_OUT_OF_RANGE;
  if (buffer_size < sizeof(morpheus_analysis))
    return MORPHEUS_BUFFER_TOO_SMALL;
  memcpy(buffer, &result->analyses[index], sizeof(morpheus_analysis));
  return MORPHEUS_OK;
}

morpheus_status morpheus_result_truncated_fields(
    const morpheus_result *result, size_t index,
    morpheus_truncated_fields *fields) {
  if (result == NULL || fields == NULL) return MORPHEUS_INVALID_ARGUMENT;
  if (index >= result->count) return MORPHEUS_OUT_OF_RANGE;
  *fields = result->truncated[index];
  return MORPHEUS_OK;
}

void morpheus_result_free(morpheus_result *result) { free(result); }

static int generation_matches(const morpheus_generation *generation,
                              const morpheus_generation_options *options) {
  if (options->flags & MORPHEUS_GENERATION_EXCLUDE_DUALS) {
    if (generation->number == MORPHEUS_NUMBER_DUAL) return 0;
  }
  if (options->part_of_speech != 0u &&
      generation->part_of_speech != options->part_of_speech) return 0;
  if (options->dialect != 0u &&
      (generation->dialect & options->dialect) == 0u) return 0;
  if (options->geographic_region != 0u &&
      (generation->geographic_region & options->geographic_region) == 0u)
    return 0;
  if (options->person != 0u && generation->person != options->person) return 0;
  if (options->number != 0u && generation->number != options->number) return 0;
  if (options->gender != 0u &&
      (generation->gender & options->gender) == 0u) return 0;
  if (options->grammatical_case != 0u &&
      (generation->grammatical_case & options->grammatical_case) == 0u)
    return 0;
  if (options->tense != 0u && generation->tense != options->tense) return 0;
  if (options->mood != 0u && generation->mood != options->mood) return 0;
  if (options->voice != 0u &&
      (generation->voice & options->voice) == 0u) return 0;
  if (options->degree != 0u && generation->degree != options->degree) return 0;
  return 1;
}

static void initialize_generations(morpheus_generation *generations) {
  morpheus_generation *first = &generations[0];
  first->struct_size = sizeof(*first);
  first->part_of_speech = MORPHEUS_PART_OF_SPEECH_NOUN;
  first->dialect = MORPHEUS_DIALECT_ATTIC;
  first->number = MORPHEUS_NUMBER_SINGULAR;
  first->gender = MORPHEUS_GENDER_MASCULINE;
  first->grammatical_case = MORPHEUS_CASE_NOMINATIVE;
  set_text(first->surface, sizeof(first->surface), "lo/gos");
  set_text(first->lemma, sizeof(first->lemma), "lo/gos");

  morpheus_generation *second = &generations[1];
  second->struct_size = sizeof(*second);
  second->part_of_speech = MORPHEUS_PART_OF_SPEECH_NOUN;
  second->dialect = MORPHEUS_DIALECT_ATTIC | MORPHEUS_DIALECT_IONIC;
  second->geographic_region = MORPHEUS_REGION_ARGOLID;
  second->number = MORPHEUS_NUMBER_DUAL;
  second->gender = MORPHEUS_GENDER_FEMININE | MORPHEUS_GENDER_MASCULINE;
  second->grammatical_case = MORPHEUS_CASE_NOMINATIVE |
                             MORPHEUS_CASE_ACCUSATIVE;
  set_text(second->surface, sizeof(second->surface), "lo/gw");
  set_text(second->lemma, sizeof(second->lemma), "lo/gos");
  set_generation_flag(second, MORPHEUS_MORPH_FLAG_RARE);

  morpheus_generation *third = &generations[2];
  *third = *second;
  third->dialect = MORPHEUS_DIALECT_IONIC;
  third->geographic_region = MORPHEUS_REGION_RHODES;
  third->grammatical_case = MORPHEUS_CASE_GENITIVE |
                            MORPHEUS_CASE_DATIVE;
}

morpheus_status morpheus_generate(
    morpheus_context *context, const uint8_t *lemma, size_t length,
    const morpheus_generation_options *options,
    morpheus_generation_result **result) {
  morpheus_generation_options defaults = {0};
  morpheus_generation candidates[3] = {0};
  size_t index;
  if (context == NULL || lemma == NULL || length == 0u || result == NULL)
    return MORPHEUS_INVALID_ARGUMENT;
  defaults.version = MORPHEUS_GENERATION_OPTIONS_VERSION;
  defaults.struct_size = sizeof(defaults);
  defaults.result_limit = MORPHEUS_GENERATION_DEFAULT_LIMIT;
  if (options == NULL) options = &defaults;
  if (options->version != MORPHEUS_GENERATION_OPTIONS_VERSION ||
      options->struct_size < sizeof(*options)) return MORPHEUS_ABI_MISMATCH;
  if (options->result_limit > MORPHEUS_GENERATION_MAX_LIMIT)
    return MORPHEUS_INVALID_ARGUMENT;

  morpheus_generation_result *created = calloc(1u, sizeof(*created));
  if (created == NULL) return MORPHEUS_NO_MEMORY;
  if (length == 7u && memcmp(lemma, "partial", 7u) == 0) {
    created->skipped = 2u;
    *result = created;
    return MORPHEUS_OK;
  }
  if (length != 6u || memcmp(lemma, "lo/gos", 6u) != 0) {
    *result = created;
    return MORPHEUS_OK;
  }

  initialize_generations(candidates);
  for (index = 0u; index != 3u; index++) {
    uint64_t limit = options->result_limit == 0u
                         ? MORPHEUS_GENERATION_DEFAULT_LIMIT
                         : options->result_limit;
    if (!generation_matches(&candidates[index], options)) continue;
    if (created->count == limit) {
      free(created);
      return MORPHEUS_RESULT_LIMIT_EXCEEDED;
    }
    created->generations[created->count] = candidates[index];
    if (index == 2u)
      created->truncated[created->count] = MORPHEUS_TRUNCATED_WORKWORD;
    created->count++;
  }
  *result = created;
  return MORPHEUS_OK;
}

size_t morpheus_generation_result_count(
    const morpheus_generation_result *result) {
  return result == NULL ? 0u : result->count;
}

morpheus_status morpheus_generation_result_copy(
    const morpheus_generation_result *result, size_t index, void *buffer,
    size_t buffer_size) {
  if (result == NULL || buffer == NULL) return MORPHEUS_INVALID_ARGUMENT;
  if (index >= result->count) return MORPHEUS_OUT_OF_RANGE;
  if (buffer_size < sizeof(morpheus_generation))
    return MORPHEUS_BUFFER_TOO_SMALL;
  memcpy(buffer, &result->generations[index], sizeof(morpheus_generation));
  return MORPHEUS_OK;
}

morpheus_status morpheus_generation_result_truncated_fields(
    const morpheus_generation_result *result, size_t index,
    morpheus_truncated_fields *fields) {
  if (result == NULL || fields == NULL) return MORPHEUS_INVALID_ARGUMENT;
  if (index >= result->count) return MORPHEUS_OUT_OF_RANGE;
  *fields = result->truncated[index];
  return MORPHEUS_OK;
}

size_t morpheus_generation_result_skipped_records(
    const morpheus_generation_result *result) {
  return result == NULL ? 0u : result->skipped;
}

void morpheus_generation_result_free(morpheus_generation_result *result) {
  free(result);
}
