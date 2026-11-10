// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Antoine Boquet

#include "api_internal.h"

#include <stdlib.h>
#include <string.h>

#include <greek.h>

#include "gener_index.h"
#include "../bridge/generation_normalizer.h"
#include "../gener/generation_service.h"
#include "../morphlib/runtime_context_internal.h"

#define MORPHEUS_REGION_KNOWN_MASK                                      \
  (MORPHEUS_REGION_ARCADIA|MORPHEUS_REGION_ARGOLID|                    \
   MORPHEUS_REGION_BOEOTIA|MORPHEUS_REGION_COS|MORPHEUS_REGION_CRETE|  \
   MORPHEUS_REGION_CYPRUS|MORPHEUS_REGION_CYRENE|MORPHEUS_REGION_ELIS| \
   MORPHEUS_REGION_HERACLEA|MORPHEUS_REGION_LACONIA|                   \
   MORPHEUS_REGION_LOCRIS|MORPHEUS_REGION_MEGARID|                     \
   MORPHEUS_REGION_PHOCIS|MORPHEUS_REGION_RHODES|MORPHEUS_REGION_THERA)

static void generation_context_cleanup(morpheus_context *context);

static morpheus_generation_result *generation_result_create(size_t count)
{
  morpheus_generation_result *result=calloc(1,sizeof *result);
  if(!result) return(NULL);
  if(count) {
    result->generations=calloc(count,sizeof *result->generations);
    result->truncated_fields=calloc(count,sizeof *result->truncated_fields);
    if(!result->generations || !result->truncated_fields) {
      free(result->truncated_fields);
      free(result->generations);
      free(result);
      return(NULL);
    }
  }
  result->count=count;
  return(result);
}

static int enum_at_most(uint32_t value, uint32_t maximum)
{
  return(value <= maximum);
}

static morpheus_status validate_options(
    const morpheus_generation_options *options, size_t *limit)
{
  uint64_t requested=MORPHEUS_GENERATION_DEFAULT_LIMIT;
  if(!options) {
    *limit=(size_t)requested;
    return(MORPHEUS_OK);
  }
  if(options->version != MORPHEUS_GENERATION_OPTIONS_VERSION ||
     options->struct_size < sizeof *options)
    return(MORPHEUS_ABI_MISMATCH);
  if(options->flags & ~MORPHEUS_GENERATION_EXCLUDE_DUALS)
    return(MORPHEUS_INVALID_ARGUMENT);
  if(options->part_of_speech > MORPHEUS_PART_OF_SPEECH_INTERJECTION ||
     !enum_at_most(options->person,MORPHEUS_PERSON_THIRD) ||
     !enum_at_most(options->number,MORPHEUS_NUMBER_PLURAL) ||
     !enum_at_most(options->tense,MORPHEUS_TENSE_PAST_ABSOLUTE) ||
     !enum_at_most(options->mood,MORPHEUS_MOOD_SUPINE) ||
     !enum_at_most(options->degree,MORPHEUS_DEGREE_SUPERLATIVE) ||
     (options->gender & ~(MORPHEUS_GENDER_ADVERBIAL|
                          MORPHEUS_GENDER_FEMININE|
                          MORPHEUS_GENDER_MASCULINE|
                          MORPHEUS_GENDER_NEUTER)) ||
     (options->grammatical_case & ~(MORPHEUS_CASE_ABLATIVE|
                                    MORPHEUS_CASE_ACCUSATIVE|
                                    MORPHEUS_CASE_DATIVE|
                                    MORPHEUS_CASE_GENITIVE|
                                    MORPHEUS_CASE_NOMINATIVE|
                                    MORPHEUS_CASE_VOCATIVE)) ||
     (options->voice & ~(MORPHEUS_VOICE_ACTIVE|MORPHEUS_VOICE_PASSIVE|
                         MORPHEUS_VOICE_MIDDLE)) ||
     (options->dialect & ~MORPHEUS_DIALECT_KNOWN_MASK) ||
     (options->geographic_region & ~MORPHEUS_REGION_KNOWN_MASK) ||
     ((options->flags & MORPHEUS_GENERATION_EXCLUDE_DUALS) &&
      options->number == MORPHEUS_NUMBER_DUAL))
    return(MORPHEUS_INVALID_ARGUMENT);
  if(options->result_limit) requested=options->result_limit;
  if(requested > MORPHEUS_GENERATION_MAX_LIMIT)
    return(MORPHEUS_INVALID_ARGUMENT);
  *limit=(size_t)requested;
  return(MORPHEUS_OK);
}

static int mask_matches(uint32_t filter, uint32_t value)
{
  return(!filter || (filter & value));
}

