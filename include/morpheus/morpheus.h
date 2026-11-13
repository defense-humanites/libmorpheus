// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Antoine Boquet

#ifndef MORPHEUS_MORPHEUS_H
#define MORPHEUS_MORPHEUS_H

#include <stddef.h>
#include <stdint.h>

#if defined(_WIN32) || defined(__CYGWIN__)
#  if defined(MORPHEUS_BUILDING_LIBRARY)
#    define MORPHEUS_API __declspec(dllexport)
#  else
#    define MORPHEUS_API __declspec(dllimport)
#  endif
#elif defined(__GNUC__) || defined(__clang__)
#  define MORPHEUS_API __attribute__((visibility("default")))
#else
#  define MORPHEUS_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @file morpheus.h
 * @brief Stable C ABI for Morpheus analysis and generation.
 *
 * Contexts and results are opaque. Analysis and generation calls return owned
 * results with dedicated free functions. Distinct contexts may be used
 * concurrently, but callers must serialize operations on any one context.
 */

/** ABI version implemented by this header. */
#define MORPHEUS_ABI_VERSION 2u

typedef struct morpheus_runtime_context morpheus_context;
typedef struct morpheus_result morpheus_result;
typedef struct morpheus_generation_result morpheus_generation_result;

/** Status returned by fallible public operations. */
typedef enum {
  MORPHEUS_OK=0,
  MORPHEUS_INVALID_ARGUMENT=1,
  MORPHEUS_ABI_MISMATCH=2,
  MORPHEUS_NO_MEMORY=3,
  MORPHEUS_INPUT_TOO_LONG=4,
  MORPHEUS_OUT_OF_RANGE=5,
  MORPHEUS_INTERNAL_ERROR=6,
  MORPHEUS_BUFFER_TOO_SMALL=7,
  MORPHEUS_STEMLIB_ERROR=8,
  MORPHEUS_RESULT_LIMIT_EXCEEDED=9
} morpheus_status;

/** Runtime language selected when a context is created. */
typedef enum {
  MORPHEUS_LANGUAGE_GREEK=0,
  MORPHEUS_LANGUAGE_LATIN=1,
  MORPHEUS_LANGUAGE_ITALIAN=2
} morpheus_language;

#define MORPHEUS_TEXT_CAPACITY 64u
#define MORPHEUS_DOMAIN_CAPACITY 24u
#define MORPHEUS_MORPH_FLAG_COUNT 84u
#define MORPHEUS_MORPH_FLAG_CAPACITY 11u

