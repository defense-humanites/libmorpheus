// SPDX-License-Identifier: AGPL-3.0-or-later
#ifndef MORPHEUS_LATIN_SPELLING_INTERNAL_H
#define MORPHEUS_LATIN_SPELLING_INTERNAL_H

#include <stddef.h>
#include <string.h>

/* Only an interior i followed by a vowel can take this historical retry. */
static inline int
morpheus_latin_can_retry_j(const char *position)
{
  return position && position[0] == 'i' && position[1] != '\0' &&
         position[2] != '\0' && strchr("aeiou",position[1]) != NULL;
}

/* Expand the historical ex[cpt] spelling without reading stale tail bytes. */
static inline int
morpheus_latin_expand_ex(char *word, size_t capacity)
{
  char *end;
  size_t length;

  if (!word || !capacity) return 0;
  end = memchr(word,'\0',capacity);
  if (!end) return 0;
  length = (size_t)(end-word);
  if (length < 3 || length >= capacity-1 ||
      word[0] != 'e' || word[1] != 'x' ||
      (word[2] != 'c' && word[2] != 'p' && word[2] != 't'))
    return 0;

  /* The terminator must move too; one extra byte is needed for the s. */
  memmove(word+3,word+2,length-2+1);
  word[2] = 's';
  return 1;
}

#endif
