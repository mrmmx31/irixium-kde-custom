/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Isolate the native drop-down-list input used by the laboratory. */
#include <Xm/ComboBox.h>
#include <stdio.h>
static void changed(Widget w,XtPointer unused,XtPointer call) {
    int selected=-1;XmComboBoxCallbackStruct *event=call;(void)unused;
    XtVaGetValues(w,XmNselectedPosition,&selected,NULL);
    printf("{\"event\":%d,\"selected\":%d}\n",event->item_position,selected);fflush(stdout);
}
int main(int argc,char **argv) {
    XtAppContext app;Widget shell=XtVaAppInitialize(&app,"ComboInput",NULL,0,&argc,argv,NULL,NULL);
    const char *labels[]={"Normal","Pressionado","Desabilitado","Backdrop"};XmString items[4];
    for(int i=0;i<4;i++)items[i]=XmStringCreateLocalized((char *)labels[i]);
    Widget combo=XtVaCreateManagedWidget("editState",xmComboBoxWidgetClass,shell,
        XmNcomboBoxType,XmDROP_DOWN_LIST,XmNpositionMode,XmZERO_BASED,
        XmNitems,items,XmNitemCount,4,XmNvisibleItemCount,4,XmNselectedPosition,0,NULL);
    for(int i=0;i<4;i++)XmStringFree(items[i]);
    XtAddCallback(combo,XmNselectionCallback,changed,NULL);XtRealizeWidget(shell);
    Position x,y;Dimension width,height,arrow;XtTranslateCoords(combo,0,0,&x,&y);
    XtVaGetValues(combo,XmNwidth,&width,XmNheight,&height,XmNarrowSize,&arrow,NULL);
    printf("{\"window\":%lu,\"x\":%d,\"y\":%d,\"width\":%u,\"height\":%u,\"arrow\":%u}\n",
           (unsigned long)XtWindow(shell),x,y,width,height,arrow);fflush(stdout);
    XtAppMainLoop(app);return 0;
}
