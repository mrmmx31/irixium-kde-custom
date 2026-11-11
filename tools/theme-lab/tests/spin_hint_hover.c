/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "ui_hints.h"
#include <Xm/Form.h>
#include <Xm/SpinB.h>
#include <Xm/TextF.h>
#include <Xm/VendorS.h>
#include <locale.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"spin hint line %d\n",__LINE__);exit(1);}}while(0)
static void timer(XtPointer p,XtIntervalId *id){*(int*)p=1;(void)id;}
static void wait_ms(Widget w,unsigned long ms){int done=0;XtAppContext app=XtWidgetToApplicationContext(w);
    XtAppAddTimeOut(app,ms,timer,&done);while(!done)XtAppProcessEvent(app,XtIMAll);}
static int mapped(Widget w){XWindowAttributes a;return w&&XtIsRealized(w)&&
    XGetWindowAttributes(XtDisplay(w),XtWindow(w),&a)&&a.map_state==IsViewable;}
static void point(Widget spin,int x,int y){Position rx,ry;XtTranslateCoords(spin,x,y,&rx,&ry);
    XWarpPointer(XtDisplay(spin),None,DefaultRootWindow(XtDisplay(spin)),0,0,0,0,rx,ry);XFlush(XtDisplay(spin));}
static void mouse(const char *command){pid_t p=fork();CHECK(p>=0);if(!p){execl("/usr/bin/xdotool","xdotool",command,"1",(char*)NULL);_exit(127);}
    int status;CHECK(waitpid(p,&status,0)==p&&WIFEXITED(status)&&!WEXITSTATUS(status));}
