/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include "project_session.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static int equal(const TLModel *a,const TLModel *b) {
    char error[512];json_object *x=tl_model_encode(a,error,sizeof(error)),*y=tl_model_encode(b,error,sizeof(error));
    assert(x&&y);int same=json_object_equal(x,y);json_object_put(x);json_object_put(y);return same;
}
static void change(TLProjectSession *s,TLHistoryOperation op,const TLModel *m) {
    char error[512];assert(!tl_project_session_change(s,op,m,TL_GTK3,TL_SCROLL_THUMB,error,sizeof(error)));
}
int main(void) {
    char folder[]="/tmp/theme-lab-session-XXXXXX",path[256],lock[280],renamed[280],error[512];
    assert(mkdtemp(folder));snprintf(path,sizeof(path),"%s/history.json",folder);snprintf(lock,sizeof(lock),"%s.lock",path);
    TLModel initial,edited,current,expected;tl_model_init(&initial);edited=initial;
    TLProjectSession *s=NULL,*other=NULL;
    assert(!tl_project_session_open(&s,path,&initial,error,sizeof(error)));
    change(s,TL_HISTORY_MARK,NULL);
    edited.recipes[TL_GTK3].sizes[10][0]=350;
    edited.recipes[TL_GTK3].positions[10][1]=42;
    strcpy(edited.recipes[TL_GTK3].notes,"Ajuste: posição e dimensões preservadas.");
    assert(!tl_part_relief_set(&edited.recipes[TL_GTK3].scrollbar_parts.parts[TL_SCROLL_THUMB],1,3));
    assert(!tl_part_relief_set(&edited.recipes[TL_GTK3].scrollbar_parts.parts[TL_SCROLL_ARROW],0,2));
    change(s,TL_HISTORY_PUSH,&edited);
    change(s,TL_HISTORY_RESET_PART,NULL);
    expected=edited;memset(&expected.recipes[TL_GTK3].scrollbar_parts.parts[TL_SCROLL_THUMB],0,sizeof(TLPartRecipe));
    assert(!tl_project_session_current(s,&current,error,sizeof(error))&&equal(&current,&expected));
    change(s,TL_HISTORY_UNDO,NULL);
    assert(!tl_project_session_current(s,&current,error,sizeof(error))&&equal(&current,&edited));
    tl_project_session_free(s);s=NULL;
    assert(!tl_project_session_open(&s,path,&initial,error,sizeof(error)));
    assert(tl_project_session_has_point(s)&&tl_project_session_can_step(s,1));
    assert(!tl_project_session_current(s,&current,error,sizeof(error))&&equal(&current,&edited));
    change(s,TL_HISTORY_REDO,NULL);change(s,TL_HISTORY_RESTORE,NULL);
    assert(!tl_project_session_current(s,&current,error,sizeof(error))&&equal(&current,&initial));
    change(s,TL_HISTORY_UNDO,NULL);
    assert(!tl_project_session_current(s,&current,error,sizeof(error))&&equal(&current,&expected));
    /* Another session commits; a stale operation must not change the live state. */
    assert(!tl_project_session_open(&other,path,&initial,error,sizeof(error)));
    change(other,TL_HISTORY_PUSH,&edited);
    assert(tl_project_session_change(s,TL_HISTORY_UNDO,NULL,TL_GTK3,TL_SCROLL_THUMB,error,sizeof(error))<0);
    assert(strstr(error,"Conflito"));
    assert(!tl_project_session_current(s,&current,error,sizeof(error))&&equal(&current,&expected));
    assert(tl_project_session_can_step(s,-1)&&tl_project_session_can_step(s,1));
    TLModel invalid=edited;invalid.recipes[TL_GTK3].geometry.bar_px=-1;
    assert(tl_project_session_change(other,TL_HISTORY_PUSH,&invalid,TL_GTK3,TL_SCROLL_THUMB,error,sizeof(error))<0);
    assert(!tl_project_session_current(other,&current,error,sizeof(error))&&equal(&current,&edited));
    /* Missing parent: checkpoint/save failure keeps model and prior checkpoint. */
    snprintf(renamed,sizeof(renamed),"%s-away",folder);assert(!rename(folder,renamed));
    assert(tl_project_session_change(other,TL_HISTORY_MARK,NULL,TL_GTK3,TL_SCROLL_THUMB,error,sizeof(error))<0);
    assert(!tl_project_session_current(other,&current,error,sizeof(error))&&equal(&current,&edited));
    assert(tl_project_session_has_point(other));assert(!rename(renamed,folder));
    change(other,TL_HISTORY_RESTORE,NULL);
    assert(!tl_project_session_current(other,&current,error,sizeof(error))&&equal(&current,&initial));
    tl_project_session_free(s);tl_project_session_free(other);unlink(path);unlink(lock);rmdir(folder);
    puts("Project session: transactional push/Undo/Redo/checkpoint/restore/selective reset, recovery, conflict and failed save preserve live state.");
    return 0;
}
