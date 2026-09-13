#include "morphlib_internal.h"
#include <errno.h>
#include <limits.h>
/*
 * copyright Gregory Crane
 *
 * February 1987
 */

#include "morphkeys.h"
#include <stdlib.h>
#include <string.h>
#include "../greeklib/xstrings.proto.h"
#include "gkstring.proto.h"
#ifdef LIGHTSPEED

/*
 char * p_eq_morph_keys();
*/
#else

/*
static char * NextEndTable();
static char * p_eq_morph_keys();
*/

#endif
Stemtype GetStemClass(char * );
Stemtype GetIsProse(char *);

static void RearrangeMorphflags(gk_word *, gk_string *);
static int GetGkFlag(char *, gk_string *, char *, char *, char *);
static char *p_eq_morph_keys(long, const Morph_args *);
static void clear_morph_key_state(morpheus_runtime_context *);
static int next_table_field(const char **, char *, size_t);
#define KEY_CONTEXT (morpheus_runtime_context_current())
#define keys_inited (KEY_CONTEXT->morph_keys_initialized && \
	KEY_CONTEXT->morph_key_language == cur_lang())
#define nstems (KEY_CONTEXT->morph_key_stem_count)
#define nderivs (KEY_CONTEXT->morph_key_derivation_count)
#define ndomains (KEY_CONTEXT->morph_key_domain_count)
#define nkeys (KEY_CONTEXT->morph_key_count)
#define key_table (KEY_CONTEXT->morph_key_table)
#define arg_stemtype (KEY_CONTEXT->stem_type_arguments)
#define arg_derivtype (KEY_CONTEXT->derivation_type_arguments)
#define arg_domain (KEY_CONTEXT->domain_arguments)
/*int keycomp1(Morph_args **, Morph_args **);*/
int keycomp1(const void *, const void *);

 int ScanAsciiKeys(char *s, gk_word *Gkword, gk_string *want, gk_string *avoid)
{
	char savekeys[LONGSTRING];
	char curkey[LONGSTRING];
	gk_string * gstr = want;
	char * preverb;
	char * lemma;
	
	if( ! s || ! Gkword || ! want ) {
		fprintf(stderr,"Hey! null workspace in scanasciikeys!\n");
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	} else {
		preverb = preverb_of(Gkword);
		lemma = lemma_of(Gkword);
	}
	if( oddkeys_of(Gkword) )
		oddkeys_of(Gkword)[0] = 0;
	Xstrncpy((char *)savekeys,(const char *)s,(size_t)LONGSTRING);

	while(nextkey(savekeys,curkey)) {
		if( ! strcmp( "not" , curkey )  ) {
			if( avoid ) {
				gstr = avoid;
			} else /* if no place to store the stuff to be avoided, just quit */
				break;
/* 
			  else {
			 	fprintf(stderr,"hey: got a negation in [%s], but no place to put it!\n", savekeys);
				return;
			}
*/
			continue;
		}

		if( ! strcmp( "crasis" , curkey ) ) {
			nextkey(savekeys,curkey);
			set_crasis(Gkword,curkey);
/*			
printf("crasis now set to [%s]\n", crasis_of(Gkword) );
*/
			continue;
		}

	
	if( ! strcmp(curkey,"pb") ) {
		nextkey(savekeys,curkey);
		if( preverb ) {
		    Xstrncpy(preverb,curkey,MAXWORDSIZE);
		    zap_morphflag(morphflags_of(gstr),ROOT_PREVERB);
		    add_morphflag(morphflags_of(gstr),HAS_PREVERB);
		}
		continue;
	}

	if( ! strcmp(curkey,"rpb") ) {
		nextkey(savekeys,curkey);
		if( preverb ) {
		    Xstrncpy(preverb,curkey,MAXWORDSIZE);
		    zap_morphflag(morphflags_of(gstr),HAS_PREVERB);
		    add_morphflag(morphflags_of(gstr),ROOT_PREVERB);
		}
		continue;
	}

		if( ! GetGkFlag(curkey,gstr,endstring_of(Gkword),preverb,lemma) ) {
		/*
			fprintf(stderr,"could not match key [%s] in [%s]\n", curkey , s);
		*/
			if( Gkword ) {
				if( ! oddkeys_of(Gkword) ) {
					char *oddkeys = (char *)malloc(LONGSTRING+1);

					if (!oddkeys) {
						morpheus_runtime_error_record(
							MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
						return(0);
					}
					oddkeys[0] = 0;
					oddkeys_of(Gkword) = oddkeys;
				}
				if(*oddkeys_of(Gkword))
					Xstrncat(oddkeys_of(Gkword)," ",LONGSTRING);
				Xstrncat(oddkeys_of(Gkword),curkey,LONGSTRING);
			}
		}
	}

	if( preverb_of(Gkword)[0] ) {

		if(  has_morphflag(morphflags_of(gstr),ROOT_PREVERB)) {
			add_morphflag(morphflags_of(Gkword),ROOT_PREVERB);
			add_morphflag(morphflags_of(stem_gstr_of(Gkword)),ROOT_PREVERB);
			zap_morphflag(morphflags_of(Gkword),HAS_PREVERB);
			zap_morphflag(morphflags_of(gstr),HAS_PREVERB);
			zap_morphflag(morphflags_of(stem_gstr_of(Gkword)),HAS_PREVERB);
		} else {
			zap_morphflag(morphflags_of(Gkword),ROOT_PREVERB);
			zap_morphflag(morphflags_of(stem_gstr_of(Gkword)),ROOT_PREVERB);
			add_morphflag(morphflags_of(Gkword),HAS_PREVERB);
			add_morphflag(morphflags_of(stem_gstr_of(Gkword)),HAS_PREVERB);
		}
	}

	if( Gkword )
		RearrangeMorphflags(Gkword,want);
	if( stemtype_of(want) == 0 ) 
		return(0);
	else
		return(1);
}

static 
void RearrangeMorphflags(gk_word *Gkword, gk_string *gstr)
{
	xfer_prvbflags(morphflags_of(Gkword),morphflags_of(prvb_gstr_of(Gkword)));
	xfer_prvbflags(morphflags_of(gstr),morphflags_of(prvb_gstr_of(Gkword)));
}

static
 int GetGkFlag(char *field, gk_string *gstr, char *endstring, char *preverb, char *lemma)
{
	
 	if( ! keys_inited && !init_keys() )
 		return(0);

	if( AddMorphKey(gstr,field) ) 
		return(1);

/*
 * note that if you try to stick both an ending and a preverb into
 * the same gk_string, the second one in will overwrite the first.
 * 
 * we assume that you will have endstrings with endings and preverbs with
 * stems. if not ....
 */
	if( ! Xstrncmp(field,"end:",4) ) {
		Xstrncpy(endstring,field+4,MAXWORDSIZE);
/*
		set_gkstring(gstr,field+4);
*/
		return(1);
	}

	if( ! Xstrncmp(field,"pb:",Xstrlen("pb:")) ) {
		if( preverb ) {
		    Xstrncpy(preverb,field+3,MAXWORDSIZE);
		    zap_morphflag(morphflags_of(gstr),ROOT_PREVERB);
		    add_morphflag(morphflags_of(gstr),HAS_PREVERB);
		} /* else {
		    fprintf(stderr,"got handed prevb %s but had no place to put it!\n", field+3);
		}*/
		return(1);
	}

	if( ! Xstrncmp(field,"rpb:",Xstrlen("rpb:")) ) {
		if( preverb ) {
		    Xstrncpy(preverb,field+4,MAXWORDSIZE);
		    zap_morphflag(morphflags_of(gstr),HAS_PREVERB);
		    add_morphflag(morphflags_of(gstr),ROOT_PREVERB);

		} /* else {
		    fprintf(stderr,"got handed prevb %s but had no place to put it!\n", field+3);
		}*/
		return(1);
	}

	if( ! Xstrncmp(field,"le:",Xstrlen("le:")) ) {
		if( ! lemma ) {
		    fprintf(stderr,"got handed lemma %s but had no place to put it!\n", field+3);
		} else {
			Xstrncpy(lemma,field+3,MAXWORDSIZE);
		}
		return(1);
	}
	return(0);
}

char * 
 NextEndTable(int *index, Stemtype mask)
{
	Morph_args *morph_args;
	
	mask &= (PPARTMASK|ADJSTEM|NOUNSTEM);
 
 	if( ! keys_inited && !init_keys() )
 		return(NULL);
	morph_args = arg_stemtype + *index;
 		
 	while( morph_args->morph_key[0] ) {
		if( ! mask ) {
			(*index)++;
if( mask )
printf("0 mask returns [%s]\n", morph_args->morph_key );
			return(morph_args->morph_key);
		} else if( ( (long)mask & morph_args->morph_flags ) ) {
/*
printf("mask of [%o] on [%lo] returns [%s]\n", mask , morph_args->morph_flags , morph_args->morph_key );
*/
			(*index)++;
			return(morph_args->morph_key);
		}
/*
printf("stype [%o] fails on [%s]\n", mask , morph_args->morph_key );
*/
		(*index)++;
		morph_args++;
	}
	return(NULL);

}

char *
 NameOfDerivtype(Derivtype st)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)st,arg_derivtype) );
}


