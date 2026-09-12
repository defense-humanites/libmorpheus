<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Stemlib production source manifest

`tools/stemlib-source-manifest.tsv` freezes the first reproducible-production
input boundary for Greek and Latin ending, ending-macro, and derivation tables.
Each row has five tab-separated fields:

| Field | Meaning |
| --- | --- |
| `language` | `Greek` or `Latin` |
| `status` | `active` or `excluded` |
| `kind` | `rule`, `ending-basic`, `ending` or `derivation` |
| `path` | Language-relative source path |
| `sha256` | Digest of the exact committed input bytes |

All `rule_files/*.table`, `endtables/basics/*.end`,
`endtables/source/*.end` and `derivs/source/*.deriv` files must occur exactly
once. Rules and ending macros are always active.
An ending or derivation is active when the curated tree contains its compiled
`.out` baseline; this preserves the effective historical selection without
pretending that every registry entry is buildable. A new or removed file, a
digest change, a missing active baseline, or a compiled baseline for an
excluded source fails CI until the manifest and its review evidence change
together.

The twelve explicit Greek exclusions are:

- endings: `conj3`, `conj3io`, `conj4`, `is_ios`, `us_uos2`, `verb_adj`, and
  `vh_vhs`;
- derivations: `cw`, `es_denom`, `ow_fact`, `ow_instr`, and `ww`.

Latin currently has no source-file exclusions in these two groups. This does
not resolve the separate Latin registry entries whose source tables are absent;
they remain an audited corpus gap and must not be silently synthesized.

The table manifest is intentionally narrower than the complete stemlib build
receipts. It selects table inputs but not lexical `stemsrc/` inputs; the
separate lexical manifest supplies that layer. Production receipts and
provenance records connect both manifests to their producers and regenerated
outputs.

## Isolated source staging

`tools/stage-stemlib-sources.cmake` validates the complete manifest before it
writes anything. It rejects a destination inside the source stemlib and rejects
any destination that already exists. For one requested language it then:

1. creates fresh rule, ending, and derivation directories;
2. copies every active input and verifies its staged SHA-256;
3. emits the active subset as `MORPHEUS-STEMLIB-INPUTS.tsv`;
4. emits ordered `ending-tables.list` and `derivation-tables.list` producer
   inputs, plus `derivation-index-tables.list` for the active tables classified
   as `reg_deriv` by the pinned registry.

CI stages Greek and Latin twice into independent directories, revalidates every
copied digest, compares the four metadata files, checks representative
exclusions, and verifies that an existing destination is refused. The stager
does not use global temporary paths and never overlays a prior distribution.

## Table production

`tools/build-stemlib-tables.cmake` consumes a fresh staging destination and the
two ordered lists. It runs `buildend` and `buildderiv` once for every active
table, then builds the nominal, verb, and derivation indexes from those same
lists. Derivation expansion includes all active derivation tables, while its
index is limited to the 18 Greek and two Latin `reg_deriv` tables selected from
the pinned registry. The list-driven index mode filters nominal and verb tables by their
registered stem class, rejects malformed or unknown names, and never treats an
unlisted registry entry as an implicit input.

This is a single-pass explicit dependency graph, not the inherited makefile's
undocumented two-pass iteration. Table sources produce tables, rebuilt
irregular sources and the complete table stage feed lexical assembly, and the
stem indexes are terminal outputs. No generated index feeds a producer input.
Each labeled producer may run only once; duplicate labels are fatal. Two fresh
executions then provide the independent reproducibility proof rather than a
second mutation of one staging tree.

Every producer runs with `LC_ALL=C`, `LANG=C`, `TZ=UTC`, and `MORPHLIB` fixed to
the staging root. Successful completion emits
`MORPHEUS-STEMLIB-TABLE-OUTPUTS.tsv`, containing the sorted output paths and
their SHA-256 digests. The receipt covers expanded ASCII and binary tables plus
their three text indexes. Its companion table-provenance record identifies the
configured source revision and C toolchain.

