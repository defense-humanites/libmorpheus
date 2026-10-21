#define _POSIX_C_SOURCE 200809L

// SPDX-License-Identifier: MPL-2.0

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gkstring.h>

#include "../src/gener/derivation.h"

#define LINE_CAPACITY 8192u

typedef enum {
	BASE_NONE,
	BASE_DIRECT,
	BASE_DERIVATION
} base_kind;

typedef enum {
	EXCEPTION_INVALID_DERIVATION,
	EXCEPTION_INVALID_RECORD,
	EXCEPTION_ORPHAN_CONTINUATION,
	EXCEPTION_ORPHAN_REQUEST,
	EXCEPTION_ZERO_CONTINUATION,
	EXCEPTION_ZERO_REQUEST
} exception_kind;

typedef struct {
	char *path;
	unsigned long long line_number;
	exception_kind kind;
	char sha256[65];
	int seen;
} source_exception;

typedef struct {
	source_exception *items;
	size_t count;
} exception_set;

typedef struct {
	char *data;
	size_t size;
	size_t capacity;
} prepared_buffer;

typedef struct {
	prepared_buffer *output;
	char *base_prefix;
	char derivation_stem[MAXWORDSIZE];
	char derivation_type[MAXWORDSIZE];
	char derivation_keys[LONGSTRING];
	char saved_request[LONGSTRING];
	base_kind base;
	int have_lemma;
	int have_derivation;
	int have_explicit_request;
	int skip_invalid_derivation;
} prepare_state;

static int append_bytes(prepared_buffer *output, const char *data,
                        size_t size);
static int is_generation_record(const char *line);
static void report_errno(const char *operation, const char *path);

static void
free_exceptions(exception_set *exceptions)
{
	size_t index;

	for (index = 0; index != exceptions->count; index++)
		free(exceptions->items[index].path);
	free(exceptions->items);
	exceptions->items = NULL;
	exceptions->count = 0;
}

static int
parse_exception_kind(const char *name, exception_kind *kind)
{
	static const struct {
		const char *name;
		exception_kind kind;
	} values[] = {
		{ "invalid_derivation", EXCEPTION_INVALID_DERIVATION },
		{ "invalid_record", EXCEPTION_INVALID_RECORD },
		{ "orphan_continuation", EXCEPTION_ORPHAN_CONTINUATION },
		{ "orphan_request", EXCEPTION_ORPHAN_REQUEST },
		{ "zero_continuation", EXCEPTION_ZERO_CONTINUATION },
		{ "zero_request", EXCEPTION_ZERO_REQUEST }
	};
	size_t index;

	for (index = 0; index != sizeof values / sizeof values[0]; index++) {
		if (!strcmp(name,values[index].name)) {
			*kind = values[index].kind;
			return 1;
		}
	}
	return 0;
}

static int
valid_sha256(const char *value)
{
	size_t index;

	if (strlen(value) != 64)
		return 0;
	for (index = 0; index != 64; index++) {
		if (!((value[index] >= '0' && value[index] <= '9') ||
		      (value[index] >= 'a' && value[index] <= 'f')))
			return 0;
	}
	return 1;
}

typedef struct {
	uint32_t state[8];
	uint64_t bit_count;
	unsigned char block[64];
	size_t block_size;
} sha256_context;

static uint32_t
rotate_right(uint32_t value, unsigned int count)
{
	return (value >> count) | (value << (32 - count));
}

