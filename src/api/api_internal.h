// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Antoine Boquet

#ifndef MORPHEUS_API_INTERNAL_H
#define MORPHEUS_API_INTERNAL_H
#include <morpheus/morpheus.h>
#include "../morphlib/runtime_context.h"
struct morpheus_result {
  size_t count;
  morpheus_analysis *analyses;
  morpheus_truncated_fields *truncated_fields;
};
struct morpheus_generation_result {
  size_t count;
  size_t skipped_records;
  morpheus_generation *generations;
  morpheus_truncated_fields *truncated_fields;
};
morpheus_result *morpheus_result_create(size_t count);
static inline morpheus_status morpheus_runtime_status(
    const morpheus_runtime_context *context)
{
  switch(morpheus_runtime_context_error(context)) {
  case MORPHEUS_RUNTIME_ERROR_NO_MEMORY: return(MORPHEUS_NO_MEMORY);
  case MORPHEUS_RUNTIME_ERROR_INTERNAL: return(MORPHEUS_INTERNAL_ERROR);
  default: return(MORPHEUS_OK);
  }
}
#endif
