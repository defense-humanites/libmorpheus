/* SPDX-License-Identifier: MPL-2.0 */

#include "generation_compounds.h"

#include <stdlib.h>
#include <string.h>

#include "../morphlib/runtime_context_internal.h"

int compound_verb_lemma(const char *preverbs, const char *lemma, char *name,
                        size_t size);
int compound_verb_lines(char ***lines, int *count);
int preverb_lemmas(const char **lemmas, int capacity);

#define MAX_PREVERB_LEMMAS 64

typedef struct {
	char *name;          /* canonical compound name */
	char *decomposition; /* "preverbs-lemma", as listed */
} compound_entry;

typedef struct {
	char *canonical;     /* canonical simple lemma */
	char *source;        /* the lemma as the list spells it */
} simple_entry;

struct morpheus_compound_table {
	compound_entry *entries;
	size_t entry_count;
	simple_entry *simples;
	size_t simple_count;
	const char *preverbs[MAX_PREVERB_LEMMAS];
	int preverb_count;
};

typedef struct {
	morpheus_compound_decomposition *items;
	size_t count;
	size_t capacity;
} decomposition_list;

int
morpheus_compound_canonical(const char *source, size_t length, char *out,
                            size_t size)
{
	size_t input;
	size_t output = 0;

	if (!source || !out || !size)
		return 0;
	if (length && source[0] == '!')
		source++, length--;
	for (input = 0; input != length; input++) {
		char c = source[input];

		if (c == '-' || c == '_' || c == '^' || c == '+')
			continue;
		if (output + 1 >= size)
			return 0;
		out[output++] = c;
	}
	out[output] = 0;
	return 1;
}

static char *
copy_text(const char *source, size_t length)
{
	char *copy = malloc(length + 1);

	if (!copy)
		return NULL;
	memcpy(copy,source,length);
	copy[length] = 0;
	return copy;
}

static char *
canonical_copy(const char *source, size_t length)
{
	char buffer[MAXWORDSIZE];

	if (!morpheus_compound_canonical(source,length,buffer,sizeof buffer))
		return NULL;
	return copy_text(buffer,strlen(buffer));
}

static int
compare_entries(const void *left, const void *right)
{
	const compound_entry *a = left;
	const compound_entry *b = right;
	int order = strcmp(a->name,b->name);

	return order ? order : strcmp(a->decomposition,b->decomposition);
}

static int
compare_simples(const void *left, const void *right)
{
	const simple_entry *a = left;
	const simple_entry *b = right;
	int order = strcmp(a->canonical,b->canonical);

	return order ? order : strcmp(a->source,b->source);
}

void
morpheus_compound_table_destroy(morpheus_compound_table *table)
{
	size_t item;

	if (!table)
		return;
	for (item = 0; item != table->entry_count; item++) {
		free(table->entries[item].name);
		free(table->entries[item].decomposition);
	}
	for (item = 0; item != table->simple_count; item++) {
		free(table->simples[item].canonical);
		free(table->simples[item].source);
	}
	free(table->entries);
	free(table->simples);
	free(table);
}

/*
 * A stemlib without a compound list, or without a preverb table, has no
 * compounds: the table stays empty and simple lemmas are unaffected.
 */
static morpheus_compound_status
build_table(morpheus_compound_table **built)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	morpheus_compound_table *table;
	char **lines = NULL;
	int line_count = 0;
	int line;

	table = calloc(1,sizeof *table);
	if (!table)
		return MORPHEUS_COMPOUND_NO_MEMORY;
	if (!compound_verb_lines(&lines,&line_count) ||
	    (table->preverb_count =
	         preverb_lemmas(table->preverbs,MAX_PREVERB_LEMMAS)) < 0) {
		if (morpheus_runtime_context_error(context) ==
		    MORPHEUS_RUNTIME_ERROR_NO_MEMORY) {
			morpheus_compound_table_destroy(table);
			return MORPHEUS_COMPOUND_NO_MEMORY;
		}
		morpheus_runtime_context_clear_error(context);
		table->preverb_count = 0;
		*built = table;
		return MORPHEUS_COMPOUND_OK;
	}
	if (line_count > 0) {
		table->entries = calloc((size_t)line_count,sizeof *table->entries);
		table->simples = calloc((size_t)line_count,sizeof *table->simples);
		if (!table->entries || !table->simples) {
			morpheus_compound_table_destroy(table);
			return MORPHEUS_COMPOUND_NO_MEMORY;
		}
	}
	for (line = 0; line < line_count; line++) {
		const char *text = lines[line];
		size_t decomposition_length;
		const char *name;
		size_t name_length;
		const char *hyphen;
		compound_entry *entry;
		simple_entry *simple;

		if (!text)
			continue;
		decomposition_length = strcspn(text," \t\r\n");
		name = text + decomposition_length;
		name += strspn(name," \t");
		name_length = strcspn(name," \t\r\n");
		hyphen = memchr(text,'-',decomposition_length);
		if (!decomposition_length || !name_length || !hyphen ||
		    hyphen == text || hyphen + 1 == text + decomposition_length)
			continue;
		entry = table->entries + table->entry_count;
		entry->name = canonical_copy(name,name_length);
		entry->decomposition = copy_text(text,decomposition_length);
		simple = table->simples + table->simple_count;
		simple->source = copy_text(hyphen + 1,
		                           (size_t)(text + decomposition_length -
		                                    hyphen - 1));
		simple->canonical = simple->source
		    ? canonical_copy(simple->source,strlen(simple->source))
		    : NULL;
		if (!entry->name || !entry->decomposition || !simple->source ||
		    !simple->canonical) {
			free(entry->name);
			free(entry->decomposition);
			free(simple->source);
			free(simple->canonical);
			entry->name = entry->decomposition = NULL;
			simple->source = simple->canonical = NULL;
			morpheus_compound_table_destroy(table);
			return MORPHEUS_COMPOUND_NO_MEMORY;
		}
		table->entry_count++;
		table->simple_count++;
	}
	if (table->entry_count)
		qsort(table->entries,table->entry_count,sizeof *table->entries,
		      compare_entries);
	if (table->simple_count) {
		size_t read;
		size_t write = 0;

		qsort(table->simples,table->simple_count,sizeof *table->simples,
		      compare_simples);
		for (read = 0; read != table->simple_count; read++) {
			if (write &&
			    !compare_simples(table->simples + write - 1,
			                     table->simples + read)) {
				free(table->simples[read].canonical);
				free(table->simples[read].source);
				continue;
			}
			table->simples[write++] = table->simples[read];
		}
		table->simple_count = write;
	}
	*built = table;
	return MORPHEUS_COMPOUND_OK;
}

