<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Stemlib production audit

This audit records what can and cannot currently be reproduced from the
repository. It covers the compiled analysis stemlibs, not the separate
`gener.index` preparation pipeline documented in
[`gener-corpus.md`](gener-corpus.md).

## Conclusion

`libmorpheus` can consume and integrity-check pinned stemlib trees, but it does
not yet provide a supported stemlib compiler. Most historical sources and build
drivers are present, and Alpheios demonstrates that the Greek pipeline still
runs on Linux. Some referenced Latin inputs are absent from every known commit.
Neither the inherited makefiles nor the Alpheios automation is a hermetic,
fail-closed, byte-reproducible build.

The two production baselines have different status:

| Baseline | Runtime path | Production status |
| --- | --- | --- |
| Perseids Greek and Latin | `stemlib/` | Compiled snapshot introduced by commit `55f6ea6359a341d81fd0e6dc33f754f68119602f` in 2018 and unchanged since; no current producer runs in this repository. |
| Alpheios Greek | `vendor/alpheios-morpheus/dist/stemlib` | Output committed by the Alpheios stemlib workflow and pinned here at `4632415fe93c85e9fdca47a0c5a13f31385f0023`; this is the Greek reference dataset. |

Restoring reproducible production is therefore a distinct future task. It must
not be treated as a side effect of building the native runtime.

## Data layers

The historical tree mixes inputs, intermediates and runtime outputs. A future
build must model them as separate stages:

| Layer | Principal paths | Role |
| --- | --- | --- |
| Curated inputs | `stemsrc/`, `endtables/basics/`, `endtables/source/`, `derivs/source/`, `rule_files/` | Lexical entries and morphology rules maintained by humans or imported from external lexica. |
| Expanded tables | `endtables/ascii/`, `endtables/out/`, `derivs/ascii/`, `derivs/out/` | Text and binary tables emitted by `buildend` and `buildderiv`. |
| Search indexes | `steminds/`, `endtables/indices/`, `derivs/indices/` | Runtime lookup data emitted by `indexnoms`, `indexvbs`, `indendtables` and `indderivtables`. |
| Distribution | Alpheios `dist/stemlib/`; the bundled Perseids `stemlib/` snapshot | Selected rules, lexical data and compiled outputs consumed by Morpheus. |

Alpheios makes the distinction visible. Its `stemlib/Greek` directory contains
343 input files and no compiled `steminds`, ending outputs or indexes. Its
`dist/stemlib/Greek` directory contains 237 distribution files. The Alpheios
build compiles in the input tree and copies selected results into `dist/`; only
`dist/` is committed by its workflow. Consequently,
`vendor/alpheios-morpheus/stemlib/Greek` is not a runtime stemlib.

The bundled Perseids tree does not preserve that boundary: it contains 711
Greek files and 372 Latin files, including both sources and generated outputs.

## Existing production chain

The inherited chain is split across several directories:

| Stage | Programs | Historical build definition |
| --- | --- | --- |
| Build native tools | libraries plus all programs below | `src/makefile` and component makefiles |
| Expand irregular words | `buildword` | `src/gkends/expwordmain.c` |
| Expand ending tables | `buildend` | `src/gkends/expendmain.c` |
| Index ending tables | `indendtables` | `src/gkends/imain.c` |
| Expand derivations | `buildderiv` | `src/gkends/expsuffmain.c` |
| Index derivations | `indderivtables` | `src/gkends/smain.c` |
| Expand verb stems | `do_conj` | `src/gener/conjmain.c` |
| Build nominal and verbal indexes | `indexnoms`, `indexvbs` | `src/gkdict/indexnoms.main.c`, `src/gkdict/indexvbs.main.c` |
| Orchestrate one language | all of the above | `stemlib/Greek/makefile`, `stemlib/Latin/makefile` |

The modern CMake build compiles the reusable libraries and runtime but exposes
none of these eight historical producer programs as targets. A normal CMake
build therefore cannot rebuild a stemlib. The legacy route first installs the
programs into `bin/`, appends that directory to `PATH`, then invokes each
language makefile twice.

Alpheios is the only observed active producer. At the pinned revision its
GitHub workflow uses Ubuntu 22.04, `build-essential`, `flex-old`, and
`CFLAGS='-std=gnu89 -fcommon'`; `build_stemlib.sh` invokes the Greek makefile
twice and overlays selected output directories into `dist/stemlib/Greek`.

## Greek baseline

The reference inputs and runtime outputs are pinned together by the Alpheios
submodule revision. The Deno acquisition command additionally verifies the
selected 237-file distribution tree with the digest recorded in
`bindings/js/deno/internal/data_manifest.ts`. This proves acquisition integrity;
it does not prove that rebuilding the inputs produces the same tree.

