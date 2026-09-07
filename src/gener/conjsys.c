/* SPDX-License-Identifier: MPL-2.0 */

#include "conjugation_internal.h"
#include "../morphlib/setlang.proto.h"
#include <gkstring.h>
#include <string.h>

static int scan_keys(char *text, gk_word *word, gk_string *want, gk_string *avoid)
{
    int result = ScanAsciiKeys(text, word, want, avoid);
    free(oddkeys_of(word));
    oddkeys_of(word) = NULL;
    return result;
}


#define DEFPPARTS 1
char *fullkeys[] = {
        "pr",
        "fu",
        "ao",
        "pf",
        "pp",
        "ap",
        "fp",
        "p4",
        "va",
        "vn"
        };

void dummyfnc(void)
{
}

static char curlemma[MAXWORDSIZE*2];
static	char linebuf[LONGSTRING];
static	char origline[LONGSTRING];
static	char stembuf[MAXWORDSIZE];
static	char derivbuf[LONGSTRING];

static	char savekeys[LONGSTRING];
static	char globalkeys[LONGSTRING];
static	char vsbuf[LONGSTRING];
static	char cobuf[LONGSTRING];
static int npparts = -1;
static int wantpparts = 0;

int fullconj = 0;

static int implicit_defaults(void)
{
    /* Latin's committed short index includes regular present-stem defaults;
     * Greek short production expands only irregular defaults. */
    return cur_lang() == LATIN ? regular_entry(derivbuf) : irreg_conj();
}

