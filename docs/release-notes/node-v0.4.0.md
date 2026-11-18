<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/node` 0.4.0 — Node-API binding; acquires native libmorpheus 0.6.0 (C ABI 2) and depends on `@libmorpheus/data` 0.3.0.

- `generate()` accepts the compound verbs analysis reports and returns their preverb variants; `excludePreverbVariants: true` leaves the variants out.
- It also returns the unaugmented indicatives, movable ν and accented clitics analysis reads, with the dialects all of a form's parts allow. The default limit becomes 65,536 records.
- `--with-gener` prepares the index that keeps the compound-only stems (`8ba328ca…`), which compound verbs need.

Install: `npm install @libmorpheus/node@0.4.0`, then `npx libmorpheus-setup --dataset perseids`

Assets: the four npm tarballs (`@libmorpheus/node` and its three platform addon packages) and `SHA256SUMS`.

Release decision: [release-node-0.4.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-node-0.4.0.md)
