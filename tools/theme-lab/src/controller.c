/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "controller.h"
#include "manual_paint_view.h"
#include "preview_event.h"
#include "generated_preview.h"
#include "control_dimensions.h"
#include "gtk2_r584_catalog.h"
#include "project_session.h"
#include "owned_processes.h"
#include <X11/cursorfont.h>
#include <X11/Xutil.h>
#include <X11/StringDefs.h>
#include <X11/Shell.h>
#include <X11/Xatom.h>
#include <json-c/json.h>
#include <openssl/evp.h>
#include <openssl/rand.h>
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

typedef enum { JOB_PALETTE, JOB_SHELL_PALETTE, JOB_REFERENCE_PALETTE, JOB_SCHEMES, JOB_SNIPPET, JOB_PROBE, JOB_GENERATE, JOB_PREVIEW, JOB_COUPLED, JOB_EXPORT, JOB_IMPORT, JOB_INSPECT_FILES, JOB_RECONSTRUCT, JOB_PAINT_SAMPLE, JOB_PAINT_REFERENCE_SAMPLE } JobKind;
typedef struct { pid_t pid; int fd; JobKind kind; char *text; size_t used, capacity;
                 long long started_ms, cancelled_ms; TLFamily family; unsigned long revision; int cancelled, overflow, timed_out;
                 int sample_control, sample_state; TLManualPaintSampleRequest sample_request;
                 char sample_path[TL_PATH_MAX]; char instance[33]; } Job;
