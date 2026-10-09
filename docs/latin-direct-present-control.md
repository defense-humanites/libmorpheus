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
then appends only `not_in_comp` to its unique explicit `:vs:`/`conj1` directive.
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
