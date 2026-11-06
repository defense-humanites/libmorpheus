// SPDX-License-Identifier: AGPL-3.0-or-later
//
// A pool of benchmark workers, each holding one WebAssembly instance and one
// Greek context. The compiled module and the stemlib bytes are shared with
// every worker through structured cloning; memories are separate.

import { Worker } from "node:worker_threads";

/**
 * @typedef {(
 *   | { type: "init", moduleUrl: string, dataMode: import("./wasm-runtime.mjs").WasmDataMode,
 *       stemlibPath: string, compiledModule: WebAssembly.Module | null,
 *       files: ReadonlyMap<string, Uint8Array> | null }
 *   | { type: "analyze", words: readonly string[], first: number, step: number, operations: number }
 *   | { type: "generate", lemma: string, iterations: number }
 *   | { type: "close" }
 * )} WorkerRequest
 */

/**
 * @typedef {(
 *   | { type: "ready" }
 *   | { type: "done", results: number }
 *   | { type: "closed" }
 *   | { type: "error", message: string }
 * )} WorkerResponse
 */

const workerUrl = new URL("./wasm-worker.mjs", import.meta.url);

class PoolWorker {
  /** @type {Worker} */
  #worker;
  /** @type {{ resolve: (response: WorkerResponse) => void, reject: (error: Error) => void } | null} */
  #pending = null;

  constructor() {
    this.#worker = new Worker(workerUrl);
    this.#worker.on("message", (/** @type {WorkerResponse} */ response) => {
      const pending = this.#pending;
      this.#pending = null;
      if (!pending) return;
      if (response.type === "error") pending.reject(new Error(response.message));
      else pending.resolve(response);
    });
    this.#worker.on("error", (error) => {
      const pending = this.#pending;
      this.#pending = null;
      pending?.reject(error instanceof Error ? error : new Error(String(error)));
    });
    this.#worker.on("exit", (code) => {
      const pending = this.#pending;
      this.#pending = null;
      pending?.reject(new Error(`benchmark worker exited with code ${code}`));
    });
  }

  /**
   * @param {WorkerRequest} request
   * @returns {Promise<WorkerResponse>}
   */
  request(request) {
    if (this.#pending) throw new Error("worker is busy");
    return new Promise((resolve, reject) => {
      this.#pending = { resolve, reject };
      this.#worker.postMessage(request);
    });
  }

  terminate() {
    return this.#worker.terminate();
  }
}

/**
 * @typedef {object} WasmPoolOptions
 * @property {number} size
 * @property {URL} moduleUrl
 * @property {import("./wasm-runtime.mjs").WasmDataMode} dataMode
 * @property {string} stemlibPath
 * @property {WebAssembly.Module | null} compiledModule
 * @property {ReadonlyMap<string, Uint8Array> | null} files
 */

export class WasmPool {
  /** @type {readonly PoolWorker[]} */
  #workers;

  /** @param {readonly PoolWorker[]} workers */
  constructor(workers) {
    this.#workers = workers;
  }

  /**
   * Spawn and initialize every worker; resolves once all contexts are open.
   *
   * @param {WasmPoolOptions} options
   */
  static async start(options) {
    const workers = Array.from({ length: options.size }, () => new PoolWorker());
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
      await Promise.all(workers.map((worker) => worker.terminate()));
      throw error;
    }
    return new WasmPool(workers);
  }

  get size() {
    return this.#workers.length;
  }

  /**
   * Analyze `operations` words distributed round-robin, exactly as the native
   * benchmark assigns them to its contexts. Returns the total analysis count.
   *
   * @param {readonly string[]} words
   * @param {number} operations
   */
  async analyze(words, operations) {
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
      (sum, response) => sum + (response.type === "done" ? response.results : 0),
      0,
    );
  }

  /**
   * Generate `iterations` times on every worker. Returns the total result count.
   *
   * @param {string} lemma
   * @param {number} iterations
   */
  async generate(lemma, iterations) {
    const responses = await Promise.all(
      this.#workers.map((worker) => worker.request({ type: "generate", lemma, iterations })),
    );
    return responses.reduce(
      (sum, response) => sum + (response.type === "done" ? response.results : 0),
      0,
    );
  }

  async close() {
    try {
      await Promise.all(this.#workers.map((worker) => worker.request({ type: "close" })));
    } finally {
      await Promise.all(this.#workers.map((worker) => worker.terminate()));
    }
  }
}
