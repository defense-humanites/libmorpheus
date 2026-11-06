// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Release benchmark validator: node bench/validate.mjs REPORT --label LABEL
// --revision SHA --stemlib-revision SHA --compiler COMPILER

import { readFile } from "node:fs/promises";

import { isMainModule } from "./main-module.mjs";

import { validateReleaseBenchmark } from "./report.mjs";

/** @param {readonly string[]} arguments_ */
export function parseCommandLine(arguments_) {
  const reportPath = arguments_[0];
  if (!reportPath || reportPath.startsWith("--")) {
    throw new Error(
      "usage: validate.mjs REPORT --label LABEL --revision SHA " +
        "--stemlib-revision SHA --compiler COMPILER",
    );
  }
  /** @type {Map<string, string>} */
  const values = new Map();
  for (let index = 1; index < arguments_.length; index += 2) {
    const option = arguments_[index];
    const value = arguments_[index + 1];
    if (!option?.startsWith("--") || value === undefined) {
      throw new Error("release benchmark options require name-value pairs");
    }
    if (values.has(option)) throw new Error(`duplicate option: ${option}`);
    values.set(option, value);
  }
  /** @param {string} option */
  const take = (option) => {
    const value = values.get(option);
    if (value === undefined) throw new Error(`${option} is required`);
    values.delete(option);
    return value;
  };
  const expected = {
    label: take("--label"),
    sourceRevision: take("--revision"),
    stemlibRevision: take("--stemlib-revision"),
    compiler: take("--compiler"),
  };
  if (values.size) throw new Error(`unknown option: ${values.keys().next().value}`);
  return { reportPath, expected };
}

/** @param {readonly string[]} arguments_ */
export async function main(arguments_) {
  const { reportPath, expected } = parseCommandLine(arguments_);
  const report = JSON.parse(await readFile(reportPath, "utf8"));
  validateReleaseBenchmark(report, expected);
  console.log(`validated release benchmark: ${reportPath}`);
}

if (import.meta.main ?? isMainModule(import.meta.url)) {
  await main(process.argv.slice(2));
}
