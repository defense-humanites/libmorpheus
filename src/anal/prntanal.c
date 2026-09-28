#include "anal_internal.h"
#include "../morphlib/runtime_context_internal.h"

#define ANALYSIS_CONTEXT (morpheus_runtime_context_current())
#define pbuf (ANALYSIS_CONTEXT->analysis_print_buffer)
#define prevlemma (ANALYSIS_CONTEXT->analysis_previous_lemma)
#define prevword (ANALYSIS_CONTEXT->analysis_previous_word)
#define prevstem (ANALYSIS_CONTEXT->analysis_previous_stem)
#define curan (ANALYSIS_CONTEXT->analysis_current_number)
#define NEWLINE "\r"

#include "prntanal.proto.h"

static size_t print_capacity(void)
{
  return ANALYSIS_CONTEXT->analysis_print_capacity;
}

int PrntAnalyses(gk_word *Gkword, PrntFlags prntflags, FILE *fout)
{
  int i, nanals;
  gk_analysis * Anal;
  char tmp[LONGSTRING];

	if (!Gkword) {
	  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
	  return(0);
	}
	nanals = totanal_of(Gkword);
	if (nanals < 0 || (nanals && !analysis_of(Gkword))) {
	  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
	  return(0);
	}
  {
    /* Reserve room for the longest formatted analysis, including its labels. */
    size_t unit = (size_t)LONGSTRING * 4 + 256;
    size_t required;
    char *grown;
    if ((size_t)nanals > (SIZE_MAX - unit) / unit) {
      morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
      return(0);
    }
    required = ((size_t)nanals + 1) * unit;
    if (print_capacity() < required) {
      grown = realloc(pbuf,required);
      if (!grown) {
        morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
        return(0);
      }
      pbuf = grown;
      ANALYSIS_CONTEXT->analysis_print_capacity = required;
    }
  }
  *pbuf = 0;
  SortAnals(analysis_of(Gkword),nanals);

  if(  prntflags & SHOW_LEMMA ) {
    DumpLemmaInfo(Gkword,prntflags,fout);
    return(nanals);
  }

  if( prntflags & (DBASEFORMAT|SHOW_FULL_INFO|LEXICON_OUTPUT|PARSE_FORMAT|PERSEUS_FORMAT|ENDING_INDEX) ) {
    dump_all_anals(Gkword,prntflags,fout);
    return(nanals);
  }

	

  if( ! (prntflags & SHOW_LEMMA )  ) {
	if (snprintf(tmp,sizeof tmp,"$%s&  %s%s", rawword_of(Gkword),
	             nanals == 1 ? "is" : "could be",NEWLINE) >=
	    (int)sizeof tmp) {
	  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
	  return(0);
	}
    if( prntflags & KEEP_BETA ) {
	  if (!Xstrncat(pbuf,tmp,print_capacity())) {
	    morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
	    return(0);
	  }
    } else {
      beta2smarta(tmp,pbuf);
    }
  }
	
  prevlemma[0] = 0;
  Xstrncpy(prevword,rawword_of(Gkword),MAXWORDSIZE );
  Xstrncpy(prevstem,stem_of(Gkword),MAXWORDSIZE );
	
  for(i=0,curan=0;i<nanals;i++) {
    Anal = analysis_of(Gkword)+i;
    PrntOneAnalysis(Anal,prntflags,fout);
    Xstrncpy(prevlemma,lemma_of(Anal),MAXWORDSIZE);
  }
	
  if(i ) {
    /*		if(! (prntflags_of(Gkword) & BUFFER_ANALS))
		putchar( '\n' );
		else*/
    if( prntflags & SHOW_LEMMA ) 
      morpheus_runtime_string_append(
	  pbuf,"\n",print_capacity());
    else
      morpheus_runtime_string_append(
	  pbuf,"\r",print_capacity());
  }
  /*	puts(pbuf);*/
  return(nanals);
}

char *
anal_buf(void)
{
  return(pbuf);
}