char *
 NameOfStemtype(Stemtype st)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)st,arg_stemtype) );
}

/*
char * 
  part_of_speech(st)
    Stemtype st;
{
	 	if( ! keys_inited )
 		init_keys();
 		
 		if( 

}
*/

char *
 NameOfDomain(Stemtype st)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)st,arg_domain) );
}

char *
 NameOfPerson(word_form vf)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)person_of(vf),arg_person) );
}

char *
 NameOfNumber(word_form vf)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)number_of(vf),arg_number) );
}

char *
 NameOfTense(word_form vf)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)tense_of(vf),arg_tense) );
}

char *
 NameOfMood(word_form vf)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)mood_of(vf),arg_mood) );
}

char *
 NameOfVoice(word_form vf)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)voice_of(vf),arg_voice) );
}


char *
 NameOfDialect(Dialect di)
{
	 if( ! keys_inited && !init_keys() )
		return("");
 		
	return( p_eq_morph_keys((long)di,arg_dialect) );
}


int DomainNames(char *domp, char *res, size_t capacity, const char *dels)
{
	char * p;

	if (!domp || !res || !capacity || !dels) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	p = domp;
	*res = 0;
	
	while(*p) {
		if((*res && !Xstrncat(res,dels,capacity)) ||
		   !Xstrncat(res,NameOfDomain((Stemtype)*p),capacity)) {
			*res = 0;
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			return(0);
		}
		p++;
	}
	return(1);
}
  
 int DialectNames(Dialect di, char *res, size_t capacity, const char *dels)
{
	char * s;
	int i;
	Dialect mask = 1;
	Dialect sofar = 0;
	Morph_flags mf;
	const Morph_args *morph_args;
	
	morph_args = arg_dialect;
	
	if (!res || !capacity || !dels) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	*res = 0;
	if( ! di )
		return(1);
	mf = (Morph_flags)di;

	while( morph_args->morph_key[0] ) {
		if( morph_args->morph_flags && 
		   ( (mf & morph_args->morph_flags) == morph_args->morph_flags ) ) {

			if((*res && !Xstrncat(res,dels,capacity)) ||
			   !Xstrncat(res,morph_args->morph_key,capacity)) {
				*res = 0;
				morpheus_runtime_error_record(
				    MORPHEUS_RUNTIME_ERROR_INTERNAL);
				return(0);
			}
			mf &= ~(morph_args->morph_flags);
		}
		morph_args++;
	}
	return(1);
}

 int GeogRegionNames(GeogRegion gr, char *res, size_t capacity,
                     const char *dels)
{
	char * s;
	int i;
	GeogRegion mask = 1;
	GeogRegion sofar = 0;
	Morph_flags mf;
	const Morph_args *morph_args;
	
	morph_args = arg_geogregion;
	
	if (!res || !capacity || !dels) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	*res = 0;
	if( ! gr )
		return(1);
	mf = (Morph_flags)gr;

	while( morph_args->morph_key[0] ) {
		if( morph_args->morph_flags && ( (mf & morph_args->morph_flags) == morph_args->morph_flags ) ) {
			if((*res && !Xstrncat(res,dels,capacity)) ||
			   !Xstrncat(res,morph_args->morph_key,capacity)) {
				*res = 0;
				morpheus_runtime_error_record(
				    MORPHEUS_RUNTIME_ERROR_INTERNAL);
				return(0);
			}
			mf &= ~(morph_args->morph_flags);
		}
		morph_args++;
	}
	return(1);
}

