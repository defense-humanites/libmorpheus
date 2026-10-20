<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# WebAssembly binding 0.1.0 release decision

Version 0.1.0 is the first candidate release of the independently versioned
WebAssembly binding. It compiles libmorpheus 0.4.2, C ABI 2, with Emscripten
4.0.15. This document records the intended contract; it does not authorize or
record creation of the `wasm-v0.1.0` tag.

## Distribution contract

The release is one public package, `@libmorpheus/wasm`, published at the same
version from the same directory on npm and on JSR, plus the module files
attached to a `wasm-v0.1.0` GitHub pre-release:

- `dist/morpheus.mjs`, the Emscripten ES-module loader, stamped with its SPDX
  expression, the libmorpheus release, the ABI and the Emscripten release;
- `dist/morpheus.wasm`, the complete public C API (`morpheus.h` and
  `compat.h`) as a single-threaded WebAssembly module;
- `index.mjs` with `index.d.ts`, the JavaScript facade, and
  `internal/version.mjs`, which declares the four versions above.

Unlike the native bindings, this package ships the runtime; it therefore
declares the libmorpheus release and ABI of the tree it was built from, not an
independently acquired native release. It contains no linguistic data.
Applications provide a compiled stem library through the module's virtual file
system, as the binding README describes.

## Behavioral contract

The facade exposes synchronous Greek and Latin analysis, the historical
`cruncher` text output, and experimental Greek generation, over a context per
language inside one module instance. It returns the numeric codes of the C
structures (`MorpheusRawAnalysis`, `MorpheusRawGeneration`) with:

- every interpretation returned by the runtime, in order;
- raw numeric traits, truncation markers and morphological flags;
- fixed-capacity Beta Code text fields decoded as strings.

The named decoding offered by the Deno and Node.js bindings is not part of
this release. The module is single-threaded: contexts within one instance are
independent but never concurrent, and parallel work means one instance per
worker, with one compiled `WebAssembly.Module` shared between workers.
`createMorpheus()` accepts a precompiled module for that and for runtimes that
forbid compilation from bytes (Cloudflare Workers), and loads `morpheus.wasm`
itself when the package is served from a registry.

## Qualification and publication

The WebAssembly workflow builds the module in the `emscripten/emsdk:4.0.15`
container, compiles the native C test suite to WebAssembly and runs it under
Node.js (64 of 64 enabled tests; the two pthread-based tests are disabled, as
`docs/wasm.md` records), runs the facade tests against the Perseids stemlib
and a prepared generation index, dry-runs both package manifests against the
built module, and uploads the module with its SHA-256 digests. Linux CI runs
`wasm_package_metadata`, which checks both manifests, the version coupling to
the tree, the Emscripten pin, the closed file set and the absence of
linguistic data.

On an authorized `wasm-v0.1.0` tag, the publication workflow waits for both
tagged workflows on the exact commit, rebuilds the module in the pinned
container and requires it to equal the qualified artifact byte for byte, tests
the facade from an `npm pack` tarball and with its own suite, publishes to npm
through GitHub OIDC with provenance and to JSR, then attaches `morpheus.mjs`,
`morpheus.wasm` and `SHA256SUMS` to the pre-release.

The first release required the documented one-time `0.0.0` bootstrap, since
npm grants a trusted publisher only to an existing package. That placeholder
was published under the `bootstrap` dist-tag on 2026-10-20 and, as npm does
for a package's first version, also received `latest`; publishing 0.1.0 moves
`latest` to it. The JSR package was linked to this repository beforehand.

## Licensing

The facade, version module, bootstrap tool, workflows, metadata test and this
release decision are AGPL-3.0-or-later. The built module combines the
AGPL-3.0-or-later and MPL-2.0 runtime sources with the MIT-licensed Emscripten
support code and is stamped `AGPL-3.0-or-later AND MPL-2.0 AND MIT`; the
package carries the MPL and Emscripten texts under `LICENSES/`. No stem data is
distributed; applications remain bound by the stemlib redistribution policy
for any data they ship with the module.

## Known limits

- Indicative benchmarks on a shared 2-vCPU host put warm analysis with the
  data in module memory at parity with the native FFI path and warm
  generation at parity or better; instantiation (30–40 ms) and per-instance
  memory are the costs. The decisive comparison on a quiet multi-core host
  with the release procedure is still to be made.
- The Cloudflare Workers configuration was exercised with `wrangler dev` and a
  dry-run deploy, not on the hosted platform. No browser smoke test has run.

## Remaining authorization

Before publication, a maintainer must:

1. confirm the final tagged CI candidate, including the WebAssembly workflow;
2. confirm that the npm trusted publisher and the JSR repository link are in
   place (both recorded as done on 2026-10-20);
3. explicitly authorize creation of `wasm-v0.1.0`.
