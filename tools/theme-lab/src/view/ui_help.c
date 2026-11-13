/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "ui_help.h"
#include "help_topics.h"
#include "ui_hints.h"
#include <Xm/Form.h>
#include <Xm/RowColumn.h>
#include <Xm/CascadeB.h>
#include <Xm/PushB.h>
#include <Xm/ComboBox.h>
#include <Xm/Text.h>
#include <stdlib.h>
#include <stdio.h>
typedef struct {struct TLHelp *help;int topic;} Binding;
struct TLHelp {
    Widget menu,popup,dialog,topic_combo,level_combo,text;
    int topic,level;
    Binding bindings[TL_HELP_TOPIC_COUNT];
};
static XmString string(const char *s){return XmStringGenerate((XtPointer)s,NULL,XmMULTIBYTE_TEXT,NULL);}
static void refresh(TLHelp *h){
    const char *body=tl_help_topic_text(h->topic,h->level);
    if(!body)return;
    XmTextSetString(h->text,(char*)body);XmTextSetTopCharacter(h->text,0);
}
static void select_topic(Widget w,XtPointer data,XtPointer call){
    TLHelp *h=data;int value=-1;(void)call;
    XtVaGetValues(w,XmNselectedPosition,&value,NULL);
    if(value>=0&&value<TL_HELP_TOPIC_COUNT){h->topic=value;refresh(h);}
}
static void select_level(Widget w,XtPointer data,XtPointer call){
    TLHelp *h=data;int value=-1;(void)call;
    XtVaGetValues(w,XmNselectedPosition,&value,NULL);
    if(value>=0&&value<TL_HELP_LEVEL_COUNT){h->level=value;refresh(h);}
}
static void open_topic(Widget w,XtPointer data,XtPointer call){
    Binding *b=data;TLHelp *h=b->help;(void)w;(void)call;
    h->topic=b->topic;
    XtRemoveCallback(h->topic_combo,XmNselectionCallback,select_topic,h);
    XtVaSetValues(h->topic_combo,XmNselectedPosition,h->topic,NULL);
    XtAddCallback(h->topic_combo,XmNselectionCallback,select_topic,h);
    refresh(h);XtManageChild(h->dialog);
}
static void close_help(Widget w,XtPointer data,XtPointer call){
    (void)w;(void)call;XtUnmanageChild(((TLHelp*)data)->dialog);
}
static Widget combo(Widget parent,const char *name,int count,int topic){
    XmString entries[TL_HELP_TOPIC_COUNT];
    for(int i=0;i<count;++i)entries[i]=string(topic?tl_help_topic_title(i):tl_help_level_title(i));
    Widget result=XtVaCreateManagedWidget(name,xmComboBoxWidgetClass,parent,
        XmNcomboBoxType,XmDROP_DOWN_LIST,XmNpositionMode,XmZERO_BASED,
        XmNitems,entries,XmNitemCount,count,XmNvisibleItemCount,count,
        XmNselectedPosition,topic?0:1,NULL);
    for(int i=0;i<count;++i)XmStringFree(entries[i]);
    return result;
}
TLHelp *tl_help_create(Widget parent,Widget shell){
    TLHelp *h=calloc(1,sizeof(*h));if(!h)return NULL;h->level=1;
    h->menu=XmCreateMenuBar(parent,"laboratoryHelpMenu",NULL,0);
    Widget popup=XmCreatePulldownMenu(h->menu,"helpTopics",NULL,0);
    h->popup=popup;
    XmString label=string("Ajuda");
    Widget cascade=XtVaCreateManagedWidget("helpCascade",xmCascadeButtonWidgetClass,h->menu,
        XmNlabelString,label,XmNsubMenuId,popup,XmNmnemonic,'A',NULL);XmStringFree(label);
    XtVaSetValues(h->menu,XmNmenuHelpWidget,cascade,NULL);
    tl_ui_hint(cascade,"Ajuda do laboratório: finalidade, medidas e limites, com níveis novice, intermediate e expert. Não altera o projeto.");
    for(int i=0;i<TL_HELP_TOPIC_COUNT;++i){
        label=string(tl_help_topic_title(i));char name[32];
        snprintf(name,sizeof(name),"helpTopic%d",i);
        Widget item=XtVaCreateManagedWidget(name,xmPushButtonWidgetClass,popup,XmNlabelString,label,NULL);
        XmStringFree(label);h->bindings[i]=(Binding){h,i};
        XtAddCallback(item,XmNactivateCallback,open_topic,&h->bindings[i]);
        tl_ui_hint(item,"Abre este assunto na ajuda, com o nível de explicação escolhido. Não altera o projeto, a montagem ou as prévias.");
    }
    h->dialog=XmCreateFormDialog(shell,"laboratoryHelp",NULL,0);
    XtVaSetValues(h->dialog,XmNdialogStyle,XmDIALOG_MODELESS,XmNautoUnmanage,False,
        XmNwidth,740,XmNheight,440,XmNmarginWidth,8,XmNmarginHeight,8,NULL);
    Widget hs=XtParent(h->dialog);
    XtVaSetValues(hs,XmNdeleteResponse,XmUNMAP,XtNtitle,"Ajuda — Laboratório de temas",NULL);
    tl_ui_hints_shell(hs);
    Widget selectors=XtVaCreateManagedWidget("helpSelectors",xmRowColumnWidgetClass,h->dialog,
        XmNorientation,XmVERTICAL,XmNpacking,XmPACK_TIGHT,
        XmNtopAttachment,XmATTACH_FORM,XmNleftAttachment,XmATTACH_FORM,XmNrightAttachment,XmATTACH_FORM,NULL);
    h->topic_combo=combo(selectors,"helpTopicCombo",TL_HELP_TOPIC_COUNT,1);
    h->level_combo=combo(selectors,"helpLevelCombo",TL_HELP_LEVEL_COUNT,0);
    tl_ui_hint(h->topic_combo,"Escolhe o assunto desta ajuda. A escolha troca somente o texto explicativo; projeto e prévias são preservados.");
    tl_ui_hint(h->level_combo,"Escolhe a profundidade: novice explica termos e passos; intermediate liga conceitos; expert resume o contrato técnico.");
    XtAddCallback(h->topic_combo,XmNselectionCallback,select_topic,h);
    XtAddCallback(h->level_combo,XmNselectionCallback,select_level,h);
    label=string("Fechar ajuda");
    Widget close=XtVaCreateManagedWidget("closeHelp",xmPushButtonWidgetClass,h->dialog,XmNlabelString,label,
        XmNbottomAttachment,XmATTACH_FORM,XmNrightAttachment,XmATTACH_FORM,NULL);XmStringFree(label);
    XtAddCallback(close,XmNactivateCallback,close_help,h);
    tl_ui_hint(close,"Fecha somente esta janela de ajuda; mantém os ajustes, a montagem e as prévias abertas.");
    h->text=XmCreateScrolledText(h->dialog,"helpText",NULL,0);
    XtVaSetValues(h->text,XmNeditMode,XmMULTI_LINE_EDIT,XmNeditable,False,
        XmNcursorPositionVisible,False,XmNwordWrap,True,XmNscrollHorizontal,False,NULL);
    XtVaSetValues(XtParent(h->text),XmNtopAttachment,XmATTACH_WIDGET,XmNtopWidget,selectors,XmNtopOffset,8,
        XmNbottomAttachment,XmATTACH_WIDGET,XmNbottomWidget,close,XmNbottomOffset,8,
        XmNleftAttachment,XmATTACH_FORM,XmNrightAttachment,XmATTACH_FORM,NULL);
    XtManageChild(h->text);
    tl_ui_hint(h->text,"Explicação somente leitura; selecione e copie o texto. Nenhuma escolha nesta ajuda altera a receita ou autoriza outra tarefa.");
    refresh(h);return h;
}
Widget tl_help_menu(TLHelp *h){return h?h->menu:NULL;}
Widget tl_help_dialog(TLHelp *h){return h?h->dialog:NULL;}
Widget tl_help_popup(TLHelp *h){return h?h->popup:NULL;}
void tl_help_destroy(TLHelp *h){
    if(!h)return;
    XtDestroyWidget(XtParent(h->dialog));XtDestroyWidget(h->menu);free(h);
}
