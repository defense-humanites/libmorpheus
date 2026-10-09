<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Future and imperative quotation evidence for present radicals

This separate opt-in tier follows the [citation-supported present trial](latin-cited-present-qualification.md). It uses the same complete alternate, source class-three grammar, active voice, conjugation-subclass and unique unflagged canonical radical checks. Its quotation evidence is restricted to six active future indicative endings and two active present imperative endings. The default evidence tier remains unchanged. Each tier only appends an orthographic present-system radical; neither adds perfect or participial parts.

Four records under four source lemmas are added; two eligible alternates are already present. Whole-word matching uses Latin quotations within the same pinned article. Source quantities and internal delimiters are preserved individually. Actual words, articles, quotations and per-entry checks remain private. The source revision remains `56061ca127f4a2844980baffc5f2b6d1332897b3`.

The letter-oriented candidate SHA-256 is `3115fbe2580b39ed27fd705fc19fc5e82e76e627affdef5e01b7d87e78ce96f9`; the all-quantity candidate is `c1c1497cb233b75e89607bf48c0ee303cd596bd3764a51b88516537762c9a775`. The letter-oriented verbal index is `ed24bc5d45456fec60fbc0ab9c8ab9a919506e7476295543666defc569226fd1`, with sidecar `7309e63a8210661f168421cb4e295dbd2d6cb7f220d01e5cb8e65ef8b4635aa0`. Nominal indexes are unchanged.

Both quantity treatments build identical verbal indexes and sidecars. The historical filters independently reproduce all four added present stem/tag pairs using each isolated alternate header's original source grammar. The previous default evidence trial remains byte-identical.

An independent 52-form trial checks six present indicative, six present subjunctive and one present infinitive per radical. Expected source-lemma present readings increase from zero to 66 across all 52 forms. All 34 previous eleven-field rows are retained, 66 are added, and none are removed. Before/after private dossier SHA-256 values are `99e5ff3c1e6d34f46d92c20f92608eb9a162c1f605d65b712c01ffcffa88e109` and `290789e53c556cae997f1db1cf541cd8c427abf94a20009b51f224a2ee673cf4`.

A separate probe checks the four exact lowercased quotation forms. Before the trial, none has its source lemma with the expected mood and tense. Afterward all four do: three present imperatives and one future indicative. Quotation evidence is thus checked against generated grammar independently of the 52-form present trial.

An extended independent probe checks all 32 active future/imperative forms under the four source lemmas. Expected grammar increases from zero to 32 forms and 32 matching readings. All 18 previous eleven-field rows are retained, 36 are added, and none are removed. Before/after private dossier hashes are `9792dd002b5041a845d2bf40ca16c88d7576255e28e5cee34cedd51d0889b90f` and `76d90d99d8c2dcfdf5971be49973fd56120ce0c4713bf7ceaa31c433c170afe1`. The four additional rows outside the expected future/imperative subset are retained in the dossier, rather than counted as expected grammar.

The synthetic suite now includes six tests for this tool. The added test verifies that future/imperative citations select only their explicit tier, including class-three `io` endings, while an imperfect citation is withheld. CI applies both tiers sequentially in both quantity treatments with expected counts eleven and four. Full LISTALL comparisons are qualified separately before any promotion; the production corpus remains unchanged.

Removing only the four added alternates leaves 31 variants in 31 articles. The inventory SHA-256 is `bbc3221bd6af842e1523f1ddd4f4a07e4b3ef987e3ff59d37fc6bc52e88c6e1d`. A separate source review records article hashes and Latin quotation counts: six alternates do not retain the headword's compound prefix, and 25 need a different source criterion. These are review categories, not automatic rejection of those spellings. This private review's SHA-256 is `e9ebed7bb661d01a975c07cb9c451488a6b1a8b5d8838b2c5543e09e7d143a48`.

All 31 remaining alternate headers reproduce their expected present stem/tag pair through the historical filters when isolated with the original source grammar. This mechanical result does not resolve the absent quotation or compound-prefix evidence and does not authorize promotion. The separate private filter-review SHA-256 is `4b87fc374cbf47bec5f5dff8efc043ec319d892d5000cf6789cd8fcd3fc763f5`.

## Full LISTALL qualification

Three complete passes cover all 1,033,579 literal forms with options zero and ABI two, with zero errors. The identical-root control has zero changed counts. Relative to the preceding citation trial, 309 forms become recognized, none becomes absent, and all 1,339 changed counts increase. The final trial recognizes 844,546 forms and returns 2,100,496 readings, adding 2,020 readings.

An eleven-field multiset comparison on all changed forms retains all 2,026 previous rows, adds 2,020, and removes none. Before/after private dossier hashes are `7e29e3c91567d4d2f189aadcef84c352e59abfe8ae6d70369b0d9ecc36f5cd95` and `5fdba671546ff5104f3d4997fbc8f3d71d5f497c423dbc57e0d3b13d60227da5`. A separate native-preverb provenance comparison classifies 620 added readings on 412 forms as direct source-lemma verbs and 1,400 added readings on 927 forms as native-prefix review leads. These two form sets do not overlap.

Restricting that provenance review to the 309 gained forms gives 206 direct-only gains with 308 readings and 103 prefix-only gains with 154 readings. No gained form has both provenances or another classification. The 103 native-prefix gains are not source-qualified compound paradigms; the same limitation applies to the other added native-prefix readings on previously recognized forms. The trial preserves native policy rather than treating count increases as linguistic proof.

The full compound article corresponding to all 103 prefix-only gains has no complete orthographic alternate supplying the contracted present spelling. Its explicit class-three parts and uncontracted quoted verbal forms do not establish the contracted present inherited from the base article. The private article SHA-256 is `175454372ce17fea6dcd0322e3f6c23c5dc49bed7ac7cda72a5b0fff0ce869df`. This remains a source-evidence blocker for qualifying those compound readings directly; neither a source lemma insertion nor a native policy change is made to resolve it by counts alone.

Baseline recognition cells are 826,523 recognized by both, 11,467 baseline-only, 18,023 trial-only and 177,566 recognized by neither. The ordered baseline-only list is unchanged. The original 15,255-loss subset remains at 4,238 recognized forms and 7,937 readings, and all 488 first-repair losses remain absent.

Across the two quotation evidence tiers, fifteen alternate present radicals add 309 recognized forms and 2,803 readings without a new absence. All six full comparisons have zero errors, and both identical controls have zero differences. All 61 synthetic tests in the eleven-stage repair/recovery pipeline pass. Linux CI, platform/release qualification and lexical research are green on code commit `be80d5f` (runs `36990411770`, `36990411781`, `36990406201`). The PR remains a draft, and the production corpus is unchanged.

The next separate source trial is documented in [bounded prefix-boundary present alternates](latin-boundary-present-qualification.md).
