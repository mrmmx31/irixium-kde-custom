/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "native_parts_motif.h"
#include <Xm/Xm.h>
#include <string.h>
#include <dlfcn.h>
/* Private structures are deliberately isolated from the portable View.
 * Different build/runtime versions fall back to unknown, not guessed offsets. */
#if XmVERSION == 2 && XmREVISION == 3 && XmUPDATE_LEVEL == 8
#include <Xm/ScrollBarP.h>
static int rectangle(TLNativeRect *out,int x,int y,int width,int height,int w,int h)
{
    if(x<0 || y<0 || width<1 || height<1 || x>w-width || y>h-height)return 0;
    *out=(TLNativeRect){x,y,width,height};
    return 1;
}
#endif
void tl_motif_parts_measure(Widget widget, TLNativePieces *out)
{
    if(!out)return;
    memset(out,0,sizeof(*out));
#if XmVERSION == 2 && XmREVISION == 3 && XmUPDATE_LEVEL == 8
    const char *version=dlsym(RTLD_DEFAULT,"_XmVersionString");
    if(!version || !widget || !XtIsRealized(widget) || !XtIsManaged(widget) ||
       XtClass(widget)!=xmScrollBarWidgetClass ||
       xmScrollBarClassRec.core_class.widget_size!=sizeof(XmScrollBarRec) ||
       strncmp(version,XmVERSION_STRING,sizeof(XmVERSION_STRING)))return;
    out->source=1;
    const XmScrollBarRec *bar=(const XmScrollBarRec *)widget;
    int w=bar->core.width,h=bar->core.height;
    const XmScrollBarPart *part=&bar->scrollBar;
    if(rectangle(&out->slider,part->slider_x,part->slider_y,
                 part->slider_width,part->slider_height,w,h))out->mask|=1;
    if(rectangle(&out->track,part->slider_area_x,part->slider_area_y,
                 part->slider_area_width,part->slider_area_height,w,h))out->mask|=2;
    if(part->show_arrows) {
        if(rectangle(&out->arrows[0],part->arrow1_x,part->arrow1_y,
                     part->arrow_width,part->arrow_height,w,h))out->mask|=4;
        if(rectangle(&out->arrows[1],part->arrow2_x,part->arrow2_y,
                     part->arrow_width,part->arrow_height,w,h))out->mask|=8;
    }
#else
    (void)widget;
#endif
}
