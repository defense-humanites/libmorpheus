/* SPDX-License-Identifier: MPL-2.0 */

#include "derivation.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <gkstring.h>
#include <contract.h>
#include <libfiles.h>

#include "../gkends/gkends_internal.h"
#include "../greeklib/greeklib_internal.h"
#include "../morphlib/morphlib_internal.h"

typedef struct {
	gk_string constraints;
	Stemtype principal_part;
	char suffix[MAXWORDSIZE];
	char odd_keys[LONGSTRING * 2];
	char preverb[MAXWORDSIZE];
} derivation_request;

static int
copy_text(char *destination, size_t capacity, const char *source)
{
	int length;

	if (!destination || !capacity || !source)
		return 0;
	length = snprintf(destination,capacity,"%s",source);
	return length >= 0 && (size_t)length < capacity;
}

static int
join_keys(char *destination, size_t capacity, const char *left,
          const char *right)
{
	int length;

	if (!*left)
		return copy_text(destination,capacity,right);
	if (!*right)
		return copy_text(destination,capacity,left);
	length = snprintf(destination,capacity,"%s %s",left,right);
	return length >= 0 && (size_t)length < capacity;
}

static int
parse_request(const char *global_keys, const char *request_keys,
              derivation_request *request)
{
	const gk_string blank = { 0 };
	char local[LONGSTRING];
	char parsed_keys[LONGSTRING * 2];
	char principal_name[MAXWORDSIZE];
	char principal_key[MAXWORDSIZE];
	char *cursor;
	gk_word *word;
	int name_length;

	if (!copy_text(local,sizeof local,request_keys))
		return 0;
	for (cursor = local; *cursor && !isspace((unsigned char)*cursor); cursor++) {
		if (*cursor == ',')
			*cursor = ' ';
	}
	if (!nextkey(local,principal_key) || !*principal_key)
		return 0;
	name_length = snprintf(principal_name,sizeof principal_name,
	                       "pp_%s",principal_key);
	if (name_length < 0 || (size_t)name_length >= sizeof principal_name)
		return 0;
	request->principal_part = GetStemClass(principal_name);
	if (request->principal_part == 0 ||
	    request->principal_part == (Stemtype)-1)
		return 0;

	request->suffix[0] = 0;
	if (*local == '-') {
		if (!nextkey(local,request->suffix))
			return 0;
		memmove(request->suffix,request->suffix + 1,
		        strlen(request->suffix));
	}
	if (!join_keys(parsed_keys,sizeof parsed_keys,global_keys,local))
		return 0;

	request->constraints = blank;
	request->odd_keys[0] = 0;
	request->preverb[0] = 0;
	word = CreatGkword(1);
	if (!word)
		return 0;
	ScanAsciiKeys(parsed_keys,word,&request->constraints,NULL);
	add_morphflags(&request->constraints,
	               morphflags_of(prvb_gstr_of(word)));
	if (oddkeys_of(word) &&
	    !copy_text(request->odd_keys,sizeof request->odd_keys,
	               oddkeys_of(word))) {
		FreeGkword(word);
		return 0;
	}
	if (!copy_text(request->preverb,sizeof request->preverb,
	               preverb_of(word))) {
		FreeGkword(word);
		return 0;
	}
	set_gkstring(&request->constraints,endstring_of(word));
	add_morphflag(morphflags_of(&request->constraints),IS_DERIV);
	FreeGkword(word);
	return 1;
}

static int
suffix_matches(const char *rule_suffix, const char *requested_suffix)
{
	char unmarked[MAXWORDSIZE];

	if (!strcmp(rule_suffix,requested_suffix))
		return 1;
	if (!copy_text(unmarked,sizeof unmarked,rule_suffix))
		return 0;
	stripshortmark(unmarked);
	return !strcmp(unmarked,requested_suffix);
}

static int
conjoin_rule(gk_string *rule, char *word)
{
	gk_string *contracted;
	size_t word_length = strlen(word);
	size_t ending_length = strlen(gkstring_of(rule));

	if (word_length + ending_length >= MAXWORDSIZE)
		return 0;
	memcpy(word + word_length,gkstring_of(rule),ending_length + 1);
	set_gkstring(rule,word);
	contracted = do_euph(rule,(Dialect)0);
	if (!contracted)
		return 1;
	*rule = *contracted;
	return copy_text(word,MAXWORDSIZE,gkstring_of(contracted));
}

