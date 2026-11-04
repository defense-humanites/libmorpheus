// SPDX-License-Identifier: AGPL-3.0-or-later

export type MorpheusDatasetName = "alpheios" | "perseids";
export type MorpheusLanguageCode = "grc" | "lat";
export type MorpheusDataSubset = "full" | "runtime";

export interface MorpheusDatasetDefinition {
  readonly name: MorpheusDatasetName;
  readonly repository: string;
  readonly revision: string;
  readonly archiveUrl: string;
  readonly archiveRoot: string;
  readonly dataPrefix: string;
  readonly fileCount: number;
  readonly treeSha256: string;
  readonly licensePath: string;
  readonly licenseSha256: string;
  readonly languages: readonly MorpheusLanguageCode[];
  readonly generation: boolean;
}

export interface AcquireMorpheusDataOptions {
  readonly dataset: MorpheusDatasetName;
  readonly output: string;
  /** `full` (default) writes the whole dataset; `runtime` only what libmorpheus reads. */
  readonly subset?: MorpheusDataSubset;
  /** Languages to keep (default: all of the dataset). */
  readonly languages?: readonly MorpheusLanguageCode[];
  /** Build the experimental Greek generation index (Alpheios only). */
  readonly withGener?: boolean;
  /** Also write `stemlib-manifest.json` listing every written file. */
  readonly manifest?: boolean;
}

export interface MorpheusDataSource {
  readonly repository: string;
  readonly revision: string;
  readonly archiveUrl: string;
}

export interface MorpheusDataReceipt {
  readonly schema: number;
  readonly packageVersion: string;
  readonly dataset: MorpheusDatasetName;
  readonly languages: readonly MorpheusLanguageCode[];
  readonly source: MorpheusDataSource;
  /** The verified upstream tree. */
  readonly files: { readonly count: number; readonly treeSha256: string };
  /** What was written, `gener.index` included when built. */
  readonly subset: { readonly name: MorpheusDataSubset; readonly count: number; readonly treeSha256: string };
  readonly generation: {
    readonly experimental: true;
    readonly available: boolean;
    readonly indexSha256: string | null;
    readonly supportSource: MorpheusDataSource | null;
  };
  /** Name of the written manifest, or `null`. */
  readonly manifest: string | null;
}

export interface MorpheusManifestEntry {
  readonly path: string;
  readonly size: number;
  readonly sha256: string;
}

/** Contents of `stemlib-manifest.json`. */
export interface MorpheusStemlibManifest {
  readonly schema: number;
  readonly dataset: MorpheusDatasetName;
  readonly revision: string;
  readonly subset: MorpheusDataSubset;
  readonly languages: readonly MorpheusLanguageCode[];
  readonly files: readonly MorpheusManifestEntry[];
}

export interface MorpheusDataCommandLineOptions extends AcquireMorpheusDataOptions {
  readonly help: boolean;
}

export const MORPHEUS_DATA_VERSION: string;
export const MORPHEUS_DATASETS: Readonly<Record<MorpheusDatasetName, MorpheusDatasetDefinition>>;
export const LANGUAGE_DIRECTORIES: Readonly<Record<MorpheusLanguageCode, string>>;
export const RECEIPT_FILE: "MORPHEUS-DATA.json";
export const MANIFEST_FILE: "stemlib-manifest.json";

export function acquireMorpheusData(options: AcquireMorpheusDataOptions): Promise<MorpheusDataReceipt>;
export function parseMorpheusDataArgs(args: readonly string[]): MorpheusDataCommandLineOptions;
/** Whether a stemlib-relative path belongs to the runtime subset of `languages`. */
export function isRuntimeFile(path: string, languages: readonly MorpheusLanguageCode[]): boolean;
