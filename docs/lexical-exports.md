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

### Source topology of the Latin partition gaps

`tools/prepare-latin-partition-review.py` joins the unchanged projected
headers back to the pinned archival Latin TEI. It selects a private dossier
of the **393** verbal-only witness entries assigned to the nominal trial,
then locates source evidence independently of those inventory labels.
The dossier binds each source entry to its exact header-row SHA-256 and
records direct grammatical fields of the first sense, explicitly styled
italic verb labels, and source references. Quoted grammatical labels and
later-sense labels are not inherited. No partition or stem record changes.

Among the 393 dossiers, **375** have an explicit verbal `<pos>` as a direct
child of the first `<sense>`. Another **eight** have a direct italic verbal
label there (using the recorded `v. a.`, `v. n.`, deponent, frequentative or
inchoative prefixes). **Ten** have no such first-sense verbal signal and
need individual cross-reference handling. The old field-profile counts
(273 `<orth>` only, 120 `<orth>` plus `<itype>`) describe the projected
header, not the complete source entry. At least 383 gaps therefore reflect
source information omitted at the first-sense boundary, rather than absence
of grammatical information in the lexicon.

Across the nominal trial, the same independent inspection also finds
91 direct verbal `<pos>` signals and 155 italic verbal labels in entries
absent from both curated inventories. One nominal-only witness entry has
an italic verb label, and a different one has a conjugation-shaped `<itype>`
inside the first sense which actually encodes a citation. These controls
show why neither witness membership nor blindly appending every nested
`<itype>` can supply a safe global selector. Source labels, source syntax
and candidate stem generation need separate review before reconstructing
the missing historical `vtags` behavior.

```sh
python3 tools/prepare-latin-partition-review.py \
  --headers /private/Latin.headers.jsonl \
  --lexica /private/lexica \
  --nominal-baseline stemlib/Latin/stemsrc/ls.nom \
  --verbal-baseline stemlib/Latin/stemsrc/vbs.latin \
  --private-output /private/latin-partition-source-review.jsonl \
  --expected 393
```

The source TEI and unchanged header SHA-256 are
`ccbd2f79db1006edc607fe51227babab6872fbdaa4e925f4c1999a3b978041ee`
and `21a8475e126d8e912c1d5cf75026c4305e7a6deb14aae846c9362e36afede480`;
the private dossier SHA-256 is
`bb910aea9bb215662e05263aebe87b38a6913f01702f186c2df5dd0e06d68da5`.
The tool verifies the pinned revision and clean exact source, source keys,
duplicate IDs, optional expected count and owner-only output boundaries.
Four synthetic tests cover these checks and the source-topology exclusions.
The lexical research workflow now also runs on `research/lexical-arbitration-*`
branches. It reproduces this audit without writing or uploading the individual
dossier, and exercises the existing historical importer chains separately.

### Separate source-backed first-sense recovery trial

`tools/recover-latin-initial-sense.py` stages an alternative Latin header
stream using **only source evidence**, without consulting either curated
inventory. It augments a nominal-trial record only when the first sense
has a direct explicit verbal `<pos>` or one of the styled verbal labels
identified above. The direct grammatical fields are then appended with
source-location provenance. Italic verbal labels become explicit trial
`<pos>` fields. Conjugation-shaped `<itype>` alone does not authorize
recovery, so the mis-tagged citation is excluded. Quoted and later-sense
labels are also excluded. Any unsupported recovered field withholds the
whole recovery rather than silently discarding that field.

All old projected rows are verified against their **entire** original
header, not just the leading headword, before the new stage is created.
Unchanged rows retain their literal candidate text. Source joins, pinned
revision, exact source, row order, duplicate IDs, expected recovery count,
and new private stage boundaries are checked. The original projection and
selector remain the baseline; no public lexical file is overwritten.

```sh
python3 tools/recover-latin-initial-sense.py \
  --headers /private/Latin.headers.jsonl \
  --lemmata /private/Latin.lemmata \
  --lexica /private/lexica \
  --output /private/latin-source-recovered \
  --expected 630
```

The pinned source restores **630** projected records: 466 from verbal
`<pos>` and 164 from styled verbal labels. All recovered fields are
supported by the projection; 136 previously unprojected entries remain
unprojected. Re-running the unchanged partition on this alternative stream
gives **43,218 nominal**, **7,480 verbal**, and **762 participial** projected
rows. The verbal-only witness entries still routed nominal fall from 393
to **ten**; those ten are bare cross-references whose paradigms are not
inherited by this trial. Inventory labels do not select the 630 recoveries.

The alternative header and candidate-stream SHA-256 are
`77d759464aacf11b91ff3884be62bc846831b53e95574ff099ae23aaf71ebfa3`
and `0c260d9ea9875f376801f43ba45fd035da3764488028840ba32ae20db8250ada`.
The research workflow runs both historical filter chains on this stream
as a separate experiment, with per-record outputs and filter diagnostics
kept ephemeral and no artifacts uploaded. Three synthetic tests cover
explicit versus weak source signals, unsupported-field withholding,
exact old-row validation and private stage creation. This is a reviewed
source-recovery rule for a diagnostic trial, not recovery of historical
`vtags` or approval of the resulting stem corpus.

