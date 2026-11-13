// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Antoine Boquet

import { Buffer } from "node:buffer";
import os from "node:os";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

import { MORPHEUS_NODE_VERSION } from "./internal/version.js";

export { MORPHEUS_NODE_VERSION };

const require = createRequire(import.meta.url);

function platformAddonPackage() {
  if (process.platform === "darwin" && process.arch === "arm64") {
    return "@libmorpheus/node-darwin-arm64";
  }
  if (process.platform === "linux" && ["arm64", "x64"].includes(process.arch)) {
    const glibc = process.report?.getReport()?.header?.glibcVersionRuntime;
    if (glibc === undefined) {
      throw new Error("The libmorpheus native runtime requires glibc on Linux");
    }
    return `@libmorpheus/node-linux-${process.arch}-gnu`;
  }
  throw new Error(
    `No libmorpheus Node-API addon supports ${process.platform}-${process.arch}`,
  );
}

function loadAddon() {
  if (process.env.MORPHEUS_NODE_ADDON !== undefined) {
    return require(process.env.MORPHEUS_NODE_ADDON);
  }
  const packageName = platformAddonPackage();
  try {
    return require(packageName);
  } catch (error) {
    if (error?.code !== "MODULE_NOT_FOUND") throw error;
  }
  try {
    return require(fileURLToPath(new URL("./libmorpheus_node.node", import.meta.url)));
  } catch (error) {
    if (error?.code !== "MODULE_NOT_FOUND") throw error;
  }
  throw new Error(
    `Missing optional native package ${packageName}; reinstall ` +
      "@libmorpheus/node without omitting optional dependencies",
  );
}

const addon = loadAddon();

// The addon returns the records of one operation as a single packed buffer
// (the C ABI's morpheus_analysis / morpheus_generation layout, followed by
// the truncated-field masks) that this module decodes; see decodeRecords().
const RECORD_ENCODING = 2;
if (addon.recordEncoding !== RECORD_ENCODING) {
  throw new Error(
    `The libmorpheus Node-API addon encodes results as ${addon.recordEncoding ?? "an earlier"}` +
      ` format; this package expects ${RECORD_ENCODING}. Rebuild or update the addon.`,
  );
}

const TEXT_CAPACITY = 64;
const DOMAIN_CAPACITY = 24;
const MORPH_FLAG_CAPACITY = 11;
const NUMBER_FIELDS = 12;
const NUMBERS_SIZE = NUMBER_FIELDS * 4;
const ANALYSIS_TEXT_FIELDS = [
  "raw", "workword", "lemma", "preverb", "augment", "stem", "suffix",
  "ending", "crasis", "dictionaryForm", "englishForm", "rawPreverb",
];
const ANALYSIS_MINIMUM_SIZE = NUMBERS_SIZE + ANALYSIS_TEXT_FIELDS.length *
    TEXT_CAPACITY + DOMAIN_CAPACITY + MORPH_FLAG_CAPACITY;
const GENERATION_MINIMUM_SIZE = NUMBERS_SIZE + 2 * TEXT_CAPACITY +
  MORPH_FLAG_CAPACITY;
const littleEndian = true;
const littleEndianHost = os.endianness() === "LE";

function cString(bytes, offset, capacity) {
  let end = bytes.indexOf(0, offset);
  if (end < 0 || end > offset + capacity) end = offset + capacity;
  return bytes.toString("utf8", offset, end);
}

function packedView(packed, minimumRecordSize) {
  const { count, recordSize, buffer } = packed;
  if (!Number.isInteger(count) || !Number.isInteger(recordSize) ||
      !(buffer instanceof ArrayBuffer) || recordSize < minimumRecordSize ||
      buffer.byteLength !== count * (recordSize + 4)) {
    throw new Error("Malformed result buffer from the libmorpheus addon");
  }
  return {
    count,
    recordSize,
    bytes: Buffer.from(buffer),
    view: new DataView(buffer),
    truncatedBase: count * recordSize,
  };
}

