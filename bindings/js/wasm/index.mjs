// SPDX-License-Identifier: AGPL-3.0-or-later
//
// JavaScript facade for the libmorpheus WebAssembly module.
//
// The module (dist/morpheus.mjs plus dist/morpheus.wasm) is the complete
// public C API compiled by Emscripten. This file owns the memory discipline
// at the boundary: it marshals Beta Code in, copies fixed-layout result
// structures out, and frees every native object it creates. It runs wherever
// the module runs: browsers, web workers, Node.js, Deno, and Bun.
//
// No linguistic data is bundled. Callers place a compiled stemlib in the
// module's virtual file system, either by mounting a host directory (Node.js)
// or by writing fetched bytes into memory (browsers).

/** ABI version this facade understands. */
export const ABI_VERSION = 2;

/** Numeric language selectors accepted by `open()`. */
export const MorpheusLanguage = Object.freeze({
  Greek: 0,
  Latin: 1,
  Italian: 2,
});

/** Status codes returned by the stable ABI. */
export const MorpheusStatus = Object.freeze({
  Ok: 0,
  InvalidArgument: 1,
  AbiMismatch: 2,
  NoMemory: 3,
  InputTooLong: 4,
  OutOfRange: 5,
  InternalError: 6,
  BufferTooSmall: 7,
  StemlibError: 8,
  ResultLimitExceeded: 9,
});

/** Bit flags customizing `analyze()`. Combine with `|` (BigInt). */
export const MorpheusOption = Object.freeze({
  StrictCase: 1n << 0n,
  IgnoreAccents: 1n << 1n,
  VerbsOnly: 1n << 2n,
  NoCrasis: 1n << 3n,
  Quick: 1n << 4n,
  HqDictionary: 1n << 5n,
  DialectAeolic: 1n << 16n,
  DialectAttic: 2n << 16n,
  DialectDoric: 4n << 16n,
  DialectHomeric: 8n << 16n,
  DialectIonic: 16n << 16n,
  DialectLesbian: 32n << 16n,
  DialectNonHomericEpic: 64n << 16n,
  DialectParadigm: 128n << 16n,
  DialectEpic: 72n << 16n,
  DialectProse: 256n << 16n,
});

/** Flags for the historical text output of `analyzeCompat()`. */
export const MorpheusCompatFlag = Object.freeze({
  BufferAnalyses: 0o10,
  CheckPreverb: 0o20,
  KeepBeta: 0o40,
  ShowFullInfo: 0o100,
  DatabaseFormat: 0o200,
  DatabaseShort: 0o600,
  StrictCase: 0o1000,
  ParseFormat: 0o2000,
  PerseusFormat: 0o4000,
  EndingIndex: 0o10000,
  IgnoreAccents: 0o20000,
  LexiconOutput: 0o40000,
  LemmaCount: 0o200000,
  VerbsOnly: 0o400000,
});

/**
 * Files that `open()` requires under `<root>/<Language>/`. The analyzer also
 * reads lazily, by stem class and analysis path: `endtables/out/*.out`,
 * `derivs/indices/derivind`, `stemsrc/vbs.cmp.ml` (compound verbs) and
 * `stemsrc/lemlist` (dictionary entries); Greek generation reads
 * `<root>/gener.index`.
 */
export const REQUIRED_STEMLIB_FILES = Object.freeze({
  common: Object.freeze([
    "rule_files/vowcontr.table",
    "rule_files/conseuph.table",
    "rule_files/stemtypes.table",
    "rule_files/derivtypes.table",
    "rule_files/domainlist.table",
    "rule_files/raw_preverbs.table",
    "steminds/nomind",
    "steminds/nomind.lindex",
    "steminds/vbind",
    "steminds/vbind.lindex",
    "endtables/indices/nendind",
    "endtables/indices/vbendind",
    "derivs/indices/derivind",
  ]),
  greek: Object.freeze(["rule_files/ppasslist.table"]),
});

/** Directory name of each language inside a stemlib root. */
export const LANGUAGE_DIRECTORIES = Object.freeze({
  [MorpheusLanguage.Greek]: "Greek",
  [MorpheusLanguage.Latin]: "Latin",
  [MorpheusLanguage.Italian]: "Italian",
});

