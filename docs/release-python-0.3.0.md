<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Python binding 0.3.0 release decision

Version 0.3.0 of the Python binding declares native libmorpheus **0.5.0**
(C ABI 2). It supersedes 0.2.2 for the generation changes of that release
and of the new generation index, and exposes the count of skipped
generation records. It is the first release qualified on Python 3.15. This
document records the intended contract and, in its last section, the
publication.

## Why a new version

- **Native 0.5.0** ([release-0.5.0.md](release-0.5.0.md)). A lemma no
  longer fails because of one record the engine cannot generate. Generated
  records carry the degree and flags analysis reports, and surfaces lose
  the stem hyphen. `libmorpheus-native` and `libmorpheus-setup` acquire the
  `v0.5.0` archives.
- **The skipped count.** `generate()` and `generate_raw()` return a
  `Generations` tuple, a subclass of `tuple` that compares and unpacks as
  before, with a `skipped_records` attribute. With an earlier native
  library, which lacks the function, the count is zero. That is exact there,
  since that library fails the request instead of skipping a record.
- **The generation index.** `libmorpheus-data --gener-index` verifies the
  index of the generation contract, `a2f97677…`, the one
  `@libmorpheus/data` 0.2.0 prepares
  ([release-data-0.2.0.md](release-data-0.2.0.md)), and refuses the
  earlier `5aa76d8c…`. Generation returns the forms analysis accepts for a
  lemma, not a reference paradigm
  ([public-api.md](public-api.md#greek-lemma-generation)).

The minor version follows the project's rule within 0.x: requests that
failed now succeed, generation results change, and the accepted index
changes.

## Python 3.15

The Linux qualification matrix adds Python 3.15 to 3.11 and 3.14, and the
distribution declares it. Before this decision, the unit tests (25), the
runtime smoke test, generation over the Alpheios index from four threads
and `uv build` passed under CPython 3.15.2.

The first CI run of the matrix found that `build` 1.3.0, which the
workflows pinned, fails under 3.15 before building anything: its help
formatter rejects the `color` argument that 3.15's `argparse` passes. Both
the Linux CI and the publication workflow now pin `build` 1.6.1, which
supports 3.15. Under 3.11 the two versions build the same wheel and the
same sdist file list.

## Distribution, behavioral and licensing contracts

Unchanged from [0.2.2](release-python-0.2.2.md), except for the skipped
count, the pinned index and Python 3.15 above.

## Qualification and publication

As for 0.2.2: tagged Linux CI on the exact commit, now with Python 3.11,
3.14 and 3.15. Then `python-release.yml` verifies that `v0.5.0` is
published and publishes through PyPI trusted publishing. It creates the
`python-v0.3.0` GitHub release from `docs/release-notes/python-v0.3.0.md`
and the distributions PyPI serves, and triggers the published PyPI smoke
test.

## Publication record

- Tag: `python-v0.3.0`, created by the maintainer on 2026-11-11 on
  `a54d752f7bebb1b6bc3a9fee1a95f43a234d2743`, the merge of this decision,
  together with `node-v0.3.0`.
- Tagged Linux CI: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/43084850039),
  with Python 3.11, 3.14 and 3.15.
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/43084850046);
  `libmorpheus` 0.3.0 is on PyPI, declaring Python 3.11 to 3.15; the wheel
  `libmorpheus-0.3.0-py3-none-any.whl` has SHA-256
  `a7c74b2e491cee2f1daa9d462595b00d4f479d3949efd3c30641dd0d6f35f298` and
  the source distribution
  `733f4e4bcb907443fb4062c834f7e10c4f98395c2e4749d124ed59b13cac24be`.
- GitHub release: [`python-v0.3.0`](https://github.com/defense-humanites/libmorpheus/releases/tag/python-v0.3.0),
  published at 19:20 UTC with the two distributions PyPI serves and
  `SHA256SUMS`.
- Published PyPI smoke test: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/43086297928):
  the public wheel repeated the analysis and generation checks against a
  runtime built from the tagged sources, and its published
  `libmorpheus-setup` acquired the declared runtime 0.5.0 and the Perseids
  data from the public endpoints.
- Check from PyPI under CPython 3.15.2: the wheel installed in an empty
  environment reports binding 0.3.0 and native 0.5.0. With the `v0.5.0`
  library and the index that `@libmorpheus/data` 0.2.0 prepared
  (`a2f97677…`), δίδωμι generates 3,636 records with `skipped_records` 1.
