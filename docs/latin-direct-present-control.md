<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Direct-present counterfactual with composition disabled

The open source-present trial adds 123 direct readings and 123 native-preverb
readings. The latter use one literal preverb–base identifier; no attestation
has been established by the bounded source search. This control measures
those effects separately. It does not assert that the lexical source requires
composition to be disabled.

`tools/qualify-latin-direct-present-control.py` binds the open trial's source,
verbal indexes, thirteen-cell family and LISTALL to their qualified receipts.
It requires that the selected lemma has no original candidate definition,
then appends only `not_in_comp` to its unique explicit `:vs:` directive with exactly `conj1 are_vb`. The `are_vb` token survives
native expansion of the qualified derivation; it is preserved by the control.
Other bytes and homograph suffixes remain unchanged. The flag is an existing
native input feature, used here solely as a diagnostic intervention.

The tool cleans generated inputs/logs only in a copied template, builds fresh
verbal indexes in another private copy and preserves the nominal indexes.
It compares the open and restricted thirteen-cell families at grammar and
decomposition level and requires each source expectation to remain covered.
Three full LISTALL passes then compare restricted→same restricted,
original candidate→restricted, and open→restricted, including equal-count
multiset changes and guarded per-analysis text truncation. Original candidate
and open-trial index hashes, source receipts and input-form scope are verified
afterward. Only aggregates and hashes are printed; private differences, stems
and logs remain outside the repository and are not uploaded.

Results are measured, not predeclared: the control does not assume exactly
123 removed preverb readings, unchanged recognition or zero original-candidate
loss. Any such conclusion needs the actual global report. The three passes
use eleven-field signatures; only the thirteen family cells receive the
extended decomposition equality check, not the entire input inventory.

Eight unit tests cover exact insertion, line endings, unsupported/duplicate
directives, truncation, family decomposition drift, expected-cell coverage
and receipt failures. One native synthetic integration test confirms unchanged
direct multisets over thirteen present cells and disabled prefixed readings;
it also exercises the complete three-pass control on 26 synthetic forms,
including reconstruction from an already built trial without file collisions.
The control does not promote a candidate, change native policy, add a lexical
restriction, or validate the remaining direct ambiguities or past reconstructions.

The first Linux run on `9f9ba4c` passed all preceding qualifications but
stopped before the three new global passes: its new guard incorrectly expected
only `conj1`. The corrected native synthetic test builds an `are_vb` derivation
and uses its expanded present directive, rather than a manually shortened
fixture. Input receipts remain unchanged; no result is inferred from that failed
run. Unknown tokens, bare `conj1`, and an existing restriction are rejected.

## Measured Linux qualification on `b022abb`

The [completed Latin job](https://github.com/defense-humanites/libmorpheus/actions/runs/37906199108/job/113740138007)
succeeded, as did [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37906207005)
and [platform qualification](https://github.com/defense-humanites/libmorpheus/actions/runs/37906207082).
The [complete aggregate report](qualification/latin-direct-present-b022abb.json)
preserves the measured report and its exact qualifying revision.

All three passes cover **1,033,579** distinct forms, with native options zero,
only status pairs `0,0`, and no changes at equal analysis counts.
The restricted identical-root control retains all **2,100,653** readings and
changes no form. The restricted root recognizes **847,843** forms; **185,736**
remain unrecognized.

| Comparison | Retained readings | Removed | Added | Changed grammatical multisets | Recognition gains | Recognition losses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original candidate → restricted | 2,100,530 | 0 | 123 | 94 | 93 | 0 |
| Open trial → restricted | 2,100,653 | 123 | 0 | 94 | 0 | 0 |

Every addition relative to the original candidate is a direct verbal reading
of the selected source lemma. Every removal relative to the open trial is a
native-preverb reading. Their separate measured tense profiles are:

| API tense | Direct additions vs original | Preverb removals vs open |
| --- | ---: | ---: |
| Unspecified (0) | 33 | 33 |
| Present (1) | 47 | 47 |
| Imperfect (2) | 26 | 26 |
| Future (3) | 17 | 17 |

The **thirteen** source-present cells retain their full grammar/decomposition
multisets and all **thirteen** expected readings. This family result and the
global additions are overlapping measurements and must not be added together.
The global passes compare eleven fields; they do not establish equality of
every native attribute.

Thus the 93 recognition gains persist when composition is disabled, and
removing the 123 preverb readings loses no recognition on this inventory.
The control separates these measured effects. It neither attests the
preverb–base lexical identifier nor establishes that the source lemma should
carry `not_in_comp`. It does not resolve the extra direct readings or the
remaining past-tense/source reconstruction issues.

| Restricted output or private comparison | SHA-256 |
| --- | --- |
| Restricted source | `00dd8391949a2459d2d202ffe76889a7b9b8b6816369a7eb6c9768ef3edbca75` |
| Verbal index | `c27e45299cbdf530f1412b221466bebf1d8e4459a585dd78e69ea73586825ee5` |
| Verbal side index | `d0edf0dc3cf6d8614d1b68912885ea557b872156ac435bea39581cd301b9cf51` |
| Original candidate → restricted private differences | `bd278fc724a8c3d8a84c47a2388d79f2ca01537e6923bff1a079687169583dbd` |
| Open trial → restricted private differences | `f32f57d49d367aa5a23de827e288ace31a660ce7f1c6fff880252505aebe558e` |
| Restricted identical-root private differences | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The source, family, LISTALL and original-candidate receipts match the pinned
inputs in the aggregate report. Both nominal index receipts remain unchanged,
as do every original-candidate and open-trial index and input receipt.
No lexical form, directive or individual analysis is published. No candidate,
native production policy or production corpus is changed.

The complete run on `b4cd55d` (Latin job `113750704211`, workflow
`37909422275`) reproduces this entire aggregate report exactly, including
family counts, all global comparisons, index and private difference receipts.
Its separate diagnostic historical-filter comparison does not substitute
the original candidate or open-trial inputs.

