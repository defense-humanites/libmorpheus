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

The wheel contains neither the native library nor linguistic stem data. Install
a compatible native `libmorpheus` release and stemlib as described below, then
create `app.py`:

```python
from libmorpheus import Language, Library, Option

with Library("/path/to/libmorpheus.so") as library:
    with library.context("/path/to/stemlib", Language.GREEK) as context:
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

Version `0.1.1` deliberately leaves runtime and data acquisition outside the
Python package. The [native releases](https://github.com/defense-humanites/libmorpheus/releases)
and [runtime-data guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/runtime-data.md)
provide the required components; a complete source-checkout recipe appears
below.

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
            "/path/to/stemlib", Language.GREEK
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
| PyPI wheel or source distribution | Not included | Not included | Install a compatible native release and acquire a stemlib. |
| Recursive project checkout | Build with CMake | Perseids submodule | Pass the build output and `stemlib/` paths explicitly. |

Binding and runtime versions are independent. Python binding `0.1.1` targets
native runtime `0.4.5` and requires C ABI `2`. The package exports
`MORPHEUS_PYTHON_VERSION`, `MORPHEUS_NATIVE_VERSION`, and
`MORPHEUS_NATIVE_ABI_VERSION`; `__version__` is the conventional alias for the
Python package version.

### Acquire stem data

For analysis from a source checkout, use its recursively initialized
`stemlib/` directory. It contains the Perseids dataset for Ancient Greek and
Latin. The Alpheios dataset is a Greek-only alternative under
`vendor/alpheios-morpheus/dist/stemlib`.

Experimental generation requires a prepared Alpheios directory containing a
validated `gener.index`:

```sh
sh tools/prepare-runtime-data.sh "$PWD/morpheus-greek-data"
```

The output directory must not already exist. Pass its absolute path to
`Library.context()`. See the complete
[runtime-data guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/runtime-data.md)
for pinned sources, validation, and redistribution boundaries.

### Acquire the native library

Version `0.1.1` does not download native code during `pip install` and provides
no Python acquisition command. Install the compatible `v0.4.5` native archive
from the [GitHub releases page](https://github.com/defense-humanites/libmorpheus/releases),
or build the runtime from a matching source checkout as shown above. Pass the
actual `.so` or `.dylib` path to `Library`; the binding does not search system
paths or environment variables implicitly.

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
supported by native runtime `0.4.5`.

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
