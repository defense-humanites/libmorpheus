// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Shared helpers for benchmarking the WebAssembly module under Node.js: the
// runtime subset of a stemlib, instantiation with an optional precompiled
// module, and the two data placements the benchmark separates (MEMFS, where
// the stemlib bytes live in the module's memory, and NODEFS, where every read
// is a host system call reached through JavaScript).

import { readdir, readFile, realpath, stat } from "node:fs/promises";

import { createMorpheus, MorpheusLanguage } from "../bindings/js/wasm/index.mjs";

/** @typedef {"memfs" | "nodefs"} WasmDataMode */

/** @type {readonly WasmDataMode[]} */
export const WASM_DATA_MODES = Object.freeze(["memfs", "nodefs"]);

/**
 * @typedef {object} WasmInstanceOptions
 * @property {URL} moduleUrl
 * @property {WasmDataMode} dataMode
 * @property {string} stemlibPath
 * @property {WebAssembly.Module} [compiledModule] Precompiled module shared between workers; compiled from disk when absent.
 * @property {ReadonlyMap<string, Uint8Array>} [files] Stemlib bytes for MEMFS; read from disk when absent.
 */

/**
 * @typedef {object} WasmInstance
 * @property {import("../bindings/js/wasm/index.mjs").Morpheus} morpheus
 * @property {string} root Virtual path to pass to `open()`.
 */

/** @param {string} path */
async function exists(path) {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}

/**
 * Relative paths the Greek runtime can read, under `<stemlibPath>/Greek/`:
 * every rule table, the four stem indices, the ending indices, every ending
 * table, the derivation index and the compound-verb and dictionary-entry
 * indices under `stemsrc/`, plus `<stemlibPath>/gener.index` when it has been
 * prepared.
 *
 * @param {string} stemlibPath
 * @returns {Promise<readonly string[]>}
 */
export async function greekRuntimeFiles(stemlibPath) {
  const directory = `${stemlibPath}/Greek`;
  /** @type {string[]} */
  const paths = [];
  /** @param {string} relative */
  const listDirectory = async (relative) => {
    const entries = await readdir(`${directory}/${relative}`, { withFileTypes: true });
    paths.push(
      ...entries
        .filter((entry) => entry.isFile())
        .map((entry) => `${relative}/${entry.name}`)
        .sort(),
    );
  };
  await listDirectory("rule_files");
  paths.push(
    "steminds/nomind",
    "steminds/nomind.lindex",
    "steminds/vbind",
    "steminds/vbind.lindex",
  );
  await listDirectory("endtables/indices");
  await listDirectory("endtables/out");
  paths.push("derivs/indices/derivind");
  for (const optional of ["stemsrc/vbs.cmp.ml", "stemsrc/lemlist"]) {
    // Not every stemlib ships both source-derived indices.
    if (await exists(`${directory}/${optional}`)) paths.push(optional);
  }
  const files = paths.map((path) => `Greek/${path}`);
  // Analysis-only stemlibs have no generation index.
  if (await exists(`${stemlibPath}/gener.index`)) files.push("gener.index");
  return files;
}

/**
 * Read the runtime subset into memory once so workers can share the bytes.
 *
 * @param {string} stemlibPath
 * @returns {Promise<ReadonlyMap<string, Uint8Array>>}
 */
export async function readGreekRuntimeFiles(stemlibPath) {
  /** @type {Map<string, Uint8Array>} */
  const files = new Map();
  for (const relative of await greekRuntimeFiles(stemlibPath)) {
    // An exact copy, so that neither a pooled Buffer nor the module that
    // adopts the bytes through writeStemlib() shares its storage.
    files.set(relative, new Uint8Array(await readFile(`${stemlibPath}/${relative}`)));
  }
  return files;
}

/**
 * Total bytes of a runtime subset.
 *
 * @param {ReadonlyMap<string, Uint8Array>} files
 */
export function runtimeBytes(files) {
  let total = 0;
  for (const bytes of files.values()) total += bytes.byteLength;
  return total;
}

/**
 * Compile the module once from the `.wasm` next to the ES module.
 *
 * @param {URL} moduleUrl
 */
export async function compileWasmModule(moduleUrl) {
  return await WebAssembly.compile(await readFile(new URL("./morpheus.wasm", moduleUrl)));
}

/**
 * Mount each language directory of a stemlib root through NODEFS. Benchmark
 * roots are often staged like bench/release.sh does, with `Greek` a symlink to
 * the pinned data and `gener.index` copied next to it; NODEFS resolves a
 * symlink against the virtual file system, where its target does not exist,
 * so every directory is mounted by its real path. Root-level files (the
 * generation index, read once per context) are copied into memory.
 *
 * @param {import("../bindings/js/wasm/index.mjs").Morpheus} morpheus
 * @param {string} stemlibPath
 * @param {string} [root]
 */
async function mountStemlibDirectories(morpheus, stemlibPath, root = "/stemlib") {
  const FS = morpheus.fs;
  const NODEFS = FS.filesystems?.NODEFS;
  if (!NODEFS) throw new Error("NODEFS is unavailable in this runtime");
  FS.mkdir(root);
  for (const entry of (await readdir(stemlibPath)).sort()) {
    const hostPath = await realpath(`${stemlibPath}/${entry}`);
    const mountPoint = `${root}/${entry}`;
    if ((await stat(hostPath)).isDirectory()) {
      FS.mkdir(mountPoint);
      FS.mount(NODEFS, { root: hostPath }, mountPoint);
    } else {
      FS.writeFile(mountPoint, await readFile(hostPath));
    }
  }
  return root;
}

/**
 * Instantiate the facade. With `compiledModule`, the facade instantiates that
 * module instead of compiling the bytes again, which is the sharing model for
 * a worker pool.
 *
 * @param {WasmInstanceOptions} options
 * @returns {Promise<WasmInstance>}
 */
export async function createWasmInstance(options) {
  const morpheus = await createMorpheus({
    moduleUrl: options.moduleUrl,
    wasmModule: options.compiledModule,
    moduleOptions: {
      print: () => undefined,
      printErr: () => undefined,
    },
  });
  if (options.dataMode === "nodefs") {
    return {
      morpheus,
      root: await mountStemlibDirectories(morpheus, options.stemlibPath),
    };
  }
  const files = options.files ?? await readGreekRuntimeFiles(options.stemlibPath);
  return { morpheus, root: morpheus.writeStemlib(files) };
}

export { MorpheusLanguage };
