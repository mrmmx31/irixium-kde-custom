#include "part_relief_editor.h"
/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Native Motif View. The controller owns the model, actions and persistence. */
#include "theme_lab.h"
#include "manual_paint_view.h"
#include "project_history_controls.h"
#include "text_editor.h"
#include "control_dimensions.h"
#include "native_font_motif.h"
#include "font_policy_motif.h"
#include "native_pair_motif.h"
#include "native_parts_motif.h"
#include "sample_controls.h"
#include "ui_hints.h"
#include "ui_help.h"
#include "ui_export_review.h"
#include "control_catalog.h"
#include "control_availability.h"
#include "gtk2_r584_catalog.h"
#include "code_search.h"
#include "../native-gtk4/canvas_identity.h"
#include "../native-gtk4/focus.h"

#include <Xm/Xm.h>
#include <Xm/Form.h>
#include <Xm/RowColumn.h>
#include <Xm/Label.h>
#include <Xm/List.h>
#include <Xm/PushB.h>
#include <Xm/ToggleB.h>
#include <Xm/TextF.h>
#include <Xm/Text.h>
#include <Xm/Scale.h>
#include <Xm/ScrollBar.h>
#include <Xm/ScrolledW.h>
#include <Xm/Frame.h>
#include <Xm/DrawingA.h>
#include <Xm/PanedW.h>
#include <Xm/FileSB.h>
#include <Xm/Protocols.h>
#include <Xm/ComboBox.h>
#include <Xm/CascadeB.h>
#include <Xm/Separator.h>
#include <Xm/SpinB.h>
#include <Xm/ArrowB.h>
#include <Xm/LabelG.h>
#include <Xm/VendorS.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <X11/extensions/Xcomposite.h>
#include <png.h>
#include <errno.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

enum { FACE, TEXT, VIEW, SELECTION, LIGHT, SHADOW, TROUGH, COLOR_COUNT };
enum { PREVIEW_COUNT = TL_CONTROL_COUNT, ACTION_COUNT = 12, SCHEME_LIMIT = 128 };
enum {
    TL_PAGE_CATALOG,
    TL_PAGE_CONTROL,
    TL_PAGE_GEOMETRY,
    TL_PAGE_COLORS,
    TL_PAGE_MODEL,
    TL_PAGE_CODE,
    TL_PAGE_COUNT
};
enum { XE_EMBEDDED_NOTIFY, XE_WINDOW_ACTIVATE, XE_WINDOW_DEACTIVATE,
       XE_REQUEST_FOCUS, XE_FOCUS_IN, XE_FOCUS_OUT, XE_FOCUS_NEXT, XE_FOCUS_PREV };
enum { XE_FOCUS_CURRENT, XE_FOCUS_FIRST, XE_FOCUS_LAST };

static const char *const control_labels[TL_CONTROL_COUNT] = {
    "Botão", "Botão alternável", "Caixa de seleção", "Botão de opção",
    "Entrada de texto", "ComboBox", "SpinBox", "Texto multilinha",
    "Escala horizontal", "Escala vertical", "Rolagem horizontal", "Rolagem vertical",
    "Botão de seta", "Progresso / nível", "Lista", "Moldura"
};
static const char *const category_labels[TL_CATEGORY_COUNT] = {
    "Botões", "Entradas", "Faixas / rolagem", "Dados", "Contêineres"
};
static const int control_category[TL_CONTROL_COUNT] = {
    0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 4
};

typedef struct {
    struct TLView *view;
    TLAction action;
} ActionBinding;

typedef struct {
    struct TLView *view;
    int control;
} ControlBinding;

typedef struct {
    struct TLView *view;
    int page;
} PageBinding;

typedef struct FileChoice {
    struct TLView *view;
    Widget dialog;
    TLFileChosen chosen;
    void *context;
    struct FileChoice *next;
} FileChoice;

struct TLView {
    TLHelp *help;
    TLExportReview *export_review;
    TLManualPaintView *manual_paint;
    Widget history_controls;
    TLEditorStore *editors;
    Widget shell, root, workspace, menu_bar, family_combo, scheme_combo, name, reference_path;
    Widget context_bar, page_selector, page_host, pages[TL_PAGE_COUNT];
    Widget history_menu_items[5];
    PageBinding page_bindings[TL_PAGE_COUNT];
    int selected_page;
    Widget fields[TL_FIELD_COUNT], scale_fields[2], scale_geometry, factors[3], roles[4], notes, palette_scope;
    Widget part_combo, part_fields[TL_SCROLL_PARAM_COUNT], part_notice, part_captions[TL_SCROLL_PARAM_COUNT];
    TLPartReliefEditor *part_relief_editor;
    Widget automatic, delay, separate;
    TLControlCatalog *catalog;
    Widget edit_state, anchor_combo, position[2], size[2], control_label, code, code_search;
    Widget code_search_previous, code_search_next, code_search_case, code_search_word, code_search_status;
    Widget canvas, canvas_notice;
    char code_search_last[1024];
    TLCodeSearchMatch code_search_match;
    int code_search_has_match;
    TLRecipe preview_recipe;
    TLRecipe reference_recipe;
    int reference_ready;
    Widget metric_summary;
    TLNativeMetrics gtk_metrics[2][TL_CONTROL_COUNT];
    Widget status, capability, pick_summary, preview_notice;
    Widget preview_form, preview_frame, preview_menu, preview_widgets[PREVIEW_COUNT];
    Widget preview_stack_scroll, preview_stack, preview_canvas_scroll, motif_reference_scroll;
    Dimension preview_stack_min_width, preview_stack_min_height;
    Dimension preview_canvas_min_width, motif_reference_min_width;
    Dimension preview_canvas_min_height, motif_reference_min_height;
    int preview_stack_layout_ready;
    Widget reference_area, reference_notice, reference_dialog;
    Widget motif_reference_form, motif_reference_frame, motif_reference_notice;
    Widget motif_reference_widgets[TL_CONTROL_COUNT];
    int preview_sizes[TL_CONTROL_COUNT][2], reference_sizes[TL_CONTROL_COUNT][2];
    Dimension preview_base_sizes[TL_CONTROL_COUNT][2], reference_base_sizes[TL_CONTROL_COUNT][2];
    ActionBinding bindings[ACTION_COUNT + 1];
    ActionBinding history_bindings[5];
    ControlBinding control_bindings[TL_CONTROL_COUNT];
    TLDispatch dispatch;
    void *context;
    TLModel snapshot;
    int has_model, updating;
    char capabilities[TL_FAMILY_COUNT][TL_TEXT_MAX];
    Pixel pixels[COLOR_COUNT];
    unsigned short rgb[6][3];
    int palette_valid, pixel_allocated[COLOR_COUNT];
    Pixel header_pixels[COLOR_COUNT];
    unsigned short header_rgb[6][3];
    int header_palette_valid, header_pixel_allocated[COLOR_COUNT];
    Pixel preview_pixels[COLOR_COUNT];
    unsigned short preview_rgb[6][3];
    int preview_palette_valid, preview_pixel_allocated[COLOR_COUNT];
    Pixel reference_pixels[COLOR_COUNT];
    unsigned short reference_rgb[6][3];
    int reference_palette_valid, reference_pixel_allocated[COLOR_COUNT];
    double reference_trough;
    double preview_trough;
    TLFamily preview_family;
    Window embedded_child, embedded_candidate;
    Window paint_redirected[TL_CONTROL_COUNT * 2 + 1];
    size_t paint_redirected_count;
    int composite_checked, composite_supported;
    XImage *paint_motif_samples[TL_CONTROL_COUNT];
    XImage *paint_native_samples[TL_CONTROL_COUNT];
    XImage *paint_reference_sample;
    TLGtk2R584Catalog *paint_r584_catalog;
    char paint_r584_error[TL_TEXT_MAX];
    int paint_context_valid, paint_family, paint_control, paint_state;
    int paint_request_valid;
    TLManualPaintSampleRequest paint_request;
    int paint_reference_request_valid;
    TLManualPaintSampleRequest paint_reference_request;
    TLGTK4Focus *gtk4_focus;
    Atom xembed_atom, xembed_info_atom;
    int embedded_focus, embedded_active, embedded_focus_detail;
    char schemes[SCHEME_LIMIT][128];
    int scheme_count;
    XtWorkProcId selection_work;
    int pending_control;
    int dragging, drag_control, drag_root[2], drag_origin[2];
    Widget drag_widget;
    XmFontList native_font, preview_font, reference_font;
    char native_xlfd[512];
    int preview_font_px, reference_font_px;
    XImage *reference_image;
    GC reference_gc;
    unsigned int reference_width, reference_height;
    FileChoice *choices;
};

static void metrics_geometry_event(Widget widget, XtPointer data, XEvent *event, Boolean *dispatch);

static void preview_stack_resize_event(Widget widget, XtPointer data,
                                       XEvent *event, Boolean *dispatch);

static int number_read(Widget widget, int integer, double *result);
static void metrics_refresh(TLView *view);

static void number_set(Widget field, double value)
{
    short digits = 0;
    int minimum, maximum, position;
    double current;
    XtVaGetValues(field, XmNdecimalPoints, &digits, XmNminimumValue, &minimum,
                  XmNmaximumValue, &maximum, NULL);
    if(number_read(field,!digits,&current)&&fabs(current-value)<1e-9)return;
    position = (int)lround(value * (digits ? 10000.0 : 1.0));
    if (position < minimum) position = minimum;
    if (position > maximum) position = maximum;
    XtVaSetValues(field, XmNposition, position, NULL);
    /* Typing changes the child text without updating XmNposition. Setting an
     * unchanged position therefore does not replace a previous control's text. */
    char text[64];
    if(digits)snprintf(text,sizeof(text),"%.*f",digits,position/10000.0);
    else snprintf(text,sizeof(text),"%d",position);
    tl_editor_set_text(field,text);
}

static void number_verify(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view = client;
    XmSpinBoxCallbackStruct *event = call;
    int minimum, maximum, increment, position, field = -1;
    short digits;
    double value;
    (void)widget;
    if (!event || !event->widget || view->updating) return;
    XtVaGetValues(event->widget, XmNminimumValue, &minimum, XmNmaximumValue, &maximum,
                  XmNincrementValue, &increment, XmNdecimalPoints, &digits, NULL);
    if (!number_read(event->widget, !digits, &value)) {
        event->doit = False;
        tl_view_status(view, "Corrija o número digitado antes de usar as setas."); return;
    }
    if (value < minimum / (digits ? 10000.0 : 1.0) ||
        value > maximum / (digits ? 10000.0 : 1.0)) {
        event->doit = False;
        tl_view_status(view, "Número fora do intervalo deste controle."); return;
    }
    position = (int)lround(value * (digits ? 10000.0 : 1.0));
    if (event->reason == XmCR_SPIN_NEXT) position += increment;
    else if (event->reason == XmCR_SPIN_PRIOR) position -= increment;
    else if (event->reason == XmCR_SPIN_FIRST) position = minimum;
    else if (event->reason == XmCR_SPIN_LAST) position = maximum;
    if (position < minimum) position = minimum;
    if (position > maximum) position = maximum;
    /* Keep the measured composition coherent when using one increment arrow.
     * Typing still allows a batch of explicit edits before Atualizar. */
    for (int i = 0; i < TL_FIELD_COUNT; ++i)
        if (event->widget == view->fields[i]) field = i;
    if (field >= 0 && field <= 6 && field != 4 && field != 5 &&
        (view->snapshot.selected == TL_MOTIF || view->snapshot.selected == TL_GTK3)) {
        TLGeometry geometry = view->snapshot.recipes[view->snapshot.selected].geometry;
        for (int i = 0; i < TL_FIELD_COUNT; ++i)
            if (number_read(view->fields[i], 1, &value))
                tl_model_geometry_set(&geometry, i, (int)value);
        tl_model_geometry_set(&geometry, field, position);
        if (field == 6) geometry.shadow_px = geometry.view_inset_px;
        if (field == 0) geometry.arrow_px = geometry.bar_px - 2 * geometry.shadow_px;
        else if (field == 3) geometry.arrow_px = geometry.thumb_cross_px;
        if (geometry.arrow_px <= 2 * geometry.shadow_px)
            geometry.arrow_px = 2 * geometry.shadow_px + 1;
        if (!(geometry.arrow_px & 1)) ++geometry.arrow_px;
        geometry.bar_px = geometry.arrow_px + 2 * geometry.shadow_px;
        geometry.thumb_cross_px = geometry.arrow_px;
        geometry.view_inset_px = geometry.shadow_px;
        if (geometry.bar_px > 127) { event->doit = False; return; }
        view->updating = 1;
        for (int i = 0; i <= 6; ++i)
            if (i != field) number_set(view->fields[i], tl_model_geometry_get(&geometry, i));
        view->updating = 0;
        position = tl_model_geometry_get(&geometry, field);
    }
    if(event->widget==view->part_fields[0] && view->snapshot.recipes[view->snapshot.selected].selected_scroll_part==TL_SCROLL_ARROW && position==1)
        position=event->reason==XmCR_SPIN_PRIOR ? -1 : 3;
    event->position = position;
    event->crossed_boundary = False;
}

static void separate_callback(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view = client;
    (void)call;
    if (!view->updating)
        view->dispatch(view->context, TL_SEPARATE_TOGGLE, XmToggleButtonGetState(widget) ? 1 : 0);
}

static void set_error(char *error, size_t capacity, const char *message)
{
    if (error != NULL && capacity > 0)
        (void)snprintf(error, capacity, "%s", message);
}

static XmString compound(const char *text)
{
    return XmStringGenerate((XtPointer)(text != NULL ? text : ""),
                            NULL, XmMULTIBYTE_TEXT, NULL);
}

static void label_set(Widget widget, const char *text)
{
    XmString value = compound(text);
    XtVaSetValues(widget, XmNlabelString, value, NULL);
    XmStringFree(value);
}

/* Motif labels do not wrap automatically. Keep controller descriptions readable
 * in the fixed-width family column without changing or truncating model data. */
static void label_wrapped(Widget widget, const char *text, unsigned int columns)
{
    char *wrapped;
    size_t input = 0, output = 0, last_space = 0;
    unsigned int line = 0;
    if (text == NULL) text = "";
    wrapped=malloc(strlen(text)+1);
    if(!wrapped) {label_set(widget,text);return;}
    while (text[input] != '\0') {
        unsigned char character = (unsigned char)text[input++];
        wrapped[output++] = (char)character;
        if (character == '\n') {
            line = 0; last_space = 0;
        } else {
            if ((character & 0xc0U) != 0x80U)
                ++line;
            if (character == ' ') last_space = output;
            if (line >= columns && last_space != 0) {
                wrapped[last_space - 1] = '\n';
                line = (unsigned int)(output - last_space);
                last_space = 0;
            }
        }
    }
    wrapped[output] = '\0';
    label_set(widget, wrapped);
    free(wrapped);
}

static Widget label_new(Widget parent, const char *name, const char *text)
{
    Widget widget = XtVaCreateManagedWidget(name, xmLabelWidgetClass, parent,
                    XmNalignment, XmALIGNMENT_BEGINNING,
                    XmNmarginWidth, 2, XmNmarginHeight, 2, NULL);
    label_set(widget, text);
    return widget;
}

static void action_callback(Widget widget, XtPointer client, XtPointer call)
{
    ActionBinding *binding = (ActionBinding *)client;
    (void)widget;
    (void)call;
    if (binding->view->dispatch != NULL && !binding->view->updating)
        binding->view->dispatch(binding->view->context, binding->action, 0);
}

/* Motif builds have disagreed about whether XmComboBoxCallbackStruct's
 * item_position is already in XmNpositionMode and may expose the previous
 * row while the selection callback is running. Read the committed row from
 * the ComboBox's internal list before falling back to callback metadata. */
static int combo_callback_index(Widget widget, XtPointer call)
{
    XmComboBoxCallbackStruct *selection = call;
    Widget list = NULL;
    XmString *items = NULL;
    int *positions = NULL, position_count = 0;
    int count = 0, i;
    if (!selection || selection->reason != XmCR_SELECT)
        return -1;
    XtVaGetValues(widget, XmNitems, &items, XmNitemCount, &count, XmNlist, &list, NULL);
    /* The internal list owns the committed selection before the ComboBox
     * callback. Read its one-based position first; callback text encodings
     * differ across Motif builds, so XmStringCompare alone is not sufficient. */
    if (list && XmListGetSelectedPos(list, &positions, &position_count)) {
        int selected = position_count == 1 ? positions[0] - 1 : -1;
        XtFree((char *)positions);
        if (selected >= 0 && selected < count)
            return selected;
    }
    for (i = 0; selection->item_or_text && items && i < count; ++i)
        if (XmStringCompare(selection->item_or_text, items[i]))
            return i;
    /* Keep the documented XmZERO_BASED callback position as a bounded final
     * fallback for Motif variants whose list-selection query is unavailable. */
    if (selection->item_position >= 0 && selection->item_position < count)
        return selection->item_position;
    return -1;
}

static void family_callback(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view = (TLView *)client;
    int family = combo_callback_index(widget, call);
    if (!view->updating &&
        family >= 0 && family < TL_FAMILY_COUNT &&
        view->dispatch != NULL)
        view->dispatch(view->context, TL_SELECT_FAMILY, family);
}

static void changed_callback(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view = (TLView *)client;
    (void)widget; (void)call;
    if (!view->updating && view->dispatch != NULL) {
        if(widget==view->size[0]||widget==view->size[1])metrics_refresh(view);
        view->dispatch(view->context, TL_CHANGED, 0);
    }
}

static void code_search_clear(TLView *view, const char *message)
{
    XmTextPosition end;
    if (!view || !view->code) return;
    end = XmTextGetLastPosition(view->code);
    XmTextSetHighlight(view->code, 0, end, XmHIGHLIGHT_NORMAL);
    view->code_search_has_match = 0;
    if (view->code_search_status && message) label_set(view->code_search_status, message);
}

static void code_search_changed(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view = (TLView *)client;
    (void)widget; (void)call;
    if (view->code_search_has_match)
        code_search_clear(view, "Consulta alterada; localize novamente.");
}

static void code_search_run(TLView *view, int direction)
{
    char *query, *text;
    size_t start;
    TLCodeSearchMatch match;
    Boolean match_case, whole_word;
    if (!view || !view->code_search || !view->code) return;
    query = XmTextFieldGetString(view->code_search);
    text = XmTextGetString(view->code);
    if (!query || !text) {
        if (query) XtFree(query);
        if (text) XtFree(text);
        code_search_clear(view, "Busca indisponível.");
        return;
    }
    match_case = XmToggleButtonGetState(view->code_search_case);
    whole_word = XmToggleButtonGetState(view->code_search_word);
    if (strcmp(query, view->code_search_last) == 0 && view->code_search_has_match)
        start = direction > 0 ? view->code_search_match.end : view->code_search_match.start;
    else
        start = direction > 0 ? 0 : tl_code_search_length(text);
    if (tl_code_search_find(text, query, start, direction, match_case, whole_word, &match)) {
        view->code_search_match = match;
        view->code_search_has_match = 1;
        (void)snprintf(view->code_search_last, sizeof(view->code_search_last), "%s", query);
        XmTextSetHighlight(view->code, (XmTextPosition)match.start,
                           (XmTextPosition)match.end, XmHIGHLIGHT_SELECTED);
        XmTextSetInsertionPosition(view->code, (XmTextPosition)match.end);
        XmTextShowPosition(view->code, (XmTextPosition)match.start);
        char result[128];
        (void)snprintf(result, sizeof(result), "Encontrado: %lu–%lu",
                       (unsigned long)(match.start + 1), (unsigned long)match.end);
        label_set(view->code_search_status, result);
    } else {
        (void)snprintf(view->code_search_last, sizeof(view->code_search_last), "%s", query);
        code_search_clear(view, query[0] ? "Sem ocorrência nesta direção." : "Digite um termo.");
    }
    XtFree(query);
    XtFree(text);
}

static void code_search_previous_callback(Widget widget, XtPointer client, XtPointer call)
{
    (void)widget; (void)call;
    code_search_run((TLView *)client, -1);
}

static void code_search_next_callback(Widget widget, XtPointer client, XtPointer call)
{
    (void)widget; (void)call;
    code_search_run((TLView *)client, 1);
}

static void code_search_activate_callback(Widget widget, XtPointer client, XtPointer call)
{
    (void)widget; (void)call;
    code_search_run((TLView *)client, 1);
}

static void part_state_callback(Widget widget,XtPointer client,XtPointer call) {
    TLView *view=client;(void)widget;(void)call;
    if(!view->updating&&view->dispatch)view->dispatch(view->context,TL_SELECT_PART_STATE,0);
}
static void part_relief_callback(Widget widget,XtPointer client,XtPointer call) {
    TLView *view=client;(void)widget;(void)call;
    if(!view->updating&&view->dispatch)view->dispatch(view->context,TL_PART_RELIEF_CHANGED,0);
}
int tl_view_part_state(const TLView *view) {
    return view?tl_part_editor_state(view->part_relief_editor):-1;
}
static void selected_part_callback(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view=client;
    int part=combo_callback_index(widget,call);
    if(!view->updating && part>=0 && part<TL_SCROLL_PART_COUNT && view->dispatch)
        view->dispatch(view->context,TL_SELECT_SCROLL_PART,part);
}

static void selected_anchor_callback(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view=client;
    (void)call;
    if(!view->updating && view->dispatch) {
        int selected;
        /* This runtime can report the previous item_position while the
         * widget already exposes its actual new selection. */
        XtVaGetValues(widget,XmNselectedPosition,&selected,NULL);
        view->dispatch(view->context,TL_SELECT_ANCHOR,selected);
    }
}

static void catalog_changed(void *context,int control)
{
    TLView *view=context;
    if(!view->updating&&view->dispatch) {
        if(control>=0)view->dispatch(view->context,TL_SELECT_CONTROL,control);
        else view->dispatch(view->context,TL_CHANGED,0);
    }
}

static Boolean selection_idle(XtPointer client)
{
    TLView *view = (TLView *)client;
    int control = view->pending_control;
    view->selection_work = 0;
    view->pending_control = -1;
    if (!view->updating && view->dispatch != NULL && control >= 0 && control < TL_CONTROL_COUNT)
        view->dispatch(view->context, TL_SELECT_CONTROL, control);
    return True;
}

static int control_place(Widget widget, const TLRecipe *recipe, int index,
                         Dimension *width, Dimension *height, int origin[2]);

static void control_move(TLView *view, int root_x, int root_y)
{
    int coordinates[2], i, previous;
    char text[32];
    coordinates[0] = view->drag_origin[0] + root_x - view->drag_root[0];
    coordinates[1] = view->drag_origin[1] + root_y - view->drag_root[1];
    for (i = 0; i < 2; ++i) {
        if (coordinates[i] < 0) coordinates[i] = 0;
        if (coordinates[i] > 2048) coordinates[i] = 2048;
    }
    TLRecipe candidate=view->preview_recipe;
    Dimension width,height;
    int origin[2];
    Widget widget=view->preview_widgets[view->drag_control];
    candidate.positions[view->drag_control][0]=coordinates[0];
    candidate.positions[view->drag_control][1]=coordinates[1];
    XtVaGetValues(widget,XmNwidth,&width,XmNheight,&height,NULL);
    if(tl_control_anchor_origin(&candidate,view->drag_control,width,height,origin)) {
        tl_view_status(view,"Arraste recusado: extremidade fora do canvas; posição preservada.");
        return;
    }
    previous = view->updating; view->updating = 1;
    for (i = 0; i < 2; ++i) {
        (void)snprintf(text, sizeof(text), "%d", coordinates[i]);
        XmTextFieldSetString(view->position[i], text);
    }
    (void)control_place(widget,&candidate,view->drag_control,&width,&height,origin);
    view->preview_recipe=candidate;
    view->updating = previous;
    /* The model stays read-only here. Only the controller can accept the
     * coordinates from the edited fields and persist a new candidate. */
    if (!view->updating && view->dispatch != NULL)
        view->dispatch(view->context, TL_MOVE_CONTROL, view->drag_control);
}

static void canvas_control_event(Widget widget, XtPointer client, XEvent *event, Boolean *continue_dispatch)
{
    ControlBinding *binding = (ControlBinding *)client;
    TLView *view = binding->view;
    if (view->updating || view->dispatch == NULL) return;
    if (view->dragging) {
        if (event->type == MotionNotify) {
            control_move(view, event->xmotion.x_root, event->xmotion.y_root);
            *continue_dispatch = False;
        } else if (event->type == ButtonRelease && event->xbutton.button == Button1) {
            control_move(view, event->xbutton.x_root, event->xbutton.y_root);
            XtUngrabPointer(view->drag_widget, event->xbutton.time);
            view->dragging = 0; view->drag_widget = NULL;
            *continue_dispatch = False;
        }
        return;
    }
    if (event->type == ButtonPress && event->xbutton.button == Button1) {
        if (event->xbutton.state & ControlMask) {
            *continue_dispatch = False;
            if (view->selection_work) {
                XtRemoveWorkProc(view->selection_work); view->selection_work = 0;
            }
            view->pending_control = -1;
            view->dispatch(view->context, TL_SELECT_CONTROL, binding->control);
            if (!view->has_model || view->snapshot.recipes[view->snapshot.selected].selected_control != binding->control)
                return;
            if (XtGrabPointer(widget, False, PointerMotionMask | ButtonReleaseMask,
                              GrabModeAsync, GrabModeAsync, None, None, event->xbutton.time) != GrabSuccess) {
                tl_view_status(view, "Não foi possível capturar o ponteiro para mover o controle.");
                return;
            }
            view->dragging = 1; view->drag_widget = widget; view->drag_control = binding->control;
            view->drag_origin[0] = view->snapshot.recipes[view->snapshot.selected].positions[binding->control][0];
            view->drag_origin[1] = view->snapshot.recipes[view->snapshot.selected].positions[binding->control][1];
            view->drag_root[0] = event->xbutton.x_root; view->drag_root[1] = event->xbutton.y_root;
        } else {
            /* Preserve translations/native grabs for ordinary button, entry,
             * combo and scrollbar operations. Selection waits for release. */
            view->pending_control = binding->control;
        }
    } else if (event->type == ButtonRelease && event->xbutton.button == Button1 && view->pending_control >= 0) {
        if (view->selection_work) XtRemoveWorkProc(view->selection_work);
        view->selection_work = XtAppAddWorkProc(XtWidgetToApplicationContext(view->shell), selection_idle, view);
    }
}

