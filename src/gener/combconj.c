/* SPDX-License-Identifier: MPL-2.0 */

#include "conjugation_internal.h"
#include <gkstring.h>

static	char origformula[LONGSTRING];
static	char curlemma[LONGSTRING];

int combine_conj(FILE * fout, char * lemma, char * origline, char * stemstr, char * derivstr, char * globalkeys, char * localkeys)
{
    gk_string CurGstr;
    Stemtype ppartflag;
    char stembuf[MAXWORDSIZE];
    char suffbuf[MAXWORDSIZE];
    char oddkeys[LONGSTRING*2];
    char preverb[MAXWORDSIZE];

    preverb[0] = suffbuf[0] = oddkeys[0] = 0;
    conj_copy(origformula, origline, sizeof origformula);
    conj_copy(curlemma, lemma, sizeof curlemma);

    conj_copy(stembuf, stemstr, sizeof stembuf);

    ppartflag = ConjGkstr(&CurGstr,suffbuf,globalkeys,localkeys,oddkeys,preverb);

    if( DoConjStem(fout,derivstr,&CurGstr,suffbuf,ppartflag,stembuf,oddkeys,preverb) <= 0 ) {
        fprintf(stderr,"unmatched derivation: %s | %s | %s | %s\n",lemma,stemstr,derivstr,localkeys);
        return(0);
    } return(1);
}

int DoConjStem(FILE * fout, char * derivstr, gk_string * gstr, char * suffstr, Stemtype ppartflag, char * stemstr, char * oddptr, char * preverb)
{
    char derivfile[MAXPATHNAME];
    FILE * fderiv;
    int lno, maxend, i, rval;
    gk_string CurGstr;
    int gotstem = 0;

    conj_format(derivfile,sizeof derivfile,"derivs:out:%s.out", derivstr);

    if( (fderiv=MorphFopen(derivfile,"rb")) == NULL ) {
        fprintf(stderr,"could not open [%s] for %s\n", derivfile, derivstr );
        conj_fail("missing derivation table");
    }

    lno = get_endheader(fderiv,&maxend);
    if( lno < 0 ) {

        fclose(fderiv);
        conj_fail("invalid derivation table");
    }
    for(i=0;i<lno;i++ ) {
        rval=ReadEnding(fderiv,&CurGstr,maxend);

        if (rval <= 0 ) {
            fprintf(stdout,"hey! fname [%s] wanted [%d] endings got [%d]!\n", derivstr, lno , i );
            fclose(fderiv);
            conj_fail("truncated derivation table");
        }

        if( ((stemtype_of(&CurGstr) & PPARTMASK) == ppartflag ) ||
            ((stemtype_of(&CurGstr) & ADJSTEM) == ppartflag ) ||
            ((stemtype_of(&CurGstr) & NOUNSTEM) == ppartflag )) {

            if( *suffstr && !MatchSuff(gkstring_of(&CurGstr), suffstr))
                continue;
            if( (gotstem=CheckConjPpart(fout,derivstr,gstr,&CurGstr,stemstr,oddptr,preverb)) )
                break;
        }

    }

    fclose(fderiv);
    return(gotstem);
}

gk_string blnk;

