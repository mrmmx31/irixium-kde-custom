/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "control_catalog.h"
#include "ui_hints.h"
#include <Xm/RowColumn.h>
#include <Xm/PushB.h>
#include <Xm/ToggleB.h>
#include <stdio.h>

typedef struct {struct TLControlCatalog *catalog; int index, action;} Binding;
struct TLControlCatalog {
    Widget root, categories[TL_CATEGORY_COUNT], children[TL_CATEGORY_COUNT];
    Widget expanders[TL_CATEGORY_COUNT], controls[TL_CONTROL_COUNT];
    Binding category_bindings[TL_CATEGORY_COUNT][2], control_bindings[TL_CONTROL_COUNT][2];
    int expanded[TL_CATEGORY_COUNT];
    TLCatalogChanged changed; void *context;
};
static void label(Widget widget,const char *text) {
    XmString s=XmStringGenerate((XtPointer)text,NULL,XmMULTIBYTE_TEXT,NULL);
    XtVaSetValues(widget,XmNlabelString,s,NULL);XmStringFree(s);
}
static void clicked(Widget widget,XtPointer client,XtPointer call) {
    Binding *b=client;TLControlCatalog *c=b->catalog;(void)widget;(void)call;
    if(b->action==0) {
        c->expanded[b->index]=!c->expanded[b->index];
        if(c->expanded[b->index])XtManageChild(c->children[b->index]);
        else XtUnmanageChild(c->children[b->index]);
        label(c->expanders[b->index],c->expanded[b->index]?"-":"+");
    } else if(c->changed)c->changed(c->context,b->action==3?b->index:-1);
}
TLControlCatalog *tl_catalog_create(Widget parent,const char *const *categories,
    const char *const *controls,const int *membership,TLCatalogChanged changed,void *context) {
    TLControlCatalog *c=(TLControlCatalog *)XtCalloc(1,sizeof(*c));
    c->changed=changed;c->context=context;
    c->root=XtVaCreateManagedWidget("controlCatalog",xmRowColumnWidgetClass,parent,
        XmNorientation,XmVERTICAL,XmNpacking,XmPACK_TIGHT,NULL);
    for(int i=0;i<TL_CATEGORY_COUNT;i++) {
        char name[64];snprintf(name,sizeof(name),"catalogCategory%d",i);
        Widget group=XtVaCreateManagedWidget(name,xmRowColumnWidgetClass,c->root,
            XmNorientation,XmVERTICAL,XmNpacking,XmPACK_TIGHT,NULL);
        Widget row=XtVaCreateManagedWidget("categoryHeader",xmRowColumnWidgetClass,group,
            XmNorientation,XmHORIZONTAL,XmNpacking,XmPACK_TIGHT,NULL);
        snprintf(name,sizeof(name),"catalogExpand%d",i);
        c->expanders[i]=XtVaCreateManagedWidget(name,xmPushButtonWidgetClass,row,NULL);
        label(c->expanders[i],"-");c->expanded[i]=1;
        c->category_bindings[i][0]=(Binding){c,i,0};
        XtAddCallback(c->expanders[i],XmNactivateCallback,clicked,&c->category_bindings[i][0]);
        tl_ui_hint(c->expanders[i],"Expande ou recolhe esta categoria no catálogo; não altera a montagem ou a visibilidade dos controles.");
        snprintf(name,sizeof(name),"catalogCategoryCheck%d",i);
        c->categories[i]=XtVaCreateManagedWidget(name,xmToggleButtonWidgetClass,row,XmNset,True,NULL);
        label(c->categories[i],categories[i]);c->category_bindings[i][1]=(Binding){c,i,1};
        XtAddCallback(c->categories[i],XmNvalueChangedCallback,clicked,&c->category_bindings[i][1]);
        tl_ui_hint(c->categories[i],"Mostra ou oculta esta categoria na montagem; mantém escolhas individuais, receitas e posições.");
        c->children[i]=XtVaCreateManagedWidget("categoryChildren",xmRowColumnWidgetClass,group,
            XmNorientation,XmVERTICAL,XmNpacking,XmPACK_TIGHT,XmNmarginWidth,14,NULL);
        for(int j=0;j<TL_CONTROL_COUNT;j++)if(membership[j]==i) {
            Widget item=XtVaCreateManagedWidget("controlRow",xmRowColumnWidgetClass,c->children[i],
                XmNorientation,XmHORIZONTAL,XmNpacking,XmPACK_TIGHT,NULL);
            snprintf(name,sizeof(name),"catalogCheck%d",j);
            c->controls[j]=XtVaCreateManagedWidget(name,xmToggleButtonWidgetClass,item,XmNset,True,NULL);
            label(c->controls[j],"");c->control_bindings[j][0]=(Binding){c,j,2};
            XtAddCallback(c->controls[j],XmNvalueChangedCallback,clicked,&c->control_bindings[j][0]);
            tl_ui_hint(c->controls[j],"Ativa ou desativa este controle na montagem; mantém posição e receita e não muda o controle em edição.");
            snprintf(name,sizeof(name),"catalogControl%d",j);
            Widget select=XtVaCreateManagedWidget(name,xmPushButtonWidgetClass,item,NULL);
            label(select,controls[j]);c->control_bindings[j][1]=(Binding){c,j,3};
            /* Enter selects the focused member, without changing visibility. */
            XtOverrideTranslations(select,XtParseTranslationTable("<Key>Return: ArmAndActivate()"));
            XtAddCallback(select,XmNactivateCallback,clicked,&c->control_bindings[j][1]);
            tl_ui_hint(select,"Seleciona este controle para editar propriedades e posição; não altera seu checkbox de visibilidade.");
        }
    }
    return c;
}
void tl_catalog_update(TLControlCatalog *c,int categories,int controls) {
    for(int i=0;i<TL_CATEGORY_COUNT;i++)XmToggleButtonSetState(c->categories[i],(categories&(1<<i))!=0,False);
    for(int i=0;i<TL_CONTROL_COUNT;i++)XmToggleButtonSetState(c->controls[i],(controls&(1<<i))!=0,False);
}
void tl_catalog_read(const TLControlCatalog *c,int *categories,int *controls) {
    *categories=0;*controls=0;
    for(int i=0;i<TL_CATEGORY_COUNT;i++)if(XmToggleButtonGetState(c->categories[i]))*categories|=1<<i;
    for(int i=0;i<TL_CONTROL_COUNT;i++)if(XmToggleButtonGetState(c->controls[i]))*controls|=1<<i;
}
void tl_catalog_destroy(TLControlCatalog *c) {
    if(!c)return;
    XtDestroyWidget(c->root);XtFree((char *)c);
}
