/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "ui_hints.h"
#include <X11/Shell.h>
#include <Xm/Label.h>
#include <Xm/SpinB.h>
#include <stdlib.h>

/* The SpinBox manager paints arrows rather than child primitives. Observe
 * only its own window, without replacing translations, grabs or callbacks. */
typedef struct {
    Widget spin,shell,label,source;
    XtIntervalId delay,duration;
    int hovering;
} SpinHint;
static void hide(SpinHint *h){
    if(h->delay){XtRemoveTimeOut(h->delay);h->delay=0;}
    if(h->duration){XtRemoveTimeOut(h->duration);h->duration=0;}
    if(XtIsRealized(h->shell))XtPopdown(h->shell);
}
static int over_arrows(Widget spin){
    if(!XtIsRealized(spin)||!XtIsManaged(spin)||!XtIsSensitive(spin))return 0;
    Display *d=XtDisplay(spin);XWindowAttributes a;
    if(!XGetWindowAttributes(d,XtWindow(spin),&a)||a.map_state!=IsViewable)return 0;
    Window root,child;int rx,ry,x,y;unsigned mask;
    return XQueryPointer(d,XtWindow(spin),&root,&child,&rx,&ry,&x,&y,&mask)&&
        child==None&&x>=0&&y>=0&&x<a.width&&y<a.height&&
        !(mask&(Button1Mask|Button2Mask|Button3Mask|Button4Mask|Button5Mask));
}
static void appearance(SpinHint *h){
    XmFontList fonts=NULL;Pixel bg,fg,top,bottom;
    XtVaGetValues(h->source,XmNfontList,&fonts,XmNbackground,&bg,XmNforeground,&fg,
        XmNtopShadowColor,&top,XmNbottomShadowColor,&bottom,NULL);
    XtVaSetValues(h->label,XmNfontList,fonts,XmNbackground,bg,XmNforeground,fg,
        XmNtopShadowColor,top,XmNbottomShadowColor,bottom,NULL);
    XtVaSetValues(h->shell,XtNbackground,bg,NULL);
}
static void expire(XtPointer data,XtIntervalId *id){SpinHint *h=data;(void)id;h->duration=0;hide(h);}
static void post(XtPointer data,XtIntervalId *id){
    SpinHint *h=data;(void)id;h->delay=0;
    if(!h->hovering||!over_arrows(h->spin)){hide(h);return;}
    XmString tip=NULL;XtVaGetValues(h->source,XmNtoolTipString,&tip,NULL);if(!tip)return;
    XtVaSetValues(h->label,XmNlabelString,tip,NULL);appearance(h);
    XtWidgetGeometry g={0};XtQueryGeometry(h->label,NULL,&g);
    Position ox,oy;Dimension ow,oh;XtTranslateCoords(h->spin,0,0,&ox,&oy);
    XtVaGetValues(h->spin,XtNwidth,&ow,XtNheight,&oh,NULL);
    int sw=WidthOfScreen(XtScreen(h->spin)),sh=HeightOfScreen(XtScreen(h->spin));
    int w=g.width,height=g.height,x=ox,y=oy+oh+6;
    if(w>sw||height>sh)return;
    if(y+height>sh)y=oy-height-6;
    if(y<0){x=ox+ow+6;y=oy;if(x+w>sw)x=ox-w-6;if(x<0)return;}
    if(x+w>sw)x=sw-w;
    if(x<0)x=0;
    if(y+height>sh)y=sh-height;
    if(!(x+w<=ox||x>=ox+ow||y+height<=oy||y>=oy+oh))return;
    XtVaSetValues(h->shell,XtNx,x,XtNy,y,XtNwidth,w,XtNheight,height,NULL);
    XtPopup(h->shell,XtGrabNone);
    h->duration=XtAppAddTimeOut(XtWidgetToApplicationContext(h->spin),6000,expire,h);
}
static void event(Widget widget,XtPointer data,XEvent *e,Boolean *dispatch){
    SpinHint *h=data;(void)widget;(void)dispatch;
    if(e->type==LeaveNotify||e->type==ButtonPress||e->type==UnmapNotify||
        (e->type==EnterNotify&&e->xcrossing.mode!=NotifyNormal)){
        h->hovering=0;hide(h);return;
    }
    if(e->type!=EnterNotify&&e->type!=MotionNotify)return;
    if(!over_arrows(h->spin)){h->hovering=0;hide(h);return;}
    if(!h->hovering){h->hovering=1;
        h->delay=XtAppAddTimeOut(XtWidgetToApplicationContext(h->spin),750,post,h);}
}
static void destroyed(Widget widget,XtPointer data,XtPointer call){
    SpinHint *h=data;(void)widget;(void)call;
    if(h->delay)XtRemoveTimeOut(h->delay);
    if(h->duration)XtRemoveTimeOut(h->duration);
    free(h);
}
void tl_ui_spin_hints(Widget spin){
    if(!XtIsSubclass(spin,xmSpinBoxWidgetClass)||XtNameToWidget(spin,"*spinArrowHintLabel"))return;
    WidgetList children=NULL;Cardinal count=0;Widget source=NULL;
    XtVaGetValues(spin,XtNchildren,&children,XtNnumChildren,&count,NULL);
    for(Cardinal i=0;i<count;++i)if(XmIsPrimitive(children[i])){
        XmString tip=NULL;XtVaGetValues(children[i],XmNtoolTipString,&tip,NULL);
        if(tip){source=children[i];break;}
    }
    if(!source)return;
    tl_ui_disabled_spin_hint(spin,source);
    SpinHint *h=calloc(1,sizeof(*h));if(!h)return;h->spin=spin;h->source=source;
    h->shell=XtVaCreatePopupShell("spinArrowHint",transientShellWidgetClass,spin,
        XtNoverrideRedirect,True,XtNallowShellResize,True,XtNinput,False,NULL);
    h->label=XtVaCreateManagedWidget("spinArrowHintLabel",xmLabelWidgetClass,h->shell,
        XmNmarginWidth,4,XmNmarginHeight,4,XmNtraversalOn,False,XmNuserData,h,NULL);
    XtAddEventHandler(spin,EnterWindowMask|LeaveWindowMask|PointerMotionMask|ButtonPressMask|StructureNotifyMask,
        False,event,h);
    XtAddCallback(spin,XtNdestroyCallback,destroyed,h);
}
void tl_ui_spin_hints_refresh(Widget tree){
    if(!tree)return;
    if(XtIsSubclass(tree,xmSpinBoxWidgetClass)){
        Widget label=XtNameToWidget(tree,"*spinArrowHintLabel");SpinHint *h=NULL;
        if(label){XtVaGetValues(label,XmNuserData,&h,NULL);if(h)appearance(h);}
    }
    if(XtIsComposite(tree)){
        WidgetList children=NULL;Cardinal count=0;
        XtVaGetValues(tree,XtNchildren,&children,XtNnumChildren,&count,NULL);
        for(Cardinal i=0;i<count;++i)tl_ui_spin_hints_refresh(children[i]);
    }
}
