/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Test-only wrapper: observes public widgets; production has no probe hooks. */
#include "controller.h"
#include "native_parts_motif.h"
#include "part_relief_editor.h"
#include <Xm/Label.h>
#include <Xm/TextF.h>
#include <Xm/Text.h>
#include <Xm/List.h>
#include <Xm/ScrolledW.h>
#include <Xm/ScrollBar.h>
#include <Xm/ComboBox.h>
#include <Xm/FileSB.h>
#include <json-c/json.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static Widget shell;
static XtAppContext app;
static TLView *observed_view;
static TLDispatch controller_dispatch;
static void *controller_context;
static int anchor_event=-1, selected_control_event=-1;
static int anchor_result=0;
static char anchor_error[1024];
int __real_tl_view_set_anchor(TLView *, TLModel *, int, char *, size_t);
int __wrap_tl_view_set_anchor(TLView *view, TLModel *model, int anchor, char *error, size_t capacity) {
    anchor_result=__real_tl_view_set_anchor(view,model,anchor,error,capacity);
    snprintf(anchor_error,sizeof(anchor_error),"%s",anchor_result?error:"");
    return anchor_result;
}
static int family_argument=-1,family_selection=-1;
static int anchor_calls=0,anchor_arguments[32],anchor_selections[32];
static json_object *relief_trace;
static void trace_relief(const char *kind,int position,const TLPartRecipe *part) {
    if(!relief_trace)relief_trace=json_object_new_array();
    if(json_object_array_length(relief_trace)>=256)return;
    json_object *row=json_object_new_object();
    json_object_object_add(row,"event",json_object_new_string(kind));
    json_object_object_add(row,"position",json_object_new_int(position));
    if(part) {
        json_object_object_add(row,"mask",json_object_new_int(part->relief_present));
        json_object_object_add(row,"normal",json_object_new_int(part->relief[0]));
        json_object_object_add(row,"pressed",json_object_new_int(part->relief[1]));
    }
    json_object_array_add(relief_trace,row);
}
void __real_tl_part_editor_update(TLPartReliefEditor *,const TLPartRecipe *,int);
void __wrap_tl_part_editor_update(TLPartReliefEditor *,const TLPartRecipe *,int);
void __wrap_tl_part_editor_update(TLPartReliefEditor *editor,const TLPartRecipe *part,int supported) {
    trace_relief("model-update",supported,part);
    __real_tl_part_editor_update(editor,part,supported);
}
int __real_tl_part_editor_capture(const TLPartReliefEditor *,TLPartRecipe *);
int __wrap_tl_part_editor_capture(const TLPartReliefEditor *,TLPartRecipe *);
int __wrap_tl_part_editor_capture(const TLPartReliefEditor *editor,TLPartRecipe *part) {
    int result=__real_tl_part_editor_capture(editor,part);
    trace_relief("capture",result,part);return result;
}
static void relief_observed(Widget widget,XtPointer context,XtPointer call) {
    XmComboBoxCallbackStruct *event=call;(void)context;
    trace_relief(XtName(widget),event?event->item_position:-1,NULL);
    int selected=-1;XtVaGetValues(widget,XmNselectedPosition,&selected,NULL);
    trace_relief("native-list-position",selected,NULL);
}
static void observed_dispatch(void *context,TLAction action,int argument) {
    (void)context;
    if(action==TL_SELECT_CONTROL)selected_control_event=argument;
    if(action==TL_SELECT_FAMILY) {family_argument=argument;
        XtVaGetValues(XtNameToWidget(shell,"*familyCombo"),XmNselectedPosition,&family_selection,NULL);}
    if(action==TL_SELECT_ANCHOR) {
        anchor_event=argument;
        if(anchor_calls<32) {
            int selected=-1;Widget combo=XtNameToWidget(shell,"*lengthAnchor");
            if(combo)XtVaGetValues(combo,XmNselectedPosition,&selected,NULL);
            anchor_arguments[anchor_calls]=argument;anchor_selections[anchor_calls++]=selected;
        }
    }
    controller_dispatch(controller_context,action,argument);
}
TLView *__real_tl_view_create(Widget,TLDispatch,void *);
TLView *__wrap_tl_view_create(Widget,TLDispatch,void *);
static void geometry(json_object *root,Widget w,const char *name) {
    Position x,y;Dimension width,height;
    XtTranslateCoords(w,0,0,&x,&y);
    XtVaGetValues(w,XmNwidth,&width,XmNheight,&height,NULL);
    json_object *a=json_object_new_array();int values[]={x,y,width,height};
    for(int i=0;i<4;++i)json_object_array_add(a,json_object_new_int(values[i]));
    json_object_object_add(root,name,a);
}
static void select_left_page(int page) {
    Widget combo=XtNameToWidget(shell,"*leftPanelSelector"),list=NULL;
    if(!combo||page<0||page>5)return;
    XtVaGetValues(combo,XmNlist,&list,NULL);
    if(list)XmListSelectPos(list,page+1,False);
    XmComboBoxCallbackStruct event={0};
    event.reason=XmCR_SELECT;event.item_position=page;
    XtVaSetValues(combo,XmNselectedPosition,page,NULL);
    XtCallCallbacks(combo,XmNselectionCallback,&event);
}
static void report(XtPointer data,XtIntervalId *id) {
    const char *path=getenv("TL_SPIN_PROBE");
    (void)data;(void)id;
    if(path&&XtIsRealized(shell)) {
        Widget width=XtNameToWidget(shell,"*controlWidth*fieldValue");
        const char *command=getenv("TL_SPIN_COMMAND");
        if(command&&width) {
            FILE *f=fopen(command,"r");
            if(f) {
                char input[80]={0};int value;
                (void)fgets(input,sizeof(input),f);fclose(f);remove(command);
                char action_name[40]={0};
                if(sscanf(input,"action %39s",action_name)==1) {
                    static const char *const keys[]={
                        "apply","save","load","export","import_delta",
                        "reconstruct_files","manual_paint","quit",
                        "projectUndo","projectRedo","projectMark",
                        "projectRestore","projectResetPart"};
                    static const char *const widgets[]={
                        "*menuRefresh","*menuSave","*menuLoad","*menuExport",
                        "*menuImportDelta","*menuReconstructFiles",
                        "*menuManualPaint","*menuQuit","*projectUndoMenu",
                        "*projectRedoMenu","*projectMarkMenu",
                        "*projectRestoreMenu","*projectResetPartMenu"};
                    for(size_t i=0;i<sizeof(keys)/sizeof(keys[0]);++i)
                        if(!strcmp(action_name,keys[i])) {
                            Widget action=XtNameToWidget(shell,(char *)widgets[i]);
                            if(action)XtCallCallbacks(action,XmNactivateCallback,NULL);
                            goto command_complete;
                        }
                }
                Widget target=input[0]=='h'?XtNameToWidget(shell,"*controlHeight*fieldValue"):width;
                char tree_kind[32];int tree_index;
                if(sscanf(input,"tree %31s %d",tree_kind,&tree_index)==2&&tree_index>=0&&tree_index<16) {
                    char name[80];snprintf(name,sizeof(name),"*catalog%s%d",tree_kind,tree_index);
                    target=XtNameToWidget(shell,name);
                }
                if(sscanf(input,"focus-control %d",&value)==1&&value>=0&&value<16) {
                    char name[64];snprintf(name,sizeof(name),"*catalogControl%d",value);
                    target=XtNameToWidget(shell,name);
                }
                if(!strncmp(input,"family",6))target=XtNameToWidget(shell,"*familyCombo");
                if(!strncmp(input,"automatic",9))target=XtNameToWidget(shell,"*automaticPreview");
                if(!strncmp(input,"separate",8)){select_left_page(4);target=XtNameToWidget(shell,"*separatePreview");}
                if(!strncmp(input,"edit-state",10)){select_left_page(1);target=XtNameToWidget(shell,"*editState");}
                if(input[0]=='m'){select_left_page(1);target=XtNameToWidget(shell,"*nativeMetrics");}
                if(input[0]=='n'){select_left_page(4);target=XtNameToWidget(shell,"*notesText");}
                if(input[0]=='\0'||input[0]=='w'||input[0]=='h'||!strncmp(input,"set-width",9)||
                   !strncmp(input,"set-height",10)||!strncmp(input,"anchor",6))
                    select_left_page(1);
                if(!strncmp(input,"gap",3))target=XtNameToWidget(shell,"*partGap*fieldValue");
                else if(input[0]=='g')target=XtNameToWidget(shell,"*partGlyph*fieldValue");
                if(!strncmp(input,"shadow",6))target=XtNameToWidget(shell,"*partShadow*fieldValue");
                if(!strncmp(input,"gap",3)||input[0]=='g'||!strncmp(input,"shadow",6)||
                   !strncmp(input,"piece",5)||!strncmp(input,"relief-",7))select_left_page(2);
                if(!strncmp(input,"tree",4)||!strncmp(input,"control",7)||
                   !strncmp(input,"focus-control",13))select_left_page(0);
                if(sscanf(input,"family-select %d",&value)==1&&value>=0&&value<TL_FAMILY_COUNT) {
                    Widget combo=XtNameToWidget(shell,"*familyCombo"),list=NULL;
                    XtVaGetValues(combo,XmNlist,&list,NULL);
                    if(list)XmListSelectPos(list,value+1,True);
                } else if(sscanf(input,"set-width %d",&value)==1||sscanf(input,"set-height %d",&value)==1) {
                    target=strstr(input,"set-height")==input?XtNameToWidget(shell,"*controlHeight*fieldValue"):width;
                    if(value>=0&&value<=2048) {char text[16];snprintf(text,sizeof(text),"%d",value);XmTextFieldSetString(target,text);}
                } else if(sscanf(input,"piece %d",&value)==1 && value>=0 && value<5) {
                    Widget combo=XtNameToWidget(shell,"*scrollPartCombo");
                    XmComboBoxCallbackStruct event={0};event.item_position=value;
                    XtVaSetValues(combo,XmNselectedPosition,value,NULL);
                    XtCallCallbacks(combo,XmNselectionCallback,&event);
                } else if(sscanf(input,"control %d",&value)==1&&value>=0&&value<16) {
                    char name[64];snprintf(name,sizeof(name),"*catalogControl%d",value);
                    XtCallCallbacks(XtNameToWidget(shell,name),XmNactivateCallback,NULL);
                } else if(!strncmp(input,"relief-state",12)||!strncmp(input,"relief-kind",11)) {
                    target=XtNameToWidget(shell,!strncmp(input,"relief-state",12)?"*pieceReliefState":"*pieceReliefKind");
                    Widget scroll=XtNameToWidget(shell,"*recipeScroll");
                    XmScrollVisible(scroll,target,8,8);
                    Widget clip=NULL,bar=NULL;
                    XtVaGetValues(scroll,XmNclipWindow,&clip,XmNverticalScrollBar,&bar,NULL);
                    if(clip&&bar) {
                        Position tx,ty,cx,cy;Dimension height;
                        XtTranslateCoords(target,0,0,&tx,&ty);XtTranslateCoords(clip,0,0,&cx,&cy);
                        XtVaGetValues(clip,XmNheight,&height,NULL);
                        int value,minimum,maximum,slider;
                        XtVaGetValues(bar,XmNvalue,&value,XmNminimum,&minimum,XmNmaximum,&maximum,XmNsliderSize,&slider,NULL);
                        int next=value+ty-cy-(int)height/2;
                        if(next<minimum)next=minimum;
                        if(next>maximum-slider)next=maximum-slider;
                        XmScrollBarSetValues(bar,next,slider,0,0,True);
                        Widget horizontal=NULL;Dimension clip_width,target_width;
                        XtVaGetValues(scroll,XmNhorizontalScrollBar,&horizontal,NULL);
                        XtVaGetValues(clip,XmNwidth,&clip_width,NULL);
                        XtVaGetValues(target,XmNwidth,&target_width,NULL);
                        XtTranslateCoords(target,0,0,&tx,&ty);XtTranslateCoords(clip,0,0,&cx,&cy);
                        if(horizontal&&tx+(int)target_width>cx+(int)clip_width) {
                            XtVaGetValues(horizontal,XmNvalue,&value,XmNminimum,&minimum,XmNmaximum,&maximum,XmNsliderSize,&slider,NULL);
                            next=value+tx+(int)target_width-cx-(int)clip_width+8;
                            if(next<minimum)next=minimum;
                            if(next>maximum-slider)next=maximum-slider;
                            XmScrollBarSetValues(horizontal,next,slider,0,0,True);
                        }
                    }
                } else if(!strncmp(input,"anchor",6)) {
                    target=XtNameToWidget(shell,"*lengthAnchor");
                    XmScrollVisible(XtNameToWidget(shell,"*recipeScroll"),target,8,8);
                } else if(!strncmp(input,"catalog",7)) {
                    const char *ids[]={"DomainOS-SR10.4"};tl_view_schemes(observed_view,ids,1);
                } else XmScrollVisible(XtNameToWidget(shell,"*recipeScroll"),target,8,8);
                if(!strncmp(input,"focus-control",13)&&target)
                    XmProcessTraversal(target,XmTRAVERSE_CURRENT);
                if(!strncmp(input,"family",6) || !strncmp(input,"anchor",6) || !strncmp(input,"edit-state",10)) {
                    Widget clip=NULL,bar=NULL;Position x,y,cx,cy;Dimension w,cw;
                    Widget scroll=XtNameToWidget(shell,"*recipeScroll");
                    XtVaGetValues(scroll,XmNclipWindow,&clip,XmNhorizontalScrollBar,&bar,NULL);
                    XtVaGetValues(target,XmNwidth,&w,NULL);XtVaGetValues(clip,XmNwidth,&cw,NULL);
                    XtTranslateCoords(target,0,0,&x,&y);XtTranslateCoords(clip,0,0,&cx,&cy);
                    if(bar&&x+(int)w>cx+(int)cw) {
                        int value,minimum,maximum,slider;
                        XtVaGetValues(bar,XmNvalue,&value,XmNminimum,&minimum,XmNmaximum,&maximum,XmNsliderSize,&slider,NULL);
                        int next=value+x+(int)w-cx-(int)cw;
                        if(next>maximum-slider)next=maximum-slider;
                        if(next<minimum)next=minimum;
                        XmScrollBarSetValues(bar,next,slider,0,0,True);
                    }
                }
command_complete:
                ;
            }
        }
        json_object *root=json_object_new_object();
        json_object_object_add(root,"controller_pid",json_object_new_int(getpid()));
        json_object_object_add(root,"canvas_window",json_object_new_int64((long long)tl_view_canvas(observed_view)));
        Widget focus=XmGetFocusWidget(shell);
        json_object_object_add(root,"keyboard_focus",json_object_new_string(focus?XtName(focus):""));
        TLNativeMetrics push;
        if(!tl_view_get_native_metrics(observed_view,0,0,&push)) {
            json_object *allocation=json_object_new_array();
            json_object_array_add(allocation,json_object_new_int(push.width));
            json_object_array_add(allocation,json_object_new_int(push.height));
            json_object_object_add(root,"native_push_allocation",allocation);
        }
        json_object_object_add(root,"anchor_event",json_object_new_int(anchor_event));
        json_object_object_add(root,"anchor_result",json_object_new_int(anchor_result));
        json_object_object_add(root,"anchor_error",json_object_new_string(anchor_error));
        json_object_object_add(root,"selected_control_event",json_object_new_int(selected_control_event));
        json_object_object_add(root,"family_argument",json_object_new_int(family_argument));
        json_object_object_add(root,"family_selection",json_object_new_int(family_selection));
        json_object *calls=json_object_new_array();
        for(int i=0;i<anchor_calls;i++) {
            json_object *call=json_object_new_object();
            json_object_object_add(call,"argument",json_object_new_int(anchor_arguments[i]));
            json_object_object_add(call,"selection",json_object_new_int(anchor_selections[i]));
            json_object_array_add(calls,call);
        }
        json_object_object_add(root,"anchor_calls",calls);
        Widget status=XtNameToWidget(shell,"*controllerStatus");
        if(status) {XmString label;XtVaGetValues(status,XmNlabelString,&label,NULL);
            char *message=XmStringUnparse(label,NULL,XmCHARSET_TEXT,XmMULTIBYTE_TEXT,NULL,0,XmOUTPUT_ALL);
            json_object_object_add(root,"status",json_object_new_string(message?message:""));XtFree(message);}
        json_object *native=json_object_new_array();
        for(int separate=0;separate<2;++separate)for(int control=10;control<=11;++control) {
            TLNativeMetrics metrics;
            if(!tl_view_get_native_metrics(observed_view,control,separate,&metrics)) {
                json_object *item=json_object_new_object();
                json_object_object_add(item,"control",json_object_new_int(control));
                json_object_object_add(item,"separate",json_object_new_int(separate));
                json_object_object_add(item,"width",json_object_new_int(metrics.width));
                json_object_object_add(item,"height",json_object_new_int(metrics.height));
                json_object_object_add(item,"x",json_object_new_int(metrics.position_x));
                json_object_object_add(item,"y",json_object_new_int(metrics.position_y));
                json_object_object_add(item,"offset_y",json_object_new_int(metrics.cell_offset_y));
                json_object_object_add(item,"cell_offset_valid",json_object_new_boolean(metrics.cell_offset_valid));
                json_object_object_add(item,"position_valid",json_object_new_boolean(metrics.position_valid));
                json_object_object_add(item,"pieces_source",json_object_new_int(metrics.pieces.source));
                json_object_object_add(item,"pieces_mask",json_object_new_int(metrics.pieces.mask));
                const TLNativeRect *rects[]={&metrics.pieces.slider,&metrics.pieces.track,&metrics.pieces.arrows[0],&metrics.pieces.arrows[1]};
                const char *keys[]={"slider","track","arrow_first","arrow_last"};
                for(int n=0;n<4;++n)if(metrics.pieces.mask&(1u<<n)) {
                    const TLNativeRect *r=rects[n];json_object *rect=json_object_new_array();
                    int values[]={r->x,r->y,r->width,r->height};
                    for(int k=0;k<4;++k)json_object_array_add(rect,json_object_new_int(values[k]));
                    json_object_object_add(item,keys[n],rect);
                }
                json_object_array_add(native,item);
            }
        }
        json_object_object_add(root,"native_bars",native);
        json_object *controls=json_object_new_array();
        for(int separate=0;separate<2;++separate)for(int control=0;control<16;++control) {
            TLNativeMetrics metrics;
            if(!tl_view_get_native_metrics(observed_view,control,separate,&metrics)) {
                json_object *item=json_object_new_object();
                json_object_object_add(item,"control",json_object_new_int(control));
                json_object_object_add(item,"separate",json_object_new_int(separate));
                json_object_object_add(item,"scale",json_object_new_int(metrics.scale_factor));
                json_object_object_add(item,"font_kind",json_object_new_int(metrics.font.kind));
                json_object_object_add(item,"font",json_object_new_string(metrics.font.description));
                json_object_object_add(item,"width",json_object_new_int(metrics.width));
                json_object_object_add(item,"height",json_object_new_int(metrics.height));
                json_object_object_add(item,"natural_width",json_object_new_int(metrics.natural_width));
                json_object_object_add(item,"x",json_object_new_int(metrics.position_x));
                json_object_object_add(item,"y",json_object_new_int(metrics.position_y));
                json_object_object_add(item,"natural_height",json_object_new_int(metrics.natural_height));
                json_object_array_add(controls,item);
            }
        }
        json_object_object_add(root,"native_controls",controls);
        json_object_object_add(root,"window",json_object_new_int64((int64_t)XtWindow(shell)));
        const char *names[]={"controlWidth*fieldValue","controlHeight*fieldValue","separatePreview","automaticPreview","nativeMetrics","motifReferenceControls.nativePushButton","editState"};
        for(size_t i=0;i<sizeof(names)/sizeof(names[0]);++i) {
            char search[120];snprintf(search,sizeof(search),"*%s",names[i]);Widget w=XtNameToWidget(shell,search);
            if(!w)continue;
            geometry(root,w,names[i]);
            if(i<2) {char *text=XmTextFieldGetString(w);
                json_object_object_add(root,i?"height_text":"width_text",json_object_new_string(text));XtFree(text);
                json_object_object_add(root,i?"height_sensitive":"width_sensitive",json_object_new_boolean(XtIsSensitive(w)));}
            if(i==2) {Boolean checked=False;XtVaGetValues(w,XmNset,&checked,NULL);json_object_object_add(root,"separate_preview_checked",json_object_new_boolean(checked));}
            if(i==0)geometry(root,XtParent(w),"width_spin");
            if(i==1)geometry(root,XtParent(w),"height_spin");
            if(i==4) {XmString value;XtVaGetValues(w,XmNlabelString,&value,NULL);char *text=XmStringUnparse(value,NULL,XmCHARSET_TEXT,XmMULTIBYTE_TEXT,NULL,0,XmOUTPUT_ALL);json_object_object_add(root,"metrics",json_object_new_string(text));XtFree(text);}
        }
        if(relief_trace)json_object_object_add(root,"relief_trace",json_object_get(relief_trace));
        const char *relief_names[]={"pieceReliefState","pieceReliefKind"};
        const char *relief_keys[]={"relief_state","relief_kind"};
        for(int choice=0;choice<2;choice++) {
            char query[64];snprintf(query,sizeof(query),"*%s",relief_names[choice]);
            Widget combo=XtNameToWidget(shell,query);if(!combo)continue;
            geometry(root,combo,relief_keys[choice]);int position=-1;
            Dimension aw,mw,sh,hi,cw,ch;Position rx,ry;
            XtVaGetValues(combo,XmNarrowSize,&aw,XmNmarginWidth,&mw,XmNshadowThickness,&sh,
                          XmNhighlightThickness,&hi,XmNwidth,&cw,XmNheight,&ch,NULL);
            XtTranslateCoords(combo,0,0,&rx,&ry);
            char arrow_key[80];snprintf(arrow_key,sizeof(arrow_key),"%s_arrow",relief_keys[choice]);
            json_object *arrow=json_object_new_array();int arrow_values[]={rx+cw-mw-sh-hi-aw,ry+(ch-aw)/2,aw,aw};
            for(int n=0;n<4;n++)json_object_array_add(arrow,json_object_new_int(arrow_values[n]));
            json_object_object_add(root,arrow_key,arrow);
            XtVaGetValues(combo,XmNselectedPosition,&position,NULL);
            char key[80];snprintf(key,sizeof(key),"%s_selected",relief_keys[choice]);
            json_object_object_add(root,key,json_object_new_int(position));
            snprintf(key,sizeof(key),"%s_sensitive",relief_keys[choice]);
            json_object_object_add(root,key,json_object_new_boolean(XtIsSensitive(combo)));
            Widget list=NULL;XtVaGetValues(combo,XmNlist,&list,NULL);
            XWindowAttributes attributes;
            if(list&&XtIsRealized(list)&&XGetWindowAttributes(XtDisplay(list),XtWindow(list),&attributes)&&attributes.map_state==IsViewable) {
                for(int index=0;index<(choice?4:6);index++) {
                    Position x,y,rx,ry;Dimension w,h;
                    if(XmListPosToBounds(list,index+1,&x,&y,&w,&h)) {
                        XtTranslateCoords(list,x,y,&rx,&ry);
                        snprintf(key,sizeof(key),"%s_option_%d",relief_keys[choice],index);
                        json_object *bounds=json_object_new_array();int values[]={rx,ry,w,h};
                        for(int n=0;n<4;n++)json_object_array_add(bounds,json_object_new_int(values[n]));
                        json_object_object_add(root,key,bounds);
                    }
                }
            }
        }
        Widget canvas=XtNameToWidget(shell,"*familyCanvas");
        Widget anchor=XtNameToWidget(shell,"*lengthAnchor");
        if(anchor) {int selected;geometry(root,anchor,"anchor");
            XtVaGetValues(anchor,XmNselectedPosition,&selected,NULL);
            json_object_object_add(root,"anchor_selected",json_object_new_int(selected));
            json_object_object_add(root,"anchor_sensitive",json_object_new_boolean(XtIsSensitive(anchor)));}
        if(anchor) {
            Widget list=NULL;XtVaGetValues(anchor,XmNlist,&list,NULL);
            if(list && XtIsRealized(list)) {
                XWindowAttributes attributes;
                if(XGetWindowAttributes(XtDisplay(list),XtWindow(list),&attributes) && attributes.map_state==IsViewable) {
                    Position x,y,root_x,root_y;Dimension w,h;
                    if(XmListPosToBounds(list,2,&x,&y,&w,&h)) {
                        XtTranslateCoords(list,x,y,&root_x,&root_y);
                        json_object *bounds=json_object_new_array();int values[]={root_x,root_y,w,h};
                        for(int i=0;i<4;++i)json_object_array_add(bounds,json_object_new_int(values[i]));
                        json_object_object_add(root,"anchor_end_option",bounds);
                    }
                }
            }
        }
        if(canvas)geometry(root,canvas,"canvas");
        Widget preview_stack=XtNameToWidget(shell,"*previewStack");
        Widget preview_scroll=XtNameToWidget(shell,"*previewScroll");
        Widget preview_clip=NULL;
        Widget canvas_scroll=XtNameToWidget(shell,"*canvasScroll");
        Widget motif_scroll=XtNameToWidget(shell,"*motifReferenceScroll");
        if(preview_scroll)XtVaGetValues(preview_scroll,XmNclipWindow,&preview_clip,NULL);
        if(preview_stack)geometry(root,preview_stack,"preview_stack");
        if(preview_clip)geometry(root,preview_clip,"preview_clip");
        if(canvas_scroll)geometry(root,canvas_scroll,"preview_native_scroll");
        if(motif_scroll)geometry(root,motif_scroll,"preview_motif_scroll");
        Widget code=XtNameToWidget(shell,"*proposalCode");
        if(code) {char *text=XmTextGetString(code);json_object_object_add(root,"code",json_object_new_string(text));XtFree(text);}
        Widget shadow=XtNameToWidget(shell,"*partShadow*fieldValue");
        if(shadow) {geometry(root,shadow,"shadow");char *text=XmTextFieldGetString(shadow);
            json_object_object_add(root,"shadow_text",json_object_new_string(text));XtFree(text);}
        Widget gap=XtNameToWidget(shell,"*partGap*fieldValue");
        if(gap) {geometry(root,gap,"gap");char *text=XmTextFieldGetString(gap);
            json_object_object_add(root,"gap_text",json_object_new_string(text));XtFree(text);
            json_object_object_add(root,"gap_visible",json_object_new_boolean(XtIsManaged(XtParent(XtParent(gap)))));}
        Widget glyph=XtNameToWidget(shell,"*partGlyph*fieldValue");
        if(glyph) {
            char *text=XmTextFieldGetString(glyph);geometry(root,glyph,"glyph");
            json_object_object_add(root,"glyph_text",json_object_new_string(text));XtFree(text);
            json_object_object_add(root,"glyph_sensitive",json_object_new_boolean(XtIsSensitive(glyph)));
        }
        const char *history_names[]={"projectUndo","projectRedo","projectMark","projectRestore","projectResetPart"};
        for(int i=0;i<5;++i) {
            char query[80],sensitive[80];snprintf(query,sizeof(query),"*%s",history_names[i]);
            Widget button=XtNameToWidget(shell,query);if(!button)continue;
            geometry(root,button,history_names[i]);snprintf(sensitive,sizeof(sensitive),"%s_sensitive",history_names[i]);
            json_object_object_add(root,sensitive,json_object_new_boolean(XtIsSensitive(button)));
        }
        const char *tree_kinds[]={"Expand","CategoryCheck","Check","Control"};
        for(int kind=0;kind<4;kind++)for(int i=0;i<(kind<2?5:16);i++) {
            char name[80],query[90];snprintf(name,sizeof(name),"catalog%s%d",tree_kinds[kind],i);
            snprintf(query,sizeof(query),"*%s",name);Widget tree=XtNameToWidget(shell,query);
            if(tree)geometry(root,tree,name);
        }
        for(int i=0;i<5;i++) {
            char query[100],name[64];snprintf(query,sizeof(query),"*catalogCategory%d*categoryChildren",i);
            Widget children=XtNameToWidget(shell,query);snprintf(name,sizeof(name),"catalog_children%d",i);
            if(children)json_object_object_add(root,name,json_object_new_boolean(XtIsManaged(children)));
        }
        Widget recipe_clip=NULL;
        XtVaGetValues(XtNameToWidget(shell,"*recipeScroll"),XmNclipWindow,&recipe_clip,NULL);
        if(recipe_clip)geometry(root,recipe_clip,"recipe_clip");
        Widget state_combo=XtNameToWidget(shell,"*editState"),state_list=NULL;
        int state_selected=-1;
        XtVaGetValues(state_combo,XmNselectedPosition,&state_selected,XmNlist,&state_list,NULL);
        json_object_object_add(root,"edit_state_selected",json_object_new_int(state_selected));
        Dimension state_width,state_height,state_arrow,state_margin,state_shadow,state_highlight;
        Position state_x,state_y;
        XtTranslateCoords(state_combo,0,0,&state_x,&state_y);
        XtVaGetValues(state_combo,XmNwidth,&state_width,XmNheight,&state_height,
            XmNarrowSize,&state_arrow,XmNmarginWidth,&state_margin,
            XmNshadowThickness,&state_shadow,XmNhighlightThickness,&state_highlight,NULL);
        json_object *state_rect=json_object_new_array();
        int state_bounds[]={state_x+state_width-state_margin-state_shadow-state_highlight-state_arrow,
                            state_y+(state_height-state_arrow)/2,state_arrow,state_arrow};
        for(int n=0;n<4;n++)json_object_array_add(state_rect,json_object_new_int(state_bounds[n]));
        json_object_object_add(root,"edit_state_arrow",state_rect);
        if(state_list&&XtIsRealized(state_list)) {
            XWindowAttributes attrs;
            if(XGetWindowAttributes(XtDisplay(state_list),XtWindow(state_list),&attrs)&&attrs.map_state==IsViewable) {
                Position x,y,rx,ry;Dimension width,height;
                if(XmListPosToBounds(state_list,2,&x,&y,&width,&height)) {
                    XtTranslateCoords(state_list,x,y,&rx,&ry);
                    json_object *rect=json_object_new_array();int bounds[]={rx,ry,width,height};
                    for(int n=0;n<4;n++)json_object_array_add(rect,json_object_new_int(bounds[n]));
                    json_object_object_add(root,"edit_state_pressed_item",rect);
                }
                json_object *state_items=json_object_new_array();
                for(int pos=1;pos<=4;pos++) {
                    if(!XmListPosToBounds(state_list,pos,&x,&y,&width,&height))break;
                    XtTranslateCoords(state_list,x,y,&rx,&ry);
                    json_object *rect=json_object_new_array();int bounds[]={rx,ry,width,height};
                    for(int n=0;n<4;n++)json_object_array_add(rect,json_object_new_int(bounds[n]));
                    json_object_array_add(state_items,rect);
                }
                json_object_object_add(root,"edit_state_items",state_items);
            }
        }
        Widget family_combo=XtNameToWidget(shell,"*familyCombo"),family_list=NULL;
        geometry(root,family_combo,"family_combo");
        XtVaGetValues(family_combo,XmNlist,&family_list,NULL);
        if(family_list&&XtIsRealized(family_list)) {
            XWindowAttributes attrs;
            if(XGetWindowAttributes(XtDisplay(family_list),XtWindow(family_list),&attrs)&&attrs.map_state==IsViewable)
                for(int item=0;item<4;item+=3) {
                    Position x,y,rx,ry;Dimension w,h;
                    if(XmListPosToBounds(family_list,item+1,&x,&y,&w,&h)) {
                        char name[64];snprintf(name,sizeof(name),"family_item%d",item);
                        XtTranslateCoords(family_list,x,y,&rx,&ry);
                        json_object *rect=json_object_new_array();
                        json_object_array_add(rect,json_object_new_int(rx));json_object_array_add(rect,json_object_new_int(ry));
                        json_object_array_add(rect,json_object_new_int(w));json_object_array_add(rect,json_object_new_int(h));
                        json_object_object_add(root,name,rect);
                    }
                }
        }

        Widget actions=XtNameToWidget(shell,"*controllerActions");WidgetList children;Cardinal count;
        Widget notes=XtNameToWidget(shell,"*notesText");
        if(notes) {geometry(root,notes,"notes");char *s=XmTextGetString(notes);json_object_object_add(root,"notes_text",json_object_new_string(s));XtFree(s);}
        Widget menu=XtNameToWidget(width,"*textEditMenu");
        if(menu&&XtIsManaged(menu)) {
            WidgetList entries;Cardinal total;
            XtVaGetValues(menu,XtNchildren,&entries,XtNnumChildren,&total,NULL);
            json_object_object_add(root,"edit_menu_entries",json_object_new_int((int)total));
        }
        XtVaGetValues(actions,XtNchildren,&children,XtNnumChildren,&count,NULL);
        if(count)geometry(root,children[0],"apply");
        if(count>1)geometry(root,children[1],"save");
        if(count>2)geometry(root,children[2],"load");
        if(count>5)geometry(root,children[5],"export");
        if(count>8)geometry(root,children[8],"import_delta");
        if(count>9)geometry(root,children[9],"reconstruct_files");
        if(count>10)geometry(root,children[10],"manual_paint");
        if(count)geometry(root,children[count-1],"quit");
        Widget paint_label=XtNameToWidget(shell,"*nativeSampleLabel");
        if(paint_label) {
            XmString label=NULL;char *text=NULL;
            XtVaGetValues(paint_label,XmNlabelString,&label,NULL);
            if(label&&XmStringGetLtoR(label,XmFONTLIST_DEFAULT_TAG,&text)) {
                json_object_object_add(root,"paint_native_label",json_object_new_string(text));
                XtFree(text);
            }
        }
        Widget file=XtNameToWidget(shell,"*chooseRecipeFile");
        if(file&&XtIsManaged(file)) {
            geometry(root,XmFileSelectionBoxGetChild(file,XmDIALOG_TEXT),"file_path");
            geometry(root,XmFileSelectionBoxGetChild(file,XmDIALOG_OK_BUTTON),"file_ok");
            geometry(root,XmFileSelectionBoxGetChild(file,XmDIALOG_CANCEL_BUTTON),"file_cancel");
            json_object_object_add(root,"file_window",json_object_new_int64((int64_t)XtWindow(XtParent(file))));
        }
        Widget review=XtNameToWidget(shell,"*exportReview"),review_text=XtNameToWidget(shell,"*exportReviewText");
        if(review&&XtIsManaged(review)&&review_text) {
            char *text=XmTextGetString(review_text);
            json_object_object_add(root,"export_review_text",json_object_new_string(text));XtFree(text);
            geometry(root,XtNameToWidget(shell,"*closeExportReview"),"export_review_close");
        }
        char temporary[4096];snprintf(temporary,sizeof(temporary),"%s.tmp",path);
        if(!json_object_to_file_ext(temporary,root,JSON_C_TO_STRING_PLAIN))rename(temporary,path);
        json_object_put(root);
    }
    XtAppAddTimeOut(app,100,report,NULL);
}
TLView *__wrap_tl_view_create(Widget w,TLDispatch dispatch,void *context) {
    shell=w;app=XtWidgetToApplicationContext(w);
    controller_dispatch=dispatch;controller_context=context;
    TLView *view=__real_tl_view_create(w,observed_dispatch,NULL);
    observed_view=view;
    const char *names[]={"*pieceReliefState","*pieceReliefKind"};
    for(int i=0;i<2;i++) {
        Widget combo=XtNameToWidget(shell,names[i]);
        if(combo)XtAddCallback(combo,XmNselectionCallback,relief_observed,NULL);
    }
    XtAppAddTimeOut(app,100,report,NULL);return view;
}
int main(int argc,char **argv) {
    const char *path=getenv("TL_SPIN_FIXTURE");
    if(path) {TLModel model;char error[1024];tl_model_init(&model);model.selected=TL_GTK3;model.automatic_preview=0;const char *scheme=getenv("TL_SPIN_SCHEME_ID");
        snprintf(model.color_scheme,sizeof(model.color_scheme),"%s",scheme?scheme:"DomainOS-SR10.4");model.recipes[TL_GTK3].sizes[0][0]=220;model.recipes[TL_GTK3].sizes[0][1]=80;
        for(int i=10;i<=11;i++) {model.recipes[TL_GTK3].positions[i][0]=16;model.recipes[TL_GTK3].positions[i][1]=i==10?16:70;}
        model.recipes[TL_GTK3].sizes[10][0]=220;
        model.recipes[TL_GTK3].sizes[11][1]=180;
        if(getenv("TL_SPIN_SEPARATE_GTK3")&&!strcmp(getenv("TL_SPIN_SEPARATE_GTK3"),"1")) {
            model.recipes[TL_GTK3].visible_controls=1u<<13;
            model.recipes[TL_GTK3].selected_control=13;
            model.recipes[TL_GTK3].positions[13][0]=16;model.recipes[TL_GTK3].positions[13][1]=16;
            model.recipes[TL_GTK3].sizes[13][0]=220;model.recipes[TL_GTK3].sizes[13][1]=40;
        }
        if(getenv("TL_SPIN_GTK2")&&!strcmp(getenv("TL_SPIN_GTK2"),"1")) {
            model.selected=TL_GTK2;model.recipes[TL_GTK2]=model.recipes[TL_GTK3];
            model.recipes[TL_GTK2].visible_controls=(1u<<10)|(1u<<11);
            model.recipes[TL_GTK2].selected_control=10;
            if(getenv("TL_SPIN_GTK2_PROGRESS")&&!strcmp(getenv("TL_SPIN_GTK2_PROGRESS"),"1")) {
                model.recipes[TL_GTK2].visible_controls=1u<<13;
                model.recipes[TL_GTK2].selected_control=13;
                model.recipes[TL_GTK2].positions[13][0]=16;model.recipes[TL_GTK2].positions[13][1]=16;
                model.recipes[TL_GTK2].sizes[13][0]=220;model.recipes[TL_GTK2].sizes[13][1]=40;
            }
            if(getenv("TL_SPIN_GTK2_FRAME_CONTROL")&&!strcmp(getenv("TL_SPIN_GTK2_FRAME_CONTROL"),"1")) {
                model.recipes[TL_GTK2].visible_controls=1u<<15;
                model.recipes[TL_GTK2].selected_control=15;
                model.recipes[TL_GTK2].positions[15][0]=16;model.recipes[TL_GTK2].positions[15][1]=16;
                model.recipes[TL_GTK2].sizes[15][0]=220;model.recipes[TL_GTK2].sizes[15][1]=40;
            }
            if(getenv("TL_SPIN_GTK2_LIST_CONTROL")&&!strcmp(getenv("TL_SPIN_GTK2_LIST_CONTROL"),"1")) {
                model.recipes[TL_GTK2].visible_controls=1u<<14;
                model.recipes[TL_GTK2].selected_control=14;
                model.recipes[TL_GTK2].positions[14][0]=16;model.recipes[TL_GTK2].positions[14][1]=16;
                model.recipes[TL_GTK2].sizes[14][0]=220;model.recipes[TL_GTK2].sizes[14][1]=40;
            }
            if(getenv("TL_SPIN_GTK2_ARROW_CONTROL")&&!strcmp(getenv("TL_SPIN_GTK2_ARROW_CONTROL"),"1")) {
                model.recipes[TL_GTK2].visible_controls=1u<<12;
                model.recipes[TL_GTK2].selected_control=12;
                model.recipes[TL_GTK2].positions[12][0]=16;model.recipes[TL_GTK2].positions[12][1]=16;
                model.recipes[TL_GTK2].sizes[12][0]=220;model.recipes[TL_GTK2].sizes[12][1]=40;
            }
            if(getenv("TL_SPIN_GTK2_SCALE_CONTROL")&&
               (!strcmp(getenv("TL_SPIN_GTK2_SCALE_CONTROL"),"8")||!strcmp(getenv("TL_SPIN_GTK2_SCALE_CONTROL"),"9"))) {
                int control=atoi(getenv("TL_SPIN_GTK2_SCALE_CONTROL"));
                model.recipes[TL_GTK2].visible_controls=1u<<control;
                model.recipes[TL_GTK2].selected_control=control;
                model.recipes[TL_GTK2].positions[control][0]=16;model.recipes[TL_GTK2].positions[control][1]=16;
                model.recipes[TL_GTK2].sizes[control][0]=220;model.recipes[TL_GTK2].sizes[control][1]=40;
            }
            if(getenv("TL_SPIN_GTK2_SPIN_CONTROL")&&!strcmp(getenv("TL_SPIN_GTK2_SPIN_CONTROL"),"1")) {
                model.recipes[TL_GTK2].visible_controls=1u<<6;
                model.recipes[TL_GTK2].selected_control=6;
                model.recipes[TL_GTK2].positions[6][0]=16;model.recipes[TL_GTK2].positions[6][1]=16;
                model.recipes[TL_GTK2].sizes[6][0]=220;model.recipes[TL_GTK2].sizes[6][1]=40;
            }
            if(getenv("TL_SPIN_GTK2_COMBO_CONTROL")&&!strcmp(getenv("TL_SPIN_GTK2_COMBO_CONTROL"),"1")) {
                model.recipes[TL_GTK2].visible_controls=1u<<5;
                model.recipes[TL_GTK2].selected_control=5;
                model.recipes[TL_GTK2].positions[5][0]=16;model.recipes[TL_GTK2].positions[5][1]=16;
                model.recipes[TL_GTK2].sizes[5][0]=220;model.recipes[TL_GTK2].sizes[5][1]=40;
            }
            if(getenv("TL_SPIN_GTK2_TEXT_CONTROL")&&!strcmp(getenv("TL_SPIN_GTK2_TEXT_CONTROL"),"1")) {
                model.recipes[TL_GTK2].visible_controls=1u<<7;
                model.recipes[TL_GTK2].selected_control=7;
                model.recipes[TL_GTK2].positions[7][0]=16;model.recipes[TL_GTK2].positions[7][1]=16;
                model.recipes[TL_GTK2].sizes[7][0]=220;model.recipes[TL_GTK2].sizes[7][1]=40;
            }
            if(getenv("TL_SPIN_GTK2_ENTRY_CONTROL")&&!strcmp(getenv("TL_SPIN_GTK2_ENTRY_CONTROL"),"1")) {
                model.recipes[TL_GTK2].visible_controls=1u<<4;
                model.recipes[TL_GTK2].selected_control=4;
                model.recipes[TL_GTK2].positions[4][0]=16;model.recipes[TL_GTK2].positions[4][1]=16;
                model.recipes[TL_GTK2].sizes[4][0]=220;model.recipes[TL_GTK2].sizes[4][1]=40;
            }
            if(getenv("TL_SPIN_GTK2_CHECK")&&!strcmp(getenv("TL_SPIN_GTK2_CHECK"),"1")) {
                model.recipes[TL_GTK2].visible_controls|=4u;
                model.recipes[TL_GTK2].selected_control=2;
                model.recipes[TL_GTK2].positions[2][0]=20;model.recipes[TL_GTK2].positions[2][1]=90;
                model.recipes[TL_GTK2].sizes[2][0]=180;model.recipes[TL_GTK2].sizes[2][1]=50;
                model.recipes[TL_GTK2].positions[10][1]=200;
                model.recipes[TL_GTK2].positions[11][0]=500;
            }
            if(getenv("TL_SPIN_GTK2_RADIO")&&!strcmp(getenv("TL_SPIN_GTK2_RADIO"),"1")) {
                model.recipes[TL_GTK2].visible_controls|=1u<<3;
                model.recipes[TL_GTK2].selected_control=3;
                model.recipes[TL_GTK2].positions[3][0]=260;model.recipes[TL_GTK2].positions[3][1]=20;
                model.recipes[TL_GTK2].sizes[3][0]=180;model.recipes[TL_GTK2].sizes[3][1]=100;
                model.recipes[TL_GTK2].positions[10][1]=200;
                model.recipes[TL_GTK2].positions[11][0]=600;
            }
            if(getenv("TL_SPIN_GTK2_PUSH")&&!strcmp(getenv("TL_SPIN_GTK2_PUSH"),"1")) {
                model.recipes[TL_GTK2].visible_controls|=1u;
                model.recipes[TL_GTK2].selected_control=0;
                model.recipes[TL_GTK2].sizes[0][0]=180;model.recipes[TL_GTK2].sizes[0][1]=50;
                model.recipes[TL_GTK2].positions[10][1]=100;
                model.recipes[TL_GTK2].positions[11][0]=400;
            }
            if(getenv("TL_SPIN_GTK2_TOGGLE")&&!strcmp(getenv("TL_SPIN_GTK2_TOGGLE"),"1")) {
                model.recipes[TL_GTK2].visible_controls|=3u;
                model.recipes[TL_GTK2].selected_control=1;
                model.recipes[TL_GTK2].positions[0][0]=20;model.recipes[TL_GTK2].positions[0][1]=20;
                model.recipes[TL_GTK2].positions[1][0]=20;model.recipes[TL_GTK2].positions[1][1]=90;
                model.recipes[TL_GTK2].sizes[1][0]=180;model.recipes[TL_GTK2].sizes[1][1]=50;
                model.recipes[TL_GTK2].positions[10][1]=200;
                model.recipes[TL_GTK2].positions[11][0]=500;
            }
        }
        if(getenv("TL_SPIN_GTK4_PUSH")&&!strcmp(getenv("TL_SPIN_GTK4_PUSH"),"1")) {
            model.selected=TL_GTK4;
            model.recipes[TL_GTK4].selected_control=0;
            if(!(getenv("TL_SPIN_GTK4_ALL")&&!strcmp(getenv("TL_SPIN_GTK4_ALL"),"1"))) {
                model.recipes[TL_GTK4].visible_controls=1;
                model.recipes[TL_GTK4].positions[0][0]=32;model.recipes[TL_GTK4].positions[0][1]=32;
                model.recipes[TL_GTK4].sizes[0][0]=180;model.recipes[TL_GTK4].sizes[0][1]=50;
            }
            if(getenv("TL_SPIN_GTK4_TOGGLE")&&!strcmp(getenv("TL_SPIN_GTK4_TOGGLE"),"1")) {
                model.recipes[TL_GTK4].visible_controls=2;
                model.recipes[TL_GTK4].selected_control=1;
                model.recipes[TL_GTK4].positions[1][0]=32;model.recipes[TL_GTK4].positions[1][1]=32;
                model.recipes[TL_GTK4].sizes[1][0]=180;model.recipes[TL_GTK4].sizes[1][1]=50;
            }
        }
        if(tl_model_save(&model,path,error,sizeof(error))) {fprintf(stderr,"%s\n",error);return 1;}}
    return tl_controller_run(argc,argv);
}
