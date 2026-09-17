# SPDX-License-Identifier: AGPL-3.0-or-later

foreach(required_variable IN ITEMS
        MORPHEUS_SOURCE_DIR
        MORPHEUS_PROJECT_VERSION
        MORPHEUS_ABI_VERSION
        MORPHEUS_SOVERSION)
  if(NOT DEFINED ${required_variable})
    message(FATAL_ERROR "${required_variable} is required")
  endif()
endforeach()

file(READ "${MORPHEUS_SOURCE_DIR}/include/morpheus/morpheus.h" c_header)
string(REGEX MATCH
  "#define[ \t]+MORPHEUS_ABI_VERSION[ \t]+([0-9]+)u"
  c_abi_definition "${c_header}"
)
if(NOT "${CMAKE_MATCH_1}" STREQUAL "${MORPHEUS_ABI_VERSION}")
  message(FATAL_ERROR
    "C header ABI ${CMAKE_MATCH_1} differs from CMake ABI ${MORPHEUS_ABI_VERSION}"
  )
endif()

file(READ "${MORPHEUS_SOURCE_DIR}/docs/public-api.md" api_documentation)
set(expected_api_versions
    "The current project version is ${MORPHEUS_PROJECT_VERSION}, the SONAME major is ${MORPHEUS_SOVERSION}, and")
string(FIND "${api_documentation}" "${expected_api_versions}"
            api_versions_at)
if(api_versions_at EQUAL -1)
  message(FATAL_ERROR
    "public-api.md does not document project ${MORPHEUS_PROJECT_VERSION} and SONAME ${MORPHEUS_SOVERSION}"
  )
endif()

file(READ "${MORPHEUS_SOURCE_DIR}/CHANGELOG.md" changelog)
foreach(expected_changelog_value IN ITEMS
        "Target project version: **${MORPHEUS_PROJECT_VERSION}**"
        "C ABI: **${MORPHEUS_ABI_VERSION}**"
        "Shared-library SONAME: **${MORPHEUS_SOVERSION}**")
  string(FIND "${changelog}" "${expected_changelog_value}"
              changelog_value_at)
  if(changelog_value_at EQUAL -1)
    message(FATAL_ERROR
      "CHANGELOG.md is missing: ${expected_changelog_value}"
    )
  endif()
endforeach()

set(release_decision_path
    "${MORPHEUS_SOURCE_DIR}/docs/release-${MORPHEUS_PROJECT_VERSION}.md")
if(NOT EXISTS "${release_decision_path}")
  message(FATAL_ERROR
    "release decision is missing: docs/release-${MORPHEUS_PROJECT_VERSION}.md"
  )
endif()
file(READ "${release_decision_path}" release_decision)
foreach(expected_release_value IN ITEMS
        "Project version: **${MORPHEUS_PROJECT_VERSION}**"
        "C ABI: **${MORPHEUS_ABI_VERSION}**"
        "SONAME major: **${MORPHEUS_SOVERSION}**")
  string(FIND "${release_decision}" "${expected_release_value}"
              release_value_at)
  if(release_value_at EQUAL -1)
    message(FATAL_ERROR
      "release-${MORPHEUS_PROJECT_VERSION}.md is missing: "
      "${expected_release_value}"
    )
  endif()
endforeach()

file(READ "${MORPHEUS_SOURCE_DIR}/docs/releasing.md" releasing_guide)
string(FIND "${releasing_guide}"
  "release-${MORPHEUS_PROJECT_VERSION}.md" current_release_at)
if(current_release_at EQUAL -1)
  message(FATAL_ERROR
    "releasing.md does not identify release-${MORPHEUS_PROJECT_VERSION}.md")
endif()

file(READ "${MORPHEUS_SOURCE_DIR}/.github/workflows/platform.yml"
     platform_workflow)
foreach(expected_workflow_value IN ITEMS
        "publish-release:"
        "actions/download-artifact@v5"
        "contents: write"
        "bench/release-evidence/benchmark-"
        "workflow_id: 'test.yml'"
        "Linux-x86_64-glibc.tar.gz")
  string(FIND "${platform_workflow}" "${expected_workflow_value}"
              workflow_value_at)
  if(workflow_value_at EQUAL -1)
    message(FATAL_ERROR
      "platform workflow is missing: ${expected_workflow_value}")
  endif()
endforeach()
string(FIND "${platform_workflow}" "publish-jsr:" coupled_jsr_at)
if(NOT coupled_jsr_at EQUAL -1)
  message(FATAL_ERROR "native platform workflow still publishes JSR")
endif()