CI performs two complete clean table builds for each language. It requires the
two receipts and every received output to be byte-identical, then compares all
568 regenerated files with the checked-in Greek and Latin table baselines.
Textual expansions and indexes must match byte for byte. Binary `.out`
differences are counted separately because the restored writer uses the
qualified explicit serialization rather than historical in-memory structure
bytes. CI prints a compact TSV summary of the comparison. This comparison
covers table production only; stem indexes remain outside this phase.

The current comparison records 156 Greek and 73 Latin binary differences, with
zero textual or index differences. Their complete sorted path set is pinned in
`test/stemlib-binary-baseline-exceptions.tsv`; CI rejects a missing, unexpected,
duplicated, reordered, malformed, or reclassified exception.

## Lexical production and qualification

`tools/stemlib-lexical-manifest.tsv` adds an ordered lexical boundary without
changing the 379-source table manifest. It inventories every file below both
`stemsrc/` trees, pins selected inputs and exclusions by SHA-256, and declares
Latin `stemsrc/vbs.mpi` as `unavailable`. The prepared `nom.irreg` and
`vbs.irreg` files are pinned comparison baselines; their `irreg.nom.src` and
`irreg.vbs.src` inputs are expanded afresh inside every complete staging.

The lexical manifest has four tab-separated fields: `language`, `role`, `path`,
and `sha256`. In addition to `nominal`, `verb`, `constraints`,
`constraint-tool`, `assembly-baseline`, `excluded`, and `unavailable`, four
irregular source/baseline roles identify exactly one nominal and one verbal pair
per language. Nominal and verb rows, including each irregular baseline's
position, define concatenation order. Greek nominal preparation uses the pinned
`addconstraints.pl` and entity-name input. The historical Latin perfect-stem
substitution is retained. Although `vbs.mpi` is absent, the available ordered
inputs reproduce the same `conjfile` lemma sequence and per-lemma record
multisets; the recipe verifies that notice-level equivalence before continuing.
An inventory, digest, baseline or unavailable-file change fails validation.

Configure the internal tools and build both complete distributions with:

```sh
cmake --preset dev -DMORPHEUS_BUILD_STEMLIB_TOOLS=ON
cmake --build --preset dev --target morpheus_stemlib_production
```

The opt-in target deletes only its two prior build-tree destinations, then
creates fresh `stemlib-production/greek` and `stemlib-production/latin` stages.
The language-specific targets remain available independently. The orchestrator
and lower-level recipes reject direct reuse of an existing stage. Python 3 and
Perl are build-time dependencies only. The recipe verifies staged table inputs
and outputs, copies and verifies selected lexical sources, fixes the locale,
timezone and `MORPHLIB`, and invokes `indexnoms`, `do_conj`, and `indexvbs` with
explicit paths after two `buildword` expansions.
`lexical/inputs.tsv`, per-producer diagnostics
and `lexical/comparison.json` remain available when a corpus blocks production.
A sorted `MORPHEUS-STEMLIB-LEXICAL-COMPARISON.tsv` is also written after every
attempt. It records output and baseline digests with an identical, different or
unavailable classification, without implying that the complete build passed.
A successful complete-corpus run emits
`MORPHEUS-STEMLIB-LEXICAL-OUTPUTS.tsv` covering both rebuilt irregular files,
the four stem-index files, verb expansion, and odd-key output. Fixture receipts
remain limited to their six applicable outputs. No success receipt is written
after a failed or blocked producer. Baseline comparisons explicitly distinguish
identical, different, and unavailable references.

Every successful fixture or complete-corpus run also emits the schema 2
`MORPHEUS-STEMLIB-PRODUCTION-RECEIPT.json`. This deterministic aggregate receipt
contains the source revision, fixed environment, compiler identity, ordered
table and lexical input digests, every table and lexical output digest, and the
digests of both provenance records. It also declares the single-pass execution
model and one table and lexical pass. It is absent after any failed producer.
CTest verifies every received output against it and compares receipts from the
two independent builds byte for byte.

