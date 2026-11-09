<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/data` 0.1.0 — first release of the data acquisition package: downloads a pinned upstream Morpheus stemlib (Alpheios or Perseids), verifies its tree and license, and writes it with a provenance receipt. Contains no linguistic data; runs under Node.js, Deno and Bun.

- `--subset runtime` writes only the files the runtime reads; `--languages` keeps some of a dataset's languages; `--manifest` writes `stemlib-manifest.json` for WebAssembly deployments; `--with-gener` prepares the experimental generation index.

Install: `npx @libmorpheus/data@0.1.0 --help` · `deno add jsr:@libmorpheus/data@0.1.0`

Assets: the npm tarball and `SHA256SUMS`.

Release decision: [release-data-0.1.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-data-0.1.0.md)
