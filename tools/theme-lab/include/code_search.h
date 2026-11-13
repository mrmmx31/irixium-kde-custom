/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef THEME_LAB_CODE_SEARCH_H
#define THEME_LAB_CODE_SEARCH_H

#include <stddef.h>

typedef struct {
    size_t start;
    size_t end;
} TLCodeSearchMatch;

/* Positions are multibyte characters, matching Motif XmTextPosition. */
size_t tl_code_search_length(const char *text);
int tl_code_search_find(const char *text, const char *query, size_t start,
                        int direction, int match_case, int whole_word,
                        TLCodeSearchMatch *match);

#endif
