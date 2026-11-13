/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "font_policy_motif.h"
#include <X11/Xutil.h>
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <stdlib.h>

static int charset_xlfd(const char *primary, const char *charset,
                        char *out, size_t capacity)
{
    const char *registry = NULL;
    size_t dashes = 0, prefix, encoding_dashes = 0;
    if (!primary || primary[0] != '-' || !out || !capacity || !charset) return 0;
    out[0] = '\0';
    for (const char *p = charset; *p; ++p) {
        unsigned char c = (unsigned char)*p;
        if (c == '-') ++encoding_dashes;
        else if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                   (c >= '0' && c <= '9') || c == '.' || c == '_')) return 0;
    }
    if (encoding_dashes != 1 || strlen(charset) > 80) return 0;
    for (const char *p = primary; *p; ++p) {
        if (*p == '-' && ++dashes == 13) registry = p;
        if (*p == ',' || *p == '*' || *p == '?') return 0;
    }
    if (dashes != 14 || !registry || !registry[1]) return 0;
    prefix = (size_t)(registry-primary);
    if (prefix + strlen(charset) + 2 > capacity) return 0;
    memcpy(out, primary, prefix);
    out[prefix] = '-';
    memcpy(out+prefix+1, charset, strlen(charset)+1);
    return 1;
}

int tl_font_unicode_xlfd(const char *primary, char *out, size_t capacity)
{
    return charset_xlfd(primary, "iso10646-1", out, capacity);
}

static XmFontList load(Display *display, const char *pattern)
{
    XmFontListEntry entry = XmFontListEntryLoad(display, (char *)pattern,
                                              XmFONT_IS_FONTSET,
                                              _MOTIF_DEFAULT_LOCALE);
    XmFontList list;
    if (!entry) return NULL;
    list = XmFontListAppendEntry(NULL, entry);
    XmFontListEntryFree(&entry);
    return list;
}

static XFontSet fontset(XmFontList list)
{
    XmFontContext context;
    XmFontListEntry entry;
    XmFontType type;
    XtPointer font = NULL;
    if (!list || !XmFontListInitFontContext(&context, list)) return NULL;
    entry = XmFontListNextEntry(context);
    if (entry) {
        font = XmFontListEntryGetFont(entry, &type);
        if (type != XmFONT_IS_FONTSET) font = NULL;
    }
    XmFontListFreeFontContext(context);
    return (XFontSet)font;
}

static int unicode_name(const char *name)
{
    size_t n = name ? strlen(name) : 0;
    const char suffix[] = "-iso10646-1";
    return n >= sizeof(suffix)-1 &&
        !strcasecmp(name+n-(sizeof(suffix)-1), suffix);
}

static int has_unicode(XFontSet set)
{
    XFontStruct **fonts;
    char **names;
    int n = set ? XFontsOfFontSet(set, &fonts, &names) : 0;
    for (int i = 0; i < n; ++i) if (unicode_name(names[i])) return 1;
    return 0;
}

static int equal_ascii(XFontSet before, XFontSet after)
{
    if (!before || !after) return 0;
    for (int c = 32; c <= 126; ++c) {
        char value = (char)c;
        XRectangle ink1, ink2, logical1, logical2;
        Xutf8TextExtents(before, &value, 1, &ink1, &logical1);
        Xutf8TextExtents(after, &value, 1, &ink2, &logical2);
        if (ink1.x != ink2.x || ink1.y != ink2.y ||
            ink1.width != ink2.width || ink1.height != ink2.height ||
            logical1.x != logical2.x || logical1.y != logical2.y ||
            logical1.width != logical2.width || logical1.height != logical2.height)
            return 0;
    }
    return 1;
}

