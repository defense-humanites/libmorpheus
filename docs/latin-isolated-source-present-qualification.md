<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Source-digit present recovery trial

The native isolation diagnostic identifies one lemma for which two separate
source fields emit the same directive. This qualification selects only the
successful occurrence containing a literal conjugation digit. It preserves
the original multi-field header as evidence and does not simplify that header
for extraction or reconstruct a past part.

`tools/qualify-latin-isolated-source-present.py` revalidates the source header
and every isolation transcript. The selected header must have exactly one
bare conjugation digit, no conflicting terminal class digit in another
`itype`, a full source orthography and the same literal lemma. More than one
supported successful source-digit trial aborts the qualification. The present
family is constructed from the source headword and digit, independently of
the native expansion. No conjugation is inferred from the emitted stem.

The existing qualified present-only copy is bound by its source, index and
private native probe receipts. Its payload must preserve the entire candidate
and append only the unique literal present expansion. The copy must contain
one present class for the selected lemma, no derivative or past class. Its
retained verbal inputs and nominal indexes must match the candidate.

Thirteen source cells (indicative, subjunctive and infinitive) must return
the expected direct lemma and morphology and retain all existing eleven-field
readings. Extended decomposition differences are measured on these cells.
Then a same-root control and a candidate-to-present-copy comparison examine
all 1,033,579 LISTALL forms, including changes at equal reading counts. All
native text fields used in these comparisons are checked for truncation.

For forms with an eleven-field change, the native decomposition is reprobed
and compared with multiplicity. Public additions distinguish the selected
source lemma from other lemmas and direct from native-preverb routes. This
second review is limited to the forms changed in the global grammar audit;
it is not a global sixteen-field equivalence proof. Literal differences and
forms remain in separate exclusive mode-0600 dossiers outside the repository.

The qualification reports additions and removals rather than hiding a failed
trial. Successful targeted coverage alone does not approve a global result
containing losses or source-unjustified additions. The source, indexes and
previous native probe receipts remain unchanged, as do the four final
candidate indexes. No private CI artifact is uploaded, and no production
replacement occurs. Actual results are recorded in PR #18 after completion.
