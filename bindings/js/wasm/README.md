<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# @libmorpheus/wasm

WebAssembly build of the libmorpheus morphological analyzer, with a small
JavaScript facade. The same module runs in browsers, web workers, Node.js,
Deno and Bun, so a client-side application can analyze Ancient Greek and Latin
forms without a native toolchain or a server.

The package contains **no linguistic data**. Applications provide a compiled
stem library at runtime, exactly as the native library does. See
[Acquiring runtime data](../../../docs/runtime-data.md).

## Status

Experimental. The module exposes the complete stable C ABI (version 2) and the
historical `cruncher` text output. The facade returns the numeric codes of the
C structures (`MorpheusRawAnalysis`, `MorpheusRawGeneration`) rather than the
named decoding offered by the Deno and Node.js bindings. The module is
single-threaded; use one instance per worker for parallel work.

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
object code; see [docs/wasm.md](../../../docs/wasm.md).

## Node.js

```js
import { createMorpheus, MorpheusLanguage } from "@libmorpheus/wasm";

const morpheus = await createMorpheus();
const root = morpheus.mountDirectory("/path/to/stemlib"); // contains Greek/ and Latin/
const latin = morpheus.open({ stemlib: root, language: MorpheusLanguage.Latin });
for (const analysis of latin.analyze("amavimus")) {
  console.log(analysis.lemma, analysis.tense, analysis.person, analysis.number);
}
latin.close();
```

Beta Code in, Beta Code out: the analyzer expects the historical transliteration
(`lo/gos`, `e)/dwken`).

## Browsers

Serve `morpheus.mjs`, `morpheus.wasm` and the stemlib tree as static files,
then load the files the analyzer needs into the module's in-memory file system:

```js
import { createMorpheus, Morpheus, MorpheusLanguage } from "@libmorpheus/wasm";

const morpheus = await createMorpheus({
  moduleUrl: new URL("./morpheus.mjs", import.meta.url),
});
const manifest = await (await fetch("./stemlib/latin-manifest.json")).json();
const root = await morpheus.fetchStemlib("./stemlib/", manifest);
const latin = morpheus.open({ stemlib: root, language: MorpheusLanguage.Latin });
```

`Morpheus.requiredFiles(language)` lists the files that `open()` validates.
Beyond those, analysis reads `endtables/out/*.out` lazily by stem class and
`derivs/indices/derivind`; Greek generation reads `Greek/gener.index`. The
full set the runtime can touch is roughly 3 MiB for Latin and 7 MiB for Greek
in the Perseids stemlib (`rule_files/`, `steminds/{nomind,vbind}{,.lindex}`,
`endtables/indices/`, `endtables/out/`, `derivs/indices/derivind`). Publish a
manifest of those paths next to the data and pass it to `fetchStemlib()`.

For a very large stemlib or a long-lived page, run the module in a web worker
and cache the files with the Cache API; the facade is indifferent to how bytes
reach `writeStemlib()`.

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
repository's [licensing](../../../docs/licensing.md) and
[provenance](../../../docs/provenance.md) documents before redistributing a
stemlib with an application.
