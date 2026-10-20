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

# Emscripten treats any runtime with process.versions.node as Node.js and then
# calls createRequire(import.meta.url) and reads files through node:fs. That
# only works when the module itself was loaded from a file: URL. Two cases
# fail before a precompiled WebAssembly.Module can even be instantiated: edge
# runtimes with Node compatibility (Cloudflare Workers) present such a
# process object but no import.meta.url, and a module served from a registry
# (JSR under Deno, Node.js or Bun) has an https: URL that createRequire
# rejects. Restrict the Node branch to modules loaded from file: URLs;
# everything else takes the generic path, where Module.instantiateWasm (or
# the facade's own fetch of morpheus.wasm) supplies the module.
set(node_detection_original
  "ENVIRONMENT_IS_NODE=typeof process==\"object\"&&process.versions?.node&&process.type!=\"renderer\";")
set(node_detection_portable
  "ENVIRONMENT_IS_NODE=typeof process==\"object\"&&process.versions?.node&&process.type!=\"renderer\"&&typeof import.meta.url==\"string\"&&import.meta.url.startsWith(\"file:\");")
string(FIND "${content}" "${node_detection_original}" node_detection_at)
if(node_detection_at EQUAL -1)
  string(FIND "${content}" "${node_detection_portable}" node_detection_at)
  if(node_detection_at EQUAL -1)
    message(FATAL_ERROR
      "Emscripten output no longer contains the expected Node.js detection")
  endif()
else()
  string(REPLACE
    "${node_detection_original}" "${node_detection_portable}"
    content "${content}")
endif()

if(NOT DEFINED MORPHEUS_WASM_EMSCRIPTEN_VERSION)
  message(FATAL_ERROR "MORPHEUS_WASM_EMSCRIPTEN_VERSION is required")
endif()
string(CONCAT header
  "// SPDX-License-Identifier: AGPL-3.0-or-later AND MPL-2.0 AND MIT\n"
  "// libmorpheus ${MORPHEUS_WASM_VERSION} WebAssembly module, "
  "ABI ${MORPHEUS_WASM_ABI_VERSION}. "
  "Generated with Emscripten ${MORPHEUS_WASM_EMSCRIPTEN_VERSION} from the "
  "libmorpheus runtime sources; contains no linguistic data.\n"
)
string(FIND "${content}" "${header}" header_at)
if(NOT header_at EQUAL 0)
  file(WRITE "${MORPHEUS_WASM_MODULE}" "${header}${content}")
endif()
