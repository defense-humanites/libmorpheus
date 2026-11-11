<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# libmorpheus for Node.js

`libmorpheus` modernizes the [Morpheus](https://github.com/PerseusDL/morpheus)
morphological analyzer for Ancient Greek and Latin. It turns the historical C
programs into an installable C17 shared library with a stable, opaque ABI and a
typed Node.js binding.

This package loads the
[`libmorpheus`](https://github.com/defense-humanites/libmorpheus) shared library
through a small Node-API addon. It exposes normalized Greek and Latin analysis
plus experimental Greek lemma generation. Native results are copied into owned
JavaScript objects before their C allocations are released.

## Summary

1. [Quick start (using the npm package)](#quick-start-using-the-npm-package)
2. [In-depth overview](#in-depth-overview)
   1. [Analyze a form](#analyze-a-form)
   2. [Generate forms from a lemma](#generate-forms-from-a-lemma)
   3. [Use parallel contexts](#use-parallel-contexts)
   4. [Raw access and cleanup](#raw-access-and-cleanup)
3. [Other installation options](#other-installation-options)
   1. [Acquire components separately](#acquire-components-separately)
   2. [Build the Node-API addon](#build-the-node-api-addon)
4. [Native library and runtime data](#native-library-and-runtime-data)
   1. [Acquire stem data](#acquire-stem-data)
   2. [Acquire the native library](#acquire-the-native-library)
   3. [Language and data coverage](#language-and-data-coverage)
5. [Supported environments](#supported-environments)
6. [Documentation](#documentation)
7. [Local checks](#local-checks)
8. [License](#license)

## Quick start (using the npm package)

The simplest installation needs Node.js 20 or later and no C toolchain. The
prebuilt Node-API addons and native archives currently support Linux x86-64
glibc, Linux aarch64 glibc, and macOS arm64. Install the binding:

```sh
npm install @libmorpheus/node
```

Package installation runs no scripts. Acquire the matching native library and
the Perseids dataset for Greek and Latin analysis with the explicit setup
command:

```sh
npx libmorpheus-setup --dataset perseids
```

The output directories must not already exist and must not overlap; the command
refuses to overwrite an installation or dataset. It creates
`./morpheus-native` and `./morpheus-data` by default.

Create `app.js`:

```js
import {
  MorpheusLanguage,
  MorpheusLibrary,
  MorpheusOption,
} from "@libmorpheus/node";
import { nativeLibraryPath } from "@libmorpheus/node/native";
import { resolve } from "node:path";

const library = new MorpheusLibrary(
  nativeLibraryPath("./morpheus-native"),
);
const context = library.createContext(
  resolve("./morpheus-data"),
  MorpheusLanguage.Greek,
);

try {
  const analyses = await context.analyze(
    "a)/nqrwpos",
    MorpheusOption.StrictCase,
  );
  for (const analysis of analyses) {
    console.log(analysis.lemma, analysis.partOfSpeech);
  }
} finally {
  await context.close();
  library.close();
}
```

Run it normally:

```sh
node app.js
```

The binding itself performs no network access and needs no environment
variables at runtime. Applications may instead pass paths from their own
configuration, including `MORPHEUS_LIBRARY` and `MORPHEUS_STEMLIB`.

For Greek analysis and experimental generation, choose the Alpheios dataset and
build its validated index during setup:

```sh
npx libmorpheus-setup --dataset alpheios --with-gener
```

## In-depth overview

### Analyze a form

```js
import {
  MorpheusError,
  MorpheusLanguage,
  MorpheusLibrary,
  MorpheusOption,
} from "@libmorpheus/node";

const library = new MorpheusLibrary("/usr/local/lib/libmorpheus.so");
const context = library.createContext(
  "/path/to/stemlib",
  MorpheusLanguage.Greek,
);

try {
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
} finally {
  await context.close();
  library.close();
}
```

`analyze()` returns stable English identifiers, arrays for combinable masks, and
`null` for inapplicable scalar values. It preserves all analyses. A generic
stemlib `indecl` class remains `"unknown"` because it does not identify a
lexical category. An empty dialect array means no recorded restriction.

The arrays are frozen and shared between the records that carry the same
values, as their `readonly` types declare: a paradigm of thousands of forms
holds only a few dozen distinct arrays. Copy one (`[...analysis.genders]`)
before changing it.

Options are `bigint` bit flags and may be combined with `|`. For example,
strict case plus accent-insensitive fallback is:

```js
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

Generation is the inverse of analysis: it returns the forms the analyzer
accepts for a lemma, dialectal and late variants and unattested regular
forms included, not a reference paradigm. See
[Greek lemma generation](https://github.com/defense-humanites/libmorpheus/blob/main/docs/public-api.md#greek-lemma-generation)
for its uses and limits.

```js
import {
  MorpheusDialect,
  MorpheusError,
  MorpheusLanguage,
  MorpheusLibrary,
  MorpheusNumber,
  MorpheusStatus,
} from "@libmorpheus/node";

const library = new MorpheusLibrary("/usr/local/lib/libmorpheus.so");
const context = library.createContext(
  "/path/to/stemlib",
  MorpheusLanguage.Greek,
);

try {
  const duals = await context.generate("lo/gos", {
    number: MorpheusNumber.Dual,
    dialect: MorpheusDialect.Attic,
    resultLimit: 256,
  });
  for (const form of duals) {
    console.log(form.surface, form.grammaticalCases);
  }
} catch (error) {
  if (
    error instanceof MorpheusError &&
    error.status === MorpheusStatus.ResultLimitExceeded
  ) {
    console.error("Increase the explicit result limit for this paradigm");
  } else {
    throw error;
  }
} finally {
  await context.close();
  library.close();
}
```

`generate()` is nonblocking and accepts typed filters for part of speech,
dialect, region, person, number, gender, case, tense, mood, voice, and degree.
It preserves dialect masks, duals, duplicate surfaces, and multiple indexed
interpretations unless filters remove them. `excludeDuals` is available when
dual forms are unwanted. The default native limit is 4,096 and the explicit
hard maximum is 65,536.

A lemma's source record that the engine cannot generate (for example, one
whose stem class has no ending table) is skipped rather than failing the
request. The returned array carries the count as a read-only, non-enumerable
`skippedRecords` property: zero when every record was generated, and nonzero
with an empty array when every record of a known lemma failed.

### Use parallel contexts

One context deliberately queues analysis and generation calls because the
native context is stateful. Create separate contexts to perform independent
work concurrently on Node's asynchronous worker pool:

```js
const library = new MorpheusLibrary("/usr/local/lib/libmorpheus.so");
const first = library.createContext(stemlib, MorpheusLanguage.Greek);
const second = library.createContext(stemlib, MorpheusLanguage.Greek);

try {
  const [analyses, forms] = await Promise.all([
    first.analyze("a)/nqrwpos"),
    second.generate("lo/gos"),
  ]);
} finally {
  await Promise.all([first.close(), second.close()]);
  library.close();
}
```

The actual speedup depends on the workload and machine. Reuse warm contexts;
the generation index is loaded lazily once per context.

### Raw access and cleanup

Use `analyzeRaw()` and `generateRaw()` for ABI inspection and low-level tools.
They return numeric normalized traits, `structSize`, the complete 11-byte public
morphology vector, and a numeric truncation mask. The semantic methods return
named morphology flags and truncated fields.

The addon hands the records of one operation to JavaScript as a single
packed buffer in the C ABI's layout, decoded by the facade; the generated
forms of a large paradigm therefore cost one copy per operation rather than
one Node-API call per field. The facade checks the addon's `recordEncoding`
at load and refuses an addon built from an older source tree.

Close contexts before their parent library. `context.close()` waits for queued
work and is idempotent. `library.close()` is synchronous and rejects while any
child context remains open. A `try`/`finally` block provides deterministic
cleanup, including when an operation rejects.

## Other installation options

### Acquire components separately

The combined setup command is a convenience wrapper. The same verified native
runtime and datasets can be acquired independently:

```sh
npx libmorpheus-native --output ./morpheus-native
npx libmorpheus-data \
  --dataset perseids \
  --output ./morpheus-data
```

Applications that provision their own compatible runtime or stemlib do not need
to run either command. The npm package contains neither component and has no
post-install hook.

### Build the Node-API addon

Configure a source checkout with a Node.js installation that provides
`node_api.h`:

```sh
cmake -S . -B build/node -G Ninja \
  -DMORPHEUS_BUILD_NODE_BINDING=ON
cmake --build build/node --target libmorpheus_node
```

If CMake cannot infer the header location, set
`MORPHEUS_NODE_INCLUDE_DIR=/path/to/node/include/node`. Point the JavaScript
facade at the result during development:

```sh
export MORPHEUS_NODE_ADDON="$PWD/build/node/node/libmorpheus_node.node"
```

`MORPHEUS_NODE_ADDON` must be an absolute path; it is a development override,
and published applications should normally use the optional platform package
selected by npm. The addon and the facade are matched: an addon from another
source tree is refused at load when its result encoding differs.

## Native library and runtime data

The binding needs a Node-API addon, a native `libmorpheus` library, and a
compatible stemlib. The npm installation supplies only the first component.

| Component | Included by `npm install` | What to do |
| --- | :---: | --- |
| JavaScript facade and types | Yes | Import `@libmorpheus/node`. |
| Platform Node-API addon | Yes, as an optional dependency | Do not omit optional dependencies. |
| Native `libmorpheus` runtime | No | Run `libmorpheus-setup` or `libmorpheus-native`. |
| Linguistic stem data | No | Run `libmorpheus-setup` or `libmorpheus-data`. |

Binding and runtime versions are independent. Binding `0.2.0` currently
acquires native runtime `0.4.6` and requires C ABI `2`. The main module exports
`MORPHEUS_NODE_VERSION`; the `/native` module exports
`MORPHEUS_NATIVE_VERSION` and `MORPHEUS_NATIVE_ABI_VERSION` for tooling.

### Acquire stem data

Acquisition is provided by the binding's dependency
[`@libmorpheus/data`](https://github.com/defense-humanites/libmorpheus/tree/main/bindings/js/data),
which npm installs with it; `libmorpheus-data` and the `/data` export are the
same command and library, so deployments without a native binding (the
WebAssembly binding, browsers, Workers) can use that package directly. Its
`--subset runtime`, `--languages` and `--manifest` options are available
from this binding's command as well.

For Greek and Latin analysis, acquire the Perseids dataset:

```sh
npx libmorpheus-data \
  --dataset perseids \
  --output ./morpheus-data
```

Choose `--dataset alpheios` instead for the Greek-only reference dataset. Add
`--with-gener` to build its experimental Greek generation index:

```sh
npx libmorpheus-data \
  --dataset alpheios \
  --with-gener \
  --output ./morpheus-greek-data
```

The command verifies pinned sources, the complete selected file tree, the
upstream license, and—when requested—the generated index. It refuses to
overwrite an existing directory and writes a provenance receipt. See the
complete [runtime-data guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/runtime-data.md).

### Acquire the native library

Install the matching native release without Git or a C toolchain:

```sh
npx libmorpheus-native --output ./morpheus-native
```

The command selects the declared native release for the current platform,
verifies its SHA-256 digest, safely extracts it into a new directory, and writes
`MORPHEUS-NATIVE.json`. Use the exported helper to avoid platform-specific
filenames:

```js
import { MorpheusLibrary } from "@libmorpheus/node";
import { nativeLibraryPath } from "@libmorpheus/node/native";

const library = new MorpheusLibrary(
  nativeLibraryPath("./morpheus-native"),
);
```

### Language and data coverage

The operation and selected dataset together determine language coverage:

| Operation or dataset | Ancient Greek | Latin | Additional requirement |
| --- | :---: | :---: | --- |
| `analyze()` | Yes | Yes | A stemlib for the selected language. |
| `generate()` | Yes | No | Alpheios data prepared with `gener.index`. |
| Perseids | Yes | Yes | No |
| Alpheios | Yes | No | Pass `--with-gener` for generation. |

See the [stem-library inventory](https://github.com/defense-humanites/libmorpheus/blob/main/docs/stem-libraries.md)
for dataset origins and repository locations.

## Supported environments

The package requires Node.js 20 or later and uses ESM. Prebuilt addon and native
runtime acquisition currently support:

| Operating system | Architecture | C library |
| --- | --- | --- |
| Linux | x86-64 | glibc |
| Linux | aarch64 | glibc |
| macOS | arm64 | system |

On Linux, musl environments are rejected rather than loading an incompatible
binary. npm optional dependencies must remain enabled. There is no Windows or
macOS x86-64 prebuilt package in version `0.2.0`.

## Documentation

The npm package exposes the main binding and independently importable
`@libmorpheus/node/setup`, `@libmorpheus/node/data`, and
`@libmorpheus/node/native` entrypoints. Their TypeScript declarations ship with
the package.

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

Build the library, Node-API addon, and small differential generation index
before running the binding tests:

```sh
cmake --preset dev -DMORPHEUS_BUILD_NODE_BINDING=ON
cmake --build --preset dev --target \
  morpheus libmorpheus_node morpheus_gener_index_builder
build/dev/morpheus_gener_index_builder \
  stemlib/gener.index test/generation-service-source.txt
MORPHEUS_NODE_ADDON="$PWD/build/dev/node/libmorpheus_node.node" \
MORPHEUS_LIBRARY="$PWD/build/dev/libmorpheus.so" \
MORPHEUS_STEMLIB="$PWD/stemlib" \
npm --prefix bindings/js/node test
```

## License

The Node.js binding, Node-API adapter, and acquisition tooling are licensed
under [AGPL-3.0-or-later](LICENSE). The package contains neither the native
runtime nor linguistic stem data.

Dataset acquisition comes from the dependency `@libmorpheus/data`, whose
internal data preparer is built from MPL-2.0-covered Morpheus code and the
MIT-licensed Emscripten runtime; that package carries those texts and its own
notice. They do not change the license of the binding itself. See the
[package notice](NOTICE) and the project's
[licensing guide](https://github.com/defense-humanites/libmorpheus/blob/main/docs/licensing.md)
for the precise file-level boundary.
