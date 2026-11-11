/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "project_history.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int equal(const TLModel *a,const TLModel *b) {
    char error[512];json_object *x=tl_model_encode(a,error,sizeof(error)),*y=tl_model_encode(b,error,sizeof(error));
    assert(x&&y);int same=json_object_equal(x,y);json_object_put(x);json_object_put(y);return same;
}
int main(void) {
    char error[512];TLModel initial,changed,current;tl_model_init(&initial);
    TLProjectHistory *h=tl_history_new(&initial,error,sizeof(error));assert(h);
    assert(!tl_history_can_step(h,-1)&&!tl_history_can_step(h,1));
    assert(!tl_history_mark(h));changed=initial;
    changed.separate_preview=1;
    changed.recipes[TL_GTK3].sizes[10][0]=280;
    changed.recipes[TL_GTK3].positions[10][0]=40;
    assert(!tl_part_relief_set(&changed.recipes[TL_GTK3].scrollbar_parts.parts[TL_SCROLL_THUMB],1,3));
    assert(!tl_part_relief_set(&changed.recipes[TL_GTK3].scrollbar_parts.parts[TL_SCROLL_ARROW],0,2));
    strcpy(changed.recipes[TL_GTK3].notes,"Medição: ação e posição — texto preservado.");
    assert(!tl_history_push(h,&changed,error,sizeof(error)));
    assert(tl_history_can_step(h,-1));
    assert(!tl_history_step(h,-1,error,sizeof(error)));
    assert(!tl_history_current(h,&current,error,sizeof(error)));assert(equal(&initial,&current));
    assert(!tl_history_step(h,1,error,sizeof(error)));
    assert(!tl_history_current(h,&current,error,sizeof(error)));assert(equal(&changed,&current));
    assert(!tl_history_push(h,&current,error,sizeof(error)));
    json_object *saved=tl_history_encode(h);assert(json_object_array_length(json_object_object_get(saved,"entries"))==2);
    TLProjectHistory *reloaded=tl_history_decode(saved,error,sizeof(error));assert(reloaded);
    assert(tl_history_has_point(reloaded));assert(!tl_history_current(reloaded,&current,error,sizeof(error)));assert(equal(&changed,&current));
    assert(!tl_history_reset_part(reloaded,TL_GTK3,TL_SCROLL_THUMB,error,sizeof(error)));
    assert(!tl_history_current(reloaded,&current,error,sizeof(error)));
    TLModel expected=changed;memset(&expected.recipes[TL_GTK3].scrollbar_parts.parts[TL_SCROLL_THUMB],0,sizeof(TLPartRecipe));
    assert(equal(&expected,&current));
    assert(!tl_history_step(reloaded,-1,error,sizeof(error)));assert(!tl_history_current(reloaded,&current,error,sizeof(error)));assert(equal(&changed,&current));
    assert(!tl_history_restore(reloaded,error,sizeof(error)));assert(!tl_history_can_step(reloaded,1));
    assert(!tl_history_current(reloaded,&current,error,sizeof(error)));assert(equal(&initial,&current));
    assert(!tl_history_step(reloaded,-1,error,sizeof(error)));assert(!tl_history_current(reloaded,&current,error,sizeof(error)));assert(equal(&changed,&current));
    json_object *before=tl_history_encode(reloaded);TLModel invalid=current;invalid.recipes[TL_GTK3].geometry.bar_px=-1;
    assert(tl_history_push(reloaded,&invalid,error,sizeof(error))<0);
    assert(tl_history_reset_part(reloaded,(TLFamily)-1,TL_SCROLL_THUMB,error,sizeof(error))<0);
    json_object *after=tl_history_encode(reloaded);assert(json_object_equal(before,after));json_object_put(after);
    json_object_object_add(saved,"position",json_object_new_int(-1));assert(!tl_history_decode(saved,error,sizeof(error)));
    json_object *bad=tl_history_encode(reloaded);
    json_object_object_add(bad,"kind",json_object_new_string_len("theme_lab_project_history\0suffix",32));
    assert(!tl_history_decode(bad,error,sizeof(error)));json_object_put(bad);
    bad=tl_history_encode(reloaded);
    json_object *bad_entry=json_object_array_get_idx(json_object_object_get(bad,"entries"),0);
    json_object_object_add(bad_entry,"selected_family",json_object_new_string("unsupported"));
    assert(!tl_history_decode(bad,error,sizeof(error)));json_object_put(bad);
    bad=tl_history_encode(reloaded);json_object_object_add(bad,"point",json_object_new_object());
    assert(!tl_history_decode(bad,error,sizeof(error)));json_object_put(bad);
    after=tl_history_encode(reloaded);assert(json_object_equal(before,after));json_object_put(after);
    for(int i=0;i<140;++i) {changed.recipes[TL_GTK3].sizes[10][0]=300+i;assert(!tl_history_push(h,&changed,error,sizeof(error)));}
    after=tl_history_encode(h);assert(json_object_array_length(json_object_object_get(after,"entries"))==TL_HISTORY_LIMIT);
    int steps=0;while(tl_history_can_step(h,-1)) {assert(!tl_history_step(h,-1,error,sizeof(error)));++steps;}assert(steps==127);
    assert(tl_history_step(h,-1,error,sizeof(error))<0);
    assert(!tl_history_current(h,&current,error,sizeof(error)));assert(current.recipes[TL_GTK3].sizes[10][0]==312);
    json_object_put(after);json_object_put(before);json_object_put(saved);tl_history_free(h);tl_history_free(reloaded);
    puts("Project history: multistep states/numbers/layout, independent checkpoint, selective reset, branch, validated codec and bounds passed.");return 0;
}
