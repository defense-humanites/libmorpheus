/* SPDX-License-Identifier: MPL-2.0 */

#ifndef MORPHEUS_GENER_DERIVATION_H
#define MORPHEUS_GENER_DERIVATION_H

#include <stdio.h>

/*
 * Correct two stem alterations of the historical expansion
 * (docs/gener-derivations.md): aspirate dissimilation applies neither to an
 * aorist passive stem ending in its aspirate, as its 1989 exception meant,
 * nor to a regular (`reg_deriv`) derivation, whose stem keeps the aspirates
 * of its noun; consonant euphony applies only at the junction of the stem
 * and the suffix. Without it, the expansion matches the historical `do_conj`.
 */
#define MORPHEUS_GENER_EXPAND_CORRECTED 1u

/*
 * Expand one historical principal-part request into one explicit generation
 * record. The rule tables are resolved through the active MORPHLIB context.
 * flags is 0 or MORPHEUS_GENER_EXPAND_CORRECTED.
 *
 * Returns 1 when a rule produced a record, 0 when no rule matched, and -1 on
 * malformed input, I/O failure, or allocation failure.
 */
int morpheus_gener_expand_derivation(FILE *output, const char *stem,
                                     const char *derivation,
                                     const char *global_keys,
                                     const char *request_keys,
                                     unsigned int flags);

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

/*
 * Whether a derivation type is a regular derivation (`reg_deriv` in
 * rule_files/derivtypes.table: ew_denom, ow_denom, izw...), as opposed to a
 * primary conjugation (`prim_deriv`: reg_conj) or a verb stem class
 * (`verbstem`: e_suppl, skw, o_stem...).
 */
int morpheus_gener_derivation_is_regular(const char *type, int *regular);

/* The voice bits (ACTIVE, MIDDLE, PASSIVE) fixed by ASCII keys, or zero. */
int morpheus_gener_keys_voice(const char *keys, int *voice);

/*
 * Whether the ASCII keys of a :de: line confine the derivation: they fix a
 * tense or a mood, or mark a present formation (pres_redupl, n_infix) that
 * the expansion applies to every principal part it builds.
 */
int morpheus_gener_keys_confine(const char *keys, int *confined);

#endif