static void
sha256_transform(sha256_context *context, const unsigned char block[64])
{
	static const uint32_t constants[64] = {
		UINT32_C(0x428a2f98), UINT32_C(0x71374491), UINT32_C(0xb5c0fbcf), UINT32_C(0xe9b5dba5),
		UINT32_C(0x3956c25b), UINT32_C(0x59f111f1), UINT32_C(0x923f82a4), UINT32_C(0xab1c5ed5),
		UINT32_C(0xd807aa98), UINT32_C(0x12835b01), UINT32_C(0x243185be), UINT32_C(0x550c7dc3),
		UINT32_C(0x72be5d74), UINT32_C(0x80deb1fe), UINT32_C(0x9bdc06a7), UINT32_C(0xc19bf174),
		UINT32_C(0xe49b69c1), UINT32_C(0xefbe4786), UINT32_C(0x0fc19dc6), UINT32_C(0x240ca1cc),
		UINT32_C(0x2de92c6f), UINT32_C(0x4a7484aa), UINT32_C(0x5cb0a9dc), UINT32_C(0x76f988da),
		UINT32_C(0x983e5152), UINT32_C(0xa831c66d), UINT32_C(0xb00327c8), UINT32_C(0xbf597fc7),
		UINT32_C(0xc6e00bf3), UINT32_C(0xd5a79147), UINT32_C(0x06ca6351), UINT32_C(0x14292967),
		UINT32_C(0x27b70a85), UINT32_C(0x2e1b2138), UINT32_C(0x4d2c6dfc), UINT32_C(0x53380d13),
		UINT32_C(0x650a7354), UINT32_C(0x766a0abb), UINT32_C(0x81c2c92e), UINT32_C(0x92722c85),
		UINT32_C(0xa2bfe8a1), UINT32_C(0xa81a664b), UINT32_C(0xc24b8b70), UINT32_C(0xc76c51a3),
		UINT32_C(0xd192e819), UINT32_C(0xd6990624), UINT32_C(0xf40e3585), UINT32_C(0x106aa070),
		UINT32_C(0x19a4c116), UINT32_C(0x1e376c08), UINT32_C(0x2748774c), UINT32_C(0x34b0bcb5),
		UINT32_C(0x391c0cb3), UINT32_C(0x4ed8aa4a), UINT32_C(0x5b9cca4f), UINT32_C(0x682e6ff3),
		UINT32_C(0x748f82ee), UINT32_C(0x78a5636f), UINT32_C(0x84c87814), UINT32_C(0x8cc70208),
		UINT32_C(0x90befffa), UINT32_C(0xa4506ceb), UINT32_C(0xbef9a3f7), UINT32_C(0xc67178f2)
	};
	uint32_t words[64];
	uint32_t a, b, c, d, e, f, g, h;
	size_t index;

	for (index = 0; index != 16; index++) {
		size_t at = index * 4;
		words[index] = ((uint32_t)block[at] << 24) |
		               ((uint32_t)block[at + 1] << 16) |
		               ((uint32_t)block[at + 2] << 8) |
		               (uint32_t)block[at + 3];
	}
	for (index = 16; index != 64; index++) {
		uint32_t first = rotate_right(words[index - 15],7) ^
		                 rotate_right(words[index - 15],18) ^
		                 (words[index - 15] >> 3);
		uint32_t second = rotate_right(words[index - 2],17) ^
		                  rotate_right(words[index - 2],19) ^
		                  (words[index - 2] >> 10);
		words[index] = words[index - 16] + first + words[index - 7] + second;
	}
	a = context->state[0]; b = context->state[1];
	c = context->state[2]; d = context->state[3];
	e = context->state[4]; f = context->state[5];
	g = context->state[6]; h = context->state[7];
	for (index = 0; index != 64; index++) {
		uint32_t choose = (e & f) ^ (~e & g);
		uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
		uint32_t upper_e = rotate_right(e,6) ^ rotate_right(e,11) ^ rotate_right(e,25);
		uint32_t upper_a = rotate_right(a,2) ^ rotate_right(a,13) ^ rotate_right(a,22);
		uint32_t first = h + upper_e + choose + constants[index] + words[index];
		uint32_t second = upper_a + majority;
		h = g; g = f; f = e; e = d + first;
		d = c; c = b; b = a; a = first + second;
	}
	context->state[0] += a; context->state[1] += b;
	context->state[2] += c; context->state[3] += d;
	context->state[4] += e; context->state[5] += f;
	context->state[6] += g; context->state[7] += h;
}

static void
sha256_init(sha256_context *context)
{
	static const uint32_t initial[8] = {
		UINT32_C(0x6a09e667), UINT32_C(0xbb67ae85), UINT32_C(0x3c6ef372), UINT32_C(0xa54ff53a),
		UINT32_C(0x510e527f), UINT32_C(0x9b05688c), UINT32_C(0x1f83d9ab), UINT32_C(0x5be0cd19)
	};
	memcpy(context->state,initial,sizeof initial);
	context->bit_count = 0;
	context->block_size = 0;
}

