// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Antoine Boquet

/**
 * Deno FFI binding for libmorpheus Greek and Latin analysis and experimental
 * Greek lemma generation.
 *
 * **No longer maintained: version 0.4.3 is the final release.** It acquires
 * native libmorpheus 0.4.5. Use `jsr:@libmorpheus/wasm` (no FFI permission
 * needed) or, on Node.js, `npm:@libmorpheus/node` for new code.
 *
 * The separately distributed native library and stem data must be supplied at
 * runtime. Applications need Deno's `--allow-ffi` permission.
 *
 * After adding the package, run its `/setup` entrypoint to acquire the native
 * library and verified stem data with explicit permissions.
 *
 * @example Analyze an Ancient Greek Beta Code form
 * ```ts
 * import {
 *   MorpheusLanguage,
 *   MorpheusLibrary,
 *   MorpheusOption,
 * } from "@libmorpheus/deno";
 *
 * using library = new MorpheusLibrary("/path/to/libmorpheus.so");
 * await using context = library.createContext(
 *   "/path/to/stemlib",
 *   MorpheusLanguage.Greek,
 * );
 * const analyses = await context.analyze(
 *   "a)/nqrwpos",
 *   MorpheusOption.StrictCase,
 * );
 * ```
 *
 * @module
 */

import { MORPHEUS_NATIVE_ABI_VERSION } from "./internal/version.ts";

export { MORPHEUS_DENO_VERSION } from "./internal/version.ts";

const ABI_VERSION = MORPHEUS_NATIVE_ABI_VERSION;
const TEXT_CAPACITY = 64;
const DOMAIN_CAPACITY = 24;
const MORPH_FLAG_CAPACITY = 11;
const GENERATION_OPTIONS_VERSION = 1;
const GENERATION_OPTIONS_SIZE = 64;

const SYMBOLS = {
  morpheus_abi_version: { parameters: [], result: "u32" },
  morpheus_analysis_size: { parameters: [], result: "usize" },
  morpheus_generation_size: { parameters: [], result: "usize" },
  morpheus_status_message: { parameters: ["u32"], result: "pointer" },
  morpheus_open_path: {
    parameters: ["u32", "buffer", "usize", "u32", "buffer"],
    result: "u32",
  },
  morpheus_close: { parameters: ["pointer"], result: "void" },
  morpheus_analyze: {
    parameters: ["pointer", "buffer", "usize", "u64", "buffer"],
    result: "u32",
    nonblocking: true,
  },
  morpheus_result_count: { parameters: ["pointer"], result: "usize" },
  morpheus_result_copy: {
    parameters: ["pointer", "usize", "buffer", "usize"],
    result: "u32",
  },
  morpheus_result_truncated_fields: {
    parameters: ["pointer", "usize", "buffer"],
    result: "u32",
  },
  morpheus_result_free: { parameters: ["pointer"], result: "void" },
  morpheus_generate: {
    parameters: ["pointer", "buffer", "usize", "buffer", "buffer"],
    result: "u32",
    nonblocking: true,
  },
  morpheus_generation_result_count: {
    parameters: ["pointer"],
    result: "usize",
  },
  morpheus_generation_result_copy: {
    parameters: ["pointer", "usize", "buffer", "usize"],
    result: "u32",
  },
  morpheus_generation_result_truncated_fields: {
    parameters: ["pointer", "usize", "buffer"],
    result: "u32",
  },
  morpheus_generation_result_free: {
    parameters: ["pointer"],
    result: "void",
  },
} as const;

type NativeLibrary = Deno.DynamicLibrary<typeof SYMBOLS>;

/** Numeric language selectors accepted by {@link MorpheusLibrary.createContext}. */
export const MorpheusLanguage = {
  Greek: 0,
  Latin: 1,
  Italian: 2,
} as const;
/** A numeric language selector. */
export type MorpheusLanguage =
  typeof MorpheusLanguage[keyof typeof MorpheusLanguage];

/** Status codes returned by the stable native ABI. */
export const MorpheusStatus = {
  Ok: 0,
  InvalidArgument: 1,
  AbiMismatch: 2,
  NoMemory: 3,
  InputTooLong: 4,
  OutOfRange: 5,
  InternalError: 6,
  BufferTooSmall: 7,
  StemlibError: 8,
  ResultLimitExceeded: 9,
} as const;
/** A native status code, also exposed by {@link MorpheusError}. */
export type MorpheusStatus =
  typeof MorpheusStatus[keyof typeof MorpheusStatus];

/** Bit flags that customize analysis requests. Combine flags with `|`. */
export const MorpheusOption = {
  StrictCase: 1n << 0n,
  IgnoreAccents: 1n << 1n,
  VerbsOnly: 1n << 2n,
  NoCrasis: 1n << 3n,
  Quick: 1n << 4n,
  HqDictionary: 1n << 5n,
  DialectAeolic: 1n << 16n,
  DialectAttic: 2n << 16n,
  DialectDoric: 4n << 16n,
  DialectHomeric: 8n << 16n,
  DialectIonic: 16n << 16n,
  DialectLesbian: 32n << 16n,
  DialectNonHomericEpic: 64n << 16n,
  DialectParadigm: 128n << 16n,
  DialectEpic: 72n << 16n,
  DialectProse: 256n << 16n,
} as const;