file(READ "${MORPHEUS_SOURCE_DIR}/.github/workflows/deno-release.yml"
     deno_release_workflow)
foreach(expected_workflow_value IN ITEMS
        "deno-v*"
        "MORPHEUS_DENO_VERSION"
        "MORPHEUS_NATIVE_VERSION"
        "libmorpheus-deno-"
        "workflow_id: 'test.yml'"
        "deno publish --dry-run"
        "run: deno publish"
        "id-token: write")
  string(FIND "${deno_release_workflow}" "${expected_workflow_value}"
              workflow_value_at)
  if(workflow_value_at EQUAL -1)
    message(FATAL_ERROR
      "Deno release workflow is missing: ${expected_workflow_value}")
  endif()
endforeach()

file(READ "${MORPHEUS_SOURCE_DIR}/Dockerfile" dockerfile)
foreach(expected_container_value IN ITEMS
        "tools/prepare-runtime-data.sh /opt/morpheus-runtime-data"
        "/opt/morpheus-runtime-data"
        "ENV MORPHEUS_LIBRARY=/opt/morpheus/lib/libmorpheus.so"
        "ENV MORPHEUS_STEMLIB=/opt/morpheus/share/morpheus/stemlib"
        "jsr:@libmorpheus/deno@0.4.0"
        "test ! -e /opt/morpheus/share/morpheus/deno"
        "5aa76d8c86c54af5121a3cce506ecaa57d14c6667ac0f091efd164ddfa9822d6"
        "generation lost dual forms")
  string(FIND "${dockerfile}${platform_workflow}"
              "${expected_container_value}" container_value_at)
  if(container_value_at EQUAL -1)
    message(FATAL_ERROR
      "Docker generation qualification is missing: ${expected_container_value}")
  endif()
endforeach()
string(FIND "${dockerfile}" "bindings/js/deno" embedded_deno_binding_at)
if(NOT embedded_deno_binding_at EQUAL -1)
  message(FATAL_ERROR "deno-runtime still embeds the source-tree Deno binding")
endif()
string(FIND "${platform_workflow}"
  "from \"/opt/morpheus/share/morpheus/deno/mod.ts\""
  local_deno_import_at)
if(NOT local_deno_import_at EQUAL -1)
  message(FATAL_ERROR "container qualification still imports a bundled binding")
endif()

if(MORPHEUS_PROJECT_VERSION STREQUAL "0.3.0")
  string(FIND "${release_decision}"
    "@humanities/libmorpheus" jsr_package_at)
  if(jsr_package_at EQUAL -1)
    message(FATAL_ERROR
      "release-0.3.0.md does not identify the reserved JSR package")
  endif()
  string(FIND "${release_decision}"
    "generation surface and Deno `generate()`/`generateRaw()` methods are\nexperimental"
    experimental_at)
  if(experimental_at EQUAL -1)
    message(FATAL_ERROR
      "release-0.3.0.md does not retain experimental generation status")
  endif()
  set(benchmark_path
      "${MORPHEUS_SOURCE_DIR}/bench/release-evidence/benchmark-0.3.0.json")
  set(benchmark_checksum
      "82875bed7e33312a1315819dc8c73fb53aa79a05c8aef0407b5768c2baf2a290")
  if(NOT EXISTS "${benchmark_path}" OR
     NOT EXISTS "${benchmark_path}.sha256")
    message(FATAL_ERROR "Accepted 0.3.0 benchmark evidence is missing")
  endif()
  file(SHA256 "${benchmark_path}" actual_benchmark_checksum)
  file(READ "${benchmark_path}.sha256" recorded_benchmark_checksum)
  if(NOT actual_benchmark_checksum STREQUAL benchmark_checksum OR
     NOT recorded_benchmark_checksum MATCHES
       "^${benchmark_checksum}  benchmark-0.3.0.json")
    message(FATAL_ERROR "Accepted 0.3.0 benchmark digest differs")
  endif()
endif()