typedef struct {
    TLModel model, applied; TLProjectSession *history; TLView *view; XtAppContext app; Widget shell;
    char root[TL_PATH_MAX], work[TL_PATH_MAX], project[TL_PATH_MAX];
    char history_path[TL_PATH_MAX], working[TL_PATH_MAX], generated[TL_PATH_MAX], backend[TL_PATH_MAX];
    char manual_paint_path[TL_PATH_MAX];
    char import_base[TL_PATH_MAX], import_delta[TL_PATH_MAX];
    char reconstruct_files[TL_PATH_MAX], reconstruct_base[TL_PATH_MAX];
    char scene[TL_PATH_MAX], events[TL_PATH_MAX], native[TL_PATH_MAX], native2[TL_PATH_MAX], native4[TL_PATH_MAX], host4[TL_PATH_MAX], theme[TL_PATH_MAX], themes[TL_FAMILY_COUNT][TL_PATH_MAX], scene_hash[65], editor_path[TL_PATH_MAX];
    Job jobs[16]; int picking, closing, preview_after_generate, coupled_after_generate, refresh_pending, want_separate, working_dirty;
    TLManualPaintSampleRequest paint_sample_request;
    TLManualPaintSampleRequest paint_reference_request;
    TLFamily pending_family; Cursor cursor; time_t pick_started, palette_due;
    /* Ephemeral native state, independently owned by each preview origin. */
    int toggle_known[2], toggle_active[2];
    int check_known[2], check_active[2];
    int radio_known[2], radio_member[2];
    unsigned short last_palette[6][3], last_shell_palette[6][3], last_header_palette[6][3];
    int have_palette, have_shell_palette, have_header_palette, palette_failed;
    unsigned short last_reference_palette[6][3]; int have_reference_palette, reference_palette_failed;
    long long change_due, persist_due; unsigned long revision, snippet_revision;
} Controller;
static int read_edits(Controller *c);
static long long milliseconds(void);
static void choose_load(void *context,const char *path);
static void choose_reconstruction_base(void *context,const char *path);
static Controller *live_controller;
static volatile sig_atomic_t interrupted;
static void caught_signal(int signum) { (void)signum; interrupted=1; }
static int preview_error_log(Controller *c,const Job *job,char *path,size_t capacity) {
    char temporary[TL_PATH_MAX];int fd=-1,result=-1,length;size_t offset=0;
    const char *origin=job->kind==JOB_COUPLED?"coupled":"separate";
    length=snprintf(path,capacity,"%s/preview-%s-%s-error.log",c->work,
                    tl_family_ids[job->family],origin);
    if(length<0||(size_t)length>=capacity)return -1;
    length=snprintf(temporary,sizeof(temporary),"%s/.preview-error-%ld-%d.tmp",c->work,
                    (long)getpid(),(int)job->pid);
    if(length<0||(size_t)length>=sizeof(temporary))return -1;
    fd=open(temporary,O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);if(fd<0)return -1;
    while(offset<job->used) {
        ssize_t written=write(fd,job->text+offset,job->used-offset);
        if(written<0&&errno==EINTR)continue;
        if(written<=0)goto done;
        offset+=(size_t)written;
    }
    if(fsync(fd)||close(fd)) {fd=-1;goto done;}
    fd=-1;if(rename(temporary,path))goto done;
    result=0;
done:
    if(fd>=0)close(fd);
    if(result)unlink(temporary);
    return result;
}
static void shutdown_jobs(Controller *c) {
    pid_t leaders[16];
    for(int i=0;i<16;i++)leaders[i]=c->jobs[i].pid;
    if(tl_owned_processes_shutdown(leaders,16))
        fprintf(stderr,"theme-lab: encerramento de filhos não confirmado\n");
}
static int display_closed(Display *display) {
    (void)display;
    if(live_controller)shutdown_jobs(live_controller);
    _exit(0);
}
static void status(Controller *c, const char *s) { tl_view_status(c->view,s); }
static void update_view(Controller *c) {
    tl_view_update(c->view,&c->model);tl_view_scene(c->view,&c->applied);
    tl_view_history_state(c->view,tl_project_session_can_step(c->history,-1),
                          tl_project_session_can_step(c->history,1),tl_project_session_has_point(c->history));
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
/* The history file is authoritative. working.json is a derived backend input. */
static int commit_project(Controller *c,const TLModel *candidate) {
    char err[TL_TEXT_MAX];
    json_object *old=tl_model_encode(&c->model,err,sizeof(err)),*next=tl_model_encode(candidate,err,sizeof(err));
    if(!old||!next) {json_object_put(old);json_object_put(next);status(c,err);return -1;}
    int same=json_object_equal(old,next);json_object_put(old);json_object_put(next);
    if(same&&!c->working_dirty)return 0;
    int result=tl_project_session_change(c->history,TL_HISTORY_PUSH,candidate,
                                       TL_MOTIF,TL_SCROLL_ARROW,err,sizeof(err));
    if(result<0) {status(c,err);return -1;}
    c->model=*candidate;++c->revision;
    tl_view_history_state(c->view,tl_project_session_can_step(c->history,-1),
                          tl_project_session_can_step(c->history,1),tl_project_session_has_point(c->history));
    if(result>0)status(c,err);
    c->working_dirty=1;
    if(tl_model_save(&c->model,c->working,err,sizeof(err))) {
        status(c,"Histórico preservado; falha ao gerar working.json. Aplicação da prévia interrompida.");return -1;
    }
    c->working_dirty=0;
    return 0;
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
    char err[TL_TEXT_MAX], previous_hash[65];
    memcpy(previous_hash,c->scene_hash,sizeof(previous_hash));
    if(access(c->scene,F_OK)==0) {
        TLModel saved;
        if(tl_model_load(&saved,c->scene,err,sizeof(err))) {status(c,err);return -1;}
        json_object *old=tl_model_encode(&saved,err,sizeof(err));
        json_object *next=tl_model_encode(&c->applied,err,sizeof(err));
        if(!old||!next) {json_object_put(old);json_object_put(next);status(c,err);return -1;}
        int same=json_object_equal(old,next);json_object_put(old);json_object_put(next);
        if(same) {
            if(digest_file(c->scene,c->scene_hash)) {status(c,"Não foi possível conferir a cena privada.");return -1;}
            if(strcmp(previous_hash,c->scene_hash)) {
                tl_view_metrics_reset(c->view);
                c->theme[0]=0;
                memset(c->themes,0,sizeof(c->themes));
            }
            return 0;
        }
    }
    if(tl_model_save(&c->applied,c->scene,err,sizeof(err))||digest_file(c->scene,c->scene_hash)) {
        status(c,"Não foi possível salvar a cena privada.");return -1;
    }
    if(strcmp(previous_hash,c->scene_hash)) {
        tl_view_metrics_reset(c->view);
        c->theme[0]=0;
        memset(c->themes,0,sizeof(c->themes));
    }
    return 0;
}
static int active_kind(Controller *c,JobKind kind) {
    int i;for(i=0;i<16;i++)if(c->jobs[i].pid>0&&!c->jobs[i].cancelled&&c->jobs[i].kind==kind)return 1;return 0;
}
static int scene_family(TLFamily family) { return family==TL_GTK2 || family==TL_GTK3 || family==TL_GTK4; }
static int backend_coupled_family(TLFamily family) {
    return family==TL_QT5 || family==TL_QT6 || family==TL_KVANTUM || family==TL_PLASMA;
}
static int coupled_family(TLFamily family) {
    return scene_family(family) || backend_coupled_family(family);
}
static int private_preview_session(void) {
    const char *mode=getenv("IRIX_DOMAINOS_PRIVATE_NAMESPACE");
    return mode!=NULL&&!strcmp(mode,"bwrap");
}

enum { GTK4_RENDER_NONE, GTK4_RENDER_BUTTONS, GTK4_RENDER_SCROLLBARS };

static int recipe_control_visible(const TLRecipe *recipe,int control,int category) {
    return recipe!=NULL && control>=0 && control<TL_CONTROL_COUNT &&
           category>=0 && category<TL_CATEGORY_COUNT &&
           (recipe->visible_controls&(1<<control))!=0 &&
           (recipe->visible_categories&(1<<category))!=0;
}

/* Keep this dispatch identical to gtk4_route.renderer(). A mixed catalog is
 * filtered to one real GTK4 renderer without changing the saved masks. */
static int gtk4_renderer(const TLRecipe *recipe) {
    static const int categories[TL_CONTROL_COUNT]={0,0,0,0,1,1,1,1,2,2,2,2,2,2,3,4};
    int selected=recipe?recipe->selected_control:-1;
    if((selected==10||selected==11)&&recipe_control_visible(recipe,selected,2))
        return GTK4_RENDER_SCROLLBARS;
    if(selected>=0&&selected<=2&&recipe_control_visible(recipe,selected,0))
        return GTK4_RENDER_BUTTONS;
    /* A visible selected control owns the canvas.  Do not silently replace an
     * untranslated choice with the first translated neighbor. */
    if(selected>=0&&selected<TL_CONTROL_COUNT&&
       recipe_control_visible(recipe,selected,categories[selected]))
        return GTK4_RENDER_NONE;
    for(int control=0;control<=2;control++)
        if(recipe_control_visible(recipe,control,0))return GTK4_RENDER_BUTTONS;
    for(int control=10;control<=11;control++)
        if(recipe_control_visible(recipe,control,2))return GTK4_RENDER_SCROLLBARS;
    return GTK4_RENDER_NONE;
}

static int preview_origin_active(Controller *c,int separate) {
    JobKind kind=separate?JOB_PREVIEW:JOB_COUPLED;
    for(int i=0;i<16;i++)if(c->jobs[i].pid>0&&!c->jobs[i].cancelled&&
        c->jobs[i].kind==kind&&c->jobs[i].family==c->applied.selected)return 1;
    return 0;
}

static int preview_event_active(Controller *c,const TLPreviewEvent *event) {
    if(!event->instance[0])return 0;
    for(int i=0;i<16;i++) {
        Job *j=&c->jobs[i];
        if(j->pid<=0||j->cancelled||j->family!=c->applied.selected||
            (j->kind!=JOB_PREVIEW&&j->kind!=JOB_COUPLED)||strcmp(j->instance,event->instance))continue;
        int separate=j->kind==JOB_PREVIEW;
        if(event->action==TL_EVENT_METRICS&&event->metrics.separate!=separate)return 0;
        if(event->toggle_state_known&&event->toggle_separate!=separate)return 0;
        if(event->radio_state_known&&event->radio_separate!=separate)return 0;
        return 1;
    }
    return 0;
}
static int paint_sample_job(JobKind kind) {
    return kind==JOB_PAINT_SAMPLE||kind==JOB_PAINT_REFERENCE_SAMPLE;
}
static const TLManualPaintSampleRequest *paint_request_for(
    const Controller *c,JobKind kind) {
    return kind==JOB_PAINT_REFERENCE_SAMPLE?
        &c->paint_reference_request:&c->paint_sample_request;
}
static const char *paint_theme_for(const Controller *c,TLFamily family) {
    if(family>=0&&family<TL_FAMILY_COUNT&&c->themes[family][0])
        return c->themes[family];
    if(family==c->applied.selected&&c->theme[0])
        return c->theme;
    return NULL;
}
static int start_job(Controller *c,JobKind kind,TLFamily family) {
    int i,p[2],fd;pid_t pid;const char *mode;
    char *argv[64],window[32],host_pid[32],toggle[2],check[2],radio[2],instance[33]={0},*output;
    char sample_length[32],sample_thickness[32],sample_value[32],sample_page[32];
    int n=0;size_t capacity;const char *sample_theme=NULL;
    if(kind==JOB_PREVIEW&&scene_family(family)&&!private_preview_session()) {
        c->want_separate=0;
        status(c,"Escolha de prévia separada salva; nesta sessão normal permanece apenas a prévia acoplada. Use o lançador privado para abrir a janela separada.");
        return -1;
    }
    for(i=0;i<16;i++)if(c->jobs[i].pid==0)break;
    if(i==16) {status(c,"Feche uma prévia antes de abrir outra.");return -1;}
    if(kind!=JOB_PREVIEW&&active_kind(c,kind))return -1;
    mode=(kind==JOB_PALETTE||kind==JOB_SHELL_PALETTE||kind==JOB_REFERENCE_PALETTE)?"--palette":kind==JOB_SCHEMES?"--schemes":kind==JOB_SNIPPET?"--snippet":kind==JOB_PROBE?"--probe":kind==JOB_EXPORT?"--export":kind==JOB_IMPORT?"--import-delta":kind==JOB_INSPECT_FILES?"--inspect-files":kind==JOB_RECONSTRUCT?"--reconstruct-files":kind==JOB_GENERATE?"--generate":"--preview";
    argv[n++]="/usr/bin/python3";argv[n++]="-B";
    int sample_control=-1,sample_state=0; char sample_path[TL_PATH_MAX]={0};
    if(paint_sample_job(kind)) {
        const TLManualPaintSampleRequest *request=paint_request_for(c,kind);
        sample_theme=paint_theme_for(c,family);
        if((family!=TL_GTK2&&family!=TL_GTK3&&family!=TL_GTK4)||!sample_theme||
           (family==TL_GTK2?!c->native2[0]:family==TL_GTK4?!c->native4[0]:!c->native[0])) {
            status(c,"Amostra nativa indisponível: esta família ainda não possui captura de controle.");return -1;
        }
        if(family==TL_GTK4&&request->control!=0&&request->control!=1&&
           request->control!=2&&request->control!=10&&request->control!=11) {
            status(c,"Amostra GTK4 indisponível: este controle ainda não tem tradutor nativo.");return -1;
        }
        if(family==TL_GTK3&&(request->length_px||request->thickness_px||
           request->value!=25||request->page_size!=25||
           request->part!=TL_PAINT_SAMPLE_WHOLE||
           request->direction!=TL_PAINT_DIRECTION_AUTO)) {
            status(c,"Ensaio geométrico GTK3 indisponível: a captura atual aceita somente a amostra inteira natural.");return -1;
        }
    }
    if(kind==JOB_COUPLED&&backend_coupled_family(family)) {
        unsigned long xid=tl_view_canvas(c->view);
        if(!xid)return -1;
        snprintf(window,sizeof(window),"%lu",xid);
        snprintf(host_pid,sizeof(host_pid),"%ld",(long)getpid());
        argv[n++]=c->backend;argv[n++]="--preview";
        argv[n++]="--project";argv[n++]=c->scene;
        argv[n++]="--root";argv[n++]=c->root;
        argv[n++]="--output";argv[n++]=c->generated;
        argv[n++]="--family";argv[n++]=(char*)tl_family_ids[family];
        argv[n++]="--embed-window";argv[n++]=window;
        argv[n++]="--host-pid";argv[n++]=host_pid;
        argv[n++]="--host-bridge";argv[n++]=c->host4;
        argv[n++]="--host-session-root";argv[n++]=c->work;
        argv[n]=NULL;goto execute;
    }
    if(kind==JOB_COUPLED||(kind==JOB_PREVIEW&&scene_family(family))) {
        if(!c->theme[0])return -1;
        unsigned char nonce[16];
        if(RAND_bytes(nonce,sizeof(nonce))!=1) {status(c,"Não foi possível identificar a prévia.");return -1;}
        for(int byte=0;byte<16;byte++)snprintf(instance+byte*2,3,"%02x",nonce[byte]);
        argv[n++]=family==TL_GTK2?c->native2:family==TL_GTK4?c->native4:c->native;argv[n++]="--project";argv[n++]=c->scene;
        argv[n++]="--root";argv[n++]=c->root;
        argv[n++]="--events-dir";argv[n++]=c->events;
        argv[n++]="--preview-instance";argv[n++]=instance;
        argv[n++]=family==TL_GTK2?"--rc":family==TL_GTK4?"--snapshot":"--theme-directory";argv[n++]=c->theme;
        int origin=kind==JOB_PREVIEW;
        const TLRecipe *recipe=&c->applied.recipes[family];
        int gtk4_mode=family==TL_GTK4?gtk4_renderer(recipe):GTK4_RENDER_NONE;
        if(family==TL_GTK4&&gtk4_mode==GTK4_RENDER_NONE) {
            status(c,"Prévia GTK4 indisponível: o controle selecionado não possui tradutor DomainOS (cobertura atual 5/16) ou nenhum controle traduzido está visível.");
            return -1;
        }
        int gtk4_scrollbar=gtk4_mode==GTK4_RENDER_SCROLLBARS;
        int gtk4_toggle=gtk4_mode==GTK4_RENDER_BUTTONS&&
                        recipe_control_visible(recipe,1,0);
        int gtk4_check=gtk4_mode==GTK4_RENDER_BUTTONS&&
                       recipe_control_visible(recipe,2,0);
        if(gtk4_toggle)argv[n++]="--private-toggle-session";
        if(gtk4_check)argv[n++]="--private-check-session";
        if(gtk4_scrollbar)argv[n++]="--private-scrollbar-session";
        if((family==TL_GTK2||gtk4_toggle) && c->toggle_known[origin]) {
            toggle[0]=c->toggle_active[origin]?'1':'0';toggle[1]=0;
            argv[n++]="--runtime-toggle-active";argv[n++]=toggle;
        }
        if(family==TL_GTK2 && c->radio_known[origin]) {
            radio[0]=c->radio_member[origin]?'1':'0';radio[1]=0;
            argv[n++]="--runtime-radio-member";argv[n++]=radio;
        }
        if((family==TL_GTK2||gtk4_check) && c->check_known[origin]) {
            check[0]=c->check_active[origin]?'1':'0';check[1]=0;
            argv[n++]="--runtime-check-active";argv[n++]=check;
        }
        if(kind==JOB_COUPLED) {
            unsigned long xid=tl_view_canvas(c->view);if(!xid)return -1;
            snprintf(window,sizeof(window),"%lu",xid);argv[n++]="--embed-window";argv[n++]=window;
            if(family==TL_GTK2||family==TL_GTK3||family==TL_GTK4) {
                argv[n++]="--host-session-root";argv[n++]=c->work;
            }
            if(family==TL_GTK4) {
                snprintf(host_pid,sizeof(host_pid),"%ld",(long)getpid());
                argv[n++]="--host-pid";argv[n++]=host_pid;
                argv[n++]="--host-bridge";argv[n++]=c->host4;
            }
        }
        argv[n]=NULL;goto execute;
    }
    if(paint_sample_job(kind)) {
        unsigned char nonce[16];
        if(RAND_bytes(nonce,sizeof(nonce))!=1) {status(c,"Não foi possível identificar a amostra nativa.");return -1;}
        for(int byte=0;byte<16;byte++)snprintf(instance+byte*2,3,"%02x",nonce[byte]);
        if(snprintf(sample_path,sizeof(sample_path),"%s/paint-sample-%s.png",c->events,instance)>=
           (int)sizeof(sample_path)) {status(c,"O caminho privado da amostra excede o limite.");return -1;}
        /* The request is private probe state, never a mutation of scene.json. */
        const TLManualPaintSampleRequest *request=paint_request_for(c,kind);
        static const char *const parts[] = {
            "arrow", "arrow_button", "trough", "thumb", "fitting"};
        static const char *const directions[] = {
            "auto", "left", "right", "up", "down"};
        sample_control=request->control; sample_state=request->state;
        argv[n++]=family==TL_GTK2?c->native2:family==TL_GTK4?c->native4:c->native;
        argv[n++]="--project";argv[n++]=c->scene;
        argv[n++]="--root";argv[n++]=c->root;argv[n++]="--events-dir";argv[n++]=c->events;
        argv[n++]="--preview-instance";argv[n++]=instance;
        if(family==TL_GTK4) {
            argv[n++]="--snapshot";argv[n++]=(char*)sample_theme;
            if(sample_control==1)argv[n++]="--private-toggle-session";
            else if(sample_control==2)argv[n++]="--private-check-session";
            else if(sample_control==10||sample_control==11)argv[n++]="--private-scrollbar-session";
            if(sample_control==1&&c->toggle_known[0]) {
                toggle[0]=c->toggle_active[0]?'1':'0';toggle[1]=0;
                argv[n++]="--runtime-toggle-active";argv[n++]=toggle;
            }
            if(sample_control==2&&c->check_known[0]) {
                check[0]=c->check_active[0]?'1':'0';check[1]=0;
                argv[n++]="--runtime-check-active";argv[n++]=check;
            }
        } else if(family==TL_GTK2) {
            argv[n++]="--rc";argv[n++]=(char*)sample_theme;
            /* GTK2 manual samples use Gtk.OffscreenWindow, not XEmbed or a
             * mapped top-level. Let the helper validate this narrow capture
             * against the private session directory even in the normal user
             * launch, where the gallery bwrap guard is intentionally absent. */
            argv[n++]="--host-session-root";argv[n++]=c->work;
        }
        else {argv[n++]="--theme-directory";argv[n++]=(char*)sample_theme;argv[n++]="--family";argv[n++]="gtk3";
            argv[n++]="--host-session-root";argv[n++]=c->work;}
        argv[n++]="--capture-control";
        snprintf(window,sizeof(window),"%d",sample_control);argv[n++]=window;
        argv[n++]="--capture-state";snprintf(host_pid,sizeof(host_pid),"%d",sample_state);argv[n++]=host_pid;
        if(family==TL_GTK2||family==TL_GTK4) {
            snprintf(sample_length,sizeof(sample_length),"%d",request->length_px);
            snprintf(sample_thickness,sizeof(sample_thickness),"%d",request->thickness_px);
            snprintf(sample_value,sizeof(sample_value),"%d",request->value);
            snprintf(sample_page,sizeof(sample_page),"%d",request->page_size);
            argv[n++]="--capture-length";argv[n++]=sample_length;
            argv[n++]="--capture-thickness";argv[n++]=sample_thickness;
            argv[n++]="--capture-value";argv[n++]=sample_value;
            argv[n++]="--capture-page-size";argv[n++]=sample_page;
            argv[n++]="--capture-part";
            argv[n++]=request->part==TL_PAINT_SAMPLE_WHOLE?"whole":
                      (char*)parts[request->part];
            argv[n++]="--capture-direction";
            argv[n++]=(char*)directions[request->direction];
        }
        argv[n++]="--capture-output";argv[n++]=sample_path;argv[n]=NULL;
        goto execute;
    }
    argv[n++]=c->backend;argv[n++]=(char*)mode;
    if(kind!=JOB_PROBE&&kind!=JOB_SCHEMES&&kind!=JOB_SHELL_PALETTE&&kind!=JOB_INSPECT_FILES&&kind!=JOB_RECONSTRUCT) {argv[n++]="--project";argv[n++]=kind==JOB_IMPORT?c->import_base:(kind==JOB_GENERATE||kind==JOB_PALETTE||kind==JOB_REFERENCE_PALETTE)?c->scene:c->working;}
    if(kind==JOB_GENERATE||kind==JOB_EXPORT||kind==JOB_PREVIEW||kind==JOB_IMPORT||kind==JOB_RECONSTRUCT) {
        argv[n++]="--root";argv[n++]=c->root;argv[n++]="--output";argv[n++]=c->generated;
    }
    if(kind==JOB_EXPORT) {argv[n++]="--applied-project";argv[n++]=c->scene;}
    if(kind==JOB_IMPORT) {argv[n++]="--delta";argv[n++]=c->import_delta;}
    if(kind==JOB_INSPECT_FILES||kind==JOB_RECONSTRUCT) {
        argv[n++]="--file-delta";argv[n++]=c->reconstruct_files;
        if(kind==JOB_RECONSTRUCT&&c->reconstruct_base[0]) {argv[n++]="--base-directory";argv[n++]=c->reconstruct_base;}
    }
    if(kind==JOB_PREVIEW||kind==JOB_SNIPPET) {argv[n++]="--family";argv[n++]=(char*)tl_family_ids[family];}
    if(kind==JOB_SNIPPET) {
        int selected=tl_view_part_state(c->view);
        const char *states[]={"normal","pressed","disabled","backdrop","hover","focus"};
        if(selected>=0&&selected<6) {argv[n++]="--recipe-state";argv[n++]=(char*)states[selected];}
    }
    if(kind==JOB_REFERENCE_PALETTE) {argv[n++]="--family";argv[n++]="motif";}
    argv[n]=NULL;
execute:
    capacity=(kind==JOB_GENERATE||kind==JOB_EXPORT||kind==JOB_RECONSTRUCT)?2*1024*1024:262144;
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
    c->jobs[i]=(Job){.pid=pid,.fd=p[0],.kind=kind,.text=output,.capacity=capacity,.started_ms=milliseconds(),.family=family,.revision=c->revision};
    memcpy(c->jobs[i].instance,instance,sizeof(instance));
    if(paint_sample_job(kind)) {
        c->jobs[i].sample_control=sample_control;c->jobs[i].sample_state=sample_state;
        c->jobs[i].sample_request=*paint_request_for(c,kind);
        snprintf(c->jobs[i].sample_path,sizeof(c->jobs[i].sample_path),"%s",sample_path);
    }
    if(kind==JOB_SNIPPET)c->snippet_revision=c->revision;
    return 0;
}
static void stop_kind(Controller *c,JobKind kind) {
    for(int i=0;i<16;i++)if(c->jobs[i].pid>0&&c->jobs[i].kind==kind) {
        if(!c->jobs[i].cancelled) {c->jobs[i].cancelled=1;c->jobs[i].cancelled_ms=milliseconds();kill(-c->jobs[i].pid,SIGTERM);}
    }
}
/* The saved preference is separate from a child process being alive. Opening
 * never applies pending edits: both origins use the existing applied scene. */
static void sync_separate_preview(Controller *c) {
    tl_view_separate_preview(c->view,c->model.separate_preview);
    c->want_separate=c->model.separate_preview;
    if(!c->want_separate) {
        c->preview_after_generate=0;stop_kind(c,JOB_PREVIEW);
        tl_view_metrics_clear_origin(c->view,1);return;
    }
    if(c->applied.selected==TL_MOTIF) {
        c->want_separate=0;
        status(c,"Escolha de prévia separada salva; janela Motif separada ainda indisponível.");return;
    }
    if(scene_family(c->applied.selected)&&!private_preview_session()) {
        c->want_separate=0;
        status(c,"Escolha de prévia separada salva; nesta sessão normal permanece apenas a prévia acoplada. Use o lançador privado para abrir a janela separada.");return;
    }
    for(int i=0;i<16;i++)if(c->jobs[i].pid>0&&!c->jobs[i].cancelled&&
        c->jobs[i].kind==JOB_PREVIEW&&c->jobs[i].family==c->applied.selected)return;
    if(scene_family(c->applied.selected)) {
        c->pending_family=c->applied.selected;c->preview_after_generate=1;
        c->refresh_pending=1;c->coupled_after_generate=1;
    }else start_job(c,JOB_PREVIEW,c->applied.selected);
}
static void stop_detached_native(Controller *c) {
    for(int i=0;i<16;i++)if(c->jobs[i].pid>0&&c->jobs[i].kind==JOB_PREVIEW&&scene_family(c->jobs[i].family)&&!c->jobs[i].cancelled) {
        c->jobs[i].cancelled=1;c->jobs[i].cancelled_ms=milliseconds();kill(-c->jobs[i].pid,SIGTERM);
        c->preview_after_generate=c->want_separate;c->pending_family=c->applied.selected;
    }
}
static struct json_object *job_json(const char *output) {
    const char *line;
    struct json_object *root;
    if(!output)return NULL;
    root=json_tokener_parse(output);
    if(root)return root;
    /* Native helpers may emit a toolkit/accessibility warning to stderr before
     * their single JSON result.  stdout and stderr intentionally share the
     * bounded job pipe, so retry only at a new line that starts with a JSON
     * object.  Warning-only output remains invalid. */
    line=output;
    while((line=strstr(line,"\n{"))!=NULL) {
        root=json_tokener_parse(line+1);
        if(root)return root;
        line++;
    }
    return NULL;
}
static void finish_job(Controller *c,Job *j,int exit_status) {
    struct json_object *root=NULL,*value=NULL,*row=NULL,*families=NULL,*entry=NULL;
    int i,k,good=WIFEXITED(exit_status)&&WEXITSTATUS(exit_status)==0&&!j->overflow;
    j->text[j->used]=0;
    /* Snippet failures also return a structured explanation. Parse it for
       display; successful source still requires a successful process. */
    if(good||j->kind==JOB_SNIPPET)root=job_json(j->text);
    if(paint_sample_job(j->kind)) {
        struct stat sample_info;
        const char *state=NULL;
        const TLManualPaintSampleRequest *current=
            paint_request_for(c,j->kind);
        int delivered=-1;
        if(root&&json_object_object_get_ex(root,"status",&value)&&json_object_is_type(value,json_type_string))
            state=json_object_get_string(value);
        if(!j->cancelled&&good&&j->revision==c->revision&&
           !memcmp(&j->sample_request,current,sizeof(j->sample_request))&&
           state&&!strcmp(state,"captured")&&
           !lstat(j->sample_path,&sample_info)&&S_ISREG(sample_info.st_mode)&&
           sample_info.st_uid==getuid()&&(sample_info.st_mode&0777)==0600) {
            delivered=j->kind==JOB_PAINT_REFERENCE_SAMPLE?
                tl_view_manual_paint_reference_png(
                    c->view,j->sample_path,j->family,j->sample_control,
                    j->sample_state):
                tl_view_manual_paint_native_png(
                    c->view,j->sample_path,j->family,j->sample_control,
                    j->sample_state);
        }
        if(!delivered) {
            char message[192];
            snprintf(message,sizeof(message),
                     "%s %s atualizada; arte raster e receita permanecem "
                     "independentes.",
                     j->kind==JOB_PAINT_REFERENCE_SAMPLE?"Referência":"Amostra nativa",
                     j->family==TL_GTK2?"GTK2":j->family==TL_GTK4?"GTK4":"GTK3");
            status(c,message);
        }
        else if(!j->cancelled) {
            const char *reason=NULL;
            if(root&&json_object_object_get_ex(root,"reason",&value)&&
               json_object_is_type(value,json_type_string))reason=json_object_get_string(value);
            if(reason) {
                const char *family=j->family==TL_GTK2?"GTK2":j->family==TL_GTK4?"GTK4":"GTK3";
                char message[512];snprintf(message,sizeof(message),"%s %s indisponível: %.350s",
                    j->kind==JOB_PAINT_REFERENCE_SAMPLE?"Referência":"Amostra",
                    family,reason);status(c,message);
            } else {
                char message[256];
                snprintf(message,sizeof(message),
                         "Não foi possível capturar %s %s; arte e receita "
                         "foram preservadas.",
                         j->kind==JOB_PAINT_REFERENCE_SAMPLE?"a referência":"a amostra",
                         j->family==TL_GTK2?"GTK2":j->family==TL_GTK4?"GTK4":"GTK3");
                status(c,message);
            }
        }
        if(j->sample_path[0])unlink(j->sample_path);
        goto done;
    }
    if((j->kind==JOB_PALETTE||j->kind==JOB_REFERENCE_PALETTE||j->kind==JOB_SNIPPET)&&j->revision!=c->revision)goto done;
    if((j->kind==JOB_PALETTE||j->kind==JOB_SHELL_PALETTE||j->kind==JOB_REFERENCE_PALETTE)&&good&&root&&json_object_object_get_ex(root,"rgb16",&value)&&
       json_object_is_type(value,json_type_array)&&json_object_array_length(value)==6) {
        unsigned short rgb[6][3],header_rgb[6][3];int valid=1,header_valid=0;
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
        if(valid&&j->kind==JOB_SHELL_PALETTE&&
           json_object_object_get_ex(root,"header_rgb16",&value)&&
           json_object_is_type(value,json_type_array)&&
           json_object_array_length(value)==6) {
            header_valid=1;
            for(i=0;i<6;i++) {
                row=json_object_array_get_idx(value,(size_t)i);
                if(!json_object_is_type(row,json_type_array)||
                   json_object_array_length(row)!=3) {header_valid=0;break;}
                for(k=0;k<3;k++) {
                    struct json_object *component=json_object_array_get_idx(row,(size_t)k);
                    int v=json_object_get_int(component);
                    if(!json_object_is_type(component,json_type_int)||v<0||v>65535)
                        header_valid=0;
                    header_rgb[i][k]=(unsigned short)v;
                }
            }
        }
        if(valid&&j->kind==JOB_SHELL_PALETTE&&header_valid&&
           (!c->have_shell_palette||!c->have_header_palette||
            memcmp(c->last_shell_palette,rgb,sizeof(rgb))||
            memcmp(c->last_header_palette,header_rgb,sizeof(header_rgb)))) {
            tl_view_shell_palettes(c->view,rgb,header_rgb);
            memcpy(c->last_shell_palette,rgb,sizeof(rgb));
            memcpy(c->last_header_palette,header_rgb,sizeof(header_rgb));
            c->have_shell_palette=1;
            c->have_header_palette=1;
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
        else if(root&&json_object_object_get_ex(root,"reason",&value)&&json_object_is_type(value,json_type_string))
            tl_view_code(c->view,json_object_get_string(value));
        else tl_view_code(c->view,"Trecho indisponível. A família ou o controle ainda requer um tradutor.");
    } else if(j->kind==JOB_PROBE&&good&&root&&json_object_object_get_ex(root,"families",&families)) {
        for(i=0;i<TL_FAMILY_COUNT;i++)if(json_object_object_get_ex(families,tl_family_ids[i],&entry)) {
            struct json_object *available=NULL,*version=NULL,*reason=NULL,*adapter=NULL,*pressure=NULL;char description[1024];
            json_object_object_get_ex(entry,"available",&available);json_object_object_get_ex(entry,"version",&version);
            json_object_object_get_ex(entry,"reason",&reason);json_object_object_get_ex(entry,"adapter",&adapter);
            json_object_object_get_ex(entry,"pressure_reason",&pressure);
            const char *adapter_name=adapter&&json_object_is_type(adapter,json_type_string)?
                json_object_get_string(adapter):"not_implemented";
            const char *scope=i==TL_MOTIF?"Controles Motif reais nesta interface; a VM SR10.4 continua sendo a referência histórica. ":
                i==TL_GTK2?"GTK2: receita parcial em controles nativos; pressão depende do controle e runtime. ":
                i==TL_GTK4?"GTK4: receita parcial para controles declarados pelo recibo nativo. ":
                strcmp(adapter_name,"not_implemented")?"Adaptador nativo privado disponível para esta família. ":
                "Sem adaptador nativo utilizável nesta instalação. ";
            snprintf(description,sizeof(description),"%s%s%s. %s%s%s%s",
                json_object_get_boolean(available)?"Disponível":"Indisponível",version&&json_object_is_type(version,json_type_string)?" Versão ":"",
                version&&json_object_is_type(version,json_type_string)?json_object_get_string(version):"",
                scope,
                reason&&json_object_is_type(reason,json_type_string)?json_object_get_string(reason):"",
                pressure&&json_object_is_type(pressure,json_type_string)?" ":"",
                pressure&&json_object_is_type(pressure,json_type_string)?json_object_get_string(pressure):"");
            tl_view_capability(c->view,(TLFamily)i,description);
        }
    } else if(j->kind==JOB_EXPORT) {
        if(good&&root&&json_object_object_get_ex(root,"review_text",&value)&&json_object_is_type(value,json_type_string)) {
            tl_view_export_review(c->view,json_object_get_string(value));
            status(c,"Comparação da exportação aberta; caminho do pacote no relatório. Nenhum tema instalado.");
        }
        else {char msg[1024];snprintf(msg,sizeof(msg),"Falha ao exportar: %.920s",j->text);status(c,msg);}
    } else if(j->kind==JOB_INSPECT_FILES) {
        if(good&&root&&json_object_object_get_ex(root,"requires_base",&value)&&json_object_is_type(value,json_type_boolean)) {
            if(json_object_get_boolean(value))tl_view_choose_directory(c->view,"Reconstruir — pasta dos arquivos certificados da base",c->work,choose_reconstruction_base,c);
            else choose_reconstruction_base(c,"");
        } else {char msg[1024];snprintf(msg,sizeof(msg),"Falha ao inspecionar arquivos: %.900s",j->text);status(c,msg);}
    } else if(j->kind==JOB_RECONSTRUCT) {
        if(good&&root&&json_object_object_get_ex(root,"review_text",&value)&&json_object_is_type(value,json_type_string)) {
            tl_view_export_review(c->view,json_object_get_string(value));
            status(c,"Reconstrução privada concluída. Projeto e cena intactos; nenhum tema instalado.");
        } else {char msg[1024];snprintf(msg,sizeof(msg),"Falha ao reconstruir arquivos: %.900s",j->text);status(c,msg);}
    } else if(j->kind==JOB_IMPORT) {
        if(good&&root&&json_object_object_get_ex(root,"project_path",&value)&&json_object_is_type(value,json_type_string)) {
            char path[TL_PATH_MAX],prefix[TL_PATH_MAX];
            const char *source=json_object_get_string(value);
            if(!realpath(source,path)||path_join(prefix,sizeof(prefix),c->generated,"imports/")||
               strncmp(path,prefix,strlen(prefix))) {
                status(c,"Importação retornou um caminho fora das revisões privadas.");
            } else if(read_edits(c)||j->revision!=c->revision) {
                char msg[TL_PATH_MAX+128];snprintf(msg,sizeof(msg),"Projeto editado durante a importação; ajustes mantidos. Proposta reconstruída: %s",path);status(c,msg);
            } else choose_load(c,path);
        } else {char msg[1024];snprintf(msg,sizeof(msg),"Falha ao importar delta: %.900s",j->text);status(c,msg);}
    } else if(j->kind==JOB_GENERATE) {
        const char *theme=NULL;
        if(good) {
            const TLFamily paint_families[]={TL_GTK2,TL_GTK3,TL_GTK4};
            for(size_t p=0;p<sizeof(paint_families)/sizeof(paint_families[0]);++p) {
                const char *candidate=NULL;TLFamily family=paint_families[p];
                c->themes[family][0]=0;
                if(!tl_generated_preview(root,family,c->scene_hash,c->generated,
                                         &candidate)&&candidate)
                    snprintf(c->themes[family],sizeof(c->themes[family]),"%s",
                             candidate);
            }
            if(j->family>=0&&j->family<TL_FAMILY_COUNT&&c->themes[j->family][0])
                theme=c->themes[j->family];
        }
        if(good&&theme) {status(c,j->family==TL_GTK2?"Prévia GTK2 usa somente os controles traduzidos; o escopo da receita permanece parcial.":j->family==TL_GTK4?"Botão GTK4 gerado para prévia nativa; outros controles pendentes.":"Proposta privada gerada. GTK3 possui montagem interativa; demais tradutores seguem na fila.");
            if(!c->refresh_pending) {
                strcpy(c->theme,theme);
                tl_view_manual_paint_refresh_sample(c->view);
                if(c->coupled_after_generate&&scene_family(j->family))start_job(c,JOB_COUPLED,j->family);
                if(c->preview_after_generate)start_job(c,JOB_PREVIEW,c->pending_family);
            }
        } else { char msg[1024];snprintf(msg,sizeof(msg),"Falha ao gerar: %.940s",j->text);status(c,msg); }
        if(!c->refresh_pending)c->preview_after_generate=c->coupled_after_generate=0;
    } else if((j->kind==JOB_PREVIEW||j->kind==JOB_COUPLED)&&!good&&!j->cancelled) {
        char msg[1024],log_path[TL_PATH_MAX];
        if(!preview_error_log(c,j,log_path,sizeof(log_path)))
            snprintf(msg,sizeof(msg),"Prévia %s indisponível; erro completo salvo em %.760s. %.120s",
                     j->kind==JOB_COUPLED?"acoplada":"separada",log_path,j->text);
        else snprintf(msg,sizeof(msg),"Prévia indisponível: %.910s",j->text);
        status(c,msg);
    } else if(!good&&j->kind==JOB_PROBE)status(c,"Falha no inventário; veja a saída do backend.");
done:
    if(j->kind==JOB_COUPLED) {
        int another=0;
        for(int n=0;n<16;n++)if(&c->jobs[n]!=j&&c->jobs[n].pid>0&&
            c->jobs[n].kind==JOB_COUPLED&&!c->jobs[n].cancelled)another=1;
        if(!another)tl_view_metrics_clear_origin(c->view,0);
    }
    if(j->kind==JOB_PREVIEW&&!j->cancelled&&!c->preview_after_generate) {
        int another=0;
        for(int i=0;i<16;i++)if(&c->jobs[i]!=j&&c->jobs[i].pid>0&&c->jobs[i].kind==JOB_PREVIEW&&!c->jobs[i].cancelled)another=1;
        if(!another) {c->want_separate=0;tl_view_separate_preview(c->view,c->model.separate_preview);
            tl_view_metrics_clear_origin(c->view,1);}
    }
    if(j->overflow)status(c,"Resposta do processo excedeu o limite; não foi aplicada à prévia.");
    if(j->timed_out)status(c,"Tempo limite excedido (30 s). Editor e dados mantidos; tente novamente a operação.");
    if(root)json_object_put(root);
    close(j->fd);free(j->text);memset(j,0,sizeof(*j));
}
static void cancel_pick(Controller *c) {
    if(!c->picking)return;
    XUngrabPointer(XtDisplay(c->shell),CurrentTime);XUngrabKeyboard(XtDisplay(c->shell),CurrentTime);
    XFlush(XtDisplay(c->shell));c->picking=0;
}
static void picker(Widget w,XtPointer ctx,XEvent *event,Boolean *cont) {
    Controller *c=ctx;Display *d=XtDisplay(w);XImage *image;XColor color;TLModel next=c->model;
    if(!c->picking)return;
    if(event->type==KeyPress&&XLookupKeysym(&event->xkey,0)==XK_Escape) {cancel_pick(c);status(c,"Captura de cor cancelada.");*cont=False;return;}
    if(event->type!=ButtonPress)return;
    *cont=False;
    if(event->xbutton.button!=Button1) {cancel_pick(c);status(c,"Captura de cor cancelada.");return;}
    next.picked.x=event->xbutton.x_root;next.picked.y=event->xbutton.y_root;
    image=XGetImage(d,RootWindowOfScreen(XtScreen(w)),event->xbutton.x_root,event->xbutton.y_root,1,1,AllPlanes,ZPixmap);
    cancel_pick(c);
    if(!image) {status(c,"Não foi possível ler esse pixel.");return;}
    color.pixel=XGetPixel(image,0,0);XDestroyImage(image);
    if(!XQueryColor(d,DefaultColormapOfScreen(XtScreen(w)),&color)) {status(c,"Cor indisponível nesse visual.");return;}
    next.picked.rgb16[0]=color.red;next.picked.rgb16[1]=color.green;next.picked.rgb16[2]=color.blue;
    next.picked.rgb8[0]=(unsigned char)((color.red+128u)/257u);
    next.picked.rgb8[1]=(unsigned char)((color.green+128u)/257u);
    next.picked.rgb8[2]=(unsigned char)((color.blue+128u)/257u);
    next.picked.visual_id=XVisualIDFromVisual(DefaultVisualOfScreen(XtScreen(w)));
    next.picked.valid=1;strcpy(next.picked.purpose,"evidence_only");
    snprintf(next.picked.origin,sizeof(next.picked.origin),"X11 screen %s; pixel measured, not a final UI color",DisplayString(d));
    if(commit_project(c,&next))return;
    update_view(c);
    status(c,"Pixel medido. RGB é evidência; os controles continuam seguindo os papéis KDE.");
}
static int pieces_pending(const TLModel *model) {
    for(int i=0;i<TL_FAMILY_COUNT;i++) {
        const TLScrollbarParts *parts=&model->recipes[i].scrollbar_parts;
        for(int control=0;control<TL_CONTROL_COUNT;control++)
            if(i!=TL_MOTIF && i!=TL_GTK3 && i!=TL_GTK2 && model->recipes[i].length_anchor[control])return 1;
        if(i != TL_GTK3 && tl_scroll_parts_any(parts))return 1;
    }
    return 0;
}
static void choose_load(void *context,const char *path) {
    Controller *c=context;TLModel candidate;char err[TL_TEXT_MAX];
    if(read_edits(c))return;
    if(tl_model_load(&candidate,path,err,sizeof(err))) {status(c,err);return;}
    if(commit_project(c,&candidate))return;
    memset(c->toggle_known,0,sizeof(c->toggle_known));
    memset(c->toggle_active,0,sizeof(c->toggle_active));
    memset(c->check_known,0,sizeof(c->check_known));
    memset(c->check_active,0,sizeof(c->check_active));
    memset(c->radio_known,0,sizeof(c->radio_known));
    memset(c->radio_member,0,sizeof(c->radio_member));
    stop_kind(c,JOB_GENERATE);
    c->refresh_pending=0;c->coupled_after_generate=0;c->preview_after_generate=0;
    c->change_due=0;update_view(c);sync_separate_preview(c);
    status(c,pieces_pending(&candidate)?
        "Projeto importado como proposta, incluindo receitas pendentes. Cena anterior preservada; use Aplicar para atualizar a prévia suportada.":
        "Projeto importado como proposta. Cena anterior preservada; use Aplicar para atualizar a prévia.");
}
static void choose_import_delta(void *context,const char *path) {
    Controller *c=context;
    if(strlen(path)>=sizeof(c->import_delta)) {status(c,"Caminho do delta muito longo.");return;}
    if(active_kind(c,JOB_IMPORT)||read_edits(c))return;
    strcpy(c->import_delta,path);
    if(!start_job(c,JOB_IMPORT,c->model.selected))status(c,"Conferindo base e delta; a cena permanece intacta.");
}
static void choose_import_base(void *context,const char *path) {
    Controller *c=context;TLModel base;char error[TL_TEXT_MAX];
    if(strlen(path)>=sizeof(c->import_base)) {status(c,"Caminho da base muito longo.");return;}
    if(tl_model_load(&base,path,error,sizeof(error))) {status(c,error);return;}
    strcpy(c->import_base,path);
    tl_view_choose_file(c->view,"Importar delta — 2/2: selecione DELTA.json",path,choose_import_delta,c);
}
static void choose_reconstruction_base(void *context,const char *path) {
    Controller *c=context;
    if(strlen(path)>=sizeof(c->reconstruct_base)) {status(c,"Caminho da base muito longo.");return;}
    strcpy(c->reconstruct_base,path);
    if(!start_job(c,JOB_RECONSTRUCT,c->model.selected))status(c,"Validando arquivos e base para reconstrução privada.");
}
static void choose_reconstruction_files(void *context,const char *path) {
    Controller *c=context;
    if(strlen(path)>=sizeof(c->reconstruct_files)) {status(c,"Caminho do recibo muito longo.");return;}
    strcpy(c->reconstruct_files,path);c->reconstruct_base[0]=0;
    if(!start_job(c,JOB_INSPECT_FILES,c->model.selected))status(c,"Inspecionando necessidade de base; projeto e cena intactos.");
}
static void choose_reference(void *context,const char *path) {
    Controller *c=context;char err[TL_TEXT_MAX];
    if(strlen(path)>=sizeof(c->model.reference)) {status(c,"Caminho de referência muito longo.");return;}
    if(tl_view_reference(c->view,path,err,sizeof(err))) {status(c,err);return;}
    tl_view_show_reference_image(c->view);
    TLModel next=c->model;strcpy(next.reference,path);
    if(commit_project(c,&next))return;
    update_view(c);
    status(c,"Referência carregada em pixels nativos. Use a pipeta para medir.");
}
static void choose_save(void *context,const char *path) {
    Controller *c=context;char err[TL_TEXT_MAX];
    if(tl_model_save(&c->model,path,err,sizeof(err))) {status(c,err);return;}
    status(c,"Projeto salvo. Papéis de cor e medições mantidos separados.");
}
static int read_edits(Controller *c) {
    TLModel next=c->model;char err[TL_TEXT_MAX];
    c->persist_due=0;
    if(tl_view_editor_checkpoint(c->view,err,sizeof(err))) {status(c,err);return -1;}
    if(tl_view_read(c->view,&next,err,sizeof(err))||tl_model_validate(&next,err,sizeof(err))) {status(c,err);return -1;}
    return commit_project(c,&next);
}
static long long milliseconds(void) {
    struct timespec stamp;clock_gettime(CLOCK_MONOTONIC,&stamp);
    return (long long)stamp.tv_sec*1000+stamp.tv_nsec/1000000;
}
static void dispatch(void *context,TLAction action,int argument) {
    Controller *c=context;char err[TL_TEXT_MAX];TLModel defaults;
    if(c->picking&&action!=TL_QUIT)cancel_pick(c);
    switch(action) {
    case TL_PAINT_SAMPLE:
    case TL_PAINT_REFERENCE_SAMPLE: {
        TLManualPaintSampleRequest request;
        JobKind kind=action==TL_PAINT_REFERENCE_SAMPLE?
            JOB_PAINT_REFERENCE_SAMPLE:JOB_PAINT_SAMPLE;
        err[0]=0;
        int family=(argument>>8)&15, control=(argument>>4)&15, state=argument&15;
        if(family<0||family>=TL_FAMILY_COUNT||control<0||control>=TL_CONTROL_COUNT||state<0||state>=5)break;
        stop_kind(c,kind);
        if((action==TL_PAINT_REFERENCE_SAMPLE?
            tl_view_manual_paint_reference_current(c->view,&request):
            tl_view_manual_paint_sample_current(c->view,&request))||
           request.family!=family||request.control!=control||request.state!=state||
           request.source!=TL_PAINT_SAMPLE_LIVE||
           tl_manual_paint_sample_request_validate(&request,err,sizeof(err))) {
            status(c,err[0]?err:"Pedido privado de amostra mudou antes da captura.");break;
        }
        if(family!=TL_GTK2&&family!=TL_GTK3&&family!=TL_GTK4) {
            status(c,"Amostra nativa indisponível: esta família ainda não possui captura privada de controle.");break;
        }
        if(action==TL_PAINT_REFERENCE_SAMPLE)
            c->paint_reference_request=request;
        else
            c->paint_sample_request=request;
        if(start_job(c,kind,(TLFamily)family)) {
            char message[256];
            snprintf(message,sizeof(message),"%s %s aguarda uma receita "
                     "gerada para a cena aplicada.",
                     action==TL_PAINT_REFERENCE_SAMPLE?"A referência":"A amostra",
                     family==TL_GTK2?"GTK2":family==TL_GTK4?"GTK4":"GTK3");
            status(c,message);
        }
        break;
    }
    case TL_SELECT_FAMILY: {
        if(argument<0||argument>=TL_FAMILY_COUNT||read_edits(c))return;
        TLModel next=c->model;next.selected=(TLFamily)argument;
        if(commit_project(c,&next))return;
        stop_kind(c,JOB_COUPLED);stop_kind(c,JOB_PREVIEW);
        /* Selecting a family changes which already-applied recipe is shown;
         * it must not silently promote pending fields from working.json into
         * the applied scene.  TL_APPLY remains the only operation that copies
         * the complete draft model into c->applied. */
        c->applied.selected=c->model.selected;
        update_view(c);if(save_scene(c))return;c->palette_due=0;
        c->refresh_pending=scene_family(c->model.selected);c->coupled_after_generate=c->refresh_pending;
        c->want_separate=c->model.separate_preview;
        c->preview_after_generate=c->want_separate&&scene_family(c->model.selected);c->pending_family=c->model.selected;
        if(backend_coupled_family(c->model.selected))
            start_job(c,JOB_COUPLED,c->model.selected);
        if(c->want_separate&&!scene_family(c->model.selected)) {
            if(c->model.selected==TL_MOTIF) {c->want_separate=0;status(c,"Escolha salva; prévia Motif separada ainda indisponível.");}
            else start_job(c,JOB_PREVIEW,c->model.selected);
        }
        c->change_due=0;break;
    }
    case TL_SELECT_PART_STATE:
        if(!read_edits(c))start_job(c,JOB_SNIPPET,c->model.selected);
        break;
    case TL_PART_RELIEF_CHANGED:
        if(read_edits(c))return;
        start_job(c,JOB_SNIPPET,c->model.selected);
        /* Only edits schedule automatic preview; browsing states does not. */
        /* fall through */
    case TL_CHANGED: {
        /* Group a typing burst. The text journal still checkpoints every tick;
         * explicit actions capture immediately before changing project state. */
        c->persist_due=milliseconds()+300;
        tl_view_history_state(c->view,1,tl_project_session_can_step(c->history,1),
                              tl_project_session_has_point(c->history));
        int automatic=0,delay=600;tl_view_preview_settings(c->view,&automatic,&delay);
        c->change_due=automatic?milliseconds()+delay:0;
        break;
    }
    case TL_SELECT_SCROLL_PART: {
        if(argument<0||argument>=TL_SCROLL_PART_COUNT||read_edits(c))return;
        TLModel next=c->model;next.recipes[next.selected].selected_scroll_part=argument;
        if(commit_project(c,&next))return;
        update_view(c);start_job(c,JOB_SNIPPET,c->model.selected);break;
    }
    case TL_SELECT_ANCHOR: {
        if(argument<0 || argument>1 || read_edits(c))return;
        TLModel next=c->model;
        if(tl_view_set_anchor(c->view,&next,argument,err,sizeof(err))) {
            update_view(c);status(c,err);break;
        }
        if(commit_project(c,&next))return;
        int control=next.recipes[next.selected].selected_control;
        c->applied.recipes[next.selected].length_anchor[control]=next.recipes[next.selected].length_anchor[control];
        memcpy(c->applied.recipes[next.selected].positions[control],
               next.recipes[next.selected].positions[control],sizeof(int)*2);
        update_view(c);
        if(save_scene(c))return;
        c->change_due=c->model.automatic_preview?milliseconds()+c->model.debounce_ms:0;
        start_job(c,JOB_SNIPPET,c->model.selected);
        status(c,"Extremidade escolhida; posição preservada pela medida nativa. Alterações de tamanho seguem a opção Atualizar.");
        break;
    }
    case TL_SELECT_CONTROL: {
        if(argument<0||argument>=TL_CONTROL_COUNT||read_edits(c))return;
        TLModel next=c->model;next.recipes[next.selected].selected_control=argument;
        if(commit_project(c,&next))return;
        update_view(c);start_job(c,JOB_SNIPPET,c->model.selected);break;
    }
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
        if(scene_family(c->model.selected)) {
            /* A failed detached preview leaves its saved preference checked,
             * but suppresses automatic restart to avoid a crash loop. Apply
             * is the explicit recovery action: regenerate and reopen both
             * origins from the newly applied scene. */
            c->want_separate=c->model.separate_preview;
            c->preview_after_generate=c->want_separate;
            c->pending_family=c->model.selected;
            c->refresh_pending=1;c->coupled_after_generate=1;
            status(c,"Atualizando a cena nativa privada com os parâmetros escolhidos.");
        }else if(!save_scene(c)) {
            if(backend_coupled_family(c->model.selected)) {
                stop_kind(c,JOB_COUPLED);
                start_job(c,JOB_COUPLED,c->model.selected);
                status(c,"Atualizando a cena nativa acoplada com a receita privada desta família.");
            } else status(c,c->model.selected==TL_MOTIF?
                "Montagem Motif atualizada.":
                "Receita guardada; esta família não possui runtime nativo utilizável.");
        }break;
    case TL_SAVE: if(!read_edits(c))tl_view_choose_file(c->view,"Salvar projeto JSON",c->project,choose_save,c);break;
    case TL_LOAD: if(!read_edits(c))tl_view_choose_file(c->view,"Importar projeto JSON",c->project,choose_load,c);break;
    case TL_IMPORT_DELTA:
        if(active_kind(c,JOB_IMPORT)) {status(c,"Aguarde a importação em curso.");break;}
        if(!read_edits(c))tl_view_choose_file(c->view,"Importar delta — 1/2: selecione PROJECT.json da base",c->project,choose_import_base,c);
        break;
    case TL_RECONSTRUCT_FILES:
        if(active_kind(c,JOB_INSPECT_FILES)||active_kind(c,JOB_RECONSTRUCT)) {status(c,"Aguarde a reconstrução em curso.");break;}
        if(!read_edits(c))tl_view_choose_file(c->view,"Reconstruir arquivos — selecione FILES.json",c->generated,choose_reconstruction_files,c);
        break;
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
    case TL_PREVIEW: case TL_SEPARATE_TOGGLE: {
        if(read_edits(c))return;
        TLModel next=c->model;
        next.separate_preview=action==TL_PREVIEW?1:(argument!=0);
        if(commit_project(c,&next)) {
            tl_view_separate_preview(c->view,c->model.separate_preview);return;
        }
        update_view(c);sync_separate_preview(c);
        if(!next.separate_preview)status(c,"Prévia separada fechada; escolha salva e montagem acoplada preservada.");
        else if(c->applied.selected!=TL_MOTIF)status(c,"Abrindo a cena aplicada; escolha salva. Famílias sem tradutor mostram o tema atual, com limite explícito.");
        break;
    }
    case TL_EXPORT:
        if(active_kind(c,JOB_GENERATE)||active_kind(c,JOB_EXPORT)) {status(c,"Aguarde a geração privada em curso.");break;}
        if(!read_edits(c)) {start_job(c,JOB_EXPORT,c->model.selected);status(c,"Gerando proposta privada; o tema instalado permanece intacto.");}break;
    case TL_MANUAL_PAINT:
        if(read_edits(c))return;
        if(tl_view_manual_paint_open(c->view,c->manual_paint_path,c->model.selected,
             c->model.recipes[c->model.selected].selected_control,
             c->model.recipes[c->model.selected].edit_state))
            status(c,"Não foi possível abrir a camada manual. O arquivo original foi preservado.");
        else status(c,"Pintura manual aberta: camada raster separada; a receita e a prévia nativa permanecem inalteradas.");
        break;
    case TL_RESET: {
        if(read_edits(c))return;
        TLModel next=c->model;tl_model_init(&defaults);next.recipes[next.selected]=defaults.recipes[next.selected];
        next.recipes[next.selected].geometry=next.native_measured;
        if(commit_project(c,&next))return;
        c->applied=c->model;update_view(c);if(save_scene(c))return;c->palette_due=0;
        c->refresh_pending=scene_family(c->model.selected);c->coupled_after_generate=c->refresh_pending;
        if(backend_coupled_family(c->model.selected)) {
            stop_kind(c,JOB_COUPLED);start_job(c,JOB_COUPLED,c->model.selected);
        }
        status(c,"Receita desta família restaurada à base medida; recuperável por Desfazer projeto.");break;
    }
    case TL_PROJECT_UNDO: case TL_PROJECT_REDO: case TL_PROJECT_MARK:
    case TL_PROJECT_RESTORE: case TL_PROJECT_RESET_PART: {
        if(read_edits(c))return;
        int previous_separate=c->model.separate_preview;
        TLHistoryOperation operation=action==TL_PROJECT_UNDO?TL_HISTORY_UNDO:
            action==TL_PROJECT_REDO?TL_HISTORY_REDO:action==TL_PROJECT_MARK?TL_HISTORY_MARK:
            action==TL_PROJECT_RESTORE?TL_HISTORY_RESTORE:TL_HISTORY_RESET_PART;
        TLRecipe *recipe=&c->model.recipes[c->model.selected];
        int result=tl_project_session_change(c->history,operation,NULL,c->model.selected,
                                            (TLScrollPart)recipe->selected_scroll_part,err,sizeof(err));
        if(result<0) {status(c,err);return;}
        if(tl_project_session_current(c->history,&c->model,err,sizeof(err))) {status(c,err);return;}
        ++c->revision;c->change_due=0;update_view(c);
        c->working_dirty=1;
        if(tl_model_save(&c->model,c->working,err,sizeof(err))) {status(c,err);return;}
        c->working_dirty=0;
        if(previous_separate!=c->model.separate_preview)sync_separate_preview(c);
        start_job(c,JOB_SNIPPET,c->model.selected);
        status(c,result>0?err:action==TL_PROJECT_MARK?
            "Ponto de comparação salvo; não modifica a prévia.":
            "Projeto recuperado. Atualizar aplica à prévia; Undo dos textos continua independente.");
        break;
    }
    case TL_QUIT:
        if(read_edits(c))break;
        if(tl_view_manual_paint_checkpoint(c->view)) {
            status(c,"A camada manual não pôde ser salva; o laboratório continua aberto e o desenho permanece em memória.");
            break;
        }
        c->closing=1;cancel_pick(c);XtAppSetExitFlag(c->app);break;
    default: snprintf(err,sizeof(err),"Ação desconhecida: %d",action);status(c,err);
    }
}
static void preview_events(Controller *c) {
    DIR *folder=opendir(c->events);struct dirent *item;
    char names[TL_PREVIEW_EVENT_BATCH][TL_PREVIEW_EVENT_FILENAME];size_t count=0;
    if(!folder)return;
    while((item=readdir(folder)))count=tl_preview_event_order(names,count,item->d_name);
    for(size_t index=0;index<count;index++) {
        char buffer[16385];struct stat info;ssize_t size;TLPreviewEvent event;
        int file=openat(dirfd(folder),names[index],O_RDONLY|O_NOFOLLOW|O_NONBLOCK);
        if(file<0)continue;
        if(!fstat(file,&info)&&S_ISREG(info.st_mode)&&info.st_uid==getuid()&&!(info.st_mode&0077)&&info.st_size<=16384&&
           (size=read(file,buffer,16384))>0&&size==info.st_size&&
           scene_family(c->applied.selected) &&
           !tl_preview_event_family(buffer,(size_t)size,c->scene_hash,tl_family_ids[c->applied.selected],&event)&&
           preview_event_active(c,&event)) {
            if(event.action==TL_EVENT_METRICS) {
                /* A cancelled detached job can still have atomic events in
                 * the queue. Same scene hash does not mean its window is
                 * enabled: never resurrect allocations after closing it. */
                if((!event.metrics.separate || c->want_separate)&&
                    preview_origin_active(c,event.metrics.separate))
                    tl_view_native_metrics(c->view,event.control,&event.metrics);
            } else if(event.action==TL_EVENT_NATIVE && event.toggle_state_known) {
                int origin=event.toggle_separate;
                if((!origin || c->want_separate)&&preview_origin_active(c,origin)) {
                    int *known=event.control==2?c->check_known:c->toggle_known;
                    int *active=event.control==2?c->check_active:c->toggle_active;
                    known[origin]=1;active[origin]=event.toggle_active;
                }
            } else if(event.action==TL_EVENT_NATIVE && event.radio_state_known) {
                int origin=event.radio_separate;
                if((!origin || c->want_separate)&&preview_origin_active(c,origin)) {
                    c->radio_known[origin]=1;c->radio_member[origin]=event.radio_member;
                }
            } else if(event.action!=TL_EVENT_NATIVE&&!read_edits(c)) {
                /* Capture pending editor fields before selecting the rendered
                 * family. A scene gesture must never mutate another recipe. */
                TLModel next=c->model;next.selected=c->applied.selected;
                TLRecipe *recipe=&next.recipes[next.selected];recipe->selected_control=event.control;
                if(event.action==TL_EVENT_MOVE) {
                    recipe->positions[event.control][0]=event.x;recipe->positions[event.control][1]=event.y;

                }
                if(!commit_project(c,&next)) {
                    if(event.action==TL_EVENT_MOVE) {
                        c->applied.recipes[c->model.selected].selected_control=event.control;
                        memcpy(c->applied.recipes[c->model.selected].positions[event.control],recipe->positions[event.control],sizeof(int)*2);
                        c->refresh_pending=1;c->coupled_after_generate=1;
                    }
                    update_view(c);
                }
            }
        }
        close(file);(void)unlinkat(dirfd(folder),names[index],0);
    }
    closedir(folder);
}
static void tick(XtPointer context,XtIntervalId *id) {
    Controller *c=context;time_t now=time(NULL);int i;(void)id;
    if(interrupted) {
        /* A rejected close must keep checkpoints and jobs running. Consume
         * only this signal so another request can retry after the edit is fixed. */
        interrupted=0;
        dispatch(c,TL_QUIT,0);
        if(c->closing)return;
    }
    for(i=0;i<16;i++)if(c->jobs[i].pid>0) {
        Job *j=&c->jobs[i];char block[4096];ssize_t n;int result;
        while((n=read(j->fd,block,sizeof(block)))>0) {size_t room=j->capacity-j->used, take=(size_t)n<room?(size_t)n:room;
            if(take<(size_t)n)j->overflow=1;
            memcpy(j->text+j->used,block,take);j->used+=take;}
        if(j->cancelled&&milliseconds()-j->cancelled_ms<2000)continue;
        if(j->cancelled)kill(-j->pid,SIGKILL);
        if(j->kind!=JOB_PREVIEW&&j->kind!=JOB_COUPLED&&!j->timed_out&&
            milliseconds()-j->started_ms>=30000) {j->timed_out=1;kill(-j->pid,SIGKILL);}
        if(tl_owned_process_poll(j->pid,&result)==1)finish_job(c,j,result);
    }
    {char error[TL_TEXT_MAX];if(tl_view_editor_checkpoint(c->view,error,sizeof(error)))status(c,error);}
    preview_events(c);
    if(c->persist_due&&milliseconds()>=c->persist_due)read_edits(c);
    if(c->refresh_pending&&!active_kind(c,JOB_GENERATE)&&!active_kind(c,JOB_EXPORT)) {
        stop_detached_native(c);
        if(active_kind(c,JOB_COUPLED))stop_kind(c,JOB_COUPLED);
        else if(scene_family(c->applied.selected)&&!save_scene(c)) {
            c->refresh_pending=0;start_job(c,JOB_GENERATE,c->applied.selected);
        }else if(!scene_family(c->applied.selected))c->refresh_pending=0;
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
    Controller c={0};char err[TL_TEXT_MAX],contract[TL_PATH_MAX],temporary[TL_PATH_MAX],temp_base[TL_PATH_MAX];
    char r584_receipt[TL_PATH_MAX],r584_manifest[TL_PATH_MAX];
    const char *initial=NULL,*reference=NULL,*family=NULL;int i;char *xtargv[]={argv[0],NULL};int xtargc=1;
    setlocale(LC_ALL,"");umask(0077);tl_model_init(&c.model);
    for(i=1;i<argc;i++) {
        if(!strcmp(argv[i],"--help")) {puts("theme-lab --root REPOSITORY --work-dir PRIVATE_DIR [--project JSON] [--reference PNG] [--family gtk3|motif|...] [--gtk4-host-bridge LIBRARY]\nInterface Motif C99/MVC. Apply and export affect private proposals only.");return 0;}
        if(i+1>=argc) {fprintf(stderr,"Argumento incompleto: %s\n",argv[i]);return 2;}
        if(!strcmp(argv[i],"--root")) {if(strlen(argv[++i])>=sizeof(c.root))return 2;strcpy(c.root,argv[i]);}
        else if(!strcmp(argv[i],"--work-dir")) {if(strlen(argv[++i])>=sizeof(c.work))return 2;strcpy(c.work,argv[i]);}
        else if(!strcmp(argv[i],"--project")) initial=argv[++i];
        else if(!strcmp(argv[i],"--reference"))reference=argv[++i];
        else if(!strcmp(argv[i],"--family"))family=argv[++i];
        else if(!strcmp(argv[i],"--gtk4-host-bridge")) {if(strlen(argv[++i])>=sizeof(c.host4))return 2;strcpy(c.host4,argv[i]);}
        else {fprintf(stderr,"Argumento desconhecido: %s\n",argv[i]);return 2;}
    }
    if(!c.root[0]) {fprintf(stderr,"Informe --root com a raiz dos tradutores.\n");return 2;}
    if(!c.work[0]) {
        const char *home=getenv("HOME");
        if(!home||home[0]!='/') {fputs("HOME absoluto é necessário para criar a sessão privada em ~/tempia.\n",stderr);return 1;}
        if(path_join(temp_base,sizeof(temp_base),home,"tempia/domainos-theme-work")) {fputs("Caminho de ~/tempia/domainos-theme-work muito longo.\n",stderr);return 1;}
        if(private_directory(temp_base,err,sizeof(err))) {fprintf(stderr,"Não foi possível preparar ~/tempia/domainos-theme-work: %s\n",err);return 1;}
        int n=snprintf(temporary,sizeof(temporary),"%s/theme-lab-XXXXXX",temp_base);
        if(n<0||(size_t)n>=sizeof(temporary)) {fputs("Caminho temporário muito longo.\n",stderr);return 1;}
        char *made=mkdtemp(temporary);if(!made) {perror("mkdtemp em ~/tempia");return 1;}
        if(strlen(made)>=sizeof(c.work)) {fputs("Caminho da sessão temporária muito longo.\n",stderr);return 1;}
        strcpy(c.work,made);
    }
    if(private_directory(c.work,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}
    if(path_join(c.project,sizeof(c.project),c.work,"project.json")||path_join(c.working,sizeof(c.working),c.work,"working.json")||
       path_join(c.generated,sizeof(c.generated),c.work,"generated")||path_join(c.backend,sizeof(c.backend),c.root,"tools/theme-lab/backend.py")||
       path_join(c.editor_path,sizeof(c.editor_path),c.work,"editor-journal.json")||
       path_join(c.history_path,sizeof(c.history_path),c.work,"project-history.json")||
       path_join(c.manual_paint_path,sizeof(c.manual_paint_path),c.work,"manual-paint.json")||
       path_join(c.scene,sizeof(c.scene),c.work,"scene.json")||path_join(c.events,sizeof(c.events),c.work,"preview-events")||
       path_join(c.native,sizeof(c.native),c.root,"tools/theme-lab/preview_gtk.py")||
       path_join(c.native2,sizeof(c.native2),c.root,"tools/theme-lab/preview_gtk2.py")||
       path_join(c.native4,sizeof(c.native4),c.root,"tools/theme-lab/preview_gtk4.py")||
       path_join(contract,sizeof(contract),c.root,"tools/domainos_scrollbar_rules.json")) {fputs("Caminho muito longo.\n",stderr);return 2;}
    if(!c.host4[0]&&path_join(c.host4,sizeof(c.host4),c.root,"tools/theme-lab/build/libtheme-lab-gtk4-host.so"))return 2;
    if(initial) {if(tl_model_load(&c.model,initial,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}}
    else if(access(c.working,F_OK)==0) {if(tl_model_load(&c.model,c.working,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}}
    else if(tl_model_contract(&c.model,contract,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}
    if(family) {
        int found=0;
        for(i=0;i<TL_FAMILY_COUNT;i++)if(!strcmp(family,tl_family_ids[i])) {c.model.selected=(TLFamily)i;found=1;break;}
        if(!found) {fprintf(stderr,"Família desconhecida: %s\n",family);return 2;}
    }
    if(reference) {if(strlen(reference)>=sizeof(c.model.reference))return 2;strcpy(c.model.reference,reference);}
    if(pieces_pending(&c.model)) {
        fputs("Projeto contém receitas pendentes; dados preservados. A geração informa o suporte da família selecionada.\n",stderr);
    }
    TLModel requested=c.model;
    if(tl_project_session_open(&c.history,c.history_path,&requested,err,sizeof(err))<0 ||
       (initial&&tl_project_session_change(c.history,TL_HISTORY_PUSH,&requested,TL_MOTIF,TL_SCROLL_ARROW,err,sizeof(err))<0) ||
       tl_project_session_current(c.history,&c.model,err,sizeof(err))) {
        fprintf(stderr,"%s\n",err);tl_project_session_free(c.history);return 1;
    }
    if(family)c.model.selected=requested.selected;
    if(reference)strcpy(c.model.reference,requested.reference);
    if((family||reference)&&tl_project_session_change(c.history,TL_HISTORY_PUSH,&c.model,TL_MOTIF,TL_SCROLL_ARROW,err,sizeof(err))<0) {
        fprintf(stderr,"%s\n",err);tl_project_session_free(c.history);return 1;
    }
    if(pieces_pending(&c.model)) {
        fputs("Histórico recuperado com receitas pendentes; dados preservados, sem alegar tradução nativa.\n",stderr);
    }
    int restored_scene=access(c.scene,F_OK)==0;
    if(restored_scene) {
        if(tl_model_load(&c.applied,c.scene,err,sizeof(err))||digest_file(c.scene,c.scene_hash)) {
            fprintf(stderr,"Cena salva inválida; arquivo preservado: %s\n",err);
            tl_project_session_free(c.history);return 1;
        }
    } else c.applied=c.model;
    if(tl_model_save(&c.model,c.working,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}
    if(!restored_scene&&(tl_model_save(&c.applied,c.scene,err,sizeof(err))||digest_file(c.scene,c.scene_hash))) {fprintf(stderr,"Não foi possível salvar a cena privada.\n");return 1;}
    if(private_directory(c.events,err,sizeof(err))) {fprintf(stderr,"%s\n",err);return 1;}
    XtSetLanguageProc(NULL,NULL,NULL);
    c.shell=XtVaAppInitialize(&c.app,"ThemeLab",NULL,0,&xtargc,xtargv,NULL,XtNtitle,"Laboratório de temas — Motif MVC / três painéis",XtNwidth,1320,XtNheight,850,NULL);
    c.view=tl_view_create(c.shell,dispatch,&c);if(!c.view)return 1;
    {
        const char *home=getenv("HOME");
        err[0]=0;
        int receipt_ok=path_join(r584_receipt,sizeof(r584_receipt),c.root,
            "docs/review/I167-GTK2-USER-PALETTE-UPDATE-20261028-R584.json")==0;
        int manifest_length=home&&home[0]=='/'?
            snprintf(r584_manifest,sizeof(r584_manifest),
                "%s/.local/share/irixium/gtk2-palette/%s/manifest.json",
                home,tl_gtk2_r584_canonical_identity.bundle_id):-1;
        if(!receipt_ok||manifest_length<0||
           (size_t)manifest_length>=sizeof(r584_manifest)||
           tl_view_manual_paint_r584_catalog(c.view,r584_receipt,r584_manifest,
                                             err,sizeof(err)))
            fprintf(stderr,"theme-lab: fonte R584 indisponível: %s\n",
                    err[0]?err:"caminho inválido");
    }
    if(tl_view_editor_open(c.view,c.editor_path,err,sizeof(err))) {fprintf(stderr,"%s\n",err);tl_view_destroy(c.view);XtDestroyWidget(c.shell);XtDestroyApplicationContext(c.app);return 1;}
    live_controller=&c;XSetIOErrorHandler(display_closed);
    update_view(&c);XtRealizeWidget(c.shell);
    { unsigned long pid=(unsigned long)getpid();
      XChangeProperty(XtDisplay(c.shell),XtWindow(c.shell),XInternAtom(XtDisplay(c.shell),"_NET_WM_PID",False),
                      XA_CARDINAL,32,PropModeReplace,(unsigned char*)&pid,1); }
    if(c.model.reference[0]&&tl_view_reference(c.view,c.model.reference,err,sizeof(err)))status(&c,err);
    c.cursor=XCreateFontCursor(XtDisplay(c.shell),XC_crosshair);
    XtAddEventHandler(c.shell,ButtonPressMask|KeyPressMask,False,picker,&c);
    {
        struct sigaction action={0};
        sigemptyset(&action.sa_mask);
        action.sa_handler=caught_signal;
        if(sigaction(SIGTERM,&action,NULL)||sigaction(SIGINT,&action,NULL)) {
            perror("Falha ao instalar sinais de encerramento");return 2;
        }
        action.sa_handler=SIG_IGN;
        if(sigaction(SIGPIPE,&action,NULL)) {
            perror("Falha ao configurar SIGPIPE");return 2;
        }
    }
    start_job(&c,JOB_PROBE,TL_MOTIF);start_job(&c,JOB_SCHEMES,TL_MOTIF);start_job(&c,JOB_SNIPPET,c.model.selected);
    start_job(&c,JOB_PALETTE,c.model.selected);start_job(&c,JOB_SHELL_PALETTE,c.model.selected);start_job(&c,JOB_REFERENCE_PALETTE,TL_MOTIF);c.palette_due=time(NULL)+4;
    c.refresh_pending=scene_family(c.applied.selected);c.coupled_after_generate=c.refresh_pending;
    if(coupled_family(c.applied.selected)&&!scene_family(c.applied.selected))
        start_job(&c,JOB_COUPLED,c.applied.selected);
    sync_separate_preview(&c);
    XtAppAddTimeOut(c.app,100,tick,&c);XtAppMainLoop(c.app);
    cancel_pick(&c);
    shutdown_jobs(&c);
    for(i=0;i<16;i++)if(c.jobs[i].pid>0) {close(c.jobs[i].fd);free(c.jobs[i].text);}
    tl_project_session_free(c.history);tl_view_destroy(c.view);XFreeCursor(XtDisplay(c.shell),c.cursor);XtDestroyWidget(c.shell);XtDestroyApplicationContext(c.app);return 0;
}
