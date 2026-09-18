// SPDX-License-Identifier: AGPL-3.0-or-later

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gkstring.h>

#include "../src/morphlib/gkstring.proto.h"
#include "../src/morphlib/is_thirdmono.proto.h"
#include "../src/morphlib/adddomain.proto.h"
#include "../src/morphlib/antepenform.proto.h"
#include "../src/morphlib/augment.proto.h"
#include "../src/morphlib/conjstem.proto.h"
#include "../src/morphlib/fixacc.proto.h"
#include "../src/morphlib/errormess.proto.h"
#include "../src/morphlib/morphflags.proto.h"
#include "../src/morphlib/morphkeys.proto.h"
#include "../src/morphlib/markstem.proto.h"
#include "../src/morphlib/new_val.proto.h"
#include "../src/morphlib/numovable.proto.h"
#include "../src/morphlib/penultform.proto.h"
#include "../src/morphlib/preverb3.proto.h"
#include "../src/morphlib/preverb2.proto.h"
#include "../src/morphlib/preverb.proto.h"
#include "../src/morphlib/runtime_context.h"
#include "../src/morphlib/setlang.proto.h"
#include "../src/morphlib/standphon.proto.h"
#include "../src/morphlib/sprntGkflags.h"
#include "../src/morphlib/ultform.proto.h"
#include "../src/morphlib/ulttakescirc.proto.h"
#include "../src/greeklib/addaccent.proto.h"
#include "../src/greeklib/addbreath.proto.h"
#include "../src/greeklib/aspirate.proto.h"
#include "../src/greeklib/checkaccent.proto.h"
#include "../src/greeklib/cinsert.proto.h"
#include "../src/greeklib/do_dissim.proto.h"
#include "../src/greeklib/endsinstr.proto.h"
#include "../src/greeklib/Fclose.proto.h"
#include "../src/greeklib/getaccent.proto.h"
#include "../src/greeklib/getaccp.proto.h"
#include "../src/greeklib/getbreath.proto.h"
#include "../src/greeklib/getquantity.proto.h"
#include "../src/greeklib/getsyll.proto.h"
#include "../src/greeklib/gkstrlen.proto.h"
#include "../src/greeklib/hasaccent.proto.h"
#include "../src/greeklib/hasdiaer.proto.h"
#include "../src/greeklib/hasquant.proto.h"
#include "../src/greeklib/isdiphth.proto.h"
#include "../src/greeklib/isblank.proto.h"
#include "../src/greeklib/issubstring.proto.h"
#include "../src/greeklib/longbyposition.proto.h"
#include "../src/greeklib/naccents.proto.h"
#include "../src/greeklib/nsylls.proto.h"
#include "../src/greeklib/quantprim.proto.h"
#include "../src/greeklib/shortanalog.proto.h"
#include "../src/greeklib/standalpha.proto.h"
#include "../src/greeklib/standword.proto.h"
#include "../src/greeklib/stripacc.proto.h"
#include "../src/greeklib/stripbreath.proto.h"
#include "../src/greeklib/stripdiaer.proto.h"
#include "../src/greeklib/stripquant.proto.h"
#include "../src/greeklib/stripstemsep.proto.h"
#include "../src/greeklib/stripzeroend.proto.h"
#include "../src/greeklib/xstrings.proto.h"
#include "../src/greeklib/zap2ndbreath.proto.h"

static int
compare_text(char *left, char *right)
{
	return(strcmp(left,right));
}

