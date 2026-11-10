// SPDX-License-Identifier: AGPL-3.0-or-later

#include <assert.h>
#include <inttypes.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <modes.h>

#include "../src/api/gener_index.h"
#include "../src/bridge/generation_normalizer.h"
#include "../src/gener/generation_service.h"

typedef struct {
	uint64_t fingerprint;
	size_t nondual_count;
} form_summary;

typedef struct {
	const morpheus_gener_index *index;
	const char *lemma;
	size_t expected_count;
	size_t expected_nondual_count;
	uint64_t expected_fingerprint;
} thread_case;

typedef struct {
	int saw_first;
	int saw_second;
} multiple_summary;

static uint64_t
hash_byte(uint64_t hash, unsigned char byte)
{
	return (hash ^ byte) * UINT64_C(1099511628211);
}

static uint64_t
hash_u32(uint64_t hash, uint32_t value)
{
	int shift;

	for (shift = 0; shift != 32; shift += 8)
		hash = hash_byte(hash,(unsigned char)(value >> shift));
	return hash;
}

static uint64_t
hash_string(uint64_t hash, const char *value)
{
	const unsigned char *cursor = (const unsigned char *)value;

	while (*cursor)
		hash = hash_byte(hash,*cursor++);
	return hash_byte(hash,0);
}

static uint64_t
hash_form(uint64_t hash, const gk_word *form)
{
	word_form info = forminfo_of(form);
	int flag;

	hash = hash_string(hash,workword_of(form));
	hash = hash_string(hash,lemma_of(form));
	hash = hash_string(hash,preverb_of(form));
	hash = hash_string(hash,aug1_of(form));
	hash = hash_string(hash,stem_of(form));
	hash = hash_string(hash,suffix_of(form));
	hash = hash_string(hash,endstring_of(form));
	hash = hash_u32(hash,voice_of(info));
	hash = hash_u32(hash,mood_of(info));
	hash = hash_u32(hash,tense_of(info));
	hash = hash_u32(hash,person_of(info));
	hash = hash_u32(hash,number_of(info));
	hash = hash_u32(hash,case_of(info));
	hash = hash_u32(hash,degree_of(info));
	hash = hash_u32(hash,gender_of(info));
	hash = hash_u32(hash,stemtype_of(form));
	hash = hash_u32(hash,derivtype_of(form));
	hash = hash_u32(hash,(uint32_t)(unsigned short)dialect_of(form));
	hash = hash_u32(hash,(uint32_t)geogregion_of(form));
	for (flag = 0; flag != MORPHFLAG_STORAGE_BYTES; flag++)
		hash = hash_byte(hash,morphflags_of(form)[flag]);
	return hash;
}

static int
summarize(const gk_word *form, void *state)
{
	form_summary *summary = state;

	summary->fingerprint = hash_form(summary->fingerprint,form);
	if (number_of(forminfo_of(form)) != DUAL)
		summary->nondual_count++;
	return 1;
}

static void
generate_and_check(const morpheus_gener_index *index, const char *lemma,
                   size_t expected_count, size_t expected_nondual_count,
                   uint64_t expected_fingerprint)
{
	morpheus_generation_service *service = NULL;
	form_summary summary = { UINT64_C(14695981039346656037), 0 };
	size_t count = 0;
	size_t skipped = 1;

	assert(morpheus_generation_service_create(index,&service) ==
	       MORPHEUS_GENERATION_OK);
	assert(morpheus_generation_service_generate(service,lemma,summarize,&summary,
	                                            &count,&skipped) ==
	       MORPHEUS_GENERATION_OK);
	assert(skipped == 0);
	assert(count == expected_count);
	assert(summary.nondual_count == expected_nondual_count);
	assert(summary.fingerprint == expected_fingerprint);
	morpheus_generation_service_destroy(service);
}

static int
summarize_multiple(const gk_word *form, void *state)
{
	multiple_summary *summary = state;

	if (!strcmp(workword_of(form),"prw=ton"))
		summary->saw_first = 1;
	if (!strcmp(workword_of(form),"deu/teron"))
		summary->saw_second = 1;
	return 1;
}

static size_t
parse_size(const char *value)
{
	char *end;
	uintmax_t parsed = strtoumax(value,&end,10);

	assert(*value && !*end && parsed <= SIZE_MAX);
	return (size_t)parsed;
}

