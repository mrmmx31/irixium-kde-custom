/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include "project_history_store.h"
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
static int fail(char *error,size_t capacity,const char *text) {
    if(error&&capacity)snprintf(error,capacity,"%s",text);
    return -1;
}
static int read_root(const char *path,json_object **root,char *error,size_t capacity) {
    int fd=open(path,O_RDONLY|O_NOFOLLOW|O_NONBLOCK);
    if(fd<0)return errno==ENOENT?1:fail(error,capacity,"Não foi possível ler o histórico; arquivo preservado.");
    struct stat st;
    if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size<1||st.st_size>TL_HISTORY_JSON_LIMIT) {
        close(fd);return fail(error,capacity,"Tipo ou tamanho inválido do histórico.");
    }
    size_t length=(size_t)st.st_size,offset=0;
    char *text=malloc(length+1);
    if(!text){close(fd);return fail(error,capacity,"Memória insuficiente.");}
    while(offset<length) {
        ssize_t n=read(fd,text+offset,length-offset);
        if(n<0&&errno==EINTR)continue;
        if(n<=0)break;
        offset+=(size_t)n;
    }
    char extra;ssize_t more=read(fd,&extra,1);close(fd);text[length]=0;
    if(offset!=length||more!=0||memchr(text,0,length)) {
        free(text);return fail(error,capacity,"Histórico mudou durante a leitura ou contém dados inválidos.");
    }
    json_tokener *tok=json_tokener_new();
    if(!tok){free(text);return fail(error,capacity,"Memória insuficiente.");}
    json_tokener_set_flags(tok,JSON_TOKENER_VALIDATE_UTF8);
    json_object *value=json_tokener_parse_ex(tok,text,(int)length);
    size_t end=json_tokener_get_parse_end(tok);
    while(end<length&&isspace((unsigned char)text[end]))++end;
    int valid=json_tokener_get_error(tok)==json_tokener_success&&end==length;
    json_tokener_free(tok);free(text);
    TLProjectHistory *h=valid?tl_history_decode(value,error,capacity):NULL;
    if(!h){json_object_put(value);return fail(error,capacity,"Histórico inválido; arquivo não foi substituído.");}
    tl_history_free(h);*root=value;return 0;
}
int tl_history_store_load(const char *path,TLProjectHistory **history,json_object **revision,char *error,size_t capacity) {
    json_object *root=NULL;
    if(!path||!history||!revision)return fail(error,capacity,"Destino inválido.");
    int result=read_root(path,&root,error,capacity);
    if(result)return result;
    TLProjectHistory *h=tl_history_decode(root,error,capacity);
    if(!h){json_object_put(root);return -1;}
    *history=h;*revision=root;return 0;
}
int tl_history_store_commit(const char *path,const TLProjectHistory *candidate,json_object *expected,json_object **revision,char *error,size_t capacity) {
    char lockpath[PATH_MAX],temporary[PATH_MAX],directory[PATH_MAX];
    int lock=-1,fd=-1,dir=-1,result=-1,created=0;json_object *root=NULL,*current=NULL;
    temporary[0]=0;
    if(!path||!*path||!revision||snprintf(lockpath,sizeof(lockpath),"%s.lock",path)>=(int)sizeof(lockpath)||
       snprintf(temporary,sizeof(temporary),"%s.tmp-XXXXXX",path)>=(int)sizeof(temporary)||
       snprintf(directory,sizeof(directory),"%s",path)>=(int)sizeof(directory))return fail(error,capacity,"Caminho inválido.");
    char *slash=strrchr(directory,'/');
    if(!slash)snprintf(directory,sizeof(directory),".");else if(slash==directory)slash[1]=0;else *slash=0;
    root=tl_history_encode(candidate);
    TLProjectHistory *validated=root?tl_history_decode(root,error,capacity):NULL;
    if(!validated){json_object_put(root);return fail(error,capacity,"Candidato de histórico inválido.");}
    tl_history_free(validated);
    const char *text=json_object_to_json_string_ext(root,JSON_C_TO_STRING_PLAIN);size_t length=strlen(text);
    if(length>TL_HISTORY_JSON_LIMIT){fail(error,capacity,"Histórico excede limite de 32 MiB.");goto done;}
    lock=open(lockpath,O_CREAT|O_RDWR|O_NOFOLLOW|O_NONBLOCK,0600);
    struct stat st;
    if(lock<0||fstat(lock,&st)||!S_ISREG(st.st_mode)||flock(lock,LOCK_EX|LOCK_NB)) {
        fail(error,capacity,"Histórico ocupado ou lock indisponível; tente novamente.");goto done;
    }
    int loaded=read_root(path,&current,error,capacity);
    if(loaded<0)goto done;
    if((loaded==1&&expected)||(loaded==0&&(!expected||!json_object_equal(current,expected)))) {
        fail(error,capacity,"Conflito: outra instância alterou o histórico; nada foi substituído.");goto done;
    }
    dir=open(directory,O_RDONLY|O_DIRECTORY);
    if(dir<0||(fd=mkstemp(temporary))<0){fail(error,capacity,"Não foi possível preparar a gravação.");goto done;}
    created=1;
    size_t offset=0;
    while(offset<length) {
        ssize_t n=write(fd,text+offset,length-offset);
        if(n<0&&errno==EINTR)continue;
        if(n<=0)break;
        offset+=(size_t)n;
    }
    if(offset!=length||fsync(fd)||rename(temporary,path)) {
        fail(error,capacity,"Falha ao gravar; histórico anterior preservado.");goto done;
    }
    temporary[0]=0;result=fsync(dir)?1:0;
    if(result==1)fail(error,capacity,"Histórico gravado, mas a durabilidade do diretório não pôde ser confirmada.");
    *revision=json_object_get(root);
done:
    if(fd>=0)close(fd);
    if(created&&temporary[0])unlink(temporary);
    if(dir>=0)close(dir);
    if(lock>=0)close(lock);
    json_object_put(root);json_object_put(current);return result;
}
