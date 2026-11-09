<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Node.js binding 0.1.4 release decision

Version 0.1.4 is the fifth release of the Node.js binding. It supersedes
0.1.3 for two reasons: the native release it declares and acquires, and the
error raised when a context cannot be opened. This document records the
intended contract; it does not authorize or record creation of the
`node-v0.1.4` tag.

## Why a new version

**Declared native release.** Version 0.1.3 declared and acquired native
libmorpheus 0.4.5. This version declares **0.4.6** (C ABI 2, unchanged):
`libmorpheus-native` and `libmorpheus-setup` download the `v0.4.6` archives,
verified against their published SHA-256 sidecars, and the receipts record
that version. Native 0.4.6 analyzes about three times faster with results
unchanged ([release-0.4.6.md](release-0.4.6.md)); through this binding, the
accepted release benchmark measures 215, 132 and 88 µs per analysis at one,
two and four contexts against 649, 412 and 276 µs on 0.4.5. A context of
0.4.6 keeps up to four stem index files open until it is closed. Checked
here: `libmorpheus-native` of this tree installs the Linux x86-64 archive
of `v0.4.6` (`33d6ca3a…`, the published digest), and the acquired library
analyzes Latin `amatus` as `amo`.

**Context errors.** Through 0.1.3, `createContext()` raised a
`MorpheusError` with the status text only (`stemlib is unavailable or
incomplete`). It now names the stemlib and the language, as the WebAssembly
facade does (`opening /srv/stemlib for Latin failed: stemlib is
unavailable or incomplete`); the status is unchanged (8). The usual cause
is a stemlib without that language, such as the Greek-only Alpheios
dataset opened for Latin.

The public surface and the addon are otherwise unchanged; the addon's
`recordEncoding` is still 1. The `@libmorpheus/data` dependency stays
pinned to 0.1.0.

## Distribution, behavioral and licensing contracts

Unchanged from [0.1.3](release-node-0.1.3.md): four coordinated npm
packages at the same version, no installation script, no native runtime
and no linguistic data in any package, AGPL-3.0-or-later for the facade,
the adapter, the workflows and this decision.

## Qualification and publication

As for 0.1.3, with `v0.4.6` as the declared native release that
`node-release.yml` verifies before publishing and that the published npm
smoke test acquires. The tag's workflow also creates the `node-v0.1.4`
GitHub release, titled with the tag, from `docs/release-notes/node-v0.1.4.md`
and the four tarballs npm serves, checked against the registry's integrity.

## Remaining authorization

Before publication, a maintainer must confirm the tagged Linux CI and
platform runs on the candidate commit and explicitly authorize creation of
`node-v0.1.4`.
