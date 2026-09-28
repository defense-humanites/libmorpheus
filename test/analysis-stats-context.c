// SPDX-License-Identifier: AGPL-3.0-or-later

#include <assert.h>
#include <stdio.h>

#include <gkstring.h>

#include "../src/anal/checkgenwds.proto.h"
#include "../src/morphlib/gkstring.proto.h"
#include "../src/morphlib/runtime_context.h"
#include "../src/morphlib/runtime_context_internal.h"

int quickflag = 0;

static void
add_empty_analysis(void)
{
	gk_word candidate = { 0 };
	gk_word generated = { 0 };

	set_rawword(&candidate,"alpha");
	set_rawword(&generated,"alpha");
	set_workword(&generated,"alpha");
	set_lemma(&generated,"alpha");
	assert(AddAnalysis(&candidate,&generated));
	assert(totanal_of(&candidate) == 1);
	FreeGkAnal(analysis_of(&candidate));
}

static void
add_many_analyses(void)
{
	gk_word candidate = { 0 };
	gk_word generated = { 0 };
	char lemma[32];
	int i;

	set_rawword(&candidate,"many");
	set_rawword(&generated,"many");
	set_workword(&generated,"many");
	for (i = 0; i < 40; ++i) {
		snprintf(lemma,sizeof lemma,"lemma%d",i);
		set_lemma(&generated,lemma);
		assert(AddAnalysis(&candidate,&generated));
		assert(totanal_of(&candidate) == i + 1);
	}
	assert(candidate.gw_anal_capacity >= 40);
	FreeGkAnal(analysis_of(&candidate));
}

int
main(void)
{
	morpheus_runtime_context *first = morpheus_runtime_context_create();
	morpheus_runtime_context *second = morpheus_runtime_context_create();
	morpheus_runtime_context *previous;

	assert(first);
	assert(second);
	previous = morpheus_runtime_context_activate(first);
	assert(!AddAnalysis(NULL,NULL));
	assert(morpheus_runtime_context_error(first) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(first);
	{
		gk_word inconsistent = { 0 };
		gk_word generated = { 0 };

		set_totanal(&inconsistent,1);
		assert(!AddAnalysis(&inconsistent,&generated));
		assert(!analysis_of(&inconsistent));
		assert(morpheus_runtime_context_error(first) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(first);
		first->analysis_storage_error = 0;
	}
	add_empty_analysis();
	add_many_analyses();
	assert(show_totanals() == 41);
	assert(show_totlems() == 41);
	first->analysis_storage_error = 1;

	morpheus_runtime_context_activate(second);
	assert(!show_totanals());
	assert(!show_totlems());
	assert(!second->analysis_storage_error);
	add_empty_analysis();

	morpheus_runtime_context_activate(first);
	assert(show_totanals() == 41);
	assert(show_totlems() == 41);
	assert(first->analysis_storage_error);

	morpheus_runtime_context_activate(previous);
	morpheus_runtime_context_destroy(first);
	morpheus_runtime_context_destroy(second);
	return(0);
}
