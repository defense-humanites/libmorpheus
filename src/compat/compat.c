/* SPDX-License-Identifier: MPL-2.0 */

#if !defined(_POSIX_C_SOURCE)
#define _POSIX_C_SOURCE 200809L
#endif

#include <morpheus/compat.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../anal/anal_internal.h"
#include "../morphlib/runtime_context.h"

struct morpheus_compat_output {
  char *data;
  size_t length;
  size_t analysis_count;
  size_t lemma_count;
};

static morpheus_status compat_runtime_status(
    const morpheus_runtime_context *context)
{
  switch(morpheus_runtime_context_error(context)) {
  case MORPHEUS_RUNTIME_ERROR_NO_MEMORY: return(MORPHEUS_NO_MEMORY);
  case MORPHEUS_RUNTIME_ERROR_INTERNAL: return(MORPHEUS_INTERNAL_ERROR);
  default: return(MORPHEUS_OK);
  }
}

/*
 * The compatibility surface reproduces the historical analyzer, cruncher
 * included, so it keeps the inherited diagnostics that the public API
 * silences on its contexts.
 */
static void restore_context(morpheus_context *context,
                            morpheus_runtime_context *previous,
                            int diagnostics)
{
  morpheus_runtime_context_set_diagnostics(context,diagnostics);
  morpheus_runtime_context_activate(previous);
}

morpheus_status
morpheus_compat_analyze(
    morpheus_context *context, const uint8_t *beta_code, size_t length,
    morpheus_compat_flags flags, morpheus_compat_output **output)
{
  morpheus_runtime_context *previous;
  morpheus_status runtime_status;
  int diagnostics;
  morpheus_compat_output *owned;
  gk_word *word;
  FILE *stream;
  char input[MAXWORDSIZE];

  if(!context || !beta_code || !output) return(MORPHEUS_INVALID_ARGUMENT);
  *output=NULL;
  if(length >= sizeof input) return(MORPHEUS_INPUT_TOO_LONG);
  if(memchr(beta_code,0,length)) return(MORPHEUS_INVALID_ARGUMENT);
  memcpy(input,beta_code,length);
  input[length]=0;

  owned=calloc(1,sizeof *owned);
  if(!owned) return(MORPHEUS_NO_MEMORY);
  stream=open_memstream(&owned->data,&owned->length);
  if(!stream) {
    free(owned);
    return(MORPHEUS_NO_MEMORY);
  }

  previous=morpheus_runtime_context_activate(context);
  diagnostics=morpheus_runtime_context_diagnostics(context);
  morpheus_runtime_context_set_diagnostics(context,1);
  morpheus_runtime_context_clear_error(context);
  word=morpheus_check_word(input,(PrntFlags)flags);
  runtime_status=compat_runtime_status(context);
  if(runtime_status != MORPHEUS_OK) {
    if(word) FreeGkword(word);
    restore_context(context,previous,diagnostics);
    fclose(stream);
    morpheus_compat_output_free(owned);
    return(runtime_status);
  }
  if(!word) {
    restore_context(context,previous,diagnostics);
    fclose(stream);
    morpheus_compat_output_free(owned);
    return(MORPHEUS_INVALID_ARGUMENT);
  }
  owned->analysis_count=(size_t)totanal_of(word);
  owned->lemma_count=(size_t)cntlems(word);
  if(flags && owned->analysis_count) {
    PrntAnalyses(word,(PrntFlags)flags,stream);
    if(anal_buf() && anal_buf()[0]) fputs(anal_buf(),stream);
  }
  runtime_status=compat_runtime_status(context);
  FreeGkword(word);
  restore_context(context,previous,diagnostics);
  if(runtime_status != MORPHEUS_OK) {
    fclose(stream);
    morpheus_compat_output_free(owned);
    return(runtime_status);
  }
  if(fclose(stream) != 0) {
    morpheus_compat_output_free(owned);
    return(MORPHEUS_INTERNAL_ERROR);
  }
  *output=owned;
  return(MORPHEUS_OK);
}

const char *
morpheus_compat_output_data(const morpheus_compat_output *output)
{
  return(output ? output->data : NULL);
}

size_t
morpheus_compat_output_length(const morpheus_compat_output *output)
{
  return(output ? output->length : 0);
}

size_t
morpheus_compat_output_analysis_count(const morpheus_compat_output *output)
{
  return(output ? output->analysis_count : 0);
}

size_t
morpheus_compat_output_lemma_count(const morpheus_compat_output *output)
{
  return(output ? output->lemma_count : 0);
}

void
morpheus_compat_output_free(morpheus_compat_output *output)
{
  if(!output) return;
  free(output->data);
  free(output);
}
