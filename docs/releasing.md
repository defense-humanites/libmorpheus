<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Release qualification

This checklist defines the independent native-runtime, Deno-binding,
Node.js-binding, and Python-binding release tracks. Native releases cover the C
library, installed metadata, containers, `cruncher`, and pinned fixture data.
Deno releases cover the TypeScript binding, its acquisition commands,
standalone archive, and JSR package. Node.js releases cover the ESM facade,
acquisition commands, and three optional Node-API addon packages on npm. Python
releases cover the pure-Python `ctypes` facade on PyPI. Historical standalone
utilities are outside these release contracts.

Native releases use `v<version>` tags. Deno binding releases use
`deno-v<version>` tags and declare the compatible native release and ABI in
`bindings/js/deno/internal/version.ts`. Node.js binding releases use
`node-v<version>` tags and declare native compatibility in
`bindings/js/node/internal/native-manifest.js`. Python binding releases use
`python-v<version>` tags and declare compatibility in
`bindings/python/src/libmorpheus/_version.py`. Releases through `0.3.2` predate
this separation and used one `v<version>` tag for the native and Deno tracks.

Each native release records its version and ABI decision in
`release-<version>.md`; binding releases use a track-qualified name such as
`release-node-0.1.0.md`. The current native candidate is recorded in
`release-0.4.0.md`; the earlier decisions remain historical evidence.

## 1. Version and compatibility decisions

- Choose the project version and update `project(VERSION ...)` in
  `CMakeLists.txt`.
- Review the diff of `include/morpheus/morpheus.h` and
  `cmake/PublicApi.cmake`.
- Keep `MORPHEUS_ABI_VERSION` and `SOVERSION` unchanged only for compatible
  additions. A removed function, changed signature, reassigned constant, or
  changed `morpheus_analysis` layout requires an explicit ABI/SONAME decision.
- For a Deno release, update `bindings/js/deno/jsr.json` and
  `MORPHEUS_DENO_VERSION` together. Review `MORPHEUS_NATIVE_VERSION` and
  `MORPHEUS_NATIVE_ABI_VERSION` independently; they identify the already
  published native release acquired by the binding.
- Confirm that the Deno `ABI_VERSION` and native structure declarations match
  the binding's declared native ABI. They need not match a newer native ABI
  being developed concurrently on `main`.
- For a Node.js release, update `bindings/js/node/package.json`,
  `MORPHEUS_NODE_VERSION`, and all three `npm/*/package.json` templates
  together. Keep every optional dependency pinned to that exact package
  version, then review the separately declared native release and ABI.
- For a Python release, update `bindings/python/pyproject.toml` and
  `MORPHEUS_PYTHON_VERSION` together, then independently review
  `MORPHEUS_NATIVE_VERSION` and `MORPHEUS_NATIVE_ABI_VERSION`.
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
levels. Pull requests run the native CMake and Deno jobs. Pushes to `main`
additionally run the optimized build, sanitizers, byte-signedness matrix, and
inherited Makefile compatibility check. Native `v*` tags delegate optimized
package verification to the architecture workflow. Deno `deno-v*` tags run the
Linux binding checks before their dedicated publication workflow builds the
standalone source archive. Superseded runs are cancelled, except for immutable
version-tag runs.

The expensive native architecture workflow in `.github/workflows/platform.yml`
runs weekly, on explicit manual dispatch, and for every native `v*` or Node.js
`node-v*` tag. It covers native Linux aarch64, Alpine x86-64/aarch64, and Apple
Silicon. Manual dispatches can request all three native release-candidate
packages; version tags always build the artifacts needed by their release
track. Packages and checksums are retained as short-lived CI artifacts on
non-tag runs. After a native version tag passes the full platform matrix and
separate Linux CI, the tag workflow publishes only the verified native assets
and benchmark evidence to the native GitHub release.

The Deno publication workflow runs only for `deno-v*` tags. It requires Linux
CI on the tagged commit, verifies that the declared native `v<version>` release
and all six native archive files exist, builds the standalone binding archive,
publishes a separate non-latest GitHub release, and then publishes JSR.

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
- Deno type checking and FFI tests;
- inherited Makefile compatibility.

