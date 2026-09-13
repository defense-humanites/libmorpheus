// SPDX-License-Identifier: AGPL-3.0-or-later

#define _POSIX_C_SOURCE 200809L

#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "../src/api/api_internal.h"
#include "../src/morphlib/runtime_context.h"
#include "../src/morphlib/runtime_context_internal.h"
#include "../src/morphlib/morphstrcmp.proto.h"
#include "../src/morphlib/morphkeys.proto.h"
#include "../src/morphlib/indkeys.proto.h"
#include "../src/morphlib/morphpath.proto.h"
#include "../src/morphlib/retrentry.proto.h"

static void build_test_path(char *destination,size_t capacity,
                            const char *base,const char *suffix)
{
  size_t base_length=strlen(base);
  size_t suffix_length=strlen(suffix);

  if(base_length>=capacity || suffix_length>=capacity-base_length) abort();
  memcpy(destination,base,base_length);
  memcpy(destination+base_length,suffix,suffix_length+1);
}

int main(void)
{
  morpheus_runtime_context *context=morpheus_runtime_context_create();
  morpheus_runtime_context *previous;
  static const char missing_stemlib[]="/morpheus-test-missing-stemlib";
  endtags tag={0};
  char keys[LONGSTRING]="not empty";
  int maxkeys=1;

  assert(context);
  previous=morpheus_runtime_context_activate(context);
  assert(morpheus_runtime_context_error(context)==
         MORPHEUS_RUNTIME_ERROR_NONE);
  assert(morpheus_runtime_status(context)==MORPHEUS_OK);

  {
    char transactional[8]="base";

    assert(!morpheus_runtime_string_append(
      transactional,"-overflow",sizeof transactional));
    assert(!strcmp(transactional,"base"));
    assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);
    morpheus_runtime_context_clear_error(context);
  }

  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  context->analysis_storage_error=1;
  morpheus_runtime_context_clear_error(context);
  assert(context->analysis_storage_error==0);
  morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
  assert(morpheus_runtime_status(context)==MORPHEUS_NO_MEMORY);

  morpheus_runtime_context_clear_error(context);
  context->stemlib_path=malloc(sizeof missing_stemlib);
  assert(context->stemlib_path);
  memcpy(context->stemlib_path,missing_stemlib,sizeof missing_stemlib);
  assert(!init_keys());
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);
  assert(!context->stem_type_arguments);
  assert(!context->derivation_type_arguments);
  assert(!context->domain_arguments);
  assert(!context->morph_key_table);
  assert(!context->morph_key_stem_count);
  assert(!context->morph_key_derivation_count);
  assert(!context->morph_key_domain_count);
  assert(!context->morph_key_count);
  assert(!context->morph_keys_initialized);

  morpheus_runtime_context_clear_error(context);
  assert(!init_preind(NULL,&maxkeys));
  assert(maxkeys==0);
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  {
    char path[BUFSIZ]="not empty";
    int opened=context->files_opened;

    morpheus_runtime_context_clear_error(context);
    assert(!MorphFopen(NULL,"r"));
    assert(context->files_opened==opened);
    assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);
    morpheus_runtime_context_clear_error(context);
    assert(!MorphFopen("input",NULL));
    assert(context->files_opened==opened);
    assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);
    morpheus_runtime_context_clear_error(context);
    MorphPathName(NULL,path);
    assert(!path[0]);
    assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);
    morpheus_runtime_context_clear_error(context);
    MorphPathName("input",NULL);
    assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);
    morpheus_runtime_context_clear_error(context);
    SysFolderFile(NULL,"input");
    assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);
    morpheus_runtime_context_clear_error(context);
    SysFolderFile(path,NULL);
    assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);
  }

  morpheus_runtime_context_clear_error(context);
  assert(!init_preind("missing",NULL));
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  morpheus_runtime_context_clear_error(context);
  assert(ChckPreIndex(NULL,"a",0,1,morphstrcmp)==-1);
  assert(morpheus_runtime_status(context)==MORPHEUS_OK);
  assert(ChckPreIndex(NULL,"a",1,1,morphstrcmp)==-1);
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  morpheus_runtime_context_clear_error(context);
  assert(ChckPreIndex(&tag,NULL,1,1,morphstrcmp)==-1);
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  morpheus_runtime_context_clear_error(context);
  assert(ChckPreIndex(&tag,"a",1,1,NULL)==-1);
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  morpheus_runtime_context_clear_error(context);
  assert(!ChckFullIndex(NULL,keys,"missing",0,morphstrncmp));
  assert(!keys[0]);
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  morpheus_runtime_context_clear_error(context);
  assert(!ChckFullIndex("a",NULL,"missing",0,morphstrncmp));
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  morpheus_runtime_context_clear_error(context);
  strcpy(keys,"not empty");
  assert(!ChckFullIndex("a",keys,NULL,0,morphstrncmp));
  assert(!keys[0]);
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  morpheus_runtime_context_clear_error(context);
  strcpy(keys,"not empty");
  assert(!ChckFullIndex("a",keys,"missing",0,NULL));
  assert(!keys[0]);
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  morpheus_runtime_context_clear_error(context);
  assert(index_list(NULL,NULL,1)==-1);
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  morpheus_runtime_context_clear_error(context);
  assert(index_list("input",NULL,0)==-1);
  assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);

  {
    char temporary[BUFSIZ];
    char greek[BUFSIZ];
    char input[BUFSIZ];
    char output[BUFSIZ];
    const char *temporary_base=getenv("TMPDIR");
    FILE *stream;
    char *root=temporary;
    size_t path_length;
    unsigned int attempt;
    int created=0;
    int written;

    if(!temporary_base || !*temporary_base) temporary_base="/tmp";
    for(attempt=0;attempt<100;attempt++) {
      written=snprintf(temporary,sizeof temporary,
                       "%s/morpheus-index-%ld-%u",temporary_base,
                       (long)getpid(),attempt);
      assert(written>0 && (size_t)written<sizeof temporary);
      if(mkdir(temporary,0700)==0) {
        created=1;
        break;
      }
      assert(errno==EEXIST);
    }
    assert(created);
    build_test_path(greek,sizeof greek,root,"/Greek");
    build_test_path(input,sizeof input,greek,"/input");
    build_test_path(output,sizeof output,input,".lindex");
    assert(mkdir(greek,0700)==0);
    stream=fopen(input,"w");
    assert(stream);
    assert(fputs("alpha\n",stream)>=0);
    assert(fclose(stream)==0);
    assert(mkdir(output,0700)==0);
    free(context->stemlib_path);
    path_length=strlen(root);
    context->stemlib_path=malloc(path_length+1);
    assert(context->stemlib_path);
    memcpy(context->stemlib_path,root,path_length+1);
    morpheus_runtime_context_clear_error(context);
    assert(index_list("input",NULL,1)==-1);
    assert(morpheus_runtime_status(context)==MORPHEUS_INTERNAL_ERROR);
    assert(rmdir(output)==0);
    assert(unlink(input)==0);
    assert(rmdir(greek)==0);
    assert(rmdir(root)==0);
  }

  morpheus_runtime_context_activate(previous);
  morpheus_runtime_context_destroy(context);
  return(0);
}
