<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Runtime benchmarks

`bench/compare.ts` measures the production-facing Deno FFI path for analysis
and generation and compares analysis with the compatibility `cruncher` client
on the same Beta Code corpus. It is a manual benchmark rather than a CI
performance gate: shared runners execute only one-iteration protocol smoke
tests.

Build the normal runtime first, then run:

```sh
cmake --preset dev
cmake --build --preset dev

MORPHEUS_LIBRARY="$PWD/build/dev/libmorpheus.so" \
MORPHEUS_STEMLIB="$PWD/stemlib" \
MORPHEUS_CRUNCHER="$PWD/build/dev/cruncher" \
deno run --allow-env --allow-ffi --allow-read --allow-run \
  bench/compare.ts \
  --iterations 20 \
  --warmup 2 \
  --contexts 1,2,4 \
  --cold-samples 10 \
  --generation-small 'lo/gos' \
  --generation-maximal 'i(/hmi'
```

Use `libmorpheus.dylib` on macOS. Pass `--json` to produce a machine-readable
report suitable for archiving with a release or deployment evaluation.

Release reports should identify the exact code, data, and compiler inputs:

```sh
MORPHEUS_LIBRARY="$PWD/build/release/libmorpheus.so" \
MORPHEUS_STEMLIB="$PWD/vendor/alpheios-morpheus/dist/stemlib" \
MORPHEUS_CRUNCHER="$PWD/build/release/cruncher" \
deno run --allow-env --allow-ffi --allow-read --allow-run \
  bench/compare.ts --json \
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

Pass a previous report as the second argument to add the normalized comparison:

```sh
sh bench/release.sh benchmark-0.4.0.json \
  bench/release-evidence/benchmark-0.3.2.json
```

The accepted 0.2.0 baseline is
[`benchmark-0.2.0.json`](https://github.com/defense-humanites/libmorpheus/releases/download/v0.2.0/benchmark-0.2.0.json)
with SHA-256
`d877dadd080a31ae75c8f970fb179a6638b54a2db0afd11c336eb9b2e33cf977`.
It uses schema 1 and therefore compares only the five historical analysis
configurations. Generation was introduced in schema 2; the first accepted
0.3.0 report establishes its performance baseline instead of fabricating a
comparison with 0.2.0.

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

The 0.4.0 candidate must be measured from its exact finalized source revision
against the accepted 0.3.2 report on the same controlled host. Its report is
not accepted evidence until the comparison has been reviewed, copied to
`bench/release-evidence/benchmark-0.4.0.json`, and accompanied by its SHA-256
sidecar and an updated release decision.

The wrapper refuses a dirty tracked worktree or submodule, an uninitialized or
displaced Alpheios submodule, and an existing output path. Its label, stemlib
path, iteration counts, warmup, context list, and cold-sample count can be
overridden through the environment variables documented in the script without
weakening the release-report validator.

Before accepting the file as release evidence, validate both its completeness
and the revisions it claims:

```sh
deno run --allow-read bench/validate.ts benchmark.json \
  --label release-candidate \
  --revision "$(git rev-parse HEAD)" \
  --stemlib-revision "$(git -C vendor/alpheios-morpheus rev-parse HEAD)" \
  --compiler "$(cc --version | head -n 1)"
```

The validator requires full 40-character Git object IDs, compiler and platform
metadata, SHA-256 identities for both the analysis corpus and complete
generation index, analysis FFI with 1, 2, and 4 contexts, persistent and cold
`cruncher`, and both generation workloads with 1, 2, and 4 warm contexts plus
cold samples. It does not impose timing thresholds; accepting or rejecting a
measured regression remains an explicit release decision.

Benchmark schema 2 records the Deno runtime, target platform, hardware
concurrency, corpus path and SHA-256 digest, generation lemmas and index digest,
source and stemlib revisions, compiler label, run parameters, and raw
measurements. The revision and compiler values may instead be supplied through
`MORPHEUS_BENCHMARK_REVISION`, `MORPHEUS_STEMLIB_REVISION`, and
`MORPHEUS_BENCHMARK_COMPILER`.

## Measurements

The runner reports seven execution models:

- `ffi`: structured analysis through the Deno binding, including native result
  copying into TypeScript objects. Each configured context count is measured;
  work is distributed evenly and each context retains its required serial
  queue.
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
where it can be isolated. FFI measurements also sample the Deno process RSS,
which includes the loaded native library, contexts, caches, native results, and
copied TypeScript objects.

The persistent-process startup is included in its elapsed time and amortized
over every measured word; it is not reported separately. The cold-process
startup value is the mean end-to-end duration per sample. RSS for child
`cruncher` processes is not currently sampled, so memory columns are reported
only for FFI measurements.

The default corpus is the set of unique `input` values from the option-free
Greek fixtures in `test/fixture.json`. This keeps both engines in their shared
strict-case mode; Latin, `-n`, and `-S` variants are excluded instead of being
measured under mismatched settings. Fixture output is deliberately not
compared: this benchmark measures analysis execution, not differential
correctness. Those contracts remain covered by the fixture tests.

## Interpreting results

Run benchmarks on otherwise idle native hardware, use a release build for
deployment decisions, and retain the JSON report with compiler, Deno, stemlib,
CPU, and operating-system metadata. Compare at least:

1. single-context analysis FFI latency against persistent-`cruncher` throughput;
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
deno run --allow-env --allow-ffi --allow-read --allow-run \
  bench/compare.ts --baseline previous.json --json > current.json
```

The output adds percentage changes for throughput, mean latency, peak RSS, and
RSS growth. Positive throughput is an improvement; positive latency or memory
is an increase. Schema 2 baselines require matching corpus and generation-index
digests, generation lemmas, and every engine/context pair. A schema 1 baseline
must use the same corpus and contain only historical analysis configurations;
each must exist in the current report. New schema 2 generation measurements are
deliberately omitted from that legacy comparison.

No timing threshold is enforced in CI because shared-runner variance would make
it unstable. CI type-checks the runner, tests report comparison and corpus
validation deterministically, tests the release-evidence validator, and
executes a one-iteration end-to-end smoke run. Release decisions use repeated
measurements on controlled hardware.
