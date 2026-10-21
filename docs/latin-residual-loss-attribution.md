<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Attribution of the residual Latin losses to the open decisions

Not yet run on LISTALL: the `Latin residual loss attribution` workflow is
dispatched by hand (one LISTALL pass, about 25 minutes) and this page will
carry its receipt.

After the [combined candidate](latin-combined-candidate.md) and its
lemma-identity review, two residues remain against the controlled rebuilt
baseline: the 9,033 readings on the 5,766 forms the candidate no longer
recognizes at all, and the 4,863 removed readings on recognized forms that
agree with no candidate reading at ten or nine fields. The
[witness backlog screen](latin-witness-backlog-screen.md) classified the
curated verbal lemmas without definitions but did not say which of them carry
the lost forms. The remaining questions are decisions rather than recipes;
this diagnostic sizes each of them.

`tools/attribute-latin-residual-losses.py` rebuilds the combined candidate,
compares the controlled baseline with it on LISTALL once (the receipt must
reproduce 38,066 removed readings and 5,766 completely lost forms), then
attributes every residual reading by the category of its lemma:

| Category | Decision it belongs to |
| --- | --- |
| `native_preverb_identifier` | composed identities from native preverbs |
| `curated_lemma_with_candidate_definition` | the changed-definition dossiers |
| `curated_lemma_without_definition:unjoined:*` | lemma identity (voice variant, alternate spelling, homograph numbering) or admission of a curated lemma without source support |
| `curated_lemma_without_definition:joined:*` | a grammar string the historical filter does not read (vowel-initial principal parts, several fields, no field, other) |
| `candidate_lemma_outside_curated_witness` | a lemma the source projects but the witness never had |
| `lemma_outside_curated_witness_and_candidate`, `non_verbal_reading:*` | outside the verbal arbitration |

For the unmatched readings on recognized forms it adds the smallest set of
fields on which the reading differs from a candidate reading of the same form
(the workword compared without vowel-length notation), both exactly and in
coarse sizes: one grammatical field, two or three, four or more, each with or
without the lemma. A reading lost to a tense or a mood under its own lemma is
a paradigm question; a reading whose nearest candidate reading differs in
four fields and the lemma has no counterpart at all.

The witness supplies lemma membership only; no stem of it labels anything.
Only categories, counts and SHA-256 values are published; the per-form
difference file stays private. No candidate is changed and the PR remains a
draft.
