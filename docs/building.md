<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Building libmorpheus from source

This guide collects the build, installation and qualification details that
the [README](../README.md) summarizes. Applications that only need to analyze
forms can instead install one of the
[distributions](../README.md#distributions).

## Build the native library

### Requirements

- CMake 3.25 or newer;
- Ninja;
- a C17 compiler.

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
[public API reference](public-api.md) documents the complete ABI, error
statuses, ownership rules, and buffer contracts.

## Prepare the runtime data

From a recursive source checkout, prepare a standalone Alpheios directory with
the validated experimental generation index using:

```sh
sh tools/prepare-runtime-data.sh "$PWD/morpheus-greek-data"
```

Use the resulting absolute path for both analysis and generation. The
[runtime-data guide](runtime-data.md#prepare-greek-generation-data) gives the
expected digest of its `gener.index` and a route that needs no C toolchain.

## Rebuild and qualify the stemlibs

The source checkout can reconstruct complete Greek and Latin stemlibs through
an explicit, opt-in production graph. Python 3 is required in addition to the
native build requirements; Perl is not required. Configure the internal
producers, then invoke the aggregate target:

```sh
cmake --preset dev -DMORPHEUS_BUILD_STEMLIB_TOOLS=ON
cmake --build --preset dev --target morpheus_stemlib_production
```

The target recreates two isolated stages without modifying the source tree or
the checked-in stemlibs:

| Language | Reconstructed stemlib root | Production receipt |
| --- | --- | --- |
| Greek | `build/dev/stemlib-production/greek/` | `build/dev/stemlib-production/greek/MORPHEUS-STEMLIB-PRODUCTION-RECEIPT.json` |
| Latin | `build/dev/stemlib-production/latin/` | `build/dev/stemlib-production/latin/MORPHEUS-STEMLIB-PRODUCTION-RECEIPT.json` |

Each root contains its `Greek/` or `Latin/` runtime tree plus ordered input and
output manifests, provenance, and baseline comparisons. The
`morpheus_stemlib_production_greek` and
`morpheus_stemlib_production_latin` targets can be run independently. Repeated
invocations delete and recreate only the corresponding build-tree stage.

Portable developer builds record the local compiler and tool versions. The
reference qualification is deliberately stricter and fails configuration
unless it runs on Ubuntu 24.04 x86-64 with GCC 14 and Python 3.12:

```sh
CC=gcc-14 cmake --preset dev \
  -DMORPHEUS_BUILD_STEMLIB_TOOLS=ON \
  -DMORPHEUS_STEMLIB_QUALIFICATION_PROFILE=github-ubuntu-24.04-gcc-14-python-3.12
cmake --build --preset dev --target morpheus_stemlib_production
ctest --preset dev
```

CI performs two additional clean builds per language, compares their complete
outputs and receipts, and checks every reviewed difference against the
Perseids and pinned Alpheios baselines. The
[production manifest](stemlib-production-manifest.md) documents the 379
source inputs and staging corrections; the
[production audit](stemlib-production-audit.md) records the restored
producers, reproducibility proof, and accepted binary-format exceptions.

This facility is internal production and qualification infrastructure. It is
not installed, its outputs are not included in native or binding packages, and
successful reconstruction does not grant permission to redistribute the
linguistic datasets.

For deployment-shape qualification, a second opt-in target filters each fresh
stage down to the files read by the runtime and writes deterministic archives,
SHA-256 sidecars, and schema-1 runtime receipts:

```sh
cmake --build --preset dev --target morpheus_stemlib_runtime_artifacts
```

The results are written below `build/dev/stemlib-runtime-artifacts/`. They are
internal test artifacts: CI exercises the complete Greek and Latin fixture
suite after extraction but retains only their receipts and checksums, not the
archives. The target does not make the datasets release assets or establish a
redistribution right. The
[redistribution gate](stemlib-redistribution.md) records the exact data
trees and licensing evidence and keeps every payload publication channel
closed pending an explicit review.

## Alpine container image

The Dockerfile supports `linux/amd64` and `linux/arm64` with BuildKit/QEMU. Its
image is a local qualification and application-build target. The default
Alpine multi-stage image builds and tests the C17 runtime on musl,
then ships the installed library, `cruncher`, runtime dependencies, and the
prepared `alpheios-project` stemlib:

```sh
docker build --target runtime -t morpheus .
printf 'a)/nqrwpos\n' | docker run --rm -i morpheus -S
```

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

## Test suites

Two separate fixture suites prevent stemlib differences from being mistaken for
runtime regressions:

- `legacy_fixtures` checks inherited Greek and Latin expectations against the
  `perseids-tools` dataset;
- `alpheios_greek_fixtures` checks Greek reference cases against the pinned
  Alpheios dataset.

Public ABI, installed-package, parallel-context, binding, ASan/UBSan, and TSan
tests complement those fixtures.