function decodeAnalysisRecords(packed) {
  const { count, recordSize, bytes, view, truncatedBase } = packedView(
    packed,
    ANALYSIS_MINIMUM_SIZE,
  );
  const records = new Array(count);
  for (let index = 0; index < count; index++) {
    const base = index * recordSize;
    const record = {
      structSize: view.getUint32(base, littleEndian),
      partOfSpeech: view.getUint32(base + 4, littleEndian),
      dialect: view.getUint32(base + 8, littleEndian),
      geographicRegion: view.getUint32(base + 12, littleEndian),
      person: view.getUint32(base + 16, littleEndian),
      number: view.getUint32(base + 20, littleEndian),
      gender: view.getUint32(base + 24, littleEndian),
      grammaticalCase: view.getUint32(base + 28, littleEndian),
      tense: view.getUint32(base + 32, littleEndian),
      mood: view.getUint32(base + 36, littleEndian),
      voice: view.getUint32(base + 40, littleEndian),
      degree: view.getUint32(base + 44, littleEndian),
    };
    let offset = base + NUMBERS_SIZE;
    for (const field of ANALYSIS_TEXT_FIELDS) {
      record[field] = cString(bytes, offset, TEXT_CAPACITY);
      offset += TEXT_CAPACITY;
    }
    record.domains = cString(bytes, offset, DOMAIN_CAPACITY);
    offset += DOMAIN_CAPACITY;
    record.morphFlags = new Uint8Array(
      packed.buffer,
      offset,
      MORPH_FLAG_CAPACITY,
    ).slice();
    record.truncatedFields = view.getUint32(truncatedBase + index * 4, littleEndian);
    records[index] = record;
  }
  return records;
}

function decodeGenerationRecords(packed) {
  const { count, recordSize, bytes, view, truncatedBase } = packedView(
    packed,
    GENERATION_MINIMUM_SIZE,
  );
  const records = new Array(count);
  for (let index = 0; index < count; index++) {
    const base = index * recordSize;
    const textBase = base + NUMBERS_SIZE;
    records[index] = {
      structSize: view.getUint32(base, littleEndian),
      partOfSpeech: view.getUint32(base + 4, littleEndian),
      dialect: view.getUint32(base + 8, littleEndian),
      geographicRegion: view.getUint32(base + 12, littleEndian),
      person: view.getUint32(base + 16, littleEndian),
      number: view.getUint32(base + 20, littleEndian),
      gender: view.getUint32(base + 24, littleEndian),
      grammaticalCase: view.getUint32(base + 28, littleEndian),
      tense: view.getUint32(base + 32, littleEndian),
      mood: view.getUint32(base + 36, littleEndian),
      voice: view.getUint32(base + 40, littleEndian),
      degree: view.getUint32(base + 44, littleEndian),
      surface: cString(bytes, textBase, TEXT_CAPACITY),
      lemma: cString(bytes, textBase + TEXT_CAPACITY, TEXT_CAPACITY),
      morphFlags: new Uint8Array(
        packed.buffer,
        textBase + 2 * TEXT_CAPACITY,
        MORPH_FLAG_CAPACITY,
      ).slice(),
      truncatedFields: view.getUint32(truncatedBase + index * 4, littleEndian),
    };
  }
  return records;
}

export const MorpheusLanguage = {
  Greek: 0,
  Latin: 1,
  Italian: 2,
};

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
};

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
};

