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
- Benchmark evidence: pending (maintainer's schema 3 report from the
  controlled Apple Silicon host, on the candidate commit)
- Pre-release Linux CI: pending (the tagged commit's run)
- Pre-release platform qualification: pending (manual dispatch with
  `package_artifacts` on the exact candidate commit)

## Expected benchmark outcome

The release report is compared with
[`benchmark-0.4.5-node-packed.json`](../bench/release-evidence/benchmark-0.4.5-node-packed.json),
the schema 3 baseline measured through the Node.js binding on the `v0.4.5`
sources (`complete` scope):

```sh
sh bench/release.sh benchmark-0.4.6.json \
  bench/release-evidence/benchmark-0.4.5-node-packed.json
```

All thirteen result counts must equal the baseline's. The analysis rows
(`node` at one, two and four contexts, `cruncher-persistent`) should fall by
roughly half, as `cruncher` does above; `cruncher-cold` less, since one
analysis per process pays start-up. Generation reads its index rather than
scanning keys and shares fewer of the changed paths; its rows may move
less, in either direction within noise. The report records `runtime.uvThreadpoolSize` (four, the default, for one to
four contexts).

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
