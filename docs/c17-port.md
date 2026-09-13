<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# C17 runtime port

## Status

The runtime closure used by `cruncher` builds in C17 mode with `-fno-common`.
This removes the dependency on the GNU `-fcommon` compatibility switch that
the inherited Perseids build required.

CMake now disables compiler language extensions, so GCC and Clang compile the
runtime and test closure with `-std=c17` rather than `-std=gnu17`. POSIX
interfaces such as `open_memstream` are requested explicitly with feature-test
macros in the translation units that use them. The shared build options enforce
`-Wpedantic -Werror=pedantic`, reject non-prototype declarations with
`-Werror=strict-prototypes`, and reject K&R-style definitions with
`-Werror=old-style-definition`. These checks cover declarations reached
transitively through the historical headers as well as declarations written
directly in the compiled sources.

SmartA and SMK output bytes above `CHAR_MAX` are converted through an explicit
8-bit representation before storage in the historical `char *` buffers. GCC's
overflow diagnostic and Clang's constant-conversion diagnostic are errors, so
new implementation-defined byte stores cannot enter the runtime unnoticed. A
stemlib-independent conversion test verifies the exact output bytes and their
round trip with both `-fsigned-char` and `-funsigned-char` in CI.
Both conversion directions also pass byte values to the `<ctype.h>` interfaces
through `unsigned char`, as required by C. The inverse converter interprets the
legacy octal SmartA/SMK ranges as unsigned bytes, so accented capitals no longer
disappear on targets where plain `char` is signed.
The same contract now covers every active `<ctype.h>` call in the runtime
closure: string bytes are converted to `unsigned char` before classification or
case conversion, while integer temporaries are initialized from unsigned bytes.
This removes the remaining locale-sensitive undefined behavior for input bytes
above `0x7f` without changing ASCII Beta Code processing.

The first staged conversion-warning pass aligns the `Xstrlen` wrapper with the
standard `size_t` contract and carries that type through string offsets,
collection counts, allocation sizes, and comparison lengths. Character-table
and in-place byte helpers now make their unsigned-byte interpretation explicit;
domain insertion rejects values that cannot be represented by its historical
single-byte storage. The cleaned translation units compile with
`-Werror=conversion -Werror=sign-conversion`, while morphology bitfields remain
a separate audited migration rather than being silenced with broad casts.
The next conversion pass keeps promoted shift expressions in unsigned working
types before storing dialect masks, carries augment offsets as `size_t`, and
represents individual morphology-flag bits as `MorphFlags` throughout their
helper boundary. This prevents compiler-dependent narrowing while preserving
the historical on-disk and in-memory field widths.
The final staged pass gives morphology-key counts an explicit checked boundary
between `size_t` and the historical integer lookup API. Morphology callbacks
mask values to their declared bitfield widths, and ending selection applies the
same bounded writes when it propagates voice, case, gender, and degree. The
runtime closure is consequently clean under both conversion diagnostics without
changing the public ABI or the stemlib record layout.

The entire `cruncher` runtime closure is now a strict boundary. Its internal
interfaces are declared in `src/anal/cruncher_internal.h`,
`src/anal/anal_internal.h`,
`src/gkdict/gkdict_internal.h`, `src/gkends/gkends_internal.h`, and
`src/gener/gener_internal.h`, with the Greek primitives collected by
`src/greeklib/greeklib_internal.h` and the morphology interfaces by
`src/morphlib/morphlib_internal.h`. All seven targets compile with
`-Werror=implicit-function-declaration`.

`src/includes/greek.h` now has an include guard, allowing these interfaces to
share its historical type definitions safely. The `addaccent` and `cinsert`
prototypes were also aligned with their existing `int` parameters.

Declaring the `morphlib` boundary exposed two more incomplete historical calls.
`fixacc.c` passed a third argument to the two-argument `getsyll` and `getsyll2`
implementations; the unused extra arguments were removed. `PrntDialect` called
the three-argument `AddDialect` without its delimiter; it now passes the space
separator expected by the formatted output. The `AddDialect` prototype was
aligned with that implementation.

All six runtime modules are explicit-return-type boundaries. Their definitions
no longer rely on implicit `int`, and their `qsort` calls use `const void *`
comparators matching the standard-library callback. All six targets treat
implicit `int` and incompatible pointer types as errors.

