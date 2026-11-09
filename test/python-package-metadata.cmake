# SPDX-License-Identifier: AGPL-3.0-or-later

if(NOT DEFINED MORPHEUS_SOURCE_DIR)
  message(FATAL_ERROR "MORPHEUS_SOURCE_DIR is required")
endif()

set(python_dir "${MORPHEUS_SOURCE_DIR}/bindings/python")
file(READ "${python_dir}/pyproject.toml" pyproject)
string(REGEX MATCH "\nversion = \"([0-9.]+)\"" _ "${pyproject}")
set(python_version "${CMAKE_MATCH_1}")
if(NOT python_version STREQUAL "0.2.0")
  message(FATAL_ERROR "Unexpected Python package version: ${python_version}")
endif()
foreach(required IN ITEMS
    "name = \"libmorpheus\""
    "requires-python = \">=3.11\""
    "license = \"AGPL-3.0-or-later\""
    "dependencies = []"
    "package-dir = { \"\" = \"src\" }"
    "license-files = [\"LICENSE\", \"NOTICE\"]"
    "libmorpheus-native = \"libmorpheus._cli:native_main\""
    "libmorpheus-data = \"libmorpheus._cli:data_main\""
    "libmorpheus-setup = \"libmorpheus._cli:setup_main\"")
  string(FIND "${pyproject}" "${required}" required_at)
  if(required_at EQUAL -1)
    message(FATAL_ERROR "Python package metadata is missing: ${required}")
  endif()
endforeach()

file(READ "${python_dir}/src/libmorpheus/_version.py" version_module)
foreach(required IN ITEMS
    "MORPHEUS_PYTHON_VERSION = \"${python_version}\""
    "MORPHEUS_NATIVE_VERSION = \"0.4.5\""
    "MORPHEUS_NATIVE_ABI_VERSION = 2")
  string(FIND "${version_module}" "${required}" required_at)
  if(required_at EQUAL -1)
    message(FATAL_ERROR "Python version metadata is missing: ${required}")
  endif()
endforeach()

file(READ "${python_dir}/README.md" python_readme)
if(NOT python_readme MATCHES "Python binding `${python_version}` targets\nnative runtime `0.4.5`")
  message(FATAL_ERROR "Python README disagrees with the declared versions")
endif()

foreach(required IN ITEMS
    LICENSE NOTICE README.md pyproject.toml
    src/libmorpheus/__init__.py src/libmorpheus/_abi.py
    src/libmorpheus/_acquisition.py src/libmorpheus/_cli.py
    src/libmorpheus/_library.py src/libmorpheus/_manifest.py
    src/libmorpheus/_types.py src/libmorpheus/_version.py
    src/libmorpheus/data.py src/libmorpheus/native.py
    src/libmorpheus/setup.py
    src/libmorpheus/py.typed test/fixture.c test/runtime_smoke.py
    test/test_acquisition.py test/test_binding.py)
  if(NOT EXISTS "${python_dir}/${required}")
    message(FATAL_ERROR "Missing Python binding source: ${required}")
  endif()
endforeach()

foreach(required_file IN ITEMS
    "${MORPHEUS_SOURCE_DIR}/.github/workflows/python-release.yml"
    "${MORPHEUS_SOURCE_DIR}/.github/workflows/pypi-smoke.yml"
    "${MORPHEUS_SOURCE_DIR}/docs/release-python-${python_version}.md")
  if(NOT EXISTS "${required_file}")
    message(FATAL_ERROR "Missing Python release contract: ${required_file}")
  endif()
endforeach()

file(READ "${MORPHEUS_SOURCE_DIR}/.github/workflows/python-release.yml"
  release_workflow)
foreach(required IN ITEMS
    "python-v*" "pypa/gh-action-pypi-publish@release/v1"
    "environment:" "name: pypi" "id-token: write")
  string(FIND "${release_workflow}" "${required}" required_at)
  if(required_at EQUAL -1)
    message(FATAL_ERROR "Python publication workflow is missing: ${required}")
  endif()
endforeach()

file(READ "${MORPHEUS_SOURCE_DIR}/.github/workflows/pypi-smoke.yml"
  smoke_workflow)
