# SPDX-License-Identifier: AGPL-3.0-or-later

cmake_minimum_required(VERSION 3.25)

foreach(required IN ITEMS MORPHEUS_GREEK_ARCHIVE MORPHEUS_LATIN_ARCHIVE
                          MORPHEUS_CRUNCHER MORPHEUS_FIXTURES
                          MORPHEUS_FIXTURE_RUNNER MORPHEUS_WORK_DIR)
  if(NOT DEFINED ${required})
    message(FATAL_ERROR "${required} is required")
  endif()
endforeach()

file(REMOVE_RECURSE "${MORPHEUS_WORK_DIR}")
file(MAKE_DIRECTORY "${MORPHEUS_WORK_DIR}/greek"
                    "${MORPHEUS_WORK_DIR}/latin"
                    "${MORPHEUS_WORK_DIR}/combined")

foreach(language IN ITEMS greek latin)
  string(TOUPPER "${language}" language_upper)
  execute_process(
    COMMAND "${CMAKE_COMMAND}" -E tar xzf "${MORPHEUS_${language_upper}_ARCHIVE}"
    WORKING_DIRECTORY "${MORPHEUS_WORK_DIR}/${language}"
    RESULT_VARIABLE extract_result
    ERROR_VARIABLE extract_error
  )
  if(NOT extract_result EQUAL 0)
    message(FATAL_ERROR "${language} runtime artifact extraction failed:\n${extract_error}")
  endif()
endforeach()

file(COPY "${MORPHEUS_WORK_DIR}/greek/morpheus-stemlib-greek/Greek"
     DESTINATION "${MORPHEUS_WORK_DIR}/combined")
file(COPY "${MORPHEUS_WORK_DIR}/latin/morpheus-stemlib-latin/Latin"
     DESTINATION "${MORPHEUS_WORK_DIR}/combined")

execute_process(
  COMMAND "${CMAKE_COMMAND}"
          "-DMORPHEUS_FIXTURES=${MORPHEUS_FIXTURES}"
          "-DMORPHEUS_CRUNCHER=${MORPHEUS_CRUNCHER}"
          "-DMORPHEUS_STEMLIB=${MORPHEUS_WORK_DIR}/combined"
          "-DMORPHEUS_WORK_DIR=${MORPHEUS_WORK_DIR}/fixtures"
          -P "${MORPHEUS_FIXTURE_RUNNER}"
  RESULT_VARIABLE fixture_result
  OUTPUT_VARIABLE fixture_output
  ERROR_VARIABLE fixture_error
)
if(NOT fixture_result EQUAL 0)
  message(FATAL_ERROR "runtime artifact fixtures failed:\n${fixture_output}${fixture_error}")
endif()
file(READ "${MORPHEUS_FIXTURES}" fixtures_json)
string(JSON fixture_count LENGTH "${fixtures_json}")
file(WRITE "${MORPHEUS_WORK_DIR}/MORPHEUS-STEMLIB-RUNTIME-SMOKE.json"
     "{\n"
     "  \"fixtures\": ${fixture_count},\n"
     "  \"languages\": [\"Greek\", \"Latin\"],\n"
     "  \"schema\": 1,\n"
     "  \"status\": \"passed\"\n"
     "}\n")
message(STATUS "Qualified both internal runtime artifacts against the fixture suite")
