/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "ui_hints.h"
#include <X11/Shell.h>
#include <Xm/Label.h>
#include <stdlib.h>

/* Motif menu buttons do not post the ordinary primitive tooltip in this
 * runtime. Keep this bridge local to our editor menu, using public APIs.
 * No translation, grab, focus or editor callback is replaced. */
typedef struct {
    Widget menu, owner, shell, label;
    XtIntervalId delay, duration, watch;
} MenuHint;

static void hide(MenuHint *hint) {
    if(hint->delay){XtRemoveTimeOut(hint->delay);hint->delay=0;}
    if(hint->duration){XtRemoveTimeOut(hint->duration);hint->duration=0;}
    if(XtIsRealized(hint->shell))XtPopdown(hint->shell);
    XtVaSetValues(hint->label,XmNuserData,NULL,NULL);
    hint->owner=NULL;
}
static void expire(XtPointer data,XtIntervalId *id) {
    MenuHint *hint=data;(void)id;hint->duration=0;hide(hint);
}
static void appearance(Widget label,Widget owner) {
    XmFontList font;Pixel bg,fg,top,bottom;
    XtVaGetValues(owner,XmNfontList,&font,XmNbackground,&bg,XmNforeground,&fg,
        XmNtopShadowColor,&top,XmNbottomShadowColor,&bottom,NULL);
    XtVaSetValues(label,XmNfontList,font,XmNbackground,bg,XmNforeground,fg,
        XmNtopShadowColor,top,XmNbottomShadowColor,bottom,NULL);
    XtVaSetValues(XtParent(label),XmNbackground,bg,NULL);
}
void tl_ui_menu_hint_refresh(Widget menu) {
    Widget label=XtNameToWidget(menu,"*menuHintLabel"),owner=NULL;
    if(!label)return;
    XtVaGetValues(label,XmNuserData,&owner,NULL);
    if(owner)appearance(label,owner);
}
static int pointer_over_visible_owner(Widget menu,Widget owner) {
    if(!XtIsRealized(menu)||!XtIsRealized(owner))return 0;
    XWindowAttributes attributes;
    Display *display=XtDisplay(owner);
    if(!XGetWindowAttributes(display,XtWindow(menu),&attributes)||
        attributes.map_state!=IsViewable)return 0;
    if(!XGetWindowAttributes(display,XtWindow(owner),&attributes)||
        attributes.map_state!=IsViewable)return 0;
    Window root,child;int rx,ry,x,y;unsigned mask;
    return XQueryPointer(display,XtWindow(owner),&root,&child,&rx,&ry,&x,&y,&mask)&&
        x>=0&&y>=0&&x<attributes.width&&y<attributes.height;
}
static void post(XtPointer data,XtIntervalId *id) {
    MenuHint *hint=data;(void)id;hint->delay=0;
    Widget owner=hint->owner;
    if(!owner||!XtIsManaged(hint->menu)||
        !pointer_over_visible_owner(hint->menu,owner)){hide(hint);return;}
    XmString text=NULL;
    XtVaGetValues(owner,XmNtoolTipString,&text,NULL);
    if(!text)return;
    XtVaSetValues(hint->label,XmNlabelString,text,XmNuserData,owner,NULL);
    appearance(hint->label,owner);
    XtWidgetGeometry geometry={0};XtQueryGeometry(hint->label,NULL,&geometry);
    Position mx,my,ox,oy;Dimension mw,mh;
    XtTranslateCoords(hint->menu,0,0,&mx,&my);XtTranslateCoords(owner,0,0,&ox,&oy);
    XtVaGetValues(hint->menu,XmNwidth,&mw,XmNheight,&mh,NULL);
    int width=geometry.width,height=geometry.height;
    int sw=WidthOfScreen(XtScreen(owner)),sh=HeightOfScreen(XtScreen(owner));
    int x=mx+mw+6,y=oy;
    if(width>sw||height>sh)return;
    if(x+width>sw)x=mx-width-6;
    if(x<0){x=mx;y=my+mh+6;
        if(y+height>sh)y=my-height-6;
        if(y<0)return;
    }
    if(x+width>sw)x=sw-width;
    if(y+height>sh)y=sh-height;
    if(y<0)y=0;
    XtVaSetValues(hint->shell,XtNx,x,XtNy,y,XtNwidth,width,XtNheight,height,NULL);
    XtPopup(hint->shell,XtGrabNone);
    hint->duration=XtAppAddTimeOut(XtWidgetToApplicationContext(owner),6000,expire,hint);
}
static void crossing(Widget owner,XtPointer data,XEvent *event,Boolean *dispatch) {
    MenuHint *hint=data;(void)dispatch;
    if(event->type==EnterNotify||event->type==MotionNotify){
        /* Releasing the native menu grab can synthesize Enter after the
         * activation/unmap. It is not a new hover request. */
        if(event->type==EnterNotify&&event->xcrossing.mode==NotifyUngrab){hide(hint);return;}
        if(hint->owner==owner&&(hint->delay||hint->duration))return;
        hide(hint);hint->owner=owner;
        hint->delay=XtAppAddTimeOut(XtWidgetToApplicationContext(owner),750,post,hint);
    }else if(hint->owner==owner)hide(hint);
}
static void menu_motion(Widget menu,XtPointer data,XEvent *event,Boolean *dispatch) {
    MenuHint *hint=data;(void)dispatch;
    if(event->type==LeaveNotify){
        if(event->xcrossing.detail!=NotifyInferior)hide(hint);
        return;
    }
    if(event->type!=MotionNotify)return;
    Window root=None,child=None;int rx=0,ry=0,x=0,y=0;unsigned mask=0;
    if(!XQueryPointer(XtDisplay(menu),XtWindow(menu),&root,&child,&rx,&ry,&x,&y,&mask)||
        child==None){hide(hint);return;}
    Widget owner=XtWindowToWidget(XtDisplay(menu),child);
    if(!owner||XtParent(owner)!=menu){hide(hint);return;}
    if(hint->owner==owner&&(hint->delay||hint->duration))return;
    hide(hint);hint->owner=owner;
    hint->delay=XtAppAddTimeOut(XtWidgetToApplicationContext(owner),750,post,hint);
}
static void watch_pointer(XtPointer data,XtIntervalId *id) {
    MenuHint *hint=data;(void)id;hint->watch=0;
    if(!XtIsManaged(hint->menu)||!XtIsRealized(hint->menu))return;
    Window root=None,child=None;int rx=0,ry=0,x=0,y=0;unsigned mask=0;
    Widget owner=NULL;XmString text=NULL;
    if(XQueryPointer(XtDisplay(hint->menu),XtWindow(hint->menu),&root,&child,
        &rx,&ry,&x,&y,&mask)&&child!=None)
        owner=XtWindowToWidget(XtDisplay(hint->menu),child);
    if(!owner||XtParent(owner)!=hint->menu)owner=NULL;
    if(owner)XtVaGetValues(owner,XmNtoolTipString,&text,NULL);
    if(!text)owner=NULL;
    if(owner!=hint->owner){
        hide(hint);
        if(owner){
            hint->owner=owner;
            hint->delay=XtAppAddTimeOut(XtWidgetToApplicationContext(owner),750,post,hint);
        }
    }
    hint->watch=XtAppAddTimeOut(XtWidgetToApplicationContext(hint->menu),50,
        watch_pointer,hint);
}
static void mapped_menu(Widget w,XtPointer data,XtPointer call){
    MenuHint *hint=data;(void)w;(void)call;
    if(!hint->watch)hint->watch=XtAppAddTimeOut(
        XtWidgetToApplicationContext(hint->menu),1,watch_pointer,hint);
}
static void unmapped(Widget w,XtPointer data,XtPointer call){
    MenuHint *hint=data;(void)w;(void)call;
    if(hint->watch){XtRemoveTimeOut(hint->watch);hint->watch=0;}
    hide(hint);
}
static void destroyed(Widget w,XtPointer data,XtPointer call){
    MenuHint *hint=data;(void)w;(void)call;
    if(hint->delay)XtRemoveTimeOut(hint->delay);
    if(hint->duration)XtRemoveTimeOut(hint->duration);
    if(hint->watch)XtRemoveTimeOut(hint->watch);
    free(hint);
}
void tl_ui_menu_hints(Widget menu) {
    MenuHint *hint=calloc(1,sizeof(*hint));if(!hint)return;
    hint->menu=menu;
    hint->shell=XtVaCreatePopupShell("editorMenuHint",transientShellWidgetClass,menu,
        XtNoverrideRedirect,True,XtNallowShellResize,True,XtNinput,False,NULL);
    hint->label=XtVaCreateManagedWidget("menuHintLabel",xmLabelWidgetClass,hint->shell,
        XmNmarginWidth,4,XmNmarginHeight,4,XmNtraversalOn,False,NULL);
    WidgetList children=NULL;Cardinal count=0;
    XtVaGetValues(menu,XtNchildren,&children,XtNnumChildren,&count,NULL);
    for(Cardinal i=0;i<count;++i)
        /* Raw handlers keep the explanatory hover available while an action
         * is insensitive.  Activation remains blocked by Xt sensitivity; no
         * translation, callback or native menu grab is replaced. */
        XtAddRawEventHandler(children[i],EnterWindowMask|LeaveWindowMask|ButtonPressMask,
            False,crossing,hint);
    /* Motion selected on the parent receives propagation from an insensitive
     * child, for which Xt intentionally suppresses that child's handlers. */
    XtAddRawEventHandler(menu,PointerMotionMask|LeaveWindowMask,False,
        menu_motion,hint);
    XtAddCallback(menu,XmNmapCallback,mapped_menu,hint);
    XtAddCallback(menu,XmNunmapCallback,unmapped,hint);
    XtAddCallback(menu,XtNdestroyCallback,destroyed,hint);
}
