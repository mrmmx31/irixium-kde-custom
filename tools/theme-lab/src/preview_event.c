/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "preview_event.h"
#include <json-c/json.h>
#include <string.h>
static const char *const ids[] = {"push","toggle","check","radio","entry","combo","spin","text","scale_h","scale_v","scroll_h","scroll_v","arrow","progress","list","frame"};
static int string_is(struct json_object *root,const char *key,const char *expected) {
    struct json_object *value=NULL;
    return json_object_object_get_ex(root,key,&value)&&json_object_is_type(value,json_type_string)&&
           (size_t)json_object_get_string_len(value)==strlen(expected)&&!strcmp(json_object_get_string(value),expected);
}
static int bounded_integer(struct json_object *root,const char *key,int lower,int upper,int *out) {
    struct json_object *value=NULL;int64_t number;
    if(!json_object_object_get_ex(root,key,&value)||!json_object_is_type(value,json_type_int))return -1;
    number=json_object_get_int64(value);if(number<lower||number>upper)return -1;
    *out=(int)number;return 0;
}
int tl_preview_event(const char *text,size_t length,const char *scene_hash,TLPreviewEvent *event) {
    struct json_tokener *parser;struct json_object *root;TLPreviewEvent next={0};int schema,result=-1;
    if(!text||!event||!scene_hash||strlen(scene_hash)!=64||length==0||length>16384||memchr(text,0,length))return -1;
    parser=json_tokener_new_ex(24);if(!parser)return -1;
    json_tokener_set_flags(parser,JSON_TOKENER_STRICT);
    root=json_tokener_parse_ex(parser,text,(int)length);
    if(json_tokener_get_error(parser)!=json_tokener_success||!json_object_is_type(root,json_type_object))goto done;
    if(bounded_integer(root,"schema_version",1,1,&schema)||
       !string_is(root,"kind","theme_lab_preview_event")||!string_is(root,"family","gtk3")||
       !string_is(root,"project_sha256",scene_hash)||bounded_integer(root,"control_index",0,15,&next.control)||
       !string_is(root,"control_id",ids[next.control]))goto done;
    if(string_is(root,"action","select"))next.action=TL_EVENT_SELECT;
    else if(string_is(root,"action","move")) {
        next.action=TL_EVENT_MOVE;
        if(bounded_integer(root,"x",0,2048,&next.x)||bounded_integer(root,"y",0,2048,&next.y)||
           !string_is(root,"coordinate_space","gtk_logical_px"))goto done;
    }else if(string_is(root,"action","native"))next.action=TL_EVENT_NATIVE;
    else goto done;
    *event=next;result=0;
done: if(root)json_object_put(root);json_tokener_free(parser);return result;
}
