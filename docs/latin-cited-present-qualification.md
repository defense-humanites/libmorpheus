<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Citation-supported third-conjugation present alternates

This opt-in research stage follows the [velar suffix qualification](latin-velar-suffix-qualification.md). It requires a complete same-article alternate, a single source principal-parts field ending in class three, compatible active voice, and a whole-word Latin quotation matching the alternate's bounded present paradigm. The candidate must contain exactly one unflagged canonical present radical in the same conjugation subclass. Only an orthographic present radical is appended; perfect and participial records are preserved.

Quotation matching is literal after the existing Latin projection and quantity/delimiter removal. It does not expand abbreviated forms, replace a missing compound prefix, search translations, or infer principal parts. A quotation is evidence for the spelling; the controlled generator trial separately verifies the present paradigm. It does not establish the semantics of every generated reading or validate native preverb analyses.

On the pinned source revision `56061ca127f4a2844980baffc5f2b6d1332897b3`, eleven records are added under eleven existing lemma blocks. Three attested alternates are already present, three ambiguous source/candidate joins are withheld, and one notation-only variant is withheld. All actual articles, forms, quotations, and per-entry checks remain private.

Both quantity treatments produce identical native indexes. The letter-oriented candidate SHA-256 is `400c28d887045100f9e8b1aa703345bfe19db562e3de454b5abf6c166831f1e6`; the all-quantity candidate is `8acff6ba36f422207288bee3e6bb9c1f8ec4e7c15c394bdb697633048571c5d1`. The verbal index is `530b5e6db59c6aaaea3a8aff7846f6492ef4b58ca01f379323f59d5bdef7d5bd`, with sidecar `13d73e9467b1d37e8c298a5e102c09ad00a500704c400aae68e36e6d1abf1baa`. Nominal indexes are unchanged.

The historical header filters independently reproduce all eleven added present stem/tag pairs from isolated alternate headers with their original source grammar. This does not promote any other output of those isolated headers.

The independent targeted trial covers 143 literal forms: six present indicative, six present subjunctive, and one present infinitive per radical. Expected source-lemma present grammar increases from 26 to 143 forms, with 37 to 187 matching readings. All 259 previous eleven-field readings are retained, 150 are added, and none are removed. Before/after private dossier SHA-256 values are `ac644eb3f7d99d1050273119e210a4e175e20aebad284073ee26e3050cd9779c` and `3a245c6a102c9cf4d202eb6a23079986c060bfd96c843e2308740e3343da40e2`.

Five synthetic tests cover present-only insertion and idempotence, quotation language and whole-word boundaries, abbreviated compound exclusion, grammar/voice/subclass rejection, ambiguous or flagged canonical records, and private output permissions/count/no-overwrite guards. The CI pipeline runs this stage after the suffix trial in both quantity treatments with an expected count of eleven. No production corpus or native preverb policy is changed.

## Full LISTALL qualification

Three complete passes cover all 1,033,579 distinct literal ASCII forms with options zero and ABI two. Every pass reports zero errors; the identical-root control reports zero changed counts. Relative to the previous suffix trial, no form is gained or lost and 520 forms have increased reading counts. The final trial recognizes 844,237 forms and returns 2,098,476 readings, an increase of 783.

An eleven-field multiset comparison of all 520 changed forms retains all 862 previous readings, adds 783, and removes none. Before/after private dossier hashes are `d0c1f0d6aee4146972f963184d0d3a9a0a312c5c8e22834b49ce258c3553f087` and `3df3d99e74dabab6ff5703ebb31c59495f7600da79ce4d9ebf59a44458e67505`. A separate native-preverb provenance comparison classifies all 783 added rows as direct source-lemma verb readings, covering all 520 forms. No added row requires native prefix inference.

The baseline recognition cells remain 826,523 recognized by both, 11,467 baseline-only, 17,714 trial-only, and 177,875 recognized by neither. The ordered baseline-only form list is unchanged, so its previously recorded private source-join review remains applicable. The original 15,255-loss subset retains its previous 4,238 recognized forms and 7,937 readings; none of the original 488 first-repair loss forms becomes recognized. Counts and provenance do not establish semantic equivalence for the whole corpus.

Removing only the eleven added alternates from the previous review inventory leaves 35 variants in 35 articles. Other alternates in an already treated article remain in this inventory. Its private SHA-256 is `639b815a56d0104e32ad181e1070359ea6e5a152cf5bae3e477f33159fcb3a21`. Lack of a qualifying quotation withholds a variant from this trial; it does not prove the spelling incorrect.
