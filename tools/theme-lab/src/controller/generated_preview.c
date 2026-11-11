/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "generated_preview.h"
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

static const char *text(json_object *object, const char *key) {
    json_object *value=NULL;
    return object && json_object_object_get_ex(object,key,&value) &&
           json_object_is_type(value,json_type_string) ? json_object_get_string(value) : NULL;
}

static bool gtk2_catalogue_controls_valid(json_object *entry,
                                         json_object *controls) {
    static const char *const catalogue[] = {
        "push", "toggle", "check", "radio", "entry", "combo", "spin",
        "text", "scale_h", "scale_v", "scroll_h", "scroll_v", "arrow",
        "progress", "list", "frame"
    };
    size_t count;
    int previous = -1;
    if (!json_object_is_type(controls, json_type_array)) return false;
    count = json_object_array_length(controls);
    if (count > sizeof(catalogue) / sizeof(catalogue[0])) return false;
    for (size_t i = 0; i < count; i++) {
        json_object *value = json_object_array_get_idx(controls, i);
        const char *name, *style_key = NULL, *style;
        int position = -1;
        if (!json_object_is_type(value, json_type_string)) return false;
        name = json_object_get_string(value);
        for (size_t n = 0; n < sizeof(catalogue) / sizeof(catalogue[0]); n++) {
            if (!strcmp(name, catalogue[n])) {
                position = (int)n;
                break;
            }
        }
        if (position <= previous) return false;
        previous = position;
        switch (position) {
        case 4: style_key = "entry_style_id"; break;
        case 5: style_key = "combo_style_id"; break;
        case 6: style_key = "spin_style_id"; break;
        case 7: style_key = "text_style_id"; break;
        case 8:
        case 9: style_key = "scale_style_id"; break;
        case 12: style_key = "arrow_style_id"; break;
        case 13: style_key = "progress_style_id"; break;
        case 14: style_key = "list_style_id"; break;
        case 15: style_key = "frame_style_id"; break;
        default: break;
        }
        if (style_key) {
            style = text(entry, style_key);
            if (!style || strlen(style) != 16 ||
                strspn(style, "0123456789abcdef") != 16)
                return false;
        }
    }
    return true;
}

