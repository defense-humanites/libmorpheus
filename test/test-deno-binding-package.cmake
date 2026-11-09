# SPDX-License-Identifier: AGPL-3.0-or-later

if(NOT DEFINED MORPHEUS_SOURCE_DIR OR
   NOT DEFINED MORPHEUS_BUILD_DIR OR
   NOT DEFINED MORPHEUS_PACKAGE_DIR)
  message(FATAL_ERROR
    "MORPHEUS_SOURCE_DIR, MORPHEUS_BUILD_DIR, and MORPHEUS_PACKAGE_DIR are required")
endif()

file(READ "${MORPHEUS_SOURCE_DIR}/bindings/js/deno/jsr.json" source_jsr_config)
string(JSON expected_deno_version GET "${source_jsr_config}" version)
set(package_basename "libmorpheus-deno-${expected_deno_version}")
set(archive "${MORPHEUS_PACKAGE_DIR}/${package_basename}.tar.gz")
set(checksum "${archive}.sha256")
foreach(required IN ITEMS "${archive}" "${checksum}")
  if(NOT EXISTS "${required}")
    message(FATAL_ERROR "Deno binding package is missing: ${required}")
  endif()
endforeach()

file(SHA256 "${archive}" actual_checksum)
file(READ "${checksum}" recorded_checksum)
string(FIND "${recorded_checksum}" "${actual_checksum}" checksum_at)
if(checksum_at EQUAL -1)
  message(FATAL_ERROR "Deno binding package checksum does not match")
endif()

set(extract_root "${MORPHEUS_BUILD_DIR}/deno-binding-package-test")
file(REMOVE_RECURSE "${extract_root}")
file(MAKE_DIRECTORY "${extract_root}")
execute_process(
  COMMAND "${CMAKE_COMMAND}" -E tar xzf "${archive}"
  WORKING_DIRECTORY "${extract_root}"
  RESULT_VARIABLE extract_result
  OUTPUT_VARIABLE extract_output
  ERROR_VARIABLE extract_error
)
if(NOT extract_result EQUAL 0)
  message(FATAL_ERROR
    "could not extract Deno binding package:\n${extract_output}\n${extract_error}")
endif()

set(binding_dir "${extract_root}/${package_basename}")
foreach(required IN ITEMS
        mod.ts data.ts native.ts setup.ts
        internal/data_internal.ts internal/data_manifest.ts
        internal/gener_index_internal.ts internal/gener_manifest.ts
        internal/gener_preparer.mjs internal/gener_runtime_internal.ts
        internal/native_internal.ts internal/native_manifest.ts
        internal/setup_internal.ts internal/version.ts
        LICENSES/EMSCRIPTEN.txt LICENSES/MPL-2.0.txt
        README.md LICENSE NOTICE jsr.json)
  if(NOT EXISTS "${binding_dir}/${required}")
    message(FATAL_ERROR "Deno binding package is missing ${required}")
  endif()
endforeach()

file(READ "${binding_dir}/jsr.json" jsr_config)
string(JSON jsr_name GET "${jsr_config}" name)
string(JSON jsr_version GET "${jsr_config}" version)
string(JSON jsr_export GET "${jsr_config}" exports .)
string(JSON jsr_data_export GET "${jsr_config}" exports ./data)
string(JSON jsr_native_export GET "${jsr_config}" exports ./native)
string(JSON jsr_setup_export GET "${jsr_config}" exports ./setup)
if(NOT jsr_name STREQUAL "@libmorpheus/deno")
  message(FATAL_ERROR "Packaged Deno binding has unexpected JSR name: ${jsr_name}")
endif()
string(JSON jsr_license GET "${jsr_config}" license)
if(NOT jsr_license STREQUAL "AGPL-3.0-or-later")
  message(FATAL_ERROR
    "Packaged Deno binding has unexpected primary license: ${jsr_license}")
endif()
if(NOT jsr_version STREQUAL "${expected_deno_version}")
  message(FATAL_ERROR
    "Packaged Deno binding JSR version ${jsr_version} differs from ${expected_deno_version}")
endif()
file(READ "${binding_dir}/internal/version.ts" version_source)
string(REGEX MATCH
  "MORPHEUS_DENO_VERSION[ \t]*=[ \t]*\"([0-9]+\\.[0-9]+\\.[0-9]+)\""
  deno_version_definition "${version_source}")
if(NOT deno_version_definition OR
   NOT "${CMAKE_MATCH_1}" STREQUAL "${expected_deno_version}")
  message(FATAL_ERROR
    "Packaged Deno version declaration differs from ${expected_deno_version}")
