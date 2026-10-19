# SPDX-License-Identifier: AGPL-3.0-or-later
#
# Prefix the Emscripten-generated ES module with its license and provenance
# header. The module links the AGPL-3.0-or-later and MPL-2.0 runtime sources
# with Emscripten's MIT-licensed JavaScript runtime support code.

if(NOT DEFINED MORPHEUS_WASM_MODULE)
  message(FATAL_ERROR "MORPHEUS_WASM_MODULE is required")
endif()
if(NOT DEFINED MORPHEUS_WASM_VERSION OR NOT DEFINED MORPHEUS_WASM_ABI_VERSION)
  message(FATAL_ERROR "MORPHEUS_WASM_VERSION and MORPHEUS_WASM_ABI_VERSION are required")
endif()
file(READ "${MORPHEUS_WASM_MODULE}" content)
string(CONCAT header
  "// SPDX-License-Identifier: AGPL-3.0-or-later AND MPL-2.0 AND MIT\n"
  "// libmorpheus ${MORPHEUS_WASM_VERSION} WebAssembly module, "
  "ABI ${MORPHEUS_WASM_ABI_VERSION}. "
  "Generated with Emscripten from the libmorpheus runtime sources; "
  "contains no linguistic data.\n"
)
string(FIND "${content}" "${header}" header_at)
if(NOT header_at EQUAL 0)
  file(WRITE "${MORPHEUS_WASM_MODULE}" "${header}${content}")
endif()
