/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "project_history_controls.h"
#include "ui_hints.h"
#include <Xm/RowColumn.h>
#include <Xm/PushB.h>
#include <X11/keysym.h>
#include <stdlib.h>
typedef struct {TLDispatch dispatch;void *context;TLAction action;} Binding;
static void destroy(Widget widget,XtPointer data,XtPointer call) {(void)widget;(void)call;free(data);}
static void activate(Widget widget,XtPointer data,XtPointer call) {
    Binding *b=data;(void)widget;(void)call;b->dispatch(b->context,b->action,0);
}
Widget tl_history_controls_create(Widget parent,TLDispatch dispatch,void *context) {
    static const char *names[]={"projectUndo","projectRedo","projectMark","projectRestore","projectResetPart"};
    static const char *labels[]={"Desfazer projeto","Refazer projeto","Guardar ponto","Voltar ao ponto","Resetar peça"};
    static const char *hints[]={
        "Desfaz o ajuste do projeto. Ctrl+Alt+Z no Motif. Ctrl+Z nos textos mantém seu Undo próprio. Atualizar aplica à prévia.",
        "Refaz o ajuste do projeto. Ctrl+Alt+Y no Motif. Ctrl+Y nos textos mantém seu Redo próprio. Atualizar aplica à prévia.",
        "Guarda o projeto atual como ponto de comparação persistente, independente da posição no histórico.",
        "Recupera o ponto de comparação como nova alteração recuperável; não aplica à prévia automaticamente.",
        "Remove somente os ajustes da peça selecionada, retomando a herança da família. Desfazer projeto recupera a peça."};
    static const TLAction actions[]={TL_PROJECT_UNDO,TL_PROJECT_REDO,TL_PROJECT_MARK,TL_PROJECT_RESTORE,TL_PROJECT_RESET_PART};
    Widget row=XtVaCreateManagedWidget("projectHistoryActions",xmRowColumnWidgetClass,parent,
        XmNorientation,XmHORIZONTAL,XmNpacking,XmPACK_COLUMN,XmNnumColumns,2,XmNspacing,5,NULL);
    for(int i=0;i<5;++i) {
        Binding *b=calloc(1,sizeof(*b));if(!b)abort();*b=(Binding){dispatch,context,actions[i]};
        XmString label=XmStringCreateLocalized((char*)labels[i]);
        Widget button=XtVaCreateManagedWidget(names[i],xmPushButtonWidgetClass,row,
            XmNlabelString,label,NULL);
        XmStringFree(label);tl_ui_hint(button,hints[i]);
        XtAddCallback(button,XmNactivateCallback,activate,b);XtAddCallback(button,XmNdestroyCallback,destroy,b);
    }
    return row;
}
void tl_history_controls_state(Widget row,int undo,int redo,int point) {
    XtSetSensitive(XtNameToWidget(row,"projectUndo"),undo);
    XtSetSensitive(XtNameToWidget(row,"projectRedo"),redo);
    XtSetSensitive(XtNameToWidget(row,"projectRestore"),point);
}
static void key(Widget widget,XtPointer data,XEvent *event,Boolean *cont) {
    Widget row=data;(void)widget;
    if(event->type!=KeyPress||(event->xkey.state&(ControlMask|Mod1Mask))!=(ControlMask|Mod1Mask))return;
    KeySym symbol=XLookupKeysym(&event->xkey,0);Widget button=NULL;
    if(symbol==XK_z)button=XtNameToWidget(row,event->xkey.state&ShiftMask?"projectRedo":"projectUndo");
    if(symbol==XK_y)button=XtNameToWidget(row,"projectRedo");
    if(button){*cont=False;if(XtIsSensitive(button))XtCallCallbacks(button,XmNactivateCallback,NULL);}
}
void tl_history_controls_watch(Widget tree,Widget row) {
    if(XtIsWidget(tree))XtAddEventHandler(tree,KeyPressMask,False,key,row);
    if(XtIsComposite(tree)) {
        WidgetList children=NULL;Cardinal count=0;
        XtVaGetValues(tree,XtNchildren,&children,XtNnumChildren,&count,NULL);
        for(Cardinal i=0;i<count;++i)tl_history_controls_watch(children[i],row);
    }
}
