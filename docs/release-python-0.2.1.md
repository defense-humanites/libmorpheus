<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Python binding 0.2.1 release decision

Version 0.2.1 of the Python binding supersedes 0.2.0 for two reasons: the
native release it declares and acquires, and the error raised when a
context cannot be opened. This document records the intended contract; it
does not authorize or record creation of the `python-v0.2.1` tag.

## Why a new version

**Declared native release.** Version 0.2.0 declared and acquired native
libmorpheus 0.4.5. This version declares **0.4.6** (C ABI 2, unchanged):
`libmorpheus-native` and `libmorpheus-setup` download the `v0.4.6` archive
for the host, verified against its published SHA-256 sidecar, and the
receipt records that version. Native 0.4.6 analyzes about three times
faster with results unchanged ([release-0.4.6.md](release-0.4.6.md)); a
context keeps up to four stem index files open until it is closed. Checked
here: `python -m libmorpheus.native` of this tree installs the Linux x86-64
archive of `v0.4.6` (`33d6ca3a…`, the published digest), and the acquired
library analyzes Latin `amatus` as `amo` and Greek `e)/kstasis`.

**Context errors.** Through 0.2.0, `Library.context()` raised a
`MorpheusError` with the status text only. It now names the stemlib and
the language (`opening /srv/stemlib for Latin failed: stemlib is
unavailable or incomplete`); the status is unchanged
(`Status.STEMLIB_ERROR`). The usual cause is a stemlib without that
language, such as the Greek-only Alpheios dataset opened for Latin.

The acquisition pins (data revisions, digests, the generation index) and
the analysis and generation API are otherwise unchanged.

## Distribution, behavioral and licensing contracts

Unchanged from [0.2.0](release-python-0.2.0.md).

## Qualification and publication

As for 0.2.0, with `v0.4.6` as the native release that `python-release.yml`
verifies before publishing and that the published smoke test's
`libmorpheus-setup` acquires. The tag's workflow also creates the
`python-v0.2.1` GitHub release from `docs/release-notes/python-v0.2.1.md`
and the wheel and source distribution PyPI serves, checked against the
registry's digests.

## Publication record

- Tag: `python-v0.2.1`, created by the maintainer on 2026-11-09 on
  `515b24de5b58c69b278c8df6cbe9021afb87a30f`, the merge of this decision,
  together with `node-v0.1.4`.
- Tagged Linux CI: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/42692801522).
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/42692801411);
  `libmorpheus` 0.2.1 is on PyPI; the wheel
  `libmorpheus-0.2.1-py3-none-any.whl` has SHA-256
  `1aeca4c5db252fdd416acb952fdbf9baa8a16af129c7af606c950023e58e30a6` and
  the source distribution
  `a0539b69adb7e58f318dacb6b2a4716423efa595c804ff09306e8ff610ae4f40`.
- GitHub release: [`python-v0.2.1`](https://github.com/defense-humanites/libmorpheus/releases/tag/python-v0.2.1),
  with the two distributions PyPI serves and `SHA256SUMS`.
- Published PyPI smoke test: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/42693852853):
  the public wheel repeated the analysis and generation checks against a
  runtime built from the tagged sources, and its published
  `libmorpheus-setup` acquired the declared runtime 0.4.6 and the Perseids
  data from the public endpoints, through which Latin and Greek were
  analyzed. The PyPI page now shows the README that states the generation
  prerequisite.
