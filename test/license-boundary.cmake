# SPDX-License-Identifier: AGPL-3.0-or-later

if(NOT DEFINED MORPHEUS_SOURCE_DIR)
  message(FATAL_ERROR "MORPHEUS_SOURCE_DIR is required")
endif()

set(agpl_files
    .github/workflows/deno-release.yml
    .github/workflows/node-release.yml
    .github/workflows/npm-smoke.yml
    .github/workflows/platform.yml
    .github/workflows/pypi-smoke.yml
    .github/workflows/python-release.yml
    CHANGELOG.md
    CMakeLists.txt
    docs/release-node-0.1.0.md
    cmake/stamp-gener-preparer.cmake
    bindings/js/node/CMakeLists.txt
    bindings/js/node/NOTICE
    bindings/js/node/README.md
    bindings/js/node/addon.c
    bindings/js/node/bootstrap-npm.mjs
    bindings/js/node/data.d.ts
    bindings/js/node/data.js
    bindings/js/node/index.d.ts
    bindings/js/node/index.js
    bindings/js/node/internal/archive.js
    bindings/js/node/internal/data-internal.js
    bindings/js/node/internal/data-manifest.js
    bindings/js/node/internal/gener-index.js
    bindings/js/node/internal/gener-runtime.js
    bindings/js/node/internal/main-module.js
    bindings/js/node/internal/native-internal.js
    bindings/js/node/internal/native-manifest.js
    bindings/js/node/internal/version.js
    bindings/js/node/native.d.ts
    bindings/js/node/native.js
    bindings/js/node/setup.d.ts
    bindings/js/node/setup.js
    bindings/js/node/internal/setup-internal.js
    bindings/js/node/package-platform.mjs
    bindings/js/node/test/binding.test.js
    bindings/js/node/test/bootstrap-npm.test.js
    bindings/js/node/test/data.test.js
    bindings/js/node/test/gener.test.js
    bindings/js/node/test/main-module.test.js
    bindings/js/node/test/native.test.js
    bindings/js/node/test/setup.test.js
    bindings/python/NOTICE
    bindings/python/README.md
    bindings/python/pyproject.toml
    bindings/python/src/libmorpheus/__init__.py
    bindings/python/src/libmorpheus/_abi.py
    bindings/python/src/libmorpheus/_library.py
    bindings/python/src/libmorpheus/_types.py
    bindings/python/src/libmorpheus/_version.py
    bindings/python/test/fixture.c
    bindings/python/test/runtime_smoke.py
    bindings/python/test/test_binding.py
    test/npm-published-smoke.mjs
    bindings/js/deno/NOTICE
    bindings/js/deno/README.md
    bindings/js/deno/data.ts
    bindings/js/deno/internal/data_internal.ts
    bindings/js/deno/internal/data_manifest.ts
    bindings/js/deno/test/data_test.ts
    bindings/js/deno/internal/gener_index_internal.ts
    bindings/js/deno/test/gener_preparer_test.ts
    bindings/js/deno/internal/gener_runtime_internal.ts
    bindings/js/deno/mod.ts
    bindings/js/deno/test/mod_test.ts
    bindings/js/deno/native.ts
    bindings/js/deno/internal/native_internal.ts
    bindings/js/deno/internal/native_manifest.ts
    bindings/js/deno/test/native_test.ts
    bindings/js/deno/setup.ts
    bindings/js/deno/internal/setup_internal.ts
    bindings/js/deno/test/setup_test.ts
    bindings/js/deno/internal/version.ts
    include/morpheus/morpheus.h
    src/api/gener_index.c
    src/api/gener_index.h
    src/api/api_internal.h
    src/api/analyze.c
    src/api/context.c
    src/api/generation.c
    src/api/result.c
    tools/prepare-runtime-data.sh
    tools/build-stemlib-distribution.cmake
    tools/build-stemlib-tables.cmake
    tools/stage-stemlib-sources.cmake
    tools/gener-index-builder.c)
file(GLOB agpl_support_files
     RELATIVE "${MORPHEUS_SOURCE_DIR}"
     "${MORPHEUS_SOURCE_DIR}/bench/*.sh"
     "${MORPHEUS_SOURCE_DIR}/bench/*.ts"
     "${MORPHEUS_SOURCE_DIR}/cmake/*.cmake"
     "${MORPHEUS_SOURCE_DIR}/cmake/*.in"
     "${MORPHEUS_SOURCE_DIR}/docs/*.md"
     "${MORPHEUS_SOURCE_DIR}/test/*.c"
     "${MORPHEUS_SOURCE_DIR}/test/*.cmake"
     "${MORPHEUS_SOURCE_DIR}/test/install-consumer/CMakeLists.txt"
     "${MORPHEUS_SOURCE_DIR}/test/install-consumer/*.c")
list(APPEND agpl_files ${agpl_support_files})
list(REMOVE_DUPLICATES agpl_files)

foreach(agpl_file IN LISTS agpl_files)
  file(READ "${MORPHEUS_SOURCE_DIR}/${agpl_file}" contents)
  string(FIND "${contents}"
         "SPDX-License-Identifier: AGPL-3.0-or-later" spdx_at)
  if(spdx_at EQUAL -1)
    message(FATAL_ERROR "AGPL SPDX identifier missing from ${agpl_file}")
  endif()
endforeach()

