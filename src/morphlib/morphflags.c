#include "morphlib_internal.h"
#include <gkstring.h>

void add_morphflags(gk_string *gstr, MorphFlags * Flags)
{
	unsigned char * Mf = morphflags_of(gstr);
	int i;
	
	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++ ) 
		morphflags_of(gstr)[i] |= Flags[i];
}

void set_morphflags(gk_string *gstr, MorphFlags *Flags)
{
	unsigned char * Mf = morphflags_of(gstr);
	int i;
	
	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++ ) 
		morphflags_of(gstr)[i] = Flags[i];
}


void set_gwmorphflags(gk_word *gkword, MorphFlags *Flags)
{
	unsigned char * Mf = morphflags_of(gkword);
	int i;
	
	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++ ) 
		morphflags_of(gkword)[i] = Flags[i];
}


void zap_morphflags(gk_string *gstr, MorphFlags *Flags)
{
	unsigned char * Mf = morphflags_of(gstr);
	int i;
	
	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++ ) 
		morphflags_of(gstr)[i] &= ~(Flags[i]);
}

int has_morphflags(gk_string *gstr, MorphFlags *Flags)
{
	unsigned char * Mf = morphflags_of(gstr);
	int i;
	
	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++ ) 
		if( morphflags_of(gstr)[i] & Flags[i])
			return(1);
	return(0);
}

int no_morphflags(gk_string *gstr)
{
	MorphFlags * Mf = morphflags_of(gstr);
	int i;
	
	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++ ) 
		if( morphflags_of(gstr)[i] )
			return(0);
	return(1);
}

void add_morphflag(MorphFlags *Mf, int n)
{
	int index;
	MorphFlags setbit;

	if(n <= 0 || n > MORPHFLAG_MAX) return;
	mflag_num_to_bits(n,&index,&setbit);

	Mf[index] = (MorphFlags)(Mf[index] | setbit);
/*
morpheus_runtime_diagnostic("n [%d] index [%d] setbit [%o] Mf[index] [%o]\n", n , index, setbit, Mf[index]) ;
*/
}

int overlap_morphflags(MorphFlags *Mf1, MorphFlags *Mf2)
{
	int i;
	
	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++ ) 
		if( Mf1[i] & Mf2[i] ) return(1);
	return(0);
}

int has_morphflag(MorphFlags *Mf, int n)
{
	int index;
	MorphFlags setbit;

	if(n <= 0 || n > MORPHFLAG_MAX) return(0);
	mflag_num_to_bits(n,&index,&setbit);
/*	
morpheus_runtime_diagnostic("n %d , index %d setbit [%o] Mf[Index] %o anded [%o]\n", n,index, setbit,Mf[index],
Mf[index] & (setbit & 0377));
*/	
	return(Mf[index] & setbit);
}


void zap_morphflag(MorphFlags *Mf, int n)
{
	int index;
	MorphFlags setbit;

	if(n <= 0 || n > MORPHFLAG_MAX) return;
	mflag_num_to_bits(n,&index,&setbit);

	Mf[index] = (MorphFlags)(Mf[index] & (MorphFlags)~setbit);
}

void set_morphflag(MorphFlags *Mf, int n)
{
	int i;
	int index;
	MorphFlags setbit;

	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++) Mf[i] = 0;
	if(n < 0 || n > MORPHFLAG_MAX) return;
	if(n > 0) mflag_num_to_bits(n,&index,&setbit);
	if( n > 0 ) 
		Mf[index] = setbit;
}

int no_morphflag(MorphFlags *mf)
{
	int i;
	
	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++ ) 
		if( mf[i] )
			return(0);
	return(1);
}

void mflag_num_to_bits(int n, int *ind, MorphFlags *bitnum)
{
	if(n <= 0 || n > MORPHFLAG_MAX) {
		*ind = -1;
		*bitnum = 0;
		return;
	}
	if( (n % 8) == 0 ) {
		*ind = (n/8) - 1;
		*bitnum = (MorphFlags)0200;
	} else {
		*ind = n/8;
		*bitnum = (MorphFlags)(1U << (((unsigned int)n % 8U) - 1U));
	}
/*
morpheus_runtime_diagnostic("num to bits [%d] ind %o bit %o\n", n , *ind, *bitnum );
*/
}

