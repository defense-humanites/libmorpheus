<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Public C API

`<morpheus/morpheus.h>` defines the normalized structured API. Historical
`cruncher` formatting is deliberately isolated in `<morpheus/compat.h>`.
The shared library hides every other symbol, and both headers are C-compatible
from C++.

## Versioning

The current project version is 0.4.0, the SONAME major is 1, and
`MORPHEUS_ABI_VERSION` is 2. Version 0.4.0 adds opt-in, non-installed stemlib
production and qualification infrastructure: the public C declarations and
symbol set remain identical to 0.3.2. The generation surface remains
experimental, but its additions remain covered by the same ABI 2 compatibility
contract.

Call `morpheus_abi_version()` after dynamically loading the library and compare
it with the header constant. `morpheus_analysis_size()` returns the producing
library's native record size for FFI consumers. Within ABI 2, removing or
changing a function, reassigning a constant, or changing the record layout
requires another ABI review.

## Ownership and concurrency

- `morpheus_open()` and `morpheus_open_path()` return owned opaque contexts;
  release them with `morpheus_close()`.
- `morpheus_analyze()` returns an owned result, including when its count is
  zero; release it with `morpheus_result_free()`.
- `morpheus_generate()` returns an owned generation result, including when its
  count is zero; release it with `morpheus_generation_result_free()`.
- `morpheus_compat_analyze()` returns an owned compatibility output; release it
  with `morpheus_compat_output_free()`.
- Distinct contexts may be used concurrently. Calls on one context, including
  destruction, must be serialized.
- Results remain independent of their context after a successful call.
- All documented `*_free(NULL)` operations and `morpheus_close(NULL)` are
  no-ops.

## Status values

| Status | Meaning |
| --- | --- |
| `MORPHEUS_OK` | Success and documented ownership transfer. |
| `MORPHEUS_INVALID_ARGUMENT` | Invalid pointer, input, language, or option combination. |
| `MORPHEUS_ABI_MISMATCH` | Header ABI or configuration size mismatch. |
| `MORPHEUS_NO_MEMORY` | Allocation failed. |
| `MORPHEUS_INPUT_TOO_LONG` | Input or constructed stemlib path exceeds capacity. |
| `MORPHEUS_OUT_OF_RANGE` | Result index is invalid. |
| `MORPHEUS_INTERNAL_ERROR` | Internal state or arithmetic failure. |
| `MORPHEUS_BUFFER_TOO_SMALL` | Caller storage is too small. |
| `MORPHEUS_STEMLIB_ERROR` | Required language data is absent, unreadable, or empty. |
| `MORPHEUS_RESULT_LIMIT_EXCEEDED` | A generation request matched more records than its configured limit. |

`morpheus_status_message()` returns borrowed static diagnostic text. Programs
should branch on the numeric status.

## Function reference

| Function | Contract |
| --- | --- |
| `morpheus_abi_version()` | Returns the loaded ABI version. |
| `morpheus_analysis_size()` | Returns the native analysis-record size. |
| `morpheus_generation_size()` | Returns the native generation-record size. |
| `morpheus_status_message()` | Returns borrowed status text. |
| `morpheus_open()` | Creates a validated context from `morpheus_config`. |
| `morpheus_open_path()` | Creates a context from an explicit-length path. |
| `morpheus_close()` | Destroys a context and its caches. |
| `morpheus_analyze()` | Produces normalized structured analyses. |
| `morpheus_generate()` | Produces normalized forms for one Greek lemma. |
| `morpheus_result_count()` | Returns the count, or zero for `NULL`. |
| `morpheus_result_copy()` | Copies a record into caller storage. |
| `morpheus_result_get()` | Copies a record into `morpheus_analysis`. |
| `morpheus_result_truncated_fields()` | Reports truncated fixed-text fields. |
| `morpheus_result_free()` | Destroys a structured result. |
| `morpheus_generation_result_count()` | Returns the generated interpretation count. |
| `morpheus_generation_result_copy()` | Copies a generated record into caller storage. |
| `morpheus_generation_result_get()` | Copies a generated record into `morpheus_generation`. |
| `morpheus_generation_result_truncated_fields()` | Reports truncated generated text fields. |
| `morpheus_generation_result_free()` | Destroys a generation result. |
| `morpheus_compat_analyze()` | Produces historical `cruncher` text and counts. |
| `morpheus_compat_output_data()` | Returns borrowed formatted bytes. |
| `morpheus_compat_output_length()` | Returns the formatted byte count. |
| `morpheus_compat_output_analysis_count()` | Returns the analysis count before formatting. |
| `morpheus_compat_output_lemma_count()` | Returns the distinct-lemma count. |
| `morpheus_compat_output_free()` | Destroys compatibility output. |

