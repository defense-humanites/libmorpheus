# SPDX-License-Identifier: AGPL-3.0-or-later

cmake_minimum_required(VERSION 3.25)

foreach(required IN ITEMS MORPHEUS_STEMLIB_ROOT MORPHEUS_STEMLIB_MANIFEST
                          MORPHEUS_STEMLIB_BINARY_EXCEPTIONS
                          MORPHEUS_STEMLIB_MANIFEST_VALIDATOR
                          MORPHEUS_STEMLIB_STAGER MORPHEUS_STEMLIB_BUILDER
                          MORPHEUS_BUILDEND MORPHEUS_BUILDDERIV
                          MORPHEUS_INDENDTABLES MORPHEUS_INDDERIVTABLES
                          MORPHEUS_SOURCE_REVISION MORPHEUS_C_COMPILER
                          MORPHEUS_C_COMPILER_ID MORPHEUS_C_COMPILER_VERSION
                          MORPHEUS_SYSTEM_NAME MORPHEUS_SYSTEM_PROCESSOR
                          MORPHEUS_WORK_DIR)
  if(NOT DEFINED ${required})
    message(FATAL_ERROR "${required} is required")
  endif()
endforeach()

file(REMOVE_RECURSE "${MORPHEUS_WORK_DIR}")
file(MAKE_DIRECTORY "${MORPHEUS_WORK_DIR}")

set(invalid_provenance_stage "${MORPHEUS_WORK_DIR}/invalid-provenance")
execute_process(
  COMMAND "${CMAKE_COMMAND}"
          -DMORPHEUS_STEMLIB_ROOT=${MORPHEUS_STEMLIB_ROOT}
          -DMORPHEUS_STEMLIB_MANIFEST=${MORPHEUS_STEMLIB_MANIFEST}
          -DMORPHEUS_STEMLIB_MANIFEST_VALIDATOR=${MORPHEUS_STEMLIB_MANIFEST_VALIDATOR}
          -DMORPHEUS_STEMLIB_STAGER=${MORPHEUS_STEMLIB_STAGER}
          -DMORPHEUS_STEMLIB_LANGUAGE=Greek
          -DMORPHEUS_STEMLIB_STAGE=${invalid_provenance_stage}
          -DMORPHEUS_BUILDEND=${MORPHEUS_BUILDEND}
          -DMORPHEUS_BUILDDERIV=${MORPHEUS_BUILDDERIV}
          -DMORPHEUS_INDENDTABLES=${MORPHEUS_INDENDTABLES}
          -DMORPHEUS_INDDERIVTABLES=${MORPHEUS_INDDERIVTABLES}
          -DMORPHEUS_SOURCE_REVISION=invalid
          -DMORPHEUS_C_COMPILER=${MORPHEUS_C_COMPILER}
          -DMORPHEUS_C_COMPILER_ID=${MORPHEUS_C_COMPILER_ID}
          -DMORPHEUS_C_COMPILER_VERSION=${MORPHEUS_C_COMPILER_VERSION}
          -DMORPHEUS_SYSTEM_NAME=${MORPHEUS_SYSTEM_NAME}
          -DMORPHEUS_SYSTEM_PROCESSOR=${MORPHEUS_SYSTEM_PROCESSOR}
          -P "${MORPHEUS_STEMLIB_BUILDER}"
  RESULT_VARIABLE invalid_provenance_result
  OUTPUT_QUIET
  ERROR_QUIET
)
if(invalid_provenance_result EQUAL 0)
  message(FATAL_ERROR "invalid source revision was accepted")
endif()
if(EXISTS "${invalid_provenance_stage}")
  message(FATAL_ERROR "invalid provenance created a staging tree")
endif()