static void control_event_install(Widget widget, ControlBinding *binding)
{
    WidgetList children = NULL;
    Cardinal count = 0, i;
    if (!XtIsWidget(widget)) return;
    XtAddEventHandler(widget, ButtonPressMask | ButtonReleaseMask | PointerMotionMask,
                       False, canvas_control_event, binding);
    if (XtIsComposite(widget)) {
        XtVaGetValues(widget, XtNchildren, &children, XtNnumChildren, &count, NULL);
        for (i = 0; i < count; ++i) control_event_install(children[i], binding);
    }
}

/* Gtk.Plug uses the public XEmbed protocol. Foreign operations are bounded to
 * a direct child of this canvas; disappearing children cannot kill the editor. */
static int embed_error;
static int embed_error_handler(Display *display, XErrorEvent *event)
{
    (void)display; embed_error = event->error_code; return 0;
}

static int (*embed_trap(Display *display))(Display *, XErrorEvent *)
{
    XSync(display, False); embed_error = 0;
    return XSetErrorHandler(embed_error_handler);
}

static int embed_untrap(Display *display, int (*previous)(Display *, XErrorEvent *))
{
    XSync(display, False); XSetErrorHandler(previous); return embed_error == 0;
}

static XImage *safe_xget_image(Display *display, Drawable drawable, int x,
                               int y, unsigned int width,
                               unsigned int height)
{
    int (*previous)(Display *, XErrorEvent *);
    XImage *image;
    previous = embed_trap(display);
    image = XGetImage(display, drawable, x, y, width, height, AllPlanes,
                      ZPixmap);
    if (!embed_untrap(display, previous)) {
        if (image)
            XDestroyImage(image);
        return NULL;
    }
    return image;
}

static int embed_direct_child(TLView *view, Window window)
{
    Display *display = XtDisplay(view->canvas);
    Window root, parent, *children = NULL;
    unsigned int count;
    int result, success, (*previous)(Display *, XErrorEvent *);
    if (window == None || !XtIsRealized(view->canvas)) return 0;
    previous = embed_trap(display);
    result = XQueryTree(display, window, &root, &parent, &children, &count);
    success = embed_untrap(display, previous);
    if (children != NULL) XFree(children);
    return success && result && parent == XtWindow(view->canvas);
}

static int embed_shell_active(TLView *view)
{
    Display *display = XtDisplay(view->shell);
    Window current, root, parent, *children;
    unsigned int count;
    int revert, depth, result, success, (*previous)(Display *, XErrorEvent *);
    XGetInputFocus(display, &current, &revert);
    for (depth = 0; depth < 32 && current != None && current != PointerRoot; ++depth) {
        if (current == XtWindow(view->shell)) return 1;
        children = NULL; previous = embed_trap(display);
        result = XQueryTree(display, current, &root, &parent, &children, &count);
        success = embed_untrap(display, previous);
        if (children != NULL) XFree(children);
        if (!success || !result || current == root || parent == current) break;
        current = parent;
    }
    return 0;
}

static void embed_send(TLView *view, long opcode, long detail, long data1, Time time)
{
    Display *display = XtDisplay(view->canvas);
    XEvent message;
    int (*previous)(Display *, XErrorEvent *);
    if (!embed_direct_child(view, view->embedded_child)) return;
    memset(&message, 0, sizeof(message));
    message.xclient.type = ClientMessage; message.xclient.display = display;
    message.xclient.window = view->embedded_child;
    message.xclient.message_type = view->xembed_atom; message.xclient.format = 32;
    message.xclient.data.l[0] = (long)time; message.xclient.data.l[1] = opcode;
    message.xclient.data.l[2] = detail; message.xclient.data.l[3] = data1;
    previous = embed_trap(display);
    XSendEvent(display, view->embedded_child, False, NoEventMask, &message);
    (void)embed_untrap(display, previous);
}

static void embed_resize(TLView *view)
{
    Display *display = XtDisplay(view->canvas);
    Dimension width, height;
    XEvent configured;
    Window descendant;
    int root_x = 0, root_y = 0;
    int (*previous)(Display *, XErrorEvent *);
    if (!embed_direct_child(view, view->embedded_child)) return;
    XtVaGetValues(view->canvas, XmNwidth, &width, XmNheight, &height, NULL);
    previous = embed_trap(display);
    XMoveResizeWindow(display, view->embedded_child, 0, 0,
                      width > 0 ? width : 1, height > 0 ? height : 1);
    /* GtkSocket acknowledges even a denied/same-size ConfigureRequest. GTK
     * waits for this notification before allocating the Plug's widget tree. */
    XTranslateCoordinates(display, view->embedded_child, DefaultRootWindow(display),
                           0, 0, &root_x, &root_y, &descendant);
    memset(&configured, 0, sizeof(configured));
    configured.xconfigure.type = ConfigureNotify; configured.xconfigure.display = display;
    configured.xconfigure.event = configured.xconfigure.window = view->embedded_child;
    configured.xconfigure.x = root_x; configured.xconfigure.y = root_y;
    configured.xconfigure.width = width > 0 ? width : 1;
    configured.xconfigure.height = height > 0 ? height : 1;
    XSendEvent(display, view->embedded_child, False, NoEventMask, &configured);
    (void)embed_untrap(display, previous);
}

static void embed_activation(TLView *view)
{
    int active = embed_shell_active(view);
    if (view->embedded_child != None && active != view->embedded_active) {
        view->embedded_active = active;
        embed_send(view, active ? XE_WINDOW_ACTIVATE : XE_WINDOW_DEACTIVATE,
                   0, 0, XtLastTimestampProcessed(XtDisplay(view->shell)));
    }
}

static void embed_notice(TLView *view)
{
    if (view->embedded_child != None || tl_gtk4_focus_has_child(view->gtk4_focus)) {
        char notice[256];
        XtUnmanageChild(view->canvas_notice);
        (void)snprintf(notice,sizeof(notice),
          "%s nativo acoplado.\nDesenho e entrada pertencem ao próprio renderizador; canvas em escala 1:1.",
          tl_family_labels[view->preview_family]);
        label_set(view->preview_notice,notice);
    } else if (view->preview_family != TL_MOTIF) {
        XtManageChild(view->canvas_notice);
        label_set(view->preview_notice,
          "Prévia nativa da família pelo controller.\nBackend acoplado ainda não mapeado neste canvas.");
    }
}
static void gtk4_embed_notice(XtPointer data)
{
    TLView *view = (TLView *)data;
    embed_notice(view);
    metrics_refresh(view);
}

static void embed_unregister(TLView *view, Window window)
{
    Display *display = XtDisplay(view->canvas);
    if (window == None || window == XtWindow(view->canvas)) return;
    /* Foreign drawable registration is not idempotent in Xt: it prepends a
     * mapping and UnregisterDrawable removes one.  Only remove our mappings. */
    while (XtWindowToWidget(display, window) == view->canvas)
        XtUnregisterDrawable(display, window);
}

static void embed_forget(TLView *view, Window window)
{
    if (window == None || (window != view->embedded_candidate && window != view->embedded_child)) return;
    embed_unregister(view, window);
    if (view->embedded_candidate == window) view->embedded_candidate = None;
    if (view->embedded_child == window) {
        view->embedded_child = None; view->embedded_focus = view->embedded_active = 0;
        embed_notice(view);
    }
}

static void embed_adopt(TLView *view, Window window)
{
    Display *display = XtDisplay(view->canvas);
    Atom type;
    int format, result, success, (*previous)(Display *, XErrorEvent *);
    unsigned long length, remaining, flags = 0;
    unsigned char *property = NULL;
    /* GTK4 has its own focus/size protocol and never claims GtkPlug support. */
    Atom gtk4_type;
    int gtk4_format;
    unsigned long gtk4_length, gtk4_remaining;
    unsigned char *gtk4_info = NULL;
    previous = embed_trap(display);
    Atom gtk4_atom = XInternAtom(display, "_THEME_LAB_GTK4_INFO", False);
    int gtk4_result = XGetWindowProperty(display, window, gtk4_atom, 0, 2, False,
        XA_CARDINAL, &gtk4_type, &gtk4_format, &gtk4_length, &gtk4_remaining, &gtk4_info);
    int gtk4_clean = embed_untrap(display, previous);
    int is_gtk4 = gtk4_clean && gtk4_result == Success && gtk4_type == XA_CARDINAL &&
        gtk4_format == 32 && gtk4_length == 2 && gtk4_remaining == 0 &&
        ((unsigned long *)gtk4_info)[0] == 1;
    if (gtk4_info) XFree(gtk4_info);
    if (is_gtk4) return;
    if (XtWindowToWidget(display, window) != NULL && window != view->embedded_candidate &&
        window != view->embedded_child) return;
    if (!embed_direct_child(view, window) ||
        (view->embedded_child != None && view->embedded_child != window)) return;
    previous = embed_trap(display);
    XSelectInput(display, window, PropertyChangeMask | StructureNotifyMask);
    result = XGetWindowProperty(display, window, view->xembed_info_atom, 0, 2, False,
                                view->xembed_info_atom, &type, &format, &length, &remaining, &property);
    success = embed_untrap(display, previous);
    if (!success || result != Success) { if (property != NULL) XFree(property); return; }
    if (XtWindowToWidget(display, window) == NULL)
        XtRegisterDrawable(display, window, view->canvas);
    if (type != view->xembed_info_atom || format != 32 || length != 2 || remaining != 0) {
        if (property != NULL) XFree(property);
        view->embedded_candidate = window; return;
    }
    flags = ((unsigned long *)property)[1]; XFree(property);
    if (view->embedded_child == None) {
        view->embedded_candidate = None; view->embedded_child = window;
        view->embedded_focus = view->embedded_active = 0;
        embed_resize(view);
        previous = embed_trap(display);
        if (flags & 1UL) XMapWindow(display, window); else XUnmapWindow(display, window);
        (void)embed_untrap(display, previous);
        embed_send(view, XE_EMBEDDED_NOTIFY, 0, (long)XtWindow(view->canvas), CurrentTime);
        embed_activation(view); embed_notice(view);
    } else {
        previous = embed_trap(display);
        if (flags & 1UL) XMapWindow(display, window); else XUnmapWindow(display, window);
        (void)embed_untrap(display, previous);
    }
}

static void embed_scan(TLView *view)
{
    Display *display = XtDisplay(view->canvas);
    Window root, parent, *children = NULL;
    unsigned int count = 0, i;
    if (view->embedded_child != None || !XtIsRealized(view->canvas)) return;
    if (XQueryTree(display, XtWindow(view->canvas), &root, &parent, &children, &count))
        for (i = 0; i < count && view->embedded_child == None; ++i)
            embed_adopt(view, children[i]);
    if (children != NULL) XFree(children);
}

static void embed_event(Widget widget, XtPointer client, XEvent *event, Boolean *continue_dispatch)
{
    TLView *view = (TLView *)client;
    Display *display = XtDisplay(view->canvas);
    Window canvas = XtIsRealized(view->canvas) ? XtWindow(view->canvas) : None;
    if (canvas == None) return;
    if (event->type == CreateNotify && event->xcreatewindow.parent == canvas)
        embed_adopt(view, event->xcreatewindow.window);
    else if (event->type == MapRequest && event->xmaprequest.parent == canvas)
        embed_adopt(view, event->xmaprequest.window);
    else if (event->type == MapNotify && event->xmap.event == canvas)
        embed_adopt(view, event->xmap.window);
    else if (event->type == ReparentNotify) {
        if (event->xreparent.parent == canvas) embed_adopt(view, event->xreparent.window);
        else { embed_forget(view, event->xreparent.window); embed_scan(view); }
    } else if (event->type == DestroyNotify) {
        embed_forget(view, event->xdestroywindow.window); embed_scan(view);
    }
    else if (event->type == PropertyNotify && event->xproperty.atom == view->xembed_info_atom &&
             (event->xproperty.window == view->embedded_child || event->xproperty.window == view->embedded_candidate))
        embed_adopt(view, event->xproperty.window);
    else if (event->type == ConfigureNotify && event->xconfigure.window == canvas)
        embed_resize(view);
    else if (event->type == ConfigureRequest && event->xconfigurerequest.parent == canvas) {
        if (view->embedded_child == None) embed_adopt(view, event->xconfigurerequest.window);
        if (event->xconfigurerequest.window == view->embedded_child) embed_resize(view);
    }
    else if (event->type == FocusIn || event->type == FocusOut) {
        embed_activation(view);
        if (widget == view->canvas && event->xfocus.window == canvas && event->xfocus.mode == NotifyNormal) {
            if (event->type == FocusIn && !view->embedded_focus) {
                view->embedded_focus = 1;
                embed_send(view, XE_FOCUS_IN, view->embedded_focus_detail, 0,
                           XtLastTimestampProcessed(display));
                view->embedded_focus_detail = XE_FOCUS_FIRST;
            } else if (event->type == FocusOut && event->xfocus.detail != NotifyInferior && view->embedded_focus) {
                view->embedded_focus = 0;
                embed_send(view, XE_FOCUS_OUT, 0, 0, XtLastTimestampProcessed(display));
            }
        }
    } else if (event->type == ClientMessage && event->xclient.window == canvas &&
               event->xclient.message_type == view->xembed_atom && event->xclient.format == 32 &&
               event->xclient.data.l[2] == 0 && event->xclient.data.l[3] == 0 && event->xclient.data.l[4] == 0 &&
               embed_direct_child(view, view->embedded_child) && embed_shell_active(view)) {
        long opcode = event->xclient.data.l[1];
        Time time = (Time)(uint32_t)event->xclient.data.l[0];
        if (opcode == XE_REQUEST_FOCUS) {
            view->embedded_focus_detail = XE_FOCUS_CURRENT;
            if (XmProcessTraversal(view->canvas, XmTRAVERSE_CURRENT)) {
                view->embedded_focus = 1; embed_activation(view);
                embed_send(view, XE_FOCUS_IN, XE_FOCUS_CURRENT, 0, time);
            }
        } else if (opcode == XE_FOCUS_NEXT || opcode == XE_FOCUS_PREV) {
            view->embedded_focus = 0; embed_send(view, XE_FOCUS_OUT, 0, 0, time);
            (void)XmProcessTraversal(view->canvas, opcode == XE_FOCUS_NEXT ?
                                     XmTRAVERSE_NEXT_TAB_GROUP : XmTRAVERSE_PREV_TAB_GROUP);
        }
        *continue_dispatch = False;
    } else if ((event->type == KeyPress || event->type == KeyRelease) && event->xkey.window == canvas &&
               view->embedded_focus && embed_shell_active(view) && embed_direct_child(view, view->embedded_child)) {
        XEvent forwarded = *event;
        int (*previous)(Display *, XErrorEvent *);
        forwarded.xkey.window = view->embedded_child;
        previous = embed_trap(display);
        XSendEvent(display, view->embedded_child, False, NoEventMask, &forwarded);
        (void)embed_untrap(display, previous);
        *continue_dispatch = False;
    }
}

static Widget combo_new(Widget parent, const char *name, const char *const *labels, int count)
{
    Widget combo;
    XmString *items = (XmString *)calloc((size_t)count, sizeof(*items));
    int i;
    if (items == NULL)
        return NULL;
    for (i = 0; i < count; ++i) items[i] = compound(labels[i]);
    combo = XtVaCreateManagedWidget(name, xmComboBoxWidgetClass, parent,
          XmNcomboBoxType, XmDROP_DOWN_LIST, XmNpositionMode, XmZERO_BASED,
          XmNitems, items, XmNitemCount, count, XmNvisibleItemCount, count < 10 ? count : 10,
          XmNselectedPosition, 0, NULL);
    for (i = 0; i < count; ++i) XmStringFree(items[i]);
    free(items);
    return combo;
}

static Widget field_row(Widget parent, const char *name, const char *caption,
                        int columns, Widget *field)
{
    Widget row = XtVaCreateManagedWidget(name, xmFormWidgetClass, parent,
                                         XmNfractionBase, 100, NULL);
    Widget label = label_new(row, "fieldLabel", caption);
    XtVaSetValues(label, XmNleftAttachment, XmATTACH_FORM,
                  XmNtopAttachment, XmATTACH_FORM,
                  XmNbottomAttachment, XmATTACH_FORM,
                  XmNrightAttachment, XmATTACH_POSITION,
                  XmNrightPosition, 63, NULL);
    *field = XtVaCreateManagedWidget("fieldValue", xmTextFieldWidgetClass, row,
                XmNcolumns, columns, XmNmaxLength, 95,
                XmNleftAttachment, XmATTACH_POSITION, XmNleftPosition, 64,
                XmNrightAttachment, XmATTACH_FORM,
                XmNtopAttachment, XmATTACH_FORM, NULL);
    return row;
}

static Widget section(Widget parent, const char *name, const char *title)
{
    Widget frame = XtVaCreateManagedWidget(name, xmFrameWidgetClass, parent,
                    XmNshadowType, XmSHADOW_ETCHED_IN, XmNshadowThickness, 2,
                    XmNmarginWidth, 5, XmNmarginHeight, 4, NULL);
    Widget heading = label_new(frame, "sectionTitle", title);
    XtVaSetValues(heading, XmNchildType, XmFRAME_TITLE_CHILD, NULL);
    return XtVaCreateManagedWidget("sectionContent", xmRowColumnWidgetClass,
                    frame, XmNorientation, XmVERTICAL, XmNpacking, XmPACK_TIGHT,
                    XmNspacing, 3, XmNmarginWidth, 0, XmNmarginHeight, 0, NULL);
}

static Widget menu_create(Widget menu_bar, const char *name,
                          const char *label, char mnemonic, int position,
                          const char *hint)
{
    char cascade_name[96];
    Widget popup = XmCreatePulldownMenu(menu_bar, (char *)name, NULL, 0);
    XmString title = compound(label);
    snprintf(cascade_name, sizeof(cascade_name), "%sCascade", name);
    Widget cascade = XtVaCreateManagedWidget(cascade_name, xmCascadeButtonWidgetClass,
          menu_bar, XmNlabelString, title, XmNsubMenuId, popup,
          XmNmnemonic, mnemonic, XmNpositionIndex, position, NULL);
    XmStringFree(title);
    tl_ui_hint(cascade, hint);
    return popup;
}

static Widget menu_item(Widget menu, const char *name, const char *label,
                        const char *hint, XtCallbackProc callback,
                        XtPointer data)
{
    XmString title = compound(label);
    Widget item = XtVaCreateManagedWidget(name, xmPushButtonWidgetClass, menu,
                                          XmNlabelString, title, NULL);
    XmStringFree(title);
    tl_ui_hint(item, hint);
    if (callback)
        XtAddCallback(item, XmNactivateCallback, callback, data);
    return item;
}

static void menu_separator(Widget menu, const char *name)
{
    (void)XtVaCreateManagedWidget(name, xmSeparatorWidgetClass, menu, NULL);
}

static void page_show(TLView *view, int page)
{
    if (!view || page < 0 || page >= TL_PAGE_COUNT)
        return;
    for (int i = 0; i < TL_PAGE_COUNT; ++i) {
        if (!view->pages[i])
            continue;
        if (i == page)
            XtManageChild(view->pages[i]);
        else
            XtUnmanageChild(view->pages[i]);
    }
    view->selected_page = page;
    if (view->page_selector)
        XtVaSetValues(view->page_selector, XmNselectedPosition, page, NULL);
}

static void page_combo_callback(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view = client;
    int page = combo_callback_index(widget, call);
    if (page >= 0)
        page_show(view, page);
}

static void page_menu_callback(Widget widget, XtPointer client, XtPointer call)
{
    PageBinding *binding = client;
    (void)widget;
    (void)call;
    page_show(binding->view, binding->page);
}

static void menus_create(TLView *view)
{
    static const char *const page_labels[TL_PAGE_COUNT] = {
        "Catálogo", "Controle e medições", "Peça e geometria",
        "Cores e relevo", "Modelo e referências", "Código da proposta"
    };
    static const char *const page_hints[TL_PAGE_COUNT] = {
        "Mostra a árvore de famílias e controles; trocar de página não altera a seleção.",
        "Mostra estado, posição, dimensões solicitadas e medidas nativas do controle em edição.",
        "Mostra peças independentes, geometria compartilhada e medidas específicas da escala GTK2.",
        "Mostra papéis KDE e fatores de relevo; nenhuma entrada define uma cor RGB final estática.",
        "Mostra nome, referência histórica, notas, limites e resultado da pipeta.",
        "Mostra busca e trecho da proposta somente leitura; gerar código não aplica o tema."
    };
    Widget file, reference, comparison, tools, display;
    Widget help_cascade;
    const int file_actions[] = {1, 2, 8, 5, 11};
    const char *const file_names[] = {"menuSave", "menuLoad", "menuImportDelta",
                                      "menuExport", "menuQuit"};
    const int reference_actions[] = {6, 3};
    const char *const reference_names[] = {"menuHistoricalImage", "menuPicker"};
    const int comparison_actions[] = {0, 4};
    const char *const comparison_names[] = {"menuRefresh", "menuSeparatePreview"};
    const int tool_actions[] = {10, 7, 9};
    const char *const tool_names[] = {"menuManualPaint", "menuRestoreFamily",
                                      "menuReconstructFiles"};
    static const char *const action_labels[ACTION_COUNT] = {
        "Atualizar", "Salvar", "Carregar", "Pipeta", "Prévia separada",
        "Exportar", "Imagem histórica", "Restaurar família", "Importar delta",
        "Reconstruir arquivos", "Pintura manual", "Sair"
    };
    static const char *const history_names[5] = {
        "projectUndoMenu", "projectRedoMenu", "projectMarkMenu",
        "projectRestoreMenu", "projectResetPartMenu"
    };
    static const char *const history_labels[5] = {
        "Desfazer projeto", "Refazer projeto", "Guardar ponto",
        "Voltar ao ponto", "Resetar peça"
    };
    static const char *const history_hints[5] = {
        "Desfaz um ajuste do projeto. O Undo próprio dos campos de texto permanece separado.",
        "Refaz um ajuste do projeto. O Redo próprio dos campos de texto permanece separado.",
        "Guarda o projeto atual como ponto persistente de comparação.",
        "Recupera o ponto guardado como uma alteração que também pode ser desfeita.",
        "Remove somente os ajustes da peça selecionada; Desfazer projeto recupera a peça."
    };
    static const TLAction history_actions[5] = {
        TL_PROJECT_UNDO, TL_PROJECT_REDO, TL_PROJECT_MARK,
        TL_PROJECT_RESTORE, TL_PROJECT_RESET_PART
    };

    help_cascade = XtNameToWidget(view->menu_bar, "*helpCascade");
    if (help_cascade)
        XtVaSetValues(help_cascade, XmNpositionIndex, 5, NULL);
    file = menu_create(view->menu_bar, "fileMenu", "Arquivo", 'A', 0,
                       "Operações persistentes do projeto e saída do laboratório.");
    reference = menu_create(view->menu_bar, "referenceMenu", "Referência", 'R', 1,
                            "Imagem histórica e amostra de cor, separadas das prévias nativas.");
    comparison = menu_create(view->menu_bar, "comparisonMenu", "Comparação", 'C', 2,
                             "Atualização e janela de prévia da família selecionada.");
    tools = menu_create(view->menu_bar, "toolsMenu", "Ferramentas", 'F', 3,
                        "Pintura, reconstrução e histórico recuperável do projeto.");
    display = menu_create(view->menu_bar, "displayMenu", "Exibir", 'E', 4,
                          "Escolhe qual grupo de ferramentas aparece na coluna esquerda.");

    for (size_t i = 0; i < sizeof(file_actions) / sizeof(file_actions[0]); ++i) {
        int action = file_actions[i];
        if (i == 4) menu_separator(file, "fileExitSeparator");
        menu_item(file, file_names[i], action_labels[action], tl_ui_action_hint(action),
                  action_callback, &view->bindings[action]);
    }
    for (size_t i = 0; i < sizeof(reference_actions) / sizeof(reference_actions[0]); ++i) {
        int action = reference_actions[i];
        menu_item(reference, reference_names[i], action_labels[action],
                  tl_ui_action_hint(action), action_callback, &view->bindings[action]);
    }
    for (size_t i = 0; i < sizeof(comparison_actions) / sizeof(comparison_actions[0]); ++i) {
        int action = comparison_actions[i];
        menu_item(comparison, comparison_names[i], action_labels[action],
                  tl_ui_action_hint(action), action_callback, &view->bindings[action]);
    }
    for (size_t i = 0; i < sizeof(tool_actions) / sizeof(tool_actions[0]); ++i) {
        int action = tool_actions[i];
        menu_item(tools, tool_names[i], action_labels[action], tl_ui_action_hint(action),
                  action_callback, &view->bindings[action]);
    }
    menu_separator(tools, "toolsHistorySeparator");
    for (int i = 0; i < 5; ++i) {
        view->history_bindings[i].view = view;
        view->history_bindings[i].action = history_actions[i];
        view->history_menu_items[i] = menu_item(
            tools, history_names[i], history_labels[i], history_hints[i],
            action_callback, &view->history_bindings[i]);
    }
    for (int i = 0; i < TL_PAGE_COUNT; ++i) {
        view->page_bindings[i].view = view;
        view->page_bindings[i].page = i;
        menu_item(display, "displayPage", page_labels[i], page_hints[i],
                  page_menu_callback, &view->page_bindings[i]);
    }
    /* Motif does not post ordinary Primitive tooltips for pulldown entries in
     * this runtime.  Install the same delayed, palette-aware bridge used by
     * the editor menu after every child has been created. */
    tl_ui_menu_hints(file);
    tl_ui_menu_hints(reference);
    tl_ui_menu_hints(comparison);
    tl_ui_menu_hints(tools);
    tl_ui_menu_hints(display);
}

