// SPDX-License-Identifier: AGPL-3.0-or-later

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define HEADER_SIZE 64u
#define LEMMA_ENTRY_SIZE 24u
#define BLOCK_ENTRY_SIZE 16u
#define RECORD_ENTRY_SIZE 24u
#define FORMAT_VERSION 1u
#define LANGUAGE_GREEK 1u
#define LINE_CAPACITY 8192u

typedef enum {
	RECORD_NOUN = 1,
	RECORD_ADJECTIVE = 2,
	RECORD_VERB_STEM = 3,
	RECORD_INDECLINABLE = 4,
	RECORD_IRREGULAR_VERB = 5
} record_kind;

typedef struct {
	record_kind kind;
	char *stem;
	char *keys;
} source_record;

typedef struct {
	char *lemma;
	uint64_t ordinal;
	source_record *records;
	size_t record_count;
	size_t record_capacity;
} source_block;

typedef struct {
	source_block *blocks;
	size_t block_count;
	size_t block_capacity;
	uint64_t next_ordinal;
} source_index;

static void
report_errno(const char *operation, const char *path)
{
	fprintf(stderr,"morpheus-gener-index: %s %s: %s\n",
	        operation,path,strerror(errno));
}

static void *
checked_realloc(void *value, size_t count, size_t size)
{
	void *result;

	if (size && count > SIZE_MAX / size)
		return NULL;
	result = realloc(value,count * size);
	return result;
}

static char *
duplicate_string(const char *value)
{
	size_t length = strlen(value) + 1;
	char *copy = malloc(length);

	if (copy)
		memcpy(copy,value,length);
	return copy;
}

static void
free_block(source_block *block)
{
	size_t record;

	free(block->lemma);
	for (record = 0; record != block->record_count; record++) {
		free(block->records[record].stem);
		free(block->records[record].keys);
	}
	free(block->records);
	*block = (source_block){ 0 };
}

static void
free_index(source_index *index)
{
	size_t block;

	for (block = 0; block != index->block_count; block++) {
		free_block(index->blocks + block);
	}
	free(index->blocks);
	*index = (source_index){ 0 };
}

static int
append_block(source_index *index, char *lemma, source_block **block)
{
	if (index->block_count == index->block_capacity) {
		size_t capacity = index->block_capacity
		                  ? index->block_capacity * 2 : 64;
		source_block *blocks;

		if (capacity < index->block_capacity)
			return 0;
		blocks = checked_realloc(index->blocks,capacity,sizeof *blocks);
		if (!blocks)
			return 0;
		index->blocks = blocks;
		index->block_capacity = capacity;
	}
	*block = index->blocks + index->block_count++;
	**block = (source_block){ .lemma = lemma,
	                         .ordinal = index->next_ordinal++ };
	return 1;
}

static int
append_record(source_block *block, record_kind kind,
              const char *stem, const char *keys)
{
	source_record *record;

	if (block->record_count == block->record_capacity) {
		size_t capacity = block->record_capacity
		                  ? block->record_capacity * 2 : 8;
		source_record *records;

		if (capacity < block->record_capacity)
			return 0;
		records = checked_realloc(block->records,capacity,sizeof *records);
		if (!records)
			return 0;
		block->records = records;
		block->record_capacity = capacity;
	}
	record = block->records + block->record_count++;
	*record = (source_record){ .kind = kind,
	                          .stem = duplicate_string(stem),
	                          .keys = duplicate_string(keys) };
	if (!record->stem || !record->keys) {
		free(record->stem);
		free(record->keys);
		*record = (source_record){ 0 };
		block->record_count--;
		return 0;
	}
	return 1;
}

static char *
trim(char *value)
{
	char *end;

	while (*value == ' ' || *value == '\t')
		value++;
	end = value + strlen(value);
	while (end != value && (end[-1] == ' ' || end[-1] == '\t' ||
	                        end[-1] == '\r' || end[-1] == '\n'))
		*--end = 0;
	return value;
}

static char *
canonical_lemma(const char *source)
{
	size_t length = strcspn(source," \t\r\n");
	char *lemma = malloc(length + 1);
	size_t input;
	size_t output = 0;

	if (!lemma)
		return NULL;
	/*
	 * A leading '-' marks the compound-only stems of a lemma (-dhme/w), which
	 * the preparer keeps apart; requests are canonicalised without hyphens
	 * and so never name them.
	 */
	if (length && source[0] == '-') {
		lemma[output++] = '-';
		source++, length--;
	}
	if (length && source[0] == '!')
		source++, length--;
	for (input = 0; input != length; input++) {
		if (source[input] != '-' && source[input] != '_' &&
		    source[input] != '^' && source[input] != '+')
			lemma[output++] = source[input];
	}
	lemma[output] = 0;
	return lemma;
}

