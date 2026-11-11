<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Python binding 0.3.0 release decision

Version 0.3.0 of the Python binding declares native libmorpheus **0.5.0**
(C ABI 2). It supersedes 0.2.2 for the generation changes of that release
and of the new generation index, and exposes the count of skipped
generation records. It is the first release qualified on Python 3.15. This
document records the intended contract; it does not authorize or record
creation of the `python-v0.3.0` tag.

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
