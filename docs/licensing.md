<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Licensing boundary

This repository is a mixed-license work. A file's SPDX identifier controls when
present; files without one remain under the repository's default MPL-2.0 license
in `LICENSE`.

## AGPL-3.0-or-later

The independently written normalized API, Deno integration, and project support
work are licensed under AGPL-3.0-or-later:

- `include/morpheus/morpheus.h`;
- `src/api/`;
- the AGPL-marked JavaScript binding files under `bindings/js/`;
- the marked CMake, benchmark, release-workflow, and test sources;
- the marked project documentation and changelog.

These files expose context and result ownership, status handling, normalized
analysis records, and language bindings without publishing internal stemlib
identifiers or storage encodings. `docs/license-inventory.md` records the
file-level provenance rationale. `CMakePresets.json` uses an adjacent `.license`
file because JSON does not permit an inline SPDX comment.

## MPL-2.0

The inherited analyzer and all code that preserves or translates its historical
representations remain under MPL-2.0, including:

- the inherited implementation outside the explicitly AGPL directories;
- internal headers extracted from or coupled to that implementation;
- `src/bridge/legacy_values.c` and `src/bridge/legacy_values.h`;
- `include/morpheus/compat.h` and `src/compat/compat.c`;
- the historical `cruncher` behavior.

The bridge is intentionally the only structured-API component that knows both
the public values and the historical numeric encodings. This placement does not
relicense inherited expressions; it isolates them in MPL-covered files.

The Deno and Node data commands bundle an internal WebAssembly build of the
MPL-covered generation source preparer and an MPL-marked copy of its qualified
corpus manifest. Emscripten runtime portions are distributed under their
permissive license recorded in each package's `LICENSES/EMSCRIPTEN.txt`. The
WebAssembly module neither changes the public API nor moves historical code
across the MPL/AGPL boundary.

## License texts and provenance

Canonical texts are available in `LICENSES/MPL-2.0.txt` and
`LICENSES/AGPL-3.0-or-later.txt`. The root `LICENSE` remains MPL-2.0 so that
unmarked inherited files keep their existing treatment. The root
`LICENSE-AGPL-3.0-or-later` is an exact copy of the canonical AGPL text so that
GitHub exposes both licenses in its repository metadata; it does not change the
file-level boundary. Source ancestry is recorded in
[the provenance record](provenance.md); the current classification is recorded
in [the license inventory](license-inventory.md).

No file in this repository is relicensed from MPL-2.0 to CC BY-SA.