After the two CTest builds and one execution of the production target, CI
validates and emits `stemlib-qualification.json`. This schema 1 report binds the
common source revision, qualification profile and execution model to both
language receipts. It records table and lexical output counts, reviewed
Perseids difference-manifest hashes and the complete pinned Alpheios comparison
summary. It is written only when the independent CTest receipts match each
other, both match the production target, and all comparison counts and
exception sets retain their reviewed values. CI preserves
the report, receipts, provenance and comparison tables as one revision-named
artifact for 30 days. Stale evidence is rejected when its recorded revision and
tracked dirty state do not match the source tree being qualified.

`MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv` schema 4 records the configured Git
revision (or `unavailable` outside a Git checkout), marks tracked modifications
with `+dirty`, and identifies the compiler by name, CMake ID, version and
executable SHA-256. It also records the target system and processor, plus
SHA-256 identities for the table manifest, validator, staging and table-build
recipes, the top-level distribution orchestrator, four producer executables
and CMake executable. Invalid metadata is rejected before staging.

The reference CI qualification uses the explicit
`github-ubuntu-24.04-gcc-14-python-3.12-perl-5.38` profile. Configuration fails
closed unless the runner is Linux x86-64 and the configured compiler and
interpreters have those major/minor versions. Local and portability builds use
the `portable` profile by default; both profiles are recorded in table, lexical
and aggregate production provenance.

The lexical recipe requires this record and writes schema 2
`lexical/provenance.json` before invoking producers. It verifies and carries
forward the source/toolchain identity, then identifies the lexical manifest,
staged input and table-output receipts, table provenance, recipe, four native
tools, Python executable/version and, when used, the Perl executable. Neither
record contains absolute build paths or timestamps, so two clean builds with
the same inputs and executables can compare them directly. Records survive
corpus failures and are not success receipts. They do not identify every
dynamic library or the complete operating-system environment used to build and
run the executables.

The restored `do_conj` uses the historical binary derivation reader. Short mode
expands the implicit present stem of regular derivations while preserving the
historical handling of `@` continuations; this is the only combination that
matches the committed Latin verbal index outside the corrected records. Its
internal CLI is:

```text
do_conj [-I|-L] [-f] INPUT EXPANDED_OUTPUT ODD_KEY_OUTPUT
```

Outputs must not exist. The tool removes its owned outputs on failure. Missing
or truncated tables, oversized fields, invalid requests and unmatched
principal parts are fatal instead of embedding `errorN: nothing found` in an
apparently successful lexical output. The restored code also fixes undefined
returns, missing commas in the principal-part list and two ineffective newline
tests. None of these tools is installed or used by runtime releases.

CTest now takes two independent table builds per language, runs the lexical
chain on small Greek and Latin fixtures, and verifies all twelve output hashes
against `test/stemlib-lexical/outputs.tsv`. The Greek fixture expands present,
future and aorist stems; the Latin fixture also checks that an indexed
derivation need not carry an inflectional stem type. Existing output files,
failed expansions, malformed inputs and missing dependencies are exercised.

The same test independently stages the complete committed corpora twice and
verifies the following status:

| Producer | Corpus | Status |
| --- | --- | --- |
| `buildword` | Greek and Latin | Complete; all four prepared irregular files are rebuilt reproducibly from their source forms before indexing. |
| `indexnoms` | Greek | Complete; the regenerated nominal indexes are reproducible and their reviewed baseline differences are pinned. |
| `indexnoms` | Latin | Complete; verified staging corrections resolve or quarantine every formerly rejected record, and the regenerated indexes are reproducible with pinned baseline differences. |
| `do_conj` and `indexvbs` | Greek | Complete; the expanded verbs, odd keys and regenerated indexes are reproducible and their reviewed baseline differences are pinned. |
| Verb-source assembly | Latin | `vbs.mpi` is absent, but the available ordered inputs reproduce the same lemma sequence and per-lemma record multisets as `conjfile`; only equivalent record ordering differs. |

