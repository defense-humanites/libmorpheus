// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Antoine Boquet

export declare const MORPHEUS_NODE_VERSION = "0.2.0";

export declare const MorpheusLanguage: {
  readonly Greek: 0; readonly Latin: 1; readonly Italian: 2;
};
export type MorpheusLanguage =
  typeof MorpheusLanguage[keyof typeof MorpheusLanguage];

export declare const MorpheusStatus: {
  readonly Ok: 0; readonly InvalidArgument: 1; readonly AbiMismatch: 2;
  readonly NoMemory: 3; readonly InputTooLong: 4; readonly OutOfRange: 5;
  readonly InternalError: 6; readonly BufferTooSmall: 7;
  readonly StemlibError: 8; readonly ResultLimitExceeded: 9;
};
export type MorpheusStatus = typeof MorpheusStatus[keyof typeof MorpheusStatus];

export declare const MorpheusOption: {
  readonly StrictCase: bigint; readonly IgnoreAccents: bigint;
  readonly VerbsOnly: bigint; readonly NoCrasis: bigint;
  readonly Quick: bigint; readonly HqDictionary: bigint;
  readonly DialectAeolic: bigint; readonly DialectAttic: bigint;
  readonly DialectDoric: bigint; readonly DialectHomeric: bigint;
  readonly DialectIonic: bigint; readonly DialectLesbian: bigint;
  readonly DialectNonHomericEpic: bigint; readonly DialectParadigm: bigint;
  readonly DialectEpic: bigint; readonly DialectProse: bigint;
};

export declare const MorpheusPartOfSpeech: {
  readonly Unknown: 0; readonly Noun: 1; readonly Verb: 2;
  readonly Adjective: 3; readonly Adverb: 4; readonly Article: 5;
  readonly Pronoun: 6; readonly Numeral: 7; readonly Preposition: 8;
  readonly Conjunction: 9; readonly Particle: 10; readonly Interjection: 11;
};
export type MorpheusPartOfSpeech =
  typeof MorpheusPartOfSpeech[keyof typeof MorpheusPartOfSpeech];
export declare const MorpheusPerson: {
  readonly None: 0; readonly First: 1; readonly Second: 2; readonly Third: 3;
};
export type MorpheusPerson = typeof MorpheusPerson[keyof typeof MorpheusPerson];
export declare const MorpheusNumber: {
  readonly None: 0; readonly Singular: 1; readonly Dual: 2; readonly Plural: 3;
};
export type MorpheusNumber = typeof MorpheusNumber[keyof typeof MorpheusNumber];
export declare const MorpheusGender: {
  readonly None: 0; readonly Adverbial: 1; readonly Feminine: 2;
  readonly Masculine: 4; readonly Neuter: 8;
};
export type MorpheusGender = typeof MorpheusGender[keyof typeof MorpheusGender];
export declare const MorpheusCase: {
  readonly None: 0; readonly Ablative: 1; readonly Accusative: 2;
  readonly Dative: 4; readonly Genitive: 8; readonly Nominative: 16;
  readonly Vocative: 32;
};
export type MorpheusCase = typeof MorpheusCase[keyof typeof MorpheusCase];
export declare const MorpheusTense: {
  readonly None: 0; readonly Present: 1; readonly Imperfect: 2;
  readonly Future: 3; readonly Aorist: 4; readonly Perfect: 5;
  readonly Pluperfect: 6; readonly FuturePerfect: 7;
  readonly PastAbsolute: 8;
};
export type MorpheusTense = typeof MorpheusTense[keyof typeof MorpheusTense];
export declare const MorpheusMood: {
  readonly None: 0; readonly Conditional: 1; readonly Gerundive: 2;
  readonly Imperative: 3; readonly Indicative: 4; readonly Infinitive: 5;
  readonly Optative: 6; readonly Participle: 7; readonly Subjunctive: 8;
  readonly Supine: 9;
};
export type MorpheusMood = typeof MorpheusMood[keyof typeof MorpheusMood];
export declare const MorpheusVoice: {
  readonly None: 0; readonly Active: 1; readonly Passive: 2;
  readonly Middle: 4; readonly MedioPassive: 6; readonly Deponent: 5;
};
export type MorpheusVoice = typeof MorpheusVoice[keyof typeof MorpheusVoice];
export declare const MorpheusDegree: {
  readonly None: 0; readonly Positive: 1; readonly Comparative: 2;
  readonly Superlative: 3;
};
export type MorpheusDegree = typeof MorpheusDegree[keyof typeof MorpheusDegree];
export declare const MorpheusDialect: {
  readonly All: 0; readonly Aeolic: 1; readonly Attic: 2;
  readonly Doric: 4; readonly Homeric: 8; readonly Ionic: 16;
  readonly Lesbian: 32; readonly NonHomericEpic: 64;
  readonly Paradigm: 128; readonly Epic: 72; readonly Prose: 256;
};
export type MorpheusDialect =
  typeof MorpheusDialect[keyof typeof MorpheusDialect];
