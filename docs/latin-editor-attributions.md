<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Editor attributions tagged as inflection fields

Qualified code: `ad814035e92d83ab884368075bb00a6c90bb5812`. The
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39021056468)
succeeds with the full LISTALL diagnostic; the
[aggregate receipt](qualification/latin-editor-attributions-ad81403.json)
records counts, categories and SHA-256 values only. Linux CI and the
platform/release qualification also succeed on this commit.

Two of the 25 third-conjugation headers left outside the earlier recipes,
and thirteen other verbal headers of the full candidate, share a markup
accident of the archival Lewis & Short TEI: an editor name or a citation is
tagged `<itype>` (`<itype>Kayser</itype>`, `<itype>Ritschl, Fleckeisen</itype>`,
`<itype>Liv 33</itype>`) immediately before the written principal parts.
The two complete-loss cases account for 132 historical readings.

## Historical defect

The historical `latvb` filter reads the first `<itype>` that follows the
headword as the perfect specification. With an attribution in that position
it trims the present stem, concatenates the capitalized token and writes a
`perfstem` record such as `…dKayser`; the written parts that follow are then
ignored. For a first-conjugation header the `conj1` filter likewise fails to
recognise the regular `a_vi, a_tum, 1` pattern behind the attribution, so the
present is emitted as a bare `conj1` stem instead of the regular `are_vb`
derivative: the engine still reads its present, but has no perfect or supine.
When the attribution stands between two `<orth>` fields, the lexer's own
`<orth>` rule resets its state and the written parts are read normally; those
blocks are unaffected and the trial leaves them unchanged.

## Bounded recipe

`tools/recover-latin-editor-attributions.py` adds no stem of its own. For
each projected header it:

- selects the `<itype>` fields whose text begins with an ASCII capital
  letter, after checking that the same text is an `<itype>` of the source
  article (Latin grammar fields are lowercase; the capital marks a name or a
  citation), and requires a lowercase grammar field after the last of them;
- withholds `-io` headwords, whose part trimming is the subject of a
  separate repair;
- replays the unchanged historical filter chain (`combitype`, `splitlat`,
  `conj1`, `latvb`) on the single header **with** its fields and requires
  the output to equal the candidate block exactly, so the block is
  attributable to this header alone;
- replays the same chain on the header **without** the attribution fields
  and replaces the block with that output, provided the replay yields one
  block under the same lemma, contains no capitalized stem, and keeps every
  stem spelling of the non-attribution records; a replay that drops a stem
  (as happens when the lexer loses an `orth` derivative) or yields no block
  is withheld and counted.

A present kept alive as `conj1` may come back as the regular `are_vb`
derivative; that reclassing is the filters' own behaviour for the grammar
field and is counted separately. Seven synthetic tests cover the attribution
test, source and grammar bounds, the anchor and replay bounds, reclassing,
the filter driver and the private output.

## Trial on the full source candidate

Over the unchanged qualified candidate
`6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9`, 31
projected headers carry an attribution field before a grammar field; 25 more
carry one with no grammar field after it and are withheld. Ten of the 31
blocks are unaffected, one is the `-io` case, one has no candidate block
reproduced by the anchor replay, six have no unique candidate block, one
yields no block without the field, and one loses a stem. The trial replaces
**12 blocks**: 13 attribution records are removed, 8 `conj1` presents are
reclassed as `are_vb` derivatives, and 4 perfects and 3 supines are written
from the source parts. The private trial source has SHA-256
`46e06edb3f4401c1ce0f921f53c11d602ff0fa44a8222e982e13d33dec992dde`.

## Native family qualification

`tools/qualify-latin-editor-attributions.py` rebuilds the original native
candidate, checks its index receipts, builds the trial and requires unchanged
nominal indexes. The 15 added records receive the engine's present, perfect
or supine cells, 90 cells on 87 forms with the reclassed presents: 48 are
covered before and all 90 after, every added record covered. The 48 cells of
the reclassed `conj1` presents remain covered. On these forms the
sixteen-field comparison retains 229 readings, adds 122 and removes none; 13
forms become recognized and none is lost. The identical-root control changes
nothing.

Against the controlled rebuilt baseline, 80 of the additions on these forms
are exact sixteen-field historical readings and 42 lie beyond the historical
multiset. Two of the 59 changed-definition loss cases have a replaced block.

## Full LISTALL diagnostic

| Metric | Original candidate | Editor attribution trial |
| --- | ---: | ---: |
| Recognized literal forms | 847,750 | 847,926 |
| Native analysis rows | 2,100,530 | 2,101,682 |
| Lost recognized forms | — | 0 |
| Removed eleven-field readings | — | 0 |
| Added eleven-field readings | — | 1,152 |
| Changed grammatical multisets | — | 618 |
| Equal-count multiset changes | — | 0 |

All 2,100,530 original readings are retained: the reclassed presents keep
their LISTALL readings. Of the 1,152 additions, 882 are direct, 68 carry
native preverbs and 202 occur on forms with both; by API tense they are 27
without tense, 330 future, 597 perfect, 132 pluperfect and 66 future perfect.
The identical-root control over the same forms changes nothing; all status
pairs are `0,0`. The complete historical readings of the two replaced loss
cases are not isolated by this global comparison; the 80 family-form
readings above are the historical attribution so far.

## Remaining arbitration

The recipe does not read parts for headers whose grammar follows no
attribution, does not touch the `-io` class, and leaves the lexer and the
withheld blocks unchanged. No selector, corpus or production source is
promoted; the PR remains a draft.