/* The comparison keeps a scrollable minimum.  Above that minimum, Motif and
 * the selected family divide extra horizontal space and both receive the same
 * extra viewport height.  Their inner canvases remain 1:1 and scroll
 * independently; only the viewport grows, never control geometry or the
 * historical scale. */
static void preview_stack_resize(TLView *view)
{
    Widget clip = NULL;
    Dimension clip_width = 0, clip_height = 0;
    Dimension stack_width = 0, stack_height = 0, wanted_width = 0, wanted_height = 0;
    Dimension native_width = 0, motif_width = 0;
    Dimension native_height = 0, motif_height = 0;
    unsigned long width_extra, height_extra, native_extra;

    if (view == NULL || view->preview_stack_scroll == NULL ||
        view->preview_stack == NULL || view->preview_canvas_scroll == NULL ||
        view->motif_reference_scroll == NULL)
        return;
    XtVaGetValues(view->preview_stack_scroll, XmNclipWindow, &clip, NULL);
    if (clip == NULL)
        return;
    XtVaGetValues(clip, XmNwidth, &clip_width, XmNheight, &clip_height, NULL);
    XtVaGetValues(view->preview_stack, XmNwidth, &stack_width,
                  XmNheight, &stack_height, NULL);
    XtVaGetValues(view->preview_canvas_scroll, XmNwidth, &native_width,
                  XmNheight, &native_height, NULL);
    XtVaGetValues(view->motif_reference_scroll, XmNwidth, &motif_width,
                  XmNheight, &motif_height, NULL);
    if (!clip_width || !clip_height || !stack_width || !stack_height ||
        !native_width || !motif_width || !native_height || !motif_height)
        return;
    if (!view->preview_stack_layout_ready) {
        unsigned long combined_width = (unsigned long)native_width +
                                       motif_width + 24;
        Dimension tallest = native_height > motif_height ? native_height : motif_height;
        unsigned long combined_height = (unsigned long)tallest + 72;
        view->preview_stack_min_width =
            combined_width > stack_width ? (Dimension)combined_width : stack_width;
        view->preview_stack_min_height =
            combined_height > stack_height ? (Dimension)combined_height : stack_height;
        view->preview_canvas_min_width = native_width;
        view->motif_reference_min_width = motif_width;
        view->preview_canvas_min_height = native_height;
        view->motif_reference_min_height = motif_height;
        view->preview_stack_layout_ready = 1;
    }
    wanted_width = clip_width > view->preview_stack_min_width ?
                   clip_width : view->preview_stack_min_width;
    width_extra = (unsigned long)wanted_width - view->preview_stack_min_width;
    native_extra = width_extra / 2;
    motif_width = (Dimension)(view->motif_reference_min_width + native_extra);
    native_width = (Dimension)(view->preview_canvas_min_width +
                               width_extra - native_extra);
    {
        Dimension current_native = 0, current_motif = 0;
        XtVaGetValues(view->preview_canvas_scroll, XmNwidth, &current_native, NULL);
        XtVaGetValues(view->motif_reference_scroll, XmNwidth, &current_motif, NULL);
        if (current_native != native_width)
            XtVaSetValues(view->preview_canvas_scroll, XmNwidth, native_width, NULL);
        if (current_motif != motif_width)
            XtVaSetValues(view->motif_reference_scroll, XmNwidth, motif_width, NULL);
    }
    if (stack_width != wanted_width)
        XtVaSetValues(view->preview_stack, XmNwidth, wanted_width, NULL);
    wanted_height = clip_height > view->preview_stack_min_height ?
                    clip_height : view->preview_stack_min_height;
    height_extra = (unsigned long)wanted_height - view->preview_stack_min_height;
    native_height = (Dimension)(view->preview_canvas_min_height + height_extra);
    motif_height = (Dimension)(view->motif_reference_min_height + height_extra);
    if (stack_height != wanted_height)
        XtVaSetValues(view->preview_stack, XmNheight, wanted_height, NULL);
    {
        Dimension current_native = 0, current_motif = 0;
        XtVaGetValues(view->preview_canvas_scroll, XmNheight, &current_native, NULL);
        XtVaGetValues(view->motif_reference_scroll, XmNheight, &current_motif, NULL);
        if (current_native != native_height)
            XtVaSetValues(view->preview_canvas_scroll, XmNheight, native_height, NULL);
        if (current_motif != motif_height)
            XtVaSetValues(view->motif_reference_scroll, XmNheight, motif_height, NULL);
    }
}

static void preview_stack_resize_event(Widget widget, XtPointer data,
                                       XEvent *event, Boolean *dispatch)
{
    (void)widget;
    (void)dispatch;
    if (event != NULL &&
        (event->type == ConfigureNotify || event->type == MapNotify))
        preview_stack_resize((TLView *)data);
}

static void number_row(TLView *view, Widget parent, const char *name,
                       const char *caption, int columns, Widget *field,
                       int minimum, int maximum, int step, int digits)
{
    Widget row = field_row(parent, name, caption, columns, field);
    Widget spin;
    XtDestroyWidget(*field);
    spin = XtVaCreateManagedWidget("numberSpin", xmSpinBoxWidgetClass, row,
          XmNarrowLayout, XmARROWS_END, XmNwrap, False, XmNspacing, 1,
          XmNleftAttachment, XmATTACH_POSITION, XmNleftPosition, 64,
          XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_FORM, NULL);
    *field = XtVaCreateManagedWidget("fieldValue", xmTextFieldWidgetClass, spin,
          XmNcolumns, columns, XmNmaxLength, 31, XmNspinBoxChildType, XmNUMERIC,
          XmNpositionType, XmPOSITION_VALUE, XmNminimumValue, minimum,
          XmNmaximumValue, maximum, XmNincrementValue, step,
          XmNdecimalPoints, digits, XmNposition, minimum, NULL);
    XtAddCallback(spin, XmNmodifyVerifyCallback, number_verify, view);
}

static void font_widget(Widget widget, XmFontList fonts)
{
    WidgetList children = NULL;
    Cardinal count = 0, i;
    if (fonts == NULL) return;
    if (XmIsLabel(widget) || XmIsLabelGadget(widget) || XmIsText(widget) ||
        XmIsTextField(widget) || XmIsList(widget) || XmIsScale(widget))
        XtVaSetValues(widget, XmNfontList, fonts, NULL);
    if (XmIsComboBox(widget))
        XtVaSetValues(widget, XmNrenderTable, fonts, NULL);
    if (XtIsComposite(widget)) {
        XtVaGetValues(widget, XtNchildren, &children, XtNnumChildren, &count, NULL);
        for (i = 0; i < count; ++i) font_widget(children[i], fonts);
    }
}

static XmFontList fontset_load(TLView *view, const char *pattern)
{
    TLFontPolicy report;
    return tl_font_policy_load(XtDisplay(view->shell), pattern, &report);
}

static void remember_native_font(TLView *view)
{
    XmFontContext context;
    XmFontListEntry entry;
    XmFontType type;
    XtPointer font;
    XFontStruct **fonts = NULL;
    char **names = NULL;
    /* FontSet interprets all UTF-8 labels, entries and text in the actual
     * locale. The previous FONT_IS_FONT treated UTF-8 bytes as Latin-1. */
    view->native_font = fontset_load(view, "fixed");
    if (view->native_font == NULL) return;
    font_widget(view->root, view->native_font);
    font_widget(view->reference_dialog, view->native_font);
    font_widget(tl_help_dialog(view->help),view->native_font);
    font_widget(tl_export_review_dialog(view->export_review),view->native_font);
    font_widget(XmToolTipGetLabel(XtParent(tl_export_review_dialog(view->export_review))),view->native_font);
    font_widget(tl_help_popup(view->help),view->native_font);
    font_widget(XmToolTipGetLabel(XtParent(tl_help_dialog(view->help))),view->native_font);
    if (!XmFontListInitFontContext(&context, view->native_font)) return;
    entry = XmFontListNextEntry(context);
    if (entry != NULL) {
        font = XmFontListEntryGetFont(entry, &type);
        if (font != NULL && type == XmFONT_IS_FONTSET &&
            XFontsOfFontSet((XFontSet)font, &fonts, &names) > 0 && names[0] != NULL)
            (void)snprintf(view->native_xlfd, sizeof(view->native_xlfd), "%s", names[0]);
    }
    XmFontListFreeFontContext(context);
}

/* Keep the native family/style while sizing a locale FontSet, so preview
 * updates cannot reintroduce the single-byte font bug. */
static XmFontList sized_native_font(TLView *view, int pixels)
{
    TLFontPolicy report;
    return tl_font_policy_sized_load(XtDisplay(view->shell), view->native_xlfd,
                                    pixels, &report);
}

static void preview_font_apply(TLView *view, int pixels)
{
    XmFontList list;
    if (pixels == view->preview_font_px) return;
    view->preview_font_px = pixels;
    list = sized_native_font(view, pixels);
    font_widget(view->preview_form, list != NULL ? list : view->native_font);
    if (view->preview_font != NULL) XmFontListFree(view->preview_font);
    view->preview_font = list;
}

static void reference_font_apply(TLView *view, int pixels)
{
    XmFontList list;
    if (pixels == view->reference_font_px) return;
    view->reference_font_px = pixels;
    list = sized_native_font(view, pixels);
    font_widget(view->motif_reference_form, list != NULL ? list : view->native_font);
    if (view->reference_font != NULL) XmFontListFree(view->reference_font);
    view->reference_font = list;
}

static void motif_controls_create(Widget form, Widget widgets[TL_CONTROL_COUNT])
{
    Widget spin_text, list, inner;
    static const char *const options[] = { TL_SAMPLE_COMBO_A, TL_SAMPLE_COMBO_B, TL_SAMPLE_COMBO_C };
    XmString entries[3];
    int i;
    widgets[0] = XtVaCreateManagedWidget("nativePushButton",
          xmPushButtonWidgetClass, form, NULL);
    label_set(widgets[0], TL_SAMPLE_PUSH);
    widgets[1] = XtVaCreateManagedWidget("nativeToggleButton",
          xmToggleButtonWidgetClass, form, XmNindicatorOn, False, NULL);
    label_set(widgets[1], TL_SAMPLE_TOGGLE);
    widgets[2] = XtVaCreateManagedWidget("nativeCheckButton",
          xmToggleButtonWidgetClass, form, XmNset, True, NULL);
    label_set(widgets[2], TL_SAMPLE_CHECK);
    widgets[3] = XtVaCreateManagedWidget("nativeRadioButton",
          xmToggleButtonWidgetClass, form, XmNindicatorType, XmONE_OF_MANY,
          XmNset, True, NULL);
    label_set(widgets[3], TL_SAMPLE_RADIO);
    widgets[4] = XtVaCreateManagedWidget("nativeTextField",
          xmTextFieldWidgetClass, form, XmNcolumns, 14,
          XmNvalue, TL_SAMPLE_ENTRY, NULL);
    widgets[5] = combo_new(form, "nativeComboBox", options, 3);
    widgets[6] = XtVaCreateManagedWidget("nativeSpinBox",
          xmSpinBoxWidgetClass, form, NULL);
    spin_text = XtVaCreateManagedWidget("nativeSpinValue", xmTextFieldWidgetClass,
          widgets[6], XmNspinBoxChildType, XmNUMERIC, XmNminimumValue, 0,
          XmNmaximumValue, 100, XmNposition, TL_SAMPLE_SPIN, XmNcolumns, 5, NULL);
    (void)spin_text;
    widgets[7] = XtVaCreateManagedWidget("nativeMultilineText",
          xmTextWidgetClass, form, XmNeditMode, XmMULTI_LINE_EDIT,
          XmNrows, 3, XmNcolumns, 14, XmNwordWrap, True, NULL);
    XmTextSetString(widgets[7], TL_SAMPLE_TEXT);
    widgets[8] = XtVaCreateManagedWidget("nativeHorizontalScale",
          xmScaleWidgetClass, form, XmNorientation, XmHORIZONTAL,
          XmNminimum, 0, XmNmaximum, 100, XmNvalue, TL_SAMPLE_SCALE_H, XmNshowValue, True,
          XmNscaleWidth, 135, NULL);
    widgets[9] = XtVaCreateManagedWidget("nativeVerticalScale",
          xmScaleWidgetClass, form, XmNorientation, XmVERTICAL,
          XmNminimum, 0, XmNmaximum, 100, XmNvalue, TL_SAMPLE_SCALE_V, XmNshowValue, True,
          XmNscaleHeight, 66, NULL);
    widgets[10] = XtVaCreateManagedWidget("nativeHorizontalScrollBar",
          xmScrollBarWidgetClass, form, XmNorientation, XmHORIZONTAL,
          XmNminimum, 0, XmNmaximum, 100, XmNvalue, TL_SAMPLE_SCROLL, XmNsliderSize, TL_SAMPLE_PAGE_SIZE, NULL);
    widgets[11] = XtVaCreateManagedWidget("nativeVerticalScrollBar",
          xmScrollBarWidgetClass, form, XmNorientation, XmVERTICAL,
          XmNminimum, 0, XmNmaximum, 100, XmNvalue, TL_SAMPLE_SCROLL, XmNsliderSize, TL_SAMPLE_PAGE_SIZE,
          XmNheight, 65, NULL);
    widgets[12] = XtVaCreateManagedWidget("nativeArrowButton",
          xmArrowButtonWidgetClass, form, XmNarrowDirection, XmARROW_DOWN, NULL);
    /* Standard Motif has no ProgressBar class. A read-only Scale is explicitly
     * identified as the native level substitute; GTK gets a real ProgressBar. */
    widgets[13] = XtVaCreateManagedWidget("nativeLevelScale",
          xmScaleWidgetClass, form, XmNorientation, XmHORIZONTAL,
          XmNminimum, 0, XmNmaximum, 100, XmNvalue, TL_SAMPLE_LEVEL, XmNshowValue, True,
          XmNsensitive, False, XmNscaleWidth, 125, NULL);
    entries[0] = compound(TL_SAMPLE_LIST_A); entries[1] = compound(TL_SAMPLE_LIST_B); entries[2] = compound(TL_SAMPLE_LIST_C);
    list = XtVaCreateManagedWidget("nativeList", xmListWidgetClass, form,
          XmNitems, entries, XmNitemCount, 3, XmNvisibleItemCount, 3,
          XmNselectionPolicy, XmSINGLE_SELECT, NULL);
    widgets[14] = list;
    XmListSelectPos(list, 2, False);
    for (i = 0; i < 3; ++i) XmStringFree(entries[i]);
    widgets[15] = XtVaCreateManagedWidget("nativeControlFrame", xmFrameWidgetClass,
          form, XmNshadowType, XmSHADOW_IN, XmNshadowThickness, 2, NULL);
    inner = label_new(widgets[15], "frameCaption", TL_SAMPLE_FRAME);
    XtVaSetValues(inner, XmNwidth, 110, XmNheight, 40, NULL);
    for (i = 0; i < TL_CONTROL_COUNT; ++i) {
        tl_ui_hint(widgets[i],tl_ui_motif_control_hint(i));
        XtVaSetValues(widgets[i], XmNleftAttachment, XmATTACH_NONE,
                      XmNtopAttachment, XmATTACH_NONE,
                      XmNx, 16 + (i % 4) * 160, XmNy, 16 + (i / 4) * 80,
                      XmNwidth, i == 9 || i == 11 ? 35 : 135, NULL);
    }
}

static void preview_create(TLView *view, Widget parent)
{
    Widget content, scroll;
    int i;
    content = section(parent, "nativePreview", "Canvas da família — controles reais");
    view->preview_notice = label_new(content, "previewNotice", "Motif nativo do toolkit instalado.");
    XtVaSetValues(view->preview_notice, XmNrecomputeSize, False, XmNwidth, 490,
                   XmNheight, 42, NULL);
    view->preview_frame = XtVaCreateManagedWidget("nativeSunkenFrame", xmFrameWidgetClass,
          content, XmNshadowType, XmSHADOW_IN, XmNshadowThickness, 2, NULL);
    scroll = XtVaCreateManagedWidget("canvasScroll", xmScrolledWindowWidgetClass,
          view->preview_frame, XmNscrollingPolicy, XmAUTOMATIC,
          XmNscrollBarDisplayPolicy, XmAS_NEEDED, XmNwidth, 510, XmNheight, 370, NULL);
    view->preview_canvas_scroll = scroll;
    view->canvas = XtVaCreateManagedWidget("familyCanvas", xmDrawingAreaWidgetClass,
          scroll, XmNwidth, 740, XmNheight, 410, XmNresizePolicy, XmRESIZE_NONE,
          XmNmarginWidth, 0, XmNmarginHeight, 0,
          XmNtraversalOn, True, XmNnavigationType, XmTAB_GROUP, NULL);
    view->xembed_atom = XInternAtom(XtDisplay(view->canvas), "_XEMBED", False);
    view->xembed_info_atom = XInternAtom(XtDisplay(view->canvas), "_XEMBED_INFO", False);
    view->embedded_focus_detail = XE_FOCUS_FIRST;
    XtAddEventHandler(view->canvas, SubstructureRedirectMask | SubstructureNotifyMask |
             StructureNotifyMask | PropertyChangeMask | FocusChangeMask | KeyPressMask | KeyReleaseMask,
             True, embed_event, view);
    XtAddEventHandler(view->shell, FocusChangeMask, False, embed_event, view);
    view->gtk4_focus = tl_gtk4_focus_create(view->canvas);
    view->preview_form = XtVaCreateManagedWidget("nativePreviewControls", xmFormWidgetClass,
          view->canvas, XmNwidth, 740, XmNheight, 410, XmNresizePolicy, XmRESIZE_NONE, NULL);
    view->canvas_notice = label_new(view->canvas, "canvasCapability",
         "Esta família utiliza seu próprio backend nativo.\nAbra a prévia da família; embedding ainda não confirmado.");
    XtVaSetValues(view->canvas_notice, XmNx, 12, XmNy, 12,
                   XmNwidth, 480, XmNheight, 65, NULL);
    XtUnmanageChild(view->canvas_notice);
    tl_gtk4_focus_observer(view->gtk4_focus,gtk4_embed_notice,view);
    motif_controls_create(view->preview_form, view->preview_widgets);
    for (i = 0; i < TL_CONTROL_COUNT; ++i) {
        Widget widget = view->preview_widgets[i];
        view->control_bindings[i].view = view; view->control_bindings[i].control = i;
        XtVaSetValues(widget, XmNleftAttachment, XmATTACH_NONE,
                      XmNtopAttachment, XmATTACH_NONE,
                      XmNx, 16 + (i % 4) * 160, XmNy, 16 + (i / 4) * 80,
                      XmNwidth, i == 9 || i == 11 ? 35 : 135, NULL);
        control_event_install(widget, &view->control_bindings[i]);
    }
}

static void palette_widget(Widget widget, const Pixel pixels[COLOR_COUNT])
{
    WidgetList children = NULL;
    Cardinal count = 0, i;
    Pixel background;
    if (widget == NULL) return;
    background = pixels[FACE];
    if (XmIsText(widget) || XmIsTextField(widget) || XmIsList(widget)) background = pixels[VIEW];
    XtVaSetValues(widget, XmNbackground, background, NULL);
    if (XmIsPrimitive(widget) || XmIsManager(widget))
        XtVaSetValues(widget, XmNforeground, pixels[TEXT], XmNtopShadowColor, pixels[LIGHT],
                       XmNbottomShadowColor, pixels[SHADOW], NULL);
    if (XmIsPrimitive(widget)) XtVaSetValues(widget, XmNhighlightColor, pixels[SELECTION], NULL);
    if (XmIsToggleButton(widget))
        XtVaSetValues(widget, XmNselectColor, pixels[SELECTION], XmNunselectColor, pixels[FACE], NULL);
    if (XmIsPushButton(widget)) XtVaSetValues(widget, XmNarmColor, pixels[TROUGH], NULL);
    if (XmIsScrollBar(widget)) XtVaSetValues(widget, XmNtroughColor, pixels[TROUGH], NULL);
    if (XtIsComposite(widget)) {
        XtVaGetValues(widget, XtNchildren, &children, XtNnumChildren, &count, NULL);
        for (i = 0; i < count; ++i) palette_widget(children[i], pixels);
    }
}

static void palette_header_widget(Widget widget,
                                  const Pixel pixels[COLOR_COUNT])
{
    if (widget == NULL)
        return;
    XtVaSetValues(widget, XmNbackground, pixels[FACE], NULL);
    if (XmIsPrimitive(widget) || XmIsManager(widget))
        XtVaSetValues(widget, XmNforeground, pixels[TEXT],
                      XmNtopShadowColor, pixels[LIGHT],
                      XmNbottomShadowColor, pixels[SHADOW], NULL);
    if (XmIsPrimitive(widget))
        XtVaSetValues(widget, XmNhighlightColor, pixels[SELECTION], NULL);
}

static void palette_menu_bar(Widget menu, const Pixel pixels[COLOR_COUNT])
{
    WidgetList children = NULL;
    Cardinal count = 0, i;
    palette_header_widget(menu, pixels);
    if (menu == NULL || !XtIsComposite(menu))
        return;
    XtVaGetValues(menu, XtNchildren, &children, XtNnumChildren, &count, NULL);
    for (i = 0; i < count; ++i)
        if (XmIsCascadeButton(children[i]))
            palette_header_widget(children[i], pixels);
}

static void colors_allocate(TLView *view, const unsigned short rgb[6][3], double trough,
                            Pixel pixels[COLOR_COUNT], int allocated[COLOR_COUNT])
{
    Display *display = XtDisplay(view->shell);
    Colormap colormap;
    int i, channel;
    if (trough < 0.0) trough = 0.0;
    if (trough > 1.0) trough = 1.0;
    XtVaGetValues(view->shell, XtNcolormap, &colormap, NULL);
    for (i = 0; i < COLOR_COUNT; ++i) {
        XColor color;
        unsigned short values[3];
        Pixel old = pixels[i];
        int old_allocated = allocated[i];
        for (channel = 0; channel < 3; ++channel)
            values[channel] = i < TROUGH ? rgb[i][channel] :
                 (unsigned short)(rgb[FACE][channel] * (1.0 - trough) + rgb[SHADOW][channel] * trough + 0.5);
        color.red = values[0]; color.green = values[1]; color.blue = values[2];
        color.flags = DoRed | DoGreen | DoBlue;
        allocated[i] = XAllocColor(display, colormap, &color) != 0;
        if (allocated[i]) pixels[i] = color.pixel;
        else XtVaGetValues(view->root, i == TEXT ? XmNforeground : XmNbackground, &pixels[i], NULL);
        if (old_allocated) XFreeColors(display, colormap, &old, 1, 0);
    }
}

static void palette_apply(TLView *view)
{
    if (view->palette_valid) {
        colors_allocate(view, view->rgb, .15, view->pixels, view->pixel_allocated);
        palette_widget(view->root, view->pixels);
        palette_widget(view->reference_dialog, view->pixels);
        palette_widget(tl_help_dialog(view->help),view->pixels);
        palette_widget(tl_export_review_dialog(view->export_review),view->pixels);
        palette_widget(XmToolTipGetLabel(XtParent(tl_export_review_dialog(view->export_review))),view->pixels);
        palette_widget(tl_help_popup(view->help),view->pixels);
        palette_widget(XmToolTipGetLabel(XtParent(tl_help_dialog(view->help))),view->pixels);
        for(FileChoice *choice=view->choices;choice;choice=choice->next){
            palette_widget(choice->dialog,view->pixels);
            palette_widget(XmToolTipGetLabel(XtParent(choice->dialog)),view->pixels);
        }
        Widget tip=XmToolTipGetLabel(view->shell);
        if(tip)palette_widget(tip,view->pixels);
        XtVaSetValues(view->shell, XmNbackground, view->pixels[FACE], NULL);
    }
    if (view->header_palette_valid) {
        colors_allocate(view, view->header_rgb, .15, view->header_pixels,
                        view->header_pixel_allocated);
        palette_menu_bar(view->menu_bar, view->header_pixels);
    }
    if (view->preview_palette_valid) {
        colors_allocate(view, view->preview_rgb, view->preview_trough,
                        view->preview_pixels, view->preview_pixel_allocated);
        /* Keep tools/headers/code on the current palette, even when testing a
         * different selectable scheme in this one preview area. */
        palette_widget(view->preview_form, view->preview_pixels);
        /* Search selection is the one code-panel detail that follows the
         * selected test scheme; the surrounding editor remains on KDE UI roles. */
        if (view->code)
            XtVaSetValues(view->code, XmNselectColor,
                          view->preview_pixels[SELECTION], NULL);
    }
    if (view->reference_palette_valid) {
        colors_allocate(view, view->reference_rgb, view->reference_trough,
                        view->reference_pixels, view->reference_pixel_allocated);
        palette_widget(view->motif_reference_form, view->reference_pixels);
    }
    tl_editor_refresh_menus(view->editors);
    tl_ui_spin_hints_refresh(view->root);
}