/** Zero-based, alphabetically ordered trait indices used by the public ABI. */
typedef uint32_t morpheus_morph_flag;
#define MORPHEUS_MORPH_FLAG_ACCENT_OPTIONAL 0u
#define MORPHEUS_MORPH_FLAG_ALPHA_COPULATIVE 1u
#define MORPHEUS_MORPH_FLAG_ALPHA_PRIVATIVE 2u
#define MORPHEUS_MORPH_FLAG_ANTEPENULT_ACCENT 3u
#define MORPHEUS_MORPH_FLAG_APOCOPE 4u
#define MORPHEUS_MORPH_FLAG_ATTIC_REDUPLICATION 5u
#define MORPHEUS_MORPH_FLAG_CAUSAL 6u
#define MORPHEUS_MORPH_FLAG_COMP_ONLY 7u
#define MORPHEUS_MORPH_FLAG_CONTRACTED 8u
#define MORPHEUS_MORPH_FLAG_DELTA_PREVERB 9u
#define MORPHEUS_MORPH_FLAG_DERIVATIVE 10u
#define MORPHEUS_MORPH_FLAG_DESIDERATIVE 11u
#define MORPHEUS_MORPH_FLAG_DIMINUTIVE 12u
#define MORPHEUS_MORPH_FLAG_DISSIMILATION 13u
#define MORPHEUS_MORPH_FLAG_DOUBLED_CONSONANT 14u
#define MORPHEUS_MORPH_FLAG_DOUBLE_AUGMENT 15u
#define MORPHEUS_MORPH_FLAG_DOUBLE_REDUPLICATION 16u
#define MORPHEUS_MORPH_FLAG_EARLY 17u
#define MORPHEUS_MORPH_FLAG_ELIDED_PREVERB 18u
#define MORPHEUS_MORPH_FLAG_ENCLITIC 19u
#define MORPHEUS_MORPH_FLAG_ENDS_IN_DIGAMMA 20u
#define MORPHEUS_MORPH_FLAG_EN_TO_ENI 21u
#define MORPHEUS_MORPH_FLAG_FREQUENTATIVE 22u
#define MORPHEUS_MORPH_FLAG_GEOGRAPHIC_NAME 23u
#define MORPHEUS_MORPH_FLAG_GROUP_NAME 24u
#define MORPHEUS_MORPH_FLAG_HAS_AUGMENT 25u
#define MORPHEUS_MORPH_FLAG_HAS_PREVERB 26u
#define MORPHEUS_MORPH_FLAG_IMPERSONAL 27u
#define MORPHEUS_MORPH_FLAG_INDECLINABLE_FORM 28u
#define MORPHEUS_MORPH_FLAG_INTERVOCALIC_S_TO_H 29u
#define MORPHEUS_MORPH_FLAG_INTRANSITIVE 30u
#define MORPHEUS_MORPH_FLAG_IOTA_INTENSIVE 31u
#define MORPHEUS_MORPH_FLAG_IRREGULAR_COMPARATIVE 32u
#define MORPHEUS_MORPH_FLAG_IRREGULAR_FORM 33u
#define MORPHEUS_MORPH_FLAG_IRREGULAR_SUPERLATIVE 34u
#define MORPHEUS_MORPH_FLAG_ITERATIVE 35u
#define MORPHEUS_MORPH_FLAG_LATE 36u
#define MORPHEUS_MORPH_FLAG_LATER 37u
#define MORPHEUS_MORPH_FLAG_LONG_PENULT 38u
#define MORPHEUS_MORPH_FLAG_LOST_ACCENT 39u
#define MORPHEUS_MORPH_FLAG_METATHESIS 40u
#define MORPHEUS_MORPH_FLAG_META_TO_PEDA 41u
#define MORPHEUS_MORPH_FLAG_METRICALLY_LONG 42u
#define MORPHEUS_MORPH_FLAG_NEEDS_ACCENT 43u
#define MORPHEUS_MORPH_FLAG_NEEDS_ROUGH_BREATHING 44u
#define MORPHEUS_MORPH_FLAG_NOT_IN_COMPOSITION 45u
#define MORPHEUS_MORPH_FLAG_NO_CIRCUMFLEX 46u
#define MORPHEUS_MORPH_FLAG_NO_COMPARISON 47u
#define MORPHEUS_MORPH_FLAG_NO_REDUPLICATION 48u
#define MORPHEUS_MORPH_FLAG_NU_MOVABLE 49u
#define MORPHEUS_MORPH_FLAG_N_INFIX 50u
#define MORPHEUS_MORPH_FLAG_PARA_TO_PARAI 51u
#define MORPHEUS_MORPH_FLAG_PERSON_NAME 52u
#define MORPHEUS_MORPH_FLAG_POETIC 53u
#define MORPHEUS_MORPH_FLAG_PRESENT_REDUPLICATION 54u
#define MORPHEUS_MORPH_FLAG_PREVERB_AUGMENT 55u
#define MORPHEUS_MORPH_FLAG_PROCLITIC 56u
#define MORPHEUS_MORPH_FLAG_PRODELISION 57u
#define MORPHEUS_MORPH_FLAG_PROS_TO_POTI 58u
#define MORPHEUS_MORPH_FLAG_PROS_TO_PROTI 59u
#define MORPHEUS_MORPH_FLAG_QUANTITY_METATHESIS 60u
#define MORPHEUS_MORPH_FLAG_RARE 61u
#define MORPHEUS_MORPH_FLAG_RAW_PREVERB 62u
#define MORPHEUS_MORPH_FLAG_RAW_SONANT 63u
#define MORPHEUS_MORPH_FLAG_RECESSIVE_ACCENT 64u
#define MORPHEUS_MORPH_FLAG_REDUPLICATION 65u
#define MORPHEUS_MORPH_FLAG_RHO_ETA_IOTA_ALPHA 66u
#define MORPHEUS_MORPH_FLAG_ROOT_PREVERB 67u
#define MORPHEUS_MORPH_FLAG_SHORT_EIS 68u
#define MORPHEUS_MORPH_FLAG_SHORT_PENULT 69u
#define MORPHEUS_MORPH_FLAG_SHORT_SUBJUNCTIVE 70u
#define MORPHEUS_MORPH_FLAG_SIGMA_TO_CI 71u
#define MORPHEUS_MORPH_FLAG_STEM_ACCENT 72u
#define MORPHEUS_MORPH_FLAG_SUFFIX_ACCENT 73u
#define MORPHEUS_MORPH_FLAG_SYLL_AUGMENT 74u
#define MORPHEUS_MORPH_FLAG_SYNCOPE 75u
#define MORPHEUS_MORPH_FLAG_TAU_PREVERB 76u
#define MORPHEUS_MORPH_FLAG_TMESIS 77u
#define MORPHEUS_MORPH_FLAG_UNASPIRATED_PREVERB 78u
#define MORPHEUS_MORPH_FLAG_UNAUGMENTED 79u
#define MORPHEUS_MORPH_FLAG_UNCONTRACTED_ENDING 80u
#define MORPHEUS_MORPH_FLAG_UNCONTRACTED_STEM 81u
#define MORPHEUS_MORPH_FLAG_UPER_TO_UPEIR 82u
#define MORPHEUS_MORPH_FLAG_UPO_TO_UPAI 83u

