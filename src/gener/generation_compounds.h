/* SPDX-License-Identifier: MPL-2.0 */

#ifndef MORPHEUS_GENERATION_COMPOUNDS_H
#define MORPHEUS_GENERATION_COMPOUNDS_H

#include <stddef.h>

#include <gkstring.h>

/*
 * Compound verbs are generated from the simple verb's records, as analysis
 * finds them: preverb(s) + simple verb, named after stemsrc/vbs.cmp.ml.
 */
typedef struct morpheus_compound_table morpheus_compound_table;

typedef struct {
	/* The preverbs, outermost first: "a)nti/,para/". */
	char preverbs[MAXWORDSIZE];
	/* The simple verb's generation-index key: "di/dwmi". */
	char lemma[MAXWORDSIZE];
} morpheus_compound_decomposition;

typedef enum {
	MORPHEUS_COMPOUND_OK = 0,
	MORPHEUS_COMPOUND_NO_MEMORY = 1
} morpheus_compound_status;

/*
 * Copies the canonical form of a lemma: an initial '!', hyphens, quantity
 * marks and diaeresis marks removed, as the generation index and the public
 * API canonicalise lemma keys. Returns 0 when it does not fit.
 */
int morpheus_compound_canonical(const char *source, size_t length, char *out,
                                size_t size);

/*
 * The decompositions of a canonical lemma that analysis reports under that
 * lemma: the listed compound (a)podi/dwmi), a compound absent from the list
 * that analysis names with a hyphen (a)mfi/-lu/w, canonically a)mfi/lu/w),
 * or the outer preverbs of a listed compound (a)nti/-paradi/dwmi). Each
 * candidate is kept only when the naming analysis applies gives back the
 * requested lemma. Must run with the generation service's runtime context
 * active; the table is built on first use from the context's stemlib and
 * stays empty when the stemlib has no compound list. *decompositions is
 * allocated and must be freed by the caller.
 */
morpheus_compound_status morpheus_compound_decompositions(
    morpheus_compound_table **table, const char *canonical_lemma,
    morpheus_compound_decomposition **decompositions, size_t *count);

/*
 * Whether analysis reports a stem of canonical_lemma that carries its own
 * preverbs (a pb: key) under canonical_lemma itself: a)mfisbhte/w for its
 * pb:a)mfi/ stems, but e)pimele/omai, not mele/omai, for the pb:e)pi/ stems
 * filed under mele/omai. Same conditions as above.
 */
morpheus_compound_status morpheus_compound_names_lemma(
    morpheus_compound_table **table, const char *preverbs,
    const char *canonical_lemma, int *same);

void morpheus_compound_table_destroy(morpheus_compound_table *table);

#endif