/** Numeric morphological feature flags preserved from the engine. */
export const MorpheusMorphFlag = {
  SyllAugment: 74,
  CompOnly: 7,
  Enclitic: 19,
  Iterative: 35,
  SuffixAccent: 73,
  StemAccent: 72,
  Contracted: 8,
  PersonName: 52,
  AntepenultAccent: 3,
  IrregularSuperlative: 34,
  IrregularComparative: 32,
  NoComparison: 47,
  ShortPenult: 69,
  LongPenult: 38,
  RecessiveAccent: 64,
  AccentOptional: 0,
  NeedsAccent: 43,
  RhoEtaIotaAlpha: 66,
  NotInComposition: 45,
  HasPreverb: 26,
  Unaugmented: 79,
  Dissimilation: 13,
  Proclitic: 56,
  Apocope: 4,
  IrregularForm: 33,
  HasAugment: 25,
  QuantityMetathesis: 60,
  NuMovable: 49,
  IntervocalicSToH: 29,
  PreverbAugment: 55,
  Poetic: 53,
  UncontractedStem: 81,
  Metathesis: 40,
  ElidedPreverb: 18,
  IndeclinableForm: 28,
  RootPreverb: 67,
  Diminutive: 12,
  Late: 36,
  Rare: 61,
  RawPreverb: 62,
  Early: 17,
  ShortSubjunctive: 70,
  UnaspiratedPreverb: 78,
  Reduplication: 65,
  UncontractedEnding: 80,
  Derivative: 10,
  AtticReduplication: 5,
  NoReduplication: 48,
  NInfix: 50,
  Syncope: 75,
  Impersonal: 27,
  NeedsRoughBreathing: 44,
  NoCircumflex: 46,
  Causal: 6,
  Intransitive: 30,
  Tmesis: 77,
  RawSonant: 63,
  Prodelision: 57,
  Frequentative: 22,
  Later: 37,
  DoubleAugment: 15,
  DoubleReduplication: 16,
  Desiderative: 11,
  PresentReduplication: 54,
  EndsInDigamma: 20,
  GeographicName: 23,
  DoubledConsonant: 14,
  IotaIntensive: 31,
  LostAccent: 39,
  SigmaToCi: 71,
  ShortEis: 68,
  ProsToPoti: 58,
  MetaToPeda: 41,
  ProsToProti: 59,
  UpoToUpai: 83,
  ParaToParai: 51,
  UperToUpeir: 82,
  EnToEni: 21,
  AlphaPrivative: 2,
  AlphaCopulative: 1,
  MetricallyLong: 42,
  DeltaPreverb: 9,
  TauPreverb: 76,
  GroupName: 24,
} as const;
/** A numeric morphological feature flag. */
export type MorpheusMorphFlag =
  typeof MorpheusMorphFlag[keyof typeof MorpheusMorphFlag];

/** Stable normalized name for a morphological feature flag. */
export type MorpheusMorphFlagName =
  | "syllabic-augment" | "compound-only" | "enclitic" | "iterative"
  | "suffix-accent" | "stem-accent" | "contracted" | "person-name"
  | "antepenult-accent" | "irregular-superlative" | "irregular-comparative"
  | "no-comparison" | "short-penult" | "long-penult" | "recessive-accent"
  | "accent-optional" | "needs-accent" | "rho-eta-iota-alpha"
  | "not-in-composition" | "has-preverb" | "unaugmented" | "dissimilation"
  | "proclitic" | "apocope" | "irregular-form" | "has-augment"
  | "quantity-metathesis" | "nu-movable" | "intervocalic-s-to-h"
  | "preverb-augment" | "poetic" | "uncontracted-stem" | "metathesis"
  | "elided-preverb" | "indeclinable-form" | "root-preverb" | "diminutive"
  | "late" | "rare" | "raw-preverb" | "early" | "short-subjunctive"
  | "unaspirated-preverb" | "reduplication" | "uncontracted-ending"
  | "derivative" | "attic-reduplication" | "no-reduplication" | "n-infix"
  | "syncope" | "impersonal" | "needs-rough-breathing" | "no-circumflex"
  | "causal" | "intransitive" | "tmesis" | "raw-sonant" | "prodelision"
  | "frequentative" | "later" | "double-augment" | "double-reduplication"
  | "desiderative" | "present-reduplication" | "ends-in-digamma"
  | "geographic-name" | "doubled-consonant" | "iota-intensive"
  | "lost-accent" | "sigma-to-ci" | "short-eis" | "pros-to-poti"
  | "meta-to-peda" | "pros-to-proti" | "upo-to-upai" | "para-to-parai"
  | "uper-to-upeir" | "en-to-eni" | "alpha-privative" | "alpha-copulative"
  | "metrically-long" | "delta-preverb" | "tau-preverb" | "group-name";

const MORPH_FLAG_NAMES = new Map<number, MorpheusMorphFlagName>([
  [74, "syllabic-augment"], [7, "compound-only"], [19, "enclitic"],
  [35, "iterative"], [73, "suffix-accent"], [72, "stem-accent"],
  [8, "contracted"], [52, "person-name"], [3, "antepenult-accent"],
  [34, "irregular-superlative"], [32, "irregular-comparative"],
  [47, "no-comparison"], [69, "short-penult"], [38, "long-penult"],
  [64, "recessive-accent"], [0, "accent-optional"], [43, "needs-accent"],
  [66, "rho-eta-iota-alpha"], [45, "not-in-composition"], [26, "has-preverb"],
  [79, "unaugmented"], [13, "dissimilation"], [56, "proclitic"],
  [4, "apocope"], [33, "irregular-form"], [25, "has-augment"],
  [60, "quantity-metathesis"], [49, "nu-movable"],
  [29, "intervocalic-s-to-h"], [55, "preverb-augment"], [53, "poetic"],
  [81, "uncontracted-stem"], [40, "metathesis"], [18, "elided-preverb"],
  [28, "indeclinable-form"], [67, "root-preverb"], [12, "diminutive"],
  [36, "late"], [61, "rare"], [62, "raw-preverb"], [17, "early"],
  [70, "short-subjunctive"], [78, "unaspirated-preverb"],
  [65, "reduplication"], [80, "uncontracted-ending"], [10, "derivative"],
  [5, "attic-reduplication"], [48, "no-reduplication"], [50, "n-infix"],
  [75, "syncope"], [27, "impersonal"], [44, "needs-rough-breathing"],
  [46, "no-circumflex"], [6, "causal"], [30, "intransitive"],
  [77, "tmesis"], [63, "raw-sonant"], [57, "prodelision"],
  [22, "frequentative"], [37, "later"], [15, "double-augment"],
  [16, "double-reduplication"], [11, "desiderative"],
  [54, "present-reduplication"], [20, "ends-in-digamma"],
  [23, "geographic-name"], [14, "doubled-consonant"],
  [31, "iota-intensive"], [39, "lost-accent"], [71, "sigma-to-ci"],
  [68, "short-eis"], [58, "pros-to-poti"], [41, "meta-to-peda"],
  [59, "pros-to-proti"], [83, "upo-to-upai"], [51, "para-to-parai"],
  [82, "uper-to-upeir"], [21, "en-to-eni"], [2, "alpha-privative"],
  [1, "alpha-copulative"], [42, "metrically-long"],
  [9, "delta-preverb"], [76, "tau-preverb"], [24, "group-name"],
]);

type MorpheusMorphFlagAnalysis =
  | Pick<MorpheusRawAnalysis, "morphFlags">
  | Pick<MorpheusAnalysis, "morphFlags">
  | Pick<MorpheusRawGeneration, "morphFlags">
  | Pick<MorpheusGeneration, "morphFlags">;

function isMorpheusMorphFlagAnalysisArray(
  analysis: MorpheusMorphFlagAnalysis | readonly MorpheusMorphFlagAnalysis[],
): analysis is readonly MorpheusMorphFlagAnalysis[] {
  return Array.isArray(analysis);
}

/**
 * Tests one raw or normalized result, or an array of results, for a
 * morphological feature.
 */
