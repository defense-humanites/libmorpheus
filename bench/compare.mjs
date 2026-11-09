// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Runtime benchmark: the native library through the Node.js binding (one
// Node-API addon, `MORPHEUS_NODE_ADDON`, opening `MORPHEUS_LIBRARY`), the
// compatibility `cruncher` client as a child process, and optionally the
// WebAssembly module over a pool of worker threads. Produces a schema 3
// report; see docs/benchmarks.md.

import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import { availableParallelism, release } from "node:os";
import { pathToFileURL } from "node:url";

import {
  MORPHEUS_NODE_VERSION,
  MorpheusLanguage,
  MorpheusLibrary,
  MorpheusOption,
} from "../bindings/js/node/index.js";
import { isMainModule } from "./main-module.mjs";
import {
  compareReports,
  CURRENT_SCHEMA_VERSION,
  uvThreadpoolSize,
  WASM_RESULT_DELIVERY,
} from "./report.mjs";
import {
  compileWasmModule,
  createWasmInstance,
  readGreekRuntimeFiles,
  runtimeBytes,
  WASM_DATA_MODES,
} from "./wasm-runtime.mjs";
import { WasmPool } from "./wasm-pool.mjs";

/** @typedef {import("./report.mjs").Measurement} Measurement */
/** @typedef {import("./report.mjs").BenchmarkReport} BenchmarkReport */
/** @typedef {import("./wasm-runtime.mjs").WasmDataMode} WasmDataMode */

/**
 * @typedef {object} Configuration
 * @property {string} fixturePath
 * @property {number} iterations
 * @property {number} warmupIterations
 * @property {readonly number[]} contextCounts
 * @property {number} coldSamples
 * @property {boolean} json
 * @property {string | null} baselinePath
 * @property {string | null} label
 * @property {string | null} sourceRevision
 * @property {string | null} stemlibRevision
 * @property {string | null} compiler
 * @property {string | null} generationSmallLemma
 * @property {string | null} generationMaximalLemma
 * @property {readonly WasmDataMode[]} wasmDataModes
 */

const GENERATION_RESULT_LIMIT = 65_536;

/**
 * @param {string} value
 * @param {string} option
 * @param {boolean} [allowZero]
 */
function positiveInteger(value, option, allowZero = false) {
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < (allowZero ? 0 : 1)) {
    throw new Error(`${option} requires ${allowZero ? "a non-negative" : "a positive"} integer`);
  }
  return parsed;
}

/**
 * @param {readonly string[]} arguments_
 * @returns {Configuration}
 */
export function parseArguments(arguments_) {
  let fixturePath = "test/fixture.json";
  let iterations = 20;
  let warmupIterations = 2;
  /** @type {readonly number[]} */
  let contextCounts = [1, 2, 4];
  let coldSamples = 10;
  let json = false;
  /** @type {string | null} */
  let baselinePath = null;
  /** @type {string | null} */
  let label = null;
  /** @type {string | null} */
  let sourceRevision = null;
  /** @type {string | null} */
  let stemlibRevision = null;
  /** @type {string | null} */
  let compiler = null;
  /** @type {string | null} */
  let generationSmallLemma = null;
  /** @type {string | null} */
  let generationMaximalLemma = null;
  /** @type {readonly WasmDataMode[]} */
  let wasmDataModes = WASM_DATA_MODES;

  for (let index = 0; index < arguments_.length; index++) {
    const argument = arguments_[index];
    const next = () => {
      const value = arguments_[++index];
      if (value === undefined) throw new Error(`${argument} requires a value`);
      return value;
    };
    switch (argument) {
      case "--fixture": fixturePath = next(); break;
      case "--iterations": iterations = positiveInteger(next(), argument); break;
      case "--warmup": warmupIterations = positiveInteger(next(), argument, true); break;
      case "--contexts": {
        const values = next().split(",").map((value) => positiveInteger(value, argument));
        contextCounts = [...new Set(values)];
        break;
      }
      case "--cold-samples": coldSamples = positiveInteger(next(), argument, true); break;
      case "--baseline": baselinePath = next(); break;
      case "--label": label = next(); break;
      case "--revision": sourceRevision = next(); break;
      case "--stemlib-revision": stemlibRevision = next(); break;
      case "--compiler": compiler = next(); break;
      case "--generation-small": generationSmallLemma = next(); break;
      case "--generation-maximal": generationMaximalLemma = next(); break;
      case "--wasm-data": {
        const modes = next().split(",");
        for (const mode of modes) {
          if (!WASM_DATA_MODES.includes(/** @type {WasmDataMode} */ (mode))) {
            throw new Error(`${argument} accepts ${WASM_DATA_MODES.join(",")}`);
          }
        }
        wasmDataModes = /** @type {WasmDataMode[]} */ ([...new Set(modes)]);
        break;
      }
      case "--json": json = true; break;
      default: throw new Error(`unknown argument: ${argument}`);
    }
  }
  if ((generationSmallLemma === null) !== (generationMaximalLemma === null)) {
    throw new Error("--generation-small and --generation-maximal must be provided together");
  }
  return {
    fixturePath,
    iterations,
    warmupIterations,
    contextCounts,
    coldSamples,
    json,
    baselinePath,
    label,
    sourceRevision,
    stemlibRevision,
    compiler,
    generationSmallLemma,
    generationMaximalLemma,
    wasmDataModes,
  };
}

