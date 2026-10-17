<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Combined Latin candidate

Qualified code: `6d0f7668d25dbc096da066799d88509c78ffa84d`. The
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39054628293)
succeeds with four full LISTALL passes; the
[aggregate receipt](qualification/latin-combined-candidate-6d0f766.json)
records counts, categories and SHA-256 values only.

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

Against the original candidate:

| Metric | Original candidate | Combined candidate |
| --- | ---: | ---: |
| Recognized literal forms | 847,750 | 852,926 |
| Native analysis rows | 2,100,530 | 2,145,245 |
| Lost recognized forms | — | 0 |
| Removed eleven-field readings | — | 16 |
| Added eleven-field readings | — | 44,731 |
| Changed grammatical multisets | — | 27,493 |
| Equal-count multiset changes | — | 0 |

Of the 44,731 additions, 40,550 are direct, 1,886 carry native preverbs and
2,295 occur on forms with both. The 16 removed readings, on eight forms that
stay recognized, are all enclitic retries displaced by a new direct
analysis: the displacement review reproduces every one on the input without
its `-dum`. The identical-root control over the same forms changes nothing.
The sum of the separate trials' additions (38,064 + 1,117 + 1,152 + 2,538 +
2,427) is 45,298; the combination adds 44,731 because the two present
proofs overlap and because a repaired or reclassed record replaces readings
another trial would have added beside the defective one.

Against the controlled rebuilt baseline, which the earlier global
qualification used as the historical witness, the run reproduces the
original candidate's comparison exactly (2,006,554 readings retained,
41,774 removed, 93,976 added; 6,789 forms completely lost under 133 lemmas)
and then measures the combination:

| Controlled baseline → | Original candidate | Combined candidate |
| --- | ---: | ---: |
| Readings retained | 2,006,554 | 2,010,262 |
| Readings removed | 41,774 | 38,066 |
| Readings added | 93,976 | 134,983 |
| Forms recognized by both | 831,201 | 832,224 |
| Forms completely lost | 6,789 | 5,766 |
| Lemmas with completely lost forms | 133 | 114 |

The combination therefore stops removing **3,708** historical readings and
**1,023** completely lost forms are recognized again, under 19 fewer lemmas.
These are exact eleven-field matches with the historical witness on
LISTALL, not family-form estimates. The 38,066 readings still removed and the
5,766 forms still lost remain the arbitration backlog; the 134,983 additions
include the native-preverb readings whose composed identities are
unqualified.

## Remaining arbitration

The combination is a measured candidate, not a selector or a production
source. Composed identities from native preverbs, the residual complete
alternates without proof, the remaining loss dossiers and the other open
questions of the separate trials are unchanged. The PR remains a draft.
