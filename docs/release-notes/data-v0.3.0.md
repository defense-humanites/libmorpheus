<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

`@libmorpheus/data` 0.3.0 — downloads and verifies a pinned upstream Morpheus stemlib; contains no linguistic data. Same datasets and options as 0.2.0.

- `--with-gener` prepares a new generation index (`8ba328ca…`): the stems that occur only in compounds are kept apart under reserved keys (`-dhme/w`) instead of dropped, for the compound verbs that native libmorpheus 0.6.0 and `@libmorpheus/wasm` 0.3.0 generate.
- Earlier runtimes never read those keys and generate as with 0.2.0's index.

Install: `npx @libmorpheus/data@0.3.0 --help` · `deno add jsr:@libmorpheus/data@0.3.0`

Assets: the npm tarball and `SHA256SUMS`.

Release decision: [release-data-0.3.0.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/release-data-0.3.0.md)