Analysis inputs are explicit-length byte sequences. They need not end in NUL,
but an embedded NUL is invalid.

## Greek lemma generation

> [!CAUTION]
> The generation implementation and its public generation functions are
> experimental. Their contracts are tested, but the qualification remains
> until sufficient real-world use complements the automated differential,
> isolation, failure, portability, and sanitizer coverage.

`morpheus_generate()` accepts an explicit-length Greek Beta Code lemma. It
applies the generation-index canonicalisation rules (initial `!`, hyphens,
quantity marks, and diaeresis marks are removed), preserves duplicate
morphological interpretations and dual forms by default, and returns records
in a deterministic total order. Results own all text and remain valid after
their context is closed.

Pass `NULL` options for defaults, including a 4,096-record limit. A non-NULL
`morpheus_generation_options` must set
`MORPHEUS_GENERATION_OPTIONS_VERSION`, its complete `struct_size`, and may set
a limit up to `MORPHEUS_GENERATION_MAX_LIMIT` (65,536). Zero trait fields mean
no filter. Equality-valued traits select one value; dialect, region, gender,
case, and voice fields accept their documented masks. Dialect-neutral forms
match any requested dialect. `MORPHEUS_GENERATION_EXCLUDE_DUALS` removes dual
records and conflicts with an explicit dual-number filter.

Generation is currently Greek-only. The context loads and validates
`<stemlib_path>/gener.index` on its first generation call and retains it for
warm lookups. The index is derived stem data and is not part of the installed
C ABI package. Its absence does not affect analysis calls; generation reports
`MORPHEUS_STEMLIB_ERROR` until a valid index is deployed.

## Normalized analysis values

ABI 2 exposes only public `uint32_t` values. Person, number, tense, mood, and
degree are equality-tested enumerations. Gender, case, voice, dialect, and
geographic region are public masks and may combine values. The bridge converts
between these values and the engine's historical encodings; equality between a
public constant and an internal constant is never part of the contract.

`MORPHEUS_DEGREE_NONE` distinguishes an inapplicable degree from
`MORPHEUS_DEGREE_POSITIVE`. Irregular comparative and superlative markers are
normalized by the native bridge before a result is returned.

The record does not expose stem-type or derivation-type numbers. The public
part-of-speech classification replaces the useful lexical portion of those
internal identifiers. No stemlib record number is a supported ABI value.

## Public traits

`morph_flags` is an 11-byte public bitset covering
`MORPHEUS_MORPH_FLAG_COUNT` named traits. Trait values are zero-based,
alphabetically ordered public indices. For trait `n`, inspect byte `n / 8` and
bit `1 << (n % 8)`. The bridge translates each selected historical flag into
this representation; raw engine bytes and sparse historical flag numbers are
not returned.

The Deno binding exposes the same indices through `MorpheusMorphFlag` and
returns either the public byte vector (`analyzeRaw()` and `generateRaw()`) or
stable names (`analyze()` and `generate()`). `hasMorpheusMorphFlag()` accepts
either representation or a readonly array of analyses or generations.

## Fixed-capacity text

Every text field is NUL-terminated. At most `capacity - 1` bytes are copied.
`morpheus_result_truncated_fields()` reports any truncated field; zero means all
text was complete. The Deno semantic API returns named truncated fields, while
the raw API preserves the mask.

## Request options

Options are scoped to one `morpheus_analyze()` call. State is restored before
returning on success or failure.

| Option | Effect |
| --- | --- |
| `MORPHEUS_OPTION_STRICT_CASE` | Requires the requested capitalization path. |
| `MORPHEUS_OPTION_IGNORE_ACCENTS` | Enables accent-insensitive fallback. |
| `MORPHEUS_OPTION_VERBS_ONLY` | Restricts results to verbal forms. |
| `MORPHEUS_OPTION_NO_CRASIS` | Disables crasis expansion. |
| `MORPHEUS_OPTION_QUICK` | Stops after the first successful dictionary class. |
| `MORPHEUS_OPTION_HQ_DICTIONARY` | Uses the optional HQ dictionary backend. |
| `MORPHEUS_OPTION_DIALECT_*` | Combines one or more public Greek dialect masks. |

Dialect options are converted to the internal mask by the bridge and are
invalid for Latin or Italian contexts. Unknown option bits are invalid.

## Stemlib validation

Context creation verifies the language-specific rule, dictionary, ending, and
derivation files before analysis. This catches deployment errors but does not
fully validate historical binary formats; differential fixtures remain the
integrity check for distributed data.

## Historical compatibility API

The compatibility API exists for `cruncher` behavior and migration testing.
Include `<morpheus/compat.h>` explicitly. Its formatter flags retain their
historical octal layout, and the implementation remains on the MPL side of the
licensing boundary. New integrations should include only
`<morpheus/morpheus.h>` and use structured results.
