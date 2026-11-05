// SPDX-License-Identifier: AGPL-3.0-or-later

import { createHash } from "node:crypto";
import { lstat, mkdir, rm, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { promisify } from "node:util";
import { gunzip } from "node:zlib";

import { parseTarArchive } from "./archive.js";
import { MORPHEUS_DATA_SCHEMA_VERSION, MORPHEUS_DATASETS } from "./data-manifest.js";
import { prepareGenerIndex } from "./gener-runtime.js";
import { isRuntimeFile, selectLanguages } from "./runtime-subset.js";
import { MORPHEUS_DATA_VERSION } from "./version.js";

const gunzipAsync = promisify(gunzip);
const MAX_COMPRESSED_SIZE = 64 * 1024 * 1024;
const MAX_UNCOMPRESSED_SIZE = 256 * 1024 * 1024;

/** Name of the provenance receipt written at the root of the output. */
export const RECEIPT_FILE = "MORPHEUS-DATA.json";
/** Name of the file manifest written at the root of the output on request. */
export const MANIFEST_FILE = "stemlib-manifest.json";
/** Schema of the file manifest. */
export const MORPHEUS_MANIFEST_SCHEMA_VERSION = 1;

export function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function safeRelativePath(path) {
  if (path === "" || path.startsWith("/") || path.includes("\\") || path.includes("\0")) {
    throw new Error(`unsafe archive path: ${path}`);
  }
  const components = path.split("/");
  if (components.some((component) => component === "" || component === "." || component === "..")) {
    throw new Error(`unsafe archive path: ${path}`);
  }
  return components.join("/");
}

function treeDigest(lines) {
  lines.sort((left, right) => {
    const leftPath = left.slice(66);
    const rightPath = right.slice(66);
    return leftPath < rightPath ? -1 : leftPath === rightPath ? 0 : 1;
  });
  return sha256(new TextEncoder().encode(`${lines.join("\n")}\n`));
}

function extractArchiveDataset(archive, definition) {
  const dataRoot = `${definition.archiveRoot}${definition.dataPrefix}`;
  const licensePath = `${definition.archiveRoot}${definition.licensePath}`;
  const paths = new Set();
  const files = new Map();
  const digestLines = [];
  let license;
  for (const entry of parseTarArchive(archive)) {
    if (entry.path === licensePath) {
      if (entry.type !== "0") throw new Error("upstream license is not a file");
      license = entry.content;
      continue;
    }
    if (!entry.path.startsWith(dataRoot)) continue;
    const relative = entry.path.slice(dataRoot.length).replace(/\/$/, "");
    if (relative === "") continue;
    const path = safeRelativePath(relative);
    if (entry.type === "5") continue;
    if (entry.type !== "0") throw new Error(`unsupported dataset archive entry: ${entry.path}`);
    if (paths.has(path)) throw new Error(`duplicate dataset path: ${path}`);
    paths.add(path);
    files.set(path, entry.content);
    digestLines.push(`${sha256(entry.content)}  ${path}`);
  }
  if (paths.size !== definition.fileCount) {
    throw new Error(`${definition.name} archive contains ${paths.size} dataset files; expected ${definition.fileCount}`);
  }
  const actualTree = treeDigest(digestLines);
  if (actualTree !== definition.treeSha256) {
    throw new Error(`${definition.name} dataset digest mismatch: ${actualTree}`);
  }
  if (license === undefined || sha256(license) !== definition.licenseSha256) {
    throw new Error(`${definition.name} upstream license digest mismatch`);
  }
  return { files, license };
}

async function readLimited(response, limit, description) {
  if (!response.ok || response.body === null) {
    throw new Error(`${description} download failed: HTTP ${response.status}`);
  }
  const chunks = [];
  let size = 0;
  for await (const chunk of response.body) {
    size += chunk.length;
    if (size > limit) throw new Error(`${description} exceeds size limit`);
    chunks.push(chunk);
  }
  return Buffer.concat(chunks, size);
}

async function downloadArchive(definition, fetcher) {
  const response = await fetcher(definition.archiveUrl, { redirect: "error" });
  const compressed = await readLimited(response, MAX_COMPRESSED_SIZE, `${definition.name} dataset`);
  return gunzipAsync(compressed, { maxOutputLength: MAX_UNCOMPRESSED_SIZE });
}

async function pathExists(path) {
  try {
    await lstat(path);
    return true;
  } catch (error) {
    if (error?.code === "ENOENT") return false;
    throw error;
  }
}

/**
 * The files to write for `options` out of the verified `files`: the whole
 * tree, or the runtime subset of the selected languages. Returns a Map in
 * the dataset's path order.
 */
export function selectFiles(files, subset, languages) {
  if (subset === "full") return new Map(files);
  if (subset !== "runtime") throw new TypeError(`unsupported subset: ${subset}`);
  const selected = new Map();
  for (const [path, content] of files) {
    if (isRuntimeFile(path, languages)) selected.set(path, content);
  }
  return selected;
}

async function writeFiles(files, directory) {
  for (const [path, content] of files) {
    const destination = join(directory, ...path.split("/"));
    await mkdir(dirname(destination), { recursive: true });
    await writeFile(destination, content, { flag: "wx" });
  }
}

function manifestOf(files, receipt) {
  const entries = [...files]
    .sort(([left], [right]) => (left < right ? -1 : left === right ? 0 : 1))
    .map(([path, content]) => ({ path, size: content.length, sha256: sha256(content) }));
  return {
    schema: MORPHEUS_MANIFEST_SCHEMA_VERSION,
    dataset: receipt.dataset,
    revision: receipt.source.revision,
    subset: receipt.subset.name,
    languages: receipt.languages,
    files: entries,
  };
}

export async function acquireMorpheusDataWithDependencies(options, dependencies) {
  const definition = dependencies.datasets[options.dataset];
  if (definition === undefined) throw new TypeError(`unsupported Morpheus dataset: ${options.dataset}`);
  if (options.withGener && !definition.generation) {
    throw new TypeError(`dataset ${definition.name} does not support experimental generation`);
  }
  const subset = options.subset ?? "full";
  if (subset !== "full" && subset !== "runtime") throw new TypeError(`unsupported subset: ${subset}`);
  const languages = selectLanguages(options.languages, definition.languages);
  if (options.withGener && !languages.includes("grc")) {
    throw new TypeError("--with-gener requires Greek among the selected languages");
  }
  const output = resolve(options.output);
  if (await pathExists(output)) throw new Error(`output path already exists: ${output}`);
  await mkdir(output);
  try {
    const dataset = extractArchiveDataset(await downloadArchive(definition, dependencies.fetch), definition);
    const written = selectFiles(dataset.files, subset, languages);
    let indexSha256 = null;
    let supportSource = null;
    if (options.withGener) {
      const supportDefinition = dependencies.datasets.perseids;
      if (supportDefinition === undefined) {
        throw new Error("Perseids support dataset is unavailable");
      }
      const supportDataset = extractArchiveDataset(
        await downloadArchive(supportDefinition, dependencies.fetch),
        supportDefinition,
      );
      const index = await prepareGenerIndex(dataset.files, supportDataset.files, sha256);
      indexSha256 = sha256(index);
      written.set("gener.index", index);
      supportSource = {
        repository: supportDefinition.repository,
        revision: supportDefinition.revision,
        archiveUrl: supportDefinition.archiveUrl,
      };
    }
    await writeFiles(written, output);
    await writeFile(join(output, "UPSTREAM-LICENSE"), dataset.license, { flag: "wx" });
    const subsetLines = [...written].map(([path, content]) => `${sha256(content)}  ${path}`);
    const receipt = {
      schema: MORPHEUS_DATA_SCHEMA_VERSION,
      packageVersion: MORPHEUS_DATA_VERSION,
      dataset: definition.name,
      languages,
      source: {
        repository: definition.repository,
        revision: definition.revision,
        archiveUrl: definition.archiveUrl,
      },
      files: { count: definition.fileCount, treeSha256: definition.treeSha256 },
      subset: { name: subset, count: written.size, treeSha256: treeDigest(subsetLines) },
      generation: {
        experimental: true,
        available: options.withGener === true,
        indexSha256,
        supportSource,
      },
      manifest: options.manifest ? MANIFEST_FILE : null,
    };
    if (options.manifest) {
      await writeFile(
        join(output, MANIFEST_FILE),
        `${JSON.stringify(manifestOf(written, receipt), null, 2)}\n`,
        { flag: "wx" },
      );
    }
    await writeFile(join(output, RECEIPT_FILE), `${JSON.stringify(receipt, null, 2)}\n`, { flag: "wx" });
    return receipt;
  } catch (error) {
    try {
      await rm(output, { recursive: true, force: true });
    } catch (cleanupError) {
      throw new AggregateError([error, cleanupError], `data acquisition and cleanup both failed for ${output}`);
    }
    throw error;
  }
}

export function acquireMorpheusData(options) {
  return acquireMorpheusDataWithDependencies(options, { datasets: MORPHEUS_DATASETS, fetch });
}
