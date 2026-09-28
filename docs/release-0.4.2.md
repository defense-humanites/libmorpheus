<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Release decision: 0.4.2

Status: candidate; sanitizer CI, benchmark and platform qualification pending.

- Project version: **0.4.2**
- C ABI: **2**
- SONAME major: **1**
- Previous release tag: `v0.4.1`
- Benchmark evidence: **pending**

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

## Remaining gates

1. Require Linux CI, including ASan/UBSan, on the exact candidate commit.
2. Benchmark the corrected runtime against the accepted 0.4.1 report and
   record the accepted evidence and checksum.
3. Qualify all native packages and Docker images on the platform matrix.
4. Tag `v0.4.2` only after those gates pass, then verify the published assets.
