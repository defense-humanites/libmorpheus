#include "morphlib_internal.h"
#include <limits.h>
#include <stdint.h>
#include <string.h>
#include <gkstring.h>

#include "endio.proto.h"

#define LEGACY_GROUP_DOMAIN_INDEX 1
#define LEGACY_GROUP_DOMAIN_MASK ((unsigned char)040)

static int valid_ending_io(FILE *f, const gk_string *gstr, int maxend)
{
	if (f && gstr && maxend > 0 && maxend <= MAXWORDSIZE) return(1);
	morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
	return(0);
}

static int32 pack_word_form(word_form form)
{
	return((int32)(
	    ((int32)voice_of(form)&UINT32_C(0x07))|
	    (((int32)mood_of(form)&UINT32_C(0x0f))<<3U)|
	    (((int32)tense_of(form)&UINT32_C(0x0f))<<7U)|
	    (((int32)person_of(form)&UINT32_C(0x07))<<11U)|
	    (((int32)number_of(form)&UINT32_C(0x07))<<14U)|
	    (((int32)case_of(form)&UINT32_C(0x3f))<<17U)|
	    (((int32)degree_of(form)&UINT32_C(0x03))<<23U)|
	    (((int32)gender_of(form)&UINT32_C(0x0f))<<25U)));
}

static void unpack_word_form(int32 packed, word_form *form)
{
	word_form decoded = {0};
	set_voice(decoded,(unsigned int)(packed&UINT32_C(0x07)));
	set_mood(decoded,(unsigned int)((packed>>3U)&UINT32_C(0x0f)));
	set_tense(decoded,(unsigned int)((packed>>7U)&UINT32_C(0x0f)));
	set_person(decoded,(unsigned int)((packed>>11U)&UINT32_C(0x07)));
	set_number(decoded,(unsigned int)((packed>>14U)&UINT32_C(0x07)));
	set_case(decoded,(unsigned int)((packed>>17U)&UINT32_C(0x3f)));
	set_degree(decoded,(unsigned int)((packed>>23U)&UINT32_C(0x03)));
	set_gender(decoded,(unsigned int)((packed>>25U)&UINT32_C(0x0f)));
	*form = decoded;
}

int WriteEnding(FILE *f, gk_string *gstr, int maxend)
{
	char stored_domains[MAXDOMAINS+1];
	int32 stored_form;

	if (!valid_ending_io(f,gstr,maxend)) return(-1);
	stored_form = pack_word_form(forminfo_of(gstr));
	memcpy(stored_domains,domains_of(gstr),sizeof stored_domains);
	if(Is_group_name(morphflags_of(gstr))) {
		if(stored_domains[0]) {
			morpheus_runtime_diagnostic("cannot encode group name with domains\n");
			return(-1);
		}
		stored_domains[LEGACY_GROUP_DOMAIN_INDEX]=(char)(
		    (unsigned char)stored_domains[LEGACY_GROUP_DOMAIN_INDEX]|
		    LEGACY_GROUP_DOMAIN_MASK);
	}

	localtrimwhite(gkstring_of(gstr),maxend);
	if(vax_fwrite(gkstring_of(gstr),sizeof *gkstring_of(gstr),maxend,f)
		!= maxend)
		goto outputerr;
	if(vax_fwrite(&stored_form,sizeof stored_form,1,f) != 1)
		goto outputerr;
	if(vax_fwrite(&dialect_of(gstr),sizeof dialect_of(gstr),1,f) != 1)
		goto outputerr;
	if(vax_fwrite(&geogregion_of(gstr),sizeof geogregion_of(gstr),1,f) != 1)
		goto outputerr;
	if(vax_fwrite(&stemtype_of(gstr),sizeof stemtype_of(gstr),1,f) != 1)
		goto outputerr;
	if(vax_fwrite(&derivtype_of(gstr),sizeof derivtype_of(gstr),1,f) != 1)
		goto outputerr;

	if(vax_fwrite(morphflags_of(gstr),1,MORPHFLAG_BYTES,f)
		!= MORPHFLAG_BYTES)
		goto outputerr;

	if(vax_fwrite(stored_domains,1,sizeof stored_domains,f) !=
	   (int)sizeof stored_domains)
		goto outputerr;

	return(1);
	outputerr:
		morpheus_runtime_diagnostic("output error!\n");
		return(-1);
}


