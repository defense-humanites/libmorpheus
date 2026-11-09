<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# @libmorpheus/deno 0.4.3

Version 0.4.3 is the **final release** of the Deno binding. Deno's maintainers
announced the end of its development on 2026-10-09, and the maintainer decided
on 2026-11-09 that libmorpheus would no longer depend on Deno: the benchmark
harness already runs under Node.js, and this binding, its release workflow,
its JSR smoke test and the `deno-runtime` Docker target are removed from the
repository after this release. The JSR package stays available, frozen at this
version.

## Why a final version

Binding 0.4.2 acquires native libmorpheus 0.4.2. Users who stay on the Deno
binding would otherwise never receive the native releases that followed. This
version declares **native 0.4.5** (C ABI 2, unchanged since 0.2.0), so `/setup`
and `/native` acquire the `v0.4.5` archives, verified against their published
sidecars: the provenance release 0.4.3, the single-request index loaders of
0.4.4 and the stem-class resolution of 0.4.5, under which the perfect
participles of Latin deponent lemmas are reported as deponent (see
[release-0.4.5.md](release-0.4.5.md)). Greek results are unchanged.

It also carries the deprecation notice where users see it: at the top of the
README, which JSR shows on the package page, and in the module documentation.
A published JSR version cannot be edited, so a release is the only way to put
the notice on JSR. The notice directs new code to `@libmorpheus/wasm`, which
runs under Deno without the FFI permission, or `@libmorpheus/node` on Node.js.
The README no longer documents the `deno-runtime` Docker target, which is
withdrawn with the binding.

The API is unchanged. The binding's tests pass against the tree's library,
which is 0.4.5's, and the published 0.4.5 Linux x86-64 archive was exercised
through the binding during preparation (Latin `amatus` analyzed as `amo`). The
standalone binding archive and the JSR package contain no native binary or stem
data.

## Publication

As for 0.4.2: an authorized `deno-v0.4.3` tag makes `deno-release.yml` verify
the versions and the published native release `v0.4.5`, package and verify the
standalone archive, publish it as the release's assets, and publish the JSR
package. After publication, a maintainer may archive the package in its JSR
settings if JSR offers it, so that the page marks it as no longer maintained.

## Publication record

- Tag: `deno-v0.4.3`, created by the maintainer on 2026-11-09 on
  `78b122376868596ec81e976e3508c1341ea1776f`, the merge of this decision.
- Tagged Linux CI: [passed](https://github.com/defense-humanites/libmorpheus/actions/runs/42621217458).
- Publication workflow: [passed at the first attempt](https://github.com/defense-humanites/libmorpheus/actions/runs/42621217202):
  the [`deno-v0.4.3` release](https://github.com/defense-humanites/libmorpheus/releases/tag/deno-v0.4.3)
  carries `libmorpheus-deno-0.4.3.tar.gz` and its sidecar, with the tag as
  title and the release notes as body, and JSR accepted
  `@libmorpheus/deno@0.4.3`, which shows the deprecation notice.
- The binding, its workflows and the `deno-runtime` Docker target were then
  removed from the repository; this version is the last.
