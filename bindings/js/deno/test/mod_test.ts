// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Antoine Boquet

import {
  hasMorpheusMorphFlag,
  MorpheusDialect,
  MorpheusError,
  MorpheusLanguage,
  MorpheusLibrary,
  MorpheusMorphFlag,
  MorpheusNumber,
  MorpheusOption,
  MorpheusPartOfSpeech,
  MorpheusStatus,
  MorpheusTruncatedField,
} from "../mod.ts";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

Deno.test("tests zero-based public morphology trait bits", () => {
  const morphFlags = new Uint8Array(11);
  morphFlags[Math.floor(MorpheusMorphFlag.SyllAugment / 8)] |=
    1 << (MorpheusMorphFlag.SyllAugment % 8);
  morphFlags[Math.floor(MorpheusMorphFlag.GroupName / 8)] |=
    1 << (MorpheusMorphFlag.GroupName % 8);
  assert(
    hasMorpheusMorphFlag({ morphFlags }, MorpheusMorphFlag.SyllAugment),
    "the syllabic-augment trait must use its public index",
  );
  assert(
    hasMorpheusMorphFlag({ morphFlags }, MorpheusMorphFlag.GroupName),
    "the group-name trait must use its public index",
  );
  assert(
    hasMorpheusMorphFlag([{ morphFlags }], "group-name"),
    "arrays of raw analyses must support named flags",
  );
  assert(
    hasMorpheusMorphFlag(
      [{ morphFlags: ["person-name"] as const }],
      MorpheusMorphFlag.PersonName,
    ),
    "arrays of semantic analyses must support numeric flags",
  );
  assert(
    !hasMorpheusMorphFlag({ morphFlags }, MorpheusMorphFlag.Poetic),
    "unset flags must remain false",
  );
});

