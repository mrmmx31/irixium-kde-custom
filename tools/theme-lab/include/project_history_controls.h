/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_HISTORY_CONTROLS_H
#define TL_HISTORY_CONTROLS_H
#include "theme_lab.h"
Widget tl_history_controls_create(Widget parent,TLDispatch dispatch,void *context);
void tl_history_controls_state(Widget row,int undo,int redo,int point);
/* Ctrl+Alt+Z/Y belongs to the project. Ctrl+Z/Y remains with the text editor. */
void tl_history_controls_watch(Widget tree,Widget row);
#endif
