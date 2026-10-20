# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Metadata contract of the WebAssembly binding package, published as
# @libmorpheus/wasm on npm (package.json) and JSR (jsr.json) from the same
# directory. Unlike the native bindings, this package ships the compiled
# runtime (dist/), so it also declares which libmorpheus release and which
# Emscripten release produced it.

if(NOT DEFINED MORPHEUS_SOURCE_DIR)
  message(FATAL_ERROR "MORPHEUS_SOURCE_DIR is required")
endif()

set(binding_dir "${MORPHEUS_SOURCE_DIR}/bindings/js/wasm")

# --- Declared versions ------------------------------------------------------

set(version_path "${binding_dir}/internal/version.mjs")
file(READ "${version_path}" version_source)
string(REGEX MATCH
  "MORPHEUS_WASM_VERSION[ \t]*=[ \t]*\"([0-9]+\\.[0-9]+\\.[0-9]+)\""
  wasm_version_definition "${version_source}")
set(wasm_version "${CMAKE_MATCH_1}")
if(NOT wasm_version_definition)
  message(FATAL_ERROR "WebAssembly binding version is missing")
endif()
string(REGEX MATCH
  "MORPHEUS_NATIVE_VERSION[ \t]*=[ \t]*\"([0-9]+\\.[0-9]+\\.[0-9]+)\""
  native_version_definition "${version_source}")
set(native_version "${CMAKE_MATCH_1}")
if(NOT native_version_definition)
  message(FATAL_ERROR "WebAssembly binding native runtime version is missing")
endif()
string(REGEX MATCH
  "MORPHEUS_NATIVE_ABI_VERSION[ \t]*=[ \t]*([0-9]+)"
  native_abi_definition "${version_source}")
set(native_abi "${CMAKE_MATCH_1}")
if(NOT native_abi_definition)
  message(FATAL_ERROR "WebAssembly binding native ABI version is missing")
endif()
string(REGEX MATCH
  "MORPHEUS_EMSCRIPTEN_VERSION[ \t]*=[ \t]*\"([0-9]+\\.[0-9]+\\.[0-9]+)\""
  emscripten_version_definition "${version_source}")
set(emscripten_version "${CMAKE_MATCH_1}")
if(NOT emscripten_version_definition)
  message(FATAL_ERROR "WebAssembly binding Emscripten version is missing")
endif()

# The packaged module is built from this tree, so the declared runtime release
# and ABI must be the tree's own. The native bindings may lag behind main;
# this one cannot.
if(DEFINED MORPHEUS_PROJECT_VERSION AND
   NOT native_version STREQUAL MORPHEUS_PROJECT_VERSION)
  message(FATAL_ERROR
    "WebAssembly binding declares runtime ${native_version}; the tree is "
    "${MORPHEUS_PROJECT_VERSION}")
endif()
if(DEFINED MORPHEUS_ABI_VERSION AND NOT native_abi EQUAL MORPHEUS_ABI_VERSION)
  message(FATAL_ERROR
    "WebAssembly binding declares ABI ${native_abi}; the tree is "
    "${MORPHEUS_ABI_VERSION}")
endif()

# The qualified Emscripten release is the one the Node.js and Deno preparer
# modules are stamped with, the one the workflows pin, and, when dist/ has
# been staged, the one stamped into the packaged module.
file(READ "${MORPHEUS_SOURCE_DIR}/cmake/stamp-gener-preparer.cmake"
     preparer_stamp)
if(NOT preparer_stamp MATCHES "Emscripten ${emscripten_version} ")
  message(FATAL_ERROR
    "WebAssembly binding declares Emscripten ${emscripten_version}, which "
    "differs from the stamped preparer toolchain")
endif()
if(EXISTS "${binding_dir}/dist/morpheus.mjs")
  file(READ "${binding_dir}/dist/morpheus.mjs" packaged_module LIMIT 400)
  string(CONCAT expected_stamp
    "// SPDX-License-Identifier: AGPL-3.0-or-later AND MPL-2.0 AND MIT\n"
    "// libmorpheus ${native_version} WebAssembly module, ABI ${native_abi}. "
    "Generated with Emscripten ${emscripten_version} ")
  string(FIND "${packaged_module}" "${expected_stamp}" stamp_at)
  if(NOT stamp_at EQUAL 0)
    message(FATAL_ERROR
      "dist/morpheus.mjs is not stamped as libmorpheus ${native_version}, "
      "ABI ${native_abi}, Emscripten ${emscripten_version}")
  endif()
endif()
foreach(workflow IN ITEMS wasm.yml wasm-release.yml)
  file(READ "${MORPHEUS_SOURCE_DIR}/.github/workflows/${workflow}"
       workflow_contents)
  if(NOT workflow_contents MATCHES "emscripten/emsdk:${emscripten_version}")
    message(FATAL_ERROR
      "${workflow} does not pin emscripten/emsdk:${emscripten_version}")
  endif()
endforeach()

file(READ "${binding_dir}/index.mjs" facade)
string(FIND "${facade}" "const ABI_VERSION = MORPHEUS_NATIVE_ABI_VERSION;"
       facade_abi_at)
