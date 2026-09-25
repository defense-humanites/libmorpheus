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

For Latin, the first token of each pseudo-TEI record is the first projected
`<orth>` spelling, including quantity marks and any homograph suffix. That
first field is omitted from the following pseudo-TEI fragments, since the
historical `latnom` and `latvb` filters use the leading spelling as the stem
base and treat later `<orth>` fields as alternates. The TEI `key` remains in
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
2. Establish and review a replacement for the missing Latin `vtags` selector,
   then rerun the isolated importers on correctly partitioned inputs and
   compare stems with all four curated snapshots. Do not overwrite them.
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
threshold to declare stem equivalence.

The original Latin makefile requires an untracked `vtags` file to select
verbal records and exclude them from the nominal chain. No `vtags` file is
available in this checkout. Both diagnostic chains therefore received the
whole candidate stream. The nominal run also omitted the makefile's separate
filter for `<pos>P. a.</pos>`. These measurements are **not** a reconstruction
of the historical partition or evidence that the remaining stems are correct.

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