static Pixel fixture_color(Widget w,const char *name){
    const char *value=getenv(name);char *end=NULL;CHECK(value&&*value);
    unsigned long rgb=strtoul(value,&end,16);CHECK(end&&!*end&&rgb<=0xffffff);
    XColor c={.red=((rgb>>16)&255)*257,.green=((rgb>>8)&255)*257,.blue=(rgb&255)*257};
    CHECK(XAllocColor(XtDisplay(w),DefaultColormapOfScreen(XtScreen(w)),&c));return c.pixel;
}
int main(int argc,char **argv){setlocale(LC_ALL,"");XtSetLanguageProc(NULL,NULL,NULL);
    XtAppContext app;Widget shell=XtVaAppInitialize(&app,"SpinHintProbe",NULL,0,&argc,argv,NULL,
        XmNwidth,650,XmNheight,300,NULL);
    Widget form=XtVaCreateManagedWidget("form",xmFormWidgetClass,shell,NULL);
    Widget spin=XtVaCreateManagedWidget("spin",xmSpinBoxWidgetClass,form,XmNx,100,XmNy,70,
        XmNarrowLayout,XmARROWS_END,XmNwrap,False,NULL);
    Widget field=XtVaCreateManagedWidget("value",xmTextFieldWidgetClass,spin,XmNcolumns,8,
        XmNspinBoxChildType,XmNUMERIC,XmNpositionType,XmPOSITION_VALUE,
        XmNminimumValue,0,XmNmaximumValue,100,XmNincrementValue,1,XmNposition,20,NULL);
    tl_ui_hints_shell(shell);tl_ui_numeric_hint(field,"Comprimento em pixels. 0 delega ao toolkit; use as setas para ajustar o pedido, sem alterar os demais controles.");
    if(getenv("TL_HINT_FACE")){
        Pixel bg=fixture_color(field,"TL_HINT_FACE"),fg=fixture_color(field,"TL_HINT_TEXT");
        XtVaSetValues(field,XmNbackground,bg,XmNforeground,fg,NULL);
    }
    XtRealizeWidget(shell);point(form,0,0);wait_ms(shell,850);
    Dimension width,height,arrow;XtVaGetValues(spin,XmNwidth,&width,XmNheight,&height,XmNarrowSize,&arrow,NULL);
    int x=width-arrow/2-2,y=height/2;
    point(spin,x,y);wait_ms(shell,400);
    Widget ordinary=XmToolTipGetLabel(shell),bridge=XtNameToWidget(spin,"*spinArrowHintLabel");
    CHECK(!mapped(ordinary)&&!mapped(bridge));wait_ms(shell,550);
    printf("Spin arrow hover: spin=%ux%u arrow=%u pointer=%d,%d nativeTip=%d bridgeTip=%d\n",
        width,height,arrow,x,y,mapped(ordinary),mapped(bridge));fflush(stdout);
    if(getenv("TL_EXPECT_NO_SPIN_HINT")){CHECK(!mapped(ordinary)&&!mapped(bridge));XtDestroyWidget(shell);return 0;}
    CHECK(mapped(bridge)&&!mapped(ordinary));
    Position ox,oy,tx,ty;Dimension tw,th;XtTranslateCoords(spin,0,0,&ox,&oy);
    XtTranslateCoords(bridge,0,0,&tx,&ty);XtVaGetValues(bridge,XmNwidth,&tw,XmNheight,&th,NULL);
    CHECK(tx>=0&&ty>=0&&tx+tw<=WidthOfScreen(XtScreen(shell))&&ty+th<=HeightOfScreen(XtScreen(shell)));
    CHECK(tx+tw<=ox||tx>=ox+width||ty+th<=oy||ty>=oy+height);
    wait_ms(shell,400);CHECK(mapped(bridge));
    Position xx,yy;XtTranslateCoords(bridge,0,0,&xx,&yy);CHECK(xx==tx&&yy==ty);
    Pixel bg,fg,tbg,tfg;XtVaGetValues(field,XmNbackground,&bg,XmNforeground,&fg,NULL);
    XtVaGetValues(bridge,XmNbackground,&tbg,XmNforeground,&tfg,NULL);CHECK(bg==tbg&&fg==tfg);
    /* A live role change refreshes the open hint without restarting its delay. */
    XtVaSetValues(field,XmNbackground,fg,XmNforeground,bg,NULL);tl_ui_spin_hints_refresh(form);
    wait_ms(shell,160);CHECK(mapped(bridge));
    XtVaGetValues(bridge,XmNbackground,&tbg,XmNforeground,&tfg,NULL);CHECK(fg==tbg&&bg==tfg);
    int before,after;XtVaGetValues(field,XmNposition,&before,NULL);mouse("click");wait_ms(shell,160);
    XtVaGetValues(field,XmNposition,&after,NULL);CHECK(after==before+1&&!mapped(bridge));
    point(form,0,0);wait_ms(shell,850);CHECK(!mapped(bridge));
    /* XmARROWS_END in this native layout stacks the two painted regions.
       The first point above is the increment region; the lower region
       remains outside the TextField window. */
    point(spin,x,height-arrow/2-2);wait_ms(shell,950);CHECK(mapped(bridge));
    before=after;mouse("click");wait_ms(shell,160);XtVaGetValues(field,XmNposition,&after,NULL);
    CHECK(after==before-1&&!mapped(bridge));
    point(spin,x,y);mouse("mousedown");wait_ms(shell,800);mouse("mouseup");wait_ms(shell,160);
    before=after;XtVaGetValues(field,XmNposition,&after,NULL);CHECK(after>before+1&&!mapped(bridge));
    wait_ms(shell,1100);CHECK(!mapped(bridge));
    point(form,0,0);wait_ms(shell,160);XtSetSensitive(spin,False);
    Widget targets[]={field,spin};
    for(int i=0;i<2;++i){
        Widget disabled=XtNameToWidget(targets[i],"disabledControlHint.disabledControlHintLabel");
        CHECK(disabled);Dimension fw,fh;
        XtVaGetValues(field,XmNwidth,&fw,XmNheight,&fh,NULL);
        if(i)point(spin,x,y);else point(field,fw/2,fh/2);
        wait_ms(shell,400);CHECK(!mapped(disabled));wait_ms(shell,550);
        CHECK(mapped(disabled)&&!mapped(bridge)&&!mapped(ordinary)&&!XtIsSensitive(field));
        before=after;mouse("click");wait_ms(shell,160);XtVaGetValues(field,XmNposition,&after,NULL);
        CHECK(after==before&&!XtIsSensitive(spin));
        point(form,0,0);wait_ms(shell,160);CHECK(!mapped(disabled));wait_ms(shell,850);
    }
    puts("Spin arrow delay, bounds, no overlap, stability, live roles, dismissal, native increment/decrement/repeat and no late hint passed.");
    puts("Disabled SpinBox field and painted arrow hints passed; clicks remain blocked and numeric value unchanged.");
    XtDestroyWidget(shell);return 0;
}