int
main(void)
{
	gk_string entries[3] = { 0 };
	gk_string item = { 0 };
	gk_word word_item = { 0 };
	char empty[] = "";
	morpheus_runtime_context *context = morpheus_runtime_context_create();
	morpheus_runtime_context *previous;
	int length = 0;

	assert(context);
	previous = morpheus_runtime_context_activate(context);
	ErrorMess(NULL);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	SprintGkFlags(NULL,empty,sizeof empty,empty,NO);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	JakeSprintGkFlags(&item,NULL,0,empty,empty,NO);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	GregSprintGkFlags(&item,empty,sizeof empty,empty,NULL,NO);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	assert(CreatGkString(0) == NULL);
	assert(CreatGkAnal(0) == NULL);
	assert(CreatGkword(0) == NULL);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_NONE);
	assert(CreatGkString(-1) == NULL);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	assert(CreatGkAnal(-1) == NULL);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	assert(CreatGkword(-1) == NULL);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	ClearGkstring(NULL);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	CpGkAnal(NULL,&word_item);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	CpGkAnal(&word_item,NULL);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	assert(!stripacc(empty));
	stripbreath(empty);
	stripdiaer(empty);
	stripquant(empty);
	stripstemsep(empty);
	assert(!nsylls(empty));
	assert(getsyll(empty,ULTIMA) == P_ERR);
	assert(getsyll2(empty,ULTIMA) == empty);
	assert(!stripacc(NULL));
	stripbreath(NULL);
	stripdiaer(NULL);
	stripquant(NULL);
	stripstemsep(NULL);
	assert(!nsylls(NULL));
	assert(getsyll(NULL,ULTIMA) == P_ERR);
	assert(getsyll2(NULL,ULTIMA) == P_ERR);
	{
		gk_string movable = { 0 };
		gk_string full_movable = { 0 };
		char original[MAXWORDSIZE];

		strcpy(gkstring_of(&movable),"lu/si");
		assert(takes_nu_movable(&movable));
		add_numovable(&movable);
		assert(!strcmp(gkstring_of(&movable),"lu/sin"));
		assert(has_morphflag(morphflags_of(&movable),NU_MOVABLE));
		memset(gkstring_of(&full_movable),'a',MAXWORDSIZE-1);
		gkstring_of(&full_movable)[MAXWORDSIZE-1] = 0;
		memcpy(original,gkstring_of(&full_movable),sizeof original);
		add_numovable(&full_movable);
		assert(!memcmp(gkstring_of(&full_movable),original,sizeof original));
		assert(!has_morphflag(
		       morphflags_of(&full_movable),NU_MOVABLE));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!takes_nu_movable(NULL));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		add_numovable(NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		stand_phonetics(NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
	}
	{
		word_form form = { 0 };

		assert(!antepen_form(NULL,form));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!penult_form(NULL,form));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!ultima_form(NULL));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!ulttakescirc(NULL,form));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		markstem(NULL,&item);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		markstem(empty,NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		markstem(empty,&item);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_NONE);
	}
	{
		gk_string preverb = { 0 };
		char word[MAXWORDSIZE] = "beta";
		char oldpreverb[MAXWORDSIZE] = "";
		char lemma[MAXWORDSIZE] = "";

		assert(!nextpreverb(NULL,oldpreverb,lemma,&preverb));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!nextpreverb(word,NULL,lemma,&preverb));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!nextpreverb(word,oldpreverb,NULL,&preverb));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!nextpreverb(word,oldpreverb,lemma,NULL));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!has_rawpreverb(NULL,&preverb));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!has_rawpreverb(word,NULL));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!is_rawpreverb(NULL));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
	}
	{
		void (*shifts[])(char *) = {
			shift_su_to_cu, shift_eis_to_es, shift_pros_to_poti,
			shift_pros_to_proti, shift_upo_to_upai,
			shift_uper_to_upeir, shift_para_to_parai,
			shift_meta_to_peda, shift_en_to_eni
		};
		MorphFlags flags[MORPHFLAG_STORAGE_BYTES] = { 0 };
		char long_shift[MAXWORDSIZE];
		char original[MAXWORDSIZE];
		size_t i;

		strcpy(long_shift,"pros");
		memset(long_shift+4,'a',sizeof long_shift - 5);
		long_shift[sizeof long_shift - 1] = 0;
		strcpy(original,long_shift);

		assert(!First_K_aspirate(NULL));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		for (i = 0; i < sizeof shifts / sizeof shifts[0]; i++) {
			shifts[i](NULL);
			assert(morpheus_runtime_context_error(context) ==
			       MORPHEUS_RUNTIME_ERROR_INTERNAL);
			morpheus_runtime_context_clear_error(context);
		}
		shift_pros_to_proti(long_shift);
		assert(!strcmp(long_shift,original));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		set_odd_prvb(NULL,empty);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		set_odd_prvb(flags,NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
	}
	{
		MorphFlags flags[MORPHFLAG_STORAGE_BYTES] = { 0 };
		char result[MAXWORDSIZE] = "not empty";

		simpleaugment(NULL,NO);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		simpleredupit(NULL,NO,'e');
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!redupit2(NULL,NO,'e',1));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!un_redupl(NULL,result,'e'));
		assert(!result[0]);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!un_redupl(empty,NULL,'e'));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		add_double_augment(NULL,flags);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		add_double_augment(empty,NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
	}
	{
		gk_word augment_word = { 0 };
		gk_string possible = { 0 };
		gk_string quantity = { 0 };
		gk_string *possibles[] = { &possible };
		gk_string *quantities[] = { &quantity };
		MorphFlags flags[MORPHFLAG_STORAGE_BYTES] = { 0 };

		assert(!do_syllaug(NULL,1));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!do_tempaug(&augment_word,0));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!unaugment(NULL,possibles,quantities,1,(Dialect)0,NO,NO));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!unaugment(empty,possibles,quantities,0,(Dialect)0,NO,NO));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(unaugfromlemma(NULL,empty) == -1);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!add_augment(NULL,flags,1));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!add_augment(&augment_word,flags,0));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!needs_augment(NULL));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!needs_augment2(NULL,empty));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
	}
	{
		gk_word accent_word = { 0 };
		gk_string form = { 0 };
		gk_string stem = { 0 };
		word_form form_info = { 0 };
		MorphFlags flags[MORPHFLAG_STORAGE_BYTES] = { 0 };
		char output[MAXWORDSIZE] = "not empty";
		char long_stem[MAXWORDSIZE];

		putsimpleacc(NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		FixRecAcc(NULL,flags,output);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		FixRecAcc(&accent_word,NULL,output);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		FixPersAcc(&form,flags,&stem,empty,NULL,form_info,NO);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		FixPersAcc(NULL,flags,&stem,empty,output,form_info,NO);
		assert(!output[0]);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		memset(long_stem,'a',sizeof long_stem-1);
		long_stem[sizeof long_stem-1] = 0;
		set_gkstring(&stem,long_stem);
		strcpy(output,"sentinel");
		set_lang(LATIN);
		FixPersAcc(&form,flags,&stem,"z",output,form_info,NO);
		assert(!output[0]);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		set_lang(GREEK);
	}
	{
		gk_string stem = { 0 };
		gk_string ending = { 0 };
		word_form form = { 0 };
		char one_vowel[] = "a";
		char long_stem[MAXWORDSIZE];
		char long_ending[MAXWORDSIZE];

		memset(long_stem,'a',sizeof long_stem - 1);
		long_stem[sizeof long_stem - 1] = 0;
		strcpy(long_ending,"a");

		assert(!diphth_end(one_vowel,empty));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_NONE);
		assert(!diphth_end(long_stem,long_ending));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!is_thirdmono(NULL,&ending,empty,empty,form,NO));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!is_thirdmono(&stem,NULL,empty,empty,form,NO));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!is_mono_stem(NULL,empty));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!is_thirdexception(empty,NULL));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!poss_thirdmono((Stemtype)DECL3,NULL,empty));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!diphth_end(NULL,empty));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
	}
	{
		gk_string preverb = { 0 };
		char word[MAXWORDSIZE] = "beta";
		char previous[MAXWORDSIZE] = "";
		char empty_preverb[MAXWORDSIZE] = "";
		char rest[MAXWORDSIZE] = "";
		bool breathing = NO;

		assert(!checkprevb(NULL,previous,&breathing));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!checkprevb(word,NULL,&breathing));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!prvbcmp(empty_preverb,word,&breathing));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		getrest(NULL,word,word,"pro");
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		getrest(rest,word,word,empty_preverb);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		rstprevb(word,empty_preverb,&preverb);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		rstprevb(word,"pro",NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
	}
	{
		gk_string preverb = { 0 };
		MorphFlags flags[MORPHFLAG_STORAGE_BYTES] = { 0 };
		char empty_preverb[MAXWORDSIZE] = "";
		char rest[MAXWORDSIZE] = "beta";
		char full[MAXWORDSIZE] = "";

		assert(!CombPbStem(NULL,rest,(Dialect)0,flags));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!CombPbStem(empty_preverb,rest,(Dialect)0,flags));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!CombPbStemL("pro",NULL,(Dialect)0,flags));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!CombPbStemG("pro",rest,(Dialect)0,NULL));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!is_preverb(NULL,full,&preverb));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!is_preverb(rest,NULL,&preverb));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!exp_preverb(NULL,full,&preverb));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!exp_preverb(rest,full,NULL));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
	}
	{
		const char *temporary_path = "morpheus-gkstring-helper-context.tmp";
		FILE *temporary = fopen(temporary_path,"w+");
		void *allocation = malloc(1);

		assert(temporary);
		assert(allocation);
		xFclose(temporary);
		assert(remove(temporary_path) == 0);
		xFclose(NULL);
		assert(!xFree(allocation,NULL));
		assert(xFree(NULL,NULL) == -1);
	}
	{
		char accents[] = "a/=\\";
		char aspirated = 'p';
		char long_vowel = 'h';

		aspirate(&aspirated);
		assert(aspirated == 'f');
		shortanalog(&long_vowel);
		assert(long_vowel == 'e');
		assert(naccents(accents) == 3);
		assert(gkstrlen("a)/") == 1);
		assert(is_blank(NULL));
		assert(!naccents(NULL));
		assert(!gkstrlen(NULL));
		aspirate(NULL);
		shortanalog(NULL);
	}
	{
		char haystack[] = "alpha beta";

		assert(is_substring("beta",haystack) == haystack+6);
		assert(!is_substring("gamma",haystack));
		assert(!is_substring("",haystack));
		assert(!is_substring(NULL,haystack));
		assert(!is_substring("beta",NULL));
	}
	{
		char adjacent[] = "a_a_";
		char unchanged[] = "alpha";

		standalpha(adjacent);
		assert(!strcmp(adjacent,"hh"));
		standalpha(unchanged);
		assert(!strcmp(unchanged,"alpha"));
		standalpha(NULL);
	}
	{
		char accents[] = "a/b=c\\d";
		char hyphens[] = "--a--b--";
		char normalized[] = "-a\\*-b+";
		char oversized[MAXWORDSIZE+32];

		standword(normalized);
		assert(!strcmp(normalized,"a/b"));
		memset(oversized,'a',sizeof oversized-1);
		oversized[sizeof oversized-1] = 0;
		standword(oversized);
		assert(strlen(oversized) == sizeof oversized-1);
		zap2acc(accents);
		assert(!strcmp(accents,"a/bcd"));
		striphyph(hyphens);
		assert(!strcmp(hyphens,"ab"));
		standword(NULL);
		zap2acc(NULL);
		striphyph(NULL);
	}
	{
		char long_word[600];

		memset(long_word,'a',sizeof long_word-1);
		memcpy(long_word+sizeof long_word-7,"suffix",7);
		assert(ends_in(long_word,"suffix"));
		assert(ends_in("lo/g+os","gos"));
		assert(ends_in("logos","g/o+s"));
		assert(ends_in("", ""));
		assert(ends_in("logos", ""));
		assert(!ends_in("", "s"));
		assert(!ends_in("logos", "nos"));
		assert(!ends_in(NULL, "s"));
		assert(!ends_in("logos", NULL));
	}
	{
		char consecutive[] = "e)n((a";
		char extra[] = "e)nh(/bwsa";
		char initial_rho[] = "r(a)";
		char repeated_rho[] = "a)nanti/r)r(hton";
		char short_word[] = "";

		assert(has_extra_breath(extra));
		zap_extra_breath(extra);
		assert(!strcmp(extra,"e)nh/bwsa"));
		assert(!has_extra_breath(extra));
		assert(has_extra_breath(consecutive));
		zap_extra_breath(consecutive);
		assert(!strcmp(consecutive,"e)na"));
		assert(!has_extra_breath(consecutive));
		assert(!has_extra_breath(initial_rho));
		zap_extra_breath(initial_rho);
		assert(!strcmp(initial_rho,"r(a)"));
		assert(!has_extra_breath(short_word));
		zap_extra_breath(short_word);
		assert(!short_word[0]);
		zap_rr_breath(repeated_rho);
		assert(!strcmp(repeated_rho,"a)nanti/rrhton"));
		zap_rr_breath(short_word);
		assert(!short_word[0]);
		zap_extra_breath(NULL);
		assert(!has_extra_breath(NULL));
		zap_rr_breath(NULL);
	}
	{
		char accented[MAXWORDSIZE] = "a";
		char breathed[MAXWORDSIZE] = "a";
		char empty[MAXWORDSIZE] = "";
		char plain[] = "a";
		char unrelated[] = "a";
		int accent = ACUTE;
		int syllable = ULTIMA;

		addaccent(accented,ACUTE,accented);
		assert(!strcmp(accented,"a/"));
		addaccent(accented,ACUTE,unrelated);
		assert(!strcmp(accented,"a/"));
		addaccent(NULL,ACUTE,accented);
		addaccent(accented,ACUTE,NULL);
		addaccent(empty,ACUTE,empty);
		assert(!empty[0]);
		addbreath(breathed,SMOOTHBR);
		assert(!strcmp(breathed,"a)"));
		addbreath(empty,SMOOTHBR);
		assert(!empty[0]);
		addbreath(NULL,SMOOTHBR);
		assert(getbreath(NULL) == NOBREATH);
		assert(getaccp(NULL,ULTIMA) == P_ERR);
		assert(getaccent(NULL,ULTIMA) == C_ERR);
		assert(getquantity(NULL,ULTIMA,NULL,NO,NO) == I_ERR);
		assert(!hasaccent(NULL));
		assert(!has_diaeresis(NULL));
		assert(!has_quant(NULL));
		assert(!longbyposition(NULL));
		assert(!longbyposition(""));
		assert(!long_by_isub(NULL));
		assert(!long_by_isub(""));
		assert(long_by_isub("a|"));
		assert(checkaccent(NULL,&syllable,&accent) == -1);
		assert(syllable == -1);
		assert(accent == NOACCENT);
		assert(checkaccent(empty,&syllable,&accent) == -1);
		assert(syllable == -1);
		assert(accent == NOACCENT);
		assert(checkaccent(plain,&syllable,&accent) == -1);
		assert(syllable == -1);
		assert(accent == NOACCENT);
		assert(checkaccent(accented,&syllable,&accent) == ULTIMA);
		assert(syllable == ULTIMA);
		assert(accent == ACUTE);
		assert(checkaccent(empty,NULL,&accent) == -1);
		assert(accent == NOACCENT);
		assert(checkaccent(empty,&syllable,NULL) == -1);
		assert(syllable == -1);
	}
	{
		char diphthong[] = "ai";
		char empty_insert[MAXWORDSIZE] = "";
		char insert[MAXWORDSIZE] = "abc";
		char unrelated[] = "ai";

		assert(!is_diphth(diphthong,diphthong));
		assert(is_diphth(diphthong+1,diphthong));
		assert(!is_diphth(diphthong+2,diphthong));
		assert(!is_diphth(diphthong+1,unrelated));
		assert(!is_diphth(NULL,diphthong));
		assert(!is_diphth(diphthong,NULL));
		assert(!starts_w_diphth(NULL));
		assert(!starts_w_diphth(""));
		assert(!starts_w_diphth("a"));
		assert(starts_w_diphth(diphthong));
		cinsert('x',insert+1);
		assert(!strcmp(insert,"axbc"));
		cinsert('x',empty_insert);
		assert(!strcmp(empty_insert,"x"));
		cinsert('x',NULL);
		assert(!do_dissim(NULL,0));
		assert(!do_dissim("",0));
		assert(next_cons(NULL) == NULL);
		assert(!next_cons_rough(NULL));
		stripzeroend(NULL);
	}
	{
		char empty[MAXWORDSIZE] = "";
		char dental[MAXWORDSIZE] = "t";
		char full[MAXWORDSIZE];
		char nasal_labial[MAXWORDSIZE] = "mp";
		char one[MAXWORDSIZE] = "p";
		char short_verb[MAXWORDSIZE] = "a";
		char stem[MAXWORDSIZE] = "stem";
		char full_before[MAXWORDSIZE];

		fixcontr(stem,short_verb);
		assert(!strcmp(stem,"stem"));
		fixcontr(stem,"a/w");
		assert(!strcmp(stem,"stemh"));
		makeperf(empty);
		assert(!empty[0]);
		fixperf(empty);
		fixperf(one);
		assert(!strcmp(one,"p"));
		assert(do_sigma(empty,"s") == NO);
		assert(do_theta(empty) == NO);
		assert(do_mu(empty) == NO);
		assert(do_tau(empty) == NO);
		assert(do_mu(one) == YES);
		assert(!strcmp(one,"m"));
		assert(do_mu(nasal_labial) == YES);
		assert(!strcmp(nasal_labial,"m"));
		conjstem(empty,"a");
		assert(!strcmp(empty,"a"));
		empty[0] = 0;
		conjoin(empty,"a");
		assert(!strcmp(empty,"a"));
		conjoin(dental,"s");
		assert(!strcmp(dental,"s"));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_NONE);
		memset(full,'a',sizeof full - 1);
		full[sizeof full - 1] = 0;
		memcpy(full_before,full,sizeof full_before);
		conjoin(full,"a");
		assert(strlen(full) == sizeof full - 1);
		assert(!memcmp(full,full_before,sizeof full_before));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);

		fixcontr(NULL,"a/w");
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		fixcontr(stem,NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		makeperf(NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		fixperf(NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		conjstem(NULL,"a");
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		conjstem(stem,NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		conjoin(NULL,"a");
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		conjoin(stem,NULL);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(do_sigma(NULL,"s") == NO);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(do_sigma(stem,NULL) == NO);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(do_theta(NULL) == NO);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(do_mu(NULL) == NO);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(do_tau(NULL) == NO);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
	}
	{
		struct {
			char value[5];
			char guard[4];
		} bounded = { "", "end" };
		char overlap_left[8] = "abcdef";
		char overlap_right[8] = "abc";
		char one[1] = { 'x' };
		char unchanged[5] = "keep";

		assert(!Xstrncpy(bounded.value,"abcdef",sizeof bounded.value));
		assert(!strcmp(bounded.value,"abcd"));
		assert(!strcmp(bounded.guard,"end"));
		assert(Xstrncpy(bounded.value,"abc",sizeof bounded.value));
		assert(!strcmp(bounded.value,"abc"));
		assert(Xstrncpy(overlap_left,overlap_left+2,sizeof overlap_left));
		assert(!strcmp(overlap_left,"cdef"));
		assert(Xstrncpy(overlap_right+1,overlap_right,
		                sizeof overlap_right - 1));
		assert(!strcmp(overlap_right,"aabc"));
		assert(!Xstrncpy(unchanged,"drop",0));
		assert(!strcmp(unchanged,"keep"));
		assert(!Xstrncpy(one,"value",sizeof one));
		assert(!one[0]);
		assert(!Xstrncpy(NULL,"value",5));
		assert(!Xstrncpy(unchanged,NULL,sizeof unchanged));
	}
	{
		struct {
			char value[6];
			char guard[4];
		} bounded = { "abc", "end" };
		char overlap[8] = "abc";
		char one[1] = { 'x' };
		char unterminated[4] = { 'a', 'b', 'c', 'd' };
		char unchanged[5] = "keep";

		assert(!Xstrncat(bounded.value,"def",sizeof bounded.value));
		assert(!strcmp(bounded.value,"abc"));
		assert(!strcmp(bounded.guard,"end"));
		assert(Xstrncat(overlap,overlap,sizeof overlap));
		assert(!strcmp(overlap,"abcabc"));
		assert(!Xstrncat(unterminated,"x",sizeof unterminated));
		assert(!memcmp(unterminated,"abcd",sizeof unterminated));
		assert(!Xstrncat(unchanged,"drop",0));
		assert(!strcmp(unchanged,"keep"));
		assert(!Xstrncat(one,"value",sizeof one));
		assert(one[0]=='x');
		assert(!Xstrncat(NULL,"value",5));
		assert(!Xstrncat(unchanged,NULL,sizeof unchanged));
	}
	{
		char tiny[2] = "x";
		char transactional[8] = "base";
		word_form form = { 0 };

		set_dialect(&item,(Dialect)ATTIC);
		assert(!DialectNames(dialect_of(&item),tiny,sizeof tiny," "));
		assert(!tiny[0]);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		set_morphflag(morphflags_of(&item),SYLL_AUGMENT);
		assert(!MorphNames(morphflags_of(&item),tiny,sizeof tiny," ",NO));
		assert(!tiny[0]);
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		set_tense(form,PRESENT);
		assert(!AddParadigmInfo(transactional,sizeof transactional,
		                        form," "));
		assert(!strcmp(transactional,"base"));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
		assert(!SprintGkFlags(&item,transactional,sizeof transactional,
		                      " ",NO));
		assert(!strcmp(transactional,"base"));
		assert(morpheus_runtime_context_error(context) ==
		       MORPHEUS_RUNTIME_ERROR_INTERNAL);
		morpheus_runtime_context_clear_error(context);
	}
	assert(add_domain(&item,1) == 1);
	assert(add_domain(&item,1) == 0);
	assert(add_domain(&item,0) == -1);
	assert(add_domain(&item,256) == -1);
	assert(add_domain(NULL,1) == -1);
	assert(morpheus_runtime_context_error(context) ==
	       MORPHEUS_RUNTIME_ERROR_INTERNAL);
	morpheus_runtime_context_clear_error(context);
	{
		void (*mutators[])(gk_string *, unsigned long) = {
			new_person, new_number, new_case, new_tense, new_voice,
			new_mood, new_degree, new_gender, new_dialect, new_region,
			new_morphflags, new_stemtype, new_domain, new_derivtype
		};
		size_t i;

		for (i = 0; i < sizeof mutators / sizeof mutators[0]; i++) {
			mutators[i](NULL,1);
			assert(morpheus_runtime_context_error(context) ==
			       MORPHEUS_RUNTIME_ERROR_INTERNAL);
			morpheus_runtime_context_clear_error(context);
		}
	}
	set_morphflag(morphflags_of(&item),8);
	assert(morphflags_of(&item)[0] == (MorphFlags)0200);
	add_morphflag(morphflags_of(&item),9);
	assert(morphflags_of(&item)[1] == (MorphFlags)1);
	zap_morphflag(morphflags_of(&item),8);
	assert(morphflags_of(&item)[0] == (MorphFlags)0);
	new_person(&item,PERS3);
	new_case(&item,NOMINATIVE);
	new_case(&item,ACCUSATIVE);
	new_gender(&item,MASCULINE);
	new_gender(&item,FEMININE);
	assert(person_of(forminfo_of(&item)) == PERS3);
	assert(case_of(forminfo_of(&item)) == (NOMINATIVE | ACCUSATIVE));
	assert(gender_of(forminfo_of(&item)) == (MASCULINE | FEMININE));

	set_gkstring(&item,"beta");
	add_morphflag(morphflags_of(&item),POETIC);
	ClearGkstring(&item);
	assert(!gkstring_of(&item)[0]);
	assert(no_morphflags(&item));

	set_gkstring(&item,"beta");
	length = xInsertGstr(entries,&item,length,compare_text,NO);
	set_gkstring(&item,"alpha");
	length = xInsertGstr(entries,&item,length,compare_text,NO);
	set_gkstring(&item,"gamma");
	length = xInsertGstr(entries,&item,length,compare_text,NO);

	assert(length == 3);
	assert(!strcmp(gkstring_of(entries),"alpha"));
	assert(!strcmp(gkstring_of(entries+1),"beta"));
	assert(!strcmp(gkstring_of(entries+2),"gamma"));

	{
		gk_string empty = { 0 };
		gk_string parsed = { 0 };
		gk_word parsed_word = { 0 };
		MorphFlags flags[MORPHFLAG_STORAGE_BYTES] = { 0 };
		char *oddkeys;
		char simple[MAXWORDSIZE] = "logos";
		char word[MAXWORDSIZE] = { 0 };

		set_lang(GREEK);
		putsimpleacc(simple);
		assert(simple[0]);
		FixPersAcc(&empty,flags,&empty,"",word,(word_form){ 0 },0);
		assert(!word[0]);

		assert(!ScanAsciiKeys("codex_unknown_a",&parsed_word,&parsed,NULL));
		assert(oddkeys_of(&parsed_word));
		assert(!strcmp(oddkeys_of(&parsed_word),"codex_unknown_a"));
		oddkeys = oddkeys_of(&parsed_word);
		assert(!ScanAsciiKeys("codex_unknown_b",&parsed_word,&parsed,NULL));
		assert(oddkeys_of(&parsed_word) == oddkeys);
		assert(!strcmp(oddkeys_of(&parsed_word),"codex_unknown_b"));
		free(oddkeys_of(&parsed_word));
	}
	morpheus_runtime_context_activate(previous);
	morpheus_runtime_context_destroy(context);
	return(0);
}
