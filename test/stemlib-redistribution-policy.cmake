# SPDX-License-Identifier: AGPL-3.0-or-later

if(NOT DEFINED MORPHEUS_SOURCE_DIR)
  message(FATAL_ERROR "MORPHEUS_SOURCE_DIR is required")
endif()

set(policy_path
    "${MORPHEUS_SOURCE_DIR}/tools/stemlib-redistribution-policy.json")
file(READ "${policy_path}" policy)

function(require_json expected)
  string(JSON actual ERROR_VARIABLE json_error GET "${policy}" ${ARGN})
  if(json_error OR NOT actual STREQUAL expected)
    list(JOIN ARGN "." field)
    message(FATAL_ERROR
      "stemlib redistribution policy ${field}: expected ${expected}, got "
      "${actual} (${json_error})")
  endif()
endfunction()

require_json("1" schema)
require_json("review-required" state)
string(JSON decision_type TYPE "${policy}" decision_record)
if(NOT decision_type STREQUAL "NULL")
  message(FATAL_ERROR
    "review-required stemlib policy must not carry an approval decision")
endif()

foreach(channel IN ITEMS github_release_assets native_packages
                         binding_packages container_images
                         ci_payload_artifacts)
  require_json("OFF" publication ${channel})
endforeach()
foreach(operation IN ITEMS local_reconstruction local_runtime_packaging
                           direct_acquisition_from_upstream
                           receipt_and_checksum_publication)
  require_json("ON" permitted_operations ${operation})
endforeach()

find_package(Git REQUIRED)
set(expected_ids perseids-tools alpheios-project)
set(expected_roots stemlib vendor/alpheios-morpheus/dist/stemlib)
set(expected_revisions
    ab6898ffed335fc6169fa02c9940657a9b5a78e0
    4632415fe93c85e9fdca47a0c5a13f31385f0023)
set(expected_trees
    5dcaeb87f8d65f6ee0cde88abfc860b82faab046
    ccbe43e3f99b827bf8ea1fe9eec102edd49d6c93)

string(JSON dataset_count LENGTH "${policy}" datasets)
if(NOT dataset_count EQUAL 2)
  message(FATAL_ERROR "stemlib policy must describe exactly two datasets")
endif()

foreach(index RANGE 0 1)
  list(GET expected_ids ${index} expected_id)
  list(GET expected_roots ${index} expected_root)
  list(GET expected_revisions ${index} expected_revision)
  list(GET expected_trees ${index} expected_tree)
  require_json("${expected_id}" datasets ${index} id)
  require_json("${expected_root}" datasets ${index} local_root)
  require_json("${expected_revision}" datasets ${index} source_revision)
  require_json("${expected_tree}" datasets ${index} selected_tree)
  require_json("not-qualified" datasets ${index} redistribution)

  if(index EQUAL 0)
    execute_process(
      COMMAND "${GIT_EXECUTABLE}" rev-parse "HEAD:${expected_root}"
      WORKING_DIRECTORY "${MORPHEUS_SOURCE_DIR}"
      RESULT_VARIABLE tree_result
      OUTPUT_VARIABLE actual_tree
      OUTPUT_STRIP_TRAILING_WHITESPACE
      ERROR_VARIABLE tree_error)
  else()
    execute_process(
      COMMAND "${GIT_EXECUTABLE}" rev-parse "HEAD:dist/stemlib"
      WORKING_DIRECTORY
        "${MORPHEUS_SOURCE_DIR}/vendor/alpheios-morpheus"
      RESULT_VARIABLE tree_result
      OUTPUT_VARIABLE actual_tree
      OUTPUT_STRIP_TRAILING_WHITESPACE
      ERROR_VARIABLE tree_error)
    execute_process(
      COMMAND "${GIT_EXECUTABLE}" rev-parse HEAD
      WORKING_DIRECTORY
        "${MORPHEUS_SOURCE_DIR}/vendor/alpheios-morpheus"
      RESULT_VARIABLE revision_result
      OUTPUT_VARIABLE actual_revision
      OUTPUT_STRIP_TRAILING_WHITESPACE
      ERROR_VARIABLE revision_error)
    if(NOT revision_result EQUAL 0 OR
       NOT actual_revision STREQUAL expected_revision)
      message(FATAL_ERROR
        "Alpheios revision differs from the redistribution policy: "
        "${actual_revision} (${revision_error})")
    endif()
  endif()
  if(NOT tree_result EQUAL 0 OR NOT actual_tree STREQUAL expected_tree)
    message(FATAL_ERROR
      "${expected_id} tree differs from the redistribution policy: "
      "${actual_tree} (${tree_error})")
  endif()

  string(JSON evidence_count LENGTH "${policy}" datasets ${index}
              license_evidence)
  if(evidence_count LESS 1)
    message(FATAL_ERROR "${expected_id} has no recorded license evidence")
  endif()
  math(EXPR evidence_last "${evidence_count} - 1")
  foreach(evidence_index RANGE 0 ${evidence_last})
    string(JSON evidence_path GET "${policy}" datasets ${index}
                license_evidence ${evidence_index} path)
    string(JSON evidence_sha GET "${policy}" datasets ${index}
                license_evidence ${evidence_index} sha256)
    if(evidence_path MATCHES "(^/|(^|/)\\.\\.(/|$))")
      message(FATAL_ERROR "unsafe license evidence path: ${evidence_path}")
    endif()
    set(evidence_file "${MORPHEUS_SOURCE_DIR}/${evidence_path}")
    if(NOT EXISTS "${evidence_file}")
      message(FATAL_ERROR "license evidence is missing: ${evidence_path}")
    endif()
    file(SHA256 "${evidence_file}" actual_evidence_sha)
    if(NOT actual_evidence_sha STREQUAL evidence_sha)
      message(FATAL_ERROR
        "license evidence changed without policy review: ${evidence_path}")
    endif()
  endforeach()
endforeach()

foreach(workflow IN ITEMS platform.yml deno-release.yml node-release.yml
                          python-release.yml)
  file(READ "${MORPHEUS_SOURCE_DIR}/.github/workflows/${workflow}"
       workflow_contents)
  if(workflow_contents MATCHES
     "morpheus-stemlib-|stemlib-runtime-artifacts[^\\n]*[.]tar")
    message(FATAL_ERROR
      "${workflow} attempts to publish an unqualified stemlib payload")
  endif()
endforeach()

file(READ
  "${MORPHEUS_SOURCE_DIR}/tools/stemlib-redistribution-policy.json.license"
  policy_license)
if(NOT policy_license MATCHES
   "SPDX-License-Identifier: AGPL-3[.]0-or-later")
  message(FATAL_ERROR "stemlib policy SPDX sidecar is missing")
endif()