static size_t
first_entry(const morpheus_compound_table *table, const char *name)
{
	size_t low = 0;
	size_t high = table->entry_count;

	while (low < high) {
		size_t middle = low + (high - low) / 2;

		if (strcmp(table->entries[middle].name,name) < 0)
			low = middle + 1;
		else
			high = middle;
	}
	return low;
}

static size_t
first_simple(const morpheus_compound_table *table, const char *canonical)
{
	size_t low = 0;
	size_t high = table->simple_count;

	while (low < high) {
		size_t middle = low + (high - low) / 2;

		if (strcmp(table->simples[middle].canonical,canonical) < 0)
			low = middle + 1;
		else
			high = middle;
	}
	return low;
}

/*
 * Keeps (preverbs, lemma) when the name analysis gives that verb is the
 * requested lemma. A naming failure (a key too long for analysis) drops the
 * candidate, as analysis drops the reading.
 */
static morpheus_compound_status
add_candidate(decomposition_list *list, const char *request,
              const char *preverbs, const char *lemma)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	char name[MAXWORDSIZE];
	char canonical_name[MAXWORDSIZE];
	char key[MAXWORDSIZE];
	morpheus_compound_decomposition *item;
	size_t index;

	if (strlen(preverbs) >= sizeof item->preverbs)
		return MORPHEUS_COMPOUND_OK;
	if (!compound_verb_lemma(preverbs,lemma,name,sizeof name)) {
		if (morpheus_runtime_context_error(context) ==
		    MORPHEUS_RUNTIME_ERROR_NO_MEMORY)
			return MORPHEUS_COMPOUND_NO_MEMORY;
		morpheus_runtime_context_clear_error(context);
		return MORPHEUS_COMPOUND_OK;
	}
	if (!morpheus_compound_canonical(name,strlen(name),canonical_name,
	                                 sizeof canonical_name) ||
	    strcmp(canonical_name,request) ||
	    !morpheus_compound_canonical(lemma,strlen(lemma),key,sizeof key) ||
	    !*key)
		return MORPHEUS_COMPOUND_OK;
	for (index = 0; index != list->count; index++) {
		if (!strcmp(list->items[index].preverbs,preverbs) &&
		    !strcmp(list->items[index].lemma,key))
			return MORPHEUS_COMPOUND_OK;
	}
	if (list->count == list->capacity) {
		size_t capacity = list->capacity ? list->capacity * 2 : 4;
		morpheus_compound_decomposition *grown =
		    realloc(list->items,capacity * sizeof *grown);

		if (!grown)
			return MORPHEUS_COMPOUND_NO_MEMORY;
		list->items = grown;
		list->capacity = capacity;
	}
	item = list->items + list->count++;
	memcpy(item->preverbs,preverbs,strlen(preverbs) + 1);
	memcpy(item->lemma,key,strlen(key) + 1);
	return MORPHEUS_COMPOUND_OK;
}

