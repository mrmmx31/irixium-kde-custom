/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "ui_hints.h"
#include <X11/Shell.h>
#include <Xm/Label.h>
#include <Xm/Text.h>
#include <Xm/TextF.h>
#include <Xm/List.h>
#include <Xm/RowColumn.h>
#include <Xm/SpinB.h>
#include <stdlib.h>

/* Xt suppresses dispatch to insensitive primitives. Ancestor crossings
 * provide observation only; sensitivity and input dispatch are untouched. */
typedef struct {
    Widget owner,source,shell,label,ancestors[32];
    unsigned ancestors_count;
    XtIntervalId delay,duration,watch;
    int hovering,disabled_only;
} DisabledHint;
static void hide(DisabledHint *h){
    if(h->delay){XtRemoveTimeOut(h->delay);h->delay=0;}
    if(h->duration){XtRemoveTimeOut(h->duration);h->duration=0;}
    if(h->watch){XtRemoveTimeOut(h->watch);h->watch=0;}
    if(XtIsRealized(h->shell))XtPopdown(h->shell);
}
static int over(DisabledHint *h){
    Widget owner=h->owner;
    if((h->disabled_only&&XtIsSensitive(owner))||!XtIsManaged(owner)||!XtIsRealized(owner))return 0;
    Display *d=XtDisplay(owner);XWindowAttributes a;
    if(!XGetWindowAttributes(d,XtWindow(owner),&a)||a.map_state!=IsViewable)return 0;
    Window root,child;int rx,ry,x,y;unsigned mask;
    if(!XQueryPointer(d,XtWindow(owner),&root,&child,&rx,&ry,&x,&y,&mask)||
        x<0||y<0||x>=a.width||y>=a.height||
        (mask&(Button1Mask|Button2Mask|Button3Mask|Button4Mask|Button5Mask)))return 0;
    if(XtIsSubclass(owner,xmSpinBoxWidgetClass)&&child!=None)return 0;
    /* Confirm the actual pointer path, not just coordinates in an occluded
       window. All ancestors here are native widgets in this application. */
    for(Widget w=owner;!XtIsShell(w);w=XtParent(w)){
        Widget parent=XtParent(w);
        if(!parent||!XtIsRealized(parent)||!XQueryPointer(d,XtWindow(parent),
            &root,&child,&rx,&ry,&x,&y,&mask)||child!=XtWindow(w))return 0;
    }
    return 1;
}
static void appearance(DisabledHint *h){
    XmFontList font;Pixel bg,fg,top,bottom;
    XtVaGetValues(h->source,XmNfontList,&font,XmNbackground,&bg,XmNforeground,&fg,
        XmNtopShadowColor,&top,XmNbottomShadowColor,&bottom,NULL);
    XtVaSetValues(h->label,XmNfontList,font,XmNbackground,bg,XmNforeground,fg,
        XmNtopShadowColor,top,XmNbottomShadowColor,bottom,NULL);
    XtVaSetValues(h->shell,XtNbackground,bg,NULL);
}
static void watch(XtPointer data,XtIntervalId *id){
    DisabledHint *h=data;(void)id;h->watch=0;
    if(!over(h)){h->hovering=0;hide(h);return;}
    appearance(h);
    h->watch=XtAppAddTimeOut(XtWidgetToApplicationContext(h->owner),100,watch,h);
}
static void expire(XtPointer data,XtIntervalId *id){DisabledHint *h=data;(void)id;h->duration=0;hide(h);}
static void post(XtPointer data,XtIntervalId *id){
    DisabledHint *h=data;(void)id;h->delay=0;
    if(!h->hovering||!over(h)){h->hovering=0;hide(h);return;}
    XmString tip=NULL;XtVaGetValues(h->source,XmNtoolTipString,&tip,NULL);if(!tip)return;
    XtVaSetValues(h->label,XmNlabelString,tip,NULL);appearance(h);
    XtWidgetGeometry g={0};XtQueryGeometry(h->label,NULL,&g);
    Position ox,oy;Dimension ow,oh;XtTranslateCoords(h->owner,0,0,&ox,&oy);
    XtVaGetValues(h->owner,XtNwidth,&ow,XtNheight,&oh,NULL);
    int sw=WidthOfScreen(XtScreen(h->owner)),sh=HeightOfScreen(XtScreen(h->owner));
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
    h->duration=XtAppAddTimeOut(XtWidgetToApplicationContext(h->owner),6000,expire,h);
    h->watch=XtAppAddTimeOut(XtWidgetToApplicationContext(h->owner),100,watch,h);
}
static void crossing(Widget widget,XtPointer data,XEvent *e,Boolean *dispatch){
    DisabledHint *h=data;(void)widget;(void)dispatch;
    if(e->type!=EnterNotify&&e->type!=LeaveNotify&&e->type!=MotionNotify)return;
    if(!over(h)){h->hovering=0;hide(h);return;}
    if((e->type==EnterNotify||e->type==LeaveNotify)&&e->xcrossing.mode!=NotifyNormal)return;
    if(!h->hovering){h->hovering=1;
        h->delay=XtAppAddTimeOut(XtWidgetToApplicationContext(h->owner),750,post,h);}
}
static void destroyed(Widget widget,XtPointer data,XtPointer call){
    DisabledHint *h=data;(void)widget;(void)call;
    if(h->delay)XtRemoveTimeOut(h->delay);
    if(h->duration)XtRemoveTimeOut(h->duration);
    if(h->watch)XtRemoveTimeOut(h->watch);
    EventMask mask=EnterWindowMask|LeaveWindowMask;
    if(h->disabled_only)mask|=PointerMotionMask;
    for(unsigned i=0;i<h->ancestors_count;++i)XtRemoveEventHandler(h->ancestors[i],
        mask,False,crossing,h);
    free(h);
}
static void attach(Widget owner,Widget source,int disabled_only){
    const char *path=disabled_only?"disabledControlHint.disabledControlHintLabel":
                                   "surfaceHint.surfaceHintLabel";
    if(XtNameToWidget(owner,(char*)path))return;
    Widget parent=XtParent(owner);
    if(XmIsRowColumn(parent)){
        unsigned char type;XtVaGetValues(parent,XmNrowColumnType,&type,NULL);
        if(type==XmMENU_POPUP||type==XmMENU_PULLDOWN)return;
    }
    DisabledHint *h=calloc(1,sizeof(*h));if(!h)return;h->owner=owner;h->source=source;
    h->disabled_only=disabled_only;
    const char *shell_name=disabled_only?"disabledControlHint":"surfaceHint";
    const char *label_name=disabled_only?"disabledControlHintLabel":"surfaceHintLabel";
    h->shell=XtVaCreatePopupShell(shell_name,transientShellWidgetClass,owner,
        XtNoverrideRedirect,True,XtNallowShellResize,True,XtNinput,False,NULL);
    h->label=XtVaCreateManagedWidget(label_name,xmLabelWidgetClass,h->shell,
        XmNmarginWidth,4,XmNmarginHeight,4,XmNtraversalOn,False,NULL);
    Widget first=disabled_only?parent:owner;
    for(Widget w=first;w&&h->ancestors_count<32;w=XtParent(w)){
        h->ancestors[h->ancestors_count++]=w;
        EventMask mask=EnterWindowMask|LeaveWindowMask;
        if(disabled_only)mask|=PointerMotionMask;
        XtAddEventHandler(w,mask,False,crossing,h);
        if(XtIsShell(w))break;
    }
    XtAddCallback(owner,XtNdestroyCallback,destroyed,h);
}
void tl_ui_disabled_hint(Widget owner){
    if(XmIsLabel(owner)||XmIsText(owner)||XmIsTextField(owner)||XmIsList(owner))attach(owner,owner,1);
}
void tl_ui_disabled_spin_hint(Widget spin,Widget source){attach(spin,source,1);}
void tl_ui_surface_hint(Widget owner,Widget source){
    if(owner&&source)attach(owner,source,0);
}
