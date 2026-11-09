<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Release qualification

This checklist defines the independent native-runtime, Node.js-binding,
Python-binding, WebAssembly-binding and data-package release tracks. Native
releases cover the C library, installed metadata, the container, `cruncher`,
and pinned fixture data. Node.js releases cover the ESM facade,
acquisition commands, and three optional Node-API addon packages on npm. Python
releases cover the pure-Python `ctypes` facade and its acquisition commands on
PyPI. WebAssembly releases
cover the Emscripten-compiled runtime module and its JavaScript facade,
published as one package on npm and JSR. Historical standalone utilities are
outside these release contracts. The Deno binding track ended with
`deno-v0.4.3` (`release-deno-0.4.3.md`): the binding, its workflows and its
container target were removed afterwards, and libmorpheus no longer depends on
Deno.

Native releases use `v<version>` tags. Node.js binding releases use
`node-v<version>` tags and declare native compatibility in
`bindings/js/node/internal/native-manifest.js`. Python binding releases use
`python-v<version>` tags and declare compatibility in
`bindings/python/src/libmorpheus/_version.py`. WebAssembly binding releases
use `wasm-v<version>` tags and declare, in
`bindings/js/wasm/internal/version.mjs`, the libmorpheus release and ABI
compiled into the module and the Emscripten release that reproduces it;
unlike the other bindings, this package ships the runtime, so its declared
native version must equal the tagged tree's own. The data acquisition
package uses `data-v<version>` tags and declares its version in
`bindings/js/data/internal/version.js`; it ships neither runtime nor data,
only the pinned upstream revisions it verifies, so it is coupled to the
redistribution policy's reviewed revisions rather than to a native release.
Like the WebAssembly binding it is published to npm and JSR from one
directory (`package.json` and `jsr.json` must agree).
Releases through `0.3.2` predate this separation and used one `v<version>`
tag for the native and Deno tracks.

Each native release records its version and ABI decision in
`release-<version>.md`; binding releases use a track-qualified name such as
`release-node-0.1.3.md` or `release-wasm-0.1.3.md`. The most recent native
release is recorded in `release-0.4.5.md`; the earlier decisions remain
historical evidence.

## 1. Version and compatibility decisions

- Choose the project version and update `project(VERSION ...)` in
  `CMakeLists.txt`.
- Review the diff of `include/morpheus/morpheus.h` and
  `cmake/PublicApi.cmake`.
- Keep `MORPHEUS_ABI_VERSION` and `SOVERSION` unchanged only for compatible
  additions. A removed function, changed signature, reassigned constant, or
  changed `morpheus_analysis` layout requires an explicit ABI/SONAME decision.
- For a Node.js release, update `bindings/js/node/package.json`,
  `MORPHEUS_NODE_VERSION`, and all three `npm/*/package.json` templates
  together. Keep every optional dependency pinned to that exact package
  version, keep the `@libmorpheus/data` dependency pinned to the exact data
  package version the tree carries (a data release that the binding should
  pick up therefore implies a binding release), then review the separately
  declared native release and ABI.
- For a Python release, update `bindings/python/pyproject.toml` and
  `MORPHEUS_PYTHON_VERSION` together, then independently review
  `MORPHEUS_NATIVE_VERSION` and `MORPHEUS_NATIVE_ABI_VERSION`.
- For a WebAssembly release, update `bindings/js/wasm/package.json`,
  `bindings/js/wasm/jsr.json` and `MORPHEUS_WASM_VERSION` together. Keep
  `MORPHEUS_NATIVE_VERSION` equal to `project(VERSION ...)` and
  `MORPHEUS_NATIVE_ABI_VERSION` equal to `MORPHEUS_ABI_VERSION`; a runtime
  change therefore needs a native release first and a WebAssembly release
  after it, from the same commit or a descendant with an unchanged runtime.
  Change `MORPHEUS_EMSCRIPTEN_VERSION` only together with the `emsdk` image
  pinned in `wasm.yml`, `wasm-release.yml` and `test.yml`, and regenerate the
  checked-in preparer modules with it.