static int GoodAnals(gk_word *Gkword, int lemmflag)
{
  char curlem[MAXWORDSIZE];
  gk_analysis * Anal;
  int goodanals = 0;
  int difflems = 0;
  int i;
	
  curlem[0] = 0;

  /*
   * grc 6/11/94
   *
   * option to filter out those compounds that are not in a known dictionary --
   * this gets rid of lots of weird analyses
   */
  for(i=0;i<totanal_of(Gkword);i++) {
    Anal = analysis_of(Gkword)+i;
    if( strcmp(curlem,lemma_of(Anal) ) ) {
      difflems ++;
      Xstrcpy(curlem,lemma_of(Anal));
    }
    if(strchr(lemma_of(Anal),'-') == NULL) {
      goodanals++;
    }
  }
  return(lemmflag? difflems : goodanals );
}

void DumpLemmaInfo(gk_word *Gkword, PrntFlags prntflags, FILE *f)
{
  int i = 0;
  gk_analysis * Anal;
  int goodanals = 0;
  int difflems = 0;
  char curlem[MAXWORDSIZE];
	
  curlem[0] = 0;

  goodanals = GoodAnals(Gkword,0);
  difflems =  GoodAnals(Gkword,1);
	
	
  if(! goodanals ) goodanals = totanal_of(Gkword);

  curlem[0] = 0;
  fprintf(f,"form:%s\n", rawword_of(Gkword));
  for(i=0;i<totanal_of(Gkword);i++) {
    Anal = analysis_of(Gkword)+i;

    if( strcmp(curlem,lemma_of(Anal) ) ) {
      if( (strchr(lemma_of(Anal),'-') == NULL ) || (goodanals == totanal_of(Gkword)) ) {
	fprintf(f,"%s\n",  lemma_of(Anal) );
      }
      Xstrcpy(curlem,lemma_of(Anal));
    }
  }
}

