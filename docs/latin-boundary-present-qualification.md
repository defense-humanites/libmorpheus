<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Bounded prefix-boundary present alternates

This opt-in trial follows the [future/imperative quotation qualification](latin-cited-future-imperative-qualification.md). It does not require a quotation: its evidence is a complete alternate explicitly supplied by the same pinned source article, constrained to one of five whole-word spelling transformations. A single explicit class-three grammar field, compatible active voice, the same conjugation subclass and exactly one matching unflagged canonical present radical are required. Only the alternate's present radical is added; perfect and participial parts remain unchanged.

The symbolic transformations below describe entire projected headwords, with quantity marks ignored only for comparing the spelling pattern. `ROOT` is the literal remainder, not an inferred lexical base. Each emitted alternate keeps its own original quantity marks and delimiters.

| Canonical headword | Explicit full alternate |
| --- | --- |
| `a-ROOT` | `abROOT` |
| `dis-ROOT` | `diROOT` |
| `trans-ROOT` | `traROOT` |
| `ex-sROOT` | `exROOT` |
| `tran` + `sROOT` | `trans-sROOT` |

These patterns never expand an abbreviated suffix or supply a missing arbitrary prefix. They do not change native preverb policy or infer a compound paradigm from a different source article. The source revision is `56061ca127f4a2844980baffc5f2b6d1332897b3`. Actual headwords, forms and per-entry dossiers remain private.

Eleven present radicals are added under eleven existing lemma blocks, and two matching alternates are already present. The historical filters independently reproduce all eleven added stem/tag pairs using each isolated full alternate header with its original grammar.

The letter-oriented input SHA-256 is `389b969799b4a47446a13ba60e390312940ccfcf92ff77edca9daec910413f8d`; the all-quantity input is `022b6f97761008dfec9eb432736813f279aa540a5e128dfbe65c3152fab9d086`. Both build identical verbal indexes: `71f2312a7cea7209e31bf22724140d2d34af6de58ef47645a126bf05896c55da`, with sidecar `1717ed360358822c49a793c50a99c75e0efab7193301ad1a908b673c97239dcc`. Nominal indexes are unchanged.

An independent trial covers 143 present forms. Expected source-lemma present grammar increases from 13 to 143 forms, with 17 to 187 matching readings. All 277 previous eleven-field rows are retained, 170 are added and none are removed. The before/after private dossier hashes are `8143b1ec7532e2a5a72b74ef471876b3abfa3fa2183a2a3cb972c6438604b52b` and `7256c36ed41e8f827092399208b4a0d3134c03bd605c6a50472851b77fa1d237`.

Five synthetic tests cover the five bounded patterns, rejection of other root/prefix changes, alternate quantity retention, present-only insertion, idempotence, incompatible grammar/voice/subclass, abbreviations, duplicate or flagged canonical records, and private output guards. CI applies the trial to both quantity treatments after the quotation tiers with an expected count of eleven. Full LISTALL qualification follows below. The production corpus remains unchanged.

## Full LISTALL qualification

Three complete passes cover all 1,033,579 distinct literal forms with options zero and ABI two. All report zero errors; the identical control reports zero changed counts. No form is gained or lost relative to the preceding quotation trial, and all 528 changed reading counts increase. The runtime recognizes 844,546 forms and returns 2,101,290 readings, adding 794.

An eleven-field multiset comparison of every changed form retains all 1,163 previous rows, adds 794 and removes none. Before/after private dossier hashes are `78382e99863092d17858bf1ac4d810a2d0e6026111753993efaed93aeaede41e` and `154ab0478007f0630f310c89fe44a32ee2731d096a24969af00c9869189205e9`. A separate native-preverb provenance comparison classifies 780 added readings on 515 forms as direct source-lemma verb readings, and 14 added readings on 13 forms as native-prefix review leads. The form sets do not overlap; the latter readings are not source-qualified merely by the base alternate.

Baseline recognition cells remain 826,523 recognized by both, 11,467 baseline-only, 18,023 trial-only and 177,566 recognized by neither. The ordered baseline-only list is unchanged, and all original 488 first-repair losses remain absent. The original 15,255-loss subset stays at 4,238 recognized forms and 7,937 readings.

Removing precisely the eleven added alternates from the preceding inventory leaves 20 variants in 20 articles. The private inventory SHA-256 is `e4079285c26d6e73528381a4bfa18e372abae676beec5e61f188aad010a7757e`.

The next opt-in trial is documented in [bounded internal-vowel present alternates](latin-vowel-present-qualification.md).

Linux CI, platform/release qualification and lexical research passed on code commit `03426ac` (runs `36993155934`, `36993155938`, `36993149140`). All 66 synthetic tests in the twelve-tool repair/recovery pipeline passed at this stage.

A later [controlled-nominal replay](latin-present-replay-qualification.md#complete-runner-measurements)
passed on `25b5839` (research run `37341356033`). It reproduces this stage's
528 increased counts, 794 added readings and zero recognition changes:
780 additions are direct source-lemma verbs and 14 remain native-preverb
review leads. All 1,163 previous rows are retained under that replay's explicit
eleven-field grammatical scope. Its nominal witness differs from the earlier
private candidate, so its cumulative totals are recorded separately.
