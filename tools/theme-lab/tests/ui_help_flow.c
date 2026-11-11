/* SPDX-License-Identifier: GPL-3.0-or-later */
#include <Xm/Xm.h>
#include <Xm/Text.h>
#include <Xm/TextF.h>
#include <Xm/Protocols.h>
#include <Xm/List.h>
#include <Xm/FileSB.h>
#include <Xm/ScrolledW.h>
#include "theme_lab.h"
#include "ui_hints.h"
#include <Xm/VendorS.h>
#include <unistd.h>
#include <sys/wait.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"help flow line %d\n",__LINE__);exit(1);}}while(0)
static void timeout(XtPointer p,XtIntervalId *id){*(int*)p=1;(void)id;}
static void drain_app(XtAppContext app){int done=0;
    XtAppAddTimeOut(app,160,timeout,&done);while(!done)XtAppProcessEvent(app,XtIMAll);}
static void drain(Widget w){drain_app(XtWidgetToApplicationContext(w));}
static void run(char *const argv[]){
    pid_t pid=fork();CHECK(pid>=0);
    if(!pid){execv("/usr/bin/xdotool",argv);_exit(127);}
    int status;CHECK(waitpid(pid,&status,0)==pid&&WIFEXITED(status)&&!WEXITSTATUS(status));
}
static Widget find(Widget shell,const char *name){Widget w=XtNameToWidget(shell,(char*)name);CHECK(w);return w;}
static void click(Widget w,int right){
    XtAppContext app=XtWidgetToApplicationContext(w);
    Dimension width,height;Position x,y;char sx[32],sy[32];
    CHECK(XtIsRealized(w));XtVaGetValues(w,XmNwidth,&width,XmNheight,&height,NULL);
    if(XmIsGadget(w)){
        XtTranslateCoords(w,right?width-8:width/2,height/2,&x,&y);
    }else{
        Window child=None;int root_x=0,root_y=0;
        CHECK(XTranslateCoordinates(XtDisplay(w),XtWindow(w),DefaultRootWindow(XtDisplay(w)),
                                    right?width-8:width/2,height/2,&root_x,&root_y,&child));
        x=(Position)root_x;y=(Position)root_y;
    }
    snprintf(sx,sizeof(sx),"%d",x);snprintf(sy,sizeof(sy),"%d",y);
    /* Activation may destroy the clicked dialog. Keep only its live app
       context while draining the queued native events. */
    char *args[]={"xdotool","mousemove",sx,sy,"click","1",NULL};run(args);drain_app(app);
}
static void choose(Widget w,int index){
    click(w,1);
    Widget list=NULL;XtVaGetValues(w,XmNlist,&list,NULL);CHECK(list&&XtIsRealized(list));
    Position lx,ly,x,y;Dimension width,height;char sx[32],sy[32];
    CHECK(XmListPosToBounds(list,index+1,&lx,&ly,&width,&height));
    XtTranslateCoords(list,lx+width/2,ly+height/2,&x,&y);
    snprintf(sx,sizeof(sx),"%d",x);snprintf(sy,sizeof(sy),"%d",y);
    char *args[]={"xdotool","mousemove",sx,sy,"click","1",NULL};run(args);drain(w);
    int selected=-1;XtVaGetValues(w,XmNselectedPosition,&selected,NULL);
    fprintf(stderr,"Combo %s requested=%d selected=%d\n",XtName(w),index,selected);
}
static int mapped(Widget w){XWindowAttributes a;return XtIsRealized(w)&&XGetWindowAttributes(XtDisplay(w),XtWindow(w),&a)&&a.map_state==IsViewable;}
static void wait_ms(Widget w,unsigned long ms){int done=0;
    XtAppContext app=XtWidgetToApplicationContext(w);
    XtAppAddTimeOut(app,ms,timeout,&done);while(!done)XtAppProcessEvent(app,XtIMAll);}
