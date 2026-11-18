<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Python binding 0.4.0 release decision

Version 0.4.0 of the Python binding declares native libmorpheus **0.6.0**
(C ABI 2). It supersedes 0.3.0 for the generation changes of that release
and of the new generation index, and passes the new preverb-variant flag.
This document records the intended contract and, in its last section, the
publication.

## Why a new version

- **Native 0.6.0** ([release-0.6.0.md](release-0.6.0.md)).
  - `generate()` accepts the compound verbs analysis reports and returns
    their preverb variants.
  - It also returns the unaugmented indicatives, movable ν and accented
    clitics that analysis reads, each form with the dialects all its parts
    allow.
  - On the AGDT 2.1 treebank, the readings analysis gives that generation
    returns rise from 82.8 % to 95.2 %.
  - The default limit, which the binding uses when no `result_limit` is
    given, becomes 65,536 records.
  - `libmorpheus-native` and `libmorpheus-setup` acquire the `v0.6.0`
    archives.
- **`exclude_preverb_variants`.** `GenerationOptions` gains this field,
  which leaves a compound's preverb variants out. The binding passes it as
  the new flag. Native 0.5.0 rejects that flag, so the field needs the
  declared runtime.
- **The generation index.** `libmorpheus-data --gener-index` verifies the
  index that `@libmorpheus/data` 0.3.0 prepares, `8ba328ca…`
  ([release-data-0.3.0.md](release-data-0.3.0.md)). That index keeps the
  compound-only stems under reserved keys. The binding refuses 0.2.0's
  `a2f97677…`.

The minor version follows the project's rule within 0.x: generation results
change, the options gain a field, and the accepted index changes.

## Distribution, behavioral and licensing contracts

Unchanged from [0.3.0](release-python-0.3.0.md), except for the field and
the pinned index above. It is qualified on Python 3.11, 3.14 and 3.15.
Analysis results are unchanged except one reading of χρῆς
([release-0.6.0.md](release-0.6.0.md#results-and-compatibility)).

## Qualification and publication

As for 0.3.0:
1. Tagged Linux CI runs on the exact commit, with Python 3.11, 3.14 and
   3.15.
2. `python-release.yml` verifies that `v0.6.0` is published, then publishes
   through PyPI trusted publishing.
3. It creates the `python-v0.4.0` GitHub release from
   `docs/release-notes/python-v0.4.0.md` and the distributions PyPI serves.
4. It triggers the published PyPI smoke test.

## Publication record

- Tag: `python-v0.4.0`, created by the maintainer on 2026-11-18 on
  `d36f39532a83a29ee0f3e93a38e47c8bdd14fd6a`, the merge of this decision,
  together with `node-v0.4.0`.
- Tagged Linux CI: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/44271687221),
  with Python 3.11, 3.14 and 3.15.
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/44271686991).
  `libmorpheus` 0.4.0 is on PyPI and declares Python 3.11 to 3.15.

  | File | SHA-256 |
  | --- | --- |
  | `libmorpheus-0.4.0-py3-none-any.whl` | `73a0a46b83e0aac0bc9b9cfe2f5a0650d19b3ccf27a3e27fb033ef827fa32aae` |
  | `libmorpheus-0.4.0.tar.gz` | `13af8056b01397757da37d3be0516fba73454b532ccc2061400656917563f8cc` |
- GitHub release: [`python-v0.4.0`](https://github.com/defense-humanites/libmorpheus/releases/tag/python-v0.4.0),
  published at 09:06 UTC with the two distributions PyPI serves and
  `SHA256SUMS`.
- Published PyPI smoke test: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/44272820710).
  The public wheel repeated the analysis and generation checks against a
  runtime built from the tagged sources. Its published `libmorpheus-setup`
  acquired the declared runtime 0.6.0 and the Perseids data.
- Check from PyPI under CPython 3.15.2: the wheel installed in an empty
  environment reports binding 0.4.0 and native 0.6.0. With the `v0.6.0`
  library and the index that `@libmorpheus/data` 0.3.0 prepared
  (`8ba328ca…`), it gives the counts of native 0.6.0:
  - δίδωμι generates 3,317 records, with `skipped_records` 1;
  - καταβάλλω generates 5,825 records, and 3,040 with
    `exclude_preverb_variants`.

  Its `libmorpheus-data --gener-index` refuses the index of data 0.2.0
  (`a2f97677…`) before any download.