function(build_and_validate language pass expected_outputs)
  set(stage "${MORPHEUS_WORK_DIR}/${language}-${pass}")
  execute_process(
    COMMAND "${CMAKE_COMMAND}"
            -DMORPHEUS_STEMLIB_ROOT=${MORPHEUS_STEMLIB_ROOT}
            -DMORPHEUS_STEMLIB_MANIFEST=${MORPHEUS_STEMLIB_MANIFEST}
            -DMORPHEUS_STEMLIB_MANIFEST_VALIDATOR=${MORPHEUS_STEMLIB_MANIFEST_VALIDATOR}
            -DMORPHEUS_STEMLIB_STAGER=${MORPHEUS_STEMLIB_STAGER}
            -DMORPHEUS_STEMLIB_LANGUAGE=${language}
            -DMORPHEUS_STEMLIB_STAGE=${stage}
            -DMORPHEUS_BUILDEND=${MORPHEUS_BUILDEND}
            -DMORPHEUS_BUILDDERIV=${MORPHEUS_BUILDDERIV}
            -DMORPHEUS_INDENDTABLES=${MORPHEUS_INDENDTABLES}
            -DMORPHEUS_INDDERIVTABLES=${MORPHEUS_INDDERIVTABLES}
            -DMORPHEUS_SOURCE_REVISION=${MORPHEUS_SOURCE_REVISION}
            -DMORPHEUS_C_COMPILER=${MORPHEUS_C_COMPILER}
            -DMORPHEUS_C_COMPILER_ID=${MORPHEUS_C_COMPILER_ID}
            -DMORPHEUS_C_COMPILER_VERSION=${MORPHEUS_C_COMPILER_VERSION}
            -DMORPHEUS_SYSTEM_NAME=${MORPHEUS_SYSTEM_NAME}
            -DMORPHEUS_SYSTEM_PROCESSOR=${MORPHEUS_SYSTEM_PROCESSOR}
            -P "${MORPHEUS_STEMLIB_BUILDER}"
    RESULT_VARIABLE build_result
    OUTPUT_VARIABLE build_output
    ERROR_VARIABLE build_error
  )
  if(NOT build_result EQUAL 0)
    message(FATAL_ERROR
            "${language} table build failed:\n${build_output}${build_error}")
  endif()

  set(receipt "${stage}/MORPHEUS-STEMLIB-TABLE-OUTPUTS.tsv")
  if(NOT EXISTS "${receipt}")
    message(FATAL_ERROR "${language} table build produced no receipt")
  endif()
  file(STRINGS "${receipt}" receipt_lines)
  set(output_count 0)
  foreach(line IN LISTS receipt_lines)
    if(line MATCHES "^[ \t]*#" OR line MATCHES "^[ \t]*$")
      continue()
    endif()
    string(REPLACE "\t" ";" fields "${line}")
    list(LENGTH fields field_count)
    if(NOT field_count EQUAL 2)
      message(FATAL_ERROR "invalid table-output receipt line: ${line}")
    endif()
    list(GET fields 0 relative_path)
    list(GET fields 1 expected_sha256)
    set(output "${stage}/${relative_path}")
    if(NOT EXISTS "${output}")
      message(FATAL_ERROR "received table output is missing: ${relative_path}")
    endif()
    file(SHA256 "${output}" actual_sha256)
    if(NOT actual_sha256 STREQUAL expected_sha256)
      message(FATAL_ERROR "received table output changed: ${relative_path}")
    endif()
    math(EXPR output_count "${output_count} + 1")
  endforeach()
  if(NOT output_count EQUAL expected_outputs)
    message(FATAL_ERROR
            "unexpected ${language} table-output count: ${output_count}")
  endif()
  set(${language}_${pass}_stage "${stage}" PARENT_SCOPE)
endfunction()