static void count_activation(Widget widget,XtPointer data,XtPointer call){
    (void)widget;(void)call;++*(int*)data;
}
void tl_test_history_hover(TLView *view,Widget shell){
    const char *names[]={"*projectUndo","*projectRedo","*projectMark",
        "*projectRestore","*projectResetPart"};
    Widget area=find(shell,"*recipeScroll"),tip=XmToolTipGetLabel(shell);
    CHECK(tip);tl_view_history_state(view,1,1,1);
    for(size_t i=0;i<sizeof(names)/sizeof(*names);++i){
        Widget owner=find(shell,names[i]);
        XmScrollVisible(area,owner,4,4);wait_ms(shell,160);
        Position ox,oy,tx,ty;Dimension ow,oh,tw,th;
        XtTranslateCoords(owner,0,0,&ox,&oy);
        XtVaGetValues(owner,XmNwidth,&ow,XmNheight,&oh,NULL);
        XWarpPointer(XtDisplay(shell),None,DefaultRootWindow(XtDisplay(shell)),0,0,0,0,0,0);
        XFlush(XtDisplay(shell));wait_ms(shell,850);CHECK(!mapped(tip));
        XWarpPointer(XtDisplay(shell),None,DefaultRootWindow(XtDisplay(shell)),0,0,0,0,ox+ow/2,oy+oh/2);
        XFlush(XtDisplay(shell));wait_ms(shell,400);CHECK(!mapped(tip));
        wait_ms(shell,550);CHECK(mapped(tip));
        XtTranslateCoords(tip,0,0,&tx,&ty);
        XtVaGetValues(tip,XmNwidth,&tw,XmNheight,&th,NULL);
        CHECK(tx>=0&&ty>=0&&tx+tw<=WidthOfScreen(XtScreen(shell))&&ty+th<=HeightOfScreen(XtScreen(shell)));
        CHECK(tx+tw<=ox||tx>=ox+ow||ty+th<=oy||ty>=oy+oh);
        wait_ms(shell,400);CHECK(mapped(tip));
        Position x,y;XtTranslateCoords(tip,0,0,&x,&y);CHECK(x==tx&&y==ty);
        printf("History hover %s owner=%d,%d %ux%u tip=%d,%d %ux%u delay400 stable400 passed\n",
            XtName(owner),ox,oy,ow,oh,tx,ty,tw,th);
        XWarpPointer(XtDisplay(shell),None,DefaultRootWindow(XtDisplay(shell)),0,0,0,0,0,0);
        XFlush(XtDisplay(shell));wait_ms(shell,160);CHECK(!mapped(tip));
    }
    tl_view_history_state(view,0,0,0);
    Widget undo=find(shell,names[0]);XmString hint=NULL;
    XtVaGetValues(undo,XmNtoolTipString,&hint,NULL);CHECK(!XtIsSensitive(undo)&&hint);
    Position x,y;Dimension w,h;XtTranslateCoords(undo,0,0,&x,&y);
    XtVaGetValues(undo,XmNwidth,&w,XmNheight,&h,NULL);
    XWarpPointer(XtDisplay(shell),None,DefaultRootWindow(XtDisplay(shell)),0,0,0,0,x+w/2,y+h/2);
    XFlush(XtDisplay(shell));wait_ms(shell,400);
    Widget bridge=XtNameToWidget(undo,"*disabledControlHintLabel");CHECK(bridge&&!mapped(bridge));
    wait_ms(shell,550);CHECK(mapped(bridge)&&!mapped(tip)&&!XtIsSensitive(undo));
    Position bx,by;Dimension bw,bh;XtTranslateCoords(bridge,0,0,&bx,&by);
    XtVaGetValues(bridge,XmNwidth,&bw,XmNheight,&bh,NULL);
    CHECK(bx>=0&&by>=0&&bx+bw<=WidthOfScreen(XtScreen(shell))&&by+bh<=HeightOfScreen(XtScreen(shell)));
    CHECK(bx+bw<=x||bx>=x+w||by+bh<=y||by>=y+h);
    wait_ms(shell,400);CHECK(mapped(bridge));
    int activations=0;XtAddCallback(undo,XmNactivateCallback,count_activation,&activations);
    click(undo,0);CHECK(!activations&&!XtIsSensitive(undo));
    XtRemoveCallback(undo,XmNactivateCallback,count_activation,&activations);
    XWarpPointer(XtDisplay(shell),None,DefaultRootWindow(XtDisplay(shell)),0,0,0,0,0,0);
    XFlush(XtDisplay(shell));wait_ms(shell,160);CHECK(!mapped(bridge));
    printf("History disabled Undo: delayed bridge, bounds/non-overlap, stable400, click blocked and leave passed\n");
}
static void file_hover(Widget dialog){
    const unsigned char tags[]={XmDIALOG_FILTER_TEXT,XmDIALOG_TEXT,
        XmDIALOG_CANCEL_BUTTON,XmDIALOG_APPLY_BUTTON};
    Display *display=XtDisplay(dialog);Widget tip=XmToolTipGetLabel(XtParent(dialog));
    CHECK(tip);
    for(size_t i=0;i<sizeof(tags);++i){
        Widget owner=XmFileSelectionBoxGetChild(dialog,tags[i]);CHECK(owner);
        Position ox,oy,tx,ty;Dimension ow,oh,tw,th;
        XtTranslateCoords(owner,0,0,&ox,&oy);
        XtVaGetValues(owner,XmNwidth,&ow,XmNheight,&oh,NULL);
        XWarpPointer(display,None,DefaultRootWindow(display),0,0,0,0,0,0);
        XFlush(display);wait_ms(dialog,850);CHECK(!mapped(tip));
        XWarpPointer(display,None,DefaultRootWindow(display),0,0,0,0,ox+ow/2,oy+oh/2);
        XFlush(display);wait_ms(dialog,400);CHECK(!mapped(tip));
        wait_ms(dialog,550);CHECK(mapped(tip));
        XtTranslateCoords(tip,0,0,&tx,&ty);
        XtVaGetValues(tip,XmNwidth,&tw,XmNheight,&th,NULL);
        CHECK(tx>=0&&ty>=0&&tx+tw<=WidthOfScreen(XtScreen(dialog))&&ty+th<=HeightOfScreen(XtScreen(dialog)));
        CHECK(tx+tw<=ox||tx>=ox+ow||ty+th<=oy||ty>=oy+oh);
        wait_ms(dialog,400);CHECK(mapped(tip));
        Position x,y;XtTranslateCoords(tip,0,0,&x,&y);CHECK(x==tx&&y==ty);
        printf("File hover child=%u owner=%d,%d %ux%u tip=%d,%d %ux%u delay400 stable400 passed\n",
            tags[i],ox,oy,ow,oh,tx,ty,tw,th);
        XWarpPointer(display,None,DefaultRootWindow(display),0,0,0,0,0,0);
        XFlush(display);wait_ms(dialog,160);CHECK(!mapped(tip));
    }
}
static void expect(Widget text,const char *fragment){char *s=XmTextGetString(text);
    if(!s||!strstr(s,fragment))fprintf(stderr,"Expected: %s\nActual: %s\n",fragment,s?s:"(null)");
    CHECK(s&&strstr(s,fragment));XtFree(s);}
