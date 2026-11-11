/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_GTK4_CANVAS_IDENTITY_H
#define TL_GTK4_CANVAS_IDENTITY_H
#include <X11/Xatom.h>
#include <X11/Xlib.h>
#include <unistd.h>

static void tl_gtk4_canvas_publish(Display *display, Window canvas) {
    unsigned long identity[] = {1, (unsigned long)getpid(), (unsigned long)getuid()};
    Atom marker = XInternAtom(display, "_THEME_LAB_CANVAS_V1", False);
    XChangeProperty(display, canvas, marker, XA_CARDINAL, 32, PropModeReplace,
                    (unsigned char *)identity, 3);
    XSync(display, False);
}
#endif
