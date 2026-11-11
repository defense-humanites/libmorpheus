<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/libmorpheus-logo-sombre.png">
    <img src="docs/assets/libmorpheus-logo-clair.png" alt="libmorpheus" width="525">
  </picture>
</p>

<p align="center">
  A modernization of the Morpheus morphological analyzer for Ancient Greek and Latin.
</p>

<p align="center">
  <a href="docs/public-api.md">C API</a> ·
  <a href="bindings/python/README.md">Python</a> ·
  <a href="bindings/js/node/README.md">Node.js</a> ·
  <a href="bindings/js/wasm/README.md">WebAssembly</a> ·
  <a href="https://humanites.fr/projets/libmorpheus">humanites.fr</a>
</p>

# libmorpheus

`libmorpheus` modernizes the [Morpheus](https://github.com/PerseusDL/morpheus)
morphological analyzer for Ancient Greek and Latin. It turns the historical C
programs into an installable C17 shared library with a stable, opaque ABI, and
comes with JavaScript and Python bindings.

## Distributions

| Distribution | Install | Guide |
| --- | --- | --- |
| C | Release archives for Linux x86-64, Linux aarch64 and macOS arm64, or [build from source](docs/building.md) | [Public C API](docs/public-api.md) |
| Python 3.11+ | `pip install libmorpheus` | [Python guide](bindings/python/README.md) |
| Node.js 20+ | `npm install @libmorpheus/node` | [Node.js guide](bindings/js/node/README.md) |
| WebAssembly (experimental) | `npm install @libmorpheus/wasm` | [WebAssembly guide](bindings/js/wasm/README.md) |

No distribution contains linguistic data: each guide explains how to acquire a
stem library, which [`@libmorpheus/data`](bindings/js/data/README.md) can
download and verify. The Deno FFI binding is no longer maintained; Deno
applications can use the WebAssembly binding from JSR.

## Example

Every analysis that Morpheus accepts is returned. With the Perseids stem
library, the Greek form λύομεν (`lu/omen`) is the first person plural of λύω,
present or unaugmented imperfect, with a short or long stem vowel:

```python
from libmorpheus import Language, Library, Option

with Library("/usr/local/lib/libmorpheus.so") as library:
    with library.context("/path/to/stemlib", Language.GREEK) as context:
        for a in context.analyze("lu/omen", Option.STRICT_CASE):
            print(a.lemma, a.stem, a.ending, a.tense, a.person,
                  a.grammatical_number, a.dialects)
```

```text
lu/w lu omen present first plural ('epic',)
lu/w lu_ omen present first plural ()
lu/w lu omen imperfect first plural ('epic',)
lu/w lu_ omen imperfect first plural ('ionic', 'homeric')
```

## Project status

| Available operation | Ancient Greek | Latin | Status |
| --- | :---: | :---: | --- |
| Analyze an inflected form | Yes | Yes | Supported |
| Generate forms from a lemma | Yes | No | Experimental |

Generation is the inverse of analysis: it returns the forms that the analyzer
accepts for a lemma. These include dialectal, poetic and late variants, and
regular forms that no text may attest. Use it to search texts by lemma, to
precompute a form-to-lemma table or to check the stem data; it does not give
a reference paradigm. See
[Greek lemma generation](docs/public-api.md#greek-lemma-generation).

The public runtime includes:

- structured, caller-owned analysis and generation results;
- per-request analysis options and generation filters;
- isolated contexts that can be used concurrently;
- `cruncher`, retained as a compatibility client of the public library;
- CMake and `pkg-config` installation metadata.

> [!NOTE]
> Native archives and the distributed packages contain no linguistic data. Applications
> must acquire a compatible stem library separately; see [Runtime data](#runtime-data).

## Runtime data

Morpheus reads compiled binary databases called **stemlibs**. Code and data are
versioned and distributed separately.

| Dataset | Analysis | Generation | Repository location |
| --- | --- | --- | --- |
| `perseids-tools` | Greek and Latin | No | `stemlib/` |
| `alpheios-project` (pinned) | Greek | Requires a prepared `gener.index` | `vendor/alpheios-morpheus/dist/stemlib/` |

From a recursive source checkout, prepare a standalone Alpheios directory with
the validated experimental generation index using:

```sh
sh tools/prepare-runtime-data.sh "$PWD/morpheus-greek-data"
```

The [runtime-data guide](docs/runtime-data.md) records exact pinned revisions,
digests, acquisition permissions, and redistribution caveats. The
[stem-library inventory](docs/stem-libraries.md) explains the origin and role of
each dataset.

The [build guide](docs/building.md#rebuild-and-qualify-the-stemlibs) explains
how to rebuild and qualify the stemlibs from their sources.

## Build from source

Building requires CMake 3.25 or newer, Ninja and a C17 compiler. Clone
recursively, then configure, build and test the development preset:

```sh
git clone --recurse-submodules \
  https://github.com/defense-humanites/libmorpheus.git
cd libmorpheus
cmake --preset dev
cmake --build --preset dev
ctest --preset dev
```

The [build guide](docs/building.md) covers the other presets, installation and
use from C, the Alpine container image, the historical `cruncher` command-line
client and the test suites.

## Releases and platform support

Native `v<version>` release tags provide data-free archives and SHA-256 files
for:

- Linux x86-64 glibc;
- Linux aarch64 glibc;
- macOS arm64.

Each binding is versioned independently and declares the native runtime
release and ABI it supports.

The Node.js binding is versioned independently with `node-v<version>` tags. npm
publishes the ESM facade as `@libmorpheus/node` and a matching optional Node-API
addon for each supported native platform; the runtime and stem data remain
separate, verified acquisitions.

The Python binding is versioned independently with `python-v<version>` tags and
publishes the pure-Python `libmorpheus` distribution to PyPI. It uses `ctypes`,
so one universal wheel supports Python 3.11 and newer while applications provide
the compatible native runtime and stem data separately.

The checksum detects corruption; it is not a release signature. See
[platform support](docs/portability.md) for the complete qualification matrix
and [release qualification](docs/releasing.md) for the checks required before a
tag. Release changes are recorded in the [changelog](CHANGELOG.md).

## Architecture and provenance

The current implementation derives from the `perseids-tools` fork, the only
baseline known to compile before this modernization. The repository bundles its
Greek and Latin stemlib and pins a newer Alpheios Greek stemlib for additional
testing and validation.

Further documentation:

- [Architecture baseline](docs/architecture.md)
- [C17 port notes](docs/c17-port.md)
- [Source provenance](docs/provenance.md)
- [Historical utility policy](docs/historical-utilities.md)

The inherited Makefiles remain as a compatibility check for `libs` and
`cruncher`, but new consumers should use CMake and the public ABI. Other
historical programs below `src/` are quarantined and excluded from supported
builds.

## License

This is a mixed-license repository:

- inherited engine, bridge, compatibility, and derived internal code remain
  under [MPL-2.0](LICENSE);
- the normalized public API, the bindings, and marked independently written
  support files use
  [AGPL-3.0-or-later](LICENSE-AGPL-3.0-or-later).

A file's SPDX identifier controls when present; otherwise the root MPL-2.0
license applies. See the [licensing guide](docs/licensing.md) for the precise
file-level boundary and the [license inventory](docs/license-inventory.md) for
its rationale and provenance.

The libmorpheus logos under `docs/assets/` are not covered by these licenses:
all rights are reserved, as recorded in
[`LicenseRef-libmorpheus-marks`](LICENSES/LicenseRef-libmorpheus-marks.txt).