export function hasMorpheusMorphFlag(
  analysis: MorpheusMorphFlagAnalysis | readonly MorpheusMorphFlagAnalysis[],
  flag: number | MorpheusMorphFlagName,
): boolean {
  if (isMorpheusMorphFlagAnalysisArray(analysis)) {
    return analysis.some((item) => hasMorpheusMorphFlag(item, flag));
  }
  if (!(analysis.morphFlags instanceof Uint8Array)) {
    const name = typeof flag === "number" ? MORPH_FLAG_NAMES.get(flag) : flag;
    return name !== undefined && analysis.morphFlags.includes(name);
  }
  if (typeof flag !== "number") {
    for (const [code, name] of MORPH_FLAG_NAMES) {
      if (name === flag) return hasMorpheusMorphFlag(analysis, code);
    }
    return false;
  }
  if (flag < 0) return false;
  const index = Math.floor(flag / 8);
  return index < analysis.morphFlags.length &&
    (analysis.morphFlags[index] & (1 << (flag % 8))) !== 0;
}

/** Numeric part-of-speech values used by the native ABI and generation filters. */
export const MorpheusPartOfSpeech = {
  Unknown: 0,
  Noun: 1,
  Verb: 2,
  Adjective: 3,
  Adverb: 4,
  Article: 5,
  Pronoun: 6,
  Numeral: 7,
  Preposition: 8,
  Conjunction: 9,
  Particle: 10,
  Interjection: 11,
} as const;
/** A numeric part-of-speech value. */
export type MorpheusPartOfSpeech =
  typeof MorpheusPartOfSpeech[keyof typeof MorpheusPartOfSpeech];

/** Numeric grammatical-person values used by generation filters. */
export const MorpheusPerson = {
  None: 0,
  First: 1,
  Second: 2,
  Third: 3,
} as const;
/** A numeric grammatical-person value. */
export type MorpheusPerson =
  typeof MorpheusPerson[keyof typeof MorpheusPerson];

/** Numeric grammatical-number values, including the dual. */
export const MorpheusNumber = {
  None: 0,
  Singular: 1,
  Dual: 2,
  Plural: 3,
} as const;
/** A numeric grammatical-number value. */
export type MorpheusNumber =
  typeof MorpheusNumber[keyof typeof MorpheusNumber];

/** Numeric grammatical-gender mask values. */
export const MorpheusGender = {
  None: 0,
  Adverbial: 1,
  Feminine: 2,
  Masculine: 4,
  Neuter: 8,
} as const;
/** A numeric grammatical-gender mask. */
export type MorpheusGender =
  typeof MorpheusGender[keyof typeof MorpheusGender];

/** Numeric grammatical-case mask values. */
export const MorpheusCase = {
  None: 0,
  Ablative: 1,
  Accusative: 2,
  Dative: 4,
  Genitive: 8,
  Nominative: 16,
  Vocative: 32,
} as const;
/** A numeric grammatical-case mask. */
export type MorpheusCase =
  typeof MorpheusCase[keyof typeof MorpheusCase];

/** Numeric tense values used by generation filters. */
export const MorpheusTense = {
  None: 0,
  Present: 1,
  Imperfect: 2,
  Future: 3,
  Aorist: 4,
  Perfect: 5,
  Pluperfect: 6,
  FuturePerfect: 7,
  PastAbsolute: 8,
} as const;
/** A numeric tense value. */
export type MorpheusTense =
  typeof MorpheusTense[keyof typeof MorpheusTense];

/** Numeric mood values used by generation filters. */
export const MorpheusMood = {
  None: 0,
  Conditional: 1,
  Gerundive: 2,
  Imperative: 3,
  Indicative: 4,
  Infinitive: 5,
  Optative: 6,
  Participle: 7,
  Subjunctive: 8,
  Supine: 9,
} as const;
/** A numeric mood value. */
export type MorpheusMood =
  typeof MorpheusMood[keyof typeof MorpheusMood];

/** Numeric grammatical-voice mask values. */
export const MorpheusVoice = {
  None: 0,
  Active: 1,
  Passive: 2,
  Middle: 4,
  MedioPassive: 6,
  Deponent: 5,
} as const;
/** A numeric grammatical-voice mask. */
export type MorpheusVoice =
  typeof MorpheusVoice[keyof typeof MorpheusVoice];

/** Numeric comparison-degree values used by generation filters. */
export const MorpheusDegree = {
  None: 0,
  Positive: 1,
  Comparative: 2,
  Superlative: 3,
} as const;
/** A numeric comparison-degree value. */
export type MorpheusDegree =
  typeof MorpheusDegree[keyof typeof MorpheusDegree];

/** Numeric dialect mask values preserved by analysis and generation. */
export const MorpheusDialect = {
  All: 0,
  Aeolic: 1,
  Attic: 2,
  Doric: 4,
  Homeric: 8,
  Ionic: 16,
  Lesbian: 32,
  NonHomericEpic: 64,
  Paradigm: 128,
  Epic: 72,
  Prose: 256,
} as const;
/** A numeric dialect mask. */
export type MorpheusDialect =
  typeof MorpheusDialect[keyof typeof MorpheusDialect];

/** Numeric geographic-region mask values. */
export const MorpheusGeographicRegion = {
  None: 0,
  Arcadia: 1,
  Argolid: 2,
  Boeotia: 4,
  Cos: 8,
  Crete: 16,
  Cyprus: 32,
  Cyrene: 64,
  Elis: 128,
  Heraclea: 256,
  Laconia: 512,
  Locris: 1024,
  Megarid: 2048,
  Phocis: 4096,
  Rhodes: 8192,
  Thera: 16384,
} as const;
/** A numeric geographic-region mask. */
export type MorpheusGeographicRegion =
  typeof MorpheusGeographicRegion[keyof typeof MorpheusGeographicRegion];

/**
 * Filters and limits for experimental Greek lemma generation.
 *
 * @experimental Pending sufficient real-world validation.
 */
export interface MorpheusGenerationOptions {
  /** Maximum returned records, from 1 through 65,536. */
  readonly resultLimit?: number;
  /** Remove dual-number forms after generation. */
  readonly excludeDuals?: boolean;
  /** Keep only this part of speech. */
  readonly partOfSpeech?: MorpheusPartOfSpeech;
  /** Keep forms matching this dialect mask. */
  readonly dialect?: MorpheusDialect;
  /** Keep forms matching this geographic-region mask. */
  readonly geographicRegion?: MorpheusGeographicRegion;
  /** Keep only this grammatical person. */
  readonly person?: MorpheusPerson;
  /** Keep only this grammatical number. */
  readonly number?: MorpheusNumber;
  /** Keep forms matching this gender mask. */
  readonly gender?: MorpheusGender;
  /** Keep forms matching this grammatical-case mask. */
  readonly grammaticalCase?: MorpheusCase;
  /** Keep only this tense. */
  readonly tense?: MorpheusTense;
  /** Keep only this mood. */
  readonly mood?: MorpheusMood;
  /** Keep forms matching this voice mask. */
  readonly voice?: MorpheusVoice;
  /** Keep only this comparison degree. */
  readonly degree?: MorpheusDegree;
}

