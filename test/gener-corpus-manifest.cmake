# SPDX-License-Identifier: AGPL-3.0-or-later

foreach(required IN ITEMS MORPHEUS_GENER_CORPUS_ROOT
                          MORPHEUS_GENER_CORPUS_MANIFEST
                          MORPHEUS_GENER_CORPUS_EXCEPTIONS
                          MORPHEUS_GENER_CORPUS_PATCHES
                          MORPHEUS_GENER_DATA_MANIFEST)
  if(NOT DEFINED ${required})
    message(FATAL_ERROR "${required} is required")
  endif()
endforeach()

if(NOT IS_DIRECTORY "${MORPHEUS_GENER_CORPUS_ROOT}/stemsrc")
  message(FATAL_ERROR
    "Greek stem source directory is missing: ${MORPHEUS_GENER_CORPUS_ROOT}/stemsrc")
endif()

file(STRINGS "${MORPHEUS_GENER_CORPUS_MANIFEST}" manifest_lines)
set(manifest_nominal)
set(manifest_verbs)
set(manifest_paths)

foreach(line IN LISTS manifest_lines)
  if(line STREQUAL "" OR line MATCHES "^#")
    continue()
  endif()
  string(REPLACE "\t" ";" fields "${line}")
  list(LENGTH fields field_count)
  if(NOT field_count EQUAL 3)
    message(FATAL_ERROR "invalid generation-corpus manifest line: ${line}")
  endif()
  list(GET fields 0 group)
  list(GET fields 1 expected_sha256)
  list(GET fields 2 relative_path)
  if(NOT group STREQUAL "nominal" AND NOT group STREQUAL "verb")
    message(FATAL_ERROR "invalid generation-corpus group: ${group}")
  endif()
  string(LENGTH "${expected_sha256}" sha256_length)
  if(NOT sha256_length EQUAL 64 OR
     NOT expected_sha256 MATCHES "^[0-9a-f]+$")
    message(FATAL_ERROR "invalid SHA-256 for ${relative_path}")
  endif()
  if(NOT relative_path MATCHES "^stemsrc/[A-Za-z0-9._-]+$")
    message(FATAL_ERROR "unsafe generation-corpus path: ${relative_path}")
  endif()
  list(FIND manifest_paths "${relative_path}" duplicate_at)
  if(NOT duplicate_at EQUAL -1)
    message(FATAL_ERROR "duplicate generation-corpus path: ${relative_path}")
  endif()
  set(absolute_path "${MORPHEUS_GENER_CORPUS_ROOT}/${relative_path}")
  if(NOT EXISTS "${absolute_path}")
    message(FATAL_ERROR "generation-corpus input is missing: ${relative_path}")
  endif()
  file(SHA256 "${absolute_path}" actual_sha256)
  if(NOT actual_sha256 STREQUAL expected_sha256)
    message(FATAL_ERROR
      "generation-corpus checksum mismatch for ${relative_path}: ${actual_sha256}")
  endif()
  list(APPEND manifest_paths "${relative_path}")
  if(group STREQUAL "nominal")
    list(APPEND manifest_nominal "${relative_path}")
  else()
    list(APPEND manifest_verbs "${relative_path}")
  endif()
endforeach()

file(GLOB nominal_files
  RELATIVE "${MORPHEUS_GENER_CORPUS_ROOT}"
  "${MORPHEUS_GENER_CORPUS_ROOT}/stemsrc/nom.*"
  "${MORPHEUS_GENER_CORPUS_ROOT}/stemsrc/nom[0-9]*"
)
list(FILTER nominal_files EXCLUDE REGEX "~$")
list(APPEND nominal_files stemsrc/lsj.nom stemsrc/lsj.byhand)
set(verb_files
  stemsrc/vbs.irreg
  stemsrc/vbs.simp.ml
  stemsrc/vbs.simp.02.new
  stemsrc/lsj.vbs
)

if(NOT "${manifest_nominal}" STREQUAL "${nominal_files}")
  message(FATAL_ERROR
    "nominal generation-corpus manifest no longer matches the historical build order")
endif()
if(NOT "${manifest_verbs}" STREQUAL "${verb_files}")
  message(FATAL_ERROR
    "verb generation-corpus manifest no longer matches the historical build order")
endif()

list(LENGTH manifest_nominal nominal_count)
list(LENGTH manifest_verbs verb_count)
if(NOT nominal_count EQUAL 45 OR NOT verb_count EQUAL 4)
  message(FATAL_ERROR
    "unexpected generation-corpus size: ${nominal_count} nominal, ${verb_count} verb")
endif()

file(STRINGS "${MORPHEUS_GENER_CORPUS_EXCEPTIONS}" exception_lines)
set(exception_locations)
set(previous_exception_path "")
set(previous_exception_line 0)
set(invalid_derivation_count 0)
set(invalid_record_count 0)
set(orphan_continuation_count 0)
set(orphan_request_count 0)
set(zero_continuation_count 0)
set(zero_request_count 0)

