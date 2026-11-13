/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "part_relief_editor.h"
#include <Xm/ComboBox.h>
#include <Xm/RowColumn.h>
#include <assert.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
static int changes;
static void changed(Widget widget,XtPointer context,XtPointer call) {
    (void)widget;(void)context;(void)call;++changes;
}
static void select_item(Widget widget,int position) {
    /* SetValues emits an interim selection callback in this Motif build.
       Suppress it, then exercise the selection event after the value exists.
       This is a callback-level test, not a real pointer-input claim. */
    XtCallbackList original;XtVaGetValues(widget,XmNselectionCallback,&original,NULL);
    size_t count=0;while(original[count].callback)++count;
    XtCallbackList saved=calloc(count+1,sizeof(*saved));assert(saved);
    memcpy(saved,original,count*sizeof(*saved));
    XtRemoveAllCallbacks(widget,XmNselectionCallback);
    XtVaSetValues(widget,XmNselectedPosition,position,NULL);
    XtAddCallbacks(widget,XmNselectionCallback,saved);free(saved);
    /* Native integrated evidence reports zero when the edit-box compound
       string does not match list tags. The actual list selection must win. */
    XmComboBoxCallbackStruct event={0};event.item_position=0;
    XtCallCallbacks(widget,XmNselectionCallback,&event);
}
int main(int argc,char **argv) {
    XtAppContext app;
    Widget shell=XtVaAppInitialize(&app,"PartReliefTest",NULL,0,&argc,argv,NULL,NULL);
    Widget parent=XtVaCreateManagedWidget("root",xmRowColumnWidgetClass,shell,NULL);
    TLPartReliefEditor *editor=tl_part_editor_create(parent,changed,NULL,NULL);assert(editor);
    Widget state=XtNameToWidget(parent,"*pieceReliefState"),relief=XtNameToWidget(parent,"*pieceReliefKind");
    assert(state&&relief);XtRealizeWidget(shell);
    TLPartRecipe original={0},result={0};original.present=1;original.values[0]=7;
    tl_part_editor_update(editor,&original,1);
    select_item(relief,2);assert(changes==1);
    select_item(state,1);select_item(relief,3);assert(changes==2);
    assert(!tl_part_editor_capture(editor,&result));
    assert(result.relief[0]==2&&result.relief[1]==3);
    /* Capture only relief; caller retains current independent geometry. */
    result.present=1;result.values[0]=9;
    assert(!tl_part_editor_capture(editor,&result));assert(result.values[0]==9);
    select_item(state,0);select_item(relief,0);
    assert(!tl_part_editor_capture(editor,&result));
    assert(!(result.relief_present&1)&&result.relief[1]==3);
    TLPartRecipe preserved=result;
    select_item(state,2);assert(XtIsSensitive(relief));select_item(relief,2);
    select_item(state,3);assert(XtIsSensitive(relief));select_item(relief,1);
    assert(!tl_part_editor_capture(editor,&result));
    assert(result.relief[1]==3&&result.relief[2]==2&&result.relief[3]==1);
    preserved=result;
    select_item(state,5);assert(!XtIsSensitive(relief));select_item(relief,1);
    assert(!tl_part_editor_capture(editor,&result));assert(!memcmp(&result,&preserved,sizeof(result)));
    tl_part_editor_update(editor,&original,0);select_item(state,0);
    assert(!XtIsSensitive(relief));select_item(relief,3);
    assert(!tl_part_editor_capture(editor,&result));assert(!result.relief_present);
    tl_part_editor_update(editor,&preserved,1);select_item(state,1);
    int position=-1;XtVaGetValues(relief,XmNselectedPosition,&position,NULL);assert(position==3);
    assert(!tl_part_editor_capture(editor,&result));assert(result.relief[1]==3);
    /* Isolated button focus is editable; the range stepper remains guarded.
       Switching capability presents the existing draft without modifying it. */
    int before=changes;
    tl_part_editor_update(editor,&preserved,TL_RELIEF_GTK3_ARROW_BUTTON);
    select_item(state,5);assert(XtIsSensitive(relief));select_item(relief,2);
    assert(changes==before+1);
    assert(!tl_part_editor_capture(editor,&result));
    assert(result.relief[5]==2&&result.relief[1]==3);
    preserved=result;
    tl_part_editor_update(editor,&preserved,TL_RELIEF_GTK3_STEPPER);
    assert(!XtIsSensitive(relief));select_item(relief,3);
    assert(!tl_part_editor_capture(editor,&result));assert(!memcmp(&result,&preserved,sizeof(result)));
    tl_part_editor_update(editor,&preserved,99);assert(tl_part_editor_state(editor)==-1);
    assert(!XtIsSensitive(relief));
    tl_part_editor_update(editor,&original,TL_RELIEF_GTK3_ENCLOSURE);
    select_item(state,0);assert(XtIsSensitive(relief));select_item(relief,1);
    select_item(state,2);assert(XtIsSensitive(relief));select_item(relief,2);
    select_item(state,3);assert(XtIsSensitive(relief));select_item(relief,3);
    assert(!tl_part_editor_capture(editor,&result));
    assert(result.relief[0]==1&&result.relief[2]==2&&result.relief[3]==3);
    preserved=result;
    const int unsupported[]={1,4,5};
    for(int i=0;i<3;++i) {
        select_item(state,unsupported[i]);assert(!XtIsSensitive(relief));select_item(relief,1);
        assert(!tl_part_editor_capture(editor,&result));assert(!memcmp(&result,&preserved,sizeof(result)));
    }
    tl_part_editor_update(editor,&original,TL_RELIEF_GTK3_THUMB);
    for(int state_index=0;state_index<5;++state_index) {
        select_item(state,state_index);assert(XtIsSensitive(relief));
        select_item(relief,state_index%3+1);
    }
    assert(!tl_part_editor_capture(editor,&result));assert(result.relief_present==31);
    preserved=result;select_item(state,5);assert(!XtIsSensitive(relief));select_item(relief,3);
    assert(!tl_part_editor_capture(editor,&result));assert(!memcmp(&result,&preserved,sizeof(result)));
    select_item(state,4);select_item(relief,0);
    assert(!tl_part_editor_capture(editor,&result));assert(result.relief_present==15);
    tl_part_editor_update(editor,&original,TL_RELIEF_GTK3_FITTING);
    const int fitting_states[]={0,2,3};
    for(int i=0;i<3;++i) {
        select_item(state,fitting_states[i]);assert(XtIsSensitive(relief));select_item(relief,i+1);
    }
    assert(!tl_part_editor_capture(editor,&result));assert(result.relief_present==13);
    preserved=result;
    for(int i=0;i<3;++i) {
        select_item(state,unsupported[i]);assert(!XtIsSensitive(relief));select_item(relief,1);
        assert(!tl_part_editor_capture(editor,&result));assert(!memcmp(&result,&preserved,sizeof(result)));
    }
    select_item(state,3);select_item(relief,0);
    assert(!tl_part_editor_capture(editor,&result));assert(result.relief_present==5);
    XtDestroyWidget(shell);XtDestroyApplicationContext(app);
    puts("Motif editor: state switching, inheritance, geometry preservation and unsupported-state guards passed (callback-level).");return 0;
}
