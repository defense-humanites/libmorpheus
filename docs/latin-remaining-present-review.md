<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Reproducible dossiers for remaining complete present alternates

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

CI requires sixteen variants and sixteen articles for both quantity
treatments. Their new serialized dossiers and aggregate counts must be
identical. This new schema includes article text and cannot reproduce the
older inventory's serialized hash; matching the old count alone does not
establish identity with every old private record.

Eight synthetic tests cover several alternates in one article, homographs,
source quantities, existing records, voice and conjugation compatibility,
abbreviations, ambiguous or flagged blocks, missing source identities,
source changes, unchanged candidate bytes, no overwrite, expected counts and
private output permissions. Dossiers remain in private runner temporary
directories and are not uploaded. Only their counts and fingerprint are
published after the source run completes.

The next individual arbitration requires the pinned TEI or the generated
private dossiers in a readable working environment. The current local reader
cannot transport the complete source file, and direct network download is
unavailable. This access constraint does not justify a generic recovery rule.
The production corpus and sixteen lexical decisions remain pending.