if(MORPHEUS_PROJECT_VERSION STREQUAL "0.3.1")
  foreach(expected_patch_release_value IN ITEMS
          "@humanities/libmorpheus@0.3.1"
          "Benchmark evidence: **accepted**"
          "generation surface and Deno `generate()`/`generateRaw()` methods remain\nexperimental"
          "Tag that qualified commit as `v0.3.1` only after explicit authorization")
    string(FIND "${release_decision}" "${expected_patch_release_value}"
                patch_release_value_at)
    if(patch_release_value_at EQUAL -1)
      message(FATAL_ERROR
        "release-0.3.1.md is missing: ${expected_patch_release_value}")
    endif()
  endforeach()
  set(benchmark_path
      "${MORPHEUS_SOURCE_DIR}/bench/release-evidence/benchmark-0.3.1.json")
  set(benchmark_checksum
      "336db599db9f87ba06cedb7c2e0435125fc9918a62215ddc6988b5612c94ca78")
  if(NOT EXISTS "${benchmark_path}" OR
     NOT EXISTS "${benchmark_path}.sha256")
    message(FATAL_ERROR "Accepted 0.3.1 benchmark evidence is missing")
  endif()
  file(SHA256 "${benchmark_path}" actual_benchmark_checksum)
  file(READ "${benchmark_path}.sha256" recorded_benchmark_checksum)
  if(NOT actual_benchmark_checksum STREQUAL benchmark_checksum OR
     NOT recorded_benchmark_checksum MATCHES
       "^${benchmark_checksum}  benchmark-0.3.1.json")
    message(FATAL_ERROR "Accepted 0.3.1 benchmark digest differs")
  endif()
endif()

if(MORPHEUS_PROJECT_VERSION STREQUAL "0.3.2")
  foreach(expected_patch_release_value IN ITEMS
          "@humanities/libmorpheus@0.3.2"
          "Benchmark evidence: **accepted**"
          "generation surface and Deno `generate()`/`generateRaw()` methods remain\nexperimental"
          "path-scoped `--allow-read` and `--allow-write`"
          "Tag that qualified commit as `v0.3.2` only after explicit authorization")
    string(FIND "${release_decision}" "${expected_patch_release_value}"
                patch_release_value_at)
    if(patch_release_value_at EQUAL -1)
      message(FATAL_ERROR
        "release-0.3.2.md is missing: ${expected_patch_release_value}")
    endif()
  endforeach()
  set(benchmark_path
      "${MORPHEUS_SOURCE_DIR}/bench/release-evidence/benchmark-0.3.2.json")
  set(benchmark_checksum
      "5b20eb33ac4f1731bc3b1f1a417afd381d6f9573ad7bcb73b6ae91914b0c83d6")
  if(NOT EXISTS "${benchmark_path}" OR
     NOT EXISTS "${benchmark_path}.sha256")
    message(FATAL_ERROR "Accepted 0.3.2 benchmark evidence is missing")
  endif()
  file(SHA256 "${benchmark_path}" actual_benchmark_checksum)
  file(READ "${benchmark_path}.sha256" recorded_benchmark_checksum)
  if(NOT actual_benchmark_checksum STREQUAL benchmark_checksum OR
     NOT recorded_benchmark_checksum MATCHES
       "^${benchmark_checksum}  benchmark-0.3.2.json")
    message(FATAL_ERROR "Accepted 0.3.2 benchmark digest differs")
  endif()
endif()

if(MORPHEUS_PROJECT_VERSION STREQUAL "0.4.0")
  foreach(expected_minor_release_value IN ITEMS
          "Previous release tag: `v0.3.2`"
          "Benchmark evidence: **accepted**"
          "public C declarations and symbol set remain identical to 0.3.2"
          "`morpheus_stemlib_production`"
          "3048fdad64b30f5ba35423bacb5197f5a347e228"
          "1ad54b590a1a30be3ffb9c79d52f4c58944d12edcb1d92c527d0fb845a4e3793"
          "Tag that qualified commit as `v0.4.0` only after explicit authorization")
    string(FIND "${release_decision}" "${expected_minor_release_value}"
                minor_release_value_at)
    if(minor_release_value_at EQUAL -1)
      message(FATAL_ERROR
        "release-0.4.0.md is missing: ${expected_minor_release_value}")
    endif()
  endforeach()
  set(benchmark_path
      "${MORPHEUS_SOURCE_DIR}/bench/release-evidence/benchmark-0.4.0.json")
  set(benchmark_checksum
      "1ad54b590a1a30be3ffb9c79d52f4c58944d12edcb1d92c527d0fb845a4e3793")
  if(NOT EXISTS "${benchmark_path}" OR
     NOT EXISTS "${benchmark_path}.sha256")
    message(FATAL_ERROR "Accepted 0.4.0 benchmark evidence is missing")
  endif()
  file(SHA256 "${benchmark_path}" actual_benchmark_checksum)
  file(READ "${benchmark_path}.sha256" recorded_benchmark_checksum)
  if(NOT actual_benchmark_checksum STREQUAL benchmark_checksum OR
     NOT recorded_benchmark_checksum MATCHES
       "^${benchmark_checksum}  benchmark-0.4.0.json")
    message(FATAL_ERROR "Accepted 0.4.0 benchmark digest differs")
  endif()
endif()
