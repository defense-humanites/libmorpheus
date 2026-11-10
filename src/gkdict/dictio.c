#include "gkdict_internal.h"
#include "../morphlib/runtime_context_internal.h"
static int append_dictionary_keys(char *, const char *);
#define DICT_CONTEXT (morpheus_runtime_context_current())
#define VbTags (DICT_CONTEXT->verb_dictionary_tags)
#define NomTags (DICT_CONTEXT->nominal_dictionary_tags)
#define LemmTags (DICT_CONTEXT->lemma_dictionary_tags)
#define num_of_vtags (DICT_CONTEXT->verb_dictionary_tag_count)
#define num_of_ntags (DICT_CONTEXT->nominal_dictionary_tag_count)
#define num_of_ltags (DICT_CONTEXT->lemma_dictionary_tag_count)
#define vbindex (DICT_CONTEXT->dictionary_hq_mode ? STEMLIST : VBINDEX)
#define nomindex (DICT_CONTEXT->dictionary_hq_mode ? STEMLIST : NOMINDEX)

void
SetHqDict(int enabled)
{
	DICT_CONTEXT->dictionary_hq_mode = enabled != 0;
}

int
GetHqDict(void)
{
	return(DICT_CONTEXT->dictionary_hq_mode);
}

static morpheus_runtime_context *
dictionary_context(void)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	int language = cur_lang();

	if (!context->dictionary_tags_initialized) {
		context->dictionary_tag_language = language;
		context->dictionary_tag_hq_mode = context->dictionary_hq_mode;
		context->dictionary_tags_initialized = 1;
	} else if (context->dictionary_tag_language != language ||
		   context->dictionary_tag_hq_mode != context->dictionary_hq_mode) {
		free(context->verb_dictionary_tags);
		free(context->nominal_dictionary_tags);
		free(context->lemma_dictionary_tags);
		context->verb_dictionary_tags = NULL;
		context->nominal_dictionary_tags = NULL;
		context->lemma_dictionary_tags = NULL;
		context->verb_dictionary_tag_count = 0;
		context->nominal_dictionary_tag_count = 0;
		context->lemma_dictionary_tag_count = 0;
		context->dictionary_tag_language = language;
		context->dictionary_tag_hq_mode = context->dictionary_hq_mode;
	}
	return(context);
}


endtags *
init_dict(char *fname, int *ntags)
{
	dictionary_context();
	if( GetHqDict() ) {
		fname = STEMLIST;
	}
	return(init_preind(fname,ntags));
}


/*
 * check to see if the current string is an irregular verb.
 */
int
 chckirrverb(char *irregstr, char *lemmas)
{
	char workstem[MAXWORDSIZE];
	int rval;
	long startoff;

	dictionary_context();
	
	workstem[0] = '1';
	Xstrncpy(workstem+1,irregstr,MAXWORDSIZE);
	stripmetachars(workstem);
	stripacc(workstem);
	rval = chckvstem(workstem,lemmas);
	return(rval);

	if( ! VbTags ) {
		VbTags = init_dict(vbindex,&num_of_vtags);
	}

	startoff = ChckPreIndex(VbTags,workstem,num_of_vtags,YES,morphstrcmp);

	if( startoff < 0 ) return(0);
	if( ChckFullIndex(workstem,lemmas,vbindex,startoff,morphstrncmp) ) {
		return(1);
	}
	return(0);
}


/*
 * check to see if string "indeclstring" is in the indeclinable list. if so, 
 * store any flags associated with it in the ascii string "lemmas".
 * 
 * return 0 if "indeclstring" is not in the indeclinable list.
 */
int
 chckindecl(char *indeclstr, char *lemmas)
{
	long startoff;
	int rval = 0;
	char tmpindecl[MAXWORDSIZE];

	dictionary_context();
	
	*lemmas = 0;
	if( ! NomTags ) {
		NomTags = init_dict(nomindex,&num_of_ntags);
	}
	tmpindecl[0] = '2';
	Xstrncpy(tmpindecl+1,indeclstr,MAXWORDSIZE);
	stripquant(tmpindecl);
	stripdiaer(tmpindecl);
	stripacc(tmpindecl);


/*
	printf("will look for [%s] in indecl\n", tmpindecl );
*/
	startoff = ChckPreIndex(NomTags,tmpindecl,num_of_ntags,NO,morphstrcmp);
/*
printf("startoff [%ld]\n", startoff );
*/
	if( startoff < 0 ) return(0);
	if( ChckFullIndex(tmpindecl,lemmas,nomindex,startoff,morphstrncmp) ) {
		return(1);
	}

	return(rval);
}

