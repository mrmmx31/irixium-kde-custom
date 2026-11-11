/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "font_policy_motif.h"
#include <assert.h>
#include <locale.h>
#include <stdio.h>
#include <string.h>
int main(void)
{
    Display *display;
    TLFontPolicy policy;
    TLFontCoverage coverage;
    XmFontList fonts;
    XtAppContext app;
    int argc = 1;
    char *argv[] = { "font-policy-test", NULL };
    char pattern[384];
    const char *sample = "Árvore — ação";
    assert(setlocale(LC_ALL, "C.UTF-8"));
    assert(tl_font_unicode_xlfd("-misc-fixed-medium-r-semicondensed--13-120-75-75-c-60-iso8859-1", pattern, sizeof(pattern)));
    assert(!strcmp(pattern, "-misc-fixed-medium-r-semicondensed--13-120-75-75-c-60-iso10646-1"));
    assert(!tl_font_unicode_xlfd("fixed", pattern, sizeof(pattern)));
    assert(!tl_font_unicode_xlfd("-*-fixed-medium-r-normal--13-120-75-75-c-60-iso8859-1", pattern, sizeof(pattern)));
    assert(!tl_font_unicode_xlfd("-misc-fixed-medium-r-normal--13-120-75-75-c-60-iso8859-1", pattern, 8));
    XtSetLanguageProc(NULL, NULL, NULL);
    XtToolkitInitialize();
    app = XtCreateApplicationContext();
    display = XtOpenDisplay(app, NULL, "fontPolicyTest", "FontPolicyTest", NULL, 0, &argc, argv);
    assert(display);
    fonts = tl_font_policy_load(display, "fixed", &policy);
    assert(fonts && policy.fallback_added && policy.charsets_added > 0 && policy.ascii_preserved);
    printf("primary=%s\nunicode=%s\n", policy.primary, policy.unicode);
    tl_font_coverage(display, fonts, sample, &coverage);
    printf("Latin coverage valid=%d unicode=%d missing=%zu unsupported=%zu first=U+%04X\n", coverage.valid_utf8, coverage.unicode_font_present, coverage.missing, coverage.unsupported, coverage.first_missing);
    assert(coverage.valid_utf8 && coverage.unicode_font_present && !coverage.missing && !coverage.unsupported);
    printf("Latin: %zu characters present\n", coverage.characters);
    tl_font_coverage(display, fonts, "Ελληνικά Русский", &coverage);
    printf("Greek/Cyrillic missing=%zu unsupported=%zu first=U+%04X\n", coverage.missing, coverage.unsupported, coverage.first_missing);
    assert(coverage.valid_utf8 && !coverage.unsupported);
    tl_font_coverage(display, fonts, "漢字", &coverage);
    printf("CJK missing=%zu unsupported=%zu first=U+%04X\n", coverage.missing, coverage.unsupported, coverage.first_missing);
    assert(coverage.valid_utf8 && coverage.missing == 2 && coverage.unsupported == 0);
    tl_font_coverage(display, fonts, "😀", &coverage);
    assert(coverage.valid_utf8 && coverage.unsupported == 1);
    tl_font_coverage(display, fonts, "\xc0\xaf", &coverage);
    assert(!coverage.valid_utf8);
    tl_font_coverage(display, fonts, "\xed\xa0\x80", &coverage);
    assert(!coverage.valid_utf8);
    tl_font_coverage(display, fonts, "\xf4\x90\x80\x80", &coverage);
    assert(!coverage.valid_utf8);
    tl_font_coverage(display, fonts, "\xe2\x80", &coverage);
    assert(!coverage.valid_utf8);
    XmFontListFree(fonts);
    fonts = tl_font_policy_load(display, "-*-helvetica-bold-r-normal--12-*,fixed", &policy);
    assert(fonts && policy.ascii_preserved);
    tl_font_coverage(display, fonts, "Árvore — ação", &coverage);
    assert(coverage.valid_utf8 && !coverage.missing && !coverage.unsupported);
    char primary[384];
    snprintf(primary, sizeof(primary), "%s", policy.primary);
    for (int px = 12; px <= 24; px += 6) {
        TLFontPolicy sized_policy;
        XmFontList sized = tl_font_policy_sized_load(display, primary, px, &sized_policy);
        assert(sized && sized_policy.ascii_preserved);
        tl_font_coverage(display, sized, "Árvore — ação Ελληνικά Русский", &coverage);
        printf("Sized primary px=%d resolved=%s missing=%zu unsupported=%zu first=U+%04X\n", px, sized_policy.primary, coverage.missing, coverage.unsupported, coverage.first_missing);
        assert(coverage.valid_utf8);
        tl_font_coverage(display, sized, "Árvore — ação", &coverage);
        assert(coverage.valid_utf8 && !coverage.missing && !coverage.unsupported);
        XmFontListFree(sized);
    }
    assert(!tl_font_policy_sized_load(display, "fixed", 13, &policy));
    assert(!tl_font_policy_sized_load(display, primary, 0, &policy));
    assert(!tl_font_policy_sized_load(display, primary, 129, &policy));
    XmFontListFree(fonts);
    XtCloseDisplay(display);
    XtDestroyApplicationContext(app);
    puts("Font policy native coverage passed");
    return 0;
}