if(facade_abi_at EQUAL -1)
  message(FATAL_ERROR
    "WebAssembly facade does not consume its declared native ABI")
endif()
string(FIND "${facade}" "// @ts-self-types=\"./index.d.ts\"" self_types_at)
if(self_types_at EQUAL -1)
  message(FATAL_ERROR "WebAssembly facade lacks its @ts-self-types directive")
endif()

# --- package.json (npm) -----------------------------------------------------

set(npm_path "${binding_dir}/package.json")
file(READ "${npm_path}" npm_config)
foreach(field IN ITEMS name version license type types)
  string(JSON "npm_${field}" ERROR_VARIABLE json_error
         GET "${npm_config}" "${field}")
  if(json_error)
    message(FATAL_ERROR "Invalid ${field} in ${npm_path}: ${json_error}")
  endif()
endforeach()
if(NOT npm_name STREQUAL "@libmorpheus/wasm")
  message(FATAL_ERROR "Unexpected npm package name: ${npm_name}")
endif()
if(NOT npm_version STREQUAL wasm_version)
  message(FATAL_ERROR
    "npm version ${npm_version} differs from binding ${wasm_version}")
endif()
if(NOT npm_license STREQUAL "AGPL-3.0-or-later")
  message(FATAL_ERROR "Unexpected npm package license: ${npm_license}")
endif()
if(NOT npm_type STREQUAL "module" OR NOT npm_types STREQUAL "./index.d.ts")
  message(FATAL_ERROR "npm package must be an ES module typed by index.d.ts")
endif()
string(JSON npm_access ERROR_VARIABLE json_error
       GET "${npm_config}" publishConfig access)
if(json_error OR NOT npm_access STREQUAL "public")
  message(FATAL_ERROR "npm package must publish with public access")
endif()
string(JSON npm_private ERROR_VARIABLE json_error GET "${npm_config}" private)
if(NOT json_error)
  message(FATAL_ERROR "npm package must not be marked private")
endif()
string(JSON npm_default_import GET "${npm_config}" exports . import)
string(JSON npm_default_types GET "${npm_config}" exports . types)
string(JSON npm_module_export GET "${npm_config}" exports ./module)
string(JSON npm_wasm_export GET "${npm_config}" exports ./morpheus.wasm)
if(NOT npm_default_import STREQUAL "./index.mjs" OR
   NOT npm_default_types STREQUAL "./index.d.ts" OR
   NOT npm_module_export STREQUAL "./dist/morpheus.mjs" OR
   NOT npm_wasm_export STREQUAL "./dist/morpheus.wasm")
  message(FATAL_ERROR "Unexpected npm package exports")
endif()

# npm "files" lists directories as well as files; LICENSES/ holds exactly the
# two license texts the module needs.
set(expected_npm_files
    LICENSE LICENSES NOTICE README.md dist/morpheus.mjs dist/morpheus.wasm
    index.d.ts index.mjs internal/version.mjs)
string(JSON npm_files_count ERROR_VARIABLE json_error
       LENGTH "${npm_config}" files)
if(json_error)
  message(FATAL_ERROR "Invalid files in ${npm_path}: ${json_error}")
endif()
list(LENGTH expected_npm_files expected_count)
if(NOT npm_files_count EQUAL expected_count)
  message(FATAL_ERROR
    "npm files has ${npm_files_count} entries; expected ${expected_count}")
endif()
math(EXPR last_file "${npm_files_count} - 1")
foreach(index RANGE 0 ${last_file})
  string(JSON included GET "${npm_config}" files ${index})
  list(FIND expected_npm_files "${included}" expected_at)
  if(expected_at EQUAL -1)
    message(FATAL_ERROR "Unexpected npm package file: ${included}")
  endif()
  list(REMOVE_ITEM expected_npm_files "${included}")
endforeach()
if(expected_npm_files)
  message(FATAL_ERROR "Missing npm package files: ${expected_npm_files}")
endif()

# --- jsr.json (JSR) ---------------------------------------------------------

set(jsr_path "${binding_dir}/jsr.json")
file(READ "${jsr_path}" jsr_config)
foreach(field IN ITEMS name version license)
  string(JSON "jsr_${field}" ERROR_VARIABLE json_error
         GET "${jsr_config}" "${field}")
  if(json_error)
    message(FATAL_ERROR "Invalid ${field} in ${jsr_path}: ${json_error}")
  endif()
endforeach()
if(NOT jsr_name STREQUAL "@libmorpheus/wasm")
  message(FATAL_ERROR "Unexpected JSR package name: ${jsr_name}")
endif()
if(NOT jsr_version STREQUAL wasm_version)
  message(FATAL_ERROR
    "JSR version ${jsr_version} differs from binding ${wasm_version}")
endif()
if(NOT jsr_license STREQUAL "AGPL-3.0-or-later")
  message(FATAL_ERROR "Unexpected JSR package license: ${jsr_license}")
endif()
string(JSON jsr_default_export GET "${jsr_config}" exports .)
if(NOT jsr_default_export STREQUAL "./index.mjs")
  message(FATAL_ERROR "Unexpected JSR package exports: ${jsr_default_export}")
