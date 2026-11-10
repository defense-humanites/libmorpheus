#include "morphlib_internal.h"
#include <limits.h>
#include <stdint.h>
#include <gkstring.h>
#include <endtags.h>
#define LINDEXSUFFIX "lindex"

#include "retrentry.proto.h"
#include "morphstrcmp.proto.h"
endtags *
init_preind(char *fname, int *maxkeys)
{
	FILE *f;
	endtags *etags;
	long file_size;
	size_t divisor;
	size_t record_count;
	size_t sofar;
	size_t i;
	int written;
	unsigned char *records;
	char tmp[LONGSTRING];

	if (!maxkeys) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	*maxkeys = 0;
	if (!fname) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	written = snprintf(tmp,sizeof tmp,"%s.%s",fname,LINDEXSUFFIX);
	if (written < 0 || written >= (int)sizeof tmp) {
		morpheus_runtime_diagnostic("preindex path is too long: %s\n",fname);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	
	if( (f=MorphFopen(tmp,"rb"))==NULL) {
		morpheus_runtime_diagnostic("init_preind: could not open %s\n", tmp );
		return( NULL );
	}
	
	divisor = (size_t)KEYLEN + sizeof tagoffset_of(etags);
	if (fseek(f,0L,SEEK_END) != 0 || (file_size = ftell(f)) < 0 ||
	    (uintmax_t)file_size > (uintmax_t)SIZE_MAX ||
	    fseek(f,0L,SEEK_SET) != 0 || (size_t)file_size % divisor != 0) {
		morpheus_runtime_diagnostic("invalid preindex size for %s\n",tmp);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		fclose(f);
		return(NULL);
	}
	record_count = (size_t)file_size/divisor;
	if (record_count > (size_t)INT_MAX ||
	    record_count > SIZE_MAX/sizeof *etags-1) {
		morpheus_runtime_diagnostic("preindex is too large: %s\n",tmp);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		fclose(f);
		return(NULL);
	}
	etags = (endtags *)calloc(record_count+1,sizeof *etags);
	if (!etags) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		fclose(f);
		return(NULL);
	}

/*
 * Read the records through one buffer rather than one ReadKey() per
 * record, so the C library issues a few system calls instead of one per
 * stdio buffer; the WebAssembly build pays for every call. The layout is
 * the one WriteKey() produces: KEYLEN key bytes, then the offset as four
 * little-endian bytes (get_int32()).
 */
	records = record_count ? (unsigned char *)malloc(record_count*divisor) : NULL;
	if (record_count && !records) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		free(etags);
		fclose(f);
		return(NULL);
	}
	sofar = 0;
	while (sofar < record_count*divisor) {
		size_t remaining = record_count*divisor-sofar;
		int requested = remaining > (size_t)INT_MAX ? INT_MAX : (int)remaining;
		int nread = vax_fread(records+sofar,1,requested,f);

		if (nread != requested) {
			morpheus_runtime_diagnostic("short read while loading %s\n",tmp);
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			free(records);
			free(etags);
			fclose(f);
			return(NULL);
		}
		sofar += (size_t)nread;
	}
	for(i=0; i < record_count; i++) {
		const unsigned char *record = records+i*divisor;
		unsigned int byte;
		morpheus_stemlib_offset tagoffset = 0;

		memcpy(tagstring_of(etags+i),record,(size_t)KEYLEN);
		for (byte = 0; byte < sizeof tagoffset; byte++) {
			tagoffset |= (morpheus_stemlib_offset)record[KEYLEN+byte]
				<< (8U*byte);
		}
		tagoffset_of(etags+i) = tagoffset;
	}
	free(records);
/*
printf("flen %d i %d last tags [%s]\n", flen, i , tagstring_of(etags+i) );
*/
	fclose(f);
	*maxkeys = (int)record_count;
	return(etags);
}

long
ChckPreIndex(endtags *etags, char *tag, int ntags, int exact_match,
             int (*scmp)(char *, char *))
{
	int rval;
	long roff;
	char curtag[KEYLEN+1];

	if (!tag || !scmp || ntags < 0 || (!etags && ntags > 0)) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return((long)-1);
	}
	if (!etags || !ntags)
		return((long)-1);
	if( Xstrlen(tag) > KEYLEN ) exact_match = NO;
	strncpy(curtag,tag,KEYLEN);
	curtag[KEYLEN] = 0;
	rval = binlook( (char *)etags , curtag , ntags , (int)sizeof *etags , exact_match ,scmp );
	if( rval < 0 )
		return((long) -1 );

	if( ! rval )
		roff = 0;
	else {
		/* The pre-index stores 32-bit offsets. Callers treat a negative
		 * value as failure, so refuse an offset that long cannot hold
		 * where long is also 32 bits (ILP32, wasm32). */
		morpheus_stemlib_offset tagoffset = tagoffset_of(etags+rval);
#if LONG_MAX < UINT32_MAX
		if (tagoffset > (morpheus_stemlib_offset)LONG_MAX) {
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			return((long) -1 );
		}
#endif
		roff = (long)tagoffset;
	}

