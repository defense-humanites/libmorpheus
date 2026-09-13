<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Changelog

This file records user-visible changes to the supported `libmorpheus` runtime.
Historical standalone utilities are outside the release contract. Stemlib data
changes are recorded separately because the native installation does not ship
the corpus.

## [Unreleased]

### Added

- An opt-in `morpheus_stemlib_production` CMake target now builds fresh Greek
  and Latin distributions through the qualified table and lexical recipes.
- A deterministic stemlib qualification report now cross-checks both clean
  CTest builds, the production target and the reviewed Perseids/Alpheios
  comparisons. It also binds the required public runtime and generation tests
  from CTest's JUnit result; a dedicated fail-closed parser regression test is
  itself required by the report, and CI retains all supporting evidence.
- An initial `@libmorpheus/node` binding uses a stable Node-API addon to load
  the separately installed C runtime and performs analysis and experimental
  generation on Node's asynchronous worker pool.
- An initial pure-Python `libmorpheus` package targets the stable C ABI through
  `ctypes`, avoiding interpreter- and platform-specific extension wheels while
  exposing analysis and experimental generation with runtime and stem data kept
  separate.
- Dedicated `node-v<version>` tags qualify three optional native-addon packages,
  publish them before the `@libmorpheus/node` facade through npm trusted
  publishing, and trigger a clean public-package smoke test.
- Dedicated `python-v<version>` tags qualify the universal Python wheel and
  source distribution, publish them through PyPI trusted publishing, and
  trigger a clean public-wheel smoke test against the native runtime.
- Dedicated `deno-v<version>` tags now publish the standalone Deno archive and
  JSR package independently from native runtime releases.

### Changed

- Reference stemlib qualification now runs on an explicit Ubuntu 24.04 image
  and fails closed unless GCC 14, Python 3.12 and Perl 5.38 are selected. The
  applied profile is carried through table, lexical and aggregate provenance.
- Complete Greek builds now compare all 143 runtime artifacts shared with the
  pinned Alpheios distribution and emit both digests and their classification.
  Three additional generated tables are reported as unavailable in that
  reference. This comparison remains distinct from the Perseids baseline.
- Stemlib production now declares a single-pass explicit dependency graph in
  its provenance and final receipt. Duplicate producer labels are rejected,
  making the inherited undocumented second make pass unnecessary.
- Successful full stemlib builds now emit one deterministic production receipt
  containing the source revision, environment, toolchain, ordered table and
  lexical input digests, all table and lexical output digests, and provenance
  record digests.
- Stemlib table provenance schema 4 now records the qualification profile and
  top-level production recipe, configured Git revision, dirty tracked state,
  compiler identity/version/executable digest, and target system. Lexical
  provenance verifies and carries this identity forward.
- The lexical recipe now rebuilds Greek and Latin `nom.irreg` and `vbs.irreg`
  from their checksum-pinned irregular-word sources before indexing. Three
  malformed Greek expansions are disabled only in staging; the Greek verbal
  snapshot is byte-identical, both Latin snapshots have identical notice
  records in producer order, and the reviewed Greek nominal divergence is
  pinned. Complete-corpus receipts now cover eight outputs per language.
- The complete Greek verbal corpus now passes the restored `do_conj` and
  `indexvbs` chain. Six historically non-producing derivation requests are
  disabled in the verified staging copy, and two empty-stem derivations are
  replaced by their explicit historical stems; clean builds emit identical
  eight-output receipts and pinned baseline differences.
- The complete Greek nominal corpus now passes the restored fail-closed
  indexer. Eight malformed stem types use existing registered paradigms, two
  source defects are repaired, and fourteen entries that require absent or
  unusable paradigms are explicitly marked `#noanalysis` rather than retained
  as untyped index entries.
- The complete Latin nominal corpus now also passes the restored indexer. Its
  verified staging corrections apply 62 evidence-backed type substitutions,
  quarantine 90 records without a qualified Latin paradigm, and repair two
  malformed notice boundaries without changing the historical source files.
  Two independent full Greek and Latin lexical builds now emit identical
  eight-output receipts and pinned baseline comparisons.
