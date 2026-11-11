<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/node` 0.3.0 — Node-API binding; acquires native libmorpheus 0.5.0 (C ABI 2) and depends on `@libmorpheus/data` 0.2.0.

- Generation no longer fails a lemma on one record the engine cannot generate: the record is skipped, and the arrays `generate()` and `generateRaw()` return gain a read-only, non-enumerable `skippedRecords` count.
- Generated records carry the degree and flags analysis reports, and surfaces lose the stem hyphen.
- `--with-gener` prepares the new generation index: every regular derivation complete, as analysis accepts it. Generation returns the forms analysis accepts, not a reference paradigm.

Install: `npm install @libmorpheus/node@0.3.0`, then `npx libmorpheus-setup --dataset perseids`

Assets: the four npm tarballs (`@libmorpheus/node` and its three platform addon packages) and `SHA256SUMS`.

Release decision: [release-node-0.3.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-node-0.3.0.md)
