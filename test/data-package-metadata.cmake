# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Contract of the data acquisition package, bindings/js/data
# (@libmorpheus/data on npm): identity, entry points, closed file lists,
# the files it shares byte for byte with the Node.js binding, and the
# absence of any linguistic data from the package tree and its manifest.
# The package downloads datasets; it never carries one.

if(NOT DEFINED MORPHEUS_SOURCE_DIR)
  message(FATAL_ERROR "MORPHEUS_SOURCE_DIR is required")
endif()

set(data_dir "${MORPHEUS_SOURCE_DIR}/bindings/js/data")
set(node_dir "${MORPHEUS_SOURCE_DIR}/bindings/js/node")
set(expected_version "0.1.0")

# --- Identity -----------------------------------------------------------------

file(READ "${data_dir}/package.json" package)
foreach(field IN ITEMS name version license type description)
  string(JSON "data_${field}" ERROR_VARIABLE json_error GET "${package}" "${field}")
  if(json_error)
    message(FATAL_ERROR "Invalid data package ${field}: ${json_error}")
  endif()
endforeach()
if(NOT data_name STREQUAL "@libmorpheus/data" OR
   NOT data_version STREQUAL expected_version OR
   NOT data_license STREQUAL "AGPL-3.0-or-later" OR
   NOT data_type STREQUAL "module")
  message(FATAL_ERROR
    "Unexpected data package identity: ${data_name}@${data_version}, ${data_license}, ${data_type}")
endif()
if(NOT data_description MATCHES "Contains no linguistic data")
  message(FATAL_ERROR
    "The data package description must state that it contains no linguistic data")
endif()

file(READ "${data_dir}/internal/version.js" version_module)
string(FIND "${version_module}"
  "MORPHEUS_DATA_VERSION = \"${data_version}\"" version_at)
if(version_at EQUAL -1)
  message(FATAL_ERROR "Data version module differs from package.json")
endif()

foreach(forbidden_script IN ITEMS preinstall install postinstall)
  string(JSON ignored ERROR_VARIABLE script_error
    GET "${package}" scripts "${forbidden_script}")
  if(NOT script_error)
    message(FATAL_ERROR
      "Data package must not run ${forbidden_script} during npm installation")
  endif()
endforeach()
foreach(forbidden_field IN ITEMS dependencies optionalDependencies peerDependencies)
  string(JSON ignored ERROR_VARIABLE field_error GET "${package}" "${forbidden_field}")
  if(NOT field_error)
    message(FATAL_ERROR "Data package unexpectedly declares ${forbidden_field}")
  endif()
endforeach()

string(JSON repository_directory GET "${package}" repository directory)
if(NOT repository_directory STREQUAL "bindings/js/data")
  message(FATAL_ERROR "Data package repository directory: ${repository_directory}")
endif()
string(JSON publish_access GET "${package}" publishConfig access)
if(NOT publish_access STREQUAL "public")
  message(FATAL_ERROR "Data package must publish publicly")
endif()

# --- Entry points -------------------------------------------------------------

string(JSON default_import GET "${package}" exports . import)
string(JSON default_types GET "${package}" exports . types)
string(JSON data_bin GET "${package}" bin libmorpheus-data)
string(JSON types_field GET "${package}" types)
if(NOT default_import STREQUAL "./data.js" OR
   NOT default_types STREQUAL "./data.d.ts" OR
   NOT data_bin STREQUAL "./data.js" OR
   NOT types_field STREQUAL "./data.d.ts")
  message(FATAL_ERROR "Unexpected data package entry points")
endif()

# --- jsr.json (JSR) ---------------------------------------------------------

set(jsr_path "${data_dir}/jsr.json")
file(READ "${jsr_path}" jsr_config)
foreach(field IN ITEMS name version license)
  string(JSON "jsr_${field}" ERROR_VARIABLE json_error
         GET "${jsr_config}" "${field}")
  if(json_error)
    message(FATAL_ERROR "Invalid ${field} in ${jsr_path}: ${json_error}")
  endif()
