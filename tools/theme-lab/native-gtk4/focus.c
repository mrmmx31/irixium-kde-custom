/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Explicit GTK4/Motif focus protocol. Does not emulate XEmbed. */
#include "focus.h"
#include <Xm/Xm.h>
#include <X11/Xatom.h>
#include <stdlib.h>

struct TLGTK4Focus {
    Widget canvas;
    Atom child_atom, traverse_atom, info_atom;
    Window child;
    unsigned long pid, sequence;
    int enabled, registered, saved;
    XtWorkProcId work;
    unsigned long direction;
    void (*notify)(XtPointer);
    XtPointer notify_data;
};
static int xerror;
static int catch_error(Display *display, XErrorEvent *error) {
    (void)display; xerror = error->error_code; return 0;
}
static int (*begin(Display *display))(Display *, XErrorEvent *) {
    XSync(display, False); xerror = 0;
    return XSetErrorHandler(catch_error);
}
static int end(Display *display, int (*previous)(Display *, XErrorEvent *)) {
    XSync(display, False); XSetErrorHandler(previous); return xerror == 0;
}
static int read_values(Display *display, Window window, Atom atom,
                       unsigned long *values, unsigned long count) {
    Atom type; int format;
    unsigned long length, remaining;
    unsigned char *data = NULL;
    int status = XGetWindowProperty(display, window, atom, 0, (long)count, False,
                                   XA_CARDINAL, &type, &format, &length, &remaining, &data);
    int valid = status == Success && type == XA_CARDINAL && format == 32 &&
                length == count && remaining == 0;
    if (valid)
        for (unsigned long i = 0; i < count; ++i) values[i] = ((unsigned long *)data)[i];
    if (data) XFree(data);
    return valid;
}
static int direct_child(TLGTK4Focus *focus, Window child) {
    Window root, parent, *children = NULL; unsigned int count;
    Display *display = XtDisplay(focus->canvas);
    int valid = XQueryTree(display, child, &root, &parent, &children, &count);
    if (children) XFree(children);
    return valid && parent == XtWindow(focus->canvas);
}
static void forget(TLGTK4Focus *focus) {
    if (focus->work) { XtRemoveWorkProc(focus->work); focus->work = 0; }
    if (focus->saved && focus->child) {
        Display *display = XtDisplay(focus->canvas);
        int (*previous)(Display *, XErrorEvent *) = begin(display);
        XRemoveFromSaveSet(display, focus->child);
        (void)end(display, previous);
    }
    if (focus->registered && XtWindowToWidget(XtDisplay(focus->canvas), focus->child) == focus->canvas)
        XtUnregisterDrawable(XtDisplay(focus->canvas), focus->child);
    focus->child = None; focus->registered = focus->saved = 0; focus->sequence = 0;
    if(focus->notify)focus->notify(focus->notify_data);
}
static Boolean finish_traversal(XtPointer data) {
    TLGTK4Focus *focus = data;
    focus->work = 0;
    if (!focus->enabled || !focus->child || !XtIsRealized(focus->canvas)) return True;
    Display *display = XtDisplay(focus->canvas);
    int (*previous)(Display *, XErrorEvent *) = begin(display);
    int valid = direct_child(focus, focus->child);
    int clean = end(display, previous);
    int traversed = valid && clean && XmProcessTraversal(focus->canvas,
        focus->direction == 1 ? XmTRAVERSE_NEXT_TAB_GROUP : XmTRAVERSE_PREV_TAB_GROUP);
    Widget selected = XmGetFocusWidget(focus->canvas);
    Window input; int revert;
    previous = begin(display);
    XGetInputFocus(display, &input, &revert);
    unsigned long reply[] = {1, focus->child, focus->pid, focus->sequence,
        (unsigned long)traversed, selected ? XtWindow(selected) : None, input};
    Atom result = XInternAtom(display, "_THEME_LAB_GTK4_TRAVERSE_RESULT", False);
    XChangeProperty(display, XtWindow(focus->canvas), result, XA_CARDINAL, 32,
                    PropModeReplace, (unsigned char *)reply, 7);
    (void)end(display, previous);
    return True;
}
static void adopt(TLGTK4Focus *focus) {
    Display *display = XtDisplay(focus->canvas);
    unsigned long values[3], info[2];
    int (*previous)(Display *, XErrorEvent *) = begin(display);
    int valid = read_values(display, XtWindow(focus->canvas), focus->child_atom, values, 3) &&
                values[0] == 1 && values[1] && values[2] &&
                direct_child(focus, values[1]) &&
                read_values(display, values[1], focus->info_atom, info, 2) &&
                info[0] == 1 && info[1] == values[2];
    int clean = end(display, previous);
    if (!valid || !clean || values[1] == focus->child) return;
    forget(focus);
    focus->child = values[1]; focus->pid = values[2];
    previous = begin(display);
    XAddToSaveSet(display, focus->child);
    XSelectInput(display, focus->child, StructureNotifyMask | FocusChangeMask);
    clean = end(display, previous);
    if (!clean) { forget(focus); return; }
    focus->saved = 1;
    if (XtWindowToWidget(display, focus->child) == NULL) {
        XtRegisterDrawable(display, focus->child, focus->canvas);
        focus->registered = 1;
    }
    if(focus->notify)focus->notify(focus->notify_data);
}
static void event(Widget widget, XtPointer data, XEvent *event, Boolean *dispatch) {
    (void)widget;
    TLGTK4Focus *focus = data;
    if (!focus->enabled || !XtIsRealized(focus->canvas)) return;
    Display *display = XtDisplay(focus->canvas);
    Window canvas = XtWindow(focus->canvas);
    if (event->type == PropertyNotify && event->xproperty.window == canvas &&
        event->xproperty.atom == focus->child_atom) adopt(focus);
    else if (event->type == DestroyNotify && event->xdestroywindow.window == focus->child)
        forget(focus);
    else if (event->type == FocusIn && event->xfocus.window == canvas &&
             event->xfocus.mode == NotifyNormal && focus->child) {
        int (*previous)(Display *, XErrorEvent *) = begin(display);
        if (direct_child(focus, focus->child))
            XSetInputFocus(display, focus->child, RevertToParent, CurrentTime);
        (void)end(display, previous);
    } else if (event->type == PropertyNotify && event->xproperty.window == canvas &&
               event->xproperty.atom == focus->traverse_atom && focus->child) {
        unsigned long request[5];
        int (*previous)(Display *, XErrorEvent *) = begin(display);
        int valid = direct_child(focus, focus->child) &&
            read_values(display, canvas, focus->traverse_atom, request, 5) &&
            request[0] == 1 && request[1] == focus->child && request[2] == focus->pid &&
            request[3] > focus->sequence && (request[4] == 1 || request[4] == 2);
        int clean = end(display, previous);
        if (valid && clean) {
            focus->sequence = request[3];
            focus->direction = request[4];
            Widget shell = focus->canvas;
            while (XtParent(shell) && !XtIsShell(shell)) shell = XtParent(shell);
            previous = begin(display);
            XSetInputFocus(display, XtWindow(shell), RevertToParent, CurrentTime);
            (void)end(display, previous);
            /* Xt drains the resulting FocusIn/Out events before this idle
             * action. Traversal can then use Motif's updated focus state. */
            if (!focus->work)
                focus->work = XtAppAddWorkProc(XtWidgetToApplicationContext(focus->canvas),
                                              finish_traversal, focus);
            *dispatch = False;
        }
    }
}