static int make_clipboard_capture(char *path,size_t capacity){
    const char *directory=getenv("TMPDIR");
    if(!directory||!*directory){
        const char *home=getenv("HOME");
        if(!home||!*home)return -1;
        if(snprintf(path,capacity,"%s/tempia/theme-lab-help-clipboard.XXXXXX",home)>=(int)capacity)return -1;
    }else if(snprintf(path,capacity,"%s/theme-lab-help-clipboard.XXXXXX",directory)>=(int)capacity)return -1;
    return mkstemp(path);
}
static void copied(Widget w,const char *expected){
    char path[4096];int fd=make_clipboard_capture(path,sizeof(path));CHECK(fd>=0);
    pid_t pid=fork();CHECK(pid>=0);
    if(!pid){CHECK(dup2(fd,STDOUT_FILENO)>=0);close(fd);
        execl("/usr/bin/xclip","xclip","-selection","clipboard","-o",(char*)NULL);_exit(127);}
    close(fd);int status=0,finished=0;
    for(int i=0;i<20;++i){drain(w);pid_t p=waitpid(pid,&status,WNOHANG);CHECK(p>=0);if(p==pid){finished=1;break;}}
    if(!finished){kill(pid,SIGTERM);waitpid(pid,&status,0);}CHECK(finished&&WIFEXITED(status)&&!WEXITSTATUS(status));
    FILE *f=fopen(path,"rb");CHECK(f);char output[4096];size_t n=fread(output,1,sizeof(output)-1,f);
    output[n]=0;CHECK(!ferror(f)&&fgetc(f)==EOF);fclose(f);
    if(strcmp(output,expected))fprintf(stderr,"Clipboard mismatch\nExpected: %s\nActual: %s\n",expected,output);
    CHECK(!strcmp(output,expected));CHECK(!unlink(path));
}
void tl_test_help_native(Widget shell){
    Widget cascade=find(shell,"*helpCascade"),item=find(shell,"*helpTopic2");
    Widget dialog=find(shell,"*laboratoryHelp"),text=find(shell,"*helpText");
    Widget field=find(shell,"*modelNameRow*fieldValue");char *original=XmTextFieldGetString(field);
    CHECK(original&&!mapped(dialog));
    /* Let the WM finish mapping/reparenting the shell before translating the
       first click into root coordinates. The popup item is translated only
       after the cascade has positioned its menu shell. */
    wait_ms(shell,700);click(cascade,0);wait_ms(shell,250);click(item,0);
    CHECK(mapped(dialog));
    Boolean editable=True;XtVaGetValues(text,XmNeditable,&editable,NULL);CHECK(!editable);
    expect(text,"Pedido, mínimo, natural");
    Widget level=find(shell,"*helpLevelCombo");choose(level,2);expect(text,"Comparar pedido/mínimo");
    choose(level,0);expect(text,"px significa pixel");
    choose(find(shell,"*helpTopicCombo"),4);expect(text,"Um papel é uma função");
    choose(level,1);expect(text,"sufixo breeze");
    click(text,0);char *all[]={"xdotool","key","ctrl+a",NULL};run(all);drain(text);
    char *selection=XmTextGetSelection(text),*body=XmTextGetString(text);CHECK(selection&&!strcmp(selection,body));
    XtFree(selection);
    char *copy[]={"xdotool","key","ctrl+c",NULL};run(copy);drain(text);
    copied(text,body);
    char *blocked[]={"xdotool","key","ctrl+x","ctrl+v",NULL};run(blocked);drain(text);
    char *unchanged=XmTextGetString(text);CHECK(unchanged&&!strcmp(unchanged,body));XtFree(unchanged);XtFree(body);
    click(find(shell,"*closeHelp"),0);CHECK(!mapped(dialog));
    click(cascade,0);click(find(shell,"*helpTopic7"),0);CHECK(mapped(dialog));expect(text,"Amostra contém");
    XEvent message={0};message.xclient.type=ClientMessage;message.xclient.display=XtDisplay(shell);
    message.xclient.window=XtWindow(XtParent(dialog));message.xclient.format=32;
    message.xclient.message_type=XmInternAtom(XtDisplay(shell),"WM_PROTOCOLS",False);
    message.xclient.data.l[0]=(long)XmInternAtom(XtDisplay(shell),"WM_DELETE_WINDOW",False);
    message.xclient.data.l[1]=CurrentTime;
    CHECK(XSendEvent(XtDisplay(shell),message.xclient.window,False,NoEventMask,&message));XFlush(XtDisplay(shell));drain(shell);
    CHECK(!mapped(dialog));click(cascade,0);click(item,0);CHECK(mapped(dialog));expect(text,"Pedido, mínimo");
    char *after=XmTextFieldGetString(field);CHECK(after&&!strcmp(after,original));XtFree(after);XtFree(original);
    puts("T07 help: native menu, three levels, topic selection, read-only select/copy, close/reopen and WM close/reopen; project field preserved.");
}
typedef struct {int count;char path[4096];} Chosen;
void tl_test_export_review_native(TLView *view,Widget shell){
    const char *report="Exportação — proposta e cena salva\nPacote: /fixture/PACKAGE\nNenhum tema instalado.\nSão Paulo — ação.\n";
    Widget project=find(shell,"*modelNameRow*fieldValue");char *original=XmTextFieldGetString(project);
    tl_view_export_review(view,report);drain(shell);
    Widget dialog=find(shell,"*exportReview"),field=find(shell,"*exportReviewText"),notes=find(shell,"*notesText");
    CHECK(mapped(dialog));Boolean editable=True;XtVaGetValues(field,XmNeditable,&editable,NULL);CHECK(!editable);
    char *body=XmTextGetString(field);CHECK(body&&!strcmp(body,report));XtFree(body);
    Pixel fg,bg,nfg,nbg;XtVaGetValues(field,XmNforeground,&fg,XmNbackground,&bg,NULL);
    XtVaGetValues(notes,XmNforeground,&nfg,XmNbackground,&nbg,NULL);CHECK(fg==nfg&&bg==nbg);
    click(field,0);char *all[]={"xdotool","key","ctrl+a",NULL};run(all);drain(field);
    char *selection=XmTextGetSelection(field);CHECK(selection&&!strcmp(selection,report));XtFree(selection);
    char *copy[]={"xdotool","key","ctrl+c",NULL};run(copy);drain(field);copied(field,report);
    char *blocked[]={"xdotool","key","ctrl+x","ctrl+v","ctrl+z","ctrl+y",NULL};run(blocked);drain(field);
    body=XmTextGetString(field);CHECK(body&&!strcmp(body,report));XtFree(body);
    Pixel pixels[6];XtVaGetValues(dialog,XmNbackground,&pixels[0],XmNtopShadowColor,&pixels[4],XmNbottomShadowColor,&pixels[5],NULL);
    pixels[1]=fg;pixels[2]=bg;pixels[3]=fg;unsigned short rgb[6][3];
    for(int i=0;i<6;++i){XColor color={.pixel=pixels[i]};XQueryColor(XtDisplay(shell),DefaultColormapOfScreen(XtScreen(shell)),&color);
        rgb[i][0]=color.red;rgb[i][1]=color.green;rgb[i][2]=color.blue;}
    for(int i=0;i<3;++i){unsigned short old=rgb[0][i];rgb[0][i]=rgb[1][i];rgb[1][i]=old;}
    tl_view_palette(view,(const unsigned short (*)[3])rgb);drain(field);
    XtVaGetValues(field,XmNforeground,&fg,XmNbackground,&bg,NULL);
    XtVaGetValues(notes,XmNforeground,&nfg,XmNbackground,&nbg,NULL);CHECK(fg==nfg&&bg==nbg);
    body=XmTextGetString(field);CHECK(body&&!strcmp(body,report));XtFree(body);
    click(find(shell,"*closeExportReview"),0);CHECK(!mapped(dialog));
    tl_view_export_review(view,"Novo relatório — sem substituir ajustes.");drain(shell);CHECK(mapped(dialog));
    expect(field,"Novo relatório");
    XEvent message={0};message.xclient.type=ClientMessage;message.xclient.display=XtDisplay(shell);
    message.xclient.window=XtWindow(XtParent(dialog));message.xclient.format=32;
    message.xclient.message_type=XmInternAtom(XtDisplay(shell),"WM_PROTOCOLS",False);
    message.xclient.data.l[0]=(long)XmInternAtom(XtDisplay(shell),"WM_DELETE_WINDOW",False);
    message.xclient.data.l[1]=CurrentTime;
    CHECK(XSendEvent(XtDisplay(shell),message.xclient.window,False,NoEventMask,&message));XFlush(XtDisplay(shell));drain(shell);
    CHECK(!mapped(dialog));tl_view_export_review(view,report);drain(shell);CHECK(mapped(dialog));
    click(find(shell,"*closeExportReview"),0);
    char *after=XmTextFieldGetString(project);CHECK(after&&!strcmp(original,after));XtFree(after);XtFree(original);
    puts("T08 export review: UTF-8 report, real select/copy, read-only cut/paste/undo/redo, dynamic UI roles, native close/reopen; project field preserved.");
}
static void chosen(void *data,const char *path){Chosen *c=data;++c->count;snprintf(c->path,sizeof(c->path),"%s",path);}
static void expect_field(Widget field,const char *expected){char *s=XmTextFieldGetString(field);
    if(!s||strcmp(s,expected))fprintf(stderr,"Field expected: %s\nField actual: %s\n",expected,s?s:"(null)");
    CHECK(s&&!strcmp(s,expected));XtFree(s);}