static void
run_differential(const morpheus_gener_index *index, const char *fixture_path)
{
	FILE *fixtures = fopen(fixture_path,"r");
	char line[4096];
	size_t fixture_count = 0;

	assert(fixtures);
	while (fgets(line,sizeof line,fixtures)) {
		char *fields[10];
		char *cursor = line;
		char *end;
		uintmax_t fingerprint;
		int field;

		if (!line[0] || line[0] == '#')
			continue;
		line[strcspn(line,"\r\n")] = 0;
		for (field = 0; field != 10; field++) {
			char *tab;

			fields[field] = cursor;
			tab = strchr(cursor,'\t');
			if (!tab)
				break;
			*tab = 0;
			cursor = tab + 1;
		}
		assert(field == 9);
		fingerprint = strtoumax(fields[9],&end,16);
		assert(*fields[9] && !*end && fingerprint <= UINT64_MAX);
		generate_and_check(index,fields[2],parse_size(fields[5]),
		                   parse_size(fields[7]),(uint64_t)fingerprint);
		fixture_count++;
	}
	assert(!ferror(fixtures));
	assert(!fclose(fixtures));
	assert(fixture_count == 5);
	/* Two blocks with the same key must both survive lookup and generation. */
	{
		morpheus_generation_service *service = NULL;
		multiple_summary summary = { 0 };
		size_t count = 0;

		assert(morpheus_generation_service_create(index,&service) ==
		       MORPHEUS_GENERATION_OK);
		assert(morpheus_generation_service_generate(
		           service,"multiple",summarize_multiple,&summary,&count,NULL) ==
		       MORPHEUS_GENERATION_OK);
		assert(count == 2);
		assert(summary.saw_first && summary.saw_second);
		morpheus_generation_service_destroy(service);
	}
	/* The historical front end expands commas in the stem-type glob. */
	{
		morpheus_generation_service *service = NULL;
		form_summary summary = { UINT64_C(14695981039346656037), 0 };
		size_t count = 0;

		assert(morpheus_generation_service_create(index,&service) ==
		       MORPHEUS_GENERATION_OK);
		assert(morpheus_generation_service_generate(
		           service,"comma",summarize,&summary,&count,NULL) ==
		       MORPHEUS_GENERATION_OK);
		assert(count > 0);
		morpheus_generation_service_destroy(service);
	}
}

static void *
run_thread(void *argument)
{
	thread_case *test = argument;
	int iteration;

	for (iteration = 0; iteration != 8; iteration++)
		generate_and_check(test->index,test->lemma,test->expected_count,
		                   test->expected_nondual_count,
		                   test->expected_fingerprint);
	return NULL;
}

static void
run_isolation(const morpheus_gener_index *index)
{
	thread_case noun = {
		index,"lo/gos",18,15,UINT64_C(0xbf6c20106dd493f9)
	};
	thread_case indeclinable = {
		index,"korba=n",1,1,UINT64_C(0xce89f06fbaeb1bac)
	};
	pthread_t first;
	pthread_t second;

	assert(!pthread_create(&first,NULL,run_thread,&noun));
	assert(!pthread_create(&second,NULL,run_thread,&indeclinable));
	assert(!pthread_join(first,NULL));
	assert(!pthread_join(second,NULL));
}

static int
stop_after_one(const gk_word *form, void *state)
{
	(void)form;
	(void)state;
	return 0;
}

static void
run_failure(const morpheus_gener_index *index)
{
	morpheus_generation_service *service = (void *)(uintptr_t)1;
	form_summary summary = { UINT64_C(14695981039346656037), 0 };
	size_t count = 123;
	size_t skipped = 123;

	assert(morpheus_generation_service_create(NULL,&service) ==
	       MORPHEUS_GENERATION_INVALID);
	assert(service == (void *)(uintptr_t)1);
	assert(morpheus_generation_service_create(index,&service) ==
	       MORPHEUS_GENERATION_OK);
	assert(morpheus_generation_service_generate(service,"missing",summarize,NULL,
	                                            &count,&skipped) ==
	       MORPHEUS_GENERATION_NOT_FOUND);
	/* Without a skipped-record counter, an unusable record fails the lemma. */
	assert(morpheus_generation_service_generate(service,"broken",summarize,NULL,
	                                            &count,NULL) ==
	       MORPHEUS_GENERATION_ENGINE_ERROR);
	assert(morpheus_generation_service_generate(service,"mixed",summarize,
	                                            &summary,&count,NULL) ==
	       MORPHEUS_GENERATION_ENGINE_ERROR);
	/* With one, the record is skipped and counted, and the others survive. */
	assert(morpheus_generation_service_generate(service,"broken",summarize,
	                                            &summary,&count,&skipped) ==
	       MORPHEUS_GENERATION_OK);
	assert(count == 0 && skipped == 1);
	assert(morpheus_generation_service_generate(service,"mixed",summarize,
	                                            &summary,&count,&skipped) ==
	       MORPHEUS_GENERATION_OK);
	assert(count == 1 && skipped == 2);
	assert(morpheus_generation_service_generate(service,"stop",stop_after_one,
	                                            NULL,&count,&skipped) ==
	       MORPHEUS_GENERATION_STOPPED);
	assert(count == 1 && skipped == 0);
	assert(morpheus_generation_service_generate(service,"broken",NULL,NULL,
	                                            &count,&skipped) ==
	       MORPHEUS_GENERATION_INVALID);
	morpheus_generation_service_destroy(service);
}

