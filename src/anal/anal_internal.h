/* SPDX-License-Identifier: MPL-2.0 */

#ifndef MORPHEUS_ANAL_INTERNAL_H
#define MORPHEUS_ANAL_INTERNAL_H

#include <gkstring.h>
#include <prntflags.h>

#include "checkcrasis.proto.h"
#include "checkdict.proto.h"
#include "checkgenwds.proto.h"
#include "checkhalf1.proto.h"
#include "checkindecl.proto.h"
#include "checkirreg.proto.h"
#include "checknom.proto.h"
#include "checkpreverb.proto.h"
#include "checkstem.proto.h"
#include "checkstring.proto.h"
#include "checkverb.proto.h"
#include "checkword.proto.h"
#include "dictstems.proto.h"
#include "prntanal.proto.h"
#include "prvb.proto.h"

#include "../gkdict/compnoun.proto.h"
#include "../gener/genwd.proto.h"
#include "../greeklib/Fclose.proto.h"
#include "../greeklib/addbreath.proto.h"
#include "../greeklib/beta_tolower.proto.h"
#include "../greeklib/checkaccent.proto.h"
#include "../greeklib/getbreath.proto.h"
#include "../greeklib/hasaccent.proto.h"
#include "../greeklib/isblank.proto.h"
#include "../greeklib/issubstring.proto.h"
#include "../greeklib/isdiphth.proto.h"
#include "../greeklib/naccents.proto.h"
#include "../greeklib/nsylls.proto.h"
#include "../greeklib/sprntGkflags.proto.h"
#include "../greeklib/standword.proto.h"
#include "../greeklib/stripacc.proto.h"
#include "../greeklib/stripacute.proto.h"
#include "../greeklib/stripbreath.proto.h"
#include "../greeklib/stripdiaer.proto.h"
#include "../greeklib/stripmeta.proto.h"
#include "../greeklib/stripquant.proto.h"
#include "../greeklib/subchar.proto.h"
#include "../greeklib/xstrings.proto.h"
#include "../greeklib/zap2ndbreath.proto.h"
#include "../morphlib/augment.proto.h"
#include "../morphlib/beta2smarta.proto.h"
#include "../morphlib/cmpend.proto.h"
#include "../morphlib/gkstring.proto.h"
#include "../morphlib/is_thirdmono.proto.h"
#include "../morphlib/morphflags.proto.h"
#include "../morphlib/morphkeys.proto.h"
#include "../morphlib/morphstrcmp.proto.h"
#include "../morphlib/nextkey.proto.h"
#include "../morphlib/preverb2.proto.h"
#include "../morphlib/preverb3.proto.h"
#include "../morphlib/setlang.proto.h"

int chckindecl(char *indeclinable, char *lemmas);
int chckirrverb(char *irregular, char *lemmas);
int chckstem(char *stem, char *stem_keys, int is_noun);
int chckcmpvb(char *ending, char *keys);
int compound_verb_lemma(const char *preverbs, const char *lemma,
                        char *name, size_t size);
int chckend(char *ending);
int chcknend(char *ending, char *keys);
int chckvend(char *ending, char *keys);

int cntlems(gk_word *word);
int is_article(gk_word *word);
void end_phrase(gk_word *candidate, gk_word *word);
int show_totanals(void);
int show_totlems(void);
void set_nocrasis(void);

#endif
