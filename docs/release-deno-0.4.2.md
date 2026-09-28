<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# @libmorpheus/deno 0.4.2

This binding now acquires native libmorpheus 0.4.2. It replaces the unsafe
native 0.4.1 acquired by binding 0.4.1, which could abort the process while
analyzing forms such as `a)mfestan` with `IgnoreAccents`. Install the new native
release in a fresh directory: `/setup` and `/native` do not overwrite existing
installations.

The Deno API and required native C ABI (2) are unchanged. High-ambiguity
forms still return their full results; with the pinned Alpheios stemlib,
`a)nalow` returns 26 analyses and `a(napinw` returns 39. The native release
has regression coverage for all 46 reported crashing forms and a 33,410-lemma
Alpheios sweep. The separate 266,100-call Bailly workload needs its own
qualification before that service upgrades.

The standalone binding archive and JSR package contain no native binary or
stem data. The locally built `deno-runtime` Docker target includes native
0.4.2 when built from `v0.4.2` and installs no binding; add this JSR version as
an application dependency inside the image. The image is not published to a
container registry.
