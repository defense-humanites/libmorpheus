<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Python binding 0.2.0 release decision

Version 0.2.0 is the third release of the independently versioned Python
binding. It adds acquisition of the native runtime and of the stem data at
parity with the Node.js binding's commands, which the maintainer asked for
after 0.1.1. The binding still targets native libmorpheus 0.4.5 and C ABI 2.
This document records the intended contract; it does not authorize or record
creation of the `python-v0.2.0` tag.

## Why a new version

Through 0.1.1 the package "deliberately leaves runtime and data acquisition
outside": an application had to download a native archive and a stemlib by
hand, while a Node.js application runs `npx libmorpheus-setup`. Version 0.2.0
provides the same three commands, as console scripts, as `python -m` modules
and as functions:

- `libmorpheus-native --output <directory>` (`acquire_native()`): downloads
  the archive of the declared native release for this host — Linux x86-64
  glibc, Linux aarch64 glibc or macOS arm64; musl hosts are refused — from the
  GitHub release, following at most one redirect to the release-asset host,
  verifies it against the published SHA-256 sidecar, extracts it with
  symbolic links materialized as files and paths checked against escape, and
  writes `MORPHEUS-NATIVE.json`.
- `libmorpheus-data --dataset <alpheios|perseids> --output <directory>`
  (`acquire_data()`): downloads the pinned upstream revision of the audited
  Alpheios or Perseids tree, verifies the file count, the tree digest and the
  license digest, and writes the tree with `UPSTREAM-LICENSE` and
  `MORPHEUS-DATA.json`; `--subset runtime`, `--languages` and `--manifest`
  select the runtime subset and the languages and write
  `stemlib-manifest.json`, with the same rules and receipts as
  `@libmorpheus/data` (the subset tree digest of a Perseids Latin runtime
  subset is identical between the two packages).
- `libmorpheus-setup --dataset <alpheios|perseids>` (`setup_morpheus()`):
  both, into two separate new directories, with the native installation
  removed if the data step fails.

The pins are one set across the bindings: the `python_package_metadata`
guard requires every revision, file count and digest of the data package's
manifest, its runtime-subset rule and the generation-index digest to appear
unchanged in the Python manifest, and the native targets to name the
declared release's assets.

**Experimental generation.** The Node.js data package prepares `gener.index`
with the WebAssembly build of the historical source preparer, which the
Python package cannot run without a JavaScript runtime. Instead of a partial
or Node-dependent `--with-gener`, `libmorpheus-data --gener-index <path>`
installs a prepared index after verifying that its SHA-256 is the pinned
digest of the index derived from the audited revisions
(`5aa76d8c86c54af5121a3cce506ecaa57d14c6667ac0f091efd164ddfa9822d6`), and
the receipt records it as it would a prepared one. The index is prepared once
with `npx libmorpheus-data --dataset alpheios --with-gener` or
`sh tools/prepare-runtime-data.sh` from a source checkout. Preparing it in
Python would require either a native entry point for the preparer in the
library's public API or a Python port of the preparer; that remains the one
acquisition difference between the bindings. The maintainer's orientation
(2026-11-09): the preparer is to be exposed in the public C API at the
latest when generation stops being experimental, which closes the
difference for every binding at once; until then the index is prepared with
the Node.js package or a source checkout and installed through
`--gener-index`.

Everything is standard library (`urllib`, `zlib`, `tarfile`, `hashlib`,
`argparse`); the package keeps no runtime dependency. Every download is
bounded (64 MiB compressed, 256 MiB extracted, 4 KiB sidecar), HTTPS only,
without redirects except the native asset's, verified before anything is
written, into a directory that must not exist, and removed on any failure.
The analysis and generation API is unchanged.

## Distribution, behavioral and licensing contracts

Unchanged from [0.1.0](release-python-0.1.0.md) except for the additions
above: the PyPI project and import package `libmorpheus`, one `py3-none-any`
wheel and one source distribution, standard-library `ctypes` only, `py.typed`,
no runtime dependency, no native runtime, stemlib or generation index embedded;
synchronous Greek and Latin analysis and experimental Greek generation with
immutable normalized records; AGPL-3.0-or-later for the facade, the
acquisition code, the tests, the workflows and this decision. The downloaded
native runtime remains a mixed-license work and the downloaded data retains
its recorded upstream license and provenance, written next to it.

## Qualification and publication

Linux CI tests Python 3.11 and 3.14 against an independent ABI fixture
library and the compiled runtime (as before) and, new, runs the acquisition
tests against synthetic archives served by a fake fetcher (verification,
rollback, redirect policy, subset and language selection, manifest, index
digest, command lines), then acquires the declared native runtime and both
datasets from the public endpoints with the package's commands, refuses an
unpinned generation index, and analyzes Latin and Greek through what was
acquired; the wheel's three console scripts are checked after installation.
An authorized `python-v0.2.0` tag makes `python-release.yml` wait for tagged
Linux CI on the exact commit, verify that `v0.4.5` is published, check both
distributions and publish through PyPI trusted publishing. The PyPI smoke
test then installs exactly version 0.2.0 from PyPI, repeats the analysis and
generation checks against a runtime built from the tagged sources, and, new,
runs the published `libmorpheus-setup` against the public endpoints and
analyzes Latin and Greek through the acquired runtime and data.

## Remaining authorization

Before publication, a maintainer must:

1. confirm the final tagged CI candidate and package file lists;
2. explicitly authorize creation of `python-v0.2.0`;
3. after publication, record the workflow and smoke-test outcome here.