XmFontList tl_font_policy_load(Display *display, const char *pattern,
                              TLFontPolicy *report)
{
    XmFontList base, candidate;
    XFontSet set, inspection;
    XFontStruct **fonts;
    char **names, **available, **missing = NULL, *default_string = NULL;
    char variant[384], request[4096];
    int count, found, missing_count = 0, appended = 0;
    size_t used;
    if (!report) return NULL;
    memset(report, 0, sizeof(*report));
    if (!display || !pattern || strlen(pattern) > 600) return NULL;
    base = load(display, pattern);
    set = fontset(base);
    count = set ? XFontsOfFontSet(set, &fonts, &names) : 0;
    if (!count || !names[0]) return base;
    snprintf(report->primary, sizeof(report->primary), "%s", names[0]);
    report->ascii_preserved = 1;
    /* Unicode glyph presence alone does not prove locale charset mapping.
     * Ask Xlib which encodings this exact locale still requires. */
    inspection = XCreateFontSet(display, pattern, &missing, &missing_count,
                                &default_string);
    if (inspection) XFreeFontSet(display, inspection);
    snprintf(request, sizeof(request), "%s", pattern);
    used = strlen(request);
    for (int i = 0; i < missing_count && i < 64; ++i) {
        size_t length;
        if (!charset_xlfd(names[0], missing[i], variant, sizeof(variant))) continue;
        available = XListFonts(display, variant, 1, &found);
        if (available) XFreeFontNames(available);
        if (!found) continue;
        length = strlen(variant);
        if (used + length + 2 > sizeof(request)) break;
        request[used++] = ',';
        memcpy(request+used, variant, length+1);
        used += length;
        ++appended;
    }
    if (missing) XFreeStringList(missing);
    if (!appended) return base;
    candidate = load(display, request);
    {
        XFontStruct **candidate_fonts;
        char **candidate_names;
        XFontSet candidate_set = fontset(candidate);
        int candidate_count = candidate_set ?
            XFontsOfFontSet(candidate_set, &candidate_fonts, &candidate_names) : 0;
        if (!candidate_count || strcasecmp(names[0], candidate_names[0]) ||
            !equal_ascii(set, candidate_set)) {
            if (candidate) XmFontListFree(candidate);
            return base;
        }
        if (has_unicode(candidate_set))
            (void)tl_font_unicode_xlfd(names[0], report->unicode, sizeof(report->unicode));
    }
    report->fallback_added = 1;
    report->charsets_added = appended;
    XmFontListFree(base);
    return candidate;
}

XmFontList tl_font_policy_sized_load(Display *display, const char *primary,
                                    int pixels, TLFontPolicy *report)
{
    char request[768], size[32], validated[768];
    const char *cursor = primary;
    size_t used = 0;
    int component = 0;
    XmFontList list = NULL;
    if (!report) return NULL;
    memset(report, 0, sizeof(*report));
    if (!primary || pixels < 1 || pixels > 128) return NULL;
    if (!tl_font_unicode_xlfd(primary, validated, sizeof(validated))) return NULL;
    if (cursor[0] == '-') {
        while (*cursor != '\0' && used + 2 < sizeof(request)) {
            const char *end;
            size_t length;
            request[used++] = *cursor++;
            end = strchr(cursor, '-');
            length = end != NULL ? (size_t)(end - cursor) : strlen(cursor);
            ++component;
            if (component >= 7) {
                int count = component == 7 ? snprintf(size, sizeof(size), "%d", pixels) : 1;
                /* Remaining fields are wildcarded: a FontSet must select
                 * encodings for the locale rather than one ISO-8859-1 font. */
                if (component != 7) { size[0] = '*'; size[1] = '\0'; count = 1; }
                if (count < 0 || used + (size_t)count >= sizeof(request)) break;
                memcpy(request + used, size, (size_t)count); used += (size_t)count;
            } else {
                if (used + length >= sizeof(request)) break;
                memcpy(request + used, cursor, length); used += length;
            }
            cursor += length;
        }
        request[used] = '\0';
        if (*cursor == '\0') list = tl_font_policy_load(display, request, report);
    }
    if (list) {
        XRectangle ink, logical;
        XFontSet set = fontset(list);
        XFontStruct *primary_font = XLoadQueryFont(display, report->primary);
        int usable_primary = primary_font && primary_font->max_bounds.width > 0 &&
                             primary_font->ascent + primary_font->descent > 0;
        if (primary_font) XFreeFont(display, primary_font);
        /* Some servers resolve an unavailable bitmap size to a scalable
         * zero-width instance. A matching XLFD is not evidence of usable ink. */
        if (set) Xutf8TextExtents(set, "Ag", 2, &ink, &logical);
        if (!usable_primary || !set || !ink.width || !ink.height || !logical.width || !logical.height) {
            XmFontListFree(list);
            memset(report, 0, sizeof(*report));
            list = NULL;
        }
    }
    return list;
}