int GenConjForms(FILE * fin, FILE * fout, int conjmode)
{
    char * lp;
    char saveline[LONGSTRING];

    fullconj = conjmode;

    while(fgets(linebuf,sizeof linebuf,fin) ) {
        if (!strchr(linebuf, '\n') && !feof(fin)) conj_fail("oversized input line");
        if (linebuf[0] == ':' && strncmp(linebuf, ":le:", 4) && !curlemma[0]) conj_fail("record precedes lemma");
        conj_copy(saveline, linebuf, sizeof saveline);
        if( !strncmp(linebuf,"@fullconj",strlen("@fullconj")) )  {
            fullconj = 1;
            continue;
        }
        if( ! strncmp(linebuf,"@shortconj",strlen("@shortconj")) ) {
            fullconj = 0;
            continue;
        }

        if( ! strncmp(linebuf,":le:",4) ) {

            if( ! npparts && wantpparts && (implicit_defaults() || fullconj)) {
                show_defvals(fout);
                fprintf(fout,"\n");
            }
            vsbuf[0] = cobuf[0] = 0;
            npparts = 0;
            wantpparts = 0;
            fprintf(fout,"%s", linebuf);
            set_newlemma(linebuf);
            continue;
        }

        if( has_pref(linebuf,":vs:" ) ) {
            wantpparts = 0;
            derivbuf[0] = 0;
            conj_copy(vsbuf, linebuf, sizeof vsbuf);
            fprintf(fout,"%s", linebuf );
            continue;
        }

        if( has_pref(linebuf,":aj:")
         || has_pref(linebuf,":no:") ) {
            wantpparts = 0;
            derivbuf[0] = 0;
            fprintf(fout,"%s", linebuf );
            continue;
        }

        if( ! strncmp(":de:",linebuf,4) ) {
            if( ! npparts && wantpparts && (implicit_defaults() || fullconj)) {
                show_defvals(fout);
                fprintf(fout,"\n");
            }
            npparts = 0;
            wantpparts = 1;
            if( linebuf[strlen(linebuf)-1] == '\n' )
                    linebuf[strlen(linebuf)-1] = 0;
            conj_copy(origline, linebuf, sizeof origline);
            conj_key(linebuf,stembuf,sizeof stembuf);
            conj_copy(stembuf, stembuf+4, sizeof stembuf);
            conj_key(linebuf,globalkeys,sizeof globalkeys);

             lp = globalkeys;
             while(*lp) {
                if(*lp == ',') *lp = ' ';
                lp++;
             }

             conj_key(globalkeys,derivbuf,sizeof derivbuf);
             if (!stembuf[0] || !derivbuf[0] || strspn(derivbuf,"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_") != strlen(derivbuf)) conj_fail("invalid derivation name or stem");
             if( * globalkeys ) {
                conj_append(globalkeys," ",sizeof globalkeys);
             }
             conj_append(globalkeys,linebuf,sizeof globalkeys);
            if( ! fullconj && ! regular_entry(derivbuf) )
                fprintf(fout,"-");
            fprintf(fout,"%s", saveline );

            if(noppart(linebuf)){

                int i;

                char tkeys[LONGSTRING*2];
                conj_format(tkeys,sizeof tkeys,"%s %s", fullkeys[0] , linebuf );

            } else {
                if( ! combine_conj(fout,curlemma,origline,stembuf,derivbuf,globalkeys,linebuf) ) {
                    conj_fail("unmatched explicit principal part");
                }

            }
            continue;

        }
        if( linebuf[0] == ';' ) {
                if (!derivbuf[0]) conj_fail("principal part without derivation");
                char tkeys[LONGSTRING*2];
                size_t len;
                int rval;
                char *s;

                fprintf(fout,"%s", linebuf );
                conj_copy(cobuf, linebuf, sizeof cobuf);
                s = cobuf;
                while(*s&&!isspace((unsigned char)*s)) s++;
                while(isspace((unsigned char)*s))s++;
                while(*s&&!isspace((unsigned char)*s)) s++;
                *s = 0;

                len = strlen(linebuf);
                if( len && linebuf[len-1] == '\n') linebuf[len-1] = 0;

                conj_copy(tkeys, linebuf+1 , sizeof tkeys);
                conj_copy(savekeys, linebuf+1, sizeof savekeys);
                s = savekeys;
                while(*s&&!isspace((unsigned char)*s)) s++;
                if( isspace((unsigned char)*s) ) *(s++) = 0;

                if( ! need_ppart(tkeys) && has_alpha(stembuf) ) {
                    continue;
                }

                npparts++;
                rval = combine_conj(fout,curlemma,origline,stembuf,derivbuf,globalkeys,tkeys);
                if( ! rval ) {
                    conj_fail("unmatched explicit principal part");
printf("rval %d stembuf [%s] global [%s] deriv [%s] tk [%s]\n", rval,
                    stembuf , globalkeys, derivbuf, tkeys );
}
                continue;
        }
        if( linebuf[0] == '@') {
                if (!curlemma[0] ) conj_fail("orphan continuation");
                char tkeys[LONGSTRING*2];
                size_t len;
                int rval;

                if( ! derivbuf[0] ) {
                    if( ! fullconj ) {
                        check_vsdupl(linebuf,fout);
                    } else
                        fprintf(fout,"%s", linebuf );
                    continue;
                }
                npparts++;
                fprintf(fout,"-%s", linebuf );

                if( ! need_codupl(linebuf) && has_alpha(stembuf) ) continue;

                len = strlen(linebuf);
                if( len && linebuf[len-1] == '\n') linebuf[len-1] = 0;

                conj_format(tkeys,sizeof tkeys, "%s %s", savekeys, linebuf+1 );
                if( ! need_ppart(tkeys)  )
                    continue;
                rval = combine_conj(fout,curlemma,origline,stembuf,derivbuf,globalkeys,tkeys);
                if( ! rval )
                    conj_fail("unmatched continuation principal part");

                continue;
        }

        fprintf(fout,"%s", linebuf );

    }
    if( ! npparts && wantpparts && (implicit_defaults() || fullconj ) )
            show_defvals(fout);

    return curlemma[0] && !ferror(fin) && !ferror(fout);
}

void show_defvals(FILE * fout)
{
    int i;

    for(i=0;i< DEFPPARTS;i++) {
        char tkeys[LONGSTRING*2];
        conj_format(tkeys,sizeof tkeys,"%s ", fullkeys[i]  );
        if (!combine_conj(fout,curlemma,origline,stembuf,derivbuf,globalkeys,tkeys))
            conj_fail("unmatched implicit principal part");

    }

}
void set_newlemma(char * s)
{
    s[strcspn(s, "\r\n")] = 0;
    if (!s[4]) conj_fail("empty lemma");
    conj_copy(curlemma, s+4, sizeof curlemma);
    derivbuf[0] = 0;
}

