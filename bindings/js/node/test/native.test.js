// SPDX-License-Identifier: AGPL-3.0-or-later

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { access, mkdir, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { gzipSync } from "node:zlib";

import { acquireMorpheusNativeWithDependencies } from "../internal/native-internal.js";
import { MORPHEUS_NATIVE_VERSION } from "../internal/native-manifest.js";
import { parseMorpheusNativeArgs } from "../native.js";

function writeString(buffer, offset, length, value) {
  buffer.write(value, offset, Math.min(length, Buffer.byteLength(value)), "ascii");
}

function tarEntry(path, content = Buffer.alloc(0), type = "0", linkPath = "") {
  const header = Buffer.alloc(512);
  writeString(header, 0, 100, path);
  writeString(header, 100, 8, "0000755\0");
  writeString(header, 108, 8, "0000000\0");
  writeString(header, 116, 8, "0000000\0");
  writeString(header, 124, 12, `${content.length.toString(8).padStart(11, "0")}\0`);
  writeString(header, 136, 12, "00000000000\0");
  header.fill(0x20, 148, 156);
  writeString(header, 156, 1, type);
  writeString(header, 157, 100, linkPath);
  writeString(header, 257, 6, "ustar\0");
  writeString(header, 263, 2, "00");
  const checksum = header.reduce((sum, byte) => sum + byte, 0);
  writeString(header, 148, 8, `${checksum.toString(8).padStart(6, "0")}\0 `);
  const padding = Buffer.alloc((512 - content.length % 512) % 512);
  return Buffer.concat([header, content, padding]);
}

function nativeArchive() {
  const root = `libmorpheus-${MORPHEUS_NATIVE_VERSION}-Linux-x86_64-glibc/`;
  return Buffer.concat([
    tarEntry(root, Buffer.alloc(0), "5"),
    tarEntry(`${root}lib/`, Buffer.alloc(0), "5"),
    tarEntry(`${root}lib/libmorpheus.so.${MORPHEUS_NATIVE_VERSION}`, Buffer.from("native fixture")),
    tarEntry(`${root}lib/libmorpheus.so`, Buffer.alloc(0), "2", `libmorpheus.so.${MORPHEUS_NATIVE_VERSION}`),
    Buffer.alloc(1024),
  ]);
}

function dependencies(compressed, sidecar) {
  return {
    platform: "linux",
    arch: "x64",
    glibcVersion: "2.39",
    fetch: async (url) => new Response(url.endsWith(".sha256") ? sidecar : compressed),
  };
}

test("native acquisition verifies, extracts, materializes links, and records provenance", async () => {
  await mkdir(tmpdir(), { recursive: true });
  const parent = await mkdtemp(join(tmpdir(), "libmorpheus-node-native-"));
  const output = join(parent, "runtime");
  try {
    const compressed = gzipSync(nativeArchive());
    const digest = createHash("sha256").update(compressed).digest("hex");
    const asset = `libmorpheus-${MORPHEUS_NATIVE_VERSION}-Linux-x86_64-glibc.tar.gz`;
    const receipt = await acquireMorpheusNativeWithDependencies(
      { output },
      dependencies(compressed, Buffer.from(`${digest}  ${asset}\n`)),
    );
    assert.equal(receipt.archiveSha256, digest);
    assert.equal(receipt.abiVersion, 2);
    assert.equal(await readFile(join(output, "lib/libmorpheus.so"), "utf8"), "native fixture");
    assert.deepEqual(
      JSON.parse(await readFile(join(output, "MORPHEUS-NATIVE.json"), "utf8")),
      receipt,
    );
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("native acquisition rolls back a checksum mismatch", async () => {
  await mkdir(tmpdir(), { recursive: true });
  const parent = await mkdtemp(join(tmpdir(), "libmorpheus-node-native-"));
  const output = join(parent, "runtime");
  try {
    const compressed = gzipSync(nativeArchive());
    const asset = `libmorpheus-${MORPHEUS_NATIVE_VERSION}-Linux-x86_64-glibc.tar.gz`;
    await assert.rejects(
      acquireMorpheusNativeWithDependencies(
        { output },
        dependencies(compressed, Buffer.from(`${"0".repeat(64)}  ${asset}\n`)),
      ),
      /checksum mismatch/,
    );
    await assert.rejects(access(output), { code: "ENOENT" });
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
});

test("native CLI parsing requires an explicit output", () => {
  assert.deepEqual(parseMorpheusNativeArgs(["--output", "runtime"]), {
    output: "runtime",
    help: false,
  });
  assert.throws(() => parseMorpheusNativeArgs([]), /--output is required/);
});
