/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "preview_event.h"
#include <json-c/json.h>
#include <string.h>
static const char *const ids[] = {"push","toggle","check","radio","entry","combo","spin","text","scale_h","scale_v","scroll_h","scroll_v","arrow","progress","list","frame"};
size_t tl_preview_event_order(char names[][TL_PREVIEW_EVENT_FILENAME],size_t count,const char *name) {
    if(!names || !name || count>TL_PREVIEW_EVENT_BATCH)return count;
    size_t length=strlen(name),position=0;
    if(length<12 || length>=TL_PREVIEW_EVENT_FILENAME || strncmp(name,"event-",6) ||
       strcmp(name+length-5,".json"))return count;
    while(position<count && strcmp(names[position],name)<0)++position;
    if(position<count && !strcmp(names[position],name))return count;
    if(position==TL_PREVIEW_EVENT_BATCH)return count;
    size_t next=count<TL_PREVIEW_EVENT_BATCH?count+1:count;
    memmove(names[position+1],names[position],(next-position-1)*TL_PREVIEW_EVENT_FILENAME);
    memcpy(names[position],name,length+1);
    return next;
}
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
int tl_preview_event_family(const char *text,size_t length,const char *scene_hash,const char *family,TLPreviewEvent *event) {
    struct json_tokener *parser;struct json_object *root;TLPreviewEvent next={0};int schema,result=-1;
    if(!family || (strcmp(family,"gtk2") && strcmp(family,"gtk3") && strcmp(family,"gtk4")) ||
       !text||!event||!scene_hash||strlen(scene_hash)!=64||length==0||length>16384||memchr(text,0,length))return -1;
    parser=json_tokener_new_ex(24);if(!parser)return -1;
    json_tokener_set_flags(parser,JSON_TOKENER_STRICT | JSON_TOKENER_VALIDATE_UTF8);
    root=json_tokener_parse_ex(parser,text,(int)length);
    if(json_tokener_get_error(parser)!=json_tokener_success||!json_object_is_type(root,json_type_object))goto done;
    if(bounded_integer(root,"schema_version",1,1,&schema)||
       !string_is(root,"kind","theme_lab_preview_event")||!string_is(root,"family",family)||
       !string_is(root,"project_sha256",scene_hash)||bounded_integer(root,"control_index",0,15,&next.control)||
       !string_is(root,"control_id",ids[next.control]))goto done;
    /* Partial GTK4 renderer: native push, toggle, and check only. */
    if(!strcmp(family,"gtk4") && next.control>2)goto done;
    struct json_object *instance=NULL;
    if(json_object_object_get_ex(root,"preview_instance",&instance)) {
        if(!json_object_is_type(instance,json_type_string)||json_object_get_string_len(instance)!=32)goto done;
        const char *id=json_object_get_string(instance);
        for(int n=0;n<32;n++)if(!((id[n]>='0'&&id[n]<='9')||(id[n]>='a'&&id[n]<='f')))goto done;
        memcpy(next.instance,id,32);
    }
    if(string_is(root,"action","select"))next.action=TL_EVENT_SELECT;
    else if(string_is(root,"action","move")) {
        next.action=TL_EVENT_MOVE;
        if(bounded_integer(root,"x",0,2048,&next.x)||bounded_integer(root,"y",0,2048,&next.y)||
           !string_is(root,"coordinate_space","gtk_logical_px"))goto done;
    }else if(string_is(root,"action","native")) {
        next.action=TL_EVENT_NATIVE;
        struct json_object *state=NULL,*active=NULL;
        if(((!strcmp(family,"gtk2") && (next.control==1 || next.control==2)) ||
            (!strcmp(family,"gtk4") && (next.control==1 || next.control==2))) &&
           json_object_object_get_ex(root,"state",&state) &&
           json_object_is_type(state,json_type_object) &&
           json_object_object_get_ex(state,"active",&active)) {
            if(!json_object_is_type(active,json_type_boolean) ||
               (!string_is(root,"origin","coupled") && !string_is(root,"origin","separate")))goto done;
            next.toggle_state_known=1;
            next.toggle_active=json_object_get_boolean(active);
            next.toggle_separate=string_is(root,"origin","separate");
        }
        if(!strcmp(family,"gtk2") && next.control==3 &&
           json_object_object_get_ex(root,"state",&state) &&
           json_object_is_type(state,json_type_object) &&
           json_object_object_get_ex(state,"selected_member",&active)) {
            if(bounded_integer(state,"selected_member",0,1,&next.radio_member) ||
               (!string_is(root,"origin","coupled") && !string_is(root,"origin","separate")))goto done;
            next.radio_state_known=1;
            next.radio_separate=string_is(root,"origin","separate");
        }
    }
    else if(string_is(root,"action","metrics")) {
        next.action=TL_EVENT_METRICS;
        if(bounded_integer(root,"width",1,65535,&next.width)||
           bounded_integer(root,"height",1,65535,&next.height)||
           bounded_integer(root,"minimum_width",0,65535,&next.minimum_width)||
           bounded_integer(root,"minimum_height",0,65535,&next.minimum_height)||
           bounded_integer(root,"natural_width",0,65535,&next.metrics.natural_width)||
           bounded_integer(root,"natural_height",0,65535,&next.metrics.natural_height)||
           bounded_integer(root,"scale_factor",1,16,&next.metrics.scale_factor)||
           !string_is(root,"coordinate_space","gtk_logical_px"))goto done;
        if(string_is(root,"origin","separate"))next.metrics.separate=1;
        else if(!string_is(root,"origin","coupled"))goto done;
        next.metrics.width=next.width;next.metrics.height=next.height;
        next.metrics.minimum_width=next.minimum_width;next.metrics.minimum_height=next.minimum_height;
        if(next.metrics.natural_width<next.minimum_width||next.metrics.natural_height<next.minimum_height)goto done;
        struct json_object *range=NULL;
        if(json_object_object_get_ex(root,"range_geometry",&range)) {
            TLNativeRange *geometry=&next.metrics.range;
            if((next.control!=10 && next.control!=11) || !json_object_is_type(range,json_type_object) ||
               !string_is(range,"coordinate_space","gtk_widget_window_px") ||
               bounded_integer(range,"axis",0,1,&geometry->axis) || geometry->axis!=next.control-10 ||
               bounded_integer(range,"slider_start",0,65535,&geometry->slider_start) ||
               bounded_integer(range,"slider_end",1,65535,&geometry->slider_end) ||
               geometry->slider_end<=geometry->slider_start ||
               bounded_integer(range,"area_x",0,65535,&geometry->area_x) ||
               bounded_integer(range,"area_y",0,65535,&geometry->area_y) ||
               bounded_integer(range,"area_width",1,65535,&geometry->area_width) ||
               bounded_integer(range,"area_height",1,65535,&geometry->area_height))goto done;
            int area_start=geometry->axis?geometry->area_y:geometry->area_x;
            int area_length=geometry->axis?geometry->area_height:geometry->area_width;
            if(geometry->slider_start<area_start || geometry->slider_end>area_start+area_length)goto done;
            geometry->valid=1;
        }
        struct json_object *pieces=NULL;
        if(json_object_object_get_ex(root,"pieces_geometry",&pieces)) {
            if(strcmp(family,"gtk3") || (next.control!=10 && next.control!=11) ||
               !json_object_is_type(pieces,json_type_object) ||
               !string_is(pieces,"source","gtk3-3.24.49-verified-margin-boxes") ||
               !string_is(pieces,"coordinate_space","gtk_widget_local_px"))goto done;
            const char *names[]={"slider","track","arrow_first","arrow_last"};
            TLNativeRect *rects[]={&next.metrics.pieces.slider,&next.metrics.pieces.track,
                &next.metrics.pieces.arrows[0],&next.metrics.pieces.arrows[1]};
            for(int n=0;n<4;++n) {
                struct json_object *box=NULL;
                if(!json_object_object_get_ex(pieces,names[n],&box))continue;
                TLNativeRect *r=rects[n];
                if(!json_object_is_type(box,json_type_object) ||
                   bounded_integer(box,"x",0,65535,&r->x) ||
                   bounded_integer(box,"y",0,65535,&r->y) ||
                   bounded_integer(box,"width",1,65535,&r->width) ||
                   bounded_integer(box,"height",1,65535,&r->height) ||
                   r->x>next.width-r->width || r->y>next.height-r->height)goto done;
                next.metrics.pieces.mask|=1u<<n;
            }
            if(!next.metrics.pieces.mask)goto done;
            next.metrics.pieces.source=2;
        }
        struct json_object *offset=NULL;
        if(json_object_object_get_ex(root,"cell_offset_x",&offset) ||
           json_object_object_get_ex(root,"cell_offset_y",&offset)) {
            if(bounded_integer(root,"cell_offset_x",0,2048,&next.metrics.cell_offset_x)||
               bounded_integer(root,"cell_offset_y",0,2048,&next.metrics.cell_offset_y))goto done;
            next.metrics.cell_offset_valid=1;
        }
        if(json_object_object_get_ex(root,"position_x",&offset) ||
           json_object_object_get_ex(root,"position_y",&offset)) {
            if(bounded_integer(root,"position_x",0,65535,&next.metrics.position_x)||
               bounded_integer(root,"position_y",0,65535,&next.metrics.position_y))goto done;
            next.metrics.position_valid=1;
        }
        struct json_object *kind=NULL, *description=NULL;
        struct json_object *sensitive=NULL;
        if(json_object_object_get_ex(root,"sensitive",&sensitive)) {
            if(!json_object_is_type(sensitive,json_type_boolean))goto done;
            next.metrics.sensitivity_known=1;
            next.metrics.sensitive=json_object_get_boolean(sensitive);
        }
        if(json_object_object_get_ex(root,"font_kind",&kind) ||
           json_object_object_get_ex(root,"font_description",&description)) {
            if(bounded_integer(root,"font_kind",TL_FONT_MEASURED,TL_FONT_NONE,&next.metrics.font.kind) ||
               !json_object_object_get_ex(root,"font_description",&description) ||
               !json_object_is_type(description,json_type_string))goto done;
            const char *value=json_object_get_string(description);
            size_t size=(size_t)json_object_get_string_len(description);
            if(size>=sizeof(next.metrics.font.description) || memchr(value,0,size) ||
               (next.metrics.font.kind==TL_FONT_MEASURED && !size) ||
               (next.metrics.font.kind==TL_FONT_NONE && size))goto done;
            for(size_t i=0;i<size;++i)if((unsigned char)value[i]<32 || (unsigned char)value[i]==127)goto done;
            memcpy(next.metrics.font.description,value,size+1);
        }
    }
    else goto done;
    *event=next;result=0;
done: if(root)json_object_put(root);json_tokener_free(parser);return result;
}
int tl_preview_event(const char *text,size_t length,const char *scene_hash,TLPreviewEvent *event) {
    return tl_preview_event_family(text,length,scene_hash,"gtk3",event);
}
