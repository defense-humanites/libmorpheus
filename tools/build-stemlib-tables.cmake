# SPDX-License-Identifier: AGPL-3.0-or-later

cmake_minimum_required(VERSION 3.25)

foreach(required IN ITEMS MORPHEUS_STEMLIB_ROOT MORPHEUS_STEMLIB_MANIFEST
                          MORPHEUS_STEMLIB_MANIFEST_VALIDATOR
                          MORPHEUS_STEMLIB_STAGER MORPHEUS_STEMLIB_LANGUAGE
                          MORPHEUS_STEMLIB_STAGE MORPHEUS_BUILDEND
                          MORPHEUS_BUILDDERIV MORPHEUS_INDENDTABLES
                          MORPHEUS_INDDERIVTABLES MORPHEUS_SOURCE_REVISION
                          MORPHEUS_C_COMPILER MORPHEUS_C_COMPILER_ID
                          MORPHEUS_C_COMPILER_VERSION MORPHEUS_SYSTEM_NAME
                          MORPHEUS_SYSTEM_PROCESSOR
                          MORPHEUS_QUALIFICATION_PROFILE
                          MORPHEUS_PRODUCTION_RECIPE)
  if(NOT DEFINED ${required})
    message(FATAL_ERROR "${required} is required")
  endif()
endforeach()
if(NOT MORPHEUS_STEMLIB_LANGUAGE MATCHES "^(Greek|Latin)$")
  message(FATAL_ERROR "MORPHEUS_STEMLIB_LANGUAGE must be Greek or Latin")
endif()

# Validate provenance before creating the staging tree.
if(NOT MORPHEUS_SOURCE_REVISION STREQUAL "unavailable")
  string(REGEX REPLACE "[+]dirty$" "" revision_base
         "${MORPHEUS_SOURCE_REVISION}")
  string(LENGTH "${revision_base}" revision_length)
  if(NOT revision_base MATCHES "^[0-9a-f]+$" OR
     NOT revision_length EQUAL 40 OR
     NOT MORPHEUS_SOURCE_REVISION MATCHES "^[0-9a-f]+([+]dirty)?$")
    message(FATAL_ERROR "invalid source revision")
  endif()
endif()
foreach(field IN ITEMS MORPHEUS_C_COMPILER_ID MORPHEUS_C_COMPILER_VERSION
                       MORPHEUS_SYSTEM_NAME MORPHEUS_SYSTEM_PROCESSOR
                       MORPHEUS_QUALIFICATION_PROFILE)
  if(NOT "${${field}}" MATCHES "^[A-Za-z0-9_.+-]+$")
    message(FATAL_ERROR "invalid provenance field: ${field}")
  endif()
endforeach()
get_filename_component(compiler_name "${MORPHEUS_C_COMPILER}" NAME)
if(NOT compiler_name MATCHES "^[A-Za-z0-9_.+-]+$")
  message(FATAL_ERROR "invalid compiler name")
endif()
file(SHA256 "${MORPHEUS_C_COMPILER}" compiler_sha256)

execute_process(
  COMMAND "${CMAKE_COMMAND}"
          -DMORPHEUS_STEMLIB_ROOT=${MORPHEUS_STEMLIB_ROOT}
          -DMORPHEUS_STEMLIB_MANIFEST=${MORPHEUS_STEMLIB_MANIFEST}
          -DMORPHEUS_STEMLIB_MANIFEST_VALIDATOR=${MORPHEUS_STEMLIB_MANIFEST_VALIDATOR}
          -DMORPHEUS_STEMLIB_LANGUAGE=${MORPHEUS_STEMLIB_LANGUAGE}
          -DMORPHEUS_STEMLIB_STAGE=${MORPHEUS_STEMLIB_STAGE}
          -P "${MORPHEUS_STEMLIB_STAGER}"
  RESULT_VARIABLE stage_result
  OUTPUT_VARIABLE stage_output
  ERROR_VARIABLE stage_error
)
if(NOT stage_result EQUAL 0)
  message(FATAL_ERROR "stemlib staging failed:\n${stage_output}${stage_error}")
endif()

set(stage_root "${MORPHEUS_STEMLIB_STAGE}")
set(language_root "${stage_root}/${MORPHEUS_STEMLIB_LANGUAGE}")
set(language_option)
if(MORPHEUS_STEMLIB_LANGUAGE STREQUAL "Latin")
  set(language_option -L)
endif()
set(build_environment
    "MORPHLIB=${stage_root}" "LC_ALL=C" "LANG=C" "TZ=UTC")