endforeach()
if(NOT jsr_name STREQUAL "@libmorpheus/data")
  message(FATAL_ERROR "Unexpected JSR package name: ${jsr_name}")
endif()
if(NOT jsr_version STREQUAL data_version)
  message(FATAL_ERROR
    "JSR version ${jsr_version} differs from package ${data_version}")
endif()
if(NOT jsr_license STREQUAL "AGPL-3.0-or-later")
  message(FATAL_ERROR "Unexpected JSR package license: ${jsr_license}")
endif()
string(JSON jsr_default_export GET "${jsr_config}" exports .)
if(NOT jsr_default_export STREQUAL "./data.js")
  message(FATAL_ERROR "Unexpected JSR package exports: ${jsr_default_export}")
endif()
file(READ "${data_dir}/data.js" data_entry)
string(FIND "${data_entry}" "// @ts-self-types=\"./data.d.ts\"" self_types_at)
if(self_types_at EQUAL -1)
  message(FATAL_ERROR "data.js must declare its types for JSR (@ts-self-types)")
endif()

# --- Packaged files -----------------------------------------------------------

set(expected_files
    LICENSE LICENSES NOTICE README.md data.d.ts data.js
    internal/archive.js internal/data-internal.js internal/data-manifest.js
    internal/gener-index.js internal/gener-manifest.js
    internal/gener-preparer.mjs internal/gener-runtime.js
    internal/main-module.js internal/runtime-subset.js internal/version.js)
string(JSON files_length LENGTH "${package}" files)
math(EXPR last_index "${files_length} - 1")
set(actual_files)
foreach(index RANGE 0 "${last_index}")
  string(JSON entry GET "${package}" files "${index}")
  list(APPEND actual_files "${entry}")
endforeach()
list(SORT actual_files)
list(SORT expected_files)
if(NOT actual_files STREQUAL expected_files)
  message(FATAL_ERROR
    "Data package files differ from the contract: ${actual_files}")
endif()
foreach(packaged IN LISTS expected_files)
  if(NOT EXISTS "${data_dir}/${packaged}")
    message(FATAL_ERROR "Missing data package source: ${packaged}")
  endif()
  if(packaged MATCHES "^(tools|test)/")
    message(FATAL_ERROR "Data package must not ship tools/ or test/: ${packaged}")
  endif()
endforeach()

# The JSR list names the same sources, with the license directory spelled
# file by file and the manifest itself.
set(expected_jsr_files ${expected_files} jsr.json)
list(REMOVE_ITEM expected_jsr_files LICENSES)
list(APPEND expected_jsr_files LICENSES/EMSCRIPTEN.txt LICENSES/MPL-2.0.txt)
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

foreach(required IN ITEMS
        package.json.license jsr.json jsr.json.license tools/bootstrap-npm.mjs
        test/bootstrap-npm.test.js test/data.test.js test/gener.test.js
        test/main-module.test.js LICENSES/EMSCRIPTEN.txt LICENSES/MPL-2.0.txt)
  if(NOT EXISTS "${data_dir}/${required}")
    message(FATAL_ERROR "Missing data package source: ${required}")
  endif()
endforeach()
file(GLOB data_root_files
     LIST_DIRECTORIES false
     RELATIVE "${data_dir}"
     "${data_dir}/*")
set(expected_root_files
    LICENSE NOTICE README.md data.d.ts data.js jsr.json jsr.json.license
    package.json package.json.license)
foreach(root_file IN LISTS data_root_files)
  list(FIND expected_root_files "${root_file}" expected_at)
  if(expected_at EQUAL -1)
    message(FATAL_ERROR "Unexpected file at data package root: ${root_file}")
  endif()
  list(REMOVE_ITEM expected_root_files "${root_file}")
endforeach()
if(expected_root_files)
  message(FATAL_ERROR "Missing data package root files: ${expected_root_files}")
