/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "scrollbar_parts.h"
#include <string.h>
const char *const tl_part_state_ids[TL_PART_STATE_COUNT]={
    "normal","pressed","disabled","backdrop","hover","focus"
};
static const char *const relief_ids[]={"","flat","raised","sunken"};
int tl_part_relief_set(TLPartRecipe *part,int state,int relief) {
    if(!part || state<0 || state>=TL_PART_STATE_COUNT || relief < -1 || relief>3 || relief==0)return -1;
    if(relief==-1) {part->relief_present&=~(1u<<state);part->relief[state]=0;}
    else {part->relief_present|=1u<<state;part->relief[state]=relief;}
    return 0;
}
int tl_part_relief_validate(const TLPartRecipe *part) {
    if(!part || part->relief_present & ~((1u<<TL_PART_STATE_COUNT)-1))return -1;
    for(int state=0;state<TL_PART_STATE_COUNT;++state) {
        int value=part->relief[state];
        if(part->relief_present&(1u<<state)) {if(value<1 || value>3)return -1;}
        else if(value)return -1;
    }
    return 0;
}
int tl_part_relief_decode(TLPartRecipe *part,json_object *object) {
    if(!part || !json_object_is_type(object,json_type_object))return -1;
    TLPartRecipe candidate=*part;candidate.relief_present=0;
    memset(candidate.relief,0,sizeof(candidate.relief));
    json_object_object_foreach(object,key,value) {
        int state,relief;
        for(state=0;state<TL_PART_STATE_COUNT;++state)if(!strcmp(key,tl_part_state_ids[state]))break;
        if(state==TL_PART_STATE_COUNT || !json_object_is_type(value,json_type_string))return -1;
        const char *text=json_object_get_string(value);
        if((size_t)json_object_get_string_len(value)!=strlen(text))return -1;
        for(relief=1;relief<4;++relief)if(!strcmp(text,relief_ids[relief]))break;
        if(relief==4)return -1;
        tl_part_relief_set(&candidate,state,relief);
    }
    *part=candidate;return 0;
}
json_object *tl_part_relief_encode(const TLPartRecipe *part) {
    if(tl_part_relief_validate(part))return NULL;
    json_object *object=json_object_new_object();
    for(int state=0;state<TL_PART_STATE_COUNT;++state)if(part->relief_present&(1u<<state))
        json_object_object_add(object,tl_part_state_ids[state],json_object_new_string(relief_ids[part->relief[state]]));
    return object;
}
