# SPDX-License-Identifier: AGPL-3.0-or-later

if(NOT DEFINED MORPHEUS_SOURCE_DIR)
  message(FATAL_ERROR "MORPHEUS_SOURCE_DIR is required")
endif()

set(node_dir "${MORPHEUS_SOURCE_DIR}/bindings/js/node")
file(READ "${node_dir}/package.json" package)
foreach(field IN ITEMS name version license type)
  string(JSON "node_${field}" ERROR_VARIABLE json_error GET "${package}" "${field}")
  if(json_error)
    message(FATAL_ERROR "Invalid Node package ${field}: ${json_error}")
  endif()
endforeach()
if(NOT node_name STREQUAL "@libmorpheus/node" OR
   NOT node_version STREQUAL "0.1.3" OR
   NOT node_license STREQUAL "AGPL-3.0-or-later" OR
   NOT node_type STREQUAL "module")
  message(FATAL_ERROR
    "Unexpected Node package identity: ${node_name}@${node_version}, ${node_license}, ${node_type}")
endif()

file(READ "${node_dir}/internal/version.js" version_module)
string(FIND "${version_module}"
  "MORPHEUS_NODE_VERSION = \"${node_version}\"" version_at)
if(version_at EQUAL -1)
  message(FATAL_ERROR "Node version module differs from package.json")
endif()
file(READ "${node_dir}/index.d.ts" index_types)
string(FIND "${index_types}"
  "MORPHEUS_NODE_VERSION = \"${node_version}\"" typed_version_at)
if(typed_version_at EQUAL -1)
  message(FATAL_ERROR "Node index.d.ts declares another MORPHEUS_NODE_VERSION")
endif()
# The declared native release is one string in the manifest, its types and
# the README; the binding version has a release decision from 0.1.3 on.
file(READ "${node_dir}/internal/native-manifest.js" native_manifest)
string(REGEX MATCH "MORPHEUS_NATIVE_VERSION = \"([0-9.]+)\"" _ "${native_manifest}")
set(declared_native_version "${CMAKE_MATCH_1}")
if(NOT declared_native_version MATCHES "^[0-9]+\\.[0-9]+\\.[0-9]+$")
  message(FATAL_ERROR "Node native manifest declares no native release")
endif()
file(READ "${node_dir}/native.d.ts" native_types)
file(READ "${node_dir}/README.md" node_readme)
if(NOT native_types MATCHES "MORPHEUS_NATIVE_VERSION: \"${declared_native_version}\"" OR
   NOT node_readme MATCHES "Binding `${node_version}` currently\nacquires native runtime `${declared_native_version}`")
  message(FATAL_ERROR
    "Node native.d.ts or README disagree with native release ${declared_native_version}")
endif()
if(NOT EXISTS "${MORPHEUS_SOURCE_DIR}/docs/release-node-${node_version}.md")
  message(FATAL_ERROR
    "Missing Node.js release decision: docs/release-node-${node_version}.md")
endif()

foreach(forbidden_script IN ITEMS preinstall install postinstall)
  string(JSON ignored ERROR_VARIABLE script_error
    GET "${package}" scripts "${forbidden_script}")
  if(NOT script_error)
    message(FATAL_ERROR
      "Node package must not run ${forbidden_script} during npm installation")
  endif()
endforeach()
# The only runtime dependency is the data acquisition package, pinned to
# the exact version the tree carries: the binding declares which
# acquisition logic it ships, as it declares its native release.
string(JSON dependency_count LENGTH "${package}" dependencies)
if(NOT dependency_count EQUAL 1)
  message(FATAL_ERROR
    "Node package must depend on @libmorpheus/data only: ${dependency_count} dependencies")
endif()
string(JSON data_dependency ERROR_VARIABLE field_error
  GET "${package}" dependencies "@libmorpheus/data")
if(field_error)
  message(FATAL_ERROR "Node package does not depend on @libmorpheus/data")
endif()
file(READ "${MORPHEUS_SOURCE_DIR}/bindings/js/data/package.json" data_package)
string(JSON data_tree_version GET "${data_package}" version)
if(NOT data_dependency STREQUAL data_tree_version)
  message(FATAL_ERROR
    "Node package pins @libmorpheus/data@${data_dependency}; the tree carries ${data_tree_version}")
