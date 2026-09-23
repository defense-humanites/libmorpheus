// SPDX-License-Identifier: AGPL-3.0-or-later

#include <assert.h>
#include <string.h>

#include <gkstring.h>
#include <prntflags.h>

#include "../src/morphlib/beta2smarta.proto.h"
#include "../src/morphlib/morphflags.proto.h"
#include "../src/morphlib/morphkeys.proto.h"
#include "../src/morphlib/morphpath.proto.h"
#include "../src/morphlib/preverb3.proto.h"
#include "../src/morphlib/runtime_context.h"
#include "../src/morphlib/morphstrcmp.proto.h"
#include "../src/morphlib/setlang.proto.h"
#include "../src/morphlib/smk2beta.proto.h"

int main(void)
{
	morpheus_runtime_context *greek = morpheus_runtime_context_create();
	morpheus_runtime_context *latin = morpheus_runtime_context_create();
	morpheus_runtime_context *previous;
	FILE *file;
	char converted[16];

	assert(greek);
	assert(latin);
	assert(cur_lang() == GREEK);

	morpheus_runtime_context_set_language(greek,GREEK);
	morpheus_runtime_context_set_language(latin,LATIN);
	assert(morpheus_runtime_context_language(greek) == GREEK);
	assert(morpheus_runtime_context_language(latin) == LATIN);

	previous = morpheus_runtime_context_activate(greek);
	assert(NumFilesOpened() == 0);
	file = MorphFopen("conjfile","r");
	assert(file);
	fclose(file);
	assert(NumFilesOpened() == 1);

	morpheus_runtime_context_activate(latin);
	assert(NumFilesOpened() == 0);
	assert(cur_lang() == LATIN);
	assert(morphstrcmp("a|","ai") == 0);
	assert(!is_pretty_morphflag(PERS_NAME));
	assert(is_prvb_morphflag(DISSIMILATION));
	assert(is_rawpreverb("trans"));
	assert(GetStemNum("a_ae"));
	assert(!strcmp(NameOfStemtype((Stemtype)(031|NOUNSTEM|DECL3)),
	               "er_eris"));
	assert(!strcmp(NameOfStemtype((Stemtype)(044|NOUNSTEM|DECL3)),
	               "er_eris"));
	assert(GetStemNum("er_eris") == (Stemtype)(044|NOUNSTEM|DECL3));
	assert(GetStemNum("demonstr") ==
	       (Stemtype)(06|INDECL|NOUNSTEM|DECL1));
	assert(GetStemNum("interrog") ==
	       (Stemtype)(016|INDECL|NOUNSTEM|DECL3));
	set_roman();
	beta2smarta("a",converted);
	assert(!strcmp(converted,"A"));
	assert(smarta2beta("a",converted,sizeof converted));
	assert(!strcmp(converted,"$a"));
	set_lang(GREEK);
	assert(is_rawpreverb("upo"));
	assert(GetStemNum("os_ou"));
	assert(!strcmp(NameOfDerivtype((Derivtype)(037|VERBSTEM|REG_CONJ)),
	               "illw"));
	assert(!strcmp(NameOfDerivtype((Derivtype)(041|VERBSTEM|REG_CONJ)),
	               "illw"));
	assert(GetStemNum("illw") == (Stemtype)(041|VERBSTEM|REG_CONJ));
	set_lang(ITALIAN);
	assert(morpheus_runtime_context_language(latin) == ITALIAN);

	morpheus_runtime_context_activate(greek);
	assert(cur_lang() == GREEK);
	assert(morphstrcmp("a|","ai") == 0);
	assert(!is_pretty_morphflag(PERS_NAME));
	assert(is_prvb_morphflag(DISSIMILATION));
	assert(is_rawpreverb("upo"));
	assert(GetStemNum("os_ou"));
	beta2smarta("a",converted);
	assert(!strcmp(converted,"a"));
	assert(smk2beta("a",converted,sizeof converted));
	assert(!strcmp(converted,"a"));
	morpheus_runtime_context_destroy(greek);
	assert(cur_lang() == GREEK);

	morpheus_runtime_context_activate(previous);
	morpheus_runtime_context_destroy(latin);
	return(0);
}
