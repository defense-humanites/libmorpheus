# SPDX-License-Identifier: AGPL-3.0-or-later
# MORPHEUS_TEST_LAUNCHER is empty for native builds; cross builds (Emscripten)
# pass the emulator that runs the compiled programs.

foreach(required IN ITEMS MORPHEUS_GENER_INDEX_BUILDER
                          MORPHEUS_GENER_INDEX_INSPECTOR
                          MORPHEUS_GENER_INDEX_SOURCE
                          MORPHEUS_GENER_INDEX_UNEXPANDED_SOURCE
                          MORPHEUS_GENER_INDEX_WORK_DIR)
  if(NOT DEFINED ${required})
    message(FATAL_ERROR "${required} is required")
  endif()
endforeach()

file(MAKE_DIRECTORY "${MORPHEUS_GENER_INDEX_WORK_DIR}")
set(first "${MORPHEUS_GENER_INDEX_WORK_DIR}/first.mgi")
set(second "${MORPHEUS_GENER_INDEX_WORK_DIR}/second.mgi")
file(REMOVE "${first}" "${second}")

foreach(output IN ITEMS "${first}" "${second}")
  execute_process(
    COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_INDEX_BUILDER}"
            "${output}" "${MORPHEUS_GENER_INDEX_SOURCE}"
    RESULT_VARIABLE build_result
    OUTPUT_VARIABLE build_output
    ERROR_VARIABLE build_error
  )
  if(NOT build_result EQUAL 0)
    message(FATAL_ERROR
      "generation-index build failed (${build_result}):\n${build_output}${build_error}")
  endif()
endforeach()

execute_process(
  COMMAND "${CMAKE_COMMAND}" -E compare_files "${first}" "${second}"
  RESULT_VARIABLE compare_result
)
if(NOT compare_result EQUAL 0)
  message(FATAL_ERROR "generation-index output is not reproducible")
endif()

execute_process(
  COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_INDEX_INSPECTOR}" "${first}"
  RESULT_VARIABLE inspect_result
  OUTPUT_VARIABLE inspect_output
  ERROR_VARIABLE inspect_error
)
if(NOT inspect_result EQUAL 0)
  message(FATAL_ERROR
    "generation-index inspection failed (${inspect_result}):\n${inspect_output}${inspect_error}")
endif()

set(rejected "${MORPHEUS_GENER_INDEX_WORK_DIR}/rejected.mgi")
file(REMOVE "${rejected}")
execute_process(
  COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_INDEX_BUILDER}"
          "${rejected}" "${MORPHEUS_GENER_INDEX_UNEXPANDED_SOURCE}"
  RESULT_VARIABLE rejected_result
  OUTPUT_QUIET
  ERROR_QUIET
)
if(rejected_result EQUAL 0 OR EXISTS "${rejected}")
  message(FATAL_ERROR "unexpanded generation input was not rejected")
endif()
