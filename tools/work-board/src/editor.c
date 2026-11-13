/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "editor.h"
#include <X11/keysym.h>
#include <Xm/PushB.h>
#include <Xm/RowColumn.h>
#include <Xm/Text.h>
#include <Xm/TextF.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* History belongs to a field/item, never to the reused Motif widget. The
 * controller persists this independent editing journal, not an authorization. */
struct WBEditor {
  Widget widget, popup, commands[6];
  json_object *histories, *history;
  WBEditorChanged changed;
  void *context;
  int replaying;
};
static json_object *get(json_object *o, const char *key) {
  json_object *v = NULL;
  json_object_object_get_ex(o, key, &v);
  return v;
}
static char *content(WBEditor *e) {
  return XmIsTextField(e->widget) ? XmTextFieldGetString(e->widget)
                                 : XmTextGetString(e->widget);
}
static void set_content(WBEditor *e, const char *s) {
  if (XmIsTextField(e->widget)) {
    XmTextFieldSetString(e->widget, (char *)s);
    XmTextFieldSetInsertionPosition(e->widget,
                                    XmTextFieldGetLastPosition(e->widget));
  } else {
    XmTextSetString(e->widget, (char *)s);
    XmTextSetInsertionPosition(e->widget, XmTextGetLastPosition(e->widget));
  }
}
static int editable(WBEditor *e) {
  Boolean value = False;
  XtVaGetValues(e->widget, XmNeditable, &value, NULL);
  return value;
}
static void remember(WBEditor *e, const char *s) {
  json_object *a;
  size_t n, pos, total = 0;
  if (!e->history)
    return;
  a = get(e->history, "entries");
  n = json_object_array_length(a);
  pos = (size_t)wb_number(e->history, "position");
  if (n && pos < n &&
      !strcmp(json_object_get_string(json_object_array_get_idx(a, pos)), s))
    return;
  if (n > pos + 1)
    json_object_array_del_idx(a, pos + 1, n - pos - 1);
  json_object_array_add(a, json_object_new_string(s));
  n = json_object_array_length(a);
  for (size_t i = 0; i < n; ++i)
    total += strlen(json_object_get_string(json_object_array_get_idx(a, i)));
  /* Bounded history: up to 128 individual edits and 1 MiB per field. The
   * current and immediately preceding values are always kept. */
  while (n > 2 && (n > 128 || total > 1024 * 1024)) {
    total -= strlen(json_object_get_string(json_object_array_get_idx(a, 0)));
    json_object_array_del_idx(a, 0, 1);
    --n;
  }
  json_object_object_add(e->history, "position", json_object_new_int((int)n - 1));
}
static void value_changed(Widget w, XtPointer data, XtPointer call) {
  WBEditor *e = data;
  char *s;
  (void)w;
  (void)call;
  if (e->replaying)
    return;
  s = content(e);
  remember(e, s);
  XtFree(s);
  if (e->changed)
    e->changed(e->context);
}
static void verify(Widget w, XtPointer data, XtPointer call) {
  XmTextVerifyCallbackStruct *c = call;
  (void)w;
  (void)data;
  /* Ctrl keys must never become invisible destructive input. */
  if (c->text && c->text->ptr)
    for (int i = 0; i < c->text->length; ++i) {
      unsigned char b = (unsigned char)c->text->ptr[i];
      if (b < 32 && b != '\n' && b != '\r' && b != '\t')
        c->doit = False;
    }
}
void wb_editor_command(WBEditor *e, int command) {
  Widget w = e->widget;
  Time time = XtLastTimestampProcessed(XtDisplay(w));
  int tf = XmIsTextField(w);
  if (command == WB_UNDO || command == WB_REDO) {
    int pos;
    json_object *a;
    if (!editable(e) || !e->history)
      return;
    pos = wb_number(e->history, "position") +
          (command == WB_UNDO ? -1 : 1);
    a = get(e->history, "entries");
    if (pos < 0 || (size_t)pos >= json_object_array_length(a))
      return;
    json_object_object_add(e->history, "position", json_object_new_int(pos));
    e->replaying = 1;
    set_content(e, json_object_get_string(json_object_array_get_idx(a, pos)));
    e->replaying = 0;
    if (e->changed)
      e->changed(e->context);
  } else if (command == WB_COPY) {
    if (tf) XmTextFieldCopy(w, time);
    else XmTextCopy(w, time);
  } else if (command == WB_CUT && editable(e)) {
    if (tf) XmTextFieldCut(w, time);
    else XmTextCut(w, time);
  } else if (command == WB_PASTE && editable(e)) {
    if (tf) XmTextFieldPaste(w);
    else XmTextPaste(w);
  } else if (command == WB_ALL) {
    if (tf) XmTextFieldSetSelection(w, 0, XmTextFieldGetLastPosition(w), time);
    else XmTextSetSelection(w, 0, XmTextGetLastPosition(w), time);
  }
}
static void menu_command(Widget w, XtPointer data, XtPointer call) {
  WBEditor *e = data;
  (void)call;
  for (int i = 0; i < 6; ++i)
    if (w == e->commands[i])
      wb_editor_command(e, i);
}
static void popup(WBEditor *e, XButtonEvent *event) {
  static const char *labels[] = {"Desfazer   Ctrl+Z", "Refazer   Ctrl+Y",
                                 "Copiar   Ctrl+C", "Recortar   Ctrl+X",
                                 "Colar   Ctrl+V", "Selecionar tudo   Ctrl+A"};
  if (!e->popup) {
    e->popup = XmCreatePopupMenu(e->widget, "textEditMenu", NULL, 0);
    for (int i = 0; i < 6; ++i) {
      XmString s = XmStringCreateLocalized((char *)labels[i]);
      e->commands[i] = XtVaCreateManagedWidget(
          "editCommand", xmPushButtonWidgetClass, e->popup, XmNlabelString, s,
          XmNtoolTipString, s, NULL);
      XmStringFree(s);
      XtAddCallback(e->commands[i], XmNactivateCallback, menu_command, e);
    }
  }
  /* Get roles and font from the actual field, no fixed palette. */
  Pixel bg, fg, top, bottom;
  XmFontList font;
  XtVaGetValues(e->widget, XmNbackground, &bg, XmNforeground, &fg,
                XmNtopShadowColor, &top, XmNbottomShadowColor, &bottom,
                XmNfontList, &font, NULL);
  XtVaSetValues(e->popup, XmNbackground, bg, XmNforeground, fg, NULL);
  for (int i = 0; i < 6; ++i) {
    XtVaSetValues(e->commands[i], XmNbackground, bg, XmNforeground, fg,
                  XmNtopShadowColor, top, XmNbottomShadowColor, bottom,
                  XmNfontList, font, NULL);
    XtSetSensitive(e->commands[i], i == WB_COPY || i == WB_ALL || editable(e));
  }
  XmMenuPosition(e->popup, event);
  XtManageChild(e->popup);
}
static void key_event(Widget w, XtPointer data, XEvent *event, Boolean *dispatch) {
  WBEditor *e = data;
  (void)w;
  if (event->type == ButtonPress && event->xbutton.button == Button3) {
    popup(e, &event->xbutton);
    *dispatch = False;
    return;
  }
  if (event->type == KeyPress &&
      (XLookupKeysym(&event->xkey, 0) == XK_Menu ||
       ((event->xkey.state & ShiftMask) && XLookupKeysym(&event->xkey, 0) == XK_F10))) {
    Position px, py;
    XButtonEvent press = {0};
    XtTranslateCoords(w, 12, 12, &px, &py);
    press.type = ButtonPress;
    press.display = XtDisplay(w);
    press.window = XtWindow(w);
    press.button = Button3;
    press.time = event->xkey.time;
    press.x_root = px;
    press.y_root = py;
    popup(e, &press);
    *dispatch = False;
    return;
  }
  if (event->type == KeyPress && (event->xkey.state & ControlMask)) {
    KeySym key = XLookupKeysym(&event->xkey, 0);
    int cmd = -1;
    if (key >= XK_A && key <= XK_Z) key += XK_a - XK_A;
    switch (key) {
    case XK_z: cmd = event->xkey.state & ShiftMask ? WB_REDO : WB_UNDO; break;
    case XK_y: cmd = WB_REDO; break;
    case XK_c: case XK_Insert: cmd = WB_COPY; break;
    case XK_x: cmd = WB_CUT; break;
    case XK_v: cmd = WB_PASTE; break;
    case XK_a: cmd = WB_ALL; break;
    }
    if (cmd >= 0) {
      *dispatch = False;
      wb_editor_command(e, cmd);
    }
  }
}
static void destroy(Widget w, XtPointer data, XtPointer call) {
  (void)w;
  (void)call;
  free(data);
}
WBEditor *wb_editor_attach(Widget w, json_object *histories,
                           WBEditorChanged changed, void *context) {
  WBEditor *e = calloc(1, sizeof(*e));
  e->widget = w;
  e->histories = histories;
  e->changed = changed;
  e->context = context;
  XtInsertEventHandler(w, KeyPressMask | ButtonPressMask, False,
                       key_event, e, XtListHead);
  XtAddCallback(w, XmNvalueChangedCallback, value_changed, e);
  XtAddCallback(w, XmNmodifyVerifyCallback, verify, e);
  XtAddCallback(w, XmNdestroyCallback, destroy, e);
  return e;
}
void wb_editor_show(WBEditor *e, const char *key, const char *s) {
  e->history = get(e->histories, key);
  if (!json_object_is_type(e->history, json_type_object) ||
      !json_object_is_type(get(e->history, "entries"), json_type_array)) {
    e->history = json_object_new_object();
    json_object_object_add(e->history, "entries", json_object_new_array());
    json_object_object_add(e->histories, key, e->history);
  }
  remember(e, s);
  e->replaying = 1;
  set_content(e, s);
  e->replaying = 0;
}
