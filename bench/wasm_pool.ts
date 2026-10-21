// SPDX-License-Identifier: AGPL-3.0-or-later
//
// A pool of benchmark workers, each holding one WebAssembly instance and one
// Greek context. The compiled module and the stemlib bytes are shared with
// every worker through structured cloning; memories are separate.

import type { WasmDataMode } from "./wasm_runtime.ts";

export type WorkerRequest =
  | {
    readonly type: "init";
    readonly moduleUrl: string;
    readonly dataMode: WasmDataMode;
    readonly stemlibPath: string;
    readonly compiledModule: WebAssembly.Module | null;
    readonly files: ReadonlyMap<string, Uint8Array> | null;
  }
  | {
    readonly type: "analyze";
    readonly words: readonly string[];
    readonly first: number;
    readonly step: number;
    readonly operations: number;
  }
  | {
    readonly type: "generate";
    readonly lemma: string;
    readonly iterations: number;
  }
  | { readonly type: "close" };

export type WorkerResponse =
  | { readonly type: "ready" }
  | { readonly type: "done"; readonly results: number }
  | { readonly type: "closed" }
  | { readonly type: "error"; readonly message: string };

const workerUrl = new URL("./wasm_worker.ts", import.meta.url);

class PoolWorker {
  readonly #worker: Worker;
  #pending: {
    resolve: (response: WorkerResponse) => void;
    reject: (error: Error) => void;
  } | null = null;

  constructor() {
    this.#worker = new Worker(workerUrl, { type: "module" });
    this.#worker.onmessage = (event: MessageEvent<WorkerResponse>) => {
      const pending = this.#pending;
      this.#pending = null;
      if (!pending) return;
      if (event.data.type === "error") {
        pending.reject(new Error(event.data.message));
      } else pending.resolve(event.data);
    };
    this.#worker.onerror = (event) => {
      const pending = this.#pending;
      this.#pending = null;
      pending?.reject(new Error(event.message));
    };
  }

  request(request: WorkerRequest): Promise<WorkerResponse> {
    if (this.#pending) throw new Error("worker is busy");
    return new Promise((resolve, reject) => {
      this.#pending = { resolve, reject };
      this.#worker.postMessage(request);
    });
  }

  terminate(): void {
    this.#worker.terminate();
  }
}

export interface WasmPoolOptions {
  readonly size: number;
  readonly moduleUrl: URL;
  readonly dataMode: WasmDataMode;
  readonly stemlibPath: string;
  readonly compiledModule: WebAssembly.Module | null;
  readonly files: ReadonlyMap<string, Uint8Array> | null;
}

export class WasmPool {
  readonly #workers: readonly PoolWorker[];

  private constructor(workers: readonly PoolWorker[]) {
    this.#workers = workers;
  }

  /** Spawn and initialize every worker; resolves once all contexts are open. */
  static async start(options: WasmPoolOptions): Promise<WasmPool> {
    const workers = Array.from(
      { length: options.size },
      () => new PoolWorker(),
    );
    try {
      await Promise.all(workers.map((worker) =>
        worker.request({
          type: "init",
          moduleUrl: options.moduleUrl.href,
          dataMode: options.dataMode,
          stemlibPath: options.stemlibPath,
          compiledModule: options.compiledModule,
          files: options.files,
        })
      ));
    } catch (error) {
      for (const worker of workers) worker.terminate();
      throw error;
    }
    return new WasmPool(workers);
  }

  get size(): number {
    return this.#workers.length;
  }

  /**
   * Analyze `operations` words distributed round-robin, exactly as the FFI
   * benchmark assigns them to its contexts. Returns the total analysis count.
   */
  async analyze(words: readonly string[], operations: number): Promise<number> {
    const responses = await Promise.all(
      this.#workers.map((worker, index) =>
        worker.request({
          type: "analyze",
          words,
          first: index,
          step: this.#workers.length,
          operations,
        })
      ),
    );
    return responses.reduce(
      (sum, response) =>
        sum + (response.type === "done" ? response.results : 0),
      0,
    );
  }

  /** Generate `iterations` times on every worker. Returns the total result count. */
  async generate(lemma: string, iterations: number): Promise<number> {
    const responses = await Promise.all(
      this.#workers.map((worker) =>
        worker.request({ type: "generate", lemma, iterations })
      ),
    );
    return responses.reduce(
      (sum, response) =>
        sum + (response.type === "done" ? response.results : 0),
      0,
    );
  }

  async close(): Promise<void> {
    try {
      await Promise.all(
        this.#workers.map((worker) => worker.request({ type: "close" })),
      );
    } finally {
      for (const worker of this.#workers) worker.terminate();
    }
  }
}
