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

## Remaining authorization

Before publication, a maintainer must:

1. publish native 0.4.5 first (`v0.4.5`), since the binding declares it;
2. confirm the tagged Linux CI and WebAssembly runs on the candidate commit;
3. explicitly authorize creation of `wasm-v0.1.3`;
4. after publication, run the JSR end-to-end check above and record its
   outcome here.
