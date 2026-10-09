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