static void
sha256_update(sha256_context *context, const unsigned char *data, size_t size)
{
	context->bit_count += (uint64_t)size * 8;
	while (size) {
		size_t available = sizeof context->block - context->block_size;
		size_t amount = size < available ? size : available;
		memcpy(context->block + context->block_size,data,amount);
		context->block_size += amount;
		data += amount;
		size -= amount;
		if (context->block_size == sizeof context->block) {
			sha256_transform(context,context->block);
			context->block_size = 0;
		}
	}
}

static void
sha256_hex(const char *text, char output[65])
{
	static const char digits[] = "0123456789abcdef";
	sha256_context context;
	uint64_t bit_count;
	unsigned char digest[32];
	size_t index;

	sha256_init(&context);
	sha256_update(&context,(const unsigned char *)text,strlen(text));
	bit_count = context.bit_count;
	context.block[context.block_size++] = 0x80;
	if (context.block_size > 56) {
		memset(context.block + context.block_size,0,64 - context.block_size);
		sha256_transform(&context,context.block);
		context.block_size = 0;
	}
	memset(context.block + context.block_size,0,56 - context.block_size);
	for (index = 0; index != 8; index++)
		context.block[63 - index] = (unsigned char)(bit_count >> (index * 8));
	sha256_transform(&context,context.block);
	for (index = 0; index != 8; index++) {
		digest[index * 4] = (unsigned char)(context.state[index] >> 24);
		digest[index * 4 + 1] = (unsigned char)(context.state[index] >> 16);
		digest[index * 4 + 2] = (unsigned char)(context.state[index] >> 8);
		digest[index * 4 + 3] = (unsigned char)context.state[index];
	}
	for (index = 0; index != sizeof digest; index++) {
		output[index * 2] = digits[digest[index] >> 4];
		output[index * 2 + 1] = digits[digest[index] & 15];
	}
	output[64] = 0;
}

