#include "anal_internal.h"
#include "../morphlib/runtime_context_internal.h"

#include "checkstem.proto.h"
int comstemtypes(char *, char *, char *);
static int wantcurstemtype(char *, char *);
extern int verbose;

static int
valid_checkstem_argument(const void *argument)
{
	if (argument) return(1);
	morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
	return(0);
}

/*
 * this routine takes a possible verb stem (poss_stem) and tries
 * to figure out whether any such stem exists. 
 *
 * it is smart enough to de-augment a stem, and stores up a 
 * a variety of possible stems in *stemtab[].
 *
 * it also uses the stem types listed in endkeys to get rid of
 * extraneous hits. thus if a previous routine has found an ending
 * that fits onto "ew_pr", "ow_pr" and "ew_fut" stems, we first check to
 * make sure that a stem falls into one of these three categories, and
 * then get rid of extraneous possibilities. thus if the stem is
 * only "ew_fut", we don't have to worry about "ew_pr" or "ow_pr" forms.
 * 
 * the resulting keys for each possible stem are stored in *keytab[]
 */

static int
initialize_augmented_stems(morpheus_runtime_context *context)
{
	int i;

	if (context->analysis_augmented_stems_initialized) return(1);
	for (i = 0; i < MORPHEUS_AUGMENT_STEM_COUNT; i++) {
		if (!context->analysis_augmented_stems[i])
			context->analysis_augmented_stems[i] = CreatGkString(1);
		if (!context->analysis_augmented_quantities[i])
			context->analysis_augmented_quantities[i] = CreatGkString(1);
		if (!context->analysis_augmented_stems[i] ||
		    !context->analysis_augmented_quantities[i])
			goto no_memory;
	}
	context->analysis_augmented_stems_initialized = 1;
	return(1);

no_memory:
	for (i = 0; i < MORPHEUS_AUGMENT_STEM_COUNT; i++) {
		if (context->analysis_augmented_stems[i])
			FreeGkString(context->analysis_augmented_stems[i]);
		if (context->analysis_augmented_quantities[i])
			FreeGkString(context->analysis_augmented_quantities[i]);
		context->analysis_augmented_stems[i] = NULL;
		context->analysis_augmented_quantities[i] = NULL;
	}
	morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
	return(0);
}

int checkstem(char *poss_stem, char *endkeys, gk_string *stemtab[], char *keytab[], int maxstems)
{
	char *curstemkeys;
	int i;
	int hits = 0;
	int poss_augs = 0;
	int possno = 0;
	int rval = 0;
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	gk_string **tstemtab = context->analysis_augmented_stems;
	gk_string **tqstemtab = context->analysis_augmented_quantities;

	if (!valid_checkstem_argument(poss_stem) ||
	    !valid_checkstem_argument(endkeys) ||
	    !valid_checkstem_argument(stemtab) ||
	    !valid_checkstem_argument(keytab) || maxstems <= 0) {
		if (maxstems <= 0)
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	for (i = 0; i < maxstems; i++) {
		if (!valid_checkstem_argument(stemtab[i]) ||
		    !valid_checkstem_argument(keytab[i]))
			return(0);
	}



	curstemkeys = (char *)malloc((size_t)LONGSTRING+1);
	if (!curstemkeys || !initialize_augmented_stems(context)) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		free(curstemkeys);
		return(0);
	}
	for(i=0;i<MORPHEUS_AUGMENT_STEM_COUNT;i++) {
		ClearGkstring(tstemtab[i]);
		ClearGkstring(tqstemtab[i]);
	}
	
	*curstemkeys = 0;
	rval = stemexists(poss_stem,endkeys,curstemkeys,0);
/*
morpheus_runtime_diagnostic("rval %d poss stem [%s] endkeys {%s] curstem [%s]\n", rval, poss_stem,endkeys,curstemkeys);
*/

	if( rval ) {

		if( curstemkeys[0] && possno < maxstems ) {
			set_gkstring(stemtab[possno],poss_stem);
			Xstrncpy((char *)keytab[possno],(char *)curstemkeys,(size_t)LONGSTRING);
			curstemkeys[0] = 0;
			possno++;
			hits++;
		}
	}

/*
 * if it starts with a consonant, forget it.
 * if it starts with a vowel, see if you can find anything by looking
 * for unaugmented forms
 */
	if( Is_cons( *poss_stem ) )
		goto finish;


	poss_augs = unaugment(poss_stem,tstemtab,tqstemtab,
		MORPHEUS_AUGMENT_STEM_COUNT,ALL_DIAL,1,0);

	for(i=0;i<poss_augs;i++) {

/*
morpheus_runtime_diagnostic("%d) %s\n", i , gkstring_of(tstemtab[i]) );
*/

		*curstemkeys = 0;
		if( stemexists(gkstring_of(tstemtab[i]),endkeys,curstemkeys,0) ) {
			if( curstemkeys[0] && hits < maxstems ) {
				*stemtab[hits] = *tstemtab[i];
				Xstrncpy((char *)keytab[hits],(char *)curstemkeys,(size_t)LONGSTRING);
				hits++;
			}
		}

	}

	finish:

	xFree(curstemkeys,"curstemkeys");
	curstemkeys = NULL;
	return(hits);
}