export const MorpheusPartOfSpeech = {
  Unknown: 0, Noun: 1, Verb: 2, Adjective: 3, Adverb: 4, Article: 5,
  Pronoun: 6, Numeral: 7, Preposition: 8, Conjunction: 9, Particle: 10,
  Interjection: 11,
};
export const MorpheusPerson = { None: 0, First: 1, Second: 2, Third: 3 };
export const MorpheusNumber = { None: 0, Singular: 1, Dual: 2, Plural: 3 };
export const MorpheusGender = {
  None: 0, Adverbial: 1, Feminine: 2, Masculine: 4, Neuter: 8,
};
export const MorpheusCase = {
  None: 0, Ablative: 1, Accusative: 2, Dative: 4, Genitive: 8,
  Nominative: 16, Vocative: 32,
};
export const MorpheusTense = {
  None: 0, Present: 1, Imperfect: 2, Future: 3, Aorist: 4, Perfect: 5,
  Pluperfect: 6, FuturePerfect: 7, PastAbsolute: 8,
};
export const MorpheusMood = {
  None: 0, Conditional: 1, Gerundive: 2, Imperative: 3, Indicative: 4,
  Infinitive: 5, Optative: 6, Participle: 7, Subjunctive: 8, Supine: 9,
};
export const MorpheusVoice = {
  None: 0, Active: 1, Passive: 2, Middle: 4, MedioPassive: 6, Deponent: 5,
};
export const MorpheusDegree = {
  None: 0, Positive: 1, Comparative: 2, Superlative: 3,
};
export const MorpheusDialect = {
  All: 0, Aeolic: 1, Attic: 2, Doric: 4, Homeric: 8, Ionic: 16,
  Lesbian: 32, NonHomericEpic: 64, Paradigm: 128, Epic: 72, Prose: 256,
};
export const MorpheusGeographicRegion = {
  None: 0, Arcadia: 1, Argolid: 2, Boeotia: 4, Cos: 8, Crete: 16,
  Cyprus: 32, Cyrene: 64, Elis: 128, Heraclea: 256, Laconia: 512,
  Locris: 1024, Megarid: 2048, Phocis: 4096, Rhodes: 8192, Thera: 16384,
};
export const MorpheusTruncatedField = {
  None: 0, Raw: 1 << 0, Workword: 1 << 1, Lemma: 1 << 2,
  Preverb: 1 << 3, Augment: 1 << 4, Stem: 1 << 5, Suffix: 1 << 6,
  Ending: 1 << 7, Crasis: 1 << 8, DictionaryForm: 1 << 9,
  EnglishForm: 1 << 10, RawPreverb: 1 << 11, Domains: 1 << 12,
};

export const MorpheusMorphFlag = {
  SyllAugment: 74, CompOnly: 7, Enclitic: 19, Iterative: 35,
  SuffixAccent: 73, StemAccent: 72, Contracted: 8, PersonName: 52,
  AntepenultAccent: 3, IrregularSuperlative: 34, IrregularComparative: 32,
  NoComparison: 47, ShortPenult: 69, LongPenult: 38, RecessiveAccent: 64,
  AccentOptional: 0, NeedsAccent: 43, RhoEtaIotaAlpha: 66,
  NotInComposition: 45, HasPreverb: 26, Unaugmented: 79, Dissimilation: 13,
  Proclitic: 56, Apocope: 4, IrregularForm: 33, HasAugment: 25,
  QuantityMetathesis: 60, NuMovable: 49, IntervocalicSToH: 29,
  PreverbAugment: 55, Poetic: 53, UncontractedStem: 81, Metathesis: 40,
  ElidedPreverb: 18, IndeclinableForm: 28, RootPreverb: 67, Diminutive: 12,
  Late: 36, Rare: 61, RawPreverb: 62, Early: 17, ShortSubjunctive: 70,
  UnaspiratedPreverb: 78, Reduplication: 65, UncontractedEnding: 80,
  Derivative: 10, AtticReduplication: 5, NoReduplication: 48, NInfix: 50,
  Syncope: 75, Impersonal: 27, NeedsRoughBreathing: 44, NoCircumflex: 46,
  Causal: 6, Intransitive: 30, Tmesis: 77, RawSonant: 63, Prodelision: 57,
  Frequentative: 22, Later: 37, DoubleAugment: 15, DoubleReduplication: 16,
  Desiderative: 11, PresentReduplication: 54, EndsInDigamma: 20,
  GeographicName: 23, DoubledConsonant: 14, IotaIntensive: 31,
  LostAccent: 39, SigmaToCi: 71, ShortEis: 68, ProsToPoti: 58,
  MetaToPeda: 41, ProsToProti: 59, UpoToUpai: 83, ParaToParai: 51,
  UperToUpeir: 82, EnToEni: 21, AlphaPrivative: 2, AlphaCopulative: 1,
  MetricallyLong: 42, DeltaPreverb: 9, TauPreverb: 76, GroupName: 24,
};

