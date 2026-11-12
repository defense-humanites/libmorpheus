<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Public C API

`<morpheus/morpheus.h>` defines the normalized structured API. Historical
`cruncher` formatting is deliberately isolated in `<morpheus/compat.h>`.
The shared library hides every other symbol, and both headers are C-compatible
from C++.

## Versioning

The current project version is 0.5.0, the SONAME major is 1, and
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

Contexts created by `morpheus_open()` and `morpheus_open_path()` do not write
to standard output or standard error: failures are reported only through
status codes. The compatibility API keeps the historical analyzer's messages on
standard error, as `cruncher` always printed them.

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
| `morpheus_generation_result_skipped_records()` | Returns the number of source records skipped because they could not be generated. |
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
> experimental. Their interfaces are tested (differential, isolation,
> failure, portability, and sanitizer coverage); the qualification will be
> lifted once generation meets both properties below and both are measured.

Generation is the inverse of analysis. It returns the forms that the
analyzer accepts for a lemma, built from the same stems and ending tables,
and aims at two properties:

- every generated form analyzes back to its lemma, with the same tense and
  mood;
- every form that analysis attributes to a lemma through its stems and
  endings can be generated.

These forms include dialectal, poetic and late variants, endings that a
source forces, and regular principal parts that no text may attest. They
carry the dialect and usage flags of the stem data, not attestations.
Generation therefore serves to find the forms of a lemma in a text, to
precompute a form-to-lemma table, and to check the stem data; it does not
give a reference paradigm, which an application must select with other
sources. A generated form may also belong to another lemma: Doric ἄγγελον,
an aorist of ἀγγέλλω, is also the accusative of ἄγγελος. To search a text by
lemma, generate the candidate forms, then confirm each match by analysis.
Generated forms are isolated words with their own accent; running text needs
the normalization that analysis applies (grave accents, enclitics, elision,
crasis).

On samples of the Alpheios data, more than 99.5 % of the generated forms
meet the first property, compounds included
([gener-derivations.md](gener-derivations.md#measures),
[compound verbs](#compound-verbs)). The second is not yet met. On the verbs
of the Perseus treebank (AGDT 2.1), 87.6 % of the tokens that analysis reads
as a verb have every such reading generated (66.6 % before compound verbs);
91.4 % of the readings as a simple verb are, 86.2 % of those as a listed
compound and 49.9 % of those as a hyphenated one.

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

A lemma has one or more source records in the index. A record that the
engine cannot generate — for example, one whose stem class has no ending table
in the stemlib, or whose forced ending matches no table cell — is skipped
instead of failing the request, and none of its forms are returned.
`morpheus_generation_result_skipped_records()` reports how many records were
skipped; it counts records, not forms, and does not depend on the filters. A
result with no records and a nonzero skipped count is a lemma whose records
all failed, not an absent one. Allocation failures still fail the request.

Generated surfaces omit the hyphen that marks the stem boundary in the stem
source: `a)nqr-w/pwn` is returned as `a)nqrw/pwn`. Where πρό, περί or προτί
meets a vowel without elision, the engine marks the hiatus with `+` after
the preverb (`pro+e/hke`). Surfaces keep it only as the diaeresis of an iota
or upsilon that would otherwise form a diphthong with the preverb's ο, placed
after that letter's own marks as the engine writes diaereses: προέηκε is
returned as `proe/hke`, περιέχω as `perie/xw`, προΐσχω as `proi/+sxw`.

### Compound verbs

Analysis does not store compound verbs: it removes a preverb from the word,
analyzes the simple verb, then names the compound after
`stemsrc/vbs.cmp.ml`. Generation composes them the same way.
`morpheus_generate()` accepts the compound lemmas that analysis reports:

- a compound the list names: `a)podi/dwmi` for ἀπέδωκε;
- preverbs and a verb the list does not join, which analysis names with a
  hyphen: `a)mfi/-lu/w` for ἀμφέλυσε, canonically `a)mfi/lu/w`;
- outer preverbs before a listed compound: `a)nti/-paradi/dwmi`.

The compound's records are the simple verb's verb records with the preverbs,
as analysis applies them; the engine places the augment between preverb and
stem, elides, assimilates and aspirates (ἀπέδωκα, ἐξέβαλον, κατέστησα,
συνέβη, πάρεστι, σύνθες). Stems that occur only in compounds take part too
([gener-derivations.md](gener-derivations.md#compound-only-records)):
ἐπιδημέω generates ἐπεδήμησε though δημέω generates nothing. A compound that
has records of its own in the index returns them as well. Verbal adjectives
are not composed, since analysis attributes ἀπόδοτος to a lemma of its own,
and neither are records that carry another preverb of their own. Records
carry the requested lemma, canonicalised.

A name that analysis never reports returns no record: `a)po/-di/dwmi`,
because analysis names that compound `a)podi/dwmi`, or a listed name that
analysis cannot reach (see the limits below). A record of a simple verb that
carries a preverb of its own (`pb:`) is generated under the lemma that
analysis names after that preverb: ἀμπέσχον under ἀμπέχω, not ἔχω.

Of the 19,289 names that `vbs.cmp.ml` lists, 19,130 generate records with
the Alpheios data. On 300 of them (seed 78), 99.90 % of the 508,733 generated
surfaces analyze back to the compound with the same tense and mood; every
other surface also fails for the simple verb, from which the compound
inherits it. The remaining limits mirror the data or are left for later:

- **Preverb variants.** Analysis also accepts Ionic unaspirated preverbs
  (ἀπίκετο), ἐς for εἰς, apocope (ἀμ-, κατ-), ἐνί, and an augment before the
  preverb; generation does not produce them yet.
- **Stems derived with their own preverb.** Analysis ignores the preverb of
  a stem derived from a `:de:` line (`:de:mel ew_denom mp pb:e)pi/` under
  μελέομαι): it reads μελεῖται under μελέομαι and μεταμελεῖται under
  μεταμέλομαι. Generation keeps these stems for the compound their preverb
  names (ἐπιμελέομαι) and does not produce the other readings; 11 listed
  names generate nothing for this reason.
- **The compound list.** `vbs.cmp.ml` is not in byte order, and analysis
  searches it by bisection: it never finds 38 of its entries and reports
  their forms with a hyphenated name (`e)k-de/rw` for ἐκδέρω). Generation
  follows; 27 of these listed names generate nothing, while their
  hyphenated names do. 11 names are hidden by another name for the same
  preverbs and verb, and 110 name a simple verb absent from the stem index;
  analysis reports none of them.

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

An analysis and a generated record carry the same flags for the same form:
those of the word together with those of its preverb, stem and ending. Stem
flags such as the irregular comparative and superlative markers therefore set
the generated record's degree as they set the analysis's.

The Node.js binding exposes the same indices through `MorpheusMorphFlag` and
returns either the public byte vector (`analyzeRaw()` and `generateRaw()`) or
stable names (`analyze()` and `generate()`); the Python binding returns the
byte vector from `analyze_raw()` and `generate_raw()` and the names from
`analyze()` and `generate()`, and `has_morph_flag()` accepts either.

## Fixed-capacity text

Every text field is NUL-terminated. At most `capacity - 1` bytes are copied.
`morpheus_result_truncated_fields()` reports any truncated field; zero means all
text was complete. The bindings' semantic APIs return named truncated fields,
while their raw APIs preserve the mask.

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
