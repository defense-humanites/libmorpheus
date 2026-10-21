<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# @libmorpheus/wasm

WebAssembly build of the libmorpheus morphological analyzer, with a small
JavaScript facade. The same module runs in browsers, web workers, Node.js,
Deno and Bun, so a client-side application can analyze Ancient Greek and Latin
forms without a native toolchain or a server.

The package contains **no linguistic data**. Applications provide a compiled
stem library at runtime, exactly as the native library does. See
[Acquiring runtime data](https://github.com/defense-humanites/libmorpheus/blob/main/docs/runtime-data.md).

## Status

Experimental. The module exposes the complete stable C ABI (version 2) and the
historical `cruncher` text output. The facade returns the numeric codes of the
C structures (`MorpheusRawAnalysis`, `MorpheusRawGeneration`) rather than the
named decoding offered by the Deno and Node.js bindings. The module is
single-threaded; use one instance per worker for parallel work.

## Installing

The package is published as `@libmorpheus/wasm` on npm and on JSR from the
same sources, with the compiled module included:

```sh
npm install @libmorpheus/wasm        # Node.js, Bun, bundlers
deno add jsr:@libmorpheus/wasm       # Deno
```

```js
import { createMorpheus, MorpheusLanguage } from "@libmorpheus/wasm";
```

Each release declares the libmorpheus runtime and C ABI compiled into its
module and the Emscripten release that reproduces it
(`MORPHEUS_NATIVE_VERSION`, `MORPHEUS_NATIVE_ABI_VERSION`,
`MORPHEUS_EMSCRIPTEN_VERSION`, exported next to `MORPHEUS_WASM_VERSION`). The
same `morpheus.mjs` and `morpheus.wasm`, with their SHA-256 digests, are
attached to the `wasm-v<version>` GitHub release for deployments that serve
the files themselves.

When the package is served from a registry rather than installed on disk (JSR
under Deno, say), `createMorpheus()` fetches and compiles `morpheus.wasm`
next to the loader itself; nothing changes for the caller. JSR also rewrites
the module's import names into relative specifiers on publish, which the
facade maps back onto the loader's imports. **Version 0.1.0 predates that
mapping and fails to instantiate from JSR**; use 0.1.1 or later from either
registry, or 0.1.0 from npm.

## Building the module

The facade imports `./dist/morpheus.mjs` by default. Build it from the
repository root with Emscripten 4.0.15 (the version the project pins):

```sh
emcmake cmake -S . -B build/wasm -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build build/wasm --target morpheus_wasm
mkdir -p bindings/js/wasm/dist
cp build/wasm/wasm/morpheus.mjs build/wasm/wasm/morpheus.wasm bindings/js/wasm/dist/
```

`morpheus.wasm` is about 150 KiB; `morpheus.mjs` is the Emscripten loader.
Configuring with `-DBUILD_TESTING=ON` additionally compiles the native C test
suite to WebAssembly so that `ctest` runs it under Node.js against the same
object code; see [docs/wasm.md](https://github.com/defense-humanites/libmorpheus/blob/main/docs/wasm.md).

## What the application sets up

The package is deliberately small: a loader, a module and a facade. Four
things are the application's responsibility, whichever runtime it targets.

1. **The two module files.** `morpheus.mjs` and `morpheus.wasm` travel
   together; the loader resolves the `.wasm` next to the `.mjs`. Where the
   runtime cannot resolve that (no `import.meta.url`, no `fetch` of relative
   URLs, or a platform that forbids compiling WebAssembly from bytes), import
   the `.wasm` through the platform's own mechanism and pass it as
   `wasmModule`; the loader then neither fetches nor compiles anything.
2. **The stemlib.** Nothing is bundled. Acquire a dataset as described in
   [Acquiring runtime data](https://github.com/defense-humanites/libmorpheus/blob/main/docs/runtime-data.md), check the
   [redistribution policy](https://github.com/defense-humanites/libmorpheus/blob/main/docs/stemlib-redistribution.md) for what
   you ship, and give the module the **whole runtime subset** of each language
   you serve (see [Which files](#which-files)).
3. **Data placement.** On a server, write the files into the module's memory
   (`writeStemlib()`) rather than mounting a host directory
   (`mountDirectory()`): a mounted directory turns every historical
   `open`/`seek`/`read`/`close` into a system call reached through
   JavaScript, which the [benchmark](https://github.com/defense-humanites/libmorpheus/blob/main/docs/wasm.md#performance-against-the-native-ffi-path)
   shows is the slow placement. Mounting is for development and tests.
4. **Instance lifetime and concurrency.** One instance costs tens of
   milliseconds to create and holds its own copy of the data, so create it
   once and keep it. A context is cheap, synchronous and single-threaded:
   open one per language at start-up and reuse it for every request; since
   `analyze()` and `generate()` never yield, concurrent requests in one event
   loop cannot interleave inside a call. For more than one core, run one
   instance per worker thread and share the compiled `WebAssembly.Module`
   between them through `postMessage`, passing it as `wasmModule`; memories
   stay separate, which is the same model as the native bindings
   (contexts are thread-affine).

### Which files

`Morpheus.requiredFiles(language)` lists the files that `open()` validates.
Beyond those, analysis reads lazily `endtables/out/*.out` (by stem class),
`derivs/indices/derivind`, `stemsrc/vbs.cmp.ml` (compound verbs) and
`stemsrc/lemlist` (dictionary entries); Greek generation reads `gener.index`
at the stemlib root. A missing lazy file surfaces as `InternalError` on the
forms that need it, so ship the whole set under `<root>/<Language>/`:

```text
rule_files/*
steminds/nomind  steminds/nomind.lindex  steminds/vbind  steminds/vbind.lindex
endtables/indices/*  endtables/out/*
derivs/indices/derivind
stemsrc/vbs.cmp.ml  stemsrc/lemlist        (when the dataset has them)
```

plus `<root>/gener.index` for Greek generation. In the Perseids stemlib that is
about 3 MiB for Latin and 8 MiB for Greek; the qualified Greek generation index
adds 11 MiB. Publish a manifest of those paths next to the data; the facade
takes any iterable of `[path, bytes]`.

## Node.js, Deno and Bun

A long-lived server keeps one instance (or one per worker thread) with the
data in memory and one context per language. The example reads a stemlib
tree placed next to the script (`./stemlib/Greek`, `./stemlib/Latin`):

```js
import { readFile, readdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join, relative } from "node:path";
import { createMorpheus, MorpheusLanguage } from "@libmorpheus/wasm";

async function loadStemlib(directory) {
  const entries = [];
  for (const entry of await readdir(directory, { recursive: true, withFileTypes: true })) {
    if (!entry.isFile()) continue;
    const path = join(entry.parentPath, entry.name);
    entries.push([relative(directory, path), await readFile(path)]);
  }
  return entries; // filter to the runtime subset above if the tree is larger
}

const stemlib = fileURLToPath(new URL("./stemlib", import.meta.url));
const morpheus = await createMorpheus();           // ./dist/morpheus.mjs
const root = morpheus.writeStemlib(await loadStemlib(stemlib));
const contexts = {
  greek: morpheus.open({ stemlib: root, language: MorpheusLanguage.Greek }),
  latin: morpheus.open({ stemlib: root, language: MorpheusLanguage.Latin }),
};

export function analyze(language, betaCode) {
  return contexts[language].analyze(betaCode);     // synchronous
}

console.log(analyze("greek", "e)/kstasis"));
```

Run as is, the script prints one analysis, a noun (`partOfSpeech: 1`) in the
feminine (`gender: 2`) singular (`number: 1`) nominative (`grammaticalCase:
16`), with the numeric codes of `include/morpheus/morpheus.h`:

```js
[
  {
    structSize: 852,
    partOfSpeech: 1,
    dialect: 0,
    geographicRegion: 0,
    person: 0,
    number: 1,
    gender: 2,
    grammaticalCase: 16,
    tense: 0,
    mood: 0,
    voice: 0,
    degree: 0,
    raw: "e)/kstasis",
    workword: "e)/kstasis",
    lemma: "e)/kstasis",
    preverb: "",
    augment: "",
    stem: "e)kstas",
    suffix: "",
    ending: "is",
    crasis: "",
    dictionaryForm: "",
    englishForm: "",
    rawPreverb: "",
    domains: "",
    morphFlags: Uint8Array(11) [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    truncatedFields: 0
  }
]
```

Beta Code in, Beta Code out: the analyzer expects the historical transliteration
(`lo/gos`, `e)/dwken`). For a quick script or a test, `mountDirectory()` reads
the host tree directly instead of copying it.

For several cores, compile once in the main thread and hand the module to each
worker:

```js
// main thread
const wasmModule = await WebAssembly.compile(await readFile("dist/morpheus.wasm"));
worker.postMessage({ wasmModule, entries });       // structured clone
// worker
const morpheus = await createMorpheus({ wasmModule });
```

## Browsers

Serve `morpheus.mjs`, `morpheus.wasm` (with the `application/wasm` media type,
so the browser can compile it while it streams) and the stemlib files as static
assets, then fetch the manifest into the module's memory:

```js
import { createMorpheus, MorpheusLanguage } from "@libmorpheus/wasm";

const morpheus = await createMorpheus({
  moduleUrl: new URL("./morpheus.mjs", import.meta.url),
});
const manifest = await (await fetch("./stemlib/latin-manifest.json")).json();
const root = await morpheus.fetchStemlib("./stemlib/", manifest);
const latin = morpheus.open({ stemlib: root, language: MorpheusLanguage.Latin });
```

Run this in a Web Worker so that analysis never blocks the page, keep the
instance for the life of the page, and let the browser cache the data (long
`Cache-Control` on immutable, versioned paths, or the Cache API). No
cross-origin isolation headers are needed: the module uses no threads and no
shared memory.

## Cloudflare Workers

Workers forbid compiling WebAssembly from bytes at run time and expose no
`import.meta.url`, so the two platform mechanisms replace the loader's own
discovery: the `.wasm` is imported as a module and passed as `wasmModule`, and
the factory is imported statically. The stemlib files are bundled as Data
modules so the Worker needs no network access to start. This configuration
was exercised with `wrangler dev` (the local `workerd` runtime); it has not yet
been run on the hosted platform.

```toml
# wrangler.toml
name = "morpheus"
main = "src/worker.mjs"
compatibility_date = "2026-10-01"

[[rules]]
type = "Data"
globs = [
  "**/*.table", "**/nomind", "**/nomind.lindex", "**/vbind", "**/vbind.lindex",
  "**/nendind", "**/vbendind", "**/*.out", "**/derivind",
  "**/vbs.cmp.ml", "**/lemlist", "**/gener.index",
]
fallthrough = true
```

```js
// src/worker.mjs
import createMorpheusModule from "@libmorpheus/wasm/module";  // dist/morpheus.mjs
import wasmModule from "@libmorpheus/wasm/morpheus.wasm";     // WebAssembly.Module
import { createMorpheus, MorpheusLanguage } from "@libmorpheus/wasm";
import { stemlibEntries } from "./stemlib-manifest.mjs";      // [[path, ArrayBuffer], ...]

let ready;
function init() {
  ready ??= (async () => {
    const morpheus = await createMorpheus({ factory: createMorpheusModule, wasmModule });
    const root = morpheus.writeStemlib(stemlibEntries.map(([path, data]) => [path, new Uint8Array(data)]));
    return {
      greek: morpheus.open({ stemlib: root, language: MorpheusLanguage.Greek }),
      latin: morpheus.open({ stemlib: root, language: MorpheusLanguage.Latin }),
    };
  })();
  return ready;
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const contexts = await init();
    const context = url.pathname.startsWith("/latin/") ? contexts.latin : contexts.greek;
    return Response.json(context.analyze(url.searchParams.get("w") ?? ""));
  },
};
```

`stemlib-manifest.mjs` is a generated file with one `import` per data file and
the `[path, buffer]` array; generate it from the directory listing of the
language trees you ship. Points that matter on this platform:

- **Initialize once per isolate.** The memoized `init()` above runs on the
  first request and is reused by every later request in that isolate.
  Instantiating at module top level is also allowed, but global-scope
  execution is capped at one second and cannot perform I/O, so the memoized
  form is the safer default and keeps a slow start from failing the deploy.
  Locally, creating the instance, writing the Latin subset and opening its
  context took about 30 ms.
- **Size.** Workers count the uncompressed bundle, with a 64 MiB limit and no
  compressed limit. The Latin subset bundles to about 2.9 MiB in total
  (measured with `wrangler deploy --dry-run`); Latin plus Greek plus the Greek
  generation index stays around 22 MiB. Data modules keep the data versioned
  with the code; for larger datasets, R2 or Static Assets fetched at `init()`
  are the alternative, at the price of network time on the first request.
- **Memory.** An isolate has 128 MB for the JavaScript heap and WebAssembly
  memory together. One instance with both languages holds about 11 MiB of
  data plus the analyzer's working memory; keep a single instance per isolate
  and do not create per-request contexts.
- **CPU time.** A warm analysis is on the order of a millisecond; the first
  request also pays initialization. On the Free plan the limit is 10 ms per
  request, which the first request exceeds; the Paid plan defaults to 30 s.
  Measure with Workers observability rather than `performance.now()`, whose
  clock does not advance during a request's CPU work on this platform.
- **No Node compatibility is required.** The module only uses `fetch` or
  `node:fs` to locate `morpheus.wasm`, which `wasmModule` makes unnecessary.
  The stamped `morpheus.mjs` ignores a Node-like `process` object when
  `import.meta.url` is absent, so the `nodejs_compat` flag neither helps nor
  hurts it.

Limits quoted here are from Cloudflare's documentation at the time of writing
(see the [platform limits](https://developers.cloudflare.com/workers/platform/limits/)
and [WebAssembly in Workers](https://developers.cloudflare.com/workers/platform/webassembly/javascript))
and change over time; check them before sizing a deployment.

## Testing

```sh
MORPHEUS_WASM_MODULE=build/wasm/wasm/morpheus.mjs MORPHEUS_STEMLIB=stemlib \
  node --test bindings/js/wasm/test/*.test.js
```

Set `MORPHEUS_GENER_STEMLIB` to a prepared Greek directory holding
`gener.index` to exercise generation.

## Licensing

The facade is AGPL-3.0-or-later. The built module combines the
AGPL-3.0-or-later and MPL-2.0 runtime sources with the MIT-licensed Emscripten
support code; the corresponding texts are under `LICENSES/`. See the
repository's [licensing](https://github.com/defense-humanites/libmorpheus/blob/main/docs/licensing.md) and
[provenance](https://github.com/defense-humanites/libmorpheus/blob/main/docs/provenance.md) documents before redistributing a
stemlib with an application.