void PrntOneAnalysis(gk_analysis *Gkanal, PrntFlags prntflags, FILE *f)
{
  PrntFlags showlemma;
  gk_string TmpGstr = { 0 };
  char tmp[LONGSTRING];
  char wtmp[LONGSTRING];
  char prntlem[MAXWORDSIZE];
  register char * s;
  int funnyacc = 0;
		

	if (!Gkanal || !pbuf) {
	  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
	  return;
	}
  tmp[0] = 0;
  curan++;

  Xstrncpy(prntlem,lemma_of(Gkanal),MAXWORDSIZE);
  /*
    if( preverb_of(Gkanal)[0] ) 
    funnyacc = build_lemma(prntlem,preverb_of(Gkanal));
    */				

  if( prntflags & SHOW_LEMMA ) {
    if( strcmp(lemma_of(Gkanal),prevlemma)) {
      if( preverb_of(Gkanal)[0] ) {
	if (snprintf(wtmp,sizeof wtmp,"%s\t%s-%s %d\t", rawword_of(Gkanal),
	             preverb_of(Gkanal),lemma_of(Gkanal),curan) >=
	    (int)sizeof wtmp) goto too_long;
      } else {
	if (snprintf(wtmp,sizeof wtmp,"%s\t%s %d\t", rawword_of(Gkanal),
	             lemma_of(Gkanal),curan) >= (int)sizeof wtmp)
	  goto too_long;
      }
      if (!morpheus_runtime_string_append(
	  pbuf,wtmp,print_capacity())) return;
      curan = 0;
      Xstrcpy(wtmp,"\n");
    }
    return;
  }
	
  if( strcmp(lemma_of(Gkanal),prevlemma)) {
				
    if (snprintf(wtmp,sizeof wtmp,"   &from$  %s",prntlem) >=
        (int)sizeof wtmp) goto too_long;
    if (!morpheus_runtime_string_append(tmp,wtmp,sizeof tmp)) goto too_long;
    Xstrncpy(prevlemma,lemma_of(Gkanal),MAXWORDSIZE);
	

    if( preverb_of(Gkanal)[0] /* && funnyacc */) {
      char tmp2[128];
		
      if (snprintf(tmp2,sizeof tmp2," [$%s&+$%s&]",
                   preverb_of(Gkanal),lemma_of(Gkanal)) >=
          (int)sizeof tmp2) goto too_long;
      if (!morpheus_runtime_string_append(tmp,tmp2,sizeof tmp)) goto too_long;
    }
    if (!morpheus_runtime_string_append(tmp,NEWLINE,sizeof tmp)) goto too_long;
  }
	
	
  if( strcmp(workword_of(Gkanal),prevword ) ) {	
    char tmp1[128];
		
    Xstrncpy(	wtmp,"      ",MAXWORDSIZE);
    if( crasis_of(Gkanal)[0] ) {
		
      if (snprintf(tmp1,sizeof tmp1,"$%s& + $",crasis_of(Gkanal)) >=
          (int)sizeof tmp1) goto too_long;
      if (!morpheus_runtime_string_append(wtmp,tmp1,sizeof wtmp)) goto too_long;
    }
    if (snprintf(tmp1,sizeof tmp1,"$%s%s",workword_of(Gkanal),NEWLINE) >=
        (int)sizeof tmp1) goto too_long;
    if (!morpheus_runtime_string_append(wtmp,tmp1,sizeof wtmp) ||
        !morpheus_runtime_string_append(tmp,wtmp,sizeof tmp)) goto too_long;
    Xstrncpy(prevword,workword_of(Gkanal),MAXWORDSIZE);
  }

  odd_morpheme(Gkanal,prvb_gstr_of(Gkanal),"prvb",tmp,0);
  odd_morpheme(Gkanal,aug1_gstr_of(Gkanal),"aug",tmp,0);
  if( strcmp(stem_of(Gkanal),prevstem ) ) {	
    odd_morpheme(Gkanal,stem_gstr_of(Gkanal),"stem",tmp,1);
  } else
    odd_morpheme(Gkanal,stem_gstr_of(Gkanal),"stem",tmp,0);
  odd_morpheme(Gkanal,ends_gstr_of(Gkanal),"end",tmp,0);

  if (!morpheus_runtime_string_append(
      tmp,"         &",sizeof tmp)) goto too_long;
  forminfo_of(&TmpGstr) = forminfo_of(Gkanal);
  dialect_of(&TmpGstr) = dialect_of(Gkanal);
  set_morphflags(&TmpGstr, morphflags_of(Gkanal));
  stemtype_of(&TmpGstr) = stemtype_of(Gkanal);
  set_geogregion(&TmpGstr,geogregion_of(Gkanal));

  SprintGkFlags(&TmpGstr,tmp,sizeof tmp," ",1);

  if (!morpheus_runtime_string_append(tmp,NEWLINE,sizeof tmp)) goto too_long;
  if (!Xstrncat(pbuf,tmp,print_capacity())) goto too_long;
  return;

too_long:
  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
  return;

}

void near_miss(gk_string *gstr, char *checks, int code)
{
/*
fprintf(stdout,"near miss with code %o checks [%s] and [%s]\n", code, checks , gkstring_of(gstr) );
PrntAVerb(gstr,"",stdout);
fputc('\n',stdout);
*/
}


