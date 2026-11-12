<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Screen of the curated verbal lemmas still without definitions

Qualified code: `545281b6bfec845266d99483723b4a9bb3f7d979`. The
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39154567379)
reproduces the combined candidate and screens both candidates; the
[aggregate receipt](qualification/latin-witness-backlog-screen-545281b.json)
records categories, counts and SHA-256 values only.

The [combined candidate](latin-combined-candidate.md) leaves 5,766 LISTALL
forms completely lost against the controlled rebuilt baseline, under 114
lemmas. The earlier loss diagnostic partitions the 133 original lemmas into
59 with changed definitions, 44 native preverb identifiers and 30 without
any final definition. The combination acted inside existing blocks; this
screen asks what remains mechanically reachable for the lemmas whose block
is empty or absent.

`tools/screen-latin-witness-backlog.py` takes the curated verbal witness
only for lemma membership: it never reads a witness stem, labels nothing
with it and proposes no record. For each curated verbal lemma without a
definition in the candidate it joins the projected source headers and
classifies the join, then, for a unique joined header, the shape of its
grammar string against the literal table of `src/gkdict/latvb.l` (88
strings) and the lexer's generic rule, which accepts only a
consonant-initial string ending in a conjugation digit.

## Results on the original and combined candidates

The two candidates give the same inventory: the combination adds no block,
so the 30 lemmas without a final definition are untouched by it. Of 6,773
curated verbal lemmas, 6,702 have definitions and **71** have none.

| Lemmas without definitions | Count |
| --- | ---: |
| No projected header: article is a deponent of this active lemma | 14 |
| No projected header: article is an active of this deponent lemma | 6 |
| No projected header: spelling is an alternate of an article | 3 |
| No projected header: homograph numbering differs | 4 |
| No projected header: no relation found | 15 |
| Joined header, grammar in the literal table | 0 |
| Joined header, vowel-initial grammar ending in a digit | 8 |
| Joined header, several inflection fields | 4 |
| Joined header, no inflection field | 7 |
| Joined header, bare infinitive outside the table | 2 |
| Joined header, other grammar | 8 |

Forty-two lemmas have no projected header at all. Twenty of them are voice
variants: the curated witness kept an active and a deponent lemma where the
dictionary has one article in the other voice. Three are alternate spellings
the witness promoted to lemmas, four differ only by homograph numbering. These
are lemma-identity policies, not filter defects; the combined candidate may
recognize their forms under the article's lemma, which the eleven-field
comparison still counts as lost.

Twenty-nine lemmas join one header. None carries a grammar string of the
literal table; eight carry a vowel-initial principal-part string that the
generic rule skips (`i^di, i^tum, 3`, `eptus, 3`, `i_tum, 3`, …), each
string unique, and the others have no inflection field, several fields or a
non-paradigm field (`a_tus sum`, `se^cu_tus`, `la_bi`). A recipe for these
would be a per-string grammar rule, not a bounded source reading; they are
the arbitration backlog proper.

## Scope

Only categories and counts are published. The screen does not measure
LISTALL readings, does not identify which of the 71 lemmas carry the 5,766
lost forms, and does not change any candidate. The PR remains a draft.