/** Lexical part-of-speech classification exposed by ABI version 2. */
typedef enum {
  MORPHEUS_PART_OF_SPEECH_UNKNOWN=0,
  MORPHEUS_PART_OF_SPEECH_NOUN=1,
  MORPHEUS_PART_OF_SPEECH_VERB=2,
  MORPHEUS_PART_OF_SPEECH_ADJECTIVE=3,
  MORPHEUS_PART_OF_SPEECH_ADVERB=4,
  MORPHEUS_PART_OF_SPEECH_ARTICLE=5,
  MORPHEUS_PART_OF_SPEECH_PRONOUN=6,
  MORPHEUS_PART_OF_SPEECH_NUMERAL=7,
  MORPHEUS_PART_OF_SPEECH_PREPOSITION=8,
  MORPHEUS_PART_OF_SPEECH_CONJUNCTION=9,
  MORPHEUS_PART_OF_SPEECH_PARTICLE=10,
  MORPHEUS_PART_OF_SPEECH_INTERJECTION=11
} morpheus_part_of_speech;

/* Normalized morphology codes. Only documented mask types may be combined. */
typedef uint32_t morpheus_person;
#define MORPHEUS_PERSON_NONE UINT32_C(0)
#define MORPHEUS_PERSON_FIRST UINT32_C(1)
#define MORPHEUS_PERSON_SECOND UINT32_C(2)
#define MORPHEUS_PERSON_THIRD UINT32_C(3)

typedef uint32_t morpheus_number;
#define MORPHEUS_NUMBER_NONE UINT32_C(0)
#define MORPHEUS_NUMBER_SINGULAR UINT32_C(1)
#define MORPHEUS_NUMBER_DUAL UINT32_C(2)
#define MORPHEUS_NUMBER_PLURAL UINT32_C(3)

