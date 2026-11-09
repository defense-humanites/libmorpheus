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
fprintf(stderr,"n [%d] index [%d] setbit [%o] Mf[index] [%o]\n", n , index, setbit, Mf[index]) ;
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
fprintf(stderr,"n %d , index %d setbit [%o] Mf[Index] %o anded [%o]\n", n,index, setbit,Mf[index],
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
fprintf(stderr,"num to bits [%d] ind %o bit %o\n", n , *ind, *bitnum );
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
		fprintf(stderr,"could not allocate morphflag display table\n");
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
 * attached to. init_prvb_tab() builds its lookup table from this list.
 */
static const int preverb_morphflags[] = {
	DISSIMILATION,
	PREVB_AUGMENT,
	ELIDE_PREVERB,
	ROOT_PREVERB,
	RAW_PREVERB,
	UNASP_PREVERB,
	APOCOPE,
	DOUBLED_CONS
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
		fprintf(stderr,"could not allocate preverb morphflag table\n");
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
 * candidate key, so it tests the eight preverb flags directly rather than
 * every flag number against the context's table.
 */
void xfer_prvbflags(MorphFlags *word_mf, MorphFlags *prvb_mf)
{
	size_t i;

	for(i=0;i<sizeof preverb_morphflags / sizeof preverb_morphflags[0];i++) {
		if( has_morphflag(word_mf,preverb_morphflags[i]) ) {
				zap_morphflag(word_mf,preverb_morphflags[i]);
				add_morphflag(prvb_mf,preverb_morphflags[i]);
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
fprintf(stderr,"%o %o %o %o \n", mf[0] , mf[1], mf[2], mf[3] );
*/
}