static void
make_passive_stem(char *stem, gk_string *rule)
{
	gk_string *table;
	char replacement[MAXWORDSIZE];
	char stem_name[MAXWORDSIZE];
	int count;
	int index;

	if (!*stem || Is_vowel(*(lastn(stem,1))))
		return;
	table = load_euph_tab(PPASSLIST,&count,NO);
	if (!table)
		return;
	for (index = 0; index < count; index++) {
		const char *entry = gkstring_of(table + index);
		const char *suffix = entry;

		if (!ends_in(stem,suffix))
			continue;
		if (!copy_text(replacement,sizeof replacement,stem) ||
		    !copy_text(stem_name,sizeof stem_name,
		               entry + MAXSUBSTRING))
			break;
		replacement[strlen(replacement) - strlen(suffix)] = 0;
		copy_text(stem,MAXWORDSIZE,replacement);
		set_stemtype(rule,GetStemNum(stem_name));
		break;
	}
	FreeGkString(table);
}

static int
write_rule(FILE *output, derivation_request *request,
           gk_string *rule, const char *stem)
{
	char flags[LONGSTRING];
	char word[MAXWORDSIZE];
	Stemtype principal_part = stemtype_of(rule) & PPARTMASK;
	int root_preverb;

	if (!copy_text(word,sizeof word,stem))
		return -1;
	if (has_morphflag(morphflags_of(&request->constraints),PRES_REDUPL))
		pres_redupl(word);
	if (has_morphflag(morphflags_of(&request->constraints),N_INFIX))
		addninfix(word);

	if (*gkstring_of(rule) != '*') {
		char *ending = gkstring_of(rule);

		if (Is_vowel(*ending) && !is_diphth(ending + 1,ending) &&
		    *word && Is_vowel(*(lastn(word,1)))) {
			char pair[3];

			pair[0] = *(lastn(word,1));
			pair[1] = *ending;
			pair[2] = 0;
			if (is_diphth(pair + 1,pair))
				addaccent(ending,DIAERESIS,ending);
		}
		if (*stem == ROUGHBR || *stem == SMOOTHBR) {
			if (!copy_text(word,sizeof word,ending))
				return -1;
			addbreath(word,*stem);
		} else {
			if (!conjoin_rule(rule,word))
				return -1;
		}
	}

	if (principal_part == PP_PF || principal_part == PP_PP ||
	    principal_part == PP_FP) {
		if (!has_morphflag(morphflags_of(&request->constraints),NO_REDUPL))
			simpleredupit(
			    word,
			    has_morphflag(morphflags_of(&request->constraints),SYLL_AUG),
			    'e');
		if (Is_primconj(rule)) {
			if (principal_part == PP_PF)
				fixperf(word);
			else if (principal_part == PP_PP)
				make_passive_stem(word,rule);
		}
	}
	if (do_dissim(word,principal_part))
		add_morphflag(morphflags_of(&request->constraints),DISSIMILATION);

	if (dialect_of(&request->constraints)) {
		Dialect dialect = AndDialect(dialect_of(&request->constraints),
		                             dialect_of(rule));

		if (dialect < 0)
			return 0;
		if (!dialect_of(rule))
			set_dialect(rule,dialect);
		else
			set_dialect(rule,dialect_of(&request->constraints));
	}
	add_morphflags(rule,morphflags_of(&request->constraints));
	zap_morphflag(morphflags_of(rule),IS_DERIV);
	zap_morphflag(morphflags_of(rule),R_E_I_ALPHA);

	if (voice_of(forminfo_of(&request->constraints))) {
		unsigned int voice = voice_of(forminfo_of(&request->constraints));

		if (voice == MEDIO_PASS) {
			if (has_passive_stype(stemtype_of(rule)))
				set_voice(forminfo_of(rule),PASSIVE);
			else if (has_middle_stype(stemtype_of(rule)))
				set_voice(forminfo_of(rule),MIDDLE);
			else
				set_voice(forminfo_of(rule),MEDIO_PASS);
		} else {
			if (voice == ACTIVE)
				set_voice(forminfo_of(rule),ACTIVE);
			else if (voice == MIDDLE)
				set_voice(forminfo_of(rule),MIDDLE);
			else if (voice == PASSIVE)
				set_voice(forminfo_of(rule),PASSIVE);
		}
	}
	if (tense_of(forminfo_of(&request->constraints)))
		set_tense(forminfo_of(rule),
		          tense_of(forminfo_of(&request->constraints)));
	if (mood_of(forminfo_of(&request->constraints)))
		set_mood(forminfo_of(rule),
		         mood_of(forminfo_of(&request->constraints)));
	if (person_of(forminfo_of(&request->constraints)))
		set_person(forminfo_of(rule),
		           person_of(forminfo_of(&request->constraints)));
	if (number_of(forminfo_of(&request->constraints)))
		set_number(forminfo_of(rule),
		           number_of(forminfo_of(&request->constraints)));

	root_preverb = has_morphflag(morphflags_of(rule),ROOT_PREVERB);
	zap_morphflag(morphflags_of(rule),ROOT_PREVERB);
	if (!copy_text(domains_of(rule),sizeof domains_of(rule),
	               domains_of(&request->constraints)))
		return -1;
	flags[0] = 0;
	if (!SprintGkFlags(rule,flags,sizeof flags," ",0))
		return -1;

	if (stemtype_of(rule) & PPARTMASK)
		fputs(":vs:",output);
	else if (stemtype_of(rule) & ADJSTEM)
		fputs(":aj:",output);
	else if (stemtype_of(rule) & NOUNSTEM)
		fputs(":no:",output);
	else
		return -1;
	fprintf(output,"%s %s",word,flags);
	if (*gkstring_of(&request->constraints))
		fprintf(output," end:%s",gkstring_of(&request->constraints));
	if (*request->preverb)
		fprintf(output," %s:%s",root_preverb ? "rpb" : "pb",
		        request->preverb);
	if (*request->odd_keys)
		fprintf(output," %s",request->odd_keys);
	if (fputc('\n',output) == EOF)
		return -1;
	return 1;
}

