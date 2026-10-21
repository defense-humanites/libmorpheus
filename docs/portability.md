<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Platform support

The runtime has explicit continuous-integration targets for its supported
native-package and container platforms:

| Target | C library and fixtures | Deno FFI | Execution mode |
| --- | --- | --- | --- |
| Linux x86_64, glibc | Yes | Yes | Native Ubuntu runner |
| Linux aarch64, glibc | Yes | Yes | Native Ubuntu ARM64 runner |
| Linux x86_64, musl | Yes | Image smoke test | Native Alpine container |
| Linux aarch64, musl | Yes | Image smoke test | Native ARM64 Alpine container |
| macOS arm64 | Yes | Yes | Native Apple Silicon runner |

The Alpine jobs build both the minimal `runtime` image and the reusable
`deno-runtime` image. The macOS job compiles with AppleClang, executes the
complete CTest suite, and runs the Deno FFI tests against the generated
`libmorpheus.dylib`.

The architecture matrix is intentionally separate from ordinary pull-request
CI. It runs weekly, on manual request, and for native `v*` version tags. Tagged
runs use optimized builds and additionally preserve verified Linux x86-64, Linux
aarch64 glibc, and macOS arm64 native packages with SHA-256 integrity files.
The Apple Silicon build sets a minimum deployment target of macOS 11.0. Alpine
images remain qualification artifacts only until stemlib redistribution has
been authorized.

The weekly trigger still creates a lightweight Linux decision job, but the
architecture matrix is skipped when `main` has the same SHA as the preceding
successful weekly run. Failed qualification is retried even without a new
commit. Manual and native-version-tag runs never apply the inactivity shortcut.
Manual runs offer a `package_artifacts` switch, enabled by default, which
produces Linux x86-64 glibc, Linux aarch64 glibc, and macOS arm64 archives.
Scheduled runs test the platforms without producing packages.

Native package labels explicitly include the operating system, architecture,
and Linux libc contract. Every candidate archive is checksum-verified,
extracted, and consumed through both its installed CMake package and its
`pkg-config` metadata. Linux qualification checks the ELF machine and dynamic
dependencies. macOS qualification checks the Mach-O architecture, install
name, absence of workspace paths, and the macOS 11.0 deployment target.

## Stemlib binary contract

The compiled stemlib is a versioned data dependency, not a native executable.
Its historical binary records require:

- 8-bit bytes;
- 16-bit dialect fields;
- 32-bit integer words, stem types, derivation types, and pre-index offsets;
- the historical 32-bit compiler layout of the morphology bitfields.

The build contains static assertions for every scalar width and a runtime test
for the bitfield allocation order. The byte-oriented VAX readers decode
multi-byte values explicitly, so pointer width and the host width of `long`
do not enter the disk format.

The supported native deployment targets are little-endian LP64 systems. The
experimental WebAssembly build targets `wasm32`, a little-endian ILP32
environment: the disk format does not depend on the width of `long`, and the
two in-memory sites that assign a 32-bit disk word to a `long` are explicit
about it (`src/morphlib/morphkeys.c`, `src/morphlib/retrentry.c`). Big-endian
targets and non-8-bit-byte C implementations are not currently supported.
See [wasm.md](wasm.md) for the WebAssembly qualification.
The Deno binding additionally requires a 64-bit `x86_64` or `aarch64`
runtime.

## Local checks

On Apple Silicon:

```sh
cmake --preset dev
cmake --build --preset dev
ctest --preset dev
```

For Alpine, the Dockerfile runs the suite during the build:

```sh
docker build --target runtime -t morpheus .
docker build --target deno-runtime -t morpheus-deno .
```

The build uses the canonical runtime-data preparer and embeds its validated
Alpheios `gener.index` beside the Greek stemlib. Platform CI checks the index
digest, verifies that no source-tree binding was copied into the image, then
runs real Deno analysis and experimental generation through the public JSR
package on both Alpine architectures, including preservation of dual forms.
