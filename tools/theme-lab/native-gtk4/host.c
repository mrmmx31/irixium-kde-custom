/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Main-thread private X11 boundary. Does not implement XEmbed or GTK events. */
#include "host.h"
#include <X11/Xatom.h>
#include <X11/Xlib.h>
#include <stdlib.h>
#include <unistd.h>

struct TLGTK4Host {
    Display *display;
    Window parent, child;
    unsigned long pid, uid;
    int width, height, original_override;
    int attach_status;
    unsigned long sequence;
};
static Display *trapped_display;
static int trapped_error;
static int (*previous_handler)(Display *, XErrorEvent *);

static int catch_error(Display *display, XErrorEvent *event) {
    if (display == trapped_display) {
        trapped_error = event->error_code;
        return 0;
    }
    return previous_handler ? previous_handler(display, event) : 0;
}
static void trap(Display *display) {
    trapped_display = display;
    trapped_error = 0;
    previous_handler = XSetErrorHandler(catch_error);
}
static int untrap(Display *display) {
    int error;
    XSync(display, False);
    error = trapped_error;
    XSetErrorHandler(previous_handler);
    trapped_display = NULL;
    return error == 0;
}

static int property(Display *display, Window window, const char *name,
                    unsigned long *values, unsigned long count) {
    Atom type, atom = XInternAtom(display, name, False);
    int format, status;
    unsigned long length, remaining;
    unsigned char *data = NULL;
    status = XGetWindowProperty(display, window, atom, 0, (long)count, False,
                               XA_CARDINAL, &type, &format, &length, &remaining, &data);
    int valid = status == Success && type == XA_CARDINAL && format == 32 &&
                length == count && remaining == 0;
    if (valid)
        for (unsigned long i = 0; i < count; ++i)
            values[i] = ((unsigned long *)data)[i];
    if (data) XFree(data);
    return valid;
}

static int parent_attributes(TLGTK4Host *host, XWindowAttributes *attributes) {
    unsigned long identity[3];
    return property(host->display, host->parent, "_THEME_LAB_CANVAS_V1", identity, 3) &&
           identity[0] == 1 && identity[1] == host->pid && identity[2] == host->uid &&
           XGetWindowAttributes(host->display, host->parent, attributes) &&
           attributes->class == InputOutput && attributes->width > 0 &&
           attributes->height > 0;
}

static int child_parent(TLGTK4Host *host) {
    Window root, parent, *children = NULL;
    unsigned int count;
    int queried = XQueryTree(host->display, host->child, &root, &parent, &children, &count);
    if (children) XFree(children);
    return queried && parent == host->parent;
}

int tl_gtk4_host_abi(void) { return 1; }

TLGTK4Host *tl_gtk4_host_open(unsigned long parent, unsigned long pid, unsigned long uid) {
    if (!parent || !pid) return NULL;
    TLGTK4Host *host = calloc(1, sizeof(*host));
    if (!host) return NULL;
    host->display = XOpenDisplay(NULL);
    if (!host->display) { free(host); return NULL; }
    host->parent = parent; host->pid = pid; host->uid = uid;
    XWindowAttributes attributes;
    trap(host->display);
    int valid = parent_attributes(host, &attributes);
    int clean = untrap(host->display);
    if (!valid || !clean) { XCloseDisplay(host->display); free(host); return NULL; }
    return host;
}

