<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Review of complete losses without final definitions

`tools/review-latin-missing-definitions.py` selects the 30 literal lemmas
with baseline definitions and no final expanded definitions from the qualified
private loss diagnostic. They account for 2,672 lost native readings. The
diagnostic, candidate source and expanded final assembly must reproduce their
qualified SHA-256 receipts before source review begins.

The complete source join is independently reconstructed against the pinned
Perseus revision. Every joined header, route, partition and article digest/XML
must equal the previous private dossier. Missing joins and ambiguous joins
remain explicit; homograph suffixes are preserved. The projected key is not
automatically substituted for the literal headword emitted by the pipeline.

For each joined article the recovered projected header is replayed in a fresh
process through `combitype`, `splitlat`, `conj1` and `latvb`. Only bound
`:vs:`, `:vb:`, `:de:` and `:wd:` directives count as emitted definitions.
Empty lemma blocks and default lexer ECHO text do not count. Multiplicity is
preserved. Process failure, timeout or malformed output aborts the review.

The public report contains counts of review decisions and crossed grammar,
identity, partition and extraction profiles. Individual articles, headers,
baseline lines, emitted definitions and filter transcripts are written only
to an exclusive private file outside the repository and inputs, mode 0600.
Neither private output is uploaded as a CI artifact.

Review decisions distinguish missing or ambiguous source joins, different
literal headword identities, nonverbal partitions, extraction failures and
definitions emitted in isolation but absent from the assembled candidate.
These are review leads. A successful isolated replay is not proof that the
full stream produces the same result, that the lost baseline paradigm is
source-supported, or that inserting its stems is justified. No candidate or
production data is modified by this tool.

The workflow first repeats the two complete grammatical LISTALL passes and
the native loss diagnostic, then runs this review against the same inputs.
The resulting counts and receipt are recorded in PR #18 after CI completes.