foreach(required IN ITEMS
    "Publish Python binding" "https://pypi.org/simple"
    "runtime_smoke.py")
  string(FIND "${smoke_workflow}" "${required}" required_at)
  if(required_at EQUAL -1)
    message(FATAL_ERROR "PyPI smoke workflow is missing: ${required}")
  endif()
endforeach()

foreach(forbidden IN ITEMS
    libmorpheus.so libmorpheus.dylib stemlib gener.index)
  file(GLOB_RECURSE embedded "${python_dir}/*${forbidden}*")
  if(embedded)
    message(FATAL_ERROR "Python package embeds forbidden runtime data: ${embedded}")
  endif()
endforeach()

# The acquisition sources are pinned once: the Python manifest must carry
# the same upstream revisions, counts and digests as the @libmorpheus/data
# manifest, the same runtime subset rule, and the same generation-index
# digest; the native targets must name the declared release's assets.
file(READ "${python_dir}/src/libmorpheus/_manifest.py" python_manifest)
file(READ "${MORPHEUS_SOURCE_DIR}/bindings/js/data/internal/data-manifest.js" data_manifest)
file(READ "${MORPHEUS_SOURCE_DIR}/bindings/js/data/internal/runtime-subset.js" runtime_subset)
file(READ "${MORPHEUS_SOURCE_DIR}/bindings/js/data/internal/gener-manifest.js" gener_manifest)
# CMake regular expressions have no counted repetition: quoted hexadecimal
# strings are collected and those of a Git object ID or a SHA-256 kept.
string(REGEX MATCHALL "\"[0-9a-f][0-9a-f]+\"|fileCount: [0-9]+" pinned_values "${data_manifest}")
list(REMOVE_DUPLICATES pinned_values)
set(pinned_count 0)
foreach(pinned IN LISTS pinned_values)
  string(LENGTH "${pinned}" pinned_length)
  if(pinned MATCHES "^\"" AND NOT pinned_length EQUAL 42 AND NOT pinned_length EQUAL 66)
    continue()
  endif()
  string(REPLACE "fileCount: " "file_count=" python_form "${pinned}")
  string(FIND "${python_manifest}" "${python_form}" pinned_at)
  if(pinned_at EQUAL -1)
    message(FATAL_ERROR "Python manifest lacks the data package's pin: ${pinned}")
  endif()
  math(EXPR pinned_count "${pinned_count} + 1")
endforeach()
if(pinned_count LESS 8)
  message(FATAL_ERROR "Data package manifest yielded only ${pinned_count} pins")
endif()
string(REGEX MATCH "GENER_INDEX_SHA256 = \"([0-9a-f]+)\"" _ "${gener_manifest}")
string(FIND "${python_manifest}" "GENER_INDEX_SHA256 = \"${CMAKE_MATCH_1}\"" gener_at)
if(gener_at EQUAL -1)
  message(FATAL_ERROR "Python manifest pins another generation index digest")
endif()
string(REGEX MATCH "const RUNTIME_FILE =\n *(/[^\n]*/);" _ "${runtime_subset}")
string(REGEX REPLACE "^/|/$" "" js_runtime_rule "${CMAKE_MATCH_1}")
string(REPLACE "\\/" "/" js_runtime_rule "${js_runtime_rule}")
string(REGEX MATCHALL "r\"[^\"]*\"" python_rule_parts "${python_manifest}")
string(JOIN "" python_runtime_rule ${python_rule_parts})
string(REGEX REPLACE "^r\"|\"$" "" python_runtime_rule "${python_runtime_rule}")
string(REPLACE "\"r\"" "" python_runtime_rule "${python_runtime_rule}")
if(NOT python_runtime_rule STREQUAL js_runtime_rule)
  message(FATAL_ERROR
    "Python runtime subset rule differs from the data package's:\n${python_runtime_rule}\n${js_runtime_rule}")
endif()
foreach(asset IN ITEMS Linux-x86_64-glibc Linux-aarch64-glibc macOS-arm64)
  string(FIND "${python_manifest}" "\"${asset}\"" asset_at)
  if(asset_at EQUAL -1)
    message(FATAL_ERROR "Python native targets lack ${asset}")
  endif()
endforeach()
