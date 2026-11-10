// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Benchmark report schema, comparison and release validation. This module
// loads no binding and spawns nothing, so the release validator and the test
// suite run on any Node.js installation.

/**
 * @typedef {object} Measurement
 * @property {string} engine
 * @property {"analysis" | "generation"} workload
 * @property {string | null} lemma
 * @property {number} contexts
 * @property {number} operations
 * @property {number} durationMs
 * @property {number} operationsPerSecond
 * @property {number} meanMicroseconds
 * @property {number | null} startupMs
 * @property {number | null} results
 * @property {number | null} peakRssBytes
 * @property {number | null} rssGrowthBytes
 */

/**
 * Schema 3: produced by `bench/compare.mjs` under Node.js. Schema 2 reports
 * were produced by the Deno harness retired after 0.4.5 and remain readable
 * as baselines; schema 1 reports (0.1.0 to 0.2.0) have analysis rows only.
 *
 * @typedef {object} BenchmarkReport
 * @property {3} schemaVersion
 * @property {string} generatedAt
 * @property {string | null} label
 * @property {{ os: string, arch: string, release: string }} platform
 * @property {{ node: string, v8: string, uv: string, uvThreadpoolSize?: number }} runtime
 * @property {{ package: string, version: string }} binding
 * @property {number} hardwareConcurrency
 * @property {string | null} sourceRevision
 * @property {string | null} stemlibRevision
 * @property {string | null} compiler
 * @property {string} corpus
 * @property {string} corpusSha256
 * @property {number} uniqueWords
 * @property {number} iterations
 * @property {number} warmupIterations
 * @property {string | null} generationSmallLemma
 * @property {string | null} generationMaximalLemma
 * @property {string | null} generationIndexSha256
 * @property {string | null} [wasmModule]
 * @property {string | null} [wasmModuleSha256]
 * @property {number | null} [wasmRuntimeBytes]
 * @property {WasmResultDelivery | null} [wasmResultDelivery]
 * @property {{ version: string, implementation: string, binding: string } | null} [python]
 * @property {readonly Measurement[]} measurements
 */

/**
 * @typedef {object} BenchmarkComparison
 * @property {string} engine
 * @property {number} contexts
 * @property {number} throughputChangePercent
 * @property {number} meanLatencyChangePercent
 * @property {number | null} peakRssChangePercent
 * @property {number | null} rssGrowthChangePercent
 */

export const CURRENT_SCHEMA_VERSION = 3;

/**
 * How the WebAssembly pool hands results to the harness. `main-thread`: one
 * request per operation, every result structured-cloned to the main thread,
 * as the native binding materializes its results there. Reports without the
 * field ran each worker's batch inside the worker and returned only a count;
 * their WebAssembly rows measure less work and are not compared with these.
 *
 * @typedef {"main-thread"} WasmResultDelivery
 */
export const WASM_RESULT_DELIVERY = "main-thread";

/** libuv's default when `UV_THREADPOOL_SIZE` is unset. */
const DEFAULT_UV_THREADPOOL_SIZE = 4;

/**
 * The size of the libuv thread pool that runs every asynchronous call of the
 * Node.js binding. libuv reads `UV_THREADPOOL_SIZE` once, when the pool
 * starts, and clamps it to [1, 1024]; the value must therefore come from the
 * environment of the process, which `bench/release.sh` sets.
 *
 * @param {string | undefined} value
 */
export function uvThreadpoolSize(value) {
  const parsed = Number.parseInt(value ?? "", 10);
  if (!Number.isSafeInteger(parsed) || parsed < 1) return DEFAULT_UV_THREADPOOL_SIZE;
  return Math.min(parsed, 1024);
}

/** @param {any} report */
function wasmResultDelivery(report) {
  return report?.wasmResultDelivery ?? "worker-count";
}

/** Analysis engine of the native binding measured by each schema. */
export const NATIVE_ANALYSIS_ENGINE = Object.freeze({ 2: "ffi", 3: "node" });

/**
 * The only row whose timing does not run through the harness's own runtime:
 * `cruncher` analyzes a whole corpus per process, so the spawn and pipe costs
 * of Deno or Node.js are amortized over hundreds of operations. It is the one
 * row compared across the schema 2 to 3 runtime change.
 */
