// SPDX-License-Identifier: AGPL-3.0-or-later

const ALPHEIOS_REVISION = "4632415fe93c85e9fdca47a0c5a13f31385f0023";
const PERSEIDS_REVISION = "ab6898ffed335fc6169fa02c9940657a9b5a78e0";

export const MORPHEUS_DATASETS = {
  alpheios: {
    name: "alpheios",
    repository: "https://github.com/alpheios-project/morpheus",
    revision: ALPHEIOS_REVISION,
    archiveUrl: `https://codeload.github.com/alpheios-project/morpheus/tar.gz/${ALPHEIOS_REVISION}`,
    archiveRoot: `morpheus-${ALPHEIOS_REVISION}/`,
    dataPrefix: "dist/stemlib/",
    fileCount: 237,
    treeSha256: "ab3b52c50a0c970647a81cd2dce56317fd7502eab697caa58da4dd97cec743a0",
    licensePath: "LICENSE",
    licenseSha256: "f27c9386a3a6dcad6e733e951aadb7dd548fcdde7518de82f60ac6ed5da67951",
    languages: ["grc"],
    generation: true,
  },
  perseids: {
    name: "perseids",
    repository: "https://github.com/perseids-tools/morpheus",
    revision: PERSEIDS_REVISION,
    archiveUrl: `https://codeload.github.com/perseids-tools/morpheus/tar.gz/${PERSEIDS_REVISION}`,
    archiveRoot: `morpheus-${PERSEIDS_REVISION}/`,
    dataPrefix: "stemlib/",
    fileCount: 1083,
    treeSha256: "b1ee71e27f00f6f69ec3c162bfb504b5165264d4de5515842e546242d597e7d2",
    licensePath: "LICENSE",
    licenseSha256: "1f256ecad192880510e84ad60474eab7589218784b9a50bc7ceee34c2b91f1d5",
    languages: ["grc", "lat"],
    generation: false,
  },
};

export const MORPHEUS_DATA_SCHEMA_VERSION = 1;
