<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Reconstructing the missing dictionary exports

The original `/local/text/lsj/lemmata` and `/local/text/ls/lemmata` files do not
survive in the inspected Morpheus history. The committed `lsj.nom`, `lsj.vbs`,
`ls.nom` and `vbs.latin` files are separately curated snapshots. This project
therefore reconstructs a **new, inspectable projection**, not the historical
bytes or the provenance of those snapshots. See
[the production audit](stemlib-production-audit.md#repository-archaeology).

## First investigation stage

`tools/reconstruct-lexical-exports.py` reads the [PerseusDL/lexica](https://github.com/PerseusDL/lexica)
revision `56061ca127f4a2844980baffc5f2b6d1332897b3`. It requires Python
3.9 or newer and `lxml`. The selected edition is all 27 LSJ TEI chunks and
`lat.ls.perseus-eng1.xml` (the archival Lewis & Short edition retaining Beta
Code in Greek quotations). The tool refuses another revision, missing chunks,
an existing output directory or an output inside this repository. Its XML
reader neither fetches DTDs nor resolves entities.

```sh
git clone --filter=blob:none --no-checkout https://github.com/PerseusDL/lexica.git /private/lexica
git -C /private/lexica sparse-checkout set CTS_XML_TEI/perseus/pdllex/grc/lsj CTS_XML_TEI/perseus/pdllex/lat/ls
git -C /private/lexica checkout 56061ca127f4a2844980baffc5f2b6d1332897b3
python3 -m pip install lxml
python3 tools/reconstruct-lexical-exports.py --lexica /private/lexica --output /private/lexical-stage
```

Use `--language Latin` or `--language Greek` to prepare only one edition.
This permits an isolated Latin import trial with just the archival Latin TEI
file checked out. The default still prepares both languages.

The output for each language consists of `headers.jsonl` (schema 1 header
records including unprojectable entries), `lemmata` (a pseudo-TEI comparison
stream), `skipped.tsv` (entry identifiers and reasons) and `report.json`
(schema 2: input and output SHA-256, entry counts and exact lemma overlap). The header
record retains the source key, entry ID, ordered direct child fields before
the first `<sense>`, their original text and a candidate Latin quantity
projection (`ā` → `a_`, `ă` → `a^`, `ï` → `i+`). Numbered source keys receive a
candidate `#` suffix. Fields with unsupported characters, unresolved entities
or unsupported keys stay in the header records but cannot enter `lemmata`.
No dictionary definitions are exported. The projected stream has **not** been
accepted as a production input to the legacy stem importers.

For both languages, the first token of each pseudo-TEI record is the first
projected `<orth>` spelling, including quantity marks and any homograph suffix.
That first field is omitted from the following pseudo-TEI fragments: the
Latin filters use the leading spelling as the stem base and treat later
`<orth>` fields as alternates; the Greek `newlems2` importer expects a `<gen>`
or `<itype>` field after the spelling. The TEI `key` remains in
the header record and supplies the candidate lemma identifier; it is not a
substitute for the quantified spelling. The other ordered fields remain
available for review. Entries with a complex first orthography still need
individual inspection before any corpus upgrade.

The archival Latin TEI also contains `ў` (U+045E) in headwords such as
`Abdalonўmus`, `ăbўla` and `Alcўŏnē`. The corresponding curated `ls.nom`
headwords read `Abdalony^mus`, `A^by^la` and `Alcy^o^ne_`; this witnesses an
explicit `ў` → `y^` conversion for this edition. Other unsupported characters
remain unprojectable rather than being silently discarded.

Initial run at that revision:

| Source | TEI entries | Projected rows | Reasons for unprojectable entries | Exact overlap with distinct committed `:le:` lemmas |
| --- | ---: | ---: | --- | ---: |
| LSJ Greek | 116,497 | 116,171 | 321 keys; 5 characters | 62,113 / 67,349 |
| Lewis & Short Latin | 51,596 | 51,460 | 106 keys; 30 characters | 40,608 / 47,175 |

The overlap is a **headword diagnostic**, not a coverage or equivalence
claim: homograph numbering, accents, subsequent manual corrections, and the
much larger number of stem records per lemma all affect the comparison. Each
skipped entry is individually recorded. Neither these provisional exports nor
new stem indexes are part of the production receipt, release archives or
redistribution policy.

The first Greek projection repeated the first `<orth>` after the leading TEI
key. A later importer-oriented projection uses the first `<orth>` as the
leading spelling and omits that repeated field. It projects 116,133 of
116,497 LSJ entries; 38 additional entries with complex first orthographies
are skipped, and the exact distinct-lemma overlap changes from 62,113 to
62,112 of 67,349 curated Greek lemmes. Both projection reports preserve the
entry-level reasons, and neither is a recovered historical export.

For Latin, an additional diagnostic pairs a projected first `<orth>` with the
raw headword **immediately preceding** `:le:` in `ls.nom`, when such a line
exists. Of 40,327 distinct curated lemmes with that adjacent line, 33,876
also have a projected header. Their first orthography matches exactly for
31,148 lemmes. It matches for 33,530 after ignoring case, trailing homograph
number and quantity/diaeresis marks. The remaining 346 include compound
hyphenation, multiple forms in one orthographic field and real differences
between editions. `report.json` records examples. This comparison concerns
headword spelling alone; it does not validate stem records or morphology.

The reproducible residual diagnostic in that report groups the 346 Latin
first-orthography mismatches left after case, homograph and quantity are
ignored: 260 agree after additionally removing hyphens, 39 after removing
other punctuation, 16 have a prefix or containment relation, and 31 do not
meet any of those tests. These are spelling probes, not accepted equivalences
or a reason to rewrite the projected headword.

## Next validation gates

1. Review the unprojectable entries and candidate headword mapping against
   the old lexer rules; preserve evidence for every change to the projection.
2. Review the experimental Latin header partition against source entries and
   historical importer behavior; establish a defensible replacement for the
   missing `vtags` selector and compare stems with all four curated snapshots.
   Do not overwrite them.
3. Compare analyzer behavior with fixtures and the archived 2007 Hopper
   morphology oracles before proposing any corpus migration.
4. Obtain the separate corpus-specific rights and notices decision described
   in [stemlib-redistribution.md](stemlib-redistribution.md) before publishing
   any derived lexical data or rebuilt stemlib.

The TEI input is credited to the Perseus Digital Library and is offered under
CC BY-SA 4.0 with its accompanying availability statement and attribution
instructions in each edition's `README.md`. The private staging directory is
kept outside the repository so its data cannot enter a program-source commit.

## Isolated Latin importer experiment

The opt-in [research workflow](../.github/workflows/lexical-import-research.yml)
checks out the pinned Latin TEI, compiles the historical `flex` filters and
runs both Latin chains in an ephemeral runner. It uploads no artifacts and
prints only aggregate counts and SHA-256 digests. `tools/audit-lexical-stems.py`
compares exact colon-tagged stem records by lemma as multisets, preserving
duplicate records. It does not use an edit-distance or normalized-spelling
threshold to declare stem equivalence. Its schema 5 diagnostic also counts
shared lemmes with no common stem line, those with partial overlap, and
unmatched records by tag. It prints only aggregate counts and digests.

The original Latin makefile requires an untracked `vtags` file to select
verbal records and exclude them from the nominal chain. No `vtags` file is
available in this checkout. The first two diagnostic chains below received
the whole candidate stream. The nominal run also omitted the makefile's
separate filter for `<pos>P. a.</pos>`. These measurements are **not** a
reconstruction of the historical partition or evidence that the remaining
stems are correct.

On [the successful full-corpus research run](https://github.com/defense-humanites/libmorpheus/actions/runs/36124653236),
the 51,460 Latin candidate rows passed through `splitlems`, `fixhesc` and
`fixgend`; the first filter emitted 52,872 lines. The unpartitioned producer
comparisons were:

| Diagnostic producer | Candidate / reference distinct lemmes | Shared lemmes | Identical record multisets among shared lemmes | Exact shared records with multiplicity |
| --- | ---: | ---: | ---: | ---: |
| `latnom` against `ls.nom` | 37,947 / 40,408 | 33,055 | 31,336 | 35,039 |
| `latvb` against `vbs.latin` | 6,618 / 6,773 | 6,316 | 6,117 | 9,277 |

Using the TEI key as the first token and repeating the first `<orth>` produced
only 3,938 equal nominal groups among 33,680 shared lemmes in an earlier
probe. Correcting the input layout explains most of that discrepancy. The
remaining differences require a reviewed `vtags` replacement, separation of
nominal and verbal inputs, and per-lemma comparison before any stem source is
changed. The curated files remain untouched and redistribution remains gated
by [the corpus-specific rights review](stemlib-redistribution.md).

### Experimental TEI header partition

`tools/partition-lexical-latin.py` makes a provisional, reproducible selection
using only projected TEI header fields: a verbal `<pos>` or a final conjugation
number/infinitive in `<itype>` selects a verbal entry. Exact `<itype>`
values used as inputs by the historical `conj1` or `latvb` rules provide a
second verbal signal; `<pos>P. a.</pos>` selects a separate participial
exclusion. All other projected entries go to the nominal trial. It reads the
header and candidate streams in order and refuses mismatched headwords. The
committed curated snapshots do **not** participate in selection. Output is
private, outside the repository, with counts and digests in the stage report;
it is neither the original `vtags` file nor a production classifier.

The initial classifier put 43,887 projected rows in the nominal
trial, 6,811 in the verbal trial and 762 in the participial exclusion; 136
entries cannot be projected. A separate check against the curated lemma
inventories shows 6,240 projected entries assigned to the verbal trial whose
lemma occurs only in `vbs.latin`, but 429 projected entries whose lemma occurs
only in that verbal witness remain in the nominal trial. Five assigned verbal
entries occur in both witnesses; four occur only in `ls.nom`. This overlap
check identifies limitations and does not supply classification labels.

An aggregate inventory audit of that initial partition, before the
source-rule refinement, shows why
the 429 verbal-only witness entries left in the nominal trial require more
than a field-presence rule: 273 projected headers have only `<orth>`, and
156 have `<orth>` and `<itype>` without a recognized conjugation signal.
The same two field profiles occur in 404 and 2,155 nominal-only witness
entries, respectively. The audit counts projected source entries, including
repeated lemmes, and never uses either witness to choose a partition.

A subsequent source-rule refinement selects 39 more verbal trial rows from
exact historical `<itype>` literals: 24 match a `conj1` input rule and 15
match `latvb` (including three with no lemma in either curated witness).
Among the 39, 36 occur only in `vbs.latin` and none only in `ls.nom`.
The revised partition has 43,848 nominal and 6,850 verbal rows; the
verbal-only witness entries still assigned nominal fall from 429 to 393.
Of those 393, 273 headers contain only `<orth>` and 120 have `<orth>`
plus `<itype>`. This remains an inventory probe, not evidence of stem
equivalence.

In [the earlier isolated partition run](https://github.com/defense-humanites/libmorpheus/actions/runs/36126908468),
the historical filter chains consumed their respective trial streams and
produced these exact comparisons:

| Diagnostic producer | Candidate / reference distinct lemmes | Shared lemmes | Identical record multisets among shared lemmes | Exact shared records with multiplicity |
| --- | ---: | ---: | ---: | ---: |
| Partitioned `latnom` against `ls.nom` | 37,366 / 40,408 | 32,953 | 31,270 | 34,967 |
| Partitioned `latvb` against `vbs.latin` | 6,542 / 6,773 | 6,256 | 6,056 | 9,197 |

In [the revised partition run](https://github.com/defense-humanites/libmorpheus/actions/runs/36326369118)
on `43d161f`, both historical filter jobs succeeded:

| Diagnostic producer | Candidate / reference distinct lemmes | Shared lemmes | Identical record multisets among shared lemmes | Exact shared records with multiplicity |
| --- | ---: | ---: | ---: | ---: |
| Revised `latnom` against `ls.nom` | 37,366 / 40,408 | 32,953 | 31,270 | 34,967 |
| Revised `latvb` against `vbs.latin` | 6,581 / 6,773 | 6,292 | 6,083 | 9,252 |

The verbal refinement adds 39 candidate lemmes, 36 shared lemmes, 27 exact
lemma groups and 55 exact shared records relative to the earlier trial. The
nominal comparison counts are unchanged, but its diagnostic file digest
changed (`ad11b97b...` to `6061cd1a...`); equal aggregate counts do not
establish byte-for-byte equality. Both exact-group counts remain below the
unpartitioned diagnostics. The selector demonstrates the importer plumbing
and isolates a concrete classification problem; it does not justify a corpus
replacement. Remaining work includes reviewing false classifications,
entries with no usable TEI signal, differences between projected and
historical header syntax, and individual stem mismatches before analyzer-level
checks.

## Isolated Greek importer experiment

The same [research workflow](../.github/workflows/lexical-import-research.yml)
also fetches all 27 pinned LSJ chunks. It runs the makefile's `sed`,
`setquant`, `splitlems`, `newlems` and `newlems2` chain against the new
first-orth projection in an ephemeral runner. The 116,133 projected records
produce 118,363 split lines. The dictionary probe in `newlems` reads the
committed `stemlib/Greek/stemsrc/lemlist`, so its decisions depend on a
pre-existing curated inventory. The job explicitly sets `MORPHLIB` and checks
that both accepted and excluded probe results occur: otherwise `newlems` may
quietly treat a missing dictionary as an empty one. No candidate records are
uploaded or logged. In the guarded run, the probe marked 90,403 split lines
for further processing and 27,960 as already present in that dictionary.

In [the successful dictionary-backed trial](https://github.com/defense-humanites/libmorpheus/actions/runs/36131613333),
the exact stem multiset comparisons were:

| Diagnostic producer | Candidate / reference distinct lemmes | Shared lemmes | Identical record multisets among shared lemmes | Exact shared records with multiplicity |
| --- | ---: | ---: | ---: | ---: |
| Greek `newlems2` nominal output against `lsj.nom` | 46,674 / 51,448 | 44,673 | 28,345 | 28,406 |
| Greek `newlems2` verbal output against `lsj.vbs` | 15,644 / 15,901 | 15,066 | 10,116 | 10,139 |

These counts describe an importer trial, not independent validation of the
source lexicon or a complete stemlib rebuild. The dictionary probe, historical
hand edits and unreviewed spelling differences remain material. The committed
Greek stem sources stay untouched pending per-lemma review, analyzer fixtures
and the separate rights decision.

### Latin differential probe with Whitaker's WORDS

Whitaker's own [description of `LISTALL`](https://mk270.github.io/whitakers-words/dictionary.html)
calls it a deduplicated list of roughly half of two million primary inflected
forms. The [historical archive is listed on SourceForge](https://sourceforge.net/projects/wwwords/files/Whitaker/),
and the [preserved HOWTO](https://github.com/mk270/whitakers-words/blob/master/HOWTO.txt)
defines its scope as the forms generated from `DICTLINE` and `INFLECTS`,
excluding `ADDONS` and spelling `TRICKS`. The available
[`mk270/whitakers-words` sources](https://github.com/mk270/whitakers-words)
provide a fallback for independently generating or checking a pinned corpus;
the unavailable 2012 Digital Gaffiot morphology archive is not an input.

Use `LISTALL` as an **external differential probe**, never as a Latin gold
standard or a replacement stemlib. First record the exact archive/source
revision, SHA-256, encoding, distinct form count and deduplication rules.
Preserve the literal forms for the first pass, then report any case or
orthographic normalization in separately named tiers; do not silently merge
`u/v`, `i/j` or enclitic variants. Analyze the same forms with the same native
binary and request options against both the curated Perseids Latin stemlib and
the privately reconstructed Latin stemlib. Report a two-by-two recognition
table, errors separately from zero analyses, and aggregate digests. Keep the
per-form differences private and outside CI artifacts.

`tools/audit-latin-listall.py` implements that literal recognition pass for
an extracted **plain ASCII, one-form-per-line** wordlist. It accepts an
explicit native library and two stemlib roots, checks duplicate and blank
lines, and emits the input SHA-256, four recognition cells and status pairs.
It does not fold case or change orthography. A private per-form JSONL can be
requested for subsequent grouping; it refuses existing files and any output
inside the repository:

```sh
python3 tools/audit-latin-listall.py \
  --forms /private/LISTALL.TXT \
  --library /private/libmorpheus.so \
  --curated /private/curated-runtime \
  --rebuilt /private/rebuilt-runtime \
  --private-output /private/listall-differences.jsonl
```

Both contexts use the same native library, Latin language and request options
zero. The optional JSONL records errors, absences and changed analysis counts
without exporting analysis contents. It is not a comparison of grammatical
interpretations: a form recognized by both analyzers can still have different
lemmes or paradigms. The tool has passed a three-form native smoke test with
the same curated root on both sides; the full `LISTALL` pass awaits the
wordlist and a complete privately reconstructed Latin runtime.

`LISTALL` alone contains surface forms, not lemma and paradigm assignments.
For the unrecognized and changed cells, a second, pinned WORDS analysis pass
can supply candidate lemmas and paradigms for grouped inspection, checked
against `DICTLINE.GEN` and `INFLECTS.LAT`. The
[`kigawas/whitakers-words` TypeScript port](https://github.com/kigawas/whitakers-words)
offers structured analyses but must be checked against the selected WORDS
data and implementation before those labels are used. Review samples in
each group against Lewis & Short, the original and rebuilt Morpheus stems and
the relevant inflection rule. A missing Morpheus analysis can reflect a
lexical gap, a paradigm or spelling difference, or a deliberately different
model; a generated WORDS form is not evidence of historical attestation.

### Shape of the remaining differences

[An aggregate-only follow-up run](https://github.com/defense-humanites/libmorpheus/actions/runs/36178088608)
classifies each shared lemma by exact stem multiset equality, disjoint stem
lines, or partial overlap. All shared lemmes in these four trials have at
least one stem line on both sides.

| Trial against curated witness | Exact | No identical stem line | Partial overlap |
| --- | ---: | ---: | ---: |
| Greek nominal | 28,345 | 16,271 | 57 |
| Greek verbal | 10,116 | 4,927 | 23 |
| Partitioned Latin nominal | 31,270 | 529 | 1,154 |
| Partitioned Latin verbal | 6,056 | 15 | 185 |

For Greek, nearly every unequal shared lemma has no exact stem line in common;
for Latin, unequal shared lemmes more often retain at least one. The comparison
does not identify whether a Greek difference comes from a spelling, quantity,
paradigm, source-edition change or later hand edit. The next review must inspect
those causes without treating normalized spellings as equivalent stems.

### Greek quantity-mark trial

The opt-in `--greek-spelling-diagnostic` compares additional signatures **only
after** exact comparison has found no common stem line. It preserves each
record's tag, morphology labels and multiplicity while removing `^` and `_`
from the first stem token. A separate tier removes the other Beta Code
diacritics; neither tier changes the exact-match counts or declares stem
equivalence. In [the isolated trial](https://github.com/defense-humanites/libmorpheus/actions/runs/36179297779),
16,110 of 16,271 disjoint nominal lemmes and 4,898 of 4,927 disjoint verbal
lemmes have identical record multisets after removing just the two quantity
marks. Of these, marks occur only on candidate stems for 14,692 nominal and
4,867 verbal lemmes, only on the witnesses for 844 and 19, and on both sides
for 574 and 12. The remaining disjoint groups need other explanations.

The pinned TEI projection's first orthography contains `^` or `_` in 34,749
Greek records; none of its projected header records has a separate `<quant>`
field. A second private [workflow trial](https://github.com/defense-humanites/libmorpheus/actions/runs/36179903316)
removed those marks from the first token of 35,263 split lines before
`newlems`, leaving every other field intact. It then ran the same historical
filters and exact multiset comparison:

| Greek witness | Original exact groups | Quantity-suppressed exact groups | Newly exact | Previously exact lost |
| --- | ---: | ---: | ---: | ---: |
| `lsj.nom` | 28,345 | 43,123 | 14,779 | 1 |
| `lsj.vbs` | 10,116 | 15,009 | 4,893 | 0 |

This isolates a substantial quantity-notation difference between the TEI
projection and committed stem snapshots. The variant is a diagnostic input,
not a corrected LSJ export: quantities may matter to analysis, and the
remaining differences and the one lost nominal match require entry-level
review. Neither variant replaces the curated sources.

[A follow-up of the same private trial](https://github.com/defense-humanites/libmorpheus/actions/runs/36233955694)
applied the spelling diagnostic to the quantity-suppressed outputs. Among
shared lemmes, the nominal variant has 43,123 exact groups, 1,560 groups with
no identical stem line, and 74 with partial overlap. The verbal variant has
15,009 exact groups, 31 with no identical stem line, and 27 with partial
overlap. The disjoint groups break down as follows; these are diagnostic
signatures, not accepted equivalences:

| Disjoint-group signature after suppressing first-token quantity | Nominal | Verbal |
| --- | ---: | ---: |
| Equal after removing remaining `^` and `_` | 1,410 | 31 |
| Equal after removing other Beta Code diacritics as well | 12 | 0 |
| Same tags and labels, different stem spelling | 87 | 0 |
| Same tags and labels, different multiplicity | 1 | 0 |
| Different tags or labels | 50 | 0 |

Of the 1,410 nominal quantity-only groups, marks occur only in the curated
witness for 1,307 lemmes, only in the variant for 60, and on both sides for
43. All 31 verbal quantity-only groups have marks only in the witness.
Suppressing the projected first-token marks therefore cannot make these
groups exact. The 150 other disjoint nominal groups, the partial-overlap
groups, and the changed lemma inventories still need entry-level review;
quantity normalization alone does not explain them. Keep the variant private
and retain both quantity-bearing curated snapshots for analyzer checks.

`tools/triage-greek-quantity-residuals.py` narrows these 1,441 disjoint
groups to the quantity marks in the **stem token**; underscores in labels such
as `os_ou` do not count. All have one stem record on each side. On the pinned
private inputs it gives this further partition:

| Quantity marks in stem tokens | Nominal | Verbal |
| --- | ---: | ---: |
| Candidate unmarked, witness marked | 1,307 | 31 |
| Witness unmarked, candidate marked | 60 | 0 |
| Both marked at distinct positions | 40 | 0 |
| Both marked with positions partly shared | 2 | 0 |
| Same positions, different marks or multiplicity | 1 | 0 |

Of the nominal cases, 1,342 candidate records are `:no:` and 68 are `:aj:`;
all 31 verbal records are `:de:`.
In the 40 distinct-position cases, 39 place a short mark (`^`) at different
vowels on the two sides, and one opposes candidate long (`_`) to witness
short (`^`) at different positions. The two partly shared cases have both
`_` and `^` on the candidate against `_` on the witness; the last has one
`_` against two at the same position. These 43 nominal cases merit earlier
entry-level source and paradigm review than the simple unmarked/marked
groups. This ordering is diagnostic, not a judgment of correct quantity.

An exact-lemma join against the pinned Greek header projection found **one
source entry for each of these 43 cases**. In 34, its first orthography has
no quantity mark within the compared stem. In nine, it marks a different
stem vowel from either side of this trial. Each of those nine still has that
source mark in the *original* projected stem, in addition to the residual
mark; removing first-token quantity removes exactly that source mark. The
other 34 projected stem records are unchanged by suppression. Thus the
nine marked sources do not settle which of the residual marks is correct.
The header projection SHA-256 is
`af61209863a354042928ff8c0cecf1ebf15264ae5920da46aa92516119a10dff`;
the 43 enriched, entry-level findings stay in a private file with SHA-256
`7028b7b208b26f5953030965e411fa6483cda1aad08905e094e162962317a16c`.

The indexer calls `stripshortmark` on a nominal stem **before** saving its
marked form. This gives a narrower analyzer-impact result for these 43
groups: replacing the witness records with the candidate records for the 39
cases with `^` on different vowels and the two with an additional candidate
`^` produced byte-identical nominal index and sidecar files both in an
isolated 43-record build and in the complete controlled nominal input. Only
two groups change the index because they differ in `_`: one has a doubled
long mark on the witness, and the other has candidate long versus witness
short marks on different vowels. Index identity here establishes the effect
of these 41 records under this indexer, not their correct vowel quantities.

The full pinned LSJ entries were inspected for the two long-mark cases. In
the doubled-mark case, `<pron>` specifies one long vowel. A controlled full
nominal-index trial with a single long mark removes an anomalous underscore
from the analyzed dictionary form. In the other, `<pron>` specifies a short
vowel while `<itype>` specifies a long vowel elsewhere; the two competing
stem records each preserve only one of those facts. The candidate long mark
adds a marked dictionary form to the analysis. An experimental stem carrying
**both** quantities produces an index byte-identical to the candidate-long
trial, because the indexer strips the short mark. The private decision ledger
(SHA-256 `2041321a9e5799877e6b1504ea52d3ca011a68d8ce5d14d9175783104478d0cf`)
records the source IDs and exact outputs. The full-index comparison used two
copies of the same private baseline, already containing the separate
19-line extra-stem experiment; a rebuild of its baseline nominal input
matched its preexisting index bytes. These two source-grounded corrections
remain experimental pending full-paradigm checks, and the curated witness
has not been edited.

The one-sided quantity groups can now be prioritized by mark type. Of the
1,410 nominal groups, **1,096** become the same complete stem record after
removing `^` from the stem token alone: 1,018 witness-only short marks, 37
candidate-only short marks, and the 41 both-marked cases just tested. A
controlled replacement of **all 1,096 at once** in the complete nominal input
again produced byte-identical `nomind` and `.lindex` files. One input record
has a separate constraint rewrite of its inflection label; that rewrite was
preserved on both sides of the comparison. The other **314** nominal groups
involve `_` differences (289 witness-only, 23 candidate-only, and the two
cases above) and remain the analyzer-impact priority. Of the 31 verbal
groups, 20 have a witness-only `^` and 11 a witness-only `_`. These figures
partition notation and index effect, not philological validity.

A private source join for the 314 nominal long-mark groups found one matched
LSJ entry for 313 groups and two possible orthographic source entries for
one. Inspecting the full pinned entries, **187** have an explicitly marked
`<pron>` but no quantity in the projected `<orth>` or `<itype>`, **104** have
both, and **23** have a marked `<orth>` or `<itype>` without a marked
`<pron>`. Every group therefore has some explicit source quantity evidence,
but the presence of a mark does not yet identify the vowel or justify either
stem record. The private 314-row source ledger, including the ambiguous
source pair, has SHA-256
`d8b850887260a654332fb879a1c14ada2e0f21d68b06d697b7af9974c9d8a5e9`.
The ledger checks nested as well as direct `<pron>` elements; this made no
difference to the nominal counts, but proved necessary for two verbal entries
below.

`tools/arbitrate-greek-quantity-long.py` applies five deliberately narrow
entry-level rules to that private ledger. In the first, the witness has one
long mark, the candidate has none, the unmarked stem is a prefix of a
**single** source headword, the marked vowel appears only once in that entire
headword, and a direct `<pron>` is exactly `[vowel_]`. This provisionally
retains the witness's long mark in **214** cases. In the second, a direct
`<pron>` supplies a longer marked segment with a unique location in the
single source headword, matching the marked position in the stem. It retains
the witness's long mark provisionally in **45** more cases. In the third, the
same contextual segment has a unique location in every matching later
`<orth>` of a single source entry when its first `<orth>` does not contain
the complete stem. This provisionally retains **two** additional witness
long marks; the matched segments are `[ni_]` and `[i_n]`. In the fourth, a
single source headword has several occurrences of the marked vowel, but
explicitly marks **every other** occurrence short in `<orth>` and has a
direct `[vowel_]` `<pron>`. This localizes the witness long mark in **two**
more cases, provisionally. In the fifth, the candidate ends its stem in
`a_`, has the `c_kos` type, and one source entry
explicitly supplies `<itype>a_kos</itype>`. All **24** candidate-only-long
cases meet this rule; one has a separate witness short mark that must be preserved.
Replacing these 24 records together in a controlled nominal index changed
the marked headword output for all 24 while retaining recognition and the
number of analyses. The rules select a source-backed quantity notation, not
an entire replacement stem record or a proven inflection class.

A controlled index trial removed just these two newly localized long marks
from a private copy of the same complete nominal input. Both `nomind` and
its `.lindex` changed. `cruncher -S -n` still recognized both queried
headwords: the first retained one analysis and the second three. Only the
marked dictionary form in the affected reading changed; the other two
readings of the second headword were identical. This compares two builds
from the same private baseline, not every form in either paradigm.

A second controlled trial removed only the two marks localized by the
contrasting short quantities. It changed both nominal index files and the
marked dictionary output for each queried headword. Each remained recognized
with one grammatical analysis. These trials establish the effect of those
marks in the controlled baseline, not full-paradigm equivalence.

The other **27** cases stay open: 26 witness-only long marks with ambiguous
positional evidence, and the doubled-mark case. The private decision ledger
has SHA-256 `3600eabf93c88c4841c77111aa345b845438eef7c230c1df0718f48e5a066f3f`.
Within this queue, 22 repeat the marked vowel in the stem, three repeat it
only elsewhere in the headword, one matches two source entries, and one is
the doubled mark already tested above. One of the 27 has an explicit long
mark in the source `<orth>` at a **different** repeated vowel from the
witness mark; three more have short marks at other positions which do not
by themselves uniquely locate the long mark. The other 23 have no explicit
quantity within the matched stem spelling in `<orth>`.
These cases are not resolved by a bare direct `<pron>` vowel. Each open case
requires its own source or paradigm decision; the current rule deliberately
leaves them unselected.

Two of the 27 have since received **individual** checks. For one, the first
matched LSJ entry is a cross-reference to another, where a later `<orth>`
spells the same headword and is immediately followed by a contextual direct
`<pron>` locating the witness's long mark. This provisionally retains that
mark, without relaxing the single-source automatic rule. The owner-only
individual decision record has SHA-256
`eaab913620acb6c33c3da0a1316d5f99ea41a4f1e953cb5a116f804c5e8e8c61`.
Removing this first
one mark in a controlled complete-index trial changed `nomind`, `.lindex`
and the displayed marked dictionary form; the queried headword retained
its single grammatical analysis. The full paradigm has not been qualified.

In the second individual case, the witness repeats `_` twice at the same
stem position, while the candidate uses a single `_` and the matching entry
has a single `[i_]` notation. A controlled one-record substitution of the
single-mark spelling changed both nominal index files. Five tested forms
remained recognized with the same grammatical readings; four inflected
outputs lost the doubled `__` while retaining one `_`. This supports the
candidate's **mark multiplicity** and removes that discrepancy from the
queue; it does not independently prove which of the headword's two `i`
vowels the source's bare `[i_]` describes. **25** nominal long-mark
differences remain for individual review.

`tools/audit-greek-pron-ambiguity.py --lexica /private/lexica` checks this
positional limitation across the same pinned 27 LSJ files. Among **171**
direct bare `[vowel_]` pronunciations whose first `<orth>` repeats that
vowel, **five** already mark the same vowel long somewhere in that `<orth>`
and **seven** mark it short somewhere. These count pronunciation occurrences,
not distinct lemmes, and the categories need not be disjoint. The combined
TEI input SHA-256 is
`6e3b08975d4d436ea929d86b63c757c70038286389edde6d48f97aa0228e1bc4`.
Thus a bare long-vowel `<pron>` cannot be assumed to name a *different*
occurrence merely because one is already marked long in `<orth>`; this
matters especially for the remaining entry with a long orthographic mark
at another occurrence. The script prints only aggregate counts and requires
the unchanged pinned checkout.
For a repeatable entry-level pass, `tools/prepare-greek-quantity-source-review.py`
joins the private output of `triage-greek-quantity-residuals.py` with the
projected Greek headers and the unchanged pinned LSJ files. It retains only
stem records with a long mark on either side, requires 314 groups when called
with `--expected 314`, and writes entry-level source fields and direct or
nested `<pron>` elements only to a newly created private file. It reports
source counts and digests without exposing individual entries. The new join
is a reconstruction of the input shape, not a claim that its bytes equal the
earlier private ledger; compare its counts and inspect any extra source match
before applying provisional rules.

```sh
python3 tools/triage-greek-quantity-residuals.py \
  --candidate /private/stage/Greek.no-first-quantity.nominal \
  --witness stemlib/Greek/stemsrc/lsj.nom \
  --private-output /private/greek-quantity-triage.jsonl
python3 tools/prepare-greek-quantity-source-review.py \
  --triage /private/greek-quantity-triage.jsonl \
  --headers /private/stage/Greek.headers.jsonl \
  --lexica /private/lexica \
  --output /private/greek-long-source-review.jsonl \
  --expected 314
```

`tools/inspect-greek-quantity-open.py` accepts that private source review
used by the long-mark arbitrator. It selects
only rows still classified `manual_review` and lists zero-based letter positions
and quantity marks in each source orthography alongside its direct or nested
`<pron>` records. The output is a **private dossier**, not a decision ledger:

```sh
python3 tools/inspect-greek-quantity-open.py \
  --source-review /private/greek-long-source-review.jsonl \
  --private-output /private/greek-long-open-positions.jsonl
```

The public summary contains only counts and SHA-256 digests. This selection
still includes the two cases subsequently checked individually; exclude them
from the 25 pending decisions during review. Explicit marks in another
orthography or a longer `<pron>` prompt inspection of their local TEI
relationship; they do not select the witness's position automatically.

A fresh private reconstruction using the portable Greek header splitter and
locally compiled `newlems`/`newlems2` reproduced the 1,410 quantity groups,
the 1,096 short-only cases, and all six previously reported dispositions of
the 314 long-mark cases. The private decision ledger SHA-256 is again
`3600eabf93c88c4841c77111aa345b845438eef7c230c1df0718f48e5a066f3f`.
The source join found 313 single-entry and one two-entry matches. Its input
triage SHA-256 is
`3c3e8cf33f6fd2721e51c6ac69f493a232e84905fb43034341e05db11a9a10fe`;
the pinned TEI SHA-256 remains the one recorded above. The first version of
the source-join selector counted two cases with `_` on both sides that differed
only by `^`; the corrected selector compares stem tokens after removing `^`
and returns exactly 314 groups.

`tools/audit-greek-open-diphthongs.py` applies Morpheus's existing
`is_diphth` distinction to the 27 open rows: an `i` or `u` immediately after
the first vowel of a recognized diphthong, without diaeresis, is not an
independent vowel to which a bare `[i_]` or `[u_]` can assign length. With a
single matching LSJ entry and direct bare `<pron>`, this leaves one eligible
position in **nine** rows. In **eight** it agrees with the witness's long
mark; in **one** it points to another occurrence and therefore does not
validate either complete stem record. The nine entry-level observations are
private (SHA-256
`55e5919a788d7ad020b33e806109b265c57c70a2574b8a6be7c9f273fb38ed1a`).
These are provisional decisions about the position indicated by LSJ, pending
controlled index and paradigm checks before any source replacement. The
other **16** of the 25 pending individual cases have no decision from this
diagnostic.

The single position conflicting with the witness was then tested by moving
its long mark to the only independent vowel indicated by the matching direct
`<pron>`. Two private nominal inputs were assembled in the same manifest
order with the **64** recorded Greek nominal corrections and the same
entity constraints; only this one stem record differs. Their SHA-256 values
are `d42629acfb53dee4267704e4a097b91a57433d399e9735e2ac8a393e028fe933`
and `a0c1f263217dbc7c5ee59fff261e8abdcb18e0a4ab1976a4daa5f563243f6952`.
Both indexed successfully with the same native `indexnoms`. The nominal
index changed; its `.lindex` remained byte-identical. In a six-form
`cruncher -S -n` probe, **five** forms were recognized in both indexes,
with the same **six** grammatical readings. The marked displayed forms
changed, including the accentuation of one plural output. This supports
a source-backed correction of the long-mark *position* for this entry, not
the candidate's entirely unmarked stem or a claim about the full paradigm.
The rebuilt baseline index differs from the bundled production index; all
comparisons here are between two builds from the same controlled input.

Five more of the 16 open cases have now received **individual** component
checks. In each, the compound's LSJ `<orth>` marks a segment boundary and
its direct bare `<pron>` is ambiguous in isolation; a separate LSJ entry
identifies the corresponding component or root. Three of those entries
explicitly mark the relevant vowel long in `<orth>`, one has a direct bare
`<pron>` with only one occurrence of that vowel, and one has a bracketed
quantity notation in its entry text with only one eligible vowel. The
matching spelling, location, and local sense relationship were reviewed
separately; one compound's alternate `<orth>` also marks the same position.
The private five-row evidence record has SHA-256
`e3f340492650031dbb750c0e543e0f843ddfebd4affffcc64d13af1cbe2790b6`.
These checks provisionally retain the witness's long position in those five
entries, without treating matching suffixes as an automatic rule. **Eleven**
of the original 25 remain without a source-backed positional decision.

A controlled trial removed only those five long marks from the corrected
complete Greek nominal input (trial input SHA-256
`ae961cb6409f17f6420c03a07ad4f6207e0a062a53e32a2d81aa0cb56b7e62dd`).
Both `nomind` and `.lindex` changed. All five queried headwords remained
recognized in both indexes with the same seven grammatical readings; their
marked dictionary display changed. This is a headword probe, not a check of
their full paradigms. The retained source files and bundled index are
unchanged.

Five further cases were inspected through their individual LSJ etymologies
and separately indexed components. Four compound relationships identify the
witness's long-vowel position: a fat-root compound, a verb-derived compound
whose prefix is explicitly short, a rust-derived noun matched to the
appropriate homograph, and a leaven compound. In the fifth, the Lydian
component explicitly has long `u`, whereas the `u(po/` prefix explicitly has
short `u`; its witness mark is on the prefix, so the source supports moving
the mark to the component. These are case-specific provisional readings,
not a general compound-transfer rule. The five private evidence rows have
SHA-256 `cea865fbda16eb96e597b7ba9071563390302db99d487401c79c8c57c47cfdb8`.

A controlled trial removed the four retained witness marks and relocated the
fifth in a copy of the same corrected complete nominal input (SHA-256
`ed393a337d27e2711237bdc69c63573bba6284220db0bd44e5a7e8a0dc99f324`).
Both nominal index files changed. `cruncher -S -n -T` recognized all five
queried headwords against each index with the same six grammatical readings.
The marked displayed forms changed, including both readings of one noun;
the relocation displayed the component's long `u` in place of the prefix's.
This checks headwords only, not full paradigms or a production index.

**Six** of the original 25 still lack a complete positional decision. Two
repeat `a` and four repeat `i`; each has a direct bare quantity notation
that cannot alone choose the occurrence. In one, a component supports the
second `a` but does not exclude the witness's first `a`. In another, the
orthography already marks the first `i` long, and the bare pronunciation may
repeat that same mark rather than establish a second one. Short orthographic
quantity at another vowel and an uncertain related-verb sense likewise do
not settle the other entries. The six private residual reasons have SHA-256
`d6b95b817d2f9fa736f5d0f094df402d8f99a1a804916da1b594e165ee50f4df`.
No curated lexical record is changed by these observations.

The six remaining positions have now been examined individually. Five
provisionally retain the witness's position. One direct `[a_]` is localized
by the short `-ma` suffix and Smyth's explicit long first `a` in the
cross-referenced eagle noun (§38); a propitiation root has a separate entry with
one `i` and direct `[i_]`; two nouns in `-i/ths` have the long `-i_ths`
formation, one also supported by a synonym with a single long `i`; and
an architectural noun has the long `i` of its door-jamb component rather
than that of an unrelated similar verb. The architectural interpretation
is supported by [Ginouvès, *Dictionnaire méthodique de l'architecture grecque
et romaine*, II (1992)](https://www.persee.fr/doc/efr_0000-0000_1992_dic_84_2),
p. 47, correcting the broader LSJ gloss. [Smyth's *Greek Grammar*](https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.04.0007%3Apart%3D3)
(§§833, 843, 861) supplies the suffix quantities. These
relationships are evaluated for these entries only; they do not license
automatic transfer to other compounds.

The sixth case provisionally **moves** the witness's long mark from the
first `a` of a short preposition to the second `a` of its independently
attested component. [Smyth's convention](https://grammars.alpheios.net/smyth/xhtml/body.1_div1.1_div2.1.html)
(§4) treats unmarked `a` as short
and prints the preposition without a macron (§1683). The pinned LSJ entry
for the component has a single `a` and direct `[a_]`; a parallel compound
explicitly marks its own first `a` short while retaining `[a_]` for that
same component. This combination localizes the bare quantity in the target
compound. The private six-row evidence ledger has SHA-256
`c23e3936fbe943b4b53a01677b34dbbfa0e0931ca27b351c47a059d06fc46fcc`.

Removing the five retained marks in a controlled copy of the corrected
complete nominal input (SHA-256
`a9f814242b78938e6ce70a4b73e24615e5be56c5c87cd4daf7f369f0f5f3879b`)
changed both nominal index files. All five headwords remained recognized
with the same six grammatical readings, while their quantity displays
changed. A separate one-record relocation (input SHA-256
`88e591434a7c12d327d6df1b0228c8931303c2fa5810bf7c00985e10af5dd1b3`)
changed `nomind` but left `.lindex` identical; the queried headword
retained its single grammatical reading and displayed the mark on the
second `a`. Thus all 25 cases that required individual review now have
provisional positional decisions: 22 retain the witness position and three
relocate a long mark. These are controlled headword probes,
not full-paradigm qualification, and they do not change the curated source.

A wider controlled generation pass has since tested the **25** individually
reviewed source blocks. It built three private generation indexes: the
corrected witness baseline, the same records with the three provisional
relocations, and a counterfactual with the other 22 witness long marks
removed. The source-file SHA-256 digests are respectively
`3cda7aaffe5331373127c704eaed08c3ba48fa9279739ebf78f042e8d67ecc59`,
`f2e637a5d0ef246b6dc304e006b22b6920a194cf98b561aa163d8b17c1ae4925`,
and `57869a64b6565467aec2c32a9303b96a621506f75760ce13d6a982119a4e8120`.
Each yielded **1,394** generated form rows, with identical counts and
grammatical feature multisets for every lemma. The three relocations changed
263 generated rows; removing the other 22 marks changed 1,131. Ignoring
quantity and accent notation, the letter forms and grammatical features
were identical. The generated accent differed for one relocated lemma and
seven of the 22 counterfactual unmarked lemmes.

For the three relocations, the union of baseline and relocated generated
forms supplied **221** distinct surfaces (private SHA-256
`5fe71ee1dfe3189d6046760e87c00b4c2c2d6af15864b0bbeca05318a53b81ad`).
Both complete indexes recognized all 221 with the same per-surface
grammatical readings: 301 XML reading rows and 357 expanded analyses on
each side. Four generated rows of one noun also changed accent. This
comparison uses the rebuilt baseline index, not the bundled index.

The union of the three generated outputs contains **1,212** distinct query
surfaces after stripping quantity marks (private input SHA-256
`7b0aff0b4b40de95364cd68af49165aac93e4ac09dc7d38c3aa914f6b8680adc`).
Two complete nominal indexes were rebuilt from the same corrected private
baseline: one with all three relocations (input SHA-256
`f1216d809d03da586d3bc420ead248c3f2bcac089728b2f4891b400e2a043908`),
the other additionally removing the 22 retained marks (input SHA-256
`f06e43754bab613e72bb55403f3ec52c27a58f355d1fa0f9d3062a6db5d8cbe6`).
`cruncher -S -n -T` recognized all 1,212 surfaces against both and returned
the expected lemma for every surface; each side produced 1,733 XML reading
rows (1,642 nominal, 87 verbal, four participial) and 1,937 expanded analyses.
The reading-kind, lemma and grammatical-reading
multisets matched **per surface**, although quantity display and some
accentuation changed. This qualifies the forms generated from these one-record
inputs under accent-insensitive lookup. It does not establish equivalence for
unattested forms, other source records of a lemma, or the distributed index.

The same 1,212 surfaces were then checked with accents enabled, using
`cruncher -S -T` and the same three rebuilt indexes:

| Complete index | Recognized surfaces | XML reading rows | Expanded analyses |
| --- | ---: | ---: | ---: |
| Corrected witness baseline | 1,209 | 1,425 | 1,497 |
| Three provisional relocations | 1,212 | 1,424 | 1,496 |
| Relocations plus 22 long marks removed | 1,191 | 1,431 | 1,503 |

The three relocations gained three circumflex surfaces of one noun and
changed the reading multisets of four other surfaces that remain recognized.
Removing the other 22 long marks lost 21 circumflex surfaces across seven
lemmes and changed the reading multisets of 28 shared surfaces. Each of
those seven lemmes accounts for three lost and four changed surfaces.
The two other relocated lemmes retain their recognition and grammatical
readings in this probe. Thus the earlier accent-insensitive result cannot
be extended to accent-sensitive lookup: long quantity affects both which
forms are accepted and which grammatical readings match a supplied accent.
All recognized forms still include the expected lemma; none is recognized
only through an unrelated homograph. The individual comparison ledgers
remain private, with SHA-256
`88b2f00d56f51c3f38681ff7b6d03e3137d3bca6d05110ebbef989571f148c57`
and `a519bb3c4f11c676e5195192008c0157f23fd9cb4e3da49ef92df13c4b5c8272`.

`tools/compare-greek-cruncher-readings.py` reproduces these counts from a
unique literal ASCII wordlist and two saved `cruncher -T` stdout files.
It includes nominal, verbal and participial homographs, compares reading
multisets per surface, and distinguishes recognition, grammatical-reading
and display changes. A headword printed without a separate displayed form
is interpreted as both display and lemma. Malformed or unsupported output
is rejected. The options used to obtain the two stdout files must be recorded
separately; the parser does not infer them. It prints aggregate counts and
digests, and only writes individual differences to a new owner-only file
outside the repository:

```sh
python3 tools/compare-greek-cruncher-readings.py \
  --forms /private/greek-generated-forms.txt \
  --left /private/greek-baseline.analysis \
  --right /private/greek-trial.analysis \
  --private-output /private/greek-reading-differences.jsonl
```

The parser also confirms the earlier accent-insensitive comparison across
all 1,733 XML readings, including the verbal and participial homographs;
all per-surface grammatical multisets still agree. Its four synthetic tests
cover omitted unrecognized inputs, duplicate readings, homographs, display
suppression, malformed output, and the private-output boundary.

The tool prints only counts and hashes; its `--private-output` must remain
outside the repository and CI artifacts. No bulk edit to the curated sources
follows from these provisional decisions.

For the two nominal long-mark cases, `cruncher -S -n` was also compared on a
small inflection probe: five recognized forms of the second noun changed
their displayed quantity, while six recognized forms of the first lost the
duplicated mark or its stray underscore. The grammatical analyses in this
probe stayed the same. It does not qualify their entire paradigms.

The verbal comparison has now followed the same controlled procedure. The
four corrected Greek verbal source files were assembled in manifest order,
expanded with `do_conj`, and indexed with the same `index_stems` implementation
used by `indexvbs`. Replacing all **20 short-mark records** at once left the
complete `vbind` and `.lindex` byte-identical. Replacing the **11 long-mark
records** changed both index files; each of the 11 changes also did so when
tested separately, while `oddkeys` remained identical. This is a comparison
between two builds from the same corrected private source tree; its rebuilt
baseline does not match the bundled `vbind` byte-for-byte, so these digests
must not be presented as production-index hashes.

Each of the 11 long-mark verbs has one matched pinned LSJ entry and an
explicit long-vowel `<pron>`: nine occur directly under the entry and two
are nested with a cited or inflected form. This distinction matters when
deciding whether the notation applies to the headword. In a controlled
`cruncher -S -n` headword probe, all 11 headwords were recognized on both
sides and all 11 outputs changed only in their displayed marked form; their
grammatical readings remained the same. The private source ledger and the
per-entry index-effect ledger have SHA-256 digests
`ad672ea19bc3cbaa6ebea8c7edfa712f87787633e25ed2a601b484f6ed9c84f4`
and `3bbfacafd41c83268c0e3fcf587c884c6037e817d83c80ecadc701a768c7d425`.
These observations prioritize preservation of source-supported length in an
experimental reconstruction, subject to inflected-form review; they do not
authorize replacing curated verbal records in this branch.

The nominal candidate and witness SHA-256
digests are `ba41260b8cc6e6bdfacbae47c58669780826245cebcb7297fb0198f0234b1b93`
and `bfb03e172cb16e464ae6e97793a9c3b0d2196433e40463081f9a1e2d481af8d2`;
the verbal digests are `8100e9aef3989f1e06a4b8535023a129ddc9be2f7f922722f1be1b2a164b1df2`
and `1169d2ccea85048e95742d12f58b49faf83fafc02f064abc2fa988239da6aa4c`.
For an entry-level ledger, run the tool with `--candidate`, `--witness` and
`--private-output /private/Greek.quantity-review.jsonl`. Its stdout contains
only counts and digests; the exclusive private output contains individual
stems and must stay outside the repository and CI artifacts. The classes
describe where notation differs. They do not establish which vowel quantity
is correct or authorize copying witness marks to the reconstructed export.

The spelling audit also classifies **unmatched records within partial-overlap
groups** after subtracting exact shared lines. One-sided residuals are counted
separately from pairs of residual multisets; the same quantity, Beta Code,
stem, label and multiplicity signatures then apply to the latter. This keeps
an already matching line from masking the cause of the remaining difference.
The classification never changes exact-match totals or accepts normalized
forms as equivalent stems.

In [the isolated follow-up run](https://github.com/defense-humanites/libmorpheus/actions/runs/36234393322),
every partial-overlap group had **one-sided** unmatched lines. There were no
groups with residual lines on both sides after exact lines were subtracted:

| Greek trial | Extra candidate lines only | Extra witness lines only | Both sides have unmatched lines |
| --- | ---: | ---: | ---: |
| Original nominal | 8 | 49 | 0 |
| Original verbal | 3 | 20 | 0 |
| Quantity-suppressed nominal | 10 | 64 | 0 |
| Quantity-suppressed verbal | 3 | 24 | 0 |

These groups require a review of missing or additional records rather than
another spelling normalization. The counts are per lemma, not numbers of
unmatched stem lines; they do not establish which side is correct.

[A further aggregate audit](https://github.com/defense-humanites/libmorpheus/actions/runs/36237959564)
counted the unmatched lines by tag and checked whether each repeats a line
already shared by that lemma. In these trials every partial-overlap group has
exactly **one** unmatched line:

| Greek trial | Candidate: repeated / new lines | Witness: repeated / new lines | Residual tags |
| --- | ---: | ---: | --- |
| Original nominal | 6 / 2 | 35 / 14 | 49 `:no:`, 8 `:aj:` |
| Original verbal | 3 / 0 | 20 / 0 | 23 `:de:` |
| Quantity-suppressed nominal | 9 / 1 | 46 / 18 | 66 `:no:`, 8 `:aj:` |
| Quantity-suppressed verbal | 3 / 0 | 24 / 0 | 27 `:de:` |

For the quantity-suppressed variant, 82 of 101 partial-overlap groups therefore
have only a multiplicity difference in an already shared stem line; the other
19 have one additional nominal line. The historical `newlems2` filter emits
one stem line per successful entry through `dump_entry`, so repeated source
entries and later curation are both possible explanations. The audit does not
identify which explanation applies to any individual lemma. Review the 19
additional nominal lines against their TEI headers and the curated witness
privately before changing the importer or a snapshot.

### Locating the 19 distinct nominal lines

An [aggregate-only provenance probe](https://github.com/defense-humanites/libmorpheus/actions/runs/36263114376)
examines just the 19 distinct lines in the quantity-suppressed trial. One is
extra in the candidate and was already present in the original candidate;
the other 18 occur only in the curated witness and in neither candidate. All
19 lemmes have exactly one projected TEI header with the same key. This is a
key match, not proof that a particular stem line came from that header.

The candidate-only line occurs under a later `:le:` marker for its lemma;
the candidate has multiple markers, whereas the witness has one. Of the 18
witness-only lines, 17 lemmes have multiple `:le:` markers in the witness;
16 lines occur in a later marker block. Two occur only in the first block,
including the one lemma with a single witness marker. Eight matching TEI
headers include `<gen>`, eleven include `<itype>` (one has both), and one has
multiple `<orth>` fields. These counts prioritize a private comparison of
the repeated marker blocks and the two first-block exceptions. They do not
identify whether a difference arose from another source edition, a historical
import step or later curation.

### Triage of the other disjoint nominal groups

[The isolated structural triage](https://github.com/defense-humanites/libmorpheus/actions/runs/36266412717)
revisited the 150 disjoint nominal groups in the quantity-suppressed trial
whose records do **not** become identical after removing `^` and `_`. It
matched the candidate lemma against the TEI key, the first `<orth>`, every
later `<orth>`, and the actual `splitlems` first-token stream. These are
traceability probes, not proof that a source entry produced a given stem.

| Signature | Groups | Structural finding |
| --- | ---: | --- |
| Other Beta Code diacritics only | 12 | All candidate records are adverbs (`:wd:`); no direct orthography or split-token match under the noun/verb lemma normalization. |
| Same tags and labels, different stem | 87 | 81 lack a first-orth/key match but match a later, untyped `<orth>`; all 87 occur in the split stream. |
| Same labels, different multiplicity | 1 | One key and first-orth match; the witness repeats its lemma marker. |
| Different tags or labels | 50 | 26 change tag sets, 24 keep the tag set but change labels; 48 match the first orthography and 2 a later untyped one. All occur in the split stream. |

Of the 26 tag-set changes, 22 compare a candidate `:no:` with witness `:aj:`,
two the reverse, and two candidate `:wd:` with witness `:aj:`. The 12 adverb
lemmes require a separate path: `newlems2` calls `standword` before emitting
their `:le:` marker, unlike the `stripmetachars` path used by its nominal and
adjectival `dump_entry`. An absent direct orthography match here is **not**
evidence of a missing TEI entry. For the 81 later-orthography matches, the
projection and `splitlems` do carry an alternate spelling; the stem mismatch
still needs entry-level comparison with the curated witness. The 24
same-tag-set label changes and 26 tag changes merit a separate morphological
review. No normalized spelling is promoted to an exact stem match.

[A follow-up on the adverb path and morphology](https://github.com/defense-humanites/libmorpheus/actions/runs/36311811500)
matched the **stem token** of each candidate `:wd:` line, rather than its
`standword`-derived lemma, against the quantity-suppressed split stream and
projected TEI orthographies. For all 12 diacritic-only adverb groups, that
candidate stem occurs in both places and a matching TEI header has
`<pos>Adv.</pos>`; none of the 12 witness stems has the same direct orthography
match. This traces the candidate's spelling input, but does not decide which
diacritics the analyzer should use.

The 50 tag-or-label groups divide further:

| Difference against witness | Groups | TEI fields in matched headers |
| --- | ---: | --- |
| Same tag `:no:`, different labels | 13 | Entry-level review needed |
| Same tag `:wd:`, different labels | 10 | Entry-level review needed |
| Same tag `:aj:`, different labels | 1 | Entry-level review needed |
| Candidate `:no:` versus witness `:aj:` | 22 | 21 with `<itype>`; 1 with `<gen>` |
| Candidate `:aj:` versus witness `:no:` | 2 | Neither `<gen>` nor `<itype>` in the matched header |
| Candidate `:wd:` versus witness `:aj:` | 2 | Both with `<pos>Adv.</pos>`; 1 with `<itype>` |

The field counts are diagnostic and may overlap within an entry. They locate
the next morphological review; they do not authorize changing tags or
replacing either curated witness.

### Private entry-level review

The projected Greek stream can be split locally without `flex` when it has no
`<quant>` field. `tools/split-greek-lexical-headers.py` reproduces the
historical `sed 's/-//' | setquant | splitlems` output for that subset and
refuses any other input with `<quant>`. It creates a private file outside the
repository and prints only its row count and SHA-256. For the pinned LSJ
projection, the local result has 118,363 lines and SHA-256
`c5b91d3d16fe8ceec05ada90c6a74aa1ee4fafa42f996ffdc161115cbf8166ba`,
identical to the `flex` output in CI. The research workflow compares both
streams byte for byte on every run.

The historical `greeklib.a`, `morphlib.a`, and `gkends.a` also build with
their legacy makefiles using `gcc`, without CMake. In a private copy of
`src/{includes,greeklib,morphlib,gkends,gkdict}`, building the three archives
and the `newlems` and `newlems2` targets recreates the research filters.
`newlems2.c` writes the verbal diagnostic to `/tmp/lsj.vbs`; a local build
with no writable `/tmp` can change that path **in the private copy only**.
Local nominal and verbal output SHA-256 values matched the CI audit for both
the original and first-token-quantity-suppressed streams. No generated stem
file is checked into the repository.

`tools/prepare-greek-lexical-review.py` selects the 150 non-quantity disjoint
nominal groups and the partial-overlap groups with a genuinely additional
line. Given locally reproduced filter outputs, it writes the candidate and
witness marker blocks, matching projected TEI headers and split input lines
to a **new file outside this repository**. Its stdout contains counts and a
digest only. For example, after privately producing the same staged streams
as the research workflow:

```sh
python3 tools/prepare-greek-lexical-review.py \
  --candidate /private/stage/Greek.no-first-quantity.nominal \
  --original-candidate /private/stage/Greek.nominal-diagnostic \
  --baseline stemlib/Greek/stemsrc/lsj.nom \
  --headers /private/stage/Greek.headers.jsonl \
  --split /private/stage/Greek.no-first-quantity.split \
  --output /private/greek-lexical-review.jsonl
```

The script refuses an existing output file and any output inside the source
repository, and creates the file with owner-only permissions. The JSONL rows
contain source-derived lexical material; keep them private, never attach them
to CI, and review each candidate/witness discrepancy before changing a
curated snapshot or the importer. The tool cannot infer which side is correct.

`tools/arbitrate-greek-lexical-review.py` records a first, deliberately narrow
decision for each row of that private file, in another owner-only file outside
the repository:

```sh
python3 tools/arbitrate-greek-lexical-review.py \
  --review /private/greek-lexical-review.jsonl \
  --output /private/greek-lexical-decisions.jsonl
```

On the pinned private review, 86 of the 87 `same_tags_and_labels` groups
become exactly equal after removing `-` **only from the candidate stem token**.
This is an accepted stem-separator representation difference: `indexstems`
calls `stripstemsep` before storing either the plain or marked stem. It calls
for no change to the curated witness or the importer. The remaining one also
differs in quantity and stays open. All 12 `beta_code_diacritics` groups
become equal after removing `+` only from that token. Their lookup key loses
the diaeresis, but `indexstems` can retain it in the marked stem. A subsequent
controlled analyzer experiment, described below, qualified this difference;
the initial decision ledger still records its pre-experiment disposition.
The other 71 groups remain for entry-level arbitration. The script makes no
equivalence claim for labels, tags, quantity, multiplicity or extra lines.
They comprise 50 tag/label changes, 19 distinct extra-line groups, one
multiplicity difference and the one quantity-bearing stem difference.
Its stdout gives counts and hashes only; the private ledger contains the
individual disposition and reason, and must never become a CI artifact.

An initial sense-level inspection of the ten candidate adverbs whose witness
adds `language` found four LSJ senses explicitly about a language or dialect,
four describing an ethnic or regional manner, and two with neither a language
nor a regional sense in that entry. Their ten entry IDs and separate
dispositions are recorded privately. The historical `getentities.pl` also
uses the `language` label to build `entitylist.txt`; copying it to the new
export as a suffix rule would therefore change an entity classification, not
merely a stem comment. Do not transfer all ten labels as a batch. Resolve the
intended historical scope of this label and check the entity index before
accepting individual annotations or editing a curated record.

The 22 cases where the candidate is `:no:` and the witness `:aj:` have also
been checked against their full LSJ entries. Twenty-one entries give an
adjectival sense and a genitive in `-onos` or `-wnos`; the historical
`newlems2` rule uses the projected `<itype>` alone to make a masculine noun.
For these entries the curated adjective is the better grammatical reading;
retain it and do not globally reinterpret that `<itype>`, which is also used
by nouns. The remaining entry is described as a nominal Attic variant in
LSJ, while the witness has a verbal adjective: keep its distinct reading
open for a homograph check. Entry IDs and individual findings stay in the
private review, not in this repository. This grammatical review settles the
choice to retain the curated adjective for 21 of the 71 initially queued
groups; 50 groups still need an individual decision, including the nominal
variant and the ten `language` labels.

The 19 partial-overlap groups have now been checked against the full LSJ
entries as well. Eleven witness-only extra lines have a second grammatical
use or paradigm explicitly described in the same entry; the one
candidate-only extra line is supported by an alternative adjective form in
another matching entry. Preserve these twelve alternatives for qualification
rather than treating the shared stem as a complete match. Seven other
witness-only lines have no direct support for that precise extra reading in
the inspected entry (some have a related cross-reference). Their provenance
remains open; absence from this edition is not grounds for deleting them.
All 19 entry-level evidence classes and source identifiers are kept privately.
Sense evidence alone does not establish that a proposed stem and inflection
class are correct. A second controlled index comparison removed the 18
witness-only lines and inserted the one candidate-only line, leaving every
other nominal source and constraint unchanged. `cruncher -S -n` changed the
headword analysis for **all 19** groups. The extra lines are therefore
analyzer-visible, including the seven whose precise provenance is still
unknown; do not drop those seven merely to improve stem multiset agreement.
The comparison qualifies the impact of those lines, not their philological
correctness or every inflected form.

The other 18 tag/label differences outside the `language` and
candidate-noun/witness-adjective groups received a first sense-level pass.
Eight concern entity labels whose semantic scope must be checked against the
historical entity list. All eight appear there under the witness's label,
with no matching override in `entitylist-byhand.txt`. Five labels have a
corresponding LSJ sense; three classify a geographic adjective or a singular
person as a place or group and need separate review. Do not infer the
historical entity labels from spelling suffixes. In two, LSJ explicitly supplies both a verbal
adjective and a noun; retaining both readings is preferable to substituting
one for the other. Two further entries are adjectives with a separately
formed adverb, while the importer's `<pos>Adv.</pos>` branch emits the
*adjective headword* as an adverb. That candidate line should not displace
the curated adjective. Two entries explicitly allow more than one gender;
two feminine headwords lack the genitive evidence needed to settle their
declension from the article alone. One headword supports the candidate's
eta-declension reading, subject to a paradigm check. The last retains a
source-supported, quantity-marked noun in the witness alongside another
reading requiring review. All entry IDs and provisional dispositions are
private; none is a global rewrite rule.

In the same controlled baseline, replacing the 21 curated adjectives with
candidate nouns, two adjectives with candidate indeclinable adverbs, and two
nouns with candidate verbal adjectives changed the headword analysis in
**all 25** cases. The noun substitutions change gender and case readings;
the adverb substitutions lose adjectival readings. An additional four-form
probe recognized all four forms with the witness and only three after these
substitutions; the missing form was a derived adverb whose adjective entry
had provided the analysis. Both index digests and the per-form outputs remain
private. This demonstrates material analyzer effects without making the
curated witness a universal gold standard.

For the 12 diaeresis entries, two private copies of the curated Greek runtime
were indexed with the same native `indexnoms` and the same nominal sources,
constraints and recorded lexical source corrections. In one copy, only the
12 adverb stem records were replaced by the source-projected `+` spellings.
`cruncher -S -n` analyzed each unmarked headword against both copies: all
12 had one analysis in each, with no error. The sole difference in these
outputs was that the source-spelling trial displayed both the marked and
unmarked dictionary forms, whereas the witness displayed only the unmarked
one. The rebuilt baseline index was not asserted byte-identical to the
bundled production index; this is a comparison between two controlled builds.
Retain the TEI diaeresis in the experimental reconstruction and preserve the
curated witness unchanged. The private record contains the two index digests
and output checks; this does not establish equivalence for other spellings or
other analyzer options.

The last two isolated cases still need provenance checks. In the
multiplicity case, the witness has two quantity variants on a different vowel
from the quantity shown in the projected orthography; suppressing first-token
quantity cannot recover them. In the remaining stem case, an earlier
orthographic variant marks a vowel's quantity but the matched alternate does
not; the witness retains that mark. Keep the witness variants and record the
source relationship without transferring quantity automatically across
alternates. The private review identifies both entries.

The local review selected 169 groups: 87 with matching tags and labels but
different stems, 50 with different tags or labels, 12 with Beta Code
diacritics beyond quantity, one with different multiplicity, and 19 partial
overlaps with a distinct line. Among those 19, 18 have a witness-only line
and one has a candidate-only line. These are review priorities, not automatic
changes to the curated data.

A private trial changed the `do_simpnom` gender branch in the copied
`newlems2.c` so a feminine `<gen>` could not be overwritten by its masculine
fallback. It altered 18 nominal lines and reduced equal record multisets
from 43,123 to 43,107 against the curated witness. That apparent code
correction is therefore not included in the importer reconstruction.

### Audit boundary

The pinned projection omits 364 of 116,497 Greek entries (321 unsupported
keys, 38 complex first orthographies and five unsupported characters) and
136 of 51,596 Latin entries (106 unsupported keys and 30 unsupported
characters). Every omitted header and its reason remains in the private
stage. Projecting one of these entries requires a defensible lemma and
orthography decision; simply deleting unsupported syntax would discard
source evidence.

The original importer trials, exact and spelling diagnostics, private Greek
entry review, Latin partition inventory audit, and Latin headword diagnostic
are complete for the pinned projection, including the revised Latin
historical filter-output comparison. None of these diagnostics
establishes a replacement lexical corpus. The 169 selected Greek entry
discrepancies have received a first review, including controlled index and
analysis checks for the 12 diaeresis cases; unresolved choices remain for
individual lexical and analyzer qualification. Another 1,410 nominal and 31 verbal disjoint
groups retain quantity differences, and the Latin trial lacks the historical
`vtags` selector while 393 verbal-only witness entries still land in its
revised nominal partition. Analyzer regression fixtures and the 2007 Hopper
oracles can qualify a selected candidate corpus only after these choices are resolved
and a complete private stemlib is built. Corpus publication also remains
subject to the separate rights decision in
[stemlib-redistribution.md](stemlib-redistribution.md).
