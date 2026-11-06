<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Runtime benchmarks

`bench/compare.mjs` measures the native library through the Node.js binding
(`bindings/js/node`, a Node-API addon) for analysis and generation and
compares analysis with the compatibility `cruncher` client on the same Beta
Code corpus. It is a manual benchmark rather than a CI performance gate:
shared runners execute only one-iteration protocol smoke tests.

The harness is plain Node.js (20 or later, ECMAScript modules, no
dependencies): `bench/compare.mjs` runs the measurements, `bench/report.mjs`
holds the report schema, the comparison and the release validation,
`bench/validate.mjs` is the validator's command line, and
`bench/wasm-runtime.mjs`, `bench/wasm-pool.mjs` and `bench/wasm-worker.mjs`
drive the optional WebAssembly models. Reports up to 0.4.5 (schema 2) were
produced by a Deno harness measuring the Deno FFI binding; the Node.js
harness produces schema 3 and establishes a new baseline, since the
measured binding changed (see [Comparing reports](#comparing-reports)).

Build the runtime and the addon first, then run:

```sh
cmake --preset dev -DMORPHEUS_BUILD_NODE_BINDING=ON
cmake --build --preset dev

MORPHEUS_LIBRARY="$PWD/build/dev/libmorpheus.so" \
MORPHEUS_NODE_ADDON="$PWD/build/dev/node/libmorpheus_node.node" \
MORPHEUS_STEMLIB="$PWD/stemlib" \
MORPHEUS_CRUNCHER="$PWD/build/dev/cruncher" \
node bench/compare.mjs \
  --iterations 20 \
  --warmup 2 \
  --contexts 1,2,4 \
  --cold-samples 10 \
  --generation-small 'lo/gos' \
  --generation-maximal 'i(/hmi'
```

Use `libmorpheus.dylib` on macOS. The addon opens the library named by
`MORPHEUS_LIBRARY`; it is built against the Node-API headers of the `node`
on `PATH` (`-DMORPHEUS_NODE_INCLUDE_DIR` names another installation). Pass
`--json` to produce a machine-readable report suitable for archiving with a
release or deployment evaluation.

Release reports should identify the exact code, data, and compiler inputs:

```sh
MORPHEUS_LIBRARY="$PWD/build/release/libmorpheus.so" \
MORPHEUS_NODE_ADDON="$PWD/build/release/node/libmorpheus_node.node" \
MORPHEUS_STEMLIB="$PWD/vendor/alpheios-morpheus/dist/stemlib" \
MORPHEUS_CRUNCHER="$PWD/build/release/cruncher" \
node bench/compare.mjs --json \
  --label release-candidate \
  --revision "$(git rev-parse HEAD)" \
  --stemlib-revision "$(git -C vendor/alpheios-morpheus rev-parse HEAD)" \
  --compiler "$(cc --version | head -n 1)" \
  > benchmark.json
```

On the controlled Linux or macOS host selected for release qualification, the
complete configure, build, CTest, benchmark, and validation sequence is wrapped
by:

```sh
sh bench/release.sh benchmark-0.4.0.json \
  bench/release-evidence/benchmark-0.3.2.json
```

The wrapper uses the checksummed complete index produced by the `gener_corpus`
CTest and exposes it through a temporary stemlib root. It never writes
`gener.index` into the tracked stemlib or the pinned Alpheios submodule.

## WebAssembly execution models

Setting `MORPHEUS_WASM_MODULE` to a built `morpheus.mjs` (see
[wasm.md](wasm.md)) adds the WebAssembly module to the same run, on the same
corpus, context counts and generation lemmas, so the native and WebAssembly
numbers in one report are directly comparable:

```sh
MORPHEUS_LIBRARY="$PWD/build/release/libmorpheus.so" \
MORPHEUS_NODE_ADDON="$PWD/build/release/node/libmorpheus_node.node" \
MORPHEUS_STEMLIB="$PWD/stemlib" \
MORPHEUS_CRUNCHER="$PWD/build/release/cruncher" \
MORPHEUS_WASM_MODULE="$PWD/build/wasm/wasm/morpheus.mjs" \
node bench/compare.mjs --iterations 20 --warmup 2 --contexts 1,2,4
```

The module is measured under both data placements the facade offers, selected
with `--wasm-data memfs,nodefs` (default both):

- `memfs`: the Greek runtime subset of the stemlib (`rule_files/`, the stem
  and ending indices, `endtables/out/`, `derivs/indices/derivind`,
  `stemsrc/{vbs.cmp.ml,lemlist}`, and `gener.index` when present) is read once
  by the main thread and written into each instance's memory. Every `read()`
  the runtime makes is a copy inside the module; no system call is involved.
  This is the placement a server deployment should use.
- `nodefs`: each language directory is mounted from the host, so every
  `open`/`seek`/`read`/`close` of the historical lookup pattern is a real
  system call reached through Emscripten's JavaScript file system layer.

Warm measurements (`wasm-<mode>`, `wasm-<mode>-generation-<lemma>-warm`) run
over a pool of worker threads, one WebAssembly instance and one Greek context
per worker, with the `WebAssembly.Module` compiled once and shared through
structured cloning (`bench/wasm-pool.mjs`, `bench/wasm-worker.mjs`); word
assignment is identical to the native model operation for operation. Their
`startup_ms` covers worker spawn, instantiation, data placement and context
creation. Cold measurements (`wasm-<mode>-cold`,
`wasm-<mode>-generation-<lemma>-cold`) compile and instantiate the module from
its bytes, place the data, open one context and run one operation per sample
in the main thread, the counterpart of `cruncher-cold`.

The report records `wasmModule`, `wasmModuleSha256` and `wasmRuntimeBytes` (the
MEMFS payload per instance). WebAssembly measurements are optional additions:
`--baseline` compares them only when the baseline contains the same engine and
context count, and the release validation does not require them.
`bench/release.sh` passes the variable through unchanged, so exporting
`MORPHEUS_WASM_MODULE` before running it adds the models to a release report.

Pass a previous report as the second argument to add the normalized comparison:

```sh
sh bench/release.sh benchmark-0.4.0.json \
  bench/release-evidence/benchmark-0.3.2.json
```

The schema 1 reports published with the first five native releases,
`v0.1.0` to `v0.2.0`, are retained under
[`bench/release-evidence/`](../bench/release-evidence/) with the SHA-256
sidecars published next to them; the retained files are byte for byte the
release assets. Each was produced on the controlled Apple Silicon host from
the exact commit its tag selects, with the Alpheios stemlib at
`4632415fe93c85e9fdca47a0c5a13f31385f0023`, and measures the five
historical analysis configurations only. The accepted 0.2.0 baseline is
[`benchmark-0.2.0.json`](../bench/release-evidence/benchmark-0.2.0.json)
with SHA-256
`d877dadd080a31ae75c8f970fb179a6638b54a2db0afd11c336eb9b2e33cf977`.
Generation was introduced in schema 2; the first accepted 0.3.0 report
establishes its performance baseline instead of fabricating a comparison
with 0.2.0. The release validator accepts schemas 2 and 3 only, so the
schema 1 reports are checked for integrity, not revalidated, by the
`release_metadata` test, which verifies every retained sidecar.

The accepted 0.3.0 preparation report is retained at
[`bench/release-evidence/benchmark-0.3.0.json`](../bench/release-evidence/benchmark-0.3.0.json)
with its companion SHA-256 file. The version-tag workflow verifies that
sidecar and publishes both files with the release assets.

The accepted 0.3.1 report is retained at
[`bench/release-evidence/benchmark-0.3.1.json`](../bench/release-evidence/benchmark-0.3.1.json)
with its companion SHA-256 file. It measures the Deno distribution candidate
against the accepted 0.3.0 evidence on the same controlled Apple Silicon host.
The native analysis and generation implementation, corpus, stemlib revision,
and generation-index digest are unchanged; the release decision records the
accepted comparison.

The accepted 0.3.2 report is retained at
[`bench/release-evidence/benchmark-0.3.2.json`](../bench/release-evidence/benchmark-0.3.2.json)
with its companion SHA-256 file. It compares the corrected Deno distribution
candidate with 0.3.1 on the same controlled Apple Silicon host. The measured
analysis and generation paths, corpus, stemlib revision, and generation-index
digest are unchanged; the release decision records the accepted comparison.

The accepted 0.4.0 report is retained at
[`bench/release-evidence/benchmark-0.4.0.json`](../bench/release-evidence/benchmark-0.4.0.json)
with its companion SHA-256 file. It measures the finalized stemlib-production
candidate against 0.3.2 on the same controlled Apple Silicon host. The release
decision records the reviewed timing and process-memory comparison.

The accepted 0.4.1 report is retained at
[`bench/release-evidence/benchmark-0.4.1.json`](../bench/release-evidence/benchmark-0.4.1.json)
with its companion SHA-256 file. Its release decision records the measured
comparison with 0.4.0.

The accepted 0.4.2 report is retained at
[`bench/release-evidence/benchmark-0.4.2.json`](../bench/release-evidence/benchmark-0.4.2.json)
with its companion SHA-256 file. It compares the corrected allocation path
against 0.4.1 on the same controlled Apple Silicon host; see the 0.4.2 release
decision for the reviewed results and the short warm-generation measurement.

The accepted 0.4.3 report is retained at
[`bench/release-evidence/benchmark-0.4.3.json`](../bench/release-evidence/benchmark-0.4.3.json)
with its companion SHA-256 file. It measures the provenance release against
0.4.2 on the same controlled Apple Silicon host; the native paths are
unchanged and the 0.4.3 release decision records the within-noise comparison
and identical result counts.

The accepted 0.4.4 report is retained at
[`bench/release-evidence/benchmark-0.4.4.json`](../bench/release-evidence/benchmark-0.4.4.json)
with its companion SHA-256 file. It measures the single-request index
loaders against 0.4.3 on the same host; result counts are identical, warm
latencies are within noise, the cold `cruncher` falls 15 %, and the 0.4.4
release decision explains the Deno-version-dependent RSS growth of the
four-context maximal generation.

The accepted 0.4.5 report is retained at
[`bench/release-evidence/benchmark-0.4.5.json`](../bench/release-evidence/benchmark-0.4.5.json)
with its companion SHA-256 file. It measures the stem-class release against
0.4.4 on the same host and toolchain; result counts are identical,
latencies are within noise, and the 0.4.5 release decision revises the
reading of the four-context maximal generation's RSS growth, which the
report shows to vary between runs under one Deno version.

The first schema 3 report, from the Node.js harness, is retained at
[`bench/release-evidence/benchmark-0.4.5-node.json`](../bench/release-evidence/benchmark-0.4.5-node.json)
with its companion SHA-256 file. It was produced on 2026-11-06 on the same
controlled Apple Silicon host and toolchain as the 0.4.5 report (Apple
Clang 2100.4.1.1; Node.js 26.13.0, binding 0.1.2), from the merge of the
harness migration, whose native sources are those of `v0.4.5`. It is the
baseline of the native binding, generation and cold rows for the next
release; its `cruncher-persistent` row, the one compared with the 0.4.5
report, differs by +0.1 %. The addendum of the
[0.4.5 release decision](release-0.4.5.md#addendum-nodejs-harness-baseline)
records what the two harnesses measure differently on an unchanged
library.

The second schema 3 report on the same sources,
[`bench/release-evidence/benchmark-0.4.5-node-packed.json`](../bench/release-evidence/benchmark-0.4.5-node-packed.json)
with its companion SHA-256 file, was produced on 2026-11-06 on the same
host from `2e8ebe63c6d0f915390c06e351e77efe3a8d25d8`, the merge of the
Node.js binding's packed result encoding (issue #47, pull request #48),
with the native sources still those of `v0.4.5`. Compared with the first
report (`complete` scope), the thirteen result counts are identical,
analysis and the `cruncher` rows are within noise, and generation falls by
44 to 58 % per warm operation (maximal paradigm: 6.3, 3.7 and 3.8 ms at
one, two and four contexts against 11.2, 8.7 and 8.7 ms) and 15 % cold,
now below the Deno-harness figures. **This report is the baseline of the
next native release**: the harness measures through the binding, and a
comparison with the earlier report would attribute the binding's change
to the library.

The wrapper refuses a dirty tracked worktree or submodule, an uninitialized or
displaced Alpheios submodule, and an existing output path. Its label, stemlib
path, iteration counts, warmup, context list, and cold-sample count can be
overridden through the environment variables documented in the script without
weakening the release-report validator.

Before accepting the file as release evidence, validate both its completeness
and the revisions it claims:

```sh
node bench/validate.mjs benchmark.json \
  --label release-candidate \
  --revision "$(git rev-parse HEAD)" \
  --stemlib-revision "$(git -C vendor/alpheios-morpheus rev-parse HEAD)" \
  --compiler "$(cc --version | head -n 1)"
```

The validator requires full 40-character Git object IDs, compiler and platform
metadata, SHA-256 identities for both the analysis corpus and complete
generation index, native analysis with 1, 2, and 4 contexts, persistent and
cold `cruncher`, and both generation workloads with 1, 2, and 4 warm contexts
plus cold samples. It does not impose timing thresholds; accepting or
rejecting a measured regression remains an explicit release decision. It
accepts schema 3 (native engine `node`, Node.js runtime and binding version
recorded) and the retained schema 2 reports (native engine `ffi`, Deno
runtime recorded).

Benchmark schema 3 records the Node.js, V8 and libuv versions, the operating
system, architecture and kernel release, the binding package and version,
hardware concurrency, corpus path and SHA-256 digest, generation lemmas and
index digest, source and stemlib revisions, compiler label, run parameters,
and raw measurements. The revision and compiler values may instead be
supplied through `MORPHEUS_BENCHMARK_REVISION`, `MORPHEUS_STEMLIB_REVISION`,
and `MORPHEUS_BENCHMARK_COMPILER`.

## Measurements

The runner reports seven execution models:

- `node`: structured analysis through the Node.js binding, including the
  copy of native results into JavaScript objects (`ffi` in schema 2 reports:
  the same measurement through the Deno binding). Each configured context
  count is measured; work is distributed evenly and each context retains its
  required serial queue. Its `startup_ms` for the first context count
  includes loading the library and binding its symbols.
- `cruncher-persistent`: all measured words are sent through one `cruncher`
  process. Its one-time startup is amortized over the corpus, approximating the
  throughput behavior of a retained process worker. The measurement includes
  the compatibility formatter and pipe writes; standard output is discarded
  only after those costs have been paid.
- `cruncher-cold`: one process is started for each sample. This quantifies the
  startup cost but does not represent a persistent production process pool.
- `generation-small-warm` and `generation-maximal-warm`: the complete index is
  loaded before timing, then one lemma is generated repeatedly through each
  configured context count. `lo/gos` is the representative small paradigm;
  `i(/hmi`, whose qualified source block contains 544 explicit records, is the
  maximal workload.
- `generation-small-cold` and `generation-maximal-cold`: every sample creates a
  new context and performs its first generation lookup. This includes index
  validation and per-context service initialization. Operating-system file
  caches are not flushed, so it is a cold-context measurement, not a cold-disk
  benchmark.

For each model the report includes elapsed time, operations per second, mean
time per operation, returned result records where available, and startup time
where it can be isolated. Native binding measurements also sample the
process RSS, which includes the loaded native library, contexts, caches,
native results, and copied JavaScript objects.

The persistent-process startup is included in its elapsed time and amortized
over every measured word; it is not reported separately. The cold-process
startup value is the mean end-to-end duration per sample. RSS for child
`cruncher` processes is not currently sampled, so memory columns are reported
only for in-process measurements.

The default corpus is the set of unique `input` values from the option-free
Greek fixtures in `test/fixture.json`. This keeps both engines in their shared
strict-case mode; Latin, `-n`, and `-S` variants are excluded instead of being
measured under mismatched settings. Fixture output is deliberately not
compared: this benchmark measures analysis execution, not differential
correctness. Those contracts remain covered by the fixture tests.

## Interpreting results

Run benchmarks on otherwise idle native hardware, use a release build for
deployment decisions, and retain the JSON report with compiler, Node.js,
stemlib, CPU, and operating-system metadata. Compare at least:

1. single-context analysis latency against persistent-`cruncher` throughput;
2. analysis and warm generation scaling across context counts;
3. small versus maximal generation latency and returned record counts;
4. RSS growth per additional warmed context and workload;
5. cold context/index initialization and cold process startup as diagnostics.

Do not infer a production context count from shared CI results. Increase the
context count only while throughput improves without unacceptable RSS growth or
tail latency in the calling application.

## Comparing reports

Pass a prior JSON report with `--baseline` to compare matching engine/context
configurations:

```sh
node bench/compare.mjs --baseline previous.json --json > current.json
```

The output adds percentage changes for throughput, mean latency, peak RSS, and
RSS growth, with `comparisonBaselineSchemaVersion` and `comparisonScope`.
Positive throughput is an improvement; positive latency or memory is an
increase. A schema 3 baseline (`complete` scope) requires matching corpus and
generation-index digests, generation lemmas, and every native engine/context
pair; WebAssembly rows absent from the baseline are skipped.

A schema 1 or 2 baseline was measured by the retired Deno harness: its `ffi`
and generation rows timed the Deno FFI binding and its cold rows include
Deno's process spawning, so none of them is comparable with the Node.js
binding's rows, however close the native work is. With such a baseline the
scope is `cross-runtime` and only `cruncher-persistent` is compared: that row
times one `cruncher` process over the whole measured corpus, where the
harness's spawn and pipe costs are amortized over hundreds of operations.
The first schema 3 report accepted as release evidence therefore
establishes the baseline of the native binding, generation and cold rows;
the release decision records the `cruncher-persistent` continuity with the
schema 2 evidence instead of fabricating the other comparisons.

No timing threshold is enforced in CI because shared-runner variance would make
it unstable. CI tests report comparison, corpus validation and the
release-evidence validator deterministically (`node --test bench/test`),
validates the accepted 0.4.5 evidence, and executes a one-iteration
end-to-end smoke run against the retained schema 3 baseline, checking
that every measured row is compared. Release decisions use repeated
measurements on controlled hardware.
