<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/deno` 0.4.3 — **final release of the Deno binding**, which is no longer maintained; acquires native libmorpheus 0.4.5 (C ABI 2).

- Acquires native 0.4.5 instead of 0.4.2, with its Latin fixes; the API is unchanged.
- Deno's development has ended and libmorpheus no longer depends on it. For new code, use `@libmorpheus/wasm` (runs under Deno without FFI permissions) or `@libmorpheus/node`.

Install: `deno add jsr:@libmorpheus/deno@0.4.3`

Assets: the standalone binding archive with its `.sha256` sidecar.

Release decision: [release-deno-0.4.3.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-deno-0.4.3.md)
