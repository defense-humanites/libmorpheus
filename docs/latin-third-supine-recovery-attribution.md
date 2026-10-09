<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Attribution of the coordinated third-conjugation supine trial

The [source trial](latin-third-supine-alternatives.md) adds 649 readings.
This review identifies which additions restore readings removed from the
historical baseline, and which native-preverb additions have literal source-base
dependencies. Addition counts alone do not establish either result.

Qualified code: `6653c1d1760e1a0ac275b5314375acedeb2df81a`.
The [dedicated job](https://github.com/defense-humanites/libmorpheus/actions/runs/37948879178/job/113882184451)
succeeds with 70 targeted checks: 51 prior checks and 19 attribution tests.
Linux CI and optimized package qualification also succeed on this commit.
The [aggregate archive](qualification/latin-third-supine-recovery-attribution-6653c1d.json)
contains receipts, categories and counts; lexical values remain private.

## Historical recovery

The comparison uses exact multisets, including multiplicities and homograph
identities, between the historical baseline, original candidate and separate
trial. It checks both eleven grammatical fields and all sixteen recorded fields
on the 245 forms in the qualified global delta.

| Attribution of the 649 additions | Readings |
| --- | ---: |
| Historical removed readings restored | 151 |
| On forms completely lost by the original candidate | 57 |
| On forms still recognized by the original candidate | 94 |
| Beyond the historical removed multiset | 498 |

The 151 restored readings agree under both signatures. The 498 other additions
are not evidence of non-attestation or rejection. On these 245 changed forms,
all 138 original sixteen-field readings are retained, 649 are added and none
are removed. This sixteen-field result is scoped to the changed forms; the
earlier whole-LISTALL eleven-field comparison remains the global receipt.

The two selected source cases account for 119 readings in the earlier
complete-loss dossier:

| Anonymous source case | Old readings | Restored | Remaining |
| --- | ---: | ---: | ---: |
| Case with 28 old readings | 28 | 28 | 0 |
| Case with 91 old readings | 91 | 0 | 91 |
| Total | 119 | 28 | 91 |

Exact source-header hashes identify these cases in the archive. No canonical
identifier is replaced or normalized to obtain recovery.

## Native dependencies

The 434 additions carrying native preverbs are compared to direct base peers.
An accepted dependency requires the recorded literal preverb followed by a
hyphen in the identifier, an exact selected source base, and matching direct
derivation and grammatical fields in both the trial and isolated source
reference. Such a peer must be absent from the original candidate.

| Dependency group | Added readings |
| --- | ---: |
| Accepted source-base dependency; historical baseline peer present | 80 |
| Accepted source-base dependency; historical baseline peer absent | 194 |
| No accepted literal identifier decomposition | 160 |
| Total | 434 |

Thus 274 additions have the qualified dependency. These groups span nine native
identifiers and two accepted literal bases. The 80 baseline peers are a separate
intersection, not a count of restored compound readings. Direct base peers do
not independently attest the composed identifier or each generated form.
All composed lexical identities remain subject to source arbitration; the
160 undecomposed readings remain unclassified.

## Reproduction and receipts

The replay selects 1,887 original literal inputs from the pinned 1,033,579-form
LISTALL using the three inserted supine stems only as a substring filter after
removing notation. It preserves the original input bytes and must reproduce
the exact previously qualified whole-input delta. This optimization introduces
no grammatical rule, quantity inference or additional qualification scope.

The replay produces the same 245 changed-form records and private delta SHA-256
`a3391afb13cfab636f50eacf2c19fe4b18a272a3ec642496733853cff3dd78f7`.
An identical-root control on these forms changes no readings. Complete native
reads require status zero and no truncation. Inputs and indexes are checked
unchanged before and after review.

The private attribution dossier agrees byte-for-byte between local execution
and CI, with SHA-256
`13e73234aeb14e7327e8dfc466d7d883bdd211c46ef86fba7722b06a8eb99f6c`.
Unjoined source cases without a header hash are excluded from the selected
source-case lookup and covered by a regression test.

## Remaining arbitration

The 91 selected historical readings, the other 25 third-conjugation source
headers, composed identities and the earlier loss dossiers remain open.
This review does not combine the separate source and present-only trials,
promote a selector or modify production sources. The PR remains a draft.
