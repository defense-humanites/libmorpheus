#ifndef MORPHEUS_MORPHSTRCMP_PROTO_H
#define MORPHEUS_MORPHSTRCMP_PROTO_H

#include <stddef.h>

int morphstrcmp(char *, char *);
int betastrcmp(char *, char *);
int morphstrncmp(const char *, const char *, size_t);
int dictstrcmp(char *, char *);
int dictstrncmp(const char *, const char *, size_t);
void init_betatab(void);

#endif