static int generation_matches(
    const morpheus_normalized_generation *generation,
    const morpheus_generation_options *options)
{
  if(!options) return(1);
  if(options->part_of_speech &&
     options->part_of_speech != generation->part_of_speech) return(0);
  if(options->person && options->person != generation->person) return(0);
  if(options->number && options->number != generation->number) return(0);
  if(options->tense && options->tense != generation->tense) return(0);
  if(options->mood && options->mood != generation->mood) return(0);
  if(options->degree && options->degree != generation->degree) return(0);
  if(options->dialect && generation->dialect &&
     !(options->dialect & generation->dialect)) return(0);
  if(!mask_matches(options->geographic_region,
                   generation->geographic_region) ||
     !mask_matches(options->gender,generation->gender) ||
     !mask_matches(options->grammatical_case,generation->grammatical_case) ||
     !mask_matches(options->voice,generation->voice)) return(0);
  if((options->flags & MORPHEUS_GENERATION_EXCLUDE_DUALS) &&
     generation->number == MORPHEUS_NUMBER_DUAL) return(0);
  return(1);
}

static void copy_generation(
    morpheus_generation *destination,
    const morpheus_normalized_generation *source)
{
  memset(destination,0,sizeof *destination);
  destination->struct_size=sizeof *destination;
  destination->part_of_speech=source->part_of_speech;
  destination->dialect=source->dialect;
  destination->geographic_region=source->geographic_region;
  destination->person=source->person;
  destination->number=source->number;
  destination->gender=source->gender;
  destination->grammatical_case=source->grammatical_case;
  destination->tense=source->tense;
  destination->mood=source->mood;
  destination->voice=source->voice;
  destination->degree=source->degree;
  memcpy(destination->surface,source->surface,sizeof destination->surface);
  memcpy(destination->lemma,source->lemma,sizeof destination->lemma);
  memcpy(destination->morph_flags,source->morph_flags,
         sizeof destination->morph_flags);
}

static morpheus_status ensure_generation_service(morpheus_context *context)
{
  static const char suffix[]="/gener.index";
  morpheus_gener_index *index=NULL;
  morpheus_generation_service *service=NULL;
  morpheus_gener_index_status index_status;
  morpheus_generation_status service_status;
  size_t root_length;
  char *path;

  if(context->public_generation_service) return(MORPHEUS_OK);
  root_length=strlen(context->stemlib_path);
  if(root_length > SIZE_MAX-sizeof suffix) return(MORPHEUS_INPUT_TOO_LONG);
  path=malloc(root_length+sizeof suffix);
  if(!path) return(MORPHEUS_NO_MEMORY);
  memcpy(path,context->stemlib_path,root_length);
  memcpy(path+root_length,suffix,sizeof suffix);
  index_status=morpheus_gener_index_open_file(path,&index);
  free(path);
  if(index_status == MORPHEUS_GENER_INDEX_NO_MEMORY) return(MORPHEUS_NO_MEMORY);
  if(index_status != MORPHEUS_GENER_INDEX_OK) return(MORPHEUS_STEMLIB_ERROR);
  service_status=morpheus_generation_service_create_at_path(
      index,context->stemlib_path,&service);
  if(service_status != MORPHEUS_GENERATION_OK) {
    morpheus_gener_index_close(index);
    return(service_status == MORPHEUS_GENERATION_NO_MEMORY ?
           MORPHEUS_NO_MEMORY : MORPHEUS_INTERNAL_ERROR);
  }
  context->public_generation_index=index;
  context->public_generation_service=service;
  context->public_generation_cleanup=generation_context_cleanup;
  return(MORPHEUS_OK);
}

static morpheus_status normalize_status(
    morpheus_generation_normalize_status status)
{
  switch(status) {
  case MORPHEUS_GENERATION_NORMALIZE_OK: return(MORPHEUS_OK);
  case MORPHEUS_GENERATION_NORMALIZE_NO_MEMORY: return(MORPHEUS_NO_MEMORY);
  case MORPHEUS_GENERATION_NORMALIZE_LIMIT:
    return(MORPHEUS_RESULT_LIMIT_EXCEEDED);
  default: return(MORPHEUS_INTERNAL_ERROR);
  }
}

size_t morpheus_generation_size(void)
{
  return(sizeof(morpheus_generation));
}

