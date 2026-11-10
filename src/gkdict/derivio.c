#include "gkdict_internal.h"
#include "../morphlib/runtime_context_internal.h"

static int append_derivation_keys(char *, const char *);

static int checkforderiv2(char *stemstr, char *stemkeys, char *had_redupl, char *redupstem);
int checkcomderivs(char * derivs,char * defstem,char * suffix,char * lemmkeys,char * nkeys,char * had_redupl,char * redupstem);
int checkcomderiv(char * derivs,char * defstem,char * suffix,char * lemmkeys,char * nkeys,char * had_redupl,char * redupstem);
int checkcomderiv2(char * asuffkeys,char * dstem,char * dstemkeys,char * suffix,char * lemma,char * lkeys,char * rkeys,char * had_redupl,int markedstem);

#define DERIV_CONTEXT (morpheus_runtime_context_current())
#define checkedsuffs (DERIV_CONTEXT->derivation_checked_suffixes)
#define checkedderivs (DERIV_CONTEXT->derivation_checked_stems)
#define realderivs (DERIV_CONTEXT->derivation_real_stems)

static void
clear_derivation_cache(morpheus_runtime_context *context)
{
	int i;

	for (i = 0; i < MORPHEUS_DERIVATION_CACHE_SIZE; i++) {
		context->derivation_cache_stems[i][0] = 0;
		free(context->derivation_cache_keys[i]);
		context->derivation_cache_keys[i] = NULL;
	}
	context->derivation_cache_index = 0;
}

static void
clear_derivation_buffers(morpheus_runtime_context *context)
{
	int i;

	for (i = 0; i < MORPHEUS_DERIVATION_BUFFER_COUNT; i++) {
		if (context->derivation_stem_buffers[i])
			FreeGkString(context->derivation_stem_buffers[i]);
		if (context->derivation_quantity_buffers[i])
			FreeGkString(context->derivation_quantity_buffers[i]);
		context->derivation_stem_buffers[i] = NULL;
		context->derivation_quantity_buffers[i] = NULL;
	}
	context->derivation_buffers_initialized = 0;
}

static morpheus_runtime_context *
derivation_context(void)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	int language = cur_lang();

	if (!context->derivation_cache_initialized) {
		context->derivation_cache_language = language;
		context->derivation_cache_initialized = 1;
	} else if (context->derivation_cache_language != language) {
		clear_derivation_cache(context);
		context->derivation_cache_language = language;
	}
	return(context);
}
int
checkforderiv(char *stemstr, char *stemkeys)
{
	int rval = 0;
	int rval2 = 0;
	char *p;
	char stemkeys2[LONGSTRING];
	int oldsuffs = checkedsuffs;

	derivation_context();

	stemkeys2[0] = 0;
	checkedderivs++;

/*
	if( stemstr_in_cache(stemstr,stemkeys) ) {
		if( *stemkeys ) return(1);
		else return(0);
	}
*/
	
	rval=checkforderiv2(stemstr,stemkeys,"","");

/*	if( rval ) return(rval);*/
	
	
	rval2 = checkforredupderiv(stemstr,stemkeys2);
	if( rval2 ) {
		if (!append_derivation_keys(stemkeys,stemkeys2)) return(rval);
	}
/*
printf("%d) %d %d [%s] checkedsuff %d, added %d\n", checkedderivs , realderivs++,
rval+rval2 ,stemstr , checkedsuffs, checkedsuffs - oldsuffs );
*/
	add_deriv_cache(stemstr,stemkeys);
	return(rval+rval2);

}

int
checkforredupderiv(char *stemstr, char *stemkeys)
{
	char noredup[MAXWORDSIZE];
		
	if( Is_cons(*stemstr) && cur_lang() != LATIN  && cur_lang() != ITALIAN ) {
		if( ! un_redupl(stemstr,noredup,'e')) return(0);
/*
		return(checkforderiv2(noredup,stemkeys,stemstr,""));
*/
		return(checkforderiv2(noredup,stemkeys,"redupl",""));
	}
	return(checkaugredup(stemstr,stemkeys));
}

