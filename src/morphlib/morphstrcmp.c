#include "morphlib_internal.h"
#include <greek.h>

#include "morphstrcmp.proto.h"

/*
 * The comparison order of morphstrcmp() and dictstrcmp(): byte order, with
 * the iota subscript matching as an 'i'. It is the same for every context,
 * so it needs no table and no lookup of the runtime context, which the
 * stem and dictionary lookups would otherwise pay on every comparison.
 */
static unsigned char compare_byte(unsigned char c)
{
	return(c == '|' ? (unsigned char)'i' : c);
}

static int compare_nulls(const char *s1, const char *s2, int *result)
{
	if (s1 && s2) return(0);
	if (s1 == s2) *result = 0;
	else *result = s1 ? 1 : -1;
	return(1);
}

/*
 * Compare strings:  s1>s2: >0  s1==s2: 0  s1<s2: <0
 */
int morphstrcmp(char *s1, char *s2)
{
	int result;

	if (compare_nulls(s1,s2,&result)) return(result);
/*
fprintf(stderr,"looking at [%s] and [%s]\n", s1, s2 );
*/
	while(1) {
		if(compare_byte((unsigned char)*s1) != compare_byte((unsigned char)*s2))
			return((int)(compare_byte((unsigned char)*s1) -
				compare_byte((unsigned char)*s2)));
		if (*s1=='\0')
			return(0);
		s1++; s2++;
	}
	return(0);
}

int betastrcmp(char *s1, char *s2)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	unsigned char *betatab = context->beta_table;
	int result;

	if (compare_nulls(s1,s2,&result)) return(result);
	if( ! context->beta_table_initialized ) {
		init_betatab();
	}
	while(1) {
		while(*s1&&!betatab[(unsigned char)*s1]) s1++;
		while(*s2&&!betatab[(unsigned char)*s2]) s2++;

		if(betatab[(unsigned char)*s1] != betatab[(unsigned char)*s2])
			return((int)(betatab[(unsigned char)*s1] -
				betatab[(unsigned char)*s2]));
		if (*s1=='\0')
			return(strcmp(s1,s2));
		s1++; s2++;
	}
/*
 * if the two strings are equal alphanumerically,
 * then check the rest
 */
 
	return(strcmp(s1,s2));

}

int morphstrncmp(const char *s1, const char *s2, size_t n)
{
	int result;

	if (!n) return(0);
	if (compare_nulls(s1,s2,&result)) return(result);
	for (; --n && (compare_byte((unsigned char)*s1) ==
		compare_byte((unsigned char)*s2)); s1++, s2++) {
		if (!*s1) break;
	}
		
	return ((int)(compare_byte((unsigned char)*s1) -
		compare_byte((unsigned char)*s2)));
}

int dictstrcmp(char *s1, char *s2)
{
	int result;

	if (compare_nulls(s1,s2,&result)) return(result);

	while(1) {
		while(! isalpha((unsigned char)*s1) && *s1 != '|'  && *s1 != HARDLONG && *s1 ) s1++;
		while(! isalpha((unsigned char)*s2) && *s2 != '|'  && *s2 != HARDLONG && *s2 ) s2++;
		if(compare_byte((unsigned char)*s1) != compare_byte((unsigned char)*s2))
			return(compare_byte((unsigned char)*s1) -
				compare_byte((unsigned char)*s2));
		if (*s1=='\0'||isspace((unsigned char)*s1))

			return(0);
 /*
 			return(Xstrlen(t1)-Xstrlen(t2));
 */
		s1++; s2++;
/*
		while(! isalpha((unsigned char)*s1) && *s1 != '|'  && *s1 ) s1++;
		while(! isalpha((unsigned char)*s2) && *s2 != '|' && *s2 ) s2++;
*/
	}
}

int dictstrncmp(const char *s1, const char *s2, size_t n)
{
	int result;

	if (!n) return(0);
	if (compare_nulls(s1,s2,&result)) return(result);
	while (n--) {
		while (*s1 && !isalpha((unsigned char)*s1)) s1++;
		while (*s2 && !isalpha((unsigned char)*s2)) s2++;
		result = (int)compare_byte((unsigned char)*s1) -
		         (int)compare_byte((unsigned char)*s2);
		if (result || !*s1) return(result);
		s1++;
		s2++;
	}
	return(0);
}

void init_betatab(void)
{
	morpheus_runtime_context *context = morpheus_runtime_context_current();
	unsigned char *betatab = context->beta_table;
	int i;
	
	context->beta_table_initialized = 1;
	for(i=0;i<MORPHEUS_BYTE_TABLE_SIZE;i++) {
/*		if( isalpha(i) )*/
			betatab[i] = (unsigned char)i;
	}
	betatab['|'] = 'i'; /* iota subscript matches as an 'i' */
	set_gkorder(betatab);
}