foreach(mpl_file IN ITEMS
        bindings/js/node/internal/gener-manifest.js
        bindings/js/node/internal/gener-preparer.mjs
        bindings/js/deno/internal/gener_manifest.ts
        bindings/js/deno/internal/gener_preparer.mjs
        include/morpheus/compat.h
        src/anal/anal_internal.h
        src/anal/cruncher_internal.h
        src/bridge/legacy_values.c
        src/bridge/legacy_values.h
        src/bridge/generation_normalizer.c
        src/bridge/generation_normalizer.h
        src/compat/compat.c
        src/gener/derivation.c
        src/gener/derivation.h
        src/gener/gener_internal.h
        src/gener/generation_service.c
        src/gener/generation_service.h
        src/gener/genwd.proto.h
        src/gkends/expendmain.c
        src/gkends/expendtable.c
        src/gkends/expsuffmain.c
        src/gkends/expwordmain.c
        src/gkdict/compnoun.proto.h
        src/gkdict/gkdict_internal.h
        src/gkdict/indexnoms.main.c
        src/gkdict/indexstems.c
        src/gkdict/indexstems.proto.h
        src/gkdict/indexvbs.main.c
        src/gkends/gkends_internal.h
        src/gkends/imain.c
        src/gkends/indexendtables.c
        src/gkends/indexendtables.proto.h
        src/gkends/indexendtables.x.proto.h
        src/gkends/mkend.c
        src/gkends/smain.c
        src/greeklib/greeklib_internal.h
        src/greeklib/standalpha.proto.h
        src/morphlib/morphlib_internal.h
        src/morphlib/indkeys.c
        src/morphlib/indkeys.proto.h
        src/morphlib/runtime_context.h
        src/morphlib/runtime_context_internal.h
        src/morphlib/setlang.proto.h
        test/gener-fixture.tsv
        test/gener-derivation-source.txt
        test/gener-derivation-invalid.txt
        test/gener-index-source.txt
        test/gener-index-unexpanded.txt
        test/generation-service-invalid-source.txt
        test/generation-service-source.txt
        test/gener-source-continuations.txt
        test/gener-source-orphan-continuation.txt
        test/stemlib-binary-baseline-exceptions.tsv
        test/stemlib-lexical-baseline-exceptions.tsv
        tools/stemlib-lexical-corrections.tsv
        tools/gener-source-preparer.c
        tools/gener-corpus-manifest.tsv
        tools/gener-corpus-exceptions.tsv
        tools/gener-derivation-manifest.tsv
        tools/stemlib-source-manifest.tsv)
  file(READ "${MORPHEUS_SOURCE_DIR}/${mpl_file}" contents)
  string(FIND "${contents}" "SPDX-License-Identifier: MPL-2.0" spdx_at)
  if(spdx_at EQUAL -1)
    message(FATAL_ERROR "MPL SPDX identifier missing from ${mpl_file}")
  endif()
endforeach()

file(READ "${MORPHEUS_SOURCE_DIR}/CMakePresets.json.license"
     presets_license)
string(FIND "${presets_license}"
       "SPDX-License-Identifier: AGPL-3.0-or-later" presets_spdx_at)
if(presets_spdx_at EQUAL -1)
  message(FATAL_ERROR
          "AGPL SPDX sidecar missing for CMakePresets.json")
endif()

file(READ "${MORPHEUS_SOURCE_DIR}/bindings/js/deno/jsr.json.license"
     jsr_license)
string(FIND "${jsr_license}"
       "SPDX-License-Identifier: AGPL-3.0-or-later" jsr_spdx_at)
if(jsr_spdx_at EQUAL -1)
  message(FATAL_ERROR
          "AGPL SPDX sidecar missing for bindings/js/deno/jsr.json")
endif()

file(READ "${MORPHEUS_SOURCE_DIR}/bindings/js/node/package.json.license"
     node_package_license)
string(FIND "${node_package_license}"
       "SPDX-License-Identifier: AGPL-3.0-or-later" node_package_spdx_at)
if(node_package_spdx_at EQUAL -1)
  message(FATAL_ERROR
          "AGPL SPDX sidecar missing for bindings/js/node/package.json")
endif()

foreach(platform IN ITEMS
    darwin-arm64 linux-arm64-gnu linux-x64-gnu)
  file(READ
    "${MORPHEUS_SOURCE_DIR}/bindings/js/node/npm/${platform}/package.json.license"
    platform_package_license)
  string(FIND "${platform_package_license}"
    "SPDX-License-Identifier: AGPL-3.0-or-later" platform_package_spdx_at)
  if(platform_package_spdx_at EQUAL -1)
    message(FATAL_ERROR
      "AGPL SPDX sidecar missing for Node platform ${platform}")
  endif()
endforeach()

foreach(license_file IN ITEMS
        LICENSE-AGPL-3.0-or-later
        LICENSES/MPL-2.0.txt
        LICENSES/AGPL-3.0-or-later.txt
        docs/licensing.md
        docs/license-inventory.md)
  if(NOT EXISTS "${MORPHEUS_SOURCE_DIR}/${license_file}")
    message(FATAL_ERROR "licensing artifact missing: ${license_file}")
  endif()
endforeach()

file(READ "${MORPHEUS_SOURCE_DIR}/LICENSE-AGPL-3.0-or-later"
     root_agpl_license)
file(READ "${MORPHEUS_SOURCE_DIR}/LICENSES/AGPL-3.0-or-later.txt"
     canonical_agpl_license)
if(NOT root_agpl_license STREQUAL canonical_agpl_license)
  message(FATAL_ERROR
          "root AGPL discovery copy differs from canonical license text")
endif()
