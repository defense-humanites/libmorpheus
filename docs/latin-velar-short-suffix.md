<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Labiovelar short-suffix repair

Qualified code: `ad814035e92d83ab884368075bb00a6c90bb5812`. The
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39021056495)
succeeds with the full LISTALL diagnostic, reproducing the `9e1f809` results; the
[aggregate receipt](qualification/latin-velar-short-suffix-ad81403.json)
records counts, categories and SHA-256 values only. Linux CI and the
platform/release qualification also succeed on this commit.

Five of the 25 third-conjugation headers left outside the earlier recipes
share one source shape: an active headword in `-quo` with the abbreviated
parts `xi, ctum, 3`. They account for 384 historical complete-loss readings.
The candidate holds a defective perfect and supine for each of them.

## Historical defect

For a conjugation-3 header the historical `latvb` filter trims a fixed
number of letters from the present stem before appending the written
suffix. With `xi, ctum` it removes one letter. After a `qu`/`gu` radical that
letter is the `u` alone, so the filter writes `…qx`/`…gx` and `…qct`/`…gct`.
The written `x` already contains the velar: `qu` + `s` is `x`, and `qu` + `t`
is `ct`. The same filter handles `xi, ctum` correctly after a plain velar
(`du_co` gives `du_x`, `duct`) and handles the fully written `nxi, nctum`
alternatives, so the defect is confined to the labiovelar radical.

## Bounded recipe

`tools/repair-latin-velar-short-suffix.py` replaces exactly two records in
each matching block and nothing else. It requires:

- a projected header joined to its exact source article, whose only
  `<itype>` in both the source projection and the trial row is the literal
  `xi, ctum, 3`;
- an active headword ending in `quo` or `guo`, with an optional explicit
  prefix and homograph marker, and a radical of at least three letters;
- a unique candidate block containing exactly one unflagged `conj3`, one
  `perfstem` and one `pp4` record, where the present is the headword radical
  and the perfect and supine are precisely the defective `u`-trimmed stems.

The repaired perfect is the radical without `qu`/`gu` plus `x`; the supine is
that radical plus `ct`. Prefixes, quantities, hyphens, separators and line
endings are preserved. Deponents, other written parts, flagged records,
duplicate blocks, already repaired blocks and any other block shape are
withheld and counted. Six synthetic tests cover the source shape, the
defective-record match, separators, withheld shapes, private output and no
overwrite.

## Trial and native qualification

Over the unchanged qualified candidate
`6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9` the
recipe repairs **8 blocks and 16 records**: seven `-quo` blocks and one
`-guo` block. The private trial source has SHA-256
`1866d2bfdc73f778909e6d726be28ae34706827124e7d1d67eff0de29d5c1b45`.

`tools/qualify-latin-velar-short-suffix.py` rebuilds the original native
candidate, checks its index receipts, builds the trial and requires unchanged
nominal indexes. The 16 repaired records receive the engine's perfect and
supine cells, 96 cells on 88 forms; none is covered before and all are
covered after. The 16 removed defective stems also generated 96 cells on 88
other forms, all covered before and none after. On the 176 forms together the
sixteen-field comparison retains 30 readings, adds 280 and removes 280. The
identical-root control changes nothing.

Against the controlled rebuilt baseline, 260 of the 280 additions are exact
sixteen-field historical readings; the 20 additions beyond the baseline belong
to the `-guo` block, whose curated witness kept the defective stems. Five of
the 59 changed-definition loss cases have a repaired block.

## Full LISTALL diagnostic

| Metric | Original candidate | Labiovelar repair trial |
| --- | ---: | ---: |
| Recognized literal forms | 847,750 | 847,977 |
| Native analysis rows | 2,100,530 | 2,101,647 |
| Lost recognized forms | — | 0 |
| Removed eleven-field readings | — | 0 |
| Added eleven-field readings | — | 1,117 |
| Changed grammatical multisets | — | 385 |
| Equal-count multiset changes | — | 0 |

The removed defective stems generate no LISTALL form, so all 2,100,530
original readings are retained. Of the 1,117 additions, 514 are direct and
603 carry native preverbs; by API tense they are 22 without tense, 364 future,
533 perfect, 132 pluperfect and 66 future perfect. The identical-root control
over the same forms changes nothing; all status pairs are `0,0`. The native
preverb additions do not qualify composed identities. The complete historical
readings of the five repaired loss cases are not isolated by this global
comparison; the 260 family-form readings above are the historical attribution
so far.

## Remaining arbitration

The recipe does not read the written parts of any other header, does not
infer parts for `xi, 3` or `e^re` headers, and leaves the lexer unchanged.
No selector, corpus or production source is promoted; the PR remains a draft.
