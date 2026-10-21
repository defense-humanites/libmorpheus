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
- Benchmark evidence: **accepted**
- Pre-release Linux CI: pending (the tagged commit's run)
- Pre-release platform qualification: pending (manual dispatch with
  `package_artifacts` on the exact candidate commit)

## Benchmark evidence

The schema 2 report from native source revision
`7892e7f14805348c2629154ef2bfe033adead256` (the merge of the release
preparation) uses the pinned Alpheios stemlib revision
`4632415fe93c85e9fdca47a0c5a13f31385f0023` on the same Apple Silicon host as
the 0.4.2 report, with Apple Clang 21 and Deno 2.9.7. Its SHA-256 is
`39ff48435c8574d84f39dc20833754db015063192d5bfdc6d87a750f299ac96d`. It
matches the accepted 0.4.2 report's corpus, generation index, toolchain,
workload parameters and all thirteen result counts. The complete benchmark
validator passes with the recorded source revision and compiler.

Relative to 0.4.2, analysis FFI mean latency falls 3.4 %, 3.3 % and 1.5 % at
one, two and four contexts; persistent and cold `cruncher` fall 4.8 % and
1.8 %. Maximal generation falls 5.1 %, 3.1 % and 2.7 % warm and 2.2 % cold;
small generation changes by +5.0 %, −20.5 % and +5.1 % warm and −1.2 % cold.
As in the 0.4.2 review, the two-context small warm generation aggregate is
too short to carry meaning: its 40 operations take 1.9 ms in the baseline and
1.5 ms in the candidate, and it had moved 19 % the other way between 0.4.1
and 0.4.2. Peak process RSS is 2 MiB higher in every configuration (0.7–3.4 %)
with unchanged growth during measurement, the ordinary difference between two
processes. All result counts are unchanged.

These timings are consistent with the nature of the release: the only runtime
sources that differ from `v0.4.2` are an explicit cast in `morphkeys.c`, a
guard in `retrentry.c` that is compiled only where `long` is 32 bits and so
is absent from the measured LP64 binary, and `src/wasm/module.c`, which native
configurations do not compile. Nothing on the analysis or generation path
changed, and the measurement shows nothing beyond run-to-run variation.

## Remaining authorization

Before publication, a maintainer must:

1. dispatch the platform workflow with `package_artifacts` for the candidate
   commit and inspect the three native archives;
2. confirm the final tagged Linux CI and platform runs and record their links
   above;
3. explicitly authorize creation of `v0.4.3`, then of `wasm-v0.1.1` on the
   same commit or a descendant with an unchanged runtime.
