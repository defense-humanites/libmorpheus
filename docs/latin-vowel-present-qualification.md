<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Bounded internal-vowel present alternates

This separate opt-in trial follows the [prefix-boundary qualification](latin-boundary-present-qualification.md). Its evidence is a complete same-article alternate whose literal word differs by exactly one internal `a/e` substitution. At least two initial letters are unchanged, the changed vowel is bounded by consonants, and an explicitly delimited canonical prefix is preserved. Quantity and delimiter removal is used only for comparing this spelling pattern; the emitted alternate retains its own source notation.

The shared source selector requires one explicit class-three grammar field, compatible active voice, the same conjugation subclass and exactly one source-matched unflagged canonical present radical. Only the alternate present radical is appended. No perfect or participial system is inferred from the vowel alternation, and native preverb policy is unchanged. The pinned source revision is `56061ca127f4a2844980baffc5f2b6d1332897b3`. Actual lexical material and per-entry dossiers remain private.

Four records are added under four existing lemmas. Historical filters independently reproduce all four added present stem/tag pairs using each isolated full alternate header with its original source grammar.

The letter-oriented candidate SHA-256 is `0481b80e25400c487ef5014a49342ae1cb8c07f00799ce60615c0e2666693d7a`; the all-quantity candidate is `8b70021dabfb0206be383b5bf8d0a9e0022e443a0e52438e4cc9cd663731fc13`. Both build identical verbal indexes: `2814f68fbad7422f4a0989bba5f6b2569cc89410888d0839c959f2f84ea0440c`, with sidecar `cb19cbd144955a2440a090b6f0747c0c6f654a5ed9bcf7e30e3645c2511ec907`. Nominal indexes are unchanged.

An independent 52-form present trial increases expected source-lemma present grammar from zero to 52 forms, with 68 matching readings. All 61 previous eleven-field rows are retained, 68 are added and none are removed. Before/after private dossier hashes are `5143b76b4406deeec2d9393c508ca97f8da81147ec3a94384bd4fabcd5d849f3` and `30cda85526dcef0ea6033dfc4b31abb29861e141115136cc0a29c5076a31c28d`.

Five synthetic tests cover internal-vowel and prefix constraints, rejection of other edits and shortened words, homograph/quantity retention, present-only insertion, idempotence, incompatible voice/grammar, abbreviations, ambiguous or flagged canonical records, and private output permissions/count/no-overwrite guards. CI applies the trial after the boundary trial in both quantity treatments with an expected count of four. Full LISTALL qualification is recorded separately once complete; the production corpus is unchanged.

Removing precisely the four added alternates leaves 16 variants in 16 articles. The private inventory SHA-256 is `9bc4d2c9dd32652c1bf99f8d81c425e7991868515d4e15d81c3a121b1d8fd79d`.
