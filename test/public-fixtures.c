// SPDX-License-Identifier: AGPL-3.0-or-later

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include <morpheus/morpheus.h>

#ifndef MORPHEUS_TEST_STEMLIB
#error MORPHEUS_TEST_STEMLIB is required
#endif

static size_t
analysis_count(morpheus_context *context, const char *word,
               morpheus_options options)
{
  morpheus_result *result = NULL;
  size_t count;

  assert(morpheus_analyze(context,(const uint8_t *)word,strlen(word),
                          options,&result) == MORPHEUS_OK);
  count=morpheus_result_count(result);
  morpheus_result_free(result);
  return(count);
}

static size_t
part_of_speech_count(morpheus_context *context, const char *word,
                     morpheus_options options,
                     morpheus_part_of_speech part_of_speech)
{
  morpheus_result *result = NULL;
  morpheus_analysis analysis;
  size_t count;
  size_t matches=0;
  size_t i;

  assert(morpheus_analyze(context,(const uint8_t *)word,strlen(word),
                          options,&result) == MORPHEUS_OK);
  count=morpheus_result_count(result);
  for(i=0;i<count;i++) {
    assert(morpheus_result_copy(result,i,&analysis,sizeof analysis) ==
           MORPHEUS_OK);
    if(analysis.part_of_speech == part_of_speech) matches++;
  }
  morpheus_result_free(result);
  return(matches);
}

int
main(void)
{
  morpheus_config config = {
    MORPHEUS_ABI_VERSION,
    sizeof config,
    MORPHEUS_TEST_STEMLIB,
    MORPHEUS_LANGUAGE_GREEK
  };
  morpheus_context *context = NULL;
  const morpheus_options strict=MORPHEUS_OPTION_STRICT_CASE;

  assert(morpheus_open(&config,&context) == MORPHEUS_OK);
  assert(analysis_count(context,"bi/ou",strict) == 4);
  assert(analysis_count(context,"bi/ou",
                        strict|MORPHEUS_OPTION_IGNORE_ACCENTS) == 8);
  assert(analysis_count(context,"tou=",strict) == 3);
  assert(analysis_count(context,"anqrwpos",
                        strict|MORPHEUS_OPTION_IGNORE_ACCENTS) > 0);
  assert(analysis_count(context,"a)nalow",
                        MORPHEUS_OPTION_IGNORE_ACCENTS) == 26);
  assert(analysis_count(context,"a(napinw",
                        MORPHEUS_OPTION_IGNORE_ACCENTS) == 39);
  assert(part_of_speech_count(context,"du/o",strict,
                              MORPHEUS_PART_OF_SPEECH_NUMERAL) == 1);
  assert(part_of_speech_count(context,"tou=",strict,
                              MORPHEUS_PART_OF_SPEECH_ARTICLE) == 1);
  assert(part_of_speech_count(context,"tou=",strict,
                              MORPHEUS_PART_OF_SPEECH_PRONOUN) == 1);
  assert(part_of_speech_count(context,"tou=",strict,
                              MORPHEUS_PART_OF_SPEECH_UNKNOWN) == 1);
  assert(part_of_speech_count(context,"tw\\",strict,
                              MORPHEUS_PART_OF_SPEECH_ADVERB) >= 1);
  assert(part_of_speech_count(context,"a)n",
                              strict|MORPHEUS_OPTION_IGNORE_ACCENTS,
                              MORPHEUS_PART_OF_SPEECH_PARTICLE) >= 1);
  assert(part_of_speech_count(context,"a)n",
                              strict|MORPHEUS_OPTION_IGNORE_ACCENTS,
                              MORPHEUS_PART_OF_SPEECH_CONJUNCTION) >= 1);
  assert(part_of_speech_count(context,"a)n",
                              strict|MORPHEUS_OPTION_IGNORE_ACCENTS,
                              MORPHEUS_PART_OF_SPEECH_PREPOSITION) >= 1);
  morpheus_close(context);

  config.language=MORPHEUS_LANGUAGE_LATIN;
  assert(morpheus_open(&config,&context) == MORPHEUS_OK);
  assert(analysis_count(context,"est",strict) == 2);
  morpheus_close(context);
  return(0);
}
