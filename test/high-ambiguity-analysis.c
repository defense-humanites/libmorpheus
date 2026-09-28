// SPDX-License-Identifier: AGPL-3.0-or-later

#include <assert.h>
#include <stdint.h>
#include <string.h>

#include <morpheus/morpheus.h>

#ifndef MORPHEUS_TEST_STEMLIB
#error MORPHEUS_TEST_STEMLIB is required
#endif

static void
check_count(morpheus_context *context, const char *word, size_t expected)
{
  morpheus_result *result = NULL;
  assert(morpheus_analyze(context,(const uint8_t *)word,strlen(word),
                          MORPHEUS_OPTION_IGNORE_ACCENTS,&result) ==
         MORPHEUS_OK);
  assert(result != NULL);
  assert(morpheus_result_count(result) == expected);
  morpheus_result_free(result);
}

int main(void)
{
  static const char *const growth_regressions[] = {
    "a)mfestan", "*)efuperqe", "*)enna", "*)epefanto", "*)ephien", "*)epiproemen",
    "*hu)lisqhn", "*kaqeton", "*parhion", "*proknh", "*prosepirriptw",
    "*sunemen", "*susseuw", "a)mfhn", "a)nh", "a)phn",
    "a)phnhs", "a)poseuw", "a)posseuw", "diafussw", "e)cemen",
    "e)cuperqe", "e)kseuw", "e)nerqe", "e)peite", "e)pirriptw",
    "e)piseuw", "e)spete", "ei(ato", "h(sqe", "h)hn", "hi)xqhn",
    "i)e", "kaqeiato", "kaquperqe", "ou(qeis", "parechs", "proemen",
    "proshnhs", "seuw", "sunete", "teucw", "u)pemnhsqhn",
    "u)penerqe", "u)perbasan", "u)perqe"
  };
  morpheus_config config = {
    MORPHEUS_ABI_VERSION, sizeof config, MORPHEUS_TEST_STEMLIB,
    MORPHEUS_LANGUAGE_GREEK
  };
  morpheus_context *context = NULL;
  assert(morpheus_open(&config,&context) == MORPHEUS_OK);
  for (size_t i = 0; i < sizeof growth_regressions /
                            sizeof growth_regressions[0]; ++i) {
    morpheus_result *result = NULL;
    const char *word = growth_regressions[i];
    assert(morpheus_analyze(context,(const uint8_t *)word,strlen(word),
                            MORPHEUS_OPTION_IGNORE_ACCENTS,&result) ==
           MORPHEUS_OK);
    assert(result != NULL);
    assert(morpheus_result_count(result) > 0);
    morpheus_result_free(result);
  }
  check_count(context,"a)nalow",26);
  check_count(context,"a(napinw",39);
  morpheus_close(context);
  return 0;
}