int mflag_bit_to_num(int ind, int bitnum)
{

	return( (ind*8) + bitnum );
}

void Dump_morphflag(MorphFlags *mf)
{
	int i;
	
	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++ )
		printf("byte %d [%o]\n", i , mf[i] );
}

#define TABSIZE MORPHFLAG_STORAGE_BYTES*8 

int is_pretty_morphflag(long mnum)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();

	if(mnum <= 0 || mnum > TABSIZE) return(0);
	if( ! context->hidden_morphflag_table )
		if(!init_ugly_tab()) return(0);
	return( ! context->hidden_morphflag_table[(int)mnum] );
}

int init_ugly_tab(void)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	char *ugly_tab;

	if( context->hidden_morphflag_table ) return(1);
	ugly_tab = (char *)calloc((size_t)TABSIZE+1,(size_t)sizeof * ugly_tab );
	if( ! ugly_tab ) {
		morpheus_runtime_diagnostic("could not allocate morphflag display table\n");
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		return(0);
	}
	context->hidden_morphflag_table = ugly_tab;
	
	ugly_tab[PERS_NAME] = 1;
	ugly_tab[SUFF_ACC] = 1;
	ugly_tab[STEM_ACC] = 1;
	ugly_tab[ANT_ACC] = 1;
	ugly_tab[NO_COMP] = 1;
	ugly_tab[SHORT_PEN] = 1;
	ugly_tab[LONG_PEN] = 1;
	ugly_tab[ACCENT_OPTIONAL] = 1;
	ugly_tab[NEEDS_ACCENT] = 1;
/*
	ugly_tab[R_E_I_ALPHA] = 1;
*/
	ugly_tab[NOT_IN_COMPOSITION] = 1;
	ugly_tab[HAS_PREVERB] = 1;
	ugly_tab[HAS_AUGMENT] = 1;
	return(1);
}


int is_prvb_morphflag(long mnum)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();

	if(mnum <= 0 || mnum > TABSIZE) return(0);
	if( ! context->preverb_morphflag_table )
		if(!init_prvb_tab()) return(0);
	return( context->preverb_morphflag_table[(int)mnum] );
}
 

/*
 * The morph flags that belong to a preverb rather than to the word it is
 * attached to. init_prvb_tab() builds its lookup table from this list, and
 * xfer_prvbflags() moves them with preverb_morphflag_mask, built from it
 * too.
 *
 * After DOUBLED_CONS come the shapes of the preverb itself (e)s for ei)s,
 * cun for su/n...), which rstprevb() applies from the preverb's flags. Not
 * IOTA_INTENS, which also marks the deictic iota of a word (e)keinosi/) and
 * must stay in the stem keys the stemlib build writes.
 */
#define PREVERB_MORPHFLAGS(X, byte) \
	X(DISSIMILATION, byte) \
	X(PREVB_AUGMENT, byte) \
	X(ELIDE_PREVERB, byte) \
	X(ROOT_PREVERB, byte) \
	X(RAW_PREVERB, byte) \
	X(UNASP_PREVERB, byte) \
	X(APOCOPE, byte) \
	X(DOUBLED_CONS, byte) \
	X(SIG_TO_CI, byte) \
	X(SHORT_EIS, byte) \
	X(PROS_TO_POTI, byte) \
	X(META_TO_PEDA, byte) \
	X(PROS_TO_PROTI, byte) \
	X(UPO_TO_UPAI, byte) \
	X(PARA_TO_PARAI, byte) \
	X(UPER_TO_UPEIR, byte) \
	X(EN_TO_ENI, byte)

#define PREVERB_MORPHFLAG_ENTRY(flag, byte) flag,
static const int preverb_morphflags[] = {
	PREVERB_MORPHFLAGS(PREVERB_MORPHFLAG_ENTRY, 0)
};

/* The bit of flag n in byte `byte` of a MorphFlags array, as mflag_num_to_bits(). */
#define PREVERB_MORPHFLAG_BIT(flag, byte) \
	| (((flag) - 1) / 8 == (byte) ? 1U << (((flag) - 1) % 8) : 0U)
