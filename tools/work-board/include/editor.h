/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef WORK_BOARD_EDITOR_H
#define WORK_BOARD_EDITOR_H
#include "board.h"
#include <Xm/Xm.h>
typedef struct WBEditor WBEditor;
typedef void (*WBEditorChanged)(void *);
WBEditor *wb_editor_attach(Widget widget, json_object *histories,
                           WBEditorChanged changed, void *context);
void wb_editor_show(WBEditor *editor, const char *key, const char *text);
void wb_editor_command(WBEditor *editor, int command);
enum { WB_UNDO, WB_REDO, WB_COPY, WB_CUT, WB_PASTE, WB_ALL };
#endif
