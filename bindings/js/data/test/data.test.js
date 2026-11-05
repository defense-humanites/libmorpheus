// SPDX-License-Identifier: AGPL-3.0-or-later

import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { gzipSync } from "node:zlib";

import {
  acquireMorpheusDataWithDependencies,
  MANIFEST_FILE,
  RECEIPT_FILE,
  selectFiles,
  sha256,
} from "../internal/data-internal.js";
import { isRuntimeFile, selectLanguages } from "../internal/runtime-subset.js";
import { MORPHEUS_DATASETS, parseMorpheusDataArgs } from "../data.js";

function writeString(buffer, offset, length, value) {
  buffer.write(value, offset, Math.min(length, Buffer.byteLength(value)), "ascii");
}

function tarEntry(path, content = Buffer.alloc(0), type = "0") {
  const header = Buffer.alloc(512);
  writeString(header, 0, 100, path);
  writeString(header, 100, 8, "0000644\0");
  writeString(header, 108, 8, "0000000\0");
  writeString(header, 116, 8, "0000000\0");
  writeString(header, 124, 12, `${content.length.toString(8).padStart(11, "0")}\0`);
  writeString(header, 136, 12, "00000000000\0");
  header.fill(0x20, 148, 156);
  writeString(header, 156, 1, type);
  writeString(header, 257, 6, "ustar\0");
  writeString(header, 263, 2, "00");
  const checksum = header.reduce((sum, byte) => sum + byte, 0);
  writeString(header, 148, 8, `${checksum.toString(8).padStart(6, "0")}\0 `);
  return Buffer.concat([header, content, Buffer.alloc((512 - content.length % 512) % 512)]);
}

const FIXTURE_FILES = [
  ["Greek/steminds/nomind", "greek nomind\n"],
  ["Greek/steminds/nomind.lindex", "greek lindex\n"],
  ["Greek/rule_files/stemtypes.table", "greek stemtypes\n"],
  ["Greek/endtables/out/os_ou.out", "greek endtable\n"],
  ["Greek/stemsrc/nom01", "greek source, not read at run time\n"],
  ["Greek/stemsrc/lemlist", "greek lemlist\n"],
  ["Greek/makefile", "all:\n"],
  ["Latin/steminds/nomind", "latin nomind\n"],
  ["Latin/rule_files/stemtypes.table", "latin stemtypes\n"],
  ["Latin/stemsrc/ls.nom", "latin source\n"],
];

function fixture(languages = ["grc", "lat"]) {
  const license = Buffer.from("fixture license\n");
  const entries = FIXTURE_FILES.map(([path, text]) => [path, Buffer.from(text)]);
  const archive = Buffer.concat([
    tarEntry("fixture/LICENSE", license),
    tarEntry("fixture/stemlib/", Buffer.alloc(0), "5"),
    ...entries.map(([path, content]) => tarEntry(`fixture/stemlib/${path}`, content)),
    Buffer.alloc(1024),
  ]);
  const lines = entries
    .map(([path, content]) => `${sha256(content)}  ${path}`)
    .sort((left, right) => (left.slice(66) < right.slice(66) ? -1 : 1));
  const definition = {
    name: "perseids",
    repository: "https://example.invalid/source",
    revision: "fixture-revision",
    archiveUrl: "https://example.invalid/archive.tar.gz",
    archiveRoot: "fixture/",
    dataPrefix: "stemlib/",
    fileCount: entries.length,
    treeSha256: sha256(new TextEncoder().encode(`${lines.join("\n")}\n`)),
    licensePath: "LICENSE",
    licenseSha256: sha256(license),
    languages,
    generation: false,
  };
  return { compressed: gzipSync(archive), definition, entries };
}

async function withOutput(name, body) {
  await mkdir(tmpdir(), { recursive: true });
  const parent = await mkdtemp(join(tmpdir(), `libmorpheus-data-${name}-`));
  try {
    await body(join(parent, "data"));
  } finally {
    await rm(parent, { recursive: true, force: true });
  }
}

async function listFiles(directory, prefix = "") {
  const names = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = `${prefix}${entry.name}`;
    if (entry.isDirectory()) names.push(...await listFiles(join(directory, entry.name), `${path}/`));
    else names.push(path);
  }
  return names.sort();
}

