<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

# Stemlib redistribution gate

The reconstructed Greek and Latin runtime archives are qualified as software
artifacts, but they are not qualified for redistribution. Reproducibility,
linguistic correctness, and a known source revision do not establish that the
data may be republished by `libmorpheus`.

`tools/stemlib-redistribution-policy.json` is the machine-readable publication
contract. Its current state is `review-required`; both datasets are
`not-qualified`, and every publication channel is closed. CI verifies the
contract, the selected Git trees, the recorded notices, and the absence of a
stemlib payload from release workflows.

## Evidence inventory

| Dataset | Content identity | Evidence | Finding |
| --- | --- | --- | --- |
| Bundled Perseids Greek and Latin data | imported revision `ab6898ffed335fc6169fa02c9940657a9b5a78e0`; current `stemlib/` tree `5dcaeb87f8d65f6ee0cde88abfc860b82faab046` | Repository-level MPL-2.0 text in `LICENSE`; no data-specific notice found under `stemlib/` | The repository notice is evidence, but it does not independently resolve the rights in every linguistic datum. |
| Pinned Alpheios Greek data | revision `4632415fe93c85e9fdca47a0c5a13f31385f0023`; selected tree `ccbe43e3f99b827bf8ea1fe9eec102edd49d6c93` | Root `LICENSE` and `dist/bin/platform/license.txt` at the pinned revision | The root file reports a repository-wide CC BY-SA default while the older platform notice identifies Morpheus source code as MPL-1.1; neither notice specifically resolves the stem data. |

The hashes of those evidence files are part of the policy. A changed upstream
revision, selected tree, or notice therefore fails CI until this record and the
policy are reviewed together. This is an evidence inventory, not legal advice
or a license determination.

## Preliminary rights and notice review (2026-09-25)

The publication decision has three corpus-specific subjects, although the
current policy groups the two Perseids languages under one repository entry.
The counts below describe the pinned Git trees, not a final selection of files
for any future reconstructed archive.

| Corpus | Files and provenance signals | Outstanding rights question |
| --- | --- | --- |
| Perseids Greek (`stemlib/Greek/`) | 711 files, including lexical sources (`lsj.nom`, `lsj.vbs`, `nom.smith.bio`, `nom.smith.geo`), rules, tables, and indexes. | Who can authorize redistribution of the historical LSJ and Smith-derived entries, later editorial contributions, and the resulting compiled data? |
| Perseids Latin (`stemlib/Latin/`) | 372 files, including `ls.nom`, `vbs.latin`, `nom.smithbio.latin`, `nom.smithgeo`, rules, and indexes. The Smith files identify their stems as derived from Smith's encyclopedias. | Which rights and notices apply to the historical Lewis & Short and Smith-derived entries, later edits, and compiled data? |
| Alpheios Greek (`dist/stemlib/Greek/`) | 237 files at the pinned revision, including 84 under `stemsrc/`, 138 ending-table files, 10 rule files, and five indexes. The distribution tree includes LSJ and Smith-related lexical sources. | Which Perseus and Alpheios contributors can authorize the selected data and its later edits, including generated indexes and any separately prepared `gener.index`? |

The repository-level notices do not answer these questions on their own:

- [PerseusDL/morpheus](https://github.com/PerseusDL/morpheus/blob/master/README.md)
  states a CC BY-SA 3.0 US default, says that its materials have varying
  copyright status, asks readers to contact the project about a specific
  component, and requests that modifications be offered to Perseus. The
  [Perseids repository](https://github.com/perseids-tools/morpheus/blob/ab6898ffed335fc6169fa02c9940657a9b5a78e0/LICENSE)
  carries an MPL-2.0 license file. Their relationship for each historical
  linguistic source and contribution remains to be established.
- The pinned [Alpheios root license](https://github.com/alpheios-project/morpheus/blob/4632415fe93c85e9fdca47a0c5a13f31385f0023/LICENSE)
  reports the Perseus repository's CC BY-SA default without itself assigning a
  license to Morpheus. Its older
  [platform notice](https://github.com/alpheios-project/morpheus/blob/4632415fe93c85e9fdca47a0c5a13f31385f0023/dist/bin/platform/license.txt)
  identifies *Morpheus source code* as MPL-1.1; it does not specifically
  license the stem data. Alpheios
  [issue #72](https://github.com/alpheios-project/morpheus/issues/72)
  records uncertainty about the licensing history.
- The separate [PerseusDL/lexica repository](https://github.com/PerseusDL/lexica)
  declares a CC BY-SA 4.0 default. Its
  [LSJ](https://github.com/PerseusDL/lexica/blob/master/CTS_XML_TEI/perseus/pdllex/grc/lsj/README.md)
  and [Lewis & Short](https://github.com/PerseusDL/lexica/blob/master/CTS_XML_TEI/perseus/pdllex/lat/ls/README.md)
  notices specify credit to Perseus and the NEH, preservation of the
  availability statement, and an offer of modifications to Perseus. Those
  editions do not establish the terms of the older, unavailable `lemmata`
  exports used to build Morpheus stems; see the
  [production audit](stemlib-production-audit.md).
- A targeted search found no data-specific copyright or license notice inside
  the bundled `stemlib/` files. A source comment identifying Smith-derived
  stems is provenance evidence, not a redistribution grant.

Before any channel is opened, obtain confirmation from Perseus/Tufts,
Alpheios, and Perseids about authority, applicable terms, and credits for each
corpus. Record the exact files in the proposed archive, the reconstruction and
editorial changes, the complete attribution and license notices, and access to
the relevant source inputs and build recipe where required. Review the
Perseus/Alpheios requests to offer modifications rather than silently omitting
them. Make a separate written decision for each of the three corpora; if a
corpus is approved, update the policy and validator deliberately so that its
publication channels can be named without implicitly approving the others.
This review does not change the current gate.

## Current boundary

The following remain allowed:

- local reconstruction and qualification;
- creation and extraction of internal runtime archives;
- publication of receipts and checksums that contain no linguistic payload;
- acquisition by users directly from a pinned upstream repository.

The following remain blocked:

- stemlib payloads in GitHub Release assets;
- stemlib payloads in native, Node.js, Python, or Deno packages;
- publication of the prepared data in container images;
- upload of runtime archives as retained CI artifacts.

## Opening the gate

Publication requires an explicit, reviewed decision for each corpus. That
review must identify the licensor or other authority, the license that applies
to the selected data files and generated forms, required attribution and
notices, modification-marking requirements, and the allowed publication
channels. It must also define the source offer or corresponding-source handling
where applicable.

Only after that record exists should a change replace `decision_record: null`,
move the affected dataset away from `not-qualified`, and open named publication
channels. The policy validator intentionally rejects such a change today;
changing the state machine is itself a separately reviewed implementation
step.
