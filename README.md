# libmorpheus

`libmorpheus` modernizes the [Morpheus](https://github.com/PerseusDL/morpheus)
morphological analyzer for Ancient Greek and Latin. It turns the historical C
programs into an installable C17 shared library with a stable, opaque ABI, and
comes with JavaScript and Python bindings.

## Summary

1. [Project status](#project-status)
2. [Bindings](#bindings)
3. [Build the native library](#build-the-native-library)
   1. [Requirements](#requirements)
   2. [Steps and options](#steps-and-options)
4. [Install and consume from C](#install-and-consume-from-c)
5. [Runtime data](#runtime-data)
6. [Alpine container images](#alpine-container-images)
   1. [`runtime`](#runtime)
   2. [`deno-runtime`](#deno-runtime)
8. [`cruncher`](#cruncher)
9. [Releases and platform support](#releases-and-platform-support)
10. [Architecture and provenance](#architecture-and-provenance)
11. [License](#license)

## Project status

| Available operation | Ancient Greek | Latin | Status |
| --- | :---: | :---: | --- |
| Analyze an inflected form | Yes | Yes | Supported |
| Generate forms from a lemma | Yes | No | Experimental |

The public runtime includes:

- structured, caller-owned analysis and generation results;
- per-request analysis options and generation filters;
- isolated contexts that can be used concurrently;
- `cruncher`, retained as a compatibility client of the public library;
- CMake and `pkg-config` installation metadata.

> [!NOTE]
> Native archives and the distributed packages contain no linguistic data. Applications
> must acquire a compatible stem library separately; see [Runtime data](#runtime-data).

## Bindings

Bindings expose the native C API to other language ecosystems. The Deno binding
is published; the Node.js binding is under active development:

| Binding | Description | Documentation |
| --- | --- | --- |
| Deno 2 | Typed TypeScript API for analysis and experimental Greek generation, published on JSR | [Deno binding guide](bindings/js/deno/README.md) |
| Node.js 20+ | ESM facade over an asynchronous Node-API addon | [Node.js binding guide](bindings/js/node/README.md) |
| Python 3.11+ | Pure-Python `ctypes` facade over the stable C ABI | [Python binding guide](bindings/python/README.md) |

Native consumers should instead use the [public C API](docs/public-api.md).

## Build the native library

### Requirements

- CMake 3.25 or newer;
- Ninja;
- a C17 compiler;
- Deno 2 only for the binding tests.

### Steps and options

The `alpheios-project` reference stemlib is a pinned Git submodule, so clone recursively:

```sh
git clone --recurse-submodules \
  https://github.com/defense-humanites/libmorpheus.git
cd libmorpheus
```

For an existing clone:

```sh
git submodule update --init --recursive
```

Configure, build, and test the development preset:

```sh
cmake --preset dev
cmake --build --preset dev
ctest --preset dev
```

This produces `build/dev/libmorpheus.so` (or the platform equivalent) and, by
default, `build/dev/cruncher`. The runtime build consumes compiled stemlibs and
does not require Flex.

To use another compiled stemlib for the Alpheios fixture suite:

```sh
cmake --preset dev -DMORPHEUS_STEMLIB_DIR=/absolute/path/to/stemlib
```

Sanitizer and optimized test configurations are available as separate presets:

```sh
cmake --preset sanitizers
cmake --build --preset sanitizers
ctest --preset sanitizers
```

```sh
cmake --preset thread-sanitizer
cmake --build --preset thread-sanitizer
ctest --preset thread-sanitizer
```

```sh
cmake --preset release -DBUILD_TESTING=ON
cmake --build --preset release
ctest --preset release
```

The Release tests also install into a clean prefix and verify the public package
boundary.

## Install and consume from C

Install the development build into the prefix of your choice:

```sh
cmake --install build/dev --prefix /chosen/prefix
```

The installation contains the shared library, `morpheus/morpheus.h`, the
`Morpheus::morpheus` CMake target, `libmorpheus.pc`, and `cruncher`. Runtime data
is not installed with the library.

With CMake:

```cmake
find_package(Morpheus 0.1 CONFIG REQUIRED)
target_link_libraries(my_analyzer PRIVATE Morpheus::morpheus)
```

With `pkg-config`:

```sh
cc analyzer.c $(pkg-config --cflags --libs libmorpheus)
```

Minimal API use:

```c
#include <stdint.h>
#include <morpheus/morpheus.h>

int main(void) {
  morpheus_config config = {
    MORPHEUS_ABI_VERSION,
    sizeof config,
    "/path/to/stemlib",
    MORPHEUS_LANGUAGE_GREEK
  };
  morpheus_context *context = NULL;
  morpheus_result *result = NULL;

  if (morpheus_open(&config, &context) == MORPHEUS_OK &&
      morpheus_analyze(
        context,
        (const uint8_t *)"a)/nqrwpos",
        sizeof "a)/nqrwpos" - 1,
        MORPHEUS_OPTION_STRICT_CASE,
        &result
      ) == MORPHEUS_OK) {
    for (size_t i = 0; i < morpheus_result_count(result); i++) {
      morpheus_analysis analysis;
      if (morpheus_result_get(result, i, &analysis) == MORPHEUS_OK) {
        /* analysis.lemma, analysis.stem, morphology fields, ... */
      }
    }
  }

  morpheus_result_free(result);
  morpheus_close(context);
  return 0;
}
```

Results preserve Morpheus ordering and duplicates. The caller owns every
successful result until `morpheus_result_free()`. Distinct contexts may run
concurrently; calls on one context must be serialized. The
[public API reference](docs/public-api.md) documents the complete ABI, error
statuses, ownership rules, and buffer contracts.

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
each dataset; the [production audit](docs/stemlib-production-audit.md) records
why the checked-in build drivers are not yet a supported reproducible compiler.

## Alpine container images

We provide two Alpine container images to facilitate the use of the library.
The Dockerfile supports `linux/amd64` and `linux/arm64` with BuildKit/QEMU.
These images are local qualification and application-build targets.

### `runtime`

The default Alpine multi-stage image builds and tests the C17 runtime on musl,
then ships the installed library, `cruncher`, runtime dependencies, and the
prepared `alpheios-project` stemlib:

```sh
docker build --target runtime -t morpheus .
printf 'a)/nqrwpos\n' | docker run --rm -i morpheus -S
```

### `deno-runtime`

The `deno-runtime` target adds Deno while preinstalling only the native runtime
and prepared data:

```sh
docker build --target deno-runtime -t morpheus-deno .
```

Applications consume the binding as a normal JSR dependency. See the
[Deno binding guide](bindings/js/deno/README.md#docker-image) for the preconfigured
paths and a consumer example.

## `cruncher`

The historical command-line interface remains available as a compatibility
client of the library. It reads `MORPHLIB` as before:

```sh
printf 'a)/nqrwpos\n' | \
  MORPHLIB="$PWD/vendor/alpheios-morpheus/dist/stemlib" \
  build/dev/cruncher -S
```

Retained options include `-L` for Latin, `-S` for non-strict case, `-n` to
ignore accents, `-d` for database format, `-e` for numeric feature indices,
`-k` to retain Beta Code, `-l` for lemma-only output, and `-V` for verbs only.

## Releases and platform support

Native `v<version>` release tags provide data-free archives and SHA-256 files
for:

- Linux x86-64 glibc;
- Linux aarch64 glibc;
- macOS arm64.

The Deno binding has an independent version and uses `deno-v<version>` tags for
its standalone source archive and JSR publication. Each binding version declares
the native runtime release and ABI it supports.

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

Two separate fixture suites prevent stemlib differences from being mistaken for
runtime regressions:

- `legacy_fixtures` checks inherited Greek and Latin expectations against the
  `perseids-tools` dataset;
- `alpheios_greek_fixtures` checks Greek reference cases against the pinned
  Alpheios dataset.

Public ABI, installed-package, parallel-context, Deno, ASan/UBSan, and TSan
tests complement those fixtures.

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
- the normalized public API, Deno binding, and marked independently written
  support files use
  [AGPL-3.0-or-later](LICENSE-AGPL-3.0-or-later).

A file's SPDX identifier controls when present; otherwise the root MPL-2.0
license applies. See the [licensing guide](docs/licensing.md) for the precise
file-level boundary and the [license inventory](docs/license-inventory.md) for
its rationale and provenance.
