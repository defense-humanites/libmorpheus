<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# WebAssembly build

The runtime compiles to WebAssembly with Emscripten. The result is one ES
module, `morpheus.mjs`, that loads a side file `morpheus.wasm` and exports the
complete public C API: every function of `morpheus.h` and `compat.h`, plus
`malloc`/`free` and a version probe. The module is a library (no `main`), is
single-threaded, and carries no linguistic data. The JavaScript facade in
[`bindings/js/wasm/`](../bindings/js/wasm/README.md) sits on top of it.

This page records why the port is small, how it is built, and how it is
qualified.

## Why the runtime ports cleanly

- **The disk format is width-independent.** Stemlib records use explicit
  8/16/32-bit little-endian words decoded byte by byte; neither pointers nor
  `long` reach the files. `wasm32` is a little-endian ILP32 target and reads
  the same stemlibs as native LP64 builds.
- **The public structures are fixed-layout.** `morpheus_analysis` (852 bytes)
  and `morpheus_generation` (188 bytes) contain only `uint32_t` words,
  fixed-capacity `char` arrays and a `uint8_t` bit set, so their offsets are
  identical on `wasm32` and `x86-64`; the Deno binding's decoders apply
  unchanged.
- **I/O goes through `stdio`.** The runtime opens stemlib files with
  `fopen`/`fread`/`fseek` and the compatibility layer writes through
  `open_memstream`, all of which Emscripten's musl provides. No `mmap`, no
  sockets, no `fork`.
- **Thread-local state is harmless without threads.** The runtime context uses
  `_Thread_local`; in a single-threaded module that is ordinary static
  storage.

Two source sites needed attention for ILP32, where `long` is 32 bits:
`morphkeys.c` now casts the 32-bit stem-type word explicitly when storing it in
a `Morph_flags` (`long`), and `retrentry.c` refuses a pre-index offset above
`LONG_MAX` instead of narrowing it. Both are no-ops on LP64.

## Build

Emscripten **4.0.15**, the version the project already pins for its internal
generation preparer, is the qualified toolchain. From an `emsdk_env.sh` shell:

```sh
emcmake cmake -S . -B build/wasm -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build build/wasm --target morpheus_wasm
ls build/wasm/wasm/   # morpheus.mjs morpheus.wasm
```

Under Emscripten the `morpheus` target is a static archive that feeds the
module link, and the native install and export rules are skipped. The module
is produced by the `morpheus_wasm` target, enabled by `MORPHEUS_BUILD_WASM`
(default `ON` under Emscripten, refused elsewhere). Its link policy:

| Flag | Purpose |
| --- | --- |
| `-sMODULARIZE=1 -sEXPORT_ES6=1 -sEXPORT_NAME=createMorpheusModule` | ES module exporting an async factory |
| `-sENVIRONMENT=web,worker,node` | One build for browsers, workers and Node.js-compatible runtimes |
| `-sFORCE_FILESYSTEM=1 -lnodefs.js` | Virtual file system (MEMFS) plus host-directory mounts under Node.js |
| `-sALLOW_MEMORY_GROWTH=1 -sSTACK_SIZE=4194304` | Growable heap; a 4 MiB stack for the analyzer's automatic buffers |
| `-sWASM_BIGINT=1` | `uint64_t` option masks cross the boundary as `BigInt` |
| `-sEXIT_RUNTIME=0 --no-entry` | Library semantics, no `main` |
| `-sEXPORTED_FUNCTIONS=…` | The public API, `_malloc`, `_free`, `_morpheus_wasm_module_version` |
| `-sEXPORTED_RUNTIME_METHODS=FS,HEAPU8,UTF8ToString,stringToUTF8,lengthBytesUTF8,getValue,setValue` | What the facade needs; nothing else is reachable |

`cmake/stamp-wasm-module.cmake` prefixes the generated `morpheus.mjs` with its
SPDX expression (`AGPL-3.0-or-later AND MPL-2.0 AND MIT`) and the libmorpheus
release that produced it, and narrows Emscripten's Node.js detection to
runtimes that expose `import.meta.url`: edge runtimes with Node compatibility
(Cloudflare Workers) present a Node-like `process` but no module URL, and the
unpatched loader throws in `createRequire(undefined)` before a precompiled
module can be instantiated. The stamp refuses to run if the expected
detection line changes in a future Emscripten. `MORPHEUS_WASM_OUTPUT_DIRECTORY` (default
`build/wasm/wasm`) chooses where both files land. In the Release
configuration `morpheus.wasm` is about 150 KiB and `morpheus.mjs` about
70 KiB.