char *
 NameOfGender(word_form af)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)gender_of(af),arg_gender) );
}

char *
 NameOfCase(word_form af)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)case_of(af),arg_case) );
}

char *
 NameOfDegree(word_form wf)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys((long)degree_of(wf),arg_degree) );
}

 
char * 
 NameOfMorphFlags(long mf)
{
 	if( ! keys_inited && !init_keys() )
 		return("");
 		
	return( p_eq_morph_keys(mf,arg_morphflags) );
	
}


const Morph_args *
MatchMorphKey(char *field)
{		
	int rval;
	
	if( ! keys_inited && !init_keys() )
		return(NULL);

	rval=binlook( (char *)key_table , field , nkeys , (int)sizeof * key_table , 1 ,  keycomp2);
	if( rval < 0 ) {

		return(NULL);
	}
	return(*(key_table+rval));
}

Stemtype
GetStemNum(char *field)
{
	const Morph_args *mp;
	
	mp = MatchMorphKey(field);
	if( ! mp )
		return((Stemtype)0);
	return((Stemtype)(mp->morph_flags));
}

static char *
 p_eq_morph_keys(long flag, const Morph_args *morph_args)
{
	if( ! flag )
		return("");
	while( morph_args->morph_key[0] ) {
		if(flag == morph_args->morph_flags) {
			return((char *)morph_args->morph_key);
		}
		morph_args++;
	}
	return("");
}
Morph_args * 
InitStemSuffs(char *fname, void (*curfunc)(gk_string *, unsigned long),
              Stemtype (*classfunc)(char *), int *snum)
{
	FILE *f = NULL;
	int i;
	int count = 0;
	char line[LONGSTRING];
	Stemtype stemnum = 0;
	Stemtype declnum = 0;
	char stemname[MAXWORDSIZE];
	char stemnumber[MAXWORDSIZE];
	char decl[MAXWORDSIZE];
	char extra[MAXWORDSIZE];
	Morph_args * targs = NULL;

	if (!fname || !curfunc || !classfunc || !snum) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	*snum = 0;
	if( (f=MorphFopen(fname,"r")) == NULL ) {
		fprintf(stderr,"could not open [%s]\n", fname );
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	
	while(GetTableLine(line,(int)sizeof line,f)) {
		if (count == INT_MAX) {
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			goto failed;
		}
		count++;
	}
	if (ferror(f) || fseek(f,0L,SEEK_SET) != 0) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		goto failed;
	}
	
	targs = (Morph_args *) calloc((size_t)count+1,sizeof * targs);
	if(!targs) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		goto failed;
	}

	for(i=0;GetTableLine(line,(int)sizeof line, f);i++) {
		char *end;
		const char *cursor = line;
		long parsed;
		int base;

		if (i >= count ||
		    next_table_field(&cursor,stemname,sizeof stemname) != 1 ||
		    next_table_field(&cursor,stemnumber,sizeof stemnumber) != 1 ||
		    next_table_field(&cursor,decl,sizeof decl) != 1 ||
		    next_table_field(&cursor,extra,sizeof extra) != 0) {
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			goto failed;
		}
		declnum = stemnum = 0;
		base = stemnumber[0] == '0' ? 8 : 10;
		errno = 0;
		parsed = strtol(stemnumber,&end,base);
		if (errno || *end || parsed < INT_MIN || parsed > INT_MAX) {
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			goto failed;
		}
		stemnum = (Stemtype)parsed;
		Xstrncpy(targs[i].morph_key , stemname,(size_t)MAXWORDSIZE);
		declnum = (*classfunc)(decl);
		

/*		if( declnum == 0 ) { 
			fprintf(stdout,"could not recognize [%s]\n", decl );
			targs[i].morph_flags = (stemnum );
		} else */
			targs[i].morph_flags = (stemnum | declnum);
		targs[i].add_val = curfunc;

/*
		printf("name [%s] num [%o] declnum [%o] decl [%s]\n", stemname , stemnum, declnum, decl);
		printf("morphflags %lo\n", targs[i].morph_flags );
*/
	}
	if (ferror(f) || i != count) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		goto failed;
	}
	xFclose(f);
	*snum = count;
	return(targs);

