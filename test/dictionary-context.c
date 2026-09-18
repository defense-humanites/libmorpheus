// SPDX-License-Identifier: AGPL-3.0-or-later

#include <assert.h>
#include <stdio.h>
#include <string.h>

#include <endtags.h>
#include <gkdict.h>
#include <gkstring.h>

#include "../src/gkdict/dictio.proto.h"
#include "../src/morphlib/morphpath.proto.h"
#include "../src/morphlib/runtime_context.h"

static void
assert_indeclinable(char *word, int expected_file_opens)
{
	char keys[LONGSTRING];
	int before = NumFilesOpened();

	assert(chckindecl(word,keys));
	assert(keys[0]);
	assert(NumFilesOpened() == before + expected_file_opens);
}

int
main(void)
{
	morpheus_runtime_context *greek = morpheus_runtime_context_create();
	morpheus_runtime_context *latin = morpheus_runtime_context_create();
	morpheus_runtime_context *previous;
	char lemmfile[LONGSTRING] = "not empty";
	long lemmoff = 1;

	assert(greek);
	assert(latin);
	morpheus_runtime_context_set_language(greek,GREEK);
	morpheus_runtime_context_set_language(latin,LATIN);

	previous = morpheus_runtime_context_activate(greek);
	assert_indeclinable("kai",2);
	assert_indeclinable("kai",1);

	morpheus_runtime_context_activate(latin);
	assert_indeclinable("et",2);
	assert_indeclinable("et",1);

	morpheus_runtime_context_activate(greek);
	assert_indeclinable("kai",1);
	morpheus_runtime_context_set_language(greek,LATIN);
	assert_indeclinable("et",2);

	morpheus_runtime_context_activate(latin);
	assert_indeclinable("et",1);

	morpheus_runtime_context_activate(greek);
	{
		const char *output_path = "morpheus-dictionary-context.tmp";
		FILE *output = fopen(output_path,"w+");

		assert(output);
		assert(prntlemmentry("zzzzzzzz",NULL,output) == -1);
		assert(morpheus_runtime_context_error(greek) ==
		       MORPHEUS_RUNTIME_ERROR_NONE);
		assert(!getlemmstart(NULL,lemmfile,&lemmoff));
		assert(!lemmfile[0]);
		assert(lemmoff == -1);
		assert(morpheus_runtime_context_error(greek) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(greek);
		strcpy(lemmfile,"not empty");
		lemmoff = 1;
		assert(!getlemmstart("logos",NULL,&lemmoff));
		assert(lemmoff == -1);
		assert(morpheus_runtime_context_error(greek) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(greek);
		assert(!getlemmstart("logos",lemmfile,NULL));
		assert(!lemmfile[0]);
		assert(morpheus_runtime_context_error(greek) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(greek);
		assert(prntlemmentry(NULL,NULL,output) == -1);
		assert(morpheus_runtime_context_error(greek) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(greek);
		assert(prntlemmentry("logos",NULL,NULL) == -1);
		assert(morpheus_runtime_context_error(greek) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(greek);
		assert(!lemma_exists(NULL));
		assert(morpheus_runtime_context_error(greek) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(greek);
		assert(fclose(output) == 0);
		assert(remove(output_path) == 0);
	}

	morpheus_runtime_context_activate(previous);
	morpheus_runtime_context_destroy(greek);
	morpheus_runtime_context_destroy(latin);
	return(0);
}