export declare const MorpheusGeographicRegion: {
  readonly None: 0; readonly Arcadia: 1; readonly Argolid: 2;
  readonly Boeotia: 4; readonly Cos: 8; readonly Crete: 16;
  readonly Cyprus: 32; readonly Cyrene: 64; readonly Elis: 128;
  readonly Heraclea: 256; readonly Laconia: 512; readonly Locris: 1024;
  readonly Megarid: 2048; readonly Phocis: 4096; readonly Rhodes: 8192;
  readonly Thera: 16384;
};
export type MorpheusGeographicRegion =
  typeof MorpheusGeographicRegion[keyof typeof MorpheusGeographicRegion];

export declare const MorpheusTruncatedField: {
  readonly None: 0; readonly Raw: number; readonly Workword: number;
  readonly Lemma: number; readonly Preverb: number; readonly Augment: number;
  readonly Stem: number; readonly Suffix: number; readonly Ending: number;
  readonly Crasis: number; readonly DictionaryForm: number;
  readonly EnglishForm: number; readonly RawPreverb: number;
  readonly Domains: number;
};

export declare const MorpheusMorphFlag: Readonly<Record<string, number>>;
export type MorpheusMorphFlag = number;
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

export interface MorpheusGenerationOptions {
  readonly resultLimit?: number;
  readonly excludeDuals?: boolean;
  readonly partOfSpeech?: MorpheusPartOfSpeech;
  readonly dialect?: MorpheusDialect;
  readonly geographicRegion?: MorpheusGeographicRegion;
  readonly person?: MorpheusPerson;
  readonly number?: MorpheusNumber;
  readonly gender?: MorpheusGender;
  readonly grammaticalCase?: MorpheusCase;
  readonly tense?: MorpheusTense;
  readonly mood?: MorpheusMood;
  readonly voice?: MorpheusVoice;
  readonly degree?: MorpheusDegree;
}

export interface MorpheusRawAnalysis {
  readonly structSize: number;
  readonly partOfSpeech: number;
  readonly dialect: number;
  readonly geographicRegion: number;
  readonly person: number;
  readonly number: number;
  readonly gender: number;
  readonly grammaticalCase: number;
  readonly tense: number;
  readonly mood: number;
  readonly voice: number;
  readonly degree: number;
  readonly raw: string;
  readonly workword: string;
  readonly lemma: string;
  readonly preverb: string;
  readonly augment: string;
  readonly stem: string;
  readonly suffix: string;
  readonly ending: string;
  readonly crasis: string;
  readonly dictionaryForm: string;
  readonly englishForm: string;
  readonly rawPreverb: string;
  readonly domains: string;
  readonly morphFlags: Uint8Array;
  readonly truncatedFields: number;
}

export interface MorpheusRawGeneration {
  readonly structSize: number;
  readonly partOfSpeech: number;
  readonly dialect: number;
  readonly geographicRegion: number;
  readonly person: number;
  readonly number: number;
  readonly gender: number;
  readonly grammaticalCase: number;
  readonly tense: number;
  readonly mood: number;
  readonly voice: number;
  readonly degree: number;
  readonly surface: string;
  readonly lemma: string;
  readonly morphFlags: Uint8Array;
  readonly truncatedFields: number;
}

export type MorpheusPartOfSpeechName =
  | "unknown" | "noun" | "verb" | "adjective" | "adverb" | "article"
  | "pronoun" | "numeral" | "preposition" | "conjunction" | "particle"
  | "interjection";
export type MorpheusPersonName = "first" | "second" | "third";
export type MorpheusNumberName = "singular" | "dual" | "plural";
export type MorpheusGenderName =
  "masculine" | "feminine" | "neuter" | "adverbial";
export type MorpheusCaseName =
  | "nominative" | "genitive" | "dative" | "accusative" | "vocative"
  | "ablative";
export type MorpheusTenseName =
  | "present" | "imperfect" | "future" | "aorist" | "perfect"
  | "pluperfect" | "future-perfect" | "past-absolute";
export type MorpheusMoodName =
  | "indicative" | "subjunctive" | "optative" | "imperative"
  | "infinitive" | "participle" | "gerundive" | "supine" | "conditional";
export type MorpheusVoiceName =
  "active" | "middle" | "passive" | "medio-passive" | "deponent";
