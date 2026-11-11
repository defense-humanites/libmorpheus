
/* contract.c */
gk_string *do_euph(gk_string *, Dialect);
gk_string *do_euph_at_junction(gk_string *, Dialect, size_t);
int sub_for_euph(gk_string *, Dialect, gk_string *, int, gk_string *, int);
int needs_sub(gk_string *, Dialect, gk_string *, char *, char *, char *, char *);
gk_string *
 poss_contracts(gk_string *gstr, Dialect skipdial);
