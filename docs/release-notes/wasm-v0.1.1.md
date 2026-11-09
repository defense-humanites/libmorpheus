<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/wasm` 0.1.1 — compiled from libmorpheus 0.4.3 (C ABI 2) with Emscripten 4.0.15. Contains no linguistic data.

- Works when installed from JSR (0.1.0 failed to instantiate there, since JSR rewrites the module's import names).
- Compiled from a published native release (0.1.0 came from an untagged commit).
- **Latin defect:** returns no analysis for forms built on the fourth principal part; use 0.1.3.

Install: `npm install @libmorpheus/wasm@0.1.1` · `deno add jsr:@libmorpheus/wasm@0.1.1`

Assets: `morpheus.mjs`, `morpheus.wasm` and `SHA256SUMS`.

Release decision: [release-wasm-0.1.1.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-wasm-0.1.1.md)
