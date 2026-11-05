#!/usr/bin/env node
// SPDX-License-Identifier: AGPL-3.0-or-later

import { lstat, rm } from "node:fs/promises";

import { acquireMorpheusData } from "@libmorpheus/data";
import {
  acquireMorpheusNativeWithDependencies,
  defaultNativeAcquisitionDependencies,
} from "./internal/native-internal.js";
import { setupMorpheusWithDependencies } from "./internal/setup-internal.js";
import { isMainModule } from "./internal/main-module.js";

async function pathExists(path) {
  try {
    await lstat(path);
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") return false;
    throw error;
  }
}

export function setupMorpheus(options) {
  const nativeDependencies = defaultNativeAcquisitionDependencies();
  return setupMorpheusWithDependencies(options, {
    pathExists,
    remove: rm,
    acquireNative: (nativeOptions) =>
      acquireMorpheusNativeWithDependencies(nativeOptions, nativeDependencies),
    acquireData: acquireMorpheusData,
  });
}

function takeValue(args, index, name) {
  const value = args[index + 1];
  if (value === undefined || value.startsWith("--")) throw new TypeError(`${name} requires a value`);
  return value;
}

export function parseMorpheusSetupArgs(args) {
  let dataset;
  let nativeOutput = "./morpheus-native";
  let dataOutput = "./morpheus-data";
  let withGener = false;
  let help = false;
  for (let index = 0; index < args.length; index++) {
    const argument = args[index];
    if (argument === "--help" || argument === "-h") help = true;
    else if (argument === "--with-gener") withGener = true;
    else if (argument === "--dataset") {
      dataset = takeValue(args, index, "--dataset");
      index++;
    } else if (argument.startsWith("--dataset=")) dataset = argument.slice("--dataset=".length);
    else if (argument === "--native-output") {
      nativeOutput = takeValue(args, index, "--native-output");
      index++;
    } else if (argument.startsWith("--native-output=")) nativeOutput = argument.slice("--native-output=".length);
    else if (argument === "--data-output") {
      dataOutput = takeValue(args, index, "--data-output");
      index++;
    } else if (argument.startsWith("--data-output=")) dataOutput = argument.slice("--data-output=".length);
    else throw new TypeError(`unknown argument: ${argument}`);
  }
  if (help) return { dataset: dataset ?? "alpheios", nativeOutput, dataOutput, withGener, help };
  if (dataset !== "alpheios" && dataset !== "perseids") {
    throw new TypeError(dataset === undefined ? "--dataset is required" : `unsupported dataset: ${dataset}`);
  }
  if (withGener && dataset !== "alpheios") throw new TypeError("--with-gener is supported only with alpheios");
  return { dataset, nativeOutput, dataOutput, withGener, help };
}

function usage() {
  return `Usage: libmorpheus-setup --dataset <alpheios|perseids> [--with-gener] [--native-output <directory>] [--data-output <directory>]`;
}

if (isMainModule(import.meta.url)) {
  try {
    const options = parseMorpheusSetupArgs(process.argv.slice(2));
    if (options.help) console.log(usage());
    else {
      const receipt = await setupMorpheus(options);
      console.log(`Installed native library: ${receipt.nativeLibraryPath}`);
      console.log(`Installed stem data: ${receipt.dataOutput}`);
    }
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    console.error(usage());
    process.exitCode = 1;
  }
}