/** @param {string} name */
function requireEnvironment(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required`);
  return value;
}

/**
 * @param {string} path
 * @returns {Promise<readonly string[]>}
 */
async function loadWords(path) {
  /** @type {Array<{ input: string, opts?: readonly string[] }>} */
  const fixtures = JSON.parse(await readFile(path, "utf8"));
  const words = [...new Set(
    fixtures
      .filter(({ opts }) => !opts?.length)
      .map(({ input }) => input)
      .filter(Boolean),
  )];
  if (!words.length) throw new Error(`no benchmark words found in ${path}`);
  return words;
}

/** @param {readonly string[]} words */
function corpusSha256(words) {
  return createHash("sha256").update(JSON.stringify(words)).digest("hex");
}

/** @param {string | URL} path */
async function fileSha256(path) {
  return createHash("sha256").update(await readFile(path)).digest("hex");
}

const rss = () => process.memoryUsage.rss();

/**
 * Run `body` while sampling the process RSS every 5 ms; returns its value and
 * the peak observed.
 *
 * @template T
 * @param {() => Promise<T>} body
 * @returns {Promise<[T, number]>}
 */
async function sampleRss(body) {
  let peakRss = rss();
  const sampler = setInterval(() => {
    peakRss = Math.max(peakRss, rss());
  }, 5);
  try {
    const value = await body();
    peakRss = Math.max(peakRss, rss());
    return [value, peakRss];
  } finally {
    clearInterval(sampler);
  }
}

/**
 * @param {string} engine
 * @param {"analysis" | "generation"} workload
 * @param {string | null} lemma
 * @param {number} contexts
 * @param {number} operations
 * @param {number} durationMs
 * @param {number | null} startupMs
 * @param {number | null} results
 * @param {number | null} peakRssBytes
 * @param {number | null} baselineRssBytes
 * @returns {Measurement}
 */
function summarize(
  engine,
  workload,
  lemma,
  contexts,
  operations,
  durationMs,
  startupMs,
  results,
  peakRssBytes,
  baselineRssBytes,
) {
  return {
    engine,
    workload,
    lemma,
    contexts,
    operations,
    durationMs,
    operationsPerSecond: operations * 1000 / durationMs,
    meanMicroseconds: durationMs * 1000 / operations,
    startupMs,
    results,
    peakRssBytes,
    rssGrowthBytes: peakRssBytes === null || baselineRssBytes === null
      ? null
      : peakRssBytes - baselineRssBytes,
  };
}

/**
 * Open the library and `contextCount` Greek contexts, timing the whole
 * start-up (library load and symbol binding included).
 *
 * @param {string} libraryPath
 * @param {string} stemlibPath
 * @param {number} contextCount
 */
function openContexts(libraryPath, stemlibPath, contextCount) {
  const startupStart = performance.now();
  const library = new MorpheusLibrary(libraryPath);
  const contexts = Array.from(
    { length: contextCount },
    () => library.createContext(stemlibPath, MorpheusLanguage.Greek),
  );
  return { library, contexts, startupMs: performance.now() - startupStart };
}

/**
 * @param {string} libraryPath
 * @param {string} stemlibPath
 * @param {readonly string[]} words
 * @param {Configuration} configuration
 * @param {number} contextCount
 * @returns {Promise<Measurement>}
 */
async function benchmarkNode(libraryPath, stemlibPath, words, configuration, contextCount) {
  const baselineRss = rss();
  const { library, contexts, startupMs } = openContexts(libraryPath, stemlibPath, contextCount);
  try {
    for (let iteration = 0; iteration < configuration.warmupIterations; iteration++) {
      await Promise.all(words.map((word, index) =>
        contexts[index % contexts.length].analyze(word, MorpheusOption.StrictCase)
      ));
    }
    const operations = configuration.iterations * words.length;
    const start = performance.now();
    const [counts, peakRss] = await sampleRss(() =>
      Promise.all(contexts.map(async (context, worker) => {
        let analyses = 0;
        for (let operation = worker; operation < operations; operation += contexts.length) {
          analyses += (await context.analyze(
            words[operation % words.length],
            MorpheusOption.StrictCase,
          )).length;
        }
        return analyses;
      }))
    );
    const durationMs = performance.now() - start;
    return summarize(
      "node",
      "analysis",
      null,
      contextCount,
      operations,
      durationMs,
      startupMs,
      counts.reduce((sum, count) => sum + count, 0),
      peakRss,
      baselineRss,
    );
  } finally {
    await Promise.all(contexts.map((context) => context.close()));
    library.close();
  }
}

/**
 * @param {string} cruncherPath
 * @param {string} stemlibPath
 * @param {readonly string[]} words
 */
function runCruncher(cruncherPath, stemlibPath, words) {
  return new Promise((resolve, reject) => {
    const child = spawn(cruncherPath, ["-T"], {
      env: { ...process.env, MORPHLIB: stemlibPath },
      stdio: ["pipe", "ignore", "ignore"],
    });
    child.on("error", reject);
    child.on("close", (code, signal) => {
      if (code === 0) resolve(undefined);
      else reject(new Error(`cruncher exited with ${signal ?? `status ${code}`}`));
    });
    child.stdin.on("error", reject);
    child.stdin.end(`${words.join("\n")}\n`);
  });
}

/**
 * @param {string} cruncherPath
 * @param {string} stemlibPath
 * @param {readonly string[]} words
 * @param {Configuration} configuration
 * @returns {Promise<Measurement>}
 */
async function benchmarkPersistentCruncher(cruncherPath, stemlibPath, words, configuration) {
  const warmupWords = Array.from({ length: configuration.warmupIterations }, () => words).flat();
  if (warmupWords.length) await runCruncher(cruncherPath, stemlibPath, warmupWords);
  const measuredWords = Array.from({ length: configuration.iterations }, () => words).flat();
  const start = performance.now();
  await runCruncher(cruncherPath, stemlibPath, measuredWords);
  const durationMs = performance.now() - start;
  return summarize(
    "cruncher-persistent",
    "analysis",
    null,
    1,
    measuredWords.length,
    durationMs,
    null,
    null,
    null,
    null,
  );
}

/**
 * @param {string} cruncherPath
 * @param {string} stemlibPath
 * @param {readonly string[]} words
 * @param {number} samples
 * @returns {Promise<Measurement | null>}
 */
async function benchmarkColdCruncher(cruncherPath, stemlibPath, words, samples) {
  if (!samples) return null;
  const start = performance.now();
  for (let sample = 0; sample < samples; sample++) {
    await runCruncher(cruncherPath, stemlibPath, [words[sample % words.length]]);
  }
  const durationMs = performance.now() - start;
  return summarize(
    "cruncher-cold",
    "analysis",
    null,
    0,
    samples,
    durationMs,
    durationMs / samples,
    null,
    null,
    null,
  );
}

/**
 * @param {string} libraryPath
 * @param {string} stemlibPath
 * @param {string} lemma
 * @param {"small" | "maximal"} label
 * @param {Configuration} configuration
 * @param {number} contextCount
 * @returns {Promise<Measurement>}
 */
async function benchmarkWarmGeneration(
  libraryPath,
  stemlibPath,
  lemma,
  label,
  configuration,
  contextCount,
) {
  const baselineRss = rss();
  const { library, contexts, startupMs } = openContexts(libraryPath, stemlibPath, contextCount);
  const generate = (/** @type {typeof contexts[number]} */ context) =>
    context.generate(lemma, { resultLimit: GENERATION_RESULT_LIMIT });
  try {
    await Promise.all(contexts.map(generate));
    for (let iteration = 0; iteration < configuration.warmupIterations; iteration++) {
      await Promise.all(contexts.map(generate));
    }
    const operations = configuration.iterations * contextCount;
    const start = performance.now();
    const [counts, peakRss] = await sampleRss(() =>
      Promise.all(contexts.map(async (context) => {
        let results = 0;
        for (let iteration = 0; iteration < configuration.iterations; iteration++) {
          results += (await generate(context)).length;
        }
        return results;
      }))
    );
    const durationMs = performance.now() - start;
    return summarize(
      `generation-${label}-warm`,
      "generation",
      lemma,
      contextCount,
      operations,
      durationMs,
      startupMs,
      counts.reduce((sum, count) => sum + count, 0),
      peakRss,
      baselineRss,
    );
  } finally {
    await Promise.all(contexts.map((context) => context.close()));
    library.close();
  }
}

/**
 * @param {string} libraryPath
 * @param {string} stemlibPath
 * @param {string} lemma
 * @param {"small" | "maximal"} label
 * @param {number} samples
 * @returns {Promise<Measurement | null>}
 */
async function benchmarkColdGeneration(libraryPath, stemlibPath, lemma, label, samples) {
  if (!samples) return null;
  const baselineRss = rss();
  const library = new MorpheusLibrary(libraryPath);
  let peakRss = baselineRss;
  let results = 0;
  const start = performance.now();
  try {
    for (let sample = 0; sample < samples; sample++) {
      const context = library.createContext(stemlibPath, MorpheusLanguage.Greek);
      try {
        results += (await context.generate(lemma, { resultLimit: GENERATION_RESULT_LIMIT }))
          .length;
        peakRss = Math.max(peakRss, rss());
      } finally {
        await context.close();
      }
    }
  } finally {
    library.close();
  }
  const durationMs = performance.now() - start;
  return summarize(
    `generation-${label}-cold`,
    "generation",
    lemma,
    0,
    samples,
    durationMs,
    durationMs / samples,
    results,
    peakRss,
    baselineRss,
  );
}

/**
 * @typedef {object} WasmShared
 * @property {URL} moduleUrl
 * @property {string} stemlibPath
 * @property {WebAssembly.Module} compiledModule
 * @property {ReadonlyMap<string, Uint8Array>} files
 */

/**
 * Analysis over a pool of `contextCount` worker threads, one WebAssembly
 * instance and one Greek context each, with the compiled module and (for
 * MEMFS) the stemlib bytes shared through structured cloning. Word assignment
 * matches the native benchmark operation for operation. Startup covers worker
 * spawn, instantiation, data placement and context creation.
 *
 * @param {WasmShared} shared
 * @param {WasmDataMode} dataMode
 * @param {readonly string[]} words
 * @param {Configuration} configuration
 * @param {number} contextCount
 * @returns {Promise<Measurement>}
 */
async function benchmarkWasmAnalysis(shared, dataMode, words, configuration, contextCount) {
  const baselineRss = rss();
  const startupStart = performance.now();
  const pool = await WasmPool.start({
    size: contextCount,
    moduleUrl: shared.moduleUrl,
    dataMode,
    stemlibPath: shared.stemlibPath,
    compiledModule: shared.compiledModule,
    files: dataMode === "memfs" ? shared.files : null,
  });
  const startupMs = performance.now() - startupStart;
  try {
    for (let iteration = 0; iteration < configuration.warmupIterations; iteration++) {
      await pool.analyze(words, words.length);
    }
    const operations = configuration.iterations * words.length;
    const start = performance.now();
    const [results, peakRss] = await sampleRss(() => pool.analyze(words, operations));
    const durationMs = performance.now() - start;
    return summarize(
      `wasm-${dataMode}`,
      "analysis",
      null,
      contextCount,
      operations,
      durationMs,
      startupMs,
      results,
      peakRss,
      baselineRss,
    );
  } finally {
    await pool.close();
  }
}

/**
 * Cold start in the main thread: compile the module from its bytes, place the
 * stemlib, open a context and analyze one word, once per sample. This is the
 * WebAssembly counterpart of `cruncher-cold`.
 *
 * @param {WasmShared} shared
 * @param {WasmDataMode} dataMode
 * @param {readonly string[]} words
 * @param {number} samples
 * @returns {Promise<Measurement | null>}
 */
async function benchmarkWasmCold(shared, dataMode, words, samples) {
  if (!samples) return null;
  const baselineRss = rss();
  let results = 0;
  const start = performance.now();
  const [, peakRss] = await sampleRss(async () => {
    for (let sample = 0; sample < samples; sample++) {
      const { morpheus, root } = await createWasmInstance({
        moduleUrl: shared.moduleUrl,
        dataMode,
        stemlibPath: shared.stemlibPath,
        files: dataMode === "memfs" ? shared.files : undefined,
      });
      const context = morpheus.open({ stemlib: root, language: MorpheusLanguage.Greek });
      try {
        results += context.analyze(words[sample % words.length]).length;
      } finally {
        context.close();
      }
    }
  });
  const durationMs = performance.now() - start;
  return summarize(
    `wasm-${dataMode}-cold`,
    "analysis",
    null,
    0,
    samples,
    durationMs,
    durationMs / samples,
    results,
    peakRss,
    baselineRss,
  );
}

/**
 * @param {WasmShared} shared
 * @param {WasmDataMode} dataMode
 * @param {string} lemma
 * @param {"small" | "maximal"} label
 * @param {Configuration} configuration
 * @param {number} contextCount
 * @returns {Promise<Measurement>}
 */
async function benchmarkWasmWarmGeneration(
  shared,
  dataMode,
  lemma,
  label,
  configuration,
  contextCount,
) {
  const baselineRss = rss();
  const startupStart = performance.now();
  const pool = await WasmPool.start({
    size: contextCount,
    moduleUrl: shared.moduleUrl,
    dataMode,
    stemlibPath: shared.stemlibPath,
    compiledModule: shared.compiledModule,
    files: dataMode === "memfs" ? shared.files : null,
  });
  const startupMs = performance.now() - startupStart;
  try {
    await pool.generate(lemma, 1 + configuration.warmupIterations, GENERATION_RESULT_LIMIT);
    const operations = configuration.iterations * contextCount;
    const start = performance.now();
    const [results, peakRss] = await sampleRss(() =>
      pool.generate(lemma, configuration.iterations, GENERATION_RESULT_LIMIT)
    );
    const durationMs = performance.now() - start;
    return summarize(
      `wasm-${dataMode}-generation-${label}-warm`,
      "generation",
      lemma,
      contextCount,
      operations,
      durationMs,
      startupMs,
      results,
      peakRss,
      baselineRss,
    );
  } finally {
    await pool.close();
  }
}

/**
 * @param {WasmShared} shared
 * @param {WasmDataMode} dataMode
 * @param {string} lemma
 * @param {"small" | "maximal"} label
 * @param {number} samples
 * @returns {Promise<Measurement | null>}
 */
async function benchmarkWasmColdGeneration(shared, dataMode, lemma, label, samples) {
  if (!samples) return null;
  const baselineRss = rss();
  let results = 0;
  const start = performance.now();
  const [, peakRss] = await sampleRss(async () => {
    for (let sample = 0; sample < samples; sample++) {
      const { morpheus, root } = await createWasmInstance({
        moduleUrl: shared.moduleUrl,
        dataMode,
        stemlibPath: shared.stemlibPath,
        files: dataMode === "memfs" ? shared.files : undefined,
      });
      const context = morpheus.open({ stemlib: root, language: MorpheusLanguage.Greek });
      try {
        results += context.generate(lemma, { resultLimit: GENERATION_RESULT_LIMIT }).length;
      } finally {
        context.close();
      }
    }
  });
  const durationMs = performance.now() - start;
  return summarize(
    `wasm-${dataMode}-generation-${label}-cold`,
    "generation",
    lemma,
    0,
    samples,
    durationMs,
    durationMs / samples,
    results,
    peakRss,
    baselineRss,
  );
}

/**
 * @param {string} wasmModulePath
 * @param {string} stemlibPath
 * @param {readonly string[]} words
 * @param {Configuration} configuration
 */
async function benchmarkWasm(wasmModulePath, stemlibPath, words, configuration) {
  const moduleUrl = pathToFileURL(wasmModulePath);
  /** @type {WasmShared} */
  const shared = {
    moduleUrl,
    stemlibPath,
    compiledModule: await compileWasmModule(moduleUrl),
    files: await readGreekRuntimeFiles(stemlibPath),
  };
  /** @type {Measurement[]} */
  const measurements = [];
  /** @type {ReadonlyArray<readonly [string, "small" | "maximal"]>} */
  const generationLemmas = configuration.generationSmallLemma !== null &&
      configuration.generationMaximalLemma !== null
    ? [
      [configuration.generationSmallLemma, "small"],
      [configuration.generationMaximalLemma, "maximal"],
    ]
    : [];
  for (const dataMode of configuration.wasmDataModes) {
    for (const contextCount of configuration.contextCounts) {
      measurements.push(
        await benchmarkWasmAnalysis(shared, dataMode, words, configuration, contextCount),
      );
    }
    const cold = await benchmarkWasmCold(shared, dataMode, words, configuration.coldSamples);
    if (cold) measurements.push(cold);
    for (const contextCount of configuration.contextCounts) {
      for (const [lemma, label] of generationLemmas) {
        measurements.push(await benchmarkWasmWarmGeneration(
          shared,
          dataMode,
          lemma,
          label,
          configuration,
          contextCount,
        ));
      }
    }
    for (const [lemma, label] of generationLemmas) {
      const generationCold = await benchmarkWasmColdGeneration(
        shared,
        dataMode,
        lemma,
        label,
        configuration.coldSamples,
      );
      if (generationCold) measurements.push(generationCold);
    }
  }
  return { measurements, runtimeBytes: runtimeBytes(shared.files) };
}

/** @param {Measurement} measurement */
function printable(measurement) {
  /** @param {number | null} value */
  const mib = (value) => value === null ? "n/a" : (value / 1024 / 1024).toFixed(2);
  return {
    engine: measurement.engine,
    workload: measurement.workload,
    lemma: measurement.lemma ?? "n/a",
    contexts: measurement.contexts,
    operations: measurement.operations,
    duration_ms: measurement.durationMs.toFixed(2),
    ops_per_second: measurement.operationsPerSecond.toFixed(2),
    mean_us: measurement.meanMicroseconds.toFixed(2),
    startup_ms: measurement.startupMs === null ? "n/a" : measurement.startupMs.toFixed(2),
    results: measurement.results ?? "n/a",
    peak_rss_mib: mib(measurement.peakRssBytes),
    rss_growth_mib: mib(measurement.rssGrowthBytes),
  };
}

/** @param {import("./report.mjs").BenchmarkComparison} comparison */
function printableComparison(comparison) {
  /** @param {number | null} value */
  const percent = (value) =>
    value === null ? "n/a" : `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  return {
    engine: comparison.engine,
    contexts: comparison.contexts,
    throughput: percent(comparison.throughputChangePercent),
    mean_latency: percent(comparison.meanLatencyChangePercent),
    peak_rss: percent(comparison.peakRssChangePercent),
    rss_growth: percent(comparison.rssGrowthChangePercent),
  };
}

