/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "scrollbar_parts.h"
#include <assert.h>
#include <string.h>
int main(void) {
    TLScrollbarParts parts={0};char error[256];
    assert(!tl_scroll_parts_set(&parts,TL_SCROLL_ARROW,0,7));
    assert(!tl_part_relief_set(&parts.parts[TL_SCROLL_ARROW],0,2));
    assert(!tl_part_relief_set(&parts.parts[TL_SCROLL_ARROW],1,3));
    assert(!tl_part_relief_set(&parts.parts[TL_SCROLL_THUMB],4,1));
    assert(tl_scroll_parts_any(&parts));
    TLScrollbarParts original=parts,decoded={0};
    json_object *data=tl_scroll_parts_encode(&parts);
    assert(!tl_scroll_parts_decode(&decoded,data,error,sizeof(error)));
    assert(!memcmp(&decoded,&parts,sizeof(parts)));
    assert(!tl_part_relief_set(&parts.parts[TL_SCROLL_ARROW],1,-1));
    assert(parts.parts[TL_SCROLL_ARROW].values[0]==7);
    assert(parts.parts[TL_SCROLL_ARROW].relief[0]==2);
    assert(!memcmp(&parts.parts[TL_SCROLL_THUMB],&original.parts[TL_SCROLL_THUMB],sizeof(TLPartRecipe)));
    assert(tl_part_relief_set(&parts.parts[TL_SCROLL_ARROW],6,1)==-1);
    assert(tl_part_relief_set(&parts.parts[TL_SCROLL_ARROW],0,0)==-1);
    json_object_put(data);
    const char *bad[]={"{\"arrow\":{\"state_relief\":{\"hover\":\"unknown\"}}}",
        "{\"arrow\":{\"state_relief\":{\"unknown\":\"raised\"}}}",
        "{\"arrow\":{\"state_relief\":{\"focus\":true}}}"};
    for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);++i) {
        data=json_tokener_parse(bad[i]);decoded=original;
        assert(tl_scroll_parts_decode(&decoded,data,error,sizeof(error))==-1);
        assert(!memcmp(&decoded,&original,sizeof(decoded)));json_object_put(data);
    }
    return 0;
}
