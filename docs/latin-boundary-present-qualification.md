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

Five synthetic tests cover the five bounded patterns, rejection of other root/prefix changes, alternate quantity retention, present-only insertion, idempotence, incompatible grammar/voice/subclass, abbreviations, duplicate or flagged canonical records, and private output guards. CI applies the trial to both quantity treatments after the quotation tiers with an expected count of eleven. Full LISTALL qualification is recorded separately once complete. The production corpus remains unchanged.
