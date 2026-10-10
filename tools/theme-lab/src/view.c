/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Native Motif View. The controller owns the model, actions and persistence. */
#include "theme_lab.h"

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
#include <Xm/SpinB.h>
#include <Xm/ArrowB.h>
#include <Xm/LabelG.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <png.h>
#include <errno.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

enum { FACE, TEXT, VIEW, SELECTION, LIGHT, SHADOW, TROUGH, COLOR_COUNT };
enum { PREVIEW_COUNT = TL_CONTROL_COUNT, ACTION_COUNT = 9, SCHEME_LIMIT = 128 };
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

typedef struct FileChoice {
    struct TLView *view;
    Widget dialog;
    TLFileChosen chosen;
    void *context;
    struct FileChoice *next;
} FileChoice;

struct TLView {
    Widget shell, root, family_combo, scheme_combo, name, reference_path;
    Widget fields[TL_FIELD_COUNT], factors[3], roles[4], notes;
    Widget automatic, delay, separate, categories[TL_CATEGORY_COUNT], controls_list;
    Widget edit_state, position[2], size[2], control_label, code, canvas, canvas_notice;
    Widget status, capability, pick_summary, preview_notice;
    Widget preview_form, preview_frame, preview_menu, preview_widgets[PREVIEW_COUNT];
    Widget reference_area, reference_notice, reference_dialog;
    Widget motif_reference_form, motif_reference_frame, motif_reference_notice;
    Widget motif_reference_widgets[TL_CONTROL_COUNT];
    int preview_sizes[TL_CONTROL_COUNT][2], reference_sizes[TL_CONTROL_COUNT][2];
    Dimension preview_base_sizes[TL_CONTROL_COUNT][2], reference_base_sizes[TL_CONTROL_COUNT][2];
    ActionBinding bindings[ACTION_COUNT + 1];
    ControlBinding control_bindings[TL_CONTROL_COUNT];
    TLDispatch dispatch;
    void *context;
    TLModel snapshot;
    int has_model, updating;
    char capabilities[TL_FAMILY_COUNT][TL_TEXT_MAX];
    Pixel pixels[COLOR_COUNT];
    unsigned short rgb[6][3];
    int palette_valid, pixel_allocated[COLOR_COUNT];
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

static int number_read(Widget widget, int integer, double *result);

static void number_set(Widget field, double value)
{
    short digits = 0;
    int minimum, maximum, position;
    XtVaGetValues(field, XmNdecimalPoints, &digits, XmNminimumValue, &minimum,
                  XmNmaximumValue, &maximum, NULL);
    position = (int)lround(value * (digits ? 10000.0 : 1.0));
    if (position < minimum) position = minimum;
    if (position > maximum) position = maximum;
    XtVaSetValues(field, XmNposition, position, NULL);
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
    char wrapped[TL_TEXT_MAX * 2];
    size_t input = 0, output = 0, last_space = 0;
    unsigned int line = 0;
    if (text == NULL) text = "";
    while (text[input] != '\0' && output + 1 < sizeof(wrapped)) {
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

static void family_callback(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view = (TLView *)client;
    XmComboBoxCallbackStruct *event = (XmComboBoxCallbackStruct *)call;
    int family = event->item_position;
    (void)widget;
    if (!view->updating && family >= 0 && family < TL_FAMILY_COUNT &&
        view->dispatch != NULL)
        view->dispatch(view->context, TL_SELECT_FAMILY, family);
}

static void changed_callback(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view = (TLView *)client;
    (void)widget; (void)call;
    if (!view->updating && view->dispatch != NULL)
        view->dispatch(view->context, TL_CHANGED, 0);
}

static void selected_control_callback(Widget widget, XtPointer client, XtPointer call)
{
    TLView *view = (TLView *)client;
    XmListCallbackStruct *event = (XmListCallbackStruct *)call;
    int control = event->item_position - 1;
    (void)widget;
    if (!view->updating && view->dispatch != NULL && control >= 0 && control < TL_CONTROL_COUNT) {
        view->dispatch(view->context, TL_SELECT_CONTROL, control);
        view->dispatch(view->context, TL_CHANGED, 0);
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
    previous = view->updating; view->updating = 1;
    for (i = 0; i < 2; ++i) {
        (void)snprintf(text, sizeof(text), "%d", coordinates[i]);
        XmTextFieldSetString(view->position[i], text);
    }
    XtVaSetValues(view->preview_widgets[view->drag_control],
                   XmNx, coordinates[0], XmNy, coordinates[1], NULL);
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
            Position x, y;
            *continue_dispatch = False;
            if (view->selection_work) {
                XtRemoveWorkProc(view->selection_work); view->selection_work = 0;
            }
            view->pending_control = -1;
            view->dispatch(view->context, TL_SELECT_CONTROL, binding->control);
            if (!view->has_model || view->snapshot.recipes[view->snapshot.selected].selected_control != binding->control)
                return;
            XtVaGetValues(view->preview_widgets[binding->control], XmNx, &x, XmNy, &y, NULL);
            if (XtGrabPointer(widget, False, PointerMotionMask | ButtonReleaseMask,
                              GrabModeAsync, GrabModeAsync, None, None, event->xbutton.time) != GrabSuccess) {
                tl_view_status(view, "Não foi possível capturar o ponteiro para mover o controle.");
                return;
            }
            view->dragging = 1; view->drag_widget = widget; view->drag_control = binding->control;
            view->drag_origin[0] = x; view->drag_origin[1] = y;
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
    if (view->embedded_child != None) {
        XtUnmanageChild(view->canvas_notice);
        label_set(view->preview_notice,
          "GTK3 nativo acoplado.\nCtrl+clique seleciona; Ctrl+arraste move; entrada nativa.");
    } else if (view->preview_family != TL_MOTIF) {
        XtManageChild(view->canvas_notice);
        label_set(view->preview_notice,
          "Prévia nativa da família pelo controller.\nBackend acoplado ainda não mapeado neste canvas.");
    }
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
    XmFontListEntry entry = XmFontListEntryLoad(XtDisplay(view->shell), (char *)pattern,
                                  XmFONT_IS_FONTSET, _MOTIF_DEFAULT_LOCALE);
    XmFontList list;
    if (entry == NULL) return NULL;
    list = XmFontListAppendEntry(NULL, entry);
    XmFontListEntryFree(&entry);
    return list;
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
    char request[768], size[32];
    const char *cursor = view->native_xlfd;
    size_t used = 0;
    int component = 0;
    XmFontList list = NULL;
    if (pixels > 0 && cursor[0] == '-') {
        while (*cursor != '\0' && used + 2 < sizeof(request)) {
            const char *end;
            size_t length;
            request[used++] = *cursor++;
            end = strchr(cursor, '-');
            length = end != NULL ? (size_t)(end - cursor) : strlen(cursor);
            ++component;
            if (component >= 7) {
                int count = component == 7 ? snprintf(size, sizeof(size), "%d", pixels) : 1;
                /* Remaining fields are wildcarded: a FontSet must select
                 * encodings for the locale rather than one ISO-8859-1 font. */
                if (component != 7) { size[0] = '*'; size[1] = '\0'; count = 1; }
                if (count < 0 || used + (size_t)count >= sizeof(request)) break;
                memcpy(request + used, size, (size_t)count); used += (size_t)count;
            } else {
                if (used + length >= sizeof(request)) break;
                memcpy(request + used, cursor, length); used += length;
            }
            cursor += length;
        }
        request[used] = '\0';
        if (*cursor == '\0') list = fontset_load(view, request);
    }
    return list;
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
    static const char *const options[] = { "Opção A", "Opção B", "Opção C" };
    XmString entries[3];
    int i;
    widgets[0] = XtVaCreateManagedWidget("nativePushButton",
          xmPushButtonWidgetClass, form, NULL);
    label_set(widgets[0], "PushButton");
    widgets[1] = XtVaCreateManagedWidget("nativeToggleButton",
          xmToggleButtonWidgetClass, form, XmNindicatorOn, False, NULL);
    label_set(widgets[1], "Alternável");
    widgets[2] = XtVaCreateManagedWidget("nativeCheckButton",
          xmToggleButtonWidgetClass, form, XmNset, True, NULL);
    label_set(widgets[2], "CheckBox");
    widgets[3] = XtVaCreateManagedWidget("nativeRadioButton",
          xmToggleButtonWidgetClass, form, XmNindicatorType, XmONE_OF_MANY,
          XmNset, True, NULL);
    label_set(widgets[3], "RadioButton");
    widgets[4] = XtVaCreateManagedWidget("nativeTextField",
          xmTextFieldWidgetClass, form, XmNcolumns, 14,
          XmNvalue, "Texto / seleção", NULL);
    widgets[5] = combo_new(form, "nativeComboBox", options, 3);
    widgets[6] = XtVaCreateManagedWidget("nativeSpinBox",
          xmSpinBoxWidgetClass, form, NULL);
    spin_text = XtVaCreateManagedWidget("nativeSpinValue", xmTextFieldWidgetClass,
          widgets[6], XmNspinBoxChildType, XmNUMERIC, XmNminimumValue, 0,
          XmNmaximumValue, 100, XmNposition, 25, XmNcolumns, 5, NULL);
    (void)spin_text;
    widgets[7] = XtVaCreateManagedWidget("nativeMultilineText",
          xmTextWidgetClass, form, XmNeditMode, XmMULTI_LINE_EDIT,
          XmNrows, 3, XmNcolumns, 14, XmNwordWrap, True, NULL);
    XmTextSetString(widgets[7], "Texto multilinha\nMotif nativo");
    widgets[8] = XtVaCreateManagedWidget("nativeHorizontalScale",
          xmScaleWidgetClass, form, XmNorientation, XmHORIZONTAL,
          XmNminimum, 0, XmNmaximum, 100, XmNvalue, 38, XmNshowValue, True,
          XmNscaleWidth, 135, NULL);
    widgets[9] = XtVaCreateManagedWidget("nativeVerticalScale",
          xmScaleWidgetClass, form, XmNorientation, XmVERTICAL,
          XmNminimum, 0, XmNmaximum, 100, XmNvalue, 62, XmNshowValue, True,
          XmNscaleHeight, 66, NULL);
    widgets[10] = XtVaCreateManagedWidget("nativeHorizontalScrollBar",
          xmScrollBarWidgetClass, form, XmNorientation, XmHORIZONTAL,
          XmNminimum, 0, XmNmaximum, 100, XmNvalue, 35, XmNsliderSize, 20, NULL);
    widgets[11] = XtVaCreateManagedWidget("nativeVerticalScrollBar",
          xmScrollBarWidgetClass, form, XmNorientation, XmVERTICAL,
          XmNminimum, 0, XmNmaximum, 100, XmNvalue, 35, XmNsliderSize, 20,
          XmNheight, 65, NULL);
    widgets[12] = XtVaCreateManagedWidget("nativeArrowButton",
          xmArrowButtonWidgetClass, form, XmNarrowDirection, XmARROW_DOWN, NULL);
    /* Standard Motif has no ProgressBar class. A read-only Scale is explicitly
     * identified as the native level substitute; GTK gets a real ProgressBar. */
    widgets[13] = XtVaCreateManagedWidget("nativeLevelScale",
          xmScaleWidgetClass, form, XmNorientation, XmHORIZONTAL,
          XmNminimum, 0, XmNmaximum, 100, XmNvalue, 60, XmNshowValue, True,
          XmNsensitive, False, XmNscaleWidth, 125, NULL);
    entries[0] = compound("Item normal"); entries[1] = compound("Selecionado"); entries[2] = compound("Outro item");
    list = XtVaCreateManagedWidget("nativeList", xmListWidgetClass, form,
          XmNitems, entries, XmNitemCount, 3, XmNvisibleItemCount, 3,
          XmNselectionPolicy, XmSINGLE_SELECT, NULL);
    widgets[14] = list;
    XmListSelectPos(list, 2, False);
    for (i = 0; i < 3; ++i) XmStringFree(entries[i]);
    widgets[15] = XtVaCreateManagedWidget("nativeControlFrame", xmFrameWidgetClass,
          form, XmNshadowType, XmSHADOW_IN, XmNshadowThickness, 2, NULL);
    inner = label_new(widgets[15], "frameCaption", "XmFrame");
    XtVaSetValues(inner, XmNwidth, 110, XmNheight, 40, NULL);
    for (i = 0; i < TL_CONTROL_COUNT; ++i)
        XtVaSetValues(widgets[i], XmNleftAttachment, XmATTACH_NONE,
                      XmNtopAttachment, XmATTACH_NONE,
                      XmNx, 16 + (i % 4) * 160, XmNy, 16 + (i / 4) * 80,
                      XmNwidth, i == 9 || i == 11 ? 35 : 135, NULL);
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
    view->preview_form = XtVaCreateManagedWidget("nativePreviewControls", xmFormWidgetClass,
          view->canvas, XmNwidth, 740, XmNheight, 410, XmNresizePolicy, XmRESIZE_NONE, NULL);
    view->canvas_notice = label_new(view->canvas, "canvasCapability",
         "Esta família utiliza seu próprio backend nativo.\nAbra a prévia da família; embedding ainda não confirmado.");
    XtVaSetValues(view->canvas_notice, XmNx, 12, XmNy, 12,
                   XmNwidth, 480, XmNheight, 65, NULL);
    XtUnmanageChild(view->canvas_notice);
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
        XtVaSetValues(view->shell, XmNbackground, view->pixels[FACE], NULL);
    }
    if (view->preview_palette_valid) {
        colors_allocate(view, view->preview_rgb, view->preview_trough,
                        view->preview_pixels, view->preview_pixel_allocated);
        /* Keep tools/headers/code on the current palette, even when testing a
         * different selectable scheme in this one preview area. */
        palette_widget(view->preview_form, view->preview_pixels);
    }
    if (view->reference_palette_valid) {
        colors_allocate(view, view->reference_rgb, view->reference_trough,
                        view->reference_pixels, view->reference_pixel_allocated);
        palette_widget(view->motif_reference_form, view->reference_pixels);
    }
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

/* The reference has its own recipe. GTK geometry and pointer events never
 * mutate it; the installed Motif widgets supply their native interaction. */
static void motif_reference_scene(TLView *view, const TLModel *model)
{
    const TLRecipe *recipe = &model->recipes[TL_MOTIF];
    const TLGeometry *geometry = &recipe->geometry;
    const TLRecipe *editing = &model->recipes[model->selected];
    Dimension width = 740, height = 410;
    char notice[256];
    int i;
    view->reference_trough = recipe->palette.trough;
    XtVaSetValues(view->motif_reference_frame, XmNshadowThickness, geometry->shadow_px,
                  XmNmarginWidth, geometry->view_bar_gap_px,
                  XmNmarginHeight, geometry->view_bar_gap_px, NULL);
    XtVaSetValues(view->motif_reference_form, XmNmarginWidth, geometry->view_inset_px,
                  XmNmarginHeight, geometry->view_inset_px, NULL);
    for (i = 0; i < TL_CONTROL_COUNT; ++i) {
        Widget widget = view->motif_reference_widgets[i];
        Dimension item_width, item_height;
        int visible = (editing->visible_controls & (1 << i)) &&
                      (editing->visible_categories & (1 << control_category[i]));
        XtVaSetValues(widget, XmNx, recipe->positions[i][0], XmNy, recipe->positions[i][1],
                      XmNsensitive, i != 13, NULL);
        if (visible) XtManageChild(widget); else XtUnmanageChild(widget);
        XtVaGetValues(widget, XmNwidth, &item_width, XmNheight, &item_height, NULL);
        if (recipe->positions[i][0] + item_width + 12U > width)
            width = (Dimension)(recipe->positions[i][0] + item_width + 12U);
        if (recipe->positions[i][1] + item_height + 12U > height)
            height = (Dimension)(recipe->positions[i][1] + item_height + 12U);
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
        XtVaGetValues(view->motif_reference_widgets[i], XmNwidth, &item_width, XmNheight, &item_height, NULL);
        if (recipe->positions[i][0] + item_width + 12U > width)
            width = (Dimension)(recipe->positions[i][0] + item_width + 12U);
        if (recipe->positions[i][1] + item_height + 12U > height)
            height = (Dimension)(recipe->positions[i][1] + item_height + 12U);
    }
    XtVaSetValues(view->motif_reference_form, XmNwidth, width, XmNheight, height, NULL);
    (void)snprintf(notice, sizeof(notice),
          "Referência Motif: %s.\nReceita independente; pressione os controles. Nível usa Scale.",
          control_labels[editing->selected_control]);
    label_set(view->motif_reference_notice, notice);
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
    int i;
    Dimension width = 740, height = 410;
    control_sizes(view->preview_widgets, recipe, view->preview_sizes, view->preview_base_sizes);
    for (i = 0; i < TL_CONTROL_COUNT; ++i) {
        Widget widget = view->preview_widgets[i];
        Dimension widget_width, widget_height;
        int visible = (recipe->visible_controls & (1 << i)) &&
                      (recipe->visible_categories & (1 << control_category[i]));
        XtVaSetValues(widget, XmNx, recipe->positions[i][0], XmNy, recipe->positions[i][1],
                      XmNsensitive, i != 13 && !(i == recipe->selected_control && recipe->edit_state == 2), NULL);
        if (visible) XtManageChild(widget); else XtUnmanageChild(widget);
        XtVaGetValues(widget, XmNwidth, &widget_width, XmNheight, &widget_height, NULL);
        if ((unsigned int)recipe->positions[i][0] + widget_width + 12 > width)
            width = (Dimension)(recipe->positions[i][0] + widget_width + 12);
        if ((unsigned int)recipe->positions[i][1] + widget_height + 12 > height)
            height = (Dimension)(recipe->positions[i][1] + widget_height + 12);
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
        "Exportar", "Imagem histórica", "Restaurar família", "Sair"
    };
    static const TLAction actions[ACTION_COUNT] = {
        TL_APPLY, TL_SAVE, TL_LOAD, TL_PICK, TL_PREVIEW,
        TL_EXPORT, TL_REFERENCE, TL_RESET, TL_QUIT
    };
    static const char *const initial_schemes[] = { "Esquema KDE atual" };
    TLView *view = (TLView *)calloc(1, sizeof(*view));
    Widget body, editor_scroll, editor, preview_scroll, previews, code_group;
    Widget group, category_row, reference_frame, reference_scroll, bottom, action_row;
    XmString control_items[TL_CONTROL_COUNT];
    Arg list_args[4];
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
                    XmNfractionBase, 100, XmNmarginWidth, 7, XmNmarginHeight, 7, NULL);
    bottom = XtVaCreateManagedWidget("viewFooter", xmRowColumnWidgetClass, view->root,
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
        view->bindings[i].view = view; view->bindings[i].action = actions[i];
        XtAddCallback(button, XmNactivateCallback, action_callback, &view->bindings[i]);
    }
    view->status = label_new(bottom, "controllerStatus", "Pronto. Edição privada de receitas.");
    XtVaSetValues(view->status, XmNrecomputeSize, False, XmNwidth, 1200, NULL);
    body = XtVaCreateManagedWidget("threePanels", xmFormWidgetClass, view->root,
          XmNfractionBase, 100, XmNleftAttachment, XmATTACH_FORM,
          XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_FORM,
          XmNbottomAttachment, XmATTACH_WIDGET, XmNbottomWidget, bottom, XmNbottomOffset, 6, NULL);
    editor_scroll = XtVaCreateManagedWidget("recipeScroll", xmScrolledWindowWidgetClass, body,
          XmNscrollingPolicy, XmAUTOMATIC, XmNscrollBarDisplayPolicy, XmAS_NEEDED,
          XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_POSITION,
          XmNrightPosition, 33, XmNtopAttachment, XmATTACH_FORM,
          XmNbottomAttachment, XmATTACH_FORM, NULL);
    editor = XtVaCreateManagedWidget("recipeEditor", xmRowColumnWidgetClass, editor_scroll,
          XmNorientation, XmVERTICAL, XmNpacking, XmPACK_TIGHT,
          XmNspacing, 6, XmNmarginWidth, 4, XmNmarginHeight, 4, XmNwidth, 380, NULL);
    (void)label_new(editor, "toolsHeading", "Ferramentas / receita da família");
    (void)label_new(editor, "familyHeading", "Família de controles");
    view->family_combo = combo_new(editor, "familyCombo", tl_family_labels, TL_FAMILY_COUNT);
    XtAddCallback(view->family_combo, XmNselectionCallback, family_callback, view);
    (void)label_new(editor, "schemeHeading", "Esquema usado apenas na prévia");
    view->scheme_combo = combo_new(editor, "schemeCombo", initial_schemes, 1);
    XtAddCallback(view->scheme_combo, XmNselectionCallback, changed_callback, view);
    view->automatic = XtVaCreateManagedWidget("automaticPreview", xmToggleButtonWidgetClass, editor, NULL);
    label_set(view->automatic, "Atualização automática");
    XtAddCallback(view->automatic, XmNvalueChangedCallback, changed_callback, view);
    view->separate = XtVaCreateManagedWidget("separatePreview", xmToggleButtonWidgetClass, editor, NULL);
    label_set(view->separate, "Mostrar prévia separada");
    XtAddCallback(view->separate, XmNvalueChangedCallback, separate_callback, view);
    number_row(view, editor, "delayRow", "Intervalo da prévia (ms)", 7, &view->delay, 100, 10000, 100, 0);
    XtAddCallback(view->delay, XmNvalueChangedCallback, changed_callback, view);
    group = section(editor, "visibleCategories", "Categorias visíveis");
    category_row = XtVaCreateManagedWidget("categoryChecks", xmRowColumnWidgetClass, group,
          XmNorientation, XmHORIZONTAL, XmNpacking, XmPACK_COLUMN, XmNnumColumns, 3, NULL);
    for (i = 0; i < TL_CATEGORY_COUNT; ++i) {
        view->categories[i] = XtVaCreateManagedWidget("visibleCategory", xmToggleButtonWidgetClass,
                                    category_row, XmNset, True, NULL);
        label_set(view->categories[i], category_labels[i]);
        XtAddCallback(view->categories[i], XmNvalueChangedCallback, changed_callback, view);
    }
    group = section(editor, "visibleControls", "Controles visíveis — seleção múltipla");
    for (i = 0; i < TL_CONTROL_COUNT; ++i) control_items[i] = compound(control_labels[i]);
    XtSetArg(list_args[0], XmNitems, control_items);
    XtSetArg(list_args[1], XmNitemCount, TL_CONTROL_COUNT);
    XtSetArg(list_args[2], XmNvisibleItemCount, 5);
    XtSetArg(list_args[3], XmNselectionPolicy, XmEXTENDED_SELECT);
    view->controls_list = XmCreateScrolledList(group, "controlsList", list_args, 4);
    XtManageChild(view->controls_list);
    for (i = 0; i < TL_CONTROL_COUNT; ++i) XmStringFree(control_items[i]);
    XtAddCallback(view->controls_list, XmNextendedSelectionCallback, selected_control_callback, view);
    group = section(editor, "controlEdit", "Controle selecionado / posição no canvas");
    view->control_label = label_new(group, "selectedControl", "Controle em edição: botão");
    (void)label_new(group, "stateHeading", "Estado em edição");
    view->edit_state = combo_new(group, "editState", state_labels, 4);
    XtAddCallback(view->edit_state, XmNselectionCallback, changed_callback, view);
    number_row(view, group, "positionX", "Posição X (px)", 6, &view->position[0], 0, 2048, 1, 0);
    number_row(view, group, "positionY", "Posição Y (px)", 6, &view->position[1], 0, 2048, 1, 0);
    for (i = 0; i < 2; ++i) XtAddCallback(view->position[i], XmNvalueChangedCallback, changed_callback, view);
    number_row(view, group, "controlWidth", "Largura (0 = automática)", 6, &view->size[0], 0, 2048, 1, 0);
    number_row(view, group, "controlHeight", "Altura (0 = automática)", 6, &view->size[1], 0, 2048, 1, 0);
    for (i = 0; i < 2; ++i) XtAddCallback(view->size[i], XmNvalueChangedCallback, changed_callback, view);
    view->capability = label_new(editor, "familyCapability", "Aguardando inventário nativo.");
    XtVaSetValues(view->capability, XmNrecomputeSize, False, XmNwidth, 360, XmNheight, 75, NULL);
    (void)field_row(editor, "modelNameRow", "Nome do modelo", 18, &view->name);
    XtVaSetValues(view->name, XmNmaxLength, 255, NULL);
    XtAddCallback(view->name, XmNvalueChangedCallback, changed_callback, view);
    (void)field_row(editor, "referencePathRow", "Referência PNG", 18, &view->reference_path);
    XtVaSetValues(view->reference_path, XmNmaxLength, TL_PATH_MAX - 1, NULL);
    XtAddCallback(view->reference_path, XmNvalueChangedCallback, changed_callback, view);
    group = section(editor, "geometryFields", "Geometria — pixels");
    for (i = 0; i < TL_FIELD_COUNT; ++i) {
        number_row(view, group, tl_field_ids[i], tl_field_labels[i], 6, &view->fields[i],
                   i == 8 ? 6 : 0, i == 8 ? 48 : (i == 0 ? 127 : 128),
                   i == 0 || i == 2 || i == 3 ? 2 : 1, 0);
        XtAddCallback(view->fields[i], XmNvalueChangedCallback, changed_callback, view);
    }
    group = section(editor, "paletteFields", "Papéis e fatores do esquema KDE");
    for (i = 0; i < 3; ++i) {
        number_row(view, group, "factorRow", factor_labels[i], 8, &view->factors[i], 0, 10000, 100, 4);
        XtAddCallback(view->factors[i], XmNvalueChangedCallback, changed_callback, view);
    }
    for (i = 0; i < 4; ++i) {
        (void)field_row(group, "roleRow", role_labels[i], 16, &view->roles[i]);
        XtAddCallback(view->roles[i], XmNvalueChangedCallback, changed_callback, view);
    }
    group = section(editor, "recipeNotes", "Notas / limites da adaptação");
    view->notes = XtVaCreateManagedWidget("notesText", xmTextWidgetClass, group,
         XmNeditMode, XmMULTI_LINE_EDIT, XmNrows, 4, XmNcolumns, 28,
         XmNwordWrap, True, XmNmaxLength, 2047, NULL);
    XtAddCallback(view->notes, XmNvalueChangedCallback, changed_callback, view);
    view->pick_summary = label_new(editor, "pickSummary", "Pipeta: sem amostra.");
    XtVaSetValues(view->pick_summary, XmNrecomputeSize, False, XmNwidth, 360, XmNheight, 110, NULL);
    preview_scroll = XtVaCreateManagedWidget("previewScroll", xmScrolledWindowWidgetClass, body,
          XmNscrollingPolicy, XmAUTOMATIC, XmNscrollBarDisplayPolicy, XmAS_NEEDED,
          XmNleftAttachment, XmATTACH_POSITION, XmNleftPosition, 33, XmNleftOffset, 5,
          XmNrightAttachment, XmATTACH_POSITION, XmNrightPosition, 75, XmNrightOffset, 5,
          XmNtopAttachment, XmATTACH_FORM, XmNbottomAttachment, XmATTACH_FORM, NULL);
    previews = XtVaCreateManagedWidget("previewStack", xmRowColumnWidgetClass, preview_scroll,
          XmNorientation, XmVERTICAL, XmNpacking, XmPACK_TIGHT,
          XmNspacing, 7, XmNmarginWidth, 4, XmNmarginHeight, 4, NULL);
    preview_create(view, previews);
    reference_frame = XtVaCreateManagedWidget("motifReferenceFrame", xmFrameWidgetClass, previews,
          XmNshadowType, XmSHADOW_IN, XmNshadowThickness, 2, NULL);
    view->motif_reference_frame = reference_frame;
    group = XtVaCreateManagedWidget("referenceGroup", xmRowColumnWidgetClass, reference_frame,
          XmNorientation, XmVERTICAL, XmNpacking, XmPACK_TIGHT, NULL);
    view->motif_reference_notice = label_new(group, "motifReferenceNotice",
          "Referência Motif — controles reais da biblioteca instalada.");
    XtVaSetValues(view->motif_reference_notice, XmNrecomputeSize, False,
                  XmNwidth, 500, XmNheight, 40, NULL);
    reference_scroll = XtVaCreateManagedWidget("motifReferenceScroll", xmScrolledWindowWidgetClass, group,
          XmNscrollingPolicy, XmAUTOMATIC, XmNscrollBarDisplayPolicy, XmAS_NEEDED,
          XmNwidth, 510, XmNheight, 240, NULL);
    view->motif_reference_form = XtVaCreateManagedWidget("motifReferenceControls", xmFormWidgetClass,
          reference_scroll, XmNwidth, 740, XmNheight, 410, XmNresizePolicy, XmRESIZE_NONE, NULL);
    motif_controls_create(view->motif_reference_form, view->motif_reference_widgets);
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
    code_group = XtVaCreateManagedWidget("codePanel", xmFormWidgetClass, body,
          XmNleftAttachment, XmATTACH_POSITION, XmNleftPosition, 75,
          XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_FORM,
          XmNbottomAttachment, XmATTACH_FORM, NULL);
    group = label_new(code_group, "codeHeading", "Código da proposta — somente leitura");
    XtVaSetValues(group, XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM,
                  XmNtopAttachment, XmATTACH_FORM, NULL);
    view->code = XmCreateScrolledText(code_group, "proposalCode", NULL, 0);
    XtVaSetValues(view->code, XmNeditMode, XmMULTI_LINE_EDIT, XmNeditable, False,
                  XmNcursorPositionVisible, False, XmNwordWrap, False,
                  XmNscrollHorizontal, True, XmNscrollVertical, True, NULL);
    XtVaSetValues(XtParent(view->code), XmNleftAttachment, XmATTACH_FORM,
                  XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment, XmATTACH_WIDGET,
                  XmNtopWidget, group, XmNtopOffset, 4, XmNbottomAttachment, XmATTACH_FORM, NULL);
    XtManageChild(view->code);
    XmTextSetString(view->code, "/* O controller mostra aqui a proposta vigente. */");
    remember_native_font(view);
    delete_window = XmInternAtom(XtDisplay(shell), "WM_DELETE_WINDOW", False);
    view->bindings[ACTION_COUNT].view = view; view->bindings[ACTION_COUNT].action = TL_QUIT;
    XmAddWMProtocolCallback(shell, delete_window, action_callback, &view->bindings[ACTION_COUNT]);
    return view;
}

void tl_view_update(TLView *view, const TLModel *model)
{
    const TLRecipe *recipe;
    const char *roles[4];
    double factors[3];
    char value[128], pick[768];
    int i;
    if (view == NULL || model == NULL || model->selected < 0 || model->selected >= TL_FAMILY_COUNT)
        return;
    view->updating = 1;
    view->snapshot = *model; view->has_model = 1;
    recipe = &model->recipes[model->selected];
    XmTextFieldSetString(view->name, (char *)model->name);
    XmTextFieldSetString(view->reference_path, (char *)model->reference);
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
    number_set(view->delay, model->debounce_ms);
    for (i = 0; i < TL_CATEGORY_COUNT; ++i)
        XmToggleButtonSetState(view->categories[i], (recipe->visible_categories & (1 << i)) != 0, False);
    {
        int positions[TL_CONTROL_COUNT], count = 0;
        for (i = 0; i < TL_CONTROL_COUNT; ++i)
            if (recipe->visible_controls & (1 << i)) positions[count++] = i + 1;
        XmListDeselectAllItems(view->controls_list);
        /* SelectPos replaces the selection under EXTENDED_SELECT.  Set all
         * positions together; Motif copies the array during SetValues. */
        if (count > 0)
            XtVaSetValues(view->controls_list, XmNselectedPositions, positions,
                          XmNselectedPositionCount, count, NULL);
    }
    XtVaSetValues(view->edit_state, XmNselectedPosition, recipe->edit_state, NULL);
    for (i = 0; i < 2; ++i) {
        number_set(view->position[i], recipe->positions[recipe->selected_control][i]);
        number_set(view->size[i], recipe->sizes[recipe->selected_control][i]);
    }
    (void)snprintf(value, sizeof(value), "Em edição: %s", control_labels[recipe->selected_control]);
    label_set(view->control_label, value);
    for (i = 0; i < TL_FIELD_COUNT; ++i) {
        number_set(view->fields[i], tl_model_geometry_get(&recipe->geometry, i));
    }
    factors[0] = recipe->palette.light; factors[1] = recipe->palette.shade; factors[2] = recipe->palette.trough;
    for (i = 0; i < 3; ++i) {
        number_set(view->factors[i], factors[i]);
    }
    roles[0] = recipe->palette.face_role; roles[1] = recipe->palette.text_role;
    roles[2] = recipe->palette.view_role; roles[3] = recipe->palette.selection_role;
    for (i = 0; i < 4; ++i)
        XmTextFieldSetString(view->roles[i], (char *)roles[i]);
    XmTextSetString(view->notes, (char *)recipe->notes);
    label_wrapped(view->capability, view->capabilities[model->selected][0] != '\0' ?
             view->capabilities[model->selected] : "Sem informação de capacidade.", 48);
    if (model->picked.valid)
        (void)snprintf(pick, sizeof(pick),
             "Pipeta (%d, %d)\nRGB16: %u / %u / %u\nRGB8: %u / %u / %u\nVisual: 0x%lx\nUso: %s\n%s",
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
    view->updating = 0;
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
    view->preview_family = model->selected;
    view->preview_trough = recipe->palette.trough;
    preview_geometry(view, &recipe->geometry);
    preview_selection(view, model->selected, recipe);
    motif_reference_scene(view, model);
    palette_apply(view);
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
        int selected_scheme, state, *positions = NULL, count = 0;
        XtVaGetValues(view->scheme_combo, XmNselectedPosition, &selected_scheme, NULL);
        if (selected_scheme < 0 || selected_scheme >= view->scheme_count) {
            set_error(error, capacity, "Escolha um esquema da lista."); return -1;
        }
        (void)snprintf(parsed.color_scheme, sizeof(parsed.color_scheme), "%s", view->schemes[selected_scheme]);
        XtVaGetValues(view->edit_state, XmNselectedPosition, &state, NULL);
        recipe->edit_state = state;
        recipe->visible_categories = 0;
        for (i = 0; i < TL_CATEGORY_COUNT; ++i)
            if (XmToggleButtonGetState(view->categories[i])) recipe->visible_categories |= 1 << i;
        recipe->visible_controls = 0;
        if (XmListGetSelectedPos(view->controls_list, &positions, &count)) {
            for (i = 0; i < count; ++i)
                if (positions[i] >= 1 && positions[i] <= TL_CONTROL_COUNT)
                    recipe->visible_controls |= 1 << (positions[i] - 1);
            XtFree((char *)positions);
        }
        for (i = 0; i < 2; ++i) {
            if (!number_read(view->position[i], 1, &value) || value < 0 || value > 2048) {
                set_error(error, capacity, "Posições do canvas devem ficar entre 0 e 2048 px."); return -1;
            }
            recipe->positions[recipe->selected_control][i] = (int)value;
            if (!number_read(view->size[i], 1, &value) || value < 0 || value > 2048) {
                set_error(error, capacity, "Dimensões entre 0 e 2048 px; 0 usa tamanho automático."); return -1;
            }
            recipe->sizes[recipe->selected_control][i] = (int)value;
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
    for (i = 0; i < 3; ++i)
        if (!number_read(view->factors[i], 0, &factors[i])) {
            set_error(error, capacity, "Fator numérico inválido (luz, sombra ou trilho).");
            return -1;
        }
    recipe->palette.light = factors[0]; recipe->palette.shade = factors[1]; recipe->palette.trough = factors[2];
    roles[0] = recipe->palette.face_role; roles[1] = recipe->palette.text_role;
    roles[2] = recipe->palette.view_role; roles[3] = recipe->palette.selection_role;
    for (i = 0; i < 4; ++i)
        if (!text_copy(view->roles[i], 0, roles[i], sizeof(recipe->palette.face_role), error, capacity))
            return -1;
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
    if (view != NULL) XmTextSetString(view->code, (char *)(text != NULL ? text : ""));
}

unsigned long tl_view_canvas(TLView *view)
{
    return view != NULL && XtIsRealized(view->canvas) ? (unsigned long)XtWindow(view->canvas) : 0UL;
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
    if (view->has_model) tl_view_update(view, &view->snapshot);
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

void tl_view_choose_file(TLView *view, const char *title, const char *initial,
                         TLFileChosen chosen, void *context)
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
    XtManageChild(choice->dialog);
}

void tl_view_destroy(TLView *view)
{
    Display *display;
    Colormap colormap;
    Atom delete_window;
    int i;
    if (view == NULL)
        return;
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
        if (view->preview_pixel_allocated[i])
            XFreeColors(display, colormap, &view->preview_pixels[i], 1, 0);
    for (i = 0; i < COLOR_COUNT; ++i)
        if (view->reference_pixel_allocated[i])
            XFreeColors(display, colormap, &view->reference_pixels[i], 1, 0);
    free(view);
}