#define MAXREDUPLS MORPHEUS_DERIVATION_BUFFER_COUNT
/*
 * store stems that would have a quantity marked
 * e.g., a)_kolouqh/seis -- doric future perfect
 *
 * grc 3/21/91
 */
int
checkaugredup(char *stemstr, char *stemkeys)
{
	morpheus_runtime_context *context = derivation_context();
	int hits = 0;
	int i;
	int poss_redupls = 0;
	int possno = 0;
	char had_redupl[MAXWORDSIZE];
	char tmpkeys[LONGSTRING];



	if( ! context->derivation_buffers_initialized ) {
		for(i=0;i<MAXREDUPLS;i++) {
			if (!context->derivation_stem_buffers[i])
				context->derivation_stem_buffers[i] = CreatGkString(1);
			if (!context->derivation_quantity_buffers[i])
				context->derivation_quantity_buffers[i] = CreatGkString(1);
			if (!context->derivation_stem_buffers[i] ||
			    !context->derivation_quantity_buffers[i]) {
				clear_derivation_buffers(context);
				morpheus_runtime_error_record(
					MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
				return(0);
			}
		}
		context->derivation_buffers_initialized = 1;
	}
	for(i=0;i<MAXREDUPLS;i++) {
		ClearGkstring(context->derivation_stem_buffers[i]);
		ClearGkstring(context->derivation_quantity_buffers[i]);
	}

	/*
	 * grc 8/4/89
	 *
	 * don't accept this possibility unless you have a word beginning with two
	 * consonants or a double consonant
	 */
	 
	if( !Xstrncmp(stemstr,"e)",2) && ! Is_cons(*(stemstr+3)) ) {
		if( *(stemstr+2) != 'z' && *(stemstr+2) != 'c' && *(stemstr+2) != 'y' )
			return(0);
	}
	poss_redupls = unaugment(stemstr,context->derivation_stem_buffers,
		context->derivation_quantity_buffers,MAXREDUPLS,
		(Dialect)ALL_DIAL,1,1);

	for(i=0;i<poss_redupls;i++) {
		char tempstem[BUFSIZ];
		tmpkeys[0] = 0;
/*
printf("checking [%s] [%s] [%s]\n", stemstr,
gkstring_of(context->derivation_stem_buffers[i]), tmpkeys);
*/
		tempstem[0] = 0;
		SprintGkFlags(context->derivation_stem_buffers[i],tmpkeys,
		              sizeof tmpkeys,"	",1);
		Xstrncpy(tempstem,gkstring_of(context->derivation_stem_buffers[i]),
			(int)sizeof tempstem );

		if( has_morphflag(
			morphflags_of(context->derivation_stem_buffers[i]),
			SYLL_AUGMENT) )
			Xstrcpy(had_redupl,"syll_aug");
		else
			Xstrcpy(had_redupl,"temp_aug");
/*
 * grc 3/21/91
 *
 * if you have a doric stem, for example, then pass this info
 * along
 */

		if( tmpkeys[0] ) {
			if (!morpheus_runtime_string_append(
			    had_redupl," ",sizeof had_redupl) ||
			    !morpheus_runtime_string_append(
			    had_redupl,tmpkeys,sizeof had_redupl)) return(hits);
		}

		if( checkforderiv2(tempstem,tmpkeys,had_redupl,
				gkstring_of(context->derivation_quantity_buffers[i])[0] ?
				gkstring_of(context->derivation_quantity_buffers[i]) :"") ) {
			if (!append_derivation_keys(stemkeys,tmpkeys)) return(hits);
			hits++;
		}

		
	}

	return(hits);
}

static int
checkforderiv2(char *stemstr, char *stemkeys, char *had_redupl, char *redupstem)
{
	char * ep;
	char derivstr[LONGSTRING];
	int rval = 0;
	int sofar = 0;
	size_t slen;
	char derivkeys2[LONGSTRING*2];
	char resbuf[LONGSTRING*2];
	
	slen = Xstrlen(stemstr);
	if (slen == 0) return(0);
	ep = stemstr + slen - 1;
	slen--;
	derivkeys2[0] = resbuf[0] = 0;
	Xstrncpy(derivstr,stemstr,LONGSTRING);

	rval = chckdvend("*",stemkeys);

	if(  chckderiv(derivstr,derivkeys2) ) {
		int n;
		n=checkcomderivs(stemkeys, derivstr,"",derivkeys2,resbuf,had_redupl,redupstem);
		if( n ) sofar++;
	}
	
	while(ep>stemstr) {
/*
		printf("for [%s] of [%s]\n", ep, stemstr );
*/
		rval = chckdvend(ep,stemkeys);
		if( rval ) {
			derivstr[slen] = 0 ;
/*
printf("[%s] ok trying [%s]\n", ep, derivstr );
*/
			if(  chckderiv(derivstr,derivkeys2) ) {
				int n;
				n=checkcomderivs(stemkeys, derivstr,ep,derivkeys2,resbuf,had_redupl,redupstem);
				if( n ) sofar++;
			}
		}
		ep--;
		slen--;
	}
	if( sofar ) {
		Xstrncpy(stemkeys,resbuf,LONGSTRING);
/*
printf("sofar [%d] stemkeys [%s] stemstr [%s]\n", sofar , stemkeys, stemstr );
*/
	}
	return(sofar);
}

int
checkcomderivs(char *derivs, char *defstem, char *suffix, char *lemmkeys, char *nkeys, char *had_redupl, char *redupstem)
{
	int rval = 0;
/*
	char lkeybuf[LONGSTRING], curlemmkeys[LONGSTRING];
*/
	char *lkeybuf, *curlemmkeys;

	lkeybuf = (char *)malloc((size_t)LONGSTRING);
	curlemmkeys = (char *)malloc((size_t)LONGSTRING);
	if (!lkeybuf || !curlemmkeys) {
		free(lkeybuf);
		free(curlemmkeys);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		return(0);
	}
	
	Xstrncpy(curlemmkeys,lemmkeys,LONGSTRING);

	while(nextkey(curlemmkeys,lkeybuf)) {
		
		rval += checkcomderiv(derivs,defstem,suffix,lkeybuf,nkeys,had_redupl,redupstem);

	}
	
	free(lkeybuf);
	free(curlemmkeys);
	return(rval);
	
}

#define Is_perfect(STYPE) (((STYPE&PPARTMASK)== PP_PP)||\
							((STYPE&PPARTMASK)== PP_PF)||((STYPE&PPARTMASK)== PP_FP))

