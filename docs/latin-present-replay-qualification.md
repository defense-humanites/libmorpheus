<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Replaying the last present trials with controlled nominals

The previous full-compound runtime included five privately reviewed nominal
decisions in addition to the committed correction manifest. Those individual
decisions and the corresponding research runtime are unavailable in the new
working environment. The public pipeline therefore cannot reproduce that
exact nominal candidate. Its recorded aggregate results remain historical
measurements, not automatically reproducible current totals.

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

The full runner measurements will be recorded after the first replay finishes.
These measurements form a separate series from the earlier reconstructed
nominal candidate. The five private nominal decisions, sixteen remaining
complete-alternate dossiers, wider lexical loss arbitration and production
corpus qualification remain open.
