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
- Benchmark evidence: pending (maintainer's schema 2 report from the
  controlled Apple Silicon host, on the candidate commit)
- Pre-release Linux CI: pending (the tagged commit's run)
- Pre-release platform qualification: pending (manual dispatch with
  `package_artifacts` on the exact candidate commit)

## Expected benchmark outcome

The change touches only the loading of the indices, which the benchmark's
warm measurements perform once per context before timing; the cold
`cruncher` and cold generation measurements include it. All result counts
must equal those of the accepted 0.4.3 report. Warm latencies are expected
within run-to-run variation; cold measurements may fall slightly, as each
`cruncher` process now issues a few hundred fewer system calls.

Reviewer's check: the module built from the candidate and one built from
`v0.4.3` agreed byte for byte over 3,000 Greek headwords from
`stemsrc/lemlist` and the Latin fixtures; the native suite passed, also under
AddressSanitizer, UBSan and ThreadSanitizer on `main`.

## Remaining authorization

Before publication, a maintainer must:

1. run `bench/release.sh` on the candidate commit on the controlled host,
   have the report reviewed against the accepted 0.4.3 report and committed
   with its sidecar as `bench/release-evidence/benchmark-0.4.4.json`;
2. dispatch the platform workflow with `package_artifacts` for the candidate
   commit and inspect the three native archives;
3. confirm the final tagged Linux CI and platform runs and record their links
   above;
4. explicitly authorize creation of `v0.4.4`, then of `wasm-v0.1.2` on the
   same commit or a descendant with an unchanged runtime.