void odd_morpheme(gk_analysis *Gkanal, gk_string *gstr, char *tag, char *bufp, int showflg)
{
  char tmp2[128];
  char mflagbuf[256];
  char result[LONGSTRING];
	
  tmp2[0] = mflagbuf[0] = 0;
  if (!Xstrncpy(result,bufp,sizeof result)) goto too_long;
  MorphNames(morphflags_of(gstr),mflagbuf,sizeof mflagbuf," ",1);

  if( (dialect_of(gstr) /*&& (dialect_of(gstr) != dialect_of(Gkanal))*/) ||
      mflagbuf[0] || showflg ) {
		
    if( ! strcmp(tag,"end") ) {
      if (snprintf(tmp2,sizeof tmp2,"        [&%s $-%s& ",
                   tag,gkstring_of(gstr)) >= (int)sizeof tmp2) goto too_long;
    } else {
      if (snprintf(tmp2,sizeof tmp2,"        [&%s $%s-& ",
                   tag,gkstring_of(gstr)) >= (int)sizeof tmp2) goto too_long;
    }
    if (!morpheus_runtime_string_append(
	result,tmp2,sizeof result)) goto too_long;
    if (dialect_of(gstr)) {
      DialectNames(dialect_of(gstr),tmp2,sizeof tmp2," ");
      if (!morpheus_runtime_string_append(
	  result,tmp2,sizeof result)) goto too_long;
    }
    if(mflagbuf[0] ) {
      if (!morpheus_runtime_string_append(result," ",sizeof result) ||
	  !morpheus_runtime_string_append(
	      result,mflagbuf,sizeof result)) goto too_long;
    }
    if (!morpheus_runtime_string_append(result,"]",sizeof result) ||
	!morpheus_runtime_string_append(
	    result,NEWLINE,sizeof result)) goto too_long;
    Xstrncpy(bufp,result,LONGSTRING);
  }
  return;

too_long:
  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
  return;
}

void dump_all_anals(gk_word *Gkword, PrntFlags prntflags, FILE *fout)
{
  int i = 0;
  int nanals = totanal_of(Gkword);
  int goodanals = 0;
  gk_analysis * Anal;
  char curlem[MAXWORDSIZE];
  int printedwork = 0;
	
  goodanals = GoodAnals(Gkword,0);
  if( (prntflags & PERSEUS_FORMAT ) )
    fprintf(fout,"%s\n", rawword_of(Gkword) );

  for(i=0;i<nanals;i++) {
    Anal = analysis_of(Gkword)+i;
    printedwork = 0;
    /*
      if( ! (prntflags & DBASEFORMAT ) )
      fprintf(fout,":raw\t%s\t%d\n", rawword_of(Anal) , i+1 );
      */
    if( (prntflags & PERSEUS_FORMAT ) ) {
      /*
	if(  strcmp(rawword_of(Anal),workword_of(Anal)) ) {
	char tmp[MAXWORDSIZE];
	
	Xstrcpy(tmp,workword_of(Anal));
	stripquant(tmp);
	
	fprintf(fout,"%s", strcmp(rawword_of(Anal),tmp) ?  tmp : "" );
	if( strcmp(rawword_of(Anal),tmp) ) printedwork = 1;
	}
	*/
      if( !goodanals || (goodanals && (!strchr(lemma_of(Anal),'-'))) ) {
	/*
	  if( strcmp(lemma_of(Anal),curlem) ) 
	  fprintf(fout,"%s\n",printedwork ? "\t" : "", lemma_of(Anal) );
	  */
	DumpPerseusAnalysis(Gkword,prntflags,Anal,fout,i+1);
	Xstrcpy(curlem,lemma_of(Anal));
      }
      continue;
    }
    if( (prntflags & ENDING_INDEX ) ) {
      DumpEndingIndex(Gkword,prntflags,Anal,fout,i+1);
      continue;
    }
    DumpOneAnalysis(Gkword,prntflags,Anal,fout,i+1);
    Xstrncpy(prevlemma,lemma_of(Anal),MAXWORDSIZE);
  }
  if( (prntflags & PERSEUS_FORMAT ) )
    fprintf(fout,"\n");
}

int CompAnals(const void*, const void*);

void SortAnals(gk_analysis *Anal, int nanals)
{
  int i;

  /*
   * The comparator intentionally groups analyses by lemma only.  Preserve
   * discovery order within each lemma so output does not depend on the
   * platform-specific ordering of equal qsort elements.
   */
  for (i = 1; i < nanals; i++) {
    gk_analysis current = Anal[i];
    int j = i;

    while (j > 0 && CompAnals(&current, &Anal[j - 1]) < 0) {
      Anal[j] = Anal[j - 1];
      j--;
    }
    Anal[j] = current;
  }
}

