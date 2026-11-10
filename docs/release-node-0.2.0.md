<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Node.js binding 0.2.0 release decision

Version 0.2.0 of the Node.js binding supersedes 0.1.4 for the decoding of
named results, which lifts the binding's ceiling on parallel generation and
changes one behaviour: the name arrays of analyses and generations are now
frozen and shared. Within 0.x a behavioural change takes the minor version.
This document records the intended contract; it does not authorize or
record creation of the `node-v0.2.0` tag.

## Why a new version

`analyze()` and `generate()` built the raw records first and then converted
each into a named object: a fresh array for every mask field, a `Set` for
the dialects and a test of all 38 known morph flags per record. For the
largest paradigm (`i(/hmi`, 2,918 forms) that conversion and the garbage it
left were most of the main thread's work, which capped wide-parallel
generation near 270 operations per second whatever the number of contexts
(the N-API / WebAssembly comparison, [wasm.md](wasm.md#outcome-the-nodejs-binding-stays)).

The named objects are now decoded straight from the packed buffer (pull
request #71). Their name arrays (`dialects`, `geographicRegions`, `genders`,
`grammaticalCases`, `voices`, `morphFlags`, `truncatedFields`) are cached per
code and **frozen and shared** between records with the same values, as their
`readonly` types already declared; an application that changes one must copy
it first (`[...analysis.genders]`). The objects are otherwise deep-equal to
0.1.4's over 34,267 generated forms and 2,667 Greek and Latin analyses.
`analyzeRaw()` and `generateRaw()` are unchanged, as is the addon
(`recordEncoding` 1).

Measured on the controlled host with the same native runtime
([`benchmark-0.4.6-node-decoding.json`](../bench/release-evidence/benchmark-0.4.6-node-decoding.json),
against `benchmark-0.4.6.json`, every result count identical): maximal warm
generation 3.17, 1.60 and 1.02 ms at one, two and four contexts instead of
5.73, 3.60 and 3.75 ms (315, 624 and 985 operations per second), small warm
generation −30 to −71 %, peak RSS of the generation rows −52 to −59 %,
analysis within noise. The later comparisons of both bindings
([`benchmark-0.4.6-bindings-1.json`](../bench/release-evidence/benchmark-0.4.6-bindings-1.json),
[`benchmark-0.4.6-bindings-2.json`](../bench/release-evidence/benchmark-0.4.6-bindings-2.json))
repeat these figures (288, 434 and 939, then 274, 560 and 933 operations
per second).

The binding still declares native **0.4.6** (C ABI 2) and pins
`@libmorpheus/data` 0.1.0.

## Distribution, behavioral and licensing contracts

Unchanged from [0.1.4](release-node-0.1.4.md) except for the frozen shared
arrays above.

## Qualification and publication

As for 0.1.4: tagged Linux CI and platform runs on the exact commit, then
`node-release.yml` verifies that `v0.4.6` is published, publishes the three
platform packages before the facade through npm OIDC with provenance,
creates the `node-v0.2.0` GitHub release from
`docs/release-notes/node-v0.2.0.md` and the tarballs npm serves, and
triggers the published npm smoke test.

## Remaining authorization

Before publication, a maintainer must confirm the tagged Linux CI and
platform runs on the candidate commit and explicitly authorize creation of
`node-v0.2.0`.