typedef uint32_t morpheus_gender;
#define MORPHEUS_GENDER_NONE UINT32_C(0)
#define MORPHEUS_GENDER_ADVERBIAL UINT32_C(1)
#define MORPHEUS_GENDER_FEMININE UINT32_C(2)
#define MORPHEUS_GENDER_MASCULINE UINT32_C(4)
#define MORPHEUS_GENDER_NEUTER UINT32_C(8)

typedef uint32_t morpheus_case;
#define MORPHEUS_CASE_NONE UINT32_C(0)
#define MORPHEUS_CASE_ABLATIVE UINT32_C(1)
#define MORPHEUS_CASE_ACCUSATIVE UINT32_C(2)
#define MORPHEUS_CASE_DATIVE UINT32_C(4)
#define MORPHEUS_CASE_GENITIVE UINT32_C(8)
#define MORPHEUS_CASE_NOMINATIVE UINT32_C(16)
#define MORPHEUS_CASE_VOCATIVE UINT32_C(32)

typedef uint32_t morpheus_tense;
#define MORPHEUS_TENSE_NONE UINT32_C(0)
#define MORPHEUS_TENSE_PRESENT UINT32_C(1)
#define MORPHEUS_TENSE_IMPERFECT UINT32_C(2)
#define MORPHEUS_TENSE_FUTURE UINT32_C(3)
#define MORPHEUS_TENSE_AORIST UINT32_C(4)
#define MORPHEUS_TENSE_PERFECT UINT32_C(5)
#define MORPHEUS_TENSE_PLUPERFECT UINT32_C(6)
#define MORPHEUS_TENSE_FUTURE_PERFECT UINT32_C(7)
#define MORPHEUS_TENSE_PAST_ABSOLUTE UINT32_C(8)

typedef uint32_t morpheus_mood;
#define MORPHEUS_MOOD_NONE UINT32_C(0)
#define MORPHEUS_MOOD_CONDITIONAL UINT32_C(1)
#define MORPHEUS_MOOD_GERUNDIVE UINT32_C(2)
#define MORPHEUS_MOOD_IMPERATIVE UINT32_C(3)
#define MORPHEUS_MOOD_INDICATIVE UINT32_C(4)
#define MORPHEUS_MOOD_INFINITIVE UINT32_C(5)
#define MORPHEUS_MOOD_OPTATIVE UINT32_C(6)
#define MORPHEUS_MOOD_PARTICIPLE UINT32_C(7)
#define MORPHEUS_MOOD_SUBJUNCTIVE UINT32_C(8)
#define MORPHEUS_MOOD_SUPINE UINT32_C(9)

typedef uint32_t morpheus_voice;
#define MORPHEUS_VOICE_NONE UINT32_C(0)
#define MORPHEUS_VOICE_ACTIVE UINT32_C(1)
#define MORPHEUS_VOICE_PASSIVE UINT32_C(2)
#define MORPHEUS_VOICE_MIDDLE UINT32_C(4)
#define MORPHEUS_VOICE_MEDIO_PASSIVE \
  (MORPHEUS_VOICE_MIDDLE|MORPHEUS_VOICE_PASSIVE)
#define MORPHEUS_VOICE_DEPONENT \
  (MORPHEUS_VOICE_MIDDLE|MORPHEUS_VOICE_ACTIVE)

typedef uint32_t morpheus_degree;
#define MORPHEUS_DEGREE_NONE UINT32_C(0)
#define MORPHEUS_DEGREE_POSITIVE UINT32_C(1)
#define MORPHEUS_DEGREE_COMPARATIVE UINT32_C(2)
#define MORPHEUS_DEGREE_SUPERLATIVE UINT32_C(3)

