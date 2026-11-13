/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_PART_RELIEF_EDITOR_H
#define TL_PART_RELIEF_EDITOR_H
#include <X11/Intrinsic.h>
#include "scrollbar_parts.h"
typedef struct TLPartReliefEditor TLPartReliefEditor;
/* Capabilities describe the native sample, not historical Motif defaults. */
typedef enum { TL_RELIEF_UNAVAILABLE, TL_RELIEF_GTK3_STEPPER,
               TL_RELIEF_GTK3_ARROW_BUTTON, TL_RELIEF_GTK3_ENCLOSURE,
               TL_RELIEF_GTK3_THUMB, TL_RELIEF_GTK3_FITTING } TLReliefCapability;
TLPartReliefEditor *tl_part_editor_create(Widget parent,XtCallbackProc changed,XtCallbackProc selected,XtPointer context);
int tl_part_editor_state(const TLPartReliefEditor *editor);
void tl_part_editor_update(TLPartReliefEditor *editor,const TLPartRecipe *part,int capability);
int tl_part_editor_capture(const TLPartReliefEditor *editor,TLPartRecipe *part);
#endif
