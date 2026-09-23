// SPDX-License-Identifier: AGPL-3.0-or-later

#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gkstring.h>

#include "../src/morphlib/endio.proto.h"

#define LINE_CAPACITY 1024
#define PATH_CAPACITY 4096
#define MAX_SEMANTIC_EXCEPTIONS 8

enum field_kind {
	FIELD_STEM_TYPE,
	FIELD_DERIVATION_TYPE
};

struct semantic_exception {
	char path[LINE_CAPACITY];
	unsigned int first_record;
	unsigned int last_record;
	enum field_kind field;
	unsigned int baseline_value;
	unsigned int generated_value;
	unsigned int observations;
};

static struct semantic_exception semantic_exceptions[MAX_SEMANTIC_EXCEPTIONS];
static size_t semantic_exception_count;

static int same_form(word_form left, word_form right)
{
	return(voice_of(left) == voice_of(right) &&
	       mood_of(left) == mood_of(right) &&
	       tense_of(left) == tense_of(right) &&
	       person_of(left) == person_of(right) &&
	       number_of(left) == number_of(right) &&
	       case_of(left) == case_of(right) &&
	       degree_of(left) == degree_of(right) &&
	       gender_of(left) == gender_of(right));
}

static int same_ending(const gk_string *left, const gk_string *right)
{
	return(same_form(forminfo_of(left),forminfo_of(right)) &&
	       stemtype_of(left) == stemtype_of(right) &&
	       derivtype_of(left) == derivtype_of(right) &&
	       dialect_of(left) == dialect_of(right) &&
	       geogregion_of(left) == geogregion_of(right) &&
	       memcmp(morphflags_of(left),morphflags_of(right),
	              MORPHFLAG_STORAGE_BYTES) == 0 &&
	       memcmp(domains_of(left),domains_of(right),MAXDOMAINS+1) == 0 &&
	       memcmp(gkstring_of(left),gkstring_of(right),MAXWORDSIZE) == 0);
}

static void describe_difference(const gk_string *left, const gk_string *right)
{
	if(!same_form(forminfo_of(left),forminfo_of(right)))
		fprintf(stderr,"  grammatical form differs\n");
	if(stemtype_of(left) != stemtype_of(right))
		fprintf(stderr,"  stem type differs: %u versus %u\n",
		        (unsigned int)stemtype_of(left),
		        (unsigned int)stemtype_of(right));
	if(derivtype_of(left) != derivtype_of(right))
		fprintf(stderr,"  derivation type differs: %u versus %u\n",
		        (unsigned int)derivtype_of(left),
		        (unsigned int)derivtype_of(right));
	if(dialect_of(left) != dialect_of(right))
		fprintf(stderr,"  dialect differs: %u versus %u\n",
		        (unsigned int)dialect_of(left),
		        (unsigned int)dialect_of(right));
	if(geogregion_of(left) != geogregion_of(right))
		fprintf(stderr,"  region differs: %u versus %u\n",
		        (unsigned int)geogregion_of(left),
		        (unsigned int)geogregion_of(right));
	if(memcmp(morphflags_of(left),morphflags_of(right),
	          MORPHFLAG_STORAGE_BYTES) != 0)
		fprintf(stderr,"  morphology flags differ\n");
	if(memcmp(domains_of(left),domains_of(right),MAXDOMAINS+1) != 0)
		fprintf(stderr,"  domains differ: %s versus %s\n",
		        domains_of(left),domains_of(right));
	if(memcmp(gkstring_of(left),gkstring_of(right),MAXWORDSIZE) != 0)
		fprintf(stderr,"  ending differs: %s versus %s\n",
		        gkstring_of(left),gkstring_of(right));
}

static int parse_unsigned(const char *text, unsigned int *value)
{
	char *end;
	unsigned long parsed;

	errno = 0;
	parsed = strtoul(text,&end,10);
	if(errno || end == text || *end || parsed > UINT_MAX) return(0);
	*value = (unsigned int)parsed;
	return(1);
}

