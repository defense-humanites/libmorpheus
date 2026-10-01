// SPDX-License-Identifier: AGPL-3.0-or-later
#include <assert.h>
#include <string.h>
#include "../src/anal/latin_spelling_internal.h"

int main(void)
{
  char word[16];
  const char *inputs[] = { "exca", "expa", "exta" };
  const char *expected[] = { "exsca", "exspa", "exsta" };
  const char *unchanged[] = { "", "e", "ex", "exa", "exsa", "Exca" };
  size_t i;

  for (i = 0; i < sizeof inputs/sizeof inputs[0]; ++i) {
    /* Nonzero tail makes a missing moved terminator fail deterministically. */
    memset(word,'!',sizeof word);
    strcpy(word,inputs[i]);
    assert(morpheus_latin_expand_ex(word,sizeof word));
    assert(!strcmp(word,expected[i]));
    assert(word[strlen(expected[i])+1] == '!');
  }
  for (i = 0; i < sizeof unchanged/sizeof unchanged[0]; ++i) {
    strcpy(word,unchanged[i]);
    assert(!morpheus_latin_expand_ex(word,sizeof word));
    assert(!strcmp(word,unchanged[i]));
  }
  {
    char fits[6] = "exta";
    char full[5] = "exta";
    char unterminated[4] = { 'e','x','t','a' };
    assert(morpheus_latin_expand_ex(fits,sizeof fits));
    assert(!strcmp(fits,"exsta"));
    assert(!morpheus_latin_expand_ex(full,sizeof full));
    assert(!strcmp(full,"exta"));
    assert(!morpheus_latin_expand_ex(unterminated,sizeof unterminated));
    assert(!memcmp(unterminated,"exta",sizeof unterminated));
  }
  assert(!morpheus_latin_expand_ex(NULL,sizeof word));
  assert(!morpheus_latin_expand_ex(word,0));
  return 0;
}
