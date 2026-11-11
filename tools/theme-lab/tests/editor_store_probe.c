/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "text_editor.h"
#include "../src/editor/internal.h"
#include <errno.h>
#include <stdio.h>
#include <string.h>
static int fail_directory_sync;
static int sync_calls;
int __real_fsync(int fd);
int __wrap_fsync(int fd) {
    ++sync_calls;
    if(fail_directory_sync&&sync_calls==2) { errno=EIO; return -1; }
    return __real_fsync(fd);
}
int main(int argc,char **argv) {
    char error[512];
    if(argc!=2&&(argc!=3||(strcmp(argv[2],"--checkpoint")&&
                           strcmp(argv[2],"--fail-directory-sync"))))return 2;
    fail_directory_sync=argc==3&&!strcmp(argv[2],"--fail-directory-sync");
    TLEditorStore *store=tl_editor_store_new();
    if(!store)return 2;
    int result=tl_editor_store_load(store,argv[1],error,sizeof(error));
    if(!result&&argc==3) {
        store->dirty=1;
        result=tl_editor_checkpoint(store,error,sizeof(error));
        if(fail_directory_sync&&(!result||!store->dirty))result=-1;
    }
    if(result)fprintf(stderr,"%s\n",error);
    tl_editor_store_free(store);return result?1:0;
}
