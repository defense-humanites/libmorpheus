<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# libmorpheus 0.4.3

This native release changes no analysis or generation result. It exists to
regularize the provenance of the WebAssembly binding: `@libmorpheus/wasm`
0.1.0 was compiled from `main` at `18d7c6a`, whose runtime sources differ from
the `v0.4.2` tag by two ILP32 corrections (`src/morphlib/morphkeys.c` casts
the 32-bit stem-type word explicitly; `src/morphlib/retrentry.c` refuses a
pre-index offset that a 32-bit `long` cannot hold). Both are no-ops on the
LP64 targets the native packages support, but a module stamped "libmorpheus
0.4.2" was not built from 0.4.2's sources. 0.4.3 is the native release those
sources belong to; WebAssembly binding 0.1.1 is compiled from it and declares
it.

The release also carries the WebAssembly build itself (the `MORPHEUS_BUILD_WASM`
option, the Emscripten test policy and the module stamp), which native
configurations do not compile, and the regenerated Deno and Node.js generation
preparer modules, whose source now honours an explicit `MORPHLIB`.

The public C API and ABI are unchanged from 0.4.1 and 0.4.2. The native
archives contain no stemlib data. The Deno, Node.js and Python bindings keep
declaring the native releases they were qualified against; none of them needs
a release for this version.

## Release record

- Project version: **0.4.3**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.4.2`
- Benchmark evidence: **pending** — to be produced with `bench/release.sh`
  on the controlled Apple Silicon host and compared with the accepted 0.4.2
  report before tagging; this record is to be completed with the reviewed
  comparison, the evidence digest and the pre-release CI links at that time.
- Pre-release Linux CI: pending
- Pre-release platform qualification: pending (manual dispatch with
  `package_artifacts` on the exact candidate commit)

## Expected benchmark outcome

The measured native paths are untouched: the two ILP32 corrections compile to
the same LP64 code apart from an explicit cast, and nothing else under `src/`
changed on the analysis or generation path since the 0.4.2 measurement. The
comparison with 0.4.2 on the same host is therefore expected to stay within
run-to-run noise on every configuration and to keep all result counts
unchanged. A material difference would indicate a measurement problem or an
unnoticed change, and must be investigated before the tag.

## Remaining authorization

Before publication, a maintainer must:

1. produce and review the benchmark evidence as described above, and commit
   `bench/release-evidence/benchmark-0.4.3.json` with its SHA-256 sidecar;
2. dispatch the platform workflow with `package_artifacts` for the candidate
   commit and inspect the three native archives;
3. confirm the final tagged Linux CI and platform runs;
4. explicitly authorize creation of `v0.4.3`, then of `wasm-v0.1.1` on the
   same commit or a descendant with an unchanged runtime.
