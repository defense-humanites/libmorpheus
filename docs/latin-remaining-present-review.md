<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Reproducible strict-selector dossiers for complete present alternates

The earlier private inventory contains sixteen remaining alternates in
sixteen articles after the boundary and internal-vowel trials. Its individual
records were not preserved in the public repository. The aggregate count and
old fingerprint alone cannot supply the articles for the next lexical review.

`tools/audit-latin-remaining-presents.py` rebuilds a new, versioned diagnostic
inventory from the pinned Lewis and Short source, validated recovered headers
and the current internal-vowel candidate. It uses the same explicit
class-three grammar and active-voice selector as the last two trials, and the
existing present-only transform's source/block uniqueness, matched unflagged
canonical present and conjugation-subclass checks. Already present alternate
records and notation-only differences are excluded.

An unrestricted in-memory proposal identifies the unhandled records. That
proposal is never written as a stem source, built into an index or analyzed as
a candidate corpus. Its sole purpose is to identify outstanding review leads;
even an orthography marked `extent="full"` can be an abbreviated contextual
ending. No spelling shape supplies linguistic approval.

Each private JSONL dossier binds the alternate to its source article ID,
headword, candidate lemma, projected grammatical fields, proposed present and
conjugation. It includes the full serialized article, its SHA-256 and its
explicit Latin quotations so that a subsequent reviewer can inspect the
original context. Homograph numbers, quantities and delimiters are retained.
The input candidate is read-only. No perfect or fourth part is reconstructed.

The public report contains only aggregate counts and hashes. Spelling-shape
counts distinguish a single substitution, insertion, deletion and more than
one changed letter. A separate mechanical count asks whether an alternate
retains the headword's first explicitly delimited segment. Such a segment is
not necessarily a philologically verified compound prefix. Quotation counts
only indicate whether a Latin quote exists; they do not assert that it attests
the proposed spelling or any of its generated forms.

## Difference from the historical sixteen-record inventory

The first source run on `21cca20` found **15** strict-selector variants,
failing the initial expectation of sixteen before writing a private dossier.
This is a newly observed diagnostic scope, not a correction to the historical
sixteen-record review pool. The old per-entry records are unavailable here,
so neither subset identity nor the reason for the difference is established.
Grammar, voice, canonical-record matching and other inventory choices must
be compared against the old dossiers before attributing the missing record.

The source run on `f9338dc` passed for both quantity treatments: fifteen
variants in fifteen articles, with identical serialized dossiers and aggregate
counts. The private inventory SHA-256 is
`66b6c1c1d3b22619a8077c788cabeda889230d4f288e27d5fdcb80eeb1b72f3d`.
All three workflows passed; the five complete LISTALL reports and private
difference hashes reproduce `37f979e` exactly.

This new schema includes article text and cannot reproduce the older
inventory's serialized hash. Even equal cardinalities would not establish
identity with every old private record.

Nine synthetic tests cover several alternates in one article, homographs,
source quantities, existing records, voice and conjugation compatibility,
abbreviations, ambiguous or flagged blocks, missing source identities,
source changes, unchanged candidate bytes, no overwrite, expected counts,
coordinated-supine diagnostic grammar and private output permissions.
Dossiers remain in private runner temporary
directories and are not uploaded. Only their counts and fingerprint are
published after the source run completes.

## Exact standalone source and the extra diagnostic article

The source access constraint is resolved with an exact local copy. Its SHA-256
is `ccbd2f79db1006edc607fe51227babab6872fbdaa4e925f4c1999a3b978041ee`,
and its Git blob ID is `a67c25871afc486ea91c44ebdb5cb2e25b718247`.
The projection and Latin article reader now accept this file directly as
`--lexica`, validating the pinned SHA-256 before reading. A standalone file
supports Latin only and must retain the selected edition's filename. Git
checkout validation remains the existing path. Five additional synthetic
checks reject modified bytes, a wrong filename, unsupported language selection
and duplicate article IDs, and preserve unresolved entities in the article
reader. CI compares the standalone and checkout projections byte for byte.

The offline projection and recovered headers reproduce the CI hashes, as do
both private fifteen-entry inventories. The current raw historical-filter
outputs on macOS differ from Linux; their whole-runtime measures must not be
substituted for the runner series.

The missing diagnostic article has a grammar field containing **two explicit
supines joined by `and`**. The strict selector accepts neither that syntax nor
its full alternate. The new `--grammar coordinated-supines` diagnostic mode
admits only the exact alphabetic perfect/two-supine/class-three syntax,
alongside the strict selector, with the same active-voice and canonical-record
checks. It restores **one** additional dossier: sixteen variants in sixteen
articles, a strict superset of the unchanged fifteen-record inventory.
Its private SHA-256 is
`f2d4517cbef3a014758ebbc6b50394126bbe96a5da2aa86c508efd2c988697a0`.
CI checks that precise subset difference for both quantity treatments.
This explains the observed selector cardinality difference. It still does
not prove identity with the older, differently serialized private inventory.
No additional stem record is authorized by the diagnostic mode.

## Individual source review

A private sixteen-dossier review records these outcomes:

| Outcome | Variants |
| --- | ---: |
| Same-article full spelling confirmed by a unique standalone reverse reference | 9 |
| Complete spelling in the source header, needing a separate recovery criterion | 5 |
| Contextual abbreviated component, withheld from literal insertion | 1 |
| Coordinated-supine grammar and a passive-present quotation, needing a separate criterion | 1 |

The private decision ledger has SHA-256
`3c007771de47fe140cdcfb3de75f17ce0cba7477f4e43aa741fcdab9e3bf2882`.
The source's `extent="full"` is insufficient by itself: one alternate is
actually an abbreviated component of a compound. Inserting it literally
under the compound lemma would assign an independent base paradigm there.
The other five spellings are explicitly supplied in their own headers, but
that finding does not supply a general edit-distance rule or authorize
perfect and participial systems. The coordinated grammar case's quotation
attests its present spelling; it does not resolve handling both supines.
A separate [quoted-present trial](latin-coordinated-present-qualification.md)
requires that quotation as a native third-singular passive-present witness,
with a bounded full-spelling selector and no supine reconstruction. Its source
count and native results remain to be verified on the pinned source.

The nine reverse-reference cases form a separate
[present-only trial](latin-backlinked-present-qualification.md). It leaves
six strict-selector dossiers (five pending spellings and one withheld
abbreviation), plus the coordinated-grammar dossier outside that selector.
The six-dossier private SHA-256 is
`bca781f7c5292333e4df155022f4816f55f0771b8669fe52ddb35a2e42d058d6`.
The production corpus remains unchanged.