static void control_sizes(Widget widgets[TL_CONTROL_COUNT], const TLRecipe *recipe,
                          int previous[TL_CONTROL_COUNT][2], Dimension base[TL_CONTROL_COUNT][2])
{
    for (int i = 0; i < TL_CONTROL_COUNT; ++i) {
        Widget widget = widgets[i];
        Dimension current[2];
        XtVaGetValues(widget, XmNwidth, &current[0], XmNheight, &current[1], NULL);
        for (int axis = 0; axis < 2; ++axis)
            if (!previous[i][axis]) base[i][axis] = current[axis];
        if (XmIsLabel(widget))
            XtVaSetValues(widget, XmNrecomputeSize, !recipe->sizes[i][0] && !recipe->sizes[i][1], NULL);
        for (int axis = 0; axis < 2; ++axis) {
            int size = recipe->sizes[i][axis];
            if (size || previous[i][axis])
                XtVaSetValues(widget, axis ? XmNheight : XmNwidth, size ? (Dimension)size : base[i][axis], NULL);
            previous[i][axis] = size;
        }
    }
}

/* Use the current native allocation after sizing; never subtract the request
 * (zero delegates to Motif, and a short request may be enlarged by it). */
static int control_place(Widget widget, const TLRecipe *recipe, int index,
                         Dimension *width, Dimension *height, int origin[2])
{
    XtVaGetValues(widget, XmNwidth, width, XmNheight, height, NULL);
    if (tl_control_anchor_origin(recipe, index, *width, *height, origin)) {
        XtUnmanageChild(widget);
        return -1;
    }
    /* XmForm retains attachment constraints across manage/unmanage. Updating
     * only core x/y lets it restore the previous position when shown. */
    XtVaSetValues(widget, XmNleftAttachment, XmATTACH_FORM,
                  XmNtopAttachment, XmATTACH_FORM,
                  XmNleftOffset, origin[0], XmNtopOffset, origin[1], NULL);
    return 0;
}

/* The reference has its own recipe. GTK geometry and pointer events never
 * mutate it; the installed Motif widgets supply their native interaction. */
static void motif_reference_scene(TLView *view, const TLModel *model)
{
    const TLRecipe *recipe = &model->recipes[TL_MOTIF];
    const TLGeometry *geometry = &recipe->geometry;
    const TLRecipe *editing = &model->recipes[model->selected];
    Dimension width = 740, height = 410;
    char notice[256];
    int i, anchor_invalid = 0;
    view->reference_trough = recipe->palette.trough;
    XtVaSetValues(view->motif_reference_frame, XmNshadowThickness, geometry->shadow_px,
                  XmNmarginWidth, geometry->view_bar_gap_px,
                  XmNmarginHeight, geometry->view_bar_gap_px, NULL);
    XtVaSetValues(view->motif_reference_form, XmNmarginWidth, geometry->view_inset_px,
                  XmNmarginHeight, geometry->view_inset_px, NULL);
    for (i = 0; i < TL_CONTROL_COUNT; ++i) {
        Widget widget = view->motif_reference_widgets[i];
        int visible = (editing->visible_controls & (1 << i)) &&
                      (editing->visible_categories & (1 << control_category[i]));
        XtVaSetValues(widget, XmNsensitive, i != 13, NULL);
        if (visible) XtManageChild(widget); else XtUnmanageChild(widget);
    }
    XtVaSetValues(view->motif_reference_widgets[10], XmNheight, geometry->bar_px,
                  XmNshadowThickness, geometry->shadow_px, NULL);
    XtVaSetValues(view->motif_reference_widgets[11], XmNwidth, geometry->bar_px,
                  XmNshadowThickness, geometry->shadow_px, NULL);
    XtVaSetValues(view->motif_reference_widgets[12], XmNwidth, geometry->bar_px,
                  XmNheight, geometry->bar_px, XmNshadowThickness, geometry->shadow_px,
                  XmNhighlightThickness, 0, NULL);
    XtVaSetValues(view->motif_reference_widgets[8], XmNscaleHeight, geometry->bar_px,
                  XmNshadowThickness, geometry->shadow_px, NULL);
    XtVaSetValues(view->motif_reference_widgets[9], XmNscaleWidth, geometry->bar_px,
                  XmNshadowThickness, geometry->shadow_px, NULL);
    reference_font_apply(view, geometry->font_px);
    control_sizes(view->motif_reference_widgets, recipe, view->reference_sizes, view->reference_base_sizes);
    width = 740; height = 410;
    for (i = 0; i < TL_CONTROL_COUNT; ++i) {
        Dimension item_width, item_height;
        int origin[2];
        if (control_place(view->motif_reference_widgets[i], recipe, i,
                          &item_width, &item_height, origin)) {
            anchor_invalid = 1; continue;
        }
        if ((unsigned)origin[0] + item_width + 12U > width)
            width = (Dimension)(origin[0] + item_width + 12U);
        if ((unsigned)origin[1] + item_height + 12U > height)
            height = (Dimension)(origin[1] + item_height + 12U);
    }
    XtVaSetValues(view->motif_reference_form, XmNwidth, width, XmNheight, height, NULL);
    (void)snprintf(notice, sizeof(notice),
          "Referência Motif: %s.\nReceita independente; pressione os controles. Nível usa Scale.",
          control_labels[editing->selected_control]);
    label_set(view->motif_reference_notice, notice);
    if (anchor_invalid)
        label_set(view->motif_reference_notice,
                  "Referência Motif: âncora fora do canvas; controle não exibido.\nCorrija a posição ou comprimento; receita preservada.");
}

/* Motif exposes these resources, but independent ScrollBar arrow/thumb/gap
 * metrics and a true ProgressBar remain capabilities of the other backends. */
static void preview_geometry(TLView *view, const TLGeometry *geometry)
{
    int i;
    XtVaSetValues(view->preview_frame, XmNshadowThickness, geometry->shadow_px,
                 XmNmarginWidth, geometry->view_bar_gap_px, XmNmarginHeight, geometry->view_bar_gap_px, NULL);
    XtVaSetValues(view->preview_form, XmNmarginWidth, geometry->view_inset_px,
                 XmNmarginHeight, geometry->view_inset_px, NULL);
    XtVaSetValues(view->preview_widgets[10], XmNheight, geometry->bar_px,
                 XmNshadowThickness, geometry->shadow_px, NULL);
    XtVaSetValues(view->preview_widgets[11], XmNwidth, geometry->bar_px,
                 XmNshadowThickness, geometry->shadow_px, NULL);
    XtVaSetValues(view->preview_widgets[8], XmNscaleHeight, geometry->bar_px,
                 XmNshadowThickness, geometry->shadow_px, NULL);
    XtVaSetValues(view->preview_widgets[9], XmNscaleWidth, geometry->bar_px,
                 XmNshadowThickness, geometry->shadow_px, NULL);
    for (i = 0; i < PREVIEW_COUNT; ++i) {
        Widget widget = view->preview_widgets[i];
        if (widget != NULL && (XmIsLabel(widget) || XmIsTextField(widget) || XmIsText(widget)))
            XtVaSetValues(widget, XmNmarginWidth, geometry->control_padding_px,
                          XmNmarginHeight, geometry->control_padding_px,
                          XmNshadowThickness, geometry->shadow_px, NULL);
    }
    preview_font_apply(view, geometry->font_px);
}

static void preview_selection(TLView *view, TLFamily family, const TLRecipe *recipe)
{
    int i, anchor_invalid = 0;
    Dimension width = 740, height = 410;
    control_sizes(view->preview_widgets, recipe, view->preview_sizes, view->preview_base_sizes);
    for (i = 0; i < TL_CONTROL_COUNT; ++i) {
        Widget widget = view->preview_widgets[i];
        Dimension widget_width, widget_height;
        int origin[2];
        int visible = (recipe->visible_controls & (1 << i)) &&
                      (recipe->visible_categories & (1 << control_category[i]));
        XtVaSetValues(widget, XmNsensitive, i != 13 && !(i == recipe->selected_control && recipe->edit_state == 2), NULL);
        if (visible) XtManageChild(widget); else XtUnmanageChild(widget);
        if (control_place(widget, recipe, i, &widget_width, &widget_height, origin)) {
            anchor_invalid = 1; continue;
        }
        if ((unsigned int)origin[0] + widget_width + 12 > width)
            width = (Dimension)(origin[0] + widget_width + 12);
        if ((unsigned int)origin[1] + widget_height + 12 > height)
            height = (Dimension)(origin[1] + widget_height + 12);
    }
    XtVaSetValues(view->preview_form, XmNwidth, width, XmNheight, height, NULL);
    XtVaSetValues(view->canvas, XmNwidth, width, XmNheight, height, NULL);
    /* DrawingArea considers navigable children even when they are unmanaged.
     * Leave its native Motif form outside the traversal graph while a foreign
     * XEmbed child owns the canvas, so the canvas can receive virtual focus. */
    XtVaSetValues(view->preview_form, XmNtraversalOn, family == TL_MOTIF, NULL);
    if (family == TL_MOTIF) {
        XtManageChild(view->preview_form); XtUnmanageChild(view->canvas_notice);
        label_set(view->preview_notice,
          "Motif instalado: posição e máscara reais.\nPressionado/backdrop: interação nativa; nível usa Scale.");
        if (anchor_invalid)
            label_set(view->preview_notice,
                      "Motif: âncora fora do canvas; controle não exibido.\nCorrija a posição ou comprimento; receita preservada.");
    } else {
        XtUnmanageChild(view->preview_form); XtManageChild(view->canvas_notice);
        label_set(view->preview_notice,
          "Prévia nativa da família pelo controller.\nO canvas está disponível para embedding; não é uma simulação Motif.");
        embed_notice(view);
    }
}

static unsigned long masked_channel(unsigned char value, unsigned long mask)
{
    unsigned int shift = 0;
    unsigned long maximum;
    if (mask == 0)
        return 0;
    while (((mask >> shift) & 1UL) == 0)
        ++shift;
    maximum = mask >> shift;
    return ((((unsigned long)value * maximum + 127UL) / 255UL) << shift) & mask;
}

static void reference_expose(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view = (TLView *)client;
    XmDrawingAreaCallbackStruct *event = (XmDrawingAreaCallbackStruct *)call;
    int x = 0, y = 0;
    unsigned int width = view->reference_width, height = view->reference_height;
    if (view->reference_image == NULL || !XtIsRealized(widget))
        return;
    if (event != NULL && event->event != NULL && event->event->type == Expose) {
        XExposeEvent *expose = &event->event->xexpose;
        x = expose->x; y = expose->y;
        width = (unsigned int)expose->width; height = (unsigned int)expose->height;
        if ((unsigned int)x >= view->reference_width || (unsigned int)y >= view->reference_height)
            return;
        if (width > view->reference_width - (unsigned int)x)
            width = view->reference_width - (unsigned int)x;
        if (height > view->reference_height - (unsigned int)y)
            height = view->reference_height - (unsigned int)y;
    }
    if (view->reference_gc == NULL)
        view->reference_gc = XCreateGC(XtDisplay(widget), XtWindow(widget), 0, NULL);
    XPutImage(XtDisplay(widget), XtWindow(widget), view->reference_gc,
              view->reference_image, x, y, x, y, width, height);
}