const TEXT_CAPACITY = 64;
const DOMAIN_CAPACITY = 24;
const MORPH_FLAG_CAPACITY = 11;
/* Minimum sizes of the version-2 structures; the module reports the actual
 * sizes, which may grow in later ABI-compatible releases. */
const MIN_ANALYSIS_SIZE = 852;
const MIN_GENERATION_SIZE = 188;
const GENERATION_OPTIONS_SIZE = 64;
const GENERATION_OPTIONS_VERSION = 1;
const POINTER_SIZE = 4;

const decoder = new TextDecoder();
const encoder = new TextEncoder();

/** Error carrying the native status code. */
export class MorpheusError extends Error {
  constructor(status, message) {
    super(message);
    this.name = "MorpheusError";
    this.status = status;
  }
}

function statusName(status) {
  for (const [name, value] of Object.entries(MorpheusStatus)) {
    if (value === status) return name;
  }
  return `Status${status}`;
}

function cString(bytes, offset, capacity) {
  const field = bytes.subarray(offset, offset + capacity);
  const terminator = field.indexOf(0);
  return decoder.decode(terminator < 0 ? field : field.subarray(0, terminator));
}

function decodeAnalysis(bytes, truncatedFields) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const numbers = [];
  for (let offset = 0; offset < 48; offset += 4) {
    numbers.push(view.getUint32(offset, true));
  }
  let offset = 48;
  const text = () => {
    const value = cString(bytes, offset, TEXT_CAPACITY);
    offset += TEXT_CAPACITY;
    return value;
  };
  const raw = text();
  const workword = text();
  const lemma = text();
  const preverb = text();
  const augment = text();
  const stem = text();
  const suffix = text();
  const ending = text();
  const crasis = text();
  const dictionaryForm = text();
  const englishForm = text();
  const rawPreverb = text();
  const domains = cString(bytes, offset, DOMAIN_CAPACITY);
  offset += DOMAIN_CAPACITY;
  const morphFlags = bytes.slice(offset, offset + MORPH_FLAG_CAPACITY);
  return {
    structSize: numbers[0],
    partOfSpeech: numbers[1],
    dialect: numbers[2],
    geographicRegion: numbers[3],
    person: numbers[4],
    number: numbers[5],
    gender: numbers[6],
    grammaticalCase: numbers[7],
    tense: numbers[8],
    mood: numbers[9],
    voice: numbers[10],
    degree: numbers[11],
    raw,
    workword,
    lemma,
    preverb,
    augment,
    stem,
    suffix,
    ending,
    crasis,
    dictionaryForm,
    englishForm,
    rawPreverb,
    domains,
    morphFlags,
    truncatedFields,
  };
}

function decodeGeneration(bytes, truncatedFields) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const numbers = [];
  for (let offset = 0; offset < 48; offset += 4) {
    numbers.push(view.getUint32(offset, true));
  }
  const surface = cString(bytes, 48, TEXT_CAPACITY);
  const lemma = cString(bytes, 48 + TEXT_CAPACITY, TEXT_CAPACITY);
  const morphFlagOffset = 48 + 2 * TEXT_CAPACITY;
  return {
    structSize: numbers[0],
    partOfSpeech: numbers[1],
    dialect: numbers[2],
    geographicRegion: numbers[3],
    person: numbers[4],
    number: numbers[5],
    gender: numbers[6],
    grammaticalCase: numbers[7],
    tense: numbers[8],
    mood: numbers[9],
    voice: numbers[10],
    degree: numbers[11],
    surface,
    lemma,
    morphFlags: bytes.slice(morphFlagOffset, morphFlagOffset + MORPH_FLAG_CAPACITY),
    truncatedFields,
  };
}