test("the full subset writes the verified tree, its license and a receipt", async () => {
  await withOutput("full", async (output) => {
    const { compressed, definition, entries } = fixture();
    const receipt = await acquireMorpheusDataWithDependencies(
      { dataset: "perseids", output },
      { datasets: { perseids: definition }, fetch: async () => new Response(compressed) },
    );
    assert.equal(receipt.files.count, entries.length);
    assert.deepEqual(receipt.languages, ["grc", "lat"]);
    assert.deepEqual(receipt.subset, { name: "full", count: entries.length, treeSha256: definition.treeSha256 });
    assert.equal(receipt.manifest, null);
    assert.equal(receipt.generation.available, false);
    assert.equal(await readFile(join(output, "Greek/steminds/nomind"), "utf8"), "greek nomind\n");
    assert.equal(await readFile(join(output, "UPSTREAM-LICENSE"), "utf8"), "fixture license\n");
    assert.deepEqual(
      await listFiles(output),
      [RECEIPT_FILE, "UPSTREAM-LICENSE", ...entries.map(([path]) => path)].sort(),
    );
    assert.deepEqual(JSON.parse(await readFile(join(output, RECEIPT_FILE), "utf8")), receipt);
  });
});

test("the runtime subset keeps only what the runtime reads, for the selected languages", async () => {
  await withOutput("runtime", async (output) => {
    const { compressed, definition } = fixture();
    const receipt = await acquireMorpheusDataWithDependencies(
      { dataset: "perseids", output, subset: "runtime", languages: ["grc"], manifest: true },
      { datasets: { perseids: definition }, fetch: async () => new Response(compressed) },
    );
    const expected = [
      "Greek/endtables/out/os_ou.out",
      "Greek/rule_files/stemtypes.table",
      "Greek/steminds/nomind",
      "Greek/steminds/nomind.lindex",
      "Greek/stemsrc/lemlist",
    ];
    assert.deepEqual(receipt.languages, ["grc"]);
    assert.equal(receipt.subset.name, "runtime");
    assert.equal(receipt.subset.count, expected.length);
    assert.notEqual(receipt.subset.treeSha256, definition.treeSha256);
    assert.equal(receipt.manifest, MANIFEST_FILE);
    assert.deepEqual(await listFiles(output), [MANIFEST_FILE, RECEIPT_FILE, "UPSTREAM-LICENSE", ...expected].sort());
    const manifest = JSON.parse(await readFile(join(output, MANIFEST_FILE), "utf8"));
    assert.equal(manifest.schema, 1);
    assert.equal(manifest.dataset, "perseids");
    assert.equal(manifest.revision, "fixture-revision");
    assert.equal(manifest.subset, "runtime");
    assert.deepEqual(manifest.languages, ["grc"]);
    assert.deepEqual(manifest.files.map((entry) => entry.path), expected);
    for (const entry of manifest.files) {
      const content = await readFile(join(output, ...entry.path.split("/")));
      assert.equal(entry.size, content.length, entry.path);
      assert.equal(entry.sha256, sha256(content), entry.path);
    }
  });
});

test("the runtime subset of a dataset is what the WebAssembly facade validates and reads", () => {
  const required = [
    "rule_files/vowcontr.table", "rule_files/conseuph.table", "rule_files/stemtypes.table",
    "rule_files/derivtypes.table", "rule_files/domainlist.table", "rule_files/raw_preverbs.table",
    "rule_files/ppasslist.table", "steminds/nomind", "steminds/nomind.lindex", "steminds/vbind",
    "steminds/vbind.lindex", "endtables/indices/nendind", "endtables/indices/vbendind",
    "derivs/indices/derivind", "endtables/out/aor1.out", "stemsrc/vbs.cmp.ml", "stemsrc/lemlist",
  ];
  for (const path of required) {
    assert.equal(isRuntimeFile(`Greek/${path}`, ["grc"]), true, path);
    assert.equal(isRuntimeFile(`Latin/${path}`, ["lat"]), true, path);
    assert.equal(isRuntimeFile(`Latin/${path}`, ["grc"]), false, path);
  }
  assert.equal(isRuntimeFile("gener.index", ["grc"]), true);
  for (const path of ["Greek/stemsrc/nom01", "Greek/makefile", "Greek/steminds/indexnoms", "Greek/stemsrc/lsj.nom", "README"]) {
    assert.equal(isRuntimeFile(path, ["grc", "lat"]), false, path);
  }
  const files = new Map([["Greek/steminds/nomind", Buffer.alloc(1)], ["Greek/stemsrc/nom01", Buffer.alloc(1)]]);
  assert.deepEqual([...selectFiles(files, "runtime", ["grc"]).keys()], ["Greek/steminds/nomind"]);
  assert.deepEqual([...selectFiles(files, "full", ["grc"]).keys()], [...files.keys()]);
  assert.throws(() => selectFiles(files, "partial", ["grc"]), TypeError);
});