The pin was audited against Alpheios `master` on 2026-08-31. Upstream was then
at `2f1a30d65ed7ae9c6120dbf64d730b863be412e4`, 25 commits after the pin, with
changes in 32 stem-source files, 55 ending-table files, two derivation files and
three rule files. Updating the submodule is therefore a corpus upgrade, not a
routine dependency refresh. It requires a new production build, tree diff,
analysis regression tests, generation-corpus qualification and benchmark
evidence.

## Perseids and Latin baseline

The repository preserves the Perseids history through
`ab6898ffed335fc6169fa02c9940657a9b5a78e0`. The compiled Greek and Latin files
under `stemlib/` were added by the earlier commit
`55f6ea6359a341d81fd0e6dc33f754f68119602f` with the description “include linux
stemlibs”. No later commit changed that tree.

The corresponding 2018 Docker recipe used Ubuntu 18.04, `build-essential`,
`flex`, `-std=gnu89`, and two make passes for each language. The image tag and
packages were not pinned by digest or version, and the commit contains no
output manifest or toolchain receipt. The checked-in bytes are thus an exact
baseline but not a reproducible-build proof.

For both languages, committed `lsj.nom`/`lsj.vbs` or `ls.nom`/`vbs.latin`
snapshots allow the compiled chain to start without the original lexicon
exports. The rules that create those snapshots still reference
`/local/text/lsj/lemmata` and `/local/text/ls/lemmata`. Those external inputs
are neither vendored nor versioned. Rebuilding the runtime indexes from the
committed curated inputs and reproducing the complete lexicon-import process
are therefore separate goals. The latter is currently impossible from this
repository alone.

## Repository archaeology

The public Morpheus repositories are not independent archives. Their commit
graphs share the same imported CVS history:

| Repository | Commits inspected | Relationship to the historical record |
| --- | ---: | --- |
| [PerseusDL/morpheus](https://github.com/PerseusDL/morpheus) | 448 | Base public history, from 1997 to two README edits in 2019. |
| [perseids-tools/morpheus](https://github.com/perseids-tools/morpheus) | 477 | Shares 446 commits with PerseusDL, then adds its Docker and compiled-stemlib work. |
| [alpheios-project/morpheus](https://github.com/alpheios-project/morpheus) | 628 | Contains all 448 PerseusDL commits, followed by its own development. |
| [perseids-tools/morpheus-perseids](https://github.com/perseids-tools/morpheus-perseids) | 120 | Starts at the 2008 Alpheios tree move; it is another descendant, not an older source. |

Consequently, finding the same makefile or derived stem file in another fork
does not provide independent provenance. An all-history path and content search
of this family found consumers of `lemmata`, but no lexicon exporter, raw
`/local/text/lsj/lemmata` or `/local/text/ls/lemmata`, renamed copy, archive, or
deleted large input blob.

The missing inputs predate the available history. Commit
`351a621e9cd37aa343a18bf4a4b624d49877c864` added the Greek tree on 1997-01-24
with `lsj.nom`, `lsj.vbs` and a makefile already pointing to
`LSJDIR=/local/text/lsj`. The Latin makefile appeared the next day; commit
`cc852baf33122dd78347768258268d9f1030fd84` added the Latin sources and derived
`ls.nom` and `vbs.latin` on 1998-07-08. Commit
`1a8b798653f6f05a6cc508b686f821f68a6b425a` later made their regeneration
conditional on the external `ls/lemmata` file. There is therefore no earlier
version in Git from which either export can be recovered.

The derived files also became curated datasets after their initial import,
rather than disposable build products:

| Derived file | First recorded version | Last change in the inspected Alpheios history | First/last line counts | Whole-history diff |
| --- | --- | --- | ---: | ---: |
| `Greek/stemsrc/lsj.nom` | 1997-01-24 | 2026-08-16 | 154,890 / 160,604 | +12,470 / -6,756 |
| `Greek/stemsrc/lsj.vbs` | 1997-01-24 | 2026-08-16 | 47,955 / 16,242 | +9,807 / -41,520 |
| `Latin/stemsrc/ls.nom` | 1998-07-08 | 2011-07-24 | 238,737 / 221,061 | +5,936 / -23,612 |
| `Latin/stemsrc/vbs.latin` | 1998-07-08 | 2010-06-17 | 17,452 / 17,220 | +588 / -820 |

Commit messages explicitly describe lemma mining, removal of bogus entries,
corpus-driven additions and hand fixes. Re-running a lexicon import must
therefore write to a separate staging tree and produce a reviewed semantic
diff; it must never overwrite these files as if they were a cache.

### External archives and replacement sources

The oldest additional public distribution located is the
[Perseus Java Hopper archive](https://sourceforge.net/projects/perseus-hopper/files/OldFiles/)
dated 2007-11-09. The inspected archive
`hopper-source-20071109.tar.gz` has SHA-256
`79b6b4220fab6962df654b6a0e6e81c8fd2d68f777a8abfa743a439f623d2b48`.
It contains the Hopper sources and dictionary DTDs, but no Morpheus stem
exporter and no LSJ or Lewis & Short `lemmata` input. Its
`LexiconEntryLoader` loads already chunked dictionary XML into the Hopper
database; it does not create Morpheus stems.

The archive does contain useful, independent behavior oracles:

| File | Size | Analyses | SHA-256 |
| --- | ---: | ---: | --- |
| `greek.morph.xml` | 195 MiB | 985,054 | `83b15693e0cf1bb96025a26366c38ea13be65796489f5f429833576b5a2eaa29` |
| `latin.morph.xml` | 140 MiB | 710,620 | `e9e3faf62cae0d1da9a0e556348fa8f9f112fe967349406cb6ca1bb529ab0264` |

These snapshots cannot recover input stems, but a future importer can compare
its analyzer behavior against them on a sampled or complete form set.

[PerseusDL/lexica](https://github.com/PerseusDL/lexica) is the best identified
public replacement source, not the missing provenance chain. Its history starts
in 2014: Lewis & Short was introduced by
`70f6431f7d4782223459aa13b082f77c042b3722` on 2014-07-11 and LSJ by
`1af61e1f3bbad38ee613e1a6683610d42206af21` later that day, years after the
derived Morpheus files and without their pre-2014 revision history. The current
[LSJ](https://github.com/PerseusDL/lexica/tree/master/CTS_XML_TEI/perseus/pdllex/grc/lsj)
and
[Lewis & Short](https://github.com/PerseusDL/lexica/tree/master/CTS_XML_TEI/perseus/pdllex/lat/ls)
XML nevertheless preserve the dictionary fields consumed by the old filters.
Lewis & Short supplies an archival Beta Code edition and a Unicode editing
edition. Both datasets are CC BY-SA 4.0 and must remain a clearly attributed
data input, separate from the AGPL/MPL program-source boundary.

### What the old importer contract reveals

The contract is implicit but sufficiently constrained for an emulator. The
lexers in `src/gkdict/` expect a flattened stream in which a headword starts a
record and nearby pseudo-TEI/SGML fragments carry fields such as `<orth>`,
`<itype>`, `<gen>` and `<pos>`. Tabs, field adjacency and record order matter.
Greek is represented in Beta Code; the Latin filters additionally normalize
HTML entities and the `_`, `^` and `+` quantity/diaeresis conventions. This is
a projection of dictionary entry headers, not an export of full definitions.

That evidence supports implementing a compatible projection from pinned TEI,
but not claiming byte identity with the missing historical export. The unknown
source revision, undocumented projection rules and decades of manual changes
make exact source reconstruction unprovable.

### Other missing historical inputs

The same archaeology confirms that the gap is wider than the two dictionary
exports. `stemlib/Latin/stemsrc/vbs.mpi` is referenced by the Latin makefile but
does not occur anywhere in the shared history. The Latin `stemtypes.table`
also contains 43 entries whose names have no corresponding
`endtables/source/*.end`; some are intentionally non-inflecting categories,
but at least the regular tables `or_uris`, `es_idis`, `aLs_aris`, `as_anis` and
`s_dis_adj` are genuine noun or adjective classes. This was independently
reported in
[PerseusDL/morpheus issue 23](https://github.com/PerseusDL/morpheus/issues/23).

The historical tools hide these gaps: `buildend` ignores the negative return
from an individual table expansion, the ending indexer silently skips a
missing `.out`, and the shell pipeline containing the missing `vbs.mpi` takes
its status from the final Perl process. A legacy build can therefore finish
while silently omitting data. Reproducing those omissions may reproduce a
snapshot; it is not evidence that the historical source set is complete.

### Archaeological verdict

The exact original import cannot be restored from currently public artifacts.
A functionally equivalent, auditable re-import remains feasible, but it is a
separate corpus-migration project from rebuilding indexes from the committed
stem sources. It should use this order:

1. restore a fail-closed stemlib compiler and reproduce the current staged
   inputs without invoking a dictionary import;
2. pin one `PerseusDL/lexica` revision and define a normalized, versioned
   intermediate representation for dictionary entry headers;
3. emit an explicitly documented legacy-`lemmata` projection into an isolated
   staging tree;
4. compare staged stems against the curated snapshots and compare analyzer
   behavior against regression fixtures and the 2007 Hopper morphology
   oracles;
5. accept corpus changes only through a separately reviewed, attributed data
   upgrade.

## Reproducibility blockers

The following issues must be resolved before a regenerated tree can replace a
published baseline:

1. **Unsupported producers.** CMake does not build the eight producer
   executables; the legacy makefiles require GNU89-era compilation and flex.
2. **Non-hermetic recipes.** The language makefiles depend on ambient `PATH`,
   `MORPHLIB`, shell utilities, Perl behavior and absolute `/local/text/...`
   paths. Tool and dependency versions are not locked.
3. **Shared temporary files.** Both languages use fixed paths such as
   `/tmp/nommorph` and `/tmp/vbmorph`, preventing isolated or parallel builds.
4. **Incorrect dependency paths.** Rules name `stemind/nomind` and
   `stemind/vbind`, while the programs write `steminds/...`. These targets are
   never satisfied and obscure the real dependency graph.
5. **Masked failures.** Setup rules use `mkdir ... || true`. Alpheios
   `build_stemlib.sh` is not fail-fast, so a failed command need not stop later
   copies and cleanup. Inside the producers, failed ending expansion is
   discarded and missing ending outputs are silently skipped; the Latin verb
   pipeline also masks its absent `vbs.mpi` input.
6. **Stateful distribution assembly.** The Alpheios script overlays files onto
   an existing `dist/` tree instead of creating an empty staging directory.
   Removed or renamed outputs can survive a later build.
7. **Unverified two-pass behavior.** The second make pass is documented as
   discovering additional stems, but the pipeline neither states which stage
   requires iteration nor proves convergence. It does not compare pass two
   with pass three or two independent clean builds.
8. **No production manifest.** Neither upstream recipe records normalized
   input hashes, producer revision, exact toolchain, locale, output list and
   output digests in one receipt.
9. **No rebuild comparison.** Existing CI tests runtime behavior and pinned
   downloads, but no job performs two clean stemlib builds and compares their
   outputs byte for byte.

The recent explicit little-endian ending-table and index I/O work reduces one
class of host-format variance. It does not by itself make ordering, staging,
iteration or the rest of the toolchain deterministic.

The restored pipeline now supplies fresh language-scoped staging, ordered and
checksum-pinned manifests, fail-closed producers, source/toolchain provenance,
output receipts, independent clean-build comparisons, and reviewed baseline
exceptions. The list above remains the audit of inherited upstream recipes;
the restoration progress below records how each acceptance criterion is met.

## Acceptance criteria for the restoration phase

The later reproducible-build work should be accepted only when it provides all
of the following:

- explicit CMake targets for producer programs, kept internal and
  MPL-covered;
- a fresh, language-scoped staging directory with no writes to the source tree
  or global `/tmp` paths;
- pinned build environment, locale and tool versions;
- an explicit ordered input manifest for Greek and Latin, with missing and
  unexpected inputs rejected;
- a documented convergence rule, or removal of the historical second pass;
- a machine-readable receipt containing source revisions and input/output
  digests;
- two independent clean builds whose selected distribution trees are
  byte-identical;
- comparison against the current Perseids Latin baseline and the pinned
  Alpheios Greek baseline, with every intentional difference reviewed;
- the existing Greek and Latin fixtures, public API tests, null/multiple
  analysis cases, dialects, duals and Greek generation qualification still
  passing.

The criteria are now met by the opt-in qualification pipeline described below.
Compiled stemlibs remain pinned external or checked-in data dependencies:
runtime and binding releases do not silently regenerate or rewrite them.

## Restoration progress

The first implementation tranche restores C17-clean, internal CMake targets for
`buildword`, `buildend`, `indendtables`, `buildderiv`, and `indderivtables`.
They remain excluded from default builds and from installation, while Linux CI
builds their aggregate target. Their command-line drivers now reject malformed
invocations and propagate failed expansion, input, and output operations instead
of reporting success after a partial table build. The ending and derivation
indexer now also reject an unavailable registry, a missing compiled table, a
malformed table and failed output, with CI asserting that these failures leave
no partial index behind.

The ordered, checksum-pinned
[production source manifest](stemlib-production-manifest.md) now covers all 379
committed Greek and Latin rule, ending-macro, ending, and derivation sources.
It makes the historical effective selection explicit: 367 inputs are active
and twelve Greek sources without compiled baselines are excluded and named. CI
rejects missing, unexpected, reclassified, or modified inputs and mismatches
between that selection and the checked-in compiled-table baseline.

The manifest can now be materialized into a new, language-scoped staging tree.
The stager refuses both source-tree destinations and existing destinations,
copies and re-hashes only active inputs, and emits ordered producer lists. CI
qualifies two independent Greek stagings and two independent Latin stagings.

The five restored producers can now consume that staging directly. Ending and
derivation expansion follows the manifest order, while list-driven indexers
derive the nominal, verb, and derivation indexes from exactly the active set.
Missing ending macros now propagate through expansion as fatal errors. A
successful Greek or Latin table build records every generated table and index
digest in a sorted output receipt.

CI now performs two clean table builds per language, compares the receipts and
all generated bytes, and compares the 568 resulting files with the checked-in
Greek and Latin compiled-table baselines. Textual tables and indexes must remain
byte-identical. Binary `.out` differences are tracked separately because the
restored writer uses explicit serialization instead of historical in-memory
structure bytes. This establishes convergence for the table-production
subgraph independently of the lexical production proof described below.

The checked-in baseline comparison currently contains 156 Greek and 73 Latin
binary differences, against zero differences in ASCII expansions or indexes.
The complete sorted path set is pinned in
`test/stemlib-binary-baseline-exceptions.tsv` with the
`explicit-binary-serialization` classification. CI rejects any change to that
reviewed exception set.

The subsequent lexical tranche restores `do_conj` as an internal MPL C17 target
and connects all three lexical producers to a separate ordered source manifest
and the verified table staging. Clean Greek and Latin fixture builds now yield
twelve reproducible outputs with pinned hashes. The Latin verbal corpus now
builds after an exact assembly proof for the historically absent `vbs.mpi` and
seven evidence-backed malformed-record repairs; its two index differences are
pinned and its odd-key output matches the baseline. The complete Greek corpus
also builds after the eight previously inventoried verbal refusals are handled
in its verified staging copy. The complete Latin nominal corpus now builds after
154 checksum-pinned staging corrections: 62 registered-type substitutions, 90
explicit quarantines and two notice-boundary repairs. `buildword` now also
reconstructs both prepared irregular-word files per language from pinned source
inside the stage. Two independent complete builds of each language emit
identical eight-output receipts, and all changed baseline paths are explicitly
pinned. See the
[lexical production boundary](stemlib-production-manifest.md#lexical-production-and-qualification)
for the reproduction command and correction evidence.

Successful builds now consolidate their source revision, fixed environment,
toolchain identity, ordered source digests, all table and lexical output
digests, and both provenance-record digests in one deterministic production
receipt. CI verifies its contents and requires byte-identical receipts from the
two independent builds of each language.

The restored recipes remove the historical second make pass. Their declared
`single-pass-explicit-dag` model builds every table source once, rebuilds both
irregular lexical sources before assembly, and treats indexes as terminal
outputs. Duplicate producer labels fail closed; convergence is established by
comparing two fresh executions rather than mutating one tree twice.

The Greek qualification now also compares the complete selected runtime-output
boundary with the pinned Alpheios distribution: all 143 Alpheios paths are
present in the reconstruction, two ending tables are byte-identical, 141 paths
differ, and three additional generated tables have no Alpheios counterpart. A
deterministic CI report records both digests for every path. This keeps the Alpheios reference
visible without conflating its different source snapshot with the Perseids
baseline used to review reconstruction changes.

The reference qualification environment is now an explicit Ubuntu 24.04
x86-64 profile rather than the moving `ubuntu-latest` alias. Configuration
fails closed unless GCC 14, Python 3.12 and Perl 5.38 are selected. The profile
is recorded in table provenance, lexical provenance and the aggregate receipt;
the exact executable versions and hashes remain attached to each run. Portable
developer builds retain a separate default profile.

The reconstruction is now exposed as the opt-in
`morpheus_stemlib_production` CMake target. It creates fresh Greek and Latin
stages below the build tree, runs the explicit table and lexical graph, and
requires a final receipt from each language. The orchestration recipe itself is
hashed in table provenance; CI invokes the target directly.

CI finally assembles a deterministic machine-readable qualification report
that cross-checks the two independent CTest builds against the public CMake
target, the 229 reviewed Perseids binary exceptions, the twelve reviewed
lexical differences, and all 146 selected Alpheios comparison paths. The report
and its supporting receipts, provenance and comparison tables are retained
together as a revision-named CI artifact. Its final gate also parses the full
CTest JUnit result and requires the named public API, null-handling,
multiple-analysis, dialect, dual, Greek-generation and Greek/Latin fixture
tests to be present and successful.