- Five inherited ending-table producers are restored as non-installed,
  default-disabled CMake targets with C17 entry points and fail-closed command
  handling. CI builds them explicitly and verifies that missing registries or
  compiled tables cannot produce a partial index, beginning the reproducible
  stemlib-production work.
- A checksum-pinned source manifest now classifies every Greek and Latin rule,
  ending macro, ending, and derivation input as active or explicitly excluded
  and rejects unreviewed input or compiled-baseline selection drift.
- Active table sources can be materialized into a fresh, language-scoped
  staging tree with ordered producer lists; existing or source-tree
  destinations are rejected and independent stagings are compared in CI.
- The ending and derivation producers can execute entirely inside that staging
  tree under a fixed locale and timezone. List-driven indexers reject implicit
  omissions, and successful builds emit sorted SHA-256 output receipts.
- CI performs two clean Greek and Latin table builds, requires byte-identical
  receipts and outputs, and compares all regenerated table artifacts with the
  checked-in baselines.
- JavaScript-family bindings now live under `bindings/js/`; the Deno package
  moves to the dedicated `@libmorpheus/deno` JSR namespace at version `0.4.0`,
  while retaining native runtime `0.3.2` and C ABI `2` compatibility.
- Native runtime and Deno binding versions are now independent. The binding
  declares the exact native release and ABI it supports, and native acquisition
  receipts record both the binding and runtime versions.
- Deno implementation modules and tests now live under `internal/` and `test/`,
  leaving only public entrypoints and package metadata at the binding root.
- The Alpine `deno-runtime` image now provides only Deno, the native runtime,
  and prepared data; applications consume the binding as a normal JSR
  dependency and use the preconfigured runtime environment variables.

## [0.3.2] - 2026-08-29

Target project version: **0.3.2**. C ABI: **2**. Shared-library SONAME: **1**.

### Changed

- The accepted schema 2 benchmark compares the unchanged analysis and
  generation paths with the 0.3.1 baseline on the same controlled Apple
  Silicon host.

### Fixed

- The Deno native installer now materializes verified shared-library aliases
  as regular files, allowing `/native` and `/setup` to retain path-scoped read
  and write permissions on Deno versions that forbid scoped `Deno.symlink()`.

## [0.3.1] - 2026-08-28

Target project version: **0.3.1**. C ABI: **2**. Shared-library SONAME: **1**.

### Added

- The JSR package now exports a combined `/setup` command that installs the
  matching verified native archive and either Alpheios or Perseids stem data;
  Alpheios setup can also prepare the experimental generation index without a
  native toolchain.
- A public-package smoke workflow now installs a freshly published JSR version
  in an empty Deno application and qualifies Greek and Latin analysis plus
  experimental Greek generation from public download endpoints.
- Exported Deno symbols and the `/data`, `/native`, and `/setup` entrypoints now
  carry JSR API documentation.

### Changed

- Deno installation documentation now presents the published JSR package and
  combined setup path first, while retaining the permission-scoped `/native`
  and `/data` commands for independent automation.
- The JSR license field now identifies the package's AGPL license; the package
  notice continues to document the MPL and MIT licenses of separately covered
  components.
- Release `0.3.1` rebuilds the native, standalone Deno, benchmark, and JSR
  assets under one version even though its runtime changes are confined to the
  Deno distribution. The C ABI and SONAME remain unchanged.
- The accepted schema 2 benchmark now compares the unchanged native execution
  paths with the 0.3.0 baseline on the same controlled Apple Silicon host.

### Fixed

- The bundled Emscripten generation preparer now loads correctly from its
  remote JSR module URL instead of passing an HTTPS URL to Node's
  `createRequire()`.
- Fresh-package CI disables Deno's default minimum dependency age for the
  exact version under test, so a just-published package can be qualified
  immediately.
- The Deno README archive notice now resolves to the binding's repository
  notice.

## [0.3.0] - 2026-08-28

Target project version: **0.3.0**. C ABI: **2**. Shared-library SONAME: **1**.

### Added

- The public C ABI now exposes owned Greek lemma-generation results, typed
  request filters, explicit result limits, and normalized morphology accessors.