static int
rule_matches(const derivation_request *request, const gk_string *rule)
{
	Stemtype stem_type = stemtype_of(rule);

	if ((stem_type & PPARTMASK) != request->principal_part &&
	    (stem_type & ADJSTEM) != request->principal_part &&
	    (stem_type & NOUNSTEM) != request->principal_part)
		return 0;
	return !*request->suffix ||
	       suffix_matches(gkstring_of(rule),request->suffix);
}

int
morpheus_gener_expand_derivation(FILE *output, const char *stem,
                                 const char *derivation,
                                 const char *global_keys,
                                 const char *request_keys)
{
	char table_path[MAXPATHNAME];
	char line[BUFSIZ];
	derivation_request request;
	FILE *table;
	int path_length;

	if (!output || !stem || !*stem || !derivation || !*derivation ||
	    !global_keys || !request_keys || !*request_keys)
		return -1;
	path_length = snprintf(table_path,sizeof table_path,
	                       "derivs:ascii:%s.asc",derivation);
	if (path_length < 0 || (size_t)path_length >= sizeof table_path)
		return -1;
	table = MorphFopen(table_path,"r");
	if (!table)
		return -1;
	if (!parse_request(global_keys,request_keys,&request)) {
		fclose(table);
		return -1;
	}

	while (fgets(line,sizeof line,table)) {
		const gk_string blank = { 0 };
		char suffix[MAXWORDSIZE];
		gk_string rule = blank;
		gk_word *word;
		int result;

		if (is_blank(line) || Is_comment(line))
			continue;
		if (!nextkey(line,suffix)) {
			fclose(table);
			return -1;
		}
		word = CreatGkword(1);
		if (!word) {
			fclose(table);
			return -1;
		}
		result = ScanAsciiKeys(line,word,&rule,NULL);
		FreeGkword(word);
		/* Historical binary tables retain non-generating rule rows. */
		if (result <= 0)
			continue;
		set_gkstring(&rule,suffix);
		if (!rule_matches(&request,&rule))
			continue;
		if (stemtype_of(&request.constraints) &&
		    stemtype_of(&request.constraints) != stemtype_of(&rule))
			continue;
		if ((stemtype_of(&rule) & PPARTMASK) == PP_PF &&
		    (voice_of(forminfo_of(&request.constraints)) & MEDIO_PASS))
			continue;
		if (!WantGkEnd(&request.constraints,&rule,NO,NO))
			continue;
		result = write_rule(output,&request,&rule,stem);
		fclose(table);
		return result;
	}
	if (ferror(table)) {
		fclose(table);
		return -1;
	}
	fclose(table);
	return 0;
}
