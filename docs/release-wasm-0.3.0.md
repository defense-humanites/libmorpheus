<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# WebAssembly binding 0.3.0 release decision

Version 0.3.0 of the WebAssembly binding compiles libmorpheus 0.6.0, C ABI 2,
with Emscripten 4.0.15. It supersedes 0.2.0 for the generation changes of
0.6.0 and passes the new preverb-variant flag. This document records the
intended contract and, in its last section, the publication.

## Why a new version

The module shares the runtime of native 0.6.0
([release-0.6.0.md](release-0.6.0.md)), whose generation changes reach
WebAssembly users unchanged:

- `generate()` accepts the compound verbs analysis reports (`a)podi/dwmi`,
  `a)mfi/-lu/w`) and returns their preverb variants, with their flags;
- it also returns the unaugmented indicatives, the movable ν of irregular
  forms and the accented clitics that analysis reads;
- each form has the dialects that all its parts allow, and the verbal
  adjectives in -τός that analysis gives to lemmas of their own are left out;
- the default limit is the maximum, 65,536 records.

On the AGDT 2.1 treebank, the readings analysis gives that generation
returns rise from 82.8 % to 95.2 %. Analysis results are unchanged except one
reading of χρῆς.

The facade passes `excludePreverbVariants`, which leaves the preverb
variants out and returns a compound's plain forms. Its types declare the
option. Nothing else in the facade changes: `generate()` still returns an
array with its non-enumerable `skippedRecords` count.

The minor version follows the project's rule within 0.x: generation returns
different records for most lemmas, and the facade gains an option.

## Contracts

Distribution, behavioural and licensing contracts are unchanged from
[0.2.0](release-wasm-0.2.0.md): one npm and JSR package, the Emscripten
loader and module built in the pinned `emsdk` container and reproduced byte
for byte by the publication workflow, the facade, its types, and no
linguistic data. Generation still needs a `gener.index` that the application
prepares. `@libmorpheus/data` 0.3.0 prepares the index this release is
qualified with ([release-data-0.3.0.md](release-data-0.3.0.md)). With
0.2.0's index, compounds are generated without their compound-only stems.

## Qualification and publication

As for 0.2.0, with these steps:

1. Tagged Linux CI and the WebAssembly qualification pass on the exact commit.
2. The workflow rebuilds the module in the pinned container, and the rebuild
   must reproduce the qualified one.
3. It tests the facade from an `npm pack` tarball.
4. It publishes to npm through OIDC with provenance, and to JSR.
5. It creates a pre-release with `morpheus.mjs`, `morpheus.wasm` and
   `SHA256SUMS`, from `docs/release-notes/wasm-v0.3.0.md`.

The `v0.6.0` tag must exist first, on the same commit or on an ancestor with
an unchanged runtime.

## Publication record

- Tag: `wasm-v0.3.0`, created by the maintainer on 2026-11-17 on
  `7dcc93a18121ff79c3b694afb3b9fc9e4ebf1886`, the commit of
  [`v0.6.0`](release-0.6.0.md), after that native release was published.
- Tagged qualification: [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/44166719612)
  and [WebAssembly](https://github.com/defense-humanites/libmorpheus/actions/runs/44166719778),
  both passed at their first attempt.
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/44166719572).
  - The rebuilt module reproduced the qualified artifact byte for byte.
  - npm accepted the version: `latest` is now `0.3.0`, with tarball
    integrity
    `sha512-OyOoEeEFRbB1piKFWJRzNPfbgTjkTjgOZ3zZjZ4KWAHUQxPsc9QfGxo2GDubQjFVQFYdp3c/7rQDt0GeEzD9gw==`.
  - JSR accepted the version.
  - The [`wasm-v0.3.0` pre-release](https://github.com/defense-humanites/libmorpheus/releases/tag/wasm-v0.3.0)
    carries the module files.
- Module digests (`SHA256SUMS`):
  `fc3e28b8a1c90c75ddce6053aaca5b554075ce0e7ad15d3c23d19c538c4665ed`
  (`morpheus.mjs`),
  `787b9e7d584289fd0a76a578264637e6cf84e05a425731b2d1a59cef7c7d3b29`
  (`morpheus.wasm`). A module built outside CI from the tagged commit with
  the pinned Emscripten 4.0.15 has the same two digests.
- npm check: `@libmorpheus/wasm@0.3.0` installed from npm reports
  WebAssembly 0.3.0 and native 0.6.0. It was run over the Alpheios Greek
  tree and the index that `@libmorpheus/data` 0.3.0 prepared from npm
  (`8ba328ca…`), and gave what native 0.6.0 gives with the same files:
  - δίδωμι generates 3,317 records, with `skippedRecords` 1, not enumerable;
  - καταβάλλω generates 5,825 records, 3,040 with
    `excludePreverbVariants`.
- JSR end-to-end check: to be done by the maintainer, from
  `@libmorpheus/wasm@0.3.0` as JSR serves it, and recorded here.
