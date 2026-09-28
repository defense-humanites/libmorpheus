// SPDX-License-Identifier: AGPL-3.0-or-later

import { parseMorpheusSetupArgs } from "../setup.ts";
import {
  type MorpheusSetupDependencies,
  setupMorpheusWithDependencies,
} from "../internal/setup_internal.ts";
import { MORPHEUS_DENO_VERSION, MORPHEUS_NATIVE_VERSION } from "../internal/version.ts";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function assertThrows(callback: () => unknown, pattern: RegExp): void {
  try {
    callback();
  } catch (error) {
    assert(error instanceof Error, "non-Error exception");
    assert(pattern.test(error.message), `unexpected error: ${error.message}`);
    return;
  }
  throw new Error("expected callback to throw");
}

async function assertRejects(
  callback: () => Promise<unknown>,
  pattern: RegExp,
): Promise<void> {
  try {
    await callback();
  } catch (error) {
    assert(error instanceof Error, "non-Error rejection");
    assert(pattern.test(error.message), `unexpected error: ${error.message}`);
    return;
  }
  throw new Error("expected promise to reject");
}

function dependencies(events: string[]): MorpheusSetupDependencies {
  return {
    pathExists: async (path) => {
      events.push(`exists:${path}`);
      return false;
    },
    remove: async (path) => {
      events.push(`remove:${path}`);
    },
    acquireNative: async (options) => {
      events.push(`native:${options.output}`);
      return {
        schema: 2,
        packageVersion: MORPHEUS_DENO_VERSION,
        nativeVersion: MORPHEUS_NATIVE_VERSION,
        abiVersion: 2,
        target: "linux-x86_64-glibc",
        asset: "native.tar.gz",
        archiveSha256: "0".repeat(64),
        sourceUrl: "https://example.invalid/native.tar.gz",
        libraryPath: "lib/libmorpheus.so",
      };
    },
    acquireData: async (options) => {
      events.push(`data:${options.dataset}:${options.output}`);
      return {
        schema: 1,
        packageVersion: MORPHEUS_DENO_VERSION,
        dataset: options.dataset,
        languages: ["grc"],
        source: {
          repository: "https://example.invalid/data",
          revision: "fixture",
          archiveUrl: "https://example.invalid/data.tar.gz",
        },
        files: { count: 1, treeSha256: "0".repeat(64) },
        generation: {
          experimental: true,
          available: options.withGener ?? false,
          indexSha256: null,
          supportSource: null,
        },
      };
    },
  };
}

Deno.test("setup CLI parses combined installation options", () => {
  const options = parseMorpheusSetupArgs([
    "--dataset=alpheios",
    "--with-gener",
    "--native-output",
    "./native",
    "--data-output=./data",
  ]);
  assert(options.dataset === "alpheios", "dataset was not parsed");
  assert(options.withGener === true, "generation flag was not parsed");
  assert(options.nativeOutput === "./native", "native output was not parsed");
  assert(options.dataOutput === "./data", "data output was not parsed");
});

Deno.test("setup CLI rejects unsupported combinations", () => {
  assertThrows(() => parseMorpheusSetupArgs([]), /--dataset is required/);
  assertThrows(
    () => parseMorpheusSetupArgs(["--dataset", "perseids", "--with-gener"]),
    /only with alpheios/,
  );
});

Deno.test("setup installs native and data after preflight", async () => {
  const events: string[] = [];
  const receipt = await setupMorpheusWithDependencies(
    {
      dataset: "alpheios",
      withGener: true,
      nativeOutput: "./native",
      dataOutput: "./data",
    },
    dependencies(events),
  );
  assert(events.length === 4, `unexpected events: ${events.join(",")}`);
  assert(events[2].startsWith("native:"), "native acquisition was not first");
  assert(events[3].startsWith("data:alpheios:"), "data was not acquired");
  assert(
    receipt.nativeLibraryPath.endsWith("lib/libmorpheus.so"),
    "native library path was not resolved",
  );
});

Deno.test("setup rolls back native output after data failure", async () => {
  const events: string[] = [];
  const base = dependencies(events);
  await assertRejects(
    () =>
      setupMorpheusWithDependencies(
        { dataset: "alpheios", nativeOutput: "./native" },
        {
          ...base,
          acquireData: () => Promise.reject(new Error("data failed")),
        },
      ),
    /data failed/,
  );
  assert(events.some((event) => event.startsWith("remove:")), "no rollback");
});

Deno.test("setup refuses existing outputs before acquisition", async () => {
  const events: string[] = [];
  const base = dependencies(events);
  await assertRejects(
    () =>
      setupMorpheusWithDependencies(
        { dataset: "perseids" },
        { ...base, pathExists: () => Promise.resolve(true) },
      ),
    /output path already exists/,
  );
  assert(!events.some((event) => event.startsWith("native:")), "native ran");
  assert(!events.some((event) => event.startsWith("data:")), "data ran");
});

Deno.test("setup rejects overlapping output directories", async () => {
  await assertRejects(
    () =>
      setupMorpheusWithDependencies(
        {
          dataset: "alpheios",
          nativeOutput: "./runtime",
          dataOutput: "./runtime/data",
        },
        dependencies([]),
      ),
    /non-overlapping directories/,
  );
});
