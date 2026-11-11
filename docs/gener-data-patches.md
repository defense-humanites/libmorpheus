<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Generation data patches

The generation corpus is read from the pinned Alpheios stem sources
([gener-corpus.md](gener-corpus.md)). A few of their lines cannot be read as
written. `tools/gener-corpus-exceptions.tsv` records them as observations, and
the preparer skips them. When the intended reading is clear, a **data patch**
corrects the line instead. Patches are listed in
`tools/gener-corpus-patches.tsv` and documented here, and each one is offered
upstream.

## Mechanism

Each patch has four tab-separated fields:

- the source path, relative to the Greek stemlib root;
- the one-based line number;
- the SHA-256 of the trimmed source line;
- the line that replaces it.

The preparer (`--patches MANIFEST`) applies a patch only after it has checked
the path, the line number and the fingerprint. It fails on a fingerprint
mismatch, on a patch that matches no line, and on a manifest out of source
order. A patch supersedes an exception recorded at the same place, which must
carry the same fingerprint. The exception stays in its manifest, because it
describes the upstream source; the patch decides how this project reads it.

Patches change what the generation index contains, and only that:

- the analysis indices that Alpheios publishes (`steminds/`) are not
  rebuilt;
- the stem sources are not modified on disk;
- nothing from the sources is redistributed beyond the corrected lines that
  the manifest itself holds.

The data package embeds the same manifest (`internal/gener-manifest.js`,
checked byte for byte by `gener_corpus_manifest`) and applies it when it
prepares `gener.index`. `--requested-parts-only` runs without patches and
reproduces the historical index (`5aa76d8c…`).

## Current patches

All seven correct the `invalid_derivation` exceptions of the corpus
([gener-derivations.md](gener-derivations.md#invalid-source-records)). Wherever
it exists, the evidence is the reading that the Alpheios analysis index
(`steminds/vbind`) gives the same line: the historical analysis build parsed
some of these lines more leniently than the generation preparer does.

| Source | Original | Patched | Reason |
| --- | --- | --- | --- |
| `stemsrc/nom.proper:7941` (Ἀμμάτας) | `:de:*)ammat as_a masc stem_acc` | `:no:*)ammat as_a masc stem_acc` | `as_a` is a noun declension, not a derivation type. The same record is in `nom.proper:3864` as `:no:`. |
| `stemsrc/vbs.simp.ml:3928` (βεβόλημαι) | `:de:bol e_stem,epic` | `:de:bol e_stem epic` | The comma joins the key `epic` to the derivation type. |
| `stemsrc/vbs.simp.ml:6272` (δινεύω) | `:de:dein ew late` | `:de:dein ew_denom late` | `ew` names no derivation type. The lemma's other group is `:de:di_n ew_denom`, and `dein` is its late spelling. |
| `stemsrc/vbs.simp.ml:9214` (ἔχω) | `:de:e)x  reg_conj,syll_aug` | `:de:e)x reg_conj syll_aug` | The comma joins the key `syll_aug` to the derivation type. Analysis reads `e)x :e)/xw:w_stem:reg_conj:syll_augment`. |
| `stemsrc/vbs.simp.ml:15142` (μελιτόομαι) | `:de: melitt ow_denom` | `:de:melitt ow_denom` | The space after `:de:` empties the stem and shifts the tokens. |
| `stemsrc/vbs.simp.ml:22130` (στείνω) | `:de:sten w_stem mp` | `:vs:sten w_stem mp` | `w_stem` is a stem type, which belongs on a `:vs:` record, as in the neighbouring στένω block (`:vs:sten w_stem`). |
| `stemsrc/vbs.simp.ml:25428` (φράσσω) | `:de:farg numi,poetic` | `:de:farg numi poetic` | The comma joins the key `poetic` to the derivation type. Analysis reads `fargn :fra/ssw:umi_pr:numi:poetic`. |

The στείνω patch corrects the record kind and keeps the source's own content:
a middle-passive present on the stem `sten`, under στείνω. Whether that stem
belongs under στείνω rather than under στένω is a question for the upstream
report, not one the patch settles.

## Effect

Over the whole Alpheios index, the patches add 16 records, one lemma
(βεβόλημαι) and 3,365 generated forms. They change nothing else and add no
skipped record. The Ἀμμάτας block becomes identical to its correct twin and is
merged with it; its stem class still has no ending table, so its single record
stays a skipped record.

| Lemma | Forms before | After | Restored |
| --- | ---: | ---: | --- |
| ἔχω | 3,518 | 3,899 | the present system: ἔχω, εἶχον, ἔχεσκον… |
| μελιτόομαι | 1,715 | 3,355 | the `melitt-` spelling, beside `meli^t-` |
| δινεύω | 2,739 | 3,592 | the late `dein-` spelling |
| φράσσω | 2,310 | 2,610 | the poetic present φάργνυμι |
| στείνω | 252 | 367 | στένομαι, as the source records it |
| βεβόλημαι | — | 76 | the epic perfect, absent until now |

The corpus test now requires ἔχω to gain exactly its four present and
imperfect records against the historical, unpatched preparation.

## Upstream report

The Alpheios sources are licensed under CC BY-SA 3.0 US, which asks that
modifications be offered to Perseus. The text below is ready to file with the
Alpheios project (`alpheios-project/morpheus`) or to send to Perseus.

> **Seven unreadable `:de:` lines in the Greek stem sources**
>
> While preparing a generation index from `stemlib/Greek/stemsrc` (commit
> pinned by libmorpheus), seven derivation lines cannot be parsed as written.
> The analysis index reads some of them leniently, but the generation tools
> reject all seven:
>
> - `nom.proper:7941`: `:de:*)ammat as_a masc stem_acc` should be a `:no:` record,
>   like line 3864;
> - `vbs.simp.ml:3928`: `:de:bol e_stem,epic` → `:de:bol e_stem epic`;
> - `vbs.simp.ml:6272`: `:de:dein ew late` → `:de:dein ew_denom late`;
> - `vbs.simp.ml:9214`: `:de:e)x  reg_conj,syll_aug` → `:de:e)x reg_conj syll_aug`
>   (ἔχω's present stem);
> - `vbs.simp.ml:15142`: `:de: melitt ow_denom` → `:de:melitt ow_denom`;
> - `vbs.simp.ml:22130`: `:de:sten w_stem mp` → `:vs:sten w_stem mp`, unless the
>   stem was meant for στένω;
> - `vbs.simp.ml:25428`: `:de:farg numi,poetic` → `:de:farg numi poetic`.
>
> libmorpheus applies these corrections when it prepares its generation index
> (`tools/gener-corpus-patches.tsv`, documented in
> `docs/gener-data-patches.md`) and will drop each one once the upstream
> source carries it.

Upstream status: not yet filed.

## Adding a patch

A patch corrects one line, keeps the source's content when the intent is not
certain, and comes with its reason and evidence in the table above. Adding one
takes these steps:

1. Add the line to `tools/gener-corpus-patches.tsv`, in source order.
2. Copy the manifest into `GENER_CORPUS_PATCHES` in
   `bindings/js/data/internal/gener-manifest.js`.
3. Update the corpus digests and counts in `test/gener-corpus.cmake` and the
   pinned index digest wherever the tree pins it.
4. Add the patch to the upstream report.

When the upstream source changes, the fingerprint check fails and the patch
has to be reviewed again. Drop it if the source now carries the correction.
