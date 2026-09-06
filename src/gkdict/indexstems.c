/* SPDX-License-Identifier: MPL-2.0 */

#include <ctype.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <gkstring.h>

#include <gkdict.h>
#include "../greeklib/addaccent.proto.h"
#include "../greeklib/getsyll.proto.h"
#include "../greeklib/hasaccent.proto.h"
#include "../greeklib/hasdiaer.proto.h"
#include "../greeklib/hasquant.proto.h"
#include "../greeklib/issubstring.proto.h"
#include "../greeklib/stripacc.proto.h"
#include "../greeklib/stripdiaer.proto.h"
#include "../greeklib/stripquant.proto.h"
#include "../greeklib/stripstemsep.proto.h"
#include "../greeklib/xstrings.proto.h"
#include "../morphlib/gkstring.proto.h"
#include "../morphlib/indkeys.proto.h"
#include "../morphlib/morphflags.proto.h"
#include "../morphlib/morphkeys.proto.h"
#include "../morphlib/morphstrcmp.proto.h"
#include "../morphlib/numovable.proto.h"
#define MAX_END_TABLE 150000

gk_word GkWord;
gk_word BlnkWord;
gk_string Gstr;
gk_string AvoidGstr;
gk_string Blnk;
char ** stems;

int index_stems(int, int, int,char *, char* ,int);
int wantstem, wantirrverb, wantindecl;
char * wlist, *indexlist;
int indfreq;
void * zogalloc(size_t, size_t);


#define BIGSTRING BUFSIZ * 5

static long stemcount = 0;
/*
	int zstrcmp(void *, void *); 
*/
#define DELIMITER " "

#include "indexstems.proto.h"
static int do_index(char *file, int indfreq);
long bufsiz =  0;
long bufcount = 0;
char * bufptr;
char * sptr;

/*
FILE * ferrfile;
*/

static long curcomp = 0;

static int take_key(char *keylist, char *output, size_t capacity)
{
	char *at=keylist;
	char *start;
	size_t length;

	while(isspace((unsigned char)*at)) at++;
	start=at;
	while(*at && !isspace((unsigned char)*at)) at++;
	length=(size_t)(at-start);
	if(!length) {
		if(capacity) output[0]=0;
		return 0;
	}
	if(length>=capacity)
		return -1;
	memcpy(output,start,length);
	output[length]=0;
	while(isspace((unsigned char)*at)) at++;
	memmove(keylist,at,strlen(at)+1);
	return 1;
}

int zstrcmp(const void * s1, const void * s2)
   {
	int rval =0;
	
	char **p1 = (char **)  s1;
	char **p2 = (char **)  s2;
	
	rval = morphstrcmp(*p1,*p2);
/*
	if( ! ( curcomp++ % 4000 ) ) fprintf(stderr,"%d:  [%s] [%s]\n", rval , *p1 , *p2 );
*/

	return(rval);
}


int index_hqdict(int wantstem, int wantirrverb, int wantindecl)
{
	return index_stems(wantstem,wantirrverb,wantindecl,
	                   WORDLIST,STEMLIST,1);
}

int index_noms(int wantstem, int wantirrverb, int wantindecl)
{
	return index_stems(wantstem,wantirrverb,wantindecl,
	                   NOMLIST,NOMINDEX,10);
}

int index_vbs(int wantstem, int wantirrverb, int wantindecl)
{
	return index_stems(wantstem,wantirrverb,wantindecl,
	                   VBLIST,VBINDEX,10);
}