int
checkcomderiv(char *derivstr, char *defstem, char *suffix, char *lkeys, char *rkeys, char *had_redupl, char *redupstem)
{
	char *asuffkeys;
	char *dstemkeys;
	char *lemma;
	char *tmpdstem;
	char * tmpsuff = suffix;
	int markedstem = 0;
	char * s;
	int rval = 0;

	asuffkeys = (char *)malloc((size_t)LONGSTRING*2);
	dstemkeys = (char *)malloc((size_t)LONGSTRING*2);
	lemma = (char *)malloc((size_t)LONGSTRING+1);
	tmpdstem = (char *)malloc((size_t)LONGSTRING+1);
	if (!asuffkeys || !dstemkeys || !lemma || !tmpdstem) {
		free(asuffkeys);
		free(dstemkeys);
		free(lemma);
		free(tmpdstem);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		return(0);
	}
	
	Xstrncpy(asuffkeys,derivstr,LONGSTRING*2);
	Xstrncpy(tmpdstem,lkeys,LONGSTRING);
	s=tmpdstem; /* separate off the stem if one is marked */

	while(*s&&*s!=':') s++;
	if(*s==':') {
		*s++ = 0;
	}
	/*
	 * save the rest of the keys in the lemma slot
	 */
	Xstrncpy(lemma,s,LONGSTRING);

	/*
	 * tmpdstem now includes any specially marked stems, e.g. "ti_m" as in tima/w,
	 * while defstem contains "tim", the stem without the long mark.
	 */
	if( tmpdstem[0] ) {
		markedstem++;
	} else {
		Xstrncpy(tmpdstem,defstem,MAXWORDSIZE);
	}
	


	s = lemma;
	while(*s&&*s!=':') s++; /* now get the lemma */
	if(*s== ':') {
		*s++ = 0;
	}
	
	Xstrncpy(dstemkeys,s,LONGSTRING*2); /* now get the rest of the keys */
	s=dstemkeys;
	while(*s) {
		if(*s == ':' )
			*s = ' ';
		s++;
	}
	if( *had_redupl && Is_vowel(tmpdstem[0]) && ! *redupstem) {
		rval += checkmultredups(asuffkeys,tmpdstem,dstemkeys,tmpsuff,lemma,lkeys,rkeys,had_redupl,markedstem);
	} else {
			if( *had_redupl ) {
				if( *redupstem ) {
			/*
			 * grc 3/21/91
			 *
			 * this case covers an instance such as a)kolouqh/s-eis, where 
			 * this *could* be a doric reduplicated form, but we want to make sure
			 * that we have labelled the long alpha:  a)_kolouqhs-
			 */
						markedstem++;
						Xstrcpy(tmpdstem,redupstem);
						tmpsuff = "";
					} else
						simpleredupit(tmpdstem,NO,'e');	
				
		}	
		rval += checkcomderiv2(asuffkeys,tmpdstem,dstemkeys,tmpsuff,lemma,lkeys,rkeys,had_redupl,markedstem);
	}
	free(asuffkeys);
	free(dstemkeys);
	free(lemma);
	free(tmpdstem);
	return(rval);
}

