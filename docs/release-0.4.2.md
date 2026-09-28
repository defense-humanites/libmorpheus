<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# libmorpheus 0.4.2

This native release fixes a process crash introduced in 0.4.1. When an analysis
grew beyond the initial storage capacity, copied word structures could retain
a freed pointer. An input such as `a)mfestan` with `IgnoreAccents` could then
abort the entire process. The analysis storage now uses a shared handle so
every copy observes the same pointer, count and capacity; only its owner frees
the storage.

Regression coverage includes all 46 reported crashing forms, growth across
several capacity boundaries, and a single-process sweep of 33,410 entries in
the pinned Alpheios Greek lemma list. With the Alpheios data, `a)nalow` and
`a(napinw` return 26 and 39 analyses respectively. The complete 266,100-call
Bailly workload has not yet been rerun against this release; its operators
should qualify it before upgrading their service.

The public C API and ABI remain compatible with 0.4.1. The native archives
contain no stemlib data. The existing Deno 0.4.1 package still downloads the
unsafe native 0.4.1 release: publishing this native fix does not upgrade that
binding or the Bailly API. A separate Deno release is needed.

## Release record

- Project version: **0.4.2**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.4.1`
- Benchmark evidence: **accepted**
- Pre-release Linux CI: [passed on `f1159c1`](https://github.com/defense-humanites/libmorpheus/actions/runs/36414984220)
- Pre-release platform qualification: [passed on `f1159c1`](https://github.com/defense-humanites/libmorpheus/actions/runs/36416173899)

## Benchmark evidence

The schema 2 report from native source revision
`5185bc8a94f2fea20afe249b4cd6e812610b4050` uses the pinned Alpheios
stemlib revision `4632415fe93c85e9fdca47a0c5a13f31385f0023` on Apple
Silicon with Apple Clang 21 and Deno 2.9.7. Its SHA-256 is
`0cc89021dbc973db5293a0a7d4c42d3ed17ac3a57fc29b247e2e28514ad90c46`.
It matches the accepted 0.4.1 report's corpus, generation index, toolchain,
workload parameters and thirteen result counts. The complete benchmark
validator passes with the recorded source revision and compiler.

Relative to 0.4.1, analysis FFI throughput falls 3.1 %, 2.5 % and 1.8 % at
one, two and four contexts. Persistent and cold `cruncher` fall 3.5 % and
3.1 %. Analysis peak RSS falls 1.3–1.6 %. Maximal generation throughput
changes by −2.5 % to +0.2 %; cold generation by −1.6 % to −0.6 %. The small
warm generation result at two contexts falls 19.4 %, but the 40 operations
take approximately 1.5 ms in the baseline and 1.9 ms in the candidate; its
single aggregate is too short to establish a material generation regression.
All result counts are unchanged. These whole-process timings are accepted
for this correctness fix; they do not measure the full Bailly search workload.

Only release documentation, benchmark evidence, metadata checks and a Docker
smoke-test policy correction follow the measured native source revision. The
native source and pinned stemlib have not changed since that measurement.
