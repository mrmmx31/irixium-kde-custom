/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "owned_processes.h"
#include <errno.h>
#include <signal.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static long long monotonic_ms(void) {
    struct timespec t;
    if(clock_gettime(CLOCK_MONOTONIC,&t))return -1;
    return (long long)t.tv_sec*1000+t.tv_nsec/1000000;
}

int tl_owned_process_poll(pid_t leader,int *status) {
    siginfo_t info={0};int result;
    if(leader<=1||!status){errno=EINVAL;return -1;}
    do {result=waitid(P_PID,(id_t)leader,&info,WEXITED|WNOHANG|WNOWAIT);}
    while(result<0&&errno==EINTR);
    if(result<0)return -1;
    if(!info.si_pid)return 0;
    if(getpgid(leader)==leader&&kill(-leader,SIGKILL)&&errno!=ESRCH)return -1;
    pid_t reaped;
    do {reaped=waitpid(leader,status,WNOHANG);}while(reaped<0&&errno==EINTR);
    return reaped==leader?1:reaped<0?-1:0;
}

int tl_owned_processes_shutdown(const pid_t *leaders,size_t count) {
    /* The controller owns at most 16 jobs. Retain waitable leaders until all
     * group signals have been sent, so their numeric IDs cannot be reused. */
    pid_t owned[16];size_t n=0;int failures=0;
    if(count>16)return -1;
    for(size_t i=0;i<count;i++) {
        siginfo_t info={0};pid_t p=leaders[i];
        if(p<=1)continue;
        int duplicate=0;
        for(size_t j=0;j<n;j++)if(owned[j]==p)duplicate=1;
        if(duplicate)continue;
        if(waitid(P_PID,(id_t)p,&info,WEXITED|WNOHANG|WNOWAIT)||getpgid(p)!=p) {
            failures++;continue;
        }
        owned[n++]=p;
        if(kill(-p,SIGTERM)&&errno!=ESRCH)failures++;
    }
    if(n) {
        struct timespec grace={0,200000000};
        while(nanosleep(&grace,&grace)&&errno==EINTR){}
    }
    for(size_t i=0;i<n;i++)if(kill(-owned[i],SIGKILL)&&errno!=ESRCH)failures++;
    long long start=monotonic_ms();
    for(int attempts=0;attempts<20;attempts++) {
        size_t remaining=0;
        for(size_t i=0;i<n;i++)if(owned[i]>0) {
            int status;pid_t r=waitpid(owned[i],&status,WNOHANG);
            if(r==owned[i]||(r<0&&errno==ECHILD))owned[i]=0;
            else remaining++;
        }
        if(!remaining)break;
        if(start<0||monotonic_ms()-start>=200)break;
        struct timespec step={0,10000000};(void)nanosleep(&step,NULL);
    }
    for(size_t i=0;i<n;i++)if(owned[i]>0)failures++;
    return failures?-1:0;
}