endif()
if(NOT jsr_export STREQUAL "./mod.ts")
  message(FATAL_ERROR "Packaged Deno binding has unexpected JSR export: ${jsr_export}")
endif()
if(NOT jsr_data_export STREQUAL "./data.ts")
  message(FATAL_ERROR
    "Packaged Deno binding has unexpected JSR data export: ${jsr_data_export}")
endif()
if(NOT jsr_setup_export STREQUAL "./setup.ts")
  message(FATAL_ERROR
    "Packaged Deno binding has unexpected JSR setup export: ${jsr_setup_export}")
endif()
if(NOT jsr_native_export STREQUAL "./native.ts")
  message(FATAL_ERROR
    "Packaged Deno binding has unexpected JSR native export: ${jsr_native_export}")
endif()

file(READ "${binding_dir}/LICENSE" binding_license)
string(FIND "${binding_license}" "GNU AFFERO GENERAL PUBLIC LICENSE" agpl_title_at)
if(agpl_title_at EQUAL -1)
  message(FATAL_ERROR "Deno binding package does not contain the AGPL license")
endif()

file(READ "${binding_dir}/mod.ts" binding_source)
string(FIND "${binding_source}"
  "SPDX-License-Identifier: AGPL-3.0-or-later" agpl_spdx_at)
if(agpl_spdx_at EQUAL -1)
  message(FATAL_ERROR "Packaged Deno source is missing its AGPL SPDX identifier")
endif()

file(READ "${binding_dir}/data.ts" data_source)
string(FIND "${data_source}"
  "SPDX-License-Identifier: AGPL-3.0-or-later" data_spdx_at)
if(data_spdx_at EQUAL -1)
  message(FATAL_ERROR "Packaged Deno data CLI is missing its AGPL SPDX identifier")
endif()
string(FIND "${binding_source}" "@experimental" experimental_api_at)
if(experimental_api_at EQUAL -1)
  message(FATAL_ERROR "Packaged Deno generation API is not experimental")
endif()

file(READ "${binding_dir}/NOTICE" binding_notice)
string(FIND "${binding_notice}" "AGPL-3.0-or-later" agpl_notice_at)
if(agpl_notice_at EQUAL -1)
  message(FATAL_ERROR "Deno binding package notice does not identify its license")
endif()
string(FIND "${binding_notice}" "MPL-2.0" mpl_notice_at)
if(mpl_notice_at EQUAL -1)
  message(FATAL_ERROR "Deno binding package notice omits the native MPL boundary")
endif()
foreach(reference IN ITEMS docs/licensing.md docs/provenance.md)
  string(FIND "${binding_notice}" "${reference}" reference_at)
  if(reference_at EQUAL -1)
    message(FATAL_ERROR
      "Deno binding package notice omits the ${reference} reference")
  endif()
endforeach()

file(READ "${binding_dir}/README.md" binding_readme)
string(FIND "${binding_readme}"
  "[archive notice](NOTICE)"
  notice_link_at)
if(notice_link_at EQUAL -1)
  message(FATAL_ERROR "Packaged Deno README does not link to its notice")
endif()
foreach(required_text IN ITEMS
    "This package is no longer maintained"
    "Standalone release archive"
    "Native library and runtime data"
    "@libmorpheus/deno/setup"
    "--dataset perseids"
    "Acquire stem data"
    "Acquire the native library"
    "@libmorpheus/deno/native"
    "tools/prepare-runtime-data.sh"
    "@libmorpheus/deno"
    "Language and data coverage"
    "MorpheusOption.StrictCase"
    "https://github.com/defense-humanites/libmorpheus"
    "`generate()` and `generateRaw()` are experimental"
    "generate()"
    "--allow-ffi app.ts"
    "## License")
  string(FIND "${binding_readme}" "${required_text}" required_text_at)
  if(required_text_at EQUAL -1)
    message(FATAL_ERROR
      "Packaged Deno README omits required text: ${required_text}")
  endif()
endforeach()
string(FIND "${binding_readme}" "../../docs/licensing.md" broken_link_at)
if(NOT broken_link_at EQUAL -1)
  message(FATAL_ERROR "Packaged Deno README contains an out-of-archive link")
endif()

find_program(deno_program deno REQUIRED)
execute_process(
  COMMAND "${deno_program}" check mod.ts data.ts native.ts setup.ts
  WORKING_DIRECTORY "${binding_dir}"
  RESULT_VARIABLE check_result
  OUTPUT_VARIABLE check_output
  ERROR_VARIABLE check_error
)
if(NOT check_result EQUAL 0)
  message(FATAL_ERROR
    "packaged Deno binding does not type-check:\n${check_output}\n${check_error}")
endif()
