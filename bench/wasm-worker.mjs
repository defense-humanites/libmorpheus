// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Benchmark worker: one WebAssembly instance and one Greek context per
// worker, which is the concurrency model the native bindings use (contexts
// are thread-affine). The main thread in compare.mjs drives the pool one
// operation per request, and every result is posted back to it, as an
// application consuming the analyses on its main thread would receive them.

import { parentPort } from "node:worker_threads";

import { createWasmInstance, MorpheusLanguage } from "./wasm-runtime.mjs";

if (!parentPort) throw new Error("wasm-worker.mjs runs as a worker thread");

/** @type {import("./wasm-runtime.mjs").WasmInstance | null} */
let instance = null;
/** @type {import("../bindings/js/wasm/index.mjs").MorpheusContext | null} */
let context = null;

/** @param {import("./wasm-pool.mjs").WorkerResponse} response */
const reply = (response) => parentPort.postMessage(response);

parentPort.on("message", async (/** @type {import("./wasm-pool.mjs").WorkerRequest} */ request) => {
  try {
    switch (request.type) {
      case "init": {
        instance = await createWasmInstance({
          moduleUrl: new URL(request.moduleUrl),
          dataMode: request.dataMode,
          stemlibPath: request.stemlibPath,
          compiledModule: request.compiledModule ?? undefined,
          files: request.files ?? undefined,
        });
        context = instance.morpheus.open({
          stemlib: instance.root,
          language: MorpheusLanguage.Greek,
        });
        reply({ type: "ready" });
        break;
      }
      case "analyze": {
        if (!context) throw new Error("worker is not initialized");
        reply({ type: "results", results: context.analyze(request.word) });
        break;
      }
      case "generate": {
        if (!context) throw new Error("worker is not initialized");
        reply({
          type: "results",
          results: context.generate(request.lemma, { resultLimit: request.resultLimit }),
        });
        break;
      }
      case "close": {
        context?.close();
        context = null;
        instance = null;
        reply({ type: "closed" });
        break;
      }
    }
  } catch (error) {
    reply({ type: "error", message: String(error) });
  }
});
