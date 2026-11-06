<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Node.js binding 0.1.3 release decision

Version 0.1.3 is the fourth release of the Node.js binding. It supersedes
0.1.2 for two reasons: the addon's result marshalling, and the native release
the binding declares and acquires. This document records the intended
contract; it does not authorize or record creation of the `node-v0.1.3` tag.

## Why a new version

**Result marshalling.** Through 0.1.2 the Node-API addon built every result
object on the main thread in its completion callback, field by field, with
about thirty-five Node-API calls and one `ArrayBuffer` per record. The
benchmark harness, once it measured this binding ([0.4.5 decision,
addendum](release-0.4.5.md#addendum-nodejs-harness-baseline)), showed what
that cost on generation: the maximal paradigm (`i(/hmi`, 2,918 forms) took
11.2 ms per operation against 7.5 ms through the Deno FFI binding, and did
not scale with contexts because the marshalling serialized on the main
thread (issue #47). The addon now copies the records the worker thread
already holds — `morpheus_analysis` / `morpheus_generation` in the C ABI's
layout, followed by their truncated-field masks — into one `ArrayBuffer`
per operation, resolved as `{ count, recordSize, buffer }`, and the facade
decodes the records in JavaScript, as the Deno and WebAssembly facades do
(pull request #48). Measured on the controlled host on the unchanged 0.4.5
sources (`bench/release-evidence/benchmark-0.4.5-node-packed.json`):
maximal warm generation 6.3, 3.7 and 3.8 ms at one, two and four contexts
against 11.2, 8.7 and 8.7 ms; small paradigm −7, −50 and −43 %; cold
maximal generation −15 %; analysis unchanged (within 2 %); every result
count identical.

The public surface is unchanged: `analyze`, `analyzeRaw`, `generate`,
`generateRaw`, their objects and `index.d.ts`. The raw and semantic outputs
over 3,024 Greek words, the Latin fixtures and five paradigms are byte for
byte identical to 0.1.2's, morph flags included. The addon and the facade
are now explicitly matched: the addon exports `recordEncoding` (1), which
the facade requires at load, so a facade of this version refuses an addon
built from an earlier source tree with a clear message — which is why the
three platform packages are republished with the facade.

**Declared native release.** Versions 0.1.0 to 0.1.2 declared and acquired
native libmorpheus 0.3.2. This version declares **0.4.5** (C ABI 2,
unchanged): `libmorpheus-native` and `libmorpheus-setup` download the
`v0.4.5` archives, verified against their published SHA-256 sidecars, and
the receipts record that version. Applications therefore receive the
native releases since 0.3.2 — in particular the Latin stem-class
resolution of 0.4.5 (issue #37: deponent perfect participles reported as
deponent) and the single-request index loaders of 0.4.4 — without any
change to the binding's contract, since the C API and ABI are unchanged
from 0.3.2 through 0.4.5. The binding's own tests run against the tree's
library, which is 0.4.5's.

The `@libmorpheus/data` dependency stays pinned to 0.1.0.

## Distribution, behavioral and licensing contracts

Unchanged from [0.1.0](release-node-0.1.0.md): four coordinated npm packages
at the same version (`@libmorpheus/node` and the `darwin-arm64`,
`linux-arm64-gnu`, `linux-x64-gnu` addon packages, pinned as exact optional
dependencies), no installation script, no native runtime and no linguistic
data in any package; asynchronous Greek and Latin analysis and experimental
Greek generation with serialized calls per context and concurrent contexts;
AGPL-3.0-or-later for the facade, the adapter, the workflows and this
decision.

## Qualification and publication

As for 0.1.2: Linux CI builds the addon, runs the binding's tests (now
including the decoded raw records), acquires the declared native runtime
and both datasets, and inspects the npm package contents; the platform
workflow repeats the addon build and tests on Linux x64 glibc, Linux arm64
glibc and macOS arm64 and retains one staged package per target. On an
authorized `node-v0.1.3` tag, `node-release.yml` verifies that the
declared native release `v0.4.5` is published, waits for both tagged
workflows on the exact commit, installs the facade and the Linux x64 addon
from the retained tarballs, publishes the platform packages before the
facade through npm OIDC with provenance, then triggers the published npm
smoke test, which acquires the declared runtime (now 0.4.5) and both
datasets in an empty application and checks Greek analysis, Latin multiple
interpretations and Greek dual generation.

## Remaining authorization

Before publication, a maintainer must:

1. confirm the tagged Linux CI and platform runs on the candidate commit;
2. explicitly authorize creation of `node-v0.1.3`;
3. after publication, record the workflow and smoke-test outcome here.
