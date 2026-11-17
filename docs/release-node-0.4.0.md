<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Node.js binding 0.4.0 release decision

Version 0.4.0 of the Node.js binding declares native libmorpheus **0.6.0**
(C ABI 2) and pins `@libmorpheus/data` **0.3.0**. It supersedes 0.3.0 for
the generation changes of those releases, and passes the new
preverb-variant flag. This document records the intended contract.

## Why a new version

- **Native 0.6.0** ([release-0.6.0.md](release-0.6.0.md)).
  - `generate()` accepts the compound verbs analysis reports and returns
    their preverb variants.
  - It also returns the unaugmented indicatives, movable ν and accented
    clitics that analysis reads, each form with the dialects all its parts
    allow.
  - On the AGDT 2.1 treebank, the readings analysis gives that generation
    returns rise from 82.8 % to 95.2 %.
  - The default limit, which the binding uses when no `resultLimit` is
    given, becomes 65,536 records.
  - `libmorpheus-native` and `libmorpheus-setup` acquire the `v0.6.0`
    archives.
- **`excludePreverbVariants`.** `generate()` and `generateRaw()` accept
  this option, which leaves a compound's preverb variants out. The addon
  passes it as the new flag, and the types declare it. Native 0.5.0 rejects
  the flag, so the option needs the declared runtime.
- **`@libmorpheus/data` 0.3.0** ([release-data-0.3.0.md](release-data-0.3.0.md)).
  `libmorpheus-data --with-gener` and `libmorpheus-setup --with-gener` now
  prepare the index that keeps the compound-only stems under reserved keys
  (`8ba328ca…`). Compound verbs need it.

The minor version follows the project's rule within 0.x: generation results
change, and the facade gains an option.

## Distribution, behavioral and licensing contracts

Unchanged from [0.3.0](release-node-0.3.0.md), except for the option above.
Analysis results are unchanged except one reading of χρῆς
([release-0.6.0.md](release-0.6.0.md#results-and-compatibility)).
Generation takes longer for a large verb: the 0.6.0 benchmark measured
maximal warm generation 51 to 78 % slower through this binding.

## Qualification and publication

The steps are those of 0.3.0:
1. Tagged Linux CI and platform runs pass on the exact commit.
2. `node-release.yml` verifies that `v0.6.0` is published.
3. It publishes the three platform packages before the facade, through
   npm OIDC with provenance.
4. It creates the `node-v0.4.0` GitHub release from
   `docs/release-notes/node-v0.4.0.md` and the tarballs npm serves.
5. It triggers the published npm smoke test.

`v0.6.0` and `data-v0.3.0` must be published first.
