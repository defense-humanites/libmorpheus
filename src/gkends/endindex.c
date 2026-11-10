#include <gkstring.h>
#include <limits.h>
#include <stdint.h>
#include "gkends_internal.h"
#include "../morphlib/runtime_context_internal.h"

#include "../morphlib/morphstrcmp.proto.h"
#include "endfiles.h"
#include "gkdict.h"
#define MAXENDTAGS 100

#include "endindex.proto.h"

/*int dictstrcmp(), dictstrncmp(), morphstrcmp(), morphstrncmp();*/

static endind *load_end_index(endind **, char *, const char *);

static endind *
load_end_index(endind **slot, char *filename, const char *description)
{
	endind *index;

	if (*slot) return(*slot);
	index = calloc(1,sizeof *index);
	if (!index) {
		morpheus_runtime_diagnostic("could not allocate %s\n",description);
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		return(NULL);
	}
	if (!init_endind(filename,index)) {
		free(index);
		return(NULL);
	}
	*slot = index;
	return(index);
}

int
chcknend(char *endstr, char *keys)
{
	long startoff;
	char tmpendstr[MAXWORDSIZE+1];
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	endind *NomEtags;

	Xstrncpy(tmpendstr,endstr,(int)sizeof  tmpendstr);
	/*
	 * ignore '_' (long marker), so that a simple 'a' will match
	 * an "a_".
	 */
	stripquant(tmpendstr);
	
	NomEtags = load_end_index(&context->nominal_ending_index,NENDLIST,
		"nominal ending index");
	if (!NomEtags) return(0);
	return( checkendind(NomEtags,tmpendstr,keys,morphstrncmp));
}


int
chckdictent(char * possent, char *keys)
{
	long startoff;
	char tmpendstr[MAXWORDSIZE+1];
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	endind *DictEntTags;

	Xstrncpy(tmpendstr,possent,(int)sizeof  tmpendstr);
	/*
	 * ignore '_' (long marker), so that a simple 'a' will match
	 * an "a_".
	 */
	stripquant(tmpendstr);
	
	DictEntTags = load_end_index(&context->dictionary_entry_index,DICTENTLIST,
		"dictionary entry index");
	if (!DictEntTags) return(0);
	return( checkendind(DictEntTags,tmpendstr,keys,strncmp));
}

int
chckcmpvb(char *endstr, char *keys)
{
	long startoff;
	char tmpendstr[MAXWORDSIZE+1];
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	endind *CmpVbtags;

	Xstrncpy(tmpendstr,endstr,(int)sizeof  tmpendstr);
	/*
	 * ignore '_' (long marker), so that a simple 'a' will match
	 * an "a_".
	 */
	stripquant(tmpendstr);
	
	CmpVbtags = load_end_index(&context->compound_verb_index,CMPVBLIST,
		"compound verb index");
	if (!CmpVbtags) return(0);
	return( checkendind(CmpVbtags,tmpendstr,keys,strncmp));
}

int
chckend(char *endstring) 
{
	char tmp[LONGSTRING];

	tmp[0] = 0;

	return(chckvend(endstring,tmp)||chcknend(endstring,tmp));
}

int
chckvend(char *endstr, char *keys)
{
	long startoff;
	int curhit;
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	endind *VbEtags;
	
	VbEtags = load_end_index(&context->verb_ending_index,VENDLIST,
		"verb ending index");
	if (!VbEtags) return(0);
	curhit = checkendind(VbEtags,endstr,keys,morphstrncmp);

	return(curhit);
}

int
chckvstem(char *stemstr, char *keys)
{
	long startoff;
	int curhit;
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	endind *VstemEtags;
	
	VstemEtags = load_end_index(&context->verb_stem_index,VBINDEX,
		"verb stem index");
	if (!VstemEtags) return(0);
	curhit = checkendind(VstemEtags,stemstr,keys,morphstrncmp);

	return(curhit);
}

int
chckdvend(char *endstr, char *keys)
{
	long startoff;
	int curhit;
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	endind *DerEtags;
	
	DerEtags = load_end_index(&context->derivation_ending_index,DERENDLIST,
		"derivation ending index");
	if (!DerEtags) return(0);

	curhit = checkendind(DerEtags,endstr,keys,morphstrncmp);

	return(curhit);
}

