// SPDX-License-Identifier: AGPL-3.0-or-later

import assert from "node:assert/strict";
import { mkdir, mkdtemp, realpath, rm, symlink } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { isMainModule } from "../internal/main-module.js";

test("recognizes a main module invoked through an npm bin symlink", async () => {
  const source = fileURLToPath(new URL("../data.js", import.meta.url));
  await mkdir(tmpdir(), { recursive: true });
  const parent = await mkdtemp(join(tmpdir(), "libmorpheus-data-main-"));
  const executable = join(parent, "libmorpheus-data");
  try {
    await symlink(await realpath(source), executable);
    assert.equal(isMainModule(pathToFileURL(source).href, executable), true);
    assert.equal(
      isMainModule(pathToFileURL(join(dirname(source), basename(executable))).href, executable),
      false,
    );
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});