function encodeGenerationOptions(options) {
  const resultLimit = options.resultLimit ?? 0;
  if (
    !Number.isSafeInteger(resultLimit) || resultLimit < 0 ||
    resultLimit > 65_536
  ) {
    throw new RangeError("resultLimit must be an integer from 0 to 65536");
  }
  const bytes = new Uint8Array(GENERATION_OPTIONS_SIZE);
  const view = new DataView(bytes.buffer);
  view.setUint32(0, GENERATION_OPTIONS_VERSION, true);
  view.setUint32(4, GENERATION_OPTIONS_SIZE, true);
  view.setBigUint64(8, BigInt(resultLimit), true);
  view.setUint32(16, options.excludeDuals ? 1 : 0, true);
  view.setUint32(20, options.partOfSpeech ?? 0, true);
  view.setUint32(24, options.dialect ?? 0, true);
  view.setUint32(28, options.geographicRegion ?? 0, true);
  view.setUint32(32, options.person ?? 0, true);
  view.setUint32(36, options.number ?? 0, true);
  view.setUint32(40, options.gender ?? 0, true);
  view.setUint32(44, options.grammaticalCase ?? 0, true);
  view.setUint32(48, options.tense ?? 0, true);
  view.setUint32(52, options.mood ?? 0, true);
  view.setUint32(56, options.voice ?? 0, true);
  view.setUint32(60, options.degree ?? 0, true);
  return bytes;
}

function encodeInput(text, label) {
  if (typeof text !== "string") throw new TypeError(`${label} must be a string`);
  const bytes = encoder.encode(text);
  if (bytes.includes(0)) {
    throw new MorpheusError(
      MorpheusStatus.InvalidArgument,
      `${label} must not contain NUL`,
    );
  }
  return bytes;
}

function normalizeAnalyzeOptions(options) {
  if (options === undefined) return MorpheusOption.StrictCase;
  if (typeof options === "bigint") return options;
  if (typeof options === "number") return BigInt(options);
  if (typeof options !== "object" || options === null) {
    throw new TypeError("analyze options must be a bigint, number, or object");
  }
  let flags = 0n;
  if (options.strictCase ?? true) flags |= MorpheusOption.StrictCase;
  if (options.ignoreAccents) flags |= MorpheusOption.IgnoreAccents;
  if (options.verbsOnly) flags |= MorpheusOption.VerbsOnly;
  if (options.noCrasis) flags |= MorpheusOption.NoCrasis;
  if (options.quick) flags |= MorpheusOption.Quick;
  if (options.hqDictionary) flags |= MorpheusOption.HqDictionary;
  for (const dialect of options.dialects ?? []) {
    const flag = MorpheusOption[`Dialect${dialect}`];
    if (flag === undefined) throw new RangeError(`unknown dialect: ${dialect}`);
    flags |= flag;
  }
  return flags;
}

/** Scoped native allocations released together. */
class Arena {
  #module;
  #pointers = [];
  constructor(module) {
    this.#module = module;
  }
  alloc(size) {
    const pointer = this.#module._malloc(Math.max(size, 1));
    if (!pointer) throw new MorpheusError(MorpheusStatus.NoMemory, "out of memory");
    this.#pointers.push(pointer);
    return pointer;
  }
  bytes(source) {
    const pointer = this.alloc(source.length);
    this.#module.HEAPU8.set(source, pointer);
    return pointer;
  }
  release() {
    for (const pointer of this.#pointers) this.#module._free(pointer);
    this.#pointers.length = 0;
  }
}

function withArena(module, body) {
  const arena = new Arena(module);
  try {
    return body(arena);
  } finally {
    arena.release();
  }
}

/** One opened stemlib and language, owning a native context. */
export class MorpheusContext {
  #library;
  #module;
  #pointer;
  #language;

  /** @internal */
  constructor(library, module, pointer, language) {
    this.#library = library;
    this.#module = module;
    this.#pointer = pointer;
    this.#language = language;
  }

  /** Numeric language of this context. */
  get language() {
    return this.#language;
  }

  /** Whether `close()` has run. */
  get closed() {
    return this.#pointer === 0;
  }

  #require() {
    if (!this.#pointer) throw new MorpheusError(MorpheusStatus.InvalidArgument, "context is closed");
    return this.#pointer;
  }