endind *
init_endind(char *fname, endind *etags)
{
	FILE *f = NULL;
	char *buffer = NULL;
	char **pointers = NULL;
	long file_size;
	size_t file_length;
	size_t sofar = 0;
	size_t nlines = 0;
	size_t i;
	int nread;

/*
 * grc 3/12/91
 * clalloc() seems not to exist in ANSI C
 	char * clalloc();
 */
 	if( (f=MorphFopen(fname,"r"))==NULL) {
		morpheus_runtime_diagnostic("init_endind: could not open %s\n", fname );
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return( NULL );
	}
	if (fseek(f,0L,SEEK_END) != 0 || (file_size = ftell(f)) < 0 ||
	    fseek(f,0L,SEEK_SET) != 0) {
		morpheus_runtime_diagnostic("could not measure %s\n",fname);
		goto invalid_index;
	}
	if ((uintmax_t)file_size > (uintmax_t)(SIZE_MAX-1)) {
		morpheus_runtime_diagnostic("ending index is too large: %s\n",fname);
		goto invalid_index;
	}
	file_length = (size_t)file_size;

/*
 * The ANSI port replaced the historical clalloc allocation of flen + 1
 * elements with calloc.
 */
	buffer = (char *)calloc(file_length + 1,sizeof *buffer);
	if (!buffer) {
		morpheus_runtime_diagnostic("could not build buffer for endtags\n");
		goto no_memory;
	}
/*
 * Request the whole file at once rather than BUFSIZ at a time: the C
 * library then reads it through at most a few system calls instead of
 * thousands, which matters where every call crosses into JavaScript
 * (the WebAssembly build). The loop only remains for a file longer than
 * INT_MAX, the most vax_fread() accepts per call.
 */
	while (sofar < file_length) {
		size_t remaining = file_length-sofar;
		int requested = remaining > (size_t)INT_MAX ? INT_MAX : (int)remaining;

		nread = vax_fread(buffer+sofar,sizeof *buffer,requested,f);
		if (nread != requested) {
			morpheus_runtime_diagnostic("short read while loading %s\n",fname);
			goto invalid_index;
		}
		sofar += (size_t)nread;
	}
	xFclose(f);
	f = NULL;
	if (file_length) {
		nlines = 1;
		for (i = 0; i + 1 < file_length; i++) {
			if (buffer[i] == '\n') nlines++;
		}
	}
	if (nlines > (size_t)INT_MAX) {
		morpheus_runtime_diagnostic("ending index has too many entries: %s\n",fname);
		goto invalid_index;
	}
	if (nlines) pointers = (char **)calloc(nlines,sizeof *pointers);
	if (nlines && !pointers) {
		morpheus_runtime_diagnostic("ran out of memory in init_endind\n");
		goto no_memory;
	}
	if (nlines) {
		size_t current = 1;

		pointers[0] = buffer;
		for (i = 0; i < file_length; i++) {
			if (buffer[i] == '\n') {
				buffer[i] = 0;
				if (i + 1 < file_length)
					pointers[current++] = buffer+i+1;
			}
		}
	}

	endbuffer_of(etags) = buffer;
	endeptr_of(etags) = pointers;
	endlen_of(etags) = (int)nlines;
/*
	printf("nread %d flen %ld nlines %d\n", nread ,flen , nlines);
	for(i=0;i<10;i++)
		printf("%d) [%s]\n", i , *(pp+i) );
	getchar();
	*/
	return(etags);

no_memory:
	morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
	if (f) xFclose(f);
	free(buffer);
	free(pointers);
	return(NULL);

invalid_index:
	morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
	if (f) xFclose(f);
	free(buffer);
	free(pointers);
	return(NULL);
}

int
checkendind(endind *etags, char *endstr, char *keys, int (*scmp)(const char *, const char *, size_t))
{
	int high = 0;
	int low = 0;
	int mid = 0;
	int comp;
	int ntags;
	char curtag[MAXWORDSIZE];
	size_t taglen;
	char ** pp;
	
	/*
	 * the table is of the form "ending<SPACE>key1<SPACE>key2<SPACE> ..."
	 */
	Xstrncpy(curtag,endstr,MAXWORDSIZE);
	if (!morpheus_runtime_string_append(curtag," ",sizeof curtag))
		return(0);
	taglen = strlen(curtag);
	
	ntags = endlen_of(etags);
	pp = endeptr_of(etags);

	high = ntags-1;
	low = 0 ;
	
	while( low<=high ) {
		mid = (low+high)/2 ;
		/*comp = morphstrncmp( curtag , *(pp+mid) , taglen );*/
		comp = (*scmp)( curtag , *(pp+mid) , taglen );
/*
morpheus_runtime_diagnostic("comparing [%s] and [%s]\n", curtag , *(pp+mid) );
*/
		if( comp < 0 ) 
			high = mid - 1 ;
		else if ( comp > 0 )
			low = mid + 1;
		else  { /* found match */
/*
printf("A returning with curtag [%s] tagstring [%s]\n", curtag, *(pp+mid) );
*/
			Xstrncpy(keys,*(pp+mid) + taglen,LONGSTRING);
			return(1);
		}
	}
/*	if( mid > 0 ) {
		for(i=mid-1;i<ntags;i++) {
			if( morphstrcmp(curtag,tagstring_of(etags+i)) < 0 ) break;
		}
		if( i > 0 ) i--;
	} else
		i = 0;
		*/
/*
printf("B returning with curtag [%s] tagstring [%s] and off %d\n", curtag, tagstring_of(etags+i) , tagoffset_of(etags+i) );
*/
	*keys = 0;
	return(0);
}
