/*
 * Greg Crane 
 * June 1987
 */

#include "contract.h"
#include <string.h>
#include "gkends_internal.h"
#include "../morphlib/runtime_context_internal.h"

#include "contract.proto.h"
#include "lcontr.proto.h"

static const gk_string Blnk;

static gk_string *
vowel_contraction_table(int *count)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	int language = cur_lang();

	if (context->vowel_contraction_table &&
	    context->vowel_contraction_language != language) {
		FreeGkString(context->vowel_contraction_table);
		context->vowel_contraction_table = NULL;
		context->vowel_contraction_count = 0;
	}
	if (!context->vowel_contraction_table) {
		context->vowel_contraction_table =
			load_vcontr(&context->vowel_contraction_count);
		if (context->vowel_contraction_table)
			context->vowel_contraction_language = language;
	}
	*count = context->vowel_contraction_count;
	return(context->vowel_contraction_table);
}

static gk_string *
consonant_euphony_table(int *count)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	int language = cur_lang();

	if (context->consonant_euphony_table &&
	    context->consonant_euphony_language != language) {
		FreeGkString(context->consonant_euphony_table);
		context->consonant_euphony_table = NULL;
		context->consonant_euphony_count = 0;
	}
	if (!context->consonant_euphony_table) {
		context->consonant_euphony_table =
			load_ccontr(&context->consonant_euphony_count);
		if (context->consonant_euphony_table)
			context->consonant_euphony_language = language;
	}
	*count = context->consonant_euphony_count;
	return(context->consonant_euphony_table);
}

static int
fix_recessive_accent(gk_string *gstr)
{
	gk_word *gkform = CreatGkword(1);

	if( ! gkform )
		return(0);
	forminfo_of(gkform) = forminfo_of(gstr);
	*ends_gstr_of(gkform) = *gstr;
	FixRecAcc(gkform,morphflags_of(gstr),gkstring_of(gstr));
	FreeGkword(gkform);
	return(1);
}

gk_string *
 poss_contracts(gk_string *gstr, Dialect skipdial)
{
	gk_string * Poss_contracts;
	gk_string *vow_contr;
	int numcontr;

	Poss_contracts = CreatGkString(MAXCONTRACTS+1);
	if( ! Poss_contracts )
		return(NULL);
	vow_contr = vowel_contraction_table(&numcontr);
	if( ! vow_contr ) {
		fprintf(stderr,"Could not create poss_contracts!\n");
		FreeGkString(Poss_contracts);
		return(NULL);
	}

	if(sub_for_euph(gstr,skipdial,Poss_contracts,MAXCONTRACTS,vow_contr,numcontr))
		return(Poss_contracts);
/*
printf("empty\n");
*/
	FreeGkString(Poss_contracts);
	return(NULL);

}

#define MAXEUPHS 5
#define ANY_POSITION ((size_t)-1)

static int substitute(gk_string *, Dialect, gk_string *, int, gk_string *,
		      int, size_t);

static gk_string *
euphonize(gk_string *gstr, Dialect skipdial, size_t junction)
{
	gk_string * euphs;
	gk_string *cons_euph;
	int hits = 0;
	int numeuphs;

	euphs = (gk_string *) CreatGkString(MAXEUPHS);
	if( ! euphs )
		return(NULL);
	cons_euph = consonant_euphony_table(&numeuphs);
	if( ! cons_euph ) {
		fprintf(stderr,"Could not create Cons_euph!\n");
		FreeGkString(euphs);
		return(NULL);
	}
	
	hits = substitute(gstr,skipdial,euphs,MAXEUPHS,cons_euph,numeuphs,
			  junction);

	if( hits )
		return(euphs);
	FreeGkString(euphs);
	return(NULL);
}

gk_string *
 do_euph(gk_string *gstr, Dialect skipdial)
{
	return(euphonize(gstr,skipdial,ANY_POSITION));
}

/*
 * Like do_euph(), but only for a pattern that reaches the junction at
 * offset `junction' of the string, typically between a stem and the suffix
 * joined to it. do_euph() takes the leftmost pattern anywhere, so the "sso"
 * or "ns" inside a stem such as glwssoxarit or palinstat would be simplified
 * as if it stood at the junction. libmorpheus addition.
 */
gk_string *
 do_euph_at_junction(gk_string *gstr, Dialect skipdial, size_t junction)
{
	return(euphonize(gstr,skipdial,junction));
}

/* Letters between offset and junction, diacritics aside. */
static size_t
letters_before(const char *string, size_t offset, size_t junction)
{
	size_t letters = 0;

	for (; offset < junction && string[offset]; offset++) {
		if (!strchr(")(/\\=+|^_",string[offset]))
			letters++;
	}
	return(letters);
}

