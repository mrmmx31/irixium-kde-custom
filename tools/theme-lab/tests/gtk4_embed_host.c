/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Private native Motif host; no theme application or user data. */
#include <Xm/DrawingA.h>
#include <Xm/RowColumn.h>
#include <Xm/PushB.h>
#include <stdio.h>
#include <string.h>
#include "../native-gtk4/canvas_identity.h"
#include "../native-gtk4/focus.h"

static void activated(Widget widget, XtPointer data, XtPointer call) {
    (void)widget; (void)call;
    printf("{\"activated\":\"%s\"}\n", (char *)data);
    fflush(stdout);
}

int main(int argc, char **argv) {
    XtAppContext app;
    int focus_mode = argc > 1 && !strcmp(argv[1], "--focus-fixture");
    if (focus_mode) { --argc; ++argv; }
    Widget shell = XtVaAppInitialize(&app, "Gtk4EmbedProbe", NULL, 0,
                                    &argc, argv, NULL, NULL);
    Widget parent = shell, before = NULL, after = NULL;
    if (focus_mode) {
        parent = XtVaCreateManagedWidget("focusColumn", xmRowColumnWidgetClass, shell,
            XmNorientation, XmVERTICAL, NULL);
        before = XtVaCreateManagedWidget("before", xmPushButtonWidgetClass, parent,
            XmNnavigationType, XmTAB_GROUP, NULL);
        XtAddCallback(before, XmNactivateCallback, activated, "before");
    }
    Widget canvas = XtVaCreateManagedWidget(
        "nativeCanvas", xmDrawingAreaWidgetClass, parent,
        XmNwidth, 360, XmNheight, 240, XmNtraversalOn, True,
        XmNnavigationType, XmTAB_GROUP, NULL);
    TLGTK4Focus *focus = tl_gtk4_focus_create(canvas);
    tl_gtk4_focus_enabled(focus, 1);
    if (focus_mode) {
        after = XtVaCreateManagedWidget("after", xmPushButtonWidgetClass, parent,
            XmNnavigationType, XmTAB_GROUP, NULL);
        XtAddCallback(after, XmNactivateCallback, activated, "after");
    }
    XtRealizeWidget(shell);
    tl_gtk4_canvas_publish(XtDisplay(shell), XtWindow(canvas));
    XSync(XtDisplay(shell), False);
    printf("%lu\n", (unsigned long)XtWindow(canvas));
    if (focus_mode)
        printf("{\"before\":%lu,\"after\":%lu,\"shell\":%lu}\n",
               (unsigned long)XtWindow(before), (unsigned long)XtWindow(after),
               (unsigned long)XtWindow(shell));
    fflush(stdout);
    XtAppMainLoop(app);
    return 0;
}
