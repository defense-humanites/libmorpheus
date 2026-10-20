// SPDX-License-Identifier: AGPL-3.0-or-later

import {
  type LegacyBenchmarkReport,
  type BenchmarkReport,
  compareReports,
  type Measurement,
} from "./compare.ts";

function measurement(
  engine: string,
  contexts: number,
  operationsPerSecond: number,
  meanMicroseconds: number,
  peakRssBytes: number | null = null,
): Measurement {
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

function legacyReport(
  measurements: readonly Measurement[],
): LegacyBenchmarkReport {
  return {
    schemaVersion: 1,
    corpusSha256: "same-corpus",
    measurements,
  };
}

function report(measurements: readonly Measurement[]): BenchmarkReport {
  return {
    schemaVersion: 2,
    generatedAt: "2026-01-01T00:00:00.000Z",
    label: null,
    platform: Deno.build,
    runtime: Deno.version,
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

Deno.test("benchmark reports compare normalized measurements", () => {
  const comparison = compareReports(
    report([measurement("ffi", 1, 100, 10, 1000)]),
    report([measurement("ffi", 1, 125, 8, 1100)]),
  );
  if (comparison.length !== 1) throw new Error("missing comparison");
  if (comparison[0].throughputChangePercent !== 25) {
    throw new Error("incorrect throughput change");
  }
  if (Math.abs(comparison[0].meanLatencyChangePercent + 20) > 1e-9) {
    throw new Error("incorrect latency change");
  }
  if (Math.abs((comparison[0].peakRssChangePercent ?? 0) - 10) > 1e-9) {
    throw new Error("incorrect RSS change");
  }
});

Deno.test("benchmark comparison rejects a different corpus", () => {
  const baseline = report([measurement("ffi", 1, 100, 10)]);
  const current = { ...baseline, corpusSha256: "different-corpus" };
  let rejected = false;
  try {
    compareReports(baseline, current);
  } catch {
    rejected = true;
  }
  if (!rejected) throw new Error("different corpus was accepted");
});

Deno.test("benchmark comparison rejects a different generation index", () => {
  const baseline = {
    ...report([measurement("ffi", 1, 100, 10)]),
    generationSmallLemma: "lo/gos",
    generationMaximalLemma: "i(/hmi",
    generationIndexSha256: "a".repeat(64),
  };
  const current = { ...baseline, generationIndexSha256: "b".repeat(64) };
  let rejected = false;
  try {
    compareReports(baseline, current);
  } catch {
    rejected = true;
  }
  if (!rejected) throw new Error("different generation index was accepted");
});

Deno.test("benchmark comparison requires matching engine configurations", () => {
  let rejected = false;
  try {
    compareReports(
      report([measurement("ffi", 1, 100, 10)]),
      report([measurement("ffi", 2, 100, 10)]),
    );
  } catch {
    rejected = true;
  }
  if (!rejected) throw new Error("missing baseline measurement was accepted");
});

Deno.test("schema 1 baseline compares historical analysis only", () => {
  const analysis = measurement("ffi", 1, 100, 10, 1000);
  const generation = {
    ...measurement("generation-small-warm", 1, 50, 20, 1200),
    workload: "generation" as const,
    lemma: "lo/gos",
    results: 18,
  };
  const current = {
    ...report([analysis, generation]),
    generationSmallLemma: "lo/gos",
    generationMaximalLemma: "i(/hmi",
    generationIndexSha256: "a".repeat(64),
  };
  const comparison = compareReports(legacyReport([analysis]), current);
  if (comparison.length !== 1 || comparison[0].engine !== "ffi") {
    throw new Error("legacy comparison included non-historical measurements");
  }
});

Deno.test("schema 1 baseline requires every historical configuration", () => {
  let rejected = false;
  try {
    compareReports(
      legacyReport([measurement("ffi", 4, 100, 10)]),
      report([measurement("ffi", 1, 100, 10)]),
    );
  } catch {
    rejected = true;
  }
  if (!rejected) throw new Error("missing historical configuration was accepted");
});

Deno.test("WebAssembly measurements absent from the baseline are skipped", () => {
  const comparison = compareReports(
    report([measurement("ffi", 1, 100, 10)]),
    report([
      measurement("ffi", 1, 110, 9),
      measurement("wasm-memfs", 1, 90, 11),
      measurement("wasm-nodefs-cold", 0, 20, 50),
    ]),
  );
  if (comparison.length !== 1 || comparison[0].engine !== "ffi") {
    throw new Error("optional WebAssembly measurements were not skipped");
  }
});

Deno.test("WebAssembly measurements present in the baseline are compared", () => {
  const comparison = compareReports(
    report([measurement("ffi", 1, 100, 10), measurement("wasm-memfs", 1, 50, 20)]),
    report([measurement("ffi", 1, 100, 10), measurement("wasm-memfs", 1, 100, 10)]),
  );
  const wasm = comparison.find((entry) => entry.engine === "wasm-memfs");
  if (!wasm || wasm.throughputChangePercent !== 100) {
    throw new Error("WebAssembly measurement was not compared");
  }
});
