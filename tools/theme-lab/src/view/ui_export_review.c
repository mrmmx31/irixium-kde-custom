/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "ui_export_review.h"
#include "ui_hints.h"
#include "text_editor.h"
#include <Xm/Form.h>
#include <Xm/PushB.h>
#include <Xm/Text.h>
#include <stdlib.h>

struct TLExportReview {Widget dialog,text;};
static void close_review(Widget w,XtPointer data,XtPointer call){
    (void)w;(void)call;XtUnmanageChild(((TLExportReview*)data)->dialog);
}
TLExportReview *tl_export_review_create(Widget shell){
    TLExportReview *r=calloc(1,sizeof(*r));if(!r)return NULL;
    r->dialog=XmCreateFormDialog(shell,"exportReview",NULL,0);
    XtVaSetValues(r->dialog,XmNdialogStyle,XmDIALOG_MODELESS,XmNautoUnmanage,False,
        XmNwidth,800,XmNheight,500,XmNmarginWidth,8,XmNmarginHeight,8,NULL);
    Widget parent=XtParent(r->dialog);
    XtVaSetValues(parent,XmNdeleteResponse,XmUNMAP,XtNtitle,"Exportação — Laboratório de temas",NULL);
    tl_ui_hints_shell(parent);
    XmString label=XmStringGenerate("Fechar comparação",NULL,XmMULTIBYTE_TEXT,NULL);
    Widget close=XtVaCreateManagedWidget("closeExportReview",xmPushButtonWidgetClass,r->dialog,
        XmNlabelString,label,XmNbottomAttachment,XmATTACH_FORM,
        XmNrightAttachment,XmATTACH_FORM,NULL);XmStringFree(label);
    XtAddCallback(close,XmNactivateCallback,close_review,r);
    tl_ui_hint(close,"Fecha somente a comparação. Preserva projeto, pacote exportado e prévias abertas.");
    r->text=XmCreateScrolledText(r->dialog,"exportReviewText",NULL,0);
    XtVaSetValues(r->text,XmNeditMode,XmMULTI_LINE_EDIT,XmNeditable,False,
        XmNcursorPositionVisible,False,XmNwordWrap,True,XmNscrollHorizontal,False,NULL);
    XtVaSetValues(XtParent(r->text),XmNtopAttachment,XmATTACH_FORM,
        XmNbottomAttachment,XmATTACH_WIDGET,XmNbottomWidget,close,XmNbottomOffset,8,
        XmNleftAttachment,XmATTACH_FORM,XmNrightAttachment,XmATTACH_FORM,NULL);
    XtManageChild(r->text);
    tl_ui_hint(r->text,"Relatório somente leitura: selecione e copie caminhos, hashes e diferenças. Não instala nem comprova pintura da prévia.");
    return r;
}
Widget tl_export_review_dialog(TLExportReview *r){return r?r->dialog:NULL;}
void tl_export_review_open(TLExportReview *r,const char *text){
    if(!r)return;
    tl_editor_set_text(r->text,text?text:"");XmTextSetTopCharacter(r->text,0);
    XtManageChild(r->dialog);
}
void tl_export_review_destroy(TLExportReview *r){
    if(!r)return;
    XtDestroyWidget(XtParent(r->dialog));free(r);
}
