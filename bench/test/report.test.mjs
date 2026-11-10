// SPDX-License-Identifier: AGPL-3.0-or-later

import assert from "node:assert/strict";
import { test } from "node:test";

import {
  compareReports,
  CROSS_RUNTIME_ENGINES,
  uvThreadpoolSize,
  validateReleaseBenchmark,
  WASM_RESULT_DELIVERY,
} from "../report.mjs";
import { parseCommandLine } from "../validate.mjs";

/**
 * @param {string} engine
 * @param {number} contexts
 * @param {number} operationsPerSecond
 * @param {number} meanMicroseconds
 * @param {number | null} [peakRssBytes]
 */
function measurement(
  engine,
  contexts,
  operationsPerSecond,
  meanMicroseconds,
  peakRssBytes = null,
) {
  return {
    engine,
    workload: "analysis",
    lemma: null,
    contexts,
    operations: 10,
    durationMs: 1,
    operationsPerSecond,
    meanMicroseconds,
    startupMs: null,
    results: null,
    peakRssBytes,
    rssGrowthBytes: peakRssBytes,
  };
}

const platform = { os: "linux", arch: "x64", release: "6.0.0" };
const runtime = { node: "24.0.0", v8: "13.0", uv: "1.50.0" };
const binding = { package: "@libmorpheus/node", version: "0.1.2" };

/** @param {readonly object[]} measurements */
function report(measurements) {
  return {
    schemaVersion: 3,
    generatedAt: "2026-01-01T00:00:00.000Z",
    label: null,
    platform,
    runtime,
    binding,
    hardwareConcurrency: 1,
    sourceRevision: null,
    stemlibRevision: null,
    compiler: null,
    corpus: "fixture.json",
    corpusSha256: "same-corpus",
    uniqueWords: 1,
    iterations: 1,
    warmupIterations: 0,
    generationSmallLemma: null,
    generationMaximalLemma: null,
    generationIndexSha256: null,
    measurements,
  };
}

/** @param {readonly object[]} measurements */
function denoReport(measurements) {
  return {
    ...report(measurements),
    schemaVersion: 2,
    platform: { os: "darwin", arch: "aarch64" },
    runtime: { deno: "2.9.8", v8: "15.0", typescript: "6.0" },
    binding: undefined,
  };
}

/** @param {readonly object[]} measurements */
function legacyReport(measurements) {
  return { schemaVersion: 1, corpusSha256: "same-corpus", measurements };
}

test("benchmark reports compare normalized measurements", () => {
  const { comparison, scope, baselineSchemaVersion } = compareReports(
    report([measurement("node", 1, 100, 10, 1000)]),
    report([measurement("node", 1, 125, 8, 1100)]),
  );
  assert.equal(scope, "complete");
  assert.equal(baselineSchemaVersion, 3);
  assert.equal(comparison.length, 1);
  assert.equal(comparison[0].throughputChangePercent, 25);
  assert.ok(Math.abs(comparison[0].meanLatencyChangePercent + 20) < 1e-9);
  assert.ok(Math.abs((comparison[0].peakRssChangePercent ?? 0) - 10) < 1e-9);
});

test("benchmark comparison rejects a different corpus", () => {
  const baseline = report([measurement("node", 1, 100, 10)]);
  assert.throws(
    () => compareReports(baseline, { ...baseline, corpusSha256: "different-corpus" }),
    /corpus differs/,
  );
});

test("benchmark comparison rejects a different generation index", () => {
  const baseline = {
    ...report([measurement("node", 1, 100, 10)]),
    generationSmallLemma: "lo/gos",
    generationMaximalLemma: "i(/hmi",
    generationIndexSha256: "a".repeat(64),
  };
  assert.throws(
    () => compareReports(baseline, { ...baseline, generationIndexSha256: "b".repeat(64) }),
    /generation benchmark inputs differ/,
  );
});

test("benchmark comparison requires matching native configurations", () => {
  assert.throws(
    () =>
      compareReports(
        report([measurement("node", 1, 100, 10)]),
        report([measurement("node", 2, 100, 10)]),
      ),
    /baseline lacks node with 2 contexts/,
  );
});

test("a schema 2 baseline compares the cross-runtime rows only", () => {
  const current = report([
    measurement("node", 1, 100, 10, 1000),
    measurement("cruncher-persistent", 1, 150, 6.67),
    measurement("cruncher-cold", 0, 300, 3333),
  ]);
  const baseline = denoReport([
    measurement("ffi", 1, 100, 10, 1000),
    measurement("cruncher-persistent", 1, 100, 10),
    measurement("cruncher-cold", 0, 300, 3333),
  ]);
  const { comparison, scope, baselineSchemaVersion } = compareReports(baseline, current);
  assert.equal(scope, "cross-runtime");
  assert.equal(baselineSchemaVersion, 2);
  assert.deepEqual(comparison.map((entry) => entry.engine), CROSS_RUNTIME_ENGINES);
  assert.equal(comparison[0].throughputChangePercent, 50);
});

