<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# WebAssembly binding 0.1.1 release decision

Version 0.1.1 is the second release of the WebAssembly binding. It compiles
libmorpheus 0.4.3, C ABI 2, with Emscripten 4.0.15, and supersedes 0.1.0 for
two reasons. This document records the intended contract and, in its last
section, the publication.

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

## Publication record

- Tag: `wasm-v0.1.1`, created by the maintainer on 2026-10-21 on
  `b907ecdf73572ff03a59022360ba4d10006f27c4`, the commit of
  [`v0.4.3`](release-0.4.3.md), after that native release was published.
- Tagged qualification: [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/39624859048)
  and [WebAssembly](https://github.com/defense-humanites/libmorpheus/actions/runs/39624858800),
  both passed.
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/39624859113);
  the rebuilt module reproduced the qualified artifact byte for byte, npm
  (`latest` now `0.1.1`, tarball integrity
  `sha512-JDxOK2Fyalgu4c4/hdO2x2Q8nuC2YR5zSaL4vqFwLLlQRiwsDwYjCbOv6Z/NagNo7WwLOQZ9dD6UHJAXcX75Ew==`)
  and JSR both accepted the version without queueing, and the
  [`wasm-v0.1.1` pre-release](https://github.com/defense-humanites/libmorpheus/releases/tag/wasm-v0.1.1)
  carries the module files.
- Module digests (`SHA256SUMS`):
  `140366fc9d40d20973f8c7358ce1296647b39010e29d80388b40c73be4e76f62`
  (`morpheus.mjs`),
  `92f82f04a110e48eae9b6ffb95d599d0042aaf19b526d2106b4ac4311fb4c74b`
  (`morpheus.wasm`).
- JSR end-to-end check: done by the maintainer on macOS (Apple Silicon)
  with Deno, from `jsr:@libmorpheus/wasm@0.1.1` and the README's
  Node.js/Deno example against a local Perseids stemlib. The module served by
  JSR was fetched, compiled and instantiated (the step at which 0.1.0 failed),
  and `analyze("greek", "e)/kstasis")` returned the expected single analysis
  (noun, feminine singular nominative, lemma `e)/kstasis`, stem `e)kstas`,
  ending `is`). The only stumble was the example's placeholder stemlib path
  (`/srv/stemlib`), which the README now derives from `import.meta.url` and
  follows with the expected output.
