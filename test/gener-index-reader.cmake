# SPDX-License-Identifier: AGPL-3.0-or-later
# MORPHEUS_TEST_LAUNCHER is empty for native builds; cross builds (Emscripten)
# pass the emulator that runs the compiled programs.

foreach(required IN ITEMS MORPHEUS_GENER_INDEX_BUILDER
                          MORPHEUS_GENER_INDEX_READER_TEST
                          MORPHEUS_GENER_INDEX_SOURCE
                          MORPHEUS_GENER_INDEX_READER_WORK_DIR)
  if(NOT DEFINED ${required})
    message(FATAL_ERROR "${required} is required")
  endif()
endforeach()

file(REMOVE_RECURSE "${MORPHEUS_GENER_INDEX_READER_WORK_DIR}")
file(MAKE_DIRECTORY "${MORPHEUS_GENER_INDEX_READER_WORK_DIR}")
set(index "${MORPHEUS_GENER_INDEX_READER_WORK_DIR}/index.mgi")
execute_process(
  COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_INDEX_BUILDER}"
          "${index}" "${MORPHEUS_GENER_INDEX_SOURCE}"
  RESULT_VARIABLE build_result
  OUTPUT_VARIABLE build_output
  ERROR_VARIABLE build_error
)
if(NOT build_result EQUAL 0)
  message(FATAL_ERROR
    "generation-index reader fixture failed (${build_result}):\n"
    "${build_output}${build_error}")
endif()
execute_process(
  COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_INDEX_READER_TEST}" "${index}"
  RESULT_VARIABLE reader_result
  OUTPUT_VARIABLE reader_output
  ERROR_VARIABLE reader_error
)
if(NOT reader_result EQUAL 0)
  message(FATAL_ERROR
    "generation-index reader failed (${reader_result}):\n"
    "${reader_output}${reader_error}")
endif()
