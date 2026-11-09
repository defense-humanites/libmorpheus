#include "morphlib_internal.h"
#include <contract.h>

#include "preverb3.proto.h"

static int ensure_preverb_table(void)
{
  morpheus_runtime_context *context = morpheus_runtime_context_current();

  if (context->raw_preverb_table &&
      context->raw_preverb_language == cur_lang())
    return(1);

  if (context->raw_preverb_table) {
    FreeGkString(context->raw_preverb_table);
    context->raw_preverb_table = NULL;
    context->raw_preverb_count = 0;
  }

  context->raw_preverb_table =
    load_euph_tab(RAWPBLIST,&context->raw_preverb_count,NO);
  if (!context->raw_preverb_table) {
    fprintf(stderr,"Could not create preverb table!\n");
    return(0);
  }
  context->raw_preverb_language = cur_lang();
  return(1);
}

static int valid_preverb_argument(const void *argument)
{
  if (argument) return(1);
  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
  return(0);
}

int nextpreverb(char *word, char *oldprevb, char *pblemma, gk_string *gstr)
{
  morpheus_runtime_context *context = morpheus_runtime_context_current();
  gk_string *prevb_table;
  int numprevb;
  int i = 0;

  if (!valid_preverb_argument(word) ||
      !valid_preverb_argument(oldprevb) ||
      !valid_preverb_argument(pblemma) ||
      !valid_preverb_argument(gstr))
    return(0);
  if (!ensure_preverb_table()) return(0);
  prevb_table = context->raw_preverb_table;
  numprevb = context->raw_preverb_count;

  for ( i = 0; i < numprevb; i++) {
    if ( !*oldprevb )
      break;
    if ( has_rawpreverb(oldprevb, prevb_table+i) ) {
      i++;
      break;
    }
  }
  
  
  for (; i < numprevb ; i++) {
    /*
       if (! Xstrncmp(prevbtab[i].rawstring,word,Xstrlen(prevbtab[i].rawstring))) {
       */
    if( has_rawpreverb(word,prevb_table+i) ) {
      
      char tmp[MAXWORDSIZE];
      
      Xstrncpy(oldprevb,gkstring_of(prevb_table+i),MAXWORDSIZE);
      Xstrncpy(pblemma,gkstring_of(prevb_table+i)+MAXSUBSTRING,MAXWORDSIZE);
      Xstrncpy(tmp,word+Xstrlen(gkstring_of(prevb_table+i)) ,MAXWORDSIZE);
      Xstrncpy(word,tmp,MAXWORDSIZE);
      
      /*
       * if no *pbflags set, then accept anything. otherwise, make sure that
       * you have an overlap
       */
      /*
       * grc 6/27/89
       *
       * that will not work--if you have a)podi-, then a)po- with its flag "raw_preverb" will
       * not match "di" which is not a raw_preverb.
       */
      
      if( ! no_morphflag(morphflags_of(gstr)) &&  
	 overlap_morphflags(morphflags_of(gstr) ,morphflags_of(prevb_table+i))
	 &&  has_morphflag(morphflags_of(gstr),RAW_PREVERB) )
	continue;
      
      add_morphflags(gstr,morphflags_of(prevb_table+i));
      if( dialect_of(prevb_table+i) ) {
	dialect_of(gstr) = dialect_of(prevb_table+i);
      }
      
      /*
	 add_dialect(gstr,dialect_of(PrevbTable+i));
	 if( prevbtab[i].pbflags ) {
	 int j;
	 
	 for(j=0;j<3;j++)
	 add_morphflag(pbflags , (prevbtab[i].pbflags)[j] );
	 }
	 */
      return (1);
    }
  }
  
  return(0);
}

int has_rawpreverb(char *curpb, gk_string *pbentry)
{
  const char *raw;

  if (!valid_preverb_argument(curpb) ||
      !valid_preverb_argument(pbentry))
    return(0);
  raw = gkstring_of(pbentry);
  /*
   * nextpreverb() tries every raw preverb against the word: a non-empty
   * preverb whose first byte differs cannot match, so skip the comparison.
   */
  if (raw[0] && raw[0] != curpb[0])
    return(0);
  return(!Xstrncmp(curpb,raw,Xstrlen(raw)));
}

int is_rawpreverb(char *s)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	int i;

	if (!valid_preverb_argument(s)) return(0);
	if (!ensure_preverb_table()) return(0);
	for ( i = 0; i < context->raw_preverb_count; i++) {
		if(!strcmp(s,gkstring_of(context->raw_preverb_table+i)))
			return(1);
	}
	return(0);
}
