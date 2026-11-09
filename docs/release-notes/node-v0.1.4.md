<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/node` 0.1.4 — Node-API binding; acquires native libmorpheus 0.4.6 (C ABI 2).

- Declares native 0.4.6 instead of 0.4.5: analysis about three times faster, results unchanged.
- A context that cannot be opened names its stemlib and language (`opening … for Latin failed: …`) instead of giving the status text alone.

Install: `npm install @libmorpheus/node@0.1.4`, then `npx libmorpheus-setup --dataset perseids`

Assets: the four npm tarballs (`@libmorpheus/node` and its three platform addon packages) and `SHA256SUMS`.

Release decision: [release-node-0.1.4.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-node-0.1.4.md)
