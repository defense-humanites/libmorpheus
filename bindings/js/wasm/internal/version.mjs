// SPDX-License-Identifier: AGPL-3.0-or-later

/** Version of the WebAssembly binding and of its npm and JSR packages. */
export const MORPHEUS_WASM_VERSION = "0.1.1";

/**
 * libmorpheus release whose runtime sources are compiled into the packaged
 * module. Unlike the native bindings, this package ships that runtime.
 */
export const MORPHEUS_NATIVE_VERSION = "0.4.3";

/** C ABI implemented by the packaged module. */
export const MORPHEUS_NATIVE_ABI_VERSION = 2;

/** Emscripten release that must reproduce the packaged module byte for byte. */
export const MORPHEUS_EMSCRIPTEN_VERSION = "4.0.15";
