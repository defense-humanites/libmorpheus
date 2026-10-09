<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->
# Literal third-conjugation supine alternatives

Qualified code: `60b3eb4336843dd87c0491271388515b37f556a8`.
The [aggregate receipt](qualification/latin-third-supine-alternatives-60b3eb4.json)
records the successful [dedicated workflow](https://github.com/defense-humanites/libmorpheus/actions/runs/37939914396).
The same code passed 81 CMake tests, 74 optimized-package tests, and the Linux
Python, Node.js and Deno binding checks.

## Bounded source selection

This trial screens the 27 third-conjugation headers left outside the earlier
[primary-source recipes](latin-loss-primary-source.md). Their original
complete-loss readings total 2,171. Two headers contain explicitly coordinated
supines, with three source alternatives absent from the candidate.

The triple-supine recipe accepts an ordinary active headword ending in
`o`, a fully written perfect matching the complete present radical after
quantity notation is removed for this comparison, and three coordinated
supines. Each supine stem must be at least as long as the present radical and
start with its same consonant. These are the whole-part bounds already used
by the earlier single-supine source recipe. A shared complete radical in every
supine is not required: no allomorph or contraction is generated.

The dual-supine recipe requires a headword ending in `i^o`, a three-letter
consonant-vowel-consonant radical, an explicitly written reduplicated perfect
with the bounded `C1-e-C1-e-C2` pattern, and two supine stems starting with
the complete present radical. The perfect is copied literally rather than
constructed from the pattern.

Both recipes require adjacent inflection fields and an exact literal lemma
join, preserving homograph markers. Source quantities are retained in every
declaration. Each original block must contain exactly the source present,
perfect and one supine, without extra flags or orthographic records. Only
the missing `pp4` declarations are inserted. Short suffixes, foreign initials,
unrelated perfects, nonadjacent fields, duplicate alternatives and compound
headwords are withheld. Seventeen synthetic tests exercise these bounds and
byte-preserving insertion; the dedicated workflow also repeats the 34 prior
filter, candidate and native-supine checks.

## Separate candidate and native families

The trial starts from the original full-source candidate
`6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9`.
It inserts exactly three supine declarations across two existing lemma blocks,
removes no declarations and retains every original byte. It is separate from
the earlier one-lemma source correction and present-only composition control.
No selector or production source is updated.

An isolated source reference contains all nine expected declarations for the
two headers, including five supine stems. The five supine/participle families
supply 30 diagnostic cells: 12 covered before the insertion and 30 afterwards.
All direct source-reference readings are retained in the trial on the exact
lemma, nine grammatical fields and all sixteen recorded native fields,
including literal stem, suffix, ending and preverb records. Before/after
family comparisons also check all sixteen fields. Nominal index receipts
remain unchanged.

These forms are generated from the declared source stems through the engine's
existing tables. They are not independent form attestations. The historical
`pp4` supine nominative/dative codes are recorded without claiming a
philological case correction.

## Full LISTALL diagnostic

| Metric | Original candidate | Separate supine trial |
| --- | ---: | ---: |
| Recognized literal forms | 847,750 | 847,921 |
| Native analysis rows | 2,100,530 | 2,101,179 |
| Lost recognized forms | — | 0 |
| Removed eleven-field readings | — | 0 |
| Added eleven-field readings | — | 649 |
| Changed grammatical multisets | — | 245 |
| Equal-count multiset changes | — | 0 |

Of the 649 additions, 215 are direct readings and 434 carry native preverbs.
All 2,100,530 original eleven-field readings are retained. The 171 newly
recognized forms and native preverb additions are diagnostic results; they
are not source attestation or composed-identifier approval. Across the 25
targeted family forms, the sixteen-field comparison retains 72 readings,
adds 42 on 15 forms, and removes none.

The global comparison uses all eleven grammatical signature fields, including
equal-count multiset changes; the targeted family comparison additionally
checks the five recorded derivation fields. Native reads require status zero
and complete, untruncated results. An identical-root control covers the same
1,033,579 literal forms. The archive records the original/trial source and
index receipts, comparison counts, provenance categories and private evidence
hashes. It publishes no lexical values.

## Remaining arbitration

The other 25 third-conjugation headers remain outside this recipe. The
earlier second/fourth/unclassified conjugation, nominal and unjoined dossiers,
missing-definition lemmas, native base dependencies and other grammatical
losses remain open.

The two selected headers account for 119 readings in the old complete-loss
snapshot. The global additions measured here are not a reading-by-reading
recovery of that dossier, nor source approval of every native composed
identifier. Such attribution requires a separate dossier comparison.
The earlier trials are not combined or promoted. The PR remains a draft.