int noppart(char * s)
{
    char buf1[LONGSTRING];
    char buf2[LONGSTRING] = {0};
    int i;

    if(is_empty(s) ) return(1);

    conj_copy(buf1, s, sizeof buf1);
    conj_key(buf1,buf2,sizeof buf2);

    if( ! buf2[0] ) return(1);

    if(buf2[2] && buf2[2] != ',' && ! isspace((unsigned char)buf2[2]) ) {
        return(1);
    }
    for(i=0;i<sizeof fullkeys/sizeof fullkeys[0];i++)
        if( ! strncmp(fullkeys[i],buf2,2) ) {
            return(0);
        }
    return(1);

}

int is_empty(char * s)
{
    while(*s) {
        if( !isspace((unsigned char)*s++) ) return(0);
    }
    return(1);
}

int has_pref(char * s, char * pref)
{
    return(strncmp(s,pref,strlen(pref)) == 0 );
}

static gk_string   BlnkGstr;
static gk_word BlnkGkword;
int need_ppart(char * s)
{
    gk_string  GlobGstr, CurGstr;
    gk_word TmpGkword;
    char tmpkeys[LONGSTRING];
    char tmpglobs[LONGSTRING*2+2];
    int rval;

    if( fullconj )
        return(1);

    while(*s&&!isspace((unsigned char)*s)&&*s!=',') s++;
    if(*s == ',' ) {
        s++;
        if(*s == '-' ) {
            while(*s&&*s!=','&&!isspace((unsigned char)*s)) s++;
            if(*s ==',') s++;
        }
    }
    conj_copy(tmpkeys, s, sizeof tmpkeys);
    s = tmpkeys;

    while(*s&&!isspace((unsigned char)*s)) {
        if(*s == ',' ) *s = ' ';
        s++;
    }

    conj_format(tmpglobs,sizeof tmpglobs,"%s %s\n", derivbuf , globalkeys );
    GlobGstr = CurGstr = BlnkGstr;
    TmpGkword = BlnkGkword;
    scan_keys(tmpglobs,&TmpGkword,&GlobGstr,NULL);

    if( ! Is_regconj(&GlobGstr) ) return(1);

    if( has_morphflag(morphflags_of(&GlobGstr),N_INFIX) ||
        has_morphflag(morphflags_of(&GlobGstr),NO_REDUPL ) ||
        has_morphflag(morphflags_of(&GlobGstr),PRES_REDUPL) ) {
            return(1);
    }

    TmpGkword = BlnkGkword;
    scan_keys(tmpkeys,&TmpGkword,&CurGstr,NULL);
    if( has_morphflag(morphflags_of(&CurGstr),N_INFIX) ||
        has_morphflag(morphflags_of(&CurGstr),NO_REDUPL ) ||
        has_morphflag(morphflags_of(&CurGstr),SYLL_AUG ) ||
        has_morphflag(morphflags_of(&CurGstr),PRES_REDUPL) ) {
            return(1);
    }
    rval = WantGkEnd(&GlobGstr,&CurGstr,NO,NO);

    return( rval <= 0 );
}

