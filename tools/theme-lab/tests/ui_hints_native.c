/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "ui_hints.h"
#include <Xm/ComboBox.h>
#include <Xm/Form.h>
#include <Xm/PushB.h>
#include <Xm/VendorS.h>
#include <Xm/RowColumn.h>
#include <Xm/Scale.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <locale.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"hint probe line %d\n",__LINE__);exit(1);}}while(0)
static void elapsed(XtPointer data,XtIntervalId *id){*(int*)data=1;(void)id;}
static void wait_ms(XtAppContext app,unsigned long ms){
    int done=0;XtAppAddTimeOut(app,ms,elapsed,&done);
    while(!done)XtAppProcessEvent(app,XtIMAll);
}
static int mapped(Widget w){
    XWindowAttributes a;
    return w&&XtIsRealized(w)&&XGetWindowAttributes(XtDisplay(w),XtWindow(w),&a)&&a.map_state==IsViewable;
}
static void point(Widget w,int x,int y){
    Position rx,ry;XtTranslateCoords(w,(Position)x,(Position)y,&rx,&ry);
    XWarpPointer(XtDisplay(w),None,DefaultRootWindow(XtDisplay(w)),0,0,0,0,rx,ry);
    XFlush(XtDisplay(w));
}
static int server_position(Widget w,int *x,int *y){
    Window child=None;
    return XtIsRealized(w)&&XTranslateCoordinates(XtDisplay(w),XtWindow(w),
        DefaultRootWindow(XtDisplay(w)),0,0,x,y,&child);
}
int main(int argc,char **argv){
    setlocale(LC_ALL,"");XtSetLanguageProc(NULL,NULL,NULL);
    XtAppContext app;
    Widget shell=XtVaAppInitialize(&app,"HintProbe",NULL,0,&argc,argv,NULL,NULL);
    int sw=WidthOfScreen(XtScreen(shell)),sh=HeightOfScreen(XtScreen(shell));
    XtVaSetValues(shell,XtNwidth,sw-20,XtNheight,sh-20,NULL);
    Widget form=XtVaCreateManagedWidget("form",xmFormWidgetClass,shell,NULL);
    Widget button=XtVaCreateManagedWidget("hintTarget",xmPushButtonWidgetClass,form,
        XmNx,sw-200,XmNy,sh-130,XmNwidth,150,XmNheight,40,NULL);
    tl_ui_hints_shell(shell);tl_ui_hint(button,tl_ui_action_hint(0));
    XtRealizeWidget(shell);point(form,0,0);wait_ms(app,100);
    Widget label=XmToolTipGetLabel(button);CHECK(label);
    point(button,20,20);wait_ms(app,400);CHECK(!mapped(label));
    wait_ms(app,550);CHECK(mapped(label));
    Position x,y;Dimension w,h;
    XtTranslateCoords(label,0,0,&x,&y);XtVaGetValues(label,XmNwidth,&w,XmNheight,&h,NULL);
    printf("tooltip=%d,%d %ux%u screen=%dx%d\n",x,y,w,h,sw,sh);fflush(stdout);
    CHECK(x>=0&&y>=0&&x+w<=sw&&y+h<=sh);
    Position bx,by;XtTranslateCoords(button,0,0,&bx,&by);
    CHECK(x+w<=bx||x>=bx+150||y+h<=by||y>=by+40);
    for(int i=0;i<4;++i){wait_ms(app,100);CHECK(mapped(label));}
    point(form,0,0);wait_ms(app,100);CHECK(!mapped(label));
    point(button,20,20);wait_ms(app,200);point(form,0,0);wait_ms(app,850);CHECK(!mapped(label));
    point(button,20,20);wait_ms(app,950);CHECK(mapped(label));
    point(form,0,0);wait_ms(app,100);CHECK(!mapped(label));
    for(int i=1;i<9;++i){
        tl_ui_hint(button,tl_ui_action_hint(i));wait_ms(app,800);
        point(button,20,20);wait_ms(app,950);CHECK(mapped(label));
        XtTranslateCoords(label,0,0,&x,&y);XtVaGetValues(label,XmNwidth,&w,XmNheight,&h,NULL);
        printf("action=%d tooltip=%d,%d %ux%u\n",i,x,y,w,h);fflush(stdout);
        CHECK(x>=0&&y>=0&&x+w<=sw&&y+h<=sh);
        CHECK(x+w<=bx||x>=bx+150||y+h<=by||y>=by+40);
        point(form,0,0);wait_ms(app,100);CHECK(!mapped(label));
    }
    tl_ui_hint(button,"Escolhe qual extremidade permanece fixa ao alterar o comprimento. A troca usa a medida nativa atual e preserva a posição. Disponível para barras Motif e GTK3; se há alterações pendentes, atualize a prévia primeiro.");
    wait_ms(app,800);point(button,20,20);wait_ms(app,950);CHECK(mapped(label));
    XtTranslateCoords(label,0,0,&x,&y);XtVaGetValues(label,XmNwidth,&w,XmNheight,&h,NULL);
    CHECK(x>=0&&y>=0&&x+w<=sw&&y+h<=sh);
    CHECK(x+w<=bx||x>=bx+150||y+h<=by||y>=by+40);
    CHECK(h>17);
    XmString tip=NULL;XtVaGetValues(button,XmNtoolTipString,&tip,NULL);CHECK(tip);
    char *text=XmStringUnparse(tip,NULL,XmCHARSET_TEXT,XmMULTIBYTE_TEXT,NULL,0,XmOUTPUT_ALL);
    /* Unparse without mappings omits compound-string separators. Geometry
       above verifies wrapping; this checks that the UTF-8 word survived. */
    CHECK(text&&strstr(text,"posição."));XtFree(text);
    point(form,0,0);wait_ms(app,100);CHECK(!mapped(label));
    Widget dimensions=XtVaCreateManagedWidget("dimensionScales",xmRowColumnWidgetClass,form,
        XmNx,20,XmNy,20,XmNwidth,sw-40,XmNorientation,XmVERTICAL,
        XmNpacking,XmPACK_TIGHT,XmNspacing,22,XmNmarginHeight,20,NULL);
    Widget width=XtVaCreateManagedWidget("width",xmScaleWidgetClass,dimensions,
        XmNorientation,XmHORIZONTAL,XmNminimum,8,XmNmaximum,512,
        XmNwidth,sw-60,XmNshowValue,True,NULL);
    Widget height=XtVaCreateManagedWidget("height",xmScaleWidgetClass,dimensions,
        XmNorientation,XmHORIZONTAL,XmNminimum,8,XmNmaximum,256,
        XmNwidth,sw-60,XmNshowValue,True,NULL);
    Widget preview=XtVaCreateManagedWidget("preview",xmPushButtonWidgetClass,form,
        XmNtopAttachment,XmATTACH_WIDGET,XmNtopWidget,dimensions,
        XmNleftAttachment,XmATTACH_FORM,XmNrightAttachment,XmATTACH_FORM,
        XmNheight,40,NULL);
    tl_ui_numeric_hint(width,"Largura da arte: 8-512 px; reduzir recorta, ampliar cria área vazia.");
    tl_ui_numeric_hint(height,"Altura da arte: 8-256 px; reduzir recorta, ampliar cria área vazia.");
    XtRealizeWidget(shell);point(form,0,0);wait_ms(app,100);
    point(width,20,20);wait_ms(app,950);
    label=XmToolTipGetLabel(width);CHECK(mapped(label));
    XtTranslateCoords(label,0,0,&x,&y);XtVaGetValues(label,XmNwidth,&w,XmNheight,&h,NULL);
    Position hx,hy;Dimension hw,hh;XtTranslateCoords(height,0,0,&hx,&hy);
    XtVaGetValues(height,XmNwidth,&hw,XmNheight,&hh,NULL);
    printf("width tooltip=%d,%d %ux%u next-scale=%d,%d %ux%u\n",x,y,w,h,hx,hy,hw,hh);fflush(stdout);
    CHECK(x+w<=hx||x>=hx+hw||y+h<=hy||y>=hy+hh);
    point(form,0,0);wait_ms(app,100);CHECK(!mapped(label));
    point(height,20,20);wait_ms(app,950);label=XmToolTipGetLabel(height);CHECK(mapped(label));
    XtTranslateCoords(label,0,0,&x,&y);XtVaGetValues(label,XmNwidth,&w,XmNheight,&h,NULL);
    XtTranslateCoords(preview,0,0,&bx,&by);XtVaGetValues(preview,XmNwidth,&hw,XmNheight,&hh,NULL);
    printf("height tooltip=%d,%d %ux%u preview=%d,%d %ux%u\n",x,y,w,h,bx,by,hw,hh);fflush(stdout);
    CHECK(x+w<=bx||x>=bx+hw||y+h<=by||y>=by+hh);
    point(form,0,0);wait_ms(app,100);CHECK(!mapped(label));
    XmString combo_items[2]={XmStringCreateLocalized("First"),
                              XmStringCreateLocalized("Second")};
    Widget combo=XtVaCreateManagedWidget("hintCombo",xmComboBoxWidgetClass,form,
        XmNcomboBoxType,XmDROP_DOWN_LIST,XmNitems,combo_items,XmNitemCount,2,
        XmNselectedPosition,0,XmNvisibleItemCount,2,
        XmNx,50,XmNy,sh/2,XmNwidth,180,XmNheight,35,NULL);
    XmStringFree(combo_items[0]);XmStringFree(combo_items[1]);
    tl_ui_hint(combo,"Escolhe a família do controle; a seleção preserva o texto da dica e a moldura inteira permanece clicável.");
    XtRealizeWidget(shell);point(form,0,0);wait_ms(app,100);
    Widget combo_text=XtNameToWidget(combo,"*Text");CHECK(combo_text);
    label=XmToolTipGetLabel(combo_text);CHECK(label);
    point(combo_text,10,10);wait_ms(app,1500);CHECK(mapped(label));
    int actual_x=0,actual_y=0;
    CHECK(server_position(label,&actual_x,&actual_y));
    XtVaGetValues(label,XmNwidth,&w,XmNheight,&h,NULL);
    Position cx,cy;Dimension cw,ch;XtTranslateCoords(combo,0,0,&cx,&cy);
    XtVaGetValues(combo,XtNwidth,&cw,XtNheight,&ch,NULL);
    printf("combo tooltip server=%d,%d %ux%u outer=%d,%d %ux%u\n",actual_x,actual_y,w,h,cx,cy,cw,ch);fflush(stdout);
    CHECK(actual_x>=0&&actual_y>=0&&actual_x+w<=sw&&actual_y+h<=sh);
    CHECK(actual_x+w<=cx||actual_x>=cx+cw||actual_y+h<=cy||actual_y>=cy+ch);
    XmString combo_tip=NULL;XtVaGetValues(combo_text,XmNtoolTipString,&combo_tip,NULL);CHECK(combo_tip);
    char *combo_text_tip=XmStringUnparse(combo_tip,NULL,XmCHARSET_TEXT,XmMULTIBYTE_TEXT,NULL,0,XmOUTPUT_ALL);
    CHECK(combo_text_tip&&strstr(combo_text_tip,"moldura inteira"));XtFree(combo_text_tip);
    point(form,0,0);wait_ms(app,100);CHECK(!mapped(label));
    puts("T07: delayed native hover, screen bounds, no owner overlap, stable display, leave and cancelled delay passed.");
    XtDestroyWidget(shell);return 0;
}
