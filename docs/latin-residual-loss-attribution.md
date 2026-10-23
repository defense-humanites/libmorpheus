<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Attribution of the residual Latin losses to the open decisions

Qualified code: `e9df2e1`, on the **nine-stage
[combined candidate](latin-combined-candidate.md)** (private source
`d02f4bdb…`). The
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39941354101)
rebuilds the combination and compares the controlled baseline with it on
LISTALL once; the
[aggregate receipt](qualification/latin-residual-loss-attribution-e9df2e1.json)
records categories, counts and SHA-256 values only. The earlier receipt
[`347a058`](qualification/latin-residual-loss-attribution-347a058.json)
measured the six-stage combination (`f719a4e1…`) with the same method; its
figures are kept below for comparison. (A run on `b5e2e60` between the two
also succeeded but its receipt is not archived: the tool then consulted
`vbs.cmp.ml` before the witness, and the losses of the 113 curated or
candidate lemmas whose names the engine also reports for a native
composition — *abdo* for `ab-do`, *abicio* for `ab-jicio` — were labelled
compositions.)

After the combined candidate and its lemma-identity review, two residues
remain against the controlled rebuilt baseline: the 8,571 readings on the
5,497 forms the candidate no longer recognizes at all, and the 4,800 removed
readings on recognized forms that agree with no candidate reading at ten or
nine fields. The
[witness backlog screen](latin-witness-backlog-screen.md) classified the
curated verbal lemmas without definitions but did not say which of them carry
the lost forms. The remaining questions are decisions rather than recipes;
this diagnostic sizes each of them.

## Method

`tools/attribute-latin-residual-losses.py` rebuilds the combined candidate,
runs the baseline comparison (the receipt reproduces 37,609 removed readings
and 5,497 completely lost forms, as the combined-candidate receipt pinned
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

## Completely lost forms: 5,497 forms, 8,571 readings

| Lemma category | Forms | Readings | Lemmas | Forms on `347a058` |
| --- | ---: | ---: | ---: | ---: |
| Changed-definition dossiers (curated lemma with a candidate definition) | 2,347 | 3,727 | 42 | 2,567 |
| Native preverb identifiers, hyphenated | 1,123 | 1,754 | 30 | 1,172 |
| Native preverb identifiers, mapped by `vbs.cmp.ml` | 416 | 543 | 7 | 416 |
| Curated lemma without definition: vowel-initial principal parts | 591 | 928 | 7 | 591 |
| Curated lemma without definition: deponent article for an active lemma | 403 | 483 | 9 | 403 |
| Curated lemma without definition: no inflection field | 288 | 439 | 4 | 288 |
| Curated lemma without definition: other grammar string | 247 | 349 | 3 | 247 |
| Curated lemma without definition: several inflection fields | 170 | 253 | 2 | 170 |
| Curated lemma without definition: no projected header | 31 | 66 | 3 | 31 |
| Curated lemma without definition: bare infinitive | 29 | 29 | 2 | 29 |

A form carrying readings of two categories is counted under both. The two
attachment repairs of the nine-stage combination recover **269** completely
lost forms, all of them in the two categories the repaired blocks can reach:
220 in the changed-definition dossiers (four fewer lemmas) and 49 under
hyphenated native preverbs composed on the repaired stems. Every other
category is unchanged to the form. The changed-definition dossiers now hold
**43 %** of the lost forms, the native preverb identifiers **28 %**, the
curated lemmas without definition **32 %** (1,759 forms under 30 lemmas), of
which the eight vowel-initial grammar strings alone 591 forms. No lost form
belongs to an active article for a deponent lemma, an alternate spelling or
a homograph numbering: those lemmas' forms are all recognized under the
article, as the lemma-identity review found.

## Unmatched readings on recognized forms: 4,800 readings

By lemma category:

| Lemma category | Readings | Lemmas | Readings on `347a058` |
| --- | ---: | ---: | ---: |
| Changed-definition dossiers | 2,338 | 68 | 2,380 |
| Native preverb identifiers, hyphenated | 1,595 | 120 | 1,616 |
| Native preverb identifiers, mapped by `vbs.cmp.ml` | 129 | 13 | 134 |
| Curated lemma without definition (seven sub-categories) | 665 | 27 | 665 |
| Outside the witness, the candidate and the composition map † | 73 | 26 | 68 |

By difference from the nearest candidate reading of the same form:

| Difference | Readings | On `347a058` |
| --- | ---: | ---: |
| Identical reading still returned, at lower multiplicity | 2,128 | 2,128 |
| One grammatical field | 221 | 221 |
| One grammatical field and the lemma | 518 | 518 |
| Two or three grammatical fields | 338 | 344 |
| Two or three grammatical fields and the lemma | 290 | 291 |
| Four or more grammatical fields | 208 | 160 |
| Four or more grammatical fields and the lemma | 1,097 | 1,201 |

**2,128 readings (44 %) are duplicates**: the candidate still returns the
identical eleven-field reading, once fewer, because the witness block
produced the same reading from two stems. 1,414 of them lie in the
changed-definition dossiers, 317 under native preverb identifiers, 291 under
the vowel-initial grammar strings; they lose no information. The
single-field differences are dominated by the mood (`lemma+mood`, 390
readings, 326 of them under native preverb identifiers; `mood` alone, 179)
and by the workword alone (181 readings: a different segmentation of the
same form). The 1,305 readings four or more fields away have no comparable
candidate reading; the nine-stage combination removes 63 unmatched readings
in all (42 in the dossiers, 21 under hyphenated preverbs), most of them from
this row, and moves 48 of the remainder from the lemma-bearing row to the
grammatical-only one.

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
  repairs reach: 220 of their lost forms came back with the nine-stage
  combination.
- The native preverb identifiers are the second residue (1,539 lost forms,
  1,724 unmatched readings): composed identities, a question of policy on
  what the engine may compose, unchanged since the earlier diagnostic except
  for the 49 lost forms composed on repaired stems.
- Among the curated lemmas without definition, the vowel-initial grammar
  strings weigh most (591 lost forms, 413 unmatched readings under 7
  lemmas); the voice variants kept as active lemmas weigh 403 lost forms,
  all of them active forms of a deponent article. No recipe so far touches
  them: these figures are identical on the two combinations.
- Nothing here changes a candidate; the PR remains a draft.