/*
 * note that this routine makes the following assumptions about 
 * sub_table:
 * 
 *  1) the list is sorted in *reverse* alphabetical
 *	order. this is done so that longer matches must go first 
 *	in the list: thus "eou" *must*
 *	precede "eo", and "eh|" must precede "eh". this is a 
 *	crude way of getting the longest possible substring.
 *
 *  2) all equivalent uncontracted forms must go one after the other 
 * in the list. Thus, we have:
 *
 *	"eoi",		"oi",	ATTIC|IONIC,
 *	"eoi",		"eoi",	IONIC,
 *	
 *	once we start matching contracts, all matches are assumed to
 *	to be contiguous. thus, if you have:
 *
 *	"eoi",		"oi",	ATTIC|IONIC,
 *	"eou",		"ou",	ATTIC,
 *	"eoi",		"eoi",	IONIC,
 *
 *	the matching routine looking for "eoi" will exit as soon as it fails on
 *	"eou", and will *not* see the second "eoi".
 */
int
 sub_for_euph(gk_string *gstr, Dialect skipdial, gk_string *poss_subs, int possno, gk_string *sub_table, int len)
{
	return(substitute(gstr,skipdial,poss_subs,possno,sub_table,len,
			  ANY_POSITION));
}

static int
 substitute(gk_string *gstr, Dialect skipdial, gk_string *poss_subs, int possno, gk_string *sub_table, int len, size_t junction)
{

	int i;
	char * raw, * cooked;
	char haveseen[MAXWORDSIZE];
	char *hp;
	int sofar = 0;
	char * curs;
	
	curs = gkstring_of(gstr);
	hp = haveseen;
	*hp = 0;
	*(poss_subs+sofar) =  *gstr;

/*
printf("\nlen %d curs [%s]\n", len , curs);
*/

  while(*curs) {
	for(i=0;i<len && sofar<possno;i++) {
		raw = gkstring_of(sub_table+i);
		cooked = gkstring_of(sub_table+i) + MAXSUBSTRING;
/*
printf("raw [%s] cooked [%s]\n", raw , cooked );
*/

		if( sofar )  {
			/*
			 * ie., if we have matched against, "aou",
			 * break if we see "ao".
			 *
			 * this says that if you have had a match
			 * and you are not looking at another instance of
			 * exactly the same match pattern, bag it.
			 *
			 * yeah, i know its ugly. i can't wait
			 * to see your elegant version of all this.
			 *		grc 6/13/87
			 */
			if( i > 0 && strcmp(gkstring_of(sub_table+i),gkstring_of(sub_table+i-1) ) )
/*
 			if( i > 0 && dictstrcmp(gkstring_of(sub_table+i),gkstring_of(sub_table+i-1) ) )
*/
				return(sofar);
		}

		/* A pattern that ends before the junction is left alone. */
		if( junction != ANY_POSITION &&
		    strlen(raw) < letters_before(gkstring_of(gstr),
				(size_t)(curs - gkstring_of(gstr)),junction) )
			continue;

		*(poss_subs+sofar) =  *gstr;

		if( needs_sub(poss_subs+sofar,skipdial,sub_table+i,haveseen,curs,raw,cooked) ){

/*
PrntGkStr(poss_subs+sofar,stdout);
*/
			sofar++;
		} else  {
			*(poss_subs+sofar) = Blnk;
		}
	}
	if( sofar ) {
		return(sofar);
	} 
  *hp++ = *curs++;
  *hp = 0;
  
  }

	return(0);
}

