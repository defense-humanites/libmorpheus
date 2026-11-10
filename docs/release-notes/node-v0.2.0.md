<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/node` 0.2.0 — Node-API binding; acquires native libmorpheus 0.4.6 (C ABI 2).

- `analyze()` and `generate()` decode named results directly: generating a large paradigm is 45–73 % faster and now scales with contexts (985 instead of 267 operations per second at four contexts), with about half the memory.
- Behaviour change: the name arrays of results (`dialects`, `genders`, `morphFlags`, …) are frozen and shared between records, as their `readonly` types declared. Copy one before changing it.

Install: `npm install @libmorpheus/node@0.2.0`, then `npx libmorpheus-setup --dataset perseids`

Assets: the four npm tarballs (`@libmorpheus/node` and its three platform addon packages) and `SHA256SUMS`.

Release decision: [release-node-0.2.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-node-0.2.0.md)