foreach(line IN LISTS exception_lines)
  if(line STREQUAL "" OR line MATCHES "^#")
    continue()
  endif()
  string(REPLACE "\t" ";" fields "${line}")
  list(LENGTH fields field_count)
  if(NOT field_count EQUAL 4)
    message(FATAL_ERROR "invalid generation-corpus exception line: ${line}")
  endif()
  list(GET fields 0 category)
  list(GET fields 1 relative_path)
  list(GET fields 2 source_line)
  list(GET fields 3 source_sha256)
  if(NOT category MATCHES
     "^(invalid_derivation|invalid_record|orphan_continuation|orphan_request|zero_continuation|zero_request)$")
    message(FATAL_ERROR "invalid generation-corpus exception category: ${category}")
  endif()
  list(FIND manifest_paths "${relative_path}" manifest_at)
  if(manifest_at EQUAL -1)
    message(FATAL_ERROR
      "generation-corpus exception references an unselected file: ${relative_path}")
  endif()
  if(NOT source_line MATCHES "^[1-9][0-9]*$")
    message(FATAL_ERROR
      "invalid generation-corpus exception line number: ${source_line}")
  endif()
  string(LENGTH "${source_sha256}" sha256_length)
  if(NOT sha256_length EQUAL 64 OR NOT source_sha256 MATCHES "^[0-9a-f]+$")
    message(FATAL_ERROR
      "invalid generation-corpus exception SHA-256: ${relative_path}:${source_line}")
  endif()
  set(location "${relative_path}:${source_line}")
  list(FIND exception_locations "${location}" duplicate_at)
  if(NOT duplicate_at EQUAL -1)
    message(FATAL_ERROR "duplicate generation-corpus exception: ${location}")
  endif()
  if(relative_path STRLESS previous_exception_path OR
     (relative_path STREQUAL previous_exception_path AND
      source_line LESS_EQUAL previous_exception_line))
    message(FATAL_ERROR "generation-corpus exceptions are not in source order")
  endif()
  list(APPEND exception_locations "${location}")
  set(previous_exception_path "${relative_path}")
  set(previous_exception_line "${source_line}")
  math(EXPR ${category}_count "${${category}_count} + 1")
endforeach()

list(LENGTH exception_locations exception_count)
if(NOT exception_count EQUAL 99 OR
   NOT invalid_derivation_count EQUAL 7 OR
   NOT invalid_record_count EQUAL 3 OR
   NOT orphan_continuation_count EQUAL 1 OR
   NOT orphan_request_count EQUAL 15 OR
   NOT zero_continuation_count EQUAL 18 OR
   NOT zero_request_count EQUAL 55)
  message(FATAL_ERROR
    "unexpected generation-corpus exceptions: ${exception_count} total; "
    "${invalid_derivation_count} invalid derivations, "
    "${invalid_record_count} invalid records, "
    "${orphan_continuation_count} orphan continuations, "
    "${orphan_request_count} orphan requests, "
    "${zero_continuation_count} zero-output continuations, "
    "${zero_request_count} zero-output requests")
endif()

# Reviewed data patches (docs/gener-data-patches.md): one corrected line per
# entry, in source order, each at a selected path. The preparer checks every
# fingerprint against the source.
file(STRINGS "${MORPHEUS_GENER_CORPUS_PATCHES}" patch_lines)
set(patch_locations)
set(previous_patch_path "")
set(previous_patch_line 0)
foreach(line IN LISTS patch_lines)
  if(line STREQUAL "" OR line MATCHES "^#")
    continue()
  endif()
  string(REPLACE "\t" ";" fields "${line}")
  list(LENGTH fields field_count)
  if(NOT field_count EQUAL 4)
    message(FATAL_ERROR "invalid generation-corpus patch line: ${line}")
  endif()
  list(GET fields 0 relative_path)
  list(GET fields 1 source_line)
  list(GET fields 2 source_sha256)
  list(GET fields 3 replacement)
  list(FIND manifest_paths "${relative_path}" manifest_at)
  if(manifest_at EQUAL -1)
    message(FATAL_ERROR
      "generation-corpus patch references an unselected file: ${relative_path}")
  endif()
  if(NOT source_line MATCHES "^[1-9][0-9]*$" OR
     NOT source_sha256 MATCHES "^[0-9a-f]+$" OR
     replacement STREQUAL "" OR replacement MATCHES "^ | $")
    message(FATAL_ERROR "invalid generation-corpus patch: ${line}")
  endif()
  string(LENGTH "${source_sha256}" sha256_length)
  if(NOT sha256_length EQUAL 64)
    message(FATAL_ERROR "invalid generation-corpus patch SHA-256: ${line}")
  endif()
  set(location "${relative_path}:${source_line}")
  list(FIND patch_locations "${location}" duplicate_at)
  if(NOT duplicate_at EQUAL -1 OR
     relative_path STRLESS previous_patch_path OR
     (relative_path STREQUAL previous_patch_path AND
      source_line LESS_EQUAL previous_patch_line))
    message(FATAL_ERROR
      "generation-corpus patches are duplicated or not in source order: ${location}")
  endif()
  list(APPEND patch_locations "${location}")
  set(previous_patch_path "${relative_path}")
  set(previous_patch_line "${source_line}")
endforeach()
list(LENGTH patch_locations patch_count)
if(NOT patch_count EQUAL 7)
  message(FATAL_ERROR "unexpected generation-corpus patches: ${patch_count}")
endif()

# The data package prepares the index with the same two manifests, embedded
# in internal/gener-manifest.js: they must match the files byte for byte.
file(READ "${MORPHEUS_GENER_DATA_MANIFEST}" data_manifest)
foreach(pair IN ITEMS "GENER_CORPUS_EXCEPTIONS|${MORPHEUS_GENER_CORPUS_EXCEPTIONS}"
                      "GENER_CORPUS_PATCHES|${MORPHEUS_GENER_CORPUS_PATCHES}")
  string(REPLACE "|" ";" pair "${pair}")
  list(GET pair 0 constant)
  list(GET pair 1 file)
  if(NOT data_manifest MATCHES
     "\nexport const ${constant} = (\"[^\n]*\");\n")
    message(FATAL_ERROR "${MORPHEUS_GENER_DATA_MANIFEST} does not define ${constant}")
  endif()
  string(JSON embedded GET "[${CMAKE_MATCH_1}]" 0)
  file(READ "${file}" expected)
  if(NOT embedded STREQUAL expected)
    message(FATAL_ERROR "${constant} differs from ${file}")
  endif()
endforeach()