typedef uint32_t morpheus_dialect;
#define MORPHEUS_DIALECT_ALL UINT32_C(0)
#define MORPHEUS_DIALECT_AEOLIC (UINT32_C(1) << 0)
#define MORPHEUS_DIALECT_ATTIC (UINT32_C(1) << 1)
#define MORPHEUS_DIALECT_DORIC (UINT32_C(1) << 2)
#define MORPHEUS_DIALECT_HOMERIC (UINT32_C(1) << 3)
#define MORPHEUS_DIALECT_IONIC (UINT32_C(1) << 4)
#define MORPHEUS_DIALECT_LESBIAN (UINT32_C(1) << 5)
#define MORPHEUS_DIALECT_NON_HOMERIC_EPIC (UINT32_C(1) << 6)
#define MORPHEUS_DIALECT_PARADIGM (UINT32_C(1) << 7)
#define MORPHEUS_DIALECT_PROSE (UINT32_C(1) << 8)
#define MORPHEUS_DIALECT_EPIC \
  (MORPHEUS_DIALECT_NON_HOMERIC_EPIC|MORPHEUS_DIALECT_HOMERIC)

typedef uint32_t morpheus_geographic_region;
#define MORPHEUS_REGION_NONE UINT32_C(0)
#define MORPHEUS_REGION_ARCADIA (UINT32_C(1) << 0)
#define MORPHEUS_REGION_ARGOLID (UINT32_C(1) << 1)
#define MORPHEUS_REGION_BOEOTIA (UINT32_C(1) << 2)
#define MORPHEUS_REGION_COS (UINT32_C(1) << 3)
#define MORPHEUS_REGION_CRETE (UINT32_C(1) << 4)
#define MORPHEUS_REGION_CYPRUS (UINT32_C(1) << 5)
#define MORPHEUS_REGION_CYRENE (UINT32_C(1) << 6)
#define MORPHEUS_REGION_ELIS (UINT32_C(1) << 7)
#define MORPHEUS_REGION_HERACLEA (UINT32_C(1) << 8)
#define MORPHEUS_REGION_LACONIA (UINT32_C(1) << 9)
#define MORPHEUS_REGION_LOCRIS (UINT32_C(1) << 10)
#define MORPHEUS_REGION_MEGARID (UINT32_C(1) << 11)
#define MORPHEUS_REGION_PHOCIS (UINT32_C(1) << 12)
#define MORPHEUS_REGION_RHODES (UINT32_C(1) << 13)
#define MORPHEUS_REGION_THERA (UINT32_C(1) << 14)

/**
 * One structured analysis.
 *
 * Numeric morphology fields use only the normalized public constants above.
 * Text fields are NUL-terminated,
 * fixed-capacity Beta Code strings. Use morpheus_result_truncated_fields() to
 * detect any value that exceeded its destination. The struct_size member
 * reports the size written by the producing library.
 */
typedef struct {
  uint32_t struct_size;
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
  char raw[MORPHEUS_TEXT_CAPACITY];
  char workword[MORPHEUS_TEXT_CAPACITY];
  char lemma[MORPHEUS_TEXT_CAPACITY];
  char preverb[MORPHEUS_TEXT_CAPACITY];
  char augment[MORPHEUS_TEXT_CAPACITY];
  char stem[MORPHEUS_TEXT_CAPACITY];
  char suffix[MORPHEUS_TEXT_CAPACITY];
  char ending[MORPHEUS_TEXT_CAPACITY];
  char crasis[MORPHEUS_TEXT_CAPACITY];
  char dictionary_form[MORPHEUS_TEXT_CAPACITY];
  char english_form[MORPHEUS_TEXT_CAPACITY];
  char raw_preverb[MORPHEUS_TEXT_CAPACITY];
  char domains[MORPHEUS_DOMAIN_CAPACITY];
  uint8_t morph_flags[MORPHEUS_MORPH_FLAG_CAPACITY];
} morpheus_analysis;

/** One normalized generated form and morphological interpretation. */
typedef struct {
  uint32_t struct_size;
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
  char surface[MORPHEUS_TEXT_CAPACITY];
  char lemma[MORPHEUS_TEXT_CAPACITY];
  uint8_t morph_flags[MORPHEUS_MORPH_FLAG_CAPACITY];
} morpheus_generation;

