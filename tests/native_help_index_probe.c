/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "work_board/view.h"
WBView *__real_wb_view_create(XtAppContext, Widget, WBAction, void *, json_object *);
WBView *__wrap_wb_view_create(XtAppContext app, Widget shell, WBAction action,
                              void *context, json_object *histories) {
  WBView *view = __real_wb_view_create(app, shell, action, context, histories);
  wb_view_help(view);
  return view;
}
