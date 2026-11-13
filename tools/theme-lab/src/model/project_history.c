/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "project_history.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct TLProjectHistory {json_object *entries,*point;size_t position;};
static int fail(char *error,size_t capacity,const char *message) {
    if(error&&capacity)snprintf(error,capacity,"%s",message);
    return -1;
}
static json_object *copy(json_object *object) {
    json_object *result=NULL;
    if(!object||json_object_deep_copy(object,&result,NULL))return NULL;
    return result;
}
void tl_history_free(TLProjectHistory *h) {
    if(h) {json_object_put(h->entries);json_object_put(h->point);free(h);}
}
TLProjectHistory *tl_history_new(const TLModel *initial,char *error,size_t capacity) {
    json_object *model=tl_model_encode(initial,error,capacity);
    if(!model)return NULL;
    TLProjectHistory *h=calloc(1,sizeof(*h));
    if(!h) {json_object_put(model);fail(error,capacity,"Memória insuficiente");return NULL;}
    h->entries=json_object_new_array();
    if(!h->entries||json_object_array_add(h->entries,model)) {
        json_object_put(model);tl_history_free(h);return NULL;
    }
    return h;
}
int tl_history_current(const TLProjectHistory *h,TLModel *model,char *error,size_t capacity) {
    if(!h)return fail(error,capacity,"Histórico ausente");
    return tl_model_decode(model,json_object_array_get_idx(h->entries,h->position),error,capacity);
}
int tl_history_can_step(const TLProjectHistory *h,int direction) {
    return h&&((direction==-1&&h->position>0)||
        (direction==1&&h->position+1<json_object_array_length(h->entries)));
}
int tl_history_step(TLProjectHistory *h,int direction,char *error,size_t capacity) {
    if(!tl_history_can_step(h,direction))return fail(error,capacity,"Não há alteração para desfazer/refazer");
    if(direction<0)--h->position;else ++h->position;
    return 0;
}
int tl_history_push(TLProjectHistory *h,const TLModel *model,char *error,size_t capacity) {
    if(!h)return fail(error,capacity,"Histórico ausente");
    json_object *next=tl_model_encode(model,error,capacity);
    if(!next)return -1;
    if(json_object_equal(next,json_object_array_get_idx(h->entries,h->position))) {json_object_put(next);return 0;}
    json_object *entries=json_object_new_array();
    if(!entries) {json_object_put(next);return fail(error,capacity,"Memória insuficiente");}
    size_t start=h->position+1>=TL_HISTORY_LIMIT?1:0;
    for(size_t i=start;i<=h->position;++i) {
        json_object *entry=json_object_get(json_object_array_get_idx(h->entries,i));
        if(json_object_array_add(entries,entry)) {json_object_put(entry);goto failed;}
    }
    if(json_object_array_add(entries,next))goto failed;
    json_object_put(h->entries);h->entries=entries;h->position=json_object_array_length(entries)-1;
    return 0;
failed:
    json_object_put(entries);json_object_put(next);return fail(error,capacity,"Memória insuficiente");
}
int tl_history_mark(TLProjectHistory *h) {
    if(!h)return -1;
    json_object *point=copy(json_object_array_get_idx(h->entries,h->position));
    if(!point)return -1;
    json_object_put(h->point);h->point=point;return 0;
}
int tl_history_has_point(const TLProjectHistory *h) {return h&&h->point;}
int tl_history_restore(TLProjectHistory *h,char *error,size_t capacity) {
    TLModel model;
    if(!tl_history_has_point(h))return fail(error,capacity,"Ponto salvo ausente");
    if(tl_model_decode(&model,h->point,error,capacity))return -1;
    return tl_history_push(h,&model,error,capacity);
}
int tl_history_reset_part(TLProjectHistory *h,TLFamily family,TLScrollPart part,char *error,size_t capacity) {
    TLModel model;
    if((int)family<0||family>=TL_FAMILY_COUNT||(int)part<0||part>=TL_SCROLL_PART_COUNT)
        return fail(error,capacity,"Peça ou família inválida");
    if(tl_history_current(h,&model,error,capacity))return -1;
    memset(&model.recipes[family].scrollbar_parts.parts[part],0,sizeof(TLPartRecipe));
    return tl_history_push(h,&model,error,capacity);
}
json_object *tl_history_encode(const TLProjectHistory *h) {
    if(!h)return NULL;
    json_object *entries=copy(h->entries),*point=h->point?copy(h->point):NULL;
    if(!entries||(h->point&&!point)) {json_object_put(entries);json_object_put(point);return NULL;}
    json_object *root=json_object_new_object();
    if(!root) {json_object_put(entries);json_object_put(point);return NULL;}
    json_object_object_add(root,"schema_version",json_object_new_int(1));
    json_object_object_add(root,"kind",json_object_new_string("theme_lab_project_history"));
    json_object_object_add(root,"position",json_object_new_int64((int64_t)h->position));
    json_object_object_add(root,"entries",entries);
    if(point)json_object_object_add(root,"point",point);
    return root;
}
TLProjectHistory *tl_history_decode(json_object *root,char *error,size_t capacity) {
    json_object *version=NULL,*kind=NULL,*position=NULL,*entries=NULL,*point=NULL;
    if(!root||!json_object_is_type(root,json_type_object)||
       !json_object_object_get_ex(root,"schema_version",&version)||!json_object_is_type(version,json_type_int)||json_object_get_int64(version)!=1||
       !json_object_object_get_ex(root,"kind",&kind)||!json_object_is_type(kind,json_type_string)||json_object_get_string_len(kind)!=25||strcmp(json_object_get_string(kind),"theme_lab_project_history")||
       !json_object_object_get_ex(root,"position",&position)||!json_object_is_type(position,json_type_int)||
       !json_object_object_get_ex(root,"entries",&entries)||!json_object_is_type(entries,json_type_array))goto invalid;
    size_t n=json_object_array_length(entries);int64_t pos=json_object_get_int64(position);
    if(n<1||n>TL_HISTORY_LIMIT||pos<0||(uint64_t)pos>=n)goto invalid;
    TLModel model;
    for(size_t i=0;i<n;++i)if(tl_model_decode(&model,json_object_array_get_idx(entries,i),error,capacity))return NULL;
    if(json_object_object_get_ex(root,"point",&point)&&tl_model_decode(&model,point,error,capacity))return NULL;
    TLProjectHistory *h=calloc(1,sizeof(*h));if(!h)return NULL;
    h->entries=copy(entries);h->point=point?copy(point):NULL;h->position=(size_t)pos;
    if(!h->entries||(point&&!h->point)) {tl_history_free(h);return NULL;}
    return h;
invalid:
    fail(error,capacity,"Histórico inválido; dados existentes preservados");return NULL;
}