/** Bit flags identifying fixed-width ABI fields that were truncated. */
export const MorpheusTruncatedField = {
  None: 0,
  Raw: 1 << 0,
  Workword: 1 << 1,
  Lemma: 1 << 2,
  Preverb: 1 << 3,
  Augment: 1 << 4,
  Stem: 1 << 5,
  Suffix: 1 << 6,
  Ending: 1 << 7,
  Crasis: 1 << 8,
  DictionaryForm: 1 << 9,
  EnglishForm: 1 << 10,
  RawPreverb: 1 << 11,
  Domains: 1 << 12,
} as const;

/** One analysis record using the numeric values and masks of the native ABI. */
export interface MorpheusRawAnalysis {
  /** Native record size used for ABI validation. */
  readonly structSize: number;
  /** Numeric {@link MorpheusPartOfSpeech} value. */
  readonly partOfSpeech: number;
  /** Numeric {@link MorpheusDialect} mask. */
  readonly dialect: number;
  /** Numeric {@link MorpheusGeographicRegion} mask. */
  readonly geographicRegion: number;
  /** Numeric {@link MorpheusPerson} value. */
  readonly person: number;
  /** Numeric {@link MorpheusNumber} value. */
  readonly number: number;
  /** Numeric {@link MorpheusGender} mask. */
  readonly gender: number;
  /** Numeric {@link MorpheusCase} mask. */
  readonly grammaticalCase: number;
  /** Numeric {@link MorpheusTense} value. */
  readonly tense: number;
  /** Numeric {@link MorpheusMood} value. */
  readonly mood: number;
  /** Numeric {@link MorpheusVoice} mask. */
  readonly voice: number;
  /** Numeric {@link MorpheusDegree} value. */
  readonly degree: number;
  /** Original engine analysis text. */
  readonly raw: string;
  /** Normalized input form used by the engine. */
  readonly workword: string;
  /** Analyzed lemma in Beta Code. */
  readonly lemma: string;
  /** Parsed preverb in Beta Code. */
  readonly preverb: string;
  /** Parsed augment in Beta Code. */
  readonly augment: string;
  /** Parsed stem in Beta Code. */
  readonly stem: string;
  /** Parsed suffix in Beta Code. */
  readonly suffix: string;
  /** Parsed ending in Beta Code. */
  readonly ending: string;
  /** Parsed crasis component in Beta Code. */
  readonly crasis: string;
  /** Dictionary headword in Beta Code. */
  readonly dictionaryForm: string;
  /** English gloss supplied by the stem data. */
  readonly englishForm: string;
  /** Unnormalized preverb retained by the engine. */
  readonly rawPreverb: string;
  /** Domain metadata supplied by the stem data. */
  readonly domains: string;
  /** Complete public morphology bit vector. */
  readonly morphFlags: Uint8Array;
  /** Bit mask of {@link MorpheusTruncatedField} values. */
  readonly truncatedFields: number;
}

/**
 * One experimental generation record using numeric native ABI values.
 *
 * @experimental Pending sufficient real-world validation.
 */
export interface MorpheusRawGeneration {
  /** Native record size used for ABI validation. */
  readonly structSize: number;
  /** Numeric {@link MorpheusPartOfSpeech} value. */
  readonly partOfSpeech: number;
  /** Numeric {@link MorpheusDialect} mask. */
  readonly dialect: number;
  /** Numeric {@link MorpheusGeographicRegion} mask. */
  readonly geographicRegion: number;
  /** Numeric {@link MorpheusPerson} value. */
  readonly person: number;
  /** Numeric {@link MorpheusNumber} value. */
  readonly number: number;
  /** Numeric {@link MorpheusGender} mask. */
  readonly gender: number;
  /** Numeric {@link MorpheusCase} mask. */
  readonly grammaticalCase: number;
  /** Numeric {@link MorpheusTense} value. */
  readonly tense: number;
  /** Numeric {@link MorpheusMood} value. */
  readonly mood: number;
  /** Numeric {@link MorpheusVoice} mask. */
  readonly voice: number;
  /** Numeric {@link MorpheusDegree} value. */
  readonly degree: number;
  /** Generated surface form in Beta Code. */
  readonly surface: string;
  /** Indexed lemma in Beta Code. */
  readonly lemma: string;
  /** Complete public morphology bit vector. */
  readonly morphFlags: Uint8Array;
  /** Bit mask of truncated generation fields. */
  readonly truncatedFields: number;
}

/** Normalized part-of-speech identifier. */
export type MorpheusPartOfSpeechName =
  | "unknown" | "noun" | "verb" | "adjective" | "adverb" | "article"
  | "pronoun" | "numeral" | "preposition" | "conjunction" | "particle"
  | "interjection";
/** Normalized grammatical-person identifier. */
export type MorpheusPersonName = "first" | "second" | "third";
/** Normalized grammatical-number identifier, including the dual. */
export type MorpheusNumberName = "singular" | "dual" | "plural";
/** Normalized grammatical-gender identifier. */
export type MorpheusGenderName = "masculine" | "feminine" | "neuter" | "adverbial";
/** Normalized grammatical-case identifier. */
export type MorpheusCaseName =
  | "nominative" | "genitive" | "dative" | "accusative" | "vocative" | "ablative";
/** Normalized tense identifier. */
export type MorpheusTenseName =
  | "present" | "imperfect" | "future" | "aorist" | "perfect"
  | "pluperfect" | "future-perfect" | "past-absolute";
/** Normalized mood identifier. */
export type MorpheusMoodName =
  | "indicative" | "subjunctive" | "optative" | "imperative" | "infinitive"
  | "participle" | "gerundive" | "supine" | "conditional";
/** Normalized grammatical-voice identifier. */
export type MorpheusVoiceName =
  | "active" | "middle" | "passive" | "medio-passive" | "deponent";
/** Normalized comparison-degree identifier. */
export type MorpheusDegreeName = "positive" | "comparative" | "superlative";
/** Normalized dialect identifier. */
export type MorpheusDialectName =
  | "attic" | "ionic" | "aeolic" | "lesbian" | "homeric" | "doric"
  | "paradigm" | "non-homeric-epic" | "epic" | "prose";
