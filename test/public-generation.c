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

/*
 * Whether lemma generates surface, and whether any of its surfaces contains
 * fragment.
 */
static void generated_surfaces(morpheus_context *context, const char *lemma,
                               const char *surface, const char *fragment,
                               int *has_surface, int *has_fragment)
{
  morpheus_generation_result *result=NULL;
  morpheus_generation item;
  size_t i;

  *has_surface=0;
  *has_fragment=0;
  assert(morpheus_generate(context,(const uint8_t *)lemma,strlen(lemma),NULL,
                           &result)==MORPHEUS_OK);
  for(i=0;i!=morpheus_generation_result_count(result);i++) {
    assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
    if(!strcmp(item.surface,surface)) *has_surface=1;
    if(strstr(item.surface,fragment)) *has_fragment=1;
  }
  assert(morpheus_generation_result_count(result));
  morpheus_generation_result_free(result);
}

/*
 * Generates lemma and checks that every record carries canonical as its
 * lemma and is a verb form. Returns the record count, and whether a record
 * has surface (when surface is not NULL).
 */
static size_t generate_compound(morpheus_context *context, const char *lemma,
                                const char *canonical, const char *surface,
                                int *has_surface)
{
  morpheus_generation_result *result=NULL;
  morpheus_generation item;
  size_t count;
  size_t i;

  if(has_surface) *has_surface=0;
  assert(morpheus_generate(context,(const uint8_t *)lemma,strlen(lemma),NULL,
                           &result)==MORPHEUS_OK);
  assert(result);
  count=morpheus_generation_result_count(result);
  for(i=0;i!=count;i++) {
    assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
    assert(!strcmp(item.lemma,canonical));
    assert(item.part_of_speech==MORPHEUS_PART_OF_SPEECH_VERB);
    if(surface && !strcmp(item.surface,surface)) *has_surface=1;
  }
  morpheus_generation_result_free(result);
  return(count);
}

/*
 * Whether lemma generates records with flag, and whether all of them begin
 * with prefix.
 */
/*
 * Counts the records of lemma that carry flag and tells whether they all
 * begin with prefix and all have the dialect *dialect (when not NULL, *dialect
 * becomes 0 when they differ). Returns the number of records.
 */
static size_t flagged_records(morpheus_context *context, const char *lemma,
                              morpheus_generation_flags request_flags,
                              unsigned int flag, const char *prefix,
                              size_t *flagged, int *all_prefixed,
                              morpheus_dialect *dialect)
{
  morpheus_generation_options options=default_options();
  morpheus_generation_result *result=NULL;
  morpheus_generation item;
  size_t count;
  size_t i;

  *flagged=0;
  *all_prefixed=1;
  options.flags=request_flags;
  assert(morpheus_generate(context,(const uint8_t *)lemma,strlen(lemma),
                           &options,&result)==MORPHEUS_OK);
  count=morpheus_generation_result_count(result);
  for(i=0;i!=count;i++) {
    assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
    if(!(item.morph_flags[flag/8u] & (1u<<(flag%8u)))) continue;
    (*flagged)++;
    if(strncmp(item.surface,prefix,strlen(prefix))) *all_prefixed=0;
    if(dialect && item.dialect!=*dialect) *dialect=0;
  }
  morpheus_generation_result_free(result);
  return(count);
}

static void flagged_surfaces(morpheus_context *context, const char *lemma,
                             unsigned int flag, const char *prefix,
                             size_t *flagged, int *all_prefixed)
{
  (void)flagged_records(context,lemma,0,flag,prefix,flagged,all_prefixed,NULL);
}