static int
load_exceptions(exception_set *exceptions, const char *path)
{
	FILE *input = fopen(path,"r");
	char line[LINE_CAPACITY];
	unsigned long long manifest_line = 0;
	int result = 0;

	if (!input) {
		report_errno("cannot open",path);
		return 0;
	}
	while (fgets(line,sizeof line,input)) {
		char *fields[4];
		char *cursor;
		char *end;
		unsigned long long source_line;
		source_exception *grown;
		size_t field;

		manifest_line++;
		cursor = line;
		while (*cursor == ' ' || *cursor == '\t')
			cursor++;
		if (!*cursor || *cursor == '\n' || *cursor == '\r' ||
		    *cursor == '#')
			continue;
		fields[0] = cursor;
		for (field = 1; field != 4; field++) {
			cursor = strchr(cursor,'\t');
			if (!cursor)
				break;
			*cursor++ = 0;
			fields[field] = cursor;
		}
		if (field != 4 || strchr(fields[3],'\t'))
			goto invalid;
		end = fields[3] + strlen(fields[3]);
		while (end != fields[3] &&
		       (end[-1] == '\n' || end[-1] == '\r'))
			*--end = 0;
		errno = 0;
		source_line = strtoull(fields[2],&end,10);
		if (errno || !source_line || *end || !*fields[1] ||
		    !valid_sha256(fields[3]))
			goto invalid;
		grown = realloc(exceptions->items,
		                (exceptions->count + 1) * sizeof *grown);
		if (!grown) {
			fprintf(stderr,"morpheus-gener-prepare: out of memory\n");
			goto finish;
		}
		exceptions->items = grown;
		grown += exceptions->count;
		grown->path = strdup(fields[1]);
		if (!grown->path) {
			fprintf(stderr,"morpheus-gener-prepare: out of memory\n");
			goto finish;
		}
		if (!parse_exception_kind(fields[0],&grown->kind)) {
			free(grown->path);
			goto invalid;
		}
		grown->line_number = source_line;
		memcpy(grown->sha256,fields[3],sizeof grown->sha256);
		grown->seen = 0;
		exceptions->count++;
		continue;

invalid:
		fprintf(stderr,
		        "morpheus-gener-prepare: %s:%llu: invalid exception record\n",
		        path,manifest_line);
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
	if (!result)
		free_exceptions(exceptions);
	return result;
}

static int
copy_text(char *destination, size_t capacity, const char *source)
{
	int length = snprintf(destination,capacity,"%s",source);

	return length >= 0 && (size_t)length < capacity;
}

static int
take_token(const char **cursor, char *token, size_t capacity)
{
	const char *start = *cursor;
	size_t length;

	while (*start == ' ' || *start == '\t')
		start++;
	length = 0;
	while (start[length] && start[length] != ' ' && start[length] != '\t')
		length++;
	if (!length || length >= capacity)
		return 0;
	memcpy(token,start,length);
	token[length] = 0;
	*cursor = start + length;
	return 1;
}

static int
valid_derivation_name(const char *name)
{
	const unsigned char *cursor = (const unsigned char *)name;

	while (*cursor) {
		if (!((*cursor >= 'a' && *cursor <= 'z') ||
		      (*cursor >= 'A' && *cursor <= 'Z') ||
		      (*cursor >= '0' && *cursor <= '9') || *cursor == '_'))
			return 0;
		cursor++;
	}
	return cursor != (const unsigned char *)name;
}

static int
expand_request(prepare_state *state, const char *request, const char *path,
               unsigned long long line_number)
{
	FILE *stream;
	char *record = NULL;
	size_t size = 0;
	int expanded;

	stream = open_memstream(&record,&size);
	if (!stream) {
		fprintf(stderr,"morpheus-gener-prepare: out of memory\n");
		return 0;
	}
	expanded = morpheus_gener_expand_derivation(
	    stream,state->derivation_stem,state->derivation_type,
	    state->derivation_keys,request);
	if (fclose(stream)) {
		free(record);
		report_errno("cannot finalize derivation",path);
		return 0;
	}
	if (expanded != 1) {
		fprintf(stderr,
		        "morpheus-gener-prepare: %s:%llu: derivation %s produced no record\n",
		        path,line_number,state->derivation_type);
		free(record);
		return 0;
	}
	if (!append_bytes(state->output,record,size)) {
		fprintf(stderr,"morpheus-gener-prepare: out of memory\n");
		free(record);
		return 0;
	}
	free(record);
	return 1;
}

static int
flush_derivation(prepare_state *state, const char *path,
                 unsigned long long line_number)
{
	if (!state->have_derivation || state->have_explicit_request)
		return 1;
	state->have_explicit_request = 1;
	return expand_request(state,"pr",path,line_number);
}

static void
report_errno(const char *operation, const char *path)
{
	fprintf(stderr,"morpheus-gener-prepare: %s %s: %s\n",
	        operation,path,strerror(errno));
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

static int
path_has_suffix(const char *path, const char *suffix)
{
	size_t path_length = strlen(path);
	size_t suffix_length = strlen(suffix);

	if (suffix_length > path_length ||
	    strcmp(path + path_length - suffix_length,suffix))
		return 0;
	return suffix_length == path_length ||
	       path[path_length - suffix_length - 1] == '/';
}

static source_exception *
find_exception(exception_set *exceptions, const char *path,
               unsigned long long line_number)
{
	size_t index;

	if (!exceptions)
		return NULL;
	for (index = 0; index != exceptions->count; index++) {
		source_exception *exception = exceptions->items + index;

		if (exception->line_number == line_number &&
		    path_has_suffix(path,exception->path))
			return exception;
	}
	return NULL;
}

static int
apply_exception(prepare_state *state, source_exception *exception,
                const char *content, const char *path,
                unsigned long long line_number)
{
	const char *cursor;
	char actual_sha256[65];

	if (exception->seen) {
		fprintf(stderr,
		        "morpheus-gener-prepare: %s:%llu: exception matched twice\n",
		        path,line_number);
		return 0;
	}
	sha256_hex(content,actual_sha256);
	if (strcmp(actual_sha256,exception->sha256)) {
		fprintf(stderr,
		        "morpheus-gener-prepare: %s:%llu: exception source fingerprint mismatch\n",
		        path,line_number);
		return 0;
	}
	switch (exception->kind) {
	case EXCEPTION_INVALID_DERIVATION:
		if (strncmp(content,":de:",4) ||
		    !flush_derivation(state,path,line_number))
			return 0;
		state->base = BASE_NONE;
		state->have_derivation = 0;
		state->have_explicit_request = 0;
		state->saved_request[0] = 0;
		state->skip_invalid_derivation = 1;
		break;
	case EXCEPTION_INVALID_RECORD:
		if (!is_generation_record(content) ||
		    (content[4] != ' ' && content[4] != '\t'))
			return 0;
		break;
	case EXCEPTION_ORPHAN_CONTINUATION:
		if (*content != '@')
			return 0;
		break;
	case EXCEPTION_ORPHAN_REQUEST:
		if (*content != ';' || state->have_derivation)
			return 0;
		break;
	case EXCEPTION_ZERO_CONTINUATION:
		if (*content != '@' || state->base != BASE_DERIVATION)
			return 0;
		break;
	case EXCEPTION_ZERO_REQUEST:
		cursor = content + 1;
		if (*content != ';' || !state->have_derivation ||
		    !take_token(&cursor,state->saved_request,
		                sizeof state->saved_request))
			return 0;
		state->have_explicit_request = 1;
		state->base = BASE_DERIVATION;
		break;
	}
	exception->seen = 1;
	return 1;
}

static int
all_exceptions_seen(const exception_set *exceptions)
{
	size_t index;

	for (index = 0; index != exceptions->count; index++) {
		if (!exceptions->items[index].seen) {
			fprintf(stderr,
			        "morpheus-gener-prepare: unmatched exception: %s:%llu\n",
			        exceptions->items[index].path,
			        exceptions->items[index].line_number);
			return 0;
		}
	}
	return 1;
}

static int
is_generation_record(const char *line)
{
	static const char *const prefixes[] = {
		":no:", ":aj:", ":vs:", ":wd:", ":vb:"
	};
	size_t prefix;

	for (prefix = 0; prefix != sizeof prefixes / sizeof prefixes[0];
	     prefix++) {
		if (!strncmp(line,prefixes[prefix],4))
			return 1;
	}
	return 0;
}

static char *
base_prefix(const char *line, int *complete)
{
	const char *cursor = line;
	const char *second;
	size_t length;
	char *result;

	*complete = 0;
	while (*cursor && *cursor != ' ' && *cursor != '\t')
		cursor++;
	if (!*cursor)
		return NULL;
	while (*cursor == ' ' || *cursor == '\t')
		cursor++;
	second = cursor;
	while (*cursor && *cursor != ' ' && *cursor != '\t')
		cursor++;
	if (cursor == second)
		return NULL;
	*complete = 1;
	length = (size_t)(cursor - line);
	result = malloc(length + 1);
	if (!result)
		return NULL;
	memcpy(result,line,length);
	result[length] = 0;
	return result;
}

static int
append_bytes(prepared_buffer *output, const char *data, size_t size)
{
	if (size > SIZE_MAX - output->size)
		return 0;
	if (output->size + size > output->capacity) {
		size_t required = output->size + size;
		size_t capacity = output->capacity ? output->capacity : 16384;
		char *grown;

		while (capacity < required) {
			if (capacity > SIZE_MAX / 2)
				capacity = required;
			else
				capacity *= 2;
		}
		grown = realloc(output->data,capacity);
		if (!grown)
			return 0;
		output->data = grown;
		output->capacity = capacity;
	}
	memcpy(output->data + output->size,data,size);
	output->size += size;
	return 1;
}

static int
write_line(prepared_buffer *output, const char *line)
{
	return append_bytes(output,line,strlen(line)) &&
	       append_bytes(output,"\n",1);
}

static int
prepare_file(prepare_state *state, exception_set *exceptions, const char *path)
{
	FILE *input = fopen(path,"r");
	char line[LINE_CAPACITY];
	unsigned long long line_number = 0;
	int result = 0;

	if (!input) {
		report_errno("cannot open",path);
		return 0;
	}
	free(state->base_prefix);
	state->base_prefix = NULL;
	state->base = BASE_NONE;
	state->have_lemma = 0;
	state->have_derivation = 0;
	state->have_explicit_request = 0;
	state->skip_invalid_derivation = 0;

	while (fgets(line,sizeof line,input)) {
		char *content;
		size_t length;

		line_number++;
		length = strlen(line);
		if (length == sizeof line - 1 && line[length - 1] != '\n') {
			fprintf(stderr,
			        "morpheus-gener-prepare: %s:%llu: line too long\n",
			        path,line_number);
			goto finish;
		}
		content = trim(line);
		if (!*content || *content == '#' || *content == '?')
			continue;
		if (state->skip_invalid_derivation &&
		    (*content == ';' || *content == '@'))
			continue;
		state->skip_invalid_derivation = 0;
		{
			source_exception *exception =
			    find_exception(exceptions,path,line_number);

			if (exception) {
				if (!apply_exception(state,exception,content,path,
				                     line_number)) {
					fprintf(stderr,
					        "morpheus-gener-prepare: %s:%llu: exception does not match parser state\n",
					        path,line_number);
					goto finish;
				}
				continue;
			}
		}

		if (!strncmp(content,":le:",4)) {
			char *lemma = trim(content + 4);

			if (!flush_derivation(state,path,line_number))
				goto finish;
			if (!*lemma) {
				fprintf(stderr,
				        "morpheus-gener-prepare: %s:%llu: invalid lemma\n",
				        path,line_number);
				goto finish;
			}
			free(state->base_prefix);
			state->base_prefix = NULL;
			state->base = BASE_NONE;
			state->have_lemma = 1;
			state->have_derivation = 0;
			state->have_explicit_request = 0;
			if (!write_line(state->output,content))
				goto write_error;
			continue;
		}

		if (is_generation_record(content)) {
			char *prefix;
			int complete;
			int clears_derivation =
			    !strncmp(content,":no:",4) ||
			    !strncmp(content,":aj:",4) ||
			    !strncmp(content,":vs:",4);

			if (!state->have_lemma) {
				fprintf(stderr,
				        "morpheus-gener-prepare: %s:%llu: record before lemma\n",
				        path,line_number);
				goto finish;
			}
			prefix = base_prefix(content,&complete);
			if (!prefix) {
				if (complete)
					fprintf(stderr,"morpheus-gener-prepare: out of memory\n");
				else
					fprintf(stderr,
					        "morpheus-gener-prepare: %s:%llu: incomplete record\n",
					        path,line_number);
				goto finish;
			}
			free(state->base_prefix);
			state->base_prefix = prefix;
			state->base = BASE_DIRECT;
			if (clears_derivation) {
				state->have_derivation = 0;
				state->have_explicit_request = 0;
				state->saved_request[0] = 0;
			}
			if (!write_line(state->output,content))
				goto write_error;
			continue;
		}

		if (*content == '@') {
			if (!state->have_lemma || state->base == BASE_NONE) {
				fprintf(stderr,
				        "morpheus-gener-prepare: %s:%llu: continuation without active record\n",
				        path,line_number);
				goto finish;
			}
			if (state->base == BASE_DIRECT) {
				if (!append_bytes(state->output,state->base_prefix,
				                  strlen(state->base_prefix)) ||
				    !write_line(state->output,content + 1))
					goto write_error;
			} else {
				char request[LONGSTRING * 2];
				char *continuation = trim(content + 1);
				int length;

				if (!*state->saved_request) {
					fprintf(stderr,
					        "morpheus-gener-prepare: %s:%llu: derivation continuation without principal part\n",
					        path,line_number);
					goto finish;
				}
				length = snprintf(request,sizeof request,"%s%s%s",
				                  state->saved_request,
				                  *continuation ? " " : "",continuation);
				if (length < 0 || (size_t)length >= sizeof request ||
				    !expand_request(state,request,path,line_number))
					goto finish;
			}
			continue;
		}

		if (!strncmp(content,":de:",4)) {
			const char *cursor = content + 4;
			char *global;

			if (!state->have_lemma || *cursor == ' ' || *cursor == '\t' ||
			    !flush_derivation(state,path,line_number) ||
			    !take_token(&cursor,state->derivation_stem,
			                sizeof state->derivation_stem) ||
			    !take_token(&cursor,state->derivation_type,
			                sizeof state->derivation_type) ||
			    !valid_derivation_name(state->derivation_type)) {
				fprintf(stderr,
				        "morpheus-gener-prepare: %s:%llu: invalid derivation record\n",
				        path,line_number);
				goto finish;
			}
			global = trim((char *)cursor);
			if (!copy_text(state->derivation_keys,
			               sizeof state->derivation_keys,global))
				goto write_error;
			state->saved_request[0] = 0;
			state->have_explicit_request = 0;
			state->base = BASE_DERIVATION;
			state->have_derivation = 1;
			continue;
		}

		if (*content == ';') {
			const char *cursor = content + 1;
			char request[LONGSTRING];

			if (!state->have_derivation ||
			    !take_token(&cursor,state->saved_request,
			                sizeof state->saved_request) ||
			    !copy_text(request,sizeof request,trim(content + 1))) {
				fprintf(stderr,
				        "morpheus-gener-prepare: %s:%llu: invalid principal-part request\n",
				        path,line_number);
				goto finish;
			}
			state->have_explicit_request = 1;
			state->base = BASE_DERIVATION;
			if (!expand_request(state,request,path,line_number))
				goto finish;
			continue;
		}
	}
	if (ferror(input)) {
		report_errno("cannot read",path);
		goto finish;
	}
	if (!flush_derivation(state,path,line_number + 1))
		goto finish;
	result = 1;
	goto finish;

write_error:
	fprintf(stderr,"morpheus-gener-prepare: out of memory\n");

finish:
	if (fclose(input) && result) {
		report_errno("cannot close",path);
		result = 0;
	}
	return result;
}

static int
write_output(const prepared_buffer *prepared, const char *path)
{
	FILE *output;
	int result = 0;

	output = fopen(path,"wb");
	if (!output) {
		report_errno("cannot create",path);
		return 0;
	}
	if (prepared->size &&
	    fwrite(prepared->data,1,prepared->size,output) != prepared->size) {
		report_errno("cannot write",path);
		goto finish;
	}
	result = 1;

finish:
	if (fclose(output) && result) {
		report_errno("cannot close",path);
		result = 0;
	}
	if (!result)
		remove(path);
	return result;
}

int
main(int argc, char **argv)
{
	prepared_buffer prepared = { 0 };
	prepare_state state = { 0 };
	exception_set exceptions = { 0 };
	exception_set *active_exceptions = NULL;
	const char *output_path;
	int input;
	int result = EXIT_FAILURE;

#ifdef __EMSCRIPTEN__
	/* The packaged module serves the stemlib from MEMFS at /morphlib. An
	 * explicit MORPHLIB (the Emscripten test build under NODERAWFS) wins. */
	if (setenv("MORPHLIB","/morphlib",0)) {
		report_errno("cannot configure","MORPHLIB");
		return EXIT_FAILURE;
	}
#endif

	if (argc >= 5 && !strcmp(argv[1],"--exceptions")) {
		if (!load_exceptions(&exceptions,argv[2]))
			goto finish;
		active_exceptions = &exceptions;
		output_path = argv[3];
		input = 4;
	} else if (argc >= 3) {
		output_path = argv[1];
		input = 2;
	} else {
		fprintf(stderr,
		        "usage: morpheus_gener_source_preparer [--exceptions MANIFEST] OUTPUT INPUT...\n");
		return EXIT_FAILURE;
	}
	state.output = &prepared;
	for (; input != argc; input++) {
		if (!prepare_file(&state,active_exceptions,argv[input]))
			goto finish;
	}
	if (active_exceptions && !all_exceptions_seen(active_exceptions))
		goto finish;
	if (!write_output(&prepared,output_path))
		goto finish;
	result = EXIT_SUCCESS;

finish:
	free_exceptions(&exceptions);
	free(state.base_prefix);
	free(prepared.data);
	return result;
}
