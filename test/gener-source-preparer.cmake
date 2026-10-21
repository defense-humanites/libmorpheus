# SPDX-License-Identifier: AGPL-3.0-or-later
# MORPHEUS_TEST_LAUNCHER is empty for native builds; cross builds (Emscripten)
# pass the emulator that runs the compiled programs.

foreach(required IN ITEMS MORPHEUS_GENER_SOURCE_PREPARER
                          MORPHEUS_GENER_INDEX_BUILDER
                          MORPHEUS_GENER_SOURCE_INPUT
                          MORPHEUS_GENER_SOURCE_EXPECTED
                          MORPHEUS_GENER_SOURCE_ORPHAN
                          MORPHEUS_GENER_DERIVATION_SOURCE
                          MORPHEUS_GENER_DERIVATION_EXPECTED
                          MORPHEUS_GENER_DERIVATION_INVALID
                          MORPHEUS_GENER_SOURCE_WORK_DIR)
  if(NOT DEFINED ${required})
    message(FATAL_ERROR "${required} is required")
  endif()
endforeach()

file(MAKE_DIRECTORY "${MORPHEUS_GENER_SOURCE_WORK_DIR}")
set(derivation "${MORPHEUS_GENER_SOURCE_WORK_DIR}/derivation.txt")
set(derivation_index "${MORPHEUS_GENER_SOURCE_WORK_DIR}/derivation.mgi")
file(REMOVE "${derivation}" "${derivation_index}")
execute_process(
  COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_SOURCE_PREPARER}"
          "${derivation}" "${MORPHEUS_GENER_DERIVATION_SOURCE}"
  RESULT_VARIABLE derivation_result
  OUTPUT_VARIABLE derivation_output
  ERROR_VARIABLE derivation_error
)
if(NOT derivation_result EQUAL 0)
  message(FATAL_ERROR
    "derivation expansion failed (${derivation_result}):\n${derivation_output}${derivation_error}")
endif()
execute_process(
  COMMAND "${CMAKE_COMMAND}" -E compare_files
          "${derivation}" "${MORPHEUS_GENER_DERIVATION_EXPECTED}"
  RESULT_VARIABLE derivation_compare_result
)
if(NOT derivation_compare_result EQUAL 0)
  message(FATAL_ERROR "derivation expansion differs from the historical full oracle")
endif()
execute_process(
  COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_INDEX_BUILDER}"
          "${derivation_index}" "${derivation}"
  RESULT_VARIABLE derivation_index_result
  OUTPUT_VARIABLE derivation_index_output
  ERROR_VARIABLE derivation_index_error
)
if(NOT derivation_index_result EQUAL 0 OR NOT EXISTS "${derivation_index}")
  message(FATAL_ERROR
    "expanded derivations were rejected by the index builder (${derivation_index_result}):\n${derivation_index_output}${derivation_index_error}")
endif()

set(first "${MORPHEUS_GENER_SOURCE_WORK_DIR}/first.txt")
set(second "${MORPHEUS_GENER_SOURCE_WORK_DIR}/second.txt")
set(index "${MORPHEUS_GENER_SOURCE_WORK_DIR}/prepared.mgi")
file(REMOVE "${first}" "${second}" "${index}")

foreach(output IN ITEMS "${first}" "${second}")
  execute_process(
    COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_SOURCE_PREPARER}"
            "${output}" "${MORPHEUS_GENER_SOURCE_INPUT}"
    RESULT_VARIABLE prepare_result
    OUTPUT_VARIABLE prepare_output
    ERROR_VARIABLE prepare_error
  )
  if(NOT prepare_result EQUAL 0)
    message(FATAL_ERROR
      "generation-source preparation failed (${prepare_result}):\n${prepare_output}${prepare_error}")
  endif()
endforeach()

foreach(expected IN ITEMS "${MORPHEUS_GENER_SOURCE_EXPECTED}" "${second}")
  execute_process(
    COMMAND "${CMAKE_COMMAND}" -E compare_files "${first}" "${expected}"
    RESULT_VARIABLE compare_result
  )
  if(NOT compare_result EQUAL 0)
    message(FATAL_ERROR "prepared generation source is not reproducible or exact")
  endif()
endforeach()

execute_process(
  COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_INDEX_BUILDER}" "${index}" "${first}"
  RESULT_VARIABLE index_result
  OUTPUT_VARIABLE index_output
  ERROR_VARIABLE index_error
)
if(NOT index_result EQUAL 0 OR NOT EXISTS "${index}")
  message(FATAL_ERROR
    "prepared generation source was rejected by the index builder (${index_result}):\n${index_output}${index_error}")
endif()

foreach(rejected IN ITEMS "${MORPHEUS_GENER_SOURCE_ORPHAN}"
                          "${MORPHEUS_GENER_DERIVATION_INVALID}")
  set(rejected_output "${MORPHEUS_GENER_SOURCE_WORK_DIR}/rejected.txt")
  file(REMOVE "${rejected_output}")
  execute_process(
    COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_SOURCE_PREPARER}"
            "${rejected_output}" "${rejected}"
    RESULT_VARIABLE rejected_result
    OUTPUT_QUIET
    ERROR_QUIET
  )
  if(rejected_result EQUAL 0 OR EXISTS "${rejected_output}")
    message(FATAL_ERROR "invalid generation source was not rejected: ${rejected}")
  endif()
endforeach()