## Qualification: the native suite under Node.js

Configuring with `-DBUILD_TESTING=ON` compiles the C test programs with
Emscripten as well. `emcmake` registers Node.js as
`CMAKE_CROSSCOMPILING_EMULATOR`, so `ctest` runs each `.js` program under
Node.js without further changes. `cmake/EmscriptenTesting.cmake` applies the
test link policy: `-sNODERAWFS=1` reads stemlibs and fixtures straight from
the host file system, `-sEXIT_RUNTIME=1` propagates exit codes, and
`cmake/emscripten-test-env.js` copies the host environment into the module so
`getenv("MORPHLIB")` works. The CMake test scripts that launch compiled
programs themselves receive the emulator as `MORPHEUS_TEST_LAUNCHER`, which is
empty for native builds.

```sh
emcmake cmake -S . -B build/wasm -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DMORPHEUS_BUILD_CRUNCHER=OFF
cmake --build build/wasm
ctest --test-dir build/wasm --output-on-failure -j 4
```

With Emscripten 4.0.15 the suite passes **64 of 64** enabled tests, including
the public-API tests, the Greek and Latin fixtures, the stemlib binary
equivalence checks, the generation index builder and the generation service.
Compared with the native suite:

| Test | Under Emscripten | Reason |
| --- | --- | --- |
| `public_parallel_contexts` | disabled | Uses `pthread_create`; the module is single-threaded. Contexts stay independent, so concurrency means one module instance per worker. |
| `gener_service_isolation` | disabled | Same pthread dependency (the other three service modes run). |
| `public_symbols` | not generated | Inspects the shared object with `nm`; the module's export list is fixed by the linker instead. |
| `installed_package_consumer`, `installed_surface`, `installed_pkg_config` | not generated | Exercise the native install tree, which Emscripten builds do not produce. |

The facade's own tests (`bindings/js/wasm/test/`) load the module as an
application would, mount or write the Perseids stemlib, and check Latin and
Greek analysis, the compatibility text output, stemlib validation errors,
context independence and Greek generation from a prepared `gener.index`.

The `WebAssembly` workflow (`.github/workflows/wasm.yml`) runs the three steps
above in the `emscripten/emsdk:4.0.15` container and uploads `morpheus.mjs`,
`morpheus.wasm` and their SHA-256 digests as a build artifact.

## Data at run time

The module validates the same required files as the native library when a
context is opened (`rule_files/*.table`, `steminds/{nomind,vbind}{,.lindex}`,
`endtables/indices/{nendind,vbendind}`, plus `rule_files/ppasslist.table` for
Greek) and then reads lazily, by stem class and analysis path,
`endtables/out/*.out`, `derivs/indices/derivind`, `stemsrc/vbs.cmp.ml`
(compound verbs) and `stemsrc/lemlist` (dictionary entries), plus
`gener.index` at the stemlib root for generation. A missing lazy file surfaces
as an internal error on the forms that need it, so applications ship the whole
set. Measured on the Perseids stemlib, that is about 3 MiB for Latin and 8 MiB
for Greek. Under Node.js the facade mounts a host directory
(NODEFS); in a browser it writes fetched bytes into MEMFS from a manifest of
paths. The distribution boundary is unchanged: neither the module nor the
facade package embeds a stemlib, and the [redistribution
policy](stemlib-redistribution.md) applies to any application that serves one.

## Performance against the native FFI path

`bench/compare.ts` measures the module next to the Deno FFI binding on the same
corpus when `MORPHEUS_WASM_MODULE` is set; [benchmarks.md](benchmarks.md)
describes the execution models. The run below is **indicative only**: a shared
2-vCPU Linux sandbox, the 24 Greek fixture words, native Release build with
GCC, Emscripten 4.0.15 at `-O2`, Deno 2.9.6, Alpheios stemlib with the
complete qualified `gener.index` (17.8 MiB runtime subset per MEMFS instance,
of which the index is 11.2 MiB). Two runs (20 and 50 iterations) are shown
because run-to-run noise on that host is around ±20 %.