/** Normalized geographic-region identifier. */
export type MorpheusGeographicRegionName =
  | "phocis" | "locris" | "elis" | "laconia" | "heraclea" | "megarid"
  | "argolid" | "rhodes" | "cos" | "thera" | "cyrene" | "crete"
  | "arcadia" | "cyprus" | "boeotia";
/** Name of a truncated analysis field. */
export type MorpheusTruncatedFieldName =
  | "raw" | "workword" | "lemma" | "preverb" | "augment" | "stem"
  | "suffix" | "ending" | "crasis" | "dictionaryForm" | "englishForm"
  | "rawPreverb" | "domains";
/** Name of a truncated experimental generation field. */
export type MorpheusGenerationTruncatedFieldName = "surface" | "lemma";

/** One normalized analysis with stable names and explicit mask arrays. */
export interface MorpheusAnalysis {
  /** Normalized lexical category. */
  readonly partOfSpeech: MorpheusPartOfSpeechName;
  /** Every dialect represented by the native mask. */
  readonly dialects: readonly MorpheusDialectName[];
  /** Every geographic region represented by the native mask. */
  readonly geographicRegions: readonly MorpheusGeographicRegionName[];
  /** Grammatical person, or `null` when inapplicable. */
  readonly person: MorpheusPersonName | null;
  /** Grammatical number, including dual, or `null` when inapplicable. */
  readonly grammaticalNumber: MorpheusNumberName | null;
  /** Every gender represented by the native mask. */
  readonly genders: readonly MorpheusGenderName[];
  /** Every grammatical case represented by the native mask. */
  readonly grammaticalCases: readonly MorpheusCaseName[];
  /** Tense, or `null` when inapplicable. */
  readonly tense: MorpheusTenseName | null;
  /** Mood, or `null` when inapplicable. */
  readonly mood: MorpheusMoodName | null;
  /** Every voice represented by the native mask. */
  readonly voices: readonly MorpheusVoiceName[];
  /** Comparison degree, or `null` when inapplicable. */
  readonly degree: MorpheusDegreeName | null;
  /** Original engine analysis text. */
  readonly raw: string;
  /** Normalized input form used by the engine. */
  readonly workword: string;
  /** Analyzed lemma in Beta Code. */
  readonly lemma: string;
  /** Parsed preverb in Beta Code. */
  readonly preverb: string;
  /** Parsed augment in Beta Code. */
  readonly augment: string;
  /** Parsed stem in Beta Code. */
  readonly stem: string;
  /** Parsed suffix in Beta Code. */
  readonly suffix: string;
  /** Parsed ending in Beta Code. */
  readonly ending: string;
  /** Parsed crasis component in Beta Code. */
  readonly crasis: string;
  /** Dictionary headword in Beta Code. */
  readonly dictionaryForm: string;
  /** English gloss supplied by the stem data. */
  readonly englishForm: string;
  /** Unnormalized preverb retained by the engine. */
  readonly rawPreverb: string;
  /** Domain metadata supplied by the stem data. */
  readonly domains: string;
  /** Stable names for every set morphology flag. */
  readonly morphFlags: readonly MorpheusMorphFlagName[];
  /** Names of fixed-width fields truncated by the native ABI. */
  readonly truncatedFields: readonly MorpheusTruncatedFieldName[];
}

/**
 * One normalized form returned by experimental Greek lemma generation.
 *
 * @experimental Pending sufficient real-world validation.
 */
export interface MorpheusGeneration {
  /** Normalized lexical category. */
  readonly partOfSpeech: MorpheusPartOfSpeechName;
  /** Every dialect represented by the indexed analysis. */
  readonly dialects: readonly MorpheusDialectName[];
  /** Every geographic region represented by the indexed analysis. */
  readonly geographicRegions: readonly MorpheusGeographicRegionName[];
  /** Grammatical person, or `null` when inapplicable. */
  readonly person: MorpheusPersonName | null;
  /** Grammatical number, including dual, or `null` when inapplicable. */
  readonly grammaticalNumber: MorpheusNumberName | null;
  /** Every gender represented by the indexed analysis. */
  readonly genders: readonly MorpheusGenderName[];
  /** Every grammatical case represented by the indexed analysis. */
  readonly grammaticalCases: readonly MorpheusCaseName[];
  /** Tense, or `null` when inapplicable. */
  readonly tense: MorpheusTenseName | null;
  /** Mood, or `null` when inapplicable. */
  readonly mood: MorpheusMoodName | null;
  /** Every voice represented by the indexed analysis. */
  readonly voices: readonly MorpheusVoiceName[];
  /** Comparison degree, or `null` when inapplicable. */
  readonly degree: MorpheusDegreeName | null;
  /** Generated surface form in Beta Code. */
  readonly surface: string;
  /** Indexed source lemma in Beta Code. */
  readonly lemma: string;
  /** Stable names for every set morphology flag. */
  readonly morphFlags: readonly MorpheusMorphFlagName[];
  /** Names of fixed-width fields truncated by the native ABI. */
  readonly truncatedFields: readonly MorpheusGenerationTruncatedFieldName[];
}

/** Error reported by the native ABI, including its numeric status. */
export class MorpheusError extends Error {
  /** Numeric {@link MorpheusStatus} value returned by the native ABI. */
  readonly status: number;

  /** Creates an error for a native status and human-readable message. */
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "MorpheusError";
  }
}

const encoder = new TextEncoder();
const decoder = new TextDecoder();
const littleEndian = new Uint8Array(new Uint16Array([1]).buffer)[0] === 1;

function pointerFromSlot(slot: BigUint64Array): Deno.PointerObject {
  const pointer = Deno.UnsafePointer.create(slot[0]);
  if (pointer === null) throw new Error("Morpheus returned a null pointer");
  return pointer;
}

function cString(bytes: Uint8Array, offset: number, capacity: number): string {
  const field = bytes.subarray(offset, offset + capacity);
  const terminator = field.indexOf(0);
  return decoder.decode(terminator < 0 ? field : field.subarray(0, terminator));
}

