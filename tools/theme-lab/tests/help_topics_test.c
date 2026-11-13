/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "help_topics.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <locale.h>
#include <wchar.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"help topics line %d\n",__LINE__);exit(1);}}while(0)
static void utf8(const char *s){
    mbstate_t state={0};wchar_t wc;
    for(const char *p=s;*p;){size_t n=mbrtowc(&wc,p,strlen(p),&state);CHECK(n&&n!=(size_t)-1&&n!=(size_t)-2);p+=n;}
}
int main(void){
    CHECK(setlocale(LC_ALL,"C.UTF-8"));
    CHECK(!tl_help_topic_title(-1)&&!tl_help_topic_title(TL_HELP_TOPIC_COUNT));
    CHECK(!tl_help_level_title(-1)&&!tl_help_level_title(TL_HELP_LEVEL_COUNT));
    CHECK(!tl_help_topic_text(0,-1)&&!tl_help_topic_text(0,TL_HELP_LEVEL_COUNT));
    CHECK(!tl_help_topic_text(-1,0)&&!tl_help_topic_text(TL_HELP_TOPIC_COUNT,0));
    for(int t=0;t<TL_HELP_TOPIC_COUNT;++t){
        const char *title=tl_help_topic_title(t);CHECK(title&&strlen(title)>8);utf8(title);
        for(int l=0;l<TL_HELP_LEVEL_COUNT;++l){
            const char *text=tl_help_topic_text(t,l);CHECK(text&&strlen(text)>80);utf8(text);utf8(tl_help_level_title(l));
            for(int k=0;k<l;++k)CHECK(strcmp(text,tl_help_topic_text(t,k)));
        }
        CHECK(strlen(tl_help_topic_text(t,0))>strlen(tl_help_topic_text(t,2)));
    }
    puts("Help model: 10 topics × 3 distinct UTF-8 levels; invalid indexes rejected.");return 0;
}