# Record the actual recipe, revision, toolchain and executables, including for
# failed production. This identifies build inputs; it is not a success receipt.
set(provenance "# SPDX-License-Identifier: MPL-2.0\n# key\tvalue\n")
string(APPEND provenance
       "schema\t4\n"
       "execution_model\tsingle-pass-explicit-dag\n"
       "qualification_profile\t${MORPHEUS_QUALIFICATION_PROFILE}\n"
       "source_revision\t${MORPHEUS_SOURCE_REVISION}\n"
       "compiler_name\t${compiler_name}\n"
       "compiler_id\t${MORPHEUS_C_COMPILER_ID}\n"
       "compiler_version\t${MORPHEUS_C_COMPILER_VERSION}\n"
       "compiler_sha256\t${compiler_sha256}\n"
       "system_name\t${MORPHEUS_SYSTEM_NAME}\n"
       "system_processor\t${MORPHEUS_SYSTEM_PROCESSOR}\n")
foreach(component IN ITEMS MORPHEUS_STEMLIB_MANIFEST
                           MORPHEUS_STEMLIB_MANIFEST_VALIDATOR
                           MORPHEUS_STEMLIB_STAGER MORPHEUS_PRODUCTION_RECIPE
                           MORPHEUS_BUILDEND
                           MORPHEUS_BUILDDERIV MORPHEUS_INDENDTABLES
                           MORPHEUS_INDDERIVTABLES CMAKE_COMMAND)
  file(SHA256 "${${component}}" component_sha256)
  string(APPEND provenance "${component}\t${component_sha256}\n")
endforeach()
file(SHA256 "${CMAKE_CURRENT_LIST_FILE}" recipe_sha256)
string(APPEND provenance "recipe\t${recipe_sha256}\n")
file(WRITE "${stage_root}/MORPHEUS-STEMLIB-TABLE-PROVENANCE.tsv" "${provenance}")

set(producer_labels)
function(run_producer label program)
  list(FIND producer_labels "${label}" producer_label_index)
  if(NOT producer_label_index EQUAL -1)
    message(FATAL_ERROR "table producer invoked twice: ${label}")
  endif()
  list(APPEND producer_labels "${label}")
  set(producer_labels "${producer_labels}" PARENT_SCOPE)
  execute_process(
    COMMAND "${CMAKE_COMMAND}" -E env ${build_environment}
            "${program}" ${ARGN}
    WORKING_DIRECTORY "${language_root}"
    RESULT_VARIABLE producer_result
    OUTPUT_VARIABLE producer_output
    ERROR_VARIABLE producer_error
  )
  if(NOT producer_result EQUAL 0)
    message(FATAL_ERROR
            "${label} failed:\n${producer_output}${producer_error}")
  endif()
endfunction()

file(STRINGS "${stage_root}/ending-tables.list" ending_tables)
foreach(table IN LISTS ending_tables)
  run_producer("ending table ${table}" "${MORPHEUS_BUILDEND}"
               ${language_option} "${table}")
endforeach()

file(STRINGS "${stage_root}/derivation-tables.list" derivation_tables)
foreach(table IN LISTS derivation_tables)
  run_producer("derivation table ${table}" "${MORPHEUS_BUILDDERIV}"
               ${language_option} "${table}")
endforeach()

run_producer("nominal ending index" "${MORPHEUS_INDENDTABLES}"
             ${language_option} -f "${stage_root}/ending-tables.list" nom)
run_producer("verb ending index" "${MORPHEUS_INDENDTABLES}"
             ${language_option} -f "${stage_root}/ending-tables.list" verb)
run_producer("derivation index" "${MORPHEUS_INDDERIVTABLES}"
             ${language_option} -f
             "${stage_root}/derivation-index-tables.list")

file(GLOB_RECURSE outputs
     RELATIVE "${stage_root}"
     "${language_root}/endtables/ascii/*.asc"
     "${language_root}/endtables/out/*.out"
     "${language_root}/endtables/indices/*"
     "${language_root}/derivs/ascii/*.asc"
     "${language_root}/derivs/out/*.out"
     "${language_root}/derivs/indices/*")
list(SORT outputs)
set(receipt "# SPDX-License-Identifier: MPL-2.0\n")
set(receipt "${receipt}# path\tsha256\n")
foreach(relative_path IN LISTS outputs)
  file(SHA256 "${stage_root}/${relative_path}" output_sha256)
  string(APPEND receipt "${relative_path}\t${output_sha256}\n")
endforeach()
file(WRITE "${stage_root}/MORPHEUS-STEMLIB-TABLE-OUTPUTS.tsv" "${receipt}")