Deno.test("analyzes Greek through the native ABI", async () => {
  const libraryPath = Deno.env.get("MORPHEUS_LIBRARY");
  const stemlibPath = Deno.env.get("MORPHEUS_STEMLIB");
  assert(libraryPath, "MORPHEUS_LIBRARY is required");
  assert(stemlibPath, "MORPHEUS_STEMLIB is required");

  using library = new MorpheusLibrary(libraryPath);
  let rejectedMissingStemlib = false;
  try {
    library.createContext(`${stemlibPath}/missing`, MorpheusLanguage.Greek);
  } catch (error) {
    assert(error instanceof MorpheusError, "stemlib failure must be typed");
    assert(
      error.status === MorpheusStatus.StemlibError,
      "missing stemlib must have a stable status",
    );
    rejectedMissingStemlib = true;
  }
  assert(rejectedMissingStemlib, "missing stemlib must be rejected at open");
  await using context = library.createContext(
    stemlibPath,
    MorpheusLanguage.Greek,
  );

  const analyses = await context.analyze(
    "bi/ou",
    MorpheusOption.StrictCase,
  );
  assert(analyses.length === 4, "bi/ou must retain the CLI fixture count");
  assert(analyses[0].raw.length > 0, "raw form must be populated");
  assert(analyses[0].lemma.length > 0, "lemma must be populated");
  assert(Array.isArray(analyses[0].morphFlags), "morph flags must be named");
  assert(
    typeof hasMorpheusMorphFlag(
      analyses[0],
      MorpheusMorphFlag.GroupName,
    ) === "boolean",
    "named morph flags must be testable",
  );
  assert(
    analyses[0].partOfSpeech !== "unknown",
    "part of speech must use a documented name",
  );
  assert(
    analyses[0].truncatedFields.length === 0,
    "fixture fields must expose no truncation names",
  );

  const rawAnalyses = await context.analyzeRaw(
    "bi/ou",
    MorpheusOption.StrictCase,
  );
  assert(rawAnalyses.length === analyses.length, "raw analysis count must match");
  assert(rawAnalyses[0].structSize >= 852, "raw ABI size must be preserved");
  assert(rawAnalyses[0].morphFlags.length === 11, "all public traits must be copied");
  assert(
    rawAnalyses[0].partOfSpeech !== MorpheusPartOfSpeech.Unknown,
    "raw part of speech must preserve its numeric code",
  );
  assert(
    rawAnalyses[0].truncatedFields === MorpheusTruncatedField.None,
    "raw truncation mask must be preserved",
  );

  const [first, second] = await Promise.all([
    context.analyze("tou=", MorpheusOption.StrictCase),
    context.analyze(
      "anqrwpos",
      MorpheusOption.StrictCase | MorpheusOption.IgnoreAccents,
    ),
  ]);
  assert(first.length === 3, "tou= must retain the CLI fixture count");
  assert(
    first.some((analysis) => analysis.partOfSpeech === "article"),
    "the article must not be classified as an adjective",
  );
  assert(
    first.some((analysis) => analysis.partOfSpeech === "pronoun"),
    "the indefinite pronoun must be classified",
  );
  assert(
    first.some((analysis) => analysis.partOfSpeech === "unknown"),
    "a generic indeclinable must remain explicitly unknown",
  );
  assert(second.length > 0, "breathing fallback must be available through FFI");
  assert(second[0].partOfSpeech === "noun", "part of speech must be readable");
  assert(
    second[0].grammaticalNumber === "singular",
    "grammatical number must be readable",
  );
  assert(
    second[0].genders.includes("masculine"),
    "gender masks must be decoded",
  );
  assert(
    second[0].grammaticalCases.includes("nominative"),
    "case masks must be decoded",
  );

  const numeral = await context.analyze("du/o", MorpheusOption.StrictCase);
  assert(numeral.length === 1, "du/o must retain its single analysis");
  assert(numeral[0].partOfSpeech === "numeral", "du/o must be a numeral");
  assert(numeral[0].degree === null, "numerals have no degree");

  const articleAndAdverb = await context.analyze(
    "tw\\",
    MorpheusOption.StrictCase,
  );
  assert(
    articleAndAdverb.some((analysis) => analysis.partOfSpeech === "article"),
    "tw\\ must retain its article analyses",
  );
  assert(
    articleAndAdverb.some((analysis) => analysis.partOfSpeech === "adverb"),
    "tw\\ must expose its adverb analysis",
  );
  assert(
    articleAndAdverb.every((analysis) => analysis.degree === null),
    "articles and adverbs have no degree",
  );

  const indeclinables = await context.analyze(
    "a)n",
    MorpheusOption.StrictCase | MorpheusOption.IgnoreAccents,
  );
  for (const expected of ["particle", "conjunction", "preposition"] as const) {
    assert(
      indeclinables.some((analysis) => analysis.partOfSpeech === expected),
      `a)n must expose its ${expected} analysis`,
    );
  }
  assert(
    indeclinables.every((analysis) => analysis.degree === null),
    "indeclinable lexical classes have no degree",
  );

  const irregularComparative = await context.analyze(
    "presbu/teros",
    MorpheusOption.StrictCase,
  );
  assert(
    irregularComparative.some((analysis) =>
      analysis.degree === "comparative" &&
      analysis.morphFlags.includes("irregular-comparative")
    ),
    "irregular comparative flags must determine the semantic degree",
  );
  const irregularSuperlative = await context.analyze(
    "e)laxiston",
    MorpheusOption.StrictCase,
  );
  assert(
    irregularSuperlative.every((analysis) =>
      analysis.degree === "superlative" &&
      analysis.morphFlags.includes("irregular-superlative")
    ),
    "irregular superlative flags must determine the semantic degree",
  );
  const positiveWithoutRegularComparison = await context.analyze(
    "a)gaqo/s",
    MorpheusOption.StrictCase,
  );
  assert(
    positiveWithoutRegularComparison.some((analysis) =>
      analysis.degree === "positive" &&
      analysis.morphFlags.includes("no-comparison")
    ),
    "no-comparison must not erase an adjective's positive degree",
  );

  const infinitives = await context.analyze(
    "parei=nai",
    MorpheusOption.StrictCase,
  );
  assert(
    infinitives.every((analysis) =>
      analysis.partOfSpeech === "verb" && analysis.degree === null &&
      analysis.person === null && analysis.grammaticalNumber === null
    ),
    "infinitives must expose inapplicable semantic fields as null",
  );
  const participles = await context.analyze(
    "lu/wn",
    MorpheusOption.StrictCase,
  );
  assert(
    participles.some((analysis) =>
      analysis.partOfSpeech === "verb" && analysis.mood === "participle" &&
      analysis.degree === null && analysis.genders.includes("masculine") &&
      analysis.grammaticalCases.includes("nominative")
    ),
    "participles must retain nominal features without becoming adjectives",
  );

  const ambiguousUnaccented = await context.analyze(
    "a)dikoi",
    MorpheusOption.StrictCase | MorpheusOption.IgnoreAccents,
  );
  const dialectVerb = ambiguousUnaccented.find((analysis) =>
    analysis.partOfSpeech === "verb" && analysis.dialects.includes("epic")
  );
  assert(dialectVerb, "the contracted verb analysis must be present");
  assert(
    dialectVerb.dialects.join(",") === "attic,doric,epic",
    "the epic composite must be consumed inside a larger dialect mask",
  );
  assert(dialectVerb.degree === null, "verbs have no semantic degree");

  let rejectedMissingHqDictionary = false;
  try {
    await context.analyze(
      "a)/nqrwpos",
      MorpheusOption.StrictCase |
        MorpheusOption.NoCrasis |
        MorpheusOption.Quick |
        MorpheusOption.HqDictionary |
        MorpheusOption.DialectAttic,
    );
  } catch (error) {
    assert(error instanceof MorpheusError, "HQ stemlib failure must be typed");
    assert(
      error.status === MorpheusStatus.StemlibError,
      "missing HQ indices must have a stable status",
    );
    rejectedMissingHqDictionary = true;
  }
  assert(
    rejectedMissingHqDictionary,
    "missing HQ dictionary must be rejected before analysis",
  );
  const afterScoped = await context.analyze(
    "a)/nqrwpos",
    MorpheusOption.StrictCase,
  );
  assert(afterScoped.length > 0, "request options must not leak to later calls");

  const generations = await context.generate("lo/gos");
  assert(generations.length === 18, "lo/gos must retain the core fixture count");
  assert(
    generations.filter((generation) =>
      generation.grammaticalNumber === "dual"
    ).length === 3,
    "generation must preserve dual forms by default",
  );
  assert(
    new Set(generations.map((generation) => generation.surface)).size === 17,
    "generation must preserve duplicate morphological interpretations",
  );
  assert(
    generations.every((generation) =>
      generation.partOfSpeech === "noun" && generation.lemma === "lo/gos" &&
      generation.truncatedFields.length === 0
    ),
    "semantic generations must preserve normalized grammar and owned text",
  );

  const rawGenerations = await context.generateRaw("lo/gos");
  assert(
    rawGenerations.length === generations.length,
    "raw generation count must match",
  );
  assert(
    rawGenerations[0].structSize >= 188,
    "raw generation ABI size must be preserved",
  );
  assert(
    rawGenerations[0].morphFlags.length === 11,
    "raw generations must copy the complete public trait vector",
  );
  assert(
    rawGenerations[0].truncatedFields === MorpheusTruncatedField.None,
    "raw generation truncation mask must be preserved",
  );

  const withoutDuals = await context.generate("lo/gos", {
    excludeDuals: true,
  });
  assert(withoutDuals.length === 15, "excludeDuals must match the fixture");
  const onlyDuals = await context.generate("lo/gos", {
    number: MorpheusNumber.Dual,
  });
  assert(onlyDuals.length === 3, "the typed number filter must retain duals");

  const attic = await context.generate("multiple", {
    dialect: MorpheusDialect.Attic,
    resultLimit: 1,
  });
  assert(
    attic.length === 1 && attic[0].surface === "prw=ton" &&
      attic[0].dialects.join(",") === "attic",
    "the Attic filter must select its indexed interpretation",
  );
  const ionic = await context.generate("multiple", {
    dialect: MorpheusDialect.Ionic,
    resultLimit: 1,
  });
  assert(
    ionic.length === 1 && ionic[0].surface === "deu/teron" &&
      ionic[0].dialects.join(",") === "ionic",
    "the Ionic filter must select its indexed interpretation",
  );
  assert(
    (await context.generate("multiple")).length === 2,
    "multiple index blocks must remain separate analyses",
  );
  assert(
    (await context.generate("lo/gos", {
      partOfSpeech: MorpheusPartOfSpeech.Verb,
    })).length === 0,
    "typed part-of-speech filters must allow an empty owned result",
  );

  let rejectedLimit = false;
  try {
    await context.generate("lo/gos", { resultLimit: 17 });
  } catch (error) {
    assert(error instanceof MorpheusError, "limit failure must be typed");
    assert(
      error.status === MorpheusStatus.ResultLimitExceeded,
      "limit failure must expose its stable status",
    );
    rejectedLimit = true;
  }
  assert(rejectedLimit, "generation must reject an exceeded result limit");

  let rejectedInvalidLimit = false;
  try {
    await context.generate("lo/gos", { resultLimit: 65_537 });
  } catch (error) {
    assert(error instanceof RangeError, "invalid limits must fail in TypeScript");
    rejectedInvalidLimit = true;
  }
  assert(rejectedInvalidLimit, "an invalid limit must not reach native code");

  const [queuedAnalysis, queuedGeneration] = await Promise.all([
    context.analyze("du/o", MorpheusOption.StrictCase),
    context.generate("multiple"),
  ]);
  assert(
    queuedAnalysis.length === 1 && queuedGeneration.length === 2,
    "analysis and generation must share one context queue",
  );

  await using parallelContext = library.createContext(
    stemlibPath,
    MorpheusLanguage.Greek,
  );
  const [parallelRegular, parallelMultiple] = await Promise.all([
    context.generate("lo/gos", { excludeDuals: true }),
    parallelContext.generate("multiple"),
  ]);
  assert(
    parallelRegular.length === 15 && parallelMultiple.length === 2,
    "distinct contexts must support concurrent generation",
  );
  assert(
    generations.length === 18 && generations[0].surface.length > 0,
    "copied generations must outlive their native result allocation",
  );

  const personAnalyses = await context.analyze(
    "*)arta/chs",
    MorpheusOption.StrictCase,
  );
  const person = personAnalyses.find((analysis) =>
    hasMorpheusMorphFlag(analysis, "person-name")
  );
  assert(person, "Artaches must preserve the person-name stem flag");
});

Deno.test("returns every high-ambiguity Alpheios analysis", async () => {
  const libraryPath = Deno.env.get("MORPHEUS_LIBRARY");
  const stemlibPath = Deno.env.get("MORPHEUS_ALPHEIOS_STEMLIB");
  assert(libraryPath, "MORPHEUS_LIBRARY is required");
  assert(stemlibPath, "MORPHEUS_ALPHEIOS_STEMLIB is required");

  using library = new MorpheusLibrary(libraryPath);
  await using context = library.createContext(stemlibPath, MorpheusLanguage.Greek);
  for (const [word, count] of [["a)nalow", 26], ["a(napinw", 39]] as const) {
    const analyses = await context.analyze(word, MorpheusOption.IgnoreAccents);
    assert(analyses.length === count, `${word} must retain ${count} analyses`);
  }
});