- Write release notes that distinguish code changes from stemlib data changes.
- Move the candidate notes in `CHANGELOG.md` from `Unreleased` to a dated
  version heading without changing their technical scope during packaging.

## 2. Source and data provenance

- Start from a clean checkout with recursive submodules initialized.
- Record the Perseids code baseline and Alpheios stemlib commit documented in
  `provenance.md`.
- Exercise `tools/prepare-runtime-data.sh` from a recursive checkout and verify
  the generated index digest documented in `runtime-data.md`.
- Confirm that intended release archives or container contexts include the
  pinned Alpheios submodule content; the native install intentionally does not
  install stem data.
- Review `historical-utilities.md` if any standalone entry point was added or
  reactivated.

## 3. Required CI

The Linux workflow in `.github/workflows/test.yml` deliberately has two
levels. Pull requests run the native CMake and binding jobs. Pushes to `main`
additionally run the optimized build, sanitizers, byte-signedness matrix, and
inherited Makefile compatibility check. Native `v*` tags delegate optimized
package verification to the architecture workflow. Binding tags run the Linux
checks their publication workflow waits for. Superseded runs are cancelled,
except for immutable version-tag runs.

The expensive native architecture workflow in `.github/workflows/platform.yml`
runs weekly, on explicit manual dispatch, and for every native `v*` or Node.js
`node-v*` tag. It covers native Linux aarch64, Alpine x86-64/aarch64, and Apple
Silicon. Manual dispatches can request all three native release-candidate
packages; version tags always build the artifacts needed by their release
track. Packages and checksums are retained as short-lived CI artifacts on
non-tag runs. After a native version tag passes the full platform matrix and
separate Linux CI, the tag workflow publishes only the verified native assets
and benchmark evidence to the native GitHub release.

The Node.js publication workflow runs only for `node-v*` tags or explicit
recovery dispatches. A tag launches both Linux CI and the complete native
platform workflow. The publication job waits for both workflows on the exact
tagged commit, downloads their three qualified addon packages, verifies the
coordinated package set, and tests installation from local tarballs before
contacting npm. It publishes the platform packages first and the facade last.

The Python publication workflow runs only for `python-v*` tags or explicit
recovery dispatches. It waits for Linux CI on the exact commit, where Python
3.11 and 3.14 exercise the ABI fixture and compiled runtime, then builds and
checks one universal wheel plus one source distribution before contacting PyPI.

Scheduled runs first compare the current default-branch SHA with the last
completed weekly run. The architecture jobs are skipped when the SHA is
unchanged and the previous run succeeded. A changed SHA, a previous failure,
the first scheduled run, a manual dispatch, or a version tag always runs the
matrix. Pull requests changing the architecture workflow execute only this
inexpensive decision job and the Linux x86-64 package qualification. Native
ARM, Alpine, and Apple Silicon remain skipped. The same targeted check runs
when shared package-generation or extracted-consumer scripts change.

Before tagging, manually dispatch the architecture workflow for the exact
candidate commit with `package_artifacts` enabled. Inspect the resulting Linux
x86-64 glibc, Linux aarch64 glibc, and macOS arm64 archives and checksums. The
tagged commit must then rebuild those packages and pass every job triggered by
both workflow files:

- native CMake build and CTest;
- ASan/UBSan and ThreadSanitizer;
- signed- and unsigned-`char` conversion builds;
- Alpine x86-64 and aarch64;
- Apple Silicon arm64;
- Node.js and Python binding tests;
- inherited Makefile compatibility.

Documentation-only work does not bypass the Linux documentation and release
metadata checks. Do not broaden path exclusions without checking those
contracts first.

