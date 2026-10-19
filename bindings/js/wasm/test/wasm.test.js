// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Smoke tests for the WebAssembly facade. They need a built module and a
// stemlib checkout:
//
//   MORPHEUS_WASM_MODULE=build/wasm/wasm/morpheus.mjs \
//   MORPHEUS_STEMLIB=stemlib node --test bindings/js/wasm/test/*.test.js
//
// MORPHEUS_GENER_STEMLIB may name a prepared Greek directory holding
// gener.index to exercise generation as well.

import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import process from "node:process";
import test from "node:test";

import {
  ABI_VERSION,
  Morpheus,
  MorpheusCompatFlag,
  MorpheusError,
  MorpheusLanguage,
  MorpheusOption,
  MorpheusStatus,
  createMorpheus,
} from "../index.mjs";

const moduleUrl = pathToFileURL(
  resolve(process.env.MORPHEUS_WASM_MODULE ?? "build/wasm/wasm/morpheus.mjs"),
);
const stemlibRoot = resolve(process.env.MORPHEUS_STEMLIB ?? "stemlib");
const generationRoot = process.env.MORPHEUS_GENER_STEMLIB
  ? resolve(process.env.MORPHEUS_GENER_STEMLIB)
  : null;

function listFiles(directory) {
  const files = [];
  const walk = (current) => {
    for (const entry of readdirSync(current)) {
      const path = join(current, entry);
      if (statSync(path).isDirectory()) walk(path);
      else files.push(path);
    }
  };
  walk(directory);
  return files;
}

test("module reports the expected ABI and layouts", async () => {
  const morpheus = await createMorpheus({ moduleUrl });
  assert.equal(morpheus.abiVersion, ABI_VERSION);
  assert.match(morpheus.version, /^\d+\.\d+\.\d+/);
  assert.equal(morpheus.statusMessage(MorpheusStatus.Ok).length > 0, true);
});

test("Latin analysis over a mounted host directory", async () => {
  const morpheus = await createMorpheus({ moduleUrl });
  const root = morpheus.mountDirectory(stemlibRoot);
  const context = morpheus.open({ stemlib: root, language: MorpheusLanguage.Latin });
  try {
    const analyses = context.analyze("amavimus");
    assert.equal(analyses.length, 1);
    assert.equal(analyses[0].lemma, "amo");
    assert.equal(analyses[0].structSize, 852);
    assert.equal(analyses[0].truncatedFields, 0);
    assert.ok(analyses[0].morphFlags instanceof Uint8Array);

    const none = context.analyze("xyzzyq");
    assert.deepEqual(none, []);

    const compat = context.analyzeCompat(
      "lupus",
      MorpheusCompatFlag.PerseusFormat | MorpheusCompatFlag.StrictCase,
    );
    assert.equal(compat.analysisCount, 1);
    assert.match(compat.text, /lupus/);
  } finally {
    context.close();
  }
  assert.equal(context.closed, true);
  assert.throws(() => context.analyze("lupus"), MorpheusError);
});

test("Greek analysis with option object and dialect filter", async () => {
  const morpheus = await createMorpheus({ moduleUrl });
  const root = morpheus.mountDirectory(stemlibRoot);
  const context = morpheus.open({ stemlib: root, language: MorpheusLanguage.Greek });
  try {
    const strict = context.analyze("e)/dwken", { strictCase: true });
    assert.equal(strict.length, 1);
    assert.equal(strict[0].lemma, "di/dwmi");
    const viaMask = context.analyze("e)/dwken", MorpheusOption.StrictCase);
    assert.deepEqual(viaMask, strict);
    const attic = context.analyze("lo/gos", { dialects: ["Attic"] });
    assert.equal(attic.length >= 1, true);
    assert.equal(attic[0].lemma, "lo/gos");
  } finally {
    context.close();
  }
});

test("in-memory stemlib written from host bytes", async () => {
  const morpheus = await createMorpheus({ moduleUrl });
  const latinDirectory = join(stemlibRoot, "Latin");
  const entries = listFiles(latinDirectory)
    .filter((path) =>
      /\/(rule_files|steminds|endtables\/(indices|out)|derivs\/indices)\//.test(path) ||
      /\/stemsrc\/(vbs\.cmp\.ml|lemlist)$/.test(path)
    )
    .map((path) => [`Latin/${relative(latinDirectory, path)}`, readFileSync(path)]);
  const root = morpheus.writeStemlib(entries, "/memory-stemlib");
  for (const required of Morpheus.requiredFiles(MorpheusLanguage.Latin)) {
    assert.equal(morpheus.fs.analyzePath(`${root}/${required}`).exists, true, required);
  }
  const context = morpheus.open({ stemlib: root, language: MorpheusLanguage.Latin });
  try {
    assert.equal(context.analyze("rosarum")[0].lemma, "rosa");
  } finally {
    context.close();
  }
});

test("opening an incomplete stemlib reports MORPHEUS_STEMLIB_ERROR", async () => {
  const morpheus = await createMorpheus({ moduleUrl });
  morpheus.writeStemlib({ "Latin/rule_files/stemtypes.table": "x" }, "/partial");
  assert.throws(
    () => morpheus.open({ stemlib: "/partial", language: MorpheusLanguage.Latin }),
    (error) => error instanceof MorpheusError && error.status === MorpheusStatus.StemlibError,
  );
});

test("independent contexts in one module do not interfere", async () => {
  const morpheus = await createMorpheus({ moduleUrl });
  const root = morpheus.mountDirectory(stemlibRoot);
  const greek = morpheus.open({ stemlib: root, language: MorpheusLanguage.Greek });
  const latin = morpheus.open({ stemlib: root, language: MorpheusLanguage.Latin });
  try {
    for (let round = 0; round < 3; round++) {
      assert.equal(greek.analyze("lo/gos")[0].lemma, "lo/gos");
      assert.equal(latin.analyze("lupus")[0].lemma, "lupus#1");
    }
  } finally {
    morpheus.closeAll();
  }
  assert.equal(greek.closed && latin.closed, true);
});

test(
  "Greek generation from a prepared gener.index",
  { skip: generationRoot ? false : "MORPHEUS_GENER_STEMLIB is not set" },
  async () => {
    const morpheus = await createMorpheus({ moduleUrl });
    const root = morpheus.mountDirectory(generationRoot);
    const context = morpheus.open({ stemlib: root, language: MorpheusLanguage.Greek });
    try {
      const forms = context.generate("lo/gos", { excludeDuals: true });
      assert.equal(forms.length > 0, true);
      assert.equal(forms.every((form) => form.lemma === "lo/gos"), true);
      assert.equal(forms.some((form) => form.surface === "lo/gos"), true);
    } finally {
      context.close();
    }
  },
);
