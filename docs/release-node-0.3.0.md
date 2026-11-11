<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Node.js binding 0.3.0 release decision

Version 0.3.0 of the Node.js binding declares native libmorpheus **0.5.0**
(C ABI 2) and pins `@libmorpheus/data` **0.2.0**. It supersedes 0.2.0 for
the generation changes of those releases, and exposes the count of skipped
generation records. This document records the intended contract; it does
not authorize or record creation of the `node-v0.3.0` tag.

## Why a new version

- **Native 0.5.0** ([release-0.5.0.md](release-0.5.0.md)). A lemma no
  longer fails because of one record the engine cannot generate. Generated
  records carry the degree and flags analysis reports, and surfaces lose
  the stem hyphen. `libmorpheus-native` and `libmorpheus-setup` acquire the
  `v0.5.0` archives.
- **The skipped count.** The arrays that `generate()` and `generateRaw()`
  return keep their type and gain a read-only, non-enumerable
  `skippedRecords` property. The addon's record encoding becomes 2, and the
  facade requires it. Loaded with an earlier native library, which lacks
  the function, the binding reports zero. That is exact there, since that
  library fails the request instead of skipping a record.
- **`@libmorpheus/data` 0.2.0** ([release-data-0.2.0.md](release-data-0.2.0.md)).
  `libmorpheus-data --with-gener` and `libmorpheus-setup --with-gener` now
  prepare the index of the generation contract (`a2f97677…`). Generation
  returns the forms analysis accepts for a lemma, not a reference paradigm
  ([public-api.md](public-api.md#greek-lemma-generation)).

The minor version follows the project's rule within 0.x: requests that
failed now succeed, and generation results change.

## Distribution, behavioral and licensing contracts

Unchanged from [0.2.0](release-node-0.2.0.md), except for the skipped
count and the addon's record encoding above.

## Qualification and publication

As for 0.2.0: tagged Linux CI and platform runs on the exact commit. Then
`node-release.yml` verifies that `v0.5.0` is published and publishes the
three platform packages before the facade, through npm OIDC with
provenance. It creates the `node-v0.3.0` GitHub release from
`docs/release-notes/node-v0.3.0.md` and the tarballs npm serves, and
triggers the published npm smoke test. `v0.5.0` and `data-v0.2.0` must be
published first.
