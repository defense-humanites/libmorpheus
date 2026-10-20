#!/usr/bin/env node
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Stage the inert 0.0.0 placeholder that reserves @libmorpheus/wasm on npm.
// npm grants a trusted publisher only to an existing package, so the first
// publication is a manual, interactive `npm publish` of this placeholder
// under the `bootstrap` dist-tag; every real version then comes from
// wasm-release.yml through OIDC. The placeholder carries no code and no
// module, only the license texts and an explanatory README.

import { cp, mkdir, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const bindingDirectory = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const packageName = "@libmorpheus/wasm";

export async function stageNpmBootstrapPackage(outputArgument) {
  if (outputArgument === undefined || outputArgument === "") {
    throw new TypeError("an output directory is required");
  }
  const directory = resolve(outputArgument);
  await mkdir(directory, { recursive: false });
  const packageJson = {
    name: packageName,
    version: "0.0.0",
    description: "Reserved for the official libmorpheus WebAssembly binding",
    license: "AGPL-3.0-or-later",
    repository: {
      type: "git",
      url: "https://github.com/defense-humanites/libmorpheus.git",
      directory: "bindings/js/wasm",
    },
    publishConfig: { access: "public" },
    files: ["LICENSE", "NOTICE", "README.md"],
  };
  await Promise.all([
    cp(join(bindingDirectory, "LICENSE"), join(directory, "LICENSE")),
    cp(join(bindingDirectory, "NOTICE"), join(directory, "NOTICE")),
    writeFile(
      join(directory, "package.json"),
      `${JSON.stringify(packageJson, null, 2)}\n`,
      { flag: "wx" },
    ),
    writeFile(
      join(directory, "README.md"),
      `# ${packageName}\n\n` +
        "Version 0.0.0 only reserves this official package name so npm " +
        "trusted publishing can be configured. Install a later version; " +
        "this placeholder contains no executable code and no WebAssembly " +
        "module.\n",
      { flag: "wx" },
    ),
  ]);
  return { directory, name: packageName, version: "0.0.0" };
}

function parseArgs(args) {
  if (args.length === 2 && args[0] === "--output" && args[1] !== "") {
    return args[1];
  }
  throw new TypeError("usage: node tools/bootstrap-npm.mjs --output <directory>");
}

if (process.argv[1] !== undefined &&
    import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const staged = await stageNpmBootstrapPackage(parseArgs(process.argv.slice(2)));
    console.log(`${staged.name}@${staged.version}: ${staged.directory}`);
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  }
}
