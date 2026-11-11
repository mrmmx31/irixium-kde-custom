/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "preview_event.h"
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv) {
    char text[16385];TLPreviewEvent event;FILE *file;size_t length;
    if(argc!=4 || !(file=fopen(argv[3],"rb")))return 2;
    length=fread(text,1,sizeof(text),file);
    int failed=ferror(file);fclose(file);
    if(failed || length>16384 || tl_preview_event_family(text,length,argv[2],argv[1],&event))return 1;
    printf("{\"action\":%d,\"control\":%d,\"width\":%d,\"height\":%d,"
           "\"toggle_state_known\":%s,\"toggle_active\":%s,\"toggle_separate\":%s}\n",
           event.action,event.control,event.width,event.height,
           event.toggle_state_known?"true":"false",
           event.toggle_active?"true":"false",
           event.toggle_separate?"true":"false");return 0;
}
