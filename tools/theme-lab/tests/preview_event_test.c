/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "preview_event.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"IPC check failed: line %d\n",__LINE__);exit(1);}}while(0)
int main(void) {
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
    puts("8 IPC checks passed: stale scene, bounds, identity, transactional parsing.");return 0;
}
