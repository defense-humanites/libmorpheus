// SPDX-License-Identifier: AGPL-3.0-or-later
//
// The subset of a stemlib that the libmorpheus runtime reads: what open()
// validates (the rule tables, the stem indices and their pre-index sidecars,
// the ending and derivation indices) plus what analysis and generation read
// lazily (the ending tables by stem class, the compound verb list, the
// dictionary entries, and gener.index at the stemlib root). The historical
// sources under stemsrc/, the index production scripts and the per-dataset
// extras are not read at run time.

/** Stemlib directory of each ISO 639-3 language code the datasets declare. */
export const LANGUAGE_DIRECTORIES = Object.freeze({ grc: "Greek", lat: "Latin" });

const RUNTIME_FILE =
  /^(?:rule_files\/[^/]+|steminds\/(?:nomind|vbind)(?:\.lindex)?|endtables\/(?:indices|out)\/[^/]+|derivs\/indices\/derivind|stemsrc\/(?:vbs\.cmp\.ml|lemlist))$/;

/**
 * Whether `path` (relative to the stemlib root, `/`-separated) belongs to
 * the runtime subset of one of `languages` (ISO 639-3 codes).
 */
export function isRuntimeFile(path, languages) {
  if (path === "gener.index") return true;
  const separator = path.indexOf("/");
  if (separator === -1) return false;
  const directory = path.slice(0, separator);
  const language = Object.keys(LANGUAGE_DIRECTORIES)
    .find((code) => LANGUAGE_DIRECTORIES[code] === directory);
  if (language === undefined || !languages.includes(language)) return false;
  return RUNTIME_FILE.test(path.slice(separator + 1));
}

/**
 * Validate a list of ISO 639-3 codes against a dataset's languages. Returns
 * the dataset's own order.
 */
export function selectLanguages(requested, available) {
  if (requested === undefined) return [...available];
  const codes = [...new Set(requested)];
  if (codes.length === 0) throw new TypeError("at least one language is required");
  for (const code of codes) {
    if (!(code in LANGUAGE_DIRECTORIES)) throw new TypeError(`unknown language: ${code}`);
    if (!available.includes(code)) throw new TypeError(`language ${code} is not in this dataset`);
  }
  return available.filter((code) => codes.includes(code));
}
