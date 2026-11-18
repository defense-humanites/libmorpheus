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
| Historical complete-loss reproduction (`reproduce-latin-complete-losses.py`: 2,048,328 baseline rows, 6,789 forms, private difference fingerprint) | reading counts and voice | cannot reproduce |

The row count was pinned as a literal in eleven qualifiers, checked after
the LISTALL passes: on the current runtime each of them would have failed at
the end of its run. It is now pinned once, per runtime, in
`tools/qualify-latin-historical-source-candidate.py`:

- `ORIGINAL_ROWS` maps a runtime to the rows qualified for it. A runtime is
  named by the SHA-256 of the fourth-principal-part ending table its
  controlled baseline builds (`Latin/endtables/out/pp4.out`), the table the
  0.4.5 change rewrote. Its one entry is the runtime of the archived
  receipts: `62b662c8…` → 2,100,530.
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

## Running the measurement

1. Dispatch `latin-combined-candidate.yml` on a branch that has an open
   pull request. Both publication steps look for an open pull request on
   the dispatched branch; on `main` the receipt, or the exception lines of
   a failure, stay in the run log.
2. The run takes four full LISTALL passes (35 to 60 minutes on the earlier
   runtime; the synthetic list above is analysed in 24 s on the current one
   against 39 s). It needs prior agreement, like every LISTALL
   qualification.
3. From the receipt posted on the pull request: add the measured rows to
   `ORIGINAL_ROWS` under the posted table fingerprint, archive the receipt
   under `docs/qualification/`, and record the figures that moved next to
   the archived ones in [latin-combined-candidate.md](latin-combined-candidate.md).
   The earlier receipts stay: they are the measurements of their runtime.
4. The residual loss attribution and the witness backlog screen come next
   (`latin-residual-loss-attribution.yml`, `latin-witness-backlog.yml`).
   The attribution first reproduces the historical complete losses against
   values of the earlier runtime; it needs its own re-pinning, decided from
   the combined receipt.

## Limits

The chain itself was not replayed locally: it needs the pinned TEI, flex
and LISTALL. The counts above come from synthetic forms on the controlled
baseline, not from the candidate over LISTALL; they show that the counts
move, not by how much. Whether the index fingerprints of the original
candidate and the family cells hold is a prediction the run settles. The
ten separate trial qualifiers share the per-runtime pin but were not
re-run; each needs the same first measurement before its receipt can be
compared with the archived one.
