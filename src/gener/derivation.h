/* SPDX-License-Identifier: MPL-2.0 */

#ifndef MORPHEUS_GENER_DERIVATION_H
#define MORPHEUS_GENER_DERIVATION_H

#include <stdio.h>

/*
 * Expand one historical principal-part request into one explicit generation
 * record. The rule tables are resolved through the active MORPHLIB context.
 *
 * Returns 1 when a rule produced a record, 0 when no rule matched, and -1 on
 * malformed input, I/O failure, or allocation failure.
 */
int morpheus_gener_expand_derivation(FILE *output, const char *stem,
                                     const char *derivation,
                                     const char *global_keys,
                                     const char *request_keys);

/*
 * Describe one prepared `:vs:` record for the default principal parts:
 * *part receives its principal part (0 present, 1 future, 2 aorist, 3
 * perfect, 4 perfect middle-passive, 5 aorist passive, 6 future perfect, or
 * -1 for none), and *restricted whether its keys fix a dialect, tense or
 * mood.
 *
 * Returns 1 on success and 0 on malformed input or allocation failure.
 */
int morpheus_gener_record_traits(const char *record, int *part,
                                 int *restricted);

/* The voice bits (ACTIVE, MIDDLE, PASSIVE) fixed by ASCII keys, or zero. */
int morpheus_gener_keys_voice(const char *keys, int *voice);

/*
 * Whether the ASCII keys of a :de: line confine the derivation: they fix a
 * tense or a mood, or mark a present formation (pres_redupl, n_infix) that
 * the expansion applies to every principal part it builds.
 */
int morpheus_gener_keys_confine(const char *keys, int *confined);

#endif
