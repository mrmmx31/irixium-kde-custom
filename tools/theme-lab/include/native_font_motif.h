/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_NATIVE_FONT_MOTIF_H
#define TL_NATIVE_FONT_MOTIF_H
#include <X11/Intrinsic.h>
#include "native_metrics.h"
/* Read the actual resource of the text-bearing widget. Never substitutes
 * the application font for a control with no text of its own. */
void tl_motif_font_measure(Widget widget, TLNativeFont *font);
#endif