function decodeAnalysis(
  bytes: Uint8Array,
  truncatedFields: number,
): MorpheusRawAnalysis {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const numbers: number[] = [];
  for (let offset = 0; offset < 48; offset += 4) {
    numbers.push(view.getUint32(offset, littleEndian));
  }
  let offset = 48;
  const text = () => {
    const value = cString(bytes, offset, TEXT_CAPACITY);
    offset += TEXT_CAPACITY;
    return value;
  };
  const raw = text();
  const workword = text();
  const lemma = text();
  const preverb = text();
  const augment = text();
  const stem = text();
  const suffix = text();
  const ending = text();
  const crasis = text();
  const dictionaryForm = text();
  const englishForm = text();
  const rawPreverb = text();
  const domains = cString(bytes, offset, DOMAIN_CAPACITY);
  offset += DOMAIN_CAPACITY;
  const morphFlags = bytes.slice(offset, offset + MORPH_FLAG_CAPACITY);

  return {
    structSize: numbers[0],
    partOfSpeech: numbers[1],
    dialect: numbers[2],
    geographicRegion: numbers[3],
    person: numbers[4],
    number: numbers[5],
    gender: numbers[6],
    grammaticalCase: numbers[7],
    tense: numbers[8],
    mood: numbers[9],
    voice: numbers[10],
    degree: numbers[11],
    raw,
    workword,
    lemma,
    preverb,
    augment,
    stem,
    suffix,
    ending,
    crasis,
    dictionaryForm,
    englishForm,
    rawPreverb,
    domains,
    morphFlags,
    truncatedFields,
  };
}

function encodeGenerationOptions(
  options: MorpheusGenerationOptions,
): Uint8Array {
  const resultLimit = options.resultLimit ?? 0;
  if (!Number.isSafeInteger(resultLimit) || resultLimit < 0 ||
    resultLimit > 65_536) {
    throw new RangeError("resultLimit must be an integer from 0 to 65536");
  }
  const bytes = new Uint8Array(GENERATION_OPTIONS_SIZE);
  const view = new DataView(bytes.buffer);
  view.setUint32(0, GENERATION_OPTIONS_VERSION, littleEndian);
  view.setUint32(4, GENERATION_OPTIONS_SIZE, littleEndian);
  view.setBigUint64(8, BigInt(resultLimit), littleEndian);
  view.setUint32(16, options.excludeDuals ? 1 : 0, littleEndian);
  view.setUint32(20, options.partOfSpeech ?? 0, littleEndian);
  view.setUint32(24, options.dialect ?? 0, littleEndian);
  view.setUint32(28, options.geographicRegion ?? 0, littleEndian);
  view.setUint32(32, options.person ?? 0, littleEndian);
  view.setUint32(36, options.number ?? 0, littleEndian);
  view.setUint32(40, options.gender ?? 0, littleEndian);
  view.setUint32(44, options.grammaticalCase ?? 0, littleEndian);
  view.setUint32(48, options.tense ?? 0, littleEndian);
  view.setUint32(52, options.mood ?? 0, littleEndian);
  view.setUint32(56, options.voice ?? 0, littleEndian);
  view.setUint32(60, options.degree ?? 0, littleEndian);
  return bytes;
}

function decodeGeneration(
  bytes: Uint8Array,
  truncatedFields: number,
): MorpheusRawGeneration {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const numbers: number[] = [];
  for (let offset = 0; offset < 48; offset += 4) {
    numbers.push(view.getUint32(offset, littleEndian));
  }
  const surface = cString(bytes, 48, TEXT_CAPACITY);
  const lemma = cString(bytes, 48 + TEXT_CAPACITY, TEXT_CAPACITY);
  const morphFlagOffset = 48 + 2 * TEXT_CAPACITY;
  return {
    structSize: numbers[0],
    partOfSpeech: numbers[1],
    dialect: numbers[2],
    geographicRegion: numbers[3],
    person: numbers[4],
    number: numbers[5],
    gender: numbers[6],
    grammaticalCase: numbers[7],
    tense: numbers[8],
    mood: numbers[9],
    voice: numbers[10],
    degree: numbers[11],
    surface,
    lemma,
    morphFlags: bytes.slice(
      morphFlagOffset,
      morphFlagOffset + MORPH_FLAG_CAPACITY,
    ),
    truncatedFields,
  };
}

function exactName<T extends string>(
  value: number,
  entries: readonly (readonly [number, T])[],
): T | null {
  return entries.find(([code]) => code === value)?.[1] ?? null;
}

function maskNames<T extends string>(
  value: number,
  entries: readonly (readonly [number, T])[],
  exactEntries: readonly (readonly [number, T])[] = [],
): readonly T[] {
  const exact = exactName(value, exactEntries);
  if (exact !== null) return [exact];
  return entries.filter(([bit]) => (value & bit) === bit).map(([, name]) => name);
}

const PART_OF_SPEECH_NAMES = [
  [0, "unknown"], [1, "noun"], [2, "verb"], [3, "adjective"],
  [4, "adverb"], [5, "article"], [6, "pronoun"], [7, "numeral"],
  [8, "preposition"], [9, "conjunction"], [10, "particle"],
  [11, "interjection"],
] as const;
const PERSON_NAMES = [[1, "first"], [2, "second"], [3, "third"]] as const;
const NUMBER_NAMES = [[1, "singular"], [2, "dual"], [3, "plural"]] as const;
const GENDER_NAMES = [[1, "adverbial"], [2, "feminine"], [4, "masculine"], [8, "neuter"]] as const;
const CASE_NAMES = [[1, "ablative"], [2, "accusative"], [4, "dative"], [8, "genitive"], [16, "nominative"], [32, "vocative"]] as const;
const TENSE_NAMES = [[1, "present"], [2, "imperfect"], [3, "future"], [4, "aorist"], [5, "perfect"], [6, "pluperfect"], [7, "future-perfect"], [8, "past-absolute"]] as const;
const MOOD_NAMES = [[1, "conditional"], [2, "gerundive"], [3, "imperative"], [4, "indicative"], [5, "infinitive"], [6, "optative"], [7, "participle"], [8, "subjunctive"], [9, "supine"]] as const;
const VOICE_NAMES = [[1, "active"], [2, "passive"], [4, "middle"]] as const;
const VOICE_EXACT_NAMES = [[6, "medio-passive"], [5, "deponent"]] as const;
const DEGREE_NAMES = [[1, "positive"], [2, "comparative"], [3, "superlative"]] as const;
const DIALECT_NAMES = [[1, "aeolic"], [2, "attic"], [4, "doric"], [8, "homeric"], [16, "ionic"], [32, "lesbian"], [64, "non-homeric-epic"], [128, "paradigm"], [256, "prose"]] as const;
const DIALECT_NAME_ORDER: readonly MorpheusDialectName[] = [
  "attic", "ionic", "aeolic", "lesbian", "homeric", "doric", "paradigm",
  "non-homeric-epic", "epic", "prose",
];
const REGION_NAMES = [[1, "arcadia"], [2, "argolid"], [4, "boeotia"], [8, "cos"], [16, "crete"], [32, "cyprus"], [64, "cyrene"], [128, "elis"], [256, "heraclea"], [512, "laconia"], [1024, "locris"], [2048, "megarid"], [4096, "phocis"], [8192, "rhodes"], [16384, "thera"]] as const;
const TRUNCATED_FIELD_NAMES = [[1 << 0, "raw"], [1 << 1, "workword"], [1 << 2, "lemma"], [1 << 3, "preverb"], [1 << 4, "augment"], [1 << 5, "stem"], [1 << 6, "suffix"], [1 << 7, "ending"], [1 << 8, "crasis"], [1 << 9, "dictionaryForm"], [1 << 10, "englishForm"], [1 << 11, "rawPreverb"], [1 << 12, "domains"]] as const;