int
index_stems(int wantstem, int wantirrverb, int wantindecl, char *wlist, char *indexlist, int indfreq)
{

	char curlemma[MAXWORDSIZE];
	char curstem[MAXWORDSIZE];
	char basename[BIGSTRING];
	char line[BIGSTRING];
	char tmp[BIGSTRING];
	FILE * finput;
/*
	char errfile[BIGSTRING];
*/
	long input_size;
	int result=0;
	
    {
        char sidecar[MAXPATHNAME];
        struct stat existing;
        int length=snprintf(sidecar,sizeof sidecar,"%s.lindex",indexlist);
        if (length<0 || (size_t)length>=sizeof sidecar ||
            stat(indexlist,&existing)==0 || stat(sidecar,&existing)==0) {
            fprintf(stderr,"lexical output already exists or path is too long\n");
            return -1;
        }
    }
	stemcount = 0;
	bufcount = 0;
	basename[0] = line[0] = 0;


	
	if(! (finput=fopen(wlist,"r"))) {
			fprintf(stderr,"Could not open %s\n", wlist );
			return(-1);
	}
/*	
	sprintf(errfile,"%s.error", wlist );
	if(! (ferrfile=MorphFopen(errfile,"w"))) {
			fprintf(stderr,"Could not open %s\n", errfile );
			return(-1);
	}
*/	
	stems = (char **) calloc((size_t)MAX_END_TABLE,(size_t)sizeof *stems);
	if( ! stems ) {
		fprintf(stderr,"could not allocate %d stems\n",MAX_END_TABLE);
		fclose(finput);
		return(-1);
	}

	if(fseek(finput,0L,SEEK_END)!=0 || (input_size=ftell(finput))<0 ||
	   input_size>(LONG_MAX-1)/2 || fseek(finput,0L,SEEK_SET)!=0) {
		fprintf(stderr,"Could not size %s\n",wlist);
		fclose(finput);
		free(stems);
		stems=NULL;
		return(-1);
	}
	bufsiz=input_size*2+1;
	printf("bufsiz %ld bytes\n", bufsiz );

	bufptr = (char *)malloc((size_t)bufsiz);
	if( ! bufptr ) {
		printf("could not allocate %ld bytes\n", bufsiz );
		fclose(finput);
		free(stems);
		stems=NULL;
		return(-1);
	}
	printf("allocated %ld bytes successfully!\n", bufsiz );
	sptr = bufptr;
	curlemma[0]=0;
	
	while(fgets(line,(int)BIGSTRING, finput )) {
		if(!strchr(line,'\n') && !feof(finput)) {
			fprintf(stderr,"input line exceeds %d bytes in %s\n",
			        BIGSTRING-1,wlist);
			result=-1;
			break;
		}

		if( ! strncmp(line,":le:",4) ) {
			if(take_key(line+4,curlemma,sizeof curlemma)!=1) {
				fprintf(stderr,"invalid or oversized lemma in %s\n",wlist);
				result=-1;
				break;
			}
			basename[0] = 0;
			continue;
		}
		if( line[0] == '@' ) {
			int written;

			if( ! basename[0] ) continue;
			written=snprintf(tmp,sizeof tmp,"%s %s",basename,line+1);
			if(written<0 || (size_t)written>=sizeof tmp) {
				fprintf(stderr,"continued stem record is too long in %s\n",wlist);
				result=-1;
				break;
			}
			memcpy(line,tmp,(size_t)written+1);
		}
		/*
		 * the stem index does not include compound
		 * verbs. it assumes that the simplex entry will
		 * have all the possible stems, and that morpheus
		 * will be able to find the compound lemma all by itself.
		 *
		if( is_substring("pb:",line) )
			continue;*/

		if( (! strncmp(line,":vs:",4) || 
			! strncmp(line,":aj:",4) ||
			! strncmp(line,":no:",4)) ) {
			if(!curlemma[0]) {
				fprintf(stderr,"stem record precedes lemma in %s\n",wlist);
				result=-1;
				break;
			}
			if( ! strncmp(line,":aj:",4) || ! strncmp(line,":no:",4) ) {
				char * t = basename;
				if(!Xstrncpy(basename,line,sizeof basename)) {
					result=-1;
					break;
				}
				while(*t&&!isspace(*t)) t++;
				while(isspace(*t)) t++;
				while(*t&&!isspace(*t)) t++;
				*t = 0;
			} else
				basename[0]=0;
			if(take_key(line+4,curstem,sizeof curstem)!=1 ||
			   !do_curstem(curstem,curlemma,line+4,"")) {
				result=-1;
				break;
			}
		} else if( ! strncmp(line,":vb:",4)) {
			if(!curlemma[0] ||
			   take_key(line+4,curstem,sizeof curstem)!=1 ||
			   !do_curstem(curstem,curlemma,line+4,"1")) {
				result=-1;
				break;
			}

		} else if( ! strncmp(line,":wd:",4) ) {
			if(!curlemma[0] ||
			   take_key(line+4,curstem,sizeof curstem)!=1 ||
			   !do_curstem(curstem,curlemma,line+4,"2")) {
				result=-1;
				break;
			}

		} else if( ! strncmp(line,":de:",4) ) {
			if(!curlemma[0] ||
			   take_key(line+4,curstem,sizeof curstem)!=1) {
				result=-1;
				break;
			}
/*
 * grc 7/6/89
 *
 * for an entry such as ":de:b azw pres_redupl", do not even bother 
 * trying to store this as a productive deriv type.
 */
			if( ! is_presredupl(line) )  {
			if( ! do_curstem(curstem,curlemma,line+4,"3") ) {
				result=-1;
				break;
			}
			}
		}	

	}
	if (ferror(finput)) result=-1;
	if (fclose(finput)!=0) result=-1;
	printf("stemcount %ld\n", stemcount );
	if(result==0 && stemcount==0) {
		fprintf(stderr,"no stem records found in %s\n",wlist);
		result=-1;
	}
	if(result==0 && wantstem)
		result=do_index(indexlist,indfreq);
	else {
		free(stems);
		stems=NULL;
	}
	free(bufptr);
	bufptr=NULL;
	sptr=NULL;
	return result;
}
		
