# SPDX-License-Identifier: AGPL-3.0-or-later

cmake_minimum_required(VERSION 3.25)

foreach(required IN ITEMS MORPHEUS_STEMLIB_ROOT MORPHEUS_STEMLIB_MANIFEST
                          MORPHEUS_STEMLIB_MANIFEST_VALIDATOR
                          MORPHEUS_STEMLIB_STAGER MORPHEUS_WORK_DIR)
  if(NOT DEFINED ${required})
    message(FATAL_ERROR "${required} is required")
  endif()
endforeach()

file(LOCK "${MORPHEUS_WORK_DIR}.lock" GUARD PROCESS TIMEOUT 600
     RESULT_VARIABLE lock_result)
if(NOT lock_result STREQUAL "0")
  message(FATAL_ERROR "could not lock the staging test: ${lock_result}")
endif()

file(REMOVE_RECURSE "${MORPHEUS_WORK_DIR}")
file(MAKE_DIRECTORY "${MORPHEUS_WORK_DIR}")

function(stage_and_validate language pass expected_active expected_endings
                            expected_derivations expected_indexed_derivations)
  set(stage "${MORPHEUS_WORK_DIR}/${language}-${pass}")
  execute_process(
    COMMAND "${CMAKE_COMMAND}"
            -DMORPHEUS_STEMLIB_ROOT=${MORPHEUS_STEMLIB_ROOT}
            -DMORPHEUS_STEMLIB_MANIFEST=${MORPHEUS_STEMLIB_MANIFEST}
            -DMORPHEUS_STEMLIB_MANIFEST_VALIDATOR=${MORPHEUS_STEMLIB_MANIFEST_VALIDATOR}
            -DMORPHEUS_STEMLIB_LANGUAGE=${language}
            -DMORPHEUS_STEMLIB_STAGE=${stage}
            -P "${MORPHEUS_STEMLIB_STAGER}"
    RESULT_VARIABLE stage_result
    OUTPUT_VARIABLE stage_output
    ERROR_VARIABLE stage_error
  )
  if(NOT stage_result EQUAL 0)
    message(FATAL_ERROR
            "${language} staging failed:\n${stage_output}${stage_error}")
  endif()

  file(STRINGS "${stage}/MORPHEUS-STEMLIB-INPUTS.tsv" receipt_lines)
  set(active_count 0)
  foreach(line IN LISTS receipt_lines)
    if(line MATCHES "^[ \t]*#" OR line MATCHES "^[ \t]*$")
      continue()
    endif()
    string(REPLACE "\t" ";" fields "${line}")
    list(GET fields 3 relative_path)
    list(GET fields 4 expected_sha256)
    set(staged_source "${stage}/${language}/${relative_path}")
    if(NOT EXISTS "${staged_source}")
      message(FATAL_ERROR "staged source is missing: ${relative_path}")
    endif()
    file(SHA256 "${staged_source}" actual_sha256)
    if(NOT actual_sha256 STREQUAL expected_sha256)
      message(FATAL_ERROR "staged source changed: ${relative_path}")
    endif()
    math(EXPR active_count "${active_count} + 1")
  endforeach()
  file(STRINGS "${stage}/ending-tables.list" ending_tables)
  file(STRINGS "${stage}/derivation-tables.list" derivation_tables)
  file(STRINGS "${stage}/derivation-index-tables.list"
       indexed_derivation_tables)
  list(LENGTH ending_tables ending_count)
  list(LENGTH derivation_tables derivation_count)
  list(LENGTH indexed_derivation_tables indexed_derivation_count)
  if(NOT active_count EQUAL expected_active OR
     NOT ending_count EQUAL expected_endings OR
     NOT derivation_count EQUAL expected_derivations OR
     NOT indexed_derivation_count EQUAL expected_indexed_derivations)
    message(FATAL_ERROR "unexpected ${language} staging selection")
  endif()

  set(${language}_${pass}_stage "${stage}" PARENT_SCOPE)
endfunction()

stage_and_validate(Greek first 239 139 38 18)
stage_and_validate(Greek second 239 139 38 18)
stage_and_validate(Latin first 128 101 3 2)
stage_and_validate(Latin second 128 101 3 2)

foreach(language IN ITEMS Greek Latin)
  foreach(metadata IN ITEMS MORPHEUS-STEMLIB-INPUTS.tsv
                            ending-tables.list derivation-tables.list
                            derivation-index-tables.list)
    execute_process(
      COMMAND "${CMAKE_COMMAND}" -E compare_files
              "${${language}_first_stage}/${metadata}"
              "${${language}_second_stage}/${metadata}"
      RESULT_VARIABLE compare_result
    )
    if(NOT compare_result EQUAL 0)
      message(FATAL_ERROR "${language} staging metadata is not reproducible")
    endif()
  endforeach()
endforeach()

foreach(excluded IN ITEMS
        "Greek/endtables/source/conj3.end"
        "Greek/derivs/source/cw.deriv")
  if(EXISTS "${Greek_first_stage}/${excluded}")
    message(FATAL_ERROR "excluded source was staged: ${excluded}")
  endif()
endforeach()

execute_process(
  COMMAND "${CMAKE_COMMAND}"
          -DMORPHEUS_STEMLIB_ROOT=${MORPHEUS_STEMLIB_ROOT}
          -DMORPHEUS_STEMLIB_MANIFEST=${MORPHEUS_STEMLIB_MANIFEST}
          -DMORPHEUS_STEMLIB_MANIFEST_VALIDATOR=${MORPHEUS_STEMLIB_MANIFEST_VALIDATOR}
          -DMORPHEUS_STEMLIB_LANGUAGE=Greek
          -DMORPHEUS_STEMLIB_STAGE=${Greek_first_stage}
          -P "${MORPHEUS_STEMLIB_STAGER}"
  RESULT_VARIABLE reused_stage_result
  OUTPUT_QUIET
  ERROR_QUIET
)
if(reused_stage_result EQUAL 0)
  message(FATAL_ERROR "the stager accepted a non-empty destination")
endif()
