/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "project_session.h"
#include "project_history_store.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
struct TLProjectSession {TLProjectHistory *history;json_object *revision;char path[TL_PATH_MAX];};
static int fail(char *error,size_t capacity,const char *text) {
    if(error&&capacity)snprintf(error,capacity,"%s",text);
    return -1;
}
void tl_project_session_free(TLProjectSession *s) {
    if(s){tl_history_free(s->history);json_object_put(s->revision);free(s);}
}
int tl_project_session_open(TLProjectSession **out,const char *path,const TLModel *initial,char *error,size_t capacity) {
    if(!out||!path||!*path||strlen(path)>=TL_PATH_MAX)return fail(error,capacity,"Sessão de histórico inválida.");
    TLProjectSession *s=calloc(1,sizeof(*s));
    if(!s)return fail(error,capacity,"Memória insuficiente.");
    strcpy(s->path,path);
    int loaded=tl_history_store_load(path,&s->history,&s->revision,error,capacity),result=0;
    if(loaded<0){tl_project_session_free(s);return -1;}
    if(loaded==1) {
        s->history=tl_history_new(initial,error,capacity);
        if(!s->history){tl_project_session_free(s);return -1;}
        result=tl_history_store_commit(path,s->history,NULL,&s->revision,error,capacity);
        if(result<0){tl_project_session_free(s);return -1;}
    }
    *out=s;return result;
}
int tl_project_session_current(const TLProjectSession *s,TLModel *model,char *error,size_t capacity) {
    return s?tl_history_current(s->history,model,error,capacity):fail(error,capacity,"Sessão ausente.");
}
int tl_project_session_can_step(const TLProjectSession *s,int direction) {
    return s&&tl_history_can_step(s->history,direction);
}
int tl_project_session_has_point(const TLProjectSession *s) {return s&&tl_history_has_point(s->history);}
int tl_project_session_change(TLProjectSession *s,TLHistoryOperation operation,const TLModel *candidate,TLFamily family,TLScrollPart part,char *error,size_t capacity) {
    if(!s)return fail(error,capacity,"Sessão ausente.");
    json_object *root=tl_history_encode(s->history);
    TLProjectHistory *next=root?tl_history_decode(root,error,capacity):NULL;
    json_object_put(root);
    if(!next)return fail(error,capacity,"Não foi possível preparar a alteração; estado preservado.");
    int result=-1;
    switch(operation) {
    case TL_HISTORY_PUSH:
        result=candidate?tl_history_push(next,candidate,error,capacity):fail(error,capacity,"Projeto candidato ausente.");break;
    case TL_HISTORY_UNDO:result=tl_history_step(next,-1,error,capacity);break;
    case TL_HISTORY_REDO:result=tl_history_step(next,1,error,capacity);break;
    case TL_HISTORY_MARK:result=tl_history_mark(next);break;
    case TL_HISTORY_RESTORE:result=tl_history_restore(next,error,capacity);break;
    case TL_HISTORY_RESET_PART:result=tl_history_reset_part(next,family,part,error,capacity);break;
    default:fail(error,capacity,"Operação de histórico desconhecida.");break;
    }
    if(result<0){tl_history_free(next);return -1;}
    json_object *encoded=tl_history_encode(next);
    if(encoded&&json_object_equal(encoded,s->revision)) {
        json_object_put(encoded);tl_history_free(next);return 0;
    }
    json_object_put(encoded);
    json_object *revision=NULL;
    result=tl_history_store_commit(s->path,next,s->revision,&revision,error,capacity);
    if(result<0){tl_history_free(next);return -1;}
    /* All allocations happened before commit. Adopt even if directory fsync warned. */
    tl_history_free(s->history);json_object_put(s->revision);
    s->history=next;s->revision=revision;return result;
}