static int do_index(char *file, int indfreq)
{
	FILE * foutput;
/*
	char curkey[BIGSTRING];
	char prevkey[BIGSTRING];
	char curtag[BIGSTRING];
	char prevtag[BIGSTRING];
*/
	char *curkey;
	char *prevkey;
	char *curtag;
	char *prevtag;
	long i;
	char ** table;
	
	curkey = malloc(BIGSTRING);
	prevkey = malloc(BIGSTRING);
	curtag = malloc(BIGSTRING);
	prevtag = malloc(BIGSTRING);
	if(!curkey || !prevkey || !curtag || !prevtag) {
		fprintf(stderr,"could not allocate stem-index workspace\n");
		free(curkey);
		free(prevkey);
		free(curtag);
		free(prevtag);
		free(stems);
		stems=NULL;
		return(-1);
	}
	
	table = stems;



	qsort(table,(size_t)stemcount,sizeof * table, zstrcmp );
	
/*
 	lqsort((char **)table,stemcount,(int) sizeof * table, xstrcmp );
*/
fprintf(stderr,"out of qsort\n");

	if(! (foutput=fopen(file,"wx"))) {
		fprintf(stderr,"Could not open %s\n",file);
		free(curkey);
		free(prevkey);
		free(curtag);
		free(prevtag);
		free(table);
		stems=NULL;
		return(-1);
	}
	
	prevtag[0] = 0;
	for(i=0;i<stemcount;i++) {

if( ! (i % 5000 ) ) printf("processing %ld: %s\n", i , *(table+i) );

        if(take_key(*(table+i),curtag,BIGSTRING)!=1) {
            fprintf(stderr,"invalid stored stem key\n");
            goto output_failure;
        }

		/*
		 * if a new keys
		 */
		if( morphstrcmp(curtag,prevtag) ) {
			if( prevtag[0] ) fprintf(foutput,"\n");
			fprintf(foutput,"%s%s%s", curtag, DELIMITER, *(table+i) );
		} else if ( strcmp(prevkey,*(table+i) ) )
			/*
			 * don't include lines such as "uiais perf_act perf_act"
			 * where the same key is repeated
			 */
			fprintf(foutput,"%s%s", DELIMITER, *(table+i) );
		Xstrcpy(prevtag,curtag);
		Xstrcpy(prevkey,*(table+i));
	}
fprintf(stderr,"done with i=%ld, %ld\n", i , stemcount-i);
	if (ferror(foutput)) goto output_failure;
	if (fclose(foutput)!=0) { foutput=NULL; goto output_failure; }
    foutput=NULL;
fprintf(stderr,"about to index [%s]\n", file);
/*
	free(bufptr);
*/
	if(index_list_file(file,"",indfreq)<0) goto output_failure;
fprintf(stderr,"have just indexed [%s]\n", file);

/*
	for(i=0;i<stemcount;i++) free(*(table+i));
*/
	free(table);
	stems=NULL;
	free(curkey);
	free(prevkey);
	free(curtag);
	free(prevtag);
	return(0);
output_failure:
    if (foutput) fclose(foutput);
    remove(file);
    {
        char sidecar[MAXPATHNAME];
        int length=snprintf(sidecar,sizeof sidecar,"%s.lindex",file);
        if (length>=0 && (size_t)length<sizeof sidecar) remove(sidecar);
    }
    free(curkey); free(prevkey); free(curtag); free(prevtag);
    free(table); stems=NULL;
    return -1;
}

