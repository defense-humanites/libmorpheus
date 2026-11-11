<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/data` 0.2.0 — downloads and verifies a pinned upstream Morpheus stemlib; contains no linguistic data. Same datasets and options as 0.1.0.

- `--with-gener` prepares a new generation index (`a2f97677…`): generation returns the forms analysis accepts, so every regular derivation is complete (ἀγγέλλω gains ἤγγειλα and ἠγγέλθην), compound-only stems are dropped, seven unreadable source lines are patched (ἔχω regains its present) and two inherited stem alterations are corrected. 22.1 million forms instead of 12.5.
- Use it with native libmorpheus 0.5.0 or `@libmorpheus/wasm` 0.2.0, which skip the 339 records the engine cannot generate.

Install: `npx @libmorpheus/data@0.2.0 --help` · `deno add jsr:@libmorpheus/data@0.2.0`

Assets: the npm tarball and `SHA256SUMS`.

Release decision: [release-data-0.2.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-data-0.2.0.md)