/*
 * check to see if string "derivstr" is in the deriv list. if so, 
 * store any flags associated with it in the ascii string "derivkeys".
 * 
 * return 0 if "indeclstring" is not in the indeclinable list.
 */
int
 chckderiv(char *derivstr, char *derivkeys)
{
	long startoff;
	int rval = 0;
	char tmpderivstr[MAXWORDSIZE];

	dictionary_context();
	
/*
	*derivkeys = 0;
*/
	tmpderivstr[0] = '3';
	Xstrncpy(tmpderivstr+1,derivstr,MAXWORDSIZE);
	stripquant(tmpderivstr);
	stripdiaer(tmpderivstr);
	rval = chckvstem(tmpderivstr,derivkeys);
	return(rval);
	
	if( ! VbTags ) {
		VbTags = init_dict(vbindex,&num_of_vtags);
	}


/*
	printf("will look for [%s] in indecl\n", derivstr );
*/
	startoff = ChckPreIndex(VbTags,tmpderivstr,num_of_vtags,YES,morphstrcmp);
/*
printf("startoff [%ld]\n", startoff );
*/
	if( startoff < 0 ) return(0);
	if( ChckFullIndex(tmpderivstr,derivkeys,vbindex,startoff,morphstrncmp) ) {
		return(1);
	}
	return(0);
}


int
 chckstem(char *stemstr, char *stemkeys, int is_nom)
{
	long startoff;
	int rval = 0;
	int rval2 = 0;
	int curntags = 0;
	char tmpkeys[LONGSTRING];
	char * indfile;
	endtags * CurTags = NULL;

	dictionary_context();
	
	stripquant(stemstr);
	stripdiaer(stemstr);
	*stemkeys = tmpkeys[0] = 0;
	if( is_nom )  {
/*
		rval = chcknstem(stemstr,stemkeys);
		rval2 = checkforderiv(stemstr,tmpkeys);
		if( rval2 ) {
			if (!append_dictionary_keys(stemkeys,tmpkeys)) return(rval);
		}
	
		return(rval+rval2);
*/
		indfile = nomindex;
	} else {
		rval = chckvstem(stemstr,stemkeys);
		rval2 = checkforderiv(stemstr,tmpkeys);
		if( rval2 ) {
			if (!append_dictionary_keys(stemkeys,tmpkeys)) return(rval);
		}
	
		return(rval+rval2);

		indfile = vbindex;
	}
	if( ! *stemstr ) return(0);
	
	
	if( ! VbTags ) {
		VbTags = init_dict(vbindex,&num_of_vtags);
	}
	if( ! NomTags ) {
		NomTags = init_dict(nomindex,&num_of_ntags);
	}
	if( is_nom ) {
		CurTags = NomTags;
		curntags = num_of_ntags;
	} else {
		CurTags = VbTags;
		curntags = num_of_vtags;
	}
	

	startoff = ChckPreIndex(CurTags,stemstr,curntags,is_nom? NO : YES,morphstrcmp);

	if( startoff >= 0 ) 
		rval = ChckFullIndex(stemstr,stemkeys,indfile,startoff,morphstrncmp);

/*
	if( ! rval ) {
		rval = checkforderiv(stemstr,stemkeys);
	}
*/
/*
	if( ! is_nom ) 
		rval2 = checkforderiv(stemstr,tmpkeys);
	if( rval2 ) {
		if (!append_dictionary_keys(stemkeys,tmpkeys)) return(rval);
	}

	return(rval+rval2);
*/
	return(rval);
}


int
 prntlemmentry(char *lemma, char *preverb, FILE *f)
{
	long startoff = 0;
	char lemmfile[LONGSTRING] = {0};
	char line[LONGSTRING] = {0};
	FILE * fword = NULL;
	int result = 1;

	if (!lemma || !f) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(-1);
	}
	if( (fword=getlemmstart(lemma,lemmfile,&startoff)) == NULL ) {
		snprintf(line,sizeof line,"No Lemma found under [%s]\n", lemma );
		ErrorMess(line);
		return(-1);
	}
	while(fgets(line,(int)sizeof line, fword) ) {
		if( is_blank(line) ) {
			if (fprintf(f,"\n\n") < 0) result = -1;
			break;
		}
		trimwhite(line);
		if( preverb && *preverb &&
			!Xstrncmp(line,LEMMTAG,Xstrlen(LEMMTAG)) ) {
			rstprevb(line+Xstrlen(LEMMTAG),preverb,0);
			if (fprintf(f,"%s\n", line) < 0) {
				result = -1;
				break;
			}
			continue;
		}
		if( preverb && *preverb ) {
			if (fprintf(f,"%s\tpb:%s\n",line,preverb) < 0) {
				result = -1;
				break;
			}
		} else if (fprintf(f,"%s\n",line) < 0) {
			result = -1;
			break;
		}
	}
	if (ferror(fword)) result = -1;
	if (result < 0)
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
	xFclose(fword);
	return(result);
}