int
checkmultredups(char *asuffkeys, char *dstem, char *dstemkeys, char *suffix, char *lemma, char *lkeys, char *rkeys, char *had_redupl, int markedstem)
{
	int rval = 0;
	int gotredups = 0;
	int i;
	gk_word * gkform;
	gk_string * gstr;
	char curstemkeys[LONGSTRING];

	gkform = CreatGkword(6);
	gstr = CreatGkString(1);
	if( ! gkform || ! gstr ) {
		morpheus_runtime_diagnostic("no memory for gkform in checkmultredups of [%s]\n",asuffkeys);
		if (gkform) FreeGkword(gkform);
		if (gstr) FreeGkString(gstr);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		return(0);
	}
		
	set_workword(gkform,dstem);
	set_dialect(gstr,(Dialect)0);
	ScanAsciiKeys(dstemkeys,gkform,gstr,(gk_string *)NULL);
	set_dialect(gkform,dialect_of(gstr));
	
	gotredups = redupit2(gkform,NO,'e',5);
	for(i=0;i<gotredups;i++) {
		char * p;
		
		curstemkeys[0] = 0;
		set_dialect(gstr,dialect_of(gkform+i) );
		SprintGkFlags(gstr,curstemkeys,sizeof curstemkeys," ",1);
		p = workword_of(gkform+i);
		rval += checkcomderiv2(asuffkeys,p,curstemkeys,suffix,lemma,lkeys,rkeys,had_redupl,markedstem);
	}

	FreeGkword(gkform);
	FreeGkString(gstr);

	
	return(rval);
}