endif()
foreach(forbidden_field IN ITEMS peerDependencies)
  string(JSON ignored ERROR_VARIABLE field_error GET "${package}" "${forbidden_field}")
  if(NOT field_error)
    message(FATAL_ERROR
      "Node package unexpectedly declares ${forbidden_field}")
  endif()
endforeach()

foreach(platform IN ITEMS
    darwin-arm64 linux-arm64-gnu linux-x64-gnu)
  set(platform_path "${node_dir}/npm/${platform}/package.json")
  file(READ "${platform_path}" platform_package)
  string(JSON platform_name GET "${platform_package}" name)
  string(JSON platform_version GET "${platform_package}" version)
  if(NOT platform_name STREQUAL "@libmorpheus/node-${platform}" OR
     NOT platform_version STREQUAL node_version)
    message(FATAL_ERROR
      "Unexpected Node platform package: ${platform_name}@${platform_version}")
  endif()
  string(JSON optional_version GET
    "${package}" optionalDependencies "${platform_name}")
  if(NOT optional_version STREQUAL node_version)
    message(FATAL_ERROR
      "Main Node package does not pin ${platform_name}@${node_version}")
  endif()
  file(READ "${MORPHEUS_SOURCE_DIR}/.github/workflows/platform.yml"
    platform_workflow)
  string(FIND "${platform_workflow}"
    "libmorpheus-node-${platform}" artifact_at)
  string(FIND "${platform_workflow}"
    "npm-node-${platform}" staging_at)
  if(artifact_at EQUAL -1 OR staging_at EQUAL -1)
    message(FATAL_ERROR
      "Platform workflow does not qualify Node target ${platform}")
  endif()
endforeach()

string(JSON default_import GET "${package}" exports . import)
string(JSON default_types GET "${package}" exports . types)
if(NOT default_import STREQUAL "./index.js" OR
   NOT default_types STREQUAL "./index.d.ts")
  message(FATAL_ERROR "Unexpected Node package exports")
endif()
string(JSON native_import GET "${package}" exports ./native import)
string(JSON native_types GET "${package}" exports ./native types)
string(JSON native_bin GET "${package}" bin libmorpheus-native)
if(NOT native_import STREQUAL "./native.js" OR
   NOT native_types STREQUAL "./native.d.ts" OR
   NOT native_bin STREQUAL "./native.js")
  message(FATAL_ERROR "Unexpected Node native acquisition entrypoint")
endif()
string(JSON data_import GET "${package}" exports ./data import)
string(JSON data_types GET "${package}" exports ./data types)
string(JSON data_bin GET "${package}" bin libmorpheus-data)
if(NOT data_import STREQUAL "./data.js" OR
   NOT data_types STREQUAL "./data.d.ts" OR
   NOT data_bin STREQUAL "./data.js")
  message(FATAL_ERROR "Unexpected Node data acquisition entrypoint")
endif()
string(JSON setup_import GET "${package}" exports ./setup import)
string(JSON setup_types GET "${package}" exports ./setup types)
string(JSON setup_bin GET "${package}" bin libmorpheus-setup)
if(NOT setup_import STREQUAL "./setup.js" OR
   NOT setup_types STREQUAL "./setup.d.ts" OR
   NOT setup_bin STREQUAL "./setup.js")
  message(FATAL_ERROR "Unexpected Node combined setup entrypoint")
endif()

# The data internals moved to bindings/js/data; the binding must not grow
# a copy back.
foreach(removed IN ITEMS internal/data-internal.js
    internal/data-manifest.js internal/gener-index.js
    internal/gener-manifest.js internal/gener-preparer.mjs
    internal/gener-runtime.js LICENSES)
  if(EXISTS "${node_dir}/${removed}")
    message(FATAL_ERROR
      "Node binding carries ${removed} again; it belongs to @libmorpheus/data")
  endif()
endforeach()
foreach(required IN ITEMS
    CMakeLists.txt LICENSE NOTICE README.md addon.c index.d.ts index.js
    data.d.ts data.js internal/archive.js internal/main-module.js
    internal/native-internal.js internal/native-manifest.js
    internal/setup-internal.js internal/version.js native.d.ts native.js
    setup.d.ts setup.js
    package-platform.mjs package.json package.json.license
    test/binding.test.js test/main-module.test.js test/native.test.js
    test/setup.test.js)
  if(NOT EXISTS "${node_dir}/${required}")
    message(FATAL_ERROR "Missing Node binding source: ${required}")
  endif()
endforeach()
