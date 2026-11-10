<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Changelog

This file records user-visible changes to the supported `libmorpheus` runtime.
Historical standalone utilities are outside the release contract. Stemlib data
changes are recorded separately because the native installation does not ship
the corpus.

## [Unreleased]

### Added

- `morpheus_generation_result_skipped_records()` reports how many of a
  lemma's source records generation skipped because the engine could not
  generate them (#78). The function is an ABI 2 addition: existing callers
  are unaffected.

### Changed

- Experimental generation no longer fails a whole lemma on one bad record
  (#78). Over the Alpheios index (106,422 lemmas), 275 lemmas failed with
  `MORPHEUS_INTERNAL_ERROR` because of 346 records: stem classes without an
  ending table (`as_a`, `gc_ggos`, `irreg_decl3`…) or forced endings that
  match no cell. Those records are now skipped and counted, and the lemmas'
  other records are generated: δίδωμι returns 3,889 forms with one record
  skipped, ἵστημι 7,337, πόλις 166; 110 lemmas whose records all fail
  return no forms and a nonzero count. The other 106,147 lemmas return the
  same records as before, apart from the hyphen below. Allocation failures
  still fail the request.
- Generated records carry the morphology flags that analysis reports for
  the same form: the word's flags together with those of its preverb, stem
  and ending, as `checkgenwds.c` combines them (#78, item 5). Generation
  read only the word's flags and lost the stem's, among them the irregular
  comparative and superlative markers, so ἡδύτερος and ἥδιστος (`h(duter
  os_h_on irreg_comp`, `h(dist … irreg_superl`) came out positive. Over the
  Alpheios index, 11,964 adjective, 28 adverb and 4 noun records change
  degree, and 101,125 lemmas have records that gain flags; surfaces, other
  traits, counts and skipped records are unchanged. On 400 random lemmas, every generated
  record that matches an analysis of its surface now has the same degree
  (32,192 of 32,192, against 32,100) and 98.1 % the same flags (27.2 %
  before); the rest differ by flags that analysis derives on its own path,
  such as reduplication.
- Generated surfaces no longer carry the stem-boundary hyphen of the stem
  source (`a)nqr-w/pwn` becomes `a)nqrw/pwn`; 1,268,920 forms of 11,823
  lemmas in the Alpheios index).
- Contexts opened through the public API no longer print the inherited
  engine's diagnostics (`Something wrong with stemkeys […]`, `MorphFopen:
  could not open […]`…) on standard error or output; failures are reported
  by status only. The compatibility API, and so `cruncher`, keeps them, as
  do the historical tools.

- Node.js binding 0.2.0 (`docs/release-node-0.2.0.md`) and Python binding
  0.2.2 (`docs/release-python-0.2.2.md`), both published, ship the decoding
  changes below; both still declare native 0.4.6. Node.js takes the minor
  version for its frozen shared name arrays. The controlled-host comparisons
  of both bindings are retained as
  `bench/release-evidence/benchmark-0.4.6-bindings-{1,2}.json`.
- Python binding: generation no longer slows down with threads. The result
  accessors (count, copy, truncation mask, free), called once or twice per
  record, now keep the GIL (`ctypes.PyDLL`); through `CDLL` each released
  and reacquired it, and with several threads those thousands of
  reacquisitions per paradigm queued on the GIL (the controlled host
  measured 68, 69 and 42 maximal generations per second at one, two and
  four threads). `analyze()` and `generate()` also decode each record's
  bytes directly into the named object through one reused buffer. On a
  2-vCPU Linux host, maximal generation goes from 26, 12 and 10 to 41, 47
  and 43 per second at one, two and four threads; results, named and raw,
  are byte-identical over the benchmark corpora.
- The benchmark harness measures the Python binding next to the Node.js
  binding when `MORPHEUS_PYTHON` names an interpreter: `python` analysis
  rows and `python-generation-<lemma>-warm` rows at the same context counts,
  one thread per context, from the binding of the source tree. The rows are
  optional in baselines and release reports.
- Python binding: `analyze()` and `generate()` cache the name tuples of
  normalized records per code (morph flags keyed by their 11 bytes) instead
  of recomputing them for every record, where the morph flags alone took 84
  tests per record. Tuples being immutable, sharing them is invisible to
  callers; the records are equal to the previous ones over 34,267 generated
  forms and 2,667 Greek and Latin analyses. Generating the largest paradigm
  (`i(/hmi`, 2,918 forms) takes about 36 ms instead of 173 ms on a Linux
  test host, most of it now the per-record copy of `generate_raw()`; that
  normalization ran under the GIL and capped multithreaded generation.
- Node.js binding: `analyze()` and `generate()` decode the packed records
  straight into the named objects, and their name arrays (dialects, regions,
  genders, cases, voices, morph flags, truncated fields) are frozen and
  shared between records with the same values, as the `readonly` types
  already declared. The objects are otherwise identical (34,267 generated
  forms and 2,667 Greek and Latin analyses compared with the previous
  decoder). Generating the largest paradigm (`i(/hmi`, 2,918 forms) costs
  about 4 ms of main-thread work instead of 20 ms on a Linux test host,
  garbage collection included. On the controlled host
  (`bench/release-evidence/benchmark-0.4.6-node-decoding.json`) it takes
  3.17, 1.60 and 1.02 ms at one, two and four contexts instead of 5.73, 3.60
  and 3.75 ms: the ceiling near 270 operations per second is gone. An
  application that changes one of these arrays must now copy it first.
  `analyzeRaw()` and `generateRaw()` are unchanged.
- The error raised when a context cannot be opened names the stemlib path
  and the language instead of the language's number, in the WebAssembly
  facade (`opening /stemlib for Latin failed: stemlib is unavailable or
  incomplete`), and now also in the Node.js and Python bindings, whose
  message gave only the status text. The status is unchanged
  (`StemlibError`, 8). The usual cause is a stemlib without that language,
  such as the Greek-only Alpheios dataset opened for Latin; the WebAssembly
  README's example says so. Each binding ships the change in its next
  release.
- Node.js binding 0.1.4 (`docs/release-node-0.1.4.md`) and Python binding
  0.2.1 (`docs/release-python-0.2.1.md`), both published, declare native
  release 0.4.6 instead of 0.4.5: `libmorpheus-native` and
  `libmorpheus-setup` acquire the `v0.4.6` archives, so applications receive
  its faster analysis, and both carry the named context error above. C ABI
  2 unchanged.
- The N-API / WebAssembly comparison is concluded (`docs/wasm.md`): on the
  same runtime sources (native 0.4.6, module 0.1.4) the Node.js binding
  analyzes faster at every concurrency measured and starts and holds
  contexts more cheaply, so it stays; the pool remains ahead only for
  wide-parallel generation of large paradigms, a main-thread decoding cost
  of the binding. The WebAssembly README now says when to prefer
  `@libmorpheus/node`, and the two further comparison reports are retained.

### Fixed

- A generation record that failed after its keys were scanned (an ending
  table that cannot be opened, a forced ending that matches no cell) leaked
  the buffer holding its unknown keys. No test generated such a record; the
  whole Alpheios index now generates under AddressSanitizer without leaks.

## [0.4.6] - 2026-11-09

Target project version: **0.4.6**. C ABI: **2**. Shared-library SONAME: **1**.

This native release makes analysis about three times faster on the
controlled Apple Silicon host and about 2.8 times faster on Linux, with
results unchanged, and fixes a memory leak in the generation source
preparer. It is the release WebAssembly binding 0.1.4 is compiled from and
declares. The binding releases published since 0.4.5 (Node.js 0.1.3,
Python 0.1.1 and 0.2.0, and the final Deno 0.4.3) and the benchmark harness
migration are listed below.

### Changed

- Analysis is faster, with identical output over 4,176 Greek lemmas, the
  benchmark corpus and the Latin irregular forms (pull requests #61 and
  #62). On the controlled Apple Silicon host, `cruncher -T` analyzes 24,000
  words in 4.9 s instead of 14.8 s; on a 2-vCPU Linux host, 10.2 s instead
  of 28.5 s. Five hot paths, found by profiling, account for it:
  `xfer_prvbflags()`, called for every candidate key, tested 112 flag
  numbers through a thread-local lookup of the runtime context each (more
  than half of all instructions); it now tests the eight preverb flags
  directly. The stem and dictionary string comparisons use a fixed byte
  mapping instead of a per-context table; `MatchMorphKey()` reads the
  context once; a raw preverb whose first byte differs is rejected before it
  is compared; and each context keeps the stem index files it reads open,
  keyed by full path, until it is destroyed, where an analysis opened and
  closed `steminds/nomind` about five times per word. A context therefore
  holds up to four more open files.
- The benchmark harness compares the WebAssembly pool and the Node.js
  binding on equal terms (pull request #60): `bench/release.sh` sizes the
  libuv thread pool to the widest context count (`UV_THREADPOOL_SIZE`,
  recorded as `runtime.uvThreadpoolSize`; the validator rejects native rows
  wider than the pool), and the pool sends one request per operation and
  returns every result to the main thread (`wasmResultDelivery`), as the
  binding does. The first controlled-host comparison is retained as
  `bench/release-evidence/benchmark-0.4.5-wasm-comparison.json`.

- GitHub releases take their title from the tag (`v0.4.5`, `wasm-v0.1.3`…)
  and their body from `docs/release-notes/<tag>.md`, a short user-facing
  summary written one line per paragraph, instead of the whole release
  decision with its hard line breaks. Node.js and Python binding tags now
  publish GitHub releases too, carrying the npm tarballs or the wheel and
  source distribution served by their registry, verified against the
  registry's digests, with `SHA256SUMS`. A manual `Release notes` workflow
  applies the notes and titles to published releases, and
  `tools/backfill-binding-releases.sh` creates, from a maintainer's machine,
  the releases of the Node.js and Python tags published before; the
  `release_notes` test guards the notes, the workflows and the script.

- Node.js binding: the addon returns the records of one operation as a
  single packed buffer in the C ABI's layout, decoded in JavaScript, instead
  of building every result object on the main thread through Node-API calls
  (about thirty-five per form, plus an `ArrayBuffer` for its morph flags;
  issue #47). Analyses and generated forms are unchanged, raw and semantic
  alike, over 3,000 Greek headwords, the Latin fixtures and five paradigms;
  the maximal generation benchmark falls by about half per operation and
  scales with contexts again. The facade requires the addon's
  `recordEncoding`, so a rebuilt addon is needed with this facade (the npm
  platform packages are rebuilt by the binding's release).
- Node.js binding 0.1.3 (`docs/release-node-0.1.3.md`, published) ships that
  encoding and declares native release 0.4.5 instead of 0.3.2:
  `libmorpheus-native` and `libmorpheus-setup` acquire the `v0.4.5` archives,
  so applications receive the native changes since 0.3.2, the Latin
  stem-class resolution of 0.4.5 included. C ABI 2 unchanged.
- Python binding 0.1.1 (`docs/release-python-0.1.1.md`, published) declares
  native release 0.4.5 instead of 0.3.2 for the same reason; the binding has
  no acquisition command, so the declaration directs applications to the
  `v0.4.5` archives and is verified by the release workflow. Source
  unchanged.

### Fixed

- The generation source preparer no longer leaks the euphony forms
  `do_euph()` returns: its derivation expansion, like the `do_conj` stemlib
  tool, copied the first form and never freed the array (311,460 bytes in
  537 allocations over the generation corpus). Neither the library nor the
  WebAssembly module links that code; the preparer bundled with
  `@libmorpheus/data` is a short-lived process. The sanitizer CI job now
  runs with leak detection.

### Deprecated

- Deno binding 0.4.3 (`docs/release-deno-0.4.3.md`, published) is the final
  release of `@libmorpheus/deno`: it declares native 0.4.5 instead of 0.4.2
  and carries a deprecation notice in its README and module documentation,
  directing new code to `@libmorpheus/wasm` or `@libmorpheus/node`. The
  binding, its release workflow and the `deno-runtime` Docker target are
  removed from the repository after this release; the JSR package stays
  available, frozen.

### Removed

- The Deno binding (`bindings/js/deno/`), its release, JSR-recovery and
  JSR-smoke workflows, its standalone-archive packaging and checks, the
  `jsr_package_metadata` test, and the `deno-runtime` Docker target, after
  the final `deno-v0.4.3` release. libmorpheus no longer depends on Deno:
  CI no longer installs it, the Alpine image is qualified with `cruncher`,
  and `@libmorpheus/wasm` and `@libmorpheus/data` are checked and published
  to JSR with JSR's own `jsr` command-line tool (`npx jsr@0.14.3 publish`),
  their tests running under Node.js. The CMake option that builds the
  WebAssembly generation preparer is renamed
  `MORPHEUS_BUILD_JS_GENER_PREPARER` (formerly
  `MORPHEUS_BUILD_DENO_GENER_PREPARER`); its only consumer is the data
  package.

### Added

- Python binding 0.2.0 (`docs/release-python-0.2.0.md`, published) acquires
  the native runtime and the stem data at parity with the Node.js binding:
  `libmorpheus-native`, `libmorpheus-data` (`--subset`, `--languages`,
  `--manifest`) and `libmorpheus-setup`, as console scripts, `python -m`
  modules and functions, standard library only, with the same pinned sources,
  verification, receipts and rollback; the `python_package_metadata` guard
  keeps the pins identical with `@libmorpheus/data`. Experimental generation
  takes a prepared index through `--gener-index`, verified against the pinned
  digest, since the Python package cannot run the WebAssembly preparer.

- The runtime benchmark harness runs under Node.js and measures the
  Node.js binding (`bindings/js/node`, Node-API) instead of the Deno FFI
  binding: `bench/compare.mjs`, `bench/validate.mjs` and `bench/report.mjs`
  replace `bench/compare.ts` and `bench/validate.ts`, the WebAssembly pool
  runs on `worker_threads`, and `bench/release.sh` builds the addon with the
  release runtime (`MORPHEUS_NODE_ADDON`). Reports are schema 3 (`node`
  engine; Node.js, V8, libuv, kernel and binding versions recorded). The
  validator still accepts the retained schema 2 evidence; a schema 1 or 2
  baseline is compared on `cruncher-persistent` only (`comparisonScope`
  `cross-runtime`), the one row whose timing does not run through the
  harness's runtime, so the first schema 3 release report establishes the
  new baseline of the binding, generation and cold rows. Deno's maintainers
  announced the end of its development on 2026-10-09; the release gate no
  longer depends on it. The native library, its results and the Deno binding
  are unchanged.

## [0.4.5] - 2026-11-05

Target project version: **0.4.5**. C ABI: **2**. Shared-library SONAME: **1**.

This native release resolves the stem classes the stem-type tables name
(`pp_su`, `nounstem`) and refuses unknown ones, which restores every Latin
fourth-principal-part analysis to the WebAssembly build and reports the
perfect participles of deponent lemmas as deponent natively. It is the
release WebAssembly binding 0.1.3 is compiled from and declares. The data
acquisition package and the Node.js binding's dependency on it, released
in between, are listed below.

### Fixed

- Latin fourth-principal-part analyses on 32-bit targets, and the voice of
  deponent perfect participles everywhere (issue #37). The Perseids Latin
  `stemtypes.table` names the fourth-principal-part class `pp_su`, and both
  Greek tables name `nounstem` for `pers_pron`; neither was in the runtime's
  class table. `GetStemClass()` reports an unknown class as all ones, and
  that value, widened into a 64-bit `long`, is positive, so `AddMorphKey()`
  accepted the key with a stem type that has every bit set; on `wasm32` it
  is `-1`, the key was refused and every stem of the class was dropped: the
  WebAssembly module returned no analysis for `amatus`, and 108 of 1,517
  Latin headwords differed from the native library. The runtime now knows
  both names, and the loader refuses a stem-type table naming an unknown
  class with a diagnostic and an internal error, on every platform alike.
  Native results change in one respect: readings whose lemma is a deponent
  or semi-deponent verb of the stemlib (`cavillor`, `vador`, `audeo`, and
  the deponent doublets Perseids records next to active verbs, such as
  `juror`, `toleror`, `lupor`) report their perfect participle as deponent
  instead of passive; readings of active lemmas are unchanged. 12 of 1,517
  Latin headwords are affected (`ingressus` gains the deponent `ingredior`
  reading next to the passive one). Greek results are unchanged over 3,000
  headwords, and WebAssembly results now equal native ones in lemma, stem
  and ending over both samples.
  `public_fixtures` asserts `amatus`, `rosarum` and `ingressus` on both
  platforms. WebAssembly binding 0.1.3, compiled from this release, carries
  the repair; 0.1.2 and earlier drop those Latin analyses. The stemlib
  production tools share the class table: tables
  regenerated from the Perseids sources now carry `PP_SU|01` where the
  historical ones carry the all-ones value (the 144 `pp4.out` records and
  four derivation records, pinned as a second reviewed semantic exception;
  the runtime analyzes identically over both), and the Latin nominal ending
  index no longer lists `pp4`, which the table-build comparison reads out of
  the checked-in baseline. The checked-in generation preparer is rebuilt
  from the repaired tree.

### Added

- Data acquisition package `@libmorpheus/data` (`bindings/js/data/`),
  extracted from the Node.js binding's `libmorpheus-data` command so that
  WebAssembly, browser and Workers deployments can acquire a pinned dataset
  without installing a native binding. It contains no linguistic data: it
  downloads the pinned upstream archive, verifies the tree and the upstream
  license, and writes the result with a provenance receipt. New in this
  package: `--subset runtime` writes only the files the runtime reads (275
  files and 10 MiB for Perseids, 156 files and 19 MiB for Alpheios with
  `gener.index`), `--languages` keeps a subset of a dataset's languages, and
  `--manifest` writes `stemlib-manifest.json` (path, size, SHA-256 of every
  written file) for `fetchStemlib()`, bundlers and `writeStemlib()`.
  `data_package_metadata` guards the package contract, requires the files
  shared with the Node.js binding to stay byte-identical until that binding
  depends on this package, and forbids any stemlib artifact in the package
  tree. Linux CI acquires both datasets from upstream, rebuilds
  `gener.index` and analyzes one form per language over the runtime subset.
  The package is published on npm and JSR from the same directory and runs
  under Node.js, Deno and Bun (its tests pass under all three;
  `import.meta.main` lets `deno run jsr:@libmorpheus/data` run the
  command). `data-release.yml` publishes a `data-v*` tag to npm (OIDC with
  provenance) and JSR after testing the package under both runtimes and
  acquiring a dataset with the command installed from the `npm pack`
  tarball; Linux CI runs on those tags. First release:
  `docs/release-data-0.1.0.md`.
- Node.js binding 0.1.2 depends on `@libmorpheus/data` 0.1.0 (exact pin)
  instead of carrying its own copy of the acquisition code: `libmorpheus-data`
  and the `/data` export re-dispatch to and re-export from that package, so
  `--subset runtime`, `--languages` and `--manifest` are available from the
  binding too; `libmorpheus-setup` is unchanged. The binding no longer
  embeds the generation preparer, so its `LICENSES/` directory and the
  MPL/Emscripten notice move to the data package (`NOTICE` says so). The
  declared native release stays 0.3.2 with C ABI 2. `node_package_metadata`
  requires the pin to equal the tree's data package version; CI links the
  in-tree data package into the binding before testing it.

## [0.4.4] - 2026-11-04

Target project version: **0.4.4**. C ABI: **2**. Shared-library SONAME: **1**.

This native release carries no change to analysis or generation results. It
reads each index file in one request instead of thousands, which halves the
first analysis of a WebAssembly context, and it is the release WebAssembly
binding 0.1.2 is compiled from and declares; that binding also adopts the
stemlib bytes it is given instead of copying them. Both changes answer the
cold-start cost of a serverless deployment.

### Changed

- The WebAssembly facade's `writeStemlib()` (and so `fetchStemlib()`) adopts
  the arrays it is given instead of copying them, and creates each directory
  once per call instead of probing every path segment of every file. Placing
  the Greek runtime subset in memory on a fresh Node.js process falls from
  about 20 ms to 7 ms, the part of a serverless cold start the facade
  controls. Node.js callers already handed over views, since Emscripten's
  "copy" of a `Buffer` is a `Buffer.slice`, which is a view; the contract is
  now explicit for every input type: the bytes belong to the module and must
  not be modified afterwards. Analyses are unchanged. (WebAssembly binding
  change only; no native release is needed.)
- The index loaders read each file in one request. `init_endind` (verb
  stem, ending and derivation indices) asked `vax_fread` for `BUFSIZ` bytes
  at a time and `init_preind` read the pre-index sidecars one record at a
  time through the stdio buffer, so a context's first Greek analysis issued
  about 3,500 `read` calls for 1.8 MiB; under WebAssembly every call crosses
  into the JavaScript file system. Both now request the whole file, which
  the C library serves in a few calls (about 80 for the same analysis), and
  `init_preind` decodes the records from memory with the layout `WriteKey`
  produces. The first analysis of a WebAssembly context falls from 10–15 ms
  to about 6 ms with optimized code on a 2 vCPU host; analyses are identical
  (3,000 Greek headwords and the Latin fixtures compared against the
  previous module). Native builds issue fewer system calls; no result or
  ABI change.
- WebAssembly binding 0.1.2, compiled from this release, with the adoption
  of stemlib bytes above. 0.1.1 remains usable from both registries.

## [0.4.3] - 2026-10-21

Target project version: **0.4.3**. C ABI: **2**. Shared-library SONAME: **1**.

This native release carries no change to analysis or generation results.
It regularizes the provenance of the WebAssembly binding: `@libmorpheus/wasm`
0.1.0 was compiled from a `main` commit whose runtime sources differ from
`v0.4.2` by the two ILP32 corrections below. 0.4.3 is the native release
those sources belong to, and WebAssembly binding 0.1.1 is compiled from it.

### Fixed

- The WebAssembly facade instantiates a module whose import module names a
  registry rewrote into relative specifiers. JSR does this to every
  published `.wasm` (`env` becomes `./env`), so `@libmorpheus/wasm` 0.1.0
  from JSR failed in `WebAssembly.instantiate()` while the same version from
  npm and the GitHub release worked. The facade now maps such names back
  onto the loader's imports; a test exercises a rewritten module. The
  binding README links to repository documents by absolute URL, since JSR
  resolves relative links against its own pages.

### Added

- Experimental WebAssembly distribution. Configuring with Emscripten
  (`emcmake cmake`) builds the complete public C API (`morpheus.h` and
  `compat.h`) into `morpheus.mjs` plus `morpheus.wasm` through the new
  `MORPHEUS_BUILD_WASM` option, and compiles the native C test suite to
  WebAssembly so `ctest` runs it under Node.js against the same object code.
  A JavaScript facade under `bindings/js/wasm/` marshals the fixed-layout
  result structures for browsers, workers, Node.js, Deno and Bun. The module
  contains no linguistic data. See `docs/wasm.md`.
- `bench/compare.ts` measures the WebAssembly module next to the native FFI
  path when `MORPHEUS_WASM_MODULE` is set: warm analysis and generation over
  a pool of Deno workers sharing one compiled module, cold instantiation, and
  both data placements (`--wasm-data memfs,nodefs`). WebAssembly measurements
  are optional in baseline comparisons.
- The WebAssembly facade accepts a precompiled `wasmModule`, which is how a
  Cloudflare Worker (`.wasm` import) or a worker pool (one compile, shared by
  `postMessage`) instantiates it; the stamped `morpheus.mjs` no longer takes
  Emscripten's Node.js path on runtimes without `import.meta.url`. The binding
  README documents the recommended configuration for servers, browsers and
  Cloudflare Workers, the latter exercised with `wrangler dev`.
- WebAssembly binding 0.1.1, compiled from this release, with the JSR
  import-name mapping above. 0.1.0 remains usable from npm.
- WebAssembly binding release track. `bindings/js/wasm/` is packaged as
  `@libmorpheus/wasm` for npm (`package.json`) and JSR (`jsr.json`) from one
  directory; `internal/version.mjs` declares the binding version, the
  libmorpheus release and ABI compiled into the module, and the Emscripten
  release that reproduces it, which the module header now also records. The
  facade loads `morpheus.wasm` itself when the package is served from a
  registry, and the stamped loader takes Emscripten's Node.js path only for
  modules loaded from `file:` URLs. `wasm_package_metadata` checks both
  manifests, the version coupling to the tree, the closed file set and the
  absence of linguistic data; `wasm-release.yml` publishes on `wasm-v*` tags
  after rebuilding the module and requiring byte-for-byte reproduction of the
  qualified artifact. `bindings/js/wasm/tools/bootstrap-npm.mjs` stages the
  inert `0.0.0` placeholder that the one-time manual npm reservation needs
  before trusted publishing can be configured, as the Node.js track does.

### Changed

- The runtime now builds cleanly on ILP32 targets (32-bit `long`, as on
  wasm32): `morphkeys.c` casts the stem-type word explicitly and
  `retrentry.c` refuses a pre-index offset that `long` cannot represent
  instead of narrowing it silently. LP64 behaviour is unchanged.
- The internal Emscripten generation preparer honours an explicit `MORPHLIB`
  instead of overriding it, so the same program runs under the host file
  system in the WebAssembly test build. The checked-in Deno and Node.js
  preparer modules are regenerated from the updated sources.

## [0.4.2] - 2026-09-28

Target project version: **0.4.2**. C ABI: **2**. Shared-library SONAME: **1**.

### Fixed

- Analysis storage now shares its mutable pointer, count and capacity between
  copied `gk_word` values. This prevents a double `free` and process abort on
  forms such as `a)mfestan` after the 0.4.1 growth change. The 46 reported
  crashing forms and a sweep of the pinned Alpheios lemma list are regression
  tests, including in the sanitizer build.

## [0.4.1] - 2026-09-28

Target project version: **0.4.1**. C ABI: **2**. Shared-library SONAME: **1**.

**Known regression:** native 0.4.1 may abort the process while analyzing some
Greek forms when its analysis array grows. The Deno 0.4.1 binding acquires that
native version. Do not deploy either 0.4.1 release for untrusted searches.

### Fixed

- Greek analysis now grows its result storage on demand instead of failing
  with an internal error at 25 analyses. The legacy `cruncher` print buffer
  also grows for larger result sets. Allocation failures remain memory errors.

### Changed

- All 229 reviewed binary stem-table differences are now decoded and compared
  record by record with their checked-in Perseids baselines. Duplicate
  morphology registry names now resolve deterministically to their last
  definition, removing the six `illw.out` differences. Of the 229 files, 228
  are semantically identical; the twelve historical `er_eris.out` numeric-ID
  differences remain pinned separately. Any other decoded difference fails
  qualification. The checked-in Deno and Node WebAssembly preparers are
  regenerated from the same deterministic lookup implementation.
- Stemlib production no longer requires Perl. The sole active Perl transform,
  Greek nominal entity constraints, now has a byte-identical MPL-licensed
  Python implementation; the original script remains a checksum-pinned
  historical reference. The reference qualification profile now requires only
  GCC 14 and Python 3.12 in addition to its Ubuntu 24.04 x86-64 platform.
- Stemlib lexical qualification now runs with an empty executable search path,
  proving that no ambient Perl or shell utility is used. Two context tests use
  build-local named streams instead of relying on a writable system temporary
  directory, and the runtime-error fixture likewise falls back to its test
  working directory. Table and lexical qualification serialize access to their
  shared evidence workspace so concurrent CTest runs cannot corrupt a build.

## [0.4.0] - 2026-09-17

Target project version: **0.4.0**. C ABI: **2**. Shared-library SONAME: **1**.

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
