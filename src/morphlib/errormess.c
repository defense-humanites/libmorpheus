#include "morphlib_internal.h"

#include "errormess.proto.h"

void ErrorMess(char *s)
{
	if (!s) {
		morpheus_runtime_error_record(MORPHEUS_RUNTIME_ERROR_INTERNAL);
		return;
	}
#ifdef LIGHTSPEED
/*
	char tmp[LONGSTRING];
	char * CtoPstr();
	
	Xstrncpy(tmp,s,LONGSTRING);
	CtoPstr(tmp);
	ErrMesg(tmp);*/
	morpheus_runtime_diagnostic("%s\n", s );
/*
	DebugStr(tmp);
*/
#else
	morpheus_runtime_diagnostic("%s\n", s );
#endif
}

/*
int sprintf(dest, fmt)
char    *dest;		pointer to buffer space
char    *fmt;		pointer to format string
{
	return xprintf(dest, &fmt,false);
}
*/
