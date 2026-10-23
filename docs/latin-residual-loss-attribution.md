<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Attribution of the residual Latin losses to the open decisions

Qualified code: `0f0d489`, on the **eleven-stage
[combined candidate](latin-combined-candidate.md)** (private source
`ec3fc3d4…`). The
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39973005734)
rebuilds the combination and compares the controlled baseline with it on
LISTALL once; the
[aggregate receipt](qualification/latin-residual-loss-attribution-0f0d489.json)
records categories, counts and SHA-256 values only. The earlier receipts
[`e9df2e1`](qualification/latin-residual-loss-attribution-e9df2e1.json)
(nine-stage combination, `d02f4bdb…`) and
[`347a058`](qualification/latin-residual-loss-attribution-347a058.json)
(six-stage, `f719a4e1…`) used the same method; their figures are kept below
for comparison. (A run on `b5e2e60` between the first two also succeeded
but its receipt is not archived: the tool then consulted `vbs.cmp.ml`
before the witness, and the losses of the 113 curated or candidate lemmas
whose names the engine also reports for a native composition — *abdo* for
`ab-do`, *abicio* for `ab-jicio` — were labelled compositions.)

After the combined candidate and its lemma-identity review, two residues
remain against the controlled rebuilt baseline: the 8,447 readings on the
5,413 forms the candidate no longer recognizes at all, and the 4,904 removed
readings on recognized forms that agree with no candidate reading at ten or
nine fields. The
[witness backlog screen](latin-witness-backlog-screen.md) classified the
curated verbal lemmas without definitions but did not say which of them carry
the lost forms. The remaining questions are decisions rather than recipes;
this diagnostic sizes each of them.

## Method

`tools/attribute-latin-residual-losses.py` rebuilds the combined candidate,
runs the baseline comparison (the receipt reproduces 37,519 removed readings
and 5,413 completely lost forms, as the combined-candidate receipt pinned
them for this hash), then attributes every residual reading by the category
of its lemma, in this order:

| Category | Decision it belongs to |
| --- | --- |
| `native_preverb_identifier:hyphenated` | composed identities from native preverbs |
| `curated_lemma_with_candidate_definition` | the changed-definition dossiers |
| `curated_lemma_without_definition:unjoined:*` | lemma identity (voice variant, alternate spelling, homograph numbering) or admission of a curated lemma without source support |
| `curated_lemma_without_definition:joined:*` | a grammar string the historical filter does not read (vowel-initial principal parts, several fields, no field, other) |
| `candidate_lemma_outside_curated_witness` | a lemma the source projects but the witness never had |
| `native_preverb_identifier:mapped_composition` (a name no block carries that `vbs.cmp.ml` maps to a composition) | composed identities from native preverbs |
| `lemma_outside_curated_witness_and_candidate` | outside the four verbal inputs of the production rebuild |

For the unmatched readings on recognized forms it adds the smallest set of
fields on which the reading differs from a candidate reading of the same form
(the workword compared without vowel-length notation), both exactly and in
coarse sizes: one grammatical field, two or three, four or more, each with or
without the lemma; a removed reading whose exact copy the candidate still
returns is a duplicate the witness produced twice, counted as
`identical_reading_at_lower_multiplicity`.

The witness supplies lemma membership only; no stem of it labels anything.
Only categories, counts and SHA-256 values are published; the per-form
difference file stays private.

## Completely lost forms: 5,413 forms, 8,447 readings

| Lemma category | Forms | Readings | Lemmas | Forms, nine stages | Forms, six stages |
| --- | ---: | ---: | ---: | ---: | ---: |
| Changed-definition dossiers (curated lemma with a candidate definition) | 2,249 | 3,589 | 39 | 2,347 | 2,567 |
| Native preverb identifiers, hyphenated | 1,137 | 1,768 | 33 | 1,123 | 1,172 |
| Native preverb identifiers, mapped by `vbs.cmp.ml` | 416 | 543 | 7 | 416 | 416 |
| Curated lemma without definition: vowel-initial principal parts | 591 | 928 | 7 | 591 | 591 |
| Curated lemma without definition: deponent article for an active lemma | 403 | 483 | 9 | 403 | 403 |
| Curated lemma without definition: no inflection field | 288 | 439 | 4 | 288 | 288 |
| Curated lemma without definition: other grammar string | 247 | 349 | 3 | 247 | 247 |
| Curated lemma without definition: several inflection fields | 170 | 253 | 2 | 170 | 170 |
| Curated lemma without definition: no projected header | 31 | 66 | 3 | 31 | 31 |
| Curated lemma without definition: bare infinitive | 29 | 29 | 2 | 29 | 29 |

