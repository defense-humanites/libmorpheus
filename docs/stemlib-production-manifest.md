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

The manifest is intentionally narrower than a complete stemlib build receipt.
It does not yet select lexical `stemsrc/` inputs, record producer or toolchain
versions, or prove that regenerated outputs match the baselines. The next
stage consumes only active rows into an empty language-scoped staging tree;
later manifests will add nominal and verb sources as their producers are
restored.

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

Every producer runs with `LC_ALL=C`, `LANG=C`, `TZ=UTC`, and `MORPHLIB` fixed to
the staging root. Successful completion emits
`MORPHEUS-STEMLIB-TABLE-OUTPUTS.tsv`, containing the sorted output paths and
their SHA-256 digests. The receipt currently covers expanded ASCII and binary
tables plus their three text indexes; it does not yet contain a compiler
identity or source revision.

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

## Lexical production and explicit blockers

`tools/stemlib-lexical-manifest.tsv` adds an ordered lexical boundary without
changing the 379-source table manifest. It inventories every file below both
`stemsrc/` trees, pins selected inputs and exclusions by SHA-256, and declares
Latin `stemsrc/vbs.mpi` as `unavailable`. Prepared `nom.irreg` and `vbs.irreg`
files are inputs here; regenerating those snapshots from their irregular-word
sources remains a later boundary.

The lexical manifest has four tab-separated fields: `language`, `role`, `path`,
and `sha256`. The roles are `nominal`, `verb`, `constraints`, `constraint-tool`,
`excluded`, and `unavailable` (the last uses `-` instead of a digest). Nominal
and verb rows define concatenation order. Greek nominal preparation uses the
pinned `addconstraints.pl` and entity-name input. The historical Latin perfect
stem substitution is retained, but the missing `vbs.mpi` is never silently
omitted. An inventory, digest or unavailable-file change fails validation.

After `build-stemlib-tables.cmake` completes in a fresh stage, run:

```sh
python3 tools/build-stemlib-lexical.py \
  --source stemlib \
  --manifest tools/stemlib-lexical-manifest.tsv \
  --language Greek --stage /absolute/path/to/greek-stage \
  --tools build/dev
```

Use a separately built Latin stage with `--language Latin`. Python 3 and Perl
are build-time dependencies only. The recipe verifies staged table inputs and
outputs, copies and verifies selected lexical sources, fixes the locale,
timezone and `MORPHLIB`, and invokes `indexnoms`, `do_conj`, and `indexvbs` with
explicit paths. It rejects reuse. `lexical/inputs.tsv`, per-producer diagnostics
and `lexical/comparison.json` remain available when a corpus blocks production.
A successful run emits `MORPHEUS-STEMLIB-LEXICAL-OUTPUTS.tsv` covering the four
stem-index files, verb expansion, and odd-key output. No success receipt is
written after a failed or blocked producer. Baseline comparisons explicitly
distinguish identical, different, and unavailable references.

`MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv` records SHA-256 identities for the
table manifest, validator, staging and production recipes, four producer
executables and CMake executable. The lexical recipe requires this record and
writes `lexical/provenance.json` before invoking producers. It identifies the
lexical manifest, staged input and table-output receipts, table provenance,
recipe, three native tools, Python executable/version and, when used, the Perl
executable. Neither record contains absolute build paths or timestamps, so two
clean builds with the same inputs and executables can compare them directly.
Records survive corpus failures and are not success receipts. These hashes
identify exact files, not their Git ancestry or the compiler, dynamic libraries
and complete operating-system environment used to build/run the executables.

The restored `do_conj` uses the historical binary derivation reader, preserving
its short-conjugation decisions. Its internal CLI is:

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

**Full-corpus qualification remains blocked.** The same test independently
stages the committed corpora and verifies the following first failures, without
adding binary exceptions or rewriting philological data:

| Producer | Corpus | First blocker |
| --- | --- | --- |
| `indexnoms` | Greek | `*glisa=s`: `eas_eantos` is not a registered stem type. |
| `indexnoms` | Latin | `Jeremiah`: `as_a` is not a registered stem type. |
| `do_conj` | Greek | The explicit request `br / o_stem / vn,-mm,h_hs` has no matching derivation rule. |
| Verb-source assembly | Latin | The historical input `stemsrc/vbs.mpi` is absent. |