Typing `anal` also made its historical common-prefix structure conversions
visible. Calls that deliberately pass a generated word or analysis to helpers
which inspect only the embedded `gk_string` prefix now use explicit casts;
the corresponding allocations and layouts are unchanged.

Typing `greeklib` distinguishes in-place string mutators from queries and I/O
status functions. Pure mutators now return `void`; capitalization normalizers
return an explicit success flag, preserving their historical zero result when
no conversion is possible.

Typing `morphlib` also exposed a disk-format width mismatch: `ReadKey` stores a
32-bit offset, while `endtags` keeps the value in a `long`. `retrentry.c` now
reads through an `int` temporary before assigning the structure field, instead
of passing a `long *` to the 32-bit reader.

The first return-contract pass identified allocation, accentuation,
transliteration, and preverb helpers that only mutate their arguments. These
procedures and their public prototypes now return `void`, so callers can no
longer consume an indeterminate integer result.

Full object compilation also classifies double augmentation and the legacy Mac
transliteration entry points as in-place procedures. Their contracts now return
`void`; the standalone RTF converter instead returns an explicit success status.

Stem contraction, ending-buffer cleanup, diagnostic output, collation-table
initialization, and stem annotation are likewise side-effect-only procedures;
their definitions and internal prototypes now expose that `void` contract.

The same classification covers movable-nu insertion, present reduplication,
language selection, flag rendering, phonetic normalization, and whitespace
cleanup. Character-level SMK conversion remains a query and now returns its
input explicitly when no special mapping applies.

Index construction and file-count queries now return explicit success or count
values, while record emission, system-path rewriting, and comparison-table
initialization are declared as `void` procedures.

Morphology-key initialization and domain-name rendering now expose their
side-effect-only contracts. The first analysis pass and its unused phrase hook
also return `void`, while the public analysis entry points retain their counts.

Morphology-flag mutation, table initialization, debugging, and name rendering
now return `void`. The `has_morphflags` predicate instead returns an explicit
false value when no requested bit is present.

The final `gkstring` pass classifies deallocation, shallow analysis copying,
formatted output, and buffer-appending helpers as procedures. `low_bit_of`
remains an integer query and now returns zero when no bit is selected. With all
118 runtime sources passing full object compilation, all six libraries enforce
`-Werror=return-type` in CMake.

The first format-contract pass aligns `size_t` diagnostics with `%zu`, makes
32-bit and native offsets explicit at variadic call sites, and supplies the
missing word argument in an ending-retrieval diagnostic. The legacy numeric
ending index now copies the `word_form` bitfield representation into a checked
unsigned scalar before printing it, instead of passing a structure through a
variadic integer conversion. Local font and domain-table constants were also
renamed to avoid collisions with public macros.

Bounded filename construction now rejects oversized converter and ending-table
paths before opening files. Ending-table display lines and irregular-generation
diagnostics use buffers large enough for the declared maximum component sizes.
The same ending-table error path no longer attempts to close a null stream when
an input file cannot be opened. This removes 14 of the 16 library
format-overflow diagnostics.

The remaining compound-lemma and derivation-key builders now use scratch
buffers matching their lookup contracts, then reject values that cannot fit in
the historical destination fields. They no longer truncate keys or pass a
60-byte lemma buffer to a lookup routine that may emit `LONGSTRING` bytes. The
command-line client applies the same checked construction to input, output,
failure, statistics, and destination paths; its destination mode now initializes
all three output names. All 118 library sources plus `stdiomorph.c` pass with
format, overflow, and truncation warnings promoted to errors. CMake enforces
these checks across the runtime.

## Buffer and allocation ownership

The runtime keeps its historical caller-supplied buffer model. Functions that
receive a writable `char *` do not allocate or retain that buffer; the caller
owns its storage and must provide the capacity stated by the interface, normally
`MAXWORDSIZE` or `LONGSTRING`. Checked path and compound-key builders now fail
instead of truncating when that capacity is insufficient.

`CreatGkString`, `CreatGkAnal`, and `CreatGkword` return heap allocations.
`FreeGkString`, `FreeGkAnal`, and `FreeGkword` release them; `FreeGkword` also
owns and releases its attached analysis array and odd-key buffer. `CpGkAnal` is
a shallow copy of the analysis pointer and count, so it does not create a second
independently owned analysis array.

