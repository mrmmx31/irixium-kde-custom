/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "native_font_motif.h"
#include "font_policy_motif.h"
#include <Xm/Xm.h>
#include <Xm/Label.h>
#include <Xm/LabelG.h>
#include <Xm/Text.h>
#include <Xm/TextF.h>
#include <Xm/List.h>
#include <Xm/Scale.h>
#include <Xm/ComboBox.h>
#include <Xm/SpinB.h>
#include <Xm/Frame.h>
#include <X11/Xatom.h>
#include <X11/StringDefs.h>
#include <stdio.h>
#include <string.h>

/* Explicit measurement of a bounded sample; never changes widget text or
 * hooks into editing callbacks. Other list members are not claimed covered. */
static int sample_text(Widget widget, char *out, size_t capacity)
{
    XmString value = NULL;
    char *text;
    size_t bytes;
    int result;
    if (XmIsText(widget)) {
        result = XmTextGetSubstring(widget, 0, 256, (int)capacity, out);
        return result == XmCOPY_SUCCEEDED;
    }
    if (XmIsTextField(widget)) {
        result = XmTextFieldGetSubstring(widget, 0, 256, (int)capacity, out);
        return result == XmCOPY_SUCCEEDED;
    }
    if (XmIsLabel(widget) || XmIsLabelGadget(widget))
        XtVaGetValues(widget, XmNlabelString, &value, NULL);
    else if (XmIsScale(widget))
        XtVaGetValues(widget, XmNtitleString, &value, NULL);
    else if (XmIsList(widget)) {
        XmStringTable items = NULL;
        int count = 0;
        XtVaGetValues(widget, XmNitems, &items, XmNitemCount, &count, NULL);
        if (count > 0 && items) value = items[0];
    }
    if (!value) return 0;
    text = XmStringUnparse(value, NULL, XmCHARSET_TEXT, XmMULTIBYTE_TEXT,
                          NULL, 0, XmOUTPUT_ALL);
    if (!text) return 0;
    bytes = strlen(text);
    if (bytes >= capacity) {
        bytes = capacity-1;
        while (bytes && ((unsigned char)text[bytes] & 0xc0) == 0x80) --bytes;
    }
    memcpy(out, text, bytes);
    out[bytes] = '\0';
    XtFree(text);
    return 1;
}

static void coverage_description(Widget widget, XmFontList list, TLNativeFont *out)
{
    char sample[1025];
    TLFontCoverage coverage;
    size_t used = strlen(out->description);
    if (!sample_text(widget, sample, sizeof(sample))) return;
    tl_font_coverage(XtDisplay(widget), list, sample, &coverage);
    if (!coverage.valid_utf8)
        snprintf(out->description+used, sizeof(out->description)-used,
                 "\nAmostra: UTF-8 inválido; texto preservado");
    else if (!coverage.unicode_font_present)
        snprintf(out->description+used, sizeof(out->description)-used,
                 "\nAmostra: cobertura Unicode não verificável");
    else if (!coverage.missing)
        snprintf(out->description+used, sizeof(out->description)-used,
                 "\nAmostra %zu caracteres: nenhum ausente na tabela; %zu fora do alcance X11",
                 coverage.characters, coverage.unsupported);
    else
        snprintf(out->description+used, sizeof(out->description)-used,
                 "\nAmostra %zu caracteres: %zu ausentes na tabela (U+%04X); %zu fora do alcance X11",
                 coverage.characters, coverage.missing, coverage.first_missing,
                 coverage.unsupported);
}
void tl_motif_font_measure(Widget widget, TLNativeFont *out)
{
    XmFontList list = NULL;
    XmFontContext context;
    XmFontListEntry entry;
    XmFontType type;
    XtPointer font;
    if (!out) return;
    memset(out, 0, sizeof(*out));
    if (!widget) return;
    if (XmIsComboBox(widget)) XtVaGetValues(widget, XmNtextField, &widget, NULL);
    else if (XtIsSubclass(widget, xmSpinBoxWidgetClass) || XmIsFrame(widget)) {
        WidgetList children = NULL; Cardinal count = 0;
        XtVaGetValues(widget, XtNchildren, &children, XtNnumChildren, &count, NULL);
        widget = NULL;
        for (Cardinal i = 0; i < count; ++i)
            if (XmIsTextField(children[i]) || XmIsLabel(children[i])) { widget = children[i]; break; }
    }
    if (!widget) return;
    if (!(XmIsLabel(widget) || XmIsLabelGadget(widget) || XmIsText(widget) ||
          XmIsTextField(widget) || XmIsList(widget) || XmIsScale(widget))) {
        out->kind = TL_FONT_NONE;
        return;
    }
    XtVaGetValues(widget, XmNfontList, &list, NULL);
    if (!list || !XmFontListInitFontContext(&context, list)) return;
    entry = XmFontListNextEntry(context);
    if (entry) {
        font = XmFontListEntryGetFont(entry, &type);
        if (font && type == XmFONT_IS_FONTSET) {
            XFontStruct **fonts; char **names;
            int count = XFontsOfFontSet((XFontSet)font, &fonts, &names);
            if (count > 0 && names[0]) {
                (void)snprintf(out->description, sizeof(out->description),
                    "FontSet (%d fontes), primeira: %s", count, names[0]);
                out->kind = TL_FONT_MEASURED;
            }
        } else if (font && type == XmFONT_IS_FONT) {
            unsigned long atom;
            if (XGetFontProperty((XFontStruct *)font, XA_FONT, &atom)) {
                char *name = XGetAtomName(XtDisplay(widget), atom);
                if (name) {
                    (void)snprintf(out->description, sizeof(out->description), "XFont: %s", name);
                    out->kind = TL_FONT_MEASURED;
                    XFree(name);
                }
            }
        }
    }
    XmFontListFreeFontContext(context);
    if (out->kind == TL_FONT_MEASURED) coverage_description(widget, list, out);
}