static int
record_prefix(const char *line, record_kind *kind)
{
	static const struct {
		const char *prefix;
		record_kind kind;
	} prefixes[] = {
		{ ":no:", RECORD_NOUN },
		{ ":aj:", RECORD_ADJECTIVE },
		{ ":vs:", RECORD_VERB_STEM },
		{ ":wd:", RECORD_INDECLINABLE },
		{ ":vb:", RECORD_IRREGULAR_VERB }
	};
	size_t prefix;

	for (prefix = 0; prefix != sizeof prefixes / sizeof prefixes[0];
	     prefix++) {
		if (!strncmp(line,prefixes[prefix].prefix,4)) {
			*kind = prefixes[prefix].kind;
			return 1;
		}
	}
	return 0;
}

static int
parse_record(source_block *block, char *line, const char *path,
             uint64_t line_number)
{
	record_kind kind;
	char *stem;
	char *keys;

	if (!record_prefix(line,&kind))
		return 1;
	if (!block) {
		fprintf(stderr,
		        "morpheus-gener-index: %s:%llu: record before lemma\n",
		        path,(unsigned long long)line_number);
		return 0;
	}
	stem = line + 4;
	keys = stem + strcspn(stem," \t\r\n");
	if (*keys)
		*keys++ = 0;
	keys = trim(keys);
	if (!*stem || !*keys) {
		fprintf(stderr,
		        "morpheus-gener-index: %s:%llu: incomplete record\n",
		        path,(unsigned long long)line_number);
		return 0;
	}
	if (!append_record(block,kind,stem,keys)) {
		fprintf(stderr,"morpheus-gener-index: out of memory\n");
		return 0;
	}
	return 1;
}

static int
parse_source(source_index *index, const char *path)
{
	FILE *input = fopen(path,"r");
	source_block *block = NULL;
	char line[LINE_CAPACITY];
	uint64_t line_number = 0;
	int result = 0;

	if (!input) {
		report_errno("cannot open",path);
		return 0;
	}
	while (fgets(line,sizeof line,input)) {
		char *content;
		size_t length;

		line_number++;
		length = strlen(line);
		if (length == sizeof line - 1 && line[length - 1] != '\n') {
			fprintf(stderr,
			        "morpheus-gener-index: %s:%llu: line too long\n",
			        path,(unsigned long long)line_number);
			goto finish;
		}
		content = trim(line);
		if (!*content || *content == '#' || *content == '?')
			continue;
		if (!strncmp(content,":le:",4)) {
			char *lemma = canonical_lemma(trim(content + 4));

			if (!lemma) {
				fprintf(stderr,"morpheus-gener-index: out of memory\n");
				goto finish;
			}
			if (!*lemma || !append_block(index,lemma,&block)) {
				free(lemma);
				fprintf(stderr,
				        "morpheus-gener-index: %s:%llu: invalid lemma\n",
				        path,(unsigned long long)line_number);
				goto finish;
			}
			continue;
		}
		if (!strncmp(content,":de:",4) || *content == ';' ||
		    *content == '@') {
			fprintf(stderr,
			        "morpheus-gener-index: %s:%llu: unexpanded generation record\n",
			        path,(unsigned long long)line_number);
			goto finish;
		}
		if (!parse_record(block,content,path,line_number))
			goto finish;
	}
	if (ferror(input)) {
		report_errno("cannot read",path);
		goto finish;
	}
	result = 1;

finish:
	if (fclose(input) && result) {
		report_errno("cannot close",path);
		result = 0;
	}
	return result;
}

static int
compare_blocks(const void *left_value, const void *right_value)
{
	const source_block *left = left_value;
	const source_block *right = right_value;
	int order = strcmp(left->lemma,right->lemma);

	if (order)
		return order;
	return left->ordinal < right->ordinal ? -1 : left->ordinal != right->ordinal;
}

static int
same_block(const source_block *left, const source_block *right)
{
	size_t record;

	if (strcmp(left->lemma,right->lemma) ||
	    left->record_count != right->record_count)
		return 0;
	for (record = 0; record != left->record_count; record++) {
		const source_record *left_record = left->records + record;
		const source_record *right_record = right->records + record;

		if (left_record->kind != right_record->kind ||
		    strcmp(left_record->stem,right_record->stem) ||
		    strcmp(left_record->keys,right_record->keys))
			return 0;
	}
	return 1;
}