static int load_semantic_exceptions(const char *path)
{
	FILE *input;
	char line[LINE_CAPACITY];
	char *fields[6];
	char *separator;
	char *newline;
	int index;
	int input_failed;
	struct semantic_exception *exception;

	input = fopen(path,"r");
	if(!input) return(0);
	while(fgets(line,sizeof line,input)) {
		newline = strchr(line,'\n');
		if(!newline && !feof(input)) goto invalid;
		if(newline) *newline = 0;
		if(line[0] == 0 || line[0] == '#') continue;
		if(semantic_exception_count >= MAX_SEMANTIC_EXCEPTIONS) goto invalid;
		fields[0] = line;
		for(index=1;index<6;index++) {
			fields[index] = strchr(fields[index-1],'\t');
			if(!fields[index]) goto invalid;
			*fields[index]++ = 0;
		}
		if(strchr(fields[5],'\t')) goto invalid;
		exception = &semantic_exceptions[semantic_exception_count];
		if(snprintf(exception->path,sizeof exception->path,"%s",fields[0])
		   >= (int)sizeof exception->path) goto invalid;
		separator = strchr(fields[1],'-');
		if(!separator) goto invalid;
		*separator++ = 0;
		if(!parse_unsigned(fields[1],&exception->first_record) ||
		   !parse_unsigned(separator,&exception->last_record) ||
		   exception->last_record < exception->first_record) goto invalid;
		if(strcmp(fields[2],"stem-type") == 0)
			exception->field = FIELD_STEM_TYPE;
		else if(strcmp(fields[2],"derivation-type") == 0)
			exception->field = FIELD_DERIVATION_TYPE;
		else goto invalid;
		if(!parse_unsigned(fields[3],&exception->baseline_value) ||
		   !parse_unsigned(fields[4],&exception->generated_value) ||
		   strcmp(fields[5],"duplicate-registry-value") != 0) goto invalid;
		semantic_exception_count++;
	}
	input_failed = ferror(input);
	if(fclose(input) != 0) input_failed = 1;
	if(input_failed || semantic_exception_count != 1)
		return(0);
	return(1);

invalid:
	fclose(input);
	return(0);
}

static int common_fields_match(const gk_string *left,
		const gk_string *right)
{
	return(same_form(forminfo_of(left),forminfo_of(right)) &&
	       dialect_of(left) == dialect_of(right) &&
	       geogregion_of(left) == geogregion_of(right) &&
	       memcmp(morphflags_of(left),morphflags_of(right),
	              MORPHFLAG_STORAGE_BYTES) == 0 &&
	       memcmp(domains_of(left),domains_of(right),MAXDOMAINS+1) == 0 &&
	       memcmp(gkstring_of(left),gkstring_of(right),MAXWORDSIZE) == 0);
}

static int accept_semantic_exception(const char *path, unsigned int record,
		const gk_string *baseline, const gk_string *generated)
{
	size_t index;
	struct semantic_exception *exception;

	for(index=0;index<semantic_exception_count;index++) {
		exception = &semantic_exceptions[index];
		if(strcmp(path,exception->path) != 0 ||
		   record < exception->first_record ||
		   record > exception->last_record ||
		   !common_fields_match(baseline,generated)) continue;
		if(exception->field == FIELD_STEM_TYPE &&
		   (unsigned int)stemtype_of(baseline) == exception->baseline_value &&
		   (unsigned int)stemtype_of(generated) == exception->generated_value &&
		   derivtype_of(baseline) == derivtype_of(generated)) {
			exception->observations++;
			return(1);
		}
		if(exception->field == FIELD_DERIVATION_TYPE &&
		   (unsigned int)derivtype_of(baseline) == exception->baseline_value &&
		   (unsigned int)derivtype_of(generated) == exception->generated_value &&
		   stemtype_of(baseline) == stemtype_of(generated)) {
			exception->observations++;
			return(1);
		}
	}
	return(0);
}

static int semantic_exceptions_complete(void)
{
	size_t index;
	unsigned int expected;

	for(index=0;index<semantic_exception_count;index++) {
		expected = semantic_exceptions[index].last_record -
		           semantic_exceptions[index].first_record + 1U;
		if(semantic_exceptions[index].observations != expected) {
			fprintf(stderr,"semantic exception observation count differs: %s\n",
			        semantic_exceptions[index].path);
			return(0);
		}
	}
	return(1);
}