The complete Greek stage is additionally compared with every runtime artifact
in the pinned Alpheios distribution's `derivs/indices`, `endtables/indices`,
`endtables/out`, and `steminds` directories. All 143 Alpheios paths occur in the
reconstruction, which additionally produces `as_a.out`, `eas_ea.out`, and
`hs_entos.out`. The comparison currently records two identical ending tables
(`ewn_ewnos.out` and `oeis_oentos.out`), 141 differences, and three outputs with
no Alpheios reference. CI
emits `alpheios-reference-comparison.tsv` with both SHA-256 digests for every
path and the verified Alpheios revision, rejects tracked submodule changes, and
requires the two clean builds to produce the same report. These
differences reflect distinct source snapshots and serialization histories; the
report does not classify them as acceptable replacements for Alpheios data.

The correction manifest leaves the historical source snapshots unchanged and
applies every replacement only after their original line numbers and SHA-256
digests have been verified in staging. Three bare `@` records in the Greek
irregular verb source name no ending table and are explicitly disabled in the
staging copy. The rebuilt `vbs.irreg` then matches its baseline byte for byte.
Both rebuilt Latin irregular files contain exactly the same line multisets as
their baselines, with only producer ordering differences. The rebuilt Greek
`nom.irreg` has six removed and five added lines due to current accent handling;
all three differing prepared paths are pinned baseline exceptions.

The Greek nominal repair replaces eight
malformed type names with existing registered paradigms, affecting 42 prepared
notices. Two additional source defects have direct structural evidence:
`*seouh=ros` receives `os_ou`, and the orphan `:no:*kei=os` starts its own
lemma. Fourteen source entries that
depend on an absent paradigm (`er_ros`, `kleos_klehs`, `pais_paidos` or the
unregistered `is_ios`) or contain no stem are explicitly marked
`#noanalysis`; no replacement inflection was synthesized. The rebuilt text
index has exactly 61 removed and 49 added lines after consuming the rebuilt
irregular snapshot. Its `nomind` and
`nomind.lindex` differences are pinned in
`test/stemlib-lexical-baseline-exceptions.tsv` as corrected Greek nominal
records.

The Latin nominal corrections cover all 154 affected source lines without
editing the historical snapshots. Sixty-two records use registered paradigms
supported by exact duplicates, nearby valid records or direct type-name
correspondence. Ninety records whose Greek-style or otherwise ambiguous types
have no qualified Latin replacement are marked `#noanalysis-stem`; this group
includes six empty-stem records. Two malformed boundaries in `nom.livy` are
repaired by changing an orphan `:le:` to `:no:` and an orphan `:no:` to `:le:`.
The rebuilt Latin nominal text index has exactly 152 removed and 86 added lines.
Its `nomind` and `nomind.lindex` differences are pinned in
`test/stemlib-lexical-baseline-exceptions.tsv`.

The same manifest handles eight Greek verbal source defects. Six explicit
requests that the historical expander could not satisfy are marked as invalid
derivations in staging, preserving the fact that they produced no indexed
stem. The empty-stem `e/w` and `i/zomai` derivations are replaced by explicit
`:vs:` records for the exact `ewpr` and `iz` stems present in the historical
index. This removes implicit empty-stem behavior without inventing a new
derivation. The current ordered source set rebuilds `vbind` with exactly 18,618
baseline lines removed and 262 added; its odd-key output removes two baseline
lines and adds none. Those three changed paths and both indexes are pinned as
reviewed exceptions. The expanded source has no committed baseline.

The Latin verb chain now completes. Seven malformed records were repaired from
structural or historical evidence: five `:vs:`/`:de:` or stem-type typos in
`vbs.latin.bas`, an empty `:vs:` in `irreg.vbs.src`, and a missing `irreg_pp1`
type on the `prosum` future macro. The `explico` correction restores its
pre-2006 `:vs:explicu perfstem` form. The generated `vbs.irreg` and assembled
`conjfile` were updated from those sources. Against the committed Latin verbal
baseline, the rebuilt text index has exactly 13 removed and 14 added lines;
the changed `vbind` and `vbind.lindex` paths are pinned in
`test/stemlib-lexical-baseline-exceptions.tsv`. All differences correspond to
the seven repairs, including reclassification of the six `prosum` future forms
from untyped words to `irreg_pp1` verbs. The odd-key output remains byte-identical.
The 229 table-binary exceptions remain intact.

### Locating additional lexical refusals