Documentation-only work does not bypass the Linux documentation and release
metadata checks. Do not broaden path exclusions without checking those
contracts first.

Do not qualify from a partial rerun that omits a failing job. Both Perseids and
Alpheios fixture suites must run where their data prerequisites are available.

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
  smoke contract aligned.

## 5. Runtime artifacts

- Build the runtime and `deno-runtime` container targets for linux/amd64 and
  linux/arm64.
- Treat container builds as qualification only. Do not publish an image
  embedding the Alpheios stemlib until its redistribution terms have been
  confirmed; this restriction does not apply to data-free native packages.
- Require both images to contain the canonical Alpheios `gener.index` digest.
  Require `deno-runtime` to contain no copied Deno binding: applications must
  consume the normal JSR dependency. Smoke-test `cruncher`, then run real Deno
  analysis and experimental generation from JSR against the prepared stemlib,
  including a dual-form assertion, rather than merely checking that Deno starts.
- Inspect the native installation and confirm it contains only the public
  header, shared library, CMake package files, `libmorpheus.pc`, and optional
  `cruncher` executable.
- Require the optimized `Release` CTest job to pass; Debug and sanitizer
  success does not substitute for testing the configuration that is published.
- Produce a versioned JSON benchmark report as described in `benchmarks.md`,
  including source revision, stemlib revision, and compiler metadata. Compare
  it with the previous accepted report on the same controlled hardware and
  investigate material regressions before tagging.
- Pass the final JSON report through `bench/validate.ts` with the exact source,
  stemlib, compiler, and label values before preserving it as release evidence.
- Generate the native archive with `cpack` and require
  `test-release-package.cmake` to verify its checksum and installed surface.
  The verification must compile and run independent CMake and `pkg-config`
  consumers against the extracted archive rather than the build-tree install.
  The CI artifact is a release candidate, not a published release or a
  cryptographic signature.

## 6. Publish and verify

- Integrate the release-preparation branch into `main` with a normal merge
  commit. Do not squash or rebase when the branch contains reviewable release
  history that must remain visible.
- Verify after the merge that the former branch tip is an ancestor of `main`
  with `git merge-base --is-ancestor <release-tip> main`.
- For a native release, tag the exact fully qualified commit as `v<version>`.
  The platform workflow rebuilds all three native archives, adds the accepted
  benchmark evidence, and publishes eight files after the separate tagged Linux
  workflow passes. It does not publish or version the Deno binding.
- Install a produced native package into a fresh prefix and repeat one CMake and
  one `pkg-config` consumer smoke test. Verify the qualification-only container
  by digest on both architectures.
- For a Deno release, run `deno publish --dry-run` from `bindings/js/deno` and
  inspect the exact file list. Require `jsr.json` to match
  `MORPHEUS_DENO_VERSION`; verify that the independent
  `MORPHEUS_NATIVE_VERSION` release exists with the declared ABI.
- Tag the qualified binding commit as `deno-v<version>`. The dedicated workflow
  waits for Linux CI, publishes `libmorpheus-deno-<version>.tar.gz` and its
  checksum in a separate GitHub release, then publishes the same version to
  JSR. Neither binding artifact embeds a native library or stem data.
- Before the first publication, link `@libmorpheus/deno` to
  `defense-humanites/libmorpheus` in the package's JSR settings. This one-time
  association authorizes tokenless GitHub Actions publication through OIDC.
- Do not move any published tag. If JSR rejects metadata after the
  Deno GitHub release succeeds and that version is still unpublished, correct
  only `bindings/js/deno/jsr.json` on `main` and manually dispatch
  `Recover JSR publication` with the `deno-v<version>` tag. The recovery refuses
  broader binding changes.
- After JSR publication, manually dispatch `Published JSR smoke test` with the
  exact package version. It starts with an empty Deno application and obtains
  the public JSR package, its declared native archive, Alpheios data plus
  generation index, and Perseids data. Require Greek and Latin analysis plus
  experimental Greek generation to pass before closing the Deno release.
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
- Apply the digest-verification step only if container publication has been
  authorized under the data-distribution policy.
- Preserve the CI run, version/ABI decision, source-data revisions, artifact
  digests, and benchmark comparison with the release notes.