Do not qualify from a partial rerun that omits a failing job. Both Perseids and
Alpheios fixture suites must run where their data prerequisites are available.
A job that built and tested successfully and failed only while uploading its
artifact (the hosted runner could not reach GitHub's artifact storage during
the `v0.4.3` run), or that was cancelled before any step ran because no
hosted runner picked it up (macOS arm64 capacity during the `v0.4.4`
dispatch, three times in a row), is a different case: re-run the failed jobs
of the same run (`gh run rerun <id> --failed`) rather than retagging. The
successful jobs keep their results and artifacts, the re-run job repeats its
whole build and test, and the publication job then runs on the same
attempt. The tag never moves. A tagged run queues independently of a
dispatch and may obtain a runner first; the publication job still waits for
every qualification job of its own run.

## 4. ABI and consumer checks

- `public_symbols` must contain exactly the functions in
  `cmake/PublicApi.cmake` and no imported `exit` or `abort`.
- `public_api_documentation` must confirm that the header, symbol manifest, and
  `public-api.md` cover the same functions.
- The installed CMake consumer must configure, build, link, and run through
  `Morpheus::morpheus`.
- `installed_surface` must confirm that no private header, internal archive,
  static library, or source-tree path enters the installation.
- The installed `pkg-config` consumer must compile, link, and run, and the
  nested-libdir test must resolve the relocated prefix correctly.
- Confirm that the generated project version, package-config version, SONAME,
  and `libmorpheus.pc` version agree.
- Require `release_metadata` to keep the C header, public API documentation,
  changelog, and CMake ABI decisions aligned. `jsr_package_metadata` separately
  keeps the JSR version and the binding's declared native compatibility aligned.
  `node_package_metadata` keeps the Node facade, its native compatibility, and
  all platform package templates aligned. `python_package_metadata` keeps the
  Python distribution, native compatibility, release workflow, and public
  smoke contract aligned. `data_package_metadata` keeps the data acquisition
  package's identity, closed file lists, pinned upstream revisions and
  release decision aligned, requires the files it shares with the Node.js
  binding to stay byte-identical, and forbids any stemlib artifact in its
  tree.

## 5. Runtime artifacts

- Build the `runtime` container target for linux/amd64 and linux/arm64.
- Treat container builds as qualification only. Do not publish an image
  embedding the Alpheios stemlib until its redistribution terms have been
  confirmed; this restriction does not apply to data-free native packages.
- Require the image to contain the canonical Alpheios `gener.index` digest and
  smoke-test `cruncher` in it.
- Inspect the native installation and confirm it contains only the public
  header, shared library, CMake package files, `libmorpheus.pc`, and optional
  `cruncher` executable.
- Require the optimized `Release` CTest job to pass; Debug and sanitizer
  success does not substitute for testing the configuration that is published.
- Produce a versioned JSON benchmark report as described in `benchmarks.md`,
  including source revision, stemlib revision, and compiler metadata. Compare
  it with the previous accepted report on the same controlled hardware and
  investigate material regressions before tagging.
- Pass the final JSON report through `bench/validate.mjs` with the exact
  source, stemlib, compiler, and label values before preserving it as release
  evidence. The benchmark host needs Node.js 20 or later with its Node-API
  headers; `bench/release.sh` builds the addon with the release runtime.
- Generate the native archive with `cpack` and require
  `test-release-package.cmake` to verify its checksum and installed surface.
  The verification must compile and run independent CMake and `pkg-config`
  consumers against the extracted archive rather than the build-tree install.
  The CI artifact is a release candidate, not a published release or a
  cryptographic signature.

## 6. Publish and verify

- Write the GitHub release notes before tagging: `docs/release-notes/<tag>.md`
  (`v0.4.6.md`, `wasm-v0.1.4.md`, `python-v0.2.1.md`…). It is the release body
  as published, so keep it short and for users: one summary line naming the
  package and the native release and ABI it carries, a few bullets on what
  changes for them, an install line for bindings, and a link to the release
  decision. GitHub renders every line break of a release body, so write each
  paragraph and list item on one line. The release title is the tag. The
  `release_notes` test requires notes for the current version of every track,
  rejects hard-wrapped lines and requires the link to the decision when one
  exists; every release workflow (native, WebAssembly, data, Node.js,
  Python) publishes them. Node.js and Python releases carry the files their
  registry serves, checked against the registry's digests
  (`tools/registry-release-assets.py`). Binding releases never become the
  repository's latest release.
