// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Shared helpers for benchmarking the WebAssembly module from Deno: the
// runtime subset of a stemlib, instantiation with an optional precompiled
// module, and the two data placements the benchmark separates (MEMFS, where
// the stemlib bytes live in the module's memory, and NODEFS, where every read
// is a host system call reached through JavaScript).

// @ts-types="../bindings/js/wasm/index.d.ts"
import {
  createMorpheus,
  type Morpheus,
  MorpheusLanguage,
} from "../bindings/js/wasm/index.mjs";

export type WasmDataMode = "memfs" | "nodefs";

export const WASM_DATA_MODES: readonly WasmDataMode[] = ["memfs", "nodefs"];

export interface WasmInstanceOptions {
  readonly moduleUrl: URL;
  readonly dataMode: WasmDataMode;
  readonly stemlibPath: string;
  /** Precompiled module shared between workers; compiled from disk when absent. */
  readonly compiledModule?: WebAssembly.Module;
  /** Stemlib bytes for MEMFS; read from disk when absent. */
  readonly files?: ReadonlyMap<string, Uint8Array>;
}

export interface WasmInstance {
  readonly morpheus: Morpheus;
  /** Virtual path to pass to `open()`. */
  readonly root: string;
}

/**
 * Relative paths the Greek runtime can read, under `<stemlibPath>/Greek/`:
 * every rule table, the four stem indices, the ending indices, every ending
 * table, the derivation index and the compound-verb and dictionary-entry
 * indices under `stemsrc/`, plus `<stemlibPath>/gener.index` when it has been
 * prepared.
 */
export async function greekRuntimeFiles(
  stemlibPath: string,
): Promise<readonly string[]> {
  const directory = `${stemlibPath}/Greek`;
  const paths: string[] = [];
  const listDirectory = async (relative: string) => {
    const entries: string[] = [];
    for await (const entry of Deno.readDir(`${directory}/${relative}`)) {
      if (entry.isFile) entries.push(`${relative}/${entry.name}`);
    }
    entries.sort();
    paths.push(...entries);
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
    try {
      await Deno.stat(`${directory}/${optional}`);
      paths.push(optional);
    } catch {
      // Not every stemlib ships both source-derived indices.
    }
  }
  const files = paths.map((path) => `Greek/${path}`);
  try {
    await Deno.stat(`${stemlibPath}/gener.index`);
    files.push("gener.index");
  } catch {
    // Analysis-only stemlib.
  }
  return files;
}

/** Read the runtime subset into memory once so workers can share the bytes. */
export async function readGreekRuntimeFiles(
  stemlibPath: string,
): Promise<ReadonlyMap<string, Uint8Array>> {
  const files = new Map<string, Uint8Array>();
  for (const relative of await greekRuntimeFiles(stemlibPath)) {
    files.set(relative, await Deno.readFile(`${stemlibPath}/${relative}`));
  }
  return files;
}

/** Total bytes of a runtime subset. */
export function runtimeBytes(files: ReadonlyMap<string, Uint8Array>): number {
  let total = 0;
  for (const bytes of files.values()) total += bytes.byteLength;
  return total;
}

/** Compile the module once from the `.wasm` next to the ES module. */
export async function compileWasmModule(
  moduleUrl: URL,
): Promise<WebAssembly.Module> {
  const wasmUrl = new URL("./morpheus.wasm", moduleUrl);
  return await WebAssembly.compile(await Deno.readFile(wasmUrl));
}

/**
 * Mount each language directory of a stemlib root through NODEFS. Benchmark
 * roots are often staged like bench/release.sh does, with `Greek` a symlink to
 * the pinned data and `gener.index` copied next to it; NODEFS resolves a
 * symlink against the virtual file system, where its target does not exist,
 * so every directory is mounted by its real path. Root-level files (the
 * generation index, read once per context) are copied into memory.
 */
async function mountStemlibDirectories(
  morpheus: Morpheus,
  stemlibPath: string,
  root = "/stemlib",
): Promise<string> {
  const FS = morpheus.fs;
  const NODEFS = FS.filesystems?.NODEFS;
  if (!NODEFS) throw new Error("NODEFS is unavailable in this runtime");
  FS.mkdir(root);
  for await (const entry of Deno.readDir(stemlibPath)) {
    const hostPath = await Deno.realPath(`${stemlibPath}/${entry.name}`);
    const mountPoint = `${root}/${entry.name}`;
    if ((await Deno.stat(hostPath)).isDirectory) {
      FS.mkdir(mountPoint);
      FS.mount(NODEFS, { root: hostPath }, mountPoint);
    } else {
      FS.writeFile(mountPoint, await Deno.readFile(hostPath));
    }
  }
  return root;
}

/**
 * Instantiate the facade. With `compiledModule`, Emscripten's
 * `instantiateWasm` hook instantiates that module instead of compiling the
 * bytes again, which is the sharing model for a worker pool.
 */
export async function createWasmInstance(
  options: WasmInstanceOptions,
): Promise<WasmInstance> {
  const moduleOptions: Record<string, unknown> = {
    print: () => undefined,
    printErr: () => undefined,
  };
  const compiled = options.compiledModule;
  if (compiled) {
    moduleOptions.instantiateWasm = (
      imports: WebAssembly.Imports,
      receive: (
        instance: WebAssembly.Instance,
        module: WebAssembly.Module,
      ) => void,
    ) => {
      WebAssembly.instantiate(compiled, imports).then((instance) =>
        receive(instance, compiled)
      );
      return {};
    };
  }
  const morpheus = await createMorpheus({
    moduleUrl: options.moduleUrl,
    moduleOptions,
  });
  if (options.dataMode === "nodefs") {
    return {
      morpheus,
      root: await mountStemlibDirectories(morpheus, options.stemlibPath),
    };
  }
  const files = options.files ??
    await readGreekRuntimeFiles(options.stemlibPath);
  return { morpheus, root: morpheus.writeStemlib(files) };
}

export { MorpheusLanguage };