`tools/audit-stemlib-lexical.py` diagnoses a prepared input using the restored
producer and a stage whose table inputs and outputs pass checksum verification:

```sh
python3 tools/audit-stemlib-lexical.py \
  --stage /absolute/path/to/greek-stage --language Greek \
  --input /absolute/path/to/greek-stage/Greek/lexical/nominal.input \
  --tool build/dev/indexnoms --producer indexnoms \
  --output /absolute/path/to/nominal-audit.json
```

For Greek expansion, select `--producer do_conj`, `build/dev/do_conj` and
`lexical/verb.input`. `indexvbs` can similarly inspect an already expanded input.
The Latin recipe continues only when the available verb assembly matches the
pinned historical baseline exactly or has the same ordered lemmas and per-lemma
record multisets despite the declared absent `vbs.mpi`.

The audit first runs the complete input, then bisects failing batches at lemma
boundaries. It records isolated refusals with one-based record and prepared-input
line numbers, lemma and stderr. Successful temporary outputs are discarded;
neither staged indexes nor production success receipts are created. Exit status
is 0 when the original batch succeeds, 1 when it fails, and 2 for an audit error.
An existing report is preserved. Reports identify the input, tool, audit recipe
and staged table receipts by SHA-256.

`test/stemlib-lexical/blockers.json` now has an empty `reports` list because all
four complete nominal and verbal inputs succeed. CTest verifies each language's
eight reproducible complete-corpus outputs and exact baseline-difference counts
instead.

The former audit counts below describe notices, not unique lemmas or
philological corrections.
Only the first failure inside each isolated notice is reported. In particular,
two Latin notices yield no stem records in isolation, although an empty notice
need not prevent an aggregate build. Successful batches are not subdivided, so
the audit does not enumerate all empty notices. Cross-notice interactions may
also change after splitting; failures that disappear in both immediate halves
are recorded separately (none observed here). This historical inventory is not
exhaustive semantic validation or an exception list authorizing partial
production; it is no longer an active blocker expectation.

### Greek verb correction qualification

The eight formerly isolated Greek expansion refusals have the following causes
in the committed inputs and matching ASCII derivation tables. Paths below are
relative to `stemlib/Greek/`; line references identify the original sources,
not the concatenated input.

| Lemma | Source | Request and observed incompatibility |
| --- | --- | --- |
| `bibrw/skw` | `stemsrc/vbs.simp.ml`, lemma at 3456 | `vn,-mm,h_hs` selects `mm`; `derivs/ascii/o_stem.asc` has `wm h_hs` (line 31). |
| `ka/mnw` | `stemsrc/vbs.simp.ml`, lemma at 10010 | `vn,-h,s_tos` has no corresponding nominal rule in `a_stem.asc`; its nominal `wn_on` rules use `a_m` or `hm` (67–69). |
| `pi/mplhmi` | `stemsrc/vbs.simp.ml`, lemma at 16938 | `va,-ht os_h_on` combines a suffix and type not present together: `ht os_on` is at line 59 of `a_stem.asc`, whereas `os_h_on` uses `a^t` (66). |
| `r(h/gnumi` | `stemsrc/vbs.simp.ml`, lemma at 18232 | `vs,hs_es` uses an unregistered principal-part name, `vs`. |
| `stei/bw` | `stemsrc/vbs.simp.ml`, lemma at 19390 | `vs,-t` has the same unregistered principal-part name. |
| `te/mnw` | `stemsrc/vbs.simp.ml`, lemma at 20383 | `fp,-h` selects `h`; the future-perfect rules in `a_stem.asc` use `a_s`, `hs`, `a_c` or `hc` (53–57). |
| `e/w` | `stemsrc/lsj.vbs`, lemma at 27328 | `:de: ew_denom` has no stem before the derivation name. |
| `i/zomai` | `stemsrc/lsj.vbs`, lemma at 31798 | `:de: izw mp` likewise has an empty stem. |

Nearby rules explain the mismatches but do not justify alternative
philological forms. The six unmatched requests are therefore disabled only in
the verified staging copy. The two empty-stem cases use explicit records for
the exact stems already present in the committed historical index.