- To change the notes or title of a published release, edit the notes file on
  `main` and run the `Release notes` workflow for that tag (`tags: v0.4.5`);
  `tags: all` applies every notes file. Tags and assets are never touched, and
  a tag without a release is only reported: GitHub refuses a workflow token
  the creation of a release on an existing tag whose workflow files differ
  from `main`'s (it requires the `workflows` permission). The Node.js and
  Python tags published before their track had GitHub releases are therefore
  completed from a maintainer's machine with
  `sh tools/backfill-binding-releases.sh` (`gh` with the `workflow` scope),
  which attaches the registry files verified against the registry's digests.
- Integrate the release-preparation branch into `main` with a normal merge
  commit. Do not squash or rebase when the branch contains reviewable release
  history that must remain visible.
- Verify after the merge that the former branch tip is an ancestor of `main`
  with `git merge-base --is-ancestor <release-tip> main`.
- For a native release, tag the exact fully qualified commit as `v<version>`.
  The platform workflow rebuilds all three native archives, adds the accepted
  benchmark evidence, and publishes eight files after the separate tagged Linux
  workflow passes. It does not publish or version any binding.
- Install a produced native package into a fresh prefix and repeat one CMake and
  one `pkg-config` consumer smoke test. Verify the qualification-only container
  by digest on both architectures.
- JSR packages (`@libmorpheus/wasm`, `@libmorpheus/data`) are checked and
  published with JSR's own command-line tool, `npx jsr@0.14.3 publish`, which
  runs the registry's publisher itself; libmorpheus has no Deno dependency.
  Each JSR package must be linked to `defense-humanites/libmorpheus` in its JSR
  settings once, which authorizes tokenless publication through OIDC. Never
  move a published tag.
- npm requires a package to exist before it can acquire a trusted publisher.
  Before the first Node.js release, run `bootstrap-npm.mjs`, inspect its four
  inert `0.0.0` packages, and publish them interactively with npm dist-tag
  `bootstrap`. This one-time reservation must not use `latest`.
- Configure trusted publishing on each package with GitHub organization
  `defense-humanites`, repository `libmorpheus`, workflow filename
  `node-release.yml` (not its full path), and `npm publish` permission. The
  versioned release workflow then needs no long-lived npm token. See npm's
  [trusted publishing documentation](https://docs.npmjs.com/trusted-publishers/)
  for the registry-side settings.
- For a Node.js release, inspect `npm pack --dry-run --ignore-scripts` for the
  facade and every staged platform package. Tag the exact qualified commit as
  `node-v<version>`. The dedicated workflow verifies the existing declared
  native release, waits for tagged CI, publishes through npm OIDC with
  provenance, then automatically triggers `Published npm smoke test`.
- Require the published npm smoke to install into an empty Node.js application,
  acquire the declared native runtime and both audited datasets, and preserve
  Greek and Latin analysis, multiple interpretations, and Greek dual
  generation. It retries only npm visibility; acquisition and semantic failures
  remain hard failures.
- If npm publication stops after only some packages were accepted, do not move
  the tag or change package contents. Manually dispatch `Publish Node.js
  binding` with the existing `node-v<version>` tag while its qualified platform
  artifacts are retained. The workflow skips exact versions already present
  and resumes in dependency-first order.
- Before the first Python publication, create the PyPI pending trusted publisher
  for project `libmorpheus`, GitHub owner `defense-humanites`, repository
  `libmorpheus`, workflow `python-release.yml`, and environment `pypi`. Unlike
  npm, this creates a new project through the first authorized OIDC publication;
  no placeholder package is needed.
- For a Python release, inspect `python -m build` and `twine check`, then tag the
  exact qualified commit as `python-v<version>`. The dedicated workflow verifies
  the declared native release, waits for tagged Linux CI, tests the built wheel
  in isolation, and publishes the wheel and source distribution through PyPI
  trusted publishing.
- Require the automatically triggered PyPI smoke test to install the exact
  public wheel into an empty virtual environment and preserve Greek analysis,
  Latin multiple interpretations, and Greek dual generation against the
  compatible compiled runtime. A recovery dispatch may reuse only the existing
  immutable tag and skips files already accepted by PyPI.
- Before the first WebAssembly publication, link `@libmorpheus/wasm` to
  `defense-humanites/libmorpheus` in the package's JSR settings (done for
  the 0.1.0 preparation). npm, unlike JSR, cannot reserve a name without a
  publication and grants a trusted publisher only to an existing package, so
  stage the inert placeholder with
  `node bindings/js/wasm/tools/bootstrap-npm.mjs --output <dir>`, inspect
  `npm pack --dry-run` in that directory (license texts, NOTICE, README,
  `package.json`; no code, no module), and publish it interactively once with
  `npm publish --access public --tag bootstrap`. npm nevertheless assigns
  `latest` to the first version of a package whatever tag is requested, and
  a single-version package cannot drop it; the first versioned publication
  moves `latest` off the placeholder, so do not announce the package before
  it. Then configure trusted publishing on
  `@libmorpheus/wasm` with GitHub organization `defense-humanites`,
  repository `libmorpheus`, workflow filename `wasm-release.yml` and
  `npm publish` permission; the versioned workflow needs no token.
