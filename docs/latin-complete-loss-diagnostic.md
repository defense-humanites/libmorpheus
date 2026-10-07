<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Source and stem diagnostics for completely lost Latin forms

The global eleven-field comparison qualified on `d861a41` found 6,789 forms
recognized only by the controlled baseline. They carried 11,005 verb readings
under 133 distinct literal lemmas. The final five spelling trials restore 206
new forms without repairing these losses. Aggregate increases cannot identify
which definitions are missing, changed or still present.

`tools/diagnose-latin-lost-stems.py` consumes the private global JSONL and its
receipt. It selects only complete losses and reanalyzes them against the same
baseline and final native roots. The candidate must remain empty, and the
baseline count and multiset of all eleven fields must reproduce the recorded
loss exactly, including duplicates. Native errors and truncation of any text
used by the diagnostic abort it. Truncation of unused display text is not a
stem or lemma mismatch.

The replay exposes copied native analysis structures whose storage remains
valid after freeing the native result. Its existing eleven-field comparison
and public C interface retain their behavior. A new synthetic native test
uses a replaced class-three stem and checks its complete loss against the
real expanded inputs, independently of the global counters.

## Literal definitions and stem leads

The diagnostic reads the complete `verb.expanded` baseline and final
`present-trial.expanded` assemblies. They include the three retained verbal
inputs as well as the substituted input. Definition lines are compared under
exact lemma bytes, preserving duplicate records, flags and whitespace while
discarding line endings, blank lines and comments. Empty or absent definitions
are distinguished from equal and changed definition multisets. These are
literal input observations; changed whitespace is not a semantic regression.

Each native stem is compared with the stem tokens of `:vs:`, `:vb:`, `:de:`
and `:wd:` definitions under the same literal lemma. An exact baseline match
is followed by an exact final match check. A separate fallback removes only
`_`, `^` and `-` and is explicitly labelled a **notation lead**, never a stem
identity or a repair rule. Unmatched baseline stems remain unresolved rather
than being declared absent. A stem token surviving with different flags does
not prove that its lost grammatical reading is still licensed. A final token
missing under one lemma does not establish a philologically justified repair.

Raw membership checks distinguish lemmas in the substituted source, retained
sources, both or neither. A block can exist without defining the required
stem. Conversely, native preverb composition can return a lemma without an
explicit block. The diagnostic does not infer source authorization from these
mechanical observations and does not change any candidate or production data.

## Source joins and private review dossiers

The existing source validator checks the pinned Lewis and Short TEI, article
IDs and keys, recovered headwords and conjugation fields. The diagnostic joins
both the literal projected key and the literal emitted headword spelling used
by the Latin filters. It keeps the join route, preserves homograph suffixes,
and deduplicates routes to the same article. Multiple articles are retained
as an ambiguity; no article is chosen by guesswork. Entries with projection
errors are not silently used as valid joins.
Unique joins are also grouped by the existing research header partition
(verbal, nominal or participial). That partition is a review signal, not a
replacement for the unavailable historical selector or a linguistic verdict.

The owner-only dossier contains the lost forms and native readings, expanded
definitions under each lemma, source routes, projected headers, partition
decisions, article hashes and XML. It is written outside the repository and
all inputs, without overwriting existing files or following output symlinks.
It is not uploaded as an Actions artifact or committed.

Public output contains only counts, mechanical review groups and hashes.
Counts by readings and counts by distinct lemmas are labelled separately.
The workflow requires the previous private global difference hash and the
6,789/11,005/133 totals. It first reconstructs and checks the unchanged final
candidate and indexes and repeats the two global grammatical passes, then
performs this bounded reprobe. Eight synthetic diagnostic tests, the existing
comparison tests, a text truncation check and six native tests cover the route.
Real diagnostic groups and the private dossier fingerprint are to be recorded
in PR #18 after the run, without publishing lexical identities.
