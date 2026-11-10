/* SPDX-License-Identifier: MPL-2.0 */

#ifndef MORPHEUS_RUNTIME_CONTEXT_H
#define MORPHEUS_RUNTIME_CONTEXT_H

typedef struct morpheus_runtime_context morpheus_runtime_context;

typedef enum {
	MORPHEUS_RUNTIME_ERROR_NONE=0,
	MORPHEUS_RUNTIME_ERROR_NO_MEMORY=1,
	MORPHEUS_RUNTIME_ERROR_INTERNAL=2
} morpheus_runtime_error;

/* Active contexts are thread-affine; NULL restores the thread default. */
morpheus_runtime_context *morpheus_runtime_context_create(void);
void morpheus_runtime_context_destroy(morpheus_runtime_context *context);
morpheus_runtime_context *morpheus_runtime_context_activate(
    morpheus_runtime_context *context);
void morpheus_runtime_context_set_language(
    morpheus_runtime_context *context, int language);
int morpheus_runtime_context_language(
    const morpheus_runtime_context *context);
void morpheus_runtime_context_clear_error(morpheus_runtime_context *context);
morpheus_runtime_error morpheus_runtime_context_error(
    const morpheus_runtime_context *context);
void morpheus_runtime_error_record(morpheus_runtime_error error);

/*
 * Diagnostics are the inherited front ends' messages on standard error. They
 * stay enabled for those front ends (the thread default context and any new
 * context); the public API silences them on its own contexts, which report
 * failures through status codes instead.
 */
void morpheus_runtime_context_set_diagnostics(
    morpheus_runtime_context *context, int enabled);
int morpheus_runtime_context_diagnostics(
    const morpheus_runtime_context *context);
#if defined(__GNUC__) || defined(__clang__)
__attribute__((format(printf,1,2)))
#endif
void morpheus_runtime_diagnostic(const char *format, ...);

#endif
