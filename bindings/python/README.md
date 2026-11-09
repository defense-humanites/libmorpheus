<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# libmorpheus for Python

`libmorpheus` modernizes the [Morpheus](https://github.com/PerseusDL/morpheus)
morphological analyzer for Ancient Greek and Latin. It turns the historical C
programs into an installable C17 shared library with a stable, opaque ABI and a
typed Python binding.

This package loads the
[`libmorpheus`](https://github.com/defense-humanites/libmorpheus) shared library
with the standard-library `ctypes` module. It exposes normalized Greek and Latin
analysis plus experimental Greek lemma generation. Native results are copied
into immutable Python objects before their C allocations are released.

## Summary

1. [Quick start (using the PyPI package)](#quick-start-using-the-pypi-package)
2. [In-depth overview](#in-depth-overview)
   1. [Analyze a form](#analyze-a-form)
   2. [Generate forms from a lemma](#generate-forms-from-a-lemma)
   3. [Use parallel contexts](#use-parallel-contexts)
   4. [Raw access and cleanup](#raw-access-and-cleanup)
3. [Other installation options](#other-installation-options)
   1. [Install from a source checkout](#install-from-a-source-checkout)
   2. [Build the native runtime](#build-the-native-runtime)
4. [Native library and runtime data](#native-library-and-runtime-data)
   1. [Acquire stem data](#acquire-stem-data)
   2. [Acquire the native library](#acquire-the-native-library)
   3. [Language and data coverage](#language-and-data-coverage)
5. [Python and platform support](#python-and-platform-support)
6. [Documentation](#documentation)
7. [Local checks](#local-checks)
8. [License](#license)

## Quick start (using the PyPI package)

The Python package requires Python 3.11 or later and has no third-party runtime
dependencies. Install the typed, universal wheel:

```sh
python -m pip install libmorpheus
```

The wheel contains neither the native library nor linguistic stem data.
Package installation runs no scripts and downloads nothing. Acquire the
matching native library and the Perseids dataset for Greek and Latin analysis
with the explicit setup command:

```sh
libmorpheus-setup --dataset perseids
```

The output directories must not already exist and must not overlap; the
command refuses to overwrite an installation or dataset. It creates
`./morpheus-native` and `./morpheus-data` by default (`--native-output`,
`--data-output`). Then create `app.py`:

```python
import json
from pathlib import Path

from libmorpheus import Language, Library, Option

receipt = json.loads(Path("morpheus-native/MORPHEUS-NATIVE.json").read_text())

with Library(Path("morpheus-native") / receipt["libraryPath"]) as library:
    with library.context("morpheus-data", Language.GREEK) as context:
        analyses = context.analyze(
            "a)/nqrwpos",
            Option.STRICT_CASE,
        )

        for analysis in analyses:
            print(analysis.lemma, analysis.part_of_speech)
```

Run it normally:

```sh
python app.py
```

The binding itself performs no network access and reads no environment
variables. Applications may pass paths from their own configuration:

```python
import os

library_path = os.environ["MORPHEUS_LIBRARY"]
stemlib_path = os.environ["MORPHEUS_STEMLIB"]
```

The acquisition commands, their receipts and the pinned sources are described
under [Native library and runtime data](#native-library-and-runtime-data); a
complete source-checkout recipe appears below.

## In-depth overview

### Analyze a form

```python
from libmorpheus import Language, Library, MorpheusError, Option

try:
    with Library("/usr/local/lib/libmorpheus.so") as library:
        with library.context(
            "/path/to/stemlib", Language.GREEK
        ) as context:
            analyses = context.analyze(
                "a)/nqrwpos", Option.STRICT_CASE
            )
            print(analyses[0].part_of_speech)  # "noun"
            print(analyses[0].grammatical_number)  # "singular"
            print(analyses[0].grammatical_cases)  # ("nominative",)
except MorpheusError as error:
    print(f"Morpheus status {error.status}: {error}")
```

`analyze()` returns stable English identifiers, tuples for combinable masks, and
`None` for inapplicable scalar values. It preserves all analyses. A generic
stemlib `indecl` class remains `"unknown"` because it does not identify a
lexical category. An empty dialect tuple means no recorded restriction.

Options are `IntFlag` values and may be combined with `|`. For example, strict
case plus accent-insensitive fallback is:

```python
options = Option.STRICT_CASE | Option.IGNORE_ACCENTS
analyses = context.analyze("a)/nqrwpos", options)
```

Passing no option uses the binding's default analysis behavior. See the
[native option table](https://github.com/defense-humanites/libmorpheus/blob/main/docs/public-api.md#request-options)
before enabling specialized modes.

`Option.HQ_DICTIONARY` requires both HQ index files. If they are absent,
`analyze()` raises `MorpheusError` with `Status.STEMLIB_ERROR` before native
analysis.

### Generate forms from a lemma

> [!WARNING]
> `generate()` and `generate_raw()` are experimental. Their automated
> differential, isolation, failure, portability, and sanitizer coverage is
> extensive, but sufficient real-world use is still required before this
> qualification can be removed.

Generation needs Alpheios data **and** a prepared generation index,
`gener.index`, at the root of the stemlib directory; analysis needs neither.
The Python package does not prepare the index yet: prepare it once with the
Node.js data package, then install it with the Alpheios data, which verifies
it against the pinned digest:

```sh
npx @libmorpheus/data --dataset alpheios --with-gener --output ./alpheios-node
libmorpheus-data --dataset alpheios --gener-index ./alpheios-node/gener.index \
  --output ./morpheus-greek-data
```

A source checkout can prepare it with `sh tools/prepare-runtime-data.sh`
instead; see [Acquire stem data](#acquire-stem-data). Without the index,
`generate()` raises `MorpheusError` ("stemlib is unavailable or incomplete"). The
example below uses such a directory:

```python
from libmorpheus import (
    Dialect,
    GenerationOptions,
    Language,
    Library,
    MorpheusError,
    Number,
    Status,
)

try:
    with Library("/usr/local/lib/libmorpheus.so") as library:
        with library.context(
            "/path/to/morpheus-greek-data", Language.GREEK
        ) as context:
            duals = context.generate(
                "lo/gos",
                GenerationOptions(
                    number=Number.DUAL,
                    dialect=Dialect.ATTIC,
                    result_limit=256,
                ),
            )
            for form in duals:
                print(form.surface, form.grammatical_cases)
except MorpheusError as error:
    if error.status == Status.RESULT_LIMIT_EXCEEDED:
        print("Increase the explicit result limit for this paradigm")
    else:
        raise
```

`generate()` accepts typed filters for part of speech, dialect, region, person,
number, gender, case, tense, mood, voice, and degree. It preserves dialect
masks, duals, duplicate surfaces, and multiple indexed interpretations unless
filters remove them. Set `exclude_duals=True` when dual forms are unwanted.
`result_limit=0` uses the native default of 4,096; a nonzero value is a hard
safety ceiling, not a truncation request. The explicit maximum is 65,536.

### Use parallel contexts

Calls are synchronous at the Python surface. One context deliberately
serializes its native operations because the underlying state is mutable.
Create separate contexts and submit them to separate threads for independent
work:

```python
from concurrent.futures import ThreadPoolExecutor

with Library("/usr/local/lib/libmorpheus.so") as library:
    with (
        library.context(stemlib, Language.GREEK) as first,
        library.context(stemlib, Language.GREEK) as second,
        ThreadPoolExecutor(max_workers=2) as executor,
    ):
        analysis_future = executor.submit(first.analyze, "a)/nqrwpos")
        generation_future = executor.submit(second.generate, "lo/gos")
        analyses = analysis_future.result()
        forms = generation_future.result()
```

`ctypes.CDLL` releases the GIL during native calls, so distinct contexts can
execute concurrently. The actual speedup depends on the workload and machine.
Reuse warm contexts; the generation index is loaded lazily once per context.

### Raw access and cleanup

Use `analyze_raw()` and `generate_raw()` for ABI inspection and low-level
tools. They return numeric normalized traits, `struct_size`, the complete
11-byte public morphology vector, and a numeric truncation mask. The semantic
methods return named morphology flags and truncated fields.

Close contexts before their parent library. Both objects support context
managers and idempotent `close()` methods. `Library.close()` raises while any
child context remains open. Context managers provide deterministic cleanup,
including when an operation raises.

## Other installation options

### Install from a source checkout

For binding development, install the Python package from a checkout in editable
mode:

```sh
python -m pip install -e bindings/python
```

This installs only the pure-Python facade. It does not compile or install the
native runtime and does not copy stem data.

### Build the native runtime

A recursive checkout can supply all three development components: the Python
facade, native library, and Perseids stemlib.

```sh
git clone --recurse-submodules \
  https://github.com/defense-humanites/libmorpheus.git
cd libmorpheus
cmake --preset dev
cmake --build --preset dev --target morpheus
python -m pip install ./bindings/python
```

Use `build/dev/libmorpheus.so` on Linux or
`build/dev/libmorpheus.dylib` on macOS, and use the checkout's `stemlib/`
directory for Greek and Latin analysis.

## Native library and runtime data

The binding needs both a native `libmorpheus` library and a compatible stemlib.
Neither is part of the Python wheel or source distribution.

| Distribution | Native library | Stem data | What to do |
| --- | --- | --- | --- |
| PyPI wheel or source distribution | Not included | Not included | Run `libmorpheus-setup`, or `libmorpheus-native` and `libmorpheus-data`. |
| Recursive project checkout | Build with CMake | Perseids submodule | Pass the build output and `stemlib/` paths explicitly. |

Binding and runtime versions are independent. Python binding `0.2.1` targets
native runtime `0.4.6` and requires C ABI `2`. The package exports
`MORPHEUS_PYTHON_VERSION`, `MORPHEUS_NATIVE_VERSION`, and
`MORPHEUS_NATIVE_ABI_VERSION`; `__version__` is the conventional alias for the
Python package version.

The three commands use only the standard library, download over HTTPS from
pinned sources, bound every download in size, verify before writing, write
into a directory that must not exist, and remove it again if anything fails.
Each is also importable (`acquire_native()`, `acquire_data()`,
`setup_morpheus()`) and runnable as a module (`python -m libmorpheus.native`,
`python -m libmorpheus.data`, `python -m libmorpheus.setup`). Their options
and receipts match the Node.js binding's commands.

### Acquire stem data

```sh
libmorpheus-data --dataset <alpheios|perseids> --output <directory>
                 [--subset <full|runtime>] [--languages <grc,lat>]
                 [--manifest] [--gener-index <path>]
```

The command downloads the pinned upstream revision of the dataset (the audited
Alpheios or Perseids tree), verifies its file count, tree digest and license
digest, and writes it with `UPSTREAM-LICENSE` and a provenance receipt,
`MORPHEUS-DATA.json` (dataset, languages, source repository and revision,
digests of the whole tree and of the written subset). Alpheios provides Greek
analysis and experimental generation; Perseids provides Greek and Latin
analysis.

- `--subset runtime` writes only the files the libmorpheus runtime reads
  (about 10 MiB for Perseids instead of the whole tree); `--languages`
  keeps only the named ISO 639-3 languages.
- `--manifest` also writes `stemlib-manifest.json` (path, size and SHA-256 of
  every written file), the list a server or a WebAssembly deployment loads
  from.
- `--gener-index <path>` installs a prepared experimental Greek generation
  index (`gener.index`, Alpheios only) after verifying that its SHA-256 is
  the pinned digest of the index derived from the audited revisions. The
  Python package does not prepare the index itself: prepare it once with
  `npx libmorpheus-data --dataset alpheios --with-gener` from the
  `@libmorpheus/data` package, or from a source checkout with
  `sh tools/prepare-runtime-data.sh`, and pass the resulting file.

For analysis from a source checkout, its recursively initialized `stemlib/`
directory (Perseids) and `vendor/alpheios-morpheus/dist/stemlib` (Alpheios)
can be passed to `Library.context()` directly. See the
[runtime-data guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/runtime-data.md)
for pinned sources, validation, and redistribution boundaries.

### Acquire the native library

```sh
libmorpheus-native --output <directory>
```

The command downloads the archive of the declared native release (`v0.4.6`)
for this host (Linux x86-64 glibc, Linux aarch64 glibc or macOS arm64; musl
hosts are refused rather than given an incompatible binary), verifies it
against the SHA-256 sidecar published with the release, extracts it with
symbolic links materialized as files, and writes the receipt
`MORPHEUS-NATIVE.json`, whose `libraryPath` names the shared library to pass
to `Library`. The archives can also be installed by hand from the
[GitHub releases page](https://github.com/defense-humanites/libmorpheus/releases),
or the runtime built from a matching source checkout as shown above. The
binding does not search system paths or environment variables implicitly.

### Language and data coverage

The operation and selected dataset together determine language coverage:

| Operation or dataset | Ancient Greek | Latin | Additional requirement |
| --- | :---: | :---: | --- |
| `analyze()` | Yes | Yes | A stemlib for the selected language. |
| `generate()` | Yes | No | Alpheios data prepared with `gener.index`. |
| Perseids | Yes | Yes | No |
| Alpheios | Yes | No | Prepare `gener.index` for generation. |

See the [stem-library inventory](https://github.com/defense-humanites/libmorpheus/blob/main/docs/stem-libraries.md)
for dataset origins and repository locations.

## Python and platform support

The package requires Python 3.11 or later, ships a `py.typed` marker, and has no
third-party runtime dependencies. Its wheel is `py3-none-any` because the FFI
layer is pure Python; execution still requires a compatible separately
installed native library.

The release qualification matrix covers Python 3.11 and 3.14 on Linux with the
real runtime and an ABI fixture. The native release currently provides Linux
x86-64 glibc, Linux aarch64 glibc, and macOS arm64 archives. Windows is not
supported by native runtime `0.4.6`.

## Documentation

Public classes, enums, immutable result dataclasses, and version constants are
exported directly from `libmorpheus`. The package includes a `py.typed` marker
for static type checkers.

| Topic | Document |
| --- | --- |
| Native ABI, ownership, and options | [Public API](https://github.com/defense-humanites/libmorpheus/blob/main/docs/public-api.md) |
| Runtime and dataset acquisition | [Runtime data](https://github.com/defense-humanites/libmorpheus/blob/main/docs/runtime-data.md) |
| AGPL/MPL file boundary | [Licensing guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/licensing.md) |
| Source and dataset lineage | [Provenance](https://github.com/defense-humanites/libmorpheus/blob/main/docs/provenance.md) |
| Available stem libraries | [Stem libraries](https://github.com/defense-humanites/libmorpheus/blob/main/docs/stem-libraries.md) |
| Supported platforms | [Portability](https://github.com/defense-humanites/libmorpheus/blob/main/docs/portability.md) |
| Release archives and qualification | [Releasing](https://github.com/defense-humanites/libmorpheus/blob/main/docs/releasing.md) |

## Local checks

Build the library and small differential generation index before running the
binding tests:

```sh
cmake --preset dev
cmake --build --preset dev --target \
  morpheus morpheus_gener_index_builder
build/dev/morpheus_gener_index_builder \
  stemlib/gener.index test/generation-service-source.txt
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=bindings/python/src \
python -B -m unittest discover -s bindings/python/test -v
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=bindings/python/src \
python -B bindings/python/test/runtime_smoke.py \
  build/dev/libmorpheus.so stemlib
```

Build and inspect the universal distributions with:

```sh
python -m build bindings/python
python -m pip install --no-deps bindings/python/dist/*.whl
```

## License

The Python binding itself is licensed under
[AGPL-3.0-or-later](LICENSE). Its pure-Python `ctypes` facade does not inherit
the mixed licensing of the separately installed native runtime and contains no
linguistic stem data.

See the [package notice](NOTICE) and the project's
[licensing guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/licensing.md)
for the precise file-level boundary and redistribution considerations.