The `sanitizers` CMake preset instruments the full runtime with ASan and UBSan.
The separate `thread-sanitizer` preset instruments it with TSan and exercises
two public contexts concurrently. CI runs both fixture suites with immediate
failure on memory, undefined-behavior, or data-race reports. The isolated
runtime-context lifecycle test also enables leak detection.

The first instrumented fixture pass found and fixed three lifetime violations:
empty ending strings no longer read before their stack buffer, preverb suffix
checks now verify the available length before computing a suffix pointer, and
the accent-insensitive comparison buffer remains alive until its final use.
The opaque runtime context owns language selection, the lazily initialized Beta
Code collation tables, the dynamically allocated morphology-flag lookup tables,
the language-specific raw-preverb table, and both directions of SmartA/SMK
conversion state. The inverse converter's 512 allocated lookup strings are
released with their owning context. The language-specific morphology-key
tables and their sorted pointer index are context-owned as well. Contexts have
explicit create, activate, and destroy operations; file-open diagnostics and
legacy volume-name state are context-owned as well. The ending composer's
language-specific vowel-contraction and consonant-euphony tables now share the
same ownership and teardown boundary. The 45-entry ending-table cache and its
circular replacement state are context-owned too. The three dictionary
pre-indexes for verbs, nominals, and lemmas now belong to the active context and
reload when its language changes. Derivation-result caching, counters, and the
eight reusable reduplication buffers are isolated and released with the context
as well. The compound-noun head table is also context-owned, dynamically grown,
and released at teardown. Buffered analysis output and its formatting cursors
are isolated and released with their active context. The reusable augmented-
stem and possible-stem analysis buffers share the same ownership boundary.
The reusable irregular-verb form and key buffers are context-owned as well.
The crasis-analysis disable option is isolated per runtime context.
Ending-selection scratch records are call-local, and its prefix-match state is
isolated per runtime context.
Suffix-table iteration keeps its stream and unavailable state in the active
context, with teardown closing an open stream.
The ending-construction store and its counters are isolated and released with
their owning runtime context.
The six ending and stem indexes loaded by `endindex` follow the same ownership
and teardown boundary.
Analysis and lemma accounting, including the sticky storage-error marker, is
isolated per runtime context.
Greek-string reset and sorted insertion no longer rely on shared workspace or a
process-global comparator callback.
Recursive ending generation also uses call-local unrestricted-form workspace
instead of static Greek-string records.
The analysis dialect-selection mask is isolated per runtime context while
preserving the historical all-dialects default.
Dictionary-entry generation no longer stores its temporary word and blank
ending in process-wide objects.
Unused analyzer memory counters, debug state, and blank work records were
removed instead of carrying inert shared state into the library ABI.
The dictionary HQ mode and its cache invalidation snapshot now live in the
active runtime context.
The unused `BinLookPrnt` diagnostic global and its conditional output paths
were removed, with exact and lower-bound lookup behavior covered by a test.
The six built-in crasis and enclitic-suffix tables are now `static const`, with
const-correct helper boundaries for their string fields.
The legacy `quickflag` analysis mode is now an active-context option, with
independent exhaustive and early-return selection for each analyzer context.
The compatibility client's timing workspace is local to `main`; the dormant
`STEMCACHE` implementation has been removed; and ending-table utilities keep
their zero-value work records within each invocation. The runtime libraries no
longer retain writable file-scope analysis state outside the explicitly
thread-local context selectors.
Activation is thread-local, while the historical `set_lang` and `cur_lang`
calls remain compatible. Destruction releases the allocated tables, and
switching a context's language invalidates its preverb, morphology-key,
contraction, euphony, ending-table, and dictionary-index data on the next
lookup. Distinct contexts can now be analyzed concurrently; callers must still
serialize simultaneous use of the same context.

Typing `gkends` exposed a `gk_string *` passed to `FixRecAcc`, which requires a
`gk_word *` and accesses fields beyond the smaller structure. `contract.c` now
constructs the required temporary word and copies the ending metadata before
accentuation.

## Transactional bounded strings

`Xstrncat` now has a transactional failure contract: an invalid or
unterminated destination and a source that does not fit leave the destination
byte-for-byte unchanged. Runtime callers wrap that primitive with
`morpheus_runtime_string_append`, which records
`MORPHEUS_RUNTIME_ERROR_INTERNAL` on failure.