/** @param {readonly string[]} arguments_ */
export async function main(arguments_) {
  const configuration = parseArguments(arguments_);
  const libraryPath = requireEnvironment("MORPHEUS_LIBRARY");
  const stemlibPath = requireEnvironment("MORPHEUS_STEMLIB");
  const cruncherPath = requireEnvironment("MORPHEUS_CRUNCHER");
  const words = await loadWords(configuration.fixturePath);
  const threadpoolSize = uvThreadpoolSize(process.env.UV_THREADPOOL_SIZE);
  const widestContexts = Math.max(...configuration.contextCounts);
  if (threadpoolSize < widestContexts) {
    console.error(
      `warning: UV_THREADPOOL_SIZE is ${threadpoolSize}; native rows above ` +
        `${threadpoolSize} contexts share ${threadpoolSize} threads`,
    );
  }
  /** @type {Measurement[]} */
  const measurements = [];

  for (const contextCount of configuration.contextCounts) {
    measurements.push(
      await benchmarkNode(libraryPath, stemlibPath, words, configuration, contextCount),
    );
  }
  measurements.push(
    await benchmarkPersistentCruncher(cruncherPath, stemlibPath, words, configuration),
  );
  const cold = await benchmarkColdCruncher(
    cruncherPath,
    stemlibPath,
    words,
    configuration.coldSamples,
  );
  if (cold) measurements.push(cold);

  if (
    configuration.generationSmallLemma !== null &&
    configuration.generationMaximalLemma !== null
  ) {
    /** @type {ReadonlyArray<readonly [string, "small" | "maximal"]>} */
    const generationLemmas = [
      [configuration.generationSmallLemma, "small"],
      [configuration.generationMaximalLemma, "maximal"],
    ];
    for (const contextCount of configuration.contextCounts) {
      for (const [lemma, label] of generationLemmas) {
        measurements.push(await benchmarkWarmGeneration(
          libraryPath,
          stemlibPath,
          lemma,
          label,
          configuration,
          contextCount,
        ));
      }
    }
    for (const [lemma, label] of generationLemmas) {
      const generationCold = await benchmarkColdGeneration(
        libraryPath,
        stemlibPath,
        lemma,
        label,
        configuration.coldSamples,
      );
      if (generationCold) measurements.push(generationCold);
    }
  }

  const wasmModulePath = process.env.MORPHEUS_WASM_MODULE ?? null;
  /** @type {number | null} */
  let wasmRuntimeBytes = null;
  if (wasmModulePath) {
    const wasm = await benchmarkWasm(wasmModulePath, stemlibPath, words, configuration);
    measurements.push(...wasm.measurements);
    wasmRuntimeBytes = wasm.runtimeBytes;
  }

  /** @type {BenchmarkReport} */
  const report = {
    schemaVersion: CURRENT_SCHEMA_VERSION,
    generatedAt: new Date().toISOString(),
    label: configuration.label,
    platform: { os: process.platform, arch: process.arch, release: release() },
    runtime: {
      node: process.versions.node,
      v8: process.versions.v8,
      uv: process.versions.uv,
      uvThreadpoolSize: threadpoolSize,
    },
    binding: { package: "@libmorpheus/node", version: MORPHEUS_NODE_VERSION },
    hardwareConcurrency: availableParallelism(),
    sourceRevision: configuration.sourceRevision ??
      process.env.MORPHEUS_BENCHMARK_REVISION ?? null,
    stemlibRevision: configuration.stemlibRevision ??
      process.env.MORPHEUS_STEMLIB_REVISION ?? null,
    compiler: configuration.compiler ?? process.env.MORPHEUS_BENCHMARK_COMPILER ?? null,
    corpus: configuration.fixturePath,
    corpusSha256: corpusSha256(words),
    uniqueWords: words.length,
    iterations: configuration.iterations,
    warmupIterations: configuration.warmupIterations,
    generationSmallLemma: configuration.generationSmallLemma,
    generationMaximalLemma: configuration.generationMaximalLemma,
    generationIndexSha256: configuration.generationSmallLemma === null
      ? null
      : await fileSha256(`${stemlibPath}/gener.index`),
    wasmModule: wasmModulePath,
    wasmModuleSha256: wasmModulePath === null
      ? null
      : await fileSha256(new URL("./morpheus.wasm", pathToFileURL(wasmModulePath))),
    wasmRuntimeBytes,
    wasmResultDelivery: wasmModulePath === null ? null : WASM_RESULT_DELIVERY,
    measurements,
  };
  const compared = configuration.baselinePath
    ? compareReports(JSON.parse(await readFile(configuration.baselinePath, "utf8")), report)
    : null;
  if (configuration.json) {
    console.log(JSON.stringify(
      compared === null ? report : {
        ...report,
        comparisonBaselineSchemaVersion: compared.baselineSchemaVersion,
        comparisonScope: compared.scope,
        comparison: compared.comparison,
      },
      null,
      2,
    ));
  } else {
    console.table(measurements.map(printable));
    if (compared) {
      console.log(
        `comparison with a schema ${compared.baselineSchemaVersion} baseline (${compared.scope})`,
      );
      console.table(compared.comparison.map(printableComparison));
    }
  }
}

if (import.meta.main ?? isMainModule(import.meta.url)) {
  await main(process.argv.slice(2));
}
