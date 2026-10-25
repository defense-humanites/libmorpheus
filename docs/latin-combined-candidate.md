<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Combined Latin candidate

Qualified code: `da8cd34` for the **eleven-stage combination** (the
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39960707178)
succeeds with four full LISTALL passes; the
[aggregate receipt](qualification/latin-combined-candidate-da8cd34.json)
records counts, categories and SHA-256 values only). The **nine-stage
combination** it extends was qualified on `1d91bb1` (receipt
[`latin-combined-candidate-1d91bb1.json`](qualification/latin-combined-candidate-1d91bb1.json),
private source `d02f4bdb…`, figures kept below); the six-stage one on
`6d0f766` and `b925a88` (`f719a4e1…`). The stage counts name the
separately qualified trials; each receipt also lists the earlier `-jicio`
repair as a closing stage entry, so the receipts carry seven, nine and
eleven entries respectively, the last one changing nothing (see
[the stage table](#stage-chain-eleven-stages) below).

Each of the recent trials was staged and measured on the unchanged full
source candidate `6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9`,
so that every receipt isolates one bounded recipe. The trials also interact:
the attribution replay reclasses presents that the prefix-alternate recipe
then copies, the prefix recipe copies the repaired labiovelar parts, and the
backlinked presents of one proof pre-empt the other. This document qualifies
the recipes applied together, in a fixed order, on one private candidate. It
changes no recipe.

## Stage chain (eleven stages)

`tools/reconstruct-latin-combined-candidate.py` applies, each on the output
of the previous stage:

| Stage | Recipe | Blocks changed | Records |
| --- | --- | ---: | --- |
| 1 | [editor attributions](latin-editor-attributions.md) | 12 | 26 removed, 20 written (8 presents reclassed) |
| 2 | [`</itype>` tag leak](latin-itype-tag-leak.md) | 13 | 13 deleted |
| 3 | [labiovelar short suffix](latin-velar-short-suffix.md) | 8 | 16 replaced |
| 4 | [written-part anchor](latin-anchor-duplication.md) | 25 | 44 replaced |
| 5 | [sigmatic suffix](latin-sigmatic-suffix.md) | 6 | 10 replaced |
| 6 | [residual attachments](latin-residual-attachments.md) | 24 | 32 replaced (3 presents reclassed) |
| 7 | [joined itype fields](latin-residual-attachments.md#joined-itype-fields) | 3 | 4 replaced |
| 8 | [abbreviated prefix alternates](latin-prefix-alternates.md) | 366 | 583 added |
| 9 | [backlinked presents, reference proof](latin-backlinked-present-classes.md) | 19 | 19 added |
| 10 | backlinked presents, quotation proof | 10 | 11 added |
| 11 | [`-jicio` duplicate components](lexical-exports.md#duplicate-components-proved-by-complete-third-conjugation-alternates) | 0 | none |

The four attachment repairs come before the prefix alternates so that the
copied perfects and supines are the repaired ones; the joined-itype stage
runs the three attachment recipes once more on the headers whose itype
fields `combitype` joins. Every stage's input and output SHA-256 is
recorded; the chain is pinned in the qualification tool and the private
eleven-stage source has SHA-256
`ec3fc3d4b154db5ad0b9df0d7f337716f7ceb7e94eea760857800fc5c74ed46e`
(nine-stage: `d02f4bdb4a3a10c56ae25779cb5c4dd65d8f027d359d4d040daec05ce88944f0`).

Against the original candidate the eleven-stage combination adds **734**
records (181 `are_vb`, 12 deponent `are_vb`, 3 `conj1`, 42 `conj2`, 134
`conj3`, 16 `conj3_io`, 12 `conj4`, 7 `ire_vb`, 182 `perfstem`, 145 `pp4`)
and removes **140** (13 attribution stems, 13 leaked-tag stems, 8 reclassed
`conj1` presents, 3 reclassed `conj3` presents, 61 replaced perfects and 42
replaced supines; the nine-stage one added 698 and removed 104). The 734
added records receive **4,404 cells on 4,177 forms**: 132 are covered before
the combination and all 4,404 after. On those forms the sixteen-field
comparison retains 6,751 readings, adds 7,085 and removes 95 (the
third-conjugation futures of the reclassed presents, now second-conjugation
presents); 887 forms become recognized and none is lost. Against the
controlled rebuilt baseline, 823 of the additions are exact historical
readings (739 before). The identical-root control changes nothing.

## Full LISTALL diagnostics of the combinations

Against the original candidate:

| Metric | Original candidate | Nine-stage combination | Eleven-stage combination |
| --- | ---: | ---: | ---: |
| Recognized literal forms | 847,750 | 853,521 | 853,570 |
| Native analysis rows | 2,100,530 | 2,149,411 | 2,149,567 |
| Lost recognized forms | — | 3 (defective readings only) | 75 (defective readings only) |
| Removed eleven-field readings | — | 165 | 1,638 |
| Added eleven-field readings | — | 49,046 | 50,675 |
| Changed grammatical multisets | — | 29,662 | 31,231 |
| Equal-count multiset changes | — | 0 | 282 |

The forms no longer recognized pass the qualification's check: every former
reading of each came from a repaired block's defective record. On the
nine-stage combination they are the three of the
[sigmatic qualification](latin-sigmatic-suffix.md). On the eleven-stage one
they are 75 forms with 107 former readings (78 direct, 29 through native
preverb composition; 14 present readings of the reclassed stems, the rest
perfect-system readings of withdrawn stems) under 8 lemmas: the
[residual attachment trial](latin-residual-attachments.md) alone lost 123,
and the chain recovers 48 of them, among which the perfect system of
*dirimo* that the joined-itype stage repairs. The 1,638 removed readings lie
on 950 forms that stay recognized: 16 are enclitic retries displaced by a
new direct analysis (reproduced on the input without its `-dum`), 1,275 are
readings of withdrawn defective stems on forms whose remaining readings
carry native preverbs (the short vowel-anchored stems composed with the
whole preverb table), and 347 are readings of withdrawn or reclassed stems
beside other direct readings.

Against the controlled rebuilt baseline:

| Controlled baseline → | Original candidate | Six-stage | Nine-stage | Eleven-stage |
| --- | ---: | ---: | ---: | ---: |
| Readings retained | 2,006,554 | 2,010,262 | 2,010,719 | 2,010,809 |
| Readings removed | 41,774 | 38,066 | 37,609 | 37,519 |
| Readings added | 93,976 | 134,983 | 138,692 | 138,758 |
| Forms recognized by both | 831,201 | 832,224 | 832,493 | 832,577 |
| Forms completely lost | 6,789 | 5,766 | 5,497 | 5,413 |
| Lemmas with completely lost forms | 133 | 114 | 109 | 109 |

The eleven-stage combination stops removing **4,255** historical readings
(4,165 at nine stages) and **1,376** completely lost forms are recognized
again (1,292), under 24 fewer lemmas. The lemma-identity review of the
37,519 readings still removed matches 24,168 of the 29,072 on recognized
forms at ten fields under another lemma (16,666 against a reading the
baseline already carried, 7,502 against an added one; 126 of 418 lemmas
fully matched, 79 in part); 4,904 readings on recognized forms and 8,447 on
completely lost forms remain unmatched.

## Six-stage combination (qualified on `6d0f766` and `b925a88`)

The six-stage chain is the one above without stages 4 to 7 (the two
attachment repairs, the residual families and the joined fields), applied in
the same order. Its fourth stage, the prefix alternates (stage 8 above), adds
two records more than
its separate trial because two attribution blocks hold a regular `are_vb`
derivative and a written perfect that the prefix spelling copies; the
quotation proof adds four records fewer because the reference proof already
staged them; the `-jicio` proof finds nothing because the `-io` block kept
outside the attribution replay still carries its attribution stem.

## Native qualification of the six-stage combination

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

## Full LISTALL diagnostics of the six-stage combination

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

## Lemma identity among the readings still removed (six-stage combination)

The eleven-field comparison counts a reading as removed when any field
differs, the lemma included. The [witness backlog screen](latin-witness-backlog-screen.md)
found that the curated witness kept voice variants, alternate spellings and
homograph numberings as lemmas of their own where the dictionary has one
article: a candidate that recognizes the same form with the same grammar
under the article still shows a removed reading under the witness's lemma,
whether the article's reading is new or was already in the baseline beside
the witness's.

`tools/review-latin-removed-lemma-identity.py` re-reads the private
per-form difference file of the baseline comparison and, for each removed
reading on a form the candidate still recognizes, asks the candidate for the
form's readings: a reading agrees at **ten fields** when only the lemma
differs (the workword compared without vowel-length notation, which belongs
to the stem spelling) and at **nine fields** when the voice differs as
well. The relation between the two lemma spellings is classified by shape
only — homograph numbering, active lemma matched by its deponent or the
reverse, native preverb composition (exact or with one assimilated letter),
single-letter spelling, other — and the closest relation is kept when
several readings agree. Readings on the completely lost forms agree with
nothing by definition and are counted apart. The qualification tool runs
the review on the original and on the combined candidate; the receipt
publishes counts, relation categories, voice pairs and the SHA-256 of the
private pair file.

On LISTALL, of the **38,066** readings the combined candidate still removes
against the controlled baseline, 9,033 lie on the 5,766 completely lost forms
and 29,033 on forms the candidate recognizes. Of those 29,033, **24,170**
(83 %) agree at ten fields with a reading the candidate carries under another
lemma; 4,863 agree with nothing. No reading needs the nine-field tier: the
engine reports the passive of an active lemma and the deponent of its article
with the same voice value. By relation of the two spellings:

| Relation of the witness's lemma to the candidate's | Readings |
| --- | ---: |
| Active lemma matched by its deponent article | 5,911 |
| Deponent lemma matched by its active article | 4,132 |
| Homograph numbering | 5,386 |
| Native preverb composition, exact (`de-coquo` ↔ `decoquo`) | 2,143 |
| Native preverb composition, one assimilated letter (`con-manduco` ↔ `commanduco`) | 3,009 |
| Single-letter spelling | 2,019 |
| Other | 1,570 |

For 16,768 of the matched readings the article's reading was already in the
baseline beside the witness's (the witness had labelled the same grammar
twice); 7,402 agree with a reading the candidate adds. The 38,066 removed
readings fall under 404 lemmas: 123 are matched completely, 74 in part, 207
not at all. On the original candidate the same review matches 25,406 of
41,774 removed readings; the combination moved 1,236 of them into exact
retained readings and reduced the unmatched readings from 5,363 to 4,863.

The 10,043 voice-variant readings are therefore not losses of grammar but of
a lemma label the witness duplicated; the homograph and composition
categories are the lemma-numbering and preverb-identifier questions already
open. What remains without any lemma match is 4,863 readings on recognized
forms and the 9,033 readings on completely lost forms.

## Remaining arbitration

The combination is a measured candidate, not a selector or a production
source. Composed identities from native preverbs, the residual complete
alternates without proof, the remaining loss dossiers and the other open
questions of the separate trials are unchanged. Whether a reading matched
under the article's lemma counts as lost is a lemma-identity policy the
review measures and does not decide. The PR remains a draft.