  /**
   * Analyze one Beta Code form. `options` is a BigInt mask of
   * `MorpheusOption`, or an object with camel-cased option names and a
   * `dialects` array of `MorpheusOption` dialect suffixes.
   */
  analyze(betaCode, options) {
    const context = this.#require();
    const module = this.#module;
    const input = encodeInput(betaCode, "betaCode");
    const flags = normalizeAnalyzeOptions(options);
    return withArena(module, (arena) => {
      const inputPointer = arena.bytes(input);
      const resultSlot = arena.alloc(POINTER_SIZE);
      module.setValue(resultSlot, 0, "i32");
      const status = module._morpheus_analyze(
        context,
        inputPointer,
        input.length,
        flags,
        resultSlot,
      );
      this.#library._check(status, "analysis failed");
      const result = module.getValue(resultSlot, "i32");
      try {
        const count = module._morpheus_result_count(result);
        const size = this.#library.analysisSize;
        const buffer = arena.alloc(size);
        const fieldsSlot = arena.alloc(4);
        const analyses = [];
        for (let index = 0; index < count; index++) {
          this.#library._check(
            module._morpheus_result_copy(result, index, buffer, size),
            "result copy failed",
          );
          this.#library._check(
            module._morpheus_result_truncated_fields(result, index, fieldsSlot),
            "truncation query failed",
          );
          const bytes = module.HEAPU8.slice(buffer, buffer + size);
          analyses.push(decodeAnalysis(bytes, module.getValue(fieldsSlot, "i32") >>> 0));
        }
        return analyses;
      } finally {
        module._morpheus_result_free(result);
      }
    });
  }

  /**
   * Run the historical text analyzer (`cruncher` output). Returns the text
   * together with the engine's analysis and lemma counts.
   */
  analyzeCompat(betaCode, flags = MorpheusCompatFlag.PerseusFormat | MorpheusCompatFlag.StrictCase) {
    const context = this.#require();
    const module = this.#module;
    const input = encodeInput(betaCode, "betaCode");
    return withArena(module, (arena) => {
      const inputPointer = arena.bytes(input);
      const outputSlot = arena.alloc(POINTER_SIZE);
      module.setValue(outputSlot, 0, "i32");
      const status = module._morpheus_compat_analyze(
        context,
        inputPointer,
        input.length,
        flags >>> 0,
        outputSlot,
      );
      this.#library._check(status, "compat analysis failed");
      const output = module.getValue(outputSlot, "i32");
      try {
        const data = module._morpheus_compat_output_data(output);
        const length = module._morpheus_compat_output_length(output);
        return {
          text: decoder.decode(module.HEAPU8.subarray(data, data + length)),
          analysisCount: module._morpheus_compat_output_analysis_count(output),
          lemmaCount: module._morpheus_compat_output_lemma_count(output),
        };
      } finally {
        module._morpheus_compat_output_free(output);
      }
    });
  }

  /**
   * Generate Greek Beta Code forms for one lemma (experimental). Requires
   * `<root>/gener.index`.
   */
  generate(lemma, options = {}) {
    const context = this.#require();
    const module = this.#module;
    const input = encodeInput(lemma, "lemma");
    const encodedOptions = encodeGenerationOptions(options);
    return withArena(module, (arena) => {
      const inputPointer = arena.bytes(input);
      const optionsPointer = arena.bytes(encodedOptions);
      const resultSlot = arena.alloc(POINTER_SIZE);
      module.setValue(resultSlot, 0, "i32");
      const status = module._morpheus_generate(
        context,
        inputPointer,
        input.length,
        optionsPointer,
        resultSlot,
      );
      this.#library._check(status, "generation failed");
      const result = module.getValue(resultSlot, "i32");
      try {
        const count = module._morpheus_generation_result_count(result);
        const size = this.#library.generationSize;
        const buffer = arena.alloc(size);
        const fieldsSlot = arena.alloc(4);
        const generations = [];
        for (let index = 0; index < count; index++) {
          this.#library._check(
            module._morpheus_generation_result_copy(result, index, buffer, size),
            "generation copy failed",
          );
          this.#library._check(
            module._morpheus_generation_result_truncated_fields(result, index, fieldsSlot),
            "truncation query failed",
          );
          const bytes = module.HEAPU8.slice(buffer, buffer + size);
          generations.push(decodeGeneration(bytes, module.getValue(fieldsSlot, "i32") >>> 0));
        }
        return generations;
      } finally {
        module._morpheus_generation_result_free(result);
      }
    });
  }

  /** Release the native context. Safe to call more than once. */
  close() {
    if (!this.#pointer) return;
    this.#module._morpheus_close(this.#pointer);
    this.#pointer = 0;
    this.#library._forget(this);
  }

}

