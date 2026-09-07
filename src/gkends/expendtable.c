/* SPDX-License-Identifier: MPL-2.0 */

/*
 * this program compiles a table of Greek endings.
 *
 * first it expands any macros that are in the tables: thus, "omen@adj1" get turned into "o/menos"
 * 	"ome/nou" "ome/nw|" etc.
 *
 * then, it sorts the resulting endings according to the ascii lexical sort weights of the endstrings:
 *	thus, "w" gets placed after "eis".
 */
#include <gkstring.h>
#include "gkends_internal.h"
#include "../morphlib/runtime_context_internal.h"
#include "endfiles.h"
#include "compostypes.h"

#include "expendtable.proto.h"

int
 expendtables(char *tabname, int maintable, int formcode)
{
	FILE * finput = NULL;
	FILE * foutput = NULL;
	char line[BUFSIZ];
	char shortname[LONGSTRING];
	char fname[MAXPATHNAME];
	char basename[MAXWORDSIZE];
	char *s;
	gk_string TmpGstr;
	const gk_string blank = { 0 };
	Stemtype stype;
	int status = 0;

	
	/*
	 * deal with things like Unix relative path names
	 */
	s = tabname;
	while(*s) s++;
	s--;
	while( (s>tabname) && (*s != DIRCHAR) ) {
		s--;
	}

	if( maintable ) {
		if( *s == DIRCHAR ) s++;
		if( snprintf(fname,sizeof fname,"%s",s) >= (int)sizeof fname ||
		    snprintf(basename,sizeof basename,"%s",s) >= (int)sizeof basename ) {
			fprintf(stderr,"table name is too long: %s\n",s);
			return(-1);
		}
/*
		if( formcode == DODERIV ) strcat(basename," is_deriv"); 
		else if( formcode == DOWORD ) strcat(basename," indeclform"); 
*/	
		TmpGstr = blank;
		stype = 0;
		{
			gk_word *word = CreatGkword(1);
			if (!word) return -1;
			ScanAsciiKeys(basename,word,&TmpGstr,NULL);
			FreeGkword(word);
			stype = stemtype_of(&TmpGstr);
			if ((formcode == DOEND && !stype) ||
			    (formcode == DODERIV && !derivtype_of(&TmpGstr))) {
				fprintf(stderr,"unregistered %s table: %s\n",
				        formcode == DODERIV ? "derivation" : "ending",basename);
				return -1;
			}
		}
		
		if( formcode == DODERIV ) {
			
			add_morphflag(morphflags_of(&TmpGstr),IS_DERIV);
			if( snprintf(shortname,sizeof shortname,"%s.deriv",fname) >= (int)sizeof shortname )
				return(-1);
			if(! (finput=fopen(shortname,"r"))) {
				if( snprintf(shortname,sizeof shortname,"derivs%csource%c%s.deriv",
				             DIRCHAR, DIRCHAR, fname) >= (int)sizeof shortname )
					return(-1);
				if(! (finput=MorphFopen(shortname,"r"))) {
					printf("could not open [%s.deriv] or [%s]\n", fname,  shortname );
					return(-1);
				}
				if( snprintf(shortname,sizeof shortname,"%s%cout%c%s.out",
				             DERIVTABLEDIR,DIRCHAR,DIRCHAR,fname) >= (int)sizeof shortname ) {
					fclose(finput);
					return(-1);
				}
			}
		} else {
			if( snprintf(shortname,sizeof shortname,"%s.end",fname) >= (int)sizeof shortname )
				return(-1);
			if(! (finput=fopen(shortname,"r"))) {
				if( snprintf(shortname,sizeof shortname,"endtables%csource%c%s.end",
				             DIRCHAR, DIRCHAR, fname) >= (int)sizeof shortname )
					return(-1);
				if(! (finput=MorphFopen(shortname,"r"))) {
					printf("could not open [%s.end] or [%s]\n", fname,  shortname );
					return(-1);
				}
			}
			if( snprintf(shortname,sizeof shortname,"%s%cout%c%s.out",
			             ENDTABLEDIR,DIRCHAR,DIRCHAR,fname) >= (int)sizeof shortname ) {
				fclose(finput);
				return(-1);
			}
		}
			
	
		if(! (foutput=MorphFopen(shortname,"wb"))) {
	/*		fprintf(stderr,"could not open %s for writing\n", shortname );*/
			fclose(finput);
			return(-1);
		}
	} else {
		if( snprintf(fname,sizeof fname,"%s",s) >= (int)sizeof fname ) {
			fprintf(stderr,"table name is too long: %s\n",s);
			return(-1);
		}
		basename[0] = 0;
		if(! (finput=fopen(fname,"r"))) {
			fprintf(stderr,"could not open %s for reading\n", fname );
			return(-1);
		}
	}
	if ((formcode == DODERIV &&
	     !morpheus_runtime_string_append(
	         basename," is_deriv",sizeof basename)) ||
	    (formcode == DOWORD &&
	     !morpheus_runtime_string_append(
	         basename," indeclform",sizeof basename))) {
		fclose(finput);
		if (foutput) fclose(foutput);
		return(-1);
	}
	
	if( ! InitGstrMem() )  {
		fprintf(stderr,"Could not allocate storage for ending array\n" );
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		fclose(finput);
		if (foutput) fclose(foutput);
		return(-1);
	}

	while(fgets(line,sizeof line,finput) ) {
		if( is_blank(line) )
			continue;
		if( Is_comment(line) )
			continue;

/*
		if( maintable ) {
			if( AddEndLine(foutput,*line,basename) < 0 )

				break;
		} else {
*/
/*
fprintf(stderr,"basenam [%s] line [%s]\n", basename , line );
*/
			if( AddEndLine(/*foutput,*/line,basename) < 0 ) {
				status = -1;
				break;
			}
/*
		}
*/
	}

	if( ferror(finput) ) status = -1;
	if( fclose(finput) == EOF ) status = -1;
	if( maintable && formcode != DOWORD ) {
		PrntNewGstrings(foutput,1);
		if( ferror(foutput) ) status = -1;
		if( foutput != stdout && fclose(foutput) == EOF ) status = -1;
		foutput = NULL;
	} else if( foutput && foutput != stdout ) {
		if( fclose(foutput) == EOF ) status = -1;
		foutput = NULL;
	}
	if( status < 0 ) {
		ResetGstrBuf();
		return(-1);
	}
	
	if( snprintf(shortname,sizeof shortname,"%s%cascii%c%s.asc",
	             formcode == DODERIV ? DERIVTABLEDIR : ENDTABLEDIR,
	             DIRCHAR,DIRCHAR,fname) >= (int)sizeof shortname ) {
		fprintf(stderr,"ASCII table path is too long: %s\n",fname);
		return(-1);
	}
printf("%s\n", shortname );
	if( (foutput=MorphFopen(shortname,"w")) == NULL ) {
		fprintf(stderr,"Could not open [%s]\n", shortname );
		ResetGstrBuf();
		return(-1);
	} else {
		PrntNewGstrings(foutput,0);
		if( ferror(foutput) ) status = -1;
		if( fclose(foutput) == EOF ) status = -1;
	}
	if( stype & ADJSTEM ) stype |= NOUNSTEM;
	else if( stype & NOUNSTEM ) stype |= ADJSTEM;
/*
	indexendtables(stype);
*/
	ResetGstrBuf();
	return(status);

}

