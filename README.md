<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/libmorpheus-logo-sombre.svg">
    <img src="docs/assets/libmorpheus-logo-clair.svg" alt="libmorpheus" width="484">
  </picture>
</p>

<p align="center">
  A modernization of the Morpheus morphological analyzer for Ancient Greek and Latin.
</p>

<p align="center">
  <a href="docs/public-api.md">C API</a> ·
  <a href="bindings/python/README.md">Python</a> ·
  <a href="bindings/js/node/README.md">Node.js</a> ·
  <a href="bindings/js/wasm/README.md">WebAssembly</a>
</p>

<br>

# libmorpheus

`libmorpheus` modernizes the [Morpheus](https://github.com/PerseusDL/morpheus)
morphological analyzer for Ancient Greek and Latin. It turns the historical C
programs into an installable C17 shared library with a stable, opaque ABI, and
comes with Python, Node.js and WebAssembly distributions.

Unlike the original programs, which kept their state in global variables, the
library is thread-safe: each context holds its own state, so an application
can give each thread its own context and analyze or generate forms in
parallel. The runtime also
analyzes about three times faster than the first release of the library (see
[Performance](#performance)).

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

## Distributions

| Distribution | Install | Guide |
| --- | --- | --- |
| C | Release archives for Linux x86-64, Linux aarch64 and macOS arm64, or [build from source](docs/building.md) | [Public C API](docs/public-api.md) |
| Python 3.11+ | `pip install libmorpheus` | [Python guide](bindings/python/README.md) |
| Node.js 20+ | `npm install @libmorpheus/node` | [Node.js guide](bindings/js/node/README.md) |
| WebAssembly | `npm install @libmorpheus/wasm` | [WebAssembly guide](bindings/js/wasm/README.md) |

No distribution contains linguistic data: applications acquire it separately,
as described under [Runtime data](#runtime-data).

## Runtime data

Morpheus reads compiled binary databases called stem libraries (stemlibs).
Code and data are versioned and distributed separately: each guide explains
how to acquire a stemlib and open a context on it, and
[`@libmorpheus/data`](bindings/js/data/README.md) downloads and verifies the
datasets for JavaScript applications.

| Dataset | Analysis | Generation | Repository location |
| --- | --- | --- | --- |
| `perseids-tools` | Greek and Latin | No | `stemlib/` |
| `alpheios-project` (pinned) | Greek | Requires a prepared `gener.index` | `vendor/alpheios-morpheus/dist/stemlib/` |

The [runtime-data guide](docs/runtime-data.md) records exact pinned revisions,
digests, acquisition permissions, and redistribution caveats. The
[stem-library inventory](docs/stem-libraries.md) explains the origin and role of
each dataset. The [build guide](docs/building.md#prepare-the-runtime-data)
explains how to prepare the data from a source checkout, and how to rebuild and
qualify the stemlibs from their sources.

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

## Performance

The figures below come from the release benchmark
([`bench/compare.mjs`](docs/benchmarks.md)), run on the same 12-core Apple
Silicon host for every release with the pinned Alpheios stem library. Analysis
times cover the 24 Greek words of the test corpus; generation produces the
complete paradigm of ἵημι (`i(/hmi`). They give orders of magnitude, not
guarantees: the reports are retained in
[`bench/release-evidence/`](bench/release-evidence/).

**Since the first release.** Analysis time per word, warm:

| | 0.1.0 (August 2026) | 0.4.6 (November 2026) |
| --- | ---: | ---: |
| `cruncher`, one process | 668 µs | 202 µs |
| Library, one context | 662 µs | 215 µs |
| Library, four contexts in parallel | 284 µs | 88 µs |

Four contexts thus analyze about 11,000 words per second, where a single
`cruncher` process of the first release analyzed 1,500. Most of the gain comes
from 0.4.6, which removed thread-local reads and repeated file opening from the
search for candidate stems ([release notes](docs/release-0.4.6.md)).

**C and its distributions.** Analysis throughput, in words per second, with
native 0.4.6:

| Distribution | 1 context | 2 contexts | 4 contexts |
| --- | ---: | ---: | ---: |
| C (`cruncher`, one process) | 4,415 | – | – |
| Python | 4,675 | 7,606 | 10,988 |
| Node.js | 4,183 | 7,064 | 10,636 |
| WebAssembly (one worker per context) | 3,798 | 6,693 | 10,949 |

The Python and Node.js bindings analyze at the speed of the C runtime. The
WebAssembly module, measured in a separate run against Node.js, reaches 86 to
93 % of the native throughput; it needs 12 to 24 ms to start a pool and about
25 MiB per instance, against a few milliseconds and a few MiB for native
contexts ([comparison](docs/wasm.md#third-run-native-046-and-module-014)).
Generating the paradigm of ἵημι takes 3.7 ms through Node.js and 9.8 ms
through Python at one context, and up to 933 paradigms per second through
Node.js with four contexts ([benchmarks](docs/benchmarks.md)).

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
use from C, the preparation and rebuilding of the stemlibs, the Alpine container
image, the historical `cruncher` command-line client and the test suites.

## Releases and platform support

Each distribution is versioned independently. Native `v<version>` tags provide
data-free archives and SHA-256 files for the platforms listed under
[Distributions](#distributions); the bindings and the data package use
`python-v`, `node-v`, `wasm-v` and `data-v` tags, and each binding declares the
native runtime release and ABI it supports. The checksum detects corruption; it
is not a release signature.

See [platform support](docs/portability.md) for the complete qualification
matrix and [release qualification](docs/releasing.md) for the checks required
before a tag. Release changes are recorded in the [changelog](CHANGELOG.md).

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
