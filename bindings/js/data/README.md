<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/defense-humanites/libmorpheus/main/docs/assets/libmorpheus-logo-sombre.svg">
    <img src="https://raw.githubusercontent.com/defense-humanites/libmorpheus/main/docs/assets/libmorpheus-logo-clair.svg" alt="libmorpheus" width="390">
  </picture>
</p>

# @libmorpheus/data

Acquires the stem data that the [libmorpheus](https://github.com/defense-humanites/libmorpheus)
morphological analyzer reads, for any of its distributions: the
[WebAssembly binding](https://github.com/defense-humanites/libmorpheus/tree/main/bindings/js/wasm)
(browsers, Node.js, Deno, Bun, Cloudflare Workers), the native bindings and
the C library.

The package **contains no linguistic data**. It downloads a pinned upstream
Morpheus dataset from its public Git repository, verifies the complete file
tree and the upstream license against digests pinned in the package, and
writes the result into a new directory next to that license and a
provenance receipt. The datasets remain distributed by their upstream
projects under their own terms; read the
[redistribution policy](https://github.com/defense-humanites/libmorpheus/blob/main/docs/stemlib-redistribution.md)
before republishing what you acquire.

## Usage

The package is published on npm and on JSR. The command is tested under
Node.js 20+; it uses only Node.js built-in modules, so it also runs under
Deno 2 and Bun through their Node.js compatibility:

```sh
# Greek and Latin analysis: the Perseids dataset, runtime files only,
# with a manifest for the WebAssembly facade or a bundler.
npx @libmorpheus/data --dataset perseids --subset runtime --manifest --output ./stemlib
deno run -A jsr:@libmorpheus/data --dataset perseids --subset runtime --manifest --output ./stemlib
bunx @libmorpheus/data --dataset perseids --subset runtime --manifest --output ./stemlib

# Greek analysis and experimental generation: the Alpheios reference
# dataset with its validated generation index.
npx @libmorpheus/data --dataset alpheios --subset runtime --with-gener --output ./stemlib-greek
```

Under Deno, `-A` can be narrowed to
`--allow-net=codeload.github.com --allow-read=./stemlib --allow-write=./stemlib`.

| Option | Effect |
|---|---|
| `--dataset <alpheios\|perseids>` | Alpheios: Greek, generation supported. Perseids: Greek and Latin. |
| `--output <directory>` | Created by the command; an existing path is refused. |
| `--subset <full\|runtime>` | `full` (default) writes the whole dataset; `runtime` only what libmorpheus reads. |
| `--languages <grc,lat>` | Keep only these ISO 639-3 languages (default: all of the dataset). |
| `--with-gener` | Build `gener.index` for experimental Greek generation (Alpheios only). |
| `--manifest` | Also write `stemlib-manifest.json`: every written file with its size and SHA-256. |

The output holds one directory per language (`Greek/`, `Latin/`),
`gener.index` at the root when built, the upstream license as
`UPSTREAM-LICENSE`, and the receipt `MORPHEUS-DATA.json` (dataset, source
repository and revision, verified tree digest, written subset and its own
digest, generation index digest).

The same operation is available as a library:

```js
import { acquireMorpheusData } from "@libmorpheus/data";

const receipt = await acquireMorpheusData({
  dataset: "perseids",
  output: "./stemlib",
  subset: "runtime",
  manifest: true,
});
console.log(receipt.subset.count, receipt.source.revision);
```

## The runtime subset

Morpheus datasets carry their historical sources and index production
scripts next to the compiled tables. The runtime reads, per language,
`rule_files/`, `steminds/{nomind,vbind}{,.lindex}`,
`endtables/{indices,out}/`, `derivs/indices/derivind` and
`stemsrc/{vbs.cmp.ml,lemlist}` (where the dataset has them; Perseids Latin
has no `lemlist`), plus `gener.index` at the stemlib root for
Greek generation. `--subset runtime` writes exactly that: 275 files and
10 MiB for Perseids (both languages), 156 files and 19 MiB for Alpheios
with `gener.index`. `isRuntimeFile(path, languages)` exposes the predicate.

## Feeding the WebAssembly binding

With `--manifest`, a server reads the manifest and hands the files to the
module:

```js
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { createMorpheus, MorpheusLanguage } from "@libmorpheus/wasm";

const root = "./stemlib";
const manifest = JSON.parse(await readFile(join(root, "stemlib-manifest.json"), "utf8"));
const entries = await Promise.all(
  manifest.files.map(async ({ path }) => [path, await readFile(join(root, ...path.split("/")))]),
);
const morpheus = await createMorpheus();
const latin = morpheus.open({ stemlib: morpheus.writeStemlib(entries), language: MorpheusLanguage.Latin });
```

A browser serves the directory as static assets and passes the manifest's
paths to `fetchStemlib()`; a Cloudflare Worker bundles the same files as
Data modules. The
[WebAssembly binding's README](https://github.com/defense-humanites/libmorpheus/blob/main/bindings/js/wasm/README.md)
describes each configuration.

## Datasets

| Dataset | Source | Languages | Generation |
|---|---|---|---|
| `alpheios` | [alpheios-project/morpheus](https://github.com/alpheios-project/morpheus) at `4632415` | Greek | experimental, validated index |
| `perseids` | [perseids-tools/morpheus](https://github.com/perseids-tools/morpheus) at `ab6898f` | Greek, Latin | no |

The pinned revisions are those the libmorpheus
[runtime-data guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/runtime-data.md)
and [provenance records](https://github.com/defense-humanites/libmorpheus/blob/main/docs/provenance.md)
describe. The command performs no other network access and installs
nothing.

## License

AGPL-3.0-or-later. The embedded generation preparer contains MPL-2.0
Morpheus code compiled with the MIT-licensed Emscripten runtime; see
`NOTICE` and `LICENSES/`.
