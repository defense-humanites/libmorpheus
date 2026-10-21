# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Link policy for the native C test programs when the tree is configured with
# the Emscripten toolchain (emcmake). The programs are compiled to JavaScript
# plus WebAssembly and run under the Node.js that emcmake registers as
# CMAKE_CROSSCOMPILING_EMULATOR, so CTest executes the historical suite
# against the same object code that the distribution module links.
#
# The distribution module itself (target morpheus_wasm) replaces these
# options with its own; see the MORPHEUS_BUILD_WASM block in CMakeLists.txt.

if(NOT EMSCRIPTEN OR NOT BUILD_TESTING)
  message(FATAL_ERROR
    "EmscriptenTesting.cmake applies only to Emscripten builds with BUILD_TESTING")
endif()

set(MORPHEUS_EMSCRIPTEN_TEST_PRE_JS
  "${PROJECT_SOURCE_DIR}/cmake/emscripten-test-env.js")

add_link_options(
  # Read the stemlib and fixtures straight from the host file system.
  "-sNODERAWFS=1"
  "-sENVIRONMENT=node"
  "-sALLOW_MEMORY_GROWTH=1"
  # The historical analyzer keeps large automatic buffers; the Emscripten
  # default of 64 KiB is too small for the deeper analysis paths.
  "-sSTACK_SIZE=4194304"
  # Propagate exit codes and flush stdio like a native process.
  "-sEXIT_RUNTIME=1"
  # Forward the host environment (MORPHLIB in particular) to getenv().
  "--pre-js=${MORPHEUS_EMSCRIPTEN_TEST_PRE_JS}"
)
set_property(
  DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
  "${MORPHEUS_EMSCRIPTEN_TEST_PRE_JS}"
)