int add_newstemkey(char *s)
{
	if( stemcount >= MAX_END_TABLE ) {
		fprintf(stderr,"more than %d endings in table! bye!\n", MAX_END_TABLE );
		return(0);
	}
/*
	*(stems+stemcount) = calloc((size_t)strlen(s)+1,sizeof ** stems );
	if( ! *(stems+stemcount) ) {
*/
	if((long)strlen(s)+1>bufsiz-bufcount) {
		fprintf(stderr,"no memory left with %ld stems!\n", stemcount );
		return(0);
	}
	*(stems+stemcount)=sptr;
	memcpy(sptr,s,strlen(s)+1);
	bufcount+=(long)strlen(s)+1;
	sptr+=strlen(s)+1;
	
	if( ! (stemcount % 1000 ) ) 	fprintf(stderr,"%ld) [%s]\n", stemcount ,s );
	stemcount++;
	return(1);
}

int do_curstem(char *curstem, char *curlemma, char *curline, char *prefix)
{

	char markedstem[BIGSTRING];
	
	GkWord = BlnkWord;

	Gstr = Blnk;
	AvoidGstr = Blnk;	
	
	clear_globs(curline);
	int parsed=ScanAsciiKeys(curline,&GkWord,&Gstr,&AvoidGstr);
    if(!parsed && !(strcmp(prefix,"3")==0 && derivtype_of(&Gstr))) {
        fprintf(stderr,"untyped record: %s %s %s %s\n",prefix,curlemma,curstem,curline);
        if(oddkeys_of(&GkWord) && oddkeys_of(&GkWord)[0])
            fprintf(stderr,"unrecognized keys: %s\n",oddkeys_of(&GkWord));
        else
            fprintf(stderr,"no inflectional stem type among recognized keys\n");
        free(oddkeys_of(&GkWord));
        oddkeys_of(&GkWord)=NULL;
        return 0;
    }
    free(oddkeys_of(&GkWord));
    oddkeys_of(&GkWord)=NULL;
/*
	if( ! stemtype_of(&Gstr) ) {
		fprintf(stderr,"no stemtype in:%s\n", curline );
		fprintf(ferrfile,"no stemtype in:%s\n", curline );
	}
*/	
	if( has_morphflag(morphflags_of(prvb_gstr_of(&GkWord)),ROOT_PREVERB) ) 
		add_morphflag(morphflags_of(&Gstr),ROOT_PREVERB);
/*
if(preverb_of(&GkWord)[0] )
	printf("if preverb_of(Gkword)[0] [%s]\n", preverb_of(&GkWord) );
*/
	
	stripstemsep(curstem);
	stripshortmark(curstem);
	if( has_quant(curstem) || has_diaeresis(curstem) || hasaccent(curstem)) {
		if(!Xstrncpy(markedstem,curstem,sizeof markedstem)) return(0);
		stripquant(curstem);
		stripacc(curstem);
	} else
		markedstem[0] = 0;
	stripdiaer(curstem);

	if( ! dump_curstem(prefix,curstem,markedstem,curlemma,&Gstr,&AvoidGstr,preverb_of(&GkWord)) )
			return(0);
	
	if( Is_proclitic(morphflags_of(&Gstr))) {
		int rval;

	
		rval=dumpaccstem(prefix,curstem,markedstem,curlemma,&Gstr,&AvoidGstr,PENULT,preverb_of(&GkWord));
		if( rval < 0 ) 
			return(0);
		if(! rval && Is_proclitic(morphflags_of(&Gstr)))
			rval=dumpaccstem(prefix,curstem,markedstem,curlemma,&Gstr,&AvoidGstr,ULTIMA,preverb_of(&GkWord));
		if( rval < 0 ) return(0);
	}
	return(1);
}

