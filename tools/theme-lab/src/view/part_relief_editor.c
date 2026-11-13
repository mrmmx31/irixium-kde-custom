/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "part_relief_editor.h"
#include "ui_hints.h"
#include <Xm/ComboBox.h>
#include <Xm/Label.h>
#include <Xm/RowColumn.h>
#include <stdlib.h>
struct TLPartReliefEditor {
    Widget state,relief,notice;
    TLPartRecipe draft;
    int state_index,capability,updating;
    XtCallbackProc changed,selected;
    XtPointer context;
};
static XmString text(const char *value) {
    return XmStringGenerate((XtPointer)value,NULL,XmMULTIBYTE_TEXT,NULL);
}
static Widget combo(Widget parent,const char *name,const char *const *labels,int count,const char *hint) {
    XmString items[TL_PART_STATE_COUNT];
    for(int i=0;i<count;++i)items[i]=text(labels[i]);
    Widget result=XtVaCreateManagedWidget(name,xmComboBoxWidgetClass,parent,
        XmNcomboBoxType,XmDROP_DOWN_LIST,XmNpositionMode,XmZERO_BASED,
        XmNitems,items,XmNitemCount,count,XmNvisibleItemCount,count,
        XmNselectedPosition,0,NULL);
    for(int i=0;i<count;++i)XmStringFree(items[i]);
    tl_ui_hint(result,hint);return result;
}
static void relief_changed(Widget widget,XtPointer data,XtPointer call);
static int editable(const TLPartReliefEditor *editor) {
    return editor->capability==TL_RELIEF_GTK3_ARROW_BUTTON ||
        (editor->capability==TL_RELIEF_GTK3_THUMB&&editor->state_index<5) ||
        ((editor->capability==TL_RELIEF_GTK3_ENCLOSURE||editor->capability==TL_RELIEF_GTK3_FITTING)&&
         (editor->state_index==0||editor->state_index==2||editor->state_index==3)) ||
        (editor->capability==TL_RELIEF_GTK3_STEPPER&&editor->state_index<5);
}
static void refresh(TLPartReliefEditor *editor) {
    int state=editor->state_index;
    int value=(editor->draft.relief_present&(1u<<state))?editor->draft.relief[state]:0;
    editor->updating=1;
    /* Programmatic selection is presentation, never a new recipe edit.
       Motif can notify with the previous list position during SetValues. */
    XtRemoveCallback(editor->relief,XmNselectionCallback,relief_changed,editor);
    XtVaSetValues(editor->relief,XmNselectedPosition,value,NULL);
    XtAddCallback(editor->relief,XmNselectionCallback,relief_changed,editor);
    XtSetSensitive(editor->relief,editable(editor));
    XmString notice=text(editor->capability==TL_RELIEF_GTK3_FITTING?
        "Encaixe GtkViewport: Normal,\nDesabilitado e Sem foco. Moldura não\ninterativa; filhos têm estados próprios.":
        editor->capability==TL_RELIEF_GTK3_THUMB?
        "Cursor GTK3: cinco estados da receita.\nPressione/arraste o cursor real para testar.\nFoco indisponível na barra padrão.":
        editor->capability==TL_RELIEF_GTK3_ENCLOSURE?
        "Moldura contínua GTK3: Normal,\nDesabilitado e Sem foco. GtkRange remove\npressão/hover; barra padrão não recebe foco.":
        editor->capability==TL_RELIEF_GTK3_ARROW_BUTTON?
        "Botão isolado GTK3: moldura da receita.\nPressione ou dê foco ao botão real para testar.\nO triângulo tem receita independente.":
        editor->capability==TL_RELIEF_GTK3_STEPPER&&state<5?
        "Seta GTK3: ajuste da receita.\nPressione a seta real para testar;\neste seletor não força o estado nativo.":
        editor->capability==TL_RELIEF_GTK3_STEPPER&&state==5?
        "GtkScrollbar padrão não aceita foco.\nFoco da seta isolada requer contrato próprio.\nA receita salva permanece preservada.":
        "Tradução desta peça/estado pendente.\nA receita salva permanece preservada.");
    XtVaSetValues(editor->notice,XmNlabelString,notice,NULL);XmStringFree(notice);
    editor->updating=0;
}
static void state_changed(Widget widget,XtPointer data,XtPointer call) {
    TLPartReliefEditor *editor=data;
    int selected=-1;(void)call;
    if(editor->updating)return;
    /* Motif's callback position is reconstructed from the edit-box string.
       The selectedPosition resource instead reads the actual list selection;
       compound-string tags can make the reconstructed position report zero. */
    XtVaGetValues(widget,XmNselectedPosition,&selected,NULL);
    if(selected<0||selected>=TL_PART_STATE_COUNT)return;
    editor->state_index=selected;refresh(editor);
    if(editor->selected)editor->selected(widget,editor->context,call);
}
static void relief_changed(Widget widget,XtPointer data,XtPointer call) {
    TLPartReliefEditor *editor=data;
    if(editor->updating||!editable(editor))return;
    int value=-1;
    XtVaGetValues(widget,XmNselectedPosition,&value,NULL);
    if(value<0||value>3)return;
    if(tl_part_relief_set(&editor->draft,editor->state_index,value?value:-1))return;
    if(editor->changed)editor->changed(widget,editor->context,call);
}
static void destroyed(Widget widget,XtPointer data,XtPointer call) {
    (void)widget;(void)call;free(data);
}
TLPartReliefEditor *tl_part_editor_create(Widget parent,XtCallbackProc changed,XtCallbackProc selected,XtPointer context) {
    TLPartReliefEditor *editor=calloc(1,sizeof(*editor));if(!editor)return NULL;
    editor->changed=changed;editor->selected=selected;editor->context=context;
    Widget group=XtVaCreateManagedWidget("pieceStateEditor",xmRowColumnWidgetClass,parent,
        XmNorientation,XmVERTICAL,XmNpacking,XmPACK_TIGHT,NULL);
    XmString caption=text("Estado e relevo da receita da peça");
    XtVaCreateManagedWidget("pieceStateCaption",xmLabelWidgetClass,group,XmNlabelString,caption,NULL);
    XmStringFree(caption);
    const char *states[]={"Normal","Pressionado","Desabilitado","Sem foco","Hover","Foco"};
    const char *reliefs[]={"Herdar desenho nativo","Plano","Elevado","Rebaixado"};
    editor->state=combo(group,"pieceReliefState",states,TL_PART_STATE_COUNT,
        "Escolha o estado da receita. Não força estados dos nós internos GTK. Alterne sem perder ajustes dos outros estados.");
    editor->relief=combo(group,"pieceReliefKind",reliefs,4,
        "Altera somente o relevo desta peça/estado. Herdar remove esse override; dimensões e papéis KDE permanecem iguais.");
    editor->notice=XtVaCreateManagedWidget("pieceReliefCapability",xmLabelWidgetClass,group,XmNalignment,XmALIGNMENT_BEGINNING,NULL);
    XtAddCallback(editor->state,XmNselectionCallback,state_changed,editor);
    XtAddCallback(editor->relief,XmNselectionCallback,relief_changed,editor);
    XtAddCallback(group,XmNdestroyCallback,destroyed,editor);
    refresh(editor);return editor;
}
void tl_part_editor_update(TLPartReliefEditor *editor,const TLPartRecipe *part,int capability) {
    if(!editor||!part)return;
    editor->draft=*part;
    editor->capability=capability>=TL_RELIEF_UNAVAILABLE&&capability<=TL_RELIEF_GTK3_FITTING?
        capability:TL_RELIEF_UNAVAILABLE;
    refresh(editor);
}
int tl_part_editor_capture(const TLPartReliefEditor *editor,TLPartRecipe *part) {
    if(!editor||!part||tl_part_relief_validate(&editor->draft))return -1;
    part->relief_present=editor->draft.relief_present;
    for(int i=0;i<TL_PART_STATE_COUNT;++i)part->relief[i]=editor->draft.relief[i];
    return 0;
}
int tl_part_editor_state(const TLPartReliefEditor *editor) {
    return editor&&editor->capability!=TL_RELIEF_UNAVAILABLE?editor->state_index:-1;
}
