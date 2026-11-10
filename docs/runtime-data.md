<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Acquiring runtime data

The native archives and the binding packages intentionally contain no
linguistic data. Applications select a compiled stem library at runtime;
experimental Greek generation additionally requires a validated `gener.index`
at that stemlib's root.

The native runtime is likewise separate from the binding packages. Binding and
runtime versions are independent; each binding declares the exact native
release and ABI its acquisition commands install. Package installation runs no
script, so the Node.js and Python bindings provide an explicit combined setup
command that installs the declared GitHub Release archive and the selected data
without a native toolchain:

```sh
npx libmorpheus-setup --dataset perseids     # Node.js binding
libmorpheus-setup --dataset perseids         # Python binding
```

Use `--dataset alpheios` for the Greek-only reference dataset (the Node.js
command also takes `--with-gener` for experimental generation; the Python one
installs a prepared index with `--gener-index`). The commands verify the release
and dataset, write both receipts, and remove the new native directory if data
acquisition fails. The two outputs must be absent and non-overlapping. Separate
`libmorpheus-native` and `libmorpheus-data` commands remain available for
independent acquisition.

The native installer verifies the release SHA-256 sidecar and extracts only
safe archive entries. Its receipt records both the binding version and the
installed native version, and names the shared library to load. It supports
Linux x86-64 glibc, Linux aarch64 glibc, and macOS arm64.

Deployments that need the data without any native binding — the WebAssembly
binding under Node.js, Deno or Bun, browsers, Cloudflare Workers — use the
standalone acquisition package, which contains no data itself:

```sh
npx @libmorpheus/data --dataset perseids --subset runtime --manifest --output ./stemlib
```

`--subset runtime` writes only the files the runtime reads (see the
WebAssembly binding's README for the list) and `--manifest` adds a
`stemlib-manifest.json` with every file's path, size and SHA-256, for
`fetchStemlib()`, bundlers and `writeStemlib()` callers. The command is the
Node.js binding's `libmorpheus-data`, published on its own with those two
additions; `bindings/js/data/README.md` documents it. The Python package
provides the same command with the same options, pins, receipts and runtime
subset (`libmorpheus-data`, `python -m libmorpheus.data`, `acquire_data()`),
except that it installs a prepared `gener.index` through `--gener-index`
after checking its digest instead of preparing one; `bindings/python/README.md`
documents it.

## Choose a dataset

| Use                     | Dataset path in a recursive `libmorpheus` checkout | Languages               | `gener.index`                    |
| ----------------------- | -------------------------------------------------- | ----------------------- | -------------------------------- |
| Analysis                | `stemlib/`                                         | Ancient Greek and Latin | Not required                     |
| Reference analysis      | `vendor/alpheios-morpheus/dist/stemlib`            | Ancient Greek           | Not required                     |
| Experimental generation | Prepared directory described below                 | Ancient Greek           | Included after local preparation |

Either dataset can be acquired without Git or a C toolchain. For Greek and
Latin analysis:

```sh
npx @libmorpheus/data --dataset perseids --output ./morpheus-data
```

Use `--dataset alpheios` for the Greek-only reference dataset. The command
downloads a pinned archive directly from the original GitHub repository, checks
the complete selected tree and license, and refuses an existing output
directory. Pass the resulting absolute `morpheus-data` path to the context.

A recursive checkout of the matching release remains useful for native
development and for the current generation-index preparation workflow:

```sh
git clone --depth 1 --branch v0.3.2 --recurse-submodules \
  --shallow-submodules \
  https://github.com/defense-humanites/libmorpheus.git libmorpheus-data
```

## Prepare Greek generation data

The data package can add `--with-gener` to the Alpheios acquisition command:

```sh
npx @libmorpheus/data --dataset alpheios --with-gener --output ./morpheus-greek-data
```

This route needs no C toolchain. It downloads the pinned Alpheios data directly
for the output and the pinned Perseids data as in-memory support for historical
derivation rules. The bundled internal WebAssembly preparer expands the source
corpus; an internal JavaScript builder emits the index. Both intermediate and
final digests must match the native reference before the command succeeds. It
refuses an existing output directory rather than overwriting data.

Native developers can produce the same bytes from a recursive release checkout
with CMake, Ninja, and a C compiler:

```sh
sh libmorpheus-data/tools/prepare-runtime-data.sh "$PWD/morpheus-greek-data"
```

Use the resulting absolute `morpheus-greek-data` path for both analysis and
experimental generation. The expected SHA-256 of its `gener.index` from this
source tree, which adds the default principal parts of
[gener-derivations.md](gener-derivations.md#default-principal-parts), is:

```text
f223ca3257b85298513cf9984bfc0c63a3aa28f900eef8cf000150a24bb68629
```

Native releases up to 0.4.6 and `@libmorpheus/data` 0.1.0 prepare the
historical index, `5aa76d8c86c54af5121a3cce506ecaa57d14c6667ac0f091efd164ddfa9822d6`.

The native preparer and index builder remain internal build-time programs. The
data package exposes only the acquisition operation; its WebAssembly preparer
and JavaScript index builder remain internal modules, not part of the C API.

## Distribution boundary

The prepared directory contains Alpheios linguistic data and an index derived
from it. `libmorpheus` does not place either one in native archives, binding
packages, or downloadable release assets. Review the
[provenance and licensing evidence](provenance.md) before redistributing a
prepared directory. The local preparation workflow does not change the MPL/AGPL
code boundary described in the [licensing guide](licensing.md).

The machine-checked [stemlib redistribution gate](stemlib-redistribution.md)
records the exact datasets and notices used by this project. Its current
`review-required` state prevents these internal archives from becoming release,
package, container, or retained CI payloads without a separate decision.

See the [stem-library inventory](stem-libraries.md) for upstream repositories
and the language coverage of the three principal datasets.