int ReadEnding(FILE *f, gk_string *gstr, int maxend)
{
	int nread = 0;
	int32 stored_form;
	gk_string decoded = {0};

	if (!valid_ending_io(f,gstr,maxend)) return(-1);
	if((nread=vax_fread(gkstring_of(&decoded),sizeof *gkstring_of(&decoded),maxend,f))
		<= 0)
		goto inputerr;
	if(nread != maxend)
		return(-1);
	if((nread=vax_fread(&stored_form,sizeof stored_form,1,f))
		!= 1)
			goto inputerr;
	unpack_word_form(stored_form,&forminfo_of(&decoded));
	if((nread=vax_fread(&dialect_of(&decoded),sizeof dialect_of(&decoded),1,f)) != 1)
			goto inputerr;
	if((nread=vax_fread(&geogregion_of(&decoded),sizeof geogregion_of(&decoded),1,f))
		!= 1)
			goto inputerr;
	if((nread=vax_fread(&stemtype_of(&decoded),sizeof stemtype_of(&decoded),1,f)) != 1)
			goto inputerr;
	if((nread=vax_fread(&derivtype_of(&decoded),sizeof derivtype_of(&decoded),1,f)) != 1)
			goto inputerr;

	if((nread=vax_fread(morphflags_of(&decoded),1,MORPHFLAG_BYTES,f))
		!= MORPHFLAG_BYTES)
			goto inputerr;

	if((nread=vax_fread(domains_of(&decoded),1,MAXDOMAINS+1,f)) != MAXDOMAINS+1)
			goto inputerr;
	memset(morphflags_of(&decoded)+MORPHFLAG_BYTES,0,
	       MORPHFLAG_STORAGE_BYTES-MORPHFLAG_BYTES);
	if(!domains_of(&decoded)[0] &&
	   ((unsigned char)domains_of(&decoded)[LEGACY_GROUP_DOMAIN_INDEX] &
	    LEGACY_GROUP_DOMAIN_MASK)) {
		add_morphflag(morphflags_of(&decoded),GROUP_NAME);
		domains_of(&decoded)[LEGACY_GROUP_DOMAIN_INDEX]=(char)(
		    (unsigned char)domains_of(&decoded)[LEGACY_GROUP_DOMAIN_INDEX] &
		    (unsigned char)~LEGACY_GROUP_DOMAIN_MASK);
	}

	*gstr = decoded;
	return(1);
	inputerr:
		if( nread < 0 ) {
			morpheus_runtime_diagnostic("input error!\n");
		}
		return(nread);
}

/*
 * note that the size of maxstring when written in a file is 32 bits.
 * these routines make sure that, whether an int is 16 or 32 bits is
 * the size of a default int on the current system, we cast the value
 * to 32 bits.
 */
int set_endheader(FILE *f, int maxstring)
{
	int32 morph_version = MORPH_VERSION;
	int32 len;

	if(!f || maxstring <= 0 || maxstring > MAXWORDSIZE) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(-1);
	}
	len = (int32)maxstring;

	if(vax_fwrite(&morph_version,sizeof morph_version,1,f) != 1)
		return(-1);
	if(vax_fwrite(&len,sizeof len,1,f) != 1)
		return(-1);
	return(1);
}

/*
 * return the number of endings in this particular file
 */
int get_endheader(FILE *f, int *maxp)
{
	int32 morph_version;
	int32 len;
	long curpos, filelen;
	long endlen;
	size_t fixed_size;
	size_t unitsize;
	size_t payload_size;
	size_t nendings;
	long header_size;

	if (!maxp) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(-1);
	}
	*maxp = 0;
	if (!f) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(-1);
	}
	if(vax_fread(&morph_version,sizeof morph_version,1,f) != 1)
		return(-1);
	if( morph_version != MORPH_VERSION ) {
		morpheus_runtime_diagnostic("Hey! new version of Morpheus!\n");
		return(-1);
	}

	if(vax_fread(&len,sizeof len,1,f) != 1)
		return(-1);
	if(len <= 0 || len > (int32)INT_MAX || len > (int32)MAXWORDSIZE)
		return(-1);
	*maxp = (int)len;
	
	curpos = ftell(f);
	if(curpos < 0 || fseek(f,0L,SEEK_END) != 0)
		return(-1);
	filelen = ftell(f);
	if(filelen < 0 || fseek(f,curpos,SEEK_SET) != 0)
		return(-1);

	header_size = (long)(sizeof morph_version + sizeof len);
	if(filelen < header_size)
		return(-1);
	endlen = filelen - header_size;
	payload_size = (size_t)endlen;
	fixed_size = sizeof(int32)
		+ sizeof(((gk_string *)0)->gs_steminfo)
		+ sizeof(((gk_string *)0)->gs_dialect)
		+ sizeof(((gk_string *)0)->gs_derivtype)
		+ sizeof(((gk_string *)0)->gs_geogregion)
		+ MORPHFLAG_BYTES
		+ sizeof(((gk_string *)0)->st_domains);
	if((size_t)*maxp > SIZE_MAX - fixed_size)
		return(-1);
	unitsize = fixed_size + (size_t)*maxp;
	if(unitsize == 0)
		return(-1);
	nendings = payload_size / unitsize;
	if(nendings > (size_t)INT_MAX)
		return(-1);
	if(payload_size % unitsize) {
		morpheus_runtime_diagnostic(
			"endio: payload %zu is not divisible by record size %zu\n",
			payload_size,unitsize);
		morpheus_runtime_diagnostic("Error in endio!\n");
		return(0);
	}
	return((int)nendings);
}

void localtrimwhite(char *s,int n)
{
	int i;
	int sdone = 0;
	if (!s || n < 0) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return;
	}
	for(i=0;i<n;i++) {
		if(!*s) sdone=1;
		if(sdone) *s = 0;
		s++;
	}
	
}
