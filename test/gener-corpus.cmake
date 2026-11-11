# SPDX-License-Identifier: AGPL-3.0-or-later
# MORPHEUS_TEST_LAUNCHER is empty for native builds; cross builds (Emscripten)
# pass the emulator that runs the compiled programs.

foreach(required IN ITEMS MORPHEUS_GENER_SOURCE_PREPARER
                          MORPHEUS_GENER_INDEX_BUILDER
                          MORPHEUS_GENER_INDEX_READER_TEST
                          MORPHEUS_GENER_CORPUS_ROOT
                          MORPHEUS_GENER_CORPUS_MANIFEST
                          MORPHEUS_GENER_CORPUS_EXCEPTIONS
                          MORPHEUS_GENER_CORPUS_PATCHES
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
            --patches "${MORPHEUS_GENER_CORPUS_PATCHES}"
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
   "ee399e9f3af34be6f9c3961041f54734e77042fdeffbde717942d04c1e72d016")
  message(FATAL_ERROR "complete prepared corpus changed: ${source_sha256}")
endif()
if(NOT index_sha256 STREQUAL
   "e04d4a7d6457cd4dd6044621197006400f425717541d9466e3e4e6cf0468fa2f")
  message(FATAL_ERROR "complete generation index changed: ${index_sha256}")
endif()

# Without default principal parts and data patches, the preparer still
# reproduces the index of data 0.1.0 and native 0.4.6, the historical do_conj
# "full" expansion.
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
          "${first_index}" 106428 108221 172766
  RESULT_VARIABLE reader_result
  OUTPUT_VARIABLE reader_output
  ERROR_VARIABLE reader_error
)
if(NOT reader_result EQUAL 0)
  message(FATAL_ERROR
    "complete generation-index reader failed (${reader_result}):\n"
    "${reader_output}${reader_error}")
endif()

# Frequent verbs, primary and regular. The default principal parts must
# leave the primary and suppletive stems as their sources give them, and add
# to the regular derivations exactly the records listed here; e)/xw receives
# the present its patched derivation restores (reviewed by hand; the
# historical blocks come from the same sources, unpatched).
function(collect_lemma_blocks content lemma result)
  set(blocks "")
  set(rest "${content}")
  foreach(guard RANGE 10000)
    string(FIND "${rest}" "\n:le:${lemma}\n" start)
    if(start EQUAL -1)
      break()
    endif()
    math(EXPR start "${start} + 1")
    string(SUBSTRING "${rest}" ${start} -1 rest)
    string(SUBSTRING "${rest}" 1 -1 tail)
    string(FIND "${tail}" "\n:le:" stop)
    if(stop EQUAL -1)
      set(block "${rest}")
      set(rest "")
    else()
      math(EXPR stop "${stop} + 2")
      string(SUBSTRING "${rest}" 0 ${stop} block)
      string(SUBSTRING "${rest}" ${stop} -1 rest)
      set(rest "\n${rest}")
    endif()
    string(APPEND blocks "${block}")
  endforeach()
  set(${result} "${blocks}" PARENT_SCOPE)
endfunction()

file(READ "${first_source}" prepared)
file(READ "${historical_source}" historical)
set(prepared "\n${prepared}")
set(historical "\n${historical}")
foreach(verb IN ITEMS
        "pa/sxw" "pi/ptw" "o(ra/w" "me/nw" "i(/sthmi" "bou/lomai"
        "lu/w" "a)kou/w")
  collect_lemma_blocks("${prepared}" "${verb}" current)
  collect_lemma_blocks("${historical}" "${verb}" earlier)
  if(current STREQUAL "" OR NOT current STREQUAL earlier)
    message(FATAL_ERROR "default principal parts changed the blocks of ${verb}")
  endif()
endforeach()

# Each entry: the verb, then the records the defaults or patches add to it.
set(regular_verbs "poie/w" "dhlo/w" "a)gge/llw" "a)gapa/w" "e)/xw")
set(regular_0
    ":vs:pohs  aor1 ew_denom poetic"
    ":vs:poihs  aor1 ew_denom")
set(regular_1
    ":vs:dhlws  aor1 ow_denom"
    ":vs:dedhlwk  perf_act ow_denom"
    ":vs:dedhlw  perfp_vow ow_denom"
    ":vs:dhlwq  aor_pass ow_denom")
set(regular_2
    ":vs:a)ggel  ew_fut ellw"
    ":vs:h)ggelk  perf_act ellw"
    ":vs:h)gge  perfp_l ellw")
set(regular_3
    ":vs:a)gap  aw_pr aw_denom"
    ":vs:a)gaphs  reg_fut aw_denom attic ionic"
    ":vs:a)gaphs  aor1 aw_denom attic ionic"
    ":vs:h)gaphk  perf_act aw_denom attic ionic"
    ":vs:h)gaph  perfp_vow aw_denom attic ionic"
    ":vs:a)gaphq  aor_pass aw_denom attic ionic")
set(regular_4
    ":vs:e)x  w_stem reg_conj syll_augment"
    ":vs:e)x  w_stem reg_conj imperf syll_augment"
    ":vs:e)x  w_stem reg_conj imperf ind act epic syll_augment unaugmented"
    ":vs:e)x  w_stem reg_conj imperf ind act ionic syll_augment iterative unaugmented")
foreach(position RANGE 4)
  list(GET regular_verbs ${position} verb)
  collect_lemma_blocks("${prepared}" "${verb}" current)
  collect_lemma_blocks("${historical}" "${verb}" earlier)
  string(REGEX MATCHALL "\n" current_lines "\n${current}")
  string(REGEX MATCHALL "\n" earlier_lines "\n${earlier}")
  list(LENGTH current_lines current_count)
  list(LENGTH earlier_lines earlier_count)
  list(LENGTH regular_${position} added_count)
  math(EXPR expected_count "${earlier_count} + ${added_count}")
  if(NOT current_count EQUAL expected_count)
    message(FATAL_ERROR
      "${verb}: ${current_count} prepared lines, expected ${expected_count}")
  endif()
  foreach(record IN LISTS regular_${position})
    string(FIND "${current}" "${record}\n" in_current)
    string(FIND "${earlier}" "${record}\n" in_earlier)
    if(in_current EQUAL -1 OR NOT in_earlier EQUAL -1)
      message(FATAL_ERROR "${verb}: expected the added record [${record}]")
    endif()
  endforeach()
endforeach()