- The Deno binding now exposes nonblocking `generate()` and `generateRaw()`
  methods with typed morphology filters, owned results, stable failures, and
  parallel execution through distinct contexts.
- Benchmark schema 2 now qualifies small and maximal generation paradigms,
  cold and warm index use, context scaling, returned records, and process RSS
  against a checksummed complete generation index.
- A differential fixture test now freezes representative regular and irregular
  Greek generation behavior, including the dual forms omitted by the historical
  text formatter.
- A deterministic offline builder and documented binary format now prepare
  duplicate-preserving lemma-to-generation-record indexes from expanded stem
  sources.
- A checksummed manifest now freezes the 49 ordered Alpheios stem-source inputs
  required to prepare the complete Greek generation corpus.
- A bounded offline source preparer now expands direct `@` continuations with
  the same base-record rule as the historical generator and rejects orphaned
  or still-derived input.
- A checksummed derivation-rule manifest and `do_conj full` differential
  fixture now freeze the inputs and representative behavior required to expand
  `:de:`/`;` records safely.
- The JSR `/data` command acquires pinned Alpheios or Perseids-Tools stem data
  without Git or a C toolchain and can prepare the validated experimental Greek
  generation index locally.
- The JSR `/native` command acquires the matching data-free GitHub Release
  archive, verifies its SHA-256 sidecar, safely extracts it, and records a
  machine-readable receipt.

### Changed

- Greek generation in the C API and Deno binding is now explicitly documented
  as experimental until representative real-world use complements its current
  automated qualification.
- Native and Deno release archives now carry self-contained licensing and
  provenance information without relying on paths outside the archives.
- Docker qualification images now include the canonical Alpheios generation
  index and exercise real Deno analysis and generation on Alpine x86-64 and
  aarch64; they remain non-published while data redistribution is unresolved.
- Version-tag automation now publishes verified native and standalone Deno
  assets before the JSR package, including the accepted benchmark evidence.

### Fixed

- The internal generation service now applies the historical first-key comma
  expansion to call-local input, allowing qualified corpus records such as
  `aor_pass,syll_augment` without changing the immutable index.

## [0.2.0] - 2026-08-25

Target project version: **0.2.0**. C ABI: **2**. Shared-library SONAME: **1**.

### Changed

- The structured ABI now uses independently assigned public morphology values;
  historical encodings are translated in an MPL-covered bridge.
- Opaque `stem_type` and `derivation_type` values were removed from
  `morpheus_analysis`.
- Morphology traits now use a complete 84-trait public bitset with zero-based,
  alphabetically ordered indices instead of exposing historical storage.
- Historical formatter declarations moved to `<morpheus/compat.h>` and their
  implementation moved to `src/compat/`.
- The normalized public API, Deno binding, and independently written project
  support files are explicitly AGPL-3.0-or-later; inherited engine, bridge,
  compatibility, fixtures, and derived internal headers remain MPL-2.0.

### Removed

- `morpheus_result_all_morph_flags()`, made redundant by the complete public
  trait bitset embedded in every structured analysis.

### Fixed

- Apple Silicon qualification now validates the current versioned Mach-O
  install name instead of assuming the previous SONAME.

## [0.1.3] - 2026-08-24

Target project version: **0.1.3**. C ABI: **1**. Shared-library SONAME: **0**.

### Added

- The Deno binding is now explicitly licensed under
  `AGPL-3.0-or-later`, independently of the MPL-2.0 native library.
- Linux CI now builds and verifies the standalone Deno binding archive,
  including its license and notice files.

### Changed

- Behavioral fixture tests now use CMake directly and no longer require Ruby.
- Obsolete inherited repository metadata and Ruby configuration were removed.
- Project documentation now describes the library independently of any
  particular downstream application.

### Fixed

- The CMake fixture runner detects optional JSON members without depending on
  version-specific diagnostic text.
- License references in the standalone Deno archive remain valid after
  extraction.

## [0.1.2] - 2026-08-24

Target project version: **0.1.2**. C ABI: **1**. Shared-library SONAME: **0**.

### Added

- A standalone, checksummed Deno binding source archive for each release.

### Fixed

- `hasMorpheusMorphFlag()` now accepts the analysis arrays returned by the Deno
  binding's `analyze()` and `analyzeRaw()` methods, as well as one
  individual analysis.