Stemtype
ConjGkstr(gk_string * gstr, char * suffstr, char * globalkeys, char * keys, char * oddkeys, char * preverb)
{
    char keytmp[LONGSTRING*2];
    gk_word * TmpGkword;

    char * s;
    char ppartname[MAXWORDSIZE];
    char tmp[LONGSTRING*4];
    Stemtype stype;
    int npparts;

    *gstr = blnk;

    TmpGkword = CreatGkword(1);
    if (!TmpGkword) conj_fail("allocation failure");

    conj_copy(keytmp, keys, sizeof keytmp);

    s = keytmp;
    while(*s&&*s!=' ') {
        if(*s == ',' )
            *s = ' ';
        s++;
    }
    conj_copy(ppartname, "pp_", sizeof ppartname);
    conj_key(keytmp,ppartname+3,sizeof ppartname-3);

    stype = GetStemClass(ppartname);
    /* Stemtype is unsigned; GetStemClass uses its all-ones value for failure. */
    if (stype == 0 || stype == (Stemtype)-1) {
        fprintf(stderr,"unknown principal part: %s\n",ppartname+3);
        FreeGkword(TmpGkword);
        conj_fail("unknown principal part");
    }

    if( keytmp[0] == '-' ) {

        conj_key(keytmp,suffstr,MAXWORDSIZE);
        conj_copy(suffstr, suffstr+1, MAXWORDSIZE);
    }
    if( * globalkeys ) {
        char tmp[LONGSTRING*4];

        conj_format(tmp,sizeof tmp,"%s %s", globalkeys , keytmp);
        conj_copy(keytmp, tmp, sizeof keytmp);
    }

    ScanAsciiKeys(keytmp,TmpGkword,gstr,NULL);

    add_morphflags(gstr,morphflags_of(prvb_gstr_of(TmpGkword)) );

    if( oddkeys_of(TmpGkword) )
        conj_copy(oddkeys, oddkeys_of(TmpGkword) , LONGSTRING*2);
    else
        oddkeys[0] = 0;

    preverb[0] = 0;
    conj_copy(preverb, preverb_of(TmpGkword), MAXWORDSIZE);

    set_gkstring(gstr,endstring_of(TmpGkword) );

    add_morphflag(morphflags_of(gstr),IS_DERIV);

    FreeGkword(TmpGkword);

    if(stype > 0)
        return(stype);
    else { conj_fail("unknown principal part"); return 0; }

}

