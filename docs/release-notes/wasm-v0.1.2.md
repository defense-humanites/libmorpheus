<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/wasm` 0.1.2 — compiled from libmorpheus 0.4.4 (C ABI 2) with Emscripten 4.0.15. Contains no linguistic data.

- Faster cold start: `writeStemlib()` adopts the bytes it is given instead of copying them (about 20 → 7 ms for the Greek runtime subset), and the first analysis falls to about 6 ms.
- **Latin defect:** returns no analysis for forms built on the fourth principal part; use 0.1.3.

Install: `npm install @libmorpheus/wasm@0.1.2` · `deno add jsr:@libmorpheus/wasm@0.1.2`

Assets: `morpheus.mjs`, `morpheus.wasm` and `SHA256SUMS`.

Release decision: [release-wasm-0.1.2.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-wasm-0.1.2.md)
