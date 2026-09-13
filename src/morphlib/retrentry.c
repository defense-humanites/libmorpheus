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
	size_t i;
	int written;
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
		fprintf(stderr,"preindex path is too long: %s\n",fname);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(NULL);
	}
	
	if( (f=MorphFopen(tmp,"rb"))==NULL) {
		fprintf(stderr,"init_preind: could not open %s\n", tmp );
		return( NULL );
	}
	
	divisor = (size_t)KEYLEN + sizeof tagoffset_of(etags);
	if (fseek(f,0L,SEEK_END) != 0 || (file_size = ftell(f)) < 0 ||
	    (uintmax_t)file_size > (uintmax_t)SIZE_MAX ||
	    fseek(f,0L,SEEK_SET) != 0 || (size_t)file_size % divisor != 0) {
		fprintf(stderr,"invalid preindex size for %s\n",tmp);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		fclose(f);
		return(NULL);
	}
	record_count = (size_t)file_size/divisor;
	if (record_count > (size_t)INT_MAX ||
	    record_count > SIZE_MAX/sizeof *etags-1) {
		fprintf(stderr,"preindex is too large: %s\n",tmp);
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

	for(i=0; i < record_count; i++) {
		morpheus_stemlib_offset tagoffset;

		if( ReadKey(tagstring_of(etags+i),&tagoffset,f) != 1) {
			fprintf(stderr,"short read while loading %s\n",tmp);
			morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
			free(etags);
			fclose(f);
			return(NULL);
		}
		tagoffset_of(etags+i) = tagoffset;
/*
if( ! (i % 25) )
printf(" i %d last tags [%s]\n",  i , tagstring_of(etags+i) );
*/
	}
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
	else
		roff = tagoffset_of(etags+rval);
	
return( roff  );
}


int ChckFullIndex(char *s, char *keys, char *fname, long offset,
                  int (*scmp)(const char *, const char *, size_t))
{
	FILE * f;
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

	if( (f=MorphFopen(fname,"r"))==NULL) {
		fprintf(stderr,"ChckFullIndex(): could not open:%s\n", fname );
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	if (offset < 0 || fseek(f,offset,SEEK_SET) != 0) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		fclose(f);
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
fprintf(stderr,"starts comp [%d] s [%s] buf [%s]\n", comp , s , buf );
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
	}
/*
fprintf(stderr,"ends comp [%d] s [%s] buf [%s]\n", comp , s , buf );
getchar();
*/
	fclose(f);
	return(rval);
}
