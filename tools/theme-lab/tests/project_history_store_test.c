/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include "project_history_store.h"
#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <signal.h>
#include <unistd.h>
int main(void) {
    char folder[]="/tmp/theme-lab-history-XXXXXX",path[256],lockpath[280],badpath[280],error[512];
    assert(mkdtemp(folder));snprintf(path,sizeof(path),"%s/history.json",folder);
    snprintf(lockpath,sizeof(lockpath),"%s.lock",path);
    TLModel model,loaded;tl_model_init(&model);
    snprintf(model.recipes[TL_GTK3].notes,sizeof(model.recipes[TL_GTK3].notes),"Comparação: ação, direção, opção — reversível.");
    TLProjectHistory *h=tl_history_new(&model,error,sizeof(error)),*recovered=NULL;
    json_object *revision=NULL,*next=NULL,*disk=NULL;
    assert(h);
    assert(tl_history_store_load(path,&recovered,&revision,error,sizeof(error))==1);
    assert(!recovered&&!revision);
    assert(!tl_history_mark(h));
    assert(!tl_history_store_commit(path,h,NULL,&revision,error,sizeof(error)));
    struct stat st;assert(!stat(path,&st)&&(st.st_mode&0777)==0600);
    model.recipes[TL_GTK3].sizes[10][0]=287;
    assert(!tl_history_push(h,&model,error,sizeof(error)));
    assert(!tl_history_store_commit(path,h,revision,&next,error,sizeof(error)));
    assert(!tl_history_store_load(path,&recovered,&disk,error,sizeof(error)));
    assert(!tl_history_current(recovered,&loaded,error,sizeof(error)));
    assert(!strcmp(loaded.recipes[TL_GTK3].notes,model.recipes[TL_GTK3].notes));
    assert(loaded.recipes[TL_GTK3].sizes[10][0]==model.recipes[TL_GTK3].sizes[10][0]);
    assert(tl_history_has_point(recovered)&&tl_history_can_step(recovered,-1));
    assert(!tl_history_step(recovered,-1,error,sizeof(error)));
    json_object *untouched=NULL;
    assert(tl_history_store_commit(path,recovered,revision,&untouched,error,sizeof(error))==-1&&!untouched);
    assert(strstr(error,"Conflito"));
    int lock=open(lockpath,O_RDWR);assert(lock>=0&&!flock(lock,LOCK_EX|LOCK_NB));
    assert(tl_history_store_commit(path,recovered,disk,&untouched,error,sizeof(error))==-1);
    assert(strstr(error,"ocupado"));close(lock);
    assert(!tl_history_store_commit(path,recovered,disk,&untouched,error,sizeof(error)));
    json_object_put(disk);disk=NULL;tl_history_free(recovered);recovered=NULL;
    assert(!tl_history_store_load(path,&recovered,&disk,error,sizeof(error)));
    assert(tl_history_can_step(recovered,1));
    /* Real short write under a per-child file-size limit must keep the old file. */
    pid_t child=fork();assert(child>=0);
    if(!child) {
        struct rlimit limit={32,32};assert(!setrlimit(RLIMIT_FSIZE,&limit));
        signal(SIGXFSZ,SIG_IGN);json_object *unused=NULL;
        assert(tl_history_store_commit(path,h,disk,&unused,error,sizeof(error))==-1);
        assert(!unused);_exit(0);
    }
    int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0);
    TLProjectHistory *still=NULL;json_object *still_revision=NULL;
    assert(!tl_history_store_load(path,&still,&still_revision,error,sizeof(error)));
    assert(json_object_equal(still_revision,disk));
    tl_history_free(still);json_object_put(still_revision);
    snprintf(badpath,sizeof(badpath),"%s/missing/history.json",folder);
    json_object *sentinel=json_object_new_object(),*out=sentinel;
    assert(tl_history_store_commit(badpath,h,NULL,&out,error,sizeof(error))==-1&&out==sentinel);
    /* Corruption is not silently replaced, and failed load keeps caller state. */
    FILE *file=fopen(path,"w");assert(file);fputs("{broken",file);assert(!fclose(file));
    TLProjectHistory *before=recovered;out=sentinel;
    assert(tl_history_store_load(path,&recovered,&out,error,sizeof(error))==-1);
    assert(recovered==before&&out==sentinel);
    assert(tl_history_store_commit(path,h,untouched,&out,error,sizeof(error))==-1);
    file=fopen(path,"r");assert(file);char text[20];assert(fgets(text,sizeof(text),file));fclose(file);
    assert(!strcmp(text,"{broken"));
    /* Neither a symlink nor a FIFO may be read as a history or overwritten. */
    unlink(path);assert(!symlink("other.json",path));
    assert(tl_history_store_load(path,&recovered,&out,error,sizeof(error))==-1);
    assert(tl_history_store_commit(path,h,NULL,&out,error,sizeof(error))==-1);
    unlink(path);assert(!mkfifo(path,0600));
    assert(tl_history_store_load(path,&recovered,&out,error,sizeof(error))==-1);
    unlink(path);unlink(lockpath);rmdir(folder);
    json_object_put(sentinel);json_object_put(revision);json_object_put(next);
    json_object_put(disk);json_object_put(untouched);tl_history_free(h);tl_history_free(recovered);
    puts("History store: UTF-8, recovery, Undo/Redo, checkpoint, CAS, busy lock, write failure, corruption, symlink and FIFO passed.");
    return 0;
}
