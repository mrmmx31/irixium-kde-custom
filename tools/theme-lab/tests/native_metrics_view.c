/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "theme_lab.h"
#include "native_font_motif.h"
#include "native_pair_motif.h"
#include "native_parts_motif.h"
#include "sample_controls.h"
#include "ui_hints.h"
#include "manual_paint_view.h"
#include "manual_paint_recovery.h"
#include "text_editor.h"
#include <X11/Xutil.h>
#include <X11/extensions/Xfixes.h>
#include <Xm/Label.h>
#include <Xm/ArrowB.h>
#include <Xm/CascadeB.h>
#include <Xm/ComboBox.h>
#include <Xm/List.h>
#include <Xm/PushB.h>
#include <Xm/Scale.h>
#include <Xm/ScrollBar.h>
#include <Xm/ScrolledW.h>
#include <Xm/SpinB.h>
#include <Xm/Text.h>
#include <Xm/TextF.h>
#include <Xm/FileSB.h>
#include <Xm/MessageB.h>
#include <X11/keysym.h>
#include <Xm/ToggleB.h>
#include <Xm/VendorS.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <string.h>
#include <locale.h>
#include <unistd.h>
#include <dlfcn.h>
#define CHECK(x) do { if (!(x)) { fprintf(stderr,"metrics view: line %d\n",__LINE__); exit(1); } } while(0)
void tl_test_help_native(Widget shell);
void tl_test_export_review_native(TLView *view,Widget shell);
void tl_test_file_dialog_native(TLView *view,Widget shell);
void tl_test_history_hover(TLView *view,Widget shell);
void tl_test_dynamic_hints(TLView *view,Widget shell,TLModel *model);
static TLAction dispatched_action;
static int dispatched_action_valid = 0;
static int dispatch_count = 0;
static void dispatch(void *data, TLAction action, int argument) {
    (void)data;
    (void)argument;
    dispatched_action = action;
    dispatched_action_valid = 1;
    ++dispatch_count;
}
static void timer(XtPointer data, XtIntervalId *id) { *(int *)data=1; (void)id; }
static void drain(XtAppContext app) {
    int finished=0;
    (void)XtAppAddTimeOut(app,80,timer,&finished);
    while(!finished) XtAppProcessEvent(app,XtIMAll);
}
static void expect_pixel_rgb(Widget widget, const char *resource,
                             const unsigned short expected[3]) {
    Pixel pixel = 0;
    Colormap colormap;
    XColor color;
    XtVaGetValues(widget, resource, &pixel, NULL);
    XtVaGetValues(widget, XmNcolormap, &colormap, NULL);
    color.pixel = pixel;
    CHECK(XQueryColor(XtDisplay(widget), colormap, &color));
    CHECK(abs((int)color.red - expected[0]) <= 257);
    CHECK(abs((int)color.green - expected[1]) <= 257);
    CHECK(abs((int)color.blue - expected[2]) <= 257);
}
static void check_header_layout_palette(TLView *view, Widget shell,
                                        XtAppContext app) {
    const unsigned short body[6][3] = {
        {0x2222, 0x4444, 0x6666}, {0xffff, 0xeeee, 0xdddd},
        {0x1111, 0x2222, 0x3333}, {0x7777, 0x8888, 0x9999},
        {0xaaaa, 0xbbbb, 0xcccc}, {0x0808, 0x1010, 0x1818}};
    const unsigned short header[6][3] = {
        {0x1234, 0x789a, 0xbcde}, {0xffff, 0xffff, 0xffff},
        {0x1234, 0x789a, 0xbcde}, {0x1234, 0x789a, 0xbcde},
        {0x8888, 0xbbbb, 0xeeee}, {0x0808, 0x3030, 0x5050}};
    Widget root = XtNameToWidget(shell, "*themeLabView");
    Widget menu = XtNameToWidget(shell, "*laboratoryHelpMenu");
    Widget workspace = XtNameToWidget(shell, "*themeLabWorkspace");
    Widget panels = XtNameToWidget(shell, "*threePanels");
    Position rx, ry, mx, my, wx, wy, px, py;
    Dimension rw, rh, mw, mh, ww, wh;
    CHECK(root && menu && workspace && panels);
    tl_view_palette(view, body);
    tl_view_header_palette(view, header);
    drain(app);
    XtTranslateCoords(root, 0, 0, &rx, &ry);
    XtTranslateCoords(menu, 0, 0, &mx, &my);
    XtTranslateCoords(workspace, 0, 0, &wx, &wy);
    XtTranslateCoords(panels, 0, 0, &px, &py);
    XtVaGetValues(root, XmNwidth, &rw, XmNheight, &rh, NULL);
    XtVaGetValues(menu, XmNwidth, &mw, XmNheight, &mh, NULL);
    XtVaGetValues(workspace, XmNwidth, &ww, XmNheight, &wh, NULL);
    CHECK(mx == rx && my == ry && mw == rw);
    CHECK(wx == rx && wy >= my + (Position)mh && ww == rw);
    CHECK(px > wx && py > wy && wh <= rh);
    expect_pixel_rgb(menu, XmNbackground, header[0]);
    expect_pixel_rgb(workspace, XmNbackground, body[0]);

    Widget left_panel = XtNameToWidget(shell, "*leftToolPanel");
    Widget page_selector = XtNameToWidget(shell, "*leftPanelSelector");
    Widget page_host = XtNameToWidget(shell, "*recipeEditor");
    Widget motif_panel = XtNameToWidget(shell, "*motifReferenceFrame");
    Widget target_panel = XtNameToWidget(shell, "*nativePreview");
    CHECK(left_panel && page_selector && page_host && motif_panel && target_panel);
    WidgetList page_children = NULL;
    Cardinal page_count = 0;
    int named_pages = 0, managed_pages = 0;
    XtVaGetValues(page_host, XtNchildren, &page_children,
                  XtNnumChildren, &page_count, NULL);
    for (Cardinal i = 0; i < page_count; ++i) {
        if (strcmp(XtName(page_children[i]), "leftPanelPage") != 0)
            continue;
        ++named_pages;
        if (XtIsManaged(page_children[i])) ++managed_pages;
    }
    CHECK(named_pages == 6 && managed_pages == 1);
    XmString *page_items = NULL;
    XtVaGetValues(page_selector, XmNitems, &page_items, NULL);
    XmComboBoxCallbackStruct page_change = {
        .reason = XmCR_SELECT, .event = NULL,
        .item_or_text = page_items[3], .item_position = 3};
    XtVaSetValues(page_selector, XmNselectedPosition, 3, NULL);
    XtCallCallbacks(page_selector, XmNselectionCallback, &page_change);
    drain(app);
    int logical_page = 0;
    managed_pages = 0;
    for (Cardinal i = 0; i < page_count; ++i) {
        if (strcmp(XtName(page_children[i]), "leftPanelPage") != 0)
            continue;
        if (XtIsManaged(page_children[i])) {
            ++managed_pages;
            CHECK(logical_page == 3);
        }
        ++logical_page;
    }
    CHECK(managed_pages == 1);
    static const struct {
        const char *path;
        TLAction action;
    } menu_actions[] = {
        {"*menuSave", TL_SAVE},
        {"*menuHistoricalImage", TL_REFERENCE},
        {"*menuRefresh", TL_APPLY},
        {"*menuManualPaint", TL_MANUAL_PAINT},
        {"*projectUndoMenu", TL_PROJECT_UNDO}
    };
    for (size_t i = 0; i < sizeof(menu_actions) / sizeof(menu_actions[0]); ++i) {
        Widget item = XtNameToWidget(shell, (char *)menu_actions[i].path);
        CHECK(item);
        int before = dispatch_count;
        dispatched_action_valid = 0;
        XtCallCallbacks(item, XmNactivateCallback, NULL);
        CHECK(dispatch_count == before + 1 &&
              dispatched_action_valid &&
              dispatched_action == menu_actions[i].action);
    }
    Position lx, ly, tx, ty;
    Dimension lw, lh, tw, th;
    XtTranslateCoords(motif_panel, 0, 0, &lx, &ly);
    XtTranslateCoords(target_panel, 0, 0, &tx, &ty);
    XtVaGetValues(motif_panel, XmNwidth, &lw, XmNheight, &lh, NULL);
    XtVaGetValues(target_panel, XmNwidth, &tw, XmNheight, &th, NULL);
    CHECK(tx >= lx + (Position)lw && abs((int)lw - (int)tw) <= 16);
    CHECK(abs((int)lh - (int)th) <= 2 && ly == ty);

    const char *tmpdir = getenv("TMPDIR");
    char path[4096], error[256];
    CHECK(tmpdir && tmpdir[0] == '/');
    CHECK(snprintf(path, sizeof(path), "%s/manual-paint-header-XXXXXX",
                   tmpdir) > 0);
    int fd = mkstemp(path);
    CHECK(fd >= 0 && close(fd) == 0 && unlink(path) == 0);
    TLManualPaint *document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_save(document, path, error,
                                           sizeof(error)) == 0);
    tl_manual_paint_free(document);
    CHECK(tl_view_manual_paint_open(view, path, TL_MOTIF, 0, 0) == 0);
    drain(app);
    Widget paint_shell = XtNameToWidget(shell, "*manualPaintEditor");
    Widget paint_root = XtNameToWidget(paint_shell, "*manualPaintRoot");
    Widget paint_menu = XtNameToWidget(paint_shell, "*manualPaintMenuBar");
    Widget paint_workspace = XtNameToWidget(paint_shell, "*manualPaintForm");
    Widget paint_sidebar = XtNameToWidget(paint_shell, "*manualPaintSidebarScroll");
    Widget paint_main = XtNameToWidget(paint_shell, "*manualPaintMain");
    Widget paint_combo = XtNameToWidget(paint_shell, "*paintFamily");
    CHECK(paint_shell && paint_root && paint_menu && paint_workspace &&
          paint_sidebar && paint_main && paint_combo);
    XtTranslateCoords(paint_root, 0, 0, &rx, &ry);
    XtTranslateCoords(paint_menu, 0, 0, &mx, &my);
    XtTranslateCoords(paint_workspace, 0, 0, &wx, &wy);
    XtVaGetValues(paint_root, XmNwidth, &rw, NULL);
    XtVaGetValues(paint_menu, XmNwidth, &mw, XmNheight, &mh, NULL);
    XtVaGetValues(paint_workspace, XmNwidth, &ww, NULL);
    CHECK(mx == rx && my == ry && mw == rw);
    CHECK(wx == rx && wy >= my + (Position)mh && ww == rw);
    Position sx, sy, ax, ay;
    Dimension sw, sh, aw, ah;
    XtTranslateCoords(paint_sidebar, 0, 0, &sx, &sy);
    XtTranslateCoords(paint_main, 0, 0, &ax, &ay);
    XtVaGetValues(paint_sidebar, XmNwidth, &sw, XmNheight, &sh, NULL);
    XtVaGetValues(paint_main, XmNwidth, &aw, XmNheight, &ah, NULL);
    CHECK(sx >= wx && sy >= wy && ax >= sx + (Position)sw);
    CHECK(abs((int)sh - (int)ah) <= 2 && sw < aw);
    expect_pixel_rgb(paint_menu, XmNbackground, header[0]);
    expect_pixel_rgb(paint_workspace, XmNbackground, body[0]);
    expect_pixel_rgb(paint_combo, XmNbackground, body[0]);
    const char *capture_wait = getenv("TL_LAYOUT_CAPTURE_WAIT");
    if (capture_wait) {
        unsigned long seconds = strtoul(capture_wait, NULL, 10);
        if (seconds > 10) seconds = 10;
        sleep((unsigned int)seconds);
    }
    CHECK(unlink(path) == 0);
    puts("Theme Lab layout: full-width menu bands, dynamic Header/Button roles and left-tools/manual-canvas split verified.");
}
static char *text(Widget label) {
    XmString value;
    XtVaGetValues(label,XmNlabelString,&value,NULL);
    return XmStringUnparse(value,NULL,XmCHARSET_TEXT,XmMULTIBYTE_TEXT,NULL,0,XmOUTPUT_ALL);
}
static void compact_hint(char *value){
    char *out=value;
    for(char *p=value;*p;++p)if(*p!=' '&&*p!='\n'&&*p!='\r'&&*p!='\t')*out++=*p;
    *out=0;
}
static int has_native_hint(Widget w) {
    if(XmIsPrimitive(w)||XmIsGadget(w)) {
        XmString tip=NULL;XtVaGetValues(w,XmNtoolTipString,&tip,NULL);
        if(tip) {
            char *value=XmStringUnparse(tip,NULL,XmCHARSET_TEXT,XmMULTIBYTE_TEXT,NULL,0,XmOUTPUT_ALL);
            int valid=value&&strlen(value)>35;XtFree(value);if(valid)return 1;
        }
    }
    if(XtIsComposite(w)) {
        WidgetList children=NULL;Cardinal count=0;
        XtVaGetValues(w,XtNchildren,&children,XtNnumChildren,&count,NULL);
        for(Cardinal i=0;i<count;++i)if(has_native_hint(children[i]))return 1;
    }
    return 0;
}
static int is_interactive_widget(Widget w) {
    return XtIsSubclass(w,xmArrowButtonWidgetClass) ||
           XtIsSubclass(w,xmCascadeButtonWidgetClass) ||
           XtIsSubclass(w,xmComboBoxWidgetClass) ||
           XtIsSubclass(w,xmListWidgetClass) ||
           XtIsSubclass(w,xmPushButtonWidgetClass) ||
           XtIsSubclass(w,xmScaleWidgetClass) ||
           XtIsSubclass(w,xmScrollBarWidgetClass) ||
           XtIsSubclass(w,xmSpinBoxWidgetClass) ||
           XtIsSubclass(w,xmTextFieldWidgetClass) ||
           XtIsSubclass(w,xmTextWidgetClass) ||
           XtIsSubclass(w,xmToggleButtonWidgetClass);
}
static int has_direct_hint(Widget w) {
    if(!XmIsPrimitive(w)&&!XmIsGadget(w))return 0;
    XmString tip=NULL;XtVaGetValues(w,XmNtoolTipString,&tip,NULL);
    return tip!=NULL;
}
static void audit_interactive_hints(Widget w,int *checked,int *direct,
                                    int *delegated,int *missing) {
    if(is_interactive_widget(w)) {
        ++*checked;
        if(has_direct_hint(w))++*direct;
        else if(has_native_hint(w))++*delegated;
        else {
            ++*missing;
            fprintf(stderr,"Interactive widget without native hint: %s\n",XtName(w));
        }
    }
    if(XtIsComposite(w)) {
        WidgetList children=NULL;Cardinal count=0;
        XtVaGetValues(w,XtNchildren,&children,XtNnumChildren,&count,NULL);
        for(Cardinal i=0;i<count;++i)
            audit_interactive_hints(children[i],checked,direct,delegated,missing);
    }
}
static void check_hints(Widget shell) {
    static const char *const paths[]={
        "*familyCombo","*schemeCombo","*automaticPreview","*separatePreview",
        "*delayRow*fieldValue","*catalogControl0","*editState",
        "*positionX*fieldValue","*positionY*fieldValue",
        "*modelNameRow*fieldValue","*referencePathRow*fieldValue",
        "*bar_px*fieldValue","*font_px*fieldValue","*factorRow*fieldValue",
        "*gtk2ScaleWidth*fieldValue","*gtk2ScaleLength*fieldValue",
        "*roleRow*fieldValue","*notesText","*proposalCode","*controllerAction",
        "*lengthAnchor","*scrollPartCombo","*controlWidth*fieldValue",
        "*partGlyph*fieldValue","*partShadow*fieldValue","*partGap*fieldValue",
        "*pieceReliefState","*pieceReliefKind",
        "*projectUndo","*projectRedo","*projectMark","*projectRestore","*projectResetPart"
    };
    for(size_t i=0;i<sizeof(paths)/sizeof(*paths);++i) {
        Widget w=XtNameToWidget(shell,(char*)paths[i]);
        if(!w)fprintf(stderr,"Missing hint widget: %s\n",paths[i]);
        CHECK(w);
        if(!has_native_hint(w))fprintf(stderr,"Missing native hint: %s\n",paths[i]);
        CHECK(has_native_hint(w));
    }
    int delay=0,duration=0;Boolean enabled=False;
    const char *scrolled_paths[]={"*recipeScroll","*previewScroll","*motifReferenceScroll","*imageReferenceScroll"};
    for(size_t i=0;i<sizeof(scrolled_paths)/sizeof(*scrolled_paths);++i) {
        Widget area=XtNameToWidget(shell,(char*)scrolled_paths[i]),horizontal=NULL,vertical=NULL;
        CHECK(area);XtVaGetValues(area,XmNhorizontalScrollBar,&horizontal,XmNverticalScrollBar,&vertical,NULL);
        CHECK(horizontal&&vertical&&has_native_hint(horizontal)&&has_native_hint(vertical));
    }
    XtVaGetValues(shell,XmNtoolTipEnable,&enabled,XmNtoolTipPostDelay,&delay,
                  XmNtoolTipPostDuration,&duration,NULL);
    CHECK(enabled&&delay==750&&duration==6000);
    CHECK(tl_ui_action_hint(-1)==NULL&&tl_ui_action_hint(12)==NULL);
    CHECK(tl_ui_action_hint(11)!=NULL);
    CHECK(tl_ui_geometry_hint(-1)==NULL&&tl_ui_geometry_hint(TL_FIELD_COUNT)==NULL);
    CHECK(tl_ui_motif_control_hint(-1)==NULL&&tl_ui_motif_control_hint(TL_CONTROL_COUNT)==NULL);
    static const char *const native_names[]={
        "nativePushButton","nativeToggleButton","nativeCheckButton","nativeRadioButton",
        "nativeTextField","nativeComboBox","nativeSpinBox","nativeMultilineText",
        "nativeHorizontalScale","nativeVerticalScale","nativeHorizontalScrollBar",
        "nativeVerticalScrollBar","nativeArrowButton","nativeLevelScale","nativeList","nativeControlFrame"
    };
    const char *panes[]={"nativePreviewControls","motifReferenceControls"};
    for(int p=0;p<2;++p)for(int i=0;i<TL_CONTROL_COUNT;++i){
        char path[160];snprintf(path,sizeof(path),"*%s.%s",panes[p],native_names[i]);
        Widget w=XtNameToWidget(shell,path);CHECK(w&&has_native_hint(w));
    }
    Widget parent=XtNameToWidget(shell,"*controllerActions");WidgetList children=NULL;Cardinal count=0;
    CHECK(parent);XtVaGetValues(parent,XtNchildren,&children,XtNnumChildren,&count,NULL);CHECK(count==12);
    for(Cardinal i=0;i<count;++i) {
        XmString tip=NULL;XtVaGetValues(children[i],XmNtoolTipString,&tip,NULL);CHECK(tip);
        char *value=XmStringUnparse(tip,NULL,XmCHARSET_TEXT,XmMULTIBYTE_TEXT,NULL,0,XmOUTPUT_ALL);
        char expected[512];snprintf(expected,sizeof(expected),"%s",tl_ui_action_hint((int)i));
        /* XmStringUnparse without separator mappings omits line breaks.
           Compare the original UTF-8 payload independently of wrapping. */
        compact_hint(expected);if(value)compact_hint(value);
        CHECK(value&&!strcmp(value,expected));XtFree(value);
    }
    puts("T07: native selectors, numeric fields, twelve action tips and tooltip policy verified.");
}
static void check_gtk2_scale_recipe(TLView *view, Widget shell, TLModel *model) {
    TLModel candidate;
    char error[256];
    Widget group=XtNameToWidget(shell,"*gtk2ScaleGeometry");
    Widget width=XtNameToWidget(shell,"*gtk2ScaleWidth*fieldValue");
    Widget length=XtNameToWidget(shell,"*gtk2ScaleLength*fieldValue");
    CHECK(group&&width&&length);
    model->selected=TL_GTK2;
    model->recipes[TL_GTK2].scale_slider_width_px=9;
    model->recipes[TL_GTK2].scale_slider_length_px=33;
    tl_view_update(view,model);
    CHECK(XtIsSensitive(group));
    char *shown_width=XmTextFieldGetString(width);
    char *shown_length=XmTextFieldGetString(length);
    CHECK(!strcmp(shown_width,"9")&&!strcmp(shown_length,"33"));
    XtFree(shown_width);XtFree(shown_length);
    CHECK(tl_view_read(view,&candidate,error,sizeof(error))==0);
    CHECK(candidate.recipes[TL_GTK2].scale_slider_width_px==9);
    CHECK(candidate.recipes[TL_GTK2].scale_slider_length_px==33);
    model->selected=TL_GTK3;
    tl_view_update(view,model);
    CHECK(!XtIsSensitive(group));
}
static unsigned long color_input(const char *name){
    const char *s=getenv(name);char *end=NULL;CHECK(s&&*s);
    unsigned long rgb=strtoul(s,&end,16);CHECK(end&&!*end&&rgb<=0xffffffUL);return rgb;
}
static void check_hint_palette(TLView *view,Widget shell){
    unsigned long face=color_input("TL_HINT_FACE"),text_color=color_input("TL_HINT_TEXT");
    unsigned long content=getenv("TL_HINT_VIEW")?color_input("TL_HINT_VIEW"):face;
    unsigned short rgb[6][3];
    for(int i=0;i<6;++i){unsigned long v=i==1?text_color:i==2?content:face;
        rgb[i][0]=(unsigned short)(((v>>16)&255)*257);
        rgb[i][1]=(unsigned short)(((v>>8)&255)*257);
        rgb[i][2]=(unsigned short)((v&255)*257);
    }
    tl_view_palette(view,rgb);
    Widget tip=XmToolTipGetLabel(shell);CHECK(tip);
    Pixel fg,bg;Colormap map;XColor colors[2];
    XtVaGetValues(tip,XmNforeground,&fg,XmNbackground,&bg,XmNcolormap,&map,NULL);
    colors[0].pixel=bg;colors[1].pixel=fg;XQueryColors(XtDisplay(shell),map,colors,2);
    for(int i=0;i<2;++i){
        CHECK(abs((int)colors[i].red-rgb[i][0])<=257);
        CHECK(abs((int)colors[i].green-rgb[i][1])<=257);
        CHECK(abs((int)colors[i].blue-rgb[i][2])<=257);
    }
    const char *help_paths[]={"*helpCascade","*helpTopic0","*helpText","*closeHelp"};
    Pixel helper_fg[4],helper_bg[4];
    for(int i=0;i<4;++i){
        Widget w=XtNameToWidget(shell,(char*)help_paths[i]);CHECK(w);
        XtVaGetValues(w,XmNforeground,&helper_fg[i],XmNbackground,&helper_bg[i],XmNcolormap,&map,NULL);
        colors[0].pixel=helper_bg[i];colors[1].pixel=helper_fg[i];XQueryColors(XtDisplay(shell),map,colors,2);
        int background=i==2?2:0;
        CHECK(abs((int)colors[0].red-rgb[background][0])<=257&&abs((int)colors[0].green-rgb[background][1])<=257&&abs((int)colors[0].blue-rgb[background][2])<=257);
        CHECK(abs((int)colors[1].red-rgb[1][0])<=257&&abs((int)colors[1].green-rgb[1][1])<=257&&abs((int)colors[1].blue-rgb[1][2])<=257);
    }
    /* A different preview palette must not recolor tool/editor help. */
    for(int i=0;i<6;++i)for(int j=0;j<3;++j)rgb[i][j]=(unsigned short)(65535-rgb[i][j]);
    tl_view_preview_palette(view,rgb);
    Pixel next_fg,next_bg;XtVaGetValues(tip,XmNforeground,&next_fg,XmNbackground,&next_bg,NULL);
    CHECK(next_fg==fg&&next_bg==bg);
    for(int i=0;i<4;++i){
        Widget w=XtNameToWidget(shell,(char*)help_paths[i]);
        XtVaGetValues(w,XmNforeground,&next_fg,XmNbackground,&next_bg,NULL);
        CHECK(next_fg==helper_fg[i]&&next_bg==helper_bg[i]);
    }
    XmFontList fonts=NULL;XtVaGetValues(tip,XmNfontList,&fonts,NULL);CHECK(fonts);
    XmFontContext context;CHECK(XmFontListInitFontContext(&context,fonts));
    XmFontListEntry entry=XmFontListNextEntry(context);CHECK(entry);
    XmFontType type;CHECK(XmFontListEntryGetFont(entry,&type));CHECK(type==XmFONT_IS_FONTSET);
    XmFontListFreeFontContext(context);
    puts("T07: tooltip follows UI roles, preserves preview isolation and uses UTF-8 FontSet.");
}
static void paint_hint_timer(XtPointer data, XtIntervalId *id) {
    *(int *)data = 1;
    (void)id;
}
static void paint_hint_wait(XtAppContext app, unsigned long milliseconds) {
    int finished = 0;
    XtAppAddTimeOut(app, milliseconds, paint_hint_timer, &finished);
    while (!finished)
        XtAppProcessEvent(app, XtIMAll);
}
static int paint_hint_viewable(Widget widget) {
    XWindowAttributes attributes;
    return widget && XtIsRealized(widget) &&
           XGetWindowAttributes(XtDisplay(widget), XtWindow(widget), &attributes) &&
           attributes.map_state == IsViewable;
}
typedef struct {
    int calls;
    TLManualPaintSampleRequest request;
} PaintReferenceCapture;
static void paint_reference_changed(void *context,
                                    const TLManualPaintSampleRequest *request) {
    PaintReferenceCapture *capture = context;
    CHECK(capture && request);
    capture->calls++;
    capture->request = *request;
}
static void paint_hint_hover(Widget widget) {
    Position x, y;
    Dimension width, height;
    XtVaGetValues(widget, XmNwidth, &width, XmNheight, &height, NULL);
    XtTranslateCoords(widget, (Position)(width / 2), (Position)(height / 2), &x, &y);
    XWarpPointer(XtDisplay(widget), None, DefaultRootWindow(XtDisplay(widget)),
                 0, 0, 0, 0, x, y);
    XFlush(XtDisplay(widget));
}
static void check_manual_paint_hints(Widget parent, XtAppContext app) {
    const char *tmpdir = getenv("TMPDIR");
    char path[4096], error[256];
    int fd, checked = 0, direct = 0, delegated = 0, missing = 0;
    CHECK(tmpdir && tmpdir[0] == '/');
    CHECK(snprintf(path, sizeof(path), "%s/manual-paint-hints-XXXXXX", tmpdir) > 0);
    fd = mkstemp(path);
    CHECK(fd >= 0 && close(fd) == 0 && unlink(path) == 0);
    TLManualPaint *document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_save(document, path, error, sizeof(error)) == 0);
    tl_manual_paint_free(document);
    TLManualPaintView *paint = tl_manual_paint_view_open(
        parent, path, TL_MOTIF, 0, 0, NULL, NULL, NULL, NULL, NULL,
        NULL, NULL);
    CHECK(paint);
    tl_manual_paint_view_present(paint);
    Widget shell = XtNameToWidget(parent, "*manualPaintEditor");
    CHECK(shell);
    paint_hint_wait(app, 100);
    audit_interactive_hints(shell, &checked, &direct, &delegated, &missing);
    CHECK(checked >= 30 && missing == 0);
    static const struct {
        const char *canvas;
        const char *source;
        const char *text;
    } canvases[] = {
        {"*referenceSampleCanvas", "*referenceSampleLabel", "zoom"},
        {"*nativeSampleCanvas", "*nativeSampleLabel", "Prévia nativa atual"},
        {"*manualPaintCanvas", "*manualSampleLabel", "pixels de arte"}
    };
    Widget sidebar_scroll = XtNameToWidget(shell, "*manualPaintSidebarScroll");
    CHECK(sidebar_scroll);
    for (size_t i = 0; i < sizeof(canvases) / sizeof(canvases[0]); ++i) {
        Widget canvas = XtNameToWidget(shell, (char *)canvases[i].canvas);
        Widget source = XtNameToWidget(shell, (char *)canvases[i].source);
        CHECK(canvas && source && has_direct_hint(source));
        if (i < 2) {
            XmScrollVisible(sidebar_scroll, canvas, 4, 4);
            paint_hint_wait(app, 120);
        }
        XmString compound = NULL;
        XtVaGetValues(source, XmNtoolTipString, &compound, NULL);
        char *tip = XmStringUnparse(compound, NULL, XmCHARSET_TEXT,
                                    XmMULTIBYTE_TEXT, NULL, 0, XmOUTPUT_ALL);
        if (!tip || !strstr(tip, canvases[i].text))
            fprintf(stderr, "paint hint mismatch: %s expected [%s], got [%s]\n",
                    canvases[i].source, canvases[i].text, tip ? tip : "(null)");
        CHECK(tip && strstr(tip, canvases[i].text));
        XtFree(tip);
        Widget label = XtNameToWidget(canvas, "surfaceHint.surfaceHintLabel");
        CHECK(label);
        paint_hint_hover(canvas);
        paint_hint_wait(app, 1300);
        CHECK(paint_hint_viewable(label));
        Position tx, ty, ox, oy;
        Dimension tw, th, ow, oh;
        XtTranslateCoords(label, 0, 0, &tx, &ty);
        XtTranslateCoords(canvas, 0, 0, &ox, &oy);
        XtVaGetValues(label, XmNwidth, &tw, XmNheight, &th, NULL);
        XtVaGetValues(canvas, XmNwidth, &ow, XmNheight, &oh, NULL);
        int overlap = tx < ox + ow && tx + tw > ox &&
                      ty < oy + oh && ty + th > oy;
        CHECK(!overlap && tx >= 0 && ty >= 0 &&
              tx + tw <= WidthOfScreen(XtScreen(canvas)) &&
              ty + th <= HeightOfScreen(XtScreen(canvas)));
        for (int sample = 0; sample < 3; ++sample) {
            paint_hint_wait(app, 100);
            CHECK(paint_hint_viewable(label));
            Position sx, sy;
            XtTranslateCoords(label, 0, 0, &sx, &sy);
            CHECK(sx == tx && sy == ty);
        }
        XWarpPointer(XtDisplay(parent), None, DefaultRootWindow(XtDisplay(parent)),
                     0, 0, 0, 0, 1550, 880);
        XFlush(XtDisplay(parent));
        paint_hint_wait(app, 120);
        CHECK(!paint_hint_viewable(label));
    }
    printf("T07 Paint: %d interactive controls carry hints; all three canvases delay, stay readable outside their target and dismiss on leave.\n",
           checked);
    tl_manual_paint_view_close(paint);
    CHECK(unlink(path) == 0);
}
static XImage *paint_sample_image(Widget parent, int width, int height,
                                  unsigned long first,
                                  unsigned long second) {
    XWindowAttributes attributes;
    XImage *image;
    size_t bytes;
    CHECK(XGetWindowAttributes(XtDisplay(parent), XtWindow(parent), &attributes));
    image = XCreateImage(XtDisplay(parent), attributes.visual,
                         (unsigned)attributes.depth, ZPixmap, 0, NULL,
                         (unsigned)width, (unsigned)height, 32, 0);
    CHECK(image);
    bytes = (size_t)image->bytes_per_line * (size_t)image->height;
    image->data = calloc(1, bytes);
    CHECK(image->data);
    for (int y = 0; y < height; ++y)
        for (int x = 0; x < width; ++x)
            XPutPixel(image, x, y, (x + y) & 1 ? first : second);
    return image;
}
static void check_manual_paint_reference_copy(Widget parent,
                                              XtAppContext app) {
    const char *tmpdir = getenv("TMPDIR");
    char path[4096], error[256];
    int fd;
    CHECK(tmpdir && tmpdir[0] == '/');
    CHECK(snprintf(path, sizeof(path), "%s/manual-paint-reference-XXXXXX",
                   tmpdir) > 0);
    fd = mkstemp(path);
    CHECK(fd >= 0 && close(fd) == 0 && unlink(path) == 0);
    TLManualPaint *document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_save(document, path, error,
                                            sizeof(error)) == 0);
    tl_manual_paint_free(document);
    TLManualPaintView *paint = tl_manual_paint_view_open(
        parent, path, TL_GTK2, 11, 0, NULL, NULL, NULL, NULL, NULL,
        NULL, NULL);
    CHECK(paint);
    tl_manual_paint_view_present(paint);
    paint_hint_wait(app, 100);
    Widget shell = XtNameToWidget(parent, "*manualPaintEditor");
    Widget motif_canvas = XtNameToWidget(shell, "*referenceSampleCanvas");
    Widget native_canvas = XtNameToWidget(shell, "*nativeSampleCanvas");
    Widget motif_label = XtNameToWidget(shell, "*referenceSampleLabel");
    Widget copy = XtNameToWidget(shell, "*paintCopyReference");
    Widget copy_native = XtNameToWidget(shell, "*paintCopyNative");
    Widget undo = XtNameToWidget(shell, "*paintUndo");
    Widget redo = XtNameToWidget(shell, "*paintRedo");
    CHECK(shell && motif_canvas && native_canvas && motif_label && copy &&
          copy_native &&
          undo && redo);
    Screen *screen = XtScreen(parent);
    tl_manual_paint_view_samples(
        paint, TL_MOTIF,
        paint_sample_image(parent, 15, 65, BlackPixelOfScreen(screen),
                           WhitePixelOfScreen(screen)),
        paint_sample_image(parent, 15, 120, BlackPixelOfScreen(screen),
                           WhitePixelOfScreen(screen)));
    drain(app);
    Dimension width, height;
    XtVaGetValues(motif_canvas, XmNwidth, &width, XmNheight, &height, NULL);
    CHECK(width == 60 && height == 260);
    XtVaGetValues(native_canvas, XmNwidth, &width, XmNheight, &height, NULL);
    CHECK(width == 60 && height == 480);
    char *label = text(motif_label);
    CHECK(label && strstr(label, "15 x 65 px / 4:1"));
    XtFree(label);
    CHECK(XtIsSensitive(copy));
    CHECK(XtIsSensitive(copy_native));
    XtCallCallbacks(copy, XmNactivateCallback, NULL);
    drain(app);
    document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_load(document, path, error,
                                            sizeof(error)) == 0);
    CHECK(tl_manual_paint_select_piece(document, TL_GTK2, 11, 0,
                                       TL_PAINT_PART_WHOLE,
                                       TL_PAINT_VARIANT_AUTO) == 0);
    CHECK(tl_manual_paint_width(document) == 15 &&
          tl_manual_paint_height(document) == 65);
    CHECK(tl_manual_paint_pixel(document, 0, 0) !=
          tl_manual_paint_pixel(document, 1, 0));
    tl_manual_paint_free(document);
    XtCallCallbacks(undo, XmNactivateCallback, NULL);
    drain(app);
    document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_load(document, path, error,
                                            sizeof(error)) == 0);
    CHECK(tl_manual_paint_select_piece(document, TL_GTK2, 11, 0,
                                       TL_PAINT_PART_WHOLE,
                                       TL_PAINT_VARIANT_AUTO) == 0);
    CHECK(tl_manual_paint_width(document) == 96 &&
          tl_manual_paint_height(document) == 32);
    tl_manual_paint_free(document);
    XtCallCallbacks(redo, XmNactivateCallback, NULL);
    drain(app);
    document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_load(document, path, error,
                                            sizeof(error)) == 0);
    CHECK(tl_manual_paint_select_piece(document, TL_GTK2, 11, 0,
                                       TL_PAINT_PART_WHOLE,
                                       TL_PAINT_VARIANT_AUTO) == 0);
    CHECK(tl_manual_paint_width(document) == 15 &&
          tl_manual_paint_height(document) == 65);
    tl_manual_paint_free(document);
    XtCallCallbacks(copy_native, XmNactivateCallback, NULL);
    drain(app);
    document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_load(document, path, error,
                                            sizeof(error)) == 0);
    CHECK(tl_manual_paint_select_piece(document, TL_GTK2, 11, 0,
                                       TL_PAINT_PART_WHOLE,
                                       TL_PAINT_VARIANT_AUTO) == 0);
    CHECK(tl_manual_paint_width(document) == 15 &&
          tl_manual_paint_height(document) == 120);
    tl_manual_paint_free(document);
    XtCallCallbacks(undo, XmNactivateCallback, NULL);
    drain(app);
    document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_load(document, path, error,
                                            sizeof(error)) == 0);
    CHECK(tl_manual_paint_select_piece(document, TL_GTK2, 11, 0,
                                       TL_PAINT_PART_WHOLE,
                                       TL_PAINT_VARIANT_AUTO) == 0);
    CHECK(tl_manual_paint_width(document) == 15 &&
          tl_manual_paint_height(document) == 65);
    tl_manual_paint_free(document);
    tl_manual_paint_view_close(paint);
    CHECK(unlink(path) == 0);
    puts("T04 Paint: Motif and native samples share explicit 4:1 zoom; ");
    puts("Reference and native copies are separate persisted Undo operations.");
}
static void check_manual_paint_control_catalog(TLView *view, Widget parent,
                                               XtAppContext app,
                                               TLModel *baseline) {
    const unsigned short reference_rgb[6][3] = {
        {0x7777, 0x9999, 0xbbbb}, {0x1111, 0x1111, 0x1111},
        {0x6666, 0x8888, 0xaaaa}, {0xaaaa, 0x7777, 0x5555},
        {0xeeee, 0xffff, 0xffff}, {0x2222, 0x4444, 0x6666}};
    const char *tmpdir = getenv("TMPDIR");
    char path[4096], error[256];
    int fd;
    CHECK(view && baseline && tmpdir && tmpdir[0] == '/');
    CHECK(snprintf(path, sizeof(path), "%s/manual-paint-catalog-XXXXXX",
                   tmpdir) > 0);
    fd = mkstemp(path);
    CHECK(fd >= 0 && close(fd) == 0 && unlink(path) == 0);
    TLManualPaint *document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_save(document, path, error,
                                            sizeof(error)) == 0);
    tl_manual_paint_free(document);

    /* Reproduce the reported failure: the main GTK2 catalog shows only one
       control.  The Paint reference must still capture every canonical Motif
       counterpart and must restore the main form's visibility afterwards. */
    TLModel filtered = *baseline;
    filtered.selected = TL_GTK2;
    filtered.recipes[TL_GTK2].visible_controls = 1;
    filtered.recipes[TL_GTK2].visible_categories = 31;
    /* A headless Xvfb has no KDE scheme.  Supply six deliberately distinct
       dynamic role values so the test can distinguish a painted Motif arrow
       from an unpainted window without depending on host X resources. */
    tl_view_reference_palette(view, reference_rgb);
    tl_view_update(view, &filtered);
    tl_view_scene(view, &filtered);
    drain(app);

    for (int control = 0; control < TL_CONTROL_COUNT; ++control) {
        CHECK(tl_view_manual_paint_open(view, path, TL_GTK2, control, 0) == 0);
        drain(app);
        Widget editor = XtNameToWidget(parent, "*manualPaintEditor");
        Widget label = XtNameToWidget(editor, "*referenceSampleLabel");
        Widget copy = XtNameToWidget(editor, "*paintCopyReference");
        Widget motif = XtNameToWidget(parent,
                                      "*motifReferenceControls");
        CHECK(editor && label && copy && motif);
        char *value = text(label);
        if (!value || !strstr(value, "Motif do form principal /") ||
            strstr(value, "indisponível"))
            fprintf(stderr, "Motif catalog slot %d (%s) unavailable: %s\n",
                    control, tl_control_ids[control], value ? value : "(null)");
        CHECK(value && strstr(value, "Motif do form principal /") &&
              !strstr(value, "indisponível"));
        XtFree(value);
        CHECK(XtIsSensitive(copy));
        XtCallCallbacks(copy, XmNactivateCallback, NULL);
        drain(app);
        document = tl_manual_paint_new();
        CHECK(document && tl_manual_paint_load(document, path, error,
                                                sizeof(error)) == 0);
        CHECK(tl_manual_paint_select_piece(document, TL_GTK2, control, 0,
                                           TL_PAINT_PART_WHOLE,
                                           TL_PAINT_VARIANT_AUTO) == 0);
        CHECK(tl_manual_paint_width(document) > 0 &&
              tl_manual_paint_height(document) > 0);
        if (control == 10 || control == 11) {
            int width = tl_manual_paint_width(document);
            int height = tl_manual_paint_height(document);
            uint32_t colors[8] = {0};
            uint32_t arrow_colors[8] = {0};
            int color_count = 0;
            int arrow_color_count = 0;
            for (int y = 0; y < height; ++y)
                for (int x = 0; x < width; ++x) {
                    uint32_t pixel = tl_manual_paint_pixel(document, x, y);
                    int known = 0;
                    for (int n = 0; n < color_count; ++n)
                        if (colors[n] == pixel) known = 1;
                    if (!known && color_count < 8)
                        colors[color_count++] = pixel;
                    if (x >= 2 && x < 13 && y >= 2 && y < 13) {
                        known = 0;
                        for (int n = 0; n < arrow_color_count; ++n)
                            if (arrow_colors[n] == pixel) known = 1;
                        if (!known && arrow_color_count < 8)
                            arrow_colors[arrow_color_count++] = pixel;
                    }
                }
            if (color_count < 3 || arrow_color_count < 2)
                fprintf(stderr,
                        "Motif scrollbar capture slot=%d size=%dx%d colors=%d "
                        "arrow-colors=%d first=%08x second=%08x third=%08x\n",
                        control, width, height, color_count, arrow_color_count,
                        colors[0], colors[1], colors[2]);
            CHECK(color_count >= 3);
            /* A rectangular border with a uniform interior is not a rendered
               scrollbar. The first 15x15 cell must contain its arrow glyph. */
            CHECK(arrow_color_count >= 2);
            CHECK(control == 10 ? width > height : height > width);
        }
        tl_manual_paint_free(document);
    }
    CHECK(tl_view_manual_paint_checkpoint(view) == 0);
    CHECK(unlink(path) == 0);
    puts("Paint catalog: all 16 canonical IDs retain Motif counterparts even ");
    puts("when the main GTK2 visibility filter exposes only one control.");
}
static TLManualPaintView *manual_paint_test_open(Widget parent,
                                                 XtAppContext app,
                                                 char path[4096],
                                                 PaintReferenceCapture *capture) {
    const char *tmpdir = getenv("TMPDIR");
    char error[256];
    int fd;
    CHECK(tmpdir && tmpdir[0] == '/');
    CHECK(snprintf(path, 4096, "%s/manual-paint-selection-XXXXXX",
                   tmpdir) > 0);
    fd = mkstemp(path);
    CHECK(fd >= 0 && close(fd) == 0 && unlink(path) == 0);
    TLManualPaint *document = tl_manual_paint_new();
    CHECK(document &&
          tl_manual_paint_save(document, path, error, sizeof(error)) == 0);
    tl_manual_paint_free(document);
    TLManualPaintView *paint = tl_manual_paint_view_open(
        parent, path, TL_MOTIF, 0, 0, NULL, NULL, NULL, NULL, NULL,
        paint_reference_changed, capture);
    CHECK(paint);
    tl_manual_paint_view_present(paint);
    paint_hint_wait(app, 100);
    return paint;
}
static void combo_select_with_stale_list(Widget combo, int target) {
    Widget list = NULL;
    XmStringTable items = NULL;
    int count = 0;
    XmComboBoxCallbackStruct selection;
    XtVaGetValues(combo, XmNlist, &list, XmNitems, &items, XmNitemCount, &count,
                  NULL);
    CHECK(list && items && target >= 0 && target < count);
    /* Reproduce the Motif callback order observed by the user: the visible
       item_or_text is new while the embedded XmList still reports item 0. */
    XmListSelectPos(list, 1, False);
    memset(&selection, 0, sizeof(selection));
    selection.reason = XmCR_SELECT;
    selection.item_or_text = items[target];
    selection.item_position = target;
    XtCallCallbacks(combo, XmNselectionCallback, &selection);
    XtVaSetValues(combo, XmNselectedPosition, target, NULL);
}
static void combo_select_with_late_commit(Widget combo, int target) {
    Widget list = NULL;
    XmStringTable items = NULL;
    int count = 0;
    XmComboBoxCallbackStruct selection;
    XtVaGetValues(combo, XmNlist, &list, XmNitems, &items, XmNitemCount, &count,
                  NULL);
    CHECK(list && items && target >= 0 && target < count);
    /* Keyboard selection on OpenMotif can report every callback source as the
       previous row. The ComboBox commits selectedPosition only after returning
       from the callback, which the editor reconciles in an Xt work procedure. */
    XmListSelectPos(list, 1, False);
    memset(&selection, 0, sizeof(selection));
    selection.reason = XmCR_SELECT;
    selection.item_or_text = items[0];
    selection.item_position = 0;
    XtCallCallbacks(combo, XmNselectionCallback, &selection);
    XtVaSetValues(combo, XmNselectedPosition, target, NULL);
}
static void combo_select_via_internal_list(Widget combo, int target) {
    Widget list = NULL;
    XmStringTable items = NULL;
    int count = 0;
    XmListCallbackStruct selection;
    XtVaGetValues(combo, XmNlist, &list, XmNitems, &items, XmNitemCount, &count,
                  NULL);
    CHECK(list && items && target >= 0 && target < count);
    CHECK(XtHasCallbacks(list, XmNbrowseSelectionCallback) ==
          XtCallbackHasSome);
    XmListSelectPos(list, target + 1, False);
    memset(&selection, 0, sizeof(selection));
    selection.reason = XmCR_BROWSE_SELECT;
    selection.item = items[target];
    selection.item_position = target + 1;
    XtCallCallbacks(list, XmNbrowseSelectionCallback, &selection);
    XtVaSetValues(combo, XmNselectedPosition, target, NULL);
}
static void combo_select_via_visible_text(Widget combo, const char *label) {
    Widget text_field = NULL;
    XtVaGetValues(combo, XmNtextField, &text_field, NULL);
    CHECK(text_field);
    CHECK(XtHasCallbacks(text_field, XmNvalueChangedCallback) ==
          XtCallbackHasSome);
    XmTextFieldSetString(text_field, (char *)label);
    XtCallCallbacks(text_field, XmNvalueChangedCallback, NULL);
}
static void expect_label_contains(Widget label, const char *needle) {
    char *value = text(label);
    if (!value || !strstr(value, needle))
        fprintf(stderr, "label mismatch: expected substring=[%s] actual=[%s]\n",
                needle, value ? value : "(null)");
    CHECK(value && strstr(value, needle));
    XtFree(value);
}
static void check_manual_paint_selection(Widget parent, XtAppContext app) {
    char path[4096];
    PaintReferenceCapture reference = {0};
    TLManualPaintView *paint = manual_paint_test_open(parent, app, path,
                                                      &reference);
    Widget shell = XtNameToWidget(parent, "*manualPaintEditor");
    Widget control = XtNameToWidget(shell, "*paintControl");
    Widget reference_family =
        XtNameToWidget(shell, "*paintReferenceFamily");
    Widget part = XtNameToWidget(shell, "*paintPart");
    Widget variant = XtNameToWidget(shell, "*paintVariant");
    Widget state = XtNameToWidget(shell, "*paintState");
    Widget status = XtNameToWidget(shell, "*paintStatus");
    Widget save = XtNameToWidget(shell, "*paintSave");
    CHECK(shell && control && reference_family && part && variant && state &&
          status && save);

    combo_select_via_internal_list(reference_family, TL_GTK3);
    drain(app);
    CHECK(reference.calls >= 2 && reference.request.family == TL_GTK3);
    expect_label_contains(status, "Fonte da referência alterada");

    /* The live OpenMotif build can update visible ComboBox text without
       emitting either of its usual selection callbacks.  The visible field
       is the final fallback shared by all five Paint selectors. */
    combo_select_via_visible_text(control, "Rolagem vertical");
    drain(app);
    expect_label_contains(status,
                          "Rolagem vertical / Controle inteiro / Automática");
    CHECK(XtIsSensitive(part));

    combo_select_via_internal_list(part, TL_PAINT_PART_ARROW);
    drain(app);
    expect_label_contains(status, "Rolagem vertical / Seta / Automática");
    CHECK(XtIsSensitive(variant));

    /* The dynamic variant list is [Auto, Start, End, Up, Down] here. */
    combo_select_with_stale_list(variant, 1);
    drain(app);
    expect_label_contains(status, "Rolagem vertical / Seta / Inicial");

    combo_select_with_late_commit(state, 2);
    drain(app);
    expect_label_contains(status,
                          "Rolagem vertical / Seta / Inicial / Pressionado");
    XtCallCallbacks(save, XmNactivateCallback, NULL);
    drain(app);

    FILE *input = fopen(path, "rb");
    CHECK(input);
    CHECK(fseek(input, 0, SEEK_END) == 0);
    long length = ftell(input);
    CHECK(length > 0 && fseek(input, 0, SEEK_SET) == 0);
    char *json = calloc((size_t)length + 1, 1);
    CHECK(json && fread(json, 1, (size_t)length, input) == (size_t)length);
    CHECK(fclose(input) == 0);
    CHECK(strstr(json, "\"control\":11"));
    CHECK(strstr(json, "\"part\":\"arrow\""));
    CHECK(strstr(json, "\"variant\":\"start\""));
    free(json);

    puts("Paint selection: callback item wins over stale XmList; Control, Piece "
         "and Variant persist as scrollbar/arrow/start.");
    tl_manual_paint_view_close(paint);
    CHECK(unlink(path) == 0);
}
static void check_manual_paint_r584(TLView *view, Widget parent,
                                    XtAppContext app) {
    const char *tmpdir = getenv("TMPDIR");
    const char *home = getenv("HOME");
    char path[4096], manifest[4096], error[256];
    const char *receipt =
        "../../docs/review/I167-GTK2-USER-PALETTE-UPDATE-20261028-R584.json";
    int fd;
    CHECK(view && tmpdir && tmpdir[0] == '/' && home && home[0] == '/');
    CHECK(snprintf(manifest, sizeof(manifest),
                   "%s/.local/share/irixium/gtk2-palette/"
                   "fe95ddd38ef6f61a941d420f6d3d33f376b4d34032c3fc2cf9cad77834710755/"
                   "manifest.json", home) > 0);
    CHECK(tl_view_manual_paint_r584_catalog(view, receipt, manifest, error,
                                            sizeof(error)) == 0);
    CHECK(snprintf(path, sizeof(path), "%s/manual-paint-r584-XXXXXX",
                   tmpdir) > 0);
    fd = mkstemp(path);
    CHECK(fd >= 0 && close(fd) == 0 && unlink(path) == 0);
    TLManualPaint *document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_save(document, path, error,
                                            sizeof(error)) == 0);
    tl_manual_paint_free(document);
    CHECK(tl_view_manual_paint_open(view, path, TL_GTK2, 11, 0) == 0);
    drain(app);
    Widget editor = XtNameToWidget(parent, "*manualPaintEditor");
    Widget source = XtNameToWidget(editor, "*paintReferenceFamily");
    Widget part = XtNameToWidget(editor, "*paintPart");
    Widget variant = XtNameToWidget(editor, "*paintVariant");
    Widget state = XtNameToWidget(editor, "*paintState");
    Widget label = XtNameToWidget(editor, "*referenceSampleLabel");
    Widget copy = XtNameToWidget(editor, "*paintCopyReference");
    CHECK(editor && source && part && variant && state && label && copy);
    combo_select_via_internal_list(source, TL_PAINT_REFERENCE_R584);
    combo_select_via_internal_list(part, TL_PAINT_PART_ARROW);
    /* Dynamic list: Automática, Inicial, Final, Cima, Baixo. */
    combo_select_via_internal_list(variant, 4);
    combo_select_via_internal_list(state, 2);
    drain(app);
    expect_label_contains(label, "Referência GTK2 R584 (assets)");
    char *value = text(label);
    CHECK(value && !strstr(value, "indisponível"));
    XtFree(value);
    CHECK(XtIsSensitive(copy));
    XtCallCallbacks(copy, XmNactivateCallback, NULL);
    drain(app);
    document = tl_manual_paint_new();
    CHECK(document && tl_manual_paint_load(document, path, error,
                                            sizeof(error)) == 0);
    CHECK(tl_manual_paint_select_piece(document, TL_GTK2, 11, 2,
                                       TL_PAINT_PART_ARROW,
                                       TL_PAINT_VARIANT_DOWN) == 0);
    CHECK(tl_manual_paint_width(document) > 0 &&
          tl_manual_paint_height(document) > 0);
    uint32_t first = tl_manual_paint_pixel(document, 0, 0);
    int diverse = 0;
    for (int y = 0; y < tl_manual_paint_height(document) && !diverse; ++y)
        for (int x = 0; x < tl_manual_paint_width(document); ++x)
            if (tl_manual_paint_pixel(document, x, y) != first) {
                diverse = 1;
                break;
            }
    CHECK(diverse);
    tl_manual_paint_free(document);
    CHECK(tl_view_manual_paint_checkpoint(view) == 0);
    CHECK(unlink(path) == 0);
    puts("Paint R584: verified down/pressed GTK2 asset is selectable and copied "
         "as a distinct editable raster; no fallback was used.");
}
typedef XFixesCursorImage *(*PaintGetCursorImage)(Display *);
static unsigned long long cursor_signature(PaintGetCursorImage get_image,
                                           Display *display) {
    XFixesCursorImage *image = get_image(display);
    CHECK(image && image->pixels && image->width && image->height);
    unsigned long long hash = 1469598103934665603ULL;
#define CURSOR_MIX(value)                                                        \
    do {                                                                         \
        hash ^= (unsigned long long)(value);                                      \
        hash *= 1099511628211ULL;                                                 \
    } while (0)
    CURSOR_MIX(image->width);
    CURSOR_MIX(image->height);
    CURSOR_MIX(image->xhot);
    CURSOR_MIX(image->yhot);
    for (size_t i = 0; i < (size_t)image->width * image->height; ++i)
        CURSOR_MIX(image->pixels[i]);
#undef CURSOR_MIX
    XFree(image);
    return hash;
}
static void check_manual_paint_cursors(Widget parent, XtAppContext app) {
    char path[4096];
    PaintReferenceCapture reference = {0};
    TLManualPaintView *paint = manual_paint_test_open(parent, app, path,
                                                      &reference);
    Widget shell = XtNameToWidget(parent, "*manualPaintEditor");
    Widget canvas = XtNameToWidget(shell, "*manualPaintCanvas");
    Widget tools = XtNameToWidget(shell, "*manualPaintTools");
    WidgetList children = NULL;
    Cardinal count = 0;
    CHECK(shell && canvas && tools && XtIsRealized(canvas));
    XtVaGetValues(tools, XtNchildren, &children, XtNnumChildren, &count, NULL);
    CHECK(children && count >= 6);

    void *library = dlopen("libXfixes.so.3", RTLD_NOW | RTLD_LOCAL);
    CHECK(library);
    void *symbol = dlsym(library, "XFixesGetCursorImage");
    PaintGetCursorImage get_image = NULL;
    CHECK(symbol && sizeof(get_image) == sizeof(symbol));
    memcpy(&get_image, &symbol, sizeof(get_image));

    XWarpPointer(XtDisplay(canvas), None, XtWindow(canvas), 0, 0, 0, 0, 4, 4);
    XSync(XtDisplay(canvas), False);
    unsigned long long signatures[6];
    for (int i = 0; i < 6; ++i) {
        CHECK(XmIsToggleButton(children[i]));
        XmToggleButtonSetState(children[i], True, True);
        paint_hint_wait(app, 20);
        XSync(XtDisplay(canvas), False);
        signatures[i] = cursor_signature(get_image, XtDisplay(canvas));
        printf("Paint cursor tool %d signature: %016llx\n", i,
               signatures[i]);
    }
    CHECK(signatures[TL_PAINT_PENCIL] != signatures[TL_PAINT_ERASER]);
    CHECK(signatures[TL_PAINT_PENCIL] != signatures[TL_PAINT_LINE]);
    CHECK(signatures[TL_PAINT_PENCIL] != signatures[TL_PAINT_FILL]);
    CHECK(signatures[TL_PAINT_PENCIL] != signatures[TL_PAINT_PICKER]);
    CHECK(signatures[TL_PAINT_ERASER] != signatures[TL_PAINT_LINE]);
    CHECK(signatures[TL_PAINT_ERASER] != signatures[TL_PAINT_FILL]);
    CHECK(signatures[TL_PAINT_ERASER] != signatures[TL_PAINT_PICKER]);
    CHECK(signatures[TL_PAINT_LINE] == signatures[TL_PAINT_RECTANGLE]);
    CHECK(signatures[TL_PAINT_LINE] != signatures[TL_PAINT_FILL]);
    CHECK(signatures[TL_PAINT_LINE] != signatures[TL_PAINT_PICKER]);
    CHECK(signatures[TL_PAINT_FILL] != signatures[TL_PAINT_PICKER]);
    CHECK(dlclose(library) == 0);

    puts("Paint cursors: pencil, eraser, crosshair, fill and picker cursor glyphs "
         "are actually applied over the canvas.");
    tl_manual_paint_view_close(paint);
    CHECK(unlink(path) == 0);
}
static void send_text_shortcut(XtAppContext app, Widget field, KeySym key,
                               unsigned int state) {
    Display *display = XtDisplay(field);
    XEvent event;
    CHECK(XmProcessTraversal(field, XmTRAVERSE_CURRENT));
    memset(&event, 0, sizeof(event));
    event.xkey.type = KeyPress;
    event.xkey.display = display;
    event.xkey.window = XtWindow(field);
    event.xkey.root = DefaultRootWindow(display);
    event.xkey.time = CurrentTime;
    event.xkey.state = state;
    event.xkey.keycode = XKeysymToKeycode(display, key);
    event.xkey.same_screen = True;
    CHECK(XSendEvent(display, XtWindow(field), False, KeyPressMask, &event));
    XSync(display, False);
    while (XPending(display))
        XtAppProcessEvent(app, XtIMXEvent);
}
static void expect_text(Widget field, const char *expected) {
    char *actual = XmTextFieldGetString(field);
    if (!actual || strcmp(actual, expected))
        fprintf(stderr, "text mismatch: expected=[%s] actual=[%s]\n",
                expected, actual ? actual : "(null)");
    CHECK(actual && !strcmp(actual, expected));
    XtFree(actual);
}
static void set_text_editable(Widget field, const char *value) {
    XmTextFieldSetString(field, (char *)value);
    XtCallCallbacks(field, XmNvalueChangedCallback, NULL);
}
static void open_recovery_chooser(Widget shell, XtAppContext app,
                                  const char *source, TLEditorStore *editors,
                                  Widget *error_out, Widget *chooser_out,
                                  Widget *field_out) {
    tl_manual_paint_recovery_error(shell, "JSON de camada inválido", source,
                                   editors);
    drain(app);
    Widget error = XtNameToWidget(shell, "*manualPaintLoadError");
    CHECK(error);
    Widget recover = XmMessageBoxGetChild(error, XmDIALOG_HELP_BUTTON);
    CHECK(recover);
    XtCallCallbacks(recover, XmNactivateCallback, NULL);
    drain(app);
    Widget chooser = XtNameToWidget(shell, "*manualPaintRecoveryDestination");
    CHECK(chooser);
    Widget field = XmFileSelectionBoxGetChild(chooser, XmDIALOG_TEXT);
    CHECK(field && XmIsTextField(field) && XtIsRealized(field));
    CHECK(tl_editor_find(editors, field));
    if (error_out) *error_out = error;
    if (chooser_out) *chooser_out = chooser;
    if (field_out) *field_out = field;
}
static void check_manual_paint_recovery_editor(Widget shell,
                                               XtAppContext app) {
    const char *tmpdir = getenv("TMPDIR");
    char source[4096], journal[4096], template[4096], error[512];
    CHECK(tmpdir && tmpdir[0] == '/');
    CHECK(snprintf(source, sizeof(source), "%s/manual-paint-invalid-XXXXXX",
                   tmpdir) > 0);
    int source_fd = mkstemp(source);
    CHECK(source_fd >= 0);
    const char invalid[] = "{not a valid manual paint project";
    CHECK(write(source_fd, invalid, sizeof(invalid) - 1) ==
          (ssize_t)(sizeof(invalid) - 1));
    CHECK(close(source_fd) == 0);
    CHECK(snprintf(template, sizeof(template),
                   "%s/manual-paint-recovery-journal-XXXXXX", tmpdir) > 0);
    int journal_fd = mkstemp(template);
    CHECK(journal_fd >= 0 && close(journal_fd) == 0 && unlink(template) == 0);
    snprintf(journal, sizeof(journal), "%s", template);

    TLEditorStore *editors = tl_editor_store_new();
    CHECK(editors && tl_editor_store_load(editors, journal, error,
                                           sizeof(error)) == 0);
    Widget first_error, first_chooser, first_field;
    open_recovery_chooser(shell, app, source, editors, &first_error,
                          &first_chooser, &first_field);
    char initial[4096];
    CHECK(snprintf(initial, sizeof(initial), "%s.recovered.json", source) > 0);
    const char first[] = "ação — rascunho 1";
    const char second[] = "ação — rascunho 2";
    set_text_editable(first_field, first);
    set_text_editable(first_field, second);
    send_text_shortcut(app, first_field, XK_z, ControlMask);
    expect_text(first_field, first);
    send_text_shortcut(app, first_field, XK_z, ControlMask);
    expect_text(first_field, initial);
    send_text_shortcut(app, first_field, XK_z, ControlMask | ShiftMask);
    expect_text(first_field, first);
    send_text_shortcut(app, first_field, XK_y, ControlMask);
    expect_text(first_field, second);

    send_text_shortcut(app, first_field, XK_a, ControlMask);
    XmTextPosition begin = -1, end = -1;
    CHECK(XmTextFieldGetSelectionPosition(first_field, &begin, &end));
    CHECK(begin == 0 && end == XmTextFieldGetLastPosition(first_field));
    send_text_shortcut(app, first_field, XK_c, ControlMask);
    send_text_shortcut(app, first_field, XK_x, ControlMask);
    expect_text(first_field, "");
    send_text_shortcut(app, first_field, XK_v, ControlMask);
    drain(app);
    expect_text(first_field, second);
    send_text_shortcut(app, first_field, XK_F10, ShiftMask);
    Widget edit_menu = XtNameToWidget(shell, "*textEditMenu");
    CHECK(edit_menu && XtIsManaged(edit_menu));
    XtUnmanageChild(edit_menu);

    CHECK(tl_editor_checkpoint(editors, error, sizeof(error)) == 0);
    struct stat journal_stat;
    CHECK(stat(journal, &journal_stat) == 0 &&
          (journal_stat.st_mode & 0777) == 0600);
    XtDestroyWidget(XtParent(first_chooser));
    drain(app);
    XtDestroyWidget(XtParent(first_error));
    drain(app);
    tl_editor_store_free(editors);

    editors = tl_editor_store_new();
    CHECK(editors && tl_editor_store_load(editors, journal, error,
                                           sizeof(error)) == 0);
    Widget second_error, second_chooser, second_field;
    open_recovery_chooser(shell, app, source, editors, &second_error,
                          &second_chooser, &second_field);
    expect_text(second_field, second);
    send_text_shortcut(app, second_field, XK_z, ControlMask);
    expect_text(second_field, "");
    send_text_shortcut(app, second_field, XK_y, ControlMask);
    expect_text(second_field, second);
    XtDestroyWidget(XtParent(second_chooser));
    drain(app);
    XtDestroyWidget(XtParent(second_error));
    drain(app);
    tl_editor_store_free(editors);
    CHECK(unlink(journal) == 0 && unlink(source) == 0);
    puts("I458 recovery file chooser: text field has multi-step Undo/Redo, ");
    puts("Ctrl+C/V/X/A, editing menu, and saved-history restoration.");
}
int main(int argc,char **argv) {
    XtAppContext app;
    setlocale(LC_ALL, "");
    XtSetLanguageProc(NULL,NULL,NULL);
    Widget shell=XtVaAppInitialize(&app,"MetricsProbe",NULL,0,&argc,argv,NULL,
                                    XmNwidth,1650,XmNheight,900,NULL);
    TLModel model;
    TLView *view=tl_view_create(shell,dispatch,NULL);
    TLNativeMetrics metric={.width=220,.height=80,.minimum_width=140,.minimum_height=44,.natural_width=140,.natural_height=44,.scale_factor=1};
    Widget label,reference;
    Dimension width,height;
    char expected[80],*value;
    tl_model_init(&model);
    model.selected=TL_GTK3;
    tl_view_update(view,&model); tl_view_scene(view,&model);
    XtRealizeWidget(shell);
    /* Keep the default Xvfb pointer away from controls: a correctly posted
       tooltip may occlude the native scrollbar pixel probe below. */
    XWarpPointer(XtDisplay(shell),None,DefaultRootWindow(XtDisplay(shell)),0,0,0,0,0,0);
    drain(app);
    if(getenv("TL_HEADER_LAYOUT_ONLY")){
        check_header_layout_palette(view,shell,app);
        tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    check_hints(shell);
    check_gtk2_scale_recipe(view,shell,&model);
    if(getenv("TL_AUDIT_ALL_HINTS")) {
        int checked=0,direct=0,delegated=0,missing=0;
        audit_interactive_hints(shell,&checked,&direct,&delegated,&missing);
        printf("T07 interactive hint coverage: %d checked, %d direct, %d on child surfaces, %d missing.\n",
               checked,direct,delegated,missing);
        CHECK(checked>0&&missing==0);
    }
    if(getenv("TL_DYNAMIC_HINTS")){
        if(getenv("TL_HINT_FACE"))check_hint_palette(view,shell);
        tl_test_dynamic_hints(view,shell,&model);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_HISTORY_HOVER")){
        if(getenv("TL_HINT_FACE"))check_hint_palette(view,shell);
        tl_test_history_hover(view,shell);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_FILE_HINTS_ONLY")){
        if(getenv("TL_HINT_FACE"))check_hint_palette(view,shell);
        tl_test_file_dialog_native(view,shell);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_EXPORT_REVIEW_ONLY")){
        if(getenv("TL_HINT_FACE"))check_hint_palette(view,shell);
        tl_test_export_review_native(view,shell);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_HELP_ONLY")){
        tl_test_help_native(shell);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_PAINT_HINTS_ONLY")){
        check_manual_paint_hints(shell,app);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_PAINT_REFERENCE_ONLY")){
        check_manual_paint_reference_copy(shell,app);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_PAINT_CATALOG_ONLY")){
        check_manual_paint_control_catalog(view,shell,app,&model);
        tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_PAINT_SELECTION_ONLY")){
        check_manual_paint_selection(shell,app);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_PAINT_R584_ONLY")){
        check_manual_paint_r584(view,shell,app);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_PAINT_CURSORS_ONLY")){
        check_manual_paint_cursors(shell,app);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_PAINT_RECOVERY_EDITOR_ONLY")){
        check_manual_paint_recovery_editor(shell,app);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    if(getenv("TL_HINTS_ONLY")){
        check_hint_palette(view,shell);tl_view_destroy(view);XtDestroyWidget(shell);return 0;
    }
    label=XtNameToWidget(shell,"*nativeMetrics");
    reference=XtNameToWidget(shell,"*motifReferenceControls.nativePushButton");
    CHECK(label&&reference);
    value=text(label);CHECK(strstr(value,"VM."));XtFree(value);
    value=text(reference);CHECK(!strcmp(value,TL_SAMPLE_PUSH));XtFree(value);
    Widget spin=XtNameToWidget(shell,"*motifReferenceControls*nativeSpinValue");
    int sample_value;
    CHECK(spin);XtVaGetValues(spin,XmNposition,&sample_value,NULL);
    CHECK(sample_value==TL_SAMPLE_SPIN);
    Widget vertical_scale=XtNameToWidget(shell,"*motifReferenceControls.nativeVerticalScale");
    CHECK(vertical_scale);XtVaGetValues(vertical_scale,XmNvalue,&sample_value,NULL);
    CHECK(sample_value==TL_SAMPLE_SCALE_V);
    Widget radio=XtNameToWidget(shell,"*motifReferenceControls.nativeRadioButton");
    CHECK(radio);value=text(radio);CHECK(!strcmp(value,TL_SAMPLE_RADIO));XtFree(value);
    Boolean radio_set;XtVaGetValues(radio,XmNset,&radio_set,NULL);CHECK(radio_set);
    Widget sample_list=XtNameToWidget(shell,"*motifReferenceControls.nativeList");
    CHECK(sample_list);XmStringTable rows;int count;
    XtVaGetValues(sample_list,XmNitems,&rows,XmNitemCount,&count,NULL);CHECK(count==3);
    const char *row_labels[]={TL_SAMPLE_LIST_A,TL_SAMPLE_LIST_B,TL_SAMPLE_LIST_C};
    for(int row=0;row<count;++row) {
        value=XmStringUnparse(rows[row],NULL,XmCHARSET_TEXT,XmMULTIBYTE_TEXT,NULL,0,XmOUTPUT_ALL);
        CHECK(value&&!strcmp(value,row_labels[row]));XtFree(value);
    }
    Widget frame_caption=XtNameToWidget(shell,"*motifReferenceControls*frameCaption");
    CHECK(frame_caption);value=text(frame_caption);CHECK(!strcmp(value,TL_SAMPLE_FRAME));XtFree(value);
    puts("Shared initial samples: native Motif labels/spin/vertical value/radio/list/frame verified.");
    TLNativeFont measured_font;
    tl_motif_font_measure(reference,&measured_font);
    CHECK(measured_font.kind==TL_FONT_MEASURED && measured_font.description[0]);
    printf("Native Motif font: %s\n",measured_font.description);
    CHECK(strstr(measured_font.description, "nenhum ausente"));
    const char *unicode_sample = "Árvore — ação Ελληνικά Русский";
    XmString unicode_label = XmStringGenerate((XtPointer)unicode_sample, NULL, XmMULTIBYTE_TEXT, NULL);
    XtVaSetValues(reference, XmNlabelString, unicode_label, NULL);
    XmStringFree(unicode_label);
    tl_motif_font_measure(reference, &measured_font);
    CHECK(strstr(measured_font.description, "nenhum ausente"));
    value=text(reference);CHECK(!strcmp(value,unicode_sample));XtFree(value);
    XtSetSensitive(reference, False);
    tl_motif_font_measure(reference, &measured_font);
    CHECK(strstr(measured_font.description, "nenhum ausente"));
    XtSetSensitive(reference, True);
    XEvent press;
    memset(&press, 0, sizeof(press));
    press.xbutton.type=ButtonPress;press.xbutton.display=XtDisplay(reference);
    press.xbutton.window=XtWindow(reference);press.xbutton.button=Button1;
    press.xbutton.x=4;press.xbutton.y=4;
    XtCallActionProc(reference,"Arm",&press,NULL,0);drain(app);
    tl_motif_font_measure(reference, &measured_font);
    CHECK(strstr(measured_font.description, "nenhum ausente"));
    value=text(reference);CHECK(!strcmp(value,unicode_sample));XtFree(value);
    press.xbutton.type=ButtonRelease;
    XtCallActionProc(reference,"Disarm",&press,NULL,0);drain(app);
    tl_motif_font_measure(reference, &measured_font);
    CHECK(strstr(measured_font.description, "nenhum ausente"));
    unicode_label = XmStringGenerate((XtPointer)"漢字", NULL, XmMULTIBYTE_TEXT, NULL);
    XtVaSetValues(reference, XmNlabelString, unicode_label, NULL);
    XmStringFree(unicode_label);
    tl_motif_font_measure(reference, &measured_font);
    CHECK(strstr(measured_font.description, "2 ausentes na tabela (U+6F22)"));
    value=text(reference);CHECK(!strcmp(value,"漢字"));XtFree(value);
    unicode_label = XmStringGenerate((XtPointer)TL_SAMPLE_PUSH, NULL, XmMULTIBYTE_TEXT, NULL);
    XtVaSetValues(reference, XmNlabelString, unicode_label, NULL);
    XmStringFree(unicode_label);
    puts("Integrated Unicode sample, diagnostics, sensitivity and original text preservation passed.");
    /* The recipe can resize the native pair without returning to a Latin1
     * font. If a fixed-family size is unavailable, keep the actual font and
     * report that resolved name, rather than inventing a substitute family. */
    int original_font_px=model.recipes[TL_MOTIF].geometry.font_px;
    for(int requested=12;requested<=24;requested+=6) {
        model.recipes[TL_MOTIF].geometry.font_px=requested;
        tl_view_scene(view,&model);drain(app);
        tl_motif_font_measure(reference,&measured_font);
        CHECK(measured_font.kind==TL_FONT_MEASURED);
        CHECK(strstr(measured_font.description,"fixed"));
        CHECK(strstr(measured_font.description,"Amostra"));
        value=text(reference);CHECK(!strcmp(value,TL_SAMPLE_PUSH));XtFree(value);
        printf("Native fixed pair requested=%d resolved: %s\n",requested,measured_font.description);
    }
    model.recipes[TL_MOTIF].geometry.font_px=original_font_px;
    tl_view_scene(view,&model);drain(app);
    Widget scrollbar=XtNameToWidget(shell,"*motifReferenceControls.nativeHorizontalScrollBar");
    CHECK(scrollbar);
    tl_motif_font_measure(scrollbar,&measured_font);
    CHECK(measured_font.kind==TL_FONT_NONE && !measured_font.description[0]);
    for(int axis=0;axis<2;++axis) {
        Widget bar=XtNameToWidget(shell,axis?"*motifReferenceControls.nativeVerticalScrollBar":"*motifReferenceControls.nativeHorizontalScrollBar");
        XmScrollVisible(XtNameToWidget(shell,"*motifReferenceScroll"),bar,2,2);
        XmScrollVisible(XtNameToWidget(shell,"*previewScroll"),bar,2,2);
        drain(app);
        /* Scrolling can enqueue Expose after the timer used by drain().
         * Finish server requests and dispatch those events before sampling;
         * XGetImage alone synchronizes Xlib, but does not dispatch Xt paint. */
        XSync(XtDisplay(bar),False);
        unsigned paint_events=0;
        while(XtAppPending(app)) {
            CHECK(paint_events++<2000);
            XtAppProcessEvent(app,XtIMAll);
        }
        XSync(XtDisplay(bar),False);
        printf("Pixel sampling axis=%d: dispatched %u pending events\n",axis,paint_events);
        TLNativePieces pieces;
        tl_motif_parts_measure(bar,&pieces);
        if(getenv("TL_TEST_UNSUPPORTED_MOTIF")) {
            CHECK(!pieces.mask);
            puts("Unsupported runtime Motif version: internal rectangles unavailable, no guessed layout.");
            tl_view_destroy(view);XtDestroyWidget(shell);
            return 0;
        }
        CHECK(pieces.mask==15);
        Dimension bw,bh;Pixel light,dark;
        XtVaGetValues(bar,XmNwidth,&bw,XmNheight,&bh,XmNtopShadowColor,&light,XmNbottomShadowColor,&dark,NULL);
        if(getenv("TL_PIXEL_DIAGNOSTICS"))for(Widget parent=bar;parent;parent=XtParent(parent)) {
            if(!XtIsWidget(parent)||!XtIsRealized(parent))continue;
            XWindowAttributes attributes;Window child;int root_x,root_y;
            CHECK(XGetWindowAttributes(XtDisplay(parent),XtWindow(parent),&attributes));
            XTranslateCoordinates(XtDisplay(parent),XtWindow(parent),DefaultRootWindow(XtDisplay(parent)),0,0,&root_x,&root_y,&child);
            printf("Pixel ancestor %s: %d,%d %dx%d mapped=%d\n",XtName(parent),root_x,root_y,attributes.width,attributes.height,attributes.map_state);
        }
        XImage *pixels=XGetImage(XtDisplay(bar),XtWindow(bar),0,0,bw,bh,AllPlanes,ZPixmap);
        CHECK(pixels);
        int center=pieces.slider.x+pieces.slider.width/2;
        printf("Pixel probe axis=%d: slider=%d,%d %dx%d light=%lu dark=%lu rows=",axis,pieces.slider.x,pieces.slider.y,pieces.slider.width,pieces.slider.height,light,dark);
        for(int r=0;r<pieces.slider.height;++r)printf("%lu,",XGetPixel(pixels,center,pieces.slider.y+r));
        puts("");
        CHECK(XGetPixel(pixels,center,pieces.slider.y)==light);
        CHECK(XGetPixel(pixels,center,pieces.slider.y+pieces.slider.height-1)==dark);
        XDestroyImage(pixels);
        printf("Motif pieces axis=%d: slider=%d,%d %dx%d area=%d,%d %dx%d arrows=%dx%d; top/bottom native pixels verified\n",axis,
            pieces.slider.x,pieces.slider.y,pieces.slider.width,pieces.slider.height,
            pieces.track.x,pieces.track.y,pieces.track.width,pieces.track.height,
            pieces.arrows[0].width,pieces.arrows[0].height);
    }
    TLNativePieces unsupported;
    tl_motif_parts_measure(reference,&unsupported);CHECK(!unsupported.mask);
    tl_motif_parts_measure(NULL,&unsupported);CHECK(!unsupported.mask);


    XtVaGetValues(reference,XmNwidth,&width,XmNheight,&height,NULL);
    snprintf(expected,sizeof(expected),"%d x %d",width,height);
    value=text(label); CHECK(value&&strstr(value,expected)); XtFree(value);
    tl_view_native_metrics(view,0,&metric);
    metric.separate=1; metric.width=221;
    tl_view_native_metrics(view,0,&metric);
    value=text(label);
    CHECK(strstr(value,"220 x 80")&&strstr(value,"221 x 80")); XtFree(value);
    tl_view_update(view,&model);tl_view_scene(view,&model);
    value=text(label);CHECK(strstr(value,"220 x 80")&&strstr(value,"221 x 80"));XtFree(value);
    /* The Motif reference recipe remains independent of GTK edits. */
    model.recipes[TL_MOTIF].sizes[0][0]=200;
    model.recipes[TL_MOTIF].sizes[0][1]=70;
    tl_view_update(view,&model);tl_view_scene(view,&model);tl_view_metrics_reset(view);drain(app);
    XtVaGetValues(reference,XmNwidth,&width,XmNheight,&height,NULL);
    CHECK(width==200&&height==70);
    value=text(label);CHECK(strstr(value,"200 x 70")&&!strstr(value,"221 x 80"));XtFree(value);
    /* Pairing is a display-only overlay, physical coordinates and sensitivity. */
    model.recipes[TL_GTK3].selected_control=10;
    tl_view_update(view,&model);tl_view_scene(view,&model);drain(app);
    TLModel unchanged=model;
    TLNativeMetrics pair={.width=210,.height=15,.scale_factor=2,
        .position_x=100,.position_y=42,.position_valid=1,
        .sensitivity_known=1,.sensitive=0};
    tl_view_native_metrics(view,10,&pair);drain(app);
    Widget horizontal=XtNameToWidget(shell,"*motifReferenceControls.nativeHorizontalScrollBar");
    Position px,py;
    XtVaGetValues(horizontal,XmNx,&px,XmNy,&py,NULL);
    CHECK(px==200 && py==84 && !XtIsSensitive(horizontal));
    CHECK(!memcmp(&model,&unchanged,sizeof(model)));
    model.recipes[TL_GTK3].selected_control=11;
    tl_view_update(view,&model);tl_view_scene(view,&model);drain(app);
    XtVaGetValues(horizontal,XmNx,&px,XmNy,&py,NULL);
    CHECK(px==model.recipes[TL_MOTIF].positions[10][0] &&
          py==model.recipes[TL_MOTIF].positions[10][1] && XtIsSensitive(horizontal));
    pair.scale_factor=1;pair.position_x=30;pair.position_y=100;pair.sensitive=1;
    tl_view_native_metrics(view,11,&pair);drain(app);
    Widget vertical=XtNameToWidget(shell,"*motifReferenceControls.nativeVerticalScrollBar");
    XtVaGetValues(vertical,XmNx,&px,XmNy,&py,NULL);
    CHECK(px==30 && py==100 && XtIsSensitive(vertical));
    tl_view_metrics_reset(view);drain(app);
    XtVaGetValues(vertical,XmNx,&px,XmNy,&py,NULL);
    CHECK(px==model.recipes[TL_MOTIF].positions[11][0] &&
          py==model.recipes[TL_MOTIF].positions[11][1]);
    int checked_origin[2]={123,456};
    pair.scale_factor=0;
    CHECK(tl_pair_physical_origin(&pair,checked_origin)==-1 && checked_origin[0]==123);
    pair.scale_factor=2;pair.position_x=2048;
    CHECK(tl_pair_physical_origin(&pair,checked_origin)==-1 && checked_origin[1]==456);
    puts("Pair overlay: physical position, sensitivity, selection restore and stale-cache restore passed.");
    /* Physical trailing edge is preserved after native sizing, in both Motif
     * panes. No assumption that a request of one pixel is accepted. */
    model.selected=TL_MOTIF;
    const int lengths[]={260,1,0,180};
    const char *forms[]={"nativePreviewControls","motifReferenceControls"};
    for (unsigned n=0;n<sizeof(lengths)/sizeof(lengths[0]);++n) {
        TLRecipe *recipe=&model.recipes[TL_MOTIF];
        recipe->length_anchor[10]=recipe->length_anchor[11]=1;
        recipe->positions[10][0]=recipe->positions[11][1]=400;
        recipe->sizes[10][0]=recipe->sizes[11][1]=lengths[n];
        tl_view_update(view,&model);tl_view_scene(view,&model);drain(app);
        for (unsigned pane=0;pane<2;++pane) for (int axis=0;axis<2;++axis) {
            char path[160];Position x,y;Dimension w,h;
            snprintf(path,sizeof(path),"*%s.%s",forms[pane],
                     axis?"nativeVerticalScrollBar":"nativeHorizontalScrollBar");
            Widget bar=XtNameToWidget(shell,path);CHECK(bar&&XtIsManaged(bar));
            XtVaGetValues(bar,XmNx,&x,XmNy,&y,XmNwidth,&w,XmNheight,&h,NULL);
            printf("Motif anchor: pane=%s requested=%d axis=%d origin=%d extent=%d edge=%d\n",
                   forms[pane],lengths[n],axis,axis?y:x,axis?h:w,axis?y+h:x+w);
            CHECK((axis?y+h:x+w)==400);
            CHECK((axis?w:h)==model.recipes[TL_MOTIF].geometry.bar_px);
        }
    }
    model.recipes[TL_MOTIF].positions[10][0]=0;
    tl_view_scene(view,&model);drain(app);
    CHECK(!XtIsManaged(XtNameToWidget(shell,"*nativePreviewControls.nativeHorizontalScrollBar")));
    CHECK(!XtIsManaged(XtNameToWidget(shell,"*motifReferenceControls.nativeHorizontalScrollBar")));
    value=text(XtNameToWidget(shell,"*previewNotice"));CHECK(strstr(value,"âncora fora"));XtFree(value);
    model.recipes[TL_MOTIF].positions[10][0]=400;
    tl_view_scene(view,&model);drain(app);
    CHECK(XtIsManaged(XtNameToWidget(shell,"*nativePreviewControls.nativeHorizontalScrollBar")));
    CHECK(XtIsManaged(XtNameToWidget(shell,"*motifReferenceControls.nativeHorizontalScrollBar")));
    char error[256];
    TLRecipe *recipe=&model.recipes[TL_MOTIF];
    recipe->selected_control=11;recipe->length_anchor[11]=0;recipe->positions[11][1]=180;
    tl_view_update(view,&model);tl_view_scene(view,&model);drain(app);
    CHECK(XtIsSensitive(XtNameToWidget(shell,"*lengthAnchor")));
    CHECK(!tl_view_set_anchor(view,&model,1,error,sizeof(error)));
    CHECK(recipe->positions[11][1]==360&&recipe->length_anchor[11]==1);
    CHECK(!tl_view_set_anchor(view,&model,0,error,sizeof(error)));
    CHECK(recipe->positions[11][1]==180&&recipe->length_anchor[11]==0);
    model.selected=TL_GTK3;recipe=&model.recipes[TL_GTK3];
    recipe->selected_control=11;recipe->positions[11][1]=180;
    tl_view_update(view,&model);tl_view_scene(view,&model);tl_view_metrics_reset(view);drain(app);
    CHECK(tl_view_set_anchor(view,&model,1,error,sizeof(error))==-1);
    CHECK(recipe->length_anchor[11]==0&&recipe->positions[11][1]==180);
    TLNativeMetrics placed={.width=15,.height=48,.minimum_width=15,.minimum_height=48,.natural_width=15,.natural_height=48,.scale_factor=1,.cell_offset_y=25,.cell_offset_valid=1};
    tl_view_native_metrics(view,11,&placed);
    CHECK(!tl_view_set_anchor(view,&model,1,error,sizeof(error)));
    CHECK(recipe->positions[11][1]==253&&recipe->length_anchor[11]==1);
    CHECK(!tl_view_set_anchor(view,&model,0,error,sizeof(error)));
    CHECK(recipe->positions[11][1]==180&&recipe->length_anchor[11]==0);
    recipe->sizes[11][1]=222;
    CHECK(tl_view_set_anchor(view,&model,1,error,sizeof(error))==-1);
    CHECK(recipe->positions[11][1]==180&&recipe->length_anchor[11]==0);
    puts("Native Motif metrics: allocation, independent recipes, two GTK origins, stale cache cleared.");
    tl_view_destroy(view);XtDestroyWidget(shell);return 0;
}