export const CROSS_RUNTIME_ENGINES = Object.freeze(["cruncher-persistent"]);

const fullGitObjectId = /^[0-9a-f]{40}$/i;
const sha256 = /^[0-9a-f]{64}$/i;

/** @param {string} engine */
export function isWasmEngine(engine) {
  return engine === "wasm" || engine.startsWith("wasm-");
}

/** @param {string} engine */
export function isPythonEngine(engine) {
  return engine === "python" || engine.startsWith("python-");
}

/**
 * Rows a report may add or omit: the WebAssembly pool (MORPHEUS_WASM_MODULE)
 * and the Python binding (MORPHEUS_PYTHON). A baseline without them yields
 * no comparison for them; the native rows are always required.
 *
 * @param {string} engine
 */
export function isOptionalEngine(engine) {
  return isWasmEngine(engine) || isPythonEngine(engine);
}

/**
 * @param {number} current
 * @param {number} baseline
 */
function percentageChange(current, baseline) {
  if (!Number.isFinite(current) || !Number.isFinite(baseline) || baseline === 0) {
    throw new Error("benchmark values must be finite and baseline values nonzero");
  }
  return (current / baseline - 1) * 100;
}

/**
 * @param {{ engine: string, contexts: number, lemma?: string | null }} measurement
 */
function measurementKey(measurement) {
  return `${measurement.engine}:${measurement.contexts}:${measurement.lemma ?? ""}`;
}

/**
 * Compare `current` (schema 3) with a baseline of schema 1, 2 or 3. A schema 3
 * baseline must hold every native row of the current report; WebAssembly
 * rows absent from it are skipped. A schema 1 or 2 baseline was measured by
 * the Deno harness, so only the cross-runtime rows are compared and the
 * result records that scope.
 *
 * @param {any} baseline
 * @param {BenchmarkReport} current
 * @returns {{ comparison: readonly BenchmarkComparison[], baselineSchemaVersion: number, scope: "complete" | "cross-runtime" }}
 */
export function compareReports(baseline, current) {
  if (![1, 2, 3].includes(baseline?.schemaVersion) || current.schemaVersion !== 3) {
    throw new Error("unsupported benchmark report schema");
  }
  if (baseline.corpusSha256 !== current.corpusSha256) {
    throw new Error("benchmark corpus differs from baseline");
  }
  if (baseline.schemaVersion >= 2 && (
    baseline.generationIndexSha256 !== current.generationIndexSha256 ||
    baseline.generationSmallLemma !== current.generationSmallLemma ||
    baseline.generationMaximalLemma !== current.generationMaximalLemma
  )) {
    throw new Error("generation benchmark inputs differ from baseline");
  }

  /** @type {Map<string, any>} */
  const baselineMeasurements = new Map();
  for (const measurement of baseline.measurements) {
    const key = measurementKey(measurement);
    if (baselineMeasurements.has(key)) {
      throw new Error(`baseline contains duplicate ${key}`);
    }
    baselineMeasurements.set(key, measurement);
  }

  const scope = baseline.schemaVersion === 3 ? "complete" : "cross-runtime";
  /** @type {Array<[Measurement, any]>} */
  const pairs = [];
  for (const measurement of current.measurements) {
    if (scope === "cross-runtime" && !CROSS_RUNTIME_ENGINES.includes(measurement.engine)) {
      continue;
    }
    if (
      isWasmEngine(measurement.engine) &&
      wasmResultDelivery(baseline) !== wasmResultDelivery(current)
    ) {
      continue;
    }
    const previous = baselineMeasurements.get(measurementKey(measurement));
    if (!previous) {
      // WebAssembly and Python measurements are optional additions to a
      // report; a baseline recorded without them simply yields no comparison
      // for them. Every native configuration must still be present.
      if (isOptionalEngine(measurement.engine)) continue;
      throw new Error(
        `baseline lacks ${measurement.engine} with ${measurement.contexts} contexts`,
      );
    }
    pairs.push([measurement, previous]);
  }
  if (!pairs.length) throw new Error("no measurement is comparable with the baseline");

  /**
   * @param {number | null} value
   * @param {number | null} baselineValue
   */
  const optionalChange = (value, baselineValue) =>
    value === null || baselineValue === null || value === undefined ||
      baselineValue === undefined
      ? null
      : baselineValue === 0
      ? (value === 0 ? 0 : null)
      : percentageChange(value, baselineValue);

  return {
    baselineSchemaVersion: baseline.schemaVersion,
    scope,
    comparison: pairs.map(([measurement, previous]) => ({
      engine: measurement.engine,
      contexts: measurement.contexts,
      throughputChangePercent: percentageChange(
        measurement.operationsPerSecond,
        previous.operationsPerSecond,
      ),
      meanLatencyChangePercent: percentageChange(
        measurement.meanMicroseconds,
        previous.meanMicroseconds,
      ),
      peakRssChangePercent: optionalChange(
        measurement.peakRssBytes,
        previous.peakRssBytes,
      ),
      rssGrowthChangePercent: optionalChange(
        measurement.rssGrowthBytes,
        previous.rssGrowthBytes,
      ),
    })),
  };
}