function(compare_builds language)
  set(first "${${language}_first_stage}")
  set(second "${${language}_second_stage}")
  set(receipt_name "MORPHEUS-STEMLIB-TABLE-OUTPUTS.tsv")
  execute_process(
    COMMAND "${CMAKE_COMMAND}" -E compare_files
            "${first}/${receipt_name}" "${second}/${receipt_name}"
    RESULT_VARIABLE receipt_compare_result
  )
  if(NOT receipt_compare_result EQUAL 0)
    message(FATAL_ERROR "${language} table-output receipts differ")
  endif()
  execute_process(
    COMMAND "${CMAKE_COMMAND}" -E compare_files
            "${first}/MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv"
            "${second}/MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv"
    RESULT_VARIABLE provenance_compare_result
  )
  if(NOT provenance_compare_result EQUAL 0)
    message(FATAL_ERROR "${language} table provenance differs")
  endif()
  file(SHA256 "${MORPHEUS_C_COMPILER}" compiler_sha256)
  get_filename_component(compiler_name "${MORPHEUS_C_COMPILER}" NAME)
  file(STRINGS "${first}/MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv"
       provenance_lines)
  foreach(expected_line IN ITEMS
      "schema\t2"
      "source_revision\t${MORPHEUS_SOURCE_REVISION}"
      "compiler_name\t${compiler_name}"
      "compiler_id\t${MORPHEUS_C_COMPILER_ID}"
      "compiler_version\t${MORPHEUS_C_COMPILER_VERSION}"
      "compiler_sha256\t${compiler_sha256}"
      "system_name\t${MORPHEUS_SYSTEM_NAME}"
      "system_processor\t${MORPHEUS_SYSTEM_PROCESSOR}")
    list(FIND provenance_lines "${expected_line}" expected_index)
    if(expected_index EQUAL -1)
      message(FATAL_ERROR "missing table provenance: ${expected_line}")
    endif()
  endforeach()

  file(STRINGS "${first}/${receipt_name}" receipt_lines)
  set(binary_baseline_differences)
  set(text_baseline_differences)
  foreach(line IN LISTS receipt_lines)
    if(line MATCHES "^[ \t]*#" OR line MATCHES "^[ \t]*$")
      continue()
    endif()
    string(REPLACE "\t" ";" fields "${line}")
    list(GET fields 0 relative_path)
    execute_process(
      COMMAND "${CMAKE_COMMAND}" -E compare_files
              "${first}/${relative_path}" "${second}/${relative_path}"
      RESULT_VARIABLE clean_compare_result
    )
    if(NOT clean_compare_result EQUAL 0)
      message(FATAL_ERROR
              "${language} clean builds differ: ${relative_path}")
    endif()
    execute_process(
      COMMAND "${CMAKE_COMMAND}" -E compare_files
              "${first}/${relative_path}"
              "${MORPHEUS_STEMLIB_ROOT}/${relative_path}"
      RESULT_VARIABLE baseline_compare_result
    )
    if(NOT baseline_compare_result EQUAL 0)
      if(relative_path MATCHES
         "^${language}/(endtables|derivs)/out/[A-Za-z0-9_]+[.]out$")
        list(APPEND binary_baseline_differences "${relative_path}")
      else()
        list(APPEND text_baseline_differences "${relative_path}")
      endif()
    endif()
  endforeach()
  if(text_baseline_differences)
    list(LENGTH text_baseline_differences difference_count)
    list(JOIN text_baseline_differences "\n  " difference_list)
    message(FATAL_ERROR
            "${language} differs from ${difference_count} textual or index baselines:\n  ${difference_list}")
  endif()
  list(LENGTH binary_baseline_differences binary_difference_count)
  message(STATUS
          "${language} binary baseline differences: ${binary_difference_count}")

  file(STRINGS "${MORPHEUS_STEMLIB_BINARY_EXCEPTIONS}" exception_lines)
  set(expected_binary_differences)
  set(seen_exception_paths)
  set(previous_exception_path)
  foreach(line IN LISTS exception_lines)
    if(line MATCHES "^[ \t]*#" OR line MATCHES "^[ \t]*$")
      continue()
    endif()
    string(REPLACE "\t" ";" fields "${line}")
    list(LENGTH fields field_count)
    if(NOT field_count EQUAL 2)
      message(FATAL_ERROR "invalid binary baseline exception line: ${line}")
    endif()
    list(GET fields 0 exception_path)
    list(GET fields 1 exception_reason)
    if(NOT exception_path MATCHES
       "^(Greek|Latin)/(endtables|derivs)/out/[A-Za-z0-9_]+[.]out$")
      message(FATAL_ERROR
              "invalid binary baseline exception path: ${exception_path}")
    endif()
    if(NOT exception_reason STREQUAL "explicit-binary-serialization")
      message(FATAL_ERROR
              "invalid binary baseline exception reason: ${exception_reason}")
    endif()
    list(FIND seen_exception_paths "${exception_path}" duplicate_index)
    if(NOT duplicate_index EQUAL -1)
      message(FATAL_ERROR
              "duplicate binary baseline exception: ${exception_path}")
    endif()
    if(previous_exception_path)
      if(NOT "${previous_exception_path}" STRLESS "${exception_path}")
        message(FATAL_ERROR "binary baseline exceptions are not sorted")
      endif()
    endif()
    list(APPEND seen_exception_paths "${exception_path}")
    set(previous_exception_path "${exception_path}")
    if(exception_path MATCHES "^${language}/")
      list(APPEND expected_binary_differences "${exception_path}")
    endif()
  endforeach()

  if(NOT "${binary_baseline_differences}" STREQUAL
         "${expected_binary_differences}")
    set(missing_exceptions ${expected_binary_differences})
    set(unexpected_differences ${binary_baseline_differences})
    foreach(path IN LISTS binary_baseline_differences)
      list(REMOVE_ITEM missing_exceptions "${path}")
    endforeach()
    foreach(path IN LISTS expected_binary_differences)
      list(REMOVE_ITEM unexpected_differences "${path}")
    endforeach()
    list(JOIN missing_exceptions ", " missing_list)
    list(JOIN unexpected_differences ", " unexpected_list)
    message(FATAL_ERROR
            "${language} binary baseline exception manifest differs; "
            "missing differences: [${missing_list}]; "
            "unexpected differences: [${unexpected_list}]")
  endif()
  set(${language}_binary_difference_count "${binary_difference_count}"
      PARENT_SCOPE)
  set(difference_rows)
  foreach(relative_path IN LISTS binary_baseline_differences)
    string(APPEND difference_rows
           "${relative_path}\texplicit-binary-serialization\n")
  endforeach()
  set(${language}_binary_difference_rows "${difference_rows}" PARENT_SCOPE)
endfunction()

build_and_validate(Greek first 357)
build_and_validate(Greek second 357)
build_and_validate(Latin first 211)
build_and_validate(Latin second 211)
compare_builds(Greek)
compare_builds(Latin)
file(WRITE "${MORPHEUS_WORK_DIR}/baseline-summary.tsv"
     "language\toutputs\tbinary_differences\ttext_or_index_differences\n"
     "Greek\t357\t${Greek_binary_difference_count}\t0\n"
     "Latin\t211\t${Latin_binary_difference_count}\t0\n")
file(WRITE "${MORPHEUS_WORK_DIR}/baseline-differences.tsv"
     "path\treason\n"
     "${Greek_binary_difference_rows}${Latin_binary_difference_rows}")