test("a schema 1 baseline compares the cross-runtime rows only", () => {
  const { comparison, scope } = compareReports(
    legacyReport([
      measurement("ffi", 1, 100, 10),
      measurement("cruncher-persistent", 1, 100, 10),
    ]),
    report([
      measurement("node", 1, 100, 10),
      measurement("cruncher-persistent", 1, 110, 9.09),
    ]),
  );
  assert.equal(scope, "cross-runtime");
  assert.equal(comparison.length, 1);
  assert.equal(comparison[0].engine, "cruncher-persistent");
});

test("a cross-runtime comparison needs its row in both reports", () => {
  assert.throws(
    () =>
      compareReports(
        denoReport([measurement("ffi", 1, 100, 10)]),
        report([measurement("node", 1, 100, 10)]),
      ),
    /no measurement is comparable/,
  );
});

test("WebAssembly measurements absent from the baseline are skipped", () => {
  const { comparison } = compareReports(
    report([measurement("node", 1, 100, 10)]),
    report([
      measurement("node", 1, 110, 9),
      measurement("wasm-memfs", 1, 90, 11),
      measurement("wasm-nodefs-cold", 0, 20, 50),
    ]),
  );
  assert.equal(comparison.length, 1);
  assert.equal(comparison[0].engine, "node");
});

test("WebAssembly measurements present in the baseline are compared", () => {
  const { comparison } = compareReports(
    report([measurement("node", 1, 100, 10), measurement("wasm-memfs", 1, 50, 20)]),
    report([measurement("node", 1, 100, 10), measurement("wasm-memfs", 1, 100, 10)]),
  );
  const wasm = comparison.find((entry) => entry.engine === "wasm-memfs");
  assert.equal(wasm?.throughputChangePercent, 100);
});

test("WebAssembly rows delivered differently are not compared", () => {
  const counted = report([measurement("node", 1, 100, 10), measurement("wasm-memfs", 1, 50, 20)]);
  const delivered = {
    ...report([measurement("node", 1, 100, 10), measurement("wasm-memfs", 1, 40, 25)]),
    wasmResultDelivery: WASM_RESULT_DELIVERY,
  };
  const { comparison } = compareReports(counted, delivered);
  assert.deepEqual(comparison.map((entry) => entry.engine), ["node"]);
  const again = compareReports(delivered, { ...delivered });
  assert.ok(again.comparison.some((entry) => entry.engine === "wasm-memfs"));
});

test("Python rows are optional in the baseline and compared when present", () => {
  const without = report([measurement("node", 1, 100, 10)]);
  const withPython = {
    ...report([measurement("node", 1, 100, 10), measurement("python", 1, 90, 11)]),
    python: { version: "3.13.0", implementation: "CPython", binding: "0.2.1" },
  };
  assert.deepEqual(
    compareReports(without, withPython).comparison.map((entry) => entry.engine),
    ["node"],
  );
  assert.deepEqual(
    compareReports(withPython, { ...withPython }).comparison.map((entry) => entry.engine),
    ["node", "python"],
  );
});

test("the libuv thread pool size follows libuv's reading of the variable", () => {
  assert.equal(uvThreadpoolSize(undefined), 4);
  assert.equal(uvThreadpoolSize(""), 4);
  assert.equal(uvThreadpoolSize("0"), 4);
  assert.equal(uvThreadpoolSize("8"), 8);
  assert.equal(uvThreadpoolSize("4096"), 1024);
});

const sourceRevision = "1".repeat(40);
const stemlibRevision = "2".repeat(40);
const expected = {
  label: "release-candidate",
  sourceRevision,
  stemlibRevision,
  compiler: "cc 1.0",
};

/**
 * @param {string} engine
 * @param {number} contexts
 * @param {"analysis" | "generation"} [workload]
 */
function releaseMeasurement(engine, contexts, workload = "analysis") {
  const native = ["ffi", "node"].includes(engine);
  return {
    engine,
    workload,
    lemma: workload === "generation"
      ? (engine.includes("maximal") ? "i(/hmi" : "lo/gos")
      : null,
    contexts,
    operations: 10,
    durationMs: 1,
    operationsPerSecond: 10_000,
    meanMicroseconds: 100,
    startupMs: native ? 0.5 : null,
    results: workload === "generation" || native ? 10 : null,
    peakRssBytes: native ? 1024 : null,
    rssGrowthBytes: native ? 128 : null,
  };
}

/** @param {string} native */
function releaseMeasurements(native) {
  return [
    releaseMeasurement(native, 1),
    releaseMeasurement(native, 2),
    releaseMeasurement(native, 4),
    releaseMeasurement("cruncher-persistent", 1),
    releaseMeasurement("cruncher-cold", 0),
    releaseMeasurement("generation-small-warm", 1, "generation"),
    releaseMeasurement("generation-small-warm", 2, "generation"),
    releaseMeasurement("generation-small-warm", 4, "generation"),
    releaseMeasurement("generation-maximal-warm", 1, "generation"),
    releaseMeasurement("generation-maximal-warm", 2, "generation"),
    releaseMeasurement("generation-maximal-warm", 4, "generation"),
    releaseMeasurement("generation-small-cold", 0, "generation"),
    releaseMeasurement("generation-maximal-cold", 0, "generation"),
  ];
}

