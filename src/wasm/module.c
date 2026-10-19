/* SPDX-License-Identifier: AGPL-3.0-or-later */

/*
 * Anchor translation unit for the WebAssembly distribution module.
 *
 * The module is the complete public C API (include/morpheus/morpheus.h and
 * include/morpheus/compat.h) linked by Emscripten into morpheus.mjs plus
 * morpheus.wasm. Every public entry point is exported through the linker's
 * export list in CMakeLists.txt; this file only adds the version probe that
 * lets the JavaScript wrapper check that it loaded the module it was written
 * for. There is no main(): the module is a library and never exits.
 */

#include <morpheus/morpheus.h>

#ifndef MORPHEUS_WASM_VERSION
#error "MORPHEUS_WASM_VERSION must name the libmorpheus release"
#endif

#define MORPHEUS_WASM_STRINGIFY_(x) #x
#define MORPHEUS_WASM_STRINGIFY(x) MORPHEUS_WASM_STRINGIFY_(x)

/** Return the libmorpheus release that produced this module. */
MORPHEUS_API const char *morpheus_wasm_module_version(void);

const char *morpheus_wasm_module_version(void)
{
  return(MORPHEUS_WASM_STRINGIFY(MORPHEUS_WASM_VERSION));
}
