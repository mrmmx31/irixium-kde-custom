/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "internal.h"
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#define JOURNAL_LIMIT (8*1024*1024)
static int utf8(const char *text,size_t n) {
    size_t i=0;
    while(i<n) {
        unsigned char c=(unsigned char)text[i++];unsigned code;int count;
        if(c<128) {if(!c)return 0;continue;}
        if(c>=194&&c<=223) {code=c&31;count=1;}
        else if(c>=224&&c<=239) {code=c&15;count=2;}
        else if(c>=240&&c<=244) {code=c&7;count=3;}
        else return 0;
        int total=count;
        while(count--) {if(i>=n)return 0;c=(unsigned char)text[i++];if((c&192)!=128)return 0;code=(code<<6)|(c&63);}
        if((total==1&&code<128)||(total==2&&code<2048)||(total==3&&code<65536)||
           code>0x10ffff||(code>=0xd800&&code<=0xdfff))return 0;
    }
    return 1;
}
static int validate(json_object *histories) {
    /* Contexts accumulate across families and controls. Bound the journal by
     * bytes (JOURNAL_LIMIT), not by an arbitrary number of visited fields. */
    if(!json_object_is_type(histories,json_type_object))return 0;
    json_object_object_foreach(histories,key,value) {
        json_object *entries=NULL,*position=NULL;
        if(!key[0]||strlen(key)>=1024||!utf8(key,strlen(key))||!json_object_is_type(value,json_type_object)||
           !json_object_object_get_ex(value,"entries",&entries)||!json_object_is_type(entries,json_type_array)||
           !json_object_object_get_ex(value,"position",&position)||!json_object_is_type(position,json_type_int))return 0;
        size_t n=json_object_array_length(entries),bytes=0;
        int pos=json_object_get_int(position);
        if(n<1||n>128||pos<0||(size_t)pos>=n)return 0;
        for(size_t i=0;i<n;++i) {
            json_object *item=json_object_array_get_idx(entries,i);
            if(!json_object_is_type(item,json_type_string))return 0;
            const char *s=json_object_get_string(item);size_t len=(size_t)json_object_get_string_len(item);
            if(len>65536||strlen(s)!=len||!utf8(s,len))return 0;
            bytes+=len;
        }
        if(bytes>1024*1024)return 0;
    }
    return 1;
}
static int open_parent_directory(const char *path) {
    char parent[4096];
    char *separator;
    size_t length = strlen(path);
    if (!length || length >= sizeof(parent))
        return -1;
    memcpy(parent, path, length + 1);
    separator = strrchr(parent, '/');
    if (!separator)
        return open(".", O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    if (separator == parent)
        separator[1] = '\0';
    else
        *separator = '\0';
    return open(parent, O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
}
TLEditorStore *tl_editor_store_new(void) {
    TLEditorStore *store=calloc(1,sizeof(*store));
    if(store)store->histories=json_object_new_object();
    return store;
}
void tl_editor_store_free(TLEditorStore *store) {
    if(store) {json_object_put(store->histories);free(store);}
}
int tl_editor_store_load(TLEditorStore *store,const char *path,char *error,size_t capacity) {
    const char *reason="arquivo";struct stat st;int fd=-1,result=-1;char *buffer=NULL;json_object *root=NULL,*histories=NULL,*version=NULL;
    if(strlen(path)>=sizeof(store->path))goto fail;
    fd=open(path,O_RDONLY|O_NOFOLLOW|O_NONBLOCK);
    if(fd<0) {if(errno==ENOENT) {snprintf(store->path,sizeof(store->path),"%s",path);return 0;}goto fail;}
    if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_uid!=getuid()||(st.st_mode&0077)||st.st_size<1||st.st_size>JOURNAL_LIMIT)goto fail;
    size_t n=(size_t)st.st_size,offset=0;buffer=malloc(n+1);if(!buffer)goto fail;
    while(offset<n) {ssize_t got=read(fd,buffer+offset,n-offset);if(got<0&&errno==EINTR)continue;if(got<=0)goto fail;offset+=(size_t)got;}
    buffer[n]=0;
    reason="JSON";
    json_tokener *tok=json_tokener_new();if(!tok)goto fail;
    /* The installed json-c 0.18 STRICT path rejects raw accented strings
     * written by its own serializer. Validate UTF-8 explicitly, then check
     * complete consumption, schema, types and history bounds below. */
    json_tokener_set_flags(tok,JSON_TOKENER_VALIDATE_UTF8);
    root=json_tokener_parse_ex(tok,buffer,(int)n);
    int valid=json_tokener_get_error(tok)==json_tokener_success&&json_tokener_get_parse_end(tok)==n;
    json_tokener_free(tok);
    reason="schema/históricos";
    if(!valid||!json_object_object_get_ex(root,"schema_version",&version)||json_object_get_int(version)!=1||
       !json_object_object_get_ex(root,"histories",&histories)||!validate(histories))goto fail;
    for(TLEditor *e=store->editors;e;e=e->next)e->history=NULL;
    json_object_put(store->histories);store->histories=json_object_get(histories);store->restoring=1;
    snprintf(store->path,sizeof(store->path),"%s",path);result=0;
fail:
    if(result)snprintf(error,capacity,"Journal de edição inválido/indisponível (%s); preservado: %.280s",reason,path);
    if(fd>=0)close(fd);
    free(buffer);json_object_put(root);return result;
}
int tl_editor_checkpoint(TLEditorStore *store,char *error,size_t capacity) {
    if(!store->dirty||!store->path[0])return 0;
    struct stat st;char temporary[4096];int fd=-1, parent_fd=-1,result=-1;
    if(!validate(store->histories))goto fail;
    if(lstat(store->path,&st)==0) {
        if(!S_ISREG(st.st_mode)||st.st_uid!=getuid()||(st.st_mode&0077))goto fail;
    } else if(errno!=ENOENT) goto fail;
    parent_fd=open_parent_directory(store->path);
    if(parent_fd<0)goto fail;
    if(snprintf(temporary,sizeof(temporary),"%s.XXXXXX",store->path)>=(int)sizeof(temporary))goto fail;
    fd=mkstemp(temporary);if(fd<0)goto fail;
    json_object *root=json_object_new_object();
    json_object_object_add(root,"schema_version",json_object_new_int(1));
    json_object_object_add(root,"histories",json_object_get(store->histories));
    const char *text=json_object_to_json_string_ext(root,JSON_C_TO_STRING_PLAIN);size_t len=strlen(text),offset=0;
    if(len<=JOURNAL_LIMIT)while(offset<len) {ssize_t n=write(fd,text+offset,len-offset);if(n<0&&errno==EINTR)continue;if(n<=0)break;offset+=(size_t)n;}
    if(offset==len&&!fsync(fd)&&!close(fd)) {
        fd=-1;
        if(!rename(temporary,store->path)&&!fsync(parent_fd)) {
            store->dirty=0;
            result=0;
        }
    }
    json_object_put(root);
    if(result)unlink(temporary);
fail:
    if(fd>=0) {close(fd);unlink(temporary);}
    if(parent_fd>=0)close(parent_fd);
    if(result)snprintf(error,capacity,"Rascunho permanece em memória; não foi possível gravar o journal de edição.");
    return result;
}
