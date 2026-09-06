<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# libmorpheus for Deno

`libmorpheus` modernizes the [Morpheus](https://github.com/PerseusDL/morpheus)
morphological analyzer for Ancient Greek and Latin. It turns the historical C
programs into an installable C17 shared library with a stable, opaque ABI and a
typed Deno 2 binding.

This module loads the
[`libmorpheus`](https://github.com/defense-humanites/libmorpheus) shared library
with `Deno.dlopen`. It exposes normalized Greek and Latin analysis plus
experimental Greek lemma generation. Native results are copied into owned
TypeScript objects before their C allocations are released.

## Summary

1. [Quick start (using the JSR package)](#quick-start-using-the-jsr-package)
2. [In-depth overview](#in-depth-overview)
   1. [Analyze a form](#analyze-a-form)
   2. [Generate forms from a lemma](#generate-forms-from-a-lemma)
   3. [Use parallel contexts](#use-parallel-contexts)
   4. [Raw access and cleanup](#raw-access-and-cleanup)
3. [Other installation options](#other-installation-options)
   1. [Standalone release archive](#standalone-release-archive)
   2. [Docker image](#docker-image)
4. [Native library and runtime data](#native-library-and-runtime-data)
   1. [Acquire stem data](#acquire-stem-data)
   2. [Acquire the native library](#acquire-the-native-library)
   3. [Language and data coverage](#language-and-data-coverage)
5. [FFI permission](#ffi-permission)
6. [Documentation](#documentation)
7. [Local checks](#local-checks)
8. [License](#license)

## Quick start (using the JSR package)

The simplest installation needs no C toolchain. The prebuilt native
archives currently support Linux x86-64 glibc, Linux aarch64 glibc, and macOS
arm64. Install the binding:

```sh
deno add jsr:@libmorpheus/deno
```

Then acquire the matching native library and the Perseids dataset for Greek and
Latin analysis:

```sh
deno x \
  --allow-net=github.com,release-assets.githubusercontent.com,codeload.github.com \
  --allow-read=./morpheus-native,./morpheus-data \
  --allow-write=./morpheus-native,./morpheus-data \
  jsr:@libmorpheus/deno/setup \
  --dataset perseids
```

The output directories must not already exist; the command refuses to overwrite
an installation or dataset.

Create `app.ts`:

```ts
import {
  MorpheusLanguage,
  MorpheusLibrary,
  MorpheusOption,
} from "@libmorpheus/deno";
import { nativeLibraryPath } from "@libmorpheus/deno/native";

using library = new MorpheusLibrary(nativeLibraryPath("./morpheus-native"));

await using context = library.createContext(
  await Deno.realPath("./morpheus-data"),
  MorpheusLanguage.Greek
);

const analyses = await context.analyze(
  "a)/nqrwpos",
  MorpheusOption.StrictCase
);

for (const analysis of analyses) {
  console.log(analysis.lemma, analysis.partOfSpeech);
}
```

Run it with the permissions used by the application:

```sh
deno run --allow-ffi --allow-read=./morpheus-data app.ts
```

The FFI permission must currently remain unscoped because Deno rejects native
pointer reads under a path-scoped `--allow-ffi` grant. The binding itself does
not require network, environment, or write access at runtime.

For Greek analysis and experimental generation, choose the Alpheios dataset and
build its validated index during setup:

```sh
deno x \
  --allow-net=github.com,release-assets.githubusercontent.com,codeload.github.com \
  --allow-read=./morpheus-native,./morpheus-data \
  --allow-write=./morpheus-native,./morpheus-data \
  jsr:@libmorpheus/deno/setup \
  --dataset alpheios \
  --with-gener
```

## In-depth overview

### Analyze a form

```ts
import {
  MorpheusError,
  MorpheusLanguage,
  MorpheusLibrary,
  MorpheusOption,
} from "@libmorpheus/deno";

try {
  using library = new MorpheusLibrary("/usr/local/lib/libmorpheus.so");
  await using context = library.createContext(
    "/path/to/stemlib",
    MorpheusLanguage.Greek,
  );

  const analyses = await context.analyze(
    "a)/nqrwpos",
    MorpheusOption.StrictCase,
  );
  console.log(analyses[0].partOfSpeech); // "noun"
  console.log(analyses[0].grammaticalNumber); // "singular"
  console.log(analyses[0].grammaticalCases); // ["nominative"]
} catch (error) {
  if (error instanceof MorpheusError) {
    console.error(`Morpheus status ${error.status}: ${error.message}`);
  } else {
    throw error;
  }
}
```

`analyze()` returns stable English identifiers, arrays for combinable masks, and
`null` for inapplicable scalar values. It preserves all analyses. A generic
stemlib `indecl` class remains `"unknown"` because it does not identify a
lexical category. An empty dialect array means no recorded restriction.

Options are bit flags and may be combined with `|`. For example, strict case
plus accent-insensitive fallback is:

```ts
const options = MorpheusOption.StrictCase |
  MorpheusOption.IgnoreAccents;
const analyses = await context.analyze("a)/nqrwpos", options);
```

Passing no option uses the binding's default analysis behavior. See the
[native option table](https://github.com/defense-humanites/libmorpheus/blob/main/docs/public-api.md#request-options)
before enabling specialized modes.

`MorpheusOption.HqDictionary` requires both HQ index files. If they are absent,
the promise rejects with `MorpheusStatus.StemlibError` before native analysis.

### Generate forms from a lemma

> [!WARNING]
> `generate()` and `generateRaw()` are experimental. Their automated
> differential, isolation, failure, portability, and sanitizer coverage is
> extensive, but sufficient real-world use is still required before this
> qualification can be removed.

```ts
import {
  MorpheusDialect,
  MorpheusError,
  MorpheusLanguage,
  MorpheusLibrary,
  MorpheusNumber,
  MorpheusStatus,
} from "@libmorpheus/deno";

try {
  using library = new MorpheusLibrary("/usr/local/lib/libmorpheus.so");
  await using context = library.createContext(
    "/path/to/stemlib",
    MorpheusLanguage.Greek,
  );

  const duals = await context.generate("lo/gos", {
    number: MorpheusNumber.Dual,
    dialect: MorpheusDialect.Attic,
    resultLimit: 256,
  });
  for (const form of duals) console.log(form.surface, form.grammaticalCases);
} catch (error) {
  if (
    error instanceof MorpheusError &&
    error.status === MorpheusStatus.ResultLimitExceeded
  ) {
    console.error("Increase the explicit result limit for this paradigm");
  } else {
    throw error;
  }
}
```

`generate()` is nonblocking and accepts typed filters for part of speech,
dialect, region, person, number, gender, case, tense, mood, voice, and degree.
It preserves dialect masks, duals, duplicate surfaces, and multiple indexed
interpretations unless filters remove them. `excludeDuals` is available when
dual forms are unwanted. The default native limit is 4,096 and the explicit hard
maximum is 65,536.

### Use parallel contexts

One context deliberately queues analysis and generation calls because the native
context is stateful. Create separate contexts to perform independent work in
parallel:

```ts
using library = new MorpheusLibrary("/usr/local/lib/libmorpheus.so");
await using first = library.createContext(stemlib, MorpheusLanguage.Greek);
await using second = library.createContext(stemlib, MorpheusLanguage.Greek);

const [analyses, forms] = await Promise.all([
  first.analyze("a)/nqrwpos"),
  second.generate("lo/gos"),
]);
```

The actual speedup depends on the workload and machine. Reuse warm contexts; the
generation index is loaded lazily once per context.

### Raw access and cleanup

Use `analyzeRaw()` and `generateRaw()` for ABI inspection and low-level tools.
They return numeric normalized traits, `structSize`, the complete 11-byte public
morphology vector, and a numeric truncation mask. The semantic methods return
named morphology flags and truncated fields.

Close contexts before their parent library. `using` and `await using` provide
deterministic cleanup, including when a promise rejects. `MorpheusLibrary.close`
rejects while any child context remains open.

## Other installation options

### Standalone release archive

Starting with the next publication after `0.3.2`, Deno binding releases use
`deno-v<version>` tags and provide `libmorpheus-deno-<version>.tar.gz` plus a
companion SHA-256 file on the
[GitHub releases page](https://github.com/defense-humanites/libmorpheus/releases).
The `0.3.2` archive remains attached to the historical combined `v0.3.2`
release. Extract the binding beside a compatible native archive, import
`mod.ts` from the extracted directory, and pass the installed shared-library
path to `MorpheusLibrary`. The binding archive contains neither native binaries
nor stem data.

### Docker image

The repository's locally built
[`deno-runtime` image target](https://github.com/defense-humanites/libmorpheus/blob/main/Dockerfile)
bundles Deno, the native library, and the pinned Alpheios stemlib prepared with
its validated `gener.index`. It deliberately does not copy this binding into the
image:

```sh
git clone --recurse-submodules \
  https://github.com/defense-humanites/libmorpheus.git
cd libmorpheus
docker build --target deno-runtime -t morpheus-deno .
```

Containerized applications declare `@libmorpheus/deno` as the same normal
JSR dependency used outside Docker:

```sh
deno add jsr:@libmorpheus/deno
```

Application code imports `@libmorpheus/deno` and reads only
`MORPHEUS_LIBRARY` and `MORPHEUS_STEMLIB`, which already contain the container
paths. It does not call `/setup` or depend on how the image provisioned those
paths:

```ts
import {
  MorpheusLanguage,
  MorpheusLibrary,
} from "@libmorpheus/deno";

using library = new MorpheusLibrary(Deno.env.get("MORPHEUS_LIBRARY")!);
await using context = library.createContext(
  Deno.env.get("MORPHEUS_STEMLIB")!,
  MorpheusLanguage.Greek,
);
```

Applications still need Deno's FFI permission. Greek `analyze()` and
experimental `generate()` are both qualified in the image; CI also checks that
generation preserves dual forms. The image is a qualification and
application-build target, not a published registry image.

## Native library and runtime data

The binding needs both a native `libmorpheus` library and a compatible stemlib.
What must be acquired depends on the distribution:

| Distribution | Native library | Stem data | What to do |
| --- | --- | --- | --- |
| JSR package | Not included | Not included | Run `/setup`, or use `/native` and `/data` separately |
| Standalone binding archive | Not included | Not included | Install the matching native release and acquire a stemlib as described below |
| `deno-runtime` Docker image | Included | Alpheios included | Add the binding from JSR; use `MORPHEUS_LIBRARY` and `MORPHEUS_STEMLIB` without running `/setup` |

The following acquisition commands therefore apply to the JSR package and the
standalone binding archive, not to the Docker image.

Binding and runtime versions are independent. Binding `0.4.0` currently
acquires native runtime `0.3.2` and requires C ABI `2`; these compatibility
values are declared in `internal/version.ts`. The main module exports
`MORPHEUS_DENO_VERSION`; the `/native` module exports
`MORPHEUS_NATIVE_VERSION` and `MORPHEUS_NATIVE_ABI_VERSION` for tooling.

### Acquire stem data

For Greek and Latin analysis, acquire the Perseids dataset:

```sh
deno x \
  --allow-net=codeload.github.com \
  --allow-read=./morpheus-data \
  --allow-write=./morpheus-data \
  jsr:@libmorpheus/deno@0.4.0/data \
  --dataset perseids \
  --output ./morpheus-data
```

Choose `--dataset alpheios` instead for the Greek-only reference dataset. Pass
the resulting absolute path to `createContext()`.

Add `--with-gener` to the Alpheios command to build its experimental Greek
generation index:

```sh
deno x \
  --allow-net=codeload.github.com \
  --allow-read=./morpheus-greek-data \
  --allow-write=./morpheus-greek-data \
  jsr:@libmorpheus/deno@0.4.0/data \
  --dataset alpheios \
  --with-gener \
  --output ./morpheus-greek-data
```

The command verifies the pinned sources and generated index, refuses to
overwrite an existing directory, and writes provenance and license receipts.
See the complete [runtime-data guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/runtime-data.md).

When working from a full source checkout instead of JSR, the repository also
provides
[`tools/prepare-runtime-data.sh`](https://github.com/defense-humanites/libmorpheus/blob/main/tools/prepare-runtime-data.sh)
for the native build workflow. The JSR data command above is the intended route
for JavaScript users who do not have a C toolchain.

### Acquire the native library

Install the matching native release without Git or a C toolchain:

```sh
deno x \
  --allow-net=github.com,release-assets.githubusercontent.com \
  --allow-read=./morpheus-native \
  --allow-write=./morpheus-native \
  jsr:@libmorpheus/deno@0.4.0/native \
  --output ./morpheus-native
```

The command selects the declared native release for the current platform,
verifies its SHA-256 digest, refuses to overwrite an existing directory, and
records the binding version, native version, target, and ABI in
`MORPHEUS-NATIVE.json`. Standalone-archive users may instead extract a compatible
native archive from its `v<version>` GitHub release.

Use the exported helper to avoid platform-specific filenames:

```ts
import { MorpheusLibrary } from "@libmorpheus/deno";
import { nativeLibraryPath } from "@libmorpheus/deno/native";

using library = new MorpheusLibrary(
  nativeLibraryPath("./morpheus-native"),
);
```

Running an application that loads the result requires `--allow-ffi` as
described below.

### Language and data coverage

The operation and selected dataset together determine language coverage:

| Operation or dataset | Ancient Greek | Latin | Additional requirement |
| --- | :---: | :---: | --- |
| `analyze()` | Yes | Yes | A stemlib for the selected language |
| `generate()` | Yes | No | Alpheios data prepared with `gener.index` |
| Perseids | Yes | Yes | No |
| Alpheios | Yes | No | With `--with-gener`; already prepared in Docker |

See the [stem-library inventory](https://github.com/defense-humanites/libmorpheus/blob/main/docs/stem-libraries.md)
for dataset origins and repository locations.

## FFI permission

Run applications with Deno's FFI permission:

```sh
deno run --allow-ffi app.ts
```

Use the installed platform name, normally `libmorpheus.so` on Linux and
`libmorpheus.dylib` on macOS. The binding reads returned pointers with
`Deno.UnsafePointerView`; current Deno releases reject those reads under a
path-scoped grant such as `--allow-ffi=/absolute/path/libmorpheus.so`. Keep the
library path explicit in code, but use the unscoped permission shown above. A
`deno.json` task can retain the same command for both `x86_64` and `aarch64`
deployments; only the library path needs to change. Environment and file
permissions are not required by the binding itself.

## Documentation

The generated [JSR API reference](https://jsr.io/@libmorpheus/deno/doc)
documents the main binding and its independently importable
[`/setup`](https://jsr.io/@libmorpheus/deno/doc/setup),
[`/data`](https://jsr.io/@libmorpheus/deno/doc/data), and
[`/native`](https://jsr.io/@libmorpheus/deno/doc/native) entrypoints.

| Topic                              | Document                                                                                            |
| ---------------------------------- | --------------------------------------------------------------------------------------------------- |
| Native ABI, ownership, and options | [Public API](https://github.com/defense-humanites/libmorpheus/blob/main/docs/public-api.md)         |
| AGPL/MPL file boundary             | [Licensing guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/licensing.md)     |
| Source and dataset lineage         | [Provenance](https://github.com/defense-humanites/libmorpheus/blob/main/docs/provenance.md)         |
| Available stem libraries           | [Stem libraries](https://github.com/defense-humanites/libmorpheus/blob/main/docs/stem-libraries.md) |
| Supported platforms                | [Portability](https://github.com/defense-humanites/libmorpheus/blob/main/docs/portability.md)       |
| Release archives and qualification | [Releasing](https://github.com/defense-humanites/libmorpheus/blob/main/docs/releasing.md)           |

## Local checks

Build the library and prepare the small differential generation index before
running the binding tests:

```sh
cmake --preset dev
cmake --build --preset dev
build/dev/morpheus_gener_index_builder \
  stemlib/gener.index test/generation-service-source.txt
deno check bindings/js/deno/mod.ts bindings/js/deno/test/mod_test.ts
MORPHEUS_LIBRARY="$PWD/build/dev/libmorpheus.so" \
MORPHEUS_STEMLIB="$PWD/stemlib" \
deno test --allow-env --allow-ffi \
  bindings/js/deno/test/mod_test.ts
```

## License

The Deno binding itself is licensed under
[AGPL-3.0-or-later](LICENSE). Its TypeScript API and acquisition tooling do not
inherit the MPL-2.0 license of the native Morpheus engine.

The binding archive also contains an internal data preparer built from
MPL-2.0-covered Morpheus code and the MIT-licensed Emscripten runtime. These
components retain their own licenses; they do not change the license of the
binding itself. See the [archive notice](NOTICE) and the project's
[licensing guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/licensing.md)
for the precise file-level boundary.
