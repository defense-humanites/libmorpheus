<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# WebAssembly binding 0.1.4 release decision

Version 0.1.4 is the fifth release of the WebAssembly binding. It compiles
libmorpheus 0.4.6, C ABI 2, with Emscripten 4.0.15, and supersedes 0.1.3 for
one reason: speed. This document records the intended contract; it does not
authorize or record creation of the `wasm-v0.1.4` tag.

## Why a new version

Native 0.4.6 removes the runtime's analysis hot spots (see
[release-0.4.6.md](release-0.4.6.md)): a preverb flag transfer that tested
112 flags per candidate key, per-context comparison tables read on every
string comparison, repeated context reads in key matching, a full
comparison of every raw preverb, and a stem index opened and closed about
five times per word. The module shares that runtime. Without threads its
context reads were already cheap, but the loops, comparisons and file
operations were not: with MEMFS each `open` and `close` goes through
Emscripten's JavaScript file system. On the 2-vCPU Linux sandbox, the
module built from these sources analyzes a word in 765–795 µs at one
context, against 1,505–1,520 µs for 0.1.3. Results are unchanged. The
leak fixed in 0.4.6 lies in the generation source preparer, which the
module does not link.

### Where the module gains

Measured on the 2-vCPU Linux sandbox with `bench/compare.mjs` (one
context, 10 iterations, two alternated rounds, the published 0.1.3 module
against modules built with Emscripten 4.0.15 after #61 and on `f1bfad7`,
mean µs per analyzed word; the host's noise is about ±15 %):

| Module | MEMFS | NODEFS |
| --- | --- | --- |
| 0.1.3 (`v0.4.5` sources) | 1,595 / 1,542 | 1,633 / 1,505 |
| after #61 | 1,093 / 1,252 | 1,357 / 1,527 |
| 0.1.4 candidate | 846 / 912 | 1,087 / 816 |

Result counts are identical throughout; warm and cold generation do not
move beyond noise. Change by change:

- **The preverb flag transfer (#61, #62)** is the largest gain with MEMFS.
  The module has no threads, so `_Thread_local` is a plain global and the
  context read never cost what `_tlv_get_addr` costs natively; but the
  transfer still made two function calls and a flag test for each of 112
  flag numbers, for every candidate key. #61 removed the context read from
  the loop, #62 the loop itself (eight direct tests, no call into the
  context).
- **The kept-open stem indices (#62)** matter most with NODEFS, where every
  `fopen`/`fclose` was a host system call through Emscripten's JavaScript
  file system, about five times per word. With MEMFS the open itself stays
  inside the module, but it still resolved the path through the JavaScript
  file system, allocated a stream and a stdio buffer and freed them again.
- **The first-byte rejection of raw preverbs (#62)** saves a `strlen` and a
  `strncmp` per raw preverb tried. The module's libc (musl, compiled to
  WebAssembly) has no vectorized string functions, so each call costs more
  than in glibc, and the share of this change is larger than natively.
- **The context-free string comparisons and `MatchMorphKey()` (#62)** save
  a call and a load per comparison or key field; small in the module, where
  the context read was cheap.
- **The leak fix (#63)** does not concern the module, which does not link
  the generation source preparer.

The facade is unchanged. The distribution, behavioral, qualification,
publication and licensing contracts of [0.1.3](release-wasm-0.1.3.md) are
otherwise unchanged: one package, `@libmorpheus/wasm`, on npm and JSR from
the same directory, plus the module files and digests on a `wasm-v0.1.4`
GitHub pre-release; no linguistic data; single-threaded module; raw numeric
decoding. A context keeps its stem index files open in the module's file
system until it is closed, as the native library does.

## Qualification and publication

As for 0.1.3: the WebAssembly workflow qualifies the module and the facade on
the tagged commit, Linux CI runs `wasm_package_metadata`, and the publication
workflow rebuilds the module in the pinned container, requires byte-for-byte
reproduction of the qualified artifact, tests the facade from an `npm pack`
tarball, publishes to npm through OIDC with provenance and to JSR (with
`npx jsr@0.14.3 publish`, Deno being no longer used), and attaches
`morpheus.mjs`, `morpheus.wasm` and `SHA256SUMS` to the pre-release. Both
registry steps skip a version already present, so a recovery dispatch
resumes at the release.

After publication, the package must be exercised from JSR itself (`npx jsr
add @libmorpheus/wasm@0.1.4` in an empty Node.js project, then the README's
example against a local stemlib, with a Greek and a Latin check such as
`analyze("latin", "amatus")` returning one analysis with lemma `amo`).

The third N-API / WebAssembly comparison, which decides the future of the
Node.js binding, is to be taken with this module and native 0.4.6, so that
both sides run the same runtime sources.

## Remaining authorization

Before publication, a maintainer must:

1. publish native 0.4.6 first (`v0.4.6`), since the binding declares it;
2. confirm the tagged Linux CI and WebAssembly runs on the candidate commit;
3. explicitly authorize creation of `wasm-v0.1.4`;
4. after publication, run the JSR end-to-end check above and record its
   outcome here.