int dumpaccstem(char *prefix, char *curstem, char *markedstem, char *curlemma, gk_string *gstr, gk_string *avoidgstr, int syllnum, char *preverb)
{
	char *p;
	char tmpmarked[MAXWORDSIZE];
	char tmpstem[MAXWORDSIZE];

	if( * markedstem ) {
		if(!Xstrncpy(tmpstem,markedstem,sizeof tmpstem)) return(-1);
	} else {
		if(!Xstrncpy(tmpstem,curstem,sizeof tmpstem)) return(-1);
	}

	
	if((p=getsyll(tmpstem,syllnum)) == P_ERR)
		return(0);

	 addaccent(tmpstem,ACUTE,p);
/*	
	if( * markedstem ) {
		Xstrcpy(tmpmarked,tmpstem);
		stripquant(tmpstem);
	} else {
		tmpmarked[0] = 0;
	}
*/
	if(!Xstrncpy(tmpmarked,tmpstem,sizeof tmpmarked)) return(-1);
	stripquant(tmpstem);
	stripdiaer(tmpstem);
	stripacc(tmpstem);
	if( ! dump_curstem(prefix,tmpstem,tmpmarked,curlemma,gstr,avoidgstr,preverb) )
		return(-1);
		
	return(1);
}
	
int dump_curstem(char *prefix, char *curstem, char *markedstem, char *curlemma, gk_string *gstr, gk_string *avoidgstr, char *preverb)
{	
	char tmp[BIGSTRING];
	char notbuf[BIGSTRING];

	set_gkstring(gstr,*markedstem ? markedstem : curstem );
	if( takes_nu_movable(gstr) && (! strcmp(prefix,"1") || ! strcmp(prefix,"2") ) ) {
			gk_string TmpGstr;
			char unmarked[MAXWORDSIZE];
			char tmpmarked[MAXWORDSIZE];
			
			TmpGstr = *gstr;
			if( * markedstem ) {
				set_gkstring(&TmpGstr,markedstem);
				add_numovable(&TmpGstr);
				if(!Xstrncpy(unmarked,gkstring_of(&TmpGstr),sizeof unmarked) ||
				   !Xstrncpy(tmpmarked,gkstring_of(&TmpGstr),sizeof tmpmarked))
					return(0);
				stripquant(unmarked);
				stripacc(unmarked);
				stripdiaer(unmarked);
			} else {
				tmpmarked[0] = 0;
				set_gkstring(&TmpGstr,curstem);
				add_numovable(&TmpGstr);
				if(!Xstrncpy(unmarked,gkstring_of(&TmpGstr),sizeof unmarked))
					return(0);
				stripquant(unmarked);
				stripacc(unmarked);
				stripdiaer(unmarked);
			}
/*
printf("numovable is [%s]\n", gkstring_of(&TmpGstr));
*/
			if(!dump_curstem(prefix,unmarked,gkstring_of(&TmpGstr),curlemma,
			                   &TmpGstr,avoidgstr,preverb))
				return(0);
	}

	{
		int written=snprintf(tmp,sizeof tmp,"%s%s %s:%s",
		                     prefix,curstem,markedstem,curlemma);
		if(written<0 || (size_t)written>=sizeof tmp)
			return(0);
	}
	if(!SprintGkFlags(gstr,tmp,sizeof tmp,":",0)) return(0);
	if( *preverb ) {
		const char *tag=has_morphflag(morphflags_of(gstr),ROOT_PREVERB)
		                ? ":rpb:" : ":pb:";
		if(!Xstrncat(tmp,tag,sizeof tmp) ||
		   !Xstrncat(tmp,preverb,sizeof tmp) ||
		   !Xstrncat(tmp,":",sizeof tmp))
			return(0);
	}
	notbuf[0] = 0;
	if(!SprintGkFlags(avoidgstr,notbuf,sizeof notbuf,":",0)) return(0);
	if( notbuf[0] ) {
		if(!Xstrncat(tmp,":not",sizeof tmp) ||
		   !Xstrncat(tmp,notbuf,sizeof tmp))
			return(0);
	}

	return (add_newstemkey(tmp));
}

void clear_globs(char *s)
{
	while(*s) {
		if( *s == ',' )
			*s = ' ';
		s++;
	}
}

int is_presredupl(char *s)
{
	if( is_substring("pres_redupl",s) )
		return(1);
	return(0);
}

int huh(void)
{
	return getchar();
}