## [0.1.1] - 2026-08-24

Target project version: **0.1.1**. C ABI: **1**. Shared-library SONAME: **0**.

### Added

- Verified native release packages for Linux x86-64 glibc, Linux aarch64
  glibc, and macOS arm64, each with a SHA-256 integrity file.
- Extracted-package qualification that compiles and runs independent CMake and
  `pkg-config` consumers against every native archive.

### Changed

- Ordinary pull requests use the lower-cost Linux validation tier, while
  manual, weekly, and version-tag runs own the architecture qualification.
- Weekly platform qualification skips the costly matrix when `main` is
  unchanged and the preceding scheduled run succeeded; failed and changed
  revisions are still retried.
- Native package names state the operating system, architecture, and Linux libc
  contract explicitly.
- Linux package checks inspect ELF architecture and runtime dependencies.
  macOS checks inspect the arm64 Mach-O contract, install name, relocatability,
  and macOS 11.0 deployment target.

### Compatibility and data notes

- This release changes packaging and qualification only. The public C ABI
  remains version 1, the shared-library SONAME remains 0, and no runtime source
  or public symbol changed after 0.1.0.
- The Alpheios stemlib remains pinned at
  `4632415fe93c85e9fdca47a0c5a13f31385f0023`; native archives continue to
  exclude stem data.

## [0.1.0] - 2026-08-24

Target project version: **0.1.0**. C ABI: **1**. Shared-library SONAME: **0**.

### Added

- A C17 shared library with a versioned opaque ABI, caller-owned structured
  results, explicit status values, per-request options, and truncation flags.
- A typed Deno 2 FFI binding and a compatibility API used by `cruncher`.
- CMake and relocatable `pkg-config` packages, installed-consumer tests, and
  Alpine multiarchitecture runtime images.
- Native fixture coverage for the inherited Perseids data and the pinned
  Alpheios Greek stemlib.
- Release-comparable JSON benchmarks carrying code, stemlib, compiler, target,
  and runtime metadata.

### Changed

- The Deno `analyze()` result uses named grammatical values, named flag and
  truncation lists, and explicit nullable fields; `analyzeRaw()` preserves the
  numeric ABI representation for low-level consumers.
- Part-of-speech results now distinguish the stemlib's adverbs, articles,
  pronouns, numerals, prepositions, conjunctions, particles, and interjections
  instead of treating all indeclinables as adjectives. The Deno semantic
  result makes degree contextual, honors irregular degree flags, and
  canonicalizes epic submasks in combined dialect values.
- Requests for the optional HQ dictionary now fail once and silently with the
  public stemlib status when its dedicated indices are unavailable, instead of
  repeatedly writing diagnostics and returning an empty successful result.
- `cruncher` is now a client of the public library rather than an independent
  owner of the analyzer runtime.
- Mutable analyzer, dictionary, ending-table, conversion, collation, option,
  statistics, and output state is owned by explicit runtime contexts.
- Active string assembly and result conversion are bounded and transactional;
  capacity failures return errors without publishing partial output.
- The active runtime closure builds as strict ISO C17 with `-fno-common`, strict
  prototypes, conversion diagnostics, and either signed or unsigned `char`.
- Internal static archives remain build-only implementation details. The
  installed surface contains only the shared library, public header, discovery
  metadata, and optional `cruncher` executable.

### Removed from the supported contract

- Historical indexers, generators, converters, GUI programs, and other
  standalone utilities are retained only as classified reference source. They
  are not built, installed, or release-qualified.
- The shared library no longer imports process-terminating `exit()` or
  `abort()` paths; failures propagate through the public status contract.

### Compatibility and data notes

- ABI version 1 is the first published native interface. The pre-1.0 SONAME is
  0; incompatible layout or symbol changes require an explicit ABI review.
- The C implementation derives from Perseids commit
  `ab6898ffed335fc6169fa02c9940657a9b5a78e0`.
- The initially qualified Alpheios stemlib is pinned at
  `4632415fe93c85e9fdca47a0c5a13f31385f0023`. Updating that submodule is a data
  release change and must be reported independently from library code changes.