export type MorpheusDegreeName = "positive" | "comparative" | "superlative";
export type MorpheusDialectName =
  | "attic" | "ionic" | "aeolic" | "lesbian" | "homeric" | "doric"
  | "paradigm" | "non-homeric-epic" | "epic" | "prose";
export type MorpheusGeographicRegionName =
  | "phocis" | "locris" | "elis" | "laconia" | "heraclea" | "megarid"
  | "argolid" | "rhodes" | "cos" | "thera" | "cyrene" | "crete"
  | "arcadia" | "cyprus" | "boeotia";
export type MorpheusTruncatedFieldName =
  | "raw" | "workword" | "lemma" | "preverb" | "augment" | "stem"
  | "suffix" | "ending" | "crasis" | "dictionaryForm" | "englishForm"
  | "rawPreverb" | "domains";
export type MorpheusGenerationTruncatedFieldName = "surface" | "lemma";

export interface MorpheusAnalysis {
  readonly partOfSpeech: MorpheusPartOfSpeechName;
  readonly dialects: readonly MorpheusDialectName[];
  readonly geographicRegions: readonly MorpheusGeographicRegionName[];
  readonly person: MorpheusPersonName | null;
  readonly grammaticalNumber: MorpheusNumberName | null;
  readonly genders: readonly MorpheusGenderName[];
  readonly grammaticalCases: readonly MorpheusCaseName[];
  readonly tense: MorpheusTenseName | null;
  readonly mood: MorpheusMoodName | null;
  readonly voices: readonly MorpheusVoiceName[];
  readonly degree: MorpheusDegreeName | null;
  readonly raw: string;
  readonly workword: string;
  readonly lemma: string;
  readonly preverb: string;
  readonly augment: string;
  readonly stem: string;
  readonly suffix: string;
  readonly ending: string;
  readonly crasis: string;
  readonly dictionaryForm: string;
  readonly englishForm: string;
  readonly rawPreverb: string;
  readonly domains: string;
  readonly morphFlags: readonly MorpheusMorphFlagName[];
  readonly truncatedFields: readonly MorpheusTruncatedFieldName[];
}

export interface MorpheusGeneration {
  readonly partOfSpeech: MorpheusPartOfSpeechName;
  readonly dialects: readonly MorpheusDialectName[];
  readonly geographicRegions: readonly MorpheusGeographicRegionName[];
  readonly person: MorpheusPersonName | null;
  readonly grammaticalNumber: MorpheusNumberName | null;
  readonly genders: readonly MorpheusGenderName[];
  readonly grammaticalCases: readonly MorpheusCaseName[];
  readonly tense: MorpheusTenseName | null;
  readonly mood: MorpheusMoodName | null;
  readonly voices: readonly MorpheusVoiceName[];
  readonly degree: MorpheusDegreeName | null;
  readonly surface: string;
  readonly lemma: string;
  readonly morphFlags: readonly MorpheusMorphFlagName[];
  readonly truncatedFields: readonly MorpheusGenerationTruncatedFieldName[];
}

type MorpheusMorphFlagAnalysis =
  | Pick<MorpheusRawAnalysis, "morphFlags">
  | Pick<MorpheusAnalysis, "morphFlags">
  | Pick<MorpheusRawGeneration, "morphFlags">
  | Pick<MorpheusGeneration, "morphFlags">;

export declare function hasMorpheusMorphFlag(
  analysis: MorpheusMorphFlagAnalysis | readonly MorpheusMorphFlagAnalysis[],
  flag: number | MorpheusMorphFlagName,
): boolean;

export declare class MorpheusError extends Error {
  readonly status: number;
  constructor(status: number, message: string);
}

export declare class MorpheusLibrary {
  constructor(path: string | URL);
  createContext(
    stemlibPath: string,
    language: MorpheusLanguage,
  ): MorpheusContext;
  close(): void;
}

/**
 * The records of one generation request. `skippedRecords` counts the lemma's
 * source records that the engine could not generate and skipped (records,
 * not forms, independent of the filters); a nonzero count with no records
 * means that every record of a known lemma failed.
 */
export type MorpheusGenerations<T> = readonly T[] & {
  readonly skippedRecords: number;
};

export declare class MorpheusContext {
  private constructor();
  analyze(betaCode: string, options?: bigint): Promise<readonly MorpheusAnalysis[]>;
  analyzeRaw(
    betaCode: string,
    options?: bigint,
  ): Promise<readonly MorpheusRawAnalysis[]>;
  generate(
    lemma: string,
    options?: MorpheusGenerationOptions,
  ): Promise<MorpheusGenerations<MorpheusGeneration>>;
  generateRaw(
    lemma: string,
    options?: MorpheusGenerationOptions,
  ): Promise<MorpheusGenerations<MorpheusRawGeneration>>;
  close(): Promise<void>;
}
