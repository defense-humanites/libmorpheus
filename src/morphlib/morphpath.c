#include "morphlib_internal.h"
#include <gkstring.h>

#include "morphpath.proto.h"

FILE *
 MorphFopen(char *fname, char *mode)
{
 	FILE * f;
 	char tmpname[BUFSIZ];

	if (!fname || !*fname || !mode || !*mode) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	morpheus_runtime_context_current()->files_opened++;
 	MorphPathName(fname,tmpname);
	if (!tmpname[0]) return(NULL);

	if( !(f=fopen(tmpname,mode)) ) {
		morpheus_runtime_diagnostic("MorphFopen: could not open [%s]\n", tmpname );
/* just die here -- should go up higher but will live with this for now. */

/*
 		return(NULL);
*/
 	}
 	
	return(f);
}

int NumFilesOpened(void)
{
	int filesopened = morpheus_runtime_context_current()->files_opened;

	printf("filesopened [%d]\n", filesopened );
	return(filesopened);
}

/*
 * take a short pathname (e.g. "lib/vowcontr.table") and derive from it a
 * full path name (e.g. "/usr/src/local/morpheus/lib/vowcontr.table")
 */
void MorphPathName(char *shorts, char *full)
 {
 	char * s;
 	short vRefNum;
 
 	
#ifdef MACINTOSH
	char *volName = morpheus_runtime_context_current()->volume_name;

	if( ! volName[0] ) {
 		GetVol((StringPtr) volName, &vRefNum);
 		PtoCstr((StringPtr)volName);
 	}
#endif
 	
/*
 	sprintf(full,"/as/fass/faculty/gcrane/morph/stemlib/%s", shorts );
*/
	const char *language_directory;
	int written;

	if (!full) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return;
	}
	full[0] = 0;
	if (!shorts || !*shorts) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return;
	}
	s = morpheus_runtime_context_current()->stemlib_path;
	if (!s) s = getenv("MORPHLIB");

	if( ! s ) {
		full[0] = 0;
		morpheus_runtime_diagnostic("MORPHLIB not set in your environment!\n");
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return;
	}

	if( cur_lang() == LATIN )
		language_directory = "Latin";
	else if ( cur_lang() == ITALIAN )
		language_directory = "Italian";
	else
		language_directory = "Greek";

	written = snprintf(full,BUFSIZ,"%s/%s/%s",s,language_directory,shorts);
	if (written < 0 || written >= BUFSIZ) {
		full[0] = 0;
		morpheus_runtime_diagnostic("MorphPathName: path is too long\n");
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return;
	}
	
 	/*
 	 * this checks to make keep compatibility with the Mac
 	 * pathname conventions
 	 */
	if( DIRCHAR != '/' ) {
		s=full;
		while(*s) {
			if( *s == '/' ) *s = DIRCHAR;
			s++;
		}
	} else if (DIRCHAR == '/' ) {
		s=full;
		while(*s) {
			if( *s == ':' ) *s = DIRCHAR;
			s++;
		}
	}
 }
 
 
void SysFolderFile(char *fullname, char *shorts)
 {
 	char * s;
 	short vRefNum = 0;
 	char vName[128];
 	
#ifdef MACINTOSH
	char *volName = morpheus_runtime_context_current()->volume_name;

	GetVol((StringPtr)vName,&vRefNum);
 	PtoCstr((StringPtr)vName);
  	
 	sprintf(fullname,"%s:[System Folder]:%s",volName, shorts );
#endif
	if (!fullname || !shorts) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return;
	}
 	/*
 	 * this checks to make keep compatibility with the Mac
 	 * pathname conventions
 	 */
	if( DIRCHAR != '/' ) {
		s=fullname;
		while(*s) {
			if( *s == '/' ) *s = DIRCHAR;
			s++;
		}
	}
 }