const MORPH_FLAG_NAMES = new Map([
  [74, "syllabic-augment"], [7, "compound-only"], [19, "enclitic"],
  [35, "iterative"], [73, "suffix-accent"], [72, "stem-accent"],
  [8, "contracted"], [52, "person-name"], [3, "antepenult-accent"],
  [34, "irregular-superlative"], [32, "irregular-comparative"],
  [47, "no-comparison"], [69, "short-penult"], [38, "long-penult"],
  [64, "recessive-accent"], [0, "accent-optional"], [43, "needs-accent"],
  [66, "rho-eta-iota-alpha"], [45, "not-in-composition"],
  [26, "has-preverb"], [79, "unaugmented"], [13, "dissimilation"],
  [56, "proclitic"], [4, "apocope"], [33, "irregular-form"],
  [25, "has-augment"], [60, "quantity-metathesis"], [49, "nu-movable"],
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

export function hasMorpheusMorphFlag(analysis, flag) {
  if (Array.isArray(analysis)) {
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
  if (!Number.isInteger(flag) || flag < 0) return false;
  const index = Math.floor(flag / 8);
  return index < analysis.morphFlags.length &&
    (analysis.morphFlags[index] & (1 << (flag % 8))) !== 0;
}

const PART_OF_SPEECH_NAMES = [
  [0, "unknown"], [1, "noun"], [2, "verb"], [3, "adjective"],
  [4, "adverb"], [5, "article"], [6, "pronoun"], [7, "numeral"],
  [8, "preposition"], [9, "conjunction"], [10, "particle"],
  [11, "interjection"],
];
const PERSON_NAMES = [[1, "first"], [2, "second"], [3, "third"]];
const NUMBER_NAMES = [[1, "singular"], [2, "dual"], [3, "plural"]];
const GENDER_NAMES = [
  [1, "adverbial"], [2, "feminine"], [4, "masculine"], [8, "neuter"],
];
const CASE_NAMES = [
  [1, "ablative"], [2, "accusative"], [4, "dative"], [8, "genitive"],
  [16, "nominative"], [32, "vocative"],
];
const TENSE_NAMES = [
  [1, "present"], [2, "imperfect"], [3, "future"], [4, "aorist"],
  [5, "perfect"], [6, "pluperfect"], [7, "future-perfect"],
  [8, "past-absolute"],
];
const MOOD_NAMES = [
  [1, "conditional"], [2, "gerundive"], [3, "imperative"],
  [4, "indicative"], [5, "infinitive"], [6, "optative"],
  [7, "participle"], [8, "subjunctive"], [9, "supine"],
];
const VOICE_NAMES = [[1, "active"], [2, "passive"], [4, "middle"]];
const VOICE_EXACT_NAMES = [[6, "medio-passive"], [5, "deponent"]];
const DEGREE_NAMES = [[1, "positive"], [2, "comparative"], [3, "superlative"]];
const DIALECT_NAMES = [
  [1, "aeolic"], [2, "attic"], [4, "doric"], [8, "homeric"],
  [16, "ionic"], [32, "lesbian"], [64, "non-homeric-epic"],
  [128, "paradigm"], [256, "prose"],
];
const DIALECT_NAME_ORDER = [
  "attic", "ionic", "aeolic", "lesbian", "homeric", "doric", "paradigm",
  "non-homeric-epic", "epic", "prose",
];
const REGION_NAMES = [
  [1, "arcadia"], [2, "argolid"], [4, "boeotia"], [8, "cos"],
  [16, "crete"], [32, "cyprus"], [64, "cyrene"], [128, "elis"],
  [256, "heraclea"], [512, "laconia"], [1024, "locris"],
  [2048, "megarid"], [4096, "phocis"], [8192, "rhodes"], [16384, "thera"],
];
const TRUNCATED_FIELD_NAMES = [
  [1 << 0, "raw"], [1 << 1, "workword"], [1 << 2, "lemma"],
  [1 << 3, "preverb"], [1 << 4, "augment"], [1 << 5, "stem"],
  [1 << 6, "suffix"], [1 << 7, "ending"], [1 << 8, "crasis"],
  [1 << 9, "dictionaryForm"], [1 << 10, "englishForm"],
  [1 << 11, "rawPreverb"], [1 << 12, "domains"],
];

function exactName(value, entries) {
  return entries.find(([code]) => code === value)?.[1] ?? null;
}

function maskNames(value, entries, exactEntries = []) {
  const exact = exactName(value, exactEntries);
  if (exact !== null) return [exact];
  return entries.filter(([bit]) => (value & bit) === bit).map(([, name]) => name);
}

function dialectNames(value) {
  let remaining = value;
  const selected = new Set();
  if ((remaining & MorpheusDialect.Epic) === MorpheusDialect.Epic) {
    selected.add("epic");
    remaining &= ~MorpheusDialect.Epic;
  }
  for (const [bit, name] of DIALECT_NAMES) {
    if ((remaining & bit) === bit) selected.add(name);
  }
  return DIALECT_NAME_ORDER.filter((name) => selected.has(name));
}

// The named fields of analyses and generations are frozen arrays shared
// between every record with the same code: a paradigm of thousands of forms
// holds a few dozen distinct values, and building fresh arrays for each form
// made their allocation and collection most of the main thread's work. The
// arrays are read-only, as their types declare; an application that needs to
// change one copies it. A cache stops growing at NAME_CACHE_LIMIT entries and
// then computes uncached, still frozen.
const NAME_CACHE_LIMIT = 4096;
const EMPTY_NAMES = Object.freeze([]);

function nameCache(compute) {
  const cache = new Map();
  return (key) => {
    let names = cache.get(key);
    if (names === undefined) {
      const computed = compute(key);
      names = computed.length === 0 ? EMPTY_NAMES : Object.freeze(computed);
      if (cache.size < NAME_CACHE_LIMIT) cache.set(key, names);
    }
    return names;
  };
}

const cachedDialects = nameCache(dialectNames);
const cachedRegions = nameCache((value) => maskNames(value, REGION_NAMES));
const cachedGenders = nameCache((value) => maskNames(value, GENDER_NAMES));
const cachedCases = nameCache((value) => maskNames(value, CASE_NAMES));
const cachedVoices = nameCache(
  (value) => maskNames(value, VOICE_NAMES, VOICE_EXACT_NAMES),
);
const cachedTruncatedFields = nameCache(
  (value) => maskNames(value, TRUNCATED_FIELD_NAMES),
);
const cachedGenerationTruncatedFields = nameCache((value) => {
  const names = [];
  if (value & MorpheusTruncatedField.Workword) names.push("surface");
  if (value & MorpheusTruncatedField.Lemma) names.push("lemma");
  return names;
});

// Morph flags are keyed by their 11 bytes read as Latin-1, which is exact;
// the names keep the order of MORPH_FLAG_NAMES.
const ZERO_MORPH_FLAGS = "\0".repeat(MORPH_FLAG_CAPACITY);
const cachedMorphFlags = nameCache((key) => {
  const names = [];
  for (const [code, name] of MORPH_FLAG_NAMES) {
    if ((key.charCodeAt(code >> 3) & (1 << (code & 7))) !== 0) names.push(name);
  }
  return names;
});

function morphFlagNames(bytes, offset) {
  const key = bytes.toString("latin1", offset, offset + MORPH_FLAG_CAPACITY);
  return key === ZERO_MORPH_FLAGS ? EMPTY_NAMES : cachedMorphFlags(key);
}

// The twelve numeric fields of a record, read through a Uint32Array when the
// record size keeps them aligned on a little-endian host (every prebuilt
// platform), through the DataView otherwise.
function numberReader(packed, recordSize) {
  if (recordSize % 4 === 0 && littleEndianHost) {
    const words = new Uint32Array(packed.buffer);
    const stride = recordSize / 4;
    return (index, field) => words[index * stride + field];
  }
  const view = new DataView(packed.buffer);
  return (index, field) => view.getUint32(index * recordSize + field * 4, littleEndian);
}

function semanticFields(read, index) {
  return {
    partOfSpeech: exactName(read(index, 1), PART_OF_SPEECH_NAMES) ?? "unknown",
    dialects: cachedDialects(read(index, 2)),
    geographicRegions: cachedRegions(read(index, 3)),
    person: exactName(read(index, 4), PERSON_NAMES),
    grammaticalNumber: exactName(read(index, 5), NUMBER_NAMES),
    genders: cachedGenders(read(index, 6)),
    grammaticalCases: cachedCases(read(index, 7)),
    tense: exactName(read(index, 8), TENSE_NAMES),
    mood: exactName(read(index, 9), MOOD_NAMES),
    voices: cachedVoices(read(index, 10)),
    degree: exactName(read(index, 11), DEGREE_NAMES),
  };
}

// analyze() and generate() decode the packed records straight into the named
// objects, without building the raw records first.
function decodeAnalyses(packed) {
  const { count, recordSize, bytes, view, truncatedBase } = packedView(
    packed,
    ANALYSIS_MINIMUM_SIZE,
  );
  const read = numberReader(packed, recordSize);
  const records = new Array(count);
  for (let index = 0; index < count; index++) {
    const record = semanticFields(read, index);
    let offset = index * recordSize + NUMBERS_SIZE;
    for (const field of ANALYSIS_TEXT_FIELDS) {
      record[field] = cString(bytes, offset, TEXT_CAPACITY);
      offset += TEXT_CAPACITY;
    }
    record.domains = cString(bytes, offset, DOMAIN_CAPACITY);
    offset += DOMAIN_CAPACITY;
    record.morphFlags = morphFlagNames(bytes, offset);
    record.truncatedFields = cachedTruncatedFields(
      view.getUint32(truncatedBase + index * 4, littleEndian),
    );
    records[index] = record;
  }
  return records;
}

function decodeGenerations(packed) {
  const { count, recordSize, bytes, view, truncatedBase } = packedView(
    packed,
    GENERATION_MINIMUM_SIZE,
  );
  const read = numberReader(packed, recordSize);
  const records = new Array(count);
  for (let index = 0; index < count; index++) {
    const record = semanticFields(read, index);
    const textBase = index * recordSize + NUMBERS_SIZE;
    record.surface = cString(bytes, textBase, TEXT_CAPACITY);
    record.lemma = cString(bytes, textBase + TEXT_CAPACITY, TEXT_CAPACITY);
    record.morphFlags = morphFlagNames(bytes, textBase + 2 * TEXT_CAPACITY);
    record.truncatedFields = cachedGenerationTruncatedFields(
      view.getUint32(truncatedBase + index * 4, littleEndian),
    );
    records[index] = record;
  }
  return records;
}

// generate() and generateRaw() return an array that also carries the
// generation result's count of skipped source records, as a read-only,
// non-enumerable property: printing or spreading the array is unchanged.
function withSkippedRecords(records, packed) {
  return Object.defineProperty(records, "skippedRecords", {
    value: packed.skippedRecords,
    enumerable: false,
    writable: false,
    configurable: false,
  });
}

function decodeGenerationResult(packed) {
  return withSkippedRecords(decodeGenerations(packed), packed);
}

function decodeRawGenerationResult(packed) {
  return withSkippedRecords(decodeGenerationRecords(packed), packed);
}

export class MorpheusError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.name = "MorpheusError";
  }
}

function languageName(language) {
  const entry = Object.entries(MorpheusLanguage).find(([, value]) => value === language);
  return entry ? entry[0] : `language ${language}`;
}

function asMorpheusError(error) {
  if (error instanceof MorpheusError) return error;
  if (error instanceof Error && Number.isInteger(error.status)) {
    return new MorpheusError(error.status, error.message);
  }
  return error;
}

function nativeGenerationOptions(options) {
  const resultLimit = options.resultLimit ?? 0;
  if (!Number.isSafeInteger(resultLimit) || resultLimit < 0 ||
      resultLimit > 65_536) {
    throw new RangeError("resultLimit must be an integer from 0 to 65536");
  }
  return {
    resultLimit,
    excludeDuals: options.excludeDuals ? 1 : 0,
    excludePreverbVariants: options.excludePreverbVariants ? 1 : 0,
    partOfSpeech: options.partOfSpeech ?? 0,
    dialect: options.dialect ?? 0,
    geographicRegion: options.geographicRegion ?? 0,
    person: options.person ?? 0,
    number: options.number ?? 0,
    gender: options.gender ?? 0,
    grammaticalCase: options.grammaticalCase ?? 0,
    tense: options.tense ?? 0,
    mood: options.mood ?? 0,
    voice: options.voice ?? 0,
    degree: options.degree ?? 0,
  };
}

export class MorpheusLibrary {
  #native;
  #contexts = 0;
  #closed = false;

  constructor(path) {
    this.#native = addon.openLibrary(
      path instanceof URL ? fileURLToPath(path) : path,
    );
  }

  createContext(stemlibPath, language) {
    if (this.#closed) throw new Error("Morpheus library is closed");
    try {
      const native = addon.openContext(this.#native, stemlibPath, language);
      this.#contexts++;
      return new MorpheusContext(native, () => this.#contexts--);
    } catch (error) {
      const failure = asMorpheusError(error);
      if (!(failure instanceof MorpheusError)) throw failure;
      // Name the stemlib and the language: an incomplete stemlib is the
      // usual cause, such as a Greek-only dataset opened for Latin.
      throw new MorpheusError(
        failure.status,
        `opening ${stemlibPath} for ${languageName(language)} failed: ${failure.message}`,
      );
    }
  }

  close() {
    if (this.#closed) return;
    if (this.#contexts !== 0) {
      throw new Error("Close all Morpheus contexts before the library");
    }
    addon.closeLibrary(this.#native);
    this.#closed = true;
  }

  [Symbol.dispose]() {
    this.close();
  }
}

export class MorpheusContext {
  #native;
  #onClose;
  #tail = Promise.resolve();
  #closed = false;

  constructor(native, onClose) {
    this.#native = native;
    this.#onClose = onClose;
  }

  analyze(betaCode, options = 0n) {
    return this.#enqueue(() => addon.analyze(this.#native, betaCode, options)
      .then(decodeAnalyses, (error) => { throw asMorpheusError(error); }));
  }

  analyzeRaw(betaCode, options = 0n) {
    return this.#enqueue(() => addon.analyze(this.#native, betaCode, options)
      .then(decodeAnalysisRecords, (error) => { throw asMorpheusError(error); }));
  }

  generate(lemma, options = {}) {
    const encoded = nativeGenerationOptions(options);
    return this.#enqueue(() => addon.generate(this.#native, lemma, encoded)
      .then(decodeGenerationResult, (error) => { throw asMorpheusError(error); }));
  }

  generateRaw(lemma, options = {}) {
    const encoded = nativeGenerationOptions(options);
    return this.#enqueue(() => addon.generate(this.#native, lemma, encoded)
      .then(decodeRawGenerationResult, (error) => { throw asMorpheusError(error); }));
  }

  async close() {
    if (this.#closed) return;
    this.#closed = true;
    await this.#tail;
    addon.closeContext(this.#native);
    this.#onClose();
  }

  async [Symbol.asyncDispose]() {
    await this.close();
  }

  #enqueue(operation) {
    if (this.#closed) {
      return Promise.reject(new Error("Morpheus context is closed"));
    }
    const run = this.#tail.then(operation);
    this.#tail = run.then(() => undefined, () => undefined);
    return run;
  }
}