/**
 * @param {unknown} value
 * @param {string} name
 * @returns {asserts value is string}
 */
function requireString(value, name) {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${name} must be a non-empty string`);
  }
}

/**
 * @param {unknown} value
 * @param {string} name
 * @param {number} minimum
 */
function requireInteger(value, name, minimum) {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < minimum) {
    throw new Error(`${name} must be an integer greater than or equal to ${minimum}`);
  }
}

/**
 * @param {unknown} value
 * @param {string} name
 * @param {number} minimum
 */
function requireFinite(value, name, minimum) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < minimum) {
    throw new Error(`${name} must be a finite number greater than or equal to ${minimum}`);
  }
}

/**
 * @param {Measurement} measurement
 * @param {number} index
 */
function validateMeasurement(measurement, index) {
  requireString(measurement.engine, `measurements[${index}].engine`);
  if (!["analysis", "generation"].includes(measurement.workload)) {
    throw new Error(`measurements[${index}].workload is invalid`);
  }
  if (measurement.workload === "generation") {
    requireString(measurement.lemma, `measurements[${index}].lemma`);
    requireFinite(measurement.results, `measurements[${index}].results`, 1);
  } else if (measurement.lemma !== null) {
    throw new Error(`measurements[${index}].lemma must be null for analysis`);
  }
  requireInteger(measurement.contexts, `measurements[${index}].contexts`, 0);
  requireInteger(measurement.operations, `measurements[${index}].operations`, 1);
  requireFinite(measurement.durationMs, `measurements[${index}].durationMs`, 0);
  requireFinite(
    measurement.operationsPerSecond,
    `measurements[${index}].operationsPerSecond`,
    0,
  );
  requireFinite(measurement.meanMicroseconds, `measurements[${index}].meanMicroseconds`, 0);
  for (const [name, value] of [
    ["startupMs", measurement.startupMs],
    ["results", measurement.results],
    ["peakRssBytes", measurement.peakRssBytes],
  ]) {
    if (value !== null) requireFinite(value, `measurements[${index}].${name}`, 0);
  }
  if (measurement.rssGrowthBytes !== null) {
    requireFinite(
      Math.abs(measurement.rssGrowthBytes),
      `measurements[${index}].rssGrowthBytes`,
      0,
    );
  }
}

/**
 * @typedef {object} ReleaseBenchmarkExpectations
 * @property {string} label
 * @property {string} sourceRevision
 * @property {string} stemlibRevision
 * @property {string} compiler
 */

/**
 * Validate a release report: schema 3 (this harness) or schema 2 (the retired
 * Deno harness, for the retained evidence). The required configurations are
 * the same thirteen rows under either schema, with the native analysis engine
 * of that schema.
 *
 * @param {any} report
 * @param {ReleaseBenchmarkExpectations} expected
 */
export function validateReleaseBenchmark(report, expected) {
  const schemaVersion = report?.schemaVersion;
  if (schemaVersion !== 2 && schemaVersion !== 3) {
    throw new Error("unsupported benchmark schema");
  }
  requireString(report.generatedAt, "generatedAt");
  const generatedAt = new Date(report.generatedAt);
  if (
    Number.isNaN(generatedAt.valueOf()) ||
    generatedAt.toISOString() !== report.generatedAt
  ) {
    throw new Error("generatedAt must be an ISO timestamp");
  }

  for (const [name, actual, wanted] of [
    ["label", report.label, expected.label],
    ["sourceRevision", report.sourceRevision, expected.sourceRevision],
    ["stemlibRevision", report.stemlibRevision, expected.stemlibRevision],
    ["compiler", report.compiler, expected.compiler],
  ]) {
    requireString(actual, name);
    requireString(wanted, `expected ${name}`);
    if (actual !== wanted) {
      throw new Error(`${name} does not match the release input`);
    }
  }
  if (!fullGitObjectId.test(report.sourceRevision)) {
    throw new Error("sourceRevision must be a full Git object ID");
  }
  if (!fullGitObjectId.test(report.stemlibRevision)) {
    throw new Error("stemlibRevision must be a full Git object ID");
  }

  requireString(report.platform?.os, "platform.os");
  requireString(report.platform?.arch, "platform.arch");
  if (schemaVersion === 3) {
    requireString(report.runtime?.node, "runtime.node");
    requireString(report.runtime?.v8, "runtime.v8");
    requireString(report.binding?.package, "binding.package");
    requireString(report.binding?.version, "binding.version");
  } else {
    requireString(report.runtime?.deno, "runtime.deno");
    requireString(report.runtime?.v8, "runtime.v8");
    requireString(report.runtime?.typescript, "runtime.typescript");
  }
  requireInteger(report.hardwareConcurrency, "hardwareConcurrency", 1);
  requireString(report.corpus, "corpus");
  if (!sha256.test(report.corpusSha256)) {
    throw new Error("corpusSha256 must be a SHA-256 digest");
  }
  requireInteger(report.uniqueWords, "uniqueWords", 1);
  requireInteger(report.iterations, "iterations", 1);
  requireInteger(report.warmupIterations, "warmupIterations", 0);
  requireString(report.generationSmallLemma, "generationSmallLemma");
  requireString(report.generationMaximalLemma, "generationMaximalLemma");
  if (!sha256.test(report.generationIndexSha256)) {
    throw new Error("generationIndexSha256 must be a SHA-256 digest");
  }
  if (!Array.isArray(report.measurements)) {
    throw new Error("measurements must be an array");
  }
  report.measurements.forEach(validateMeasurement);

  // A Node.js binding call runs on the libuv thread pool; native rows wider
  // than the pool would measure the pool, not the contexts. Reports that
  // predate the field were all taken with the default four threads and at
  // most four contexts.
  if (schemaVersion === 3 && report.runtime.uvThreadpoolSize !== undefined) {
    requireInteger(report.runtime.uvThreadpoolSize, "runtime.uvThreadpoolSize", 1);
    for (const { engine, contexts } of report.measurements) {
      if (!isOptionalEngine(engine) && contexts > report.runtime.uvThreadpoolSize) {
        throw new Error(
          `${engine} with ${contexts} contexts exceeds the libuv thread pool ` +
            `(${report.runtime.uvThreadpoolSize}); set UV_THREADPOOL_SIZE`,
        );
      }
    }
  }
  if (report.python !== undefined && report.python !== null) {
    requireString(report.python.version, "python.version");
    requireString(report.python.implementation, "python.implementation");
    requireString(report.python.binding, "python.binding");
  }
  if (report.measurements.some(({ engine }) => isPythonEngine(engine)) && !report.python) {
    throw new Error("Python rows require the python runtime record");
  }
  if (
    report.wasmResultDelivery !== undefined && report.wasmResultDelivery !== null &&
    report.wasmResultDelivery !== WASM_RESULT_DELIVERY
  ) {
    throw new Error(`unknown wasmResultDelivery: ${report.wasmResultDelivery}`);
  }

  const configurations = new Set(
    report.measurements.map(({ engine, contexts }) => `${engine}:${contexts}`),
  );
  const native = NATIVE_ANALYSIS_ENGINE[schemaVersion];
  for (const required of [
    `${native}:1`,
    `${native}:2`,
    `${native}:4`,
    "cruncher-persistent:1",
    "cruncher-cold:0",
    "generation-small-warm:1",
    "generation-small-warm:2",
    "generation-small-warm:4",
    "generation-maximal-warm:1",
    "generation-maximal-warm:2",
    "generation-maximal-warm:4",
    "generation-small-cold:0",
    "generation-maximal-cold:0",
  ]) {
    if (!configurations.has(required)) {
      throw new Error(`release report lacks ${required}`);
    }
  }
}
