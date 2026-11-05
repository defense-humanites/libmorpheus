// SPDX-License-Identifier: AGPL-3.0-or-later

import { realpathSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

export function isMainModule(moduleUrl, executablePath = process.argv[1]) {
  if (executablePath === undefined) return false;
  try {
    return realpathSync(executablePath) === realpathSync(fileURLToPath(moduleUrl));
  } catch {
    return moduleUrl === pathToFileURL(executablePath).href;
  }
}
