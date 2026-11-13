/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "owned_processes.h"
#include <assert.h>
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static void asleep(void) {for(;;)pause();}
static long long now_ms(void) {
    struct timespec t;assert(!clock_gettime(CLOCK_MONOTONIC,&t));
    return (long long)t.tv_sec*1000+t.tv_nsec/1000000;
}
static void group_case(int exit_leader,int polling,pid_t independent) {
    int ready[2];assert(!pipe(ready));pid_t leader=fork();assert(leader>=0);
    if(!leader) {
        close(ready[0]);assert(!setpgid(0,0));signal(SIGTERM,SIG_IGN);
        pid_t descendant=fork();assert(descendant>=0);
        if(!descendant){close(ready[1]);asleep();}
        assert(write(ready[1],&descendant,sizeof(descendant))==(ssize_t)sizeof(descendant));
        close(ready[1]);if(exit_leader)_exit(0);asleep();
    }
    close(ready[1]);pid_t descendant=0;
    assert(read(ready[0],&descendant,sizeof(descendant))==(ssize_t)sizeof(descendant));close(ready[0]);
    assert(getpgid(leader)==leader&&getpgid(descendant)==leader);
    if(exit_leader) {
        siginfo_t info={0};assert(!waitid(P_PID,(id_t)leader,&info,WEXITED|WNOWAIT));
    }
    long long start=now_ms();pid_t leaders[]={leader,leader,0,-1};
    if(polling) {
        int child_status;
        if(!exit_leader) {
            assert(tl_owned_process_poll(leader,&child_status)==0);
            assert(!kill(leader,SIGKILL));
        }
        int done=0;
        for(int i=0;i<100&&!done;i++) {
            done=tl_owned_process_poll(leader,&child_status);
            assert(done>=0);
            if(!done){struct timespec step={0,10000000};nanosleep(&step,NULL);}
        }
        assert(done==1);
    } else assert(!tl_owned_processes_shutdown(leaders,4));
    assert(now_ms()-start<1000);
    int status;assert(waitpid(leader,&status,WNOHANG)==-1&&errno==ECHILD);
    /* As a test subreaper we can collect the owned grandchild and prove exit,
     * rather than mistake its transient zombie for a live process. */
    pid_t result=0;
    for(int i=0;i<100&&!result;i++) {
        result=waitpid(descendant,&status,WNOHANG);
        if(!result){struct timespec step={0,10000000};nanosleep(&step,NULL);}
    }
    assert(result==descendant&&WIFSIGNALED(status)&&WTERMSIG(status)==SIGKILL);
    assert(!kill(independent,0));
}
int main(void) {
    assert(!prctl(PR_SET_CHILD_SUBREAPER,1));
    pid_t independent=fork();assert(independent>=0);
    if(!independent)asleep();
    /* This direct child shares the test parent's group; do not signal it. */
    assert(tl_owned_processes_shutdown(&independent,1)==-1);
    assert(!kill(independent,0));
    pid_t self=getpid();assert(tl_owned_processes_shutdown(&self,1)==-1);
    group_case(0,0,independent);group_case(1,0,independent);
    group_case(0,1,independent);group_case(1,1,independent);
    assert(!kill(independent,SIGKILL));int status;assert(waitpid(independent,&status,0)==independent);
    puts("owned-processes: shutdown and nonblocking completion passed; resistant descendants removed and independent child preserved");
    return 0;
}
