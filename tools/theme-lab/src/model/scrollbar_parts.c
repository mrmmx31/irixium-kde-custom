/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "scrollbar_parts.h"
#include <stdio.h>
#include <string.h>
const char *const tl_scroll_part_ids[TL_SCROLL_PART_COUNT] = {
    "arrow", "arrow_button", "trough", "thumb", "fitting"
};
static const char *const fields[TL_SCROLL_PART_COUNT][TL_SCROLL_PARAM_COUNT] = {
    {"glyph_px", "shadow_px", NULL},
    {"padding_px", "shadow_px", NULL},
    {"thickness_px", "shadow_px", NULL},
    {"cross_px", "shadow_px", "gap_px"},
    {"gap_px", "inset_px", NULL}
};
const char *tl_scroll_part_field(TLScrollPart part, int field) {
    return (int)part >= 0 && part < TL_SCROLL_PART_COUNT && field >= 0 &&
           field < TL_SCROLL_PARAM_COUNT ? fields[part][field] : NULL;
}
static int error_out(char *error,size_t capacity,const char *text) {
    if(error && capacity)snprintf(error,capacity,"%s",text);
    return -1;
}
int tl_scroll_parts_set(TLScrollbarParts *parts, TLScrollPart part, int field, int value) {
    if(!parts || !tl_scroll_part_field(part,field) || value < -1 || value > 128)return -1;
    if(value == -1) {
        parts->parts[part].present &= ~(1U << field);
        parts->parts[part].values[field] = 0;
    } else {
        parts->parts[part].values[field] = value;
        parts->parts[part].present |= 1U << field;
    }
    return 0;
}
int tl_scroll_parts_any(const TLScrollbarParts *parts) {
    for(int p=0;p<TL_SCROLL_PART_COUNT;p++)if(parts->parts[p].present || parts->parts[p].relief_present)return 1;
    return 0;
}
int tl_scroll_parts_validate(const TLScrollbarParts *parts,char *error,size_t capacity) {
    if(!parts)return error_out(error,capacity,"Receitas de peças ausentes");
    for(int p=0;p<TL_SCROLL_PART_COUNT;p++) {
        if(tl_part_relief_validate(&parts->parts[p]))return error_out(error,capacity,"Estado/relevo de peça inválido");
        unsigned int allowed = fields[p][2] ? 7U : 3U;
        if(parts->parts[p].present & ~allowed)return error_out(error,capacity,"Campo de peça desconhecido");
        for(int f=0;f<TL_SCROLL_PARAM_COUNT;f++) {
            int value=parts->parts[p].values[f];
            if(parts->parts[p].present & (1U<<f)) {
                if(value < 0 || value > 128)return error_out(error,capacity,"Medida de peça fora de 0..128 px");
            } else if(value)return error_out(error,capacity,"Campo herdado contém valor oculto");
        }
    }
    return 0;
}
int tl_scroll_parts_decode(TLScrollbarParts *parts,json_object *object,char *error,size_t capacity) {
    TLScrollbarParts candidate = {0};
    if(!json_object_is_type(object,json_type_object))return error_out(error,capacity,"scrollbar_parts deve ser objeto");
    json_object_object_foreach(object,name,piece) {
        int p,f;
        for(p=0;p<TL_SCROLL_PART_COUNT;p++)if(!strcmp(name,tl_scroll_part_ids[p]))break;
        if(p==TL_SCROLL_PART_COUNT || !json_object_is_type(piece,json_type_object))
            return error_out(error,capacity,"Peça desconhecida ou inválida");
        json_object_object_foreach(piece,key,value) {
            if(!strcmp(key,"state_relief")) {
                if(tl_part_relief_decode(&candidate.parts[p],value))
                    return error_out(error,capacity,"Estado/relevo de peça desconhecido ou inválido");
                continue;
            }
            for(f=0;f<TL_SCROLL_PARAM_COUNT;f++)if(fields[p][f] && !strcmp(key,fields[p][f]))break;
            if(f==TL_SCROLL_PARAM_COUNT || !json_object_is_type(value,json_type_int) ||
               json_object_get_int64(value)<0 || json_object_get_int64(value)>128)
                return error_out(error,capacity,"Parâmetro de peça desconhecido ou inválido");
            tl_scroll_parts_set(&candidate,(TLScrollPart)p,f,json_object_get_int(value));
        }
    }
    *parts=candidate;
    return 0;
}
json_object *tl_scroll_parts_encode(const TLScrollbarParts *parts) {
    json_object *object=json_object_new_object();
    for(int p=0;p<TL_SCROLL_PART_COUNT;p++) {
        if(!parts->parts[p].present && !parts->parts[p].relief_present)continue;
        json_object *piece=json_object_new_object();
        for(int f=0;f<TL_SCROLL_PARAM_COUNT;f++)if(parts->parts[p].present & (1U<<f))
            json_object_object_add(piece,fields[p][f],json_object_new_int(parts->parts[p].values[f]));
        if(parts->parts[p].relief_present)
            json_object_object_add(piece,"state_relief",tl_part_relief_encode(&parts->parts[p]));
        json_object_object_add(object,tl_scroll_part_ids[p],piece);
    }
    return object;
}
