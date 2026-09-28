// SPDX-License-Identifier: AGPL-3.0-or-later

import {
  MorpheusLanguage,
  MorpheusLibrary,
  MorpheusOption,
} from "@libmorpheus/deno";
import { nativeLibraryPath } from "@libmorpheus/deno/native";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const [nativeRoot, alpheiosRoot, perseidsRoot] = Deno.args;
assert(nativeRoot, "native installation path is required");
assert(alpheiosRoot, "Alpheios installation path is required");
assert(perseidsRoot, "Perseids installation path is required");

using library = new MorpheusLibrary(nativeLibraryPath(nativeRoot));

let alpheiosAnalyses = 0;
let generatedForms = 0;
let generatedDuals = 0;
{
  await using context = library.createContext(
    alpheiosRoot,
    MorpheusLanguage.Greek,
  );
  const analyses = await context.analyze(
    "a)/nqrwpos",
    MorpheusOption.StrictCase,
  );
  assert(analyses.length > 0, "Alpheios Greek analysis returned no result");
  assert(
    analyses.some((analysis) => analysis.partOfSpeech === "noun"),
    "Alpheios Greek analysis lost the expected noun interpretation",
  );
  alpheiosAnalyses = analyses.length;

  const formerlyCrashing = await context.analyze(
    "a)mfestan",
    MorpheusOption.IgnoreAccents,
  );
  assert(
    formerlyCrashing.length > 0,
    "Alpheios analysis failed on the former native 0.4.1 crash case",
  );
  for (const [word, expected] of [["a)nalow", 26], ["a(napinw", 39]] as const) {
    const found = await context.analyze(word, MorpheusOption.IgnoreAccents);
    assert(found.length === expected, `${word}: expected ${expected} analyses`);
  }

  const forms = await context.generate("lo/gos");
  const duals = forms.filter((form) => form.grammaticalNumber === "dual");
  assert(forms.length === 18, "published generation lost its fixture count");
  assert(duals.length === 3, "published generation lost dual forms");
  assert(
    new Set(forms.map((form) => form.surface)).size === 17,
    "published generation lost multiple morphological interpretations",
  );
  generatedForms = forms.length;
  generatedDuals = duals.length;
}

let perseidsGreekAnalyses = 0;
{
  await using context = library.createContext(
    perseidsRoot,
    MorpheusLanguage.Greek,
  );
  const analyses = await context.analyze("a)/nqrwpos");
  assert(analyses.length > 0, "Perseids Greek analysis returned no result");
  perseidsGreekAnalyses = analyses.length;
}

let perseidsLatinAnalyses = 0;
{
  await using context = library.createContext(
    perseidsRoot,
    MorpheusLanguage.Latin,
  );
  const analyses = await context.analyze("est");
  assert(analyses.length >= 2, "Perseids Latin analysis lost interpretations");
  assert(
    analyses.some((analysis) => analysis.lemma === "sum#1"),
    "Perseids Latin analysis lost the expected sum#1 lemma",
  );
  perseidsLatinAnalyses = analyses.length;
}

console.log(JSON.stringify({
  alpheiosAnalyses,
  generatedForms,
  generatedDuals,
  perseidsGreekAnalyses,
  perseidsLatinAnalyses,
}));