#define PREVERB_MORPHFLAG_BYTE(byte) \
	(MorphFlags)(0U PREVERB_MORPHFLAGS(PREVERB_MORPHFLAG_BIT, byte))

_Static_assert(MORPHFLAG_STORAGE_BYTES == 14,
               "preverb_morphflag_mask lists one byte per storage byte");
static const MorphFlags preverb_morphflag_mask[MORPHFLAG_STORAGE_BYTES] = {
	PREVERB_MORPHFLAG_BYTE(0), PREVERB_MORPHFLAG_BYTE(1),
	PREVERB_MORPHFLAG_BYTE(2), PREVERB_MORPHFLAG_BYTE(3),
	PREVERB_MORPHFLAG_BYTE(4), PREVERB_MORPHFLAG_BYTE(5),
	PREVERB_MORPHFLAG_BYTE(6), PREVERB_MORPHFLAG_BYTE(7),
	PREVERB_MORPHFLAG_BYTE(8), PREVERB_MORPHFLAG_BYTE(9),
	PREVERB_MORPHFLAG_BYTE(10), PREVERB_MORPHFLAG_BYTE(11),
	PREVERB_MORPHFLAG_BYTE(12), PREVERB_MORPHFLAG_BYTE(13)
};

void * zogalloc(size_t, size_t);

int init_prvb_tab(void)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	char *prvb_tab;
	size_t i;
	
	if( context->preverb_morphflag_table ) return(1);
	prvb_tab = (char *)calloc((size_t)(TABSIZE+1),(size_t)(sizeof * prvb_tab) );
		
	if (! prvb_tab) {
		morpheus_runtime_diagnostic("could not allocate preverb morphflag table\n");
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_NO_MEMORY);
		return(0);
	}
	context->preverb_morphflag_table = prvb_tab;
	

	for(i=0;i<sizeof preverb_morphflags / sizeof preverb_morphflags[0];i++)
		prvb_tab[preverb_morphflags[i]] = 1;
	return(1);

}

/*
 * Move the preverb flags of a word to its preverb. Called for every
 * candidate key during analysis, so it moves them a byte at a time through
 * preverb_morphflag_mask rather than testing each flag: with one test per
 * flag, the 17 flags cost analysis a tenth of its instructions.
 */
void xfer_prvbflags(MorphFlags *word_mf, MorphFlags *prvb_mf)
{
	size_t i;

	for(i=0;i<MORPHFLAG_STORAGE_BYTES;i++) {
		MorphFlags moved = (MorphFlags)(word_mf[i] & preverb_morphflag_mask[i]);

		if( moved ) {
			word_mf[i] = (MorphFlags)(word_mf[i] & (MorphFlags)~moved);
			prvb_mf[i] = (MorphFlags)(prvb_mf[i] | moved);
		}
	}
}


 int MorphNames(MorphFlags *mf, char *res, size_t capacity,
               const char *dels, int pretty)
{
	char *s;
	long i;
	long j;
	long curnum;
	int mask = 1;
	int hit = 0;

	if (!mf || !res || !capacity || !dels) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return(0);
	}
	*res = 0;
	
	for(i=0;i<MORPHFLAG_BYTES;i++) {
		mask = 1;
		for(j=0;j<8;j++) {
			
			if( mf[i] & mask ) {
					curnum = (long)mflag_bit_to_num((int)i,(int)j+1);
				if( ! pretty || is_pretty_morphflag(curnum) ) {
					/*(i*8) + j + 1;*/
	
					hit++;
					s=NameOfMorphFlags(curnum);

					if( *s ) {
						if((*res && !Xstrncat(res,dels,capacity)) ||
						   !Xstrncat(res,s,capacity)) {
							*res = 0;
							morpheus_runtime_error_record(
							    MORPHEUS_RUNTIME_ERROR_INTERNAL);
							return(0);
						}
					}
				}
			}
			mask = mask << 1;
		}
	}
	return(1);
	
/*
morpheus_runtime_diagnostic("%o %o %o %o \n", mf[0] , mf[1], mf[2], mf[3] );
*/
}