function dialectNames(value: number): readonly MorpheusDialectName[] {
  let remaining = value;
  const selected = new Set<MorpheusDialectName>();
  if ((remaining & MorpheusDialect.Epic) === MorpheusDialect.Epic) {
    selected.add("epic");
    remaining &= ~MorpheusDialect.Epic;
  }
  for (const [bit, name] of DIALECT_NAMES) {
    if ((remaining & bit) === bit) selected.add(name);
  }
  return DIALECT_NAME_ORDER.filter((name) => selected.has(name));
}

function semanticDegree(raw: MorpheusRawAnalysis): MorpheusDegreeName | null {
  return exactName(raw.degree, DEGREE_NAMES);
}

function semanticAnalysis(raw: MorpheusRawAnalysis): MorpheusAnalysis {
  const morphFlags: MorpheusMorphFlagName[] = [];
  for (const [code, name] of MORPH_FLAG_NAMES) {
    if (hasMorpheusMorphFlag(raw, code)) morphFlags.push(name);
  }
  const partOfSpeech =
    exactName(raw.partOfSpeech, PART_OF_SPEECH_NAMES) ?? "unknown";
  return {
    partOfSpeech,
    dialects: dialectNames(raw.dialect),
    geographicRegions: maskNames(raw.geographicRegion, REGION_NAMES),
    person: exactName(raw.person, PERSON_NAMES),
    grammaticalNumber: exactName(raw.number, NUMBER_NAMES),
    genders: maskNames(raw.gender, GENDER_NAMES),
    grammaticalCases: maskNames(raw.grammaticalCase, CASE_NAMES),
    tense: exactName(raw.tense, TENSE_NAMES),
    mood: exactName(raw.mood, MOOD_NAMES),
    voices: maskNames<MorpheusVoiceName>(
      raw.voice,
      VOICE_NAMES,
      VOICE_EXACT_NAMES,
    ),
    degree: semanticDegree(raw),
    raw: raw.raw, workword: raw.workword, lemma: raw.lemma,
    preverb: raw.preverb, augment: raw.augment, stem: raw.stem,
    suffix: raw.suffix, ending: raw.ending, crasis: raw.crasis,
    dictionaryForm: raw.dictionaryForm, englishForm: raw.englishForm,
    rawPreverb: raw.rawPreverb, domains: raw.domains,
    morphFlags,
    truncatedFields: maskNames(raw.truncatedFields, TRUNCATED_FIELD_NAMES),
  };
}

function semanticGeneration(raw: MorpheusRawGeneration): MorpheusGeneration {
  const morphFlags: MorpheusMorphFlagName[] = [];
  const truncatedFields: MorpheusGenerationTruncatedFieldName[] = [];
  for (const [code, name] of MORPH_FLAG_NAMES) {
    if (hasMorpheusMorphFlag(raw, code)) morphFlags.push(name);
  }
  if (raw.truncatedFields & MorpheusTruncatedField.Workword) {
    truncatedFields.push("surface");
  }
  if (raw.truncatedFields & MorpheusTruncatedField.Lemma) {
    truncatedFields.push("lemma");
  }
  return {
    partOfSpeech:
      exactName(raw.partOfSpeech, PART_OF_SPEECH_NAMES) ?? "unknown",
    dialects: dialectNames(raw.dialect),
    geographicRegions: maskNames(raw.geographicRegion, REGION_NAMES),
    person: exactName(raw.person, PERSON_NAMES),
    grammaticalNumber: exactName(raw.number, NUMBER_NAMES),
    genders: maskNames(raw.gender, GENDER_NAMES),
    grammaticalCases: maskNames(raw.grammaticalCase, CASE_NAMES),
    tense: exactName(raw.tense, TENSE_NAMES),
    mood: exactName(raw.mood, MOOD_NAMES),
    voices: maskNames<MorpheusVoiceName>(
      raw.voice,
      VOICE_NAMES,
      VOICE_EXACT_NAMES,
    ),
    degree: exactName(raw.degree, DEGREE_NAMES),
    surface: raw.surface,
    lemma: raw.lemma,
    morphFlags,
    truncatedFields,
  };
}

/**
 * Owns one loaded native library and creates independent stateful contexts.
 *
 * Dispose the library after all of its contexts have been closed.
 */
export class MorpheusLibrary {
  readonly #native: NativeLibrary;
  readonly #analysisSize: number;
  readonly #generationSize: number;
  #contexts = 0;
  #closed = false;

