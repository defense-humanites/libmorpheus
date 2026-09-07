# SPDX-License-Identifier: AGPL-3.0-or-later

foreach(required IN ITEMS MORPHEUS_BUILDEND MORPHEUS_BUILDDERIV
                          MORPHEUS_INDENDTABLES MORPHEUS_INDDERIVTABLES
                          MORPHEUS_STEMLIB_ROOT MORPHEUS_WORK_DIR)
  if(NOT DEFINED ${required})
    message(FATAL_ERROR "${required} is required")
  endif()
endforeach()

file(REMOVE_RECURSE "${MORPHEUS_WORK_DIR}")
set(empty_root "${MORPHEUS_WORK_DIR}/empty")
set(partial_root "${MORPHEUS_WORK_DIR}/partial")
file(MAKE_DIRECTORY "${empty_root}/Greek")
file(MAKE_DIRECTORY
     "${partial_root}/Greek/endtables/source"
     "${partial_root}/Greek/endtables/ascii"
     "${partial_root}/Greek/endtables/out"
     "${partial_root}/Greek/endtables/indices"
     "${partial_root}/Greek/derivs/out"
     "${partial_root}/Greek/derivs/indices")
file(COPY "${MORPHEUS_STEMLIB_ROOT}/Greek/rule_files"
     DESTINATION "${partial_root}/Greek")
file(COPY "${MORPHEUS_STEMLIB_ROOT}/Greek/endtables/source/h_hs.end"
     DESTINATION "${partial_root}/Greek/endtables/source")
file(WRITE "${partial_root}/ending-valid.list" "a_hs\n")
file(WRITE "${partial_root}/ending-invalid.list" "../escape\n")

function(expect_failure label root program)
  execute_process(
    COMMAND "${CMAKE_COMMAND}" -E env "MORPHLIB=${root}"
            "${program}" ${ARGN}
    RESULT_VARIABLE result
    OUTPUT_QUIET
    ERROR_QUIET
  )
  if(result EQUAL 0)
    message(FATAL_ERROR "${label} unexpectedly succeeded")
  endif()
endfunction()

expect_failure("buildend without stem-type registry"
               "${empty_root}" "${MORPHEUS_BUILDEND}" nom)
expect_failure("buildderiv without derivation registry"
               "${empty_root}" "${MORPHEUS_BUILDDERIV}" all)
expect_failure("buildend with missing ending macro"
               "${partial_root}" "${MORPHEUS_BUILDEND}" h_hs)
expect_failure("ending index with missing compiled tables"
               "${partial_root}" "${MORPHEUS_INDENDTABLES}" nom)
expect_failure("listed ending index with missing compiled table"
               "${partial_root}" "${MORPHEUS_INDENDTABLES}"
               -f "${partial_root}/ending-valid.list" nom)
expect_failure("ending index with unsafe table list"
               "${partial_root}" "${MORPHEUS_INDENDTABLES}"
               -f "${partial_root}/ending-invalid.list" nom)
expect_failure("derivation index with missing compiled tables"
               "${partial_root}" "${MORPHEUS_INDDERIVTABLES}")

if(EXISTS "${partial_root}/Greek/endtables/indices/nendind" OR
   EXISTS "${partial_root}/Greek/endtables/indices/nendind.tmp" OR
   EXISTS "${partial_root}/Greek/derivs/indices/derivind" OR
   EXISTS "${partial_root}/Greek/derivs/indices/derivind.tmp")
  message(FATAL_ERROR "a failed index operation left a partial index")
endif()

# These committed sources lack registry entries as well as compiled baselines.
# Their mere presence must not let the producers report a successful build.
file(COPY "${MORPHEUS_STEMLIB_ROOT}/Greek/endtables/basics"
     DESTINATION "${partial_root}/Greek/endtables")
file(MAKE_DIRECTORY "${partial_root}/Greek/derivs/source"
                    "${partial_root}/Greek/derivs/ascii")
foreach(kind IN ITEMS ending derivation)
  if(kind STREQUAL "ending")
    set(tables conj3 conj3io conj4 is_ios us_uos2 verb_adj vh_vhs)
    set(directory endtables)
    set(extension end)
    set(program "${MORPHEUS_BUILDEND}")
  else()
    set(tables cw es_denom ow_fact ow_instr ww)
    set(directory derivs)
    set(extension deriv)
    set(program "${MORPHEUS_BUILDDERIV}")
  endif()
  foreach(table IN LISTS tables)
    file(COPY "${MORPHEUS_STEMLIB_ROOT}/Greek/${directory}/source/${table}.${extension}"
         DESTINATION "${partial_root}/Greek/${directory}/source")
    foreach(pass IN ITEMS absent existing)
      set(binary "${partial_root}/Greek/${directory}/out/${table}.out")
      set(ascii "${partial_root}/Greek/${directory}/ascii/${table}.asc")
      if(pass STREQUAL "existing")
        file(WRITE "${binary}" "sentinel")
        file(WRITE "${ascii}" "sentinel")
      endif()
      execute_process(
        COMMAND "${CMAKE_COMMAND}" -E env "MORPHLIB=${partial_root}"
                "${program}" "${table}"
        WORKING_DIRECTORY "${partial_root}/Greek"
        RESULT_VARIABLE result OUTPUT_QUIET ERROR_VARIABLE diagnostic)
      if(result EQUAL 0 OR NOT diagnostic MATCHES "unregistered ${kind} table: ${table}")
        message(FATAL_ERROR "${table} was not rejected as unregistered: ${diagnostic}")
      endif()
      foreach(output IN ITEMS "${binary}" "${ascii}")
        if(pass STREQUAL "absent")
          if(EXISTS "${output}")
            message(FATAL_ERROR "unregistered table produced ${output}")
          endif()
        else()
          file(READ "${output}" contents)
          if(NOT contents STREQUAL "sentinel")
            message(FATAL_ERROR "unregistered table overwrote ${output}")
          endif()
        endif()
      endforeach()
    endforeach()
  endforeach()
endforeach()
