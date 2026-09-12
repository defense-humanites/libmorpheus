<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Historical utility policy

The published project installs one standalone program: `cruncher`, implemented
by `src/anal/stdiomorph.c`. The shared library and this compatibility client
form the supported runtime. They are the only installed executable surfaces
covered by the C17, sanitizer, portability, and public-error contracts.

The repository also preserves 50 quarantined historical programs. They are not CMake
targets, are not installed, and are not part of release qualification. The
authoritative inventory is `cmake/HistoricalUtilities.cmake`; CTest scans every
C source below `src` and fails if a `main()` is neither the supported client nor
explicitly quarantined.

## Classification

| Group | Purpose | Decision |
| --- | --- | --- |
| Analysis front ends | Window, batch, scanning, lemma and proper-name experiments | Retain as source reference; replace with public-API clients if a workflow is still needed. |
| Stemlib data tools | Conjugation, generation, dictionary indexing and ending-table drivers | Five ending-table producers, two lexical indexers, and `do_conj` are now internal CMake tools; retain the others for provenance and port them one at a time. |
| Platform and corpus tools | SmartA, troff, TLG, retrieval, scanner and interactive test programs | Retire from the portable build; they depend on obsolete platforms, formats, or unsafe terminal input. |
| Diagnostics | Ad-hoc Greek-library and morphology test drivers | Retire in favour of focused CTest cases. |

The low-level ending and dictionary routines used by the runtime are not in
this quarantine. Their CMake-linked implementations remain covered by the
strict compiler flags and runtime tests even when an old standalone driver for
the same subsystem is excluded.

## Stemlib production restoration

The first restoration tranche makes five inherited ending-table producers
available as explicit internal CMake targets:

- `morpheus_stemlib_buildword`;
- `morpheus_stemlib_buildend`;
- `morpheus_stemlib_indendtables`;
- `morpheus_stemlib_buildderiv`;
- `morpheus_stemlib_indderivtables`.

They are excluded from the default build unless
`MORPHEUS_BUILD_STEMLIB_TOOLS=ON`; the aggregate
`morpheus_stemlib_ending_tools` target lets CI compile them explicitly. They are
never installed. Their points of entry now obey C17 declarations, reject
invalid command lines, and propagate table-expansion and output failures.

The opt-in `morpheus_stemlib_production` target composes the ending and lexical
producers into fresh Greek and Latin build-tree stages. It is an internal data
qualification target, is never part of the default build or installation, and
records its orchestration recipe in the resulting provenance.

The nominal and verb stem indexers are also internal, opt-in CMake tools. Their
drivers require explicit input and output paths, eliminating the inherited
shared `/tmp/nommorph` and `/tmp/vbmorph` interface. The underlying producer is
C17-clean and rejects unavailable, empty, oversized or structurally invalid
inputs as well as allocation and index-construction failures. The lexical recipe now consumes checksum-pinned ordered inputs on top of the
verified table staging. `do_conj` is an internal C17 tool with explicit input,
expanded-output and odd-key-output paths. It rejects missing rule tables and
unmatched principal parts, and removes its owned outputs on failure.

The same recipe now invokes `buildword` on the pinned Greek and Latin
`irreg.nom.src` and `irreg.vbs.src` inputs before assembling the nominal and
verbal corpora. The prepared `nom.irreg` and `vbs.irreg` files are comparison
baselines rather than trusted inputs. Producer failures retain diagnostics but
cannot emit a lexical success receipt.

This remains production infrastructure, not a supported stemlib compiler.
Positive Greek and Latin fixtures and both complete corpora have reproducible
output receipts. The Latin verbal chain completes after proving that the
declared missing `vbs.mpi` contributed no bytes to its historical assembly
baseline; verified staging corrections also qualify the Latin nominal corpus
without modifying its historical sources. See
[`stemlib-production-manifest.md`](stemlib-production-manifest.md).

## Generation integration

The experimental lemma-generation feature does not reintroduce the historical
`gener` or `do_conj` executables. The request path reads a deterministic reverse
index through an internal service, constructs call-local `gk_word` values, and
invokes only the reusable `GenStemForms()` and `GenIrregForm()` core. An
internal normalizer then removes historical stem and derivation codes before
the public C API or Deno binding receives a result.

Two purpose-built CMake tools prepare that data outside the runtime request
path:

- `morpheus_gener_source_preparer` expands derivations and continuations from
  the pinned source corpus;
- `morpheus_gener_index_builder` writes and validates `gener.index`.

These tools are build-time infrastructure, are not installed, and do not make
the quarantined front ends supported. In particular, `genermain.c`,
`gensynform.c`, and the remaining historical generation drivers
retain their provenance-only status. The new implementation and its Deno
`generate()` surface remain experimental until real-world use, in addition to
the current differential, isolation, failure, portability, and sanitizer
tests, provides sufficient operational validation.

The supported local data-preparation recipe in
[`runtime-data.md`](runtime-data.md) invokes those two narrow targets through
`tools/prepare-runtime-data.sh`. This convenience workflow does not install or
expose either executable, does not revive a historical driver, and keeps the
derived index outside release and JSR artifacts.

## Safety findings

The remaining quarantined programs still contain unbounded input and formatting calls,
including `gets`, `sprintf`, and `strcat`; some also assume historical filesystem
layouts or terminal encodings. Compiling all inherited Makefile targets would
therefore create binaries with guarantees substantially weaker than
`libmorpheus` and `cruncher`. The compatibility Make job intentionally builds
only `src/libs` and `src/anal/cruncher`.

Keeping these sources is useful for format provenance, but their presence must
not imply support. Release archives may contain them as reference source; no
headers, executable, or package metadata exposes them to consumers.

## Reintroduction criteria

A quarantined program can become supported only in a dedicated change that:

1. states the current use case and input/output contract;
2. replaces unsafe input and bounded-buffer operations;
3. removes process-global or platform-specific assumptions, or documents a
   deliberately narrow platform contract;
4. adds a CMake target disabled by default until its fixtures and sanitizer
   tests pass;
5. moves the entry point from the historical manifest to the supported list
   and updates packaging documentation.

For new integrations, regenerating a data artifact should normally use a new,
narrow tool over the public or internal typed APIs instead of reviving a
large historical front end unchanged.
