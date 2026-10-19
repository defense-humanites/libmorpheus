// SPDX-License-Identifier: AGPL-3.0-or-later

/** ABI version this facade understands. */
export const ABI_VERSION: 2;

export const MorpheusLanguage: Readonly<{ Greek: 0; Latin: 1; Italian: 2 }>;
export type MorpheusLanguage = typeof MorpheusLanguage[keyof typeof MorpheusLanguage];

export const MorpheusStatus: Readonly<{
  Ok: 0;
  InvalidArgument: 1;
  AbiMismatch: 2;
  NoMemory: 3;
  InputTooLong: 4;
  OutOfRange: 5;
  InternalError: 6;
  BufferTooSmall: 7;
  StemlibError: 8;
  ResultLimitExceeded: 9;
}>;
export type MorpheusStatus = typeof MorpheusStatus[keyof typeof MorpheusStatus];

/** Bit flags customizing `analyze()`; combine with `|`. */
export const MorpheusOption: Readonly<{
  StrictCase: bigint;
  IgnoreAccents: bigint;
  VerbsOnly: bigint;
  NoCrasis: bigint;
  Quick: bigint;
  HqDictionary: bigint;
  DialectAeolic: bigint;
  DialectAttic: bigint;
  DialectDoric: bigint;
  DialectHomeric: bigint;
  DialectIonic: bigint;
  DialectLesbian: bigint;
  DialectNonHomericEpic: bigint;
  DialectParadigm: bigint;
  DialectEpic: bigint;
  DialectProse: bigint;
}>;

export type MorpheusDialectOption =
  | "Aeolic"
  | "Attic"
  | "Doric"
  | "Homeric"
  | "Ionic"
  | "Lesbian"
  | "NonHomericEpic"
  | "Paradigm"
  | "Epic"
  | "Prose";

/** Named form of the analysis options. `strictCase` defaults to `true`. */
export interface MorpheusAnalyzeOptions {
  strictCase?: boolean;
  ignoreAccents?: boolean;
  verbsOnly?: boolean;
  noCrasis?: boolean;
  quick?: boolean;
  hqDictionary?: boolean;
  dialects?: readonly MorpheusDialectOption[];
}

/** Flags for the historical text output of `analyzeCompat()`. */
export const MorpheusCompatFlag: Readonly<{
  BufferAnalyses: number;
  CheckPreverb: number;
  KeepBeta: number;
  ShowFullInfo: number;
  DatabaseFormat: number;
  DatabaseShort: number;
  StrictCase: number;
  ParseFormat: number;
  PerseusFormat: number;
  EndingIndex: number;
  IgnoreAccents: number;
  LexiconOutput: number;
  LemmaCount: number;
  VerbsOnly: number;
}>;

export const REQUIRED_STEMLIB_FILES: Readonly<{
  common: readonly string[];
  greek: readonly string[];
}>;

export const LANGUAGE_DIRECTORIES: Readonly<Record<MorpheusLanguage, string>>;

/** One structured analysis with the numeric codes of the C ABI. */
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
  /** Bit set of the 84 engine morph flags, least significant bit first. */
  readonly morphFlags: Uint8Array;
  /** Bit mask of `MORPHEUS_TRUNCATED_*` text fields. */
  readonly truncatedFields: number;
}

/** One generated form with the numeric codes of the C ABI. */
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

/** Filters for `generate()`; zero or omitted traits match everything. */
export interface MorpheusGenerationOptions {
  resultLimit?: number;
  excludeDuals?: boolean;
  partOfSpeech?: number;
  dialect?: number;
  geographicRegion?: number;
  person?: number;
  number?: number;
  gender?: number;
  grammaticalCase?: number;
  tense?: number;
  mood?: number;
  voice?: number;
  degree?: number;
}

export interface MorpheusCompatOutput {
  readonly text: string;
  readonly analysisCount: number;
  readonly lemmaCount: number;
}

export class MorpheusError extends Error {
  readonly status: MorpheusStatus | number;
  constructor(status: number, message: string);
}

export class MorpheusContext {
  readonly language: MorpheusLanguage;
  readonly closed: boolean;
  analyze(betaCode: string, options?: bigint | number | MorpheusAnalyzeOptions): MorpheusRawAnalysis[];
  analyzeCompat(betaCode: string, flags?: number): MorpheusCompatOutput;
  generate(lemma: string, options?: MorpheusGenerationOptions): MorpheusRawGeneration[];
  close(): void;
  [Symbol.dispose]?(): void;
}

/** Minimal view of the Emscripten module used by the facade. */
export interface MorpheusEmscriptenModule {
  FS: any;
  HEAPU8: Uint8Array;
  _malloc(size: number): number;
  _free(pointer: number): void;
  UTF8ToString(pointer: number): string;
  stringToUTF8(text: string, pointer: number, maxBytes: number): void;
  lengthBytesUTF8(text: string): number;
  getValue(pointer: number, type: string): number;
  setValue(pointer: number, value: number, type: string): void;
  [symbol: string]: any;
}

export type StemlibEntries =
  | Record<string, Uint8Array | ArrayBuffer | string>
  | Map<string, Uint8Array | ArrayBuffer | string>
  | Iterable<readonly [string, Uint8Array | ArrayBuffer | string]>;

export interface FetchStemlibOptions {
  root?: string;
  fetch?: typeof fetch;
  concurrency?: number;
}

export class Morpheus {
  readonly module: MorpheusEmscriptenModule;
  readonly fs: any;
  readonly version: string;
  readonly abiVersion: number;
  readonly analysisSize: number;
  readonly generationSize: number;
  statusMessage(status: number): string;
  mountDirectory(hostPath: string, mountPoint?: string): string;
  writeStemlib(entries: StemlibEntries, root?: string): string;
  fetchStemlib(baseUrl: string | URL, paths: Iterable<string>, options?: FetchStemlibOptions): Promise<string>;
  static requiredFiles(language: MorpheusLanguage): string[];
  open(options: { stemlib?: string; language: MorpheusLanguage }): MorpheusContext;
  closeAll(): void;
}

export interface CreateMorpheusOptions {
  /** Already imported default export of `morpheus.mjs`. */
  factory?: (options?: Record<string, unknown>) => Promise<MorpheusEmscriptenModule>;
  /** Location of `morpheus.mjs` when `factory` is omitted. */
  moduleUrl?: string | URL;
  /** Options forwarded to the Emscripten factory (`locateFile`, `wasmBinary`, ...). */
  moduleOptions?: Record<string, unknown>;
}

export function createMorpheus(options?: CreateMorpheusOptions): Promise<Morpheus>;
export default createMorpheus;