TLView *tl_view_create(Widget shell, TLDispatch dispatch, void *context)
{
    static const char *const factor_labels[3] = { "Fator de luz", "Fator de sombra", "Fator de trilho" };
    static const char *const role_labels[4] = { "Papel: face", "Papel: texto", "Papel: conteúdo", "Papel: seleção" };
    static const char *const state_labels[4] = { "Normal", "Pressionado", "Desabilitado", "Sem foco / backdrop" };
    static const char *const action_labels[ACTION_COUNT] = {
        "Atualizar", "Salvar", "Carregar", "Pipeta", "Prévia separada",
        "Exportar", "Imagem histórica", "Restaurar família", "Importar delta", "Reconstruir arquivos", "Pintura manual", "Sair"
    };
    static const TLAction actions[ACTION_COUNT] = {
        TL_APPLY, TL_SAVE, TL_LOAD, TL_PICK, TL_PREVIEW,
        TL_EXPORT, TL_REFERENCE, TL_RESET, TL_IMPORT_DELTA, TL_RECONSTRUCT_FILES, TL_MANUAL_PAINT, TL_QUIT
    };
    static const char *const initial_schemes[] = { "Esquema KDE atual" };
    static const char *const page_labels[TL_PAGE_COUNT] = {
        "Catálogo", "Controle e medições", "Peça e geometria",
        "Cores e relevo", "Modelo e referências", "Código da proposta"
    };
    TLView *view = (TLView *)calloc(1, sizeof(*view));
    Widget body, editor_scroll, editor, preview_scroll, previews, code_group;
    Widget group, reference_frame, reference_scroll, bottom, action_row;
    Widget native_panel;
    Widget left_panel;
    Atom delete_window;
    int i;
    if (view == NULL) return NULL;
    view->shell = shell; view->dispatch = dispatch; view->context = context;
    view->preview_font_px = view->reference_font_px = -1;
    view->scheme_count = 1; view->pending_control = -1;
    view->preview_trough = .15;
    view->reference_trough = .15;
    XtVaSetValues(shell, XtNwidth, 1280, XtNheight, 800, XtNminWidth, 940,
                   XtNminHeight, 560, XmNdeleteResponse, XmDO_NOTHING, NULL);
    view->root = XtVaCreateManagedWidget("themeLabView", xmFormWidgetClass, shell,
                    XmNfractionBase, 100, XmNmarginWidth, 0, XmNmarginHeight, 0, NULL);
    view->help=tl_help_create(view->root,shell);
    if(!view->help){XtDestroyWidget(view->root);free(view);return NULL;}
    view->export_review=tl_export_review_create(shell);
    if(!view->export_review){tl_help_destroy(view->help);XtDestroyWidget(view->root);free(view);return NULL;}
    view->menu_bar=tl_help_menu(view->help);
    XtVaSetValues(view->menu_bar,XmNtopAttachment,XmATTACH_FORM,
        XmNleftAttachment,XmATTACH_FORM,XmNrightAttachment,XmATTACH_FORM,NULL);
    XtManageChild(view->menu_bar);
    view->workspace = XtVaCreateManagedWidget("themeLabWorkspace", xmFormWidgetClass,
           view->root, XmNfractionBase, 100, XmNmarginWidth, 7, XmNmarginHeight, 7,
           XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM,
           XmNtopAttachment, XmATTACH_WIDGET, XmNtopWidget, view->menu_bar,
           XmNbottomAttachment, XmATTACH_FORM, NULL);
    for (i = 0; i < ACTION_COUNT; ++i) {
        view->bindings[i].view = view;
        view->bindings[i].action = actions[i];
    }
    menus_create(view);
    view->context_bar = XtVaCreateManagedWidget(
           "themeLabContextBar", xmRowColumnWidgetClass, view->workspace,
           XmNorientation, XmHORIZONTAL, XmNpacking, XmPACK_TIGHT,
           XmNspacing, 8, XmNleftAttachment, XmATTACH_FORM,
           XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_FORM,
           NULL);
    (void)label_new(view->context_bar, "familyHeading", "Família");
    view->family_combo = combo_new(view->context_bar, "familyCombo",
                                   tl_family_labels, TL_FAMILY_COUNT);
    XtAddCallback(view->family_combo, XmNselectionCallback, family_callback, view);
    (void)label_new(view->context_bar, "schemeHeading", "Esquema da prévia");
    view->scheme_combo = combo_new(view->context_bar, "schemeCombo",
                                   initial_schemes, 1);
    XtAddCallback(view->scheme_combo, XmNselectionCallback, changed_callback, view);
    view->automatic = XtVaCreateManagedWidget(
           "automaticPreview", xmToggleButtonWidgetClass, view->context_bar, NULL);
    label_set(view->automatic, "Atualização automática");
    XtAddCallback(view->automatic, XmNvalueChangedCallback, changed_callback, view);
    number_row(view, view->context_bar, "delayRow", "Intervalo (ms)", 7,
               &view->delay, 100, 10000, 100, 0);
    XtAddCallback(view->delay, XmNvalueChangedCallback, changed_callback, view);
    bottom = XtVaCreateManagedWidget("viewFooter", xmRowColumnWidgetClass, view->workspace,
           XmNorientation, XmVERTICAL, XmNpacking, XmPACK_TIGHT, XmNspacing, 3,
           XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM,
           XmNbottomAttachment, XmATTACH_FORM, NULL);
    action_row = XtVaCreateManagedWidget("controllerActions", xmRowColumnWidgetClass,
           bottom, XmNorientation, XmHORIZONTAL, XmNpacking, XmPACK_COLUMN,
           XmNnumColumns, 2, XmNspacing, 5, NULL);
    for (i = 0; i < ACTION_COUNT; ++i) {
        Widget button = XtVaCreateManagedWidget("controllerAction", xmPushButtonWidgetClass,
              action_row, NULL);
        label_set(button, action_labels[i]);
        tl_ui_hint(button, tl_ui_action_hint(i));
        XtAddCallback(button, XmNactivateCallback, action_callback, &view->bindings[i]);
    }
    view->history_controls=tl_history_controls_create(bottom,dispatch,context);
    /* Menus are the public action surface in the redesigned layout.  Keep the
     * established button widgets alive, but hidden, so project shortcuts,
     * state propagation and older automation names remain compatible. */
    XtUnmanageChild(action_row);
    XtUnmanageChild(view->history_controls);
    view->status = label_new(bottom, "controllerStatus", "Pronto. Edição privada de receitas.");
    XtVaSetValues(view->status, XmNrecomputeSize, False, XmNwidth, 1200, NULL);
    body = XtVaCreateManagedWidget("threePanels", xmFormWidgetClass, view->workspace,
          XmNfractionBase, 100, XmNleftAttachment, XmATTACH_FORM,
          XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_WIDGET,
          XmNtopWidget, view->context_bar, XmNtopOffset, 6,
          XmNbottomAttachment, XmATTACH_WIDGET, XmNbottomWidget, bottom, XmNbottomOffset, 6, NULL);
    left_panel = XtVaCreateManagedWidget(
          "leftToolPanel", xmFormWidgetClass, body, XmNfractionBase, 100,
          XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_POSITION,
          XmNrightPosition, 29, XmNtopAttachment, XmATTACH_FORM,
          XmNbottomAttachment, XmATTACH_FORM, NULL);
    view->page_selector = combo_new(left_panel, "leftPanelSelector",
                                    page_labels, TL_PAGE_COUNT);
    XtVaSetValues(view->page_selector, XmNleftAttachment, XmATTACH_FORM,
                  XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment,
                  XmATTACH_FORM, NULL);
    XtAddCallback(view->page_selector, XmNselectionCallback,
                  page_combo_callback, view);
    tl_ui_hint(view->page_selector,
               "Escolhe o grupo mostrado à esquerda. Trocar de página preserva "
               "campos, seleções e histórico e não aplica a receita.");
    editor_scroll = XtVaCreateManagedWidget("recipeScroll", xmScrolledWindowWidgetClass, left_panel,
          XmNscrollingPolicy, XmAUTOMATIC, XmNscrollBarDisplayPolicy, XmAS_NEEDED,
          XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM,
          XmNtopAttachment, XmATTACH_WIDGET, XmNtopWidget, view->page_selector,
          XmNtopOffset, 5,
          XmNbottomAttachment, XmATTACH_FORM, NULL);
    editor = XtVaCreateManagedWidget("recipeEditor", xmRowColumnWidgetClass, editor_scroll,
          XmNorientation, XmVERTICAL, XmNpacking, XmPACK_TIGHT,
          XmNspacing, 6, XmNmarginWidth, 4, XmNmarginHeight, 4, XmNwidth, 380, NULL);
    view->page_host = editor;
    for (i = 0; i < TL_PAGE_COUNT; ++i) {
        view->pages[i] = XtVaCreateManagedWidget(
            "leftPanelPage", xmRowColumnWidgetClass, editor,
            XmNorientation, XmVERTICAL, XmNpacking, XmPACK_TIGHT,
            XmNspacing, 6, XmNmarginWidth, 1, XmNmarginHeight, 1,
            XmNwidth, 370, NULL);
        if (i != TL_PAGE_CATALOG)
            XtUnmanageChild(view->pages[i]);
    }
    view->selected_page = TL_PAGE_CATALOG;
    group = section(view->pages[TL_PAGE_CATALOG], "catalogSection", "Catálogo de controles");
    view->catalog=tl_catalog_create(group,category_labels,control_labels,control_category,catalog_changed,view);
    group = section(view->pages[TL_PAGE_CONTROL], "controlEdit",
                    "Controle selecionado / posição no canvas");
    view->control_label = label_new(group, "selectedControl", "Controle em edição: botão");
    (void)label_new(group, "stateHeading", "Estado em edição");
    view->edit_state = combo_new(group, "editState", state_labels, 4);
    XtAddCallback(view->edit_state, XmNselectionCallback, changed_callback, view);
    const char *anchor_labels[]={"Início fixo", "Fim fixo"};
    (void)label_new(group,"anchorHeading","Extremidade fixa da barra");
    view->anchor_combo=combo_new(group,"lengthAnchor",anchor_labels,2);
    XtAddCallback(view->anchor_combo,XmNselectionCallback,selected_anchor_callback,view);
    tl_ui_hint(view->anchor_combo,"Escolhe qual extremidade permanece fixa ao alterar o comprimento. A troca usa a medida nativa atual e preserva a posição. Disponível para barras Motif, GTK2 e GTK3; se há alterações pendentes, atualize a prévia primeiro.");
    number_row(view, group, "positionX", "Posição X (px)", 6, &view->position[0], 0, 2048, 1, 0);
    number_row(view, group, "positionY", "Posição Y (px)", 6, &view->position[1], 0, 2048, 1, 0);
    for (i = 0; i < 2; ++i) XtAddCallback(view->position[i], XmNvalueChangedCallback, changed_callback, view);
    number_row(view, group, "controlWidth", "Largura (0 = automática)", 6, &view->size[0], 0, 2048, 1, 0);
    number_row(view, group, "controlHeight", "Altura (0 = automática)", 6, &view->size[1], 0, 2048, 1, 0);
    for (i = 0; i < 2; ++i) XtAddCallback(view->size[i], XmNvalueChangedCallback, changed_callback, view);
    view->metric_summary = label_new(group, "nativeMetrics", "Aguardando medidas nativas.");
    view->capability = label_new(view->pages[TL_PAGE_CONTROL], "familyCapability",
                                 "Aguardando inventário nativo.");
    XtVaSetValues(view->capability, XmNrecomputeSize, False, XmNwidth, 360, XmNheight, 75, NULL);
    (void)field_row(view->pages[TL_PAGE_MODEL], "modelNameRow", "Nome do modelo", 18, &view->name);
    XtVaSetValues(view->name, XmNmaxLength, 255, NULL);
    XtAddCallback(view->name, XmNvalueChangedCallback, changed_callback, view);
    (void)field_row(view->pages[TL_PAGE_MODEL], "referencePathRow", "Referência PNG", 18, &view->reference_path);
    XtVaSetValues(view->reference_path, XmNmaxLength, TL_PATH_MAX - 1, NULL);
    XtAddCallback(view->reference_path, XmNvalueChangedCallback, changed_callback, view);
    view->separate = XtVaCreateManagedWidget(
        "separatePreview", xmToggleButtonWidgetClass,
        view->pages[TL_PAGE_MODEL], NULL);
    label_set(view->separate, "Mostrar prévia separada");
    XtAddCallback(view->separate, XmNvalueChangedCallback, separate_callback, view);
    group = section(view->pages[TL_PAGE_GEOMETRY], "scrollbarParts",
                    "Ajuste independente da peça");
    const char *part_labels[] = {"Seta", "Botão da seta", "Trilho", "Cursor", "Encaixe"};
    view->part_combo=combo_new(group,"scrollPartCombo",part_labels,TL_SCROLL_PART_COUNT);
    XtAddCallback(view->part_combo,XmNselectionCallback,selected_part_callback,view);
    number_row(view,group,"partGlyph","Triângulo (-1 = herdar)",6,&view->part_fields[0],-1,127,2,0);
    number_row(view,group,"partShadow","Relevo (-1 = herdar)",6,&view->part_fields[1],-1,63,1,0);
    number_row(view,group,"partGap","Distância das setas (-1 = herdar)",6,&view->part_fields[2],-1,128,1,0);
    for(i=0;i<TL_SCROLL_PARAM_COUNT;i++)XtAddCallback(view->part_fields[i],XmNvalueChangedCallback,changed_callback,view);
    for(i=0;i<TL_SCROLL_PARAM_COUNT;i++)view->part_captions[i]=XtNameToWidget(XtParent(XtParent(view->part_fields[i])),"fieldLabel");
    view->part_relief_editor=tl_part_editor_create(group,part_relief_callback,part_state_callback,view);
    view->part_notice=label_new(group,"partCapability","Seta GTK3: mantém o espaço reservado; outras peças pendentes.");
    label_wrapped(view->part_notice,"Seta GTK3: mantém o espaço reservado. -1 herda da família. Outras peças pendentes.",48);
    const char *part_hints[]={"Escolha a peça; editar a seta não altera o botão, trilho, cursor ou encaixe.",
       "Tamanho ímpar do triângulo em pixels, de 3 até o espaço reservado. -1 herda da geometria. Atualizar aplica à prévia.",
       "Espessura do relevo da seta em pixels; menor que metade do triângulo. -1 herda. Cores vêm do esquema KDE."};
    Widget part_widgets[]={view->part_combo,view->part_fields[0],view->part_fields[1]};
    for(i=0;i<3;i++) {
        tl_ui_hint(part_widgets[i],part_hints[i]);
    }
    group = section(view->pages[TL_PAGE_GEOMETRY], "geometryFields",
                    "Geometria compartilhada — pixels");
    for (i = 0; i < TL_FIELD_COUNT; ++i) {
        number_row(view, group, tl_field_ids[i], tl_field_labels[i], 6, &view->fields[i],
                   i == 8 ? 6 : 0, i == 8 ? 48 : (i == 0 ? 127 : 128),
                   i == 0 || i == 2 || i == 3 ? 2 : 1, 0);
        XtAddCallback(view->fields[i], XmNvalueChangedCallback, changed_callback, view);
    }
    view->scale_geometry = section(view->pages[TL_PAGE_GEOMETRY],
                                   "gtk2ScaleGeometry",
                                   "GTK2 — cursor da escala (px)");
    number_row(view, view->scale_geometry, "gtk2ScaleWidth", "Largura transversal", 6,
               &view->scale_fields[0], 1, 128, 1, 0);
    number_row(view, view->scale_geometry, "gtk2ScaleLength", "Comprimento", 6,
               &view->scale_fields[1], 1, 128, 1, 0);
    for (i = 0; i < 2; ++i)
        XtAddCallback(view->scale_fields[i], XmNvalueChangedCallback, changed_callback, view);
    group = section(view->pages[TL_PAGE_COLORS], "paletteFields",
                    "Papéis e fatores KDE — controle em edição");
    for (i = 0; i < 3; ++i) {
        number_row(view, group, "factorRow", factor_labels[i], 8, &view->factors[i], 0, 10000, 100, 4);
        XtAddCallback(view->factors[i], XmNvalueChangedCallback, changed_callback, view);
    }
    for (i = 0; i < 4; ++i) {
        (void)field_row(group, "roleRow", role_labels[i], 16, &view->roles[i]);
        XtAddCallback(view->roles[i], XmNvalueChangedCallback, changed_callback, view);
    }
    view->palette_scope=label_new(group,"paletteScope","Controle selecionado: herda papéis/fatores da família.");
    group = section(view->pages[TL_PAGE_MODEL], "recipeNotes",
                    "Notas / limites da adaptação");
    view->notes = XtVaCreateManagedWidget("notesText", xmTextWidgetClass, group,
         XmNeditMode, XmMULTI_LINE_EDIT, XmNrows, 4, XmNcolumns, 28,
         XmNwordWrap, True, XmNmaxLength, 2047, NULL);
    XtAddCallback(view->notes, XmNvalueChangedCallback, changed_callback, view);
    view->pick_summary = label_new(view->pages[TL_PAGE_MODEL], "pickSummary",
                                   "Pipeta: sem amostra.");
    XtVaSetValues(view->pick_summary, XmNrecomputeSize, False, XmNwidth, 360, XmNheight, 110, NULL);
    preview_scroll = XtVaCreateManagedWidget("previewScroll", xmScrolledWindowWidgetClass, body,
          XmNscrollingPolicy, XmAUTOMATIC, XmNscrollBarDisplayPolicy, XmAS_NEEDED,
          XmNleftAttachment, XmATTACH_POSITION, XmNleftPosition, 29, XmNleftOffset, 6,
          XmNrightAttachment, XmATTACH_FORM,
          XmNtopAttachment, XmATTACH_FORM, XmNbottomAttachment, XmATTACH_FORM, NULL);
    view->preview_stack_scroll = preview_scroll;
    previews = XtVaCreateManagedWidget(
          "previewStack", xmFormWidgetClass, preview_scroll,
          XmNfractionBase, 100, XmNwidth, 1044, XmNheight, 500,
          XmNresizePolicy, XmRESIZE_GROW,
          XmNmarginWidth, 4, XmNmarginHeight, 4, NULL);
    view->preview_stack = previews;
    reference_frame = XtVaCreateManagedWidget("motifReferenceFrame", xmFrameWidgetClass, previews,
          XmNshadowType, XmSHADOW_IN, XmNshadowThickness, 2,
          XmNleftAttachment, XmATTACH_FORM,
          XmNrightAttachment, XmATTACH_POSITION, XmNrightPosition, 50,
          XmNrightOffset, 4, XmNtopAttachment, XmATTACH_FORM,
          XmNbottomAttachment, XmATTACH_FORM, NULL);
    view->motif_reference_frame = reference_frame;
    group = XtVaCreateManagedWidget("referenceGroup", xmRowColumnWidgetClass, reference_frame,
          XmNorientation, XmVERTICAL, XmNpacking, XmPACK_TIGHT, NULL);
    view->motif_reference_notice = label_new(group, "motifReferenceNotice",
          "Referência Motif — controles reais da biblioteca instalada.");
    XtVaSetValues(view->motif_reference_notice, XmNrecomputeSize, False,
                  XmNwidth, 500, XmNheight, 40, NULL);
    reference_scroll = XtVaCreateManagedWidget("motifReferenceScroll", xmScrolledWindowWidgetClass, group,
          XmNscrollingPolicy, XmAUTOMATIC, XmNscrollBarDisplayPolicy, XmAS_NEEDED,
          XmNwidth, 510, XmNheight, 370, NULL);
    view->motif_reference_scroll = reference_scroll;
    view->motif_reference_form = XtVaCreateManagedWidget("motifReferenceControls", xmFormWidgetClass,
          reference_scroll, XmNwidth, 740, XmNheight, 410, XmNresizePolicy, XmRESIZE_NONE, NULL);
    motif_controls_create(view->motif_reference_form, view->motif_reference_widgets);
    for (i = 0; i < TL_CONTROL_COUNT; ++i)
        XtAddEventHandler(view->motif_reference_widgets[i], StructureNotifyMask, False,
                          metrics_geometry_event, view);
    preview_create(view, previews);
    native_panel = XtNameToWidget(previews, "*nativePreview");
    if (native_panel)
        XtVaSetValues(native_panel,
                      XmNleftAttachment, XmATTACH_POSITION, XmNleftPosition, 50,
                      XmNleftOffset, 4, XmNrightAttachment, XmATTACH_FORM,
                      XmNtopAttachment, XmATTACH_FORM,
                      XmNbottomAttachment, XmATTACH_FORM, NULL);
    XtAddEventHandler(preview_scroll, StructureNotifyMask, False,
                      preview_stack_resize_event, view);
    /* The historical image remains a separate modeless window. Loading the
     * project does not map it or replace the live Motif comparison. */
    view->reference_dialog = XmCreateFormDialog(shell, "historicalReference", NULL, 0);
    XtVaSetValues(view->reference_dialog, XmNdialogStyle, XmDIALOG_MODELESS,
                  XmNautoUnmanage, False, XmNwidth, 680, XmNheight, 460, NULL);
    XtVaSetValues(XtParent(view->reference_dialog), XmNdeleteResponse, XmUNMAP,
                  XtNtitle, "Imagem histórica — referência em escala 1:1", NULL);
    view->reference_notice = label_new(view->reference_dialog, "imageReferenceNotice",
          "Imagem histórica PNG — escala 1:1.");
    XtVaSetValues(view->reference_notice, XmNleftAttachment, XmATTACH_FORM,
                  XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_FORM, NULL);
    reference_scroll = XtVaCreateManagedWidget("imageReferenceScroll", xmScrolledWindowWidgetClass,
          view->reference_dialog, XmNscrollingPolicy, XmAUTOMATIC,
          XmNscrollBarDisplayPolicy, XmAS_NEEDED,
          XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM,
          XmNtopAttachment, XmATTACH_WIDGET, XmNtopWidget, view->reference_notice,
          XmNbottomAttachment, XmATTACH_FORM, NULL);
    view->reference_area = XtVaCreateManagedWidget("referencePixels", xmDrawingAreaWidgetClass,
          reference_scroll, XmNwidth, 480, XmNheight, 210,
          XmNresizePolicy, XmRESIZE_NONE, XmNmarginWidth, 0, XmNmarginHeight, 0, NULL);
    XtAddCallback(view->reference_area, XmNexposeCallback, reference_expose, view);
    code_group = XtVaCreateManagedWidget(
          "codePanel", xmFormWidgetClass, view->pages[TL_PAGE_CODE],
          XmNwidth, 360, XmNheight, 620, XmNresizePolicy, XmRESIZE_GROW, NULL);
    group = label_new(code_group, "codeHeading", "Código da proposta — somente leitura");
    XtVaSetValues(group, XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM,
                  XmNtopAttachment, XmATTACH_FORM, NULL);
    Widget search_form = XtVaCreateManagedWidget("codeSearchControls", xmFormWidgetClass,
          code_group, XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM,
          XmNtopAttachment, XmATTACH_WIDGET, XmNtopWidget, group, XmNtopOffset, 3,
          XmNheight, 78, XmNresizePolicy, XmRESIZE_NONE, NULL);
    view->code_search = XtVaCreateManagedWidget("codeSearch", xmTextFieldWidgetClass,
          search_form, XmNleftAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_FORM,
          XmNwidth, 118, XmNmaxLength, (short)(sizeof(view->code_search_last)-1), NULL);
    view->code_search_previous = XtVaCreateManagedWidget("findPrevious", xmPushButtonWidgetClass,
          search_form, XmNleftAttachment, XmATTACH_WIDGET, XmNleftWidget, view->code_search,
          XmNtopAttachment, XmATTACH_FORM, NULL);
    label_set(view->code_search_previous, "Anterior");
    view->code_search_next = XtVaCreateManagedWidget("findNext", xmPushButtonWidgetClass,
          search_form, XmNleftAttachment, XmATTACH_WIDGET, XmNleftWidget, view->code_search_previous,
          XmNtopAttachment, XmATTACH_FORM, NULL);
    label_set(view->code_search_next, "Próximo");
    view->code_search_case = XtVaCreateManagedWidget("matchCase", xmToggleButtonWidgetClass,
          search_form, XmNleftAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_WIDGET,
          XmNtopWidget, view->code_search, XmNset, False, NULL);
    label_set(view->code_search_case, "Aa");
    view->code_search_word = XtVaCreateManagedWidget("wholeWord", xmToggleButtonWidgetClass,
          search_form, XmNleftAttachment, XmATTACH_WIDGET, XmNleftWidget, view->code_search_case,
          XmNtopAttachment, XmATTACH_WIDGET, XmNtopWidget, view->code_search, NULL);
    label_set(view->code_search_word, "Palavra inteira");
    view->code_search_status = label_new(search_form, "searchResult", "Digite um termo para localizar.");
    XtVaSetValues(view->code_search_status, XmNleftAttachment, XmATTACH_FORM,
          XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_WIDGET,
          XmNtopWidget, view->code_search_case, NULL);
    XtAddCallback(view->code_search, XmNactivateCallback, code_search_activate_callback, view);
    XtAddCallback(view->code_search, XmNvalueChangedCallback, code_search_changed, view);
    XtAddCallback(view->code_search_previous, XmNactivateCallback, code_search_previous_callback, view);
    XtAddCallback(view->code_search_next, XmNactivateCallback, code_search_next_callback, view);
    view->code = XmCreateScrolledText(code_group, "proposalCode", NULL, 0);
    XtVaSetValues(view->code, XmNeditMode, XmMULTI_LINE_EDIT, XmNeditable, False,
                  XmNcursorPositionVisible, False, XmNwordWrap, False,
                  XmNscrollHorizontal, True, XmNscrollVertical, True, NULL);
    XtVaSetValues(XtParent(view->code), XmNleftAttachment, XmATTACH_FORM,
                  XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_WIDGET,
                  XmNtopWidget, search_form, XmNtopOffset, 4, XmNbottomAttachment, XmATTACH_FORM, NULL);
    XtManageChild(view->code);
    XmTextSetString(view->code, "/* O controller mostra aqui a proposta vigente. */");
    tl_history_controls_watch(view->root,view->history_controls);
    remember_native_font(view);
    delete_window = XmInternAtom(XtDisplay(shell), "WM_DELETE_WINDOW", False);
    view->bindings[ACTION_COUNT].view = view; view->bindings[ACTION_COUNT].action = TL_QUIT;
    XmAddWMProtocolCallback(shell, delete_window, action_callback, &view->bindings[ACTION_COUNT]);
    view->editors=tl_editor_store_new();
    if(!view->editors)abort();
    tl_editor_watch_tree(view->editors,view->root,"ui");
    tl_editor_watch_tree(view->editors,tl_help_dialog(view->help),"help");
    tl_editor_watch_tree(view->editors,tl_export_review_dialog(view->export_review),"export-review");
    tl_ui_hints_shell(shell);
    Widget hint_label=XmToolTipGetLabel(shell);
    if(hint_label)font_widget(hint_label,view->native_font);
    tl_ui_hint(view->family_combo,"Escolhe o toolkit da receita e da prévia nativa. Disponibilidade e controles ainda sem tradução aparecem no estado de suporte.");
    tl_ui_hint(view->scheme_combo,"Escolhe os papéis KDE usados somente nos controles em teste. Não altera o esquema do desktop nem a paleta nativa da VM.");
    tl_ui_hint(view->automatic,"Atualiza a prévia após o intervalo em ms para reunir alterações. Desmarcado: use Atualizar; o intervalo não atrasa a ação real do controle.");
    tl_ui_hint(view->separate,"Salva no projeto a escolha de mostrar a prévia separada. Usa a cena aplicada, sem aplicar ajustes pendentes. Fechar a janela mantém a escolha; desligue esta opção para removê-la. Disponibilidade depende da família.");
    tl_ui_numeric_hint(view->delay,"Espera em milissegundos antes da atualização automática. Cada edição reinicia a espera; não representa duração de uma operação.");
    tl_ui_hint(view->edit_state,"Escolhe o estado da receita em edição. O suporte do toolkit pode exigir interação nativa; selecionar Pressionado não comprova nem força esse estado.");
    tl_ui_numeric_hint(view->position[0],"Posição horizontal em px, relativa ao canvas. Não é coordenada global da tela; use Atualizar para aplicar à prévia.");
    tl_ui_numeric_hint(view->position[1],"Posição vertical em px, relativa ao canvas. Não é coordenada global da tela; use Atualizar para aplicar à prévia.");
    tl_ui_hint(view->name,"Nome do projeto salvo. Não renomeia o tema instalado nem altera a identidade da referência histórica.");
    tl_ui_hint(view->reference_path,"Caminho da imagem PNG de referência. A imagem é evidência separada das medidas nativas e das receitas por toolkit.");
    for (i=0;i<TL_FIELD_COUNT;++i) tl_ui_numeric_hint(view->fields[i],tl_ui_geometry_hint(i));
    tl_ui_numeric_hint(view->scale_fields[0],
        "Largura transversal do cursor GtkScale GTK2, em pixels. Receita independente da barra de rolagem e das medidas Motif; 1–128 px.");
    tl_ui_numeric_hint(view->scale_fields[1],
        "Comprimento do cursor GtkScale GTK2, em pixels. Afeta somente as escalas horizontal e vertical; não representa o comprimento calculado de um thumb de rolagem. 1–128 px.");
    static const char *const factor_hints[]={
        "Fator de luz, sem unidade, somente para o controle selecionado. Deriva o realce do esquema KDE; não define RGB final.",
        "Fator de sombra, sem unidade, somente para o controle selecionado. Deriva a sombra do esquema KDE; relevo é separado.",
        "Fator de trilho, sem unidade, somente para o controle selecionado. Deriva o fundo do esquema KDE; não altera dimensões."
    };
    static const char *const role_hints[]={
        "Papel KDE da face do controle selecionado, no formato Grupo/Chave. A tradução resolve a cor no esquema atual.",
        "Papel KDE do texto do controle selecionado, no formato Grupo/Chave. Combine a face e confira contraste.",
        "Papel KDE da área de conteúdo do controle selecionado, no formato Grupo/Chave. Não é RGB fixo.",
        "Papel KDE da seleção do controle selecionado, no formato Grupo/Chave. Texto usa o papel correspondente."
    };
    for(i=0;i<3;++i)tl_ui_numeric_hint(view->factors[i],factor_hints[i]);
    for(i=0;i<4;++i)tl_ui_hint(view->roles[i],role_hints[i]);
    tl_ui_hint(view->palette_scope,"Escopo dos papéis/fatores: somente o controle em edição. Sem sobrescrita própria, herda a receita da família.");
    tl_ui_hint(view->notes,"Notas e limites da receita desta família. Salvar preserva o texto no projeto; uma nota não comprova implementação do adaptador.");
    tl_ui_hint(view->code,"Trecho da proposta do controle selecionado, somente leitura. Proposta gerada não significa prévia aplicada ou tema instalado; selecione texto para copiar.");
    tl_ui_hint(view->code_search,"Termo UTF-8 procurado somente no trecho da proposta. Enter busca a próxima ocorrência; o texto tem histórico, Undo/Redo, copiar, colar, recortar e menu de edição.");
    tl_ui_hint(view->code_search_previous,"Localiza a ocorrência anterior no trecho da proposta, sem alterar a receita.");
    tl_ui_hint(view->code_search_next,"Localiza a próxima ocorrência no trecho da proposta, sem alterar a receita.");
    tl_ui_hint(view->code_search_case,"Quando ativo, diferencia letras maiúsculas e minúsculas. Desativado, usa comparação Unicode sem distinção de caixa.");
    tl_ui_hint(view->code_search_word,"Quando ativo, exige limites de palavra ao redor do termo localizado.");
    tl_ui_hint(view->code_search_status,"Resultado da última busca. Posições começam em 1; busca vazia ou sem ocorrência não altera o código.");
    tl_ui_scroll_hints(view->root);
    tl_ui_scroll_hints(view->reference_dialog);
    return view;
}

static void metrics_refresh(TLView *view)
{
    TLNativeMetrics motif = {0};
    char native[768], coupled[768], separate[768], summary[3000], delta[192];
    const TLRecipe *recipe;
    Widget widget;
    Dimension width, height;
    XtWidgetGeometry preferred;
    int control;
    if (!view->has_model || !view->metric_summary) return;
    recipe = &view->snapshot.recipes[view->snapshot.selected];
    control = recipe->selected_control;
    int paired=0;
    if (view->reference_ready)
        paired=tl_motif_pair_bars(view->motif_reference_widgets,&view->reference_recipe,
              view->preview_family==TL_GTK3?control:-1,view->gtk_metrics[0]);
    widget = view->motif_reference_widgets[control];
    if (widget && XtIsRealized(widget) && XtIsManaged(widget)) {
        XtVaGetValues(widget, XmNwidth, &width, XmNheight, &height, NULL);
        memset(&preferred, 0, sizeof(preferred));
        (void)XtQueryGeometry(widget, NULL, &preferred);
        motif.width = width; motif.height = height;
        /* Xt core dimensions and form offsets are X11 pixels, not GTK logical units. */
        motif.scale_factor = 1;
        Position x, y;
        XtVaGetValues(widget, XmNx, &x, XmNy, &y, NULL);
        motif.position_x = x; motif.position_y = y; motif.position_valid = 1;
        tl_motif_font_measure(widget, &motif.font);
        tl_motif_parts_measure(widget, &motif.pieces);
        motif.sensitivity_known=1; motif.sensitive=XtIsSensitive(widget)?1:0;
        motif.minimum_width = motif.minimum_height = -1;
        motif.natural_width = (preferred.request_mode & CWWidth) ? preferred.width : width;
        motif.natural_height = (preferred.request_mode & CWHeight) ? preferred.height : height;
    }
    tl_metrics_format(native, sizeof(native), "Motif referência", &motif);
    if (view->snapshot.selected == TL_GTK3 || view->snapshot.selected == TL_GTK2 || view->snapshot.selected == TL_GTK4) {
        const char *family=view->snapshot.selected==TL_GTK2?"GTK2":view->snapshot.selected==TL_GTK4?"GTK4":"GTK3";
        char label[32];
        snprintf(label,sizeof(label),"%s acoplado",family);
        tl_metrics_format(coupled, sizeof(coupled), label, &view->gtk_metrics[0][control]);
        snprintf(label,sizeof(label),"%s separado",family);
        tl_metrics_format(separate, sizeof(separate), label, &view->gtk_metrics[1][control]);
        int dw, dh;
        if (!tl_metrics_size_delta(&motif, &view->gtk_metrics[0][control], &dw, &dh))
            (void)snprintf(delta, sizeof(delta), "%s - Motif: %+d x %+d px físicos (dimensão).", family, dw, dh);
        else (void)snprintf(delta, sizeof(delta), "Comparação física: aguardando medidas/escala.");
    } else if (view->snapshot.selected==TL_QT5 || view->snapshot.selected==TL_QT6 ||
               view->snapshot.selected==TL_KVANTUM || view->snapshot.selected==TL_PLASMA) {
        if (view->embedded_child != None || tl_gtk4_focus_has_child(view->gtk4_focus))
            (void)snprintf(coupled,sizeof(coupled),
                "%s acoplado: renderizador nativo adotado; emissão de métricas detalhadas ainda indisponível.",
                tl_family_labels[view->snapshot.selected]);
        else
            (void)snprintf(coupled,sizeof(coupled),
                "%s acoplado: aguardando um filho nativo verificado neste canvas.",
                tl_family_labels[view->snapshot.selected]);
        separate[0] = 0;
        delta[0] = 0;
    } else {
        (void)snprintf(coupled, sizeof(coupled), "Métricas nativas indisponíveis para esta família.");
        separate[0] = 0;
        delta[0] = 0;
    }
    char *requested_width=XmTextFieldGetString(view->size[0]);
    char *requested_height=XmTextFieldGetString(view->size[1]);
    (void)snprintf(summary, sizeof(summary),
        "Pedido em edição: %s x %s (0 = automático)\n%s\n%s\n%s\n%s\nPareamento da barra: %s\nPosições locais a cada canvas; não globais.\nPressionado/backdrop: sem equivalência Motif comprovada.\nDimensão igual não comprova desenho igual.\nMedidas da amostra; não são defaults da VM.",
        requested_width, requested_height, native, coupled, separate, delta,
        paired==2?"posição física e sensibilidade":paired==1?"posição; sensibilidade não medida":"aguardando barra/posição nativa");
    XtFree(requested_width);XtFree(requested_height);
    label_wrapped(view->metric_summary, summary, 43);
}

static void metrics_geometry_event(Widget widget, XtPointer data, XEvent *event, Boolean *dispatch)
{
    (void)widget; (void)dispatch;
    if (event->type == ConfigureNotify || event->type == MapNotify)
        metrics_refresh((TLView *)data);
}

void tl_view_native_metrics(TLView *view, int control, const TLNativeMetrics *metrics)
{
    if (!view || !metrics || control < 0 || control >= TL_CONTROL_COUNT ||
        metrics->separate < 0 || metrics->separate > 1) return;
    view->gtk_metrics[metrics->separate][control] = *metrics;
    metrics_refresh(view);
}

int tl_view_get_native_metrics(TLView *view,int control,int separate,TLNativeMetrics *metrics)
{
    if(!view || !metrics || control<0 || control>=TL_CONTROL_COUNT || separate<0 || separate>1)return -1;
    *metrics=view->gtk_metrics[separate][control];
    return metrics->width>0 && metrics->height>0?0:-1;
}

int tl_view_set_anchor(TLView *view, TLModel *model, int anchor, char *error, size_t capacity)
{
    if(!view || !model || model->selected<0 || model->selected>=TL_FAMILY_COUNT ||
       (anchor!=0 && anchor!=1)) return -1;
    TLRecipe *recipe=&model->recipes[model->selected];
    int control=recipe->selected_control, axis=tl_control_long_axis(control), extent=0;
    const char *reason="Atualize a prévia e aguarde a medida nativa antes de trocar a extremidade.";
    if(axis<0 || (model->selected!=TL_MOTIF && model->selected!=TL_GTK3 && model->selected!=TL_GTK2)) {
        reason="Este controle ou plataforma não suporta troca de extremidade.";goto unavailable;
    }
    if(anchor==recipe->length_anchor[control]) return 0;
    if(view->preview_family!=model->selected) {
        reason="Atualize a prévia da plataforma selecionada antes de trocar a extremidade.";goto unavailable;
    }
    if(memcmp(recipe->sizes[control],view->preview_recipe.sizes[control],sizeof(int)*2)) {
        reason="Há dimensões pendentes; atualize a prévia antes de trocar a extremidade.";goto unavailable;
    }
    if(memcmp(&recipe->geometry,&view->preview_recipe.geometry,sizeof(TLGeometry)) ||
       memcmp(&recipe->scrollbar_parts,&view->preview_recipe.scrollbar_parts,sizeof(TLScrollbarParts))) {
        reason="Há regras de geometria pendentes; atualize a prévia antes de trocar a extremidade.";goto unavailable;
    }
    if(model->selected==TL_MOTIF) {
        Dimension width,height;
        Widget widget=view->preview_widgets[control];
        if(!XtIsRealized(widget) || !XtIsManaged(widget)) goto unavailable;
        XtVaGetValues(widget,XmNwidth,&width,XmNheight,&height,NULL);
        extent=axis?height:width;
    } else {
        const TLNativeMetrics *metrics=&view->gtk_metrics[0][control];
        if(!metrics->cell_offset_valid || metrics->width<1 || metrics->height<1) {
            reason="A medida nativa da extremidade ainda não chegou; aguarde a atualização da prévia.";goto unavailable;
        }
        extent=axis?metrics->height+metrics->cell_offset_y:metrics->width+metrics->cell_offset_x;
    }
    int origin[2], applied_origin[2];
    if(tl_control_anchor_origin(recipe,control,axis?1:extent,axis?extent:1,origin) ||
       tl_control_anchor_origin(&view->preview_recipe,control,axis?1:extent,
                                axis?extent:1,applied_origin) ||
       memcmp(origin,applied_origin,sizeof(origin))) {
        reason="Há posição pendente ou fora do canvas; atualize ou corrija antes de trocar a extremidade.";goto unavailable;
    }
    if(tl_control_set_anchor(recipe,control,anchor,extent)) {
        snprintf(error,capacity,"Troca recusada: extremidade fora do canvas; receita preservada.");
        return -1;
    }
    return 0;
unavailable:
    snprintf(error,capacity,"%s",reason);
    return -1;
}

void tl_view_metrics_reset(TLView *view)
{
    if (!view) return;
    memset(view->gtk_metrics, 0, sizeof(view->gtk_metrics));
    metrics_refresh(view);
}

void tl_view_metrics_clear_origin(TLView *view,int separate)
{
    if(!view || separate<0 || separate>1)return;
    memset(view->gtk_metrics[separate],0,sizeof(view->gtk_metrics[separate]));
    metrics_refresh(view);
}