static void trace_crossing(Widget w,XtPointer data,XEvent *event,Boolean *dispatch){
    (void)data;(void)dispatch;
    if(event->type==EnterNotify||event->type==LeaveNotify)
        fprintf(stderr,"Editor crossing widget=%s type=%d mode=%d detail=%d root=%d,%d\n",
            XtName(w),event->type,event->xcrossing.mode,event->xcrossing.detail,
            event->xcrossing.x_root,event->xcrossing.y_root);
}
static void post_editor_menu(Widget field){
    if(getenv("TL_EDITOR_MOUSE")){
        char *down[]={"xdotool","mousedown","3",NULL};run(down);drain(field);
        char *up[]={"xdotool","mouseup","3",NULL};run(up);drain(field);return;
    }
    /* Use the existing keyboard posting gesture to isolate tooltip hover
     * from the posting-button traversal/dismissal investigated separately. */
    char *menu[]={"xdotool","key","shift+F10",NULL};run(menu);drain(field);
}
static void editor_hover(TLView *view,Widget field,Widget menu,Widget command,const char *expected){
    Widget tip=XtNameToWidget(menu,"*menuHintLabel");CHECK(tip);
    Position ox,oy,tx,ty;Dimension ow,oh,tw,th;
    XtTranslateCoords(command,0,0,&ox,&oy);
    XtVaGetValues(command,XmNwidth,&ow,XmNheight,&oh,NULL);
    Display *display=XtDisplay(field);
    if(getenv("TL_EDITOR_TRACE")){
        XtAddRawEventHandler(command,EnterWindowMask|LeaveWindowMask,False,trace_crossing,NULL);
        XtAddRawEventHandler(menu,EnterWindowMask|LeaveWindowMask,False,trace_crossing,NULL);
    }
    /* Ensure a real cold crossing even if posting placed the menu beneath
     * the existing pointer. Keep the menu grab and translations native. */
    XWarpPointer(display,None,DefaultRootWindow(display),0,0,0,0,0,0);
    XFlush(display);wait_ms(field,850);
    if(getenv("TL_EDITOR_TRACE")){
        Window root,child;int rx,ry,cx,cy;unsigned mask;
        CHECK(XQueryPointer(display,XtWindow(command),&root,&child,&rx,&ry,&cx,&cy,&mask));
        fprintf(stderr,"Editor cold observed menu=%d tip=%d pointer=%d,%d local=%d,%d\n",
            mapped(menu),mapped(tip),rx,ry,cx,cy);
    }
    if(!mapped(menu)||mapped(tip))fprintf(stderr,"Editor cold crossing: menu=%d tip=%d owner=%d,%d %ux%u\n",mapped(menu),mapped(tip),ox,oy,ow,oh);
    CHECK(mapped(menu)&&!mapped(tip));
    XWarpPointer(display,None,DefaultRootWindow(display),0,0,0,0,ox+ow/2,oy+oh/2);
    XFlush(display);wait_ms(field,400);CHECK(!mapped(tip));
    wait_ms(field,700);CHECK(mapped(tip));
    Pixel owner_fg,owner_bg,tip_fg,tip_bg;
    XtVaGetValues(command,XmNforeground,&owner_fg,XmNbackground,&owner_bg,NULL);
    XtVaGetValues(tip,XmNforeground,&tip_fg,XmNbackground,&tip_bg,NULL);
    CHECK(tip_fg==owner_fg&&tip_bg==owner_bg);
    XtTranslateCoords(tip,0,0,&tx,&ty);XtVaGetValues(tip,XmNwidth,&tw,XmNheight,&th,NULL);
    CHECK(tx>=0&&ty>=0&&tx+tw<=WidthOfScreen(XtScreen(field))&&ty+th<=HeightOfScreen(XtScreen(field)));
    CHECK(tx+tw<=ox||tx>=ox+ow||ty+th<=oy||ty>=oy+oh);
    wait_ms(field,400);CHECK(mapped(tip));
    Position x,y;XtTranslateCoords(tip,0,0,&x,&y);CHECK(x==tx&&y==ty);
    if(getenv("TL_EDITOR_LIVE_PALETTE")){
        XColor colors[2]={{0}};colors[0].pixel=owner_fg;colors[1].pixel=owner_bg;
        Colormap map;XtVaGetValues(field,XmNcolormap,&map,NULL);
        CHECK(XQueryColors(display,map,colors,2));
        unsigned short rgb[6][3];
        for(int i=0;i<6;++i){XColor *c=&colors[i==1||i==3||i==4];
            rgb[i][0]=c->red;rgb[i][1]=c->green;rgb[i][2]=c->blue;}
        XmTextPosition before_start,before_end,after_start,after_end;
        CHECK(XmTextFieldGetSelectionPosition(field,&before_start,&before_end));
        tl_view_palette(view,rgb);wait_ms(field,160);
        CHECK(mapped(menu)&&mapped(tip));
        XtVaGetValues(command,XmNforeground,&owner_fg,XmNbackground,&owner_bg,NULL);
        CHECK(owner_fg!=tip_fg&&owner_bg!=tip_bg);
        XtVaGetValues(tip,XmNforeground,&tip_fg,XmNbackground,&tip_bg,NULL);
        CHECK(tip_fg==owner_fg&&tip_bg==owner_bg);
        XtTranslateCoords(tip,0,0,&x,&y);CHECK(x==tx&&y==ty);
        CHECK(XmTextFieldGetSelectionPosition(field,&after_start,&after_end));
        CHECK(before_start==after_start&&before_end==after_end);
        puts("Editor live palette: visible menu/tip update roles without moving or losing selection.");
    }
    expect_field(field,expected);
    printf("Editor hover Copy: owner=%d,%d %ux%u tip=%d,%d %ux%u fg=%lu bg=%lu delay400 stable400 passed\n",ox,oy,ow,oh,tx,ty,tw,th,tip_fg,tip_bg);
    click(command,0);
    CHECK(!mapped(menu));CHECK(!mapped(tip));
    expect_field(field,expected);copied(field,expected);
    /* Grab-release crossing must not resurrect a hint after activation. */
    wait_ms(field,1100);CHECK(!mapped(menu)&&!mapped(tip));
    if(getenv("TL_EDITOR_TRACE")){
        XtRemoveRawEventHandler(command,EnterWindowMask|LeaveWindowMask,False,trace_crossing,NULL);
        XtRemoveRawEventHandler(menu,EnterWindowMask|LeaveWindowMask,False,trace_crossing,NULL);
    }
}
void tl_test_file_dialog_native(TLView *view,Widget shell){
    char directory[]="/tmp/theme-lab-file-dialog.XXXXXX",mask[4096];CHECK(mkdtemp(directory));
    snprintf(mask,sizeof(mask),"%s/*",directory);Chosen result={0};
    tl_view_choose_file(view,"Teste seletor — dados artificiais",mask,chosen,&result);drain(shell);
    Widget dialog=find(shell,"*chooseRecipeFile");
    const unsigned char tags[]={XmDIALOG_FILTER_TEXT,XmDIALOG_FILTER_LABEL,XmDIALOG_DIR_LIST,
        XmDIALOG_DIR_LIST_LABEL,XmDIALOG_FILE_LIST,XmDIALOG_FILE_LIST_LABEL,XmDIALOG_TEXT,
        XmDIALOG_SELECTION_LABEL,XmDIALOG_OK_BUTTON,XmDIALOG_CANCEL_BUTTON,XmDIALOG_APPLY_BUTTON};
    for(size_t i=0;i<sizeof(tags);++i){
        Widget w=XmFileSelectionBoxGetChild(dialog,tags[i]);XmString tip=NULL;CHECK(w);
        XtVaGetValues(w,XmNtoolTipString,&tip,NULL);CHECK(tip);
    }
    Widget field=XmFileSelectionBoxGetChild(dialog,XmDIALOG_TEXT);CHECK(field);
    if(getenv("TL_FILE_HOVER"))file_hover(dialog);
    char *initial=XmTextFieldGetString(field),updated[4096];CHECK(initial);
    snprintf(updated,sizeof(updated),"%sABC",initial);click(field,0);
    /* Set the fixture insertion point explicitly: this isolated X server
       does not establish a desktop virtual-key binding for End. Navigation
       shortcuts are outside this dialog-hints/palette regression. */
    XmTextFieldSetInsertionPosition(field,XmTextFieldGetLastPosition(field));
    CHECK(XmTextFieldGetInsertionPosition(field)==(XmTextPosition)strlen(initial));
    char *type[]={"xdotool","type","--clearmodifiers","ABC",NULL};run(type);drain(field);expect_field(field,updated);
    char *undo[]={"xdotool","key","ctrl+z","ctrl+z","ctrl+z",NULL};run(undo);drain(field);expect_field(field,initial);
    char *redo[]={"xdotool","key","ctrl+y","ctrl+y","ctrl+y",NULL};run(redo);drain(field);expect_field(field,updated);
    if(getenv("TL_EDITOR_HOVER")){
        char *select[]={"xdotool","key","ctrl+a",NULL};run(select);drain(field);
        post_editor_menu(field);
        Widget menu=find(field,"*textEditMenu");WidgetList commands=NULL;Cardinal count=0;
        XtVaGetValues(menu,XmNchildren,&commands,XmNnumChildren,&count,NULL);CHECK(count==6);
        editor_hover(view,field,menu,commands[2],updated);click(field,0);
    }
    /* Artificial runtime role fixture; product never stores these colours. */
    unsigned short rgb[6][3]={{11000,17000,23000},{62000,61000,60000},
        {4000,8000,12000},{50000,42000,19000},{40000,46000,51000},{1000,3000,5000}};
    Pixel before_fg,before_bg,after_fg,after_bg;
    XtVaGetValues(field,XmNforeground,&before_fg,XmNbackground,&before_bg,NULL);
    tl_view_palette(view,rgb);drain(field);expect_field(field,updated);
    XtVaGetValues(field,XmNforeground,&after_fg,XmNbackground,&after_bg,NULL);
    CHECK(after_fg!=before_fg&&after_bg!=before_bg);
    Widget tip=XmToolTipGetLabel(XtParent(dialog));CHECK(tip);
    Pixel tip_fg;XtVaGetValues(tip,XmNforeground,&tip_fg,NULL);CHECK(tip_fg==after_fg);
    run(undo);drain(field);expect_field(field,initial);run(redo);drain(field);expect_field(field,updated);
    char *all[]={"xdotool","key","ctrl+a",NULL};run(all);drain(field);
    char *copy[]={"xdotool","key","ctrl+c",NULL};run(copy);drain(field);copied(field,updated);
    char *cut[]={"xdotool","key","ctrl+x",NULL};run(cut);drain(field);expect_field(field,"");
    char *paste[]={"xdotool","key","ctrl+v",NULL};run(paste);drain(field);expect_field(field,updated);
    if(getenv("TL_EDITOR_HOVER")){run(all);drain(field);}
    post_editor_menu(field);
    Widget menu=XtNameToWidget(field,"*textEditMenu");CHECK(menu);
    WidgetList commands=NULL;Cardinal count=0;
    XtVaGetValues(menu,XmNchildren,&commands,XmNnumChildren,&count,NULL);CHECK(count==6);
    for(Cardinal i=0;i<count;++i){XmString hint=NULL;
        XtVaGetValues(commands[i],XmNtoolTipString,&hint,NULL);CHECK(hint&&tl_ui_editor_command_hint((int)i));}
    if(getenv("TL_EDITOR_HOVER")){
        editor_hover(view,field,menu,commands[2],updated);
        /* Copy already closes the menu. Reopen before the existing Escape
         * test, otherwise Escape cancels and destroys the file dialog. */
        click(field,0);post_editor_menu(field);
        CHECK(mapped(menu));
    }
    char *escape[]={"xdotool","key","Escape",NULL};run(escape);drain(field);expect_field(field,updated);
    click(XmFileSelectionBoxGetChild(dialog,XmDIALOG_CANCEL_BUTTON),0);CHECK(!result.count);
    CHECK(!XtNameToWidget(shell,"*chooseRecipeFile"));
    tl_view_choose_file(view,"Confirmação fictícia — sem escrita de arquivo",mask,chosen,&result);drain(shell);
    dialog=find(shell,"*chooseRecipeFile");field=XmFileSelectionBoxGetChild(dialog,XmDIALOG_TEXT);
    char *expected=XmTextFieldGetString(field);CHECK(expected);
    click(XmFileSelectionBoxGetChild(dialog,XmDIALOG_OK_BUTTON),0);
    CHECK(result.count==1&&!strcmp(result.path,expected));XtFree(expected);XtFree(initial);
    CHECK(!XtNameToWidget(shell,"*chooseRecipeFile"));CHECK(!rmdir(directory));
    puts("T07 file dialog: 11 native child hints, six editing-menu hints, runtime palette preserves input/Undo/Redo, copy/cut/paste, cancel and confirm callbacks passed.");
}