int
needs_sub(gk_string *gstr, Dialect skipdial, gk_string *matchgstr, char *haveseen, char *curstring, char *raw, char *cooked)
{
	register char * p1, *p2;
	int rval = 0;
	int syllno;
	Dialect curdial;
	Dialect dial;
	GeogRegion gregion;
	gk_string SaveGstr;
	char savestr[MAXWORDSIZE];
	char savecur[MAXWORDSIZE];
	int curbreath;

	savestr[0] = savecur[0] = 0;
	dial = dialect_of( matchgstr );
	set_morphflags(&SaveGstr, morphflags_of( matchgstr ));
	gregion = geogregion_of( matchgstr );
/*
printf("str [%s] skipdial %o match d [%o]\n", curstring, skipdial, dialect_of(matchgstr));
*/

	if(skipdial & dial ) {
		return(0);
	}
		
	if( (curdial=AndDialect(dialect_of(gstr),dial)) < 0 ) {
		return(0);
	} 

	Xstrcpy(savestr, haveseen );
	Xstrcpy(savecur, curstring );
    curbreath = getbreath(savecur);
    stripbreath(savecur);

		if(!strncmp(raw,savecur,strlen(raw))) {
			char tmp[MAXWORDSIZE];

			tmp[0] = 0;
			Xstrcpy(tmp,cooked);
			p1 = tmp+strlen(tmp)-1;
			if (!Xstrncat(tmp,savecur+strlen(raw),sizeof tmp)) {
				morpheus_runtime_error_record(
					MORPHEUS_RUNTIME_ERROR_INTERNAL);
				return(0);
			}
			/*
			 * here is a little beta code kludge:
			 *   -- if you have a string such as "aoi" contract to "w|", but if you
			 *   have "aoi/" you have to contract to "w/|", thus shifting the "/" and the
			 *   iota. this is because beta code assumes that the iota subscript follows all
			 *   other diacritics (i have never seen this rule written down, but it does
			 *   seem to apply).
			 *  
			 *   so, we have the code do the work. we could put the patterns "aoi/" and "w|/"
			 *   into the table of contractions, but the user should not have to worry about
			 *   accents there, so instead we bury the function in the code. a mistake, perhaps,
			 *   but it suits the major goal of simplifying the appearence of morpheus.
			 */

			 if( *p1 == SUBSCR && *(p1+1) == '/' ) {

			 	*p1++ = ACUTE;
			 	*p1++ = SUBSCR;
			 	if( *p1 == HARDLONG ) /* if  "aoi_" contracts to "w|", strip the "_"*/
			 		Xstrcpy(p1,p1+1);
			 }
			if (!Xstrncat(savestr,tmp,sizeof savestr)) {
				morpheus_runtime_error_record(
					MORPHEUS_RUNTIME_ERROR_INTERNAL);
				return(0);
			}
			Xstrcpy(gkstring_of(gstr),savestr);
			if( cur_lang() != LATIN ) addbreath(gkstring_of(gstr),curbreath);

			set_dialect(gstr,curdial);
			add_geogregion(gstr,gregion);
			add_morphflags(gstr,morphflags_of(&SaveGstr));
			return(1);
	
		} 
	/*
 	 * ok, see if there is an accent in the way of
	 * a match. if so, convert the accent accordingly.
	 *
	 * if the first syllable absorbed in the cotraction
	 * is accented, then you put a circumflex on the
	 * accent, unless you have only one syllable and
	 * you have a nominative or accusative
 	 */
		else if( (syllno = stripacc(savecur)) && (!strncmp(raw,savecur,strlen(raw)))) {
			char tmp[MAXWORDSIZE];
			char accs[MAXWORDSIZE];

			
	/*
	 * if savestr contains "men",
	 *    savecur contains "e/omen" 
	 *	  raw contains "eo"
	 *	  and cooked contains "ou",
	 *	  then stripacc() zaps the '/' and savecur contains "eomen".
	 *
	 */

			Xstrcpy(tmp,savestr);
			if (!Xstrncat(tmp,cooked,sizeof tmp) ||
			    !Xstrncat(tmp,savecur+strlen(raw),sizeof tmp)) {
				morpheus_runtime_error_record(
					MORPHEUS_RUNTIME_ERROR_INTERNAL);
				return(0);
			}
			p1 = tmp;
			
			/*
			 * if contraction causes something like "aoi_" to go to "w|_", get rid of the
			 * (now extraneous) long mark.
			 */
			while(*p1) {
				if( *p1 == SUBSCR && *(p1+1) == HARDLONG ) {
					p1++;
					Xstrcpy(p1,p1+1);
				}
				p1++;
			}
	/*
	 * acc. to the above example,
	 *	tmp should contain "oumen" and
	 *	savestr should be truncated to "men"
	 *
	 */

	/*
	 * ok, now see if you need to accent the ending
	 *
	 * grc 10/5/88
	 * remember that not every accent you strip off necessarily comes from the first
	 * syllable. e.g. we want to generate the form "i(e/si", (pres part from i(/hmi)
	 * not i(/esi.
	 */

			Xstrcpy(gkstring_of(gstr),tmp);
			if( cur_lang() != LATIN ) addbreath(gkstring_of(gstr),curbreath);
			set_dialect(gstr,curdial);
			add_geogregion(gstr,gregion);
			add_morphflags(gstr,morphflags_of(&SaveGstr));
	
			if( ! has_morphflag(morphflags_of(gstr),IS_DERIV)  ) {
				if( syllno == nsylls(gkstring_of(gstr)) - 1) 
					add_morphflag(morphflags_of(gstr),SUFF_ACC);
				add_morphflag(morphflags_of(gstr),LOST_ACC);
/*
 * grc 3/17/91
 *
 * added the following because we were generating "ei/sqai" instead of "ei=sqai"
 * for the mp pres part of epsilon contracts
 */
/*
 * grc 6/27/91
 * put this back in because we were getting
 * -a=s instead of -a/s for forms such as kata-ba/s
 */
				if( Is_verbform(gstr) && (mood_of(forminfo_of(gstr)) != PARTICIPLE) && !strchr(gkstring_of(gstr),'!')) {
					if (!fix_recessive_accent(gstr))
						return(0);
				} else {
/*
 * end 3/17/91 mod
 */
					AccComposForm(gstr);
				}
				if (morpheus_runtime_context_error(
				    morpheus_runtime_context_current()) !=
				    MORPHEUS_RUNTIME_ERROR_NONE)
					return(0);
				zap_morphflag(morphflags_of(gstr),LOST_ACC);
			}
/*
 * Commented out 5/9/92: this generated "ou/sai" instead of endings such as
 * "ou=sai".
 *
 * if(Is_verbform(gstr) && mood_of(forminfo_of(gstr)) != PARTICIPLE)
 *     FixRecAcc(gstr,morphflags_of(gstr),gkstring_of(gstr));
 */
			return(1);
		}

	if( cur_lang() != LATIN ) addbreath(gkstring_of(gstr),curbreath);
	return(0);
}