int tl_gtk4_host_attach(TLGTK4Host *host, unsigned long child) {
    if (!host || !child || host->child) return 0;
    XWindowAttributes parent, attributes;
    unsigned long owner = 0;
    host->attach_status = 0;
    trap(host->display);
    int parent_valid = parent_attributes(host, &parent);
    int owner_valid = property(host->display, child, "_NET_WM_PID", &owner, 1);
    int attributes_valid = XGetWindowAttributes(host->display, child, &attributes);
    int valid = parent_valid && owner_valid && owner == (unsigned long)getpid() &&
                attributes_valid && attributes.root == parent.root &&
                attributes.class == InputOutput;
    int clean = untrap(host->display);
    if (!valid || !clean) {
        host->attach_status = !clean ? 100 + trapped_error : !parent_valid ? 1 : !owner_valid ? 2 :
                              owner != (unsigned long)getpid() ? 3 :
                              !attributes_valid ? 4 : 5;
        return 0;
    }
    host->child = child;
    host->original_override = attributes.override_redirect;
    XSetWindowAttributes changes = {.override_redirect = True};
    trap(host->display);
    unsigned long info[] = {1, (unsigned long)getpid()};
    Atom info_atom = XInternAtom(host->display, "_THEME_LAB_GTK4_INFO", False);
    XChangeProperty(host->display, child, info_atom, XA_CARDINAL, 32,
                    PropModeReplace, (unsigned char *)info, 2);
    /* The GTK4 child does not pretend to be a GtkPlug. Its private bridge
     * manages size explicitly without interception by XEmbed/WM redirects. */
    XChangeWindowAttributes(host->display, child, CWOverrideRedirect, &changes);
    XReparentWindow(host->display, child, host->parent, 0, 0);
    XMoveResizeWindow(host->display, child, 0, 0, (unsigned)parent.width, (unsigned)parent.height);
    XMapWindow(host->display, child);
    unsigned long announcement[] = {1, child, (unsigned long)getpid()};
    Atom child_atom = XInternAtom(host->display, "_THEME_LAB_GTK4_CHILD", False);
    XChangeProperty(host->display, host->parent, child_atom, XA_CARDINAL, 32,
                    PropModeReplace, (unsigned char *)announcement, 3);
    unsigned long prior[5];
    if (property(host->display, host->parent, "_THEME_LAB_GTK4_TRAVERSE", prior, 5) &&
        prior[0] == 1 && prior[1] == child && prior[2] == (unsigned long)getpid())
        host->sequence = prior[3];
    valid = child_parent(host);
    clean = untrap(host->display);
    if (!valid || !clean) {
        host->attach_status = !clean ? 100 + trapped_error : 7;
        return 0;
    }
    host->width = parent.width; host->height = parent.height;
    host->attach_status = 0;
    return 1;
}

int tl_gtk4_host_attach_status(TLGTK4Host *host) {
    return host ? host->attach_status : -1;
}

int tl_gtk4_host_traverse(TLGTK4Host *host, int backward) {
    int width, height;
    if (!host || host->sequence == 0xffffffffUL ||
        (backward != 0 && backward != 1) || !tl_gtk4_host_poll(host, &width, &height)) return 0;
    unsigned long request[] = {1, host->child, (unsigned long)getpid(),
                               ++host->sequence, backward ? 2UL : 1UL};
    trap(host->display);
    Atom atom = XInternAtom(host->display, "_THEME_LAB_GTK4_TRAVERSE", False);
    XChangeProperty(host->display, host->parent, atom, XA_CARDINAL, 32,
                    PropModeReplace, (unsigned char *)request, 5);
    return untrap(host->display);
}

int tl_gtk4_host_traversal_result(TLGTK4Host *host, unsigned long *sequence, int *completed) {
    if (!host || !host->child || !sequence || !completed) return 0;
    unsigned long reply[7];
    trap(host->display);
    int valid = property(host->display, host->parent, "_THEME_LAB_GTK4_TRAVERSE_RESULT", reply, 7) &&
        reply[0] == 1 && reply[1] == host->child && reply[2] == (unsigned long)getpid() &&
        reply[3] == host->sequence && reply[4] <= 1;
    int clean = untrap(host->display);
    if (!valid || !clean) return 0;
    *sequence = reply[3]; *completed = (int)reply[4];
    return 1;
}

int tl_gtk4_host_poll(TLGTK4Host *host, int *width, int *height) {
    if (!host || !host->child || !width || !height) return 0;
    XWindowAttributes attributes;
    trap(host->display);
    int valid = parent_attributes(host, &attributes) && child_parent(host);
    if (valid && (attributes.width != host->width || attributes.height != host->height)) {
        XMoveResizeWindow(host->display, host->child, 0, 0,
                         (unsigned)attributes.width, (unsigned)attributes.height);
    }
    int clean = untrap(host->display);
    if (!valid || !clean) return 0;
    *width = host->width = attributes.width;
    *height = host->height = attributes.height;
    return 1;
}

void tl_gtk4_host_close(TLGTK4Host *host) {
    if (!host) return;
    if (host->child) {
        trap(host->display);
        if (child_parent(host)) {
            XSetWindowAttributes changes = {.override_redirect = host->original_override};
            XChangeWindowAttributes(host->display, host->child, CWOverrideRedirect, &changes);
        }
        (void)untrap(host->display);
    }
    XCloseDisplay(host->display);
    free(host);
}
