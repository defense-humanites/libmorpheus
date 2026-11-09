<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# libmorpheus 0.4.6

This native release makes analysis faster without changing any result, and
fixes a memory leak in the generation source preparer. It is the
release WebAssembly binding 0.1.4 is compiled from and declares
([release-wasm-0.1.4.md](release-wasm-0.1.4.md)).

## Why a new version

The N-API / WebAssembly comparison of 2026-11-09 (pull request #60,
[wasm.md](wasm.md#controlled-host-2026-11-09)) showed the WebAssembly module
analyzing faster than the native library on the controlled Apple Silicon
host: `cruncher-persistent` took 630 µs per word against 404 µs for the
module with MEMFS. Profiling `cruncher` (callgrind on Linux, `sample` on
macOS) found the cause in the runtime itself, not in the bindings.

`xfer_prvbflags()`, which `ScanAsciiKeys()` calls for every candidate key,
tested each of the 112 morph flag numbers through `is_prvb_morphflag()`,
which reads the runtime context, a `_Thread_local`, on every call. In a
shared library each such read goes through `__tls_get_addr` (Linux) or
`_tlv_get_addr` (macOS); the single-threaded WebAssembly build reads a
plain global. The transfer and the reads it caused were 52.6 % of all
instructions of an analysis on Linux and 57.8 % of the macOS samples.

Pull request #61 read the table once per transfer. Pull request #62 then
removed the next five costs the profiles showed:

- `xfer_prvbflags()` tests the eight preverb flags directly and no longer
  reads the context; `init_prvb_tab()` builds its table from the same list.
- `morphstrcmp()`, `morphstrncmp()`, `dictstrcmp()` and `dictstrncmp()`
  compare through a fixed byte mapping (the iota subscript as `i`); the
  per-context table they read was identical in every context.
- `MatchMorphKey()` reads the context once instead of up to seven times.
- `has_rawpreverb()` rejects a raw preverb whose first byte differs before
  measuring and comparing it.
- `ChckFullIndex()` keeps the stem index files it reads open per context,
  keyed by full path (at most four), and closes them when the context is
  destroyed, or at once after a failed seek or read. An analysis opened and
  closed `steminds/nomind` about five times per word.

Pull request #63 fixed the leak: `do_euph()` returns an allocated array, and
the derivation expansion (`conjoin_rule()`) and the legacy conjugator
(`conjoinX()`) kept its first form without freeing it, 311,460 bytes in 537
allocations over the generation corpus. That code is linked only by the
generation source preparer (`morpheus_gener_derivation`, also compiled to
WebAssembly for `@libmorpheus/data`) and the `do_conj` stemlib tool, not by
the library or the WebAssembly module. CI had not seen the leak because the
sanitizer job ran with `detect_leaks=0`; it now runs with leak detection.

## Results and compatibility

Results are unchanged. `cruncher` output is byte-identical to that of
`v0.4.5` over 4,176 Greek lemmas (every eighth line of the Alpheios
`lemlist`), the benchmark corpus and 192 Latin irregular forms (Perseids);
the generation corpus test keeps its digests, and the WebAssembly
generation preparer still yields the pinned `gener.index`
(`5aa76d8c…`). The native suite, AddressSanitizer/UBSan with leak detection
and ThreadSanitizer pass.

The public C API and ABI are unchanged from 0.4.1 through 0.4.5. One
behaviour is new: a context now holds up to four more open files (its stem
indices) for its lifetime. An application that keeps many contexts open
should count four file descriptors per context, and every application
should destroy contexts it no longer uses, as before.

The native archives contain no stemlib data. The Node.js and Python bindings
keep declaring native 0.4.5; they receive the faster runtime once a binding
release declares 0.4.6. `@libmorpheus/data` 0.1.0 stays current: its
generation preparer, rebuilt in the tree, prepares the same index.

## Measured effect

`cruncher -T` on the 24 benchmark words repeated 1,000 times (24,000
words), alternating builds, byte-identical outputs:

| Host | `v0.4.5` sources | after #61 | after #62 |
| --- | --- | --- | --- |
| Apple Silicon, Apple Clang 2100.4.1.1 (maintainer) | 15.0 / 14.6 s | 8.4 / 7.8 s, then 8.1 / 8.1 s | 5.1 / 4.7 s |
| 2-vCPU Linux sandbox, GCC | 28.5 s | 16.3 s | 10.2 s |

About 205 µs per word on the controlled host, against 610 µs before. The
macOS profile after #62 leaves no runtime overhead at the top: file system
calls fall from 14.0 % to 3.4 % of the samples and the context reads with
the preverb transfer from 20.2 % to 4.5 %; the rest is string copying and
comparison and the index search itself. The WebAssembly module built from
these sources analyzes about twice as fast as 0.1.3 with MEMFS on the
sandbox (765–795 µs against 1,505–1,520 µs per word at one context).

## Release record

- Project version: **0.4.6**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.4.5`
- Benchmark evidence: **accepted**
- Pre-release Linux CI: pending (the tagged commit's run)
- Pre-release platform qualification: pending (manual dispatch with
  `package_artifacts` on the exact candidate commit)

## Benchmark evidence

The schema 3 report from source revision
`f1bfad784df8af7cea1e0a05c5fcb506c0c22161` (the merge of the release
preparation) uses the pinned Alpheios stemlib revision
`4632415fe93c85e9fdca47a0c5a13f31385f0023` on the controlled Apple Silicon
host, with the toolchain of the baseline (Apple Clang 21 build 2100.4.1.1,
Node.js 26.13.0, binding 0.1.3, libuv thread pool of four). It is retained
as [`benchmark-0.4.6.json`](../bench/release-evidence/benchmark-0.4.6.json);
its SHA-256 is
`1ada96f98cf069ced13384198f3defa4e3f9de228d68d9960d44f3dd0241f448`. The
release validator passes with the recorded source revision and compiler,
and the comparison with
[`benchmark-0.4.5-node-packed.json`](../bench/release-evidence/benchmark-0.4.5-node-packed.json),
the schema 3 baseline measured through the Node.js binding on the `v0.4.5`
sources, has `complete` scope. All thirteen result counts equal the
baseline's.

| Row | 0.4.5 (µs) | 0.4.6 (µs) | Change |
| --- | --- | --- | --- |
| `node`, 1 context | 649 | 215 | −66.9 % |
| `node`, 2 contexts | 412 | 132 | −67.9 % |
| `node`, 4 contexts | 276 | 88 | −68.3 % |
| `cruncher-persistent` | 650 | 202 | −68.9 % |
| `cruncher-cold` | 3,269 | 2,743 | −16.1 % |
| maximal generation, warm, 1 / 2 / 4 contexts | 6,284 / 3,670 / 3,838 | 5,729 / 3,598 / 3,751 | −8.8 / −2.0 / −2.3 % |
| small generation, warm, 1 / 2 / 4 contexts | 120 / 28 / 33 | 120 / 27 / 31 | −0.2 / −2.9 / −5.7 % |
| maximal / small generation, cold | 22,555 / 15,032 | 21,077 / 14,820 | −6.6 / −1.4 % |

Analysis throughput triples at every width (+202 %, +212 % and +215 %),
beyond the halving the preparation expected: the release benchmark analyzes
the same 24 words, whose candidate keys pass through the changed paths, and
agrees with the `cruncher` A/B above (about 205 µs per word). The binding
adds little next to the runtime, before as after: `node` at one context is
within 13 µs of `cruncher-persistent` (215 against 202 µs; 649 against
650 µs in the baseline). `cruncher-cold` gains less because process
start-up and the first loading of the indices dominate one analysis per
process. Generation moves by −0.2 % to −8.8 %, all in the same direction
but within the run-to-run variation recorded for those rows; no claim is
made for it.

Peak RSS is within −2.9 % to +7.8 % of the baseline on every row. The RSS
growth of the two- and four-context analysis rows (3.6 and 0.5 MiB against
0.5 and 2.6 MiB) moves by a few MiB in opposite directions, as the order of
allocations within one process does; no row shows the four kept-open index
files, whose stdio buffers are a few KiB per context. This report replaces
`benchmark-0.4.5-node-packed.json` as the baseline of the next native
release.

## Remaining authorization

Before publication, a maintainer must:

1. run `bench/release.sh` on the candidate commit on the controlled host,
   have the report reviewed against the baseline and committed with its
   sidecar as `bench/release-evidence/benchmark-0.4.6.json`;
2. dispatch the platform workflow with `package_artifacts` for the candidate
   commit and inspect the three native archives;
3. confirm the final tagged Linux CI and platform runs and record their links
   above;
4. explicitly authorize creation of `v0.4.6`, then of `wasm-v0.1.4` on the
   same commit or a descendant with an unchanged runtime.
