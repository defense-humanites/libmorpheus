#include "morphlib_internal.h"
#include <limits.h>
#include <contract.h>

#include "loadeuph.proto.h"

static const gk_string Blnk;

static int next_bounded_key(char *keylist, char *key, size_t capacity)
{
	char *start;
	size_t length;

	if (!keylist || !key || !capacity) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	start = keylist;
	while (isspace((unsigned char)*start)) start++;
	length = 0;
	while (start[length] && !isspace((unsigned char)start[length])) length++;
	if (!length || length >= capacity) {
		*key = 0;
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	return(nextkey(keylist,key));
}

gk_string *
load_euph_tab(char *filename, int *gotno, int is_contr)
{
	gk_string *euph_table = NULL;
	int nunits;
	FILE *f = NULL;
	int i;
	char * s;
	char * raw;
	char * cooked;
	char line[BUFSIZ];
	char tmp[MAXWORDSIZE];
	gk_string CurStr;
	gk_word *TmpGkword = NULL;

	if (!gotno) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	*gotno = 0;
	if (!filename || !*filename) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}

	if( (f=MorphFopen(filename,"r")) == NULL ) {
		morpheus_runtime_diagnostic("Could not open [%s]\n", filename );
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	TmpGkword = CreatGkword(1);
	if (!TmpGkword)
		goto no_memory;
	
	nunits = count_rlines(f);
	if (nunits < 0)
		goto failed;
	
	euph_table = CreatGkString(nunits+1);
	if( ! euph_table ) {
		morpheus_runtime_diagnostic("no memory for %d-entry euphony table\n", nunits+1 );
		goto no_memory;
	}

	for(i=0;GetTableLine(line,sizeof line,f);i++) {
		if( i >= nunits) {
			morpheus_runtime_diagnostic("hey! more than %d contracts!\n", nunits);
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			goto failed;
		}
		CurStr = Blnk;
		s = gkstring_of(&CurStr);
/*
printf("line:%s\n", line );
*/
		if (!next_bounded_key(line,s,MAXSUBSTRING) ||
		    !next_bounded_key(line,s+MAXSUBSTRING,
		                      MAXWORDSIZE-MAXSUBSTRING))
			goto failed;
		/*
		 * if raw and cooked are the same then we hit an infinitely
		 * recursive loop. mark cooked with a diaeresis if it is the same as raw so
		 * that this will not happen.
		 */
		 raw = s;
		 cooked = s+MAXSUBSTRING;

		 if( ! Xstrncmp(raw,cooked,Xstrlen(raw)) && Xstrlen(raw) > 1 && is_contr == YES) {
				
		 		tmp[0] = *cooked;
		 		tmp[1] = '+';
		 		tmp[2] = 0;
			if (!morpheus_runtime_string_append(
			    tmp,cooked+1,sizeof tmp)) goto failed;
		 		Xstrncpy(cooked,tmp,MAXWORDSIZE);

		 }
		set_morphflag(morphflags_of(prvb_gstr_of(TmpGkword)),0);
		ScanAsciiKeys(line,TmpGkword,&CurStr,NULL);
		if (morpheus_runtime_context_error(
		    morpheus_runtime_context_current()) !=
		    MORPHEUS_RUNTIME_ERROR_NONE)
			goto failed;
/*
		InsertGstr(euph_table,&CurStr,i,strcmp,YES);
*/
		add_morphflags(&CurStr,morphflags_of(prvb_gstr_of(TmpGkword)));
		*(euph_table+i) = CurStr;
	}
	if (ferror(f) || i != nunits) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		goto failed;
	}
	* gotno = i;

/* 
 * grc 12/15/96
 *
 * took this out because it was sorting "ds -> ss epic" before "ds --> s"
 * 
 * The default future of yeu/dw was "yeu/ssw epic".
 * 
 * You now need to set the sort order in the file -- not ideal.
 *
	qsort(euph_table,(size_t)i,(size_t)sizeof * euph_table,RevCompByStr);
*/

/*
for(i=0;i<*gotno;i++) printf("%d) [%s] [%s]\n", i, gkstring_of(euph_table+i),
gkstring_of(euph_table+i)+MAXSUBSTRING );
*/
	xFclose(f);
	FreeGkword(TmpGkword);
	return(euph_table);

no_memory:
	morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);

failed:
	if (f) xFclose(f);
	if (TmpGkword) FreeGkword(TmpGkword);
	if (euph_table) FreeGkString(euph_table);
	return(NULL);
}

int count_rlines(FILE *f)
{
	char line[BUFSIZ];
	int nlines = 0;

	if (!f) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(-1);
	}
	while(GetTableLine(line,sizeof line,f)) {
		if (nlines >= INT_MAX-1) {
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			return(-1);
		}
		nlines++;
	}
	if (ferror(f) || fseek(f,0L,SEEK_SET) != 0) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(-1);
	}
	return(nlines);
}
