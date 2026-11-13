/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_TEXT_EDITOR_H
#define TL_TEXT_EDITOR_H
#include <Xm/Xm.h>
#include <stddef.h>
typedef struct TLEditorStore TLEditorStore;
typedef struct TLEditor TLEditor;
enum { TL_EDIT_UNDO, TL_EDIT_REDO, TL_EDIT_COPY, TL_EDIT_CUT, TL_EDIT_PASTE, TL_EDIT_ALL };
TLEditorStore *tl_editor_store_new(void);
void tl_editor_store_free(TLEditorStore *store);
int tl_editor_store_load(TLEditorStore *store,const char *path,char *error,size_t capacity);
int tl_editor_checkpoint(TLEditorStore *store,char *error,size_t capacity);
void tl_editor_watch_tree(TLEditorStore *store,Widget root,const char *key);
TLEditor *tl_editor_find(TLEditorStore *store,Widget widget);
void tl_editor_bind(TLEditorStore *store,Widget widget,const char *key);
void tl_editor_command(TLEditor *editor,int command);
void tl_editor_refresh_menus(TLEditorStore *store);
void tl_editor_sync_begin(TLEditorStore *store);
void tl_editor_sync_end(TLEditorStore *store);
void tl_editor_set_text(Widget widget,const char *text);
#endif
