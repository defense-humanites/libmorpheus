<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Source review of present-trial native preverb additions

The source-digit present trial qualified on `1174ee2` adds 246 grammatical
readings over LISTALL without removing an existing reading. Half are direct
under its one source lemma; half have a native preverb under other lemmas.
The latter 123 readings need their own source evidence, not an assumption
that the base verb's conjugation validates every prefixed lexical entry.

`tools/review-latin-source-present-preverbs.py` binds the private extended
route dossier, global eleven-field delta, thirteen-cell source-family dossier,
recovered headers and original final expanded candidate to their qualified
SHA-256 receipts. It reproduces the route projection into the grammatical
delta and checks the exact scope (188 changed forms, 246 additions, 123
native-preverb additions). Only those other-lemma additions enter the review.
The input routes remain a changed-form diagnostic, not a global sixteen-field
comparison.

Each literal added lemma is joined through the existing projected-key and
emitted-headword source index. Homograph numbers are never dropped for lemma
identity. All joined articles are kept; absent or ambiguous joins are not
silently resolved. Projection-error articles excluded by that index remain
outside this join's scope, so an absent join is not proof of source absence.

The private dossier records the complete article and its hash, original
header evidence, grammar profile, historical full-header replay, existing
candidate definitions and every added decomposition with multiplicity.
A present-family expectation is derived only from a full source headword
and explicit, nonconflicting source conjugation digits supported by the
existing morphology helper. It is not inherited from the base verb or native
stem class. Only present indicative, subjunctive and infinitive cells under
a unique literally identical source article contribute to the corresponding
aggregate; all other readings remain outside that bounded expectation.

The review does not check all lexical senses, quantities, transitivity,
usage restrictions, imperative/passive extensions or every imperfect/future
cell. A matching present cell is evidence, not approval of a whole lemma,
paradigm or native preverb route. Historical replay is also diagnostic only.
No source entry, runtime candidate, index or production data is changed.

Eight synthetic unit tests cover exact scope and projections, drift and
duplicate rejection, route boundaries, typed signatures, source morphology,
literal homographs, ambiguous/absent joins and receipt failures. CI collects
the actual source evidence privately from the pinned Perseus checkout;
only numeric aggregates, categorical groups and hashes are printed. No
private dossier, TEI article, form, lemma or stem is uploaded or published.
