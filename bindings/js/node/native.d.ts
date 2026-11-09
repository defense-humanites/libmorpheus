// SPDX-License-Identifier: AGPL-3.0-or-later

export const MORPHEUS_NATIVE_VERSION: "0.4.6";
export const MORPHEUS_NATIVE_ABI_VERSION: 2;

export interface AcquireMorpheusNativeOptions {
  readonly output: string;
}

export interface MorpheusNativeReceipt {
  readonly schema: number;
  readonly packageVersion: string;
  readonly nativeVersion: string;
  readonly abiVersion: number;
  readonly target: string;
  readonly asset: string;
  readonly archiveSha256: string;
  readonly sourceUrl: string;
  readonly libraryPath: string;
}

export interface MorpheusNativeCommandLineOptions extends AcquireMorpheusNativeOptions {
  readonly help: boolean;
}

export function acquireMorpheusNative(options: AcquireMorpheusNativeOptions): Promise<MorpheusNativeReceipt>;
export function nativeLibraryPath(root: string): string;
export function parseMorpheusNativeArgs(args: readonly string[]): MorpheusNativeCommandLineOptions;
