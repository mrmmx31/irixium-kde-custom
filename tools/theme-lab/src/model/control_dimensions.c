/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "control_dimensions.h"
int tl_control_long_axis(int control)
{
    if(control == TL_CONTROL_SCROLL_HORIZONTAL) return 0;
    if(control == TL_CONTROL_SCROLL_VERTICAL) return 1;
    return -1;
}
int tl_control_edit_dimensions(TLRecipe *recipe, int control, int width, int height)
{
    int axis;
    if(!recipe || control < 0 || control >= TL_CONTROL_COUNT ||
       width < 0 || width > 2048 || height < 0 || height > 2048) return -1;
    axis=tl_control_long_axis(control);
    if((axis==0 && height!=recipe->sizes[control][1]) ||
       (axis==1 && width!=recipe->sizes[control][0])) return -1;
    recipe->sizes[control][0]=width;
    recipe->sizes[control][1]=height;
    return 0;
}

int tl_control_anchor_origin(const TLRecipe *recipe, int control,
                             int native_width, int native_height, int origin[2])
{
    int axis, x, y;
    if(!recipe || !origin || control<0 || control>=TL_CONTROL_COUNT ||
       native_width<1 || native_height<1) return -1;
    axis=tl_control_long_axis(control);
    x=recipe->positions[control][0];y=recipe->positions[control][1];
    if(recipe->length_anchor[control]==1) {
        if(axis==0)x-=native_width;
        else if(axis==1)y-=native_height;
        else return -1;
    } else if(recipe->length_anchor[control]!=0) return -1;
    if(x<0 || x>2048 || y<0 || y>2048)return -1;
    origin[0]=x;origin[1]=y;return 0;
}
int tl_control_set_anchor(TLRecipe *recipe, int control, int anchor, int native_length)
{
    int axis, origin[2], boundary;
    if(!recipe || (anchor!=0 && anchor!=1) || native_length<1 || native_length>2048) return -1;
    axis=tl_control_long_axis(control);
    if(axis<0)return -1;
    if(tl_control_anchor_origin(recipe,control,axis==0?native_length:1,
                               axis==1?native_length:1,origin))return -1;
    boundary=origin[axis]+(anchor?native_length:0);
    if(boundary>2048)return -1;
    recipe->positions[control][axis]=boundary;
    recipe->length_anchor[control]=anchor;
    return 0;
}
