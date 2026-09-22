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

Publication requires an explicit, reviewed decision for each dataset. That
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