/* The listed compounds whose canonical name is name, prefixed by outer. */
static morpheus_compound_status
add_listed(decomposition_list *list, const morpheus_compound_table *table,
           const char *request, const char *outer, const char *name)
{
	size_t entry;

	for (entry = first_entry(table,name);
	     entry != table->entry_count &&
	     !strcmp(table->entries[entry].name,name);
	     entry++) {
		const char *decomposition = table->entries[entry].decomposition;
		const char *hyphen = strchr(decomposition,'-');
		char preverbs[MAXWORDSIZE];
		size_t outer_length = outer ? strlen(outer) : 0;
		size_t inner_length = (size_t)(hyphen - decomposition);
		morpheus_compound_status status;

		if (outer_length + 1 + inner_length >= sizeof preverbs)
			continue;
		preverbs[0] = 0;
		if (outer_length) {
			memcpy(preverbs,outer,outer_length);
			preverbs[outer_length] = ',';
			preverbs[outer_length + 1] = 0;
		}
		strncat(preverbs,decomposition,inner_length);
		status = add_candidate(list,request,preverbs,hyphen + 1);
		if (status != MORPHEUS_COMPOUND_OK)
			return status;
	}
	return MORPHEUS_COMPOUND_OK;
}

/*
 * Reads request + at as preverb[,preverb...] followed by a lemma, the
 * canonical form of the hyphenated names analysis gives ("a)mfi/-lu/w",
 * "a)nti/,para/-di/dwmi", "a)nti/-paradi/dwmi").
 */
static morpheus_compound_status
add_hyphenated(decomposition_list *list, const morpheus_compound_table *table,
               const char *request, size_t at, const char *outer, int depth)
{
	int preverb;

	if (depth > 8)
		return MORPHEUS_COMPOUND_OK;
	for (preverb = 0; preverb < table->preverb_count; preverb++) {
		const char *candidate = table->preverbs[preverb];
		size_t length = strlen(candidate);
		char preverbs[MAXWORDSIZE];
		const char *rest;
		morpheus_compound_status status;
		size_t simple;
		int listed_source = 0;

		if (!length || strncmp(request + at,candidate,length))
			continue;
		if ((outer ? strlen(outer) + 1 : 0) + length >= sizeof preverbs)
			continue;
		preverbs[0] = 0;
		if (outer) {
			strcpy(preverbs,outer);
			strcat(preverbs,",");
		}
		strcat(preverbs,candidate);
		rest = request + at + length;
		if (*rest == ',') {
			status = add_hyphenated(list,table,request,
			                        (size_t)(rest + 1 - request),preverbs,
			                        depth + 1);
			if (status != MORPHEUS_COMPOUND_OK)
				return status;
			continue;
		}
		if (!*rest)
			continue;
		status = add_listed(list,table,request,preverbs,rest);
		if (status != MORPHEUS_COMPOUND_OK)
			return status;
		/*
		 * Name the simple verb as analysis does: with the spelling the
		 * compound list uses, which may keep marks the canonical form drops.
		 */
		for (simple = first_simple(table,rest);
		     simple != table->simple_count &&
		     !strcmp(table->simples[simple].canonical,rest);
		     simple++) {
			listed_source = 1;
			status = add_candidate(list,request,preverbs,
			                       table->simples[simple].source);
			if (status != MORPHEUS_COMPOUND_OK)
				return status;
		}
		if (!listed_source) {
			status = add_candidate(list,request,preverbs,rest);
			if (status != MORPHEUS_COMPOUND_OK)
				return status;
		}
	}
	return MORPHEUS_COMPOUND_OK;
}

morpheus_compound_status
morpheus_compound_decompositions(
    morpheus_compound_table **table, const char *canonical_lemma,
    morpheus_compound_decomposition **decompositions, size_t *count)
{
	decomposition_list list = { 0 };
	morpheus_compound_status status;

	*decompositions = NULL;
	*count = 0;
	if (!*table) {
		status = build_table(table);
		if (status != MORPHEUS_COMPOUND_OK)
			return status;
	}
	status = add_listed(&list,*table,canonical_lemma,NULL,canonical_lemma);
	if (status == MORPHEUS_COMPOUND_OK)
		status = add_hyphenated(&list,*table,canonical_lemma,0,NULL,0);
	if (status != MORPHEUS_COMPOUND_OK) {
		free(list.items);
		return status;
	}
	*decompositions = list.items;
	*count = list.count;
	return MORPHEUS_COMPOUND_OK;
}

morpheus_compound_status
morpheus_compound_names_lemma(morpheus_compound_table **table,
                              const char *preverbs,
                              const char *canonical_lemma, int *same)
{
	decomposition_list list = { 0 };
	morpheus_compound_status status = MORPHEUS_COMPOUND_OK;
	size_t simple;
	int listed_source = 0;

	*same = 0;
	if (!*table) {
		status = build_table(table);
		if (status != MORPHEUS_COMPOUND_OK)
			return status;
	}
	/* Name the lemma with the spelling the compound list uses, if any. */
	for (simple = first_simple(*table,canonical_lemma);
	     status == MORPHEUS_COMPOUND_OK &&
	     simple != (*table)->simple_count &&
	     !strcmp((*table)->simples[simple].canonical,canonical_lemma);
	     simple++) {
		listed_source = 1;
		status = add_candidate(&list,canonical_lemma,preverbs,
		                       (*table)->simples[simple].source);
	}
	if (status == MORPHEUS_COMPOUND_OK && !listed_source)
		status = add_candidate(&list,canonical_lemma,preverbs,
		                       canonical_lemma);
	*same = list.count != 0;
	free(list.items);
	return status;
}
