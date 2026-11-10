# SPDX-License-Identifier: AGPL-3.0-or-later
# MORPHEUS_TEST_LAUNCHER is empty for native builds; cross builds (Emscripten)
# pass the emulator that runs the compiled programs.

foreach(required IN ITEMS MORPHEUS_GENER_SOURCE_PREPARER
                          MORPHEUS_GENER_INDEX_BUILDER
                          MORPHEUS_GENER_INDEX_READER_TEST
                          MORPHEUS_GENER_CORPUS_ROOT
                          MORPHEUS_GENER_CORPUS_MANIFEST
                          MORPHEUS_GENER_CORPUS_EXCEPTIONS
                          MORPHEUS_GENER_CORPUS_WORK_DIR)
  if(NOT DEFINED ${required})
    message(FATAL_ERROR "${required} is required")
  endif()
endforeach()

file(STRINGS "${MORPHEUS_GENER_CORPUS_MANIFEST}" manifest_lines)
set(inputs)
foreach(line IN LISTS manifest_lines)
  if(line STREQUAL "" OR line MATCHES "^#")
    continue()
  endif()
  string(REPLACE "\t" ";" fields "${line}")
  list(GET fields 2 relative_path)
  list(APPEND inputs "${MORPHEUS_GENER_CORPUS_ROOT}/${relative_path}")
endforeach()

file(REMOVE_RECURSE "${MORPHEUS_GENER_CORPUS_WORK_DIR}")
file(MAKE_DIRECTORY "${MORPHEUS_GENER_CORPUS_WORK_DIR}")
set(first_source "${MORPHEUS_GENER_CORPUS_WORK_DIR}/first.txt")
set(second_source "${MORPHEUS_GENER_CORPUS_WORK_DIR}/second.txt")
set(first_index "${MORPHEUS_GENER_CORPUS_WORK_DIR}/first.mgi")
set(second_index "${MORPHEUS_GENER_CORPUS_WORK_DIR}/second.mgi")

foreach(run IN ITEMS first second)
  execute_process(
    COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_SOURCE_PREPARER}"
            --exceptions "${MORPHEUS_GENER_CORPUS_EXCEPTIONS}"
            "${${run}_source}" ${inputs}
    RESULT_VARIABLE prepare_result
    OUTPUT_VARIABLE prepare_output
    ERROR_VARIABLE prepare_error
  )
  if(NOT prepare_result EQUAL 0)
    message(FATAL_ERROR
      "complete generation-corpus preparation failed (${prepare_result}):\n"
      "${prepare_output}${prepare_error}")
  endif()
  execute_process(
    COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_INDEX_BUILDER}"
            "${${run}_index}" "${${run}_source}"
    RESULT_VARIABLE index_result
    OUTPUT_VARIABLE index_output
    ERROR_VARIABLE index_error
  )
  if(NOT index_result EQUAL 0)
    message(FATAL_ERROR
      "complete generation-index build failed (${index_result}):\n"
      "${index_output}${index_error}")
  endif()
endforeach()

file(SHA256 "${first_source}" source_sha256)
file(SHA256 "${first_index}" index_sha256)
if(NOT source_sha256 STREQUAL
   "34583cc728a1e83267577519932a25324dad8b1e6dbb7f489994a3bbdbd4e604")
  message(FATAL_ERROR "complete prepared corpus changed: ${source_sha256}")
endif()
if(NOT index_sha256 STREQUAL
   "f223ca3257b85298513cf9984bfc0c63a3aa28f900eef8cf000150a24bb68629")
  message(FATAL_ERROR "complete generation index changed: ${index_sha256}")
endif()

# Without default principal parts, the preparer still reproduces the index of
# data 0.1.0 and native 0.4.6, the historical do_conj "full" expansion.
set(historical_source "${MORPHEUS_GENER_CORPUS_WORK_DIR}/historical.txt")
set(historical_index "${MORPHEUS_GENER_CORPUS_WORK_DIR}/historical.mgi")
execute_process(
  COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_SOURCE_PREPARER}"
          --requested-parts-only
          --exceptions "${MORPHEUS_GENER_CORPUS_EXCEPTIONS}"
          "${historical_source}" ${inputs}
  RESULT_VARIABLE historical_result
  OUTPUT_VARIABLE historical_output
  ERROR_VARIABLE historical_error
)
if(NOT historical_result EQUAL 0)
  message(FATAL_ERROR
    "historical generation-corpus preparation failed (${historical_result}):\n"
    "${historical_output}${historical_error}")
endif()
execute_process(
  COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_INDEX_BUILDER}"
          "${historical_index}" "${historical_source}"
  RESULT_VARIABLE historical_index_result
)
file(SHA256 "${historical_source}" historical_source_sha256)
file(SHA256 "${historical_index}" historical_index_sha256)
if(NOT historical_index_result EQUAL 0 OR
   NOT historical_source_sha256 STREQUAL
   "1c14949bb73649056d399b8d5d4f6fc1170ecba51ecc1416c036ec57ebbd4866" OR
   NOT historical_index_sha256 STREQUAL
   "5aa76d8c86c54af5121a3cce506ecaa57d14c6667ac0f091efd164ddfa9822d6")
  message(FATAL_ERROR
    "requested-parts-only preparation no longer reproduces the historical index: "
    "${historical_source_sha256} ${historical_index_sha256}")
endif()
execute_process(
  COMMAND "${CMAKE_COMMAND}" -E compare_files "${first_source}" "${second_source}"
  RESULT_VARIABLE source_compare
)
execute_process(
  COMMAND "${CMAKE_COMMAND}" -E compare_files "${first_index}" "${second_index}"
  RESULT_VARIABLE index_compare
)
if(NOT source_compare EQUAL 0 OR NOT index_compare EQUAL 0)
  message(FATAL_ERROR "complete generation corpus is not reproducible")
endif()

execute_process(
  COMMAND ${MORPHEUS_TEST_LAUNCHER} "${MORPHEUS_GENER_INDEX_READER_TEST}"
          "${first_index}" 106427 108220 182760
  RESULT_VARIABLE reader_result
  OUTPUT_VARIABLE reader_output
  ERROR_VARIABLE reader_error
)
if(NOT reader_result EQUAL 0)
  message(FATAL_ERROR
    "complete generation-index reader failed (${reader_result}):\n"
    "${reader_output}${reader_error}")
endif()