/** Bit mask returned by morpheus_result_truncated_fields(). */
typedef uint32_t morpheus_truncated_fields;
#define MORPHEUS_TRUNCATED_RAW (UINT32_C(1) << 0)
#define MORPHEUS_TRUNCATED_WORKWORD (UINT32_C(1) << 1)
#define MORPHEUS_TRUNCATED_LEMMA (UINT32_C(1) << 2)
#define MORPHEUS_TRUNCATED_PREVERB (UINT32_C(1) << 3)
#define MORPHEUS_TRUNCATED_AUGMENT (UINT32_C(1) << 4)
#define MORPHEUS_TRUNCATED_STEM (UINT32_C(1) << 5)
#define MORPHEUS_TRUNCATED_SUFFIX (UINT32_C(1) << 6)
#define MORPHEUS_TRUNCATED_ENDING (UINT32_C(1) << 7)
#define MORPHEUS_TRUNCATED_CRASIS (UINT32_C(1) << 8)
#define MORPHEUS_TRUNCATED_DICTIONARY_FORM (UINT32_C(1) << 9)
#define MORPHEUS_TRUNCATED_ENGLISH_FORM (UINT32_C(1) << 10)
#define MORPHEUS_TRUNCATED_RAW_PREVERB (UINT32_C(1) << 11)
#define MORPHEUS_TRUNCATED_DOMAINS (UINT32_C(1) << 12)

/** Per-request structured-analysis options. */
typedef uint64_t morpheus_options;

#define MORPHEUS_OPTION_STRICT_CASE (UINT64_C(1) << 0)
#define MORPHEUS_OPTION_IGNORE_ACCENTS (UINT64_C(1) << 1)
#define MORPHEUS_OPTION_VERBS_ONLY (UINT64_C(1) << 2)
#define MORPHEUS_OPTION_NO_CRASIS (UINT64_C(1) << 3)
#define MORPHEUS_OPTION_QUICK (UINT64_C(1) << 4)
#define MORPHEUS_OPTION_HQ_DICTIONARY (UINT64_C(1) << 5)

/** Shift applied to public dialect bits embedded in morpheus_options. */
#define MORPHEUS_OPTION_DIALECT_SHIFT 16u
#define MORPHEUS_DIALECT_KNOWN_MASK \
  (MORPHEUS_DIALECT_ATTIC|MORPHEUS_DIALECT_IONIC| \
   MORPHEUS_DIALECT_AEOLIC|MORPHEUS_DIALECT_LESBIAN| \
   MORPHEUS_DIALECT_HOMERIC|MORPHEUS_DIALECT_DORIC| \
   MORPHEUS_DIALECT_PARADIGM|MORPHEUS_DIALECT_NON_HOMERIC_EPIC| \
   MORPHEUS_DIALECT_PROSE)
#define MORPHEUS_OPTION_DIALECT_MASK \
  ((morpheus_options)MORPHEUS_DIALECT_KNOWN_MASK << \
   MORPHEUS_OPTION_DIALECT_SHIFT)
#define MORPHEUS_OPTION_DIALECT_ATTIC \
  ((morpheus_options)MORPHEUS_DIALECT_ATTIC << MORPHEUS_OPTION_DIALECT_SHIFT)
#define MORPHEUS_OPTION_DIALECT_IONIC \
  ((morpheus_options)MORPHEUS_DIALECT_IONIC << MORPHEUS_OPTION_DIALECT_SHIFT)
#define MORPHEUS_OPTION_DIALECT_AEOLIC \
  ((morpheus_options)MORPHEUS_DIALECT_AEOLIC << MORPHEUS_OPTION_DIALECT_SHIFT)
#define MORPHEUS_OPTION_DIALECT_LESBIAN \
  ((morpheus_options)MORPHEUS_DIALECT_LESBIAN << MORPHEUS_OPTION_DIALECT_SHIFT)