endif()

set(expected_jsr_files
    LICENSE LICENSES/EMSCRIPTEN.txt LICENSES/MPL-2.0.txt NOTICE README.md
    dist/morpheus.mjs dist/morpheus.wasm index.d.ts index.mjs
    internal/version.mjs)
string(JSON include_count ERROR_VARIABLE json_error
       LENGTH "${jsr_config}" publish include)
if(json_error)
  message(FATAL_ERROR "Invalid publish.include in ${jsr_path}: ${json_error}")
endif()
list(LENGTH expected_jsr_files expected_count)
if(NOT include_count EQUAL expected_count)
  message(FATAL_ERROR
    "JSR publish.include has ${include_count} entries; expected ${expected_count}")
endif()
math(EXPR last_include "${include_count} - 1")
foreach(index RANGE 0 ${last_include})
  string(JSON included GET "${jsr_config}" publish include ${index})
  list(FIND expected_jsr_files "${included}" expected_at)
  if(expected_at EQUAL -1)
    message(FATAL_ERROR "Unexpected JSR package file: ${included}")
  endif()
  list(REMOVE_ITEM expected_jsr_files "${included}")
endforeach()
if(expected_jsr_files)
  message(FATAL_ERROR "Missing JSR package files: ${expected_jsr_files}")
endif()

# --- Tracked sources ----------------------------------------------------------

# dist/ is produced by the release workflow and never tracked; every other
# packaged path must exist in the tree. The binding root is closed: a new
# file there is a packaging decision, so it must be added here deliberately.
foreach(required IN ITEMS
        LICENSE LICENSES/EMSCRIPTEN.txt LICENSES/MPL-2.0.txt NOTICE README.md
        index.d.ts index.mjs internal/version.mjs jsr.json jsr.json.license
        package.json package.json.license)
  if(NOT EXISTS "${binding_dir}/${required}")
    message(FATAL_ERROR "Missing WebAssembly package source: ${required}")
  endif()
endforeach()
file(GLOB binding_root_files
     LIST_DIRECTORIES false
     RELATIVE "${binding_dir}"
     "${binding_dir}/*")
set(expected_root_files
    LICENSE NOTICE README.md index.d.ts index.mjs jsr.json jsr.json.license
    package.json package.json.license)
foreach(root_file IN LISTS binding_root_files)
  list(FIND expected_root_files "${root_file}" expected_at)
  if(expected_at EQUAL -1)
    message(FATAL_ERROR
      "Unexpected file at WebAssembly binding root: ${root_file}")
  endif()
  list(REMOVE_ITEM expected_root_files "${root_file}")
endforeach()
if(expected_root_files)
  message(FATAL_ERROR
    "Missing WebAssembly binding root files: ${expected_root_files}")
endif()
file(GLOB licenses_files
     LIST_DIRECTORIES false
     RELATIVE "${binding_dir}/LICENSES"
     "${binding_dir}/LICENSES/*")
list(SORT licenses_files)
if(NOT licenses_files STREQUAL "EMSCRIPTEN.txt;MPL-2.0.txt")
  message(FATAL_ERROR
    "WebAssembly binding LICENSES/ must hold exactly EMSCRIPTEN.txt and "
    "MPL-2.0.txt: ${licenses_files}")
endif()
foreach(license_file IN ITEMS EMSCRIPTEN.txt MPL-2.0.txt)
  file(SHA256 "${binding_dir}/LICENSES/${license_file}" wasm_license_sha)
  file(SHA256 "${MORPHEUS_SOURCE_DIR}/bindings/js/node/LICENSES/${license_file}"
       node_license_sha)
  if(NOT wasm_license_sha STREQUAL node_license_sha)
    message(FATAL_ERROR
      "LICENSES/${license_file} differs between the WebAssembly and Node.js "
      "bindings")
  endif()
endforeach()

# --- No linguistic data -------------------------------------------------------

# The package carries the runtime, never a stemlib. Any file whose name
# matches a stemlib artifact anywhere under the binding (including an
# untracked dist/ or a stray test fixture) fails the contract, and so does a
# packaging list that mentions one.
file(GLOB_RECURSE binding_files
     LIST_DIRECTORIES false
     RELATIVE "${binding_dir}"
     "${binding_dir}/*")
list(FILTER binding_files EXCLUDE REGEX "^node_modules/")
set(stemlib_pattern
    "(^|/)(nomind|vbind|nendind|vbendind|derivind|lemlist|vbs\\.cmp\\.ml|gener\\.index|[^/]*\\.lindex|[^/]*\\.out|[^/]*\\.table)$")
foreach(binding_file IN LISTS binding_files)
  if(binding_file MATCHES "${stemlib_pattern}")
    message(FATAL_ERROR
      "WebAssembly binding tree contains a stemlib artifact: ${binding_file}")
  endif()
endforeach()
foreach(manifest IN ITEMS "${npm_config}" "${jsr_config}")
  if(manifest MATCHES "stemlib|steminds|endtables|rule_files|gener\\.index")
    message(FATAL_ERROR
      "WebAssembly package manifests must not reference linguistic data")
  endif()
endforeach()
