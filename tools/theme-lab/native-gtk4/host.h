/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_GTK4_HOST_H
#define TL_GTK4_HOST_H

typedef struct TLGTK4Host TLGTK4Host;
int tl_gtk4_host_abi(void);
TLGTK4Host *tl_gtk4_host_open(unsigned long parent, unsigned long pid,
                            unsigned long uid);
int tl_gtk4_host_attach(TLGTK4Host *host, unsigned long child);
int tl_gtk4_host_attach_status(TLGTK4Host *host);
int tl_gtk4_host_poll(TLGTK4Host *host, int *width, int *height);
int tl_gtk4_host_traverse(TLGTK4Host *host, int backward);
int tl_gtk4_host_traversal_result(TLGTK4Host *host, unsigned long *sequence, int *completed);
void tl_gtk4_host_close(TLGTK4Host *host);
#endif
