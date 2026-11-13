/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_EDITOR_INTERNAL_H
#define TL_EDITOR_INTERNAL_H
#include "text_editor.h"
#include <json-c/json.h>
struct TLEditorStore {
    json_object *histories;
    TLEditor *editors;
    char path[4096];
    int dirty,pause,restoring;
};
struct TLEditor {
    Widget widget,popup,commands[6];
    json_object *history;
    TLEditorStore *store;
    TLEditor *next;
    char key[1024];
    int replaying;
};
#endif
