<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Python binding 0.1.1 release decision

Version 0.1.1 is the second release of the independently versioned Python
binding. It supersedes 0.1.0 for one reason: the native release it declares.
This document records the intended contract; it does not authorize or record
creation of the `python-v0.1.1` tag.

## Why a new version

Version 0.1.0 declares native libmorpheus 0.3.2 — `MORPHEUS_NATIVE_VERSION`,
the README's installation instructions and the release workflow's check that
the declared native release is published all name it. Three native releases
followed without any change to the C API or ABI (still 2): 0.4.3 (provenance),
0.4.4 (single-request index loaders) and 0.4.5 (resolution of the stem
classes `pp_su` and `nounstem`, which reports the perfect participles of
Latin deponent lemmas as deponent; see [release-0.4.5.md](release-0.4.5.md)).
A Python application following the 0.1.0 instructions installs the `v0.3.2`
archive and receives none of them.

This version declares **0.4.5**: the README directs applications to the
`v0.4.5` archives, the package exports `MORPHEUS_NATIVE_VERSION = "0.4.5"`
and `python-release.yml` verifies that release. The binding's source is
otherwise unchanged (`_library.py`, `_abi.py`, `_types.py` are those of
0.1.0), as is its behavior: the binding's tests already ran against the
tree's library, which is 0.4.5's, and the published 0.4.5 Linux x86_64
archive was exercised through the binding during preparation (Latin
`amatus` analyzed as `amo`).

Since the Python binding provides no acquisition command, the declared
version is an instruction to applications and a release-workflow check, not
a download pin; nothing in the package changes behavior with it.

## Distribution, behavioral and licensing contracts

Unchanged from [0.1.0](release-python-0.1.0.md): the PyPI project and import
package `libmorpheus`, one `py3-none-any` wheel and one source distribution,
standard-library `ctypes` only, `py.typed`, no runtime dependency, no native
runtime, stemlib or generation index embedded, no acquisition command;
synchronous Greek and Latin analysis and experimental Greek generation with
immutable normalized records, serialized calls per context, the GIL released
during native calls, explicit and idempotent closure; AGPL-3.0-or-later for
the facade, the tests, the workflows and this decision.

## Qualification and publication

As for 0.1.0: Linux CI tests Python 3.11 and 3.14 against an independent ABI
fixture library and against the compiled runtime with Greek and Latin stem
data and the generation fixture, then builds and inspects the two
distributions. An authorized `python-v0.1.1` tag makes `python-release.yml`
wait for tagged Linux CI on the exact commit, verify that the declared native
release `v0.4.5` is published, check both distributions, install the wheel in
isolation and publish through PyPI trusted publishing in the `pypi`
environment. The public-package smoke test then installs exactly version
0.1.1 from PyPI and repeats the Greek analysis, Latin multiple-analysis and
Greek dual-generation checks against a runtime built from the tagged
sources.

## Publication record

- Tag: `python-v0.1.1`, created by the maintainer on 2026-11-06 on
  `889db68a1ebcb9578b34c61eb61d7986cba5d749`, the merge of this decision.
- Tagged Linux CI: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/42224729250).
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/42224729051);
  `libmorpheus` 0.1.1 is on PyPI; the wheel
  `libmorpheus-0.1.1-py3-none-any.whl` has SHA-256
  `26c1c2369a463fab0009db9364eb289615f11a8f3eb465c089faf34c0be7af2b`.
- Published PyPI smoke test: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/42225502565):
  the public wheel installed in an isolated environment and preserved Greek
  analysis, Latin multiple analyses and Greek dual generation against a
  runtime built from the tagged sources.

## Next version

The maintainer asks that the following Python versions reach parity with
`@libmorpheus/node` in acquisition: a native-runtime command and a data
command (and a combined setup), pinning the declared native release and the
audited upstream data revisions, verifying downloads, and writing receipts,
so that an application needs no manual download. That is the next change on
this track.
