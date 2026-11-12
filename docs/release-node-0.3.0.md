<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Node.js binding 0.3.0 release decision

Version 0.3.0 of the Node.js binding declares native libmorpheus **0.5.0**
(C ABI 2) and pins `@libmorpheus/data` **0.2.0**. It supersedes 0.2.0 for
the generation changes of those releases, and exposes the count of skipped
generation records. This document records the intended contract and, in its
last section, the publication.

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

## Publication record

- Tag: `node-v0.3.0`, created by the maintainer on 2026-11-11 on
  `a54d752f7bebb1b6bc3a9fee1a95f43a234d2743`, the merge of this decision,
  together with `python-v0.3.0`. It was first pushed on `667ca57`, the
  merge that preceded this decision, whose tree still declares 0.2.0: the
  [publication run](https://github.com/defense-humanites/libmorpheus/actions/runs/43084377825)
  failed at its version check before contacting npm, and the tag's Linux CI
  and platform runs were cancelled. Nothing was published under 0.3.0, so
  the tag was deleted and recreated on `a54d752`
  ([releasing.md](releasing.md#3-required-ci)).
- Tagged qualification: [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/43084783701)
  and [platform](https://github.com/defense-humanites/libmorpheus/actions/runs/43084783972)
  (Linux x86_64 and aarch64 glibc, macOS arm64, Alpine x86_64 and aarch64),
  both passed at the first attempt.
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/43084783817);
  the four packages are on npm at 0.3.0 with `latest` moved, tarball
  integrity `sha512-RmkpGZS7taEb57/193W9tOL7YxTjnuibHxZAR16LtKkTKbdRrUCMNre2A2PZusHhzUMHZy8Iw7CvXmOpCGe7Dg==`
  (`@libmorpheus/node`),
  `sha512-zpnGkhe1kKq2zaW23AsQLqOxnzSs8QSxg2i0r6cMJtJ1BJtIKvwN5nDY0VX3KydodKutd5x3PNiILzSJh8V8oQ==`
  (`node-darwin-arm64`),
  `sha512-4UQBo9YWsmMFxoA5fffSSOXJoITSRDqHRZEnNGh0Z6G+qoqJ1TfeSNPxQNKcFdRSkUvT9sMrm5I0H7+4mUngVg==`
  (`node-linux-arm64-gnu`),
  `sha512-lcZfLRZJEXzZt4XtYWYw4Gd9r8t23OcVMrLvcuIAWuRbtsIUj5MRAEcky2wOVwGdIySeCgT8LTwmJfbfywgaTw==`
  (`node-linux-x64-gnu`).
- GitHub release: [`node-v0.3.0`](https://github.com/defense-humanites/libmorpheus/releases/tag/node-v0.3.0),
  published at 19:23 UTC with the four tarballs npm serves and
  `SHA256SUMS`; the repository's latest release stays `v0.5.0`.
- Published npm smoke test: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/43086696578):
  an empty application installed the published packages, acquired the
  declared native runtime 0.5.0, the Alpheios data with its generation index
  and the Perseids data from the public endpoints, and preserved Greek
  analysis, Latin multiple interpretations and Greek dual generation.
- Check from npm: `@libmorpheus/node@0.3.0` installs `@libmorpheus/data`
  0.2.0 and the Linux x86-64 addon. With the `v0.5.0` library and the index
  that data 0.2.0 prepared (`a2f97677…`), δίδωμι generates 3,636 records with
  `skippedRecords` 1, not enumerable, as native 0.5.0 and WebAssembly 0.2.0
  do.
