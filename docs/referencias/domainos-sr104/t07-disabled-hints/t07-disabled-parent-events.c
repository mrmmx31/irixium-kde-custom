#include <Xm/PushB.h>
#include <Xm/Form.h>
#include <stdio.h>
#include <stdlib.h>
static int normal,raw,parent_count,done,actions;
static void event(Widget w,XtPointer data,XEvent *e,Boolean *dispatch){(void)w;(void)dispatch;
 if(e->type==EnterNotify||e->type==LeaveNotify){++*(int*)data;printf("event=%d normal=%d raw=%d parent=%d mode=%d detail=%d\n",e->type,normal,raw,parent_count,e->xcrossing.mode,e->xcrossing.detail);}}
static void timeout(XtPointer p,XtIntervalId *id){*(int*)p=1;(void)id;}
static void action(Widget w,XtPointer p,XtPointer c){(void)w;(void)p;(void)c;++actions;}
int main(int argc,char **argv){XtAppContext app;Widget shell=XtVaAppInitialize(&app,"DisabledProbe",NULL,0,&argc,argv,NULL,XtNwidth,400,XtNheight,200,NULL);
 Widget form=XtVaCreateManagedWidget("form",xmFormWidgetClass,shell,NULL);
 Widget button=XtVaCreateManagedWidget("button",xmPushButtonWidgetClass,form,XtNx,100,XtNy,60,XtNwidth,160,XtNheight,40,NULL);
 XtAddEventHandler(form,EnterWindowMask|LeaveWindowMask|PointerMotionMask,False,event,&parent_count);
 XtAddEventHandler(button,EnterWindowMask|LeaveWindowMask|ButtonPressMask,False,event,&normal);
 XtAddRawEventHandler(button,EnterWindowMask|LeaveWindowMask|ButtonPressMask,False,event,&raw);
 XtAddCallback(button,XmNactivateCallback,action,NULL);XtSetSensitive(button,False);XtRealizeWidget(shell);
 XWarpPointer(XtDisplay(shell),None,DefaultRootWindow(XtDisplay(shell)),0,0,0,0,0,0);XFlush(XtDisplay(shell));
 XtAppAddTimeOut(app,100,timeout,&done);while(!done)XtAppProcessEvent(app,XtIMAll);done=0;
 Position x,y;XtTranslateCoords(button,80,20,&x,&y);XWarpPointer(XtDisplay(shell),None,DefaultRootWindow(XtDisplay(shell)),0,0,0,0,x,y);XFlush(XtDisplay(shell));
 XtAppAddTimeOut(app,950,timeout,&done);while(!done)XtAppProcessEvent(app,XtIMAll);
 printf("disabled button regular=%d raw=%d actions=%d sensitive=%d\n",normal,raw,actions,XtIsSensitive(button));
 XtDestroyWidget(shell);return 0;}
