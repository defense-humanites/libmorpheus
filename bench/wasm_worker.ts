// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Benchmark worker: one WebAssembly instance and one Greek context per
// worker, which is the concurrency model the native bindings use (contexts
// are thread-affine). The main thread in compare.ts drives the pool.

import {
  createWasmInstance,
  MorpheusLanguage,
  type WasmInstance,
} from "./wasm_runtime.ts";
// @ts-types="../bindings/js/wasm/index.d.ts"
import type { MorpheusContext } from "../bindings/js/wasm/index.mjs";
import type { WorkerRequest, WorkerResponse } from "./wasm_pool.ts";

// The worker global scope, typed without pulling the worker lib into the
// modules that import this file's message types.
const scope = self as unknown as {
  postMessage(message: WorkerResponse): void;
  onmessage: ((event: MessageEvent<WorkerRequest>) => void) | null;
};

let instance: WasmInstance | null = null;
let context: MorpheusContext | null = null;

const reply = (response: WorkerResponse) => scope.postMessage(response);

scope.onmessage = async (event: MessageEvent<WorkerRequest>) => {
  const request = event.data;
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
        let results = 0;
        for (
          let operation = request.first;
          operation < request.operations;
          operation += request.step
        ) {
          results += context.analyze(
            request.words[operation % request.words.length],
          ).length;
        }
        reply({ type: "done", results });
        break;
      }
      case "generate": {
        if (!context) throw new Error("worker is not initialized");
        let results = 0;
        for (let iteration = 0; iteration < request.iterations; iteration++) {
          results += context.generate(request.lemma, { resultLimit: 65_536 })
            .length;
        }
        reply({ type: "done", results });
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
};