static void
discard_duplicate_blocks(source_index *index)
{
	size_t input;
	size_t output = 0;

	for (input = 0; input != index->block_count; input++) {
		size_t previous;
		int duplicate = 0;

		for (previous = output; previous; previous--) {
			if (strcmp(index->blocks[previous - 1].lemma,
			           index->blocks[input].lemma))
				break;
			if (same_block(index->blocks + previous - 1,
			               index->blocks + input)) {
				duplicate = 1;
				break;
			}
		}
		if (duplicate) {
			free_block(index->blocks + input);
			continue;
		}
		if (output != input) {
			index->blocks[output] = index->blocks[input];
			index->blocks[input] = (source_block){ 0 };
		}
		output++;
	}
	index->block_count = output;
}

static void
put_u32(unsigned char *output, uint32_t value)
{
	int byte;

	for (byte = 0; byte != 4; byte++)
		output[byte] = (unsigned char)(value >> (byte * 8));
}

static void
put_u64(unsigned char *output, uint64_t value)
{
	int byte;

	for (byte = 0; byte != 8; byte++)
		output[byte] = (unsigned char)(value >> (byte * 8));
}

static uint64_t
payload_hash(const unsigned char *payload, size_t size)
{
	uint64_t hash = UINT64_C(14695981039346656037);
	size_t byte;

	for (byte = 0; byte != size; byte++)
		hash = (hash ^ payload[byte]) * UINT64_C(1099511628211);
	return hash;
}

static int
add_size(size_t *total, size_t amount)
{
	if (amount > SIZE_MAX - *total)
		return 0;
	*total += amount;
	return 1;
}

static int
multiply_size(size_t count, size_t size, size_t *result)
{
	if (size && count > SIZE_MAX / size)
		return 0;
	*result = count * size;
	return 1;
}

static void
discard_empty_blocks(source_index *index)
{
	size_t input;
	size_t output = 0;

	for (input = 0; input != index->block_count; input++) {
		if (!index->blocks[input].record_count) {
			free(index->blocks[input].lemma);
			free(index->blocks[input].records);
			continue;
		}
		if (output != input)
			index->blocks[output] = index->blocks[input];
		output++;
	}
	index->block_count = output;
}

