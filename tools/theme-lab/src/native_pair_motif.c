/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "native_pair_motif.h"
#include "control_dimensions.h"
#include <Xm/Xm.h>
#include <Xm/Form.h>
int tl_pair_physical_origin(const TLNativeMetrics *sample, int origin[2])
{
    if (!sample || !origin || sample->width<1 || sample->height<1 || !sample->position_valid || sample->scale_factor<1 ||
        sample->scale_factor>16 || sample->position_x<0 || sample->position_y<0 ||
        sample->position_x>2048/sample->scale_factor ||
        sample->position_y>2048/sample->scale_factor) return -1;
    origin[0]=sample->position_x*sample->scale_factor;
    origin[1]=sample->position_y*sample->scale_factor;
    return 0;
}
int tl_motif_pair_bars(Widget widgets[TL_CONTROL_COUNT], const TLRecipe *baseline,
                       int selected, const TLNativeMetrics samples[TL_CONTROL_COUNT])
{
    int result=0;
    if (!widgets || !baseline || !samples) return 0;
    for (int i=10;i<=11;++i) {
        Widget widget=widgets[i];
        Dimension width,height,parent_width,parent_height;
        Position x,y;
        int origin[2], paired=0;
        if (!widget || !XtIsManaged(widget)) continue;
        XtVaGetValues(widget,XmNwidth,&width,XmNheight,&height,XmNx,&x,XmNy,&y,NULL);
        if (i==selected && !tl_pair_physical_origin(&samples[i],origin)) paired=1;
        else if (tl_control_anchor_origin(baseline,i,width,height,origin)) continue;
        if (x!=origin[0] || y!=origin[1])
            XtVaSetValues(widget,XmNleftAttachment,XmATTACH_FORM,XmNtopAttachment,XmATTACH_FORM,
                          XmNleftOffset,origin[0],XmNtopOffset,origin[1],NULL);
        Boolean sensitive=True;
        if (paired && samples[i].sensitivity_known) sensitive=samples[i].sensitive?True:False;
        if (XtIsSensitive(widget)!=sensitive) XtVaSetValues(widget,XmNsensitive,sensitive,NULL);
        if (paired) {
            result=samples[i].sensitivity_known?2:1;
            /* The reference's natural/requested size remains independent. */
            Widget parent=XtParent(widget);
            XtVaGetValues(parent,XmNwidth,&parent_width,XmNheight,&parent_height,NULL);
            if ((unsigned)origin[0]+width+12>parent_width && (unsigned)origin[0]+width+12<=65535)
                XtVaSetValues(parent,XmNwidth,(Dimension)(origin[0]+width+12),NULL);
            if ((unsigned)origin[1]+height+12>parent_height && (unsigned)origin[1]+height+12<=65535)
                XtVaSetValues(parent,XmNheight,(Dimension)(origin[1]+height+12),NULL);
        }
    }
    return result;
}
