# SPDX-License-Identifier: AGPL-3.0-or-later
#
# GitHub release notes: docs/release-notes/<tag>.md is the body of the
# release of <tag>, whose title is the tag itself. The notes are written one
# line per paragraph or list item, since GitHub renders every line break of a
# release body; every current version of every track has notes before it is
# tagged; and every workflow that creates a release reads them.

if(NOT DEFINED MORPHEUS_SOURCE_DIR OR NOT DEFINED MORPHEUS_PROJECT_VERSION)
  message(FATAL_ERROR "MORPHEUS_SOURCE_DIR and MORPHEUS_PROJECT_VERSION are required")
endif()
set(notes_dir "${MORPHEUS_SOURCE_DIR}/docs/release-notes")

file(GLOB notes_files RELATIVE "${notes_dir}" "${notes_dir}/*")
if(NOT notes_files)
  message(FATAL_ERROR "docs/release-notes is empty")
endif()

foreach(notes_file IN LISTS notes_files)
  if(NOT notes_file MATCHES "^((wasm-|data-|deno-|node-|python-)?v)([0-9]+\\.[0-9]+\\.[0-9]+)\\.md$")
    message(FATAL_ERROR "docs/release-notes/${notes_file} is not named after a release tag")
  endif()
  set(track_prefix "${CMAKE_MATCH_2}")
  set(track_version "${CMAKE_MATCH_3}")
  file(READ "${notes_dir}/${notes_file}" notes)
  if(NOT notes MATCHES "^<!-- SPDX-License-Identifier: AGPL-3\\.0-or-later -->\n\n[^\n#]")
    message(FATAL_ERROR
      "docs/release-notes/${notes_file} must open with the SPDX comment, a blank line and its summary")
  endif()
  if(NOT notes MATCHES "\n$" OR notes MATCHES "\n\n$")
    message(FATAL_ERROR "docs/release-notes/${notes_file} must end with exactly one newline")
  endif()

  # A non-blank line that follows a non-blank line is a hard-wrapped
  # continuation unless it starts a list item, a heading, a table row or a
  # quotation; code blocks are taken as they are.
  string(REPLACE ";" "\\;" escaped "${notes}")
  string(REPLACE "\n" ";" note_lines "${escaped}")
  set(previous "")
  set(in_fence FALSE)
  set(line_number 0)
  foreach(line IN LISTS note_lines)
    math(EXPR line_number "${line_number} + 1")
    if(line MATCHES "^```")
      if(in_fence)
        set(in_fence FALSE)
      else()
        set(in_fence TRUE)
      endif()
      set(previous "")
      continue()
    endif()
    if(NOT in_fence AND NOT line STREQUAL "" AND NOT previous STREQUAL "" AND
       NOT line MATCHES "^([-*] |[0-9]+\\. |#|\\||> )")
      message(FATAL_ERROR
        "docs/release-notes/${notes_file}:${line_number} continues the previous line; "
        "write each paragraph and list item on one line")
    endif()
    if(in_fence)
      set(previous "")
    else()
      set(previous "${line}")
    endif()
  endforeach()

  # Link the release decision when the track has one for that version.
  if(track_prefix STREQUAL "")
    set(decision "release-${track_version}.md")
  else()
    string(REGEX REPLACE "-$" "" track_name "${track_prefix}")
    set(decision "release-${track_name}-${track_version}.md")
  endif()
  if(EXISTS "${MORPHEUS_SOURCE_DIR}/docs/${decision}")
    string(FIND "${notes}" "/docs/${decision})" decision_at)
    if(decision_at EQUAL -1)
      message(FATAL_ERROR "docs/release-notes/${notes_file} does not link docs/${decision}")
    endif()
  endif()
endforeach()

# The version each track would tag next must already have its notes.
function(read_json_version path out)
  file(READ "${MORPHEUS_SOURCE_DIR}/${path}" json)
  string(JSON value GET "${json}" version)
  set(${out} "${value}" PARENT_SCOPE)
endfunction()
read_json_version(bindings/js/wasm/package.json wasm_version)
read_json_version(bindings/js/data/package.json data_version)
read_json_version(bindings/js/node/package.json node_version)
read_json_version(bindings/js/deno/jsr.json deno_version)
file(READ "${MORPHEUS_SOURCE_DIR}/bindings/python/pyproject.toml" pyproject)
string(REGEX MATCH "\nversion = \"([0-9.]+)\"" _ "${pyproject}")
set(python_version "${CMAKE_MATCH_1}")
foreach(current_tag IN ITEMS
        "v${MORPHEUS_PROJECT_VERSION}"
        "wasm-v${wasm_version}"
        "data-v${data_version}"
        "node-v${node_version}"
        "deno-v${deno_version}"
        "python-v${python_version}")
  if(NOT EXISTS "${notes_dir}/${current_tag}.md")
    message(FATAL_ERROR "Missing release notes for the current version: docs/release-notes/${current_tag}.md")
  endif()
endforeach()

# Every workflow that creates a GitHub release titles it with the tag and
# takes its body from the notes.
foreach(workflow IN ITEMS platform wasm-release data-release deno-release)
  file(READ "${MORPHEUS_SOURCE_DIR}/.github/workflows/${workflow}.yml" contents)
  string(FIND "${contents}" "docs/release-notes/\${tag}.md" notes_at)
  string(FIND "${contents}" "name: tag," title_at)
  if(notes_at EQUAL -1 OR title_at EQUAL -1)
    message(FATAL_ERROR "${workflow}.yml does not publish docs/release-notes with the tag as title")
  endif()
endforeach()
file(READ "${MORPHEUS_SOURCE_DIR}/.github/scripts/binding-release.cjs" binding_release)
foreach(required IN ITEMS "docs/release-notes/\${tag}.md" "name: tag," "make_latest: 'false'")
  string(FIND "${binding_release}" "${required}" required_at)
  if(required_at EQUAL -1)
    message(FATAL_ERROR "binding-release.cjs lacks ${required}")
  endif()
endforeach()
foreach(workflow IN ITEMS node-release python-release release-notes)
  file(READ "${MORPHEUS_SOURCE_DIR}/.github/workflows/${workflow}.yml" contents)
  string(FIND "${contents}" ".github/scripts/binding-release.cjs" module_at)
  if(module_at EQUAL -1)
    message(FATAL_ERROR "${workflow}.yml does not publish through binding-release.cjs")
  endif()
endforeach()