void tl_view_update(TLView *view, const TLModel *model)
{
    const TLRecipe *recipe;
    const TLPaletteRules *palette;
    const char *roles[4];
    double factors[3];
    char value[128], pick[768];
    int i;
    if (view == NULL || model == NULL || model->selected < 0 || model->selected >= TL_FAMILY_COUNT)
        return;
    view->updating = 1;
    tl_editor_sync_begin(view->editors);
    view->snapshot = *model; view->has_model = 1;
    recipe = &model->recipes[model->selected];
    palette=recipe->control_palette_custom[recipe->selected_control]?
        &recipe->control_palettes[recipe->selected_control]:&recipe->palette;
    tl_editor_set_text(view->name, model->name);
    tl_editor_set_text(view->reference_path, model->reference);
    XtVaSetValues(view->family_combo, XmNselectedPosition, (int)model->selected, NULL);
    {
        int selected_scheme = 0;
        for (i = 0; i < view->scheme_count; ++i)
            if (!strcmp(view->schemes[i], model->color_scheme)) selected_scheme = i;
        if (model->color_scheme[0] && selected_scheme == 0 && view->scheme_count < SCHEME_LIMIT) {
            XmString item = compound(model->color_scheme);
            selected_scheme = view->scheme_count++;
            (void)snprintf(view->schemes[selected_scheme], sizeof(view->schemes[selected_scheme]), "%s", model->color_scheme);
            XmComboBoxAddItem(view->scheme_combo, item, 0, True);
            XmStringFree(item);
        }
        XtVaSetValues(view->scheme_combo, XmNselectedPosition, selected_scheme, NULL);
    }
    XmToggleButtonSetState(view->automatic, model->automatic_preview != 0, False);
    XmToggleButtonSetState(view->separate, model->separate_preview != 0, False);
    number_set(view->delay, model->debounce_ms);
    tl_catalog_update(view->catalog,recipe->visible_categories,recipe->visible_controls);
    XtVaSetValues(view->edit_state, XmNselectedPosition, recipe->edit_state, NULL);
    XtVaSetValues(view->anchor_combo,XmNselectedPosition,recipe->length_anchor[recipe->selected_control],NULL);
    XtSetSensitive(view->anchor_combo,tl_control_long_axis(recipe->selected_control)>=0 &&
                   (model->selected==TL_MOTIF || model->selected==TL_GTK3 || model->selected==TL_GTK2));
    for (i = 0; i < 2; ++i) {
        number_set(view->position[i], recipe->positions[recipe->selected_control][i]);
        number_set(view->size[i], recipe->sizes[recipe->selected_control][i]);
        int longitudinal=tl_control_long_axis(recipe->selected_control);
        int locked=longitudinal>=0 && i!=longitudinal;
        XtSetSensitive(XtParent(view->size[i]),!locked);
        Widget caption=XtNameToWidget(XtParent(XtParent(view->size[i])),"fieldLabel");
        if(caption) label_set(caption,locked?"Espessura travada (0 = automática)":longitudinal>=0?"Comprimento (0 = automático)":i==0?"Largura (0 = automática)":"Altura (0 = automática)");
        const char *hint=locked?
            "Pedido transversal preservado. Ajuste a espessura na receita do trilho; o comprimento não altera setas ou relevo. O toolkit pode impor um mínimo, mostrado nas medidas.":
            longitudinal>=0?"Comprimento no eixo da barra, em pixels. 0 usa tamanho automático. A espessura e as receitas das outras peças permanecem iguais.":"Dimensão do controle em pixels; 0 delega ao toolkit. Pedido e alocação real aparecem separadamente.";
        tl_ui_numeric_hint(view->size[i],hint);
    }
    (void)snprintf(value, sizeof(value), "Em edição: %s", control_labels[recipe->selected_control]);
    label_set(view->control_label, value);
    metrics_refresh(view);
    for (i = 0; i < TL_FIELD_COUNT; ++i) {
        number_set(view->fields[i], tl_model_geometry_get(&recipe->geometry, i));
    }
    number_set(view->scale_fields[0], recipe->scale_slider_width_px);
    number_set(view->scale_fields[1], recipe->scale_slider_length_px);
    /* Disable the complete GTK2-only frame, including its title, so the UI
     * does not present an active section while another family is selected. */
    XtSetSensitive(XtParent(view->scale_geometry), model->selected == TL_GTK2);
    XtVaSetValues(view->part_combo,XmNselectedPosition,recipe->selected_scroll_part,NULL);
    const TLPartRecipe *part=&recipe->scrollbar_parts.parts[recipe->selected_scroll_part];
    int relief_capability=TL_RELIEF_UNAVAILABLE;
    if(model->selected==TL_GTK3) {
        if(recipe->selected_scroll_part==TL_SCROLL_ARROW)relief_capability=TL_RELIEF_GTK3_STEPPER;
        else if(recipe->selected_scroll_part==TL_SCROLL_ARROW_BUTTON)relief_capability=TL_RELIEF_GTK3_ARROW_BUTTON;
        else if(recipe->selected_scroll_part==TL_SCROLL_TROUGH)relief_capability=TL_RELIEF_GTK3_ENCLOSURE;
        else if(recipe->selected_scroll_part==TL_SCROLL_THUMB)relief_capability=TL_RELIEF_GTK3_THUMB;
        else if(recipe->selected_scroll_part==TL_SCROLL_FITTING)relief_capability=TL_RELIEF_GTK3_FITTING;
    }
    tl_part_editor_update(view->part_relief_editor,part,relief_capability);
    int supported=model->selected==TL_GTK3 && recipe->selected_scroll_part<=TL_SCROLL_FITTING;
    label_set(view->part_captions[0],recipe->selected_scroll_part==TL_SCROLL_FITTING?"Distância conteúdo–barra (-1 = herdar)":recipe->selected_scroll_part==TL_SCROLL_THUMB?"Espessura do cursor (-1 = herdar)":recipe->selected_scroll_part==TL_SCROLL_TROUGH?"Espessura (-1 = herdar)":recipe->selected_scroll_part==TL_SCROLL_ARROW_BUTTON?"Espaço interno (-1 = herdar)":"Triângulo (-1 = herdar)");
    label_set(view->part_captions[1],recipe->selected_scroll_part==TL_SCROLL_FITTING?"Moldura do conteúdo (-1 = herdar)":recipe->selected_scroll_part==TL_SCROLL_ARROW_BUTTON?"Moldura (-1 = herdar)":"Relevo (-1 = herdar)");
    XtVaSetValues(view->part_fields[0],XmNincrementValue,recipe->selected_scroll_part==TL_SCROLL_ARROW?2:1,NULL);
    for(i=0;i<TL_SCROLL_PARAM_COUNT;i++) {
        Widget row=XtParent(XtParent(view->part_fields[i]));
        if(!tl_scroll_part_field((TLScrollPart)recipe->selected_scroll_part,i)) {XtUnmanageChild(row);continue;}
        XtManageChild(row);
        number_set(view->part_fields[i],(part->present & (1U<<i))?part->values[i]:-1);
        XtSetSensitive(XtParent(view->part_fields[i]),supported);
    }
    const char *numeric_hints[3];
    numeric_hints[2]="Distância em pixels entre a região das setas e a faixa de movimento do cursor. -1 herda; não muda o desenho das setas.";
    if(recipe->selected_scroll_part==TL_SCROLL_FITTING) {
        numeric_hints[0]="Distância em pixels entre conteúdo e barra. -1 herda. Não muda a espessura da barra nem as setas.";
        numeric_hints[1]="Relevo rebaixado da moldura GtkViewport em pixels. -1 herda. Não cria moldura em GtkTreeView; cores seguem papéis KDE.";
    } else if(recipe->selected_scroll_part==TL_SCROLL_THUMB) {
        numeric_hints[0]="Espessura transversal do cursor em pixels. Deve caber no trilho com margens inteiras simétricas. -1 herda; comprimento depende do conteúdo.";
        numeric_hints[1]="Relevo elevado do cursor, em pixels, menor que metade de sua espessura. -1 herda. Não altera a moldura do conteúdo nem o trilho.";
    } else if(recipe->selected_scroll_part==TL_SCROLL_TROUGH) {
        numeric_hints[0]="Espessura transversal do trilho em pixels. Deve acomodar seta/cursor; o GTK pode ampliar suas alocações. -1 herda da família.";
        numeric_hints[1]="Relevo rebaixado do trilho em pixels, sem alterar a moldura do conteúdo. -1 herda da família; cores seguem papéis KDE.";
    } else if(recipe->selected_scroll_part==TL_SCROLL_ARROW_BUTTON) {
        numeric_hints[0]="Espaço interno em pixels, somente no botão isolado. Tamanho externo fixo; -1 herda zero. Não altera GtkRange.";
        numeric_hints[1]="Espessura da moldura do botão isolado em pixels, dentro do tamanho fixo. -1 herda da família. Cores seguem o esquema KDE.";
    } else {
        numeric_hints[0]="Triângulo ímpar de 3 até o espaço reservado, em pixels. -1 herda da família; demais peças intactas.";
        numeric_hints[1]="Relevo da seta em pixels, menor que metade do triângulo. -1 herda. Cores seguem o esquema KDE.";
    }
    for(i=0;i<TL_SCROLL_PARAM_COUNT;i++) tl_ui_numeric_hint(view->part_fields[i],numeric_hints[i]);
    label_wrapped(view->part_notice,supported?
        recipe->selected_scroll_part==TL_SCROLL_FITTING?
        "Encaixe GTK3: distância conteúdo–barra e moldura GtkViewport próprias. Outras peças preservadas. GtkTreeView não recebe moldura equivalente. -1 herda.":
        recipe->selected_scroll_part==TL_SCROLL_THUMB?
        "Cursor GTK3: espessura, relevo e distância próprios. Margens simétricas; comprimento calculado pelo conteúdo. -1 herda.":
        recipe->selected_scroll_part==TL_SCROLL_TROUGH?
        "Trilho GTK3: espessura/relevo próprios. Não muda máscaras da seta/cursor ou moldura do conteúdo. Confira alocações efetivas. -1 herda.":
        recipe->selected_scroll_part==TL_SCROLL_ARROW_BUTTON?
        "Botão isolado GTK3: moldura/espaço dentro do tamanho externo fixo. Não altera os nós internos das barras. -1 herda.":
        "Seta GTK3 dentro do espaço reservado. -1 herda. Botão, trilho, cursor e encaixe permanecem iguais.":
        "Edição nativa desta peça/família ainda pendente. Seus dados salvos permanecem preservados.",48);
    factors[0] = palette->light; factors[1] = palette->shade; factors[2] = palette->trough;
    for (i = 0; i < 3; ++i) {
        number_set(view->factors[i], factors[i]);
    }
    roles[0] = palette->face_role; roles[1] = palette->text_role;
    roles[2] = palette->view_role; roles[3] = palette->selection_role;
    for (i = 0; i < 4; ++i)
        tl_editor_set_text(view->roles[i], roles[i]);
    if(view->palette_scope) {
        (void)snprintf(value,sizeof(value),"%s: %s",control_labels[recipe->selected_control],
            recipe->control_palette_custom[recipe->selected_control]?
                "papéis/fatores próprios":"herda papéis/fatores da família");
        label_set(view->palette_scope,value);
    }
    tl_editor_set_text(view->notes, recipe->notes);
    label_wrapped(view->capability, view->capabilities[model->selected][0] != '\0' ?
             view->capabilities[model->selected] : "Sem informação de capacidade.", 48);
    if (model->picked.valid)
        (void)snprintf(pick, sizeof(pick),
             "Pipeta X11 — posição da tela (px): %d, %d\nRGB16 (0–65535): %u / %u / %u\nRGB8 (0–255): %u / %u / %u\nVisual: 0x%lx\nUso: %s\n%s",
             model->picked.x, model->picked.y,
             (unsigned int)model->picked.rgb16[0], (unsigned int)model->picked.rgb16[1],
             (unsigned int)model->picked.rgb16[2],
             (unsigned int)model->picked.rgb8[0], (unsigned int)model->picked.rgb8[1],
             (unsigned int)model->picked.rgb8[2], model->picked.visual_id,
             model->picked.purpose, model->picked.origin);
    else
        (void)snprintf(pick, sizeof(pick), "Pipeta: sem amostra.\nRGB histórico é evidência,\nnão cor fixa do controle.");
    label_wrapped(view->pick_summary, pick, 48);
    palette_apply(view);
    tl_editor_bind(view->editors,view->name,"project/name");
    tl_editor_bind(view->editors,view->reference_path,"project/reference");
    tl_editor_bind(view->editors,view->delay,"project/preview-delay");
    char key[160];
    for(i=0;i<2;++i) {
        snprintf(key,sizeof(key),"recipe/%s/control/%d/position/%d",tl_family_ids[model->selected],recipe->selected_control,i);
        tl_editor_bind(view->editors,view->position[i],key);
        snprintf(key,sizeof(key),"recipe/%s/control/%d/size/%d",tl_family_ids[model->selected],recipe->selected_control,i);
        tl_editor_bind(view->editors,view->size[i],key);
    }
    for(i=0;i<TL_FIELD_COUNT;++i) {
        snprintf(key,sizeof(key),"recipe/%s/geometry/%s",tl_family_ids[model->selected],tl_field_ids[i]);
        tl_editor_bind(view->editors,view->fields[i],key);
    }
    for(i=0;i<TL_SCROLL_PARAM_COUNT && tl_scroll_part_field((TLScrollPart)recipe->selected_scroll_part,i);++i) {
        snprintf(key,sizeof(key),"recipe/%s/piece/%s/%s",tl_family_ids[model->selected],tl_scroll_part_ids[recipe->selected_scroll_part],tl_scroll_part_field((TLScrollPart)recipe->selected_scroll_part,i));
        tl_editor_bind(view->editors,view->part_fields[i],key);
    }
    for(i=0;i<3;++i) {
        snprintf(key,sizeof(key),"recipe/%s/factor/%d",tl_family_ids[model->selected],i);
        tl_editor_bind(view->editors,view->factors[i],key);
    }
    for(i=0;i<4;++i) {
        snprintf(key,sizeof(key),"recipe/%s/role/%d",tl_family_ids[model->selected],i);
        tl_editor_bind(view->editors,view->roles[i],key);
    }
    snprintf(key,sizeof(key),"recipe/%s/notes",tl_family_ids[model->selected]);
    tl_editor_bind(view->editors,view->notes,key);
    tl_editor_bind(view->editors,view->code_search,"ui/code-search");
    tl_editor_sync_end(view->editors);
    metrics_refresh(view);
    view->updating = 0;
    /* The manual editor owns an inspection context independent from the main
     * proposal form.  Synchronizing it from every ordinary model refresh used
     * to reset a GTK/Qt selection to the proposal's family (often Motif) while
     * a private native sample was still being requested.  Its initial context
     * is supplied by tl_view_manual_paint_open(); reopening it explicitly may
     * still choose the current proposal, but unrelated refreshes must not. */
}

void tl_view_scene(TLView *view, const TLModel *model)
{
    const TLRecipe *recipe;
    int previous;
    if (view == NULL || model == NULL || model->selected < 0 || model->selected >= TL_FAMILY_COUNT)
        return;
    /* Only the controller's applied model changes the native scene. Editor
     * updates and selection keep their draft snapshot and field values. */
    previous = view->updating;
    view->updating = 1;
    recipe = &model->recipes[model->selected];
    view->preview_recipe=*recipe;
    view->reference_recipe=model->recipes[TL_MOTIF]; view->reference_ready=1;
    view->preview_family = model->selected;
    tl_gtk4_focus_enabled(view->gtk4_focus,
        model->selected == TL_GTK4 || model->selected == TL_QT5 ||
        model->selected == TL_QT6 || model->selected == TL_KVANTUM ||
        model->selected == TL_PLASMA);
    view->preview_trough = recipe->palette.trough;
    preview_geometry(view, &recipe->geometry);
    preview_selection(view, model->selected, recipe);
    motif_reference_scene(view, model);
    palette_apply(view);
    metrics_refresh(view);
    view->updating = previous;
}

static int text_copy(Widget widget, int multiline, char *target, size_t capacity,
                     char *error, size_t error_capacity)
{
    char *value = multiline ? XmTextGetString(widget) : XmTextFieldGetString(widget);
    size_t length;
    if (value == NULL) {
        set_error(error, error_capacity, "Não foi possível ler o campo.");
        return 0;
    }
    length = strlen(value);
    if (length >= capacity) {
        XtFree(value);
        set_error(error, error_capacity, "Um campo de texto excede o limite da receita.");
        return 0;
    }
    memcpy(target, value, length + 1);
    XtFree(value);
    return 1;
}

static int number_read(Widget widget, int integer, double *result)
{
    char *text = XmTextFieldGetString(widget), *end;
    double value;
    int valid;
    if (text == NULL)
        return 0;
    errno = 0;
    value = integer ? (double)strtol(text, &end, 10) : strtod(text, &end);
    valid = end != text && errno == 0 && isfinite(value);
    while (*end == ' ' || *end == '\t' || *end == '\n' || *end == '\r')
        ++end;
    valid = valid && *end == '\0' && (!integer || (value >= INT_MIN && value <= INT_MAX));
    XtFree(text);
    if (valid)
        *result = value;
    return valid;
}

int tl_view_read(TLView *view, TLModel *candidate, char *error, size_t capacity)
{
    TLModel parsed;
    TLRecipe *recipe;
    TLPaletteRules edited_palette;
    char message[256];
    char *roles[4];
    double factors[3], value;
    int i;
    if (view == NULL || candidate == NULL || !view->has_model) {
        set_error(error, capacity, "A view ainda não recebeu um modelo.");
        return -1;
    }
    parsed = view->snapshot;
    recipe = &parsed.recipes[parsed.selected];
    if (!text_copy(view->name, 0, parsed.name, sizeof(parsed.name), error, capacity) ||
        !text_copy(view->reference_path, 0, parsed.reference, sizeof(parsed.reference), error, capacity))
        return -1;
    parsed.automatic_preview = XmToggleButtonGetState(view->automatic) ? 1 : 0;
    if (!number_read(view->delay, 1, &value) || value < 100 || value > 10000) {
        set_error(error, capacity, "Intervalo de atualização deve ficar entre 100 e 10000 ms.");
        return -1;
    }
    parsed.debounce_ms = (int)value;
    {
        int selected_scheme, state;
        XtVaGetValues(view->scheme_combo, XmNselectedPosition, &selected_scheme, NULL);
        if (selected_scheme < 0 || selected_scheme >= view->scheme_count) {
            set_error(error, capacity, "Escolha um esquema da lista."); return -1;
        }
        (void)snprintf(parsed.color_scheme, sizeof(parsed.color_scheme), "%s", view->schemes[selected_scheme]);
        XtVaGetValues(view->edit_state, XmNselectedPosition, &state, NULL);
        recipe->edit_state = state;
        tl_catalog_read(view->catalog,&recipe->visible_categories,&recipe->visible_controls);
        int requested_size[2];
        for (i = 0; i < 2; ++i) {
            if (!number_read(view->position[i], 1, &value) || value < 0 || value > 2048) {
                set_error(error, capacity, "Posições do canvas devem ficar entre 0 e 2048 px."); return -1;
            }
            recipe->positions[recipe->selected_control][i] = (int)value;
            if (!number_read(view->size[i], 1, &value) || value < 0 || value > 2048) {
                set_error(error, capacity, "Dimensões entre 0 e 2048 px; 0 usa tamanho automático."); return -1;
            }
            requested_size[i] = (int)value;
        }
        if(tl_control_edit_dimensions(recipe,recipe->selected_control,requested_size[0],requested_size[1])) {
            set_error(error,capacity,"Espessura da barra travada: edite somente o comprimento; use a receita do trilho para a espessura.");return -1;
        }
    }
    for (i = 0; i < TL_FIELD_COUNT; ++i) {
        if (!number_read(view->fields[i], 1, &value)) {
            (void)snprintf(message, sizeof(message), "Valor inteiro inválido em %s.", tl_field_labels[i]);
            set_error(error, capacity, message);
            return -1;
        }
        tl_model_geometry_set(&recipe->geometry, i, (int)value);
    }
    if (parsed.selected == TL_GTK2) {
        if (!number_read(view->scale_fields[0], 1, &value) || value < 1 || value > 128) {
            set_error(error, capacity, "Largura transversal da escala GTK2 deve ficar entre 1 e 128 px.");
            return -1;
        }
        recipe->scale_slider_width_px = (int)value;
        if (!number_read(view->scale_fields[1], 1, &value) || value < 1 || value > 128) {
            set_error(error, capacity, "Comprimento da escala GTK2 deve ficar entre 1 e 128 px.");
            return -1;
        }
        recipe->scale_slider_length_px = (int)value;
    }
    if(parsed.selected==TL_GTK3 && recipe->selected_scroll_part<=TL_SCROLL_FITTING) {
        for(i=0;i<TL_SCROLL_PARAM_COUNT && tl_scroll_part_field((TLScrollPart)recipe->selected_scroll_part,i);i++) {
            if(!number_read(view->part_fields[i],1,&value) || value < -1 || value>128 ||
               tl_scroll_parts_set(&recipe->scrollbar_parts,(TLScrollPart)recipe->selected_scroll_part,i,(int)value)) {
                set_error(error,capacity,"Valor da peça inválido; -1 herda da família.");return -1;
            }
        }
    }
    if(tl_part_editor_capture(view->part_relief_editor,&recipe->scrollbar_parts.parts[recipe->selected_scroll_part])) {
        set_error(error,capacity,"Editor de relevo indisponível ou receita inválida; alterações preservadas.");return -1;
    }
    {
        int control=recipe->selected_control;
        edited_palette=recipe->control_palette_custom[control]?
            recipe->control_palettes[control]:recipe->palette;
    }
    for (i = 0; i < 3; ++i)
        if (!number_read(view->factors[i], 0, &factors[i])) {
            set_error(error, capacity, "Fator numérico inválido (luz, sombra ou trilho).");
            return -1;
        }
    edited_palette.light = factors[0]; edited_palette.shade = factors[1]; edited_palette.trough = factors[2];
    roles[0] = edited_palette.face_role; roles[1] = edited_palette.text_role;
    roles[2] = edited_palette.view_role; roles[3] = edited_palette.selection_role;
    for (i = 0; i < 4; ++i)
        if (!text_copy(view->roles[i], 0, roles[i], sizeof(recipe->palette.face_role), error, capacity))
            return -1;
    {
        int control=recipe->selected_control;
        const TLPaletteRules *base=&recipe->palette;
        int same=!strcmp(edited_palette.face_role,base->face_role) &&
            !strcmp(edited_palette.text_role,base->text_role) &&
            !strcmp(edited_palette.view_role,base->view_role) &&
            !strcmp(edited_palette.selection_role,base->selection_role) &&
            edited_palette.light==base->light && edited_palette.shade==base->shade &&
            edited_palette.trough==base->trough;
        recipe->control_palette_custom[control]=same?0:1;
        if(!same) recipe->control_palettes[control]=edited_palette;
    }
    if (!text_copy(view->notes, 1, recipe->notes, sizeof(recipe->notes), error, capacity) ||
        tl_model_validate(&parsed, error, capacity) != 0)
        return -1;
    *candidate = parsed;
    return 0;
}

void tl_view_separate_preview(TLView *view, int visible)
{
    if (view != NULL) XmToggleButtonSetState(view->separate, visible != 0, False);
}

void tl_view_status(TLView *view, const char *message)
{
    if (view != NULL)
        label_set(view->status, message);
}

void tl_view_capability(TLView *view, TLFamily family, const char *message)
{
    if (view == NULL || family < 0 || family >= TL_FAMILY_COUNT)
        return;
    (void)snprintf(view->capabilities[family], sizeof(view->capabilities[family]), "%s",
                   message != NULL ? message : "Sem informação de capacidade.");
    if (view->has_model && view->snapshot.selected == family)
        label_wrapped(view->capability, view->capabilities[family], 48);
}

Widget tl_view_shell(TLView *view)
{
    return view != NULL ? view->shell : NULL;
}

void tl_view_palette(TLView *view, const unsigned short rgb[6][3])
{
    if (view == NULL || rgb == NULL)
        return;
    memcpy(view->rgb, rgb, sizeof(view->rgb));
    view->palette_valid = 1;
    palette_apply(view);
    tl_manual_paint_view_palette(view->manual_paint, rgb);
}

void tl_view_header_palette(TLView *view, const unsigned short rgb[6][3])
{
    if (view == NULL || rgb == NULL)
        return;
    memcpy(view->header_rgb, rgb, sizeof(view->header_rgb));
    view->header_palette_valid = 1;
    palette_apply(view);
    tl_manual_paint_view_header_palette(view->manual_paint, rgb);
}

void tl_view_shell_palettes(TLView *view,
                            const unsigned short body[6][3],
                            const unsigned short header[6][3])
{
    if (view == NULL || body == NULL || header == NULL)
        return;
    memcpy(view->rgb, body, sizeof(view->rgb));
    memcpy(view->header_rgb, header, sizeof(view->header_rgb));
    view->palette_valid = 1;
    view->header_palette_valid = 1;
    palette_apply(view);
    tl_manual_paint_view_palettes(view->manual_paint, body, header);
}