failed:
	if (f) xFclose(f);
	free(targs);
	return(NULL);
}

static int
next_table_field(const char **cursor, char *field, size_t field_size)
{
	const char *s;
	size_t length = 0;

	if (!cursor || !*cursor || !field || !field_size)
		return(-1);
	s = *cursor;
	while (isspace((unsigned char)*s)) s++;
	if (!*s) {
		field[0] = 0;
		*cursor = s;
		return(0);
	}
	while (*s && !isspace((unsigned char)*s)) {
		if (length+1 >= field_size)
			return(-1);
		field[length++] = *s++;
	}
	field[length] = 0;
	*cursor = s;
	return(1);
}


int init_stems(void)
{
	arg_stemtype = InitStemSuffs(STEMTYPES,new_stemtype,GetStemClass,&nstems);
	if(!arg_stemtype) return(0);
	arg_derivtype = InitStemSuffs(DERIVTYPES,new_derivtype,GetStemClass,&nderivs);
	if(!arg_derivtype) return(0);
	arg_domain = InitStemSuffs(DOMAINLIST,new_domain,GetIsProse,&ndomains);
	return(arg_domain != NULL);
}
	
	
int has_octal(char *s)
{
	while(*s&& !isspace((unsigned char)*s)) s++;
	while(isspace((unsigned char)*s)) s++;
	if(*s == '0' ) return(1);
	return(0);
}

