/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef WORK_BOARD_VIEW_H
#define WORK_BOARD_VIEW_H
#include "board.h"
#include <Xm/Xm.h>
typedef struct WBView WBView;
enum {
  WB_SELECT,
  WB_SAVE,
  WB_RELOAD,
  WB_DISCARD,
  WB_FILTER,
  WB_PLACE,
  WB_INSERT,
  WB_CLOSE,
  WB_EDIT,
  WB_UNDO_NOTE,
  WB_REDO_NOTE
};
typedef void (*WBAction)(void *, int, const char *);
WBView *wb_view_create(XtAppContext app, Widget shell, WBAction action,
                       void *context, json_object *histories);
void wb_view_undo(WBView *v, int redo);
void wb_view_title_restore(WBView *v, const char *title);
char *wb_view_title(WBView *v);
void wb_view_rows(WBView *v, json_object *root, json_object *drafts,
                  const char *filter, const char *selected);
void wb_view_item(WBView *v, json_object *item, json_object *draft);
json_object *wb_view_user(WBView *v);
void wb_view_status(WBView *v, const char *message);
void wb_view_anchor(WBView *v, const char *id);
const char *wb_view_insertion(WBView *v, char *title, size_t capacity);
void wb_view_palette(WBView *v, json_object *colors);
#endif
