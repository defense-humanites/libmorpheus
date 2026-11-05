#!/usr/bin/env node
// SPDX-License-Identifier: AGPL-3.0-or-later
// @ts-self-types="./data.d.ts"

import { acquireMorpheusData, MANIFEST_FILE, RECEIPT_FILE } from "./internal/data-internal.js";
import { MORPHEUS_DATASETS } from "./internal/data-manifest.js";
import { isMainModule } from "./internal/main-module.js";
import { isRuntimeFile, LANGUAGE_DIRECTORIES } from "./internal/runtime-subset.js";
import { MORPHEUS_DATA_VERSION } from "./internal/version.js";

export {
  acquireMorpheusData,
  isRuntimeFile,
  LANGUAGE_DIRECTORIES,
  MANIFEST_FILE,
  MORPHEUS_DATA_VERSION,
  MORPHEUS_DATASETS,
  RECEIPT_FILE,
};

function takeValue(args, index, name) {
  const value = args[index + 1];
  if (value === undefined || value.startsWith("--")) throw new TypeError(`${name} requires a value`);
  return value;
}

export function parseMorpheusDataArgs(args) {
  let dataset;
  let output;
  let subset;
  let languages;
  let withGener = false;
  let manifest = false;
  let help = false;
  const options = {
    "--dataset": (value) => { dataset = value; },
    "--output": (value) => { output = value; },
    "--subset": (value) => { subset = value; },
    "--languages": (value) => { languages = value.split(",").map((code) => code.trim()).filter(Boolean); },
  };
  for (let index = 0; index < args.length; index++) {
    const argument = args[index];
    const equals = argument.indexOf("=");
    const name = equals === -1 ? argument : argument.slice(0, equals);
    if (argument === "--help" || argument === "-h") help = true;
    else if (argument === "--with-gener") withGener = true;
    else if (argument === "--manifest") manifest = true;
    else if (name in options) {
      if (equals === -1) {
        options[name](takeValue(args, index, name));
        index++;
      } else options[name](argument.slice(equals + 1));
    } else throw new TypeError(`unknown argument: ${argument}`);
  }
  if (help) {
    return {
      dataset: dataset ?? "alpheios",
      output: output ?? ".",
      subset: subset ?? "full",
      languages,
      withGener,
      manifest,
      help,
    };
  }
  if (dataset !== "alpheios" && dataset !== "perseids") {
    throw new TypeError(dataset === undefined ? "--dataset is required" : `unsupported dataset: ${dataset}`);
  }
  if (output === undefined || output === "") throw new TypeError("--output is required");
  subset ??= "full";
  if (subset !== "full" && subset !== "runtime") throw new TypeError(`unsupported subset: ${subset}`);
  if (languages !== undefined) {
    if (languages.length === 0) throw new TypeError("--languages requires at least one code");
    for (const code of languages) {
      if (!(code in LANGUAGE_DIRECTORIES)) throw new TypeError(`unknown language: ${code}`);
      if (!MORPHEUS_DATASETS[dataset].languages.includes(code)) {
        throw new TypeError(`language ${code} is not in the ${dataset} dataset`);
      }
    }
  }
  if (withGener && dataset !== "alpheios") {
    throw new TypeError("--with-gener is supported only for alpheios");
  }
  return { dataset, output, subset, languages, withGener, manifest, help };
}

function usage() {
  return [
    "Usage: libmorpheus-data --dataset <alpheios|perseids> --output <directory>",
    "                        [--subset <full|runtime>] [--languages <grc,lat>]",
    "                        [--with-gener] [--manifest]",
    "",
    "Downloads a pinned upstream Morpheus stem dataset, verifies its tree and",
    "license, and writes it into a new directory with a provenance receipt",
    `(${RECEIPT_FILE}). Alpheios provides Greek analysis and experimental`,
    "generation; Perseids provides Greek and Latin analysis.",
    "",
    "  --subset runtime   write only the files the libmorpheus runtime reads",
    "  --languages        keep only these ISO 639-3 languages (default: all)",
    "  --with-gener       build the experimental Greek generation index",
    `  --manifest         also write ${MANIFEST_FILE} (paths, sizes, SHA-256)`,
  ].join("\n");
}

// Node.js below 24.2 has no import.meta.main; the fallback compares the
// executable path (an npm bin symlink included). Deno and Bun set
// import.meta.main, which also covers `deno run jsr:@libmorpheus/data`.
if (import.meta.main ?? isMainModule(import.meta.url)) {
  try {
    const options = parseMorpheusDataArgs(process.argv.slice(2));
    if (options.help) console.log(usage());
    else {
      const receipt = await acquireMorpheusData(options);
      console.log(
        `Prepared ${receipt.dataset} data in ${options.output} ` +
          `(${receipt.subset.count} files, ${receipt.subset.name} subset, ${receipt.languages.join(", ")}` +
          `${receipt.generation.available ? ", gener.index" : ""}${receipt.manifest ? `, ${receipt.manifest}` : ""}).`,
      );
    }
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    console.error(usage());
    process.exitCode = 1;
  }
}