  /** Loads and validates an ABI-compatible shared library. Requires `--allow-ffi`. */
  constructor(path: string | URL) {
    if (!["x86_64", "aarch64"].includes(Deno.build.arch)) {
      throw new Error(`Unsupported pointer width for ${Deno.build.arch}`);
    }
    this.#native = Deno.dlopen(path, SYMBOLS);
    if (this.#native.symbols.morpheus_abi_version() !== ABI_VERSION) {
      this.#native.close();
      throw new Error("Unsupported libmorpheus ABI version");
    }
    this.#analysisSize =
      Number(this.#native.symbols.morpheus_analysis_size());
    if (this.#analysisSize < 852) {
      this.#native.close();
      throw new Error("libmorpheus analysis record is smaller than ABI version 2");
    }
    this.#generationSize =
      Number(this.#native.symbols.morpheus_generation_size());
    if (this.#generationSize < 188) {
      this.#native.close();
      throw new Error("libmorpheus generation record is smaller than ABI version 2");
    }
  }

  /**
   * Opens a context for one stemlib directory and language.
   *
   * The directory needs only analysis data unless experimental generation is
   * used, in which case it must also contain `gener.index`.
   */
  createContext(
    stemlibPath: string,
    language: MorpheusLanguage,
  ): MorpheusContext {
    if (this.#closed) throw new Error("Morpheus library is closed");
    const path = encoder.encode(stemlibPath);
    const output = new BigUint64Array(1);
    const status = this.#native.symbols.morpheus_open_path(
      ABI_VERSION,
      path,
      BigInt(path.byteLength),
      language,
      output,
    );
    this.#throwOnError(status);
    this.#contexts++;
    return new MorpheusContext(
      this.#native,
      pointerFromSlot(output),
      this.#analysisSize,
      this.#generationSize,
      () => this.#contexts--,
    );
  }

  /** Unloads the native library after all contexts have been closed. */
  close(): void {
    if (this.#closed) return;
    if (this.#contexts) {
      throw new Error("Close all Morpheus contexts before the library");
    }
    this.#native.close();
    this.#closed = true;
  }

  /** Supports deterministic cleanup with a `using` declaration. */
  [Symbol.dispose](): void {
    this.close();
  }

  #throwOnError(status: number): void {
    if (status === 0) return;
    const pointer = this.#native.symbols.morpheus_status_message(status);
    const message = pointer === null
      ? `Morpheus status ${status}`
      : new Deno.UnsafePointerView(pointer).getCString();
    throw new MorpheusError(status, message);
  }
}

/**
 * A stateful analysis and generation context bound to one language and stemlib.
 *
 * Calls on the same context are serialized. Use distinct contexts for
 * independent parallel operations.
 */
export class MorpheusContext {
  #tail: Promise<void> = Promise.resolve();
  #closed = false;

  /** @internal Contexts are created by {@link MorpheusLibrary.createContext}. */
  constructor(
    private readonly native: NativeLibrary,
    private readonly pointer: Deno.PointerObject,
    private readonly analysisSize: number,
    private readonly generationSize: number,
    private readonly onClose: () => void,
  ) {}

  /** Analyzes one Greek or Latin Beta Code form into normalized records. */
  analyze(
    betaCode: string,
    options: bigint = 0n,
  ): Promise<readonly MorpheusAnalysis[]> {
    return this.analyzeRaw(betaCode, options).then((analyses) =>
      analyses.map(semanticAnalysis)
    );
  }

  /** Analyzes one Greek or Latin Beta Code form into numeric ABI records. */
  analyzeRaw(
    betaCode: string,
    options: bigint = 0n,
  ): Promise<readonly MorpheusRawAnalysis[]> {
    return this.#enqueue(() => this.#analyze(betaCode, options));
  }

  /**
   * Generate normalized Greek forms for one Beta Code lemma.
   *
   * @experimental Pending sufficient real-world validation in addition to the
   * automated differential, isolation, failure, portability, and sanitizer
   * coverage.
   */
  generate(
    lemma: string,
    options: MorpheusGenerationOptions = {},
  ): Promise<readonly MorpheusGeneration[]> {
    return this.generateRaw(lemma, options).then((generations) =>
      generations.map(semanticGeneration)
    );
  }

  /**
   * Generate numeric ABI records for one Greek Beta Code lemma.
   *
   * @experimental Pending sufficient real-world validation in addition to the
   * automated differential, isolation, failure, portability, and sanitizer
   * coverage.
   */
  generateRaw(
    lemma: string,
    options: MorpheusGenerationOptions = {},
  ): Promise<readonly MorpheusRawGeneration[]> {
    const encodedOptions = encodeGenerationOptions(options);
    return this.#enqueue(() => this.#generate(lemma, encodedOptions));
  }

  /** Waits for queued calls, then releases this native context. */
  async close(): Promise<void> {
    if (this.#closed) return;
    this.#closed = true;
    await this.#tail;
    this.native.symbols.morpheus_close(this.pointer);
    this.onClose();
  }

  /** Supports deterministic asynchronous cleanup with `await using`. */
  async [Symbol.asyncDispose](): Promise<void> {
    await this.close();
  }

  #enqueue<T>(operation: () => Promise<T>): Promise<T> {
    if (this.#closed) {
      return Promise.reject(new Error("Morpheus context is closed"));
    }
    const run = this.#tail.then(operation);
    this.#tail = run.then(() => undefined, () => undefined);
    return run;
  }

  async #analyze(
    betaCode: string,
    options: bigint,
  ): Promise<readonly MorpheusRawAnalysis[]> {
    const input = encoder.encode(betaCode);
    const output = new BigUint64Array(1);
    const status = await this.native.symbols.morpheus_analyze(
      this.pointer,
      input,
      BigInt(input.byteLength),
      options,
      output,
    );
    this.#throwOnError(status);
    const result = pointerFromSlot(output);
    try {
      const count = Number(this.native.symbols.morpheus_result_count(result));
      const analyses: MorpheusRawAnalysis[] = [];
      for (let index = 0; index < count; index++) {
        const bytes = new Uint8Array(this.analysisSize);
        this.#throwOnError(this.native.symbols.morpheus_result_copy(
          result,
          BigInt(index),
          bytes,
          BigInt(bytes.byteLength),
        ));
        const truncatedFields = new Uint32Array(1);
        this.#throwOnError(this.native.symbols.morpheus_result_truncated_fields(
          result,
          BigInt(index),
          truncatedFields,
        ));
        analyses.push(decodeAnalysis(
          bytes,
          truncatedFields[0],
        ));
      }
      return analyses;
    } finally {
      this.native.symbols.morpheus_result_free(result);
    }
  }

  async #generate(
    lemma: string,
    options: Uint8Array,
  ): Promise<readonly MorpheusRawGeneration[]> {
    const input = encoder.encode(lemma);
    const output = new BigUint64Array(1);
    const status = await this.native.symbols.morpheus_generate(
      this.pointer,
      input,
      BigInt(input.byteLength),
      options,
      output,
    );
    this.#throwOnError(status);
    const result = pointerFromSlot(output);
    try {
      const count = Number(
        this.native.symbols.morpheus_generation_result_count(result),
      );
      const generations: MorpheusRawGeneration[] = [];
      for (let index = 0; index < count; index++) {
        const bytes = new Uint8Array(this.generationSize);
        this.#throwOnError(
          this.native.symbols.morpheus_generation_result_copy(
            result,
            BigInt(index),
            bytes,
            BigInt(bytes.byteLength),
          ),
        );
        const truncatedFields = new Uint32Array(1);
        this.#throwOnError(
          this.native.symbols.morpheus_generation_result_truncated_fields(
            result,
            BigInt(index),
            truncatedFields,
          ),
        );
        generations.push(decodeGeneration(bytes, truncatedFields[0]));
      }
      return generations;
    } finally {
      this.native.symbols.morpheus_generation_result_free(result);
    }
  }

  #throwOnError(status: number): void {
    if (status === 0) return;
    const pointer = this.native.symbols.morpheus_status_message(status);
    const message = pointer === null
      ? `Morpheus status ${status}`
      : new Deno.UnsafePointerView(pointer).getCString();
    throw new MorpheusError(status, message);
  }
}