The remaining active assembly paths in `morphlib`, the dictionary and ending
modules, and the analyzer now check that contract. Multi-part keys and printed
fragments are assembled in local scratch buffers and committed only after the
complete value fits. Accentuation, augmentation, compound heads, movable-nu
insertion, ending generation, dictionary keys, and legacy analysis rendering
therefore no longer expose a truncated prefix or set metadata for a string that
could not be stored. Ending-table utilities use checked `snprintf` construction
and return a runtime error instead of terminating the process.

Focused tests cover unchanged destinations, error propagation, movable-nu
metadata rollback, accent-output suppression, and transactional conjugation
when the destination is full.

Declaring the `gkends` boundary exposed one incomplete historical call:
`mkend.c` invoked `do_dissim` without the function's required `Stemtype`.
The call now passes `stemtype_of(Have)`, which is the ending metadata inspected
by `do_dissim` when handling aorist passive participles.

## Scope of the runtime closure

The CMake runtime consists only of the sources linked by `cruncher`:

- `anal`, `gener`, `gkends`, `gkdict`, `morphlib`, and `greeklib`;
- the `stdiomorph.c` command-line client.

The stemlib compiler, Flex lexers, platform-specific front ends, and unused
analysis utilities are outside this porting scope. They are explicitly
quarantined by `cmake/HistoricalUtilities.cmake`; a CTest scope check prevents
an unclassified standalone program from entering the supported build. See
`historical-utilities.md` for the audit, maintenance decision, and criteria for
reintroducing an individual tool.

## Verified linkage constraint

`-fno-common` links the `cruncher` runtime. The ending-table counting and
indexing utilities no longer contribute the historical duplicate `Gstr` and
`endlines` symbols. Their temporary records, line table, and entry counter are
now invocation-local; the counter therefore also starts cleanly on every run.

## Release preparation status

The public ABI, installed CMake and `pkg-config` consumers, Deno FFI boundary,
compatibility client, API documentation, comparable benchmark format, and
installed-package boundary are established. Historical standalone utilities
are classified and excluded from the supported target graph. These completed
lots are summarized in the project changelog; remaining work for a published
version is the explicit release decision and artifact production described in
`releasing.md`.

The installed `pkg-config` metadata computes its prefix relative to the actual
metadata destination instead of assuming a two-component `lib/pkgconfig`
layout. This keeps prefix overrides relocatable with multi-component GNU-style
library directories. Its installation test now compiles, links, and executes
the same independent ABI consumer used by the CMake package test; checking only
the reported project version is no longer considered sufficient.

Every lot must keep both fixture suites passing: the inherited Perseids
fixtures and the pinned Greek Alpheios stemlib fixtures.

Byte-indexed collation and conversion tables are checked with
`-Werror=char-subscripts`. The context-owned comparison tables cover all 256
byte values and preserve an unsigned identity order outside the ASCII Beta Code
range. Dedicated tests run with both `-fsigned-char` and `-funsigned-char`.

The stemlib ending I/O boundary uses explicit 32-bit header words, checked
`long` file positions, and `size_t` record-size arithmetic. Its VAX-order
helpers now report partial 16/32-bit reads instead of treating truncated input
as a complete element. `endio.c` and `vaxwords.c` compile with
`-Werror=conversion` and `-Werror=sign-conversion`, and a header/record
round-trip test fixes the on-disk contract independently of the external
stemlib corpus.

The historical long-by-position helper now distinguishes an ambiguous stop
plus liquid cluster from an unambiguously long two-consonant cluster. A focused
test covers single consonants, double consonants, double letters, both cluster
orders, and vowel diacritics; it also prevents the former always-false boolean
expression from returning unnoticed.

Nested block-comment markers and ambiguous assignment or logical conditions
are rejected with `-Werror=comment` and `-Werror=parentheses`. Historical code
kept only for reference remains commented as one well-formed block, while
active conditions now state their intended grouping explicitly.

The shared library no longer imports `exit()` or `abort()`. Allocation and
internal consistency failures formerly handled by terminating the process are
recorded on the active context and returned by the public ABI as
`MORPHEUS_NO_MEMORY` or `MORPHEUS_INTERNAL_ERROR`. The public-symbol test checks
both exported symbols and forbidden process-termination imports on ELF and
Mach-O builds.
