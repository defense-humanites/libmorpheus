#include <gkstring.h>
#include <limits.h>
#include "gkends_internal.h"
#include "../morphlib/runtime_context_internal.h"
#include "endfiles.h" 

#include "getcurrend.proto.h"

static void
clear_ending_cache(morpheus_runtime_context *context)
{
	int i;

	for (i = 0; i < MORPHEUS_END_CACHE_SIZE; i++) {
		if (context->ending_cache[i]) {
			FreeGkString(context->ending_cache[i]);
			context->ending_cache[i] = NULL;
		}
	}
	context->ending_cache_current = 0;
	context->ending_cache_size = 0;
}

static morpheus_runtime_context *
current_ending_cache(void)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	int language = cur_lang();

	if (!context->ending_cache_initialized) {
		context->ending_cache_language = language;
		context->ending_cache_initialized = 1;
	} else if (context->ending_cache_language != language) {
		clear_ending_cache(context);
		context->ending_cache_language = language;
	}
	return(context);
}

gk_string *
GetCurrentEndList(gk_string *gstr, int *lnump)
{
	char fname[MAXPATHNAME];
	gk_string * CurEndList;
	FILE * f  = NULL;
	int maxend = 0;
	int rval;
	int i = 0;
	int lno = 0;
	int written;
	char *stemtype_name;

	if (!gstr || !lnump) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	*lnump = 0;
	
	CurEndList = CheckEndCache(gstr);

	if( CurEndList) {
		for(i=0;;i++) {
			if( ! gkstring_of(CurEndList+i)[0] ) break;
		}
		*lnump = i;
		return(CurEndList);
	}

	stemtype_name = NameOfStemtype(stemtype_of(gstr));
	if (!stemtype_name || !stemtype_name[0]) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	written = snprintf(fname,sizeof fname,"%s/out/%s.out",ENDTABLEDIR,
		stemtype_name);
	if (written < 0 || written >= (int)sizeof fname) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}

	if( (f=MorphFopen(fname,"rb")) == NULL ) {
		morpheus_runtime_diagnostic("stemtype %o, could not open %s\n", stemtype_of(gstr), fname );
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}

	lno = get_endheader(f,&maxend);
	if( lno <= 0 ) {
		morpheus_runtime_diagnostic("problem with endfile [%s]\n", NameOfStemtype(stemtype_of(gstr)) );
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		xFclose(f);
		f = NULL;
		return(NULL);
	}

/*
printf("opening %s %d %d %ld\n", NameOfStemtype(stemtype_of(gstr)),
morpheus_runtime_context_current()->ending_cache_current, lno,
(long) (lno * (sizeof *gstr - (sizeof gkstring_of(gstr) + maxend ) )) );
*/
	
	if (lno > INT_MAX-2) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		xFclose(f);
		return(NULL);
	}
	CurEndList = (gk_string *) CreatGkString( lno + 2 );

	if( ! CurEndList ) {
		morpheus_runtime_diagnostic("Out of memory loading in %d new endings!\n", lno+2);
		xFclose(f);
		f = NULL;
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		return(NULL);
	}

	for(i=0;i<lno;i++ ) {
		rval=ReadEnding(f,CurEndList+i,maxend);

		if (rval <= 0 ) {
			morpheus_runtime_diagnostic("hey! fname [%s] wanted [%d] endings got [%d]!\n", fname, lno , i );
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			xFclose(f);
			FreeGkString(CurEndList);
			return(NULL);
		}
		set_stemtype(CurEndList+i,stemtype_of(gstr));
	}
/*
morpheus_runtime_diagnostic("about to close %s\n", NameOfStemtype(stemtype_of(gstr)) );
*/
	xFclose(f);
	f = NULL;

	*lnump = lno;
	InsertEndCache(CurEndList);
	return(CurEndList);
}

gk_string *
CheckEndCache(gk_string *gstr)
{
	morpheus_runtime_context *context = current_ending_cache();
	int i;
	
	
cacheconsistent();

	for(i=0;i<MORPHEUS_END_CACHE_SIZE;i++) {
		if(! context->ending_cache[i] ) break;
		if( stemtype_of(context->ending_cache[i]) == stemtype_of(gstr))
			return(context->ending_cache[i]);
	}
	return(NULL);
}

void
cacheconsistent(void)
{
	morpheus_runtime_context *context = current_ending_cache();
	int i;
	
	for(i=0;i<MORPHEUS_END_CACHE_SIZE;i++) {
		if( ! context->ending_cache[i] ) break;
		if( ! NameOfStemtype(stemtype_of(context->ending_cache[i])) ) {
			if( i > 1 ) 
				morpheus_runtime_diagnostic("%d) prev type %s\n", i, 
					NameOfStemtype(stemtype_of(context->ending_cache[i-1])) );
			else
				morpheus_runtime_diagnostic("first stemtype has been zapped!\n");
			break;
		}
	}
	if( i < context->ending_cache_size ) {
		morpheus_runtime_diagnostic("saw only %d of %d ending tables\n", i,
			context->ending_cache_size);
	} else
		context->ending_cache_size = i;
	
}
void
InsertEndCache(gk_string *gstr)
{
	morpheus_runtime_context *context = current_ending_cache();
	int current = context->ending_cache_current;
	
	if( context->ending_cache[current] ) {
		FreeGkString(context->ending_cache[current]);
		context->ending_cache[current] = NULL;
/*
printf("dumping %s curc %d\n",
NameOfStemtype(stemtype_of(context->ending_cache[current])), current);
*/
	}

	context->ending_cache[current] = gstr;

	if( ++context->ending_cache_current >= MORPHEUS_END_CACHE_SIZE )
		context->ending_cache_current = 0;
}