/* Whether surface is generated as a first singular and as a third plural. */
static void homograph_readings(morpheus_context *context, const char *lemma,
                               const char *surface, int *first_singular,
                               int *third_plural)
{
  morpheus_generation_result *result=NULL;
  morpheus_generation item;
  size_t i;

  *first_singular=0;
  *third_plural=0;
  assert(morpheus_generate(context,(const uint8_t *)lemma,strlen(lemma),NULL,
                           &result)==MORPHEUS_OK);
  for(i=0;i!=morpheus_generation_result_count(result);i++) {
    assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
    if(strcmp(item.surface,surface)) continue;
    if(item.person==MORPHEUS_PERSON_FIRST &&
       item.number==MORPHEUS_NUMBER_SINGULAR) *first_singular=1;
    if(item.person==MORPHEUS_PERSON_THIRD &&
       item.number==MORPHEUS_NUMBER_PLURAL) *third_plural=1;
  }
  morpheus_generation_result_free(result);
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

  /*
   * A form has the dialects that its preverb, augment, stem and ending all
   * allow. After r, an ending in -h is Ionic and epic, not Attic (xw/rhn,
   * as analysis reads it), and a form whose parts share no dialect is left
   * out: the Doric stem a(_duter takes -a_n (Doric) but not -hn.
   */
  {
    size_t eta=0;
    int doric=0;

    assert(morpheus_generate(context,(const uint8_t *)"xw/ra",5,NULL,
                             &result)==MORPHEUS_OK);
    for(i=0;i!=morpheus_generation_result_count(result);i++) {
      assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
      if(strcmp(item.surface,"xw/rhn") && strcmp(item.surface,"xw/rhs") &&
         strcmp(item.surface,"xw/rh|")) continue;
      assert(item.dialect==(MORPHEUS_DIALECT_IONIC|MORPHEUS_DIALECT_EPIC));
      eta++;
    }
    assert(eta==3);
    morpheus_generation_result_free(result);
    result=NULL;
    assert(morpheus_generate(context,(const uint8_t *)"h(du/s",6,NULL,
                             &result)==MORPHEUS_OK);
    for(i=0;i!=morpheus_generation_result_count(result);i++) {
      assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
      assert(strcmp(item.surface,"a(_dute/rhn"));
      if(!strcmp(item.surface,"a(_dute/ra_n")) {
        assert(item.dialect==MORPHEUS_DIALECT_DORIC);
        doric=1;
      }
    }
    assert(doric);
    morpheus_generation_result_free(result);
    result=NULL;
    /*
     * A record that forces its ending states the form's dialects: the
     * Aeolic stem takes the ending the table calls epic.
     */
    assert(morpheus_generate(context,(const uint8_t *)"eu)tri/aina",11,NULL,
                             &result)==MORPHEUS_OK);
    assert(morpheus_generation_result_count(result)==1);
    assert(morpheus_generation_result_get(result,0,&item)==MORPHEUS_OK);
    assert(!strcmp(item.surface,"eu)tri/aina"));
    assert(item.dialect==(MORPHEUS_DIALECT_AEOLIC|MORPHEUS_DIALECT_EPIC));
    morpheus_generation_result_free(result);
    result=NULL;
  }

  /*
   * Analysis reads an indicative without its augment as Homeric or Ionic,
   * and generation returns these forms too: lu/on is an imperfect as well
   * as a participle, a)po/luon an imperfect of the compound. Their readings
   * are indicative and their dialects Ionic or epic, so that an Attic
   * filter leaves them out. When no part names a dialect, the form is
   * Homeric and Ionic, as analysis labels it.
   */
  {
    const unsigned flag=MORPHEUS_MORPH_FLAG_UNAUGMENTED;
    int first_singular=0;
    int third_plural=0;
    int participle=0;
    size_t unaugmented=0;

    assert(morpheus_generate(context,(const uint8_t *)"lu/w",4,NULL,
                             &result)==MORPHEUS_OK);
    for(i=0;i!=morpheus_generation_result_count(result);i++) {
      assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
      if(item.morph_flags[flag/8u] & (1u<<(flag%8u))) {
        unaugmented++;
        assert(item.mood==MORPHEUS_MOOD_INDICATIVE);
        assert(item.dialect &&
               !(item.dialect & ~(MORPHEUS_DIALECT_IONIC|MORPHEUS_DIALECT_EPIC)));
      }
      if(strcmp(item.surface,"lu/on")) continue;
      if(item.mood==MORPHEUS_MOOD_PARTICIPLE) participle=1;
      if(item.tense==MORPHEUS_TENSE_IMPERFECT) {
        assert(item.dialect==
               (MORPHEUS_DIALECT_HOMERIC|MORPHEUS_DIALECT_IONIC));
        if(item.person==MORPHEUS_PERSON_FIRST) first_singular=1;
        if(item.person==MORPHEUS_PERSON_THIRD) third_plural=1;
      }
    }
    assert(unaugmented && participle && first_singular && third_plural);
    morpheus_generation_result_free(result);
    result=NULL;
    {
      size_t flagged;
      int prefixed;

      /* The preverb comes first, without an augment (not a)pe/luon). */
      flagged_surfaces(context,"a)polu/w",flag,"a)po",&flagged,&prefixed);
      assert(flagged && prefixed);
    }
    /*
     * lelhk ... plup ind act attic end:h forces its ending, but its Attic
     * stem does not allow the Ionic and epic of an unaugmented form: the
     * record gives its augmented e)lelh/kh and no unaugmented form.
     */
    {
      int augmented=0;

      assert(morpheus_generate(context,(const uint8_t *)"lanqa/nw",8,NULL,
                               &result)==MORPHEUS_OK);
      for(i=0;i!=morpheus_generation_result_count(result);i++) {
        assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
        assert(!(item.morph_flags[flag/8u] & (1u<<(flag%8u))));
        if(!strcmp(item.surface,"e)lelh/kh")) augmented=1;
      }
      assert(augmented);
      morpheus_generation_result_free(result);
      result=NULL;
    }
    /*
     * The unaugmented forms of a preverb variant come last (ka/lluon,
     * apocope and unaugmented), and MORPHEUS_GENERATION_EXCLUDE_PREVERB_VARIANTS
     * leaves them out with the other variants.
     */
    {
      const unsigned apocope=MORPHEUS_MORPH_FLAG_APOCOPE;
      morpheus_generation_options options=default_options();
      size_t both=0;
      size_t plain=0;
      int kalluon=0;

      assert(morpheus_generate(context,(const uint8_t *)"katalu/w",8,NULL,
                               &result)==MORPHEUS_OK);
      for(i=0;i!=morpheus_generation_result_count(result);i++) {
        assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
        if(!(item.morph_flags[flag/8u] & (1u<<(flag%8u))) ||
           !(item.morph_flags[apocope/8u] & (1u<<(apocope%8u))))
          continue;
        both++;
        assert(item.mood==MORPHEUS_MOOD_INDICATIVE);
        if(!strcmp(item.surface,"ka/lluon") &&
           item.tense==MORPHEUS_TENSE_IMPERFECT) kalluon=1;
      }
      assert(both && kalluon);
      morpheus_generation_result_free(result);
      result=NULL;
      options.flags=MORPHEUS_GENERATION_EXCLUDE_PREVERB_VARIANTS;
      assert(morpheus_generate(context,(const uint8_t *)"katalu/w",8,&options,
                               &result)==MORPHEUS_OK);
      for(i=0;i!=morpheus_generation_result_count(result);i++) {
        assert(morpheus_generation_result_get(result,i,&item)==MORPHEUS_OK);
        assert(!(item.morph_flags[apocope/8u] & (1u<<(apocope%8u))));
        if(item.morph_flags[flag/8u] & (1u<<(flag%8u))) plain++;
      }
      assert(plain);
      morpheus_generation_result_free(result);
      result=NULL;
    }
  }

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

  /*
   * Compounds are composed from the simple verb's records, under the names
   * analysis reports: the listed compound (a)po/-lu/w is listed as
   * a)polu/w), a hyphenated name when the list has none (a)mfi/-lu/w,
   * canonically a)mfi/lu/w), and stems that occur only in compounds
   * (-dhme/w), which the simple lemma never generates.
   */
  {
    size_t simple;
    size_t listed;

    assert(morpheus_generate(context,(const uint8_t *)"lu/w",4,NULL,
                             &result)==MORPHEUS_OK);
    simple=morpheus_generation_result_count(result);
    assert(simple);
    morpheus_generation_result_free(result);
    result=NULL;
    int found;

    listed=generate_compound(context,"a)polu/w","a)polu/w","a)polu/w",&found);
    assert(listed>=simple && found);
    assert(generate_compound(context,"a)mfi/-lu/w","a)mfi/lu/w","a)mfilu/w",
                             &found)>=simple && found);
    assert(generate_compound(context,"a)po/-lu/w","a)polu/w",NULL,NULL)==0);
    assert(generate_compound(context,"e)pidhme/w","e)pidhme/w",NULL,NULL));
    assert(generate_compound(context,"dhme/w","dhme/w",NULL,NULL)==0);
    assert(generate_compound(context,"-dhme/w","dhme/w",NULL,NULL)==0);
  }

  /*
   * The variants of a single preverb that analysis accepts come with their
   * flags, each spelled as the preverb table spells it: apocope (a)l-lu/w,
   * ka/l-lu), ἐς for εἰς, ξυν- for συν-, ἐνι- for ἐν-, and the unaspirated
   * preverb before a rough breathing (kati/zw).
   */
  {
    size_t flagged;
    int prefixed;

    flagged_surfaces(context,"a)nalu/w",MORPHEUS_MORPH_FLAG_APOCOPE,"a)",
                     &flagged,&prefixed);
    assert(flagged && prefixed);
    flagged_surfaces(context,"katalu/w",MORPHEUS_MORPH_FLAG_APOCOPE,"ka",
                     &flagged,&prefixed);
    assert(flagged && prefixed);
    flagged_surfaces(context,"ei)se/xw",MORPHEUS_MORPH_FLAG_SHORT_EIS,"e)",
                     &flagged,&prefixed);
    assert(flagged && prefixed);
    flagged_surfaces(context,"sullu/w",MORPHEUS_MORPH_FLAG_SIGMA_TO_CI,"cu",
                     &flagged,&prefixed);
    assert(flagged && prefixed);
    flagged_surfaces(context,"kaqi/zw",MORPHEUS_MORPH_FLAG_UNASPIRATED_PREVERB,
                     "ka",&flagged,&prefixed);
    assert(flagged && prefixed);
    /* The plain compound carries none of them. */
    flagged_surfaces(context,"a)polu/w",MORPHEUS_MORPH_FLAG_APOCOPE,"",
                     &flagged,&prefixed);
    assert(!flagged);
  }

  /*
   * A variant keeps every reading of a surface: cune/luon, like sune/luon,
   * is a first singular and a third plural. Analysis reads the unaspirated
   * preverb as Ionic, and so does generation.
   * MORPHEUS_GENERATION_EXCLUDE_PREVERB_VARIANTS leaves the variants out.
   */
  {
    size_t flagged;
    size_t all;
    size_t plain;
    int prefixed;
    int first_singular;
    int third_plural;
    morpheus_dialect dialect=MORPHEUS_DIALECT_IONIC;

    homograph_readings(context,"sullu/w","sune/luon",&first_singular,
                       &third_plural);
    assert(first_singular && third_plural);
    homograph_readings(context,"sullu/w","cune/luon",&first_singular,
                       &third_plural);
    assert(first_singular && third_plural);
    flagged_records(context,"kaqi/zw",0,
                    MORPHEUS_MORPH_FLAG_UNASPIRATED_PREVERB,"ka",&flagged,
                    &prefixed,&dialect);
    assert(flagged && prefixed && dialect==MORPHEUS_DIALECT_IONIC);
    /*
     * e(ry reg_fut doric end:w= forces its ending, so its forms keep the
     * union of their parts' dialects; the unaspirated preverb still allows
     * Ionic only, and a Doric future without Ionic is left out.
     */
    flagged_records(context,"a)fe/rpw",0,
                    MORPHEUS_MORPH_FLAG_UNASPIRATED_PREVERB,"a)",&flagged,
                    &prefixed,&dialect);
    assert(flagged && prefixed && dialect==MORPHEUS_DIALECT_IONIC);
    all=flagged_records(context,"katalu/w",0,MORPHEUS_MORPH_FLAG_APOCOPE,
                        "ka",&flagged,&prefixed,NULL);
    assert(flagged);
    plain=flagged_records(context,"katalu/w",
                          MORPHEUS_GENERATION_EXCLUDE_PREVERB_VARIANTS,
                          MORPHEUS_MORPH_FLAG_APOCOPE,"ka",&flagged,
                          &prefixed,NULL);
    assert(!flagged && plain && plain<all);
    flagged_records(context,"kaqi/zw",
                    MORPHEUS_GENERATION_EXCLUDE_PREVERB_VARIANTS,
                    MORPHEUS_MORPH_FLAG_UNASPIRATED_PREVERB,"ka",&flagged,
                    &prefixed,NULL);
    assert(!flagged);
  }

  /*
   * pro and peri do not elide before a vowel; the engine marks the hiatus
   * with '+', which surfaces keep only as the diaeresis of an iota or
   * upsilon that would otherwise form a diphthong: proe/xw, perie/xw, but
   * proi/+sxw (προΐσχω).
   */
  {
    int has_surface;
    int has_mark;

    generated_surfaces(context,"proe/xw","proe/xw","pro+",&has_surface,
                       &has_mark);
    assert(has_surface && !has_mark);
    generated_surfaces(context,"perie/xw","perie/xw","peri+",&has_surface,
                       &has_mark);
    assert(has_surface && !has_mark);
    generated_surfaces(context,"proi/sxw","proi/+sxw","pro+",&has_surface,
                       &has_mark);
    assert(has_surface && !has_mark);
  }

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
  options.flags=MORPHEUS_GENERATION_EXCLUDE_PREVERB_VARIANTS<<1;
  assert(morpheus_generate(context,(const uint8_t *)"lo/gos",6,&options,
                           &result)==MORPHEUS_INVALID_ARGUMENT);
  /* Every paradigm fits the default limit. */
  assert(MORPHEUS_GENERATION_DEFAULT_LIMIT==MORPHEUS_GENERATION_MAX_LIMIT);
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