A form carrying readings of two categories is counted under both. The
attachment repairs reach the two categories a repaired block can reach and
no other: from six to nine stages they recovered 220 dossier forms and 49
hyphenated-preverb forms; from nine to eleven they recover 98 more dossier
forms (three fewer lemmas) and lose 14 under hyphenated preverbs — forms the
baseline and the earlier combinations recognized only through a native
composition on a defective stem now withdrawn, the losses the
[combined qualification](latin-combined-candidate.md) counts as defective
readings only. Every other category is unchanged to the form across the
three combinations. The changed-definition dossiers now hold **42 %** of
the lost forms, the native preverb identifiers **29 %**, the curated lemmas
without definition **32 %** (1,759 forms under 30 lemmas), of which the
eight vowel-initial grammar strings alone 591 forms. No lost form belongs to
an active article for a deponent lemma, an alternate spelling or a homograph
numbering: those lemmas' forms are all recognized under the article, as the
lemma-identity review found.

## Unmatched readings on recognized forms: 4,904 readings

By lemma category:

| Lemma category | Readings | Lemmas | Nine stages | Six stages |
| --- | ---: | ---: | ---: | ---: |
| Changed-definition dossiers | 2,327 | 67 | 2,338 | 2,380 |
| Native preverb identifiers, hyphenated | 1,710 | 134 | 1,595 | 1,616 |
| Native preverb identifiers, mapped by `vbs.cmp.ml` | 129 | 13 | 129 | 134 |
| Curated lemma without definition (seven sub-categories) | 665 | 27 | 665 | 665 |
| Outside the witness, the candidate and the composition map † | 73 | 26 | 73 | 68 |

By difference from the nearest candidate reading of the same form:

| Difference | Readings | Nine stages | Six stages |
| --- | ---: | ---: | ---: |
| Identical reading still returned, at lower multiplicity | 2,105 | 2,128 | 2,128 |
| One grammatical field | 210 | 221 | 221 |
| One grammatical field and the lemma | 577 | 518 | 518 |
| Two or three grammatical fields | 332 | 338 | 344 |
| Two or three grammatical fields and the lemma | 314 | 290 | 291 |
| Four or more grammatical fields | 181 | 208 | 160 |
| Four or more grammatical fields and the lemma | 1,185 | 1,097 | 1,201 |

**2,105 readings (43 %) are duplicates**: the candidate still returns the
identical eleven-field reading, once fewer, because the witness block
produced the same reading from two stems. 1,396 of them lie in the
changed-definition dossiers, 312 under native preverb identifiers, 291 under
the vowel-initial grammar strings; they lose no information. The
single-field differences are dominated by the mood (`lemma+mood`, 390
readings, 326 of them under native preverb identifiers; `mood` alone, 179)
and by the workword alone (181 readings: a different segmentation of the
same form). The 1,366 readings four or more fields away have no comparable
candidate reading. The eleven-stage combination adds 104 unmatched readings
in all: 115 more under hyphenated native preverbs (readings the baseline
composed on stems the combination withdraws, now matched by nothing) and 11
fewer in the dossiers.

† 68 of these readings are non-verbal (27 nouns, 40 adjectives, 1 adverb:
participles and nouns of verbal blocks, counted apart by part of speech in
the receipt); 5 verbal readings under 2 lemmas have a lemma name that none of
the four verbal inputs nor `vbs.cmp.ml` carries.

## What the sizes say

- The changed-definition dossiers (59 lemmas) remain the largest residue on
  both sides, but a third of their unmatched readings are duplicates and the
  rest are mostly readings four or more fields away from anything the
  candidate returns: these are the records the source review already
  withheld, not new defects. They are also the only residue the attachment
  repairs reach: 318 of their lost forms came back between the six-stage and
  the eleven-stage combinations.
- The native preverb identifiers are the second residue (1,553 lost forms,
  1,839 unmatched readings): composed identities, a question of policy on
  what the engine may compose. The attachment repairs move this residue both
  ways, recovering compositions on repaired stems and withdrawing those on
  defective ones.
- Among the curated lemmas without definition, the vowel-initial grammar
  strings weigh most (591 lost forms, 413 unmatched readings under 7
  lemmas); the voice variants kept as active lemmas weigh 403 lost forms,
  all of them active forms of a deponent article. No recipe so far touches
  them: these figures are identical on the three combinations.
- Nothing here changes a candidate; the PR remains a draft.
