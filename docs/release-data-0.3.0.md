<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Data acquisition package 0.3.0 release decision

`@libmorpheus/data` 0.3.0 supersedes 0.2.0 for the generation index that
`--with-gener` prepares. The package still contains no linguistic data, and
its datasets, commands and options are unchanged. This document records the
intended contract; it does not authorize or record creation of the
`data-v0.3.0` tag.

## Release record

- Package version: **0.3.0**
- Datasets: unchanged from 0.2.0.
  - Alpheios Greek at `4632415fe93c85e9fdca47a0c5a13f31385f0023`.
  - Perseids Greek and Latin at `ab6898ffed335fc6169fa02c9940657a9b5a78e0`.
- Generation preparer: the checked-in WebAssembly build of the tree's
  preparer.
  - Prepared source `a618d41c1deec1d6ea14d767a268819ebc5e5ec9667fdfe8770f1d2479f87075`,
    290,741 lines.
  - Generated `gener.index` `8ba328ca8429c657aeb53a47a92045ac4bd64cdeab726af01e8afbcfd67d8fc2`:
    106,080 lemmas, 107,835 blocks and 177,672 records, plus 509 reserved
    keys with 2,849 records.
  - 0.2.0 prepared `a2f97677…`: 106,081 lemmas, 107,837 blocks and 177,676
    records.

## Why a new version

The preparer of 0.2.0 dropped the records whose stem occurs only in
compounds (`comp_only`), because analysis accepts those stems only after a
preverb. Generation now composes compound verbs as analysis finds them
([release-0.6.0.md](release-0.6.0.md)), and it needs those stems: 875
compounds depend on them. The preparer therefore moves them to a reserved
key instead, the lemma prefixed with a hyphen (`-dhme/w`). It also reads the
key when it is joined to a stem type by a comma (`aor2,comp_only`). The
JavaScript index builder keeps that leading hyphen. Requests are
canonicalised without hyphens, so they never name such a key.

The 2,849 records go to 509 reserved keys. The lemma keys are those of
0.2.0's index but one, with four records fewer, and the lemmas that only
such stems made, such as δημέω, stay absent.

The preparer module also carries the changes made since 0.2.0 to the code it
compiles: the engine fixes of native 0.6.0, and the faster transfer of
preverb flags (#105). Neither changes the prepared index: the native
preparer and this package's both produce `8ba328ca…`.

The minor version follows the project's rule within 0.x: the index the
command prepares changes.

## Compatibility

The index format is unchanged. With native 0.6.0 or WebAssembly 0.3.0, the
reserved keys supply the compound-only stems of the compound verbs these
runtimes generate. Earlier runtimes never reach those keys and generate
the lemma keys as with 0.2.0's index.

The Node.js binding pins this package exactly, so it picks the new index up
in its next release (0.4.0). The Python binding pins the index digest for
`--gener-index`, so its next release (0.4.0) verifies `8ba328ca…`.
Applications that pinned 0.2.0's digest must update it.

## What the package is, and is not

Unchanged from [0.1.0](release-data-0.1.0.md): the package contains no
linguistic data and never carries any. It downloads a pinned upstream
archive, verifies the dataset tree and license against pinned digests, and
writes the result with a provenance receipt. The redistribution gate stays
closed, and `gener.index` is always prepared locally.

## Qualification and publication

As for 0.2.0, `data-release.yml` does the following:

1. It waits for the tagged Linux CI and repeats the package checks.
2. It acquires a dataset with the command installed from the `npm pack`
   tarball.
3. It publishes to npm through OIDC with provenance, and to JSR.
4. It attaches the tarball and its digest to a pre-release, created from
   `docs/release-notes/data-v0.3.0.md`.

Before tagging, the package command run from the tree prepared `8ba328ca…`
from the downloaded Alpheios archive. After publication, the maintainer
prepares an index from the published package and records here that its
digest is `8ba328ca…`.
