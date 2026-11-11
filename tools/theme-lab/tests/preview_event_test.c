/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "preview_event.h"
#include <json-c/json.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"IPC check failed: line %d\n",__LINE__);exit(1);}}while(0)
int main(void) {
    char names[TL_PREVIEW_EVENT_BATCH][TL_PREVIEW_EVENT_FILENAME],filename[100];size_t count=0;
    for(int i=40;i>=1;i--) {
        snprintf(filename,sizeof(filename),"event-%020d-test.json",i);
        count=tl_preview_event_order(names,count,filename);
    }
    CHECK(count==32);
    for(int i=1;i<=32;i++) {
        snprintf(filename,sizeof(filename),"event-%020d-test.json",i);
        CHECK(!strcmp(names[i-1],filename));
    }
    CHECK(tl_preview_event_order(names,count,".temporary")==32);
    CHECK(tl_preview_event_order(names,count,names[0])==32);
    const char *hash="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
    char text[2048];TLPreviewEvent event={.control=7};
    snprintf(text,sizeof(text),"{\"schema_version\":1,\"kind\":\"theme_lab_preview_event\",\"family\":\"gtk3\",\"action\":\"move\",\"control_id\":\"arrow\",\"control_index\":12,\"project_sha256\":\"%s\",\"x\":125,\"y\":24,\"coordinate_space\":\"gtk_logical_px\"}\n",hash);
    CHECK(tl_preview_event(text,strlen(text),hash,&event)==0);
    CHECK(event.control==12&&event.x==125&&event.y==24&&event.action==TL_EVENT_MOVE);
    CHECK(tl_preview_event(text,strlen(text),"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",&event)==-1);
    CHECK(event.x==125); /* transactional on invalid/stale input */
    {char *position=strstr(text,"125");memcpy(position,"-99",3);}
    CHECK(tl_preview_event(text,strlen(text),hash,&event)==-1);
    {char *position=strstr(text,"-99");memcpy(position,"125",3);}
    {char *position=strstr(text,"\"arrow\"");memcpy(position+1,"entry",5);}
    CHECK(tl_preview_event(text,strlen(text),hash,&event)==-1);
    CHECK(tl_preview_event("{",1,hash,&event)==-1);
    CHECK(tl_preview_event(text,16385,hash,&event)==-1);
    snprintf(text,sizeof(text),"{\"schema_version\":1,\"kind\":\"theme_lab_preview_event\",\"family\":\"gtk3\",\"action\":\"metrics\",\"control_id\":\"push\",\"control_index\":0,\"project_sha256\":\"%s\",\"width\":120,\"height\":44,\"minimum_width\":150,\"minimum_height\":30,\"natural_width\":160,\"natural_height\":40,\"scale_factor\":2,\"origin\":\"separate\",\"coordinate_space\":\"gtk_logical_px\"}\n",hash);
    CHECK(tl_preview_event(text,strlen(text),hash,&event)==0);
    CHECK(event.metrics.width==120&&event.metrics.minimum_width==150&&event.metrics.scale_factor==2&&event.metrics.separate==1);
    CHECK(!event.metrics.cell_offset_valid); /* older metrics remain readable */
    struct json_object *data=json_tokener_parse(text);
    json_object_object_add(data,"sensitive",json_object_new_boolean(0));
    const char *sensitivity_text=json_object_to_json_string(data);
    CHECK(tl_preview_event(sensitivity_text,strlen(sensitivity_text),hash,&event)==0);
    CHECK(event.metrics.sensitivity_known && !event.metrics.sensitive);
    json_object_object_add(data,"sensitive",json_object_new_int(1));
    sensitivity_text=json_object_to_json_string(data);
    CHECK(tl_preview_event(sensitivity_text,strlen(sensitivity_text),hash,&event)==-1);
    CHECK(event.metrics.sensitivity_known && !event.metrics.sensitive);
    json_object_object_add(data,"sensitive",json_object_new_boolean(1));
    json_object_object_add(data,"cell_offset_x",json_object_new_int(0));
    const char *encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    json_object_object_add(data,"cell_offset_y",json_object_new_int(25));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==0);
    CHECK(event.metrics.cell_offset_valid&&event.metrics.cell_offset_y==25);
    json_object_object_add(data,"cell_offset_y",json_object_new_boolean(1));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    CHECK(event.metrics.cell_offset_y==25);
    json_object_object_add(data,"cell_offset_y",json_object_new_int(25));
    json_object_object_add(data,"position_x",json_object_new_int(16));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    json_object_object_add(data,"position_y",json_object_new_int(70));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==0);
    CHECK(event.metrics.position_valid&&event.metrics.position_x==16&&event.metrics.position_y==70);
    json_object_object_add(data,"position_y",json_object_new_int(-1));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    CHECK(event.metrics.position_y==70);
    json_object_object_add(data,"position_y",json_object_new_int(70));
    json_object_object_add(data,"font_kind",json_object_new_int(TL_FONT_MEASURED));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    json_object_object_add(data,"font_description",json_object_new_string("Pango contexto carregado: Nimbus Sans 13"));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==0);
    CHECK(event.metrics.font.kind==TL_FONT_MEASURED && strstr(event.metrics.font.description,"Nimbus Sans"));
    json_object_object_add(data,"font_description",json_object_new_string("bad\ntext"));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    CHECK(strstr(event.metrics.font.description,"Nimbus Sans"));
    json_object_object_add(data,"font_kind",json_object_new_int(TL_FONT_NONE));
    json_object_object_add(data,"font_description",json_object_new_string(""));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==0);
    CHECK(event.metrics.font.kind==TL_FONT_NONE && !event.metrics.font.description[0]);
    json_object_object_add(data,"font_description",json_object_new_string("unexpected"));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    json_object_object_add(data,"font_kind",json_object_new_int(TL_FONT_MEASURED));
    char invalid_utf8[]={ (char)0xff, 0 };
    json_object_object_add(data,"font_description",json_object_new_string(invalid_utf8));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    json_object_put(data);
    CHECK(tl_preview_event(text,strlen(text),"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",&event)==-1);
    CHECK(event.metrics.width==120);
    {char *position=strstr(text,"\"scale_factor\":2");position[strlen("\"scale_factor\":")]='0';}
    CHECK(tl_preview_event(text,strlen(text),hash,&event)==-1);
    data=json_tokener_parse(text);
    json_object_object_add(data,"scale_factor",json_object_new_int(1));
    json_object_object_add(data,"control_id",json_object_new_string("scroll_h"));
    json_object_object_add(data,"control_index",json_object_new_int(10));
    struct json_object *range=json_tokener_parse("{\"axis\":0,\"slider_start\":55,\"slider_end\":100,\"area_x\":16,\"area_y\":36,\"area_width\":120,\"area_height\":15,\"coordinate_space\":\"gtk_widget_window_px\"}");
    json_object_object_add(data,"range_geometry",range);
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==0);
    CHECK(event.metrics.range.valid && event.metrics.range.slider_end==100);
    json_object_object_add(range,"axis",json_object_new_int(1));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    CHECK(event.metrics.range.slider_end==100);
    json_object_object_add(range,"axis",json_object_new_int(0));
    json_object_object_add(range,"slider_end",json_object_new_int(200));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1); /* outside native area */
    json_object_object_add(range,"slider_end",json_object_new_int(55));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1); /* no positive extent */
    json_object_object_add(range,"slider_end",json_object_new_int(100));
    json_object_object_del(range,"area_height");
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1); /* incomplete geometry */
    json_object_object_del(data,"range_geometry");
    struct json_object *pieces=json_tokener_parse("{\"source\":\"gtk3-3.24.49-verified-margin-boxes\",\"coordinate_space\":\"gtk_widget_local_px\",\"slider\":{\"x\":20,\"y\":2,\"width\":30,\"height\":11},\"track\":{\"x\":14,\"y\":2,\"width\":90,\"height\":11}}");
    json_object_object_add(data,"pieces_geometry",pieces);
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==0);
    CHECK(event.metrics.pieces.source==2 && event.metrics.pieces.mask==3);
    TLPreviewEvent previous=event;
    struct json_object *slider=NULL;json_object_object_get_ex(pieces,"slider",&slider);
    json_object_object_add(slider,"width",json_object_new_int(65535));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    CHECK(!memcmp(&event,&previous,sizeof(event)));
    json_object_object_add(slider,"width",json_object_new_int(30));
    json_object_object_add(pieces,"source",json_object_new_string("unsupported"));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event(encoded,strlen(encoded),hash,&event)==-1);
    json_object_put(data);
    snprintf(text,sizeof(text),"{\"schema_version\":1,\"kind\":\"theme_lab_preview_event\",\"family\":\"gtk2\",\"action\":\"select\",\"control_id\":\"scroll_h\",\"control_index\":10,\"project_sha256\":\"%s\"}",hash);
    TLPreviewEvent unchanged=event;
    CHECK(tl_preview_event(text,strlen(text),hash,&event)==-1);
    CHECK(!memcmp(&event,&unchanged,sizeof(event)));
    CHECK(tl_preview_event_family(text,strlen(text),hash,"gtk2",&event)==0);
    CHECK(event.control==10 && event.action==TL_EVENT_SELECT);
    unchanged=event;
    CHECK(tl_preview_event_family(text,strlen(text),hash,"gtk3",&event)==-1);
    CHECK(tl_preview_event_family(text,strlen(text),hash,"gtk4",&event)==-1);
    CHECK(!memcmp(&event,&unchanged,sizeof(event)));
    snprintf(text,sizeof(text),"{\"schema_version\":1,\"kind\":\"theme_lab_preview_event\",\"family\":\"gtk2\",\"action\":\"native\",\"control_id\":\"toggle\",\"control_index\":1,\"project_sha256\":\"%s\",\"origin\":\"separate\",\"state\":{\"active\":true}}",hash);
    CHECK(!tl_preview_event_family(text,strlen(text),hash,"gtk2",&event));
    CHECK(event.toggle_state_known&&event.toggle_active&&event.toggle_separate);
    data=json_tokener_parse(text);
    struct json_object *toggle_state=NULL;
    json_object_object_get_ex(data,"state",&toggle_state);
    json_object_object_add(toggle_state,"active",json_object_new_boolean(0));
    json_object_object_add(data,"origin",json_object_new_string("coupled"));
    encoded=json_object_to_json_string(data);
    CHECK(!tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event));
    CHECK(event.toggle_state_known&&!event.toggle_active&&!event.toggle_separate);
    unchanged=event;
    json_object_object_add(toggle_state,"active",json_object_new_int(1));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event)==-1);
    CHECK(!memcmp(&event,&unchanged,sizeof(event)));
    json_object_object_add(toggle_state,"active",json_object_new_boolean(1));
    json_object_object_del(data,"origin");
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event)==-1);
    CHECK(!memcmp(&event,&unchanged,sizeof(event)));
    json_object_put(data);
    snprintf(text,sizeof(text),"{\"schema_version\":1,\"kind\":\"theme_lab_preview_event\",\"family\":\"gtk2\",\"action\":\"native\",\"control_id\":\"radio\",\"control_index\":3,\"project_sha256\":\"%s\",\"origin\":\"separate\",\"state\":{\"selected_member\":1}}",hash);
    CHECK(!tl_preview_event_family(text,strlen(text),hash,"gtk2",&event));
    CHECK(event.radio_state_known&&event.radio_member==1&&event.radio_separate);
    unchanged=event;data=json_tokener_parse(text);
    json_object_object_get_ex(data,"state",&toggle_state);
    for(int invalid=-1;invalid<=2;invalid+=3) {
        json_object_object_add(toggle_state,"selected_member",json_object_new_int(invalid));
        encoded=json_object_to_json_string(data);
        CHECK(tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event)==-1);
        CHECK(!memcmp(&event,&unchanged,sizeof(event)));
    }
    json_object_object_add(toggle_state,"selected_member",json_object_new_boolean(1));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event)==-1);
    json_object_object_add(toggle_state,"selected_member",json_object_new_int(0));
    json_object_object_add(data,"origin",json_object_new_string("coupled"));
    encoded=json_object_to_json_string(data);
    CHECK(!tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event));
    CHECK(event.radio_state_known&&event.radio_member==0&&!event.radio_separate);
    unchanged=event;json_object_object_del(data,"origin");
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event)==-1);
    CHECK(!memcmp(&event,&unchanged,sizeof(event)));
    json_object_put(data);
    snprintf(text,sizeof(text),"{\"schema_version\":1,\"kind\":\"theme_lab_preview_event\",\"family\":\"gtk2\",\"action\":\"native\",\"control_id\":\"check\",\"control_index\":2,\"project_sha256\":\"%s\",\"origin\":\"coupled\",\"state\":{\"active\":true}}",hash);
    CHECK(!tl_preview_event_family(text,strlen(text),hash,"gtk2",&event));
    CHECK(event.control==2&&event.toggle_state_known&&event.toggle_active&&!event.toggle_separate);
    unchanged=event;data=json_tokener_parse(text);
    json_object_object_get_ex(data,"state",&toggle_state);
    json_object_object_add(toggle_state,"active",json_object_new_int(1));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event)==-1);
    CHECK(!memcmp(&event,&unchanged,sizeof(event)));
    json_object_object_add(toggle_state,"active",json_object_new_boolean(0));
    json_object_object_add(data,"origin",json_object_new_string("separate"));
    encoded=json_object_to_json_string(data);
    CHECK(!tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event));
    CHECK(event.control==2&&event.toggle_state_known&&!event.toggle_active&&event.toggle_separate);
    json_object_object_del(data,"origin");
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event)==-1);
    json_object_put(data);
    data=json_tokener_parse(text);
    json_object_object_add(data,"preview_instance",json_object_new_string("abcdef0123456789abcdef0123456789"));
    encoded=json_object_to_json_string(data);
    CHECK(!tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event));
    CHECK(!strcmp(event.instance,"abcdef0123456789abcdef0123456789"));
    unchanged=event;
    const char *bad_instances[]={"short","ABCDEF0123456789abcdef0123456789","abcdef0123456789abcdef0123456789a"};
    for(int i=0;i<3;i++) {
        json_object_object_add(data,"preview_instance",json_object_new_string(bad_instances[i]));
        encoded=json_object_to_json_string(data);
        CHECK(tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event)==-1);
        CHECK(!memcmp(&event,&unchanged,sizeof(event)));
    }
    json_object_object_add(data,"preview_instance",json_object_new_int(17));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event_family(encoded,strlen(encoded),hash,"gtk2",&event)==-1);
    CHECK(!memcmp(&event,&unchanged,sizeof(event)));
    json_object_put(data);
    snprintf(text,sizeof(text),"{\"schema_version\":1,\"kind\":\"theme_lab_preview_event\",\"family\":\"gtk4\",\"action\":\"move\",\"control_id\":\"push\",\"control_index\":0,\"project_sha256\":\"%s\",\"x\":52,\"y\":52,\"coordinate_space\":\"gtk_logical_px\"}",hash);
    CHECK(!tl_preview_event_family(text,strlen(text),hash,"gtk4",&event));
    CHECK(event.action==TL_EVENT_MOVE && event.control==0 && event.x==52);
    unchanged=event;
    CHECK(tl_preview_event(text,strlen(text),hash,&event)==-1);
    data=json_tokener_parse(text);
    json_object_object_add(data,"control_id",json_object_new_string("toggle"));
    json_object_object_add(data,"control_index",json_object_new_int(1));
    encoded=json_object_to_json_string(data);
    CHECK(!tl_preview_event_family(encoded,strlen(encoded),hash,"gtk4",&event));
    CHECK(event.control==1 && event.action==TL_EVENT_MOVE);
    unchanged=event;
    json_object_object_add(data,"control_id",json_object_new_string("check"));
    json_object_object_add(data,"control_index",json_object_new_int(2));
    json_object_object_add(data,"action",json_object_new_string("native"));
    json_object_object_add(data,"origin",json_object_new_string("coupled"));
    struct json_object *state=json_object_new_object();
    json_object_object_add(state,"active",json_object_new_boolean(1));
    json_object_object_add(state,"selected",json_object_new_boolean(1));
    json_object_object_add(data,"state",state);
    encoded=json_object_to_json_string(data);
    CHECK(!tl_preview_event_family(encoded,strlen(encoded),hash,"gtk4",&event));
    CHECK(event.control==2 && event.action==TL_EVENT_NATIVE &&
          event.toggle_state_known && event.toggle_active && !event.toggle_separate);
    unchanged=event;
    json_object_object_add(data,"control_id",json_object_new_string("radio"));
    json_object_object_add(data,"control_index",json_object_new_int(3));
    encoded=json_object_to_json_string(data);
    CHECK(tl_preview_event_family(encoded,strlen(encoded),hash,"gtk4",&event)==-1);
    CHECK(!memcmp(&event,&unchanged,sizeof(event)));
    json_object_put(data);
    puts("IPC checks passed: transactional metrics, origins and preview identity.");return 0;
}