static int decode(const unsigned char **cursor, unsigned *value)
{
    const unsigned char *p = *cursor;
    unsigned code, minimum;
    int following;
    if (*p < 0x80) { *value = *p; *cursor = p+1; return 1; }
    if (*p >= 0xc2 && *p <= 0xdf) { code = *p & 31; following = 1; minimum = 0x80; }
    else if (*p >= 0xe0 && *p <= 0xef) { code = *p & 15; following = 2; minimum = 0x800; }
    else if (*p >= 0xf0 && *p <= 0xf4) { code = *p & 7; following = 3; minimum = 0x10000; }
    else return 0;
    ++p;
    for (int i = 0; i < following; ++i) {
        if ((*p & 0xc0) != 0x80) return 0;
        code = (code << 6) | (*p++ & 63);
    }
    if (code < minimum || code > 0x10ffff || (code >= 0xd800 && code <= 0xdfff))
        return 0;
    *value = code; *cursor = p; return 1;
}

static int glyph_present(XFontStruct *font, unsigned code)
{
    unsigned high = code >> 8, low = code & 255;
    XCharStruct *glyph;
    if (high < (unsigned)font->min_byte1 || high > (unsigned)font->max_byte1 ||
        low < (unsigned)font->min_char_or_byte2 || low > (unsigned)font->max_char_or_byte2)
        return 0;
    if (!font->per_char) return font->all_chars_exist;
    glyph = &font->per_char[(high-font->min_byte1)*
        (font->max_char_or_byte2-font->min_char_or_byte2+1)+(low-font->min_char_or_byte2)];
    return glyph->width || glyph->lbearing || glyph->rbearing || glyph->ascent || glyph->descent;
}

void tl_font_coverage(Display *display, XmFontList list, const char *text,
                      TLFontCoverage *out)
{
    XFontStruct **fonts;
    XFontStruct **queried;
    char **names;
    XFontSet set = fontset(list);
    int n = set ? XFontsOfFontSet(set, &fonts, &names) : 0;
    const unsigned char *cursor = (const unsigned char *)text;
    if (!out) return;
    memset(out, 0, sizeof(*out));
    if (!text || !display) return;
    queried = calloc(n ? (size_t)n : 1, sizeof(*queried));
    if (!queried) return;
    out->valid_utf8 = 1;
    /* FontSet's structures may only contain aggregate extents. Ask the server
     * for the per-character table of the actual resolved Unicode font. */
    for (int i = 0; i < n; ++i) if (unicode_name(names[i])) {
        queried[i] = XLoadQueryFont(display, names[i]);
        if (queried[i]) out->unicode_font_present = 1;
    }
    while (*cursor) {
        unsigned code;
        int present = 0;
        if (!decode(&cursor, &code)) { out->valid_utf8 = 0; break; }
        ++out->characters;
        if (code == '\n' || code == '\r' || code == '\t') continue;
        if (code > 0xffff) { ++out->unsupported; continue; }
        for (int i = 0; i < n; ++i) {
            /* Unicode code points cannot index arbitrary legacy encodings. */
            if (queried[i] && glyph_present(queried[i], code)) present = 1;
        }
        if (!out->unicode_font_present) { ++out->unsupported; continue; }
        if (!present) {
            if (!out->missing) out->first_missing = code;
            ++out->missing;
        }
    }
    for (int i = 0; i < n; ++i) if (queried[i]) XFreeFont(display, queried[i]);
    free(queried);
}