static void
run_normalization(const morpheus_gener_index *index)
{
	morpheus_generation_service *service = NULL;
	morpheus_normalized_generation_result *result = NULL;
	const morpheus_normalized_generation *record;
	size_t count;
	size_t duals = 0;
	size_t duplicates = 0;
	size_t current;
	size_t previous;
	int saw_attic = 0;
	int saw_ionic = 0;

	assert(morpheus_generation_service_create(index,&service) ==
	       MORPHEUS_GENERATION_OK);
	assert(morpheus_generation_normalize(service,"lo/gos",18,&result) ==
	       MORPHEUS_GENERATION_NORMALIZE_OK);
	assert(result);
	count = morpheus_normalized_generation_result_count(result);
	assert(count == 18);
	morpheus_generation_service_destroy(service);
	service = NULL;
	for (current = 0; current != count; current++) {
		record = morpheus_normalized_generation_result_at(result,current);
		assert(record);
		assert(record->part_of_speech == MORPHEUS_PART_OF_SPEECH_NOUN);
		assert(!strcmp(record->lemma,"lo/gos"));
		assert(!record->truncated_fields);
		if (record->number == MORPHEUS_NUMBER_DUAL)
			duals++;
		if (current)
			assert(morpheus_normalized_generation_compare(
			           morpheus_normalized_generation_result_at(
			               result,current - 1),record) < 0);
		for (previous = 0; previous != current; previous++) {
			if (!strcmp(morpheus_normalized_generation_result_at(
			                result,previous)->surface,record->surface)) {
				duplicates++;
				break;
			}
		}
	}
	assert(duals == 3);
	assert(duplicates);
	assert(!morpheus_normalized_generation_result_at(result,count));
	morpheus_normalized_generation_result_free(result);
	result = NULL;

	assert(morpheus_generation_service_create(index,&service) ==
	       MORPHEUS_GENERATION_OK);
	assert(morpheus_generation_normalize(service,"lo/gos",17,&result) ==
	       MORPHEUS_GENERATION_NORMALIZE_LIMIT);
	assert(!result);
	assert(morpheus_generation_normalize(service,"missing",18,&result) ==
	       MORPHEUS_GENERATION_NORMALIZE_NOT_FOUND);
	assert(!result);
	assert(morpheus_generation_normalize(service,"lo/gos",0,&result) ==
	       MORPHEUS_GENERATION_NORMALIZE_INVALID);
	assert(!result);
	assert(morpheus_generation_normalize(
	           service,"lo/gos",MORPHEUS_GENERATION_RESULT_HARD_LIMIT + 1,
	           &result) == MORPHEUS_GENERATION_NORMALIZE_INVALID);
	assert(!result);
	assert(morpheus_generation_normalize(service,"multiple",2,&result) ==
	       MORPHEUS_GENERATION_NORMALIZE_OK);
	assert(morpheus_normalized_generation_result_count(result) == 2);
	for (current = 0; current != 2; current++) {
		record = morpheus_normalized_generation_result_at(result,current);
		assert(record);
		if (record->dialect == MORPHEUS_DIALECT_ATTIC)
			saw_attic = 1;
		if (record->dialect == MORPHEUS_DIALECT_IONIC)
			saw_ionic = 1;
	}
	assert(saw_attic && saw_ionic);
	morpheus_normalized_generation_result_free(result);
	morpheus_generation_service_destroy(service);
}

int
main(int argc, char **argv)
{
	morpheus_gener_index *index = NULL;

	assert(argc >= 3);
	assert(morpheus_gener_index_open_file(argv[2],&index) ==
	       MORPHEUS_GENER_INDEX_OK);
	if (!strcmp(argv[1],"differential")) {
		assert(argc == 4);
		run_differential(index,argv[3]);
	} else if (!strcmp(argv[1],"isolation")) {
		assert(argc == 3);
		run_isolation(index);
	} else if (!strcmp(argv[1],"failure")) {
		assert(argc == 3);
		run_failure(index);
	} else if (!strcmp(argv[1],"normalization")) {
		assert(argc == 3);
		run_normalization(index);
	} else {
		assert(0);
	}
	morpheus_gener_index_close(index);
	return 0;
}
