<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# WebAssembly binding 0.1.3 release decision

Version 0.1.3 is the fourth release of the WebAssembly binding. It compiles
libmorpheus 0.4.5, C ABI 2, with Emscripten 4.0.15, and supersedes 0.1.2 for
one reason: Latin correctness. This document records the intended contract;
it does not authorize or record creation of the `wasm-v0.1.3` tag.

## Why a new version

Versions 0.1.0 to 0.1.2 return **no analysis** for Latin forms built on the
fourth principal part (`amatus`, `amatum`, `captum` and `dictum` as verbs, …)
and lose the participle reading of forms such as `rosarum`: 108 of 1,517
Latin headwords differ from the native library. The Perseids Latin
stem-type table names that class `pp_su`, which the runtime did not know;
its all-ones failure value was accepted on 64-bit hosts and refused on
`wasm32` (issue #37). Native 0.4.5 resolves the class on every platform;
the module compiled from it now equals the native library in lemma, stem
and ending over 3,000 Greek and 1,517 Latin headwords. Greek results were
never affected, and are unchanged.

The facade is unchanged. The distribution, behavioral, qualification,
publication and licensing contracts of [0.1.2](release-wasm-0.1.2.md) are
otherwise unchanged: one package, `@libmorpheus/wasm`, on npm and JSR from
the same directory, plus the module files and digests on a `wasm-v0.1.3`
GitHub pre-release; no linguistic data; single-threaded module; raw numeric
decoding. `public_fixtures`, which the Emscripten qualification runs under
Node.js, now asserts `amatus`, `rosarum` and `ingressus`, and the facade
test asserts `rosarum`'s two lemmas.

## Qualification and publication

As for 0.1.2: the WebAssembly workflow qualifies the module and the facade on
the tagged commit, Linux CI runs `wasm_package_metadata`, and the publication
workflow rebuilds the module in the pinned container, requires byte-for-byte
reproduction of the qualified artifact, tests the facade from an `npm pack`
tarball, publishes to npm through OIDC with provenance and to JSR, and
attaches `morpheus.mjs`, `morpheus.wasm` and `SHA256SUMS` to the pre-release.
Both registry steps skip a version already present, so a recovery dispatch
resumes at the release.

After publication, the package must be exercised from JSR itself
(`deno add jsr:@libmorpheus/wasm@0.1.3`, then the README's Node.js/Deno
example against a local stemlib, this time with a Latin check such as
`analyze("latin", "amatus")` returning one analysis with lemma `amo`).

## Publication record

- Tag: `wasm-v0.1.3`, created by the maintainer on 2026-11-05 on
  `4a81111dc3634087760682f05b732ec8581ea0f4`, the commit of
  [`v0.4.5`](release-0.4.5.md), after that native release was published.
- Tagged qualification: [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/42073327859)
  and [WebAssembly](https://github.com/defense-humanites/libmorpheus/actions/runs/42073327691),
  both passed.
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/42073327650);
  the rebuilt module reproduced the qualified artifact byte for byte, npm
  (`latest` now `0.1.3`, tarball integrity
  `sha512-YDCKjO8g4JVTpYyA5kK3EkODZilt7ElIu0Wrkf9DPJs7zn0Emd3/hdJFp1lqlAB9JbmkvcESpkUNWHVLRhaC1Q==`)
  and JSR both accepted the version, and the
  [`wasm-v0.1.3` pre-release](https://github.com/defense-humanites/libmorpheus/releases/tag/wasm-v0.1.3)
  carries the module files.
- Module digests (`SHA256SUMS`):
  `92edf6f1c7102fc207571a76bd6255443524b5da10d6bbbe562205bfbb90735d`
  (`morpheus.mjs`),
  `09a8841ad754ebb67f1ae218153d7a4492a4d2dd20e4a5abcff54ad85f8f8f50`
  (`morpheus.wasm`).
- JSR end-to-end check: pending (maintainer, from `jsr:@libmorpheus/wasm@0.1.3`
  with the Latin check `analyze("latin", "amatus")`).