static XImage *manual_capture(TLView *view, Drawable drawable)
{
    Display *display = XtDisplay(view->shell);
    Window root;
    int x, y;
    unsigned int width, height, border, depth;
    XWindowAttributes attributes;
    if (!drawable || !XGetGeometry(display, drawable, &root, &x, &y,
                                   &width, &height, &border, &depth) ||
        !width || !height || width > 4096 || height > 4096 ||
        (uint64_t)width * height > 16000000U)
        return NULL;
    if (XGetWindowAttributes(display, (Window)drawable, &attributes) &&
        attributes.map_state != IsViewable)
        return NULL;
    XSync(display, False);
    if (!view->composite_checked) {
        int event_base, error_base;
        view->composite_supported = XCompositeQueryExtension(
            display, &event_base, &error_base) != 0;
        view->composite_checked = 1;
    }
    if (view->composite_supported) {
        Window target = (Window)drawable;
        int known = 0;
        for (size_t i = 0; i < view->paint_redirected_count; i++)
            if (view->paint_redirected[i] == target) {
                known = 1;
                break;
            }
        if (!known && view->paint_redirected_count <
                          sizeof(view->paint_redirected) /
                              sizeof(view->paint_redirected[0])) {
            int (*previous)(Display *, XErrorEvent *) = embed_trap(display);
            XCompositeRedirectWindow(display, target,
                                     CompositeRedirectAutomatic);
            if (embed_untrap(display, previous))
                view->paint_redirected[view->paint_redirected_count++] = target;
        }
        int (*previous)(Display *, XErrorEvent *) = embed_trap(display);
        Pixmap pixmap = XCompositeNameWindowPixmap(display, target);
        int named = embed_untrap(display, previous);
        if (!named)
            pixmap = None;
        if (pixmap != None) {
            XImage *image = safe_xget_image(display, pixmap, 0, 0, width,
                                             height);
            XFreePixmap(display, pixmap);
            if (image)
                return image;
        }
    }
    return safe_xget_image(display, drawable, 0, 0, width, height);
}

/* Capture the same canonical Motif widget used by the main comparison form.
 * Read the final root composition once the widget has been made visible: this
 * includes Primitive drawing as well as child windows in ComboBox, SpinBox and
 * Frame.  A direct-window read remains the fallback for a viewable primitive.
 * Controls hidden only by the main form's visibility filter are mapped just
 * long enough to paint and read them, then restored without changing the saved
 * recipe. */
static XImage *manual_capture_widget(TLView *view, Widget widget)
{
    Display *display;
    Screen *screen;
    Dimension width = 0, height = 0;
    Position root_x = 0, root_y = 0;
    int was_managed;
    XImage *image = NULL;
    if (!view || !widget || !XtParent(widget) || !XtIsRealized(XtParent(widget)))
        return NULL;
    display = XtDisplay(widget);
    screen = XtScreen(widget);
    was_managed = XtIsManaged(widget) != 0;
    if (!was_managed)
        XtManageChild(widget);
    if (XtIsRealized(widget)) {
        XMapWindow(display, XtWindow(widget));
        XClearArea(display, XtWindow(widget), 0, 0, 0, 0, True);
        /* XClearArea generates Expose on the server.  Deliver that event before
         * XmUpdateDisplay tries to drain it; the inverse order clears a valid
         * rendering and captures only the window background. */
        XSync(display, False);
    }
    XmUpdateDisplay(widget);
    XmUpdateDisplay(XtParent(widget));
    XSync(display, False);
    if (XtIsRealized(widget)) {
        XtVaGetValues(widget, XmNwidth, &width, XmNheight, &height, NULL);
        XtTranslateCoords(widget, 0, 0, &root_x, &root_y);
        if (width && height && width <= 4096 && height <= 4096 &&
            root_x >= 0 && root_y >= 0 &&
            (unsigned int)root_x + width <= (unsigned int)WidthOfScreen(screen) &&
            (unsigned int)root_y + height <= (unsigned int)HeightOfScreen(screen))
            image = safe_xget_image(display, RootWindowOfScreen(screen),
                                    root_x, root_y, width, height);
        if (!image && !XtIsComposite(widget) && width && height)
            image = safe_xget_image(display, XtWindow(widget), 0, 0,
                                    width, height);
        if (!image)
            image = manual_capture(view, XtWindow(widget));
    }
    if (!was_managed)
        XtUnmanageChild(widget);
    return image;
}

typedef struct {
    Widget widget;
    int value;
    int slider;
    int increment;
    int page;
    int valid;
} ManualScrollState;

static void manual_capture_drain_x(Widget widget)
{
    XtAppContext app;
    unsigned int count = 0;
    if (!widget)
        return;
    app = XtWidgetToApplicationContext(widget);
    XSync(XtDisplay(widget), False);
    while ((XtAppPending(app) & XtIMXEvent) && count++ < 2000U)
        XtAppProcessEvent(app, XtIMXEvent);
    XSync(XtDisplay(widget), False);
}

static void manual_scroll_state_save(Widget widget, ManualScrollState *state)
{
    if (!state)
        return;
    memset(state, 0, sizeof(*state));
    state->widget = widget;
    if (!widget)
        return;
    XmScrollBarGetValues(widget, &state->value, &state->slider,
                         &state->increment, &state->page);
    state->valid = 1;
}

static void manual_scroll_state_restore(const ManualScrollState *state)
{
    if (!state || !state->valid || !state->widget)
        return;
    XmScrollBarSetValues(state->widget, state->value, state->slider,
                         state->increment, state->page, True);
}

/* XmScrollBar windows outside the current clip may be mapped but never receive
 * the Expose that paints their arrows and slider.  Capture the actual canonical
 * widget from the main Motif form after making it visible in that form's own
 * viewport, then restore both scroll positions and its managed state. */
static XImage *manual_capture_scrolled_widget(TLView *view, Widget scrolled,
                                              Widget widget)
{
    Widget horizontal = NULL, vertical = NULL;
    ManualScrollState hstate, vstate;
    Window root = None, parent_window = None, *children = NULL;
    Window sibling_above = None;
    unsigned int child_count = 0;
    int was_managed;
    XImage *image;
    if (!view || !scrolled || !widget)
        return NULL;
    XtVaGetValues(scrolled, XmNhorizontalScrollBar, &horizontal,
                  XmNverticalScrollBar, &vertical, NULL);
    manual_scroll_state_save(horizontal, &hstate);
    manual_scroll_state_save(vertical, &vstate);
    was_managed = XtIsManaged(widget) != 0;
    if (!was_managed)
        XtManageChild(widget);
    XmScrollVisible(scrolled, widget, 2, 2);
    manual_capture_drain_x(widget);
    if (XtIsRealized(widget) && XtParent(widget) &&
        XtIsRealized(XtParent(widget)) &&
        XQueryTree(XtDisplay(widget), XtWindow(XtParent(widget)), &root,
                   &parent_window, &children, &child_count)) {
        for (unsigned int i = 0; i < child_count; ++i)
            if (children[i] == XtWindow(widget)) {
                if (i + 1 < child_count)
                    sibling_above = children[i + 1];
                break;
            }
        if (children)
            XFree(children);
        XRaiseWindow(XtDisplay(widget), XtWindow(widget));
        manual_capture_drain_x(widget);
    }
    if (XtIsRealized(widget)) {
        /* Establish Composite redirection before the repaint.  Naming a pixmap
         * only after drawing can expose the stale pre-Expose backing image. */
        XImage *prime = manual_capture(view, XtWindow(widget));
        if (prime)
            XDestroyImage(prime);
    }
    if (getenv("TL_PAINT_CAPTURE_DIAGNOSTICS")) {
        Widget clip = NULL;
        Position widget_x = 0, widget_y = 0, clip_x = 0, clip_y = 0;
        Dimension widget_width = 0, widget_height = 0;
        Dimension clip_width = 0, clip_height = 0;
        XWindowAttributes attributes;
        int map_state = -1;
        XtVaGetValues(scrolled, XmNclipWindow, &clip, NULL);
        XtVaGetValues(widget, XmNwidth, &widget_width, XmNheight,
                      &widget_height, NULL);
        XtTranslateCoords(widget, 0, 0, &widget_x, &widget_y);
        if (clip) {
            XtVaGetValues(clip, XmNwidth, &clip_width, XmNheight,
                          &clip_height, NULL);
            XtTranslateCoords(clip, 0, 0, &clip_x, &clip_y);
        }
        if (XtIsRealized(widget) &&
            XGetWindowAttributes(XtDisplay(widget), XtWindow(widget),
                                 &attributes))
            map_state = attributes.map_state;
        fprintf(stderr,
                "Paint capture %s widget=%d,%d %ux%u clip=%d,%d %ux%u "
                "managed=%d realized=%d mapped=%d\n",
                XtName(widget), widget_x, widget_y, widget_width, widget_height,
                clip_x, clip_y, clip_width, clip_height,
                XtIsManaged(widget) != 0, XtIsRealized(widget) != 0,
                map_state);
        if (XmIsScrollBar(widget)) {
            Pixel background = 0, foreground = 0, light = 0, shadow = 0,
                  trough = 0;
            TLNativePieces pieces;
            XtVaGetValues(widget, XmNbackground, &background,
                          XmNforeground, &foreground,
                          XmNtopShadowColor, &light,
                          XmNbottomShadowColor, &shadow,
                          XmNtroughColor, &trough, NULL);
            tl_motif_parts_measure(widget, &pieces);
            fprintf(stderr,
                    "Paint scrollbar colors bg=%lu fg=%lu light=%lu "
                    "shadow=%lu trough=%lu mask=%u slider=%d,%d %dx%d\n",
                    background, foreground, light, shadow, trough, pieces.mask,
                    pieces.slider.x, pieces.slider.y, pieces.slider.width,
                    pieces.slider.height);
        }
    }
    if (XtIsRealized(widget)) {
        Dimension width = 0, height = 0;
        XEvent expose;
        XtVaGetValues(widget, XmNwidth, &width, XmNheight, &height, NULL);
        XClearArea(XtDisplay(widget), XtWindow(widget), 0, 0, 0, 0, True);
        manual_capture_drain_x(widget);
        /* A child that was unmanaged when the scene was laid out can become
         * viewable without Motif scheduling its redisplay.  Dispatch one
         * bounded Expose to the real widget window; this invokes the toolkit's
         * native drawing code and does not synthesize any bitmap ourselves. */
        memset(&expose, 0, sizeof(expose));
        expose.xexpose.type = Expose;
        expose.xexpose.display = XtDisplay(widget);
        expose.xexpose.window = XtWindow(widget);
        expose.xexpose.width = width;
        expose.xexpose.height = height;
        expose.xexpose.count = 0;
        (void)XtDispatchEventToWidget(widget, &expose);
        if (XmIsScrollBar(widget)) {
            int value = 0, slider = 0, increment = 0, page = 0;
            int minimum = 0, maximum = 0, alternate;
            XmScrollBarGetValues(widget, &value, &slider, &increment, &page);
            XtVaGetValues(widget, XmNminimum, &minimum, XmNmaximum, &maximum,
                          NULL);
            alternate = value < maximum - slider ? value + 1 : value - 1;
            if (alternate >= minimum && alternate <= maximum - slider &&
                alternate != value) {
                XmScrollBarSetValues(widget, alternate, slider, increment,
                                     page, False);
                XmScrollBarSetValues(widget, value, slider, increment, page,
                                     False);
            }
        }
        manual_capture_drain_x(widget);
    }
    image = XtIsRealized(widget) ? manual_capture(view, XtWindow(widget)) : NULL;
    if (!image)
        image = manual_capture_widget(view, widget);
    if (sibling_above != None) {
        XWindowChanges changes;
        memset(&changes, 0, sizeof(changes));
        changes.sibling = sibling_above;
        changes.stack_mode = Below;
        XConfigureWindow(XtDisplay(widget), XtWindow(widget),
                         CWSibling | CWStackMode, &changes);
    }
    manual_scroll_state_restore(&hstate);
    manual_scroll_state_restore(&vstate);
    manual_capture_drain_x(scrolled);
    if (!was_managed)
        XtUnmanageChild(widget);
    return image;
}

static XImage *manual_clone_image(TLView *view, const XImage *source)
{
    Display *display = XtDisplay(view->shell);
    XImage *copy;
    size_t bytes;
    if (!source || source->width <= 0 || source->height <= 0)
        return NULL;
    copy = XCreateImage(display, DefaultVisualOfScreen(XtScreen(view->shell)),
                        source->depth, source->format, 0, NULL,
                        (unsigned)source->width, (unsigned)source->height,
                        source->bitmap_pad > 0 ? source->bitmap_pad : 32, 0);
    if (!copy)
        return NULL;
    bytes = (size_t)copy->bytes_per_line * (size_t)copy->height;
    if (bytes > 64u * 1024u * 1024u || !(copy->data = calloc(1, bytes))) {
        XDestroyImage(copy);
        return NULL;
    }
    for (int y = 0; y < source->height; ++y)
        for (int x = 0; x < source->width; ++x)
            XPutPixel(copy, x, y, XGetPixel((XImage *)source, x, y));
    return copy;
}

static XImage *manual_png_image(TLView *view, const char *path)
{
    png_image png = {0};
    unsigned char *rgba = NULL;
    XImage *image = NULL;
    Visual *visual;
    int depth;
    size_t count;
    unsigned char background[3] = {0, 0, 0};
    png.version = PNG_IMAGE_VERSION;
    if (!png_image_begin_read_from_file(&png, path)) goto done;
    if (!png.width || !png.height || png.width > 4096 || png.height > 4096 ||
        (size_t)png.width * png.height > 16000000U) goto done;
    png.format = PNG_FORMAT_RGBA;
    count = PNG_IMAGE_SIZE(png);
    rgba = malloc(count);
    if (!rgba || !png_image_finish_read(&png, NULL, rgba, 0, NULL)) goto done;
    memcpy(background, rgba, sizeof(background));
    XtVaGetValues(view->shell, XtNvisual, &visual, XtNdepth, &depth, NULL);
    if (!visual) visual = DefaultVisualOfScreen(XtScreen(view->shell));
    if (visual->class != TrueColor) goto done;
    image = XCreateImage(XtDisplay(view->shell), visual, (unsigned int)depth,
                         ZPixmap, 0, NULL, png.width, png.height, 32, 0);
    if (!image || (size_t)image->bytes_per_line > SIZE_MAX / png.height) {
        if (image) XDestroyImage(image);
        image = NULL;
        goto done;
    }
    image->data = calloc((size_t)image->bytes_per_line, png.height);
    if (!image->data) { XDestroyImage(image); image = NULL; goto done; }
    for (unsigned int y = 0; y < png.height; ++y)
        for (unsigned int x = 0; x < png.width; ++x) {
            const unsigned char *pixel = rgba + ((size_t)y * png.width + x) * 4;
            unsigned char channel[3];
            unsigned long packed;
            for (int c = 0; c < 3; ++c)
                channel[c] = (unsigned char)(((unsigned int)pixel[c] * pixel[3] +
                    (unsigned int)background[c] * (255U - pixel[3]) + 127U) / 255U);
            packed = masked_channel(channel[0], visual->red_mask) |
                     masked_channel(channel[1], visual->green_mask) |
                     masked_channel(channel[2], visual->blue_mask);
            XPutPixel(image, (int)x, (int)y, packed);
        }
done:
    free(rgba);
    png_image_free(&png);
    return image;
}

static void manual_capture_catalog(TLView *view)
{
    if (!view)
        return;
    for (int i = 0; i < TL_CONTROL_COUNT; ++i) {
        TLControlAvailability availability;
        Widget reference = view->motif_reference_widgets[i];
        Widget native = view->preview_widgets[i];
        if (view->paint_motif_samples[i]) {
            XDestroyImage(view->paint_motif_samples[i]);
            view->paint_motif_samples[i] = NULL;
        }
        if (view->paint_native_samples[i]) {
            XDestroyImage(view->paint_native_samples[i]);
            view->paint_native_samples[i] = NULL;
        }
        if (!tl_control_availability(i, &availability) &&
            availability.motif_available)
            view->paint_motif_samples[i] = manual_capture_scrolled_widget(
                view, view->motif_reference_scroll, reference);
        if (!tl_control_availability(i, &availability) &&
            availability.gtk2_available && XtIsRealized(native) &&
            XtIsManaged(native))
            view->paint_native_samples[i] = manual_capture_widget(view, native);
    }
}

void tl_manual_paint_sample_request_default(TLManualPaintSampleRequest *request,
                                            int family, int control, int state)
{
    if (!request) return;
    *request = (TLManualPaintSampleRequest){
        .source = TL_PAINT_SAMPLE_LIVE,
        .family = family, .control = control, .state = state,
        .length_px = 0, .thickness_px = 0,
        .value = 25, .page_size = 25,
        .part = TL_PAINT_SAMPLE_WHOLE,
        .direction = TL_PAINT_DIRECTION_AUTO
    };
}

int tl_manual_paint_sample_request_validate(
    const TLManualPaintSampleRequest *request, char *error, size_t capacity)
{
    const char *message = NULL;
    int scrollbar;
    if (!request) message = "Pedido privado de amostra ausente.";
    else if (request->source < TL_PAINT_SAMPLE_LIVE ||
             request->source > TL_PAINT_SAMPLE_R584 ||
             request->family < 0 || request->family >= TL_FAMILY_COUNT ||
             request->control < 0 || request->control >= TL_CONTROL_COUNT ||
             request->state < 0 || request->state > 4)
        message = "Família, controle ou estado inválido no pedido de amostra.";
    else if (request->source == TL_PAINT_SAMPLE_R584 &&
             request->family != TL_GTK2)
        message = "A revisão R584 pertence somente ao adaptador GTK2.";
    else if ((request->length_px != 0 &&
              (request->length_px < 15 || request->length_px > 2048)) ||
             (request->thickness_px != 0 &&
              (request->thickness_px < 1 || request->thickness_px > 512)))
        message = "Comprimento deve ser natural ou 15–2048 px; espessura, natural ou 1–512 px.";
    else if (request->page_size < 1 || request->page_size > 100 ||
             request->value < 0 || request->value > 100 - request->page_size)
        message = "Faixa privada usa 0–100: página 1–100 e valor até 100 menos a página.";
    else if (request->part < TL_PAINT_SAMPLE_WHOLE ||
             request->part > TL_PAINT_SAMPLE_FITTING ||
             request->direction < TL_PAINT_DIRECTION_AUTO ||
             request->direction > TL_PAINT_DIRECTION_DOWN)
        message = "Peça ou direção inválida no pedido de amostra.";
    if (message) goto invalid;
    scrollbar = request->control == 10 || request->control == 11;
    if (!scrollbar && (request->length_px || request->thickness_px ||
                       request->value != 25 || request->page_size != 25 ||
                       request->part != TL_PAINT_SAMPLE_WHOLE ||
                       request->direction != TL_PAINT_DIRECTION_AUTO)) {
        message = "Geometria, faixa, peça e direção privadas exigem uma barra de rolagem.";
        goto invalid;
    }
    if (request->control == 10 &&
        request->direction != TL_PAINT_DIRECTION_AUTO &&
        request->direction != TL_PAINT_DIRECTION_LEFT &&
        request->direction != TL_PAINT_DIRECTION_RIGHT) {
        message = "Barra horizontal aceita direção automática, esquerda ou direita.";
        goto invalid;
    }
    if (request->control == 11 &&
        request->direction != TL_PAINT_DIRECTION_AUTO &&
        request->direction != TL_PAINT_DIRECTION_UP &&
        request->direction != TL_PAINT_DIRECTION_DOWN) {
        message = "Barra vertical aceita direção automática, cima ou baixo.";
        goto invalid;
    }
    if (error && capacity) error[0] = 0;
    return 0;
invalid:
    if (error && capacity) snprintf(error, capacity, "%s", message);
    return -1;
}

int tl_view_manual_paint_sample_current(
    const TLView *view, TLManualPaintSampleRequest *request)
{
    if (!view || !request || !view->paint_request_valid) return -1;
    *request = view->paint_request;
    return 0;
}

int tl_view_manual_paint_reference_current(
    const TLView *view, TLManualPaintSampleRequest *request)
{
    if (!view || !request || !view->paint_reference_request_valid) return -1;
    *request = view->paint_reference_request;
    return 0;
}

static int manual_request_equal(const TLManualPaintSampleRequest *left,
                                const TLManualPaintSampleRequest *right)
{
    return left && right && !memcmp(left, right, sizeof(*left));
}

static void manual_paint_present_samples(TLView *view);

static void manual_paint_r584_present(
    TLView *view, const TLManualPaintSampleRequest *request)
{
    TLGtk2R584Query query;
    TLGtk2R584Result result;
    XImage *image = NULL;
    char error[TL_TEXT_MAX] = {0};
    char notice[TL_TEXT_MAX];
    if (!view || !view->manual_paint || !request)
        return;
    if (!view->paint_r584_catalog) {
        snprintf(notice, sizeof(notice),
                 "R584 indisponível: %.420s",
                 view->paint_r584_error[0] ? view->paint_r584_error
                                           : "catálogo não carregado.");
        manual_paint_present_samples(view);
        tl_manual_paint_view_notice(view->manual_paint, notice);
        tl_view_status(view, notice);
        return;
    }
    memset(&query, 0, sizeof(query));
    query.control = request->control;
    switch (request->part) {
    case TL_PAINT_SAMPLE_WHOLE:
        query.part = TL_GTK2_R584_PART_WHOLE;
        break;
    case TL_PAINT_SAMPLE_ARROW:
        query.part = TL_GTK2_R584_PART_ARROW;
        break;
    case TL_PAINT_SAMPLE_ARROW_BUTTON:
        query.part = TL_GTK2_R584_PART_ARROW_BUTTON;
        break;
    case TL_PAINT_SAMPLE_TROUGH:
        query.part = TL_GTK2_R584_PART_TROUGH;
        break;
    case TL_PAINT_SAMPLE_THUMB:
        query.part = TL_GTK2_R584_PART_THUMB;
        break;
    default:
        snprintf(notice, sizeof(notice),
                 "R584 não contém um asset certificado para Encaixe; "
                 "a referência permaneceu vazia, sem fallback.");
        manual_paint_present_samples(view);
        tl_manual_paint_view_notice(view->manual_paint, notice);
        tl_view_status(view, notice);
        return;
    }
    switch (request->state) {
    case 0:
        query.state = TL_GTK2_R584_STATE_NORMAL;
        break;
    case 2:
        query.state = TL_GTK2_R584_STATE_PRESSED;
        break;
    case 3:
        query.state = TL_GTK2_R584_STATE_DISABLED;
        break;
    case 1:
        snprintf(notice, sizeof(notice),
                 "R584 nomeia este estado como focused, não como Hover; "
                 "nenhuma equivalência foi aplicada automaticamente.");
        manual_paint_present_samples(view);
        tl_manual_paint_view_notice(view->manual_paint, notice);
        tl_view_status(view, notice);
        return;
    default:
        snprintf(notice, sizeof(notice),
                 "R584 não declara estado Backdrop; nenhuma imagem alternativa "
                 "foi usada.");
        manual_paint_present_samples(view);
        tl_manual_paint_view_notice(view->manual_paint, notice);
        tl_view_status(view, notice);
        return;
    }
    query.direction = TL_GTK2_R584_DIRECTION_NONE;
    if (request->part == TL_PAINT_SAMPLE_TROUGH)
        query.direction = request->control == 10
                              ? TL_GTK2_R584_DIRECTION_HORIZONTAL
                              : TL_GTK2_R584_DIRECTION_VERTICAL;
    else if (request->part == TL_PAINT_SAMPLE_ARROW ||
             request->part == TL_PAINT_SAMPLE_ARROW_BUTTON) {
        switch (request->direction) {
        case TL_PAINT_DIRECTION_LEFT:
            query.direction = TL_GTK2_R584_DIRECTION_LEFT;
            break;
        case TL_PAINT_DIRECTION_RIGHT:
            query.direction = TL_GTK2_R584_DIRECTION_RIGHT;
            break;
        case TL_PAINT_DIRECTION_UP:
            query.direction = TL_GTK2_R584_DIRECTION_UP;
            break;
        case TL_PAINT_DIRECTION_DOWN:
            query.direction = TL_GTK2_R584_DIRECTION_DOWN;
            break;
        default:
            snprintf(notice, sizeof(notice),
                     "Escolha Esquerda/Direita ou Cima/Baixo para localizar "
                     "uma seta R584 sem ambiguidade.");
            manual_paint_present_samples(view);
            tl_manual_paint_view_notice(view->manual_paint, notice);
            tl_view_status(view, notice);
            return;
        }
    }
    query.variant = (request->control == 2 || request->control == 3)
                        ? TL_GTK2_R584_VARIANT_ON
                        : TL_GTK2_R584_VARIANT_NONE;
    if (tl_gtk2_r584_catalog_lookup(view->paint_r584_catalog, &query, &result,
                                    error, sizeof(error))) {
        snprintf(notice, sizeof(notice), "Consulta R584 inválida: %.430s",
                 error[0] ? error : "erro desconhecido.");
    } else if (!result.available) {
        snprintf(notice, sizeof(notice), "R584: %.450s", result.reason);
    } else {
        image = manual_png_image(view, result.path);
        if (!image)
            snprintf(notice, sizeof(notice),
                     "R584 validou %s, mas o PNG não pôde ser aberto.",
                     result.asset_name);
        else {
            if (view->paint_reference_sample)
                XDestroyImage(view->paint_reference_sample);
            view->paint_reference_sample = image;
            snprintf(notice, sizeof(notice),
                     "R584 importado como referência editável: %s; "
                     "SHA-256 %.16s…; nada foi aplicado ao tema.",
                     result.asset_name, result.sha256);
        }
    }
    manual_paint_present_samples(view);
    tl_manual_paint_view_notice(view->manual_paint, notice);
    tl_view_status(view, notice);
}

static void manual_paint_present_samples(TLView *view)
{
    XImage *reference = NULL, *native = NULL;
    int reference_source = TL_MOTIF;
    if (!view || !view->manual_paint)
        return;
    if (view->paint_reference_request_valid) {
        const TLManualPaintSampleRequest *request =
            &view->paint_reference_request;
        reference_source = request->source == TL_PAINT_SAMPLE_R584 ?
            TL_PAINT_REFERENCE_R584 : request->family;
        if (request->source == TL_PAINT_SAMPLE_R584)
            reference = manual_clone_image(view,
                                            view->paint_reference_sample);
        else if (request->family == TL_MOTIF)
            reference = manual_clone_image(
                view, view->paint_motif_samples[request->control]);
        else if (view->paint_request_valid &&
                 manual_request_equal(request, &view->paint_request))
            reference = manual_clone_image(
                view, view->paint_native_samples[request->control]);
        else
            reference = manual_clone_image(view,
                                            view->paint_reference_sample);
    }
    if (view->paint_request_valid)
        native = manual_clone_image(
            view, view->paint_native_samples[view->paint_request.control]);
    tl_manual_paint_view_samples(view->manual_paint, reference_source,
                                 reference, native);
}