int
checkcomderiv2(char *asuffkeys, char *dstem, char *dstemkeys, char *suffix, char *lemma, char *lkeys, char *rkeys, char *had_redupl, int markedstem)
{	
	char * derivsuff;
	char * tmpdsuff;
	char * stembuf;
	char * dbuf;
	register char * s;
	gk_string * gstr;
	int rval = 0;
	size_t initial_key_length = strlen(rkeys);
	
	derivsuff = (char *)malloc((size_t)LONGSTRING);
	tmpdsuff = (char *)malloc((size_t)LONGSTRING);
	dbuf = (char *)malloc((size_t)LONGSTRING);
	stembuf = (char *)malloc((size_t)MAXWORDSIZE);
	gstr = CreatGkString(1);
	if (!derivsuff || !tmpdsuff || !dbuf || !stembuf || !gstr)
		goto no_memory;

	Xstrncpy(dbuf,asuffkeys,LONGSTRING);
	
	while(nextkey(dbuf,derivsuff)) {
		stembuf[0] = 0;
		s=derivsuff;
		if( *s && *s != ':' ) {
			char * p;
			
			Xstrncpy(tmpdsuff,s,LONGSTRING);
			s++;
			while(*s&&*s!=':') s++;
			if(*s) s++;
			Xstrcpy(derivsuff,s);
			p = derivsuff;
			while(*p) {
				if( *p == ':' ) *p = ' ';
				p++;
			}
			
			p = tmpdsuff;
			while(*p&&*p!=':') p++;
			if(*p) *p = 0;
			markedstem++;
			
		} else {
			Xstrncpy(tmpdsuff,suffix,LONGSTRING);
		
		}
		
		if( markedstem ) {
			int stemlen = snprintf(stembuf,MAXWORDSIZE,"%s%s",dstem,tmpdsuff);

			if( stemlen < 0 || stemlen >= MAXWORDSIZE ) {
				morpheus_runtime_diagnostic("derived stem is too long: [%s%s]\n",dstem,tmpdsuff);
				continue;
			}
		} else stembuf[0] = 0;
		
		while(*s) {
			if(*s == ':' )
				*s = ' ';
			s++;
		}

		if( DstemTakesDsuff(derivsuff,dstemkeys,gstr,dstem,tmpdsuff))  {
			char tmp1[LONGSTRING*2], tmp2[LONGSTRING*4];
			int keylen;
			size_t used;
			
			/*
			 * grc 5/30/89
			 *
			 * don't accept things like "fi/lhka".  if the stemtype is a perfect,
			 * then the stem must have had a reduplication
			 */

			tmp1[0] = 0;
			if( cur_lang() != LATIN && cur_lang() != ITALIAN ) {
				if( ! (*had_redupl) &&  (Is_perfect(stemtype_of(gstr) )) ) {
					continue;
				}
			}

			if( *had_redupl && ! (Is_perfect(stemtype_of(gstr))) )
				continue;


/*
 * grc 8/4/89
 *
 * if the stem doesn't take a syllabic augment, then don't accept a syllabically
 * augmented perfect
 */
			if( ! Xstrncmp(had_redupl,"syll_aug",Xstrlen("syll_aug")) && 
				! has_morphflag(morphflags_of(gstr),SYLL_AUGMENT) ) {
					continue;
			}
			if( *had_redupl ) {
				gk_word * gkword;
				add_morphflag(morphflags_of(gstr),REDUPL);
				gkword = CreatGkword(1);
				if (!gkword)
					goto no_memory;
				/*
				 * grc 3/21/91
				 *
				 * the first argument in had_redup will be whether we have a redup,
				 * or, if the stem starts with a vowel, if we have a temporal or a
				 * syllabic augment for redup.
				 *
				 * the second may be a dialect (e.g., a)_kolouqhs- is a doric
				 * future perfect stem
				 */
				ScanAsciiKeys(had_redupl,gkword,gstr,(gk_string *)NULL);
				FreeGkword(gkword);
			}
			
			SprintGkFlags(gstr,tmp1,sizeof tmp1,":",1);
/*
printf("curstemkyes [%s] %o\n", tmp1 , has_morphflag(morphflags_of(gstr),R_E_I_ALPHA));
*/
/*
			
			sprintf(tmp2,"%s:%s%s", ((*had_redupl) ? dstem : stembuf), lemma , tmp1);
*/
			keylen = snprintf(tmp2,sizeof tmp2,"%s:%s%s",stembuf,lemma,tmp1);
			if( keylen < 0 || keylen >= (int)sizeof tmp2 ) {
				morpheus_runtime_diagnostic("derivation key is too long\n");
				continue;
			}
/*
printf("success on [%s] and [%s]\n", derivsuff, dstemkeys );
printf("about to add [%s]\n", tmp2 );
*/
			used = strlen(rkeys);
			if( used >= LONGSTRING ||
			    (size_t)keylen + (used != 0) >= LONGSTRING - used ) {
				morpheus_runtime_diagnostic("derivation key buffer is full\n");
				continue;
			}
			if( used ) rkeys[used++] = ' ';
			memcpy(rkeys + used,tmp2,(size_t)keylen + 1);
			rval++;
		}	

		
	}
	free(derivsuff);
	free(tmpdsuff);
	free(stembuf);
	free(dbuf);
	FreeGkString(gstr);
	return(rval);

no_memory:
	rkeys[initial_key_length] = 0;
	free(derivsuff);
	free(tmpdsuff);
	free(stembuf);
	free(dbuf);
	if (gstr) FreeGkString(gstr);
	morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
	return(0);
}

