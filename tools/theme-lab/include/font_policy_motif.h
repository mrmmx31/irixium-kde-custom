/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_FONT_POLICY_MOTIF_H
#define TL_FONT_POLICY_MOTIF_H
#include <Xm/Xm.h>
#include <stddef.h>
typedef struct {
    char primary[384], unicode[384];
    int fallback_added, ascii_preserved, charsets_added;
} TLFontPolicy;
typedef struct {
    size_t characters, missing, unsupported;
    unsigned first_missing;
    int valid_utf8, unicode_font_present;
} TLFontCoverage;
/* Derive only registry/encoding from a resolved XLFD; preserve all metrics. */
int tl_font_unicode_xlfd(const char *primary, char *result, size_t capacity);
/* List owns the fonts via Motif EntryLoad. Free with XmFontListFree. */
XmFontList tl_font_policy_load(Display *display, const char *pattern,
                              TLFontPolicy *report);
/* Keep the resolved family/style; NULL means this pixel size is unavailable. */
XmFontList tl_font_policy_sized_load(Display *display, const char *primary,
                                    int pixels, TLFontPolicy *report);
/* Character presence, not shaping or complete-language support. */
void tl_font_coverage(Display *display, XmFontList list, const char *utf8,
                      TLFontCoverage *out);
#endif
