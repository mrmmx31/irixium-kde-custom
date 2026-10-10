/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "controller.h"
#include "preview_event.h"
#include <X11/cursorfont.h>
#include <X11/Xutil.h>
#include <X11/StringDefs.h>
#include <X11/Shell.h>
#include <X11/Xatom.h>
#include <json-c/json.h>
#include <openssl/evp.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <locale.h>
#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

typedef enum { JOB_PALETTE, JOB_SHELL_PALETTE, JOB_REFERENCE_PALETTE, JOB_SCHEMES, JOB_SNIPPET, JOB_PROBE, JOB_GENERATE, JOB_PREVIEW, JOB_COUPLED, JOB_EXPORT } JobKind;
typedef struct { pid_t pid; int fd; JobKind kind; char *text; size_t used, capacity;
                 time_t started, cancelled_at; TLFamily family; unsigned long revision; int cancelled, overflow; } Job;
typedef struct {
    TLModel model, applied; TLView *view; XtAppContext app; Widget shell;
    char root[TL_PATH_MAX], work[TL_PATH_MAX], project[TL_PATH_MAX];
    char working[TL_PATH_MAX], generated[TL_PATH_MAX], backend[TL_PATH_MAX];
    char scene[TL_PATH_MAX], events[TL_PATH_MAX], native[TL_PATH_MAX], theme[TL_PATH_MAX], scene_hash[65];
    Job jobs[16]; int picking, closing, preview_after_generate, coupled_after_generate, refresh_pending, want_separate;
    TLFamily pending_family; Cursor cursor; time_t pick_started, palette_due;
    unsigned short last_palette[6][3], last_shell_palette[6][3]; int have_palette, have_shell_palette, palette_failed;
    unsigned short last_reference_palette[6][3]; int have_reference_palette, reference_palette_failed;
    long long change_due; unsigned long revision, snippet_revision;
} Controller;
static Controller *live_controller;
static volatile sig_atomic_t interrupted;
static void caught_signal(int signum) { (void)signum; interrupted=1; }
static int display_closed(Display *display) {
    (void)display;
    if(live_controller)for(int i=0;i<16;i++)if(live_controller->jobs[i].pid>0)
        kill(-live_controller->jobs[i].pid,SIGTERM);
    _exit(0);
}
static void status(Controller *c, const char *s) { tl_view_status(c->view,s); }
static void update_view(Controller *c) {
    tl_view_update(c->view,&c->model);tl_view_scene(c->view,&c->applied);
}
static int path_join(char *out,size_t cap,const char *a,const char *b) {
    int n=snprintf(out,cap,"%s/%s",a,b); return n>=0&&(size_t)n<cap?0:-1;
}
static int private_directory(const char *path,char *err,size_t cap) {
    char part[TL_PATH_MAX]; struct stat st; size_t i,len=strlen(path);
    if(path[0]!='/'||len>=sizeof(part)||strstr(path,"/../")||strstr(path,"/./")) {
        snprintf(err,cap,"Pasta de trabalho deve ser absoluta, sem . ou ..");return -1;
    }
    strcpy(part,path);
    for(i=1;i<=len;i++) if(part[i]=='/'||i==len) {
        char saved=part[i];part[i]=0;
        if(lstat(part,&st)==0) { if(!S_ISDIR(st.st_mode)||S_ISLNK(st.st_mode)) {
            snprintf(err,cap,"Pasta atravessa um link ou arquivo: %.160s",part);return -1;
        }} else if(i==len&&errno==ENOENT) { if(mkdir(part,0700)) {
            snprintf(err,cap,"Não foi possível criar a pasta: %s",strerror(errno));return -1;
        }} else { snprintf(err,cap,"Pasta pai ausente: %.160s",part);return -1; }
        part[i]=saved;
    }
    if(stat(path,&st)||st.st_uid!=getuid()||(st.st_mode&0077)) {
        snprintf(err,cap,"Pasta de trabalho precisa pertencer ao usuário e ter modo 0700");return -1;
    }return 0;
}
static int save_working(Controller *c) {
    char err[TL_TEXT_MAX];
    if(tl_model_save(&c->model,c->working,err,sizeof(err))) { status(c,err);return -1; }
    ++c->revision;return 0;
}
static int digest_file(const char *path,char output[65]) {
    unsigned char buffer[4096],digest[EVP_MAX_MD_SIZE];unsigned int length=0;ssize_t size;
    int file=open(path,O_RDONLY|O_NOFOLLOW|O_NONBLOCK),result=-1;struct stat info;
    EVP_MD_CTX *ctx=EVP_MD_CTX_new();
    if(file<0||!ctx)goto done;
    if(fstat(file,&info)||!S_ISREG(info.st_mode)||info.st_size>2*1024*1024||info.st_uid!=getuid())goto done;
    if(EVP_DigestInit_ex(ctx,EVP_sha256(),NULL)!=1)goto done;
    while((size=read(file,buffer,sizeof(buffer)))>0)if(EVP_DigestUpdate(ctx,buffer,(size_t)size)!=1)goto done;
    if(size<0||EVP_DigestFinal_ex(ctx,digest,&length)!=1||length!=32)goto done;
    for(unsigned int i=0;i<length;i++)snprintf(output+i*2,3,"%02x",digest[i]);
    result=0;
done: if(file>=0)close(file);EVP_MD_CTX_free(ctx);return result;
}
static int save_scene(Controller *c) {
    char err[TL_TEXT_MAX];
    if(tl_model_save(&c->applied,c->scene,err,sizeof(err))||digest_file(c->scene,c->scene_hash)) {
        status(c,"Não foi possível salvar a cena privada.");return -1;
    }return 0;
}
static int active_kind(Controller *c,JobKind kind) {
    int i;for(i=0;i<16;i++)if(c->jobs[i].pid>0&&c->jobs[i].kind==kind)return 1;return 0;
}
static int start_job(Controller *c,JobKind kind,TLFamily family) {
    int i,p[2],fd;pid_t pid;const char *mode;
    char *argv[24],window[32],*output;int n=0;size_t capacity;
    for(i=0;i<16;i++)if(c->jobs[i].pid==0)break;
    if(i==16) {status(c,"Feche uma prévia antes de abrir outra.");return -1;}
    if(kind!=JOB_PREVIEW&&active_kind(c,kind))return -1;
    mode=(kind==JOB_PALETTE||kind==JOB_SHELL_PALETTE||kind==JOB_REFERENCE_PALETTE)?"--palette":kind==JOB_SCHEMES?"--schemes":kind==JOB_SNIPPET?"--snippet":kind==JOB_PROBE?"--probe":(kind==JOB_GENERATE||kind==JOB_EXPORT)?"--generate":"--preview";
    argv[n++]="/usr/bin/python3";argv[n++]="-B";
    if(kind==JOB_COUPLED||(kind==JOB_PREVIEW&&family==TL_GTK3)) {
        if(!c->theme[0])return -1;
        argv[n++]=c->native;argv[n++]="--project";argv[n++]=c->scene;
        argv[n++]="--root";argv[n++]=c->root;
        argv[n++]="--events-dir";argv[n++]=c->events;
        argv[n++]="--theme-directory";argv[n++]=c->theme;
        if(kind==JOB_COUPLED) {
            unsigned long xid=tl_view_canvas(c->view);if(!xid)return -1;
            snprintf(window,sizeof(window),"%lu",xid);argv[n++]="--embed-window";argv[n++]=window;
        }
        argv[n]=NULL;goto execute;
    }
    argv[n++]=c->backend;argv[n++]=(char*)mode;
    if(kind!=JOB_PROBE&&kind!=JOB_SCHEMES&&kind!=JOB_SHELL_PALETTE) {argv[n++]="--project";argv[n++]=(kind==JOB_GENERATE||kind==JOB_PALETTE||kind==JOB_REFERENCE_PALETTE)?c->scene:c->working;}
    if(kind==JOB_GENERATE||kind==JOB_EXPORT||kind==JOB_PREVIEW) {
        argv[n++]="--root";argv[n++]=c->root;argv[n++]="--output";argv[n++]=c->generated;
    }
    if(kind==JOB_PREVIEW||kind==JOB_SNIPPET) {argv[n++]="--family";argv[n++]=(char*)tl_family_ids[family];}
    if(kind==JOB_REFERENCE_PALETTE) {argv[n++]="--family";argv[n++]="motif";}
    argv[n]=NULL;
execute:
    capacity=(kind==JOB_GENERATE||kind==JOB_EXPORT)?2*1024*1024:262144;
    output=calloc(capacity+1,1);if(!output) {status(c,"Memória insuficiente para a resposta privada.");return -1;}
    if(pipe(p)) {free(output);status(c,strerror(errno));return -1;}
    pid=fork();
    if(pid==0) {
        (void)setpgid(0,0); close(p[0]);dup2(p[1],STDOUT_FILENO);dup2(p[1],STDERR_FILENO);close(p[1]);
        execv(argv[0],argv);perror("theme-lab backend");_exit(127);
    }
    close(p[1]);
    if(pid<0) {free(output);close(p[0]);status(c,strerror(errno));return -1;}
    (void)setpgid(pid,pid);fd=fcntl(p[0],F_GETFL,0);if(fd>=0)(void)fcntl(p[0],F_SETFL,fd|O_NONBLOCK);
    c->jobs[i]=(Job){.pid=pid,.fd=p[0],.kind=kind,.text=output,.capacity=capacity,.started=time(NULL),.family=family,.revision=c->revision};
    if(kind==JOB_SNIPPET)c->snippet_revision=c->revision;
    return 0;
}
static void stop_kind(Controller *c,JobKind kind) {
    for(int i=0;i<16;i++)if(c->jobs[i].pid>0&&c->jobs[i].kind==kind) {
        if(!c->jobs[i].cancelled) {c->jobs[i].cancelled=1;c->jobs[i].cancelled_at=time(NULL);kill(-c->jobs[i].pid,SIGTERM);}
    }
}
static void stop_detached_gtk3(Controller *c) {
    for(int i=0;i<16;i++)if(c->jobs[i].pid>0&&c->jobs[i].kind==JOB_PREVIEW&&c->jobs[i].family==TL_GTK3&&!c->jobs[i].cancelled) {
        c->jobs[i].cancelled=1;c->jobs[i].cancelled_at=time(NULL);kill(-c->jobs[i].pid,SIGTERM);
        c->preview_after_generate=c->want_separate;c->pending_family=TL_GTK3;
    }
}
static int generated_theme(Controller *c,struct json_object *root,const char **theme) {
    struct json_object *hash=NULL,*families=NULL,*gtk3=NULL,*path=NULL,*applied=NULL,*state=NULL;
    char resolved[TL_PATH_MAX],base[TL_PATH_MAX];
    if(!root||!json_object_object_get_ex(root,"status",&state)||!json_object_is_type(state,json_type_string)||strcmp(json_object_get_string(state),"ok")||
       !json_object_object_get_ex(root,"project_sha256",&hash)||!json_object_is_type(hash,json_type_string)||strcmp(json_object_get_string(hash),c->scene_hash)||
       !json_object_object_get_ex(root,"families",&families)||!json_object_object_get_ex(families,"gtk3",&gtk3)||
       !json_object_object_get_ex(gtk3,"recipe_applied",&applied)||!json_object_is_type(applied,json_type_boolean)||!json_object_get_boolean(applied)||
       !json_object_object_get_ex(gtk3,"theme_path",&path)||!json_object_is_type(path,json_type_string))return -1;
    *theme=json_object_get_string(path);
    if(strlen(*theme)>=TL_PATH_MAX||!realpath(*theme,resolved)||strcmp(resolved,*theme)||
       path_join(base,sizeof(base),c->generated,"revisions")||strncmp(resolved,base,strlen(base))||resolved[strlen(base)]!='/')return -1;
    return 0;
}
static void finish_job(Controller *c,Job *j,int exit_status) {
    struct json_object *root=NULL,*value=NULL,*row=NULL,*families=NULL,*entry=NULL;
    int i,k,good=WIFEXITED(exit_status)&&WEXITSTATUS(exit_status)==0&&!j->overflow;
    j->text[j->used]=0;
    if(good)root=json_tokener_parse(j->text);
    if((j->kind==JOB_PALETTE||j->kind==JOB_REFERENCE_PALETTE||j->kind==JOB_SNIPPET)&&j->revision!=c->revision)goto done;
    if((j->kind==JOB_PALETTE||j->kind==JOB_SHELL_PALETTE||j->kind==JOB_REFERENCE_PALETTE)&&good&&root&&json_object_object_get_ex(root,"rgb16",&value)&&
       json_object_is_type(value,json_type_array)&&json_object_array_length(value)==6) {
        unsigned short rgb[6][3];int valid=1;
        for(i=0;i<6;i++) { row=json_object_array_get_idx(value,(size_t)i);
            if(!json_object_is_type(row,json_type_array)||json_object_array_length(row)!=3) {valid=0;break;}
            for(k=0;k<3;k++) {struct json_object *component=json_object_array_get_idx(row,(size_t)k);
                int v=json_object_get_int(component);
                if(!json_object_is_type(component,json_type_int)||v<0||v>65535)valid=0;
                rgb[i][k]=(unsigned short)v;
            }
        }
        if(valid&&j->kind==JOB_PALETTE&&(!c->have_palette||memcmp(c->last_palette,rgb,sizeof(rgb)))) {
            tl_view_preview_palette(c->view,rgb);memcpy(c->last_palette,rgb,sizeof(rgb));c->have_palette=1;
        }
        if(valid&&j->kind==JOB_SHELL_PALETTE&&(!c->have_shell_palette||memcmp(c->last_shell_palette,rgb,sizeof(rgb)))) {
            tl_view_palette(c->view,rgb);memcpy(c->last_shell_palette,rgb,sizeof(rgb));c->have_shell_palette=1;
        }
        if(valid&&j->kind==JOB_REFERENCE_PALETTE&&(!c->have_reference_palette||memcmp(c->last_reference_palette,rgb,sizeof(rgb)))) {
            tl_view_reference_palette(c->view,rgb);memcpy(c->last_reference_palette,rgb,sizeof(rgb));c->have_reference_palette=1;
        }
        if(valid&&j->kind==JOB_REFERENCE_PALETTE)c->reference_palette_failed=0;
        c->palette_failed=0;
    } else if(j->kind==JOB_REFERENCE_PALETTE&&!c->reference_palette_failed) {
        status(c,"Paleta da referência Motif indisponível; mantida a paleta válida do toolkit.");c->reference_palette_failed=1;
    } else if(j->kind==JOB_PALETTE&&!c->palette_failed) {
        char msg[1024];snprintf(msg,sizeof(msg),"Paleta KDE indisponível; controles mantêm a paleta Motif atual. %.830s",j->text);
        status(c,msg);c->palette_failed=1;
    } else if(j->kind==JOB_SCHEMES&&good&&root&&json_object_object_get_ex(root,"schemes",&value)&&json_object_is_type(value,json_type_array)) {
        const char *ids[256];int count=0;
        for(i=0;i<(int)json_object_array_length(value)&&count<256;i++) {
            row=json_object_array_get_idx(value,(size_t)i);
            if(json_object_object_get_ex(row,"id",&entry)&&json_object_is_type(entry,json_type_string))ids[count++]=json_object_get_string(entry);
        }
        tl_view_schemes(c->view,ids,count);
    } else if(j->kind==JOB_SNIPPET) {
        if(good&&root&&json_object_object_get_ex(root,"source",&value)&&json_object_is_type(value,json_type_string))
            tl_view_code(c->view,json_object_get_string(value));
        else tl_view_code(c->view,"Trecho indisponível. A família ou o controle ainda requer um tradutor.");
    } else if(j->kind==JOB_PROBE&&good&&root&&json_object_object_get_ex(root,"families",&families)) {
        for(i=0;i<TL_FAMILY_COUNT;i++)if(json_object_object_get_ex(families,tl_family_ids[i],&entry)) {
            struct json_object *available=NULL,*version=NULL,*reason=NULL,*adapter=NULL;char description[1024];
            json_object_object_get_ex(entry,"available",&available);json_object_object_get_ex(entry,"version",&version);
            json_object_object_get_ex(entry,"reason",&reason);json_object_object_get_ex(entry,"adapter",&adapter);
            snprintf(description,sizeof(description),"%s%s%s. %s%s",
                json_object_get_boolean(available)?"Disponível":"Indisponível",version&&json_object_is_type(version,json_type_string)?" Versão ":"",
                version&&json_object_is_type(version,json_type_string)?json_object_get_string(version):"",
                adapter&&strcmp(json_object_get_string(adapter),"not_implemented")?"Receita GTK3 traduzida. ":i==TL_MOTIF?"Controles Motif nesta interface. ":"Tradutor ainda pendente. ",
                reason&&json_object_is_type(reason,json_type_string)?json_object_get_string(reason):"");
            tl_view_capability(c->view,(TLFamily)i,description);
        }
    } else if(j->kind==JOB_EXPORT) {
        if(good)status(c,"Proposta exportada na pasta privada; a cena aplicada foi preservada.");
        else {char msg[1024];snprintf(msg,sizeof(msg),"Falha ao exportar: %.920s",j->text);status(c,msg);}
    } else if(j->kind==JOB_GENERATE) {
        const char *theme=NULL;
        if(good&&!generated_theme(c,root,&theme)) {status(c,"Proposta privada gerada. GTK3 possui montagem interativa; demais tradutores seguem na fila.");
            if(!c->refresh_pending) {
                strcpy(c->theme,theme);
                if(c->coupled_after_generate&&c->model.selected==TL_GTK3)start_job(c,JOB_COUPLED,TL_GTK3);
                if(c->preview_after_generate)start_job(c,JOB_PREVIEW,c->pending_family);
            }
        } else { char msg[1024];snprintf(msg,sizeof(msg),"Falha ao gerar: %.940s",j->text);status(c,msg); }
        if(!c->refresh_pending)c->preview_after_generate=c->coupled_after_generate=0;
    } else if((j->kind==JOB_PREVIEW||j->kind==JOB_COUPLED)&&!good&&!j->cancelled) {
        char msg[1024];snprintf(msg,sizeof(msg),"Prévia indisponível: %.910s",j->text);status(c,msg);
    } else if(!good&&j->kind==JOB_PROBE)status(c,"Falha no inventário; veja a saída do backend.");
done:
    if(j->kind==JOB_PREVIEW&&!j->cancelled&&!c->preview_after_generate) {
        int another=0;
        for(int i=0;i<16;i++)if(&c->jobs[i]!=j&&c->jobs[i].pid>0&&c->jobs[i].kind==JOB_PREVIEW&&!c->jobs[i].cancelled)another=1;
        if(!another) {c->want_separate=0;tl_view_separate_preview(c->view,0);}
    }
    if(j->overflow)status(c,"Resposta do processo excedeu o limite; não foi aplicada à prévia.");
    if(root)json_object_put(root);
    close(j->fd);free(j->text);memset(j,0,sizeof(*j));
}
static void cancel_pick(Controller *c) {
    if(!c->picking)return;
    XUngrabPointer(XtDisplay(c->shell),CurrentTime);XUngrabKeyboard(XtDisplay(c->shell),CurrentTime);
    XFlush(XtDisplay(c->shell));c->picking=0;
}
static void picker(Widget w,XtPointer ctx,XEvent *event,Boolean *cont) {
    Controller *c=ctx;Display *d=XtDisplay(w);XImage *image;XColor color;
    if(!c->picking)return;
    if(event->type==KeyPress&&XLookupKeysym(&event->xkey,0)==XK_Escape) {cancel_pick(c);status(c,"Captura de cor cancelada.");*cont=False;return;}
    if(event->type!=ButtonPress)return;
    *cont=False;
    if(event->xbutton.button!=Button1) {cancel_pick(c);status(c,"Captura de cor cancelada.");return;}
    c->model.picked.x=event->xbutton.x_root;c->model.picked.y=event->xbutton.y_root;
    image=XGetImage(d,RootWindowOfScreen(XtScreen(w)),event->xbutton.x_root,event->xbutton.y_root,1,1,AllPlanes,ZPixmap);
    cancel_pick(c);
    if(!image) {status(c,"Não foi possível ler esse pixel.");return;}
    color.pixel=XGetPixel(image,0,0);XDestroyImage(image);
    if(!XQueryColor(d,DefaultColormapOfScreen(XtScreen(w)),&color)) {status(c,"Cor indisponível nesse visual.");return;}
    c->model.picked.rgb16[0]=color.red;c->model.picked.rgb16[1]=color.green;c->model.picked.rgb16[2]=color.blue;
    c->model.picked.rgb8[0]=(unsigned char)((color.red+128u)/257u);
    c->model.picked.rgb8[1]=(unsigned char)((color.green+128u)/257u);
    c->model.picked.rgb8[2]=(unsigned char)((color.blue+128u)/257u);
    c->model.picked.visual_id=XVisualIDFromVisual(DefaultVisualOfScreen(XtScreen(w)));
    c->model.picked.valid=1;strcpy(c->model.picked.purpose,"evidence_only");
    snprintf(c->model.picked.origin,sizeof(c->model.picked.origin),"X11 screen %s; pixel measured, not a final UI color",DisplayString(d));
    update_view(c);save_working(c);
    status(c,"Pixel medido. RGB é evidência; os controles continuam seguindo os papéis KDE.");
}
static void choose_load(void *context,const char *path) {
    Controller *c=context;TLModel candidate;char err[TL_TEXT_MAX];
    if(tl_model_load(&candidate,path,err,sizeof(err))) {status(c,err);return;}
    c->model=candidate;c->applied=candidate;update_view(c);save_working(c);save_scene(c);
    stop_kind(c,JOB_COUPLED);c->refresh_pending=c->model.selected==TL_GTK3;
    c->coupled_after_generate=c->refresh_pending;
    if(c->model.reference[0])tl_view_reference(c->view,c->model.reference,err,sizeof(err));
    c->palette_due=0;status(c,"Projeto importado. Aplicar altera somente a prévia.");
}
static void choose_reference(void *context,const char *path) {
    Controller *c=context;char err[TL_TEXT_MAX];
    if(strlen(path)>=sizeof(c->model.reference)) {status(c,"Caminho de referência muito longo.");return;}
    if(tl_view_reference(c->view,path,err,sizeof(err))) {status(c,err);return;}
    tl_view_show_reference_image(c->view);
    strcpy(c->model.reference,path);update_view(c);save_working(c);
    status(c,"Referência carregada em pixels nativos. Use a pipeta para medir.");
}
static void choose_save(void *context,const char *path) {
    Controller *c=context;char err[TL_TEXT_MAX];
    if(tl_model_save(&c->model,path,err,sizeof(err))) {status(c,err);return;}
    status(c,"Projeto salvo. Papéis de cor e medições mantidos separados.");
}
static int read_edits(Controller *c) {
    TLModel next=c->model;char err[TL_TEXT_MAX];
    if(tl_view_read(c->view,&next,err,sizeof(err))||tl_model_validate(&next,err,sizeof(err))) {status(c,err);return -1;}
    c->model=next;return save_working(c);
}
static long long milliseconds(void) {
    struct timespec stamp;clock_gettime(CLOCK_MONOTONIC,&stamp);
    return (long long)stamp.tv_sec*1000+stamp.tv_nsec/1000000;
}
static void dispatch(void *context,TLAction action,int argument) {
    Controller *c=context;char err[TL_TEXT_MAX];TLModel defaults;
    if(c->picking&&action!=TL_QUIT)cancel_pick(c);
    switch(action) {
    case TL_SELECT_FAMILY:
        if(argument<0||argument>=TL_FAMILY_COUNT||read_edits(c))return;
        stop_kind(c,JOB_COUPLED);stop_kind(c,JOB_PREVIEW);
        c->model.selected=(TLFamily)argument;c->applied=c->model;
        update_view(c);save_working(c);save_scene(c);c->palette_due=0;
        c->refresh_pending=c->model.selected==TL_GTK3;c->coupled_after_generate=c->refresh_pending;
        c->preview_after_generate=c->want_separate&&c->model.selected==TL_GTK3;c->pending_family=c->model.selected;
        if(c->want_separate&&c->model.selected!=TL_GTK3) {
            if(c->model.selected==TL_MOTIF) {c->want_separate=0;tl_view_separate_preview(c->view,0);}
            else start_job(c,JOB_PREVIEW,c->model.selected);
        }
        c->change_due=0;break;
    case TL_CHANGED: {
        int automatic=0,delay=600;tl_view_preview_settings(c->view,&automatic,&delay);
        c->change_due=automatic?milliseconds()+delay:0;
        break;
    }
    case TL_SELECT_CONTROL:
        if(argument<0||argument>=TL_CONTROL_COUNT||read_edits(c))return;
        c->model.recipes[c->model.selected].selected_control=argument;
        update_view(c);save_working(c);start_job(c,JOB_SNIPPET,c->model.selected);break;
    case TL_MOVE_CONTROL:
        if(argument<0||argument>=TL_CONTROL_COUNT||read_edits(c))return;
        c->applied.recipes[c->model.selected].selected_control=argument;
        memcpy(c->applied.recipes[c->model.selected].positions[argument],c->model.recipes[c->model.selected].positions[argument],sizeof(int)*2);
        /* View moves the native Motif widget while dragging; it never writes
         * the model. Avoid resetting the active input grab here. */
        break;
    case TL_APPLY:
        if(read_edits(c))return;
        c->applied=c->model;
        update_view(c);c->palette_due=0;c->change_due=0;
        start_job(c,JOB_SNIPPET,c->model.selected);
        if(c->model.selected==TL_GTK3) {c->refresh_pending=1;c->coupled_after_generate=1;
            status(c,"Atualizando a cena GTK3 privada com os parâmetros escolhidos.");
        }else {save_scene(c);status(c,c->model.selected==TL_MOTIF?
            "Montagem Motif atualizada.":
            "Receita guardada; o tradutor desta família está pendente. A prévia separada mostra o tema atual.");}break;
    case TL_SAVE: if(!read_edits(c))tl_view_choose_file(c->view,"Salvar projeto JSON",c->project,choose_save,c);break;
    case TL_LOAD: tl_view_choose_file(c->view,"Importar projeto JSON",c->project,choose_load,c);break;
    case TL_REFERENCE:
        if(read_edits(c))return;
        if(c->model.reference[0]&&!tl_view_reference(c->view,c->model.reference,err,sizeof(err))) {
            tl_view_show_reference_image(c->view);break;
        }
        tl_view_choose_file(c->view,"Abrir referência PNG",c->model.reference,choose_reference,c);break;
    case TL_PICK:
        if(read_edits(c))return;
        if(XGrabPointer(XtDisplay(c->shell),XtWindow(c->shell),False,ButtonPressMask,
                        GrabModeAsync,GrabModeAsync,None,c->cursor,CurrentTime)!=GrabSuccess) {status(c,"Ponteiro já está capturado por outra janela.");break;}
        (void)XGrabKeyboard(XtDisplay(c->shell),XtWindow(c->shell),False,GrabModeAsync,GrabModeAsync,CurrentTime);
        c->picking=1;c->pick_started=time(NULL);status(c,"Clique num pixel desta tela X11; Esc ou botão direito cancela. Limite: 30 segundos.");break;
    case TL_PREVIEW:
        if(read_edits(c))return;
        if(c->model.selected==TL_MOTIF) {update_view(c);tl_view_separate_preview(c->view,0);status(c,"Motif está nos dois quadros centrais; prévia separada desta família ainda pendente.");break;}
        c->want_separate=1;tl_view_separate_preview(c->view,1);
        for(int i=0;i<16;i++)if(c->jobs[i].pid>0&&c->jobs[i].kind==JOB_PREVIEW&&c->jobs[i].family==c->model.selected) {status(c,"Esta família já tem uma prévia aberta; feche-a para gerar outra.");return;}
        if(c->model.selected==TL_GTK3) {c->pending_family=c->model.selected;c->preview_after_generate=1;
            c->refresh_pending=1;c->coupled_after_generate=1;
        }else start_job(c,JOB_PREVIEW,c->model.selected);
        status(c,"Abrindo controle nativo; famílias sem tradutor mostram o tema atual e avisam esse limite.");break;
    case TL_SEPARATE_TOGGLE:
        if(argument)dispatch(c,TL_PREVIEW,0);
        else {
            c->want_separate=0;c->preview_after_generate=0;
            stop_kind(c,JOB_PREVIEW);tl_view_separate_preview(c->view,0);
            status(c,"Prévia separada fechada; montagem acoplada preservada.");
        }
        break;
    case TL_EXPORT:
        if(active_kind(c,JOB_GENERATE)||active_kind(c,JOB_EXPORT)) {status(c,"Aguarde a geração privada em curso.");break;}
        if(!read_edits(c)) {start_job(c,JOB_EXPORT,c->model.selected);status(c,"Gerando proposta privada; o tema instalado permanece intacto.");}break;
    case TL_RESET:
        tl_model_init(&defaults);c->model.recipes[c->model.selected]=defaults.recipes[c->model.selected];
        c->model.recipes[c->model.selected].geometry=c->model.native_measured;
        c->applied=c->model;update_view(c);save_working(c);save_scene(c);c->palette_due=0;
        c->refresh_pending=c->model.selected==TL_GTK3;c->coupled_after_generate=c->refresh_pending;
        status(c,"Receita desta família restaurada à base medida.");break;
    case TL_QUIT: c->closing=1;cancel_pick(c);XtAppSetExitFlag(c->app);break;
    default: snprintf(err,sizeof(err),"Ação desconhecida: %d",action);status(c,err);
    }
}
static void preview_events(Controller *c) {
    DIR *folder=opendir(c->events);struct dirent *item;int processed=0;
    if(!folder)return;
    while((item=readdir(folder))&&processed<32) {
        size_t length=strlen(item->d_name);char buffer[16385];struct stat info;ssize_t size;TLPreviewEvent event;
        if(strncmp(item->d_name,"event-",6)||length<12||strcmp(item->d_name+length-5,".json"))continue;
        int file=openat(dirfd(folder),item->d_name,O_RDONLY|O_NOFOLLOW|O_NONBLOCK);++processed;
        if(file<0)continue;
        if(!fstat(file,&info)&&S_ISREG(info.st_mode)&&info.st_uid==getuid()&&!(info.st_mode&0077)&&info.st_size<=16384&&
           (size=read(file,buffer,16384))>0&&size==info.st_size&&
           !tl_preview_event(buffer,(size_t)size,c->scene_hash,&event)&&c->model.selected==TL_GTK3) {
            if(event.action!=TL_EVENT_NATIVE&&!read_edits(c)) {
                TLRecipe *recipe=&c->model.recipes[TL_GTK3];recipe->selected_control=event.control;
                if(event.action==TL_EVENT_MOVE) {
                    recipe->positions[event.control][0]=event.x;recipe->positions[event.control][1]=event.y;
                    c->applied.recipes[TL_GTK3].selected_control=event.control;
                    c->applied.recipes[TL_GTK3].positions[event.control][0]=event.x;
                    c->applied.recipes[TL_GTK3].positions[event.control][1]=event.y;
                }
                update_view(c);save_working(c);
                if(event.action==TL_EVENT_MOVE) {c->refresh_pending=1;c->coupled_after_generate=1;}
            }
        }
        close(file);(void)unlinkat(dirfd(folder),item->d_name,0);
    }
    closedir(folder);
}
static void tick(XtPointer context,XtIntervalId *id) {
    Controller *c=context;time_t now=time(NULL);int i;(void)id;
    if(interrupted) {dispatch(c,TL_QUIT,0);return;}
    for(i=0;i<16;i++)if(c->jobs[i].pid>0) {
        Job *j=&c->jobs[i];char block[4096];ssize_t n;int result;
        while((n=read(j->fd,block,sizeof(block)))>0) {size_t room=j->capacity-j->used, take=(size_t)n<room?(size_t)n:room;
            if(take<(size_t)n)j->overflow=1;
            memcpy(j->text+j->used,block,take);j->used+=take;}
        if(j->cancelled&&now-j->cancelled_at>=2)kill(-j->pid,SIGKILL);
        if(j->kind!=JOB_PREVIEW&&j->kind!=JOB_COUPLED&&now-j->started>30) {kill(-j->pid,SIGKILL);}
        if(waitpid(j->pid,&result,WNOHANG)==j->pid)finish_job(c,j,result);
    }
    preview_events(c);
    if(c->refresh_pending&&!active_kind(c,JOB_GENERATE)&&!active_kind(c,JOB_EXPORT)) {
        stop_detached_gtk3(c);
        if(active_kind(c,JOB_COUPLED))stop_kind(c,JOB_COUPLED);
        else if(c->model.selected==TL_GTK3&&!save_scene(c)) {
            c->refresh_pending=0;start_job(c,JOB_GENERATE,TL_GTK3);
        }else if(c->model.selected!=TL_GTK3)c->refresh_pending=0;
    }
    if(c->picking&&now-c->pick_started>30) {cancel_pick(c);status(c,"Captura de cor expirada; ponteiro liberado.");}
    if(c->change_due&&milliseconds()>=c->change_due&&!active_kind(c,JOB_GENERATE)) {
        c->change_due=0;dispatch(c,TL_APPLY,0);
    }
    if(now>=c->palette_due&&!active_kind(c,JOB_GENERATE)) {
        start_job(c,JOB_PALETTE,c->model.selected);start_job(c,JOB_SHELL_PALETTE,c->model.selected);start_job(c,JOB_REFERENCE_PALETTE,TL_MOTIF);c->palette_due=now+4;
    }
    if(c->snippet_revision!=c->revision&&!active_kind(c,JOB_SNIPPET)) {
        if(!start_job(c,JOB_SNIPPET,c->model.selected))c->snippet_revision=c->revision;
    }
    if(!c->closing)XtAppAddTimeOut(c->app,100,tick,c);
}
int tl_controller_run(int argc,char **argv) {
    Controller c={0};char err[TL_TEXT_MAX],contract[TL_PATH_MAX],temporary[]="/tmp/theme-lab-XXXXXX";
    const char *initial=NULL,*reference=NULL,*family=NULL;int i;char *xtargv[]={argv[0],NULL};int xtargc=1;
    setlocale(LC_ALL,"");umask(0077);tl_model_init(&c.model);
    for(i=1;i<argc;i++) {
        if(!strcmp(argv[i],"--help")) {puts("theme-lab --root REPOSITORY --work-dir PRIVATE_DIR [--project JSON] [--reference PNG] [--family gtk3|motif|...]\nInterface Motif C99/MVC. Apply and export affect private proposals only.");return 0;}
        if(i+1>=argc) {fprintf(stderr,"Argumento incompleto: %s\n",argv[i]);return 2;}
        if(!strcmp(argv[i],"--root")) {if(strlen(argv[++i])>=sizeof(c.root))return 2;strcpy(c.root,argv[i]);}
        else if(!strcmp(argv[i],"--work-dir")) {if(strlen(argv[++i])>=sizeof(c.work))return 2;strcpy(c.work,argv[i]);}
        else if(!strcmp(argv[i],"--project")) initial=argv[++i];
        else if(!strcmp(argv[i],"--reference"))reference=argv[++i];
        else if(!strcmp(argv[i],"--family"))family=argv[++i];
        else {fprintf(stderr,"Argumento desconhecido: %s\n",argv[i]);return 2;}
    }
    if(!c.root[0]) {fprintf(stderr,"Informe --root com a raiz dos tradutores.\n");return 2;}
    if(!c.work[0]) {char *made=mkdtemp(temporary);if(!made) {perror("mkdtemp");return 1;}strcpy(c.work,made);}
    if(private_directory(c.work,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}
    if(path_join(c.project,sizeof(c.project),c.work,"project.json")||path_join(c.working,sizeof(c.working),c.work,"working.json")||
       path_join(c.generated,sizeof(c.generated),c.work,"generated")||path_join(c.backend,sizeof(c.backend),c.root,"tools/theme-lab/backend.py")||
       path_join(c.scene,sizeof(c.scene),c.work,"scene.json")||path_join(c.events,sizeof(c.events),c.work,"preview-events")||
       path_join(c.native,sizeof(c.native),c.root,"tools/theme-lab/preview_gtk.py")||
       path_join(contract,sizeof(contract),c.root,"tools/domainos_scrollbar_rules.json")) {fputs("Caminho muito longo.\n",stderr);return 2;}
    if(initial) {if(tl_model_load(&c.model,initial,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}}
    else if(tl_model_contract(&c.model,contract,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}
    if(family) {
        int found=0;
        for(i=0;i<TL_FAMILY_COUNT;i++)if(!strcmp(family,tl_family_ids[i])) {c.model.selected=(TLFamily)i;found=1;break;}
        if(!found) {fprintf(stderr,"Família desconhecida: %s\n",family);return 2;}
    }
    if(reference) {if(strlen(reference)>=sizeof(c.model.reference))return 2;strcpy(c.model.reference,reference);}
    c.applied=c.model;
    if(tl_model_save(&c.model,c.working,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}
    if(tl_model_save(&c.applied,c.scene,err,sizeof(err))||digest_file(c.scene,c.scene_hash)) {fprintf(stderr,"Não foi possível salvar a cena privada.\n");return 1;}
    if(private_directory(c.events,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}
    XtSetLanguageProc(NULL,NULL,NULL);
    c.shell=XtVaAppInitialize(&c.app,"ThemeLab",NULL,0,&xtargc,xtargv,NULL,XtNtitle,"Laboratório de temas — Motif MVC / três painéis",XtNwidth,1320,XtNheight,850,NULL);
    c.view=tl_view_create(c.shell,dispatch,&c);if(!c.view)return 1;
    live_controller=&c;XSetIOErrorHandler(display_closed);
    update_view(&c);XtRealizeWidget(c.shell);
    { unsigned long pid=(unsigned long)getpid();
      XChangeProperty(XtDisplay(c.shell),XtWindow(c.shell),XInternAtom(XtDisplay(c.shell),"_NET_WM_PID",False),
                      XA_CARDINAL,32,PropModeReplace,(unsigned char*)&pid,1); }
    if(c.model.reference[0]&&tl_view_reference(c.view,c.model.reference,err,sizeof(err)))status(&c,err);
    c.cursor=XCreateFontCursor(XtDisplay(c.shell),XC_crosshair);
    XtAddEventHandler(c.shell,ButtonPressMask|KeyPressMask,False,picker,&c);
    signal(SIGTERM,caught_signal);signal(SIGINT,caught_signal);signal(SIGPIPE,SIG_IGN);
    start_job(&c,JOB_PROBE,TL_MOTIF);start_job(&c,JOB_SCHEMES,TL_MOTIF);start_job(&c,JOB_SNIPPET,c.model.selected);
    start_job(&c,JOB_PALETTE,c.model.selected);start_job(&c,JOB_SHELL_PALETTE,c.model.selected);start_job(&c,JOB_REFERENCE_PALETTE,TL_MOTIF);c.palette_due=time(NULL)+4;
    c.refresh_pending=c.model.selected==TL_GTK3;c.coupled_after_generate=c.refresh_pending;
    XtAppAddTimeOut(c.app,100,tick,&c);XtAppMainLoop(c.app);
    cancel_pick(&c);
    for(i=0;i<16;i++)if(c.jobs[i].pid>0) {kill(-c.jobs[i].pid,SIGTERM);close(c.jobs[i].fd);free(c.jobs[i].text);}
    tl_view_destroy(c.view);XFreeCursor(XtDisplay(c.shell),c.cursor);XtDestroyWidget(c.shell);XtDestroyApplicationContext(c.app);return 0;
}