static int manual_paint_sample_request_apply(
    TLView *view, const TLManualPaintSampleRequest *request,
    char *error, size_t capacity, int force)
{
    int changed;
    if (!view || !view->manual_paint ||
        tl_manual_paint_sample_request_validate(request, error, capacity))
        return -1;
    changed = !view->paint_request_valid ||
              memcmp(&view->paint_request, request, sizeof(*request)) != 0;
    view->paint_request = *request;
    view->paint_request_valid = 1;
    view->paint_context_valid = 1;
    view->paint_family = request->family;
    view->paint_control = request->control;
    view->paint_state = request->state;
    if ((changed || force) && request->family != TL_MOTIF &&
        view->paint_native_samples[request->control]) {
        XDestroyImage(view->paint_native_samples[request->control]);
        view->paint_native_samples[request->control] = NULL;
    }
    if ((changed || force) && request->family != TL_MOTIF && view->dispatch)
        view->dispatch(view->context, TL_PAINT_SAMPLE,
                       (request->family << 8) |
                       (request->control << 4) | request->state);
    manual_paint_present_samples(view);
    if (error && capacity) error[0] = 0;
    return 0;
}

int tl_view_manual_paint_sample_request(
    TLView *view, const TLManualPaintSampleRequest *request,
    char *error, size_t capacity)
{
    if (request && request->source != TL_PAINT_SAMPLE_LIVE) {
        if (error && capacity)
            snprintf(error, capacity,
                     "A amostra alvo aceita somente o renderizador nativo atual.");
        return -1;
    }
    return manual_paint_sample_request_apply(view, request, error, capacity, 0);
}

static void manual_paint_samples(void *context, int family, int control, int state)
{
    TLView *view = context;
    if (!view || !view->manual_paint || control < 0 || control >= TL_CONTROL_COUNT ||
        family < 0 || family >= TL_FAMILY_COUNT)
        return;
    view->paint_context_valid = 1;
    view->paint_family = family;
    view->paint_control = control;
    view->paint_state = state;
    manual_paint_present_samples(view);
}

static void manual_paint_reference_samples(
    void *context, const TLManualPaintSampleRequest *request)
{
    TLView *view = context;
    char error[TL_TEXT_MAX] = {0};
    int changed, uses_target;
    if (!view || !view->manual_paint)
        return;
    if (tl_manual_paint_sample_request_validate(request, error, sizeof(error))) {
        if (view && error[0])
            tl_view_status(view, error);
        return;
    }
    changed = !view->paint_reference_request_valid ||
              !manual_request_equal(&view->paint_reference_request, request);
    view->paint_reference_request = *request;
    view->paint_reference_request_valid = 1;
    uses_target = view->paint_request_valid &&
                  manual_request_equal(request, &view->paint_request);
    if (changed && view->paint_reference_sample) {
        XDestroyImage(view->paint_reference_sample);
        view->paint_reference_sample = NULL;
    }
    if (request->source == TL_PAINT_SAMPLE_R584) {
        manual_paint_r584_present(view, request);
        return;
    }
    if (changed && request->source == TL_PAINT_SAMPLE_LIVE &&
        request->family != TL_MOTIF && !uses_target && view->dispatch)
        view->dispatch(view->context, TL_PAINT_REFERENCE_SAMPLE,
                       (request->family << 8) |
                       (request->control << 4) | request->state);
    manual_paint_present_samples(view);
}

int tl_view_manual_paint_r584_catalog(TLView *view, const char *receipt_path,
                                      const char *manifest_path, char *error,
                                      size_t capacity)
{
    TLGtk2R584Catalog *catalog = NULL;
    char detail[TL_TEXT_MAX] = {0};
    if (!view || !receipt_path || !manifest_path) {
        if (error && capacity)
            snprintf(error, capacity, "Configuração R584 ausente.");
        return -1;
    }
    if (tl_gtk2_r584_catalog_load_canonical(&catalog, receipt_path,
                                             manifest_path, detail,
                                             sizeof(detail))) {
        snprintf(view->paint_r584_error, sizeof(view->paint_r584_error),
                 "%s", detail[0] ? detail : "catálogo rejeitado.");
        if (error && capacity)
            snprintf(error, capacity, "%s", view->paint_r584_error);
        return -1;
    }
    tl_gtk2_r584_catalog_free(view->paint_r584_catalog);
    view->paint_r584_catalog = catalog;
    view->paint_r584_error[0] = '\0';
    if (error && capacity)
        error[0] = '\0';
    if (view->paint_reference_request_valid &&
        view->paint_reference_request.source == TL_PAINT_SAMPLE_R584)
        manual_paint_r584_present(view, &view->paint_reference_request);
    return 0;
}

int tl_view_manual_paint_open(TLView *view, const char *path, int family,
                              int control, int state)
{
    if (!view || !path || family < 0 || family >= TL_FAMILY_COUNT ||
        control < 0 || control >= TL_CONTROL_COUNT || state < 0 || state >= 5)
        return -1;
    if (view->manual_paint != NULL) {
        /* Refresh after a real popdown, when the main form is unobscured.  A
         * context change inside an already visible Paint window must preserve
         * the last canonical snapshots: recapturing the covered main window
         * would replace them with the editor's flat background. */
        if (!tl_manual_paint_view_is_visible(view->manual_paint))
            manual_capture_catalog(view);
        tl_manual_paint_view_context(view->manual_paint, family, control, state);
        if (view->palette_valid)
            tl_manual_paint_view_palette(view->manual_paint, view->rgb);
        if (view->header_palette_valid)
            tl_manual_paint_view_header_palette(view->manual_paint,
                                                view->header_rgb);
        manual_paint_samples(view, family, control, state);
        tl_manual_paint_view_present(view->manual_paint);
        return 0;
    }
    manual_capture_catalog(view);
    view->manual_paint = tl_manual_paint_view_open(view->shell, path, family,
                          control, state, view->palette_valid ? view->rgb : NULL,
                          view->native_font, view->editors,
                          manual_paint_samples, view,
                          manual_paint_reference_samples, view);
    if (view->manual_paint != NULL) {
        if (view->header_palette_valid)
            tl_manual_paint_view_header_palette(view->manual_paint,
                                                view->header_rgb);
        manual_paint_samples(view, family, control, state);
        tl_manual_paint_view_present(view->manual_paint);
    }
    return view->manual_paint ? 0 : -1;
}
int tl_view_manual_paint_checkpoint(TLView *view)
{
    return view ? tl_manual_paint_view_checkpoint(view->manual_paint) : 0;
}

int tl_view_manual_paint_native_png(TLView *view, const char *path,
                                    int family, int control, int state)
{
    XImage *image;
    if (!view || !path || !view->manual_paint ||
        (family != TL_GTK3 && family != TL_GTK2 && family != TL_GTK4) ||
        control < 0 || control >= TL_CONTROL_COUNT || state < 0 || state >= 5 ||
        !view->paint_context_valid || view->paint_family != family ||
        view->paint_control != control || view->paint_state != state)
        return -1;
    image = manual_png_image(view, path);
    if (!image) return -1;
    if (view->paint_native_samples[control])
        XDestroyImage(view->paint_native_samples[control]);
    view->paint_native_samples[control] = image;
    manual_paint_present_samples(view);
    return 0;
}

int tl_view_manual_paint_reference_png(TLView *view, const char *path,
                                       int family, int control, int state)
{
    XImage *image;
    if (!view || !path || !view->manual_paint ||
        (family != TL_GTK3 && family != TL_GTK2 && family != TL_GTK4) ||
        control < 0 || control >= TL_CONTROL_COUNT || state < 0 || state >= 5 ||
        !view->paint_reference_request_valid ||
        view->paint_reference_request.source != TL_PAINT_SAMPLE_LIVE ||
        view->paint_reference_request.family != family ||
        view->paint_reference_request.control != control ||
        view->paint_reference_request.state != state)
        return -1;
    image = manual_png_image(view, path);
    if (!image)
        return -1;
    if (view->paint_reference_sample)
        XDestroyImage(view->paint_reference_sample);
    view->paint_reference_sample = image;
    manual_paint_present_samples(view);
    return 0;
}

void tl_view_manual_paint_refresh_sample(TLView *view)
{
    TLManualPaintSampleRequest request;
    char error[TL_TEXT_MAX];
    if (!view || !view->manual_paint || !view->paint_context_valid)
        return;
    if (view->paint_request_valid &&
        view->paint_request.family == view->paint_family &&
        view->paint_request.control == view->paint_control &&
        view->paint_request.state == view->paint_state)
        request = view->paint_request;
    else
        tl_manual_paint_sample_request_default(
            &request, view->paint_family, view->paint_control,
            view->paint_state);
    if (manual_paint_sample_request_apply(view, &request, error,
                                          sizeof(error), 1))
        tl_view_status(view, error);
    if (view->paint_reference_request_valid &&
        view->paint_reference_request.source == TL_PAINT_SAMPLE_LIVE &&
        view->paint_reference_request.family != TL_MOTIF &&
        (!view->paint_request_valid ||
         !manual_request_equal(&view->paint_reference_request,
                               &view->paint_request)) && view->dispatch) {
        const TLManualPaintSampleRequest *reference =
            &view->paint_reference_request;
        view->dispatch(view->context, TL_PAINT_REFERENCE_SAMPLE,
                       (reference->family << 8) |
                       (reference->control << 4) | reference->state);
    }
}

void tl_view_preview_palette(TLView *view, const unsigned short rgb[6][3])
{
    if (view == NULL || rgb == NULL) return;
    memcpy(view->preview_rgb, rgb, sizeof(view->preview_rgb));
    view->preview_palette_valid = 1;
    palette_apply(view);
}

void tl_view_reference_palette(TLView *view, const unsigned short rgb[6][3])
{
    if (view == NULL || rgb == NULL) return;
    memcpy(view->reference_rgb, rgb, sizeof(view->reference_rgb));
    view->reference_palette_valid = 1;
    palette_apply(view);
}

void tl_view_show_reference_image(TLView *view)
{
    if (view != NULL && view->reference_image != NULL)
        XtManageChild(view->reference_dialog);
}

void tl_view_preview_settings(TLView *view, int *automatic, int *delay_ms)
{
    double value;
    if (view == NULL) return;
    if (automatic != NULL) *automatic = XmToggleButtonGetState(view->automatic) ? 1 : 0;
    if (delay_ms != NULL) {
        *delay_ms = view->has_model ? view->snapshot.debounce_ms : 600;
        if (number_read(view->delay, 1, &value) && value >= 100 && value <= 10000)
            *delay_ms = (int)value;
    }
}

void tl_view_code(TLView *view, const char *text)
{
    if (view != NULL) {
        const char *next = text != NULL ? text : "";
        char *current = XmTextGetString(view->code);
        int changed = current == NULL || strcmp(current, next) != 0;
        if (current) XtFree(current);
        if (changed) {
            tl_editor_set_text(view->code, next);
            code_search_clear(view, "Trecho atualizado; localize novamente.");
        }
    }
}

unsigned long tl_view_canvas(TLView *view)
{
    if (view == NULL || !XtIsRealized(view->canvas)) return 0UL;
    Window canvas = XtWindow(view->canvas);
    tl_gtk4_canvas_publish(XtDisplay(view->canvas), canvas);
    return (unsigned long)canvas;
}

void tl_view_schemes(TLView *view, const char *const *ids, int count)
{
    XmString items[SCHEME_LIMIT];
    int i, j, previous;
    if (view == NULL || count < 0 || (count > 0 && ids == NULL)) return;
    previous = view->updating; view->updating = 1;
    memset(view->schemes, 0, sizeof(view->schemes)); view->scheme_count = 1;
    items[0] = compound("Esquema KDE atual");
    for (i = 0; i < count && view->scheme_count < SCHEME_LIMIT; ++i) {
        int duplicate = 0;
        if (ids[i] == NULL || ids[i][0] == '\0' || strlen(ids[i]) >= sizeof(view->schemes[0])) continue;
        for (j = 0; j < view->scheme_count; ++j)
            if (!strcmp(view->schemes[j], ids[i])) duplicate = 1;
        if (duplicate) continue;
        (void)snprintf(view->schemes[view->scheme_count], sizeof(view->schemes[0]), "%s", ids[i]);
        items[view->scheme_count++] = compound(ids[i]);
    }
    XtVaSetValues(view->scheme_combo, XmNitems, items, XmNitemCount, view->scheme_count,
                  XmNselectedPosition, 0, NULL);
    for (i = 0; i < view->scheme_count; ++i) XmStringFree(items[i]);
    view->updating = previous;
    if(view->has_model) {
        int selected=0;
        for(i=0;i<view->scheme_count;++i)if(!strcmp(view->schemes[i],view->snapshot.color_scheme))selected=i;
        view->updating=1;
        XtVaSetValues(view->scheme_combo,XmNselectedPosition,selected,NULL);
        view->updating=previous;
    }
}

int tl_view_reference(TLView *view, const char *path, char *error, size_t capacity)
{
    png_image png;
    unsigned char *rgba = NULL;
    XImage *image = NULL;
    Visual *visual;
    Display *display;
    int depth;
    unsigned int x, y;
    unsigned int background[3];
    size_t count;
    char notice[256];
    if (view == NULL || path == NULL || path[0] == '\0') {
        set_error(error, capacity, "Escolha uma referência PNG.");
        return -1;
    }
    memset(&png, 0, sizeof(png)); png.version = PNG_IMAGE_VERSION;
    if (!png_image_begin_read_from_file(&png, path)) {
        set_error(error, capacity, png.message);
        png_image_free(&png);
        return -1;
    }
    /* Bound untrusted image allocation while preserving native pixel dimensions. */
    if (png.width == 0 || png.height == 0 || png.width > 8192 || png.height > 8192 ||
        (size_t)png.width * png.height > 16777216U) {
        set_error(error, capacity, "Referência excede 8192 px por eixo ou 16 milhões de pixels.");
        png_image_free(&png);
        return -1;
    }
    png.format = PNG_FORMAT_RGBA;
    count = PNG_IMAGE_SIZE(png);
    rgba = (unsigned char *)malloc(count);
    if (rgba == NULL || !png_image_finish_read(&png, NULL, rgba, 0, NULL)) {
        set_error(error, capacity, rgba == NULL ? "Memória insuficiente para referência." : png.message);
        free(rgba); png_image_free(&png);
        return -1;
    }
    display = XtDisplay(view->shell);
    XtVaGetValues(view->shell, XtNvisual, &visual, XtNdepth, &depth, NULL);
    if (visual == NULL)
        visual = DefaultVisualOfScreen(XtScreen(view->shell));
    if (visual->class != TrueColor) {
        set_error(error, capacity, "A referência PNG exige um visual TrueColor; nenhum mapa de cores será alterado.");
        free(rgba); png_image_free(&png);
        return -1;
    }
    image = XCreateImage(display, visual, (unsigned int)depth, ZPixmap, 0, NULL,
                          png.width, png.height, 32, 0);
    if (image == NULL || (size_t)image->bytes_per_line > SIZE_MAX / png.height) {
        set_error(error, capacity, "Não foi possível criar a imagem X11 da referência.");
        if (image != NULL) XDestroyImage(image);
        free(rgba); png_image_free(&png);
        return -1;
    }
    image->data = (char *)calloc((size_t)image->bytes_per_line, png.height);
    if (image->data == NULL) {
        set_error(error, capacity, "Memória insuficiente para imagem X11.");
        XDestroyImage(image); free(rgba); png_image_free(&png);
        return -1;
    }
    if (view->palette_valid) {
        for (x = 0; x < 3; ++x)
            background[x] = (view->rgb[FACE][x] + 128U) / 257U;
    } else {
        XColor current;
        Colormap colormap;
        XtVaGetValues(view->reference_area, XmNbackground, &current.pixel, NULL);
        XtVaGetValues(view->shell, XtNcolormap, &colormap, NULL);
        XQueryColor(display, colormap, &current);
        background[0] = (current.red + 128U) / 257U;
        background[1] = (current.green + 128U) / 257U;
        background[2] = (current.blue + 128U) / 257U;
    }
    for (y = 0; y < png.height; ++y)
        for (x = 0; x < png.width; ++x) {
            const unsigned char *pixel = rgba + ((size_t)y * png.width + x) * 4;
            unsigned char channels[3];
            unsigned long packed;
            int c;
            for (c = 0; c < 3; ++c) {
                channels[c] = (unsigned char)(((unsigned int)pixel[c] * pixel[3] +
                         background[c] * (255U - pixel[3]) + 127U) / 255U);
            }
            packed = masked_channel(channels[0], visual->red_mask) |
                     masked_channel(channels[1], visual->green_mask) |
                     masked_channel(channels[2], visual->blue_mask);
            XPutPixel(image, (int)x, (int)y, packed);
        }
    free(rgba);
    if (view->reference_image != NULL)
        XDestroyImage(view->reference_image);
    view->reference_image = image;
    view->reference_width = png.width; view->reference_height = png.height;
    XtVaSetValues(view->reference_area, XmNwidth, (Dimension)png.width,
                   XmNheight, (Dimension)png.height, NULL);
    (void)snprintf(notice, sizeof(notice), "Imagem histórica: %u × %u px — escala 1:1, sem interpolação.",
                   png.width, png.height);
    label_set(view->reference_notice, notice);
    png_image_free(&png);
    if (XtIsRealized(view->reference_area))
        XClearArea(display, XtWindow(view->reference_area), 0, 0, 0, 0, True);
    return 0;
}

static void choice_destroyed(Widget widget, XtPointer client, XtPointer call)
{
    FileChoice *choice = (FileChoice *)client;
    FileChoice **entry = &choice->view->choices;
    (void)widget; (void)call;
    while (*entry != NULL && *entry != choice)
        entry = &(*entry)->next;
    if (*entry == choice)
        *entry = choice->next;
    free(choice);
}

static void choice_cancel(Widget widget, XtPointer client, XtPointer call)
{
    FileChoice *choice = (FileChoice *)client;
    (void)widget; (void)call;
    XtDestroyWidget(XtParent(choice->dialog));
}

static void choice_ok(Widget widget, XtPointer client, XtPointer call)
{
    FileChoice *choice = (FileChoice *)client;
    XmFileSelectionBoxCallbackStruct *event = (XmFileSelectionBoxCallbackStruct *)call;
    char *path = NULL;
    TLFileChosen chosen = choice->chosen;
    void *context = choice->context;
    (void)widget;
    if (event == NULL || !XmStringGetLtoR(event->value, XmFONTLIST_DEFAULT_TAG, &path) || path == NULL)
        return;
    /* Path is valid throughout the controller callback. Destroy first so a
     * controller that closes the main view cannot leave a dangling dialog. */
    XtDestroyWidget(XtParent(choice->dialog));
    if (chosen != NULL)
        chosen(context, path);
    XtFree(path);
}

static void choose_path(TLView *view, const char *title, const char *initial,
                        TLFileChosen chosen, void *context, int directory)
{
    FileChoice *choice;
    XmString heading, mask;
    if (view == NULL || chosen == NULL)
        return;
    choice = (FileChoice *)calloc(1, sizeof(*choice));
    if (choice == NULL) {
        tl_view_status(view, "Memória insuficiente para seleção de arquivo.");
        return;
    }
    choice->view = view; choice->chosen = chosen; choice->context = context;
    choice->dialog = XmCreateFileSelectionDialog(view->shell, "chooseRecipeFile", NULL, 0);
    heading = compound(title != NULL ? title : "Escolher arquivo");
    mask = compound(initial != NULL && initial[0] != '\0' ? initial : "*");
    XtVaSetValues(choice->dialog, XmNdialogTitle, heading, XmNdirMask, mask,
                   XmNfileTypeMask, directory ? XmFILE_DIRECTORY : XmFILE_REGULAR,
                   XmNautoUnmanage, False, XmNdialogStyle, XmDIALOG_FULL_APPLICATION_MODAL, NULL);
    XmStringFree(heading); XmStringFree(mask);
    XtUnmanageChild(XmFileSelectionBoxGetChild(choice->dialog, XmDIALOG_HELP_BUTTON));
    choice->next = view->choices; view->choices = choice;
    XtAddCallback(choice->dialog, XmNokCallback, choice_ok, choice);
    XtAddCallback(choice->dialog, XmNcancelCallback, choice_cancel, choice);
    XtAddCallback(choice->dialog, XtNdestroyCallback, choice_destroyed, choice);
    if (view->palette_valid)
        palette_widget(choice->dialog, view->pixels);
    font_widget(choice->dialog, view->native_font);
    tl_editor_watch_tree(view->editors,choice->dialog,"file-dialog");
    tl_ui_file_dialog_hints(choice->dialog);
    if(directory) {
        label_set(XmFileSelectionBoxGetChild(choice->dialog,XmDIALOG_FILE_LIST_LABEL),"Pastas");
        tl_ui_hint(XmFileSelectionBoxGetChild(choice->dialog,XmDIALOG_TEXT),
                   "Pasta que contém os arquivos certificados da base; não escolha o diretório geral da geração. Undo/Redo e atalhos de texto disponíveis.");
    }
    Widget tip=XmToolTipGetLabel(XtParent(choice->dialog));
    font_widget(tip,view->native_font);
    if(view->palette_valid)palette_widget(tip,view->pixels);
    XtManageChild(choice->dialog);
}

void tl_view_choose_file(TLView *view, const char *title, const char *initial,
                        TLFileChosen chosen, void *context) {
    choose_path(view,title,initial,chosen,context,0);
}
void tl_view_choose_directory(TLView *view, const char *title, const char *initial,
                             TLFileChosen chosen, void *context) {
    choose_path(view,title,initial,chosen,context,1);
}

void tl_view_export_review(TLView *view,const char *text)
{
    if(view)tl_export_review_open(view->export_review,text);
}

void tl_view_destroy(TLView *view)
{
    Display *display;
    Colormap colormap;
    Atom delete_window;
    int i;
    if (view == NULL)
        return;
    tl_manual_paint_view_close(view->manual_paint);
    for (i = 0; i < TL_CONTROL_COUNT; ++i) {
        if (view->paint_motif_samples[i])
            XDestroyImage(view->paint_motif_samples[i]);
        if (view->paint_native_samples[i])
            XDestroyImage(view->paint_native_samples[i]);
    }
    if (view->paint_reference_sample)
        XDestroyImage(view->paint_reference_sample);
    tl_gtk2_r584_catalog_free(view->paint_r584_catalog);
    tl_gtk4_focus_destroy(view->gtk4_focus);
    tl_catalog_destroy(view->catalog);
    display = XtDisplay(view->shell);
    if (view->selection_work) XtRemoveWorkProc(view->selection_work);
    if (view->dragging && view->drag_widget != NULL) XtUngrabPointer(view->drag_widget, CurrentTime);
    embed_unregister(view, view->embedded_child);
    embed_unregister(view, view->embedded_candidate);
    XtRemoveEventHandler(view->shell, FocusChangeMask, False, embed_event, view);
    XtVaGetValues(view->shell, XtNcolormap, &colormap, NULL);
    delete_window = XmInternAtom(display, "WM_DELETE_WINDOW", False);
    XmRemoveWMProtocolCallback(view->shell, delete_window, action_callback, &view->bindings[ACTION_COUNT]);
    while (view->choices != NULL)
        XtDestroyWidget(XtParent(view->choices->dialog));
    XtDestroyWidget(XtParent(view->reference_dialog));
    tl_help_destroy(view->help);
    tl_export_review_destroy(view->export_review);
    XtDestroyWidget(view->root);
    if (view->reference_image != NULL)
        XDestroyImage(view->reference_image);
    if (view->reference_gc != NULL)
        XFreeGC(display, view->reference_gc);
    if (view->preview_font != NULL)
        XmFontListFree(view->preview_font);
    if (view->reference_font != NULL)
        XmFontListFree(view->reference_font);
    if (view->native_font != NULL)
        XmFontListFree(view->native_font);
    for (i = 0; i < COLOR_COUNT; ++i)
        if (view->pixel_allocated[i])
            XFreeColors(display, colormap, &view->pixels[i], 1, 0);
    for (i = 0; i < COLOR_COUNT; ++i)
        if (view->header_pixel_allocated[i])
            XFreeColors(display, colormap, &view->header_pixels[i], 1, 0);
    for (i = 0; i < COLOR_COUNT; ++i)
        if (view->preview_pixel_allocated[i])
            XFreeColors(display, colormap, &view->preview_pixels[i], 1, 0);
    for (i = 0; i < COLOR_COUNT; ++i)
        if (view->reference_pixel_allocated[i])
            XFreeColors(display, colormap, &view->reference_pixels[i], 1, 0);
    tl_editor_store_free(view->editors);
    free(view);
}

int tl_view_editor_open(TLView *view,const char *path,char *error,size_t capacity) {
    return tl_editor_store_load(view->editors,path,error,capacity);
}
int tl_view_editor_checkpoint(TLView *view,char *error,size_t capacity) {
    return tl_editor_checkpoint(view->editors,error,capacity);
}

void tl_view_history_state(TLView *view,int undo,int redo,int point) {
    if (!view) return;
    tl_history_controls_state(view->history_controls,undo,redo,point);
    if (view->history_menu_items[0]) XtSetSensitive(view->history_menu_items[0], undo);
    if (view->history_menu_items[1]) XtSetSensitive(view->history_menu_items[1], redo);
    if (view->history_menu_items[3]) XtSetSensitive(view->history_menu_items[3], point);
}