if (typeof Symbol.dispose === "symbol") {
  MorpheusContext.prototype[Symbol.dispose] = function dispose() {
    this.close();
  };
}

/** One instantiated WebAssembly module and its virtual file system. */
export class Morpheus {
  #module;
  #contexts = new Set();

  /** @internal */
  constructor(module) {
    this.#module = module;
    const abi = module._morpheus_abi_version();
    if (abi !== ABI_VERSION) {
      throw new MorpheusError(
        MorpheusStatus.AbiMismatch,
        `module implements ABI ${abi}, this facade expects ${ABI_VERSION}`,
      );
    }
    this.analysisSize = module._morpheus_analysis_size();
    this.generationSize = module._morpheus_generation_size();
    if (this.analysisSize < MIN_ANALYSIS_SIZE) {
      throw new MorpheusError(MorpheusStatus.AbiMismatch, "unexpected morpheus_analysis layout");
    }
    if (this.generationSize < MIN_GENERATION_SIZE) {
      throw new MorpheusError(MorpheusStatus.AbiMismatch, "unexpected morpheus_generation layout");
    }
  }

  /** Native size of morpheus_analysis in bytes. */
  analysisSize;
  /** Native size of morpheus_generation in bytes. */
  generationSize;

  /** The Emscripten module, for direct `FS` access. */
  get module() {
    return this.#module;
  }

  /** The Emscripten virtual file system. */
  get fs() {
    return this.#module.FS;
  }

  /** libmorpheus release that produced the module. */
  get version() {
    return this.#module.UTF8ToString(this.#module._morpheus_wasm_module_version());
  }

  /** ABI version implemented by the module. */
  get abiVersion() {
    return this.#module._morpheus_abi_version();
  }

  /** Human-readable description of a status code. */
  statusMessage(status) {
    return this.#module.UTF8ToString(this.#module._morpheus_status_message(status));
  }

  /** @internal */
  _check(status, context) {
    if (status === MorpheusStatus.Ok) return;
    throw new MorpheusError(status, `${context}: ${this.statusMessage(status)} (${statusName(status)})`);
  }

  /** @internal */
  _forget(context) {
    this.#contexts.delete(context);
  }