int tl_generated_preview(json_object *root, TLFamily family,
                         const char *scene_hash, const char *generation_dir,
                         const char **path) {
    json_object *families=NULL,*entry=NULL,*applied=NULL,*controls=NULL;
    const char *hash=text(root,"project_sha256"),*candidate;
    char resolved[TL_PATH_MAX],base[TL_PATH_MAX]; struct stat info;
    if(!path)return -1;
    *path=NULL;
    if((family!=TL_GTK2&&family!=TL_GTK3&&family!=TL_GTK4)||!hash||strcmp(hash,scene_hash)||
       !json_object_object_get_ex(root,"families",&families)||
       !json_object_is_type(families,json_type_object)||
       !json_object_object_get_ex(families,tl_family_ids[family],&entry))return -1;
    if(family==TL_GTK3) {
        if(!json_object_object_get_ex(entry,"recipe_applied",&applied)||
           !json_object_is_type(applied,json_type_boolean)||!json_object_get_boolean(applied))return -1;
        candidate=text(entry,"theme_path");
    }else if(family==TL_GTK4) {
        const char *status=text(entry,"status"), *source=text(entry,"source_project_sha256"),
                   *saved=text(entry,"preview_project_sha256");
        const char *supported[]={"push","toggle","check"};
        bool seen_toggle=false,seen_check=false;
        if(!status||strcmp(status,"partially_generated")||
           !source||strcmp(source,scene_hash)||!saved||strlen(saved)!=64||
           strspn(saved,"0123456789abcdef")!=64||
           !json_object_object_get_ex(entry,"translated_controls",&controls)||
           !json_object_is_type(controls,json_type_array))return -1;
        size_t count=json_object_array_length(controls);
        if(count<1||count>3)return -1;
        int previous=-1;
        for(size_t i=0;i<count;i++) {
            json_object *control=json_object_array_get_idx(controls,i);
            if(!json_object_is_type(control,json_type_string))return -1;
            const char *name=json_object_get_string(control);int position=-1;
            for(int n=0;n<3;n++)if(!strcmp(name,supported[n])){position=n;break;}
            if(position<=previous)return -1;
            previous=position;
            if(position==1)seen_toggle=true;
            if(position==2)seen_check=true;
        }
        json_object *toggle=NULL,*check=NULL;
        if(!json_object_object_get_ex(entry,"private_toggle_session",&toggle)||
           !json_object_is_type(toggle,json_type_boolean)||json_object_get_boolean(toggle)!=seen_toggle)return -1;
        if(!json_object_object_get_ex(entry,"private_check_session",&check)||
           !json_object_is_type(check,json_type_boolean)||json_object_get_boolean(check)!=seen_check)return -1;
        candidate=text(entry,"snapshot");
    }else {
        const char *status=text(entry,"status");
        if(!status||strcmp(status,"partially_generated")||
           !json_object_object_get_ex(entry,"translated_controls",&controls)||
           !json_object_is_type(controls,json_type_array))return -1;
        /* New GTK2 receipts use scene_contract.CONTROLS order and may contain
         * any visible subset. Keep the legacy append-only form below readable
         * while old generated revisions are still open in the editor. */
        if (gtk2_catalogue_controls_valid(entry, controls)) {
            candidate=text(entry,"rc");
        } else {
        size_t length=json_object_array_length(controls);
        json_object *frame_tail=length?json_object_array_get_idx(controls,length-1):NULL;
        if(frame_tail&&json_object_is_type(frame_tail,json_type_string)&&
           !strcmp(json_object_get_string(frame_tail),"frame")) {
            const char *style=text(entry,"frame_style_id");
            if(!style||strlen(style)!=16||strspn(style,"0123456789abcdef")!=16)return -1;
            length--;
        }
        json_object *list_tail=length?json_object_array_get_idx(controls,length-1):NULL;
        if(list_tail&&json_object_is_type(list_tail,json_type_string)&&
           !strcmp(json_object_get_string(list_tail),"list")) {
            const char *style=text(entry,"list_style_id");
            if(!style||strlen(style)!=16||strspn(style,"0123456789abcdef")!=16)return -1;
            length--;
        }
        json_object *arrow_tail=length?json_object_array_get_idx(controls,length-1):NULL;
        if(arrow_tail&&json_object_is_type(arrow_tail,json_type_string)&&
           !strcmp(json_object_get_string(arrow_tail),"arrow")) {
            const char *style=text(entry,"arrow_style_id");
            if(!style||strlen(style)!=16||strspn(style,"0123456789abcdef")!=16)return -1;
            length--;
        }
        /* Optional scales share the generation-qualified native range style.
         * Remove in reverse canonical order; duplicates/unknown tails remain invalid. */
        for(int axis=1;axis>=0;axis--) {
            json_object *scale_tail=length?json_object_array_get_idx(controls,length-1):NULL;
            if(scale_tail&&json_object_is_type(scale_tail,json_type_string)&&
               !strcmp(json_object_get_string(scale_tail),axis?"scale_v":"scale_h")) {
                const char *style=text(entry,"scale_style_id");
                if(!style||strlen(style)!=16||strspn(style,"0123456789abcdef")!=16)return -1;
                length--;
            }
        }
        json_object *spin_tail=length?json_object_array_get_idx(controls,length-1):NULL;
        if(spin_tail&&json_object_is_type(spin_tail,json_type_string)&&
           !strcmp(json_object_get_string(spin_tail),"spin")) {
            const char *style=text(entry,"spin_style_id");
            if(!style||strlen(style)!=16||strspn(style,"0123456789abcdef")!=16)return -1;
            length--;
        }
        json_object *combo_tail=length?json_object_array_get_idx(controls,length-1):NULL;
        if(combo_tail&&json_object_is_type(combo_tail,json_type_string)&&
           !strcmp(json_object_get_string(combo_tail),"combo")) {
            const char *style=text(entry,"combo_style_id");
            if(!style||strlen(style)!=16||strspn(style,"0123456789abcdef")!=16)return -1;
            length--;
        }
        json_object *text_tail=length?json_object_array_get_idx(controls,length-1):NULL;
        if(text_tail&&json_object_is_type(text_tail,json_type_string)&&
           !strcmp(json_object_get_string(text_tail),"text")) {
            const char *style=text(entry,"text_style_id");
            if(!style||strlen(style)!=16||strspn(style,"0123456789abcdef")!=16)return -1;
            length--;
        }
        /* Entry is an optional, generation-qualified extension after progress. */
        json_object *tail=length?json_object_array_get_idx(controls,length-1):NULL;
        if(tail&&json_object_is_type(tail,json_type_string)&&
           !strcmp(json_object_get_string(tail),"entry")) {
            const char *style=text(entry,"entry_style_id");
            if(!style||strlen(style)!=16||strspn(style,"0123456789abcdef")!=16)return -1;
            length--;
        }
        /* Progress extends the same strict partial lists; never accepts a
         * missing renderer or a receipt without its generation style ID. */
        json_object *last=length?json_object_array_get_idx(controls,length-1):NULL;
        if(last&&json_object_is_type(last,json_type_string)&&
           !strcmp(json_object_get_string(last),"progress")) {
            const char *style=text(entry,"progress_style_id");
            if(!style||strlen(style)!=16||strspn(style,"0123456789abcdef")!=16)return -1;
            length--;
        }
        if(length!=2&&length!=3&&length!=4&&length!=5&&length!=6)return -1;
        const char *names[]={"push","scroll_h","scroll_v"};
        const char *expanded[]={"push","toggle","scroll_h","scroll_v"};
        const char *radio[]={"push","toggle","radio","scroll_h","scroll_v"};
        const char *check[]={"push","toggle","check","scroll_h","scroll_v"};
        const char *both[]={"push","toggle","check","radio","scroll_h","scroll_v"};
        json_object *third=json_object_array_get_idx(controls,2);
        const char **five=(third&&json_object_is_type(third,json_type_string)&&
                           !strcmp(json_object_get_string(third),"check"))?check:radio;
        for(size_t i=0;i<length;i++) {
            json_object *control=json_object_array_get_idx(controls,(size_t)i);
            if(!json_object_is_type(control,json_type_string)||
               strcmp(json_object_get_string(control),length==6?both[i]:length==5?five[i]:length==4?expanded[i]:names[i+(length==2?1:0)]))return -1;
        }
        candidate=text(entry,"rc");
        }
    }
    if(!candidate||strlen(candidate)>=TL_PATH_MAX||!realpath(candidate,resolved)||
       strcmp(candidate,resolved)||stat(resolved,&info)||
       (family==TL_GTK2?!S_ISREG(info.st_mode):!S_ISDIR(info.st_mode)))return -1;
    int count=snprintf(base,sizeof(base),"%s/revisions",generation_dir);
    if(count<0||(size_t)count>=sizeof(base)||strncmp(resolved,base,(size_t)count)||resolved[count]!='/')return -1;
    *path=candidate;return 0;
}