#define MORPHEUS_OPTION_DIALECT_HOMERIC \
  ((morpheus_options)MORPHEUS_DIALECT_HOMERIC << MORPHEUS_OPTION_DIALECT_SHIFT)
#define MORPHEUS_OPTION_DIALECT_DORIC \
  ((morpheus_options)MORPHEUS_DIALECT_DORIC << MORPHEUS_OPTION_DIALECT_SHIFT)
#define MORPHEUS_OPTION_DIALECT_PARADIGM \
  ((morpheus_options)MORPHEUS_DIALECT_PARADIGM << MORPHEUS_OPTION_DIALECT_SHIFT)
#define MORPHEUS_OPTION_DIALECT_NON_HOMERIC_EPIC \
  ((morpheus_options)MORPHEUS_DIALECT_NON_HOMERIC_EPIC << \
   MORPHEUS_OPTION_DIALECT_SHIFT)
#define MORPHEUS_OPTION_DIALECT_EPIC \
  (MORPHEUS_OPTION_DIALECT_HOMERIC| \
   MORPHEUS_OPTION_DIALECT_NON_HOMERIC_EPIC)
#define MORPHEUS_OPTION_DIALECT_PROSE \
  ((morpheus_options)MORPHEUS_DIALECT_PROSE << MORPHEUS_OPTION_DIALECT_SHIFT)

/** Context creation parameters. */
typedef struct {
  uint32_t abi_version;
  uint32_t struct_size;
  const char *stemlib_path;
  uint32_t language;
} morpheus_config;

/** Current version of morpheus_generation_options. */
#define MORPHEUS_GENERATION_OPTIONS_VERSION 1u
/** The default result_limit; 4096 before 0.6.0, below many compound verbs. */
#define MORPHEUS_GENERATION_DEFAULT_LIMIT UINT64_C(65536)
#define MORPHEUS_GENERATION_MAX_LIMIT UINT64_C(65536)

typedef uint32_t morpheus_generation_flags;
#define MORPHEUS_GENERATION_EXCLUDE_DUALS (UINT32_C(1) << 0)
/**
 * Leave out the preverb variants of a compound verb (apocope, the augment
 * before the preverb, psilosis...), keeping its plain forms. Since 0.6.0;
 * earlier versions reject the flag.
 */
#define MORPHEUS_GENERATION_EXCLUDE_PREVERB_VARIANTS (UINT32_C(1) << 1)

/** Per-request filters for morpheus_generate(). Zero traits match all. */
typedef struct {
  uint32_t version;
  uint32_t struct_size;
  uint64_t result_limit;
  morpheus_generation_flags flags;
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
} morpheus_generation_options;

/** Return the ABI version implemented by the loaded library. */
MORPHEUS_API uint32_t morpheus_abi_version(void);

/** Return the native size of morpheus_analysis for FFI callers. */
MORPHEUS_API size_t morpheus_analysis_size(void);

/** Return the native size of morpheus_generation for FFI callers. */
MORPHEUS_API size_t morpheus_generation_size(void);

/** Return a static, NUL-terminated description of @p status. */
MORPHEUS_API const char *morpheus_status_message(morpheus_status status);

/**
 * Create a context from an explicit-length path.
 *
 * This entry point avoids embedding a native pointer in a configuration
 * structure and is therefore preferred by FFI bindings. The path must not
 * contain an embedded NUL. Required files for the selected language are
 * checked before the context is created. On success, the caller owns *context.
 */
MORPHEUS_API morpheus_status morpheus_open_path(
    uint32_t abi_version, const uint8_t *stemlib_path,
    size_t stemlib_path_length, uint32_t language,
    morpheus_context **context);

/**
 * Create a context from a native C configuration.
 *
 * config->abi_version must equal MORPHEUS_ABI_VERSION and
 * config->struct_size must cover the complete version-2 structure.
 * Required files for the selected language are checked before the context is
 * created. On success, the caller owns *context.
 */
MORPHEUS_API morpheus_status morpheus_open(
    const morpheus_config *config, morpheus_context **context);

