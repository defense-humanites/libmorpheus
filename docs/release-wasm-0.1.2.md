<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# WebAssembly binding 0.1.2 release decision

Version 0.1.2 is the third release of the WebAssembly binding. It compiles
libmorpheus 0.4.4, C ABI 2, with Emscripten 4.0.15, and supersedes 0.1.1 for
one reason: the cost a serverless isolate pays before its first answer. This
document records the intended contract and, in its last section, the
publication.

## Why a new version

Both changes answer measurements from the bailly.app API thread, which
plans to serve the module from Cloudflare Workers, where every new isolate
pays the module's start-up.

- **Stemlib bytes are adopted, not copied.** `writeStemlib()` (and so
  `fetchStemlib()`) hands Emscripten the caller's arrays with `canOwn` and
  creates each directory once per call instead of probing every path segment
  of every file. Placing the Greek runtime subset (159 files, 7.8 MiB) on a
  fresh Node.js process falls from about 20 ms to 7 ms; on Workers the
  bundled Data modules are no longer duplicated. The contract is explicit
  for every input type: the bytes belong to the module and must not be
  modified afterwards. Node.js callers already handed over views, since
  Emscripten's "copy" of a `Buffer` is a `Buffer.slice`, which is a view.
  The runtime only reads stemlib files, and a later write to the same path
  replaces the array through `O_TRUNC` without writing into it; a test fixes
  both facts.
- **The first analysis halves.** Native 0.4.4 reads each index file in one
  request instead of `BUFSIZ` or one record at a time: the first Greek
  analysis of a context issues about 80 `read` calls through the JavaScript
  file system instead of about 3,500, and takes about 6 ms instead of
  10–15 ms with optimized code on a 2 vCPU host.

Analyses are unchanged: the module built from the candidate agrees byte for
byte with one built from `v0.4.3` over 3,000 Greek headwords and the Latin
fixtures, and in-memory and mounted stemlibs analyze identically.

The distribution, behavioral, qualification, publication and licensing
contracts of [0.1.0](release-wasm-0.1.0.md) and [0.1.1](release-wasm-0.1.1.md)
are otherwise unchanged: one package, `@libmorpheus/wasm`, on npm and JSR
from the same directory, plus the module files and digests on a
`wasm-v0.1.2` GitHub pre-release; no linguistic data; single-threaded
module; raw numeric decoding.

## Not in this version

Recorded in `docs/wasm.md` after tracing what the first analysis does: the
ending-table cache holds 45 tables for 139 Greek ones and reloads one about
every dozen words over varied vocabulary, at a few per cent of the per-word
cost (enlarging it measured within noise); pre-prepared index formats and a
Wizer snapshot were examined and set aside. No measurement on the hosted
Workers platform has been made yet; the Node.js figures include V8's
baseline tier on first execution, which a platform that precompiles may not
pay.

## Qualification and publication

As for 0.1.1: the WebAssembly workflow qualifies the module and the facade on
the tagged commit, Linux CI runs `wasm_package_metadata`, and the publication
workflow rebuilds the module in the pinned container, requires byte-for-byte
reproduction of the qualified artifact, tests the facade from an `npm pack`
tarball, publishes to npm through OIDC with provenance and to JSR, and
attaches `morpheus.mjs`, `morpheus.wasm` and `SHA256SUMS` to the pre-release.
Both registry steps skip a version already present, so a recovery dispatch
resumes at the release.

After publication, the package must be exercised from JSR itself
(`deno add jsr:@libmorpheus/wasm@0.1.2`, then the README's Node.js/Deno
example against a local stemlib), since JSR transforms the files it serves;
0.1.1 passed that check.

## Publication record

- Tag: `wasm-v0.1.2`, created by the maintainer on 2026-11-04 on
  `dd06be9592d8b0c713fd0025b0755cbb8eab7247`, the commit of
  [`v0.4.4`](release-0.4.4.md), after that native release was published.
- Tagged qualification: [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/41886343999)
  and [WebAssembly](https://github.com/defense-humanites/libmorpheus/actions/runs/41886344489),
  both passed.
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/41886344088);
  the rebuilt module reproduced the qualified artifact byte for byte, npm
  (`latest` now `0.1.2`, tarball integrity
  `sha512-kusagCLww5Yo1jkC5F1tUAKD6bFiBW0VrQzRY14sT/3K133iIkYPDwoLudvXgvZGgFPlT0b6E9FIoBJKgNB2Jg==`)
  and JSR both accepted the version, and the
  [`wasm-v0.1.2` pre-release](https://github.com/defense-humanites/libmorpheus/releases/tag/wasm-v0.1.2)
  carries the module files.
- Module digests (`SHA256SUMS`):
  `094b93bc177dfc8de179d4aac720b6af75d4bf54e14a906840bf6c2176726f71`
  (`morpheus.mjs`),
  `bb6ee592799885179204459a82632bf76ae233d23f670832b788eaa93292e8cc`
  (`morpheus.wasm`).
- JSR end-to-end check: done by the maintainer on 2026-11-05 on macOS
  (Apple Silicon) with Deno, from `jsr:@libmorpheus/wasm@0.1.2` and the
  README's Node.js/Deno example against a local stemlib. The module served
  by JSR instantiated and `analyze("greek", "e)/kstasis")` returned the
  expected single analysis, as for 0.1.1.
