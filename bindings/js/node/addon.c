// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Antoine Boquet

#include <dlfcn.h>
#include <node_api.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "morpheus/morpheus.h"

typedef struct {
  void *dynamic_library;
  size_t analysis_size;
  size_t generation_size;
  size_t context_count;
  bool closed;
  uint32_t (*abi_version)(void);
  size_t (*analysis_size_fn)(void);
  size_t (*generation_size_fn)(void);
  const char *(*status_message)(morpheus_status);
  morpheus_status (*open_path)(uint32_t, const uint8_t *, size_t, uint32_t,
                               morpheus_context **);
  void (*close)(morpheus_context *);
  morpheus_status (*analyze)(morpheus_context *, const uint8_t *, size_t,
                             morpheus_options, morpheus_result **);
  size_t (*result_count)(const morpheus_result *);
  morpheus_status (*result_copy)(const morpheus_result *, size_t, void *,
                                 size_t);
  morpheus_status (*result_truncated_fields)(const morpheus_result *, size_t,
                                             morpheus_truncated_fields *);
  void (*result_free)(morpheus_result *);
  morpheus_status (*generate)(morpheus_context *, const uint8_t *, size_t,
                              const morpheus_generation_options *,
                              morpheus_generation_result **);
  size_t (*generation_result_count)(const morpheus_generation_result *);
  morpheus_status (*generation_result_copy)(const morpheus_generation_result *,
                                            size_t, void *, size_t);
  morpheus_status (*generation_result_truncated_fields)(
      const morpheus_generation_result *, size_t, morpheus_truncated_fields *);
  size_t (*generation_result_skipped_records)(
      const morpheus_generation_result *);
  void (*generation_result_free)(morpheus_generation_result *);
} node_morpheus_library;

typedef struct {
  node_morpheus_library *library;
  morpheus_context *context;
  napi_ref library_reference;
  size_t pending_operations;
  bool closed;
} node_morpheus_context;

typedef enum { NODE_MORPHEUS_ANALYZE, NODE_MORPHEUS_GENERATE } operation_kind;

typedef struct {
  napi_env env;
  napi_async_work work;
  napi_deferred deferred;
  napi_ref context_reference;
  node_morpheus_context *context;
  operation_kind kind;
  uint8_t *input;
  size_t input_length;
  morpheus_options analysis_options;
  morpheus_generation_options generation_options;
  morpheus_status status;
  size_t count;
  size_t skipped_records;
  morpheus_analysis *analyses;
  morpheus_generation *generations;
  morpheus_truncated_fields *truncated_fields;
} node_morpheus_operation;

static napi_value node_morpheus_undefined(napi_env env) {
  napi_value value;
  (void)napi_get_undefined(env, &value);
  return value;
}

static void node_morpheus_throw_last_error(napi_env env, const char *fallback) {
  const napi_extended_error_info *info = NULL;
  (void)napi_get_last_error_info(env, &info);
  napi_throw_error(env, NULL,
                   info != NULL && info->error_message != NULL
                       ? info->error_message
                       : fallback);
}

static bool node_morpheus_ok(napi_env env, napi_status status,
                             const char *fallback) {
  if (status == napi_ok) return true;
  node_morpheus_throw_last_error(env, fallback);
  return false;
}

static void node_morpheus_throw_status(napi_env env,
                                       node_morpheus_library *library,
                                       morpheus_status status) {
  napi_value message;
  napi_value error;
  napi_value status_value;
  const char *text = library->status_message(status);
  if (text == NULL) text = "Unknown libmorpheus error";
  if (napi_create_string_utf8(env, text, NAPI_AUTO_LENGTH, &message) != napi_ok ||
      napi_create_error(env, NULL, message, &error) != napi_ok ||
      napi_create_uint32(env, (uint32_t)status, &status_value) != napi_ok ||
      napi_set_named_property(env, error, "status", status_value) != napi_ok) {
    node_morpheus_throw_last_error(env, "Unable to create Morpheus error");
    return;
  }
  napi_throw(env, error);
}

