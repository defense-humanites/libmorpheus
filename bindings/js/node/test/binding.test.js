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
  hasMorpheusMorphFlag,
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

test("reports skipped generation records without changing the array", async () => {
  const library = new MorpheusLibrary(nativeLibrary);
  const context = library.createContext(stemlib, MorpheusLanguage.Greek);
  try {
    const complete = await context.generate("lo/gos");
    assert.equal(complete.skippedRecords, 0);
    // The fixture's "partial" lemma has one record the engine cannot generate.
    const partial = await context.generate("partial");
    assert.equal(partial.length, 18);
    assert.equal(partial.skippedRecords, 1);
    assert.equal((await context.generateRaw("partial")).skippedRecords, 1);
    assert.equal(
      (await context.generate("partial", { number: MorpheusNumber.Dual })).skippedRecords,
      1,
    );
    const missing = await context.generate("missing");
    assert.equal(missing.length, 0);
    assert.equal(missing.skippedRecords, 0);
    assert.ok(Array.isArray(partial));
    assert.deepEqual(Object.keys(partial), Object.keys([...partial]));
    assert.throws(() => { "use strict"; partial.skippedRecords = 5; }, TypeError);
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

test("shares frozen name arrays between records and keeps raw records raw", async () => {
  const library = new MorpheusLibrary(nativeLibrary);
  const context = library.createContext(stemlib, MorpheusLanguage.Greek);
  try {
    const generations = await context.generate("lo/gos");
    const arrayFields = [
      "dialects", "geographicRegions", "genders", "grammaticalCases",
      "voices", "morphFlags", "truncatedFields",
    ];
    for (const generation of generations) {
      for (const field of arrayFields) {
        assert.ok(Array.isArray(generation[field]), field);
        assert.ok(Object.isFrozen(generation[field]), field);
      }
      assert.throws(() => generation.genders.push("neuter"), TypeError);
    }
    // Records with the same codes share one array; a copy is mutable.
    const singular = generations.filter((item) => item.grammaticalNumber === "singular");
    assert.ok(singular.length > 1);
    assert.equal(singular[0].genders, singular[1].genders);
    const copy = [...singular[0].genders];
    copy.push("neuter");
    assert.notDeepEqual(copy, singular[0].genders);
    // The named and raw views agree on the morph flags.
    const analyses = await context.analyze("bi/ou", MorpheusOption.StrictCase);
    const raw = await context.analyzeRaw("bi/ou", MorpheusOption.StrictCase);
    assert.equal(analyses.length, raw.length);
    for (let index = 0; index < raw.length; index++) {
      assert.ok(Object.isFrozen(analyses[index].morphFlags));
      for (const name of analyses[index].morphFlags) {
        assert.ok(hasMorpheusMorphFlag(raw[index], name), name);
      }
    }
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
