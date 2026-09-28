<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# @libmorpheus/deno 0.4.1

This binding release updates `/setup` and `/native` to acquire the published
libmorpheus 0.4.1 native runtime. That runtime fixes an internal error when a
Greek form has more than 25 analyses. With the pinned Alpheios stemlib and
`IgnoreAccents`, `a)nalow` now returns 26 analyses and `a(napinw` returns 39.

The Deno API and required native C ABI (2) are unchanged. The standalone
binding archive and JSR package contain no native binaries or stem data.
The `deno-runtime` Docker target is built from the native source tree and
includes the corrected runtime when built from `v0.4.1`; it installs no Deno
binding. Add this JSR package as an application dependency inside the image.

Existing native installation directories are not overwritten by `/setup` or
`/native`. Install into a new directory and point your application at the new
library to use the fix.
