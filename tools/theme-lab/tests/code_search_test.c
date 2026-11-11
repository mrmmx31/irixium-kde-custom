/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "code_search.h"

#include <assert.h>
#include <locale.h>
#include <stdio.h>

int main(void)
{
    TLCodeSearchMatch match;
    const char *text = "Breeze breeze_breeze\nAção: janela; JANELA";
    assert(setlocale(LC_CTYPE, "C.UTF-8") != NULL);
    assert(tl_code_search_length(text) == 41);

    assert(tl_code_search_find(text, "breeze", 0, 1, 0, 0, &match));
    assert(match.start == 0 && match.end == 6);
    assert(tl_code_search_find(text, "breeze", match.end, 1, 0, 0, &match));
    assert(match.start == 7 && match.end == 13);
    assert(tl_code_search_find(text, "breeze", 20, -1, 0, 0, &match));
    assert(match.start == 14 && match.end == 20);

    assert(tl_code_search_find(text, "breeze", 0, 1, 0, 1, &match));
    assert(match.start == 0 && match.end == 6);
    assert(!tl_code_search_find(text, "breeze", match.end, 1, 0, 1, &match));
    assert(tl_code_search_find(text, "Breeze", 0, 1, 1, 0, &match));
    assert(match.start == 0 && match.end == 6);
    assert(tl_code_search_find(text, "Ação", 0, 1, 1, 1, &match));
    assert(match.start == 21 && match.end == 25);
    assert(tl_code_search_find(text, "janela", 35, -1, 0, 1, &match));
    assert(match.start == 27 && match.end == 33);
    assert(!tl_code_search_find(text, "", 0, 1, 0, 0, &match));
    assert(!tl_code_search_find(text, "Breeze", 0, 0, 0, 0, &match));
    puts("code-search: UTF-8 positions, direction, case and word boundaries passed");
    return 0;
}