/** Destroy a context. Passing NULL is allowed. */
MORPHEUS_API void morpheus_close(morpheus_context *context);

/**
 * Analyze one Beta Code form.
 *
 * Input need not be NUL-terminated and must not contain an embedded NUL.
 * The result preserves the analyzer's order and duplicates. On success, the
 * caller owns *result, including when it contains zero analyses.
 */
MORPHEUS_API morpheus_status morpheus_analyze(
    morpheus_context *context, const uint8_t *beta_code, size_t length,
    morpheus_options options, morpheus_result **result);

/**
 * Generate Greek Beta Code forms for one lemma.
 *
 * @warning This generation surface is experimental pending sufficient
 * real-world validation in addition to its automated test coverage.
 *
 * Input need not be NUL-terminated and must not contain an embedded NUL.
 * options may be NULL for defaults. The generation index is loaded lazily
 * from <stemlib_path>/gener.index. On success, the caller owns *result,
 * including when the lemma is absent and the result contains zero records.
 * A source record that the engine cannot generate (for example, one whose
 * stem class has no ending table) is skipped rather than failing the request;
 * morpheus_generation_result_skipped_records() reports how many were.
 */
MORPHEUS_API morpheus_status morpheus_generate(
    morpheus_context *context, const uint8_t *lemma, size_t length,
    const morpheus_generation_options *options,
    morpheus_generation_result **result);

/** Return the number of analyses in a result, or zero for NULL. */
MORPHEUS_API size_t morpheus_result_count(const morpheus_result *result);

/**
 * Copy one analysis into caller-owned storage.
 *
 * buffer_size must be at least morpheus_analysis_size(). This is the preferred
 * accessor for FFI callers because it does not expose an internal pointer.
 */
MORPHEUS_API morpheus_status morpheus_result_copy(
    const morpheus_result *result, size_t index, void *buffer,
    size_t buffer_size);

/** Copy one analysis into a native morpheus_analysis structure. */
MORPHEUS_API morpheus_status morpheus_result_get(
    const morpheus_result *result, size_t index,
    morpheus_analysis *analysis);

/**
 * Report which fixed-capacity text fields were truncated while copying one
 * analysis. Zero means every field was copied in full.
 */
MORPHEUS_API morpheus_status morpheus_result_truncated_fields(
    const morpheus_result *result, size_t index,
    morpheus_truncated_fields *fields);

/** Destroy an owned result. Passing NULL is allowed. */
MORPHEUS_API void morpheus_result_free(morpheus_result *result);

/** Return the number of generated interpretations, or zero for NULL. */
MORPHEUS_API size_t morpheus_generation_result_count(
    const morpheus_generation_result *result);

/**
 * Return the number of the lemma's source records that could not be
 * generated and were skipped, or zero for NULL. It counts records, not forms,
 * and does not depend on the request's filters. A nonzero count with zero
 * generated records distinguishes a lemma whose records all failed from an
 * absent lemma.
 */
MORPHEUS_API size_t morpheus_generation_result_skipped_records(
    const morpheus_generation_result *result);

/** Copy one generated interpretation into caller-owned storage. */
MORPHEUS_API morpheus_status morpheus_generation_result_copy(
    const morpheus_generation_result *result, size_t index, void *buffer,
    size_t buffer_size);

/** Copy one generated interpretation into a native structure. */
MORPHEUS_API morpheus_status morpheus_generation_result_get(
    const morpheus_generation_result *result, size_t index,
    morpheus_generation *generation);

/** Report truncated generated text fields for one interpretation. */
MORPHEUS_API morpheus_status morpheus_generation_result_truncated_fields(
    const morpheus_generation_result *result, size_t index,
    morpheus_truncated_fields *fields);

/** Destroy an owned generation result. Passing NULL is allowed. */
MORPHEUS_API void morpheus_generation_result_free(
    morpheus_generation_result *result);

#ifdef __cplusplus
}
#endif

#endif