static void
clear_morph_key_state(morpheus_runtime_context *context)
{
	free(context->morph_key_table);
	free(context->stem_type_arguments);
	free(context->derivation_type_arguments);
	free(context->domain_arguments);
	context->morph_key_table = NULL;
	context->stem_type_arguments = NULL;
	context->derivation_type_arguments = NULL;
	context->domain_arguments = NULL;
	context->morph_key_stem_count = 0;
	context->morph_key_derivation_count = 0;
	context->morph_key_domain_count = 0;
	context->morph_key_count = 0;
	context->morph_keys_initialized = 0;
}

int init_keys(void)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	size_t key_count;
	size_t sofar = 0;

	clear_morph_key_state(context);
	if(!init_stems()) {
		clear_morph_key_state(context);
		return(0);
	}
	if (nstems < 0 || nderivs < 0 || ndomains < 0) {
		fprintf(stderr,"invalid negative morphology key count\n");
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		clear_morph_key_state(context);
		return(0);
	}
	key_count = (size_t)nstems + (size_t)nderivs + (size_t)ndomains
		 + LENGTH_OF(arg_degree)
		 + LENGTH_OF(arg_person)
		 + LENGTH_OF(arg_morphflags)
		 + LENGTH_OF(arg_gender)
		 + LENGTH_OF(arg_case)
		 + LENGTH_OF(arg_number)
		 + LENGTH_OF(arg_tense)
		 + LENGTH_OF(arg_voice)
		 + LENGTH_OF(arg_mood)
		 + LENGTH_OF(arg_dialect)
		 + LENGTH_OF(arg_geogregion);
	if (key_count > (size_t)INT_MAX) {
		fprintf(stderr,"morphology key count exceeds the runtime index width\n");
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		clear_morph_key_state(context);
		return(0);
	}
	nkeys = (int)key_count;
	key_table = (const Morph_args **) calloc(key_count+1,sizeof * key_table );
	if (!key_table) {
		fprintf(stderr,"could not allocate morphology key index\n");
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		clear_morph_key_state(context);
		return(0);
	}
	
	sofar += add_keyarr(key_table+sofar,arg_stemtype);
	sofar += add_keyarr(key_table+sofar,arg_derivtype);
	sofar += add_keyarr(key_table+sofar,arg_domain);
	sofar += add_keyarr(key_table+sofar,arg_degree);
	sofar += add_keyarr(key_table+sofar,arg_person);
	sofar += add_keyarr(key_table+sofar,arg_gender);
	sofar += add_keyarr(key_table+sofar,arg_case);
	sofar += add_keyarr(key_table+sofar,arg_number);
	sofar += add_keyarr(key_table+sofar,arg_tense);
	sofar += add_keyarr(key_table+sofar,arg_voice);
	sofar += add_keyarr(key_table+sofar,arg_mood);
	sofar += add_keyarr(key_table+sofar,arg_dialect);
	sofar += add_keyarr(key_table+sofar,arg_geogregion);
	sofar += add_keyarr(key_table+sofar,arg_morphflags);

	qsort((void*)key_table,sofar,sizeof * key_table,keycomp1);

	if (sofar > (size_t)INT_MAX) {
		fprintf(stderr,"morphology key index exceeds the runtime index width\n");
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		clear_morph_key_state(context);
		return(0);
	}
	nkeys = (int)sofar;
	context->morph_key_language = cur_lang();
	context->morph_keys_initialized = 1;
	return(1);
