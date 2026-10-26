<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Backlinked complete present alternates of every verbal class

Qualified code: `b94e180c61969cd8f8629d23a1078f2836f1b28e`. The
[dedicated workflow run](https://github.com/defense-humanites/libmorpheus/actions/runs/39023969432)
succeeds with the full LISTALL diagnostic for both proofs; the
[reference-proof receipt](qualification/latin-backlinked-present-classes-backlink-b94e180.json)
and the
[quotation-proof receipt](qualification/latin-backlinked-present-classes-quotation-b94e180.json)
record counts, categories and SHA-256 values only. Linux CI and the
platform/release qualification also succeed on this commit.

The [earlier backlinked-present recipe](latin-backlinked-present-qualification.md)
admits a complete same-article alternate only when the source also holds a
standalone entry for that spelling whose whole text is a bare `v. TARGET.`
reference. It is bounded to class-three active headers with explicit
principal parts. An inventory of the complete alternates still absent from
the full candidate shows the same proof available outside that selector:
second- and fourth-conjugation headers, regular first-conjugation and `-ire`
derivatives, deponents and headers whose only inflection field is an
infinitive.

## Bounded recipe

`tools/recover-latin-backlinked-present-classes.py` reuses the projection's
complete same-article alternates and stages one present record per
admitted alternate. It requires:

- a unique candidate block with exactly one unflagged present record, whose
  class tag (`conj2`, `conj3`, `conj3_io`, `conj4`, `ire_vb`, `are_vb`,
  `conj1`, with or without `dep`) decides the present ending to recognise;
  the headword must carry that ending and its root must equal the record's
  stem letter for letter, so the block's class is attributable to the header;
- an alternate carrying the same ending (hence the same voice and class),
  complete, without a leading or trailing dash, and differing from the
  headword by more than notation;
- a unique standalone source entry whose sole full orthography is the
  alternate, whose fields are at most `orth`, `itype` and a verbal `pos`,
  whose text is exactly `v. TARGET.` naming the main article's key, and
  whose inflection fields, if any, are compatible with the block's class
  (`e_re` or `2` for `conj2`, `i_re` or `4` for `conj4`, and so on).

The record is the alternate root under the block's tag and flags plus the
lexer's `orth` flag. No perfect or supine is supplied: the standalone entry
attests the present spelling only. An alternate whose ending differs from the
headword's (`claudeo` beside `claudo`, `cieo` beside `cio`, an active beside
a deponent) is withheld as another class, as are alternates without a unique
standalone entry, entries with other text, and blocks with several presents.
Six synthetic tests cover the class roots, the reference proof, insertion in
active and deponent blocks, idempotence, every withholding reason, private
output and no overwrite.

## Second proof: a whole quoted present form

The [earlier cited-present recipe](latin-cited-present-qualification.md)
admits a class-three alternate when one of the article's own
`<quote lang="la">` elements contains, as a whole word, a form of the
alternate's bounded present paradigm. The same tool offers that proof as
`--proof quotation` for every class: the paradigm is the present indicative,
infinitive and subjunctive of the block's class, active or deponent, and the
quoted word must equal the alternate root plus one of those endings letter
for letter. Everything else (unique block, single present record, headword
root identity, same ending, complete alternate) is unchanged. The two proofs
are separate trials on the original candidate and are not combined; an
alternate may satisfy both.

## Trial on the full source candidate

Over the unchanged qualified candidate
`6caf089d03e62d745aebc94d1b1cc5cf06938626db4af8c794a2326ca7a94cd9`, 83
backlinked alternates are already present (the earlier class-three recipe),
136 complete alternates have no unique standalone entry, 22 have an entry
with other text, 758 carry another ending than their headword, 88 headwords
fall outside their block's class and one reference carries another class.
The reference trial adds **19 present records in 19 blocks**: one `conj1`,
four `conj2`, eight `conj3`, three `conj3_io`, one `conj4` and two `ire_vb`.
The private trial source has SHA-256
`636f2ef1a937b3e5e263191e2a544dc7f9d7d4205cc0c5626d5d0dc1872e27a7`.

The quotation trial withholds 208 alternates without a whole quoted present
form and adds **15 present records in 14 blocks**: five `conj1`, one `conj2`,
seven `conj3`, one `conj4` and one `ire_vb`; four of them are also admitted
by the reference proof. The alternate spelling is taken literally from the
source, so an alternate written without the headword's hyphen receives an
unhyphenated stem. The private trial source has SHA-256
`e55a0e5d733731e45bdf4161da49e51e0edd5465ade68bbec06a9237d4ec4a16`.

## Native family qualification

`tools/qualify-latin-backlinked-present-classes.py` rebuilds the original
native candidate, checks its index receipts, builds each trial and requires
unchanged nominal indexes. In the reference trial the 19 records receive the
engine's present cells, 114 cells on 114 forms: six are covered before the
trial and all 114 after, every record covered. On those forms the
sixteen-field comparison retains 124 readings, adds 120 and removes none; 57
forms become recognized. Against the controlled rebuilt baseline, six of the
additions are exact historical readings and 114 lie beyond the historical
multiset: these spellings were not in the curated witness, and the present
record is the only reading each standalone entry attests. One of the 59
changed-definition loss cases has a changed block.

In the quotation trial the 15 records give 90 cells on 90 forms, six covered
before and all 90 after; 81 readings retained, 90 added, none removed, 41
forms newly recognized, and 24 of the additions are exact historical
readings. Both identical-root controls change nothing.

## Full LISTALL diagnostics

| Metric | Original candidate | Reference proof | Quotation proof |
| --- | ---: | ---: | ---: |
| Recognized literal forms | 847,750 | 848,530 | 848,453 |
| Native analysis rows | 2,100,530 | 2,103,062 | 2,102,955 |
| Lost recognized forms | — | 0 | 0 |
| Removed eleven-field readings | — | 6 | 2 |
| Added eleven-field readings | — | 2,538 | 2,427 |
| Changed grammatical multisets | — | 1,712 | 1,679 |
| Equal-count multiset changes | — | 0 | 0 |

In the reference trial 1,849 additions are direct and 689 carry native
preverbs; in the quotation trial 1,444 are direct, 859 carry native preverbs
and 124 occur on forms with both. Both profiles are dominated by the present
system (no tense, present, imperfect and future), as a present-only recipe
implies; the few perfect-system additions arise from native composition with
existing bases. The removed readings, six nominal direct readings on two
forms and two on one form, are enclitic retries displaced by a new direct
gerundive: the displacement review reproduces all of them on the input
without its `-dum`. Both identical-root controls over the same forms change
nothing; all status pairs are `0,0`. Native preverb additions do not qualify
composed identities.

## Remaining arbitration

After both proofs, **40** complete same-class alternates with a unique
verbal block remain admitted by neither: none of them is in the curated
witness, five have a standalone entry whose text carries more than the bare
reference (`etc., v. X, etc.`, `v. the preced. art.`, a reference without its
period) and the others have no standalone entry and no whole quoted present
form. `extent="full"` alone does not admit them; they stay for individual
review. Alternates of another class or voice, and the perfect and supine
systems of the added spellings, also remain open. No selector, corpus or production source is promoted;
the PR remains a draft.
