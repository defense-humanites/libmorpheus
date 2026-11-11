<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/wasm` 0.2.0 — compiled from libmorpheus 0.5.0 (C ABI 2) with Emscripten 4.0.15. Contains no linguistic data.

- Generation no longer fails a lemma on one record the engine cannot generate: the record is skipped, and the array `generate()` returns gains a read-only, non-enumerable `skippedRecords` count.
- Generated records carry the degree and flags analysis reports, and surfaces lose the stem-boundary hyphen. Analysis is unchanged.
- Prepare `gener.index` with `@libmorpheus/data` 0.2.0.

Install: `npm install @libmorpheus/wasm@0.2.0` · `npx jsr add @libmorpheus/wasm@0.2.0`

Assets: `morpheus.mjs`, `morpheus.wasm` and `SHA256SUMS`.

Release decision: [release-wasm-0.2.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-wasm-0.2.0.md)
