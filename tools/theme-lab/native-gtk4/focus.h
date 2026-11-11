/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_GTK4_FOCUS_H
#define TL_GTK4_FOCUS_H
#include <X11/Intrinsic.h>
typedef struct TLGTK4Focus TLGTK4Focus;
TLGTK4Focus *tl_gtk4_focus_create(Widget canvas);
void tl_gtk4_focus_enabled(TLGTK4Focus *focus, int enabled);
int tl_gtk4_focus_has_child(const TLGTK4Focus *focus);
void tl_gtk4_focus_observer(TLGTK4Focus *focus, void (*notify)(XtPointer), XtPointer data);
void tl_gtk4_focus_destroy(TLGTK4Focus *focus);
#endif
