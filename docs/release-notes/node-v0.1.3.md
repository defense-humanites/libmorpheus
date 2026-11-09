<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/node` 0.1.3 — Node-API binding; acquires native libmorpheus 0.4.5 (C ABI 2).

- Results cross into JavaScript as one buffer per operation: warm generation of a large paradigm is 44–58 % faster and scales with contexts again (#47). Analyses and generated forms are unchanged.
- Declares native 0.4.5 instead of 0.3.2, with its Latin fixes.

Install: `npm install @libmorpheus/node@0.1.3`, then `npx libmorpheus-setup --dataset perseids`

Assets: the four npm tarballs (`@libmorpheus/node` and its three platform addon packages) and `SHA256SUMS`.

Release decision: [release-node-0.1.3.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-node-0.1.3.md)