int CompAnals(const void* Anal1, const void* Anal2)
{
  return(strcmp(lemma_of((gk_analysis*)Anal1),lemma_of((gk_analysis*)Anal2)));
}

_Static_assert(sizeof(word_form) <= sizeof(unsigned int),
               "word_form index must fit in unsigned int");

void DumpPerseusAnalysis(
		    gk_word *Gkword,
		    PrntFlags prntflags,
		    gk_analysis *anal,
		    FILE *fout,
		    int cura
		    )
{
  char tmp[LONGSTRING];
  char tmp2[LONGSTRING];
  char workw[LONGSTRING];

  tmp[0] = workw[0] = 0;
	
  fprintf(fout,"<NL>");
  if( Is_participle(anal )) {
    fprintf(fout,"P ");
  }	else if( Is_nounform(anal) || Is_adjform(anal) ) {
    /*
     * grc 11/5/94
     * look for ENGLISH lemmas -- words not in the dict, for which we use the
     * English equivalent.
     * 
     * all Greek is in beta-code and hence lower case or marked with '*'
     *
     * only english words are upper case
     */
    if( isupper((unsigned char)lemma_of(anal)[0]) && cur_lang() == GREEK )
      fprintf(fout,"E ");
    else
      fprintf(fout,"N ");
  }
  else if( Is_verbform(anal) ) {
    fprintf(fout,"V ");
  } else
    fprintf(fout,"I ");

  if(  strcmp(rawword_of(anal),workword_of(anal)) ) {
    char tmp[MAXWORDSIZE];

    Xstrcpy(tmp,workword_of(anal));
    /* grc 2/7/97 -- don't punt the quantity
       stripquant(tmp);
       */
		
    if( strcmp(rawword_of(anal),tmp) )
      fprintf(fout,"%s,",   tmp );
  } 

  fprintf(fout,"%s ", lemma_of(anal) );

  if (prntflags & ENDING_INDEX) {
    unsigned int form_index = 0;

    memcpy(&form_index, &forminfo_of(anal), sizeof forminfo_of(anal));
    fprintf(fout,"\t%u</NL>",form_index);
  }
  else {
    GregSprintGkFlags((gk_string *)anal,tmp,sizeof tmp," "," ",1);
    fprintf(fout,"%s</NL>", tmp );
  }

}

void DumpEndingIndex(gk_word *Gkword, PrntFlags prntflags, gk_analysis *anal, FILE *fout, int cura)
{
  
  char tmp[BUFSIZ];
  
  tmp[0] = 0;
  PrntStemtype(stemtype_of(anal),fout);
  fprintf(fout,"%s ", endstring_of(anal) );
  AddParadigmInfo(tmp,sizeof tmp,forminfo_of(anal),".");
  AddPersNumInfo(tmp,sizeof tmp,forminfo_of(anal),".");
  AddAdjInfo(tmp,sizeof tmp,forminfo_of(anal),".");
  fprintf(fout,"%s %s %d", tmp+1, workword_of(anal), totanal_of(Gkword) );
  if( strcmp(workword_of(anal),rawword_of(anal)))
    fprintf(fout," %s", rawword_of(anal) );
  
  fprintf(fout,"\n");
}

