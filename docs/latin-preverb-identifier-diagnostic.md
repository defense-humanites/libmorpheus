<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Native preverb identifiers and lexical source identities

The source searches qualified on `bb92fbe` found no key, complete orthography
or reference for the one output lemma of 123 added native-preverb readings.
That output must also be examined as a native composition identifier.

In `src/anal/checkgenwds.c`, `AddAnalysis` constructs a key by joining the
native preverb, a hyphen and the stem lemma. It consults `chckcmpvb` and uses
a compound dictionary key when available; otherwise it keeps the constructed
key. `src/gkends/endindex.c` implements that compound-index lookup. Meanwhile,
`Check_preverb` in `src/anal/checkpreverb.c` returns success unconditionally;
the old compound-existence checks are disabled. These are existing native
behaviors. This research does not change them or propose a new API policy.

`tools/diagnose-latin-preverb-identifiers.py` binds the extended route,
source-family and unjoined-lemma dossiers to their qualified hashes. It
reproduces all 123 other-lemma additions within the 188-form/246-addition
scope and checks whether each output lemma literally equals its native
preverb plus a hyphen plus the selected source lemma, preserving homographs.
Other identifiers remain a separate category; no composition is forced.

The diagnostic also counts readings having at least one direct added peer
with the same grammar, literal stem, suffix and ending. This is not a
one-to-one correspondence of forms, a source-attestation proof, a complete
audit of compound-table resolution, or an approval of native prefix
productivity. Source searches of an assembled identifier must not silently
be interpreted as searches of a dictionary headword. Even a wholly composed
identifier inventory leaves the lexical legitimacy of the added prefixed
forms open.

Only numeric aggregates and hashes are printed. Exact identifier strings,
forms and decompositions stay in a 0600 private dossier. Six synthetic tests
cover literal composition, homographs, decomposition peers, scope/removals,
cross-dossier drift and receipt failures. No candidate or production data is
changed.
