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

## Publication record

- Tag: `node-v0.1.4`, created by the maintainer on 2026-11-09 on
  `515b24de5b58c69b278c8df6cbe9021afb87a30f`, the merge of this decision.
- Tagged qualification: [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/42692804388)
  and [platform](https://github.com/defense-humanites/libmorpheus/actions/runs/42692803811)
  (Linux x86_64 and aarch64 glibc, macOS arm64, Alpine x86_64 and aarch64),
  both passed at the first attempt.
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/42692803731);
  the four packages are on npm at 0.1.4 with `latest` moved, tarball
  integrity `sha512-XiLsBUHQWk/hzLVcc0y5uTdOmEufhFjU7JtJPDesFmd9E+MIcPr22/r7aH9AiZ06uyTflyMAT0ZrZWnaArZQMw==`
  (`@libmorpheus/node`),
  `sha512-V7tq13zdSWCjQ/gKS+RIfhjdV8dmoq+YBYZZATXltnZahWJe1aflYfpk7FveLORRcuAi5FGe0nma4DFmzb1bLA==`
  (`node-darwin-arm64`),
  `sha512-3CH3kuRlalHRdnLK/mjVlwhgiXbyqmEex9os1RyZGcex4OBeqP/sKqAt+7g4FMUwu5UNCWdiEDrzjRUyQI4vsw==`
  (`node-linux-arm64-gnu`),
  `sha512-4guuzRiQEeSPbCfSf5SBgq66F2YCnzxU3aif/Ri4msBIaFO/BA8IvSKYvCx3wNDc+iIrXfZfFIubJnqu0lyvTA==`
  (`node-linux-x64-gnu`).
- GitHub release: [`node-v0.1.4`](https://github.com/defense-humanites/libmorpheus/releases/tag/node-v0.1.4),
  with the four tarballs npm serves and `SHA256SUMS`; the repository's
  latest release stays `v0.4.6`.
- Published npm smoke test: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/42694137516):
  an empty application installed the published packages, acquired the
  declared native runtime 0.4.6 and both datasets from the public endpoints,
  and preserved Greek analysis, Latin multiple interpretations and Greek
  dual generation.
