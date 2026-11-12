<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Replaying the last present trials with controlled nominals

The previous full-compound runtime included five privately reviewed nominal
decisions in addition to the committed correction manifest. Those individual
decisions are not represented in the public inputs. The exact nominal
research candidate therefore cannot be recreated from the committed inputs
and recorded aggregates alone. Its recorded results remain historical
measurements, separate from the reproducible controlled-nominal series below.

`tools/qualify-latin-present-stages.py` supplies a distinct, reproducible
comparison: all nominal inputs and indexes come from the controlled rebuilt
Latin witness, using the committed manifest and corrections. Only the verbal
dictionary source changes between the future/imperative quotation trial,
the eleven boundary-present insertions and the four internal-vowel insertions.
The insertion checks require unchanged preceding bytes, source lemma blocks,
exact expected counts and present-only `conj3`/`conj3_io orth` records.

Each research copy assembles all four verbal inputs in manifest order,
including the generated irregular verbs, and applies the production recipe's
Latin perfect-stem transformation before `do_conj` and `indexvbs`. Production
receipts are removed from these modified private copies. Nominal index hashes
must remain equal to the controlled witness. Both quantity treatments of the
last trial must produce identical nominal and verbal index hashes.

The lexical research workflow now runs five complete literal LISTALL passes:
two identical-root controls, each consecutive present-trial comparison, and
the controlled baseline against the internal-vowel trial. API errors and an
unexpected distinct-form count fail the replay. Each consecutive comparison
then reanalyzes every form with a changed count and checks the full counts
against that reanalysis. Multisets preserve duplicate readings and record
retained, added and removed rows for these eleven explicit fields:
`workword`, `lemma`, `part_of_speech`, `person`, `number`, `gender`,
`grammatical_case`, `tense`, `mood`, `voice`, `degree`.

This scope does not cover unchanged-count forms or the other public analysis
attributes. Added eleven-field rows are classified as direct source-lemma
verbs, native-preverb review leads, ambiguous provenance or other review
leads. Mixed direct/preverb provenance is withheld rather than assigned to a
source article automatically. No recognition total qualifies a paradigm or
an unreviewed compound.

The workflow prints only aggregate counts and hashes. All source streams,
indexes, native diagnostics and per-form differences remain in private runner
temporary directories; no lexical artifact is uploaded. Seven synthetic
tests cover multiplicity and grammatical changes, provenance ambiguity,
insertion-only scope, count mismatches, native errors and private boundaries.
Two native integration tests replay the controlled verbal source and a
synthetic fifteen-notice source. Locally, the controlled replay reproduced all
four index hashes and the three-form count smoke; the structured ABI reader
returned the expected verb lemma. The synthetic replay exercised all four
trial builds and all five comparisons, recovered direct source-lemma verb
readings, retained previous eleven-field rows and checked private permissions.
Both integration tests also run after the native build in the research job.

## Complete runner measurements

The first full replay passed on code commit `25b5839` in research run
[`37341356033`](https://github.com/defense-humanites/libmorpheus/actions/runs/37341356033).
All five passes cover **1,033,579** distinct literal forms with ABI 2 and
options zero. Every status pair is `0,0`; both identical-root controls have
zero changed counts. The distinct input SHA-256 is
`1df0800fb1443b2cfd64d787c257319aa72b69f453c3c37ec60c359c70cebd93`.

These totals use the controlled nominal witness throughout:

| Verbal source stage | Recognized forms | Readings |
| --- | ---: | ---: |
| Future/imperative quotations | 847,452 | 2,098,215 |
| Eleven boundary presents | 847,452 | 2,099,009 |
| Four internal-vowel presents | 847,544 | 2,099,321 |

The consecutive comparisons give the following complete-corpus changes.
All changed counts increase; none decreases. The row comparison uses the
eleven fields listed above, on every changed-count form.

| Consecutive trial | Recognition gains | Recognition losses | Increased counts | Retained rows | Added rows | Removed rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Boundary presents | 0 | 0 | 528 | 1,163 | 794 | 0 |
| Internal-vowel presents | 92 | 0 | 206 | 182 | 312 | 0 |

Of the boundary trial's **794** added rows, **780** are direct source-lemma
verb readings and **14** are native-preverb review leads. All **312** added
internal-vowel rows are direct source-lemma verb readings. Neither comparison
has ambiguous-provenance or other review rows. This attribution does not
qualify the 14 compound leads or API attributes outside the eleven-field scope.

The final candidate against the controlled rebuilt baseline gives:

| Recognition cell | Forms |
| --- | ---: |
| Both | 831,201 |
| Baseline only | 6,789 |
| Candidate only | 16,343 |
| Neither | 179,246 |

The baseline recognizes **837,990** forms and returns **2,048,328** readings.
The final candidate increases the net totals by **9,554** forms and **50,993**
readings. There are **60,344** changed counts in this baseline comparison;
it has no eleven-field multiset audit. The **6,789** baseline-only forms still
require arbitration, and the net increase does not qualify a production
replacement. These cells are separate from the older research candidate's
11,467 losses and must not be treated as a resolution of its private dossiers.

Both quantity treatments build identical final indexes. All three trials
retain nominal SHA-256 `106592a19b3b34a343c271fadcc559cdef10363c0d7f4ea024a71ae613e1bd54`
and nominal sidecar SHA-256
`e70bc11f301cbdf9765cb56b30109f0fc53539c19056168c2e09c05503d05210`.
The verbal hashes reproduce the previously recorded verbal trials:

| Stage | Verbal index SHA-256 | Verbal sidecar SHA-256 |
| --- | --- | --- |
| Future/imperative | `ed24bc5d45456fec60fbc0ab9c8ab9a919506e7476295543666defc569226fd1` | `7309e63a8210661f168421cb4e295dbd2d6cb7f220d01e5cb8e65ef8b4635aa0` |
| Boundary | `71f2312a7cea7209e31bf22724140d2d34af6de58ef47645a126bf05896c55da` | `1717ed360358822c49a793c50a99c75e0efab7193301ad1a908b673c97239dcc` |
| Internal vowel | `2814f68fbad7422f4a0989bba5f6b2569cc89410888d0839c959f2f84ea0440c` | `cb19cbd144955a2440a090b6f0747c0c6f654a5ed9bcf7e30e3645c2511ec907` |

Private per-form output hashes are retained for reproducibility. Identical
controls also record absent forms, so their private outputs are not empty.

| Pass | Private output SHA-256 |
| --- | --- |
| Boundary control | `663e3a5fd06bc99d98e8fa0e36b8d34752a22ef6ad25b5c5b8056141d9160640` |
| Internal-vowel control | `fc99203e0decaba03cf7752dc68e20adbfb451099311f4a80aa4d4d7c3ceb2b2` |
| Boundary step | `af3a2325532056725920b60f730df419f6835df238258b946349d6a5f77df85e` |
| Internal-vowel step | `97b64acedf47ff9423200c26aef5c58e53aa124efc67d2e3417132ec6a39bdda` |
| Baseline to final trial | `ee07759b934140ee904ed1379ecca81715de1a65fbedbd09803e6d53c479a61b` |

The seven synthetic replay tests and both native integration tests also
passed in this research job. Linux CI and platform/release qualification are
green on the same code commit (runs `37341365479` and `37341365430`).

The five private nominal decisions, sixteen remaining complete-alternate
dossiers, wider lexical loss arbitration and production corpus qualification
remain open. No private lexical artifact was uploaded.
