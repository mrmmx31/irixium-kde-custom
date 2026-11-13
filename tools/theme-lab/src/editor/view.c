/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "internal.h"
#include "ui_hints.h"
#include <X11/keysym.h>
#include <Xm/PushB.h>
#include <Xm/RowColumn.h>
#include <Xm/Text.h>
#include <Xm/TextF.h>
#include <Xm/SpinB.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* History belongs to a field/item, never to the reused Motif widget. The
 * controller persists this independent editing journal, not an authorization. */
static json_object *get(json_object *o, const char *key) {
  json_object *v = NULL;
  json_object_object_get_ex(o, key, &v);
  return v;
}
static char *content(TLEditor *e) {
  return XmIsTextField(e->widget) ? XmTextFieldGetString(e->widget)
                                 : XmTextGetString(e->widget);
}
static void set_content(TLEditor *e, const char *s) {
  if (XmIsTextField(e->widget)) {
    XmTextFieldSetString(e->widget, (char *)s);
    XmTextFieldSetInsertionPosition(e->widget,
                                    XmTextFieldGetLastPosition(e->widget));
  } else {
    XmTextSetString(e->widget, (char *)s);
    XmTextSetInsertionPosition(e->widget, XmTextGetLastPosition(e->widget));
  }
}
static int editable(TLEditor *e) {
  Boolean value = False;
  XtVaGetValues(e->widget, XmNeditable, &value, NULL);
  return value;
}
static void remember(TLEditor *e, const char *s) {
  json_object *a;
  size_t n, pos, total = 0;
  if (!e->history || e->store->pause)
    return;
  a = get(e->history, "entries");
  n = json_object_array_length(a);
  pos = (size_t)json_object_get_int(get(e->history, "position"));
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
  e->store->dirty = 1;
}
static void value_changed(Widget w, XtPointer data, XtPointer call) {
  TLEditor *e = data;
  char *s;
  (void)w;
  (void)call;
  if (e->replaying || e->store->pause)
    return;
  s = content(e);
  remember(e, s);
  XtFree(s);
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
void tl_editor_command(TLEditor *e, int command) {
  Widget w = e->widget;
  Time time = XtLastTimestampProcessed(XtDisplay(w));
  int tf = XmIsTextField(w);
  if (command == TL_EDIT_UNDO || command == TL_EDIT_REDO) {
    int pos;
    json_object *a;
    if (!editable(e) || !e->history)
      return;
    pos = json_object_get_int(get(e->history, "position")) +
          (command == TL_EDIT_UNDO ? -1 : 1);
    a = get(e->history, "entries");
    if (pos < 0 || (size_t)pos >= json_object_array_length(a))
      return;
    json_object_object_add(e->history, "position", json_object_new_int(pos));
    e->replaying = 1;
    set_content(e, json_object_get_string(json_object_array_get_idx(a, pos)));
    e->replaying = 0;
    e->store->dirty = 1;
  } else if (command == TL_EDIT_COPY) {
    if (tf) XmTextFieldCopy(w, time);
    else XmTextCopy(w, time);
  } else if (command == TL_EDIT_CUT && editable(e)) {
    if (tf) XmTextFieldCut(w, time);
    else XmTextCut(w, time);
  } else if (command == TL_EDIT_PASTE && editable(e)) {
    if (tf) XmTextFieldPaste(w);
    else XmTextPaste(w);
  } else if (command == TL_EDIT_ALL) {
    if (tf) XmTextFieldSetSelection(w, 0, XmTextFieldGetLastPosition(w), time);
    else XmTextSetSelection(w, 0, XmTextGetLastPosition(w), time);
  }
}
static void menu_command(Widget w, XtPointer data, XtPointer call) {
  TLEditor *e = data;
  (void)call;
  for (int i = 0; i < 6; ++i)
    if (w == e->commands[i])
      tl_editor_command(e, i);
}
static void menu_appearance(TLEditor *e) {
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
    XtSetSensitive(e->commands[i], i == TL_EDIT_COPY || i == TL_EDIT_ALL || editable(e));
  }
  tl_ui_menu_hint_refresh(e->popup);
}
void tl_editor_refresh_menus(TLEditorStore *store) {
  if(!store)return;
  for(TLEditor *e=store->editors;e;e=e->next)
    if(e->popup)menu_appearance(e);
}
static void menu_mapped(Widget w,XtPointer data,XtPointer call) {
  (void)w;(void)call;menu_appearance(data);
}
static void create_menu(TLEditor *e) {
  static const char *labels[] = {"Desfazer   Ctrl+Z", "Refazer   Ctrl+Y",
                                 "Copiar   Ctrl+C", "Recortar   Ctrl+X",
                                 "Colar   Ctrl+V", "Selecionar tudo   Ctrl+A"};
  if (!e->popup) {
    Arg args[1];XtSetArg(args[0],XmNpopupEnabled,XmPOPUP_AUTOMATIC);
    e->popup = XmCreatePopupMenu(e->widget, "textEditMenu", args, 1);
    for (int i = 0; i < 6; ++i) {
      XmString s = XmStringCreateLocalized((char *)labels[i]);
      e->commands[i] = XtVaCreateManagedWidget(
          "editCommand", xmPushButtonWidgetClass, e->popup, XmNlabelString, s,
          XmNtoolTipString, s, NULL);
      tl_ui_hint(e->commands[i],tl_ui_editor_command_hint(i));
      XmStringFree(s);
      XtAddCallback(e->commands[i], XmNactivateCallback, menu_command, e);
    }
    tl_ui_menu_hints(e->popup);
    XtAddCallback(e->popup,XmNmapCallback,menu_mapped,e);
  }
}
static void popup(TLEditor *e, XButtonEvent *event) {
  create_menu(e);
  menu_appearance(e);
  XmMenuPosition(e->popup, event);
  XtManageChild(e->popup);
}
static void key_event(Widget w, XtPointer data, XEvent *event, Boolean *dispatch) {
  TLEditor *e = data;
  (void)w;
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
  if(event->type==KeyPress&&XmIsTextField(w)&&XtIsSubclass(XtParent(w),xmSpinBoxWidgetClass)) {
    KeySym key=XLookupKeysym(&event->xkey,0);
    if(key==XK_Home||key==XK_End) {
      XmTextPosition cursor=XmTextFieldGetInsertionPosition(w);
      XmTextPosition target=key==XK_Home?0:XmTextFieldGetLastPosition(w);
      if(event->xkey.state&ShiftMask) {
        XmTextPosition first,last,anchor=cursor;
        if(XmTextFieldGetSelectionPosition(w,&first,&last))anchor=cursor==first?last:first;
        XmTextFieldSetSelection(w,anchor<target?anchor:target,anchor>target?anchor:target,event->xkey.time);
      } else XmTextFieldClearSelection(w,event->xkey.time);
      XmTextFieldSetInsertionPosition(w,target);
      *dispatch=False;return;
    }
  }
  if (event->type == KeyPress && (event->xkey.state & ControlMask) &&
      !(event->xkey.state & (Mod1Mask|Mod4Mask))) {
    KeySym key = XLookupKeysym(&event->xkey, 0);
    int cmd = -1;
    if (key >= XK_A && key <= XK_Z) key += XK_a - XK_A;
    switch (key) {
    case XK_z: cmd = event->xkey.state & ShiftMask ? TL_EDIT_REDO : TL_EDIT_UNDO; break;
    case XK_y: cmd = TL_EDIT_REDO; break;
    case XK_c: case XK_Insert: cmd = TL_EDIT_COPY; break;
    case XK_x: cmd = TL_EDIT_CUT; break;
    case XK_v: cmd = TL_EDIT_PASTE; break;
    case XK_a: cmd = TL_EDIT_ALL; break;
    }
    if (cmd >= 0) {
      *dispatch = False;
      tl_editor_command(e, cmd);
    }
  }
}
static void destroy(Widget w, XtPointer data, XtPointer call) {
  TLEditor *e=data, **cursor=&e->store->editors;
  (void)w;(void)call;
  while(*cursor&&*cursor!=e)cursor=&(*cursor)->next;
  if(*cursor)*cursor=e->next;
  free(e);
}
TLEditor *tl_editor_find(TLEditorStore *store, Widget w) {
  for(TLEditor *e=store->editors;e;e=e->next)if(e->widget==w)return e;
  return NULL;
}
void tl_editor_bind(TLEditorStore *store, Widget w, const char *key) {
  TLEditor *e=tl_editor_find(store,w);
  if(!e||!key[0]||strlen(key)>=sizeof(e->key)||!editable(e))return;
  /* Recovery can rebind the existing key buffer itself. snprintf with
   * overlapping input/output erased it and merged unrelated sample fields. */
  memmove(e->key,key,strlen(key)+1);
  e->history=get(store->histories,key);
  if(!e->history) {
    e->history=json_object_new_object();
    json_object_object_add(e->history,"entries",json_object_new_array());
    json_object_object_add(e->history,"position",json_object_new_int(0));
    json_object_object_add(store->histories,key,e->history);
  } else if(store->restoring) {
    json_object *a=get(e->history,"entries");
    int pos=json_object_get_int(get(e->history,"position"));
    e->replaying=1;
    set_content(e,json_object_get_string(json_object_array_get_idx(a,(size_t)pos)));
    e->replaying=0;
  }
}
static void attach(TLEditorStore *store, Widget w, const char *key) {
  if(tl_editor_find(store,w))return;
  TLEditor *e=calloc(1,sizeof(*e));
  if(!e)abort();
  e->widget=w;e->store=store;e->next=store->editors;store->editors=e;
  /* Let RowColumn own pointer posting/tracking from the first click. */
  create_menu(e);
  XtInsertEventHandler(w,KeyPressMask,False,key_event,e,XtListHead);
  XtAddCallback(w,XmNvalueChangedCallback,value_changed,e);
  XtAddCallback(w,XmNmodifyVerifyCallback,verify,e);
  XtAddCallback(w,XmNdestroyCallback,destroy,e);
  tl_editor_bind(store,w,key);
  char *text=content(e);remember(e,text);XtFree(text);
}
static void watch(TLEditorStore *store, Widget w, const char *path) {
  if(XmIsText(w)||XmIsTextField(w))attach(store,w,path);
  if(XtIsComposite(w)) {
    WidgetList children;Cardinal count;
    XtVaGetValues(w,XtNchildren,&children,XtNnumChildren,&count,NULL);
    for(Cardinal i=0;i<count;++i) {
      char key[1024];
      int n=snprintf(key,sizeof(key),"%s/%s[%u]",path,XtName(children[i]),i);
      if(n>0&&(size_t)n<sizeof(key))watch(store,children[i],key);
    }
  }
}
void tl_editor_watch_tree(TLEditorStore *store, Widget root, const char *key) {watch(store,root,key);}
void tl_editor_sync_begin(TLEditorStore *store) {++store->pause;}
void tl_editor_sync_end(TLEditorStore *store) {
  if(store->pause==1)for(TLEditor *e=store->editors;e;e=e->next)if(!e->history&&e->key[0])tl_editor_bind(store,e->widget,e->key);
  if(store->pause)--store->pause;
  if(!store->pause) {
    for(TLEditor *e=store->editors;e;e=e->next) {char *s=content(e);remember(e,s);XtFree(s);}
    store->restoring=0;
  }
}
void tl_editor_set_text(Widget w, const char *text) {
  char *current=XmIsTextField(w)?XmTextFieldGetString(w):XmTextGetString(w);
  if(strcmp(current,text)) {
    if(XmIsTextField(w))XmTextFieldSetString(w,(char *)text);
    else XmTextSetString(w,(char *)text);
  }
  XtFree(current);
}
