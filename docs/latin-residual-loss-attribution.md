<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Attribution of the residual Latin losses to the open decisions

Qualified code: `347a058f423132a51f3d1a6411c2bf0e528587be`. The
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39640335629)
rebuilds the combined candidate and compares the controlled baseline with it
on LISTALL once; the
[aggregate receipt](qualification/latin-residual-loss-attribution-347a058.json)
records categories, counts and SHA-256 values only. Two labels of that
receipt were refined in the tool afterwards without changing a count; the
mapping is given below. The receipt measures the six-stage combination
(`f719a4e1…`); the tool pins the qualified baseline comparison of each
combination by its hash and refuses a combination it does not know, so the
nine-stage combination needs its own run once qualified.

After the [combined candidate](latin-combined-candidate.md) and its
lemma-identity review, two residues remain against the controlled rebuilt
baseline: the 9,033 readings on the 5,766 forms the candidate no longer
recognizes at all, and the 4,863 removed readings on recognized forms that
agree with no candidate reading at ten or nine fields. The
[witness backlog screen](latin-witness-backlog-screen.md) classified the
curated verbal lemmas without definitions but did not say which of them carry
the lost forms. The remaining questions are decisions rather than recipes;
this diagnostic sizes each of them.

## Method

`tools/attribute-latin-residual-losses.py` rebuilds the combined candidate,
runs the baseline comparison (the receipt reproduces 38,066 removed readings
and 5,766 completely lost forms), then attributes every residual reading by
the category of its lemma:

| Category | Decision it belongs to |
| --- | --- |
| `native_preverb_identifier` (hyphenated, or a lemma name `vbs.cmp.ml` maps to a composition) | composed identities from native preverbs |
| `curated_lemma_with_candidate_definition` | the changed-definition dossiers |
| `curated_lemma_without_definition:unjoined:*` | lemma identity (voice variant, alternate spelling, homograph numbering) or admission of a curated lemma without source support |
| `curated_lemma_without_definition:joined:*` | a grammar string the historical filter does not read (vowel-initial principal parts, several fields, no field, other) |
| `candidate_lemma_outside_curated_witness` | a lemma the source projects but the witness never had |
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

## Completely lost forms: 5,766 forms, 9,033 readings

| Lemma category | Forms | Readings | Lemmas |
| --- | ---: | ---: | ---: |
| Changed-definition dossiers (curated lemma with a candidate definition) | 2,567 | 4,100 | 46 |
| Native preverb identifiers, hyphenated | 1,172 | 1,843 | 31 |
| Native preverb identifiers, mapped by `vbs.cmp.ml` † | 416 | 543 | 7 |
| Curated lemma without definition: vowel-initial principal parts | 591 | 928 | 7 |
| Curated lemma without definition: deponent article for an active lemma | 403 | 483 | 9 |
| Curated lemma without definition: no inflection field | 288 | 439 | 4 |
| Curated lemma without definition: other grammar string | 247 | 349 | 3 |
| Curated lemma without definition: several inflection fields | 170 | 253 | 2 |
| Curated lemma without definition: no projected header | 31 | 66 | 3 |
| Curated lemma without definition: bare infinitive | 29 | 29 | 2 |

A form carrying readings of two categories is counted under both. The
changed-definition dossiers hold **45 %** of the lost forms, the native
preverb identifiers **28 %**, the curated lemmas without definition **30 %**
(1,759 forms under 30 lemmas), of which the eight vowel-initial grammar
strings alone 591 forms. No lost form belongs to an active article for a
deponent lemma, an alternate spelling or a homograph numbering: those lemmas'
forms are all recognized under the article, as the lemma-identity review
found.

## Unmatched readings on recognized forms: 4,863 readings

By lemma category:

| Lemma category | Readings | Lemmas |
| --- | ---: | ---: |
| Changed-definition dossiers | 2,380 | 69 |
| Native preverb identifiers, hyphenated | 1,616 | 120 |
| Native preverb identifiers, mapped by `vbs.cmp.ml` † | 134 | 15 |
| Curated lemma without definition (seven sub-categories) | 665 | 27 |
| Non-verbal readings of the above (participles and nouns of verbal blocks) ‡ | 68 | 24 |

By difference from the nearest candidate reading of the same form:

| Difference | Readings |
| --- | ---: |
| Identical reading still returned, at lower multiplicity | 2,128 |
| One grammatical field | 221 |
| One grammatical field and the lemma | 518 |
| Two or three grammatical fields | 344 |
| Two or three grammatical fields and the lemma | 291 |
| Four or more grammatical fields | 160 |
| Four or more grammatical fields and the lemma | 1,201 |

**2,128 readings (44 %) are duplicates**: the candidate still returns the
identical eleven-field reading, once fewer, because the witness block
produced the same reading from two stems. 1,414 of them lie in the
changed-definition dossiers, 317 under native preverb identifiers; they lose
no information. The single-field differences are dominated by the mood
(`lemma+mood`, 390 readings, 326 of them under native preverb identifiers;
`mood` alone, 179) and by the workword alone (181 readings: a different
segmentation of the same form). The 1,361 readings four or more fields away have no comparable
candidate reading.

† In receipt `347a058` these rows are labelled
`lemma_outside_curated_witness_and_candidate`: on a local probe of 52,761
forms covering every block of the four verbal inputs, every verbal reading
whose lemma is outside those inputs carries a lemma name that `vbs.cmp.ml`
maps to a native composition, so the tool now reads that file and labels them
`native_preverb_identifier:mapped_composition`.
‡ Labelled `non_verbal_reading:pos_*` in the receipt; the tool now attributes
every reading by lemma and counts parts of speech apart.
`no_candidate_reading` in the receipt is the row labelled
`identical_reading_at_lower_multiplicity` above: on a recognized form the
candidate always has readings, and the only way to differ in no field is to
be a copy at lower multiplicity.

## What the sizes say

- The changed-definition dossiers (59 lemmas) remain the largest residue on
  both sides, but a third of their unmatched readings are duplicates and the
  rest are mostly readings four or more fields away from anything the
  candidate returns: these are the records the source review already
  withheld, not new defects.
- The native preverb identifiers are the second residue (1,588 lost forms,
  1,750 unmatched readings): composed identities, a question of policy on
  what the engine may compose, unchanged since the earlier diagnostic.
- Among the curated lemmas without definition, the vowel-initial grammar
  strings weigh most (591 lost forms, 413 unmatched readings under 7
  lemmas); the voice variants kept as active lemmas weigh 403 lost forms,
  all of them active forms of a deponent article.
- Nothing here changes a candidate; the PR remains a draft.