int
AddEndLine(/*FILE *f,*/ char *el, char *basename)
{
	char havestr[MAXWORDSIZE];
	gk_string * Have;
	gk_string * Avoid;
	gk_word * TmpGkword;

	Have = CreatGkString(1);
	Avoid = CreatGkString(1);
	TmpGkword = CreatGkword(1);
	if( ! Have || ! Avoid || ! TmpGkword ) {
		if( Have ) FreeGkString(Have);
		if( Avoid ) FreeGkString(Avoid);
		if( TmpGkword ) FreeGkword(TmpGkword);
		return(-1);
	}

	nextkey(el,havestr);
	if( ScanAsciiKeys(basename,TmpGkword,Have,Avoid) < 0 ||
	    ScanAsciiKeys(el,TmpGkword,Have,Avoid) < 0 ) {
		FreeGkString(Have);
		FreeGkString(Avoid);
		FreeGkword(TmpGkword);
		return(-1);
	}
/*
printf("indeclform %d %d\n",  has_morphflag(morphflags_of(TmpGkword),INDECLFORM),
has_morphflag(morphflags_of(Have),INDECLFORM) );
*/
	set_gkstring(Have,havestr);

/*printf("[%s] [%s]\n", havestr, basename );*/
	mk_end(havestr,Have,Avoid);
	if( morpheus_runtime_context_error(
	        morpheus_runtime_context_current()) !=
	    MORPHEUS_RUNTIME_ERROR_NONE ) {
		FreeGkString(Have);
		FreeGkString(Avoid);
		FreeGkword(TmpGkword);
		return(-1);
	}

	FreeGkString(Have);
	FreeGkString(Avoid);
	FreeGkword(TmpGkword);
	return(1);
}