function releaseReport() {
  return {
    ...report(releaseMeasurements("node")),
    generatedAt: "2026-08-23T00:00:00.000Z",
    label: expected.label,
    hardwareConcurrency: 4,
    sourceRevision,
    stemlibRevision,
    compiler: expected.compiler,
    corpus: "test/fixture.json",
    corpusSha256: "a".repeat(64),
    uniqueWords: 10,
    iterations: 20,
    warmupIterations: 2,
    generationSmallLemma: "lo/gos",
    generationMaximalLemma: "i(/hmi",
    generationIndexSha256: "b".repeat(64),
  };
}

test("complete release benchmark is accepted", () => {
  validateReleaseBenchmark(releaseReport(), expected);
});

test("a retired schema 2 release benchmark is still validated", () => {
  const deno = {
    ...releaseReport(),
    schemaVersion: 2,
    runtime: { deno: "2.9.8", v8: "15.0", typescript: "6.0" },
    binding: undefined,
    measurements: releaseMeasurements("ffi"),
  };
  validateReleaseBenchmark(deno, expected);
  assert.throws(
    () => validateReleaseBenchmark({ ...deno, measurements: releaseMeasurements("node") }, expected),
    /lacks ffi:1/,
  );
});

test("a schema 3 release benchmark names the Node.js runtime and binding", () => {
  assert.throws(
    () => validateReleaseBenchmark({ ...releaseReport(), runtime: { v8: "13" } }, expected),
    /runtime\.node/,
  );
  assert.throws(
    () => validateReleaseBenchmark({ ...releaseReport(), binding: { package: "x" } }, expected),
    /binding\.version/,
  );
  assert.throws(
    () =>
      validateReleaseBenchmark(
        { ...releaseReport(), measurements: releaseMeasurements("ffi") },
        expected,
      ),
    /lacks node:1/,
  );
});

test("native rows may not outnumber the libuv thread pool", () => {
  const wide = {
    ...releaseReport(),
    measurements: [...releaseMeasurements("node"), releaseMeasurement("node", 8)],
  };
  // Reports predating the field were taken with four threads and four contexts.
  validateReleaseBenchmark(releaseReport(), expected);
  validateReleaseBenchmark({ ...wide, runtime: { ...runtime, uvThreadpoolSize: 8 } }, expected);
  assert.throws(
    () => validateReleaseBenchmark({ ...wide, runtime: { ...runtime, uvThreadpoolSize: 4 } }, expected),
    /node with 8 contexts exceeds the libuv thread pool/,
  );
  validateReleaseBenchmark(
    {
      ...releaseReport(),
      runtime: { ...runtime, uvThreadpoolSize: 4 },
      measurements: [...releaseMeasurements("node"), releaseMeasurement("wasm-memfs", 8)],
    },
    expected,
  );
  assert.throws(
    () => validateReleaseBenchmark({ ...releaseReport(), wasmResultDelivery: "batch" }, expected),
    /unknown wasmResultDelivery/,
  );
});

test("Python rows need their runtime record and escape the libuv bound", () => {
  const python = { version: "3.13.0", implementation: "CPython", binding: "0.2.1" };
  const rows = [...releaseMeasurements("node"), releaseMeasurement("python", 8)];
  validateReleaseBenchmark(
    { ...releaseReport(), runtime: { ...runtime, uvThreadpoolSize: 4 }, python, measurements: rows },
    expected,
  );
  assert.throws(
    () => validateReleaseBenchmark({ ...releaseReport(), measurements: rows }, expected),
    /Python rows require the python runtime record/,
  );
});

test("release benchmark must match the intended revision", () => {
  assert.throws(
    () =>
      validateReleaseBenchmark(
        { ...releaseReport(), sourceRevision: "3".repeat(40) },
        expected,
      ),
    /sourceRevision does not match/,
  );
});

test("release benchmark requires all execution models", () => {
  assert.throws(
    () =>
      validateReleaseBenchmark(
        { ...releaseReport(), measurements: releaseReport().measurements.slice(0, 3) },
        expected,
      ),
    /lacks cruncher-persistent:1/,
  );
});

test("validator command line takes the four release inputs", () => {
  const parsed = parseCommandLine([
    "report.json",
    "--label", "release-candidate",
    "--revision", sourceRevision,
    "--stemlib-revision", stemlibRevision,
    "--compiler", "cc 1.0",
  ]);
  assert.equal(parsed.reportPath, "report.json");
  assert.deepEqual(parsed.expected, expected);
  assert.throws(() => parseCommandLine(["report.json", "--label"]), /name-value pairs/);
  assert.throws(() => parseCommandLine(["--label", "x"]), /usage/);
  assert.throws(
    () => parseCommandLine(["report.json", "--label", "x", "--label", "y"]),
    /duplicate option/,
  );
});