int stemexists(char *s, char *endkeys, char *stemkeys, int is_nom)
{
	int rval  = 0;

	if (!valid_checkstem_argument(s) ||
	    !valid_checkstem_argument(endkeys) ||
	    !valid_checkstem_argument(stemkeys))
		return(0);
	
/*
morpheus_runtime_diagnostic("stemexists: s [%s] stemkeys [%s] endkeys [%s]\n", s , stemkeys, endkeys);
*/
	rval = chckstem(s,stemkeys,is_nom);
/*
if( rval ) printf("rval %d for [%s] with keys [%s]\n", rval , s , stemkeys );
*/
	if( ! rval ) return(0);

	rval = comstemtypes(s,stemkeys,endkeys);
/*morpheus_runtime_diagnostic("endkeys [%s] rval after comstemtypes is %d\n", endkeys, rval );*/
	return(rval);
}


/*
 * ok, here we are with a list of stems to which the current ending
 * could be appended, and a list of stemtypes (and lemmas) to which 
 * our current stem could belong. the two lists look like
 *   endkeys = "ew_pr  ew_fut ow_pr"
 *   stemkeys = "ew_fut:ba/llw aor2:ba/llw"
 *
 * now we want to get those stem types common to both lists  and
 * return with only "ew_fut:ba/llw" in the above example.
 */

int
comstemtypes(char *stem, char *stemkeys, char *endkeys)
{
	register char * s, *p;
	char tmp[LONGSTRING];
	char cstemtype[LONGSTRING];
	char cstem[MAXWORDSIZE];
	char clemma[MAXWORDSIZE];
	char stembuf[LONGSTRING];
	
	s = stemkeys;
	p = tmp;
	
	stembuf[0] = tmp[0] = 0;
	while(*s) {
		setstemvars(s,cstem,clemma,cstemtype,stembuf);

		if( wantcurstemtype(cstemtype,endkeys) ) {
			if ((tmp[0] && !morpheus_runtime_string_append(
			        tmp," ",sizeof tmp)) ||
			    !morpheus_runtime_string_append(tmp,clemma,sizeof tmp) ||
			    !morpheus_runtime_string_append(tmp,":",sizeof tmp) ||
			    !morpheus_runtime_string_append(
			        tmp,cstem[0] ? cstem : stem,sizeof tmp) ||
			    !morpheus_runtime_string_append(tmp,":",sizeof tmp) ||
			    !morpheus_runtime_string_append(
			        tmp,cstemtype,sizeof tmp) ||
			    !morpheus_runtime_string_append(tmp,":",sizeof tmp) ||
			    (*stembuf && !morpheus_runtime_string_append(
			        tmp,stembuf,sizeof tmp))) return(0);
		}
		while(! isspace((unsigned char)*s) && *s ) s++;
		while( isspace((unsigned char)*s) ) s++;
	}
	Xstrncpy((char *)stemkeys,(char *)p,(size_t)LONGSTRING);

	if( *stemkeys )
		return(1);
	else
		return(0);
}

static int wantcurstemtype(char *curst, char *stlist)
{
	char *s;
	int rval = 0;
	
	s = is_substring(curst,stlist);
	if( s != NULL ) rval = 1;
	
	return( rval );
}


void setstemvars(char *s, char *cstem, char *clemma, char *cstemtype, char *cstemkeys)
{
	*cstemkeys = *cstem = *clemma = *cstemtype = 0;
	
	s = parsefield(s,cstem,':',MAXWORDSIZE);
	s = parsefield(s,clemma,':',MAXWORDSIZE);
	s = parsefield(s,cstemtype,':',MAXWORDSIZE);
	s = parsefield(s,cstemkeys,' ',LONGSTRING);
}

char *
parsefield(char *s, char *buf, int c, int len)
{
	int i;
	
	*buf = 0;
/*
	while(*s&&*s!=c&&!isspace((unsigned char)*s)) *buf++ = *s++;
*/
	for(i=0;*s&&*s!=c&&!isspace((unsigned char)*s);i++) {
		*buf++ = *s++;
		if( i >= len ) {
			morpheus_runtime_diagnostic("Hey %d chars; %zu s [%s] left!\n", len , Xstrlen(s) ,s );
			*buf = 0;
			while(*s&&!isspace((unsigned char)*s)) s++;
			break;
		}
	}
	
	*buf = 0;
	if( isspace((unsigned char)*s) ) return("");
	if(*s) s++;
	return(s);
}

void longeststem(char *s)
{
	char * p = s;
	char tmp[256],tmp2[256];
	char stemkeys[1024];
	int rval = 0;
	
	Xstrcpy(tmp,s);
	stemkeys[0] = 0;
	p = tmp;
	
	while(*p) p++; p--;
	while(p>=tmp) {
		Xstrcpy(tmp2,p);
		*p = 0;
		if( (rval += chckstem(tmp,stemkeys,1)) ) {
			printf("%s-%s\tn\t%s\n", tmp, tmp2, stemkeys );
		}
		if( chckstem(tmp,stemkeys,0) )  {
			printf("%s-%s\tv\t%s\n", tmp, tmp2, stemkeys );
			break;
		}
		if( rval ) break;
		p--;

	}
	
}