static int
write_index(source_index *index, const char *path)
{
	size_t lemma_count = 0;
	size_t record_count = 0;
	size_t string_size = 0;
	size_t payload_size = 0;
	size_t block;
	unsigned char *payload;
	unsigned char header[HEADER_SIZE] = { 'M','O','R','P','H','G','E','N' };
	size_t lemma_cursor = 0;
	size_t block_cursor;
	size_t record_cursor;
	size_t string_cursor;
	size_t string_base;
	uint64_t first_record = 0;
	FILE *output;
	int result = 0;
	size_t table_size;

	discard_empty_blocks(index);
	qsort(index->blocks,index->block_count,sizeof *index->blocks,compare_blocks);
	discard_duplicate_blocks(index);
	for (block = 0; block != index->block_count; block++) {
		if (!index->blocks[block].record_count)
			continue;
		if (index->blocks[block].record_count > UINT32_MAX)
			goto overflow;
		if (!block || strcmp(index->blocks[block - 1].lemma,
		                     index->blocks[block].lemma)) {
			lemma_count++;
			if (!add_size(&string_size,strlen(index->blocks[block].lemma) + 1))
				goto overflow;
		}
		if (!add_size(&record_count,index->blocks[block].record_count))
			goto overflow;
		for (size_t record = 0;
		     record != index->blocks[block].record_count; record++) {
			if (!add_size(&string_size,
			              strlen(index->blocks[block].records[record].stem) + 1) ||
			    !add_size(&string_size,
			              strlen(index->blocks[block].records[record].keys) + 1))
				goto overflow;
		}
	}
	if (!multiply_size(lemma_count,LEMMA_ENTRY_SIZE,&table_size) ||
	    !add_size(&payload_size,table_size) ||
	    !multiply_size(index->block_count,BLOCK_ENTRY_SIZE,&table_size) ||
	    !add_size(&payload_size,table_size) ||
	    !multiply_size(record_count,RECORD_ENTRY_SIZE,&table_size) ||
	    !add_size(&payload_size,table_size) ||
	    !add_size(&payload_size,string_size))
		goto overflow;
	payload = calloc(payload_size ? payload_size : 1,1);
	if (!payload) {
		fprintf(stderr,"morpheus-gener-index: out of memory\n");
		return 0;
	}
	block_cursor = lemma_count * LEMMA_ENTRY_SIZE;
	record_cursor = block_cursor + index->block_count * BLOCK_ENTRY_SIZE;
	string_cursor = record_cursor + record_count * RECORD_ENTRY_SIZE;
	string_base = string_cursor;
	for (block = 0; block != index->block_count;) {
		size_t group_end = block + 1;
		size_t group_blocks = 0;
		size_t key_offset;

		while (group_end != index->block_count &&
		       !strcmp(index->blocks[block].lemma,
		               index->blocks[group_end].lemma))
			group_end++;
		for (size_t current = block; current != group_end; current++)
			if (index->blocks[current].record_count)
				group_blocks++;
		if (group_blocks > UINT32_MAX)
			goto payload_overflow;
		if (!group_blocks) {
			block = group_end;
			continue;
		}
		key_offset = string_cursor - string_base;
		memcpy(payload + string_cursor,index->blocks[block].lemma,
		       strlen(index->blocks[block].lemma) + 1);
		string_cursor += strlen(index->blocks[block].lemma) + 1;
		put_u64(payload + lemma_cursor,key_offset);
		put_u64(payload + lemma_cursor + 8,
		        (block_cursor - lemma_count * LEMMA_ENTRY_SIZE) /
		        BLOCK_ENTRY_SIZE);
		put_u32(payload + lemma_cursor + 16,(uint32_t)group_blocks);
		lemma_cursor += LEMMA_ENTRY_SIZE;
		for (size_t current = block; current != group_end; current++) {
			source_block *source = index->blocks + current;

			if (!source->record_count)
				continue;
			put_u64(payload + block_cursor,first_record);
			put_u32(payload + block_cursor + 8,
			        (uint32_t)source->record_count);
			block_cursor += BLOCK_ENTRY_SIZE;
			for (size_t record = 0; record != source->record_count;
			     record++) {
				source_record *item = source->records + record;
				size_t stem_offset = string_cursor - string_base;
				size_t keys_offset;

				memcpy(payload + string_cursor,item->stem,
				       strlen(item->stem) + 1);
				string_cursor += strlen(item->stem) + 1;
				keys_offset = string_cursor - string_base;
				memcpy(payload + string_cursor,item->keys,
				       strlen(item->keys) + 1);
				string_cursor += strlen(item->keys) + 1;
				put_u32(payload + record_cursor,(uint32_t)item->kind);
				put_u64(payload + record_cursor + 8,stem_offset);
				put_u64(payload + record_cursor + 16,keys_offset);
				record_cursor += RECORD_ENTRY_SIZE;
				first_record++;
			}
		}
		block = group_end;
	}
	if (lemma_cursor != lemma_count * LEMMA_ENTRY_SIZE ||
	    block_cursor != lemma_count * LEMMA_ENTRY_SIZE +
	                    index->block_count * BLOCK_ENTRY_SIZE ||
	    record_cursor != string_base || string_cursor != payload_size) {
		fprintf(stderr,"morpheus-gener-index: internal layout error\n");
		free(payload);
		return 0;
	}
	put_u32(header + 8,FORMAT_VERSION);
	put_u32(header + 12,LANGUAGE_GREEK);
	put_u64(header + 16,lemma_count);
	put_u64(header + 24,index->block_count);
	put_u64(header + 32,record_count);
	put_u64(header + 40,string_size);
	put_u64(header + 48,payload_hash(payload,payload_size));
	output = fopen(path,"wb");
	if (!output) {
		report_errno("cannot create",path);
		free(payload);
		return 0;
	}
	if (fwrite(header,1,sizeof header,output) != sizeof header ||
	    fwrite(payload,1,payload_size,output) != payload_size) {
		report_errno("cannot write",path);
	} else if (fclose(output)) {
		report_errno("cannot close",path);
		output = NULL;
	} else {
		result = 1;
		output = NULL;
	}
	if (output)
		fclose(output);
	if (!result)
		remove(path);
	free(payload);
	return result;

payload_overflow:
	free(payload);

overflow:
	fprintf(stderr,"morpheus-gener-index: index exceeds host limits\n");
	return 0;
}

int
main(int argc, char **argv)
{
	source_index index = { 0 };
	int input;
	int result = EXIT_FAILURE;

	if (argc < 3) {
		fprintf(stderr,"usage: %s OUTPUT INPUT...\n",argv[0]);
		return EXIT_FAILURE;
	}
	for (input = 2; input != argc; input++) {
		if (!parse_source(&index,argv[input]))
			goto finish;
	}
	if (!write_index(&index,argv[1]))
		goto finish;
	result = EXIT_SUCCESS;

finish:
	free_index(&index);
	return result;
}