- For a WebAssembly release, build `dist/` locally with the pinned Emscripten,
  run `npx jsr@0.14.3 publish --dry-run --allow-dirty` and
  `npm pack --dry-run --ignore-scripts` from
  `bindings/js/wasm`, and inspect both file lists: the loader, the module, the
  facade, its types, the version module, licenses and README, and nothing
  else. Tag the exact qualified commit as `wasm-v<version>`. The dedicated
  workflow waits for tagged Linux CI and the WebAssembly qualification,
  rebuilds the module in the pinned `emsdk` container and requires it to
  reproduce the qualified artifact byte for byte, tests the facade from an
  `npm pack` tarball, publishes to npm through OIDC with provenance and to
  JSR, then attaches `morpheus.mjs`, `morpheus.wasm` and `SHA256SUMS` to a
  pre-release GitHub release named by the tag. The package never contains
  linguistic data; `wasm_package_metadata` enforces that at every CI run.
- If one registry accepts the version and the other rejects it, or the job
  times out while JSR is still processing the upload (the `jsr` command returns
  only once JSR has processed it, and JSR may queue it for long), do not move
  the tag. Fix only package metadata on `main` if a registry requires it and
  manually dispatch `Publish WebAssembly binding` with the existing tag; both
  the npm and the JSR steps skip an exact version already present, so the
  dispatch resumes at the GitHub release.
- For a data acquisition package release, run `npm test`,
  `npx jsr@0.14.3 publish --dry-run --allow-dirty` and `npm pack
  --dry-run --ignore-scripts` from `bindings/js/data`, and tag the exact
  qualified commit as `data-v<version>`. `data-release.yml` waits for the
  tagged Linux CI, repeats those checks, acquires a dataset with the command
  installed from the `npm pack` tarball (the data never leaves the runner),
  publishes to npm through OIDC with provenance and to JSR, and attaches the
  tarball and its digest to a pre-release. Both registry steps are
  idempotent, so a recovery dispatch with `release_tag` resumes at the
  release; the npm placeholder and the JSR link are prepared as for the
  WebAssembly binding.
- After publication, exercise the package from JSR itself (`npx jsr add
  @libmorpheus/wasm@<version>` in an empty Node.js project, then the README's
  example against a local stemlib) and record the outcome in the release
  decision.
  JSR transforms published files (it rewrites `.wasm` import names and
  resolves README links against its own pages), so neither the qualification
  workflow nor a local static server stands in for it; 0.1.0 passed both and
  failed from JSR.
- Apply the digest-verification step only if container publication has been
  authorized under the data-distribution policy.
- Preserve the CI run, version/ABI decision, source-data revisions, artifact
  digests, and benchmark comparison with the release notes.