test("language selection validates against the dataset", () => {
  assert.deepEqual(selectLanguages(undefined, ["grc", "lat"]), ["grc", "lat"]);
  assert.deepEqual(selectLanguages(["lat", "grc", "lat"], ["grc", "lat"]), ["grc", "lat"]);
  assert.deepEqual(selectLanguages(["lat"], ["grc", "lat"]), ["lat"]);
  assert.throws(() => selectLanguages([], ["grc"]), /at least one/);
  assert.throws(() => selectLanguages(["xyz"], ["grc"]), /unknown language/);
  assert.throws(() => selectLanguages(["lat"], ["grc"]), /not in this dataset/);
});

test("a failed acquisition leaves no output behind", async () => {
  await withOutput("failure", async (output) => {
    const { compressed, definition } = fixture();
    await assert.rejects(
      acquireMorpheusDataWithDependencies(
        { dataset: "perseids", output },
        { datasets: { perseids: { ...definition, fileCount: definition.fileCount + 1 } }, fetch: async () => new Response(compressed) },
      ),
      /expected 11/,
    );
    await assert.rejects(readdir(output), { code: "ENOENT" });
  });
});

test("data CLI selects only pinned supported datasets and valid subsets", () => {
  assert.deepEqual(
    parseMorpheusDataArgs(["--dataset", "perseids", "--output", "out"]),
    { dataset: "perseids", output: "out", subset: "full", languages: undefined, withGener: false, manifest: false, help: false },
  );
  assert.deepEqual(
    parseMorpheusDataArgs(["--dataset=alpheios", "--output=out", "--subset=runtime", "--with-gener", "--manifest"]),
    { dataset: "alpheios", output: "out", subset: "runtime", languages: undefined, withGener: true, manifest: true, help: false },
  );
  assert.deepEqual(
    parseMorpheusDataArgs(["--dataset", "perseids", "--output", "out", "--languages", "lat"]).languages,
    ["lat"],
  );
  assert.equal(parseMorpheusDataArgs(["--help"]).help, true);
  assert.throws(() => parseMorpheusDataArgs(["--output", "out"]), /--dataset is required/);
  assert.throws(() => parseMorpheusDataArgs(["--dataset", "other", "--output", "out"]), /unsupported dataset/);
  assert.throws(() => parseMorpheusDataArgs(["--dataset", "perseids"]), /--output is required/);
  assert.throws(() => parseMorpheusDataArgs(["--dataset", "perseids", "--output", "out", "--subset", "half"]), /unsupported subset/);
  assert.throws(() => parseMorpheusDataArgs(["--dataset", "alpheios", "--output", "out", "--languages", "lat"]), /not in the alpheios dataset/);
  assert.throws(() => parseMorpheusDataArgs(["--dataset", "perseids", "--output", "out", "--with-gener"]), /only for alpheios/);
  assert.throws(() => parseMorpheusDataArgs(["--dataset", "perseids", "--output", "out", "--bogus"]), /unknown argument/);
  assert.deepEqual(Object.keys(MORPHEUS_DATASETS).sort(), ["alpheios", "perseids"]);
  for (const definition of Object.values(MORPHEUS_DATASETS)) {
    assert.match(definition.revision, /^[0-9a-f]{40}$/);
    assert.match(definition.treeSha256, /^[0-9a-f]{64}$/);
    assert.match(definition.licenseSha256, /^[0-9a-f]{64}$/);
    assert.match(definition.archiveUrl, /^https:\/\/codeload\.github\.com\//);
  }
});