static bool node_morpheus_get_utf8(napi_env env, napi_value value,
                                   uint8_t **output, size_t *length) {
  size_t required = 0;
  if (!node_morpheus_ok(env,
                        napi_get_value_string_utf8(env, value, NULL, 0,
                                                   &required),
                        "Expected a string")) {
    return false;
  }
  uint8_t *bytes = malloc(required + 1u);
  if (bytes == NULL) {
    napi_throw_error(env, NULL, "Out of memory");
    return false;
  }
  size_t written = 0;
  if (!node_morpheus_ok(
          env,
          napi_get_value_string_utf8(env, value, (char *)bytes, required + 1u,
                                     &written),
          "Unable to read string")) {
    free(bytes);
    return false;
  }
  *output = bytes;
  *length = written;
  return true;
}

static bool node_morpheus_external(napi_env env, napi_value value,
                                   void **result, const char *message) {
  if (napi_get_value_external(env, value, result) == napi_ok &&
      *result != NULL) {
    return true;
  }
  napi_throw_type_error(env, NULL, message);
  return false;
}

static void node_morpheus_unload_library(node_morpheus_library *library) {
  if (library == NULL || library->closed) return;
  if (library->dynamic_library != NULL) (void)dlclose(library->dynamic_library);
  library->dynamic_library = NULL;
  library->closed = true;
}

static void node_morpheus_library_finalizer(napi_env env, void *data,
                                            void *hint) {
  (void)env;
  (void)hint;
  node_morpheus_library *library = data;
  if (library == NULL) return;
  node_morpheus_unload_library(library);
  free(library);
}

static void node_morpheus_context_finalizer(napi_env env, void *data,
                                            void *hint) {
  (void)hint;
  node_morpheus_context *context = data;
  if (context == NULL) return;
  if (!context->closed && context->context != NULL) {
    context->library->close(context->context);
    context->context = NULL;
    context->closed = true;
    if (context->library->context_count > 0u) context->library->context_count--;
  }
  if (context->library_reference != NULL) {
    (void)napi_delete_reference(env, context->library_reference);
  }
  free(context);
}

static bool node_morpheus_load_symbol(void *handle, const char *name,
                                      void *destination,
                                      size_t destination_size) {
  void *symbol = dlsym(handle, name);
  if (symbol == NULL || destination_size != sizeof(symbol)) return false;
  memcpy(destination, &symbol, destination_size);
  return true;
}

