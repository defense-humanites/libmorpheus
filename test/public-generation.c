// SPDX-License-Identifier: AGPL-3.0-or-later

#include <assert.h>
#include <stdint.h>
#include <string.h>

#include <morpheus/morpheus.h>

static morpheus_context *open_context(const char *root)
{
  morpheus_config config={
    MORPHEUS_ABI_VERSION,sizeof config,root,MORPHEUS_LANGUAGE_GREEK
  };
  morpheus_context *context=NULL;
  assert(morpheus_open(&config,&context)==MORPHEUS_OK);
  assert(context);
  return(context);
}

static morpheus_generation_options default_options(void)
{
  morpheus_generation_options options={0};
  options.version=MORPHEUS_GENERATION_OPTIONS_VERSION;
  options.struct_size=sizeof options;
  return(options);
}

int main(int argc, char **argv)
{
  static const uint8_t canonicalized[]="!lo_-+^/gos";
  static const uint8_t embedded_nul[]={'l','o',0,'g','o','s'};
  morpheus_context *context;
  morpheus_generation_result *result=NULL;
  morpheus_generation_options options;
  morpheus_generation item;
  morpheus_truncated_fields truncated=99;
  char long_lemma[64];
  size_t i;
  size_t duals=0;
  size_t duplicates=0;

  assert(argc==3);
  assert(morpheus_generation_size()==sizeof(morpheus_generation));
  context=open_context(argv[1]);
  assert(morpheus_generate(context,canonicalized,sizeof canonicalized-1,NULL,
                           &result)==MORPHEUS_OK);
  assert(result);
  assert(morpheus_generation_result_count(result)==18);
  morpheus_close(context);
  context=NULL;
  for(i=0;i!=18;i++) {
    size_t previous;
    assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
    assert(item.struct_size==sizeof item);
    assert(item.part_of_speech==MORPHEUS_PART_OF_SPEECH_NOUN);
    assert(!strcmp(item.lemma,"lo/gos"));
    if(item.number==MORPHEUS_NUMBER_DUAL) duals++;
    for(previous=0;previous!=i;previous++) {
      morpheus_generation earlier;
      assert(morpheus_generation_result_get(result,previous,&earlier)==
             MORPHEUS_OK);
      if(!strcmp(earlier.surface,item.surface)) {
        duplicates++;
        break;
      }
    }
    assert(morpheus_generation_result_truncated_fields(result,i,&truncated)==
           MORPHEUS_OK);
    assert(!truncated);
  }
  assert(duals==3);
  assert(duplicates);
  assert(morpheus_generation_result_copy(result,0,&item,sizeof item-1)==
         MORPHEUS_BUFFER_TOO_SMALL);
  assert(morpheus_generation_result_get(result,18,&item)==
         MORPHEUS_OUT_OF_RANGE);
  assert(morpheus_generation_result_get(NULL,0,&item)==
         MORPHEUS_INVALID_ARGUMENT);
  assert(morpheus_generation_result_get(result,0,NULL)==
         MORPHEUS_INVALID_ARGUMENT);
  assert(morpheus_generation_result_truncated_fields(result,18,&truncated)==
         MORPHEUS_OUT_OF_RANGE);
  morpheus_generation_result_free(result);
  result=NULL;

  context=open_context(argv[1]);
  options=default_options();
  options.flags=MORPHEUS_GENERATION_EXCLUDE_DUALS;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_OK);
  assert(morpheus_generation_result_count(result)==15);
  morpheus_generation_result_free(result);
  result=NULL;

  options=default_options();
  options.number=MORPHEUS_NUMBER_DUAL;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_OK);
  assert(morpheus_generation_result_count(result)==3);
  morpheus_generation_result_free(result);
  result=NULL;

  options=default_options();
  options.dialect=MORPHEUS_DIALECT_ATTIC;
  options.result_limit=1;
  assert(morpheus_generate(context,(const uint8_t *)"multiple",8,&options,
                           &result)==MORPHEUS_OK);
  assert(morpheus_generation_result_count(result)==1);
  assert(morpheus_generation_result_get(result,0,&item)==MORPHEUS_OK);
  assert(item.dialect==MORPHEUS_DIALECT_ATTIC);
  assert(!strcmp(item.surface,"prw=ton"));
  morpheus_generation_result_free(result);
  result=NULL;

  options.dialect=MORPHEUS_DIALECT_IONIC;
  assert(morpheus_generate(context,(const uint8_t *)"multiple",8,&options,
                           &result)==MORPHEUS_OK);
  assert(morpheus_generation_result_count(result)==1);
  assert(morpheus_generation_result_get(result,0,&item)==MORPHEUS_OK);
  assert(item.dialect==MORPHEUS_DIALECT_IONIC);
  assert(!strcmp(item.surface,"deu/teron"));
  morpheus_generation_result_free(result);
  result=NULL;

  options=default_options();
  assert(morpheus_generate(context,(const uint8_t *)"multiple",8,&options,
                           &result)==MORPHEUS_OK);
  assert(morpheus_generation_result_count(result)==2);
  morpheus_generation_result_free(result);
  result=NULL;

  options.part_of_speech=MORPHEUS_PART_OF_SPEECH_VERB;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_OK);
  assert(result && !morpheus_generation_result_count(result));
  morpheus_generation_result_free(result);
  result=NULL;

  options=default_options();
  options.result_limit=17;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_RESULT_LIMIT_EXCEEDED);
  assert(!result);
  assert(!strcmp(morpheus_status_message(MORPHEUS_RESULT_LIMIT_EXCEEDED),
                 "generation result limit exceeded"));
  assert(morpheus_generate(context,(const uint8_t *)"missing",7,NULL,
                           &result)==MORPHEUS_OK);
  assert(result && !morpheus_generation_result_count(result));
  assert(!morpheus_generation_result_skipped_records(result));
  morpheus_generation_result_free(result);
  result=NULL;
  assert(!morpheus_generation_result_skipped_records(NULL));

  /* A record the engine cannot generate is skipped and counted. */
  assert(morpheus_generate(context,(const uint8_t *)"partial",7,NULL,
                           &result)==MORPHEUS_OK);
  assert(morpheus_generation_result_count(result)==18);
  assert(morpheus_generation_result_skipped_records(result)==1);
  morpheus_generation_result_free(result);
  result=NULL;
  options=default_options();
  options.number=MORPHEUS_NUMBER_DUAL;
  assert(morpheus_generate(context,(const uint8_t *)"partial",7,&options,
                           &result)==MORPHEUS_OK);
  assert(morpheus_generation_result_count(result)==3);
  assert(morpheus_generation_result_skipped_records(result)==1);
  morpheus_generation_result_free(result);
  result=NULL;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,NULL,
                           &result)==MORPHEUS_OK);
  assert(!morpheus_generation_result_skipped_records(result));
  morpheus_generation_result_free(result);
  result=NULL;

  /*
   * Stem flags reach the record as they reach an analysis: h(duter is an
   * irregular comparative stem, so its forms are comparatives.
   */
  assert(morpheus_generate(context,(const uint8_t *)"h(du/s",6,NULL,
                           &result)==MORPHEUS_OK);
  assert(morpheus_generation_result_count(result));
  for(i=0;i!=morpheus_generation_result_count(result);i++) {
    const unsigned flag=MORPHEUS_MORPH_FLAG_IRREGULAR_COMPARATIVE;
    assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
    assert(item.degree==MORPHEUS_DEGREE_COMPARATIVE);
    assert(item.morph_flags[flag/8u] & (1u<<(flag%8u)));
  }
  {
    size_t all=morpheus_generation_result_count(result);
    morpheus_generation_result_free(result);
    result=NULL;
    options=default_options();
    options.degree=MORPHEUS_DEGREE_COMPARATIVE;
    assert(morpheus_generate(context,(const uint8_t *)"h(du/s",6,&options,
                             &result)==MORPHEUS_OK);
    assert(morpheus_generation_result_count(result)==all);
  }
  morpheus_generation_result_free(result);
  result=NULL;

  /* The stem-boundary hyphen of a)nqr-wp does not reach the surfaces. */
  assert(morpheus_generate(context,(const uint8_t *)"a)/nqrwpos",10,NULL,
                           &result)==MORPHEUS_OK);
  assert(morpheus_generation_result_count(result)==18);
  {
    int saw_nominative=0;
    for(i=0;i!=18;i++) {
      assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
      assert(!strchr(item.surface,'-'));
      if(!strcmp(item.surface,"a)/nqrwpos")) saw_nominative=1;
    }
    assert(saw_nominative);
  }
  morpheus_generation_result_free(result);
  result=NULL;

  assert(morpheus_generate(context,NULL,0,NULL,&result)==
         MORPHEUS_INVALID_ARGUMENT);
  assert(morpheus_generate(context,embedded_nul,sizeof embedded_nul,NULL,
                           &result)==MORPHEUS_INVALID_ARGUMENT);
  assert(morpheus_generate(context,(const uint8_t *)"",0,NULL,&result)==
         MORPHEUS_INVALID_ARGUMENT);
  options=default_options();
  options.version++;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_ABI_MISMATCH);
  options=default_options();
  options.struct_size--;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_ABI_MISMATCH);
  options=default_options();
  options.voice=UINT32_C(8);
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_INVALID_ARGUMENT);
  options=default_options();
  options.dialect=UINT32_C(1)<<31;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_INVALID_ARGUMENT);
  options=default_options();
  options.result_limit=MORPHEUS_GENERATION_MAX_LIMIT+1;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_INVALID_ARGUMENT);
  memset(long_lemma,'a',sizeof long_lemma);
  assert(morpheus_generate(context,(const uint8_t *)long_lemma,
                           sizeof long_lemma,NULL,&result)==
         MORPHEUS_INPUT_TOO_LONG);
  options=default_options();
  options.number=MORPHEUS_NUMBER_DUAL;
  options.flags=MORPHEUS_GENERATION_EXCLUDE_DUALS;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_INVALID_ARGUMENT);
  morpheus_close(context);

  context=open_context(argv[2]);
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,NULL,
                           &result)==MORPHEUS_STEMLIB_ERROR);
  assert(!result);
  morpheus_close(context);
  {
    morpheus_config latin={
      MORPHEUS_ABI_VERSION,sizeof latin,argv[2],MORPHEUS_LANGUAGE_LATIN
    };
    context=NULL;
    assert(morpheus_open(&latin,&context)==MORPHEUS_OK);
    assert(morpheus_generate(context,(const uint8_t *)"amo",3,NULL,&result)==
           MORPHEUS_INVALID_ARGUMENT);
    morpheus_close(context);
  }
  morpheus_generation_result_free(NULL);
  assert(!morpheus_generation_result_count(NULL));
  return(0);
}
