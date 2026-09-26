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
number/infinitive in `<itype>` selects a verbal entry; `<pos>P. a.</pos>`
selects a separate participial exclusion; all other projected entries go to
the nominal trial. It reads the header and candidate streams in order and
refuses mismatched headwords. The committed curated snapshots do **not**
participate in selection. Output is private, outside the repository, with
counts and digests in the stage report; it is neither the original `vtags`
file nor a production classifier.

For the pinned Latin TEI this puts 43,887 projected rows in the nominal
trial, 6,811 in the verbal trial and 762 in the participial exclusion; 136
entries cannot be projected. A separate check against the curated lemma
inventories shows 6,240 projected entries assigned to the verbal trial whose
lemma occurs only in `vbs.latin`, but 429 projected entries whose lemma occurs
only in that verbal witness remain in the nominal trial. Five assigned verbal
entries occur in both witnesses; four occur only in `ls.nom`. This overlap
check identifies limitations and does not supply classification labels.

In [the isolated partition run](https://github.com/defense-humanites/libmorpheus/actions/runs/36126908468),
the historical filter chains consumed their respective trial streams and
produced these exact comparisons:

| Diagnostic producer | Candidate / reference distinct lemmes | Shared lemmes | Identical record multisets among shared lemmes | Exact shared records with multiplicity |
| --- | ---: | ---: | ---: | ---: |
| Partitioned `latnom` against `ls.nom` | 37,366 / 40,408 | 32,953 | 31,270 | 34,967 |
| Partitioned `latvb` against `vbs.latin` | 6,542 / 6,773 | 6,256 | 6,056 | 9,197 |

Both exact-group counts are lower than in the unpartitioned diagnostics. The
selector thus demonstrates the importer plumbing and isolates a concrete
classification problem; it does not justify a corpus replacement. Remaining
work includes reviewing false classifications, entries with no usable TEI
signal, differences between projected and historical header syntax, and
individual stem mismatches before analyzer-level checks.

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
