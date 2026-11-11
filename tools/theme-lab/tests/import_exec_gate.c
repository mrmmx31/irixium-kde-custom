/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Test-only scheduling gate before the real backend exec; no forged response. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <signal.h>
#include <unistd.h>

int __real_execv(const char *path, char *const argv[]);
int __wrap_execv(const char *path, char *const argv[]) {
    const char *gate=getenv("TL_SPIN_IMPORT_GATE");
    int importing=0,generating=0;
    for(int i=0;argv[i];i++) {
        if(!strcmp(argv[i],"--import-delta"))importing=1;
        if(!strcmp(argv[i],"--generate"))generating=1;
    }
    if(generating)gate=getenv("TL_SPIN_GENERATE_GATE");
    if(gate&&(importing||generating)) {
        char arm[4096],ready[4096],release[4096];
        if(snprintf(arm,sizeof(arm),"%s.arm",gate)>=(int)sizeof(arm)||
           snprintf(ready,sizeof(ready),"%s.ready",gate)>=(int)sizeof(ready)||
           snprintf(release,sizeof(release),"%s.release",gate)>=(int)sizeof(release))_exit(124);
        if(access(arm,F_OK)==0) {
            if(unlink(arm))_exit(124);
            char spawn[4096],child_ready[4096];
            if(snprintf(spawn,sizeof(spawn),"%s.spawn-descendant",gate)>=(int)sizeof(spawn)||
               snprintf(child_ready,sizeof(child_ready),"%s.descendant-ready",gate)>=(int)sizeof(child_ready))_exit(124);
            if(generating&&access(spawn,F_OK)==0) {
                signal(SIGTERM,SIG_DFL);
                int sync[2];if(pipe(sync))_exit(124);
                pid_t child=fork();if(child<0)_exit(124);
                if(!child) {
                    close(sync[0]);signal(SIGTERM,SIG_IGN);
                    if(write(sync[1],"r",1)!=1)_exit(124);
                    close(sync[1]);for(;;)pause();
                }
                close(sync[1]);char byte;
                if(read(sync[0],&byte,1)!=1)_exit(124);
                close(sync[0]);FILE *cf=fopen(child_ready,"w");if(!cf)_exit(124);
                fprintf(cf,"%ld\n",(long)child);if(fclose(cf))_exit(124);
            }
            FILE *f=fopen(ready,"w");if(!f)_exit(124);
            fprintf(f,"%ld\n",(long)getpid());if(fclose(f))_exit(124);
            struct timespec step={0,10000000};
            int attempts=0;
            while(access(release,F_OK)!=0&&attempts++<(generating?4500:1500))nanosleep(&step,NULL);
            if(access(release,F_OK)!=0)_exit(125);
        }
    }
    return __real_execv(path,argv);
}
