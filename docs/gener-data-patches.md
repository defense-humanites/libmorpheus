<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Generation data patches

The generation corpus is read from the pinned Alpheios stem sources
([gener-corpus.md](gener-corpus.md)). A few of their lines cannot be read as
written. `tools/gener-corpus-exceptions.tsv` records them as observations, and
the preparer skips them. When the intended reading is clear, or can be argued
from the neighbouring records, a **data patch** corrects the line instead.
Patches are listed in `tools/gener-corpus-patches.tsv` and documented here,
with the evidence for each and how firm it is.

## Mechanism

Each patch has four tab-separated fields:

- the source path, relative to the Greek stemlib root;
- the one-based line number;
- the SHA-256 of the trimmed source line;
- the line that replaces it.

The preparer (`--patches MANIFEST`) applies a patch only after it has checked
the path, the line number and the fingerprint. It fails on a fingerprint
mismatch and on a patch that matches no line. While it loads the manifest, it
also rejects a patch out of source order (by path in byte order, then by
line), a second patch for the same line, and a replacement that is empty or
starts or ends with whitespace. A patch supersedes an exception recorded at the same place, which
must carry the same fingerprint. The exception stays in its manifest, because
it describes the upstream source; the patch decides how this project reads it.

The preparer's options (`--exceptions`, `--patches`, `--requested-parts-only`)
may come in any order, each at most once. `--requested-parts-only` reproduces
the historical preparation, which read the sources unpatched, so the preparer
refuses to combine it with `--patches`.

Patches change what the generation index contains, and only that:

- the analysis indices that Alpheios publishes (`steminds/`) are not
  rebuilt;
- the stem sources are not modified on disk;
- nothing from the sources is redistributed beyond the corrected lines that
  the manifest itself holds.

The data package embeds the same manifest (`internal/gener-manifest.js`,
checked byte for byte by `gener_corpus_manifest`) and applies it when it
prepares `gener.index`. `--requested-parts-only`, without patches, reproduces
the historical index (`5aa76d8c…`).

## Current patches

All seven correct the `invalid_derivation` exceptions of the corpus
([gener-derivations.md](gener-derivations.md#invalid-source-records)). The
evidence is first the reading that the Alpheios analysis index
(`steminds/vbind`) gives the same stem: the historical analysis build parsed
some of these lines more leniently than the generation preparer does. A patch
is **confirmed** when that index, or an identical record elsewhere in the
sources, gives the patched reading. It is **conjectural** when the analysis
index does not know the stem under that lemma, so that only the neighbouring
records support the reading; the forms such a patch adds do not analyze back to
their lemma.

| Source | Original | Patched | Status | Reason and evidence |
| --- | --- | --- | --- | --- |
| `stemsrc/nom.proper:7941` (Ἀμμάτας) | `:de:*)ammat as_a masc stem_acc` | `:no:*)ammat as_a masc stem_acc` | Confirmed | `as_a` is a noun declension, not a derivation type. The same record is in `nom.proper:3864` as `:no:`. |
| `stemsrc/vbs.simp.ml:3928` (βεβόλημαι) | `:de:bol e_stem,epic` | `:de:bol e_stem epic` | Confirmed | The comma joins the key `epic` to the derivation type. Analysis reads `bebolh :bebo/lhmai:perfp_vow:e_stem:epic`. |
| `stemsrc/vbs.simp.ml:6272` (δινεύω) | `:de:dein ew late` | `:de:dein ew_denom late` | Conjectural | `ew` names no derivation type. The line closes the lemma's `:de:di_n ew_denom` group (δινέω), whose type is the only one that `ew` begins. The analysis index knows no `dein` stem for δινεύω. |
| `stemsrc/vbs.simp.ml:9214` (ἔχω) | `:de:e)x  reg_conj,syll_aug` | `:de:e)x reg_conj syll_aug` | Confirmed | The comma joins the key `syll_aug` to the derivation type. Analysis reads `e)x :e)/xw:w_stem:reg_conj:syll_augment`. |
| `stemsrc/vbs.simp.ml:15142` (μελιτόομαι) | `:de: melitt ow_denom` | `:de:melitt ow_denom` | Conjectural | The space after `:de:` empties the stem and shifts the tokens. The analysis index knows only `melit :melito/omai:ow_pr:ow_denom`. |
| `stemsrc/vbs.simp.ml:22130` (στείνω) | `:de:sten w_stem mp` | `:vs:sten w_stem mp` | Conjectural | `w_stem` is a stem type, which belongs on a `:vs:` record, as in the neighbouring στένω block (`:vs:sten w_stem`). The analysis index gives `sten` to στένω (`sten :ste/nw:w_stem`), not to στείνω. |
| `stemsrc/vbs.simp.ml:25428` (φράσσω) | `:de:farg numi,poetic` | `:de:farg numi poetic` | Confirmed | The comma joins the key `poetic` to the derivation type. Analysis reads `fargn :fra/ssw:umi_pr:numi:poetic`. |

The three conjectural patches keep the source's own content and make the
smallest edit that lets the preparer read the line:

- **δινεύω.** The block has two groups, `:de:di_n euw` (δινεύω) and
  `:de:di_n ew_denom` (δινέω, the variant that LSJ gives under δινεύω). The
  broken line follows the second group, and `ew` is a prefix of `ew_denom`,
  not of `euw`; the patch therefore reads it as a late spelling of δινέω,
  not of δινεύω. Neither δεινέω nor δεινεύω is in LSJ. The patch adds 853
  forms.
- **μελιτόομαι.** Removing the stray space is the only edit that makes the
  line parse. The source records `melitt-` beside `meli^t-`, but the analysis
  index has only the latter.
- **στείνω.** The patch corrects the record kind: a middle-passive present on
  the stem `sten`, under στείνω, as the source has it. Whether that stem
  belongs under στείνω rather than under στένω is not a question the patch
  settles.

Each of the three is reviewed again if Alpheios corrects the line, or as soon
as better evidence turns up.

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

The Alpheios sources are licensed under CC BY-SA 3.0 US, and their licence
adds: "You must offer Perseus any modifications you make." This project reads
that as making the modifications available: the manifest, which holds every
corrected line, and this document, which gives the reasons, are public in the
libmorpheus repository. Telling the Alpheios project or Perseus about them is
welcome but not required. The text below is ready for that, as an issue on
`alpheios-project/morpheus` or a message to Perseus.

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
> - `vbs.simp.ml:6272`: `:de:dein ew late` → `:de:dein ew_denom late`, unless
>   `dein` was meant as a spelling of δινεύω (`euw`) rather than of δινέω;
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

Upstream status: available in this repository; not reported to Alpheios or
Perseus.

## Adding a patch

A patch corrects one line, keeps the source's content when the intent is not
certain, and comes with its status, reason and evidence in the table above.
Adding one takes these steps:

1. Add the line to `tools/gener-corpus-patches.tsv`, in source order; the
   preparer rejects a manifest out of order.
2. Copy the manifest into `GENER_CORPUS_PATCHES` in
   `bindings/js/data/internal/gener-manifest.js`.
3. Update the corpus digests and counts in `test/gener-corpus.cmake` and the
   pinned index digest wherever the tree pins it.
4. Add the patch to the upstream report.

When the upstream source changes, the fingerprint check fails and the patch
has to be reviewed again. Drop it if the source now carries the correction.
