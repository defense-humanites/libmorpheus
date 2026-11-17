<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/wasm` 0.3.0 — compiled from libmorpheus 0.6.0 (C ABI 2) with Emscripten 4.0.15. Contains no linguistic data.

- `generate()` accepts the compound verbs analysis reports and returns their preverb variants; `excludePreverbVariants: true` leaves the variants out.
- It also returns the unaugmented indicatives, movable ν and accented clitics analysis reads, with the dialects all of a form's parts allow. The default limit becomes 65,536 records. Analysis is unchanged except one reading.
- Prepare `gener.index` with `@libmorpheus/data` 0.3.0.

Install: `npm install @libmorpheus/wasm@0.3.0` · `npx jsr add @libmorpheus/wasm@0.3.0`

Assets: `morpheus.mjs`, `morpheus.wasm` and `SHA256SUMS`.

Release decision: [release-wasm-0.3.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-wasm-0.3.0.md)