In [research run 36756480145](https://github.com/defense-humanites/libmorpheus/actions/runs/36756480145), both language jobs passed and the historical filters completed on the recovered stream. The nominal aggregate comparisons remain unchanged; the nominal output digest changes, so this does not establish byte identity. The verbal comparison improves substantially:

| Exact diagnostic | Original partition | Source-recovered partition |
| --- | ---: | ---: |
| Candidate verbal lemmas | 6,581 | 6,955 |
| Shared verbal lemmas | 6,292 | 6,662 |
| Shared lemmas with equal record multisets | 6,083 | 6,442 |
| Exact shared stem records, including multiplicity | 9,252 | 9,864 |
| Reference-only verbal lemmas | 481 | 111 |
| Shared lemmas with disjoint records | 15 | 16 |
| Shared lemmas with partial record overlap | 194 | 204 |

The recovered verbal output contains 10,398 stem records and has SHA-256
`dcdafaaaa24a350d94509a86cbc230c17246d49e8d07e8c24a2e4aa489ac25b0`.
The nominal output contains 40,268 records, 37,366 distinct lemmas, 32,953
shared lemmas and 31,270 equal shared record multisets; its SHA-256 is
`51c1abd4e9bf9d3e18ff3a11ea8723a1b784ec2b1387d6eea0b93bacbe3bc3f2`.
Neither output has orphan stem records or unexpected colon tags. The
additional exact matches qualify this limited projection repair; the 220
shared verbal lemmas with differing records still require lexical review.
These are stem comparisons, not analyzer or paradigm equivalence checks.

### Remaining Latin cross-reference source review

A private, manually reviewed dossier joins all ten remaining cross-reference
entries to ten exact source articles, recording source IDs, serialized-entry
digests, target orthographies, grammatical fields and witness records. Every
target is verbal in the source-recovered partition. This confirms the links,
but does not infer replacement stems from witness membership.

| Source relationship | Entries |
| --- | ---: |
| Spelling variant | 2 |
| Present-stem variant | 1 |
| Root-vowel variant | 1 |
| Present and participial variant | 1 |
| Active variant of a deponent | 3 |
| Deponent variant of an article covering both voices | 1 |
| Irregular passive relation | 1 |

All ten aliases have verbal witness records; nine target lemmas match that
inventory literally; the remaining target is absent under that literal lemma.
Separately, a numbered textual reference joins an article whose
source key does not encode that number: adding a numeric suffix would invent
an identifier. The target entry itself includes both active and deponent
fields, so neither a guessed homograph suffix nor wholesale inheritance of
its fields is justified. The private dossier SHA-256 is
`1c76769a38c7a8d408f88793fc554ca96696643624518c59e9291c5bbd519d49`.
The two spelling links still need literal stem and analyzer checks; the
remaining relations require voice, stem or irregular-paradigm handling.
None of these ten aliases is automatically reclassified or rewritten.

A separate curated-runtime dictionary-form probe checks the ten aliases and
ten target lemmas as **20 literal forms**, using `cruncher -L -S -T` against
the committed Latin stemlib. It recognizes **19/20** forms, each under its
exact expected verbal lemma. The absent form is the same target absent from
the literal witness inventory. XML output contains **29** reading rows,
including two nominal homographs; the legacy summary counter is not used
as an XML-row count. This is a curated-baseline probe, not a comparison
against a source-recovered runtime or a test of complete paradigms. Private
query and XML SHA-256 are
`fb73e46419ee6a025b7424bcc05e13d00c40b63945f5eed33e26e4f153c4731f`
and `aac4ef427a5ff3debc66d3d93757cc7aabe0532984fb114a0b68c8bf26102f4d`.

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
excluding `ADDONS` and spelling `TRICKS`. The current [`mk270/whitakers-words` sources](https://github.com/mk270/whitakers-words)
can support a separate WORDS analysis pass. Inspection of revision
`1f2f0fb0867a896d7b9284a03d615ed635d6f992` found neither a LISTALL file nor
a LISTALL generator, so that checkout alone is not a reproduction recipe.
The unavailable 2012 Digital Gaffiot morphology archive is not an input.

The historical SourceForge archive has now been fetched and pinned by
`tools/prepare-latin-listall.py`. The tool accepts only the exact archive and
its sole `listall` member, validates every token before creating a fresh
private stage, and preserves the original bytes beside a distinct literal
query list. It does not fold case, `i/j` or `u/v`. Three synthetic tests check
pin failures, archive members, invalid tokens, private output boundaries and
literal deduplication. The research workflow checks this archive in a
separate job; no lexical artifact is uploaded.

| Input | SHA-256 |
| --- | --- |
| Historical ZIP | `ea0b45df1271870b51befa882798c81cae158e8f6ebfbd748f76fbeeb692191d` |
| Original `listall` member | `6b557b50fc333cddb17082a6eb71fb87029d095738672a3cd308f7161073769b` |
| Sorted distinct literal LF queries | `1df0800fb1443b2cfd64d787c257319aa72b69f453c3c37ec60c359c70cebd93` |

The member has **13,121,619 bytes** and **1,034,157 CRLF lines**. Every line
is a nonempty ASCII token, at most 24 bytes. Despite the historical
"unique alphabetical" description, the actual bytes contain **578 repeated
lines**, giving **1,033,579 distinct forms**, and are not ordered by literal
ASCII bytes. The distinct query list removes only exact duplicate tokens
and sorts the remainder. Archive pinning does not identify the original
dictionary revision or assert that the present WORDS dictionary generates
the same list.

A full native ABI 2 pass, Latin language and request options zero, against
the committed curated runtime recognizes **837,313** of the **1,033,579**
distinct literal forms. It leaves **196,266** without an analysis, returns
**2,045,383** analysis records, and reports **zero errors**. This is a coverage
measurement against an external historical list, not an attestation claim
or a replacement-corpus result. The private static C driver uses the same
public `morpheus_open_path`, `morpheus_analyze`, result-count and free APIs
as the Python auditor; it avoids requiring a shared-library build in the
minimal local environment. These initial counts are **not qualified**: an
identical-root control subsequently exposed a native Latin spelling-buffer
defect. The corrected analyzer must be remeasured before any differential
coverage conclusion is accepted.

The defect is localized to the historical Latin `ex[cpt]` to `exs[cpt]`
spelling retry in `checkstring3`: the overlapping move copied the tail
letters but not their terminating zero. Results therefore depended on
residual stack bytes, even for a single query with identical dictionaries.
The bounded internal spelling helper now moves the terminator as well and
skips expansion when the extra byte cannot fit. Its synthetic C regression
uses poisoned tail bytes, all three supported consonants, unchanged prefixes,
exact-capacity and full-buffer cases, and an unterminated input. No lexical
source records are needed for this test. The 39-form private identical-root
reproducer now gives **216 readings on each side**, no changed counts and
zero errors. Twelve existing native API/context tests also pass locally;
the full LISTALL remeasurement and CI remain separate checks.

The first full corrected identical-root pass found **one** remaining count
difference. This localized a second spelling-retry defect: the interior `i/j`
predicate read two positions ahead before checking that the intervening byte
was not the string terminator; `strchr` also accepts the terminator itself.
The predicate now short-circuits at that boundary. Synthetic tests include
a two-byte final `i`, a nonzero poisoned byte after its terminator, unchanged
cases and valid interior vowel cases. Full coverage counts remain provisional
until the control succeeds with both fixes.

With both fixes, the full controlled-baseline identical-root pass now
recognizes **837,990** forms and leaves **195,589** absent on both sides.
Each context returns **2,048,328** readings, with **zero changed counts** and
**zero API errors** across all **1,033,579** queries. This qualifies count
stability for that exact control, not semantic equivalence of different
corpora. The synthetic spelling regression also passes ASan and UBSan
(leak detection disabled because the local sandbox has no process metadata).

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

### Corrected native full-corpus measurements

All following runs use the **same native binary with both spelling fixes**,
ABI 2, Latin, options zero, and the pinned **1,033,579** distinct literal
queries. The controlled baseline is rebuilt from the committed source
manifest and reviewed corrections, not the older committed binary indexes.
It must not be silently equated with that older curated runtime.

| Runtime | Recognized | Absent | Analysis rows | API errors |
| --- | ---: | ---: | ---: | ---: |
| Older committed curated indexes | 837,497 | 196,082 | 2,045,866 | 0 |
| Controlled rebuilt baseline | 837,990 | 195,589 | 2,048,328 | 0 |
| First-sense recovered verbs; baseline nominals | 835,582 | 197,997 | 2,056,734 | 0 |
| Full-compound trial plus five provisional nominal decisions | 832,999 | 200,580 | 2,062,058 | 0 |

The earlier pre-fix curated measurement is superseded. Both the controlled
baseline and full-compound candidate pass a complete identical-root control:
no changed counts, recognition differences or API errors. Separate baseline
and verbal-trial single-context passes reproduce their paired counts and
reading totals exactly. The full-compound candidate's two identical-root
contexts and a separate single-context full pass also reproduce its
different-root comparison totals exactly.

For the **verbal-only trial**, the controlled baseline and candidate recognize
**827,053** forms together; **10,937** are baseline-only, **8,529**
candidate-only, and **187,060** absent from both. Counts differ on **56,049**
forms. This loses a net **2,408** recognized forms, despite improving literal
agreement with witness stems.

For the **full-compound trial**, the differential recognition cells are:

| Controlled baseline | Candidate recognized | Candidate absent |
| --- | ---: | ---: |
| Recognized | 822,735 | 15,255 |
| Absent | 10,264 | 185,325 |

Counts differ on **83,744** forms. The net recognition loss is **4,991**.
These are recognition/count measurements, not a comparison of grammatical
signatures, correctness or historical attestation. Neither candidate is an
equivalent replacement for the controlled baseline.

Private reanalysis of all **10,937** verbal-trial losses yields **17,683**
baseline readings, all verbal, grouped under **165** lemmas; **61** groups
have no exact projected-header lemma join. Full-compound losses yield
**26,172** readings grouped under **1,061** lemmas, with **411** lacking an
exact projected-header join. A missing join is not proof of source absence:
spelling, homograph and curated-addition provenance still need review. The
dossiers retain literal forms and joined source headers privately. Their
SHA-256 are
`5282ab86456e593eaf40cb30ad3b5e19c8b62ce61096bef36cf7eedefceb6beb`
and `f619b3e708df456902bc8087db952c2c31a48247538d369fb90822a1d0ee9990`.

The full-compound count-control and comparison reports have SHA-256
`0a96f134f6b717a21603f326cac09af507658df0179ff7b54e16ba0fc9c10e7f`
and `3a56a1ba9ac21217958c26578b0bd11d11edffaa83ad6f689270e6d49fc1a502`.
Its independent single-context report SHA-256 is
`4d86e3c69d9252a68df6754acf333ea511b353818ede46402bc9cc6f487cabd8`.
The nine compound dictionary-probe exceptions are separately joined to the
pinned source: five absent forms and four recognized under other lemmas,
including three articles explicitly marked participial in the source.
Their lemma expectations need semantic review, not automatic paradigm
inheritance. That dossier SHA-256 is
`d42e2d25fa51a6d72e4fb417dcd26235c56c5750e38c0c284c7155ad554c097b`.

Stable native execution and successful index construction remove technical
blockers, but **do not qualify the imported corpus**. Promotion remains
blocked on these lexical losses and source/paradigm arbitration. No witness
stem copying, automatic alias inheritance, public lexical artifact or
production stemlib replacement is authorized by these measurements.

### Source-backed regular stem repair trials

The loss dossiers expose a historical `latvb` trimming defect: a first
conjugation headword ending in `eo` can lose the `e`, even though its explicit
conjugation is 1. `tools/repair-latin-first-conjugation.py` derives the primary
`are_vb` root from the complete source present spelling, removing only final
`o` or `or`. It validates the pinned source joins, headwords and conjugation
fields, requires an existing primary derivative record, and withholds
ambiguous sources, alternate records and inconsistent voice. It does not
modify historical filters, import witness stems or assign alias paradigms.
Five synthetic tests cover spelling quantities, homograph suffixes, voice,
source mismatch, output boundaries, no overwrite and a separate quantity tier.

Of **3,727** `are_vb` records, the full source trial repairs **220**:
**50** change letters and **170** change only quantity notation. **3,396**
already match, **94** lack a unique eligible source and **17** are withheld
for alternate/voice handling. `--tier letters-only` changes only the 50
letter-different records and preserves the other 170 for independent
qualification; it does not declare their quantities unnecessary. Full and
letters-only private output SHA-256 are
`0281bed9c7b231296d2786b542109243ff1db2cae79cd89183b764a1a4e6009d`
and `2d50859e3ac2b0b27d039474a291cbfe982bb5addc93a248317cac42723f418b`.

The full 220-record trial builds its complete verbal index successfully,
with the nominal index unchanged. Its complete identical-root control
recognizes **836,311** forms, leaves **197,268** absent, returns **2,070,263**
readings on each side and has zero changed counts or API errors. Compared
with the preceding full-compound trial, it gains **3,800** forms and loses
**488**, with **6,440** changed counts. Against the controlled baseline,
**823,838** are recognized by both, **14,152** baseline-only, **12,473**
candidate-only and **183,116** absent from both. Both comparisons reproduce
the control's reading totals exactly. New losses remain unqualified; source
repair is not proof that every old reading was wrong.

`tools/repair-latin-principal-parts.py` separately recognizes a precise
duplicated-present-fragment error in the historical conjugation-3 `s/d,q`
trimming path. It requires explicit perfect/fourth parts, a perfect component
spelling the present component, and an exact match to the defective output.
It removes only that duplicated fragment while retaining the explicit source
prefix and principal parts. No other ablaut, suppletion, alias or deponent
paradigm is inferred. Three synthetic tests cover the exact proof, newline
preservation, already-correct records and withheld unmatched/ambiguous cases.
This changes **two** records from one article. Full-source and letters-only
outputs after that repair have SHA-256
`e2996d043e59a2e8871289590ace2ea627ea216b1f2086d72d3746467fe32c65`
and `e857385b7a517641cf737b71e73456f7deddc6ed77bbfc1cf9857550192d1af0`.
These are separate experimental tiers; all individual records remain private.

The letters-only plus principal-parts runtime has now completed the same
**1,033,579**-form literal qualification. Its identical-root control recognizes
**836,346** forms, leaves **197,233** absent and returns **2,070,363** readings
on each side, with zero count differences or API errors. Against the preceding
full-compound runtime it gains **3,835** forms and loses **488**, with **6,494**
changed counts. Against the controlled baseline, **823,873** forms are recognized
by both, **14,117** baseline-only, **12,473** candidate-only and **183,116**
absent from both. Both comparison reading totals reproduce the controls.
The separate principal-parts repair recovers **35** additional forms from the
original full-compound loss subset: the combined trial recognizes **1,588**
of those **15,255** forms, returning **3,575** readings with no API error.

The all-quantity plus principal-parts runtime also builds successfully.
Although its expanded verbal source is not byte-identical to the letters-only
tier, removing only short marks (`^`) makes the expanded files equal. Both
produce byte-identical `vbind` and `vbind.lindex` files, with SHA-256
`887240be4655852927d701b1e8dfc49022b9b3408557f855c857fb051d5f72c9`
and `53375d51c89a236e2cdb3dc4af8a3eb4af00bae0529867e6f8a61288d874543c`.
Their nominal indexes remain unchanged. This has a specific implementation
explanation: `src/gkdict/indexstems.c` removes short marks before retaining a
marked stem. It does not establish that source quantities are dispensable,
that all quantity changes behave alike, or that Greek indexes behave likewise.
Preserve the source marks in the private reconstruction.
The subsequent complete literal comparison confirms **836,346** recognized
and **197,233** absent on each side, **2,070,363** readings per side and zero
gains, losses, count differences or API errors. This is the two specific
controlled Latin runtimes, with API options zero, not a general quantity oracle.

Reanalysis of the **488** newly absent forms against the preceding trial
returns **831** readings, all verbal, grouped under **29** native lemmas.
Of these readings, **712** carry the API's `preverb` field and **119** do not;
all have an empty `raw_preverb`. The private provenance dossier has SHA-256
`c307d213e319234c10e47aba504afb4026a649700d55b62596d812f2fd083be3`.
These losses include analyzer-generated prefix combinations: neither an empty
`raw_preverb` nor a missing exact source-header join proves a missing source
article. Conversely, a prefix/base join is only a review lead, not permission
to transfer a paradigm or dismiss a lost reading.
The 488-form loss sets are also exactly equal between the earlier all-quantity
trial and the letters-only plus principal-parts trial. A separate private
stem-spelling pass links each of the **831** readings uniquely to one of the
letter-repaired old derivative roots, either directly or with the regular
generated `at`/`av` component, ignoring quantity/stem-separator notation.
Its dossier SHA-256 is
`1ac41e140589f7e886162d70e49e7937e9537e71067b6a9ab32686488a4a63d5`.
This identifies a mechanical repair lead for every lost reading, not the
lexical validity of a compound or a grammatical signature equivalence.

The original full-compound loss dossier has also been joined with both native
preverb fields. Its **1,061** lemma groups comprise **650** exact header joins,
**20** spelling-notation joins, **22** prefixed-lemma/base review leads and
**369** unresolved groups. The five-field native dossier has SHA-256
`8898e1898db4582f3f0f651b7eff78eeca24ddeb4f436003351731b7e514f840`.
This refines the earlier **411** missing exact joins without converting them
into automatic source recovery. The new losses and the remaining baseline
losses still block corpus replacement.

### Explicit allomorph and alternative-part recovery

The principal-parts repair now offers a separate `--proof-tier source-allomorphs`
experiment; its default `exact-present` behavior remains the earlier two-record
trial. The new tier accepts conjugations 2 and 3 only, requires an existing
unflagged primary present record matching the source component, and recognizes
an explicit perfect with the same consonant skeleton or the precise `sp`/`spo`
reduplication. The source supplies every replacement letter and both principal
parts. The same exact defective `s/d,q` concatenation must still be present;
short suffixes, unmatched present records, alternate records, deponents and
ambiguous parts are withheld. These relations identify the component boundary;
they do not construct unattested allomorphs.

On the letters-only plus principal-parts candidate this changes **20** records
from **ten** articles, leaving the original two repairs already correct.
The private verbal output SHA-256 is
`95a9883c7b4c43ee7fc1782718c9a9fc73c794026a8a5f0c1216179314d1128f`.
The rebuilt verbal index and sidecar have SHA-256
`a6d34fe4dad69bb770899cf36657a0846611d66b6025a1caaa3ab2f3abefde38`
and `9e2e125df629ad699557295e438da84b1242543d1935db3cbdfe3cd3ac43854d`;
the nominal indexes are unchanged. The original **15,255**-form loss subset
now has **2,085** recognized forms and **4,582** readings, with no API error.
The principal-parts suite has five synthetic tests, including the separate
tier, source-present boundary, second conjugation, reduplication and withheld
voice/alternate cases.

`tools/recover-latin-ingo-parts.py` independently handles one narrowly
recognized unsupported header pattern: an explicit `-ingo` present, `inxi`
perfect, two `inctum`/`ictum` supines and conjugation 3. It requires one source
orthography and one matching conjugation field, preserves source quantities,
prefixes and homograph numbers, and adds four stem records only when the
complete echoed source header occurs exactly once and no existing lemma block
is present. It does not split arbitrary textual alternatives, fill another
article's paradigm or replace existing stem records. Three synthetic tests
cover those boundaries, private output and no overwrite.

This recovers **one** header. All **170** forms previously lost under its
source lemma now have that expected verbal lemma, returning **284** such
readings. On the original full-compound loss subset the combined candidate
recognizes **2,278** forms and returns **4,915** readings with no API error.
Private verbal output SHA-256 is
`b14aadb1c5ee537532f467b3b3d21fd66b06a87728dbbb3e672d9e200f787854`;
verbal index and sidecar SHA-256 are
`19b06160b4b4c366fb30ff6803ac6b5412677d38323f2503be74b2067c8b65ed`
and `9d32a43aff2119f6b1e9fc0ab75d456e9132044de321ac2430af0f5755737e99`.
The CI checks both new stages on both quantity tiers, without publishing
lexical artifacts. These targeted checks do not establish whole-corpus
recognition equivalence or resolve the remaining loss dossiers.

Both subsequent full LISTALL comparisons are complete, with **1,033,579**
literal forms and API options zero. Each runtime's identical-root control has
zero recognition/count differences and zero API errors. Their reading totals
are reproduced exactly by the baseline and preceding-trial comparisons:

| Trial | Recognized | Absent | Analysis rows | Gains / losses against preceding trial | Changed counts |
| --- | ---: | ---: | ---: | ---: | ---: |
| Explicit allomorphs | 836,843 | 196,736 | 2,072,239 | 497 / 0 | 815 |
| Allomorphs plus two-supine recovery | 837,036 | 196,543 | 2,073,111 | 193 / 0 | 498 |

Every changed count in these two preceding-trial comparisons increases;
neither decreases. The combined trial thus recovers **690** additional forms
over the earlier letters-only plus principal-parts runtime on this corpus,
without introducing a newly absent form. This does not assess unattested or
non-LISTALL spellings, nor validate every added compound reading.

Against the controlled baseline, the combined runtime has **824,563** forms
recognized by both, **13,427** baseline-only, **12,473** candidate-only and
**183,116** absent from both, with **85,289** changed counts and no API error.
Its remaining baseline-only forms yield **23,236** baseline readings under
**1,044** native lemma groups: **646** exact source-header joins, **15**
notation joins, **19** native-prefix/base review leads and **364** unresolved
groups. The updated private native provenance dossier has SHA-256
`7939a6c83063ac2059162ed83fa0afac32db2a5aa33f10af3649ec9c67c2b37c`.
These remaining losses still require lexical arbitration; recognition totals
alone do not promote this reconstruction.

### Complete same-article first-conjugation alternates

The historical `latvb` derivative branch clears its `orthstem` before emitting
alternate records, while typed alternate `<orth>` tags are outside its lexer
rule. `tools/recover-latin-full-alternates.py` stages a separate source-only
repair for existing primary `are_vb` records. It validates all supplied header
orthographies against the pinned projection and reads alternate orthographies
directly from the same article, accepting only `extent="full"`, an untyped or
`alt` spelling, and a complete present with matching voice. It requires a
unique source/article block, explicit first conjugation without a conflicting
conjugation, and an existing primary root matching the source after short-mark
removal. It preserves prefixes, quantities, homograph ownership and `orth`
flags. Abbreviations, voice differences, quantity-only alternatives, missing
primaries and cross-article paradigms are withheld. Existing alternate records
are not duplicated.

The private candidate adds **131** alternate derivative records under **118**
lemma blocks in each quantity tier. **368** incomplete spellings, **35** voice
differences, **49** ambiguous/missing source blocks and **91** unmatched
primaries are withheld; these counts describe different audit units, not one
partition of source entries. Four synthetic tests cover source-orthography
validation, ambiguity, voice, quantities, homographs, idempotence, final
newlines and private output boundaries. Letters-only and all-quantity output
SHA-256 are respectively
`a248a65b6f2053299ac6623354f48fefcedc07f4978c6e45e46f5f0d86096dce`
and `1e3671ca1f8edb263520f94807145e10e3bae1a3e269aac42b5341663dfd3f19`.

The combined verbal index builds successfully, with unchanged nominal indexes.
Its index/sidecar SHA-256 are
`9b515e4809ab17c733baaa1bf39f4474a50018786a80cffaff75b895ec3cc96b`
and `fd49351ae261e656c2dc09c5e03fcca458022905ed677edd041ba5a37bb5ab3e`.
On the original **15,255**-form loss subset it recognizes **2,721** forms and
returns **5,616** readings with no API error. A separate **286**-form source
article probe recognizes every form under its expected verbal lemma, returning
**438** readings under that one lemma. Its private reading dossier SHA-256 is
`38bde5b1f59927436467ee5bea9ed24c71ccf7500577f71d272474f2a2aab0d0`.
These checks qualify the narrowly staged alternates, not abbreviation
expansion, alias inheritance or production corpus replacement.

The alternate runtime's complete identical-root control recognizes **841,744**
forms, leaves **191,835** absent and returns **2,089,682** readings on each
side, with zero count differences or API errors. Against the preceding
two-supine runtime it gains **4,708** forms and loses none, with **9,615**
changed counts: **9,612** increase and **three** decrease. Against the controlled
baseline, **825,006** forms are recognized by both, **12,984** baseline-only,
**16,738** candidate-only and **178,851** absent from both; **90,686** counts
change. Both comparisons reproduce the control reading total exactly and
return no API error. The all-quantity tier is also built separately and
produces byte-identical verbal indexes and the same original-loss-subset
totals; this is a measured index comparison, not an assumption from equal
recognition counts.

The three decreasing counts total **22** prior readings and **15** new readings.
The new readings are direct gerundives under three source-supported verbal
lemmas. The earlier readings match the recorded features obtained after
explicitly removing terminal `dum` from the three inputs. `LatinSuff` in
`src/anal/checkstring.c` permits that suffix retry only while no direct analysis
exists. On the explicitly stripped inputs, the earlier runtime returns those
same **22** readings; the alternate runtime returns **28**, retaining all
**22** prior rows across the recorded lemma, POS, workword, stem, suffix,
ending, mood, case, gender and tense fields. The stripped-probe dossier hashes
are `6866dc3103d873cf6bf6bb02b50dffc84956e578e2eed8c9e25d7f78f1f7180f`
and `ead9dc158508a185fe560adf9a3fc4538e33f1304729938e225c91a0c66d7c51`.
This accounts for the direct-match/fallback selection change without removing
the old lexical entries or declaring every prior interpretation invalid.
The API and this analyzer selection policy are unchanged.

The current **12,984** baseline-only forms yield **22,537** baseline readings
under **1,040** lemma groups: **643** exact source-header joins, **15** notation
joins, **19** native-prefix/base review leads and **363** unresolved groups.
The updated private native dossier SHA-256 is
`9a62975377f5d388f4d73cde8bfe72186dc221f134f83ae6485b03d4edf32f4f`.
The earlier **488** newly absent forms remain absent in this runtime, with
zero API errors. These remaining dossiers, abbreviated spellings and missing
paradigm evidence still need individual arbitration; aggregate coverage gains
do not establish production-corpus equivalence.

### Remaining explicit second-supine fields

`tools/recover-latin-second-supines.py` separately stages the remaining four
simple dual-supine notices. It recognizes only explicit conjugation-3 `-tendo`
components with the supplied `d` or reduplicated perfect and `t`/`s` fourth
parts, or conjugation-4 `c` stems with explicit `s` perfect and `s`/`t` supines.
The unique source article, primary present, perfect and first fourth-part
records must all agree with the proven pattern before any change. Deponents,
conflicting conjugations, unmatched stems, duplicate blocks and unrelated
textual alternatives are withheld. Already-added records are not duplicated.

This adds **four** second fourth-part records and repairs **two** defective
records across **four** article blocks. In the conjugation-4 case, processing
the first explicit variant alone through the historical filters selects their
exact `si, sum, 4` rule and yields the repaired perfect and first supine.
Processing the second alone supplies the second supine but takes the generic
trim branch for the same perfect. The combined source field had taken that
generic branch for both records. The experiment retains the exact-rule
perfect, preserves both explicitly supplied fourth parts and leaves the
historical filters unchanged. It does not extrapolate this choice to other
principal-part alternations.

Five synthetic tests cover prefixes, quantities, homographs, both variant
orders, exact defective records, ambiguity, voice, idempotence, private output
and no overwrite. CI checks the four changed blocks in both quantity tiers.
Letters-only and all-quantity private output SHA-256 are
`36a07389a89c40bd9a0be5f3a6bf5f717d68eeba7b36623e82f48095a5497540`
and `a7b6abb64ce6d66fc08a14479ca32a503aecb207bf2f487b35eee83095764664`.
The letters-only verbal index and sidecar build successfully with SHA-256
`02c05aaf281d37a8d9a206ac3989f0b7dc38cfe62f2209e93911d475d7baa2d7`
and `6adfa718be75e5cfd1b19ea2acc66f0c169bb98e0d21c6412f9e8c384d97b825`;
the nominal indexes remain unchanged. The original full-compound loss-subset
totals remain **2,721** recognized forms and **5,616** readings, with no API
error. A source-supported missing principal part can affect readings without
increasing this subset's recognition total.

The complete **1,033,579**-form LISTALL control has zero errors and zero
count differences for identical roots. Against the preceding complete-alternate
runtime it also has zero changed recognition statuses or analysis counts:
**841,744** forms recognized and **2,089,682** readings. This corpus therefore
does not exercise the added principal parts. A separate source-derived probe
of **12** principal forms increases expected-lemma recognition from **7** to
**12**, and expected-lemma verbal readings from **30** to **58**. Its private
before/after dossier SHA-256 are
`29d0471e61fe126a05ecc7e7680847fc39209680560f5b70fe0d261d208a0ea1`
and `bce30fcb54fc49ee8d5b6c67e0847c047de09a3bf899144f85e473004ea2a54b`.

### Complete fourth-conjugation alternate with explicit perfect

`tools/recover-latin-full-alternates.py --tier fourth-explicit-perfect` is a
separate opt-in stage. It requires a unique source article whose only grammatical
field is exactly `i_vi, 4`, plus matching unflagged present and perfect records
in one existing lemma block. Only complete same-article alternate orthographies
with the same active ending qualify. The stage adds the alternate present and
explicit `i_v` perfect, without supplying an unattested fourth part. Abbreviated,
quantity-only, deponent, ambiguous and unmatched candidates are withheld.
The first-conjugation stage remains the default.

The pinned-source trial adds **two** records in **one** article. Six synthetic
tests cover both tiers, including explicit-perfect matching, voice, quantities,
homographs, ambiguity, idempotence and private output. CI reconstructs this stage
in both quantity tiers. Letters-only/all-quantity private outputs have SHA-256
`55d5467c0f3caea66dd3d42fc38304528dde412429730818c9e97be5962b541b`
and `3565bfb7744da352c26fff448030f4ffa7f86790dce467458ce10e041131241a`.

Both quantity tiers build identical native verbal indexes: SHA-256
`4b33f29060844e6994c6780bc824222d54316524e842a9f301fb043c568053ec`
and sidecar `3c4b2f850d1a7ad9026735766d8cf508056c3e5486ed26ef0e56bf4465892f5b`.
The nominal indexes remain unchanged. The original **15,255**-form loss subset
now recognizes **2,851** forms with **5,803** readings and zero API errors.
A **154**-form source-article probe recognizes **130** under the expected
verbal lemma, with **187** readings and no other lemma groups; private dossier
SHA-256 `b1789d4f1353c323fb677fd8d368cdff96639e378a7063a9f8c4316c873760e4`.
The **24** still absent forms have **56** baseline verbal readings sharing one
fourth-part stem (**54** participles and **two** supines). The explicit source
field used by this stage provides no fourth part, so those readings are held
for separate arbitration, not silently recreated. Their private baseline
provenance SHA-256 is
`ee3d884510eab6497a61e42336ae8dacf8ac5cf7ea17ac3d6aff51e4b75cbde3`.

The full **1,033,579**-form pass recognizes **841,874** forms and returns
**2,090,028** readings. Its identical-root control has zero differences and
zero errors. Relative to the preceding second-supine runtime, **130** forms
become recognized, none becomes absent, and all **237** changed analysis
counts increase. All three complete comparisons have zero API errors.
Against the controlled rebuilt baseline, the recognition cells are **825,136**
both, **12,854** baseline only, **16,738** candidate only and **178,851** neither.
The remaining loss provenance comprises **22,338** baseline readings in
**1,040** lemma groups: **643** exact source joins, **15** notation joins,
**19** native-preverb/base review leads and **363** unresolved groups. These
are still review leads, not paradigm inheritance decisions. Private dossier
SHA-256 `39d5aa1e6b3042031cb5c2901075a5a37c519120cb9e75987e2ebd67016d8aa0`.
The earlier **488** first-repair losses remain absent with zero API errors.

### Duplicate components proved by complete third-conjugation alternates

`tools/repair-latin-jicio-parts.py` stages nine exact cases separately. It
requires a single source field `je_ci, jectum, 3` or `je_ci, jactum, 3`, a
primary complete `-icio` spelling and exactly one complete same-article
`-jicio` spelling with the same prefix letters. A unique candidate block must
contain the matching unflagged present and exactly one perfect/fourth-part
record, each either already correct or equal to the precise duplicated
component pattern. Unmatched parts, flags, ambiguous source articles or
blocks, voice changes and differing prefix letters are withheld.

The stage repairs **18** records in **nine** blocks and adds **nine** alternate
present stems. Each repaired primary part preserves the source primary prefix
quantities; each added present uses its own complete alternate spelling.
Applying the historical filters independently to the nine complete alternate
headers confirms all **18** repaired principal-part letter sequences. This
is a letter comparison, not a claim that different source quantity spellings
are interchangeable. The original filters remain unchanged.

Five synthetic tests cover exact defective and already-correct records,
quantities, homographs, both supplied fourth parts, ambiguity, prefix and
voice mismatches, private output, expected counts, idempotence and no overwrite.
The complete-alternate source loader is shared without changing either
existing alternate tier; its six tests also pass. CI reconstructs both quantity
tiers. Their private output SHA-256 are
`58ea0bac73b0a8b4a7f173aa790e58689dc4a938377359faf73cf340b24b1124`
and `7e51fba761403302919957822e36ffee610ac5da7cf23c421cec4015d4c30e10`.
Both build identical native verbal indexes with SHA-256
`0ea900332be6149f47726596146f9a2e0724850a4db8914f1861e2f082a59101`
and sidecar `1933273f7c1d48daa22b7785942c4a7c905bb26708d82076bb7af304ad6765b1`;
the nominal indexes remain unchanged.

A separate **27**-form principal-part probe increases expected-lemma
recognition from **six** to **27** forms and expected-lemma verbal readings
from **21** to **93**. Private before/after dossier SHA-256 are
`423e9058d7c68ab54520134839a899553b30ed95ec656726219ecf241e97f51e`
and `3b8e9eb59828c9ba2fce3d123fe4f8b67d845c439aba272e1746e3b09884c27b`.
The original loss subset now recognizes **3,753** of **15,255** forms with
**7,160** readings and zero API errors. Complete LISTALL comparisons are
qualified separately below; this targeted subset is not a corpus-wide verdict.

The complete LISTALL comparison for this stage recognizes **842,776** forms
with **2,092,352** readings. The identical-root control has zero count
differences and zero errors. Against the preceding fourth-conjugation trial,
**902** forms become recognized, none becomes absent, and all **1,412** changed
counts increase. All **902** recovered forms are independently recognized
under their expected source verbal lemmas with **1,357** readings and no other
lemma/POS readings; private dossier SHA-256
`8f069f07ca02fbccd076189476e2b7294794b5473b66911a74da2e782eacba05`.

Against the controlled rebuilt baseline the recognition cells are **826,038**
both, **11,952** baseline only, **16,738** candidate only and **178,851** neither.
Remaining losses have **20,981** baseline readings in **1,031** lemma groups:
**634** exact source joins, **15** notation joins, **19** native-preverb/base
review leads and **363** unresolved groups. Private dossier SHA-256
`b836afcc80babeced4302ce1710bbbc4f9f1dc3e8dae88f8025d64adab205312`.
The earlier **488** first-repair losses remain absent with zero API errors.

### Complete alternates with three existing regular parts

`tools/recover-latin-regular-parts-alternates.py` is a separate additive stage.
It accepts only a unique source article with one field exactly `di, sum, 3`
and a literal active `-ndo` ending, or `i_vi, i_tum, 4` and active `-io`.
All three primary present/perfect/fourth-part records must already match that
specific regular pattern, without flags or competing primary records. Only
complete same-article alternates with the same supported ending qualify;
source ambiguities, incomplete or voice-changing spellings, and differences
limited to quantity or separators are withheld. The stage preserves all old
records and adds each alternate's own three source-supported roots.

The pinned-source trial adds **18** records in **six** blocks. It makes no
claim about omitted full spellings with unsupported internal delimiters or
other conjugations. Five synthetic tests cover both paradigms, quantities,
homographs, private output, no overwrite, missing parts, conflicting records,
flags, ambiguity, voice, notation-only variants and idempotence. CI checks
both quantity tiers. Their private output SHA-256 are
`9551c20f9295e51b2662c6035aa2fa970b943a86e42407d697c3bfbdefcb45c1`
and `ee9b8cf20942b1fea6eaa7913bc5a8e8ccddc602dbf74ecf5984805d1bddcaa2`.

A historical-filter check reproduces all **18** alternate roots and their
conjugation tags, ignoring only optional short marks while retaining long marks
and separators. A separate **18**-form principal-part probe passes from **zero**
to **18** forms recognized under the expected source lemmas, with **51** such
verbal readings. Its private before/after dossier SHA-256 are
`5ffb1b1790daad20011f251c2a7aa46fa7b8c0de640837b5aa52ef97cf67575e`
and `4519cc8b6d49d462e3600ccdbb320094c2ba454171903c19235103ce62651da0`.
The letters-only native verbal index and sidecar SHA-256 are
`862407c19591a0c6ac286a3600da26cebbe0088efdc56f57b74636557c97bc21`
and `f093d0535e029e8122969b28f6ff293b74264b50590ea0437dc61f9d1200b3b7`.

The all-quantity build has the same native verbal index and sidecar hashes;
nominal indexes remain unchanged. The complete **1,033,579**-form pass
recognizes **843,126** forms with **2,093,413** readings. Its identical-root
control has zero differences and zero errors. Relative to the preceding
duplicate-component stage, **350** forms become recognized, none becomes
absent, and all **630** changed analysis counts increase. All **350** newly
recognized forms independently return their expected source verbal lemmas,
with **588** readings and no other lemma/POS readings; private dossier SHA-256
`cde259ce894cb696e432f0fb7a61bf05ad596bcc73d118cef26c90d2dbdb5e08`.
All three complete comparison passes have zero API errors.

Against the controlled rebuilt baseline, the recognition cells are **826,058**
both, **11,932** baseline only, **17,068** candidate only and **178,521** neither.
The remaining loss dossier has **20,932** baseline readings in **1,030** lemma
groups: **633** exact source joins, **15** notation joins, **19** native-preverb
base review leads and **363** unresolved groups. Its private SHA-256 is
`eee5deda2e35cb824661dff8792c7e4eadad8746ec8879d05be82ff341f711dc`.
The earlier **488** first-repair losses remain absent with zero API errors.
The original **15,255**-form loss subset recognizes **3,773** forms with
**7,209** readings and zero API errors. Coverage improvements do not resolve
the remaining lexical decisions or qualify a production replacement.

### Unhandled combined fourth-conjugation headers

Two separate stages recover exact source headers with combined perfects,
with and without an explicit fourth part. They add **eight** and **six** stem
records, recover **218** LISTALL forms without new recognition losses and add
**1,164** readings. The final runtime recognizes **843,344** forms with
**2,094,577** readings. Of the newly recognized forms, **164** have direct
source-lemma readings and **54** have native-prefix readings requiring separate
paradigm-inheritance review. Complete source rules, controls, recorded-feature
comparisons, grammar probes, remaining losses and private dossier hashes are
in [latin-combined-fourth-qualification.md](latin-combined-fourth-qualification.md).

`tools/audit-latin-listall.py` implements that literal recognition pass for
an extracted **plain ASCII, one-form-per-line** wordlist. It accepts an
explicit native library and two stemlib roots, checks duplicate and blank
lines, and emits the input SHA-256, four recognition cells, status pairs,
analysis-row totals and changed-count totals (report schema 2).
It does not fold case or change orthography. A private per-form JSONL can be
requested for subsequent grouping; it refuses existing files and any output
inside the repository:

First run an identical-root control for each runtime. `--require-identical`
requires the same resolved root on both sides and refuses any API error or
count mismatch, without printing the affected lexical form:

```sh
python3 tools/audit-latin-listall.py \
  --forms /private/LISTALL.TXT --library /private/libmorpheus.so \
  --curated /private/curated-runtime --rebuilt /private/curated-runtime \
  --require-identical
```

Three synthetic auditor tests check differential cells, literal deduplication,
private output and fail-closed identical-root controls. Then run the
different-root comparison:

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
the same curated root on both sides. The pinned wordlist and full curated
coverage pass above are now complete; a full differential pass requires a
valid privately reconstructed Latin runtime.

The source-recovered nominal output initially has **51 untyped records**.
`tools/transfer-lexical-record-corrections.py` transfers only already-reviewed
corrections whose original record bytes and current lemma match exactly;
it does not alias unknown classes globally. **44** candidate records match,
leaving seven untyped records. Three synthetic tests cover exact matching,
stale sources, invalid replacements, private boundaries and no overwrite.
Five additional private, source-linked provisional decisions leave **two**
untyped records from two compound-headword articles. They do not constitute
a complete valid nominal index: the projection loses part of that compound
headword, so changing only the class would incorrectly legitimize a truncated
lemma. No automatic class substitution or deletion is accepted here.

A subsequent source-only trial, `tools/recover-latin-compound-headwords.py`,
restores **104** first orthographies explicitly marked `extent="full"` whose
hyphen-separated components were lost by taking only the first space-delimited
token. Only spaces adjoining component hyphens are removed; quantity marks
and component hyphens remain. Plain multiword or partial orthographies are
not expanded, alternative spellings are not inherited, and no witness
inventory selects a header. Source keys remain metadata: a numeric homograph
suffix is retained only when its base spells the same complete compound.
Three synthetic tests cover source mismatch, scope, homograph suffixes,
stream validation, private boundaries and no overwrite. The research workflow
runs this as a separate trial, without replacing the earlier 630-header trial.

The partition counts remain unchanged. Raw nominal records are **40,319**,
with **33,004** shared witness lemmas and **31,323** exact shared record
multisets. Raw verbal records remain **10,398**, with **6,700** shared lemmas,
**6,507** exact shared multisets and **73** witness-only lemmas (111 before
compound recovery). These are literal-stem diagnostics, not analyzer
equivalence. Private header and stream SHA-256 are
`85658956fa68024d032f944f7920d38fa8b424318be6454eebdb6bd74c76cc34`
and `feb65431b6bd78eddb349e5807727aaa0b3fef5fa20806db43bc088877f0ce82`;
raw nominal and verbal SHA-256 are
`210760edb2f3f8a841b28a3c790f6da3e8b5782623561ecdefdfd89f9d8e7c65`
and `22196e561a802c607249597b767652b3c0f9ad797b3155a22ec11c61875c8479`.

The exact reviewed transfer still matches **44** records. Reapplying the
five provisional source decisions above gives **40,314 typed nominal
records**, zero untyped records, and successfully builds a complete nominal
index. The complete compound-recovered verbal index also builds successfully.
The private full runtime is only an experimental candidate: a **104**-form
dictionary-spelling probe recognizes **99** forms and the exact expected lemma
for **95**, on both the curated and experimental roots, with zero API errors.
The other nine expected-lemma cases and full paradigms remain unqualified;
successful index construction does not resolve them. The private nominal
decision output SHA-256 is
`0498c0770095c3a607e786110caa8d500170dc55983d9be1fab40e8f7641bdcd`.

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

### Complete long-mark generation and analyzer qualification

The provisional consolidated decisions were applied in a private copy of
the corrected complete Greek nominal baseline. Exactly **28** records
changed: 24 candidate long marks supported by `<itype>`, three positional
relocations, and one duplicate mark removed. The source corrections and
entity constraints were retained; no public stem source was changed.
The complete decision input SHA-256 is
`a2ef91ad4755bf9f7e7ef69fed452cc8c0d8c0c1358f8c5f23c8653e8fc64e69`.

Generation indexes contained all source blocks for the **314** selected
lemmes, including other records in those blocks. Every lemma generated
forms. Both variants produced **15,880** rows with the same per-lemma
grammatical multisets and the same letter-only forms; quantity display
changed for 28 lemmes. The private baseline and decision source SHA-256
are `6f9cbf18077e955b2d4cb0c4649d8b71277832aa7ca86bcc049f719b32fe19f2`
and `81f35865ea921a557512a2f165f3013525f903614df4a2edbdc8494658be6b65`.
Their generated TSV SHA-256 are
`a59f9f7190890ae64fa952a4dcc6bf9ae2aa3933907133862e78af470bd71eeb`
and `2826b2d420b1db14c313f32edb43e7d6e40c48f101ba0bd9d44dfc65f9a6eeaa`.

The union supplied **13,634** literal query surfaces after removing only
quantity marks (SHA-256
`d9a185c70d7a6e4057cec92426184b08b8fd1f94655076bf2a44bfa5de56beb2`).
Against the two complete nominal indexes:

| Lookup | Baseline recognized | Decision recognized | Baseline XML rows | Decision XML rows |
| --- | ---: | ---: | ---: | ---: |
| `cruncher -S -n -T` | 13,634 | 13,634 | 20,031 | 20,031 |
| `cruncher -S -T` | 13,616 | 13,618 | 16,648 | 16,647 |

Accent-insensitive lookup preserves every per-surface reading-kind, lemma
and grammatical multiset; 644 surfaces change display and 12,990 are
identical. Accent-sensitive lookup gains 18 surfaces, loses 16, changes
seven shared reading multisets and 603 displays, leaving 12,990 identical.
The three relocations account for three gains and four reading changes;
the 24 `<itype>` decisions account for 15 gains, 16 losses and three reading
changes. Deduplication changes 22 displays without changing recognition or
readings. The private relaxed and strict difference ledger SHA-256 are
`6b5c13e52bdb2f653b3492ca28f92aaa8b9acda54cc2ef679111d88b6065f90c`
and `af123da60b9cd651256534ea7788b128bebc44765ee14339b2f2279fed83cebf`.

A union surface can be recognized only through an unrelated homograph:
two such strict-lookup cases occur on the baseline side and one on the
decision side. These surfaces are generated only by the other variant.
Checking each variant against its **own** generated surfaces avoids
mistaking these homographs for coverage. All 13,619 baseline and 13,621
decision expected surface/lemma pairs are covered with accents enabled,
and also with accents disabled. No own generated surface is absent or
recognized only through another lemma. These are controlled generator and
analyzer consistency checks, not evidence of attestation or full equivalence
between the two accent-sensitive corpora.

`tools/audit-greek-generated-coverage.py` reproduces expected-lemma coverage
from a saved generation TSV and `cruncher -T` stdout. The TSV has `LEMMA`
headers and rows containing surface, lemma and nine comma-separated integer
grammatical fields; its tabs are literal separators. Quantity marks alone
are removed for lookup. It validates the row/header relationship, rejects
malformed generation records and missing query surfaces, and separately
counts missing lemma pairs, absent surfaces, unrelated homographs and
partial coverage. It prints aggregate counts and input digests only.

```sh
python3 tools/audit-greek-generated-coverage.py \
  --generated /private/greek-generated.tsv \
  --forms /private/greek-union-surfaces.txt \
  --analysis /private/greek-strict.analysis
```

### Wider verbal quantity qualification

The same controlled approach now covers the **31** verbal quantity groups:
20 witness short marks and 11 witness long marks. Two complete private
Greek verb inputs were assembled from the ordered lexical manifest, with
the eight recorded verbal-source corrections applied before conjugation.
One preserves quantity; the other substitutes just the 31 unmarked candidate
records. Their SHA-256 are
`751d6d5adc057e397f13d08dea13afde06ad3e0f1faba16969df05017f93d0f2`
and `44d6d0225713e966f5a7776fe55b860227183377a4a37746869fc55fcf8a2ff7`.
Both were expanded with the same native `do_conj` and indexed with
`indexvbs`; the nominal runtime was held constant. This compares two
reconstructed verb indexes, not a reconstructed index against the bundled
historical one.

The selected source blocks were expanded with the supported generation
source preparer before constructing the generation indexes. Every one of
the 31 lemmes generated forms. Both variants yielded **14,876** rows with
identical per-lemma grammatical multisets, letter forms and accents; only
quantity notation differs. The prepared-source SHA-256 are
`7f8685a0ea005afb3705939a5027bff2d2eff79d7e035f35e2e8e9ebd1e8717b`
and `92eba749e3ec82660fef2741049c85aaaa666ee685a3f7a63b5536a022284615`.
The generated-output SHA-256 are
`a68c6a8bd19c5afe5d27ebbc0ff0a3c871803cd94b798efe87fa6185f378b9db`
and `bc16922d68c1e50d66ef1bf8e3f1be141c91d9275a27129f3aafc121f4dcb245`.

Removing only quantity marks supplied **11,563** distinct surfaces
(SHA-256 `342f6c91d788f51be74f628f03d9cb5d33676a959c68e0c256287840d859be5c`).
Both complete indexes recognized every surface under the expected lemma,
with no homograph-only or partially covered generated surfaces. With
`cruncher -S -T`, both have 20,807 XML reading rows; with `-S -n -T`, both
have 24,040. Every per-surface reading-kind, lemma and grammatical multiset
matches in each comparison. In both modes 3,901 surfaces differ only in
quantity display and 7,662 have identical outputs. The strict and relaxed
private difference ledger SHA-256 are
`e085592c82195c53b1a903ef56fe74623debc9eaaa45c70e282111479ee016ca`
and `4a2d34b9487f30a3f197ac7715cc5c1389a7c04738de31bb8e33bebc7eba8494`.

The existing source-join tool also recovered **11** single-entry matches
for the long-mark groups (private source-review SHA-256
`815af3fc311a4d75ad72d45fd1cf6657d94037d61e8c818bf737bb17ca97c38f`).
Four are positionally unambiguous under the direct bare-pron rule and one
under the contextual-pron rule. Six require individual review: three are
localized by excluding second letters of diphthongs, two by explicitly
inspecting the nested pronunciation of a matching quoted inflected form,
and one by comparing the iridescent sense with the rainbow component's
circumflex and a related explicitly quantity-marked compound. These
individual semantic and quote relationships do not become automatic rules.
All 11 provisionally retain the witness's long position. The six explicit
reviews and the complete verbal decision ledger have SHA-256
`728130ed73f2021866aa8a98f6639b25f7a0bf503b7dd05afd4554ebceca4a8d`
and `adb0f75aa7d902edb21aa45d61cea006ed779158dfbd31a41921cc28f7f835c1`.
Analyzer equivalence of the unmarked counterfactual does not justify
removing source-backed vowel quantities or establish historical attestation.

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

`tools/consolidate-greek-quantity-review.py` overlays explicit individual
reviews onto this same source queue, without changing stem records or
inferring judgments. Each private review supplies `lemma`, `source_ids`
(in source order), `source_row_sha256` (the exact JSONL row including its
line ending), a nonempty `evidence` note, `disposition`, and a zero-based
letter-only `long_position`. Supported dispositions are
`retain_witness_position`, `relocate_witness_long`, and
`deduplicate_witness_long`, and
`deduplicate_witness_long_from_source_circumflex`. Reviews may address only the automatic
`manual_review` queue. Stale source bindings, duplicate or unknown lemmas,
invalid positions and inconsistent quantity marks are rejected before any
output is written. Individual decisions remain explicitly provisional.

```sh
python3 tools/consolidate-greek-quantity-review.py \
  --source-review /private/greek-long-source-review.jsonl \
  --reviews /private/greek-explicit-quantity-reviews.jsonl \
  --private-output /private/greek-consolidated-quantity-decisions.jsonl \
  --expected 314
```

The consolidated private ledger contains all **314** source rows: 287
unchanged automatic dispositions and 27 explicit individual reviews.
The latter comprise 23 retained witness positions, three relocations and
one deduplication. **26** individual positions are provisionally resolved.
The deduplication case has `position_resolved: false`: removing a repeated
underscore does not establish which repeated vowel the source intended.
Thus an empty unreviewed queue does not mean every long position is settled.
The exact source, explicit-review and consolidated-ledger SHA-256 digests
are respectively
`12afa846e12ab7c8f830d615f104efc2f1548695866106048eb6b0cc8da76423`,
`e2b3bf2759b620ccc9852ef9d855fa39ca3c787a91b9a8f783f98f98ee0f8122`,
and `df0085cc7c768dddc2ae8181577afcc12200785256452d0639692200bc1e34d7`.
The output is a new owner-only file outside the repository; only aggregate
counts and digests are printed. Synthetic tests check binding failures,
review boundaries, multiplicity versus position, and private output rules.

A subsequent source check resolved the deduplication case's position
individually: the pinned first `<orth>` has a circumflex on the marked
monophthong. [Smyth §147a](https://www.ccel.org/s/smyth/grammar/html/smyth_1e_uni.htm)
establishes that a dichronon bearing circumflex is long. This evidence is
independent of the ambiguous bare `<pron>`. The new disposition
`deduplicate_witness_long_from_source_circumflex` requires one matched
source, matching initial stem letters, exactly one source circumflex at
the selected position, no explicit short mark there, and no preceding
vowel. The last conservative check avoids treating a circumflex on a
diphthong as proof of a long second vowel; hiatus is not inferred.
This adds no automatic selection rule and changes no stem source.

The revised private ledger therefore has **27** provisional individual
positions and zero multiplicity-only judgments. Its explicit-review and
ledger SHA-256 digests are
`db52d7850a8d9cd9725f63f5e689160345aef81e9724f863f4620b2198a3a670`
and `f64835561a8fe88ba8f6a697e7a4bde6c6e8539e7700d1c198f122fa977e68ad`.
The previous ledger remains a recorded intermediate result. Four synthetic
tests now include rejection of misplaced or repeated circumflexes,
contradictory short marks, and diphthong positions.

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

Further opt-in alternate stages and their independent principal-form checks
are recorded in [latin-complete-alternate-qualification.md](latin-complete-alternate-qualification.md).

The latest complete present-system comparisons are automated in
[latin-present-replay-qualification.md](latin-present-replay-qualification.md).
They use the controlled rebuilt nominal witness, excluding the five private
nominal decisions in earlier research runtimes. Their aggregate totals form
a separate measurement series; they do not replace or reproduce those
earlier nominal candidates.

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
individual lexical and analyzer qualification. The 1,410 nominal quantity
groups have now been triaged: 1,096 short-only cases preserve the controlled
complete index, while all 314 long-mark cases have provisional source-backed
decisions and the generation/analyzer checks recorded above. Their
accent-sensitive corpora are not equivalent. The 31 verbal quantity groups now have complete generated-form coverage
and equal grammatical signatures in the controlled comparison, as recorded
above; their long marks have source-backed retention decisions. The Latin
trial still lacks the historical `vtags` selector. Its baseline leaves 393
verbal-only witness entries nominal, while the separate source-recovery
trial leaves ten reviewed cross-references and increases exact verbal
record matches. Those links do not yet establish inherited paradigms. Analyzer regression fixtures and the 2007 Hopper
oracles can qualify a selected candidate corpus only after these choices are resolved
and a complete private stemlib is built. Corpus publication also remains
subject to the separate rights decision in
[stemlib-redistribution.md](stemlib-redistribution.md).