/*
 * given a lemma, find out where in the dictionary it shows up
 *
 * note that this routine should be changed so that it returns the actual
 * entry for that particular lemma. returning an offset presupposes that
 * the dictionary represents a single, big file, and this will not be the 
 * case (I don't think) when we have a 10 mbyte dictionary.
 *
 * this file returns a FILE pointer that is open to the place in
 * a dictionary file in which the lemma entry begins.
 *
 * the offset at which the lemma entry begins in that file is
 * stored (redundantly) in *lemmoff
 */
 
FILE * 
 getlemmstart(char *lemma, char *lemmfile, long *lemmoff)
{
	char curtarget[LONGSTRING];
	char line[LONGSTRING];
	long curoff;
	FILE * f = NULL;
	long startoff;
	int comp = 0;
	int written;
	char shorttag[MAXWORDSIZE];

	if (lemmoff) *lemmoff = -1;
	if (lemmfile) *lemmfile = 0;
	if (!lemma || !lemmfile || !lemmoff) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	dictionary_context();
	
 
	if( ! LemmTags ) {
		LemmTags = init_preind(WORDLIST,&num_of_ltags);
		if (!LemmTags) return(NULL);
	}

	Xstrncpy(shorttag,lemma,MAXWORDSIZE);
	stripquant(shorttag);
	shorttag[6] = 0;

	startoff = ChckPreIndex(LemmTags,shorttag,num_of_ltags,NO,morphstrcmp);
	if (startoff < 0)
		return(NULL);

	if( (f=MorphFopen(WORDLIST,"r")) == NULL ) {
		morpheus_runtime_diagnostic("getlemmstart: could not open %s\n", WORDLIST);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	if (fseek(f,startoff,SEEK_SET) != 0) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		xFclose(f);
		return(NULL);
	}

	Xstrncpy(shorttag,lemma,MAXWORDSIZE);
	stripquant(shorttag);

	written = snprintf(curtarget,sizeof curtarget,":le:%s",shorttag);
	if (written < 0 || written >= (int)sizeof curtarget) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		xFclose(f);
		return(NULL);
	}

	while(1) {
		char curlemm[MAXWORDSIZE];

		curoff = ftell(f);
		if (curoff < 0) {
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			xFclose(f);
			return(NULL);
		}
		if( ! fgets(line,(int)sizeof  line , f)) {
			if (ferror(f))
				morpheus_runtime_error_record(
					MORPHEUS_RUNTIME_ERROR_INTERNAL);
			*lemmoff = -1;
			break;
		}
		if( Xstrncmp(line,LEMMTAG,4) )
			continue;
		trimwhite(line);
		nextkey(line,curlemm);

		comp = morphstrcmp(curtarget,curlemm);
/*
printf("comp [%d] curtarget [%s] curlemm [%s]\n", comp , curtarget , curlemm);
*/
		if(! comp ) {
/*
char errbuf[LONGSTRING];
sprintf(errbuf,"curoff %ld targ [%s] lem [%s]\n", curoff , curtarget, curlemm );
ErrorMess(errbuf);
*/
			*lemmoff = curoff;
			break;
		}
		if( comp < 0 ) {
			*lemmoff = -1;
			break;
		}
	}
	if( *lemmoff < 0 ) {
/*
		char errbuf[LONGSTRING];
		sprintf(errbuf,"error: no such lemma as [%s]\n", shorttag );
		ErrorMess(errbuf);
*/
		*lemmfile = 0;
		xFclose(f);
		f = NULL;
		return(NULL);
	}
	
	Xstrncpy(lemmfile,WORDLIST,LONGSTRING); 
	if (fseek(f,*lemmoff,SEEK_SET) != 0) {
		*lemmoff = -1;
		*lemmfile = 0;
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		xFclose(f);
		return(NULL);
	}
	return(f);

}

int
lemma_exists(char *lemma)
{
	FILE * flemm = NULL;
	char lemmfile[LONGSTRING];
	long lemmoff = 0;
	
	if( (flemm = getlemmstart(lemma,lemmfile,&lemmoff)) == NULL )
		return(0);
	xFclose(flemm);
	flemm = NULL;
	return(1);
}
static int
append_dictionary_keys(char *destination, const char *addition)
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
