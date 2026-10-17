<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Combined Latin candidate

Each of the recent trials was staged and measured on the unchanged full
source candidate `6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9`,
so that every receipt isolates one bounded recipe. The trials also interact:
the attribution replay reclasses presents that the prefix-alternate recipe
then copies, the prefix recipe copies the repaired labiovelar parts, and the
backlinked presents of one proof pre-empt the other. This document qualifies
the recipes applied together, in a fixed order, on one private candidate. It
changes no recipe.

## Stage chain

`tools/reconstruct-latin-combined-candidate.py` applies, each on the output
of the previous stage:

| Stage | Recipe | Blocks changed | Records |
| --- | --- | ---: | --- |
| 1 | [editor attributions](latin-editor-attributions.md) | 12 | 26 removed, 20 written (8 presents reclassed) |
| 2 | [`</itype>` tag leak](latin-itype-tag-leak.md) | 13 | 13 deleted |
| 3 | [labiovelar short suffix](latin-velar-short-suffix.md) | 8 | 16 replaced |
| 4 | [abbreviated prefix alternates](latin-prefix-alternates.md) | 366 | 583 added |
| 5 | [backlinked presents, reference proof](latin-backlinked-present-classes.md) | 19 | 19 added |
| 6 | backlinked presents, quotation proof | 10 | 11 added |
| 7 | [`-jicio` duplicate components](lexical-exports.md#duplicate-components-proved-by-complete-third-conjugation-alternates) | 0 | none |

Stage 4 adds two records more than its separate trial because two
attribution blocks now hold a regular `are_vb` derivative and a written
perfect that the prefix spelling copies. Stage 6 adds four records fewer
because the reference proof already staged them. Stage 7 finds nothing: the
`-io` block kept outside the attribution replay still carries its
attribution stem, so the `-jicio` proof withholds it. Every stage's input and
output SHA-256 is recorded; the chain is pinned in the qualification tool and
the private combined source has SHA-256
`f719a4e118195bc0d7696c30121a11495fac21cdfadb70ad95dd378443812463`.

## Native qualification

`tools/qualify-latin-combined-candidate.py` rebuilds the original native
candidate, checks its index receipts, builds the combination and requires
unchanged nominal indexes. Against the original candidate the combination
adds **644** records (181 `are_vb`, 12 deponent `are_vb`, 3 `conj1`, 39
`conj2`, 134 `conj3`, 16 `conj3_io`, 12 `conj4`, 7 `ire_vb`, 129 `perfstem`,
111 `pp4`) and removes **50** (13 attribution stems, 13 leaked-tag stems, 8
reclassed `conj1` presents, 8 defective labiovelar perfects and 8 supines).

The 644 added records receive the engine's present, perfect or supine cells,
**3,864 cells on 3,675 forms**: 96 are covered before the combination and all
3,864 after, every added record covered. On those forms the sixteen-field
comparison retains 5,820 readings, adds 6,125 and removes none; 784 forms
become recognized and none is lost. Against the controlled rebuilt baseline,
628 of the additions on these forms are exact historical readings. Sixteen
of the 59 changed-definition loss cases have a changed block. The
identical-root control changes nothing.

## Full LISTALL diagnostics

The dedicated workflow compares the combination with the original candidate
(eleven fields, with the enclitic displacement review), runs the
identical-root control, and compares both the original candidate and the
combination with the controlled rebuilt baseline, so that the historical
readings no longer removed and the completely lost forms no longer lost are
measured globally rather than on family forms. See the aggregate receipt
linked from the pull request once that run is qualified.

## Remaining arbitration

The combination is a measured candidate, not a selector or a production
source. Composed identities from native preverbs, the residual complete
alternates without proof, the remaining loss dossiers and the other open
questions of the separate trials are unchanged. The PR remains a draft.