  #ensureDirectory(path) {
    const FS = this.#module.FS;
    let current = "";
    for (const part of path.split("/").filter(Boolean)) {
      current += "/" + part;
      if (!FS.analyzePath(current).exists) FS.mkdir(current);
    }
  }

  /**
   * Mount a host directory into the virtual file system (Node.js, Deno and
   * Bun only). Returns the mount point to pass to `open()`.
   */
  mountDirectory(hostPath, mountPoint = "/stemlib") {
    const FS = this.#module.FS;
    const NODEFS = FS.filesystems?.NODEFS;
    if (!NODEFS) {
      throw new Error("NODEFS is unavailable in this environment; use writeStemlib()");
    }
    this.#ensureDirectory(mountPoint);
    FS.mount(NODEFS, { root: hostPath }, mountPoint);
    return mountPoint;
  }

  /**
   * Write stemlib files into the in-memory file system. `entries` maps paths
   * relative to `root` (for example `Latin/steminds/nomind`) to bytes.
   * Returns `root` to pass to `open()`.
   */
  writeStemlib(entries, root = "/stemlib") {
    const FS = this.#module.FS;
    const iterable = entries instanceof Map || Array.isArray(entries)
      ? entries
      : Object.entries(entries);
    for (const [relativePath, data] of iterable) {
      const fullPath = `${root}/${relativePath}`.replace(/\/+/g, "/");
      const directory = fullPath.slice(0, fullPath.lastIndexOf("/"));
      this.#ensureDirectory(directory);
      const bytes = data instanceof Uint8Array
        ? data
        : data instanceof ArrayBuffer
        ? new Uint8Array(data)
        : typeof data === "string"
        ? encoder.encode(data)
        : null;
      if (!bytes) throw new TypeError(`unsupported data for ${relativePath}`);
      FS.writeFile(fullPath, bytes);
    }
    return root;
  }

  /**
   * Fetch stemlib files over HTTP into the in-memory file system. `paths`
   * are relative to both `baseUrl` and `root`; pass the directory listing or
   * manifest of the served stemlib. Returns `root` to pass to `open()`.
   */
  async fetchStemlib(baseUrl, paths, { root = "/stemlib", fetch: fetcher = globalThis.fetch, concurrency = 8 } = {}) {
    if (typeof fetcher !== "function") throw new Error("fetch is unavailable; pass options.fetch");
    const base = String(baseUrl).endsWith("/") ? String(baseUrl) : `${baseUrl}/`;
    const queue = [...paths];
    const entries = [];
    const worker = async () => {
      while (queue.length) {
        const relativePath = queue.shift();
        const response = await fetcher(new URL(relativePath, base));
        if (!response.ok) {
          throw new MorpheusError(
            MorpheusStatus.StemlibError,
            `fetching ${relativePath} failed with HTTP ${response.status}`,
          );
        }
        entries.push([relativePath, new Uint8Array(await response.arrayBuffer())]);
      }
    };
    await Promise.all(Array.from({ length: Math.max(1, concurrency) }, worker));
    return this.writeStemlib(entries, root);
  }

  /** Relative paths `open()` validates for a language. */
  static requiredFiles(language) {
    const directory = LANGUAGE_DIRECTORIES[language];
    if (!directory) throw new RangeError(`unknown language: ${language}`);
    const files = [...REQUIRED_STEMLIB_FILES.common];
    if (language === MorpheusLanguage.Greek) files.push(...REQUIRED_STEMLIB_FILES.greek);
    return files.map((file) => `${directory}/${file}`);
  }

  /** Create a context for `language` over the stemlib at `stemlib` (a virtual path). */
  open({ stemlib = "/stemlib", language }) {
    if (!Object.values(MorpheusLanguage).includes(language)) {
      throw new RangeError(`unknown language: ${language}`);
    }
    const module = this.#module;
    const path = encodeInput(stemlib, "stemlib");
    return withArena(module, (arena) => {
      const pathPointer = arena.bytes(path);
      const contextSlot = arena.alloc(POINTER_SIZE);
      module.setValue(contextSlot, 0, "i32");
      const status = module._morpheus_open_path(
        ABI_VERSION,
        pathPointer,
        path.length,
        language,
        contextSlot,
      );
      this._check(status, `opening ${stemlib} for language ${language} failed`);
      const context = new MorpheusContext(this, module, module.getValue(contextSlot, "i32"), language);
      this.#contexts.add(context);
      return context;
    });
  }

  /** Close every context created by this instance. */
  closeAll() {
    for (const context of [...this.#contexts]) context.close();
  }
}

/**
 * Instantiate the module. By default the factory is imported from
 * `./dist/morpheus.mjs` next to this file; pass `moduleUrl` or an already
 * imported `factory` to load it from elsewhere. `moduleOptions` reaches the
 * Emscripten factory (for example `locateFile` or `wasmBinary`).
 */
export async function createMorpheus({ factory, moduleUrl, moduleOptions = {} } = {}) {
  let create = factory;
  if (!create) {
    const url = moduleUrl ?? new URL("./dist/morpheus.mjs", import.meta.url);
    const imported = await import(/* @vite-ignore */ url.href ?? String(url));
    create = imported.default;
  }
  if (typeof create !== "function") {
    throw new TypeError("the module factory must be the default export of morpheus.mjs");
  }
  const module = await create({ noInitialRun: true, ...moduleOptions });
  return new Morpheus(module);
}

export default createMorpheus;
