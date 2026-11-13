#include <stddef.h>

/* endindex.c */
int chcknend(char *, char *);
int chckcmpvb(char *, char *);
int compound_verb_lemma(const char *, const char *, char *, size_t);
int compound_verb_lines(char ***, int *);
int chckend(char *);
int chckvend(char *, char *);
int chckvstem(char *, char *);
int chckdvend(char *, char *);
endind *init_endind(char *, endind *);
int checkendind(endind *, char *, char *, int (*)(const char *, const char *, size_t));
