<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Local portability findings in the historical Latin header filter

## What was observed

A local macOS replay of the pipeline qualified on `9f9ba4c` refused its final
candidate receipt. The recovered header file still matches SHA-256
`85658956fa68024d032f944f7920d38fa8b424318be6454eebdb6bd74c76cc34`,
and the nominal indexes match the qualified reference. The Python staging
tools used by the replay have the same Git blobs as that revision.

Replaying all 24 source transformation stages reproduces the old local
intermediates but yields final source SHA-256
`2f7e05eb203754cfd3cc3f55b810b86b668afc9df944f5cd9605d81dcadab4a8`,
instead of qualified Linux source
`6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9`.
The difference exists before those Python transformations:

| Initial verbal input | SHA-256 |
| --- | --- |
| Qualified Linux historical-filter output | `22196e561a802c607249597b767652b3c0f9ad797b3155a22ec11c61875c8479` |
| Old local historical-filter output | `8f234062ffeaf58e15ceabe3c8a8f5ff2ea37ef0c62d90659ea5db581a5c85de` |

Fresh local partitioning and the old local executables reproduce the latter
receipt. Recompiled `combitype`, `splitlat` and `conj1` have identical output
to their old local versions on the corresponding streams. The divergence
is isolated to `latvb`; the checked lexer sources themselves match the
qualified revision. This does not establish cross-platform equivalence of
the historical staging toolchain.

## Confirmed C defects and local build conditions

Clang rejects bare returns in the implicitly non-void historical `set_orth`.
Suppressing that diagnostic allows a diagnostic build, but the fresh local
`latvb` then stops while processing the full private input. AddressSanitizer
reports `strcpy-param-overlap` in `set_lemma` at the existing operation:

```c
strcpy(t, t + 1);
```

It removes notation characters by shifting a string left. The ranges overlap;
`strcpy` does not define this operation. The old local build already used a
private compiler-included wrapper replacing `strcpy` with a `memmove` copy.
It therefore cannot be treated as a byte-equivalent execution of the
unmodified qualified Linux filter.

Replacing only that overlapping operation in a generated diagnostic C copy
reveals another sanitizer failure: `stack-buffer-overflow` in `truncstem`,
called from `do_vstems`. The historical function forms
`workstem + strlen(workstem) - 2` when `trimn == 1`; an empty optional
orthographic stem can make this address precede its buffer. The caller
passes both the main stem and the optional orthographic stem. These findings
are reproduced on the actual private source stream; no article, headword,
stem or crash-input fixture is published.

The initial output difference has not been proved to arise solely from
either one of these defects. A single-overlap diagnostic patch does not
complete the full local replay and is not a qualified repair. Other legacy
operations and compiler conditions still need controlled examination.

## Reproducible diagnostic copy and local measurement

After guarding empty and one-character stems, AddressSanitizer reports a
second overlapping copy in `do_vstems`: the alternative-perfect branch copies
the remaining tail of `perfsuff` back into that same buffer. A private copy
replaces both `strcpy(perfsuff,t)` calls with `memmove`, including the initial
disjoint copy, as well as the notation-removal copy. Its `truncstem` uses
length-based indexes for suffix removal and reverse search, so neither empty
stems nor an absent search character form a pointer before the buffer.

`tools/probe-latin-historical-filter-portability.py` binds these interventions
to SHA-256 `27765fb0e13ba200f432c98218e1bb53126acedb391bf1d8c5cabe1fe30dd231`
of the unchanged lexer. It writes a separate lexer, generates and builds C
with AddressSanitizer and UndefinedBehaviorSanitizer, disables sanitizer
recovery, then runs the exact received private stream. It compares raw bytes
and multisets of literal lemma/directive pairs, preserving multiplicity and
homograph suffixes. It verifies all original inputs after the comparison.
Only hashes and counts are printed; process logs, outputs and differences
stay private. A difference is a measurement, not permission to replace a
qualified candidate.

The complete local macOS stream exits successfully without sanitizer output:

| Local diagnostic measurement | Result |
| --- | --- |
| Input stream SHA-256 after the first three filters | `91a7502f92f060b579f878e11c06e52f17cde1c1b66e9c0c202c467cf226ab37` |
| Diagnostic lexer SHA-256 | `197bf18656eeb1b47f040d3e6a1ce7bc93bad5475708e37d3984c3c22bbf0045` |
| Output SHA-256 | `8f234062ffeaf58e15ceabe3c8a8f5ff2ea37ef0c62d90659ea5db581a5c85de` |
| Raw bytes equal to the old local output | yes |
| Retained definition occurrences | 10,399 |
| Removed / added occurrences | 0 / 0 |
| Unchanged literal lemma multisets | 6,988 |
| Private delta SHA-256 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The defined-copy/bounds control therefore preserves the old local extraction
on this stream; it still differs from the qualified Linux output. This does
not prove portable equality or the absence of other memory defects. Six
unit tests validate receipts, multiplicity, homographs, malformed records
and private writes. Two native sanitizer tests cover short/empty stems,
absent reverse-search characters, and the complete copied lexer with
synthetic notation and alternative perfects. The workflow adds an independent
Linux comparison before the original transformation stages, with the original
Linux output receipt; its results remain pending.

The first Linux job on `b6a0454` passed six unit and two native synthetic
tests, then failed while executing the copied filter on the complete private
stream. No raw-byte or definition comparison was qualified. Its detailed
stderr remained private, and the original public failure message provided
no category or location. The tool now reports only allowlisted sanitizer
categories, source line numbers, known function names and the process exit
code on failure. It reconstructs this summary instead of copying log lines,
addresses, excerpts or paths. Three additional unit tests check redaction,
unknown errors and preservation of exclusive private logs. A failure stays
fatal; no partial result or changed receipt is accepted.

The redacted Linux failure on `2cebf54` identifies `global-buffer-overflow`
in `do_itype`, with a source location at the suffix-comparison branch. That
branch subtracts the widths of three literal endings from `strlen(lemma)`
without checking that the lemma is at least that long. The diagnostic copy
now guards those three comparisons. It also replaces the fixed backward
offset in `set_lemma` with length-guarded suffix selection, preserving the
historical order, flags and fallback; this addresses the analogous short-stem
boundary without asserting a linguistic correction.

The extended diagnostic lexer has SHA-256
`654be9aa0e2bb47ac27f9bb6f4dfe7183a522b6f657083aab99f884e806a3189`.
Its full local stream again exits without sanitizer output and reproduces
exactly the old local raw bytes, 10,399 definition occurrences and 6,988
literal lemma multisets, with zero additions or removals. Nine unit and four
native tests pass, including short synthetic lemmas through the complete
lexer and all eleven suffix/flag choices through a sanitizer-built harness.
The next Linux comparison is required before making any statement about its
output equivalence. Earlier qualified Linux candidates remain unchanged.

## Consequences for the research

The local final candidate was rejected before any real-source family or
LISTALL comparison. Its results are not substituted for the Linux
qualification. The recorded Linux metrics still describe the exact pinned
inputs and executables on which they were measured; they establish no
cross-platform portability of the historical header extraction.

No lexer source, candidate, index or production data is changed by this
investigation. The independent Linux direct-present counterfactual on `9f9ba4c`
passed the preceding qualifications, then stopped on its own directive-shape
guard before running the new global comparisons. That failure is distinct from
this historical-filter investigation. Before promoting extraction
results, a separate defined-copy/empty-stem control must compare source
identity and emitted definition multisets against the qualified historical
output, then requalify any changed candidate. Merely accepting the old local
hash or weakening its guard would erase the difference rather than resolve it.

## Completed Linux comparison on `b4cd55d`

