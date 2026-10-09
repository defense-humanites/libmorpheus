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