void DumpOneAnalysis(gk_word *Gkword, PrntFlags prntflags, gk_analysis *anal, FILE *fout, int cura)
{
  gk_string EndGstr;
  const word_form empty_form = { 0 };
  char tmp[LONGSTRING];
  char tmp2[LONGSTRING];
  char workw[LONGSTRING];
  
  tmp[0] = workw[0] = 0;
  
  if( prntflags & LEXICON_OUTPUT ) {
    if (snprintf(tmp,sizeof tmp,"%s",rawword_of(anal)) >= (int)sizeof tmp)
      goto too_long;
    if( strcmp( rawword_of(anal), workword_of(anal)) ) {
      if (!Xstrncat(tmp," ",sizeof tmp) ||
          !Xstrncat(tmp,workword_of(anal),sizeof tmp)) goto too_long;
    }
    if (!Xstrncat(tmp," ",sizeof tmp)) goto too_long;
    if(  preverb_of(anal)[0] ) {
      if (!Xstrncat(tmp,preverb_of(anal),sizeof tmp) ||
          !Xstrncat(tmp,"-",sizeof tmp)) goto too_long;
    }
    if (!Xstrncat(tmp,lemma_of(anal),sizeof tmp) ||
        !Xstrncat(tmp,"\t",sizeof tmp)) goto too_long;
    /*
      beta2smarta(tmp,tmp2);
      */
    fprintf(fout,"%s", tmp );
    tmp[0] = 0;	
    /*
      if( ! strcmp(rawword_of(anal),workword_of(anal)) ) 
      fprintf(fout,"\t");
      else
      fprintf(fout,"%s\t", workword_of(anal) );
      */
    /*
      fprintf(fout,"%s\t", part_of_speech(stemtype_of(anal)) );
      */
		
    /*
      Delimiter changed to '\t' by jjake on 04.24.92 in order to turn the
      Parse elements from a set into an (ordered) vector.
      */

    JakeSprintGkFlags((gk_string *)anal,tmp,sizeof tmp," "," ",1);
    
    fprintf(fout,"%s\t", tmp );
    
    fprintf(fout,"%s\t", crasis_of(anal) );
    /*
      if( prntflags != DBASESHORT ) {
      DumpDbGkString(prvb_gstr_of(anal),fout);
      DumpDbGkString(aug1_gstr_of(anal),fout);
      DumpDbGkString(stem_gstr_of(anal),fout);
      DumpDbGkString(suffix_gstr_of(anal),fout);
      DumpDbGkString(ends_gstr_of(anal),fout);
      }
      */
    fprintf(fout,"\n");
    return;
  }
  if( prntflags & DBASEFORMAT ) {
    char tmp[BUFSIZ];
    
    tmp[0] = 0;
    
    
    fprintf(fout,"\n:raw %s\n", rawword_of(anal) );
    fprintf(fout,"\n:workw %s\n", workword_of(anal) );
    fprintf(fout,":lem %s\n", lemma_of(anal) );
    
    fprintf(fout,":prvb "); 
    GregSprintGkFlags(prvb_gstr_of(anal),tmp,sizeof tmp," ", " ", 1);
    fprintf(fout,"%s\t%s\n", gkstring_of(prvb_gstr_of(anal)),tmp );
    tmp[0] = 0;

    fprintf(fout,":aug1 "); 
    GregSprintGkFlags(aug1_gstr_of(anal),tmp,sizeof tmp," ", " ", 1);
    fprintf(fout,"%s\t%s\n", gkstring_of(aug1_gstr_of(anal)),tmp );
    tmp[0] = 0;

    fprintf(fout,":stem "); 
    GregSprintGkFlags(stem_gstr_of(anal),tmp,sizeof tmp," ", " ", 1);
    fprintf(fout,"%s\t%s\n", gkstring_of(stem_gstr_of(anal)),tmp );
    tmp[0] = 0;

    fprintf(fout,":suff "); 
    GregSprintGkFlags(suffix_gstr_of(anal),tmp,sizeof tmp," ", " ", 1);
    fprintf(fout,"%s\t%s\n", gkstring_of(suffix_gstr_of(anal)),tmp );
    tmp[0] = 0;

    fprintf(fout,":end "); 
    GregSprintGkFlags(ends_gstr_of(anal),tmp,sizeof tmp," ", " ", 1);
    fprintf(fout,"%s\t%s\n", gkstring_of(ends_gstr_of(anal)),tmp );
    tmp[0] = 0;

    return;

    fprintf(fout,"%s\t", lemma_of(anal) );
    fprintf(fout,"%s\t", rawword_of(anal) );
    if( ! strcmp(rawword_of(anal),workword_of(anal)) ) 
      fprintf(fout,"\t");
    else
      fprintf(fout,"%s\t", workword_of(anal) );
    /*
      fprintf(fout,"%s\t", part_of_speech(stemtype_of(anal)) );
      */
		
    /*
      Delimiter changed to '\t' by jjake on 04.24.92 in order to turn the
      Parse elements from a set into an (ordered) vector.
      */

    JakeSprintGkFlags((gk_string *)anal,tmp,sizeof tmp,"\t"," ",1);
    fprintf(fout,"%s\t", tmp );
    fprintf(fout,"%s\t", crasis_of(anal) );
    if( (prntflags) != DBASESHORT ) {
      DumpDbGkString(prvb_gstr_of(anal),fout);
      DumpDbGkString(aug1_gstr_of(anal),fout);
      DumpDbGkString(stem_gstr_of(anal),fout);
      DumpDbGkString(suffix_gstr_of(anal),fout);
      DumpDbGkString(ends_gstr_of(anal),fout);
    }
    fprintf(fout,"\n");
    return;
  }
	
  /*
    SprintGkFlags(anal,tmp,sizeof tmp,"\t",1);
    */
  JakeSprintGkFlags((gk_string *)anal,tmp,sizeof tmp," "," ",1);

  if(preverb_of(anal)[0] )	{
    Xstrcpy(workw,preverb_of(anal) );
    if (!Xstrncat(workw,"-",sizeof workw)) goto too_long;
  }
  if(aug1_of(anal)[0] )	{
    if (!Xstrncat(workw,aug1_of(anal),sizeof workw) ||
        !Xstrncat(workw,"-",sizeof workw)) goto too_long;
  }
  fprintf(fout,":summ %d %s %s%s-%s %s %s\n",cura, rawword_of(anal) , workw,
	  stem_of(anal), endstring_of(anal) , lemma_of(anal) , tmp );
  /*
    fprintf(fout,":lemm %s\n", lemma_of(anal) );
    */
  if( preverb_of(anal)[0] ) {
    DumpGstr(":pvb",prvb_gstr_of(anal),fout,(int)(prntflags & PARSE_FORMAT ));
  }
  if(  aug1_of(anal)[0] ) {
    DumpGstr(":aug",aug1_gstr_of(anal),fout,(int)(prntflags & PARSE_FORMAT ));
  }
  if( stem_of(anal)[0] ) {
    DumpGstr(":stem",stem_gstr_of(anal),fout,(int)(prntflags & PARSE_FORMAT ));
  }
  if( endstring_of(anal)[0] ) {
    EndGstr = *(ends_gstr_of(anal));
    forminfo_of(&EndGstr) = empty_form;
	
    DumpGstr(":end",&EndGstr,fout,(int)(prntflags & PARSE_FORMAT ));
  }
  if( crasis_of(anal)[0] ) {
    fprintf(fout,":crasis %s\n", crasis_of(anal) );
  }
  fprintf(fout,"\n");
  return;

too_long:
  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
  return;
}

void DumpGstr(char *tags, gk_string *gstr, FILE *fout, int fullrec)
{
  char tmp[LONGSTRING];
	
  tmp[0] = 0;
	
  fprintf(fout,"%s\t%s\t", tags , gkstring_of(gstr) );
  SprintGkFlags(gstr,tmp,sizeof tmp,"\t",1);
  if( fullrec ) {
    char *s = tmp;
    while(*s) {
      if(isspace((unsigned char)*s)) {
	fprintf(fout," ");
	while(isspace((unsigned char)*s)) s++;
	continue;
      } else
	fprintf(fout,"%c", *s++);
    }
    fprintf(fout,"\n");
  } else
    fprintf(fout,"%s\n", tmp );
}

void DumpDbGkString(gk_string *gstr, FILE *fout)
{
	char tmp[LONGSTRING];
	tmp[0] = 0;
	fprintf(fout,"%s", gkstring_of(gstr) );
	SprintGkFlags(gstr,tmp,sizeof tmp,"\t",1);
	fprintf(fout,"%s\t", tmp );
}
