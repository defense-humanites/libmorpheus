<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Release decision: 0.4.2

Status: benchmark accepted; final Linux CI and platform qualification pending.

- Project version: **0.4.2**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.4.1`
- Benchmark evidence: **accepted**

## Scope and compatibility

Native 0.4.1 can abort on forms such as `a)mfestan` with `IgnoreAccents`.
The 0.4.1 dynamic array is shared by value in several analysis paths, so a
`realloc` through one copy leaves a freed pointer in the other. The candidate
keeps the array dynamic but shares a stable storage handle containing the
pointer, count and capacity. Generated forms may borrow this handle; only its
owner frees it. The public C header, exported symbols, ABI 2 and SONAME 1
remain unchanged.

Regression tests cover all 46 reported forms, the exact 26 and 39 counts for
`a)nalow` and `a(napinw`, copies that cross several growth boundaries, and a
single-process sweep of the 33,410 entries in Alpheios's pinned Greek lemma
list. The latter is separate from the 266,100 Bailly calls that exposed the
crash; that complete external corpus needs independent qualification before
the Bailly API upgrades.

The data-free native archives remain separate from the pinned Alpheios
stemlib. Bindings retain their own release versions: the published Deno 0.4.1
package still acquires unsafe native 0.4.1 and must be updated only after a
corrected native release is published.

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
smoke-test policy correction follow the measured native source revision.
Any further native or stemlib change requires a new benchmark.

## Remaining gates

1. Require complete Linux CI on the evidence-finalized commit.
2. Qualify all native packages and Docker images on the platform matrix with
   `package_artifacts` enabled, including the Deno smoke test that imports
   the pinned JSR 0.4.1 despite Deno's default minimum dependency age.
3. Tag `v0.4.2` only after those gates pass, then verify the published assets.