/*
if(1) {
Morph_args * mf;
mf = *(key_table+sofar-1);
printf("sofar %d last key [%s] second to last [%s]\n",sofar, mf->morph_key, (--mf)->morph_key);
}
*/

/*
	for(i=0;i<sofar && i < 100;i++) {
		Morph_args * mf;
		
		mf = *(key_table+i);
		printf("%d) [%s]\n", i , mf->morph_key );
	}
*/
/*
 i = binlook( key_table , "wr_oros" , nkeys , sizeof * key_table , 1 , 
 keycomp2);
 printf("i %d\n", i );

getchar();
*/

}

int
keycomp1(const void *k1, const void *k2)
{
	const Morph_args *const *m1, *const *m2;

	m1 = (const Morph_args *const *) k1;
	m2 = (const Morph_args *const *) k2;
	return(strcmp( (*m1)->morph_key, (*m2)->morph_key ));
}

int
keycomp2(char *s, char *entry)
{
	const Morph_args *const *kp = (const Morph_args *const *)entry;
	const Morph_args *m;
	int rval = 0;
	m = *kp;

	rval = strcmp(s,m->morph_key);

	return(rval);
}

size_t add_keyarr(const Morph_args **ktab, const Morph_args *morph_args)
{
	const Morph_args *ms = morph_args;
	
	while( morph_args->morph_key[0] ) {
		*ktab++ = morph_args++;
	}
	return((size_t)(morph_args - ms));
}

Stemtype		
GetStemClass(char *classp)
{
	int i;
	
	for(i=0;i<(int)(sizeof arg_stemclass/sizeof arg_stemclass[0]);i++) {
		if( ! strcmp(classp,arg_stemclass[i].class_name ) ) {
			return( (Stemtype)arg_stemclass[i].class_num);
		}
	}
	return((Stemtype)-1);
}

Stemtype		
GetIsProse(char *classp)
{

	if(! (strcmp(classp,"prose")))
		return((Stemtype)PROSEAUTHOR);
	return((Stemtype)0);
}

 int AddMorphKey(gk_string *gstr, char *field)
{
	void (*func)(gk_string *, unsigned long);
	const Morph_args *mp;
	
	mp = MatchMorphKey(field);
	if( ! mp )
		return(0);
	func = mp->add_val;

	if (mp->morph_flags < 0)
		return(0);
	(*func)(gstr,(unsigned long)mp->morph_flags);
	return(1);
}