int CheckConjPpart(FILE * fout, char * derivstr, gk_string * gstr1, gk_string * gstr2, char * stemstr, char * oddptr, char * preverb)
{
    int rval, rpb_flag;
    char word[MAXWORDSIZE];
    char showbuf[LONGSTRING];
    Stemtype ppartflag;
    register char * ep = gkstring_of(gstr2);

    ppartflag = stemtype_of(gstr2) & PPARTMASK;

    if( ! dialect_of(gstr1) && !gkstring_of(gstr2)[0] )
        set_dialect(gstr1,(Dialect)ATTIC);

    if( stemtype_of(gstr1) && stemtype_of(gstr1) != stemtype_of(gstr2) ) {
        goto failure;
    }

    if( ppartflag == PP_PF && (voice_of(forminfo_of(gstr1)) & MEDIO_PASS) ) goto failure;
    rval=WantGkEnd(gstr1,gstr2,0,0);

    if( rval ) {
        Dialect d;

        conj_copy(word, stemstr, sizeof word);

        if( has_morphflag(morphflags_of(gstr1),PRES_REDUPL)) {
            pres_redupl(word);
        }

            if( has_morphflag(morphflags_of(gstr1),N_INFIX) )
                addninfix(word);
        if( *ep != '*' ) {

            if( Is_vowel(*ep) && ! is_diphth(ep+1,ep) && Is_vowel(*(lastn(word,1))) ) {

                char tmp[MAXWORDSIZE];
                tmp[0] = *(lastn(word,1));
                tmp[1] = *ep;
                tmp[2] = 0;
                if( is_diphth(tmp+1,tmp) )
                    addaccent(ep,DIAERESIS,ep);

            }
            if( *stemstr == ROUGHBR || * stemstr == SMOOTHBR ) {
                conj_copy(word, ep, sizeof word);
                addbreath(word,*stemstr);
            } else {
                conjoinX(gstr2,word,gkstring_of(gstr2));
            }
        }

    if( (ppartflag == PP_PF || ppartflag == PP_PP || ppartflag == PP_FP) ) {

            if( ! has_morphflag(morphflags_of(gstr1),NO_REDUPL) )
                simpleredupit(word,has_morphflag(morphflags_of(gstr1),SYLL_AUG),'e');

            if( Is_primconj(gstr2) ) {
                if( ppartflag == PP_PF ) fixperf(word);
                else if( ppartflag == PP_PP) makeppass(word,gstr2);

            }
        }

    if( do_dissim(word,ppartflag)) {
            add_morphflag(morphflags_of(gstr1),DISSIMILATION);
    }

        if( dialect_of(gstr1) ) {
            d = AndDialect(dialect_of(gstr1),dialect_of(gstr2));
            if( d < 0 ) goto failure;
            if( ! dialect_of(gstr2) )
                set_dialect(gstr2,d);
            else
                set_dialect(gstr2,dialect_of(gstr1));
        }

        add_morphflags(gstr2,morphflags_of(gstr1));

        zap_morphflag(morphflags_of(gstr2),IS_DERIV);
        zap_morphflag(morphflags_of(gstr2),R_E_I_ALPHA);

        if( voice_of(forminfo_of(gstr1)) ) {
            int v = voice_of(forminfo_of(gstr1));

            if( v == MEDIO_PASS ) {
                if( has_passive_stype(stemtype_of(gstr2)))
                    set_voice(forminfo_of(gstr2),PASSIVE);
                else if( has_middle_stype(stemtype_of(gstr2)))
                    set_voice(forminfo_of(gstr2),MIDDLE);
                else
                    set_voice(forminfo_of(gstr2),voice_of(forminfo_of(gstr1)));

            } else {
                set_voice(forminfo_of(gstr2),voice_of(forminfo_of(gstr1)));

            }
        }
        if( tense_of(forminfo_of(gstr1)) )
            set_tense(forminfo_of(gstr2),tense_of(forminfo_of(gstr1)));
        if( mood_of(forminfo_of(gstr1)) )
            set_mood(forminfo_of(gstr2),mood_of(forminfo_of(gstr1)));
        if( person_of(forminfo_of(gstr1)) )
            set_person(forminfo_of(gstr2),person_of(forminfo_of(gstr1)));
        if( number_of(forminfo_of(gstr1)) )
            set_number(forminfo_of(gstr2),number_of(forminfo_of(gstr1)));

        showbuf[0] = 0;

        if( has_morphflag(morphflags_of(gstr2),ROOT_PREVERB)) {
            rpb_flag = 1;
            zap_morphflag(morphflags_of(gstr2),ROOT_PREVERB);
        } else
            rpb_flag = 0;
        if( has_morphflag(morphflags_of(gstr2),R_E_I_ALPHA) )
            zap_morphflag(morphflags_of(gstr2),R_E_I_ALPHA);

        Xstrcpy(domains_of(gstr2),domains_of(gstr1));
        SprintGkFlags(gstr2,showbuf,sizeof showbuf," ",0);

        if( stemtype_of(gstr2) & PPARTMASK ) fprintf(fout,":vs:");
        else if( stemtype_of(gstr2) & ADJSTEM ) fprintf(fout,":aj:");
        else if( stemtype_of(gstr2) & NOUNSTEM ) fprintf(fout,":no:");
        else fprintf(fout,":??:");

        fprintf(fout,"%s ", word );
        fprintf(fout,"%s",  showbuf );
        if( gkstring_of(gstr1)[0] )  {
            fprintf(fout," end:%s", gkstring_of(gstr1) );
        }

        if( *preverb ) {
            char tmppb[MAXWORDSIZE*2];

            if( rpb_flag ) conj_copy(tmppb, "rpb:", sizeof tmppb);
            else conj_copy(tmppb, "pb:", sizeof tmppb);
            conj_append(tmppb,preverb,sizeof tmppb);
            fprintf(fout," %s", tmppb );
        }

        if( *oddptr ) {
            fprintf(fout," %s", oddptr);
            add_oddstuff(oddptr);
        }

        fputc('\n',fout);



    } else {
        goto failure;
    }
    return(1);
    failure:
        return(0);
}
FILE * morpheus_conj_odd_output;

void add_oddstuff(char *s)
{
    if (fprintf(morpheus_conj_odd_output,"%s\t%s\n",curlemma,s) < 0)
        conj_fail("odd-key output failed");
}

int MatchSuff(char * s1,char * s2)
{
    char tmp[BUFSIZ];

    if( !strcmp(s1,s2) ) return(1);
    conj_copy(tmp, s1, sizeof tmp);
    stripshortmark(tmp);
    if( !strcmp(s2,tmp) ) return(1);

    return(0);

}

gk_string *
 do_euph(gk_string *, Dialect );

gk_string BlnkGstr, Gstr;
void conjoinX(gk_string *gstr,char * s1,char * s2)
{
    int i;

    gk_string *newgstr;

    Gstr = BlnkGstr;
    conj_append(s1,s2,MAXWORDSIZE);

    set_gkstring(gstr,s1);

    newgstr = do_euph(gstr,(Dialect)0);

    if( ! newgstr ) {

        return;
    }

    *gstr = *newgstr;
    conj_copy(s1, gkstring_of(newgstr), MAXWORDSIZE);

    return;
}