int check_vsdupl(char * s, FILE * fout)
{
    gk_string  GlobGstr, CurGstr;
    gk_word TmpGkword;
    char tmpvsbuf1[LONGSTRING];
    char tmpvsbuf2[LONGSTRING];
    char tmpglobs[LONGSTRING*2+2];
    int rval = 0;
    char *p;

    GlobGstr = CurGstr = BlnkGstr;
    TmpGkword = BlnkGkword;

    fprintf(fout,"-%s", s );
    if( fullconj ) return(1);

    conj_copy(tmpglobs, vsbuf, sizeof tmpglobs);
    p = tmpglobs;
    while(*p&&!isspace((unsigned char)*p)) p++;
    while(isspace((unsigned char)*p)) p++;
    while(*p&&!isspace((unsigned char)*p) ){
        if(*p==',') *p = ' ';
        p++;
    }
    conj_copy(tmpvsbuf1, tmpglobs, sizeof tmpvsbuf1);
    *p = 0;

    scan_keys(s+1,&TmpGkword,&CurGstr,NULL);
    if( has_morphflag(morphflags_of(&CurGstr),SYLL_AUG ) )
        rval = -1;

    conj_format(tmpvsbuf2,sizeof tmpvsbuf2,"%s%s", tmpglobs,s+1);

    p = tmpvsbuf1; while(*p && !isspace((unsigned char)*p)) p++;
    scan_keys(p,&TmpGkword,&GlobGstr,NULL);

    p = tmpvsbuf2; while(*p && !isspace((unsigned char)*p)) p++;
    scan_keys(p,&TmpGkword,&CurGstr,NULL);

    if( ! rval )
        rval = WantGkEnd(&GlobGstr,&CurGstr,NO,YES);

            if( rval <= 0 ) {
        fprintf(fout,"%s", tmpvsbuf2 );
        if( *(lastn(tmpvsbuf2,1)) != '\n' )
            fprintf(fout,"\n");
    }
    return(rval<=0);
}

int need_codupl(char * s)
{
    gk_string  GlobGstr, CurGstr;
    gk_word TmpGkword;
    char tmpcobuf1[LONGSTRING];
    char tmpcobuf2[LONGSTRING];
    char tmpglobs[LONGSTRING*2+2];
    int rval;
    char *p;

    GlobGstr = CurGstr = BlnkGstr;
    TmpGkword = BlnkGkword;

    if( fullconj ) return(1);

    conj_copy(tmpglobs, cobuf, sizeof tmpglobs);
    p = tmpglobs;
    while(*p&&!isspace((unsigned char)*p)) p++;
    while(isspace((unsigned char)*p)) p++;
    while(*p&&!isspace((unsigned char)*p) ){
        if(*p==',') *p = ' ';
        p++;
    }
    conj_copy(tmpcobuf1, tmpglobs, sizeof tmpcobuf1);
    *p = 0;
    conj_format(tmpcobuf2,sizeof tmpcobuf2,"%s%s", tmpglobs,s+1);

    p = tmpcobuf1; while(*p && !isspace((unsigned char)*p)&& *p !=',' ) p++;
    if(*p == ',' ) p++;
    scan_keys(p,&TmpGkword,&GlobGstr,NULL);

    p = tmpcobuf2; while(*p && !isspace((unsigned char)*p)&& *p !=',' ) p++;
    if(*p == ',' ) p++;
    scan_keys(p,&TmpGkword,&CurGstr,NULL);
    if( has_morphflag(morphflags_of(&CurGstr),SYLL_AUG ) ||
        has_morphflag(morphflags_of(&CurGstr),N_INFIX) ||
        has_morphflag(morphflags_of(&CurGstr),NO_REDUPL ))
        return(1);

    rval = WantGkEnd(&GlobGstr,&CurGstr,NO,YES);

    return(rval<=0);
}

int regular_entry(char * s)
{
    gk_string * gstr;
    gk_word * gkw;
    int rconj;

    gstr = CreatGkString(1);
    gkw = CreatGkword(1);
    if (!gstr || !gkw) conj_fail("allocation failure");

    scan_keys(s,gkw,gstr,NULL);

    rconj = Is_regconj(gstr);
    FreeGkString(gstr);
    FreeGkword(gkw);
    return(rconj);
}

int irreg_conj(void)
{
    gk_word TmpGkword;
    gk_string GlobGstr;
    GlobGstr = BlnkGstr;
    TmpGkword = BlnkGkword;

    scan_keys(derivbuf,&TmpGkword,&GlobGstr,NULL);

    return !Is_regconj(&GlobGstr);
}

int has_alpha(char * s)
{

    while(*s) {
        if(isalpha((unsigned char)*s) ) return(1);
        s++;
    }
    return(0);
}