morpheus_status morpheus_generate(
    morpheus_context *context, const uint8_t *lemma, size_t length,
    const morpheus_generation_options *options,
    morpheus_generation_result **result)
{
  morpheus_normalized_generation_result *normalized=NULL;
  morpheus_generation_result *owned;
  morpheus_generation_normalize_status normalized_status;
  morpheus_status status;
  char canonical[MAXWORDSIZE];
  size_t limit;
  size_t input;
  size_t output=0;
  size_t count;

  if(!context || !lemma || !result) return(MORPHEUS_INVALID_ARGUMENT);
  *result=NULL;
  if(context->language != GREEK) return(MORPHEUS_INVALID_ARGUMENT);
  status=validate_options(options,&limit);
  if(status != MORPHEUS_OK) return(status);
  if(!length) return(MORPHEUS_INVALID_ARGUMENT);
  if(length >= sizeof canonical) return(MORPHEUS_INPUT_TOO_LONG);
  if(memchr(lemma,0,length)) return(MORPHEUS_INVALID_ARGUMENT);
  for(input=0;input != length;input++) {
    unsigned char byte=lemma[input];
    if((input == 0 && byte == '!') || byte == '-' || byte == '_' ||
       byte == '^' || byte == '+') continue;
    canonical[output++]=(char)byte;
  }
  if(!output) return(MORPHEUS_INVALID_ARGUMENT);
  canonical[output]=0;
  status=ensure_generation_service(context);
  if(status != MORPHEUS_OK) return(status);
  normalized_status=morpheus_generation_normalize(
      context->public_generation_service,canonical,
      (size_t)MORPHEUS_GENERATION_MAX_LIMIT,&normalized);
  if(normalized_status == MORPHEUS_GENERATION_NORMALIZE_NOT_FOUND) {
    owned=generation_result_create(0);
    if(!owned) return(MORPHEUS_NO_MEMORY);
    *result=owned;
    return(MORPHEUS_OK);
  }
  if(normalized_status != MORPHEUS_GENERATION_NORMALIZE_OK)
    return(normalize_status(normalized_status));
  count=morpheus_normalized_generation_result_count(normalized);
  output=0;
  for(input=0;input != count;input++) {
    const morpheus_normalized_generation *item=
        morpheus_normalized_generation_result_at(normalized,input);
    if(generation_matches(item,options) && ++output > limit) {
      morpheus_normalized_generation_result_free(normalized);
      return(MORPHEUS_RESULT_LIMIT_EXCEEDED);
    }
  }
  owned=generation_result_create(output);
  if(!owned) {
    morpheus_normalized_generation_result_free(normalized);
    return(MORPHEUS_NO_MEMORY);
  }
  output=0;
  for(input=0;input != count;input++) {
    const morpheus_normalized_generation *item=
        morpheus_normalized_generation_result_at(normalized,input);
    if(!generation_matches(item,options)) continue;
    copy_generation(owned->generations+output,item);
    owned->truncated_fields[output]=item->truncated_fields;
    output++;
  }
  owned->skipped_records=
      morpheus_normalized_generation_result_skipped_records(normalized);
  morpheus_normalized_generation_result_free(normalized);
  *result=owned;
  return(MORPHEUS_OK);
}

size_t morpheus_generation_result_count(
    const morpheus_generation_result *result)
{
  return(result ? result->count : 0);
}

size_t morpheus_generation_result_skipped_records(
    const morpheus_generation_result *result)
{
  return(result ? result->skipped_records : 0);
}

morpheus_status morpheus_generation_result_copy(
    const morpheus_generation_result *result, size_t index, void *buffer,
    size_t buffer_size)
{
  if(!result || !buffer) return(MORPHEUS_INVALID_ARGUMENT);
  if(index >= result->count) return(MORPHEUS_OUT_OF_RANGE);
  if(buffer_size < sizeof(morpheus_generation))
    return(MORPHEUS_BUFFER_TOO_SMALL);
  memcpy(buffer,result->generations+index,sizeof(morpheus_generation));
  return(MORPHEUS_OK);
}

morpheus_status morpheus_generation_result_get(
    const morpheus_generation_result *result, size_t index,
    morpheus_generation *generation)
{
  return(morpheus_generation_result_copy(
      result,index,generation,sizeof *generation));
}

morpheus_status morpheus_generation_result_truncated_fields(
    const morpheus_generation_result *result, size_t index,
    morpheus_truncated_fields *fields)
{
  if(!result || !fields) return(MORPHEUS_INVALID_ARGUMENT);
  if(index >= result->count) return(MORPHEUS_OUT_OF_RANGE);
  *fields=result->truncated_fields[index];
  return(MORPHEUS_OK);
}

void morpheus_generation_result_free(morpheus_generation_result *result)
{
  if(!result) return;
  free(result->truncated_fields);
  free(result->generations);
  free(result);
}

static void generation_context_cleanup(morpheus_context *context)
{
  if(!context) return;
  morpheus_generation_service_destroy(context->public_generation_service);
  morpheus_gener_index_close(context->public_generation_index);
  context->public_generation_service=NULL;
  context->public_generation_index=NULL;
  context->public_generation_cleanup=NULL;
}