int
DstemTakesDsuff(char *dsuffkeys, char *dstemkeys, gk_string *gstr, char *defstem, char *derivstr)
{
	int rval = 0;

checkedsuffs++;	
	add_morphflag(morphflags_of(gstr),IS_DERIV);
/*
 * grc 7/31/89
 *
 * avoid forms such as i)sxuri+zomai
 */
 	if( has_diaeresis(derivstr) && ! ends_in_vowel(defstem) ) 
 		return(0);

	rval = CompatKeys(dsuffkeys,dstemkeys,gstr);
	zap_morphflag(morphflags_of(gstr),IS_DERIV);
/*
printf("rval %d dsuff [%s %s] dstem [%s %s]\n", rval, defstem, dsuffkeys , derivstr, dstemkeys );
*/
	if( ! rval ) return(0);
	if( !Xstrncmp(derivstr,"a_",2) && ! Is_rei_char(*(lastn(defstem,1))) &&
		need_rei_alpha(dsuffkeys) ) 
		rval = 0;
/*
if( ! rval ) printf("defstem [%s %s] derivstr [%s %s]\n", defstem , dstemkeys, 
derivstr , dsuffkeys );
*/
	return(rval);
}

int
need_rei_alpha(char *dsuffkeys)
{
	gk_string * gstr;
	gk_word * Gkword;
	int rval = 0;
	
	gstr = CreatGkString(1);
	Gkword = CreatGkword(1);
	if (!gstr || !Gkword) {
		if (gstr) FreeGkString(gstr);
		if (Gkword) FreeGkword(Gkword);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		return(0);
	}
	
	ScanAsciiKeys(dsuffkeys,Gkword,gstr,(gk_string *)NULL);

	if( has_morphflag(morphflags_of(gstr),R_E_I_ALPHA) ) {
		rval = 1;
	}

	FreeGkString(gstr);
	FreeGkword(Gkword);
	return(rval);
}

int
stemstr_in_cache(char *s, char *stemkeys)
{
	morpheus_runtime_context *context;
	int i;

	if (stemkeys) *stemkeys = 0;
	if (!s || !stemkeys) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	context = derivation_context();
	
	for(i=0;i<MORPHEUS_DERIVATION_CACHE_SIZE;i++) {
		if( context->derivation_cache_stems[i][0] &&
		    ! strcmp(s,context->derivation_cache_stems[i]) ) {
			if( context->derivation_cache_keys[i] )
				Xstrncpy(stemkeys,context->derivation_cache_keys[i],LONGSTRING);
			else *stemkeys = 0;
			return(1);
		}
		
	}
	return(0);
}

void
add_deriv_cache(char *s, char *keys)
{
	morpheus_runtime_context *context;
	int index;
	char *new_keys = NULL;

	if (!s || !keys || strlen(s) >= MAXWORDSIZE ||
	    strlen(keys) >= LONGSTRING) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return;
	}
	context = derivation_context();
	index = context->derivation_cache_index;
	if( index < 0 || index >= MORPHEUS_DERIVATION_CACHE_SIZE ) index = 0;
	if( *keys ) {
		new_keys = (char *)malloc((size_t)Xstrlen(keys)+1);
		if (!new_keys) {
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
			return;
		}
		Xstrcpy(new_keys,keys);
	}
	Xstrncpy(context->derivation_cache_stems[index],s,MAXWORDSIZE);
	free(context->derivation_cache_keys[index]);
	context->derivation_cache_keys[index] = new_keys;
	context->derivation_cache_index = index + 1;
}

int
ends_in_vowel(char *s)
{
	size_t length;

	if (!s) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	length = strlen(s);
	while (length) {
		unsigned char c = (unsigned char)s[--length];

		if (isalpha(c)) return(Is_vowel(c));
	}
	return(0);
}
static int
append_derivation_keys(char *destination, const char *addition)
{
	char merged[LONGSTRING];

	if (!destination || !addition ||
	    !Xstrncpy(merged,destination,sizeof merged) ||
	    (*merged && !morpheus_runtime_string_append(
	        merged," ",sizeof merged)) ||
	    !morpheus_runtime_string_append(merged,addition,sizeof merged)) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	Xstrncpy(destination,merged,LONGSTRING);
	return(1);
}
