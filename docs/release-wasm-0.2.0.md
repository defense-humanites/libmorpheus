<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# WebAssembly binding 0.2.0 release decision

Version 0.2.0 of the WebAssembly binding compiles libmorpheus 0.5.0, C ABI 2,
with Emscripten 4.0.15. It supersedes 0.1.4 for the generation changes of
0.5.0 and exposes the new skipped-record count. This document records the
intended contract and, in its last section, the publication.

## Why a new version

The module shares the runtime of native 0.5.0
([release-0.5.0.md](release-0.5.0.md)), whose generation changes reach
WebAssembly users unchanged:

- a lemma no longer fails because of a record the engine cannot generate:
  the record is skipped, the others are generated (δίδωμι, ἵστημι, πόλις,
  γράφω and βασιλεύς failed with 0.1.4);
- generated records carry the degree and morphology flags analysis reports
  (ἡδύτερος is comparative, no longer positive);
- surfaces lose the stem-boundary hyphen (`a)nqrw/pwn`);
- the engine's diagnostics are no longer printed.

The facade exposes the count: the array that `generate()` returns keeps its
type and gains a read-only, non-enumerable `skippedRecords` property, the
number of the lemma's source records that were skipped. Code that iterates,
spreads or serializes the array sees nothing new.

The minor version follows the project's rule within 0.x: requests that
failed now succeed, and records change degree and surface. Analysis results
are unchanged.

## Contracts

Distribution, behavioural and licensing contracts are unchanged from
[0.1.4](release-wasm-0.1.4.md): one npm and JSR package, the Emscripten
loader and module built in the pinned `emsdk` container and reproduced byte
for byte by the publication workflow, the facade, its types, and no
linguistic data. Generation still needs a `gener.index` that the
application prepares; `@libmorpheus/data` 0.2.0 prepares the index this
release is qualified with ([release-data-0.2.0.md](release-data-0.2.0.md)).

## Qualification and publication

As for 0.1.4: tagged Linux CI and the WebAssembly qualification on the exact
commit, a module rebuilt in the pinned container and required to reproduce
the qualified one, the facade tested from an `npm pack` tarball, publication
to npm through OIDC with provenance and to JSR, and a pre-release with
`morpheus.mjs`, `morpheus.wasm` and `SHA256SUMS`, created from
`docs/release-notes/wasm-v0.2.0.md`. The `v0.5.0` tag must exist first, on
the same commit or an ancestor with an unchanged runtime. After publication,
the maintainer exercises the package from JSR itself and records the result
here.

## Publication record

- Tag: `wasm-v0.2.0`, created by the maintainer on 2026-11-11 on
  `667ca578fb514fe099fcc522a0f47167bf3805a9`, the commit of
  [`v0.5.0`](release-0.5.0.md), after that native release was published.
- Tagged qualification: [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/43072917652)
  and [WebAssembly](https://github.com/defense-humanites/libmorpheus/actions/runs/43072917635),
  both passed at their first attempt.
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/43072917629);
  the rebuilt module reproduced the qualified artifact byte for byte, npm
  (`latest` now `0.2.0`, tarball integrity
  `sha512-u6L/vkiUznf1oBOKRcZHax+pFfWnDnZQtn6A3+zXmC4Xp+wrVA5gxIZWBfJ+tflzY9d5MhmXeAApAKGzicbwWA==`)
  and JSR both accepted the version, and the
  [`wasm-v0.2.0` pre-release](https://github.com/defense-humanites/libmorpheus/releases/tag/wasm-v0.2.0)
  carries the module files.
- Module digests (`SHA256SUMS`):
  `eeba93bf2f762fe29f2fb76a269cd525e0fb33000ba358602edbd5d3b6c95f21`
  (`morpheus.mjs`),
  `02477faade7c8a76fbb4d81da5e81a0684b4da99693caa5f995fccab621f347b`
  (`morpheus.wasm`). A module built outside CI from the tagged commit with
  the pinned Emscripten 4.0.15 has the same two digests.
- npm check: `@libmorpheus/wasm@0.2.0` installed from npm reports
  WebAssembly 0.2.0 and native 0.5.0. Over the Alpheios Greek tree and the
  index that `@libmorpheus/data` 0.2.0 prepared (`a2f97677…`), δίδωμι
  generates 3,636 records with `skippedRecords` 1, not enumerable, as
  native 0.5.0 does with the same files.
- JSR end-to-end check: to be done by the maintainer, from
  `@libmorpheus/wasm@0.2.0` as JSR serves it, and recorded here.
