#!/usr/bin/env node
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The data acquisition command and library now live in @libmorpheus/data,
// which this package depends on. This module keeps the `libmorpheus-data`
// command and the `@libmorpheus/node/data` export working unchanged.

import { acquireMorpheusData, parseMorpheusDataArgs } from "@libmorpheus/data";
import { isMainModule } from "./internal/main-module.js";

export { acquireMorpheusData, parseMorpheusDataArgs };

if (import.meta.main ?? isMainModule(import.meta.url)) {
  // Re-dispatch to the package's own command so that --help and errors
  // read the same whichever entry point ran.
  const { fileURLToPath } = await import("node:url");
  const { spawnSync } = await import("node:child_process");
  const command = fileURLToPath(import.meta.resolve("@libmorpheus/data"));
  const result = spawnSync(process.execPath, [command, ...process.argv.slice(2)], { stdio: "inherit" });
  process.exitCode = result.status ?? 1;
}