endif()
file(GLOB internal_files
     LIST_DIRECTORIES false
     RELATIVE "${data_dir}"
     "${data_dir}/internal/*")
list(SORT internal_files)
set(expected_internal_files ${expected_files})
list(FILTER expected_internal_files INCLUDE REGEX "^internal/")
list(SORT expected_internal_files)
if(NOT internal_files STREQUAL expected_internal_files)
  message(FATAL_ERROR
    "Data package internal/ differs from the packaged list: ${internal_files}")
endif()

# --- Files shared with the Node.js binding ------------------------------------

# Until @libmorpheus/node depends on this package, both carry these files;
# they must not drift. data-internal.js, data.js and version.js differ by
# design (the subset, the manifest and the package identity).
foreach(shared IN ITEMS
        internal/archive.js internal/data-manifest.js internal/gener-index.js
        internal/gener-manifest.js internal/gener-preparer.mjs
        internal/gener-runtime.js internal/main-module.js
        LICENSE LICENSES/EMSCRIPTEN.txt LICENSES/MPL-2.0.txt)
  file(SHA256 "${data_dir}/${shared}" data_sha)
  file(SHA256 "${node_dir}/${shared}" node_sha)
  if(NOT data_sha STREQUAL node_sha)
    message(FATAL_ERROR
      "${shared} differs between the data package and the Node.js binding")
  endif()
endforeach()

# --- No linguistic data -------------------------------------------------------

file(GLOB_RECURSE data_files
     LIST_DIRECTORIES false
     RELATIVE "${data_dir}"
     "${data_dir}/*")
list(FILTER data_files EXCLUDE REGEX "^node_modules/")
set(stemlib_pattern
    "(^|/)(nomind|vbind|nendind|vbendind|derivind|lemlist|vbs\\.cmp\\.ml|gener\\.index|[^/]*\\.lindex|[^/]*\\.out|[^/]*\\.table|UPSTREAM-LICENSE|MORPHEUS-DATA\\.json|stemlib-manifest\\.json)$")
foreach(data_file IN LISTS data_files)
  if(data_file MATCHES "${stemlib_pattern}")
    message(FATAL_ERROR
      "Data package tree contains a stemlib artifact: ${data_file}")
  endif()
endforeach()
string(JSON files_json GET "${package}" files)
foreach(manifest IN ITEMS "${files_json}" "${jsr_config}")
  if(manifest MATCHES "stemlib|steminds|endtables|rule_files|gener\\.index")
    message(FATAL_ERROR "Data package manifests must not reference linguistic data")
  endif()
endforeach()

# --- Pinned datasets ----------------------------------------------------------

# The dataset manifest pins the upstream revisions the redistribution policy
# reviewed; a change there is a provenance decision reviewed together with
# docs/stemlib-redistribution.md.
file(READ "${data_dir}/internal/data-manifest.js" datasets)
foreach(pin IN ITEMS
        "ALPHEIOS_REVISION = \"4632415fe93c85e9fdca47a0c5a13f31385f0023\""
        "PERSEIDS_REVISION = \"ab6898ffed335fc6169fa02c9940657a9b5a78e0\"")
  string(FIND "${datasets}" "${pin}" pin_at)
  if(pin_at EQUAL -1)
    message(FATAL_ERROR "Data package dataset manifest lost a pin: ${pin}")
  endif()
endforeach()

# --- Release decision ---------------------------------------------------------

set(decision "${MORPHEUS_SOURCE_DIR}/docs/release-data-${data_version}.md")
if(NOT EXISTS "${decision}")
  message(FATAL_ERROR "Missing data package release decision: ${decision}")
endif()
file(READ "${decision}" decision_text)
foreach(expected_statement IN ITEMS
        "Package version: **${data_version}**"
        "contains no linguistic data")
  string(FIND "${decision_text}" "${expected_statement}" statement_at)
  if(statement_at EQUAL -1)
    message(FATAL_ERROR "release-data-${data_version}.md is missing: ${expected_statement}")
  endif()
endforeach()
