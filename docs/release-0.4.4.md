<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# libmorpheus 0.4.4

This native release changes no analysis or generation result. It changes how
the runtime reads its index files: `init_endind` (verb stem, ending and
derivation indices) asked `vax_fread` for `BUFSIZ` bytes at a time, a VAX-era
bound, and `init_preind` read the pre-index sidecars one record at a time
through the stdio buffer, so a context's first Greek analysis issued about
3,500 `read` calls for 1.8 MiB. Both loaders now request the whole file,
which the C library serves in a few calls, and `init_preind` decodes the
records from memory with the layout `WriteKey` produces. Under WebAssembly,
where every call crosses into the JavaScript file system, the first analysis
of a context falls from 10–15 ms to about 6 ms with optimized code on a
2 vCPU host; native builds issue fewer system calls.

The release exists so that WebAssembly binding 0.1.2, which answers the
cold-start cost of a serverless deployment on two fronts (this loader change
and the adoption of stemlib bytes in the facade), is compiled from and
declares a tagged native release, as the binding's provenance rule requires.

The public C API and ABI are unchanged from 0.4.1 through 0.4.3. The native
archives contain no stemlib data. The Deno, Node.js and Python bindings keep
declaring the native releases they were qualified against; none of them
needs a release for this version.

## Release record

- Project version: **0.4.4**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.4.3`
- Benchmark evidence: **accepted**
- Pre-release Linux CI: [passed on `dd06be9`](https://github.com/defense-humanites/libmorpheus/actions/runs/41881947934)
- Pre-release platform qualification: [passed on `dd06be9`](https://github.com/defense-humanites/libmorpheus/actions/runs/41873559175)
  (manual dispatch with `package_artifacts`)
- Tagged platform run and release publication: [passed on `dd06be9`](https://github.com/defense-humanites/libmorpheus/actions/runs/41881948288)
- Release: [`v0.4.4`](https://github.com/defense-humanites/libmorpheus/releases/tag/v0.4.4),
  created on 2026-11-04 on `dd06be9592d8b0c713fd0025b0755cbb8eab7247`

## Benchmark evidence

The schema 2 report from native source revision
`3df935c0de348440c5e86ab95e3ec069da261341` (the merge of the release
preparation) uses the pinned Alpheios stemlib revision
`4632415fe93c85e9fdca47a0c5a13f31385f0023` on the same Apple Silicon host as
the 0.4.3 report, with the same corpus, generation index and workload
parameters. Its SHA-256 is
`4dd2b7bd68961766f0f85059b990e99586e1d9ab2b5722114fd5b4460834be18`. The
host's toolchain had moved since 0.4.3: Apple Clang 21 build 2100.4.1.1
(2100.3.34.2 before) and Deno 2.9.8 (2.9.7 before). The complete benchmark
validator passes with the recorded source revision and compiler. All
thirteen result counts equal those of the accepted 0.4.3 report.

Relative to 0.4.3, analysis FFI mean latency changes by +0.0 %, +5.5 % and
−0.2 % at one, two and four contexts; persistent `cruncher` by +0.5 %.
Maximal generation changes by +1.3 %, +1.2 % and +1.7 % warm and +0.9 % cold;
small generation by −5.3 %, +8.2 % and +2.1 % warm and −0.3 % cold. As in the
previous reviews, the two-context small warm generation aggregate (40
operations, 1.5 ms against 1.6 ms) is too short to carry meaning, and the
two-context FFI figure has oscillated between releases (−1.7 %, +2.5 %,
−3.3 % from 0.4.0 to 0.4.3) on an unchanged path; 444 µs is 3 % above the
0.4.0 and 0.4.2 values. These are the warm paths, which the change does not
touch: a context loads its indices once, before the timed operations.

The cold `cruncher` falls 15 % (3.85 ms to 3.27 ms per process), the one
measurement that includes the index loading in every operation. This is the
expected direction of the change, through fewer calls on the cold path.
Cold generation is unchanged (±1 %), as expected: `gener.index` is loaded by
another path.

Peak RSS is lower or equal in the first ten measurements (−1.7 % to +0.0 %).
The last three are 12 % higher, because the four-context maximal generation
grew the process by 39 MiB during its measurement against 7.5 MiB in the
0.4.3 report. The accepted reports show that this figure follows the Deno
runtime, not the native library: it was 38 MiB under Deno 2.9.6 (0.4.0
report), 7–8 MiB under 2.9.7 (0.4.1 to 0.4.3) and is 39 MiB under 2.9.8.
That measurement decodes 233,440 results per iteration into JavaScript
objects, and whether V8 collects them within the measurement window is a
property of the runtime version. The loader change itself allocates
nothing that outlives the load: `init_endind` keeps the same buffer as
before, and `init_preind` frees its 150 KiB record buffer after decoding.

The reviewer's identity check holds in addition: the module built from the
candidate and one built from `v0.4.3` agreed byte for byte over 3,000 Greek
headwords from `stemsrc/lemlist` and the Latin fixtures; the native suite
passed, also under AddressSanitizer, UBSan and ThreadSanitizer on `main`.

## Publication record

The tag was created by the maintainer on 2026-11-04 on `dd06be9`, the merge
of the accepted benchmark evidence, a descendant of the measured revision
`3df935c` that differs from it only by that evidence and this document.

GitHub's hosted macOS arm64 runners were short of capacity that evening:
on the manual `package_artifacts` dispatch, the `apple-silicon` job was
cancelled three times without a runner ("not acquired by Runner of type
hosted even after multiple attempts") and no step ran; it obtained a runner
at the fourth re-run and passed. The tagged run, started meanwhile,
obtained one at once and passed every job at its first attempt, so the
macOS qualification was supplied twice. Linux CI and the WebAssembly
workflow passed on the tag as well. The tag never moved.

The release carries the three native archives and their digests, plus the
accepted benchmark report and its sidecar:

| Asset | SHA-256 |
|---|---|
| `libmorpheus-0.4.4-Linux-x86_64-glibc.tar.gz` | `0fac8971e5926f1f7578ba1f858c6804b620f7d5557a65e44de35d96c1a35af6` |
| `libmorpheus-0.4.4-Linux-aarch64-glibc.tar.gz` | `64d8796faa07e4760688ce54b3a99a5378c0488f83ebd00fe16cb626b284e0e6` |
| `libmorpheus-0.4.4-macOS-arm64.tar.gz` | `4b40eccff7fde81f5efc60b5835fc51294875f1c8b48dd39643af48a615bf511` |
| `benchmark-0.4.4.json` | `4dd2b7bd68961766f0f85059b990e99586e1d9ab2b5722114fd5b4460834be18` |

WebAssembly binding 0.1.2 was tagged on the same commit afterwards; see
[`release-wasm-0.1.2.md`](release-wasm-0.1.2.md).
