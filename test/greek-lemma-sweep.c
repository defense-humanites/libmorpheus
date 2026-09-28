// SPDX-License-Identifier: AGPL-3.0-or-later

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include <morpheus/morpheus.h>

#ifndef MORPHEUS_TEST_STEMLIB
#error MORPHEUS_TEST_STEMLIB is required
#endif
#ifndef MORPHEUS_TEST_LEMMA_LIST
#error MORPHEUS_TEST_LEMMA_LIST is required
#endif

int main(void)
{
  morpheus_config config = {
    MORPHEUS_ABI_VERSION, sizeof config, MORPHEUS_TEST_STEMLIB,
    MORPHEUS_LANGUAGE_GREEK
  };
  morpheus_context *context = NULL;
  FILE *source = fopen(MORPHEUS_TEST_LEMMA_LIST,"r");
  char line[256];
  size_t tested = 0;

  if (!source || morpheus_open(&config,&context) != MORPHEUS_OK) {
    fprintf(stderr,"Cannot open the pinned Alpheios lemma corpus\n");
    if (source) fclose(source);
    return 1;
  }
  while (fgets(line,sizeof line,source)) {
    char word[60];
    morpheus_result *result = NULL;
    morpheus_status status;
    if (sscanf(line,"%59s",word) != 1) continue;
    status = morpheus_analyze(context,(const uint8_t *)word,strlen(word),
                              MORPHEUS_OPTION_IGNORE_ACCENTS,&result);
    if (status != MORPHEUS_OK || !result) {
      fprintf(stderr,"Analysis failed after %zu lemmas: %s (status %d)\n",
              tested,word,(int)status);
      morpheus_result_free(result);
      fclose(source);
      morpheus_close(context);
      return 1;
    }
    morpheus_result_free(result);
    ++tested;
  }
  fclose(source);
  morpheus_close(context);
  if (tested < 30000) {
    fprintf(stderr,"Pinned Alpheios lemma corpus is incomplete: %zu\n",tested);
    return 1;
  }
  return 0;
}
