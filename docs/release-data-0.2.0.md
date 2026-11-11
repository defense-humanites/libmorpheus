<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Data acquisition package 0.2.0 release decision

`@libmorpheus/data` 0.2.0 supersedes 0.1.0 for the generation index that
`--with-gener` prepares. The package still contains no linguistic data, and
its datasets, commands and options are unchanged. This document records the
intended contract; it does not authorize or record creation of the
`data-v0.2.0` tag.

## Release record

- Package version: **0.2.0**
- Datasets: unchanged from 0.1.0. Alpheios Greek at
  `4632415fe93c85e9fdca47a0c5a13f31385f0023`, Perseids Greek and Latin at
  `ab6898ffed335fc6169fa02c9940657a9b5a78e0`
- Generation preparer: the checked-in WebAssembly build of the tree's
  preparer. Prepared source `62265bf666c8a640171e66a42536174df4f2b16ff08054bcf6b467414fcdf040`
  (287,343 lines), generated `gener.index`
  `a2f9767708a488fb6e5e6672a8bf4d1701ca259bab1fb733a12299e2bd2aa331`
  (106,081 lemmas, 107,837 blocks, 177,676 records). 0.1.0 prepared
  `5aa76d8c…` (106,422 lemmas, 129,097 records).

## Why a new version

Generation is now defined as the inverse of analysis: it returns the forms
that the analyzer accepts for a lemma, to find a lemma's forms in texts,
precompute form-to-lemma tables or check the data, not reference paradigms
([public-api.md](public-api.md#greek-lemma-generation)). The index 0.1.0
prepared was much thinner than what analysis accepts. The preparer changes
it in four ways ([gener-derivations.md](gener-derivations.md)):

- **Complete regular derivations.** Analysis keeps each regular derivation
  whole (9,518 of the corpus's 9,522 regular groups have their own entry in
  `steminds/vbind`), while the historical preparation emitted only the
  requested parts. Each regular group now receives every principal part its
  derivation defines, future perfect included. ποιέω gains its active
  aorist, δηλόω its aorist, perfect and aorist passive, and ἀγγέλλω ἤγγειλα
  and ἠγγέλθην.
- **Compound-only records dropped.** Analysis accepts their stems only after
  a preverb, so 2,594 records are removed and 347 lemmas, such as δημέω,
  leave the index.
- **Seven source lines patched** ([gener-data-patches.md](gener-data-patches.md)).
  These `:de:` lines of the Alpheios sources could not be read; the patches
  restore ἔχω's present among others. The manifest is embedded in the
  package as `GENER_CORPUS_PATCHES`, and each patch is verified against the
  source line's fingerprint before it applies.
- **Two inherited stem alterations corrected.** Aspirate dissimilation and
  consonant euphony inside the stem no longer distort derived stems
  (ἠληθεύθην, not ἠλητεύθην).

Over the whole index, generated forms go from 12.5 to 22.1 million. 8,511
lemmas gain forms. On 400 lemmas changed since 0.1.0's index, 99.99 % of
the added forms analyze back to their lemma with the same tense and mood.

The preparer module also carries the changes made since 0.1.0 to the code
it compiles: the runtime changes of native 0.4.6, including the fix of a
leak in the derivation expansion, and silent diagnostics.

The minor version follows the project's rule within 0.x: the index the
command prepares changes.

## Compatibility

The index format is unchanged, and the index works with any native or
WebAssembly runtime that reads `gener.index`. With native 0.5.0 or
WebAssembly 0.2.0, the 339 records the engine cannot generate are skipped
and counted. With earlier runtimes, the 270 lemmas that hold one of them
fail.

The Node.js binding pins this package exactly, so it picks the new index up
in its next release (0.3.0). The Python binding pins the index digest for
`--gener-index`, so its next release (0.3.0) verifies `a2f97677…`.
Applications that pinned 0.1.0's digest must update it.

## What the package is, and is not

Unchanged from [0.1.0](release-data-0.1.0.md): the package contains no
linguistic data and never carries any. It downloads a pinned upstream archive,
verifies the dataset tree and license against pinned digests, and writes the
result with a provenance receipt. The redistribution gate stays closed, and
`gener.index` is always prepared locally.

## Qualification and publication

As for 0.1.0. `data-release.yml` waits for the tagged Linux CI and repeats
the package checks. It acquires a dataset with the command installed from
the `npm pack` tarball, publishes to npm through OIDC with provenance and to
JSR, and attaches the tarball and its digest to a pre-release. The
pre-release is created from `docs/release-notes/data-v0.2.0.md`. After
publication, the maintainer prepares an index from the published package and
records here that its digest is `a2f97677…`.