The two `vs` requests also exposed a tool defect: `GetStemClass` returns
`(Stemtype)-1` for an unknown name, but `Stemtype` is unsigned. A positivity
check therefore accepted the sentinel as a class and reported a misleading
unmatched derivation. Both `do_conj` and the independent ASCII derivation
expander now reject this sentinel explicitly. The former reports an unknown
principal part; the latter returns its documented malformed-input result
(`-1`) instead of the no-match result (`0`). Regression tests distinguish these
outcomes from successful expansion and check failed CLI output cleanup.
Regression tests retain the unknown-principal-part distinction and failed CLI
cleanup checks. Existing fixture outputs are unchanged; the Greek corpus now
produces a success receipt instead of a blocker report.

### Nominal refusal diagnosis

The indexer now retains the scanner's unrecognized keys in diagnostics for an
untyped record. If all remaining keys are recognized, it reports that none
provides an inflectional stem type. This affects diagnostics only: unknown
editorial keys alongside a valid type remain accepted, and failed indexing
still produces no output. Both nominal and verbal indexer CLIs exercise these
cases in regression tests.

The pre-correction nominal observations divided as follows:

| Observation on the first failing record in a notice | Greek | Latin |
| --- | ---: | ---: |
| Untyped record with unrecognized keys | 55 | 139 |
| Untyped record with only recognized keys remaining after stem extraction | 9 | 7 |
| No stem records when the notice is isolated | 0 | 2 |
| Total isolated refusals | 64 | 148 |

These are notice counts, including duplicate lemmas and generated constraints.
The second category does not imply that the original record had a well-formed
stem: for example, an empty stem can cause its type token to be consumed as the
stem, leaving only gender or accent keys. It also includes records missing type
annotations. Such cases require inspection of the original notice.

The most frequent unrecognized keys are:

| Corpus | Key or key group | Notices |
| --- | --- | ---: |
| Greek | `gc_ggos` | 27 |
| Greek | `pais_paidos` | 5 |
| Greek | `is_ios` | 4 |
| Greek | Other keys | 19 |
| Latin | `hs_ou` | 57 |
| Latin | `eLr_eLis` | 23 |
| Latin | `0_e` | 14 |
| Latin | `y_pos` | 8 |
| Latin | `c_kos` | 7 |
| Latin | `er_i` | 6 |
| Latin | Other keys or groups | 24 |

The original diagnostics included non-type annotations such as Latin `group`
and `orth`. Unknown keys were not equated automatically with missing
inflectional types; every applied substitution or quarantine is pinned to its
original source-line digest in the correction manifest.

Of the twelve distinct unrecognized Greek keys, only `is_ios` has a same-named
ending source in the committed Greek tree. `endtables/source/is_ios.end` is
explicitly excluded by the table manifest and `is_ios` is absent from the stem
type registry. Its four affected notices therefore cannot be repaired merely
by adding it to a build list: registry and table qualification must be reviewed
together. No same-named ending source exists in the Latin tree for its observed
unknown keys. This filename check is not evidence that a similarly named table
is a valid replacement; ambiguous Latin records were therefore quarantined in
staging rather than assigned a synthesized paradigm.

### Excluded-table producer guard

All twelve excluded Greek table names are also absent from their respective
registries: the seven ending names from `stemtypes.table`, and the five
derivation names from `derivtypes.table`. Every active table name in both
languages is registered. The exclusions therefore involve more than a missing
compiled baseline, including the `is_ios` source used by four nominal notices.

An isolated production probe exposed a false-success path: `buildend` and
`buildderiv` returned success for each excluded source even though the table
name supplied no registered type. The producers now validate the requested
main table's inflectional or derivation type before opening any output file.
An unregistered name produces an explicit error. This does not register a new
type, choose a historical numeric code, or qualify an excluded source.

Regression tests copy all twelve actual excluded sources alongside the
committed Greek registries and ending macros. Each request must fail with the
unregistered-table diagnostic, create no binary or ASCII output, and preserve
pre-existing output sentinels. The ordinary two-build comparison continues to
qualify the active Greek and Latin tables against their unchanged baselines.
