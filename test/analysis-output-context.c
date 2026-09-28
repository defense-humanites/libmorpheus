// SPDX-License-Identifier: AGPL-3.0-or-later

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gkstring.h>
#include <prntflags.h>

#include "../src/anal/prntanal.proto.h"
#include "../src/morphlib/runtime_context.h"

static void
render_empty_analysis(const char *word)
{
	gk_analysis analysis = { 0 };
	gk_word candidate = { 0 };

	set_analysis(&candidate,&analysis);
	set_rawword(&candidate,word);
	set_stem(&candidate,word);
	assert(!PrntAnalyses(&candidate,KEEP_BETA,stdout));
}

static void
render_one_analysis(const char *word)
{
	gk_analysis analysis = { 0 };
	gk_word candidate = { 0 };

	set_analysis(&candidate,&analysis);
	set_totanal(&candidate,1);
	set_rawword(&candidate,word);
	set_stem(&candidate,word);
	set_lemma(&analysis,word);
	set_rawword(&analysis,word);
	set_workword(&analysis,word);
	set_stem(&analysis,word);
	assert(PrntAnalyses(&candidate,KEEP_BETA,stdout) == 1);
}

static void
render_many_analyses(void)
{
	gk_analysis *analyses = calloc(40,sizeof *analyses);
	gk_word candidate = { 0 };
	char lemma[32];
	int i;

	assert(analyses);
	set_analysis(&candidate,analyses);
	set_totanal(&candidate,40);
	set_rawword(&candidate,"many");
	set_stem(&candidate,"many");
	for (i = 0; i < 40; ++i) {
		snprintf(lemma,sizeof lemma,"lemma%02d",i);
		set_lemma(&analyses[i],lemma);
		set_rawword(&analyses[i],"many");
		set_workword(&analyses[i],"many");
		set_stem(&analyses[i],"many");
	}
	assert(PrntAnalyses(&candidate,KEEP_BETA,stdout) == 40);
	assert(strstr(anal_buf(),"lemma39"));
	free(analyses);
}

static void
assert_analysis_sort_is_stable(void)
{
	gk_analysis analyses[4] = { 0 };

	set_lemma(&analyses[0],"zeta");
	set_rawword(&analyses[0],"zeta-first");
	set_lemma(&analyses[1],"alpha");
	set_rawword(&analyses[1],"alpha-first");
	set_lemma(&analyses[2],"zeta");
	set_rawword(&analyses[2],"zeta-second");
	set_lemma(&analyses[3],"alpha");
	set_rawword(&analyses[3],"alpha-second");

	SortAnals(analyses,4);

	assert(!strcmp(rawword_of(&analyses[0]),"alpha-first"));
	assert(!strcmp(rawword_of(&analyses[1]),"alpha-second"));
	assert(!strcmp(rawword_of(&analyses[2]),"zeta-first"));
	assert(!strcmp(rawword_of(&analyses[3]),"zeta-second"));
}

int
main(void)
{
	morpheus_runtime_context *greek = morpheus_runtime_context_create();
	morpheus_runtime_context *latin = morpheus_runtime_context_create();
	morpheus_runtime_context *previous;

	assert(greek);
	assert(latin);
	assert_analysis_sort_is_stable();
	previous = morpheus_runtime_context_activate(greek);
	assert(!anal_buf());
	assert(!PrntAnalyses(NULL,KEEP_BETA,stdout));
	assert(morpheus_runtime_context_error(greek) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(greek);
	render_empty_analysis("alpha");
	assert(strstr(anal_buf(),"alpha"));
	render_one_analysis("logos");
	assert(strstr(anal_buf(),"logos"));
	render_many_analyses();
	assert(morpheus_runtime_context_error(greek) ==
	       MORPHEUS_RUNTIME_ERROR_NONE);

	morpheus_runtime_context_activate(latin);
	assert(!anal_buf());
	render_empty_analysis("beta");
	assert(strstr(anal_buf(),"beta"));
	assert(!strstr(anal_buf(),"alpha"));

	morpheus_runtime_context_activate(greek);
	assert(strstr(anal_buf(),"lemma39"));
	assert(!strstr(anal_buf(),"beta"));

	morpheus_runtime_context_activate(previous);
	morpheus_runtime_context_destroy(greek);
	morpheus_runtime_context_destroy(latin);
	return(0);
}
