<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Requalifying the Latin research on the current analysis runtime

The receipts archived by PR #18 were measured on the analysis runtime of
21 October 2026 (base `8085e2d`, before native release 0.4.5). Release 0.4.5
resolved the `pp_su` stem class (issue #37), and Latin analysis has not
returned the same readings since. The research resumes from
[issue #112](https://github.com/defense-humanites/libmorpheus/issues/112);
its first step is to measure the [combined candidate](latin-combined-candidate.md)
again on the runtime of `main`. This page records what moved, what the
qualifiers do about it, and how the measurement is run. Nothing is promoted
and no recipe changes.

## What the runtime changed

Both runtimes were built from the repository (`morpheus`,
`morpheus_stemlib_production_latin`, `cruncher`; GCC 13.3, Linux x86-64) at
`8085e2d` and at `f25fa92`, and compared on the controlled Perseids
baseline.

| Object | `8085e2d` | `f25fa92` |
| --- | --- | --- |
| `steminds/nomind`, `nomind.lindex`, `vbind`, `vbind.lindex` | identical | identical |
| `endtables/out/pp4.out` | `62b662c8…` | `3955d877…` |
| `endtables/indices/nendind` | `60fc1bb1…` | `44b715c5…` |
| `derivs/out/are_vb.out`, `ire_vb.out`, `reg_conj.out` | — | differ |

The stem indexes do not move, so the index fingerprints pinned by the
qualifiers are expected to hold. The ending tables are the ones release
0.4.5 documents: they carry `PP_SU|01` where the historical ones carried the
all-ones value of an unknown class.

Analysis differs in one respect, the one the 0.4.5 changelog states. Probed
with synthetic lemmas through the qualifiers' own trial builder:

| Records of the lemma | Participle (`-atus`) at `8085e2d` | at `f25fa92` |
| --- | --- | --- |
| `:de:` stem `are_vb dep` | passive | **deponent** |
| `:vs:` stem `conj1 dep` and `:vs:` stem `pp4` | passive | passive |
| `:vs:` stem `conj1` and `:vs:` stem `pp4` | passive | passive |

A participle is deponent when its fourth-principal-part key carries `dep`,
which a deponent derivation hands down; the future participle and the
supine of such a derivation follow. A written supine record carries no flag
(`latvb.l` prints `pp4` alone) and stays passive even under a deponent
present. Finite forms are unchanged: the passive endings of a deponent
derivation still report the passive voice.

Reading counts move with the voice: some forms keep their passive
participle reading and gain the deponent one beside it (the 0.4.5 changelog
notes it for *ingressus*). Over 519,142 synthetic forms (the 9,375
alphabetic keys of the baseline `vbind` joined to 56 endings; not LISTALL),
`cruncher` reports 18,170 participle readings under 533 lemmas with another
voice, and 65 forms with 172 more readings. It also prints another
part-of-speech letter before 7,030 supine readings; the API reports those as
verbal on both runtimes, so that difference stops at the display. Through
the API, on every seventh form, the rows go from 86,327 to 86,433.

## What that does to the qualifiers

| Pinned value | Depends on | Under the current runtime |
| --- | --- | --- |
| TEI `56061ca…`, reference filter output `22196e56…`, candidate `6caf089d…`, stage and combined fingerprints (`ec3fc3d4…`), recipe counts | source, lexer, recipes | unchanged |
| LISTALL input `1df0800f…`, 1,033,579 distinct forms | LISTALL | unchanged |
| Index fingerprints of the original candidate | stem indexes | expected unchanged (the baseline indexes are) |
| Family cells of the added records (4,404 of 4,404) | voice of written `pp4` records and of finite forms | expected unchanged |
| **2,100,530 analysis rows of the original candidate** | reading counts | **moves** |
| Every LISTALL reading count of a receipt | reading counts | moves |
| Lemma identity: 24,168 readings matched at ten fields, none at nine | voice | readings of voice variants move from ten fields to nine on participles |
| Baseline comparison the residual loss attribution checks (37,519 removed readings, 5,413 lost forms) | reading counts | the removed readings move |
| Historical complete-loss reproduction of the loss source review (`reproduce-latin-complete-losses.py`: 2,048,328 baseline rows, 6,789 forms, private difference fingerprint) | reading counts and voice | cannot reproduce |

The row count was pinned as a literal in eleven qualifiers, checked after
the LISTALL passes: on the current runtime each of them would have failed at
the end of its run. It is now pinned once, per runtime, in
`tools/qualify-latin-historical-source-candidate.py`:

- `ORIGINAL_ROWS` maps a runtime to the rows qualified for it. A runtime is
  named by the SHA-256 of the fourth-principal-part ending table its
  controlled baseline builds (`Latin/endtables/out/pp4.out`), the table the
  0.4.5 change rewrote. It holds the runtime of the receipts archived by
  PR #18 (`62b662c8…` → 2,100,530) and the current one, measured below
  (`3955d877…` → 2,102,153).
- `original_rows_differ()` replaces the literal in the eleven qualifiers. A
  qualified runtime keeps the exact check. A runtime without a qualified
  count is measured, not refused.
- The combined receipt gains `global_listall.original_candidate_rows`: the
  table fingerprint, the measured rows and the qualified count (`null` on a
  first measurement).

The native supine test, which fourteen of the fifteen `latin-*.yml`
workflows run before their LISTALL passes, now asserts the voice rule of the table above with synthetic
lemmas. A runtime that changes the rule again stops a run in its first
minutes.

A local smoke exercised the global part of the combined qualifier on both
runtimes, with surrogate inputs (two subsets of the baseline verbs as the
two candidates, 57,683 synthetic forms): identical-root control, comparison,
displacement review, baseline comparisons and both lemma-identity reviews
complete on each. On the current runtime the lemma-identity review reports
nine-field matches (16, with voice pairs passive→deponent, active→deponent
and deponent→passive) where the earlier runtime reports none, and ten-field
matches fall from 511 to 495.

## First measurement on the current runtime — `69ba91c`

The [dispatched run](https://github.com/defense-humanites/libmorpheus/actions/runs/44289719751)
succeeds in under 17 minutes, 12 of them in the four LISTALL passes (the
last run on the earlier runtime posted its receipt after 33 minutes). The
[aggregate receipt](qualification/latin-combined-candidate-69ba91c.json)
carries counts, categories and SHA-256 values only. It is compared here
with the receipt of the earlier runtime,
[`8bfd450`](qualification/latin-combined-candidate-8bfd450.json).

Nothing that depends on the source, the lexer or the recipes moves: the
eleven stage fingerprints and their counts, the combined source
`ec3fc3d4…`, the +734 / −140 records, the four index fingerprints of the
original candidate and of the trial, the family cells (4,404 of 4,404
covered after, 132 before), the 823 historical readings restored on family
forms and the enclitic displacement review are identical.

| Measure | Earlier runtime | Current runtime | Change |
| --- | ---: | ---: | ---: |
| Readings of the original candidate | 2,100,530 | 2,102,153 | +1,623 |
| Readings of the combined candidate | 2,149,567 | 2,151,190 | +1,623 |
| Readings of the controlled baseline | 2,048,328 | 2,050,019 | +1,691 |
| Forms recognized by the combined candidate | 853,570 | 853,568 | −2 |
| Forms recognized by the original candidate | 847,750 | 847,748 | −2 |
| Forms recognized by the baseline | 837,990 | 837,988 | −2 |
| Forms the combination gains / loses over the original | 5,895 / 75 | 5,895 / 75 | 0 |
| Baseline forms the combination does not recognize | 5,413 | 5,413 | 0 |
| Readings on those forms | 8,447 | 8,447 | 0 |
| Baseline forms the original does not recognize | 6,789 | 6,789 | 0 |
| Baseline readings kept by the combination | 2,010,809 | 2,012,151 | +1,342 |
| Baseline readings removed by the combination | 37,519 | 37,868 | +349 |
| Readings added by the combination | 138,758 | 139,039 | +281 |
| Historical readings no longer removed | 4,255 | 4,255 | 0 |
| Completely lost forms no longer lost | 1,376 | 1,376 | 0 |

Each of the three sides recognizes two forms fewer, and every comparison
counts the same two more forms as recognized by neither side. The receipt
does not name them. On the synthetic list the one form that lost every
reading was a nominal stem read with a supine ending, a reading only the
all-ones stem type allowed; whether the two LISTALL forms are of that kind
is not established.

Lemma identity among the readings the combination still removes:

| Measure | Earlier runtime | Current runtime |
| --- | ---: | ---: |
| Removed readings | 37,519 | 37,868 |
| Matched at ten fields | 24,168 | 21,441 |
| Matched at nine fields (voice differs) | 0 | 2,727 |
| Matched, total | 24,168 | 24,168 |
| Without lemma match on recognized forms | 4,904 | 5,253 |
| On completely lost forms | 8,447 | 8,447 |
| Active lemma matched by deponent, ten / nine fields | 5,911 / 0 | 3,742 / 1,489 |
| Deponent lemma matched by active, ten / nine fields | 4,132 / 0 | 2,860 / 1,136 |

The matched total is unchanged; 2,727 matches move from ten fields to nine
because a deponent participle no longer shares the voice of its active
doublet. The nine-field voice pairs are passive→deponent 785,
active→deponent 693, deponent→passive 608, deponent→active 561,
none→deponent 45 and deponent→none 35. The voice variants counted under
the two voice relations fall from 10,043 to 9,227: the review looks for a
ten-field match before a nine-field one, and 816 readings that no longer
match their voice doublet at ten fields match a native composition there
instead (+544, +136 and +136 under the three composition relations). The
349 additional removed readings all fall among the
readings without lemma match: the baseline gains 1,691 readings where the
candidates gain 1,623.

The measured rows are pinned in `ORIGINAL_ROWS`. The receipts of the
earlier runtime stay as they are: they are the measurements of their
runtime, and the figures of [latin-combined-candidate.md](latin-combined-candidate.md)
and of the [open decisions](latin-open-decisions.md) remain those. The
sizes of the open decisions do not move with the runtime: the 5,413 lost
forms and their 8,447 readings are the same.

## Running a measurement

1. Dispatch `latin-combined-candidate.yml` on a branch that has an open
   pull request. Both publication steps look for an open pull request on
   the dispatched branch; on `main` the receipt, or the exception lines of
   a failure, stay in the run log.
2. The run takes four full LISTALL passes and needs prior agreement, like
   every LISTALL qualification.
3. On a runtime without a qualified count, add the measured rows to
   `ORIGINAL_ROWS` under the posted table fingerprint and archive the
   receipt under `docs/qualification/`.

## What comes next

The residual loss attribution (`latin-residual-loss-attribution.yml`) has
not been run on the current runtime. Its tool checks, after its LISTALL
pass, the baseline comparison of the qualified combination: 37,519 removed
readings and 5,413 lost forms for `ec3fc3d4…`. On the current runtime the
receipt above gives 37,868 and 5,413, so that check needs the same
per-runtime pin before the attribution can run.

The witness backlog screen (`latin-witness-backlog.yml`) reads no analysis:
it compares the candidate with the curated witness and does not depend on
the runtime.

The historical complete-loss reproduction of
`tools/reproduce-latin-complete-losses.py`, which only the loss source
review runs (`latin-loss-source-review.yml`), is bound to the earlier
runtime by its row counts (2,048,328 baseline and 2,100,530 candidate rows,
now 2,050,019 and 2,102,153) and by the fingerprint of a private difference
file that carries the voice. It documents the losses as first measured and
is not a step of the resumption.

## Limits

The local counts of the first section come from synthetic forms on the
controlled baseline, not from LISTALL. The ten separate trial qualifiers
share the per-runtime pin, now qualified for the current runtime, but were
not re-run: their archived receipts remain those of the earlier runtime.
The two forms no longer recognized have not been identified.