A separate exploratory run over the available Latin verb files also encounters
`:de:explicu perfstem`, which requests the absent `derivs/out/perfstem.out`.
The supported recipe stops at the missing source and does not bypass it to
claim a qualified verb build. These are first blockers, not an exhaustive
corpus-error inventory. Full lexical baseline comparisons and Git/compiler
provenance remain open; fixture reproducibility does not certify the
complete distribution. The 229 existing table-binary exceptions remain intact.

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
The Latin recipe still refuses to assemble verbs without `vbs.mpi`; the audit
does not supply or omit that missing source.

The audit first runs the complete input, then bisects failing batches at lemma
boundaries. It records isolated refusals with one-based record and prepared-input
line numbers, lemma and stderr. Successful temporary outputs are discarded;
neither staged indexes nor production success receipts are created. Exit status
is 0 when the original batch succeeds, 1 when it fails, and 2 for an audit error.
An existing report is preserved. Reports identify the input, tool, audit recipe
and staged table receipts by SHA-256.

`test/stemlib-lexical/blockers.json` pins these diagnostic observations:

| Prepared input | Lemma records | Isolated refusals |
| --- | ---: | ---: |
| Greek nominal | 107,442 | 64 |
| Latin nominal | 53,403 | 148 |
| Greek verb expansion | 20,324 | 8 |

These counts describe notices, not unique lemmas or philological corrections.
Only the first failure inside each isolated notice is reported. In particular,
two Latin notices yield no stem records in isolation, although an empty notice
need not prevent an aggregate build. Successful batches are not subdivided, so
the audit does not enumerate all empty notices. Cross-notice interactions may
also change after splitting; failures that disappear in both immediate halves
are recorded separately (none observed here). Thus this inventory supplements
the full-corpus failures; it is neither exhaustive semantic validation nor an
exception list authorizing partial production. CTest checks its input hashes,
positions and diagnostics against fresh corpus stages.

### Greek verb refusal diagnosis

The eight isolated Greek expansion refusals have the following causes in the
committed inputs and matching ASCII derivation tables. Paths below are relative
to `stemlib/Greek/`; line references identify the original sources, not the
concatenated audit input.

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

Nearby rules explain the mismatches; they are not proposed philological
replacements. No input is corrected or excluded on this evidence alone, and
the empty-stem cases remain rejected rather than receiving an inferred stem.

The two `vs` requests also exposed a tool defect: `GetStemClass` returns
`(Stemtype)-1` for an unknown name, but `Stemtype` is unsigned. A positivity
check therefore accepted the sentinel as a class and reported a misleading
unmatched derivation. Both `do_conj` and the independent ASCII derivation
expander now reject this sentinel explicitly. The former reports an unknown
principal part; the latter returns its documented malformed-input result
(`-1`) instead of the no-match result (`0`). Regression tests distinguish these
outcomes from successful expansion and check failed CLI output cleanup.
The eight notices still fail; only the two `vs` diagnostics change in the
pinned inventory. Existing fixture outputs and corpus exceptions are unchanged.

### Nominal refusal diagnosis

The indexer now retains the scanner's unrecognized keys in diagnostics for an
untyped record. If all remaining keys are recognized, it reports that none
provides an inflectional stem type. This affects diagnostics only: unknown
editorial keys alongside a valid type remain accepted, and failed indexing
still produces no output. Both nominal and verbal indexer CLIs exercise these
cases in regression tests.

The pinned nominal observations divide as follows:

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

The complete key strings remain in `test/stemlib-lexical/blockers.json`, including
non-type annotations such as Latin `group` and `orth`. Unknown keys must not be
equated automatically with missing inflectional types.

Of the twelve distinct unrecognized Greek keys, only `is_ios` has a same-named
ending source in the committed Greek tree. `endtables/source/is_ios.end` is
explicitly excluded by the table manifest and `is_ios` is absent from the stem
type registry. Its four affected notices therefore cannot be repaired merely
by adding it to a build list: registry and table qualification must be reviewed
together. No same-named ending source exists in the Latin tree for its observed
unknown keys. This filename check is not evidence that a similarly named table
is a valid replacement. No registry, source, exclusion or output baseline has
been changed by this diagnostic tranche.
