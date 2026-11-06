// SPDX-License-Identifier: AGPL-3.0-or-later

import { realpathSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

/**
 * Whether `moduleUrl` is the module Node.js was started with, for runtimes
 * without `import.meta.main`. Symbolic links to the script are resolved.
 *
 * @param {string} moduleUrl
 * @param {string | undefined} [executablePath]
 */
export function isMainModule(moduleUrl, executablePath = process.argv[1]) {
  if (executablePath === undefined) return false;
  try {
    return realpathSync(executablePath) === realpathSync(fileURLToPath(moduleUrl));
  } catch {
    return moduleUrl === pathToFileURL(executablePath).href;
  }
}