return( roff  );
}


/*
 * ChckFullIndex() reads one entry of a stem index per lookup, several
 * times per analyzed word. Opening the file each time made open() and
 * close() a measurable part of an analysis, so the context keeps the few
 * index files it reads open, keyed by their full path, until it is
 * destroyed. A file that fails a seek or a read is closed and forgotten.
 */
static FILE *
open_index_file(char *fname, int *cached)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	char path[BUFSIZ];
	FILE *f;
	int i;

	*cached = 0;
	MorphPathName(fname,path);
	if (!path[0]) return(NULL);
	for (i = 0; i < MORPHEUS_INDEX_FILE_CACHE_SIZE; i++) {
		if (context->index_files[i] &&
		    strcmp(context->index_file_paths[i],path) == 0) {
			*cached = 1;
			return(context->index_files[i]);
		}
	}
	if ((f = MorphFopen(fname,"r")) == NULL) return(NULL);
	for (i = 0; i < MORPHEUS_INDEX_FILE_CACHE_SIZE; i++) {
		if (!context->index_files[i]) {
			char *copy = malloc(strlen(path) + 1);

			if (!copy) break;
			strcpy(copy,path);
			context->index_file_paths[i] = copy;
			context->index_files[i] = f;
			*cached = 1;
			break;
		}
	}
	return(f);
}

static void
release_index_file(FILE *f, int cached, int failed)
{
	morpheus_runtime_context *context;
	int i;

	if (!cached) {
		fclose(f);
		return;
	}
	if (!failed) return;
	context = morpheus_runtime_context_current();
	for (i = 0; i < MORPHEUS_INDEX_FILE_CACHE_SIZE; i++) {
		if (context->index_files[i] == f) {
			fclose(f);
			free(context->index_file_paths[i]);
			context->index_files[i] = NULL;
			context->index_file_paths[i] = NULL;
			return;
		}
	}
}

int ChckFullIndex(char *s, char *keys, char *fname, long offset,
                  int (*scmp)(const char *, const char *, size_t))
{
	FILE * f;
	int cached;
	int failed = 0;
	register char * a;
	char buf[BUFSIZ*4];
	size_t slen;
	int comp;
	int rval = 0;
	int i;
int firstline = 1;

	if (keys) *keys = 0;
	if (!s || !keys || !fname || !scmp) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}

	if( (f=open_index_file(fname,&cached))==NULL) {
		morpheus_runtime_diagnostic("ChckFullIndex(): could not open:%s\n", fname );
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	if (offset < 0 || fseek(f,offset,SEEK_SET) != 0) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		release_index_file(f,cached,1);
		return(0);
	}
/*
printf("starting off at %ld\n", offset);
*/
	slen = strlen(s);
	while(fgets(buf,(int)sizeof buf , f)) {

/*
 * this little dance splits the line into two parts, the initial
 * key and everthing that follows. if you do not null terminate that
 * initial string one way or another, you end up having a string
 * such as "basile" get matched against "basileu"
 */



/*
		comp = morphstrncmp(s,buf,slen);
*/
		comp = (*scmp)(s,buf,slen);

/*
if( firstline ) {
morpheus_runtime_diagnostic("starts comp [%d] s [%s] buf [%s]\n", comp , s , buf );
firstline = 0;
}
*/
		if( ! comp && isspace((unsigned char)*(buf+slen)) ) {
			a = buf+slen;
			while(isspace((unsigned char)*a)) a++;
			Xstrncpy(keys,a,LONGSTRING);
			rval = 1;
			break;
		} else if (comp < 0 ) {
			rval = 0;
			break;
		}
	}
	if (ferror(f)) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		rval = 0;
		failed = 1;
	}
/*
morpheus_runtime_diagnostic("ends comp [%d] s [%s] buf [%s]\n", comp , s , buf );
getchar();
*/
	release_index_file(f,cached,failed);
	return(rval);
}