| Engine | Contexts | Mean µs (run 1 / run 2) | Startup ms |
| --- | --- | --- | --- |
| `ffi` | 1 | 1316 / 1237 | 4 / 3 |
| `wasm-memfs` | 1 | 1166 / 939 | 130 / 118 |
| `wasm-nodefs` | 1 | 1081 / 1189 | 75 / 76 |
| `ffi` | 2 | 837 / 828 | 3 / 2 |
| `wasm-memfs` | 2 | 728 / 762 | 151 / 123 |
| `wasm-nodefs` | 2 | 972 / 867 | 133 / 140 |
| `cruncher-cold` | 0 | 6028 / 5280 | 6 / 5 |
| `wasm-memfs-cold` | 0 | 33181 / 37699 | 33 / 38 |
| `generation-small-warm` (`lo/gos`) | 1 | 689 / 624 | 2 / 2 |
| `wasm-memfs-generation-small-warm` | 1 | 148 / 114 | 77 / 111 |
| `generation-maximal-warm` (`i(/hmi`) | 1 | 27815 / 26887 | 3 / 2 |
| `wasm-memfs-generation-maximal-warm` | 1 | 26722 / 20400 | 97 / 108 |
| `generation-maximal-warm` | 2 | 32688 / 39327 | 3 / 2 |
| `wasm-memfs-generation-maximal-warm` | 2 | 13070 / 13158 | 157 / 158 |
| `generation-maximal-cold` | 0 | 53420 / 53062 | 53 / 53 |
| `wasm-memfs-generation-maximal-cold` | 0 | 76834 / 82104 | 77 / 82 |

What the numbers say, within that noise:

- **Warm analysis is at parity.** Per word, the module in a worker with MEMFS
  is as fast as the native library behind Deno's FFI, and it scales with a
  second worker the way a second native context does. The historical lookup
  pattern (`MorphFopen` → `fseek` → `fgets` loop → `fclose` per stem lookup)
  makes analysis I/O-bound rather than compute-bound: with MEMFS each of those
  calls is a copy inside the module, cheaper than a system call, which offsets
  the slower scalar code. NODEFS pays the system call *and* the JavaScript
  layer; it is slower and scales worse, as expected, and is not a deployment
  option.
- **Warm generation is at parity or better.** The FFI model dispatches each
  call to Deno's blocking pool; the module runs synchronously inside its
  worker. With two workers the maximal lemma generates in less than half the
  FFI time on this host.
- **Start-up is the cost.** Instantiating the module, placing 18 MiB of data
  and opening a context takes 30–40 ms cold against 5–6 ms for a `cruncher`
  process, and a worker pool adds 100–150 ms before its first answer. A
  server should keep instances alive; a browser pays it once per page.
- **Memory is per instance.** Each worker is a V8 isolate plus its own MEMFS
  copy of the runtime subset; the process-wide peak RSS during the pool
  measurements was 350–500 MiB against about 60 MiB for the FFI model. The
  figure is order-dependent within a run (RSS does not shrink between
  models), so use `rss_growth` per measurement rather than `peak_rss` for
  attribution.

The decisive comparison is on a quiet multi-core host with the release
procedure; the harness is in place for it. The result also answers whether a
per-context file-descriptor cache in the C runtime is worth pursuing: it would
help native and NODEFS deployments, while MEMFS already removes most of the
cost it targets.

## Known limits and follow-ups

- Single-threaded by design. A `-pthread` build would require shared memory
  and cross-origin isolation in browsers; nothing in the runtime needs it.
- The facade returns the numeric codes of the C structures. The named decoding
  (part-of-speech, dialect and morph-flag names) exists in the Deno binding
  and can be shared with the WebAssembly facade in a later change.
- Publication follows the `wasm-v<version>` track described in
  [releasing.md](releasing.md): `bindings/js/wasm/` is one package for npm
  and JSR, `wasm_package_metadata` guards its manifests, and
  `wasm-release.yml` publishes only a module that reproduces the qualified
  CI artifact byte for byte. The first publication still needs the registry
  side set up (JSR link, npm trusted publisher).
- The facade has been exercised under Node.js, Deno (benchmark) and the local
  Cloudflare Workers runtime (`wrangler dev`, see the
  [binding README](../bindings/js/wasm/README.md#cloudflare-workers)); a
  browser smoke test (fetching a stemlib manifest into MEMFS) and a hosted
  Workers deployment belong in the release qualification.
