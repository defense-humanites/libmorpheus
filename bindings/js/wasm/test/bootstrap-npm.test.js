// SPDX-License-Identifier: AGPL-3.0-or-later

import assert from "node:assert/strict";
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { packageName, stageNpmBootstrapPackage } from "../tools/bootstrap-npm.mjs";

test("stages an inert bootstrap version of the WebAssembly package", async () => {
  const parent = await mkdtemp(join(tmpdir(), "libmorpheus-wasm-bootstrap-"));
  const output = join(parent, "package");
  try {
    const staged = await stageNpmBootstrapPackage(output);
    assert.equal(staged.name, packageName);
    assert.equal(staged.version, "0.0.0");
    const metadata = JSON.parse(await readFile(join(output, "package.json"), "utf8"));
    assert.equal(metadata.name, "@libmorpheus/wasm");
    assert.equal(metadata.version, "0.0.0");
    assert.equal(metadata.license, "AGPL-3.0-or-later");
    assert.deepEqual(metadata.publishConfig, { access: "public" });
    assert.deepEqual(metadata.files, ["LICENSE", "NOTICE", "README.md"]);
    assert.equal(metadata.main, undefined);
    assert.equal(metadata.exports, undefined);
    assert.deepEqual(
      (await readdir(output)).sort(),
      ["LICENSE", "NOTICE", "README.md", "package.json"],
    );
    assert.match(await readFile(join(output, "README.md"), "utf8"), /no WebAssembly module/);
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("refuses to overwrite an existing output directory", async () => {
  const parent = await mkdtemp(join(tmpdir(), "libmorpheus-wasm-bootstrap-"));
  try {
    await stageNpmBootstrapPackage(parent);
    assert.fail("existing directory was accepted");
  } catch (error) {
    assert.equal(error.code, "EEXIST");
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});