#define NODE_MORPHEUS_LOAD(library, field, symbol)                         \
  do {                                                                     \
    if (!node_morpheus_load_symbol((library)->dynamic_library, #symbol,     \
                                   &(library)->field,                       \
                                   sizeof((library)->field))) {            \
      napi_throw_error(env, NULL, "Missing native symbol: " #symbol);      \
      node_morpheus_unload_library(library);                               \
      free(library);                                                       \
      free(path);                                                          \
      return NULL;                                                         \
    }                                                                      \
  } while (false)

static napi_value node_morpheus_open_library(napi_env env,
                                             napi_callback_info info) {
  size_t argc = 1;
  napi_value argv[1];
  if (!node_morpheus_ok(env, napi_get_cb_info(env, info, &argc, argv, NULL, NULL),
                        "Unable to read arguments")) {
    return NULL;
  }
  if (argc != 1u) {
    napi_throw_type_error(env, NULL, "openLibrary expects one path");
    return NULL;
  }
  uint8_t *path = NULL;
  size_t path_length = 0;
  if (!node_morpheus_get_utf8(env, argv[0], &path, &path_length)) return NULL;
  if (memchr(path, 0, path_length) != NULL) {
    free(path);
    napi_throw_type_error(env, NULL, "Library path contains a NUL byte");
    return NULL;
  }

  node_morpheus_library *library = calloc(1u, sizeof(*library));
  if (library == NULL) {
    free(path);
    napi_throw_error(env, NULL, "Out of memory");
    return NULL;
  }
  library->dynamic_library = dlopen((const char *)path, RTLD_NOW | RTLD_LOCAL);
  if (library->dynamic_library == NULL) {
    const char *message = dlerror();
    napi_throw_error(env, NULL,
                     message != NULL ? message : "Unable to load libmorpheus");
    free(library);
    free(path);
    return NULL;
  }

  NODE_MORPHEUS_LOAD(library, abi_version, morpheus_abi_version);
  NODE_MORPHEUS_LOAD(library, analysis_size_fn, morpheus_analysis_size);
  NODE_MORPHEUS_LOAD(library, generation_size_fn, morpheus_generation_size);
  NODE_MORPHEUS_LOAD(library, status_message, morpheus_status_message);
  NODE_MORPHEUS_LOAD(library, open_path, morpheus_open_path);
  NODE_MORPHEUS_LOAD(library, close, morpheus_close);
  NODE_MORPHEUS_LOAD(library, analyze, morpheus_analyze);
  NODE_MORPHEUS_LOAD(library, result_count, morpheus_result_count);
  NODE_MORPHEUS_LOAD(library, result_copy, morpheus_result_copy);
  NODE_MORPHEUS_LOAD(library, result_truncated_fields,
                     morpheus_result_truncated_fields);
  NODE_MORPHEUS_LOAD(library, result_free, morpheus_result_free);
  NODE_MORPHEUS_LOAD(library, generate, morpheus_generate);
  NODE_MORPHEUS_LOAD(library, generation_result_count,
                     morpheus_generation_result_count);
  NODE_MORPHEUS_LOAD(library, generation_result_copy,
                     morpheus_generation_result_copy);
  NODE_MORPHEUS_LOAD(library, generation_result_truncated_fields,
                     morpheus_generation_result_truncated_fields);
  NODE_MORPHEUS_LOAD(library, generation_result_skipped_records,
                     morpheus_generation_result_skipped_records);
  NODE_MORPHEUS_LOAD(library, generation_result_free,
                     morpheus_generation_result_free);
  free(path);

  if (library->abi_version() != MORPHEUS_ABI_VERSION) {
    node_morpheus_unload_library(library);
    free(library);
    napi_throw_error(env, NULL, "Unsupported libmorpheus ABI version");
    return NULL;
  }
  library->analysis_size = library->analysis_size_fn();
  library->generation_size = library->generation_size_fn();
  if (library->analysis_size != sizeof(morpheus_analysis) ||
      library->generation_size != sizeof(morpheus_generation)) {
    node_morpheus_unload_library(library);
    free(library);
    napi_throw_error(env, NULL, "Native record size differs from ABI version 2");
    return NULL;
  }

  napi_value external;
  if (!node_morpheus_ok(
          env,
          napi_create_external(env, library, node_morpheus_library_finalizer,
                               NULL, &external),
          "Unable to wrap native library")) {
    node_morpheus_unload_library(library);
    free(library);
    return NULL;
  }
  return external;
}

static napi_value node_morpheus_close_library(napi_env env,
                                              napi_callback_info info) {
  size_t argc = 1;
  napi_value argv[1];
  if (!node_morpheus_ok(env, napi_get_cb_info(env, info, &argc, argv, NULL, NULL),
                        "Unable to read arguments")) {
    return NULL;
  }
  node_morpheus_library *library = NULL;
  if (argc != 1u ||
      !node_morpheus_external(env, argv[0], (void **)&library,
                              "Invalid Morpheus library handle")) {
    return NULL;
  }
  if (library->closed) return node_morpheus_undefined(env);
  if (library->context_count != 0u) {
    napi_throw_error(env, NULL, "Close all Morpheus contexts before the library");
    return NULL;
  }
  node_morpheus_unload_library(library);
  return node_morpheus_undefined(env);
}

static napi_value node_morpheus_open_context(napi_env env,
                                             napi_callback_info info) {
  size_t argc = 3;
  napi_value argv[3];
  if (!node_morpheus_ok(env, napi_get_cb_info(env, info, &argc, argv, NULL, NULL),
                        "Unable to read arguments")) {
    return NULL;
  }
  node_morpheus_library *library = NULL;
  if (argc != 3u ||
      !node_morpheus_external(env, argv[0], (void **)&library,
                              "Invalid Morpheus library handle")) {
    return NULL;
  }
  if (library->closed) {
    napi_throw_error(env, NULL, "Morpheus library is closed");
    return NULL;
  }
  uint8_t *path = NULL;
  size_t path_length = 0;
  uint32_t language = 0;
  if (!node_morpheus_get_utf8(env, argv[1], &path, &path_length) ||
      !node_morpheus_ok(env, napi_get_value_uint32(env, argv[2], &language),
                        "Invalid Morpheus language")) {
    free(path);
    return NULL;
  }

  node_morpheus_context *context = calloc(1u, sizeof(*context));
  if (context == NULL) {
    free(path);
    napi_throw_error(env, NULL, "Out of memory");
    return NULL;
  }
  morpheus_status status = library->open_path(
      MORPHEUS_ABI_VERSION, path, path_length, language, &context->context);
  free(path);
  if (status != MORPHEUS_OK) {
    free(context);
    node_morpheus_throw_status(env, library, status);
    return NULL;
  }
  context->library = library;
  library->context_count++;
  if (!node_morpheus_ok(env, napi_create_reference(env, argv[0], 1u,
                                                   &context->library_reference),
                        "Unable to retain Morpheus library")) {
    library->close(context->context);
    library->context_count--;
    free(context);
    return NULL;
  }
  napi_value external;
  if (!node_morpheus_ok(
          env,
          napi_create_external(env, context, node_morpheus_context_finalizer,
                               NULL, &external),
          "Unable to wrap Morpheus context")) {
    (void)napi_delete_reference(env, context->library_reference);
    library->close(context->context);
    library->context_count--;
    free(context);
    return NULL;
  }
  return external;
}

static napi_value node_morpheus_close_context(napi_env env,
                                              napi_callback_info info) {
  size_t argc = 1;
  napi_value argv[1];
  if (!node_morpheus_ok(env, napi_get_cb_info(env, info, &argc, argv, NULL, NULL),
                        "Unable to read arguments")) {
    return NULL;
  }
  node_morpheus_context *context = NULL;
  if (argc != 1u ||
      !node_morpheus_external(env, argv[0], (void **)&context,
                              "Invalid Morpheus context handle")) {
    return NULL;
  }
  if (context->closed) return node_morpheus_undefined(env);
  if (context->pending_operations != 0u) {
    napi_throw_error(env, NULL, "Morpheus context still has pending operations");
    return NULL;
  }
  context->library->close(context->context);
  context->context = NULL;
  context->closed = true;
  context->library->context_count--;
  if (context->library_reference != NULL) {
    (void)napi_delete_reference(env, context->library_reference);
    context->library_reference = NULL;
  }
  return node_morpheus_undefined(env);
}

static bool node_morpheus_set_uint32(napi_env env, napi_value object,
                                     const char *name, uint32_t number) {
  napi_value value;
  return napi_create_uint32(env, number, &value) == napi_ok &&
         napi_set_named_property(env, object, name, value) == napi_ok;
}

/*
 * Results cross into JavaScript as one packed buffer per operation: the
 * `count` records copied from the library (`morpheus_analysis` or
 * `morpheus_generation`, `recordSize` bytes each, the C ABI's layout), followed
 * by `count` little-endian uint32 truncated-field masks. index.js decodes the
 * records; building one object per record through Node-API calls here made a
 * maximal generation (2,918 forms) cost about 35 calls per form on the main
 * thread (issue #47). Encoding 2 adds `skippedRecords`, the generation
 * result's count of source records the engine skipped (zero for analysis).
 */
#define NODE_MORPHEUS_RECORD_ENCODING 2u

static bool node_morpheus_packed_result(napi_env env,
                                        const node_morpheus_operation *operation,
                                        napi_value *output) {
  const size_t record_size = operation->kind == NODE_MORPHEUS_ANALYZE
                                 ? sizeof(morpheus_analysis)
                                 : sizeof(morpheus_generation);
  const void *records = operation->kind == NODE_MORPHEUS_ANALYZE
                            ? (const void *)operation->analyses
                            : (const void *)operation->generations;
  const size_t records_bytes = operation->count * record_size;
  const size_t truncated_bytes =
      operation->count * sizeof(morpheus_truncated_fields);
  void *data = NULL;
  napi_value buffer;
  napi_value object;
  if (napi_create_arraybuffer(env, records_bytes + truncated_bytes, &data,
                              &buffer) != napi_ok) {
    return false;
  }
  if (operation->count != 0u) {
    memcpy(data, records, records_bytes);
    memcpy((uint8_t *)data + records_bytes, operation->truncated_fields,
           truncated_bytes);
  }
  if (napi_create_object(env, &object) != napi_ok ||
      !node_morpheus_set_uint32(env, object, "count",
                                (uint32_t)operation->count) ||
      !node_morpheus_set_uint32(env, object, "recordSize",
                                (uint32_t)record_size) ||
      !node_morpheus_set_uint32(env, object, "skippedRecords",
                                (uint32_t)operation->skipped_records) ||
      napi_set_named_property(env, object, "buffer", buffer) != napi_ok) {
    return false;
  }
  *output = object;
  return true;
}

static void node_morpheus_execute(napi_env env, void *data) {
  (void)env;
  node_morpheus_operation *operation = data;
  node_morpheus_library *library = operation->context->library;
  if (operation->kind == NODE_MORPHEUS_ANALYZE) {
    morpheus_result *result = NULL;
    operation->status = library->analyze(
        operation->context->context, operation->input, operation->input_length,
        operation->analysis_options, &result);
    if (operation->status != MORPHEUS_OK) return;
    operation->count = library->result_count(result);
    operation->analyses = calloc(operation->count, sizeof(*operation->analyses));
    operation->truncated_fields =
        calloc(operation->count, sizeof(*operation->truncated_fields));
    if (operation->count != 0u &&
        (operation->analyses == NULL || operation->truncated_fields == NULL)) {
      operation->status = MORPHEUS_NO_MEMORY;
    }
    for (size_t index = 0;
         operation->status == MORPHEUS_OK && index < operation->count; index++) {
      operation->status = library->result_copy(
          result, index, &operation->analyses[index],
          sizeof(operation->analyses[index]));
      if (operation->status == MORPHEUS_OK) {
        operation->status = library->result_truncated_fields(
            result, index, &operation->truncated_fields[index]);
      }
    }
    library->result_free(result);
    return;
  }

  morpheus_generation_result *result = NULL;
  operation->status = library->generate(
      operation->context->context, operation->input, operation->input_length,
      &operation->generation_options, &result);
  if (operation->status != MORPHEUS_OK) return;
  operation->count = library->generation_result_count(result);
  operation->skipped_records =
      library->generation_result_skipped_records(result);
  operation->generations =
      calloc(operation->count, sizeof(*operation->generations));
  operation->truncated_fields =
      calloc(operation->count, sizeof(*operation->truncated_fields));
  if (operation->count != 0u &&
      (operation->generations == NULL || operation->truncated_fields == NULL)) {
    operation->status = MORPHEUS_NO_MEMORY;
  }
  for (size_t index = 0;
       operation->status == MORPHEUS_OK && index < operation->count; index++) {
    operation->status = library->generation_result_copy(
        result, index, &operation->generations[index],
        sizeof(operation->generations[index]));
    if (operation->status == MORPHEUS_OK) {
      operation->status = library->generation_result_truncated_fields(
          result, index, &operation->truncated_fields[index]);
    }
  }
  library->generation_result_free(result);
}

static void node_morpheus_complete(napi_env env, napi_status async_status,
                                   void *data) {
  node_morpheus_operation *operation = data;
  napi_value value = NULL;
  if (async_status == napi_ok && operation->status == MORPHEUS_OK &&
      !node_morpheus_packed_result(env, operation, &value)) {
    value = NULL;
  }

  if (value != NULL) {
    (void)napi_resolve_deferred(env, operation->deferred, value);
  } else {
    napi_value message;
    napi_value error;
    napi_value status_value;
    morpheus_status status = operation->status;
    const char *text = async_status != napi_ok
                           ? "Node-API asynchronous work failed"
                           : operation->context->library->status_message(status);
    if (text == NULL) text = "Unable to convert Morpheus result";
    (void)napi_create_string_utf8(env, text, NAPI_AUTO_LENGTH, &message);
    (void)napi_create_error(env, NULL, message, &error);
    (void)napi_create_uint32(env, (uint32_t)status, &status_value);
    (void)napi_set_named_property(env, error, "status", status_value);
    (void)napi_reject_deferred(env, operation->deferred, error);
  }

  operation->context->pending_operations--;
  (void)napi_delete_reference(env, operation->context_reference);
  (void)napi_delete_async_work(env, operation->work);
  free(operation->input);
  free(operation->analyses);
  free(operation->generations);
  free(operation->truncated_fields);
  free(operation);
}

static bool node_morpheus_optional_uint32(napi_env env, napi_value object,
                                          const char *name, uint32_t *output) {
  bool present = false;
  if (napi_has_named_property(env, object, name, &present) != napi_ok)
    return false;
  if (!present) return true;
  napi_value value;
  return napi_get_named_property(env, object, name, &value) == napi_ok &&
         napi_get_value_uint32(env, value, output) == napi_ok;
}

static bool node_morpheus_generation_options(napi_env env, napi_value object,
                                             morpheus_generation_options *out) {
  memset(out, 0, sizeof(*out));
  out->version = MORPHEUS_GENERATION_OPTIONS_VERSION;
  out->struct_size = (uint32_t)sizeof(*out);
  uint32_t result_limit = 0;
  uint32_t exclude_duals = 0;
  if (!node_morpheus_optional_uint32(env, object, "resultLimit",
                                     &result_limit) ||
      !node_morpheus_optional_uint32(env, object, "excludeDuals",
                                     &exclude_duals) ||
      !node_morpheus_optional_uint32(env, object, "partOfSpeech",
                                     &out->part_of_speech) ||
      !node_morpheus_optional_uint32(env, object, "dialect", &out->dialect) ||
      !node_morpheus_optional_uint32(env, object, "geographicRegion",
                                     &out->geographic_region) ||
      !node_morpheus_optional_uint32(env, object, "person", &out->person) ||
      !node_morpheus_optional_uint32(env, object, "number", &out->number) ||
      !node_morpheus_optional_uint32(env, object, "gender", &out->gender) ||
      !node_morpheus_optional_uint32(env, object, "grammaticalCase",
                                     &out->grammatical_case) ||
      !node_morpheus_optional_uint32(env, object, "tense", &out->tense) ||
      !node_morpheus_optional_uint32(env, object, "mood", &out->mood) ||
      !node_morpheus_optional_uint32(env, object, "voice", &out->voice) ||
      !node_morpheus_optional_uint32(env, object, "degree", &out->degree)) {
    napi_throw_type_error(env, NULL, "Invalid generation options");
    return false;
  }
  out->result_limit = result_limit;
  if (exclude_duals != 0u) out->flags |= MORPHEUS_GENERATION_EXCLUDE_DUALS;
  return true;
}

static napi_value node_morpheus_queue_operation(napi_env env,
                                                napi_callback_info info,
                                                operation_kind kind) {
  size_t argc = 3;
  napi_value argv[3];
  if (!node_morpheus_ok(env, napi_get_cb_info(env, info, &argc, argv, NULL, NULL),
                        "Unable to read arguments")) {
    return NULL;
  }
  node_morpheus_context *context = NULL;
  if (argc != 3u ||
      !node_morpheus_external(env, argv[0], (void **)&context,
                              "Invalid Morpheus context handle")) {
    return NULL;
  }
  if (context->closed) {
    napi_throw_error(env, NULL, "Morpheus context is closed");
    return NULL;
  }

  node_morpheus_operation *operation = calloc(1u, sizeof(*operation));
  if (operation == NULL) {
    napi_throw_error(env, NULL, "Out of memory");
    return NULL;
  }
  operation->env = env;
  operation->context = context;
  operation->kind = kind;
  operation->status = MORPHEUS_OK;
  if (!node_morpheus_get_utf8(env, argv[1], &operation->input,
                              &operation->input_length)) {
    free(operation);
    return NULL;
  }
  if (kind == NODE_MORPHEUS_ANALYZE) {
    bool lossless = false;
    if (!node_morpheus_ok(
            env,
            napi_get_value_bigint_uint64(env, argv[2],
                                         &operation->analysis_options,
                                         &lossless),
            "Analysis options must be a bigint") ||
        !lossless) {
      free(operation->input);
      free(operation);
      if (lossless == false) {
        napi_throw_range_error(env, NULL, "Analysis options exceed uint64");
      }
      return NULL;
    }
  } else if (!node_morpheus_generation_options(
                 env, argv[2], &operation->generation_options)) {
    free(operation->input);
    free(operation);
    return NULL;
  }

  napi_value promise;
  napi_value resource_name;
  if (!node_morpheus_ok(env,
                        napi_create_promise(env, &operation->deferred, &promise),
                        "Unable to create promise") ||
      !node_morpheus_ok(env,
                        napi_create_reference(env, argv[0], 1u,
                                              &operation->context_reference),
                        "Unable to retain context") ||
      !node_morpheus_ok(
          env,
          napi_create_string_utf8(
              env, kind == NODE_MORPHEUS_ANALYZE ? "libmorpheus:analyze"
                                                  : "libmorpheus:generate",
              NAPI_AUTO_LENGTH, &resource_name),
          "Unable to create async resource name") ||
      !node_morpheus_ok(
          env,
          napi_create_async_work(env, NULL, resource_name,
                                 node_morpheus_execute, node_morpheus_complete,
                                 operation, &operation->work),
          "Unable to create async work")) {
    if (operation->context_reference != NULL)
      (void)napi_delete_reference(env, operation->context_reference);
    free(operation->input);
    free(operation);
    return NULL;
  }
  context->pending_operations++;
  if (!node_morpheus_ok(env, napi_queue_async_work(env, operation->work),
                        "Unable to queue async work")) {
    context->pending_operations--;
    (void)napi_delete_async_work(env, operation->work);
    (void)napi_delete_reference(env, operation->context_reference);
    free(operation->input);
    free(operation);
    return NULL;
  }
  return promise;
}

static napi_value node_morpheus_analyze(napi_env env,
                                        napi_callback_info info) {
  return node_morpheus_queue_operation(env, info, NODE_MORPHEUS_ANALYZE);
}

static napi_value node_morpheus_generate(napi_env env,
                                         napi_callback_info info) {
  return node_morpheus_queue_operation(env, info, NODE_MORPHEUS_GENERATE);
}

static napi_value node_morpheus_init(napi_env env, napi_value exports) {
  napi_value record_encoding;
  if (napi_create_uint32(env, NODE_MORPHEUS_RECORD_ENCODING,
                         &record_encoding) != napi_ok) {
    node_morpheus_throw_last_error(env, "Unable to initialize addon");
    return NULL;
  }
  const napi_property_descriptor properties[] = {
      {"recordEncoding", NULL, NULL, NULL, NULL, record_encoding,
       napi_enumerable, NULL},
      {"openLibrary", NULL, node_morpheus_open_library, NULL, NULL, NULL,
       napi_default, NULL},
      {"closeLibrary", NULL, node_morpheus_close_library, NULL, NULL, NULL,
       napi_default, NULL},
      {"openContext", NULL, node_morpheus_open_context, NULL, NULL, NULL,
       napi_default, NULL},
      {"closeContext", NULL, node_morpheus_close_context, NULL, NULL, NULL,
       napi_default, NULL},
      {"analyze", NULL, node_morpheus_analyze, NULL, NULL, NULL, napi_default,
       NULL},
      {"generate", NULL, node_morpheus_generate, NULL, NULL, NULL,
       napi_default, NULL},
  };
  if (napi_define_properties(env, exports,
                             sizeof(properties) / sizeof(properties[0]),
                             properties) != napi_ok) {
    node_morpheus_throw_last_error(env, "Unable to initialize addon");
    return NULL;
  }
  return exports;
}

NAPI_MODULE(libmorpheus_node, node_morpheus_init)
