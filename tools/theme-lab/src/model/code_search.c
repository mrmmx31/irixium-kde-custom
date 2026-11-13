/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "code_search.h"

#include <ctype.h>
#include <locale.h>
#include <stdlib.h>
#include <wchar.h>
#include <wctype.h>

static int to_wide(const char *text, wchar_t **wide, size_t *length)
{
    mbstate_t state = {0};
    const char *cursor = text;
    size_t count;
    wchar_t *result;
    if (text == NULL || wide == NULL || length == NULL)
        return 0;
    count = mbsrtowcs(NULL, &cursor, 0, &state);
    if (count == (size_t)-1 || count > 1024u * 1024u)
        return 0;
    result = calloc(count + 1, sizeof(*result));
    if (result == NULL)
        return 0;
    state = (mbstate_t){0};
    cursor = text;
    if (mbsrtowcs(result, &cursor, count + 1, &state) == (size_t)-1) {
        free(result);
        return 0;
    }
    *wide = result;
    *length = count;
    return 1;
}

static int word_character(wchar_t character)
{
    return character == L'_' || iswalnum(character);
}

static int equal_at(const wchar_t *text, size_t position,
                    const wchar_t *query, size_t query_length,
                    int match_case)
{
    size_t i;
    for (i = 0; i < query_length; ++i) {
        wchar_t left = text[position + i], right = query[i];
        if (match_case ? left != right : towlower(left) != towlower(right))
            return 0;
    }
    return 1;
}

static int whole_word_at(const wchar_t *text, size_t text_length,
                         size_t position, size_t query_length)
{
    size_t end = position + query_length;
    return (position == 0 || !word_character(text[position - 1])) &&
           (end == text_length || !word_character(text[end]));
}

size_t tl_code_search_length(const char *text)
{
    wchar_t *wide = NULL;
    size_t length = 0;
    if (!to_wide(text, &wide, &length))
        return 0;
    free(wide);
    return length;
}

int tl_code_search_find(const char *text, const char *query, size_t start,
                        int direction, int match_case, int whole_word,
                        TLCodeSearchMatch *match)
{
    wchar_t *wide_text = NULL, *wide_query = NULL;
    size_t text_length = 0, query_length = 0, position;
    int found = 0;
    if (direction != 1 && direction != -1)
        return 0;
    if (match == NULL || query == NULL || query[0] == '\0' ||
        !to_wide(text, &wide_text, &text_length) ||
        !to_wide(query, &wide_query, &query_length) || query_length == 0) {
        free(wide_text);
        free(wide_query);
        return 0;
    }
    if (start > text_length)
        start = text_length;
    if (query_length <= text_length) {
        size_t last = text_length - query_length;
        if (direction > 0) {
            for (position = start; position <= last; ++position) {
                if (equal_at(wide_text, position, wide_query, query_length, match_case) &&
                    (!whole_word || whole_word_at(wide_text, text_length, position, query_length))) {
                    match->start = position;
                    match->end = position + query_length;
                    found = 1;
                    break;
                }
            }
        } else if (start >= query_length) {
            position = start - query_length;
            for (;;) {
                if (equal_at(wide_text, position, wide_query, query_length, match_case) &&
                    (!whole_word || whole_word_at(wide_text, text_length, position, query_length))) {
                    match->start = position;
                    match->end = position + query_length;
                    found = 1;
                    break;
                }
                if (position == 0)
                    break;
                --position;
            }
        }
    }
    free(wide_text);
    free(wide_query);
    return found;
}
