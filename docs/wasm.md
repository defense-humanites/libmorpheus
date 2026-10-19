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
release that produced it. `MORPHEUS_WASM_OUTPUT_DIRECTORY` (default
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
Greek) and then reads `endtables/out/*.out` tables lazily by stem class,
`derivs/indices/derivind`, and `Greek/gener.index` for generation. Measured on
the Perseids stemlib, everything analysis can touch is about 3 MiB for Latin
and 7 MiB for Greek. Under Node.js the facade mounts a host directory
(NODEFS); in a browser it writes fetched bytes into MEMFS from a manifest of
paths. The distribution boundary is unchanged: neither the module nor the
facade package embeds a stemlib, and the [redistribution
policy](stemlib-redistribution.md) applies to any application that serves one.

## Known limits and follow-ups

- Single-threaded by design. A `-pthread` build would require shared memory
  and cross-origin isolation in browsers; nothing in the runtime needs it.
- The facade returns the numeric codes of the C structures. The named decoding
  (part-of-speech, dialect and morph-flag names) exists in the Deno binding
  and can be shared with the WebAssembly facade in a later change.
- The module is produced by CI as a build artifact; publishing it (npm, JSR,
  GitHub Release asset) and the version/receipt discipline the other bindings
  follow are deliberately left to a separate release change.
- The facade has been exercised under Node.js; a browser smoke test (fetching
  a stemlib manifest into MEMFS) belongs in the release qualification.
