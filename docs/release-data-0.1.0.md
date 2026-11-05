<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Data acquisition package 0.1.0 release decision

`@libmorpheus/data` 0.1.0 is the first release of the data acquisition
package, `bindings/js/data/`. It extracts the `libmorpheus-data` command and
`acquireMorpheusData()` library from the Node.js binding, where they had been
reachable only by installing a native binding, and adds what a WebAssembly
or browser deployment needs from them. This document records the intended
contract; it does not authorize or record creation of the `data-v0.1.0` tag.

## Release record

- Package version: **0.1.0**
- Datasets: Alpheios Greek at `4632415fe93c85e9fdca47a0c5a13f31385f0023`,
  Perseids Greek and Latin at `ab6898ffed335fc6169fa02c9940657a9b5a78e0`,
  the revisions the [redistribution gate](stemlib-redistribution.md)
  reviewed
- Generation preparer: the checked-in WebAssembly build shared byte for
  byte with the Deno and Node.js bindings; generated `gener.index` digest
  `5aa76d8c86c54af5121a3cce506ecaa57d14c6667ac0f091efd164ddfa9822d6`
- Registries: npm (`package.json`) and JSR (`jsr.json`) from the same
  directory, as for the WebAssembly binding. The package uses only `node:`
  modules that Deno and Bun provide: its fixture-based tests pass unchanged
  under Deno 2.9 and Bun 1.4, and `deno publish --dry-run` reports nothing.
  `import.meta.main` (Deno, Bun, Node.js 24.2+) makes
  `deno run -A jsr:@libmorpheus/data …` run the command; older Node.js
  falls back to the executable-path check.

## What the package is, and is not

The package **contains no linguistic data** and never carries any: it
downloads a pinned upstream archive from `codeload.github.com`, verifies the
complete dataset tree and the upstream license text against digests pinned
in `internal/data-manifest.js`, and writes the result into a new directory
with that license and a provenance receipt (`MORPHEUS-DATA.json`). The
datasets remain distributed by their upstream projects under their own
terms; the redistribution gate stays closed and `data_package_metadata`
fails on any stemlib artifact in the package tree or its manifest. A
distinct package name would be used for a dataset the gate ever qualifies.

## Contract

- **Command and API.** `libmorpheus-data --dataset <alpheios|perseids>
  --output <directory> [--subset <full|runtime>] [--languages <grc,lat>]
  [--with-gener] [--manifest]`, and `acquireMorpheusData(options)` with the
  same options. The Node.js binding's command of the same name accepts a
  subset of these arguments and writes the same receipt fields plus
  `subset` and `manifest`.
- **Runtime subset.** `--subset runtime` writes only the files the
  libmorpheus runtime reads, the set the WebAssembly binding's README
  documents: `rule_files/`, `steminds/{nomind,vbind}{,.lindex}`,
  `endtables/{indices,out}/`, `derivs/indices/derivind`,
  `stemsrc/{vbs.cmp.ml,lemlist}` per language, and `gener.index` at the root
  when built. Measured on the pinned datasets: 275 files and 10 MiB for
  Perseids (both languages), 156 files and 19 MiB for Alpheios with
  `gener.index`. The receipt records the subset's own tree digest next to
  the verified upstream tree's.
- **Languages.** `--languages` keeps a subset of a dataset's languages
  (ISO 639-3 `grc`, `lat`); generation requires `grc`.
- **Manifest.** `--manifest` writes `stemlib-manifest.json` (schema 1:
  dataset, revision, subset, languages, and each written file's path, size
  and SHA-256) for `fetchStemlib()`, bundler rules and `writeStemlib()`
  callers.
- **Verification.** Fixture-based tests cover the full and runtime subsets,
  the manifest, language selection, the CLI and the cleanup of a failed
  acquisition; the runtime-subset predicate is checked against every file
  the WebAssembly facade validates and reads lazily. Linux CI acquires both
  pinned datasets from upstream, rebuilds `gener.index` and checks its
  digest, and analyzes one form per language over the runtime subset with
  the native runtime.
- **Relation to the Node.js binding.** Until `@libmorpheus/node` depends on
  this package, both carry the archive reader, the dataset and generation
  manifests, the generation runtime and the preparer; `data_package_metadata`
  requires those files to be byte-identical. The Node.js binding's own
  `libmorpheus-data` is unchanged in this release and will be replaced by a
  dependency on this package in a later Node.js release.
- **Licensing.** AGPL-3.0-or-later for the package; the preparer embeds
  MPL-2.0 Morpheus code compiled with the MIT-licensed Emscripten runtime,
  with both texts under `LICENSES/`, as in the Node.js binding.

## Publication

On an authorized `data-v0.1.0` tag, `data-release.yml` (the WebAssembly
track's workflow without its module rebuild) verifies the tag against the
version module and both manifests, runs `data_package_metadata`, waits for
the tagged Linux CI, tests the package under Node.js and Deno, dry-runs both
manifests, installs the `npm pack` tarball in a scratch project and acquires
the Perseids Latin runtime subset with the installed command (the data
stays on the runner), then publishes to npm through OIDC with provenance
and to JSR — both steps skip a version already present — and attaches the
tarball and its SHA-256 to a `data-v0.1.0` GitHub pre-release. The
published tarball's integrity is recorded in this document afterwards.

npm grants a trusted publisher only to an existing package, so a 0.0.0
placeholder (`node bindings/js/data/tools/bootstrap-npm.mjs --output <dir>`,
then `npm publish --tag bootstrap` from that directory) must first be
published manually; as for the WebAssembly binding, npm will also give it
`latest` until 0.1.0 replaces it. JSR reserves the name when the package is
linked to the repository and to `data-release.yml`. After publication the
command must be exercised from JSR itself (`deno run -A
jsr:@libmorpheus/data --dataset perseids --subset runtime --output …`),
since JSR transforms the files it serves.

## Remaining authorization

Before publication, a maintainer must:

1. publish the npm placeholder and configure the trusted publisher for
   `data-release.yml`; link `@libmorpheus/data` on JSR to the repository
   and that workflow;
2. confirm the tagged Linux CI run on the candidate commit;
3. explicitly authorize creation of `data-v0.1.0`;
4. after publication, run the JSR end-to-end check above and record its
   outcome here.
