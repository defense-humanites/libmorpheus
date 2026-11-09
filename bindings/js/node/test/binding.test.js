// SPDX-License-Identifier: AGPL-3.0-or-later

import assert from "node:assert/strict";
import test from "node:test";

import {
  MorpheusDialect,
  MorpheusError,
  MorpheusLanguage,
  MorpheusLibrary,
  MorpheusNumber,
  MorpheusOption,
} from "../index.js";

const nativeLibrary = process.env.MORPHEUS_LIBRARY;
const stemlib = process.env.MORPHEUS_STEMLIB;

test("analyzes Greek and preserves multiple semantic records", async () => {
  assert.ok(nativeLibrary);
  assert.ok(stemlib);
  const library = new MorpheusLibrary(nativeLibrary);
  const context = library.createContext(stemlib, MorpheusLanguage.Greek);
  try {
    const analyses = await context.analyze(
      "bi/ou",
      MorpheusOption.StrictCase,
    );
    assert.equal(analyses.length, 4);
    assert.ok(analyses.every((analysis) => analysis.lemma.length > 0));
    assert.ok(analyses.some((analysis) => analysis.partOfSpeech === "noun"));
  } finally {
    await context.close();
    library.close();
  }
});

test("serializes calls and preserves experimental dual generation", async () => {
  const library = new MorpheusLibrary(nativeLibrary);
  const context = library.createContext(stemlib, MorpheusLanguage.Greek);
  try {
    const [analysis, generations] = await Promise.all([
      context.analyze("du/o", MorpheusOption.StrictCase),
      context.generate("lo/gos"),
    ]);
    assert.ok(analysis.length > 0);
    assert.equal(generations.length, 18);
    assert.equal(
      generations.filter((item) => item.grammaticalNumber === "dual").length,
      3,
    );
    assert.equal(
      (await context.generate("lo/gos", {
        number: MorpheusNumber.Dual,
      })).length,
      3,
    );
    assert.equal(
      (await context.generate("multiple", {
        dialect: MorpheusDialect.Attic,
        resultLimit: 1,
      }))[0].surface,
      "prw=ton",
    );
  } finally {
    await context.close();
    library.close();
  }
});

test("analyzes Latin without collapsing interpretations", async () => {
  const library = new MorpheusLibrary(nativeLibrary);
  const context = library.createContext(stemlib, MorpheusLanguage.Latin);
  try {
    const analyses = await context.analyze("est");
    assert.ok(analyses.length >= 2);
    assert.ok(analyses.some((analysis) => analysis.lemma === "sum#1"));
  } finally {
    await context.close();
    library.close();
  }
});

test("decodes raw records from the addon's packed buffer", async () => {
  const library = new MorpheusLibrary(nativeLibrary);
  const context = library.createContext(stemlib, MorpheusLanguage.Greek);
  try {
    const records = await context.analyzeRaw("bi/ou", MorpheusOption.StrictCase);
    assert.equal(records.length, 4);
    for (const record of records) {
      // struct_size is written by the library: the C ABI's record size, which
      // is also the stride the decoder was given.
      assert.equal(record.structSize, 852);
      assert.equal(record.raw, "bi/ou");
      assert.equal(typeof record.lemma, "string");
      assert.ok(record.lemma.length > 0 && record.lemma.length < 64);
      assert.equal(record.morphFlags.constructor, Uint8Array);
      assert.equal(record.morphFlags.length, 11);
      assert.equal(record.truncatedFields, 0);
      assert.ok(Number.isInteger(record.partOfSpeech));
    }
    // Each record owns its morph flags: one record's copy is independent of
    // the others' and of the buffer they were decoded from.
    records[0].morphFlags[0] ^= 0xff;
    const again = await context.analyzeRaw("bi/ou", MorpheusOption.StrictCase);
    assert.deepEqual(again[0].morphFlags, (await context.analyzeRaw("bi/ou", MorpheusOption.StrictCase))[0].morphFlags);
    assert.notDeepEqual(records[0].morphFlags, again[0].morphFlags);
    const empty = await context.analyzeRaw("zzzzzz", MorpheusOption.StrictCase);
    assert.deepEqual(empty, []);
  } finally {
    await context.close();
    library.close();
  }
});

test("names the stemlib and the language a context fails to open", () => {
  assert.ok(nativeLibrary);
  const library = new MorpheusLibrary(nativeLibrary);
  try {
    assert.throws(
      () => library.createContext("/nonexistent-morpheus-stemlib", MorpheusLanguage.Latin),
      (error) =>
        error instanceof MorpheusError &&
        error.status === 8 &&
        /^opening \/nonexistent-morpheus-stemlib for Latin failed: /.test(error.message),
    );
  } finally {
    library.close();
  }
});