static int compare_file(const char *relative, const char *baseline_path,
		const char *generated_path, FILE *report)
{
	FILE *baseline = NULL;
	FILE *generated = NULL;
	gk_string baseline_ending;
	gk_string generated_ending;
	int baseline_count;
	int generated_count;
	int baseline_width = 0;
	int generated_width = 0;
	int index;
	int reviewed = 0;
	int result = -1;

	baseline = fopen(baseline_path,"rb");
	generated = fopen(generated_path,"rb");
	if(!baseline || !generated) {
		fprintf(stderr,"cannot open binary baseline pair: %s\n",relative);
		goto cleanup;
	}
	baseline_count = get_endheader(baseline,&baseline_width);
	generated_count = get_endheader(generated,&generated_width);
	if(baseline_count <= 0 || generated_count <= 0 ||
	   baseline_count != generated_count) {
		fprintf(stderr,
		        "binary record count differs for %s: %d versus %d\n",
		        relative,baseline_count,generated_count);
		goto cleanup;
	}
	for(index=0;index<baseline_count;index++) {
		if(ReadEnding(baseline,&baseline_ending,baseline_width) != 1 ||
		   ReadEnding(generated,&generated_ending,generated_width) != 1) {
			fprintf(stderr,"cannot decode %s record %d\n",relative,index);
			goto cleanup;
		}
		if(!same_ending(&baseline_ending,&generated_ending)) {
			if(!accept_semantic_exception(relative,(unsigned int)index,
			                              &baseline_ending,
			                              &generated_ending)) {
				fprintf(stderr,"binary semantics differ for %s record %d\n",
				        relative,index);
				describe_difference(&baseline_ending,&generated_ending);
				goto cleanup;
			}
			reviewed = 1;
		}
	}
	if(ReadEnding(baseline,&baseline_ending,baseline_width) != 0 ||
	   ReadEnding(generated,&generated_ending,generated_width) != 0) {
		fprintf(stderr,"binary table has trailing records: %s\n",relative);
		goto cleanup;
	}
	if(fprintf(report,"%s\t%d\t%d\t%d\t%s\n",relative,baseline_width,
	           generated_width,baseline_count,
	           reviewed ? "reviewed-semantic-exception" :
	                      "semantic-identical") < 0) {
		fprintf(stderr,"cannot write semantic comparison report\n");
		goto cleanup;
	}
	result = 0;

cleanup:
	if(baseline && fclose(baseline) != 0) result = -1;
	if(generated && fclose(generated) != 0) result = -1;
	return(result);
}

int main(int argc, char **argv)
{
	FILE *manifest;
	FILE *report;
	char line[LINE_CAPACITY];
	char baseline_path[PATH_CAPACITY];
	char generated_path[PATH_CAPACITY];
	char *newline;
	char *reason;
	const char *stage;
	unsigned int count = 0;
	int failed = 0;

	if(argc != 7) {
		fprintf(stderr,
		        "usage: %s BINARY_EXCEPTIONS SEMANTIC_EXCEPTIONS BASELINE_ROOT "
		        "GREEK_STAGE LATIN_STAGE REPORT\n",
		        argv[0]);
		return(2);
	}
	if(!load_semantic_exceptions(argv[2])) {
		fprintf(stderr,"invalid binary semantic exception manifest\n");
		return(1);
	}
	manifest = fopen(argv[1],"r");
	if(!manifest) {
		fprintf(stderr,"cannot open binary exception manifest\n");
		return(1);
	}
	report = fopen(argv[6],"wx");
	if(!report) {
		fprintf(stderr,"refusing unavailable or existing report: %s\n",argv[6]);
		fclose(manifest);
		return(1);
	}
	if(fputs("# SPDX-License-Identifier: AGPL-3.0-or-later\n"
	         "# path\tbaseline_width\tgenerated_width\trecords\tcomparison\n",
	         report) == EOF) failed = 1;

	while(!failed && fgets(line,sizeof line,manifest)) {
		newline = strchr(line,'\n');
		if(!newline && !feof(manifest)) {
			fprintf(stderr,"binary exception manifest line is too long\n");
			failed = 1;
			break;
		}
		if(newline) *newline = 0;
		if(line[0] == 0 || line[0] == '#') continue;
		reason = strchr(line,'\t');
		if(!reason || strchr(reason+1,'\t')) {
			fprintf(stderr,"invalid binary exception manifest line\n");
			failed = 1;
			break;
		}
		*reason++ = 0;
		if(strcmp(reason,"explicit-binary-serialization") != 0 ||
		   (strncmp(line,"Greek/",6) != 0 &&
		    strncmp(line,"Latin/",6) != 0) ||
		   strstr(line,"..")) {
			fprintf(stderr,"invalid binary exception: %s\n",line);
			failed = 1;
			break;
		}
		stage = strncmp(line,"Greek/",6) == 0 ? argv[4] : argv[5];
		if(snprintf(baseline_path,sizeof baseline_path,"%s/%s",argv[3],line)
		     >= (int)sizeof baseline_path ||
		   snprintf(generated_path,sizeof generated_path,"%s/%s",stage,line)
		     >= (int)sizeof generated_path) {
			fprintf(stderr,"binary comparison path is too long: %s\n",line);
			failed = 1;
			break;
		}
		if(compare_file(line,baseline_path,generated_path,report) != 0) {
			failed = 1;
			break;
		}
		count++;
	}
	if(ferror(manifest)) failed = 1;
	if(count != 229U) {
		fprintf(stderr,"unexpected binary semantic comparison count: %u\n",count);
		failed = 1;
	}
	if(!semantic_exceptions_complete()) failed = 1;
	if(fclose(manifest) != 0) failed = 1;
	if(fclose(report) != 0) failed = 1;
	if(failed) {
		remove(argv[6]);
		return(1);
	}
	return(0);
}
