<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# WebAssembly binding 0.1.1 release decision

Version 0.1.1 is the second release of the WebAssembly binding. It compiles
libmorpheus 0.4.3, C ABI 2, with Emscripten 4.0.15, and supersedes 0.1.0 for
two reasons. This document records the intended contract; it does not
authorize or record creation of the `wasm-v0.1.1` tag.

## Why a new version

- **JSR instantiation failure.** JSR rewrites the import module names of
  every published `.wasm` into relative specifiers (`env` becomes `./env`)
  for its ES-module integration, and the Emscripten loader supplies the
  original names, so 0.1.0 installed from JSR fails in
  `WebAssembly.instantiate()` while the same version from npm and the
  GitHub release works. The facade now maps the module's declared import
  names onto the loader's imports; a test instantiates a module rewritten
  the way JSR does. The binding README links to repository documents by
  absolute URL, since JSR resolves relative links against its own pages.
- **Provenance.** 0.1.0 declared libmorpheus 0.4.2 but was compiled from a
  commit whose runtime sources differ from `v0.4.2` by two ILP32
  corrections. 0.1.1 is compiled from, and declares, native 0.4.3, the
  release those sources belong to.

The distribution, behavioral, qualification, publication and licensing
contracts of [0.1.0](release-wasm-0.1.0.md) are otherwise unchanged: one
package, `@libmorpheus/wasm`, on npm and JSR from the same directory, plus
the module files and digests on a `wasm-v0.1.1` GitHub pre-release; no
linguistic data; single-threaded module; raw numeric decoding.

## Qualification and publication

As for 0.1.0: the WebAssembly workflow qualifies the module and the facade on
the tagged commit, Linux CI runs `wasm_package_metadata`, and the publication
workflow rebuilds the module in the pinned container, requires byte-for-byte
reproduction of the qualified artifact, tests the facade from an `npm pack`
tarball, publishes to npm through OIDC with provenance and to JSR, and
attaches `morpheus.mjs`, `morpheus.wasm` and `SHA256SUMS` to the pre-release.
Both registry steps skip a version already present, so a recovery dispatch
resumes at the release.

Lessons from 0.1.0 recorded in `docs/releasing.md` apply: the container's
shell, Node.js and cmake are not the ones a plain runner has; JSR may queue a
publication for hours; a local static server does not simulate a registry
that transforms files, so the published JSR package must be exercised from
JSR itself after publication (`deno add jsr:@libmorpheus/wasm@0.1.1`, then
the README's Node.js/Deno example against a local stemlib).

## Remaining authorization

Before publication, a maintainer must:

1. publish native 0.4.3 first (`v0.4.3`), since the binding declares it;
2. confirm the tagged Linux CI and WebAssembly runs on the candidate commit;
3. explicitly authorize creation of `wasm-v0.1.1`;
4. after publication, run the JSR end-to-end check above and record its
   outcome here.