TLGTK4Focus *tl_gtk4_focus_create(Widget canvas) {
    TLGTK4Focus *focus = calloc(1, sizeof(*focus));
    if (!focus) return NULL;
    focus->canvas = canvas;
    Display *display = XtDisplay(canvas);
    focus->child_atom = XInternAtom(display, "_THEME_LAB_GTK4_CHILD", False);
    focus->traverse_atom = XInternAtom(display, "_THEME_LAB_GTK4_TRAVERSE", False);
    focus->info_atom = XInternAtom(display, "_THEME_LAB_GTK4_INFO", False);
    XtAddEventHandler(canvas, PropertyChangeMask | FocusChangeMask | StructureNotifyMask,
                      False, event, focus);
    return focus;
}
void tl_gtk4_focus_enabled(TLGTK4Focus *focus, int enabled) {
    if (!focus) return;
    if (focus->enabled == enabled) return;
    focus->enabled = enabled;
    if (!enabled) forget(focus);
    else if (XtIsRealized(focus->canvas)) adopt(focus);
}
void tl_gtk4_focus_destroy(TLGTK4Focus *focus) {
    if (!focus) return;
    focus->notify=NULL;
    XtRemoveEventHandler(focus->canvas, PropertyChangeMask | FocusChangeMask | StructureNotifyMask,
                         False, event, focus);
    forget(focus); free(focus);
}
int tl_gtk4_focus_has_child(const TLGTK4Focus *focus) {
    return focus && focus->enabled && focus->child!=None;
}
void tl_gtk4_focus_observer(TLGTK4Focus *focus, void (*notify)(XtPointer), XtPointer data) {
    if(!focus)return;
    focus->notify=notify;focus->notify_data=data;
}