The [Latin job](https://github.com/defense-humanites/libmorpheus/actions/runs/37909422275/job/113750704211)
completed successfully, as did [Linux CI](https://github.com/defense-humanites/libmorpheus/actions/runs/37909428223)
and [platform qualification](https://github.com/defense-humanites/libmorpheus/actions/runs/37909428206).
The [complete aggregate report](qualification/latin-historical-portability-b4cd55d.json)
records the pinned execution.

Linux and macOS received the **same input bytes**, used the **same diagnostic
lexer bytes**, and produced **identical output bytes**: the input, diagnostic
lexer and output SHA-256 values match the extended local measurement above.
Both sanitizer executions exited successfully. This establishes agreement
for these two executions and this exact stream, not universal portability
or the absence of other defects.

Relative to the original Linux historical-filter output:

| Definition multiset measurement | Occurrences |
| --- | ---: |
| Original Linux output | 10,398 |
| Diagnostic output | 10,399 |
| Retained | 10,397 |
| Removed | 1 |
| Added | 2 |

Exactly **one literal lemma multiset** changes; the other **6,987** are
identical. The raw historical and diagnostic outputs differ.
The private delta SHA-256 is
`258e211210c33e223fe3055c7c21e3a9c834f51d5e27e1ff4332d900dd2d4622`.
No changed lemma, directive or source excerpt is published.

The combined defined-copy and bounds interventions remove the observed
Linux/macOS output divergence on this stream. The experiment does not isolate
which intervention causes each changed directive or justify their lexical
content. The one-lemma delta must be reviewed against the pinned source
before rebuilding and qualifying a separate candidate. The original final
candidate receipt `6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9`
is preserved; the local alternate final receipt is not substituted.

The same completed run reproduces the entire direct-present counterfactual
report from `b022abb` exactly, including all three global comparisons, family
counts, index receipts and private delta hashes. Thus the diagnostic filter
comparison has not replaced the inputs of the existing qualification.
No production lexer, runtime index, native policy or corpus is changed.

## Private source review of the one-lemma delta

`tools/review-latin-historical-filter-delta.py` binds the original output,
diagnostic output, private delta, recovered headers and complete TEI to their
qualified hashes. It independently reconstructs the delta from the two raw
outputs, requires one changed lemma and the measured one-removal/two-addition
inventory, then revalidates the recovered headers against the pinned TEI.
The source join removes only historical notation while preserving case and
homograph digits; phrases and projection errors are excluded. A missing or
ambiguous literal join aborts the review.

Only fixed directive categories are printed. Unknown lexical tokens cannot
become public labels. For the two explicit alternative-perfect branches
already recognized by the historical lexer, a bounded source recipe preserves
the headword's quantities and constructs the expected present, alternative
perfects and optional supine. The report measures missing and extra diagnostic
directives; an unknown or ambiguous grammar is not marked as a match. This
checks source consistency, not corpus promotion or runtime acceptability.
The full header and before/after/expected directives remain in a private,
exclusive dossier, whose hash alone is published.

Six new synthetic unit tests cover categories, literal identity, quantities,
ambiguous grammar, delta validation and input receipts. A dedicated workflow
reconstructs the required source headers and four historical filters, repeats
the pinned sanitizer comparison and runs the source review. It does not build
or replace any candidate or runtime index. Its actual source-review results
are pending.

The [first dedicated review](https://github.com/defense-humanites/libmorpheus/actions/runs/37917103919/job/113775874413)
on `20cec5f` completed. The [aggregate report](qualification/latin-historical-source-review-20cec5f.json)
classifies the removal as one perfect directive and the additions as one
perfect and one supine directive. It finds exactly one source header, but the
initial two literal recipes classify its grammar as unknown. Zero expected
directives in that report means the recipe was unsupported, not that the
source contains no principal parts. No source consistency was approved.

The next bounded recipe accepts explicitly coordinated alternative perfects,
an optional explicit supine, and an explicit fourth-conjugation indication.
Only adjacent `itype` fields may be joined, following the historical
`combitype` boundary. It preserves the order-independent multiset and the
source's actual quantity notation; it does not copy quantity inserted by
historical normalization. Quantity-only missing/extra pairs are counted as
a separate diagnostic and remain unequal in the literal comparison. Eight
synthetic tests pass. The expanded recipe's real-source result is pending.

The expanded recipe on `3f02c7f` still classifies the changed lemma's grammar
as unsupported and approves no literal principal-part reconstruction. The
next trace records only counts of source type fields, bare conjugation fields
and alternative connectors. It also replays that exact revalidated header
through the first three filters and the diagnostic lexer, comparing its
selected-lemma multiset with the complete stream. This distinguishes isolated
source reproduction from stream context without publishing a header or form.
Ten synthetic tests cover these mechanisms. A matching historical replay is
mechanical evidence and cannot replace literal source attestation.

The [completed trace on `7a8cf4c`](https://github.com/defense-humanites/libmorpheus/actions/runs/37918332997/job/113779885033)
has a [full aggregate report](qualification/latin-historical-source-trace-7a8cf4c.json).
It preserves every pinned input and the private source-dossier hash
`20f15264462a6ab964f2a4d1998e2a223364f1c25fc43fba0e1863ffdac4c80a`.
The unique source header contains one `itype` field with an alternative
connector; no field is merely a bare fourth-conjugation indication. The
isolated source reproduces all four selected-lemma directives of the complete
diagnostic stream. This demonstrates reproduction without preceding articles
for this selected multiset.

The removed directive is perfect; the additions are one perfect and one
supine. The literal source recipe remains unclassified. Its zero expected
directives and zero quantity-only pairs are absence of a supported recipe,
not evidence of absent principal parts or quantity agreement. Four mechanically
reproduced directives do not count as four source-validated directives.
At this stage reconstruction of a separate candidate was withheld pending
interpretation of the actual source grammar and its quantities. No original output receipt,
qualified candidate, runtime index or production corpus is replaced.

## Explicit source alternatives qualified on `3bf22f4`

The [dedicated review](https://github.com/defense-humanites/libmorpheus/actions/runs/37919452849/job/113783585748)
completed successfully with twelve synthetic source-review tests, nine
portability tests and four native sanitizer tests. The [aggregate report](qualification/latin-historical-source-alternatives-3bf22f4.json)
revalidates all five pinned inputs and the unique literal source join.

The source grammar is now classified as an explicitly divided compound with
third-conjugation indication, two alternative perfects and two alternative
supines. The compound boundary supplies the prefix; the recipe does not infer
that boundary from the historical backwards consonant search. It preserves
all literal source quantity notation and both alternatives in each slot.
This bounded recipe applies only to one explicit compound boundary, an active
present ending, matching initial consonants, distinct alternatives and the
specified conjugation. Other cases remain unclassified.

The recipe expects five directives: one present, two perfects and two supines.
The diagnostic output has four, with one missing expectation and no extra
directive; no quantity-only difference pair is found. A local comparison of
the same pinned diagnostic output identifies the missing expectation as the
second supine. The isolated header still reproduces the complete-stream
four-directive multiset. Thus portable reproduction remains incomplete
against this source recipe and is not lexical approval.

The private source-review dossier now has SHA-256
`10d79072c4df8923acbb85fbd0cd28ec4a3e49b8a05cc2962ddb37cb03983023`.
Its changed hash records the additional source expectations; input receipts,
raw output and historical delta receipts remain identical. No source tokens,
lemma, principal parts or private logs are published. The historical filter,
qualified candidate and production corpus are unchanged. A complete candidate
and its native/global qualification remain separate work.

## Isolated native supine families qualified on `165f2d5`

The [dedicated native review](https://github.com/defense-humanites/libmorpheus/actions/runs/37920347939/job/113786502895)
completed successfully. The [full aggregate report](qualification/latin-historical-source-supines-165f2d5.json)
binds the qualified private source dossier and diagnostic raw output to their
receipts. Four trial unit tests and a native synthetic test pass, alongside
the twelve source-review tests, nine portability tests and four sanitizer tests.
The initial run on `3ad970e` stopped before real-source qualification because
the Python system environment lacked the TEI dependency; `165f2d5` uses the
existing isolated TEI environment.

Two private isolated verbal sources contain the selected lemma's four
mechanically reproduced directives and its five literal source expectations,
respectively. Exactly one source supine is inserted. Both native builds retain
the same nominal indexes and the same retained irregular verbal inputs.
These isolated sources are not the previously qualified complete candidate.

The family checks six engine-table cells per supine: two supine readings,
two perfect-passive participles and two future-active participles. Twelve
cells cover ten distinct quantity-free analysis inputs; source quantities
and compound separators remain literal in the stem input. The historical
engine labels its two supine cells nominative and dative. This diagnostic
records those API codes without claiming a philological case correction.

| Measured on ten family forms | Before | After |
| --- | ---: | ---: |
| Explicit expected cells covered | 6 | 12 |
| Expected readings | 6 | 12 |
| Recognized forms | 10 | 10 |
| All native readings | 54 | 68 |

The comparison retains all 54 readings and adds 14 on five forms, with zero
removals and no equal-count multiset changes. The added readings are direct:
two have unspecified tense (the supines), six future tense and six perfect
tense. The 14 readings include grammatical alternatives beyond the six newly
covered cells; these overlapping measurements must not be added together.
All sixteen grammatical/decomposition fields are compared on these forms,
and the eleven-field audit independently reproduces the same row totals.
Every API status pair is `0,0`; used text fields are checked for truncation.
The identical-root control retains 68 readings and changes none.

The private family evidence has SHA-256
`808b311202c8b8cc5f12c57abb99c14372b25127621b2c0a4da9e8fea0b3a200`,
identical in the local macOS and Linux runs. Inputs and baseline indexes are
verified unchanged. Lexical sources, forms, stems and native logs stay private.

This qualifies the isolated family mechanism and its measured additions.
It does not measure LISTALL, the complete verbal candidate, all inflections,
source attestation of every generated form, or global losses. Integrating the
source alternatives into a separate full candidate and requalifying its native
and global comparisons remain open. The historical lexer and production
corpus are unchanged; the PR stays draft.

The next [full-candidate qualification](latin-historical-source-candidate.md)
on `bca050d` reconstructs the original qualified candidate and measures a
separate replacement of this one lemma's directives over all LISTALL forms.
It retains 2,100,530 readings, adds 168 direct readings on 80 forms, and
removes none. Recognized-form totals are unchanged. This subsequent result
does not promote the isolated trial or resolve earlier corpus losses.



