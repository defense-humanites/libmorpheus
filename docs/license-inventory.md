<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# License inventory

This inventory records the conservative file-level boundary used by the current
repository. It does not change the license of any expression inherited from
Perseids or any data obtained from Alpheios.

## Independently written files: AGPL-3.0-or-later

The following groups were introduced after the imported Perseids baseline and
have no counterpart at the same path in either audited upstream tree:

- the normalized public ABI in `include/morpheus/morpheus.h` and `src/api/`;
- the independently written JavaScript bindings and their local documentation
  under `bindings/js/`, except the explicitly MPL-marked generation preparer
  components;
- the CMake build, package metadata, benchmark tooling, and platform-release
  workflow identified by AGPL SPDX notices;
- the C and CMake tests introduced by the modernization work;
- the deterministic generation-index builder under `tools/`;
- the project changelog and the documents under `docs/`.

`CMakePresets.json` cannot contain comments, so its license is recorded in the
adjacent `CMakePresets.json.license` file.
The same sidecar convention applies to the machine-readable
`tools/stemlib-redistribution-policy.json` contract.

The classification is based on the preserved Git history: the imported Perseids
baseline is commit `ab6898ffed335fc6169fa02c9940657a9b5a78e0`, and the
independently written support files first appear in later project commits.
Absence from an upstream path is not used on its own to relicense code that
reorganizes or translates historical implementation details.

## Inherited or derived files: MPL-2.0

The following remain MPL-2.0 even where the current path was created locally:

- all inherited implementation files and later modifications to them;
- internal headers that extract declarations or state from the inherited engine;
- the legacy-value bridge and compatibility formatter;
- the offline generation-source preparer and its internal derivation engine,
  whose continuation and morphology semantics are adapted from the inherited
  generator;
- the internal generation service under `src/gener/`, whose construction of
  historical `gk_word` values and generator ownership rules adapt the inherited
  engine;
- the internal generation normalizer under `src/bridge/`, which translates
  inherited generator records and preserves their historical distinctions;
- `tools/stemlib_constraints.py`, which is a byte-compatible translation of
  the inherited Greek nominal constraint script;
- inherited workflow, container, README, and repository configuration files;
- `test/fixture.json`, `test/alpheios-fixture.json`, `test/gener-fixture.tsv`,
  the generation-index and generation-source fixtures, and the pinned Alpheios
  data submodule;
- `tools/gener-corpus-manifest.tsv`, which records the ordered paths and
  checksums of derived corpus inputs;
- `tools/gener-corpus-exceptions.tsv`, which records qualified anomalies in
  those inherited inputs;
- `tools/gener-derivation-manifest.tsv` and the generation-derivation fixtures,
  which record and exercise inherited rule data and behavior.

The same MPL treatment applies to the Deno and Node copies of the generation
corpus manifest and compiled preparer under `bindings/js/*/internal/`. The
compiled preparer also contains the permissively licensed Emscripten runtime;
its accompanying license text is included in each standalone binding package.

The root `LICENSE` remains the default for every unmarked file. Explicit MPL
notices on boundary files prevent their accidental inclusion in the AGPL set.
The root `LICENSE-AGPL-3.0-or-later` mirrors the canonical text under
`LICENSES/` solely for repository-level discovery and does not alter that
default or any file classification.

## Future PerseusDL-based repository

This inventory makes no MPL-to-CC change. A future repository built from a
separately accepted PerseusDL baseline will require a new inventory and must not
infer its licensing from this one.
