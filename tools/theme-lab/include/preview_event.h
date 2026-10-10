/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_PREVIEW_EVENT_H
#define TL_PREVIEW_EVENT_H
#include <stddef.h>
typedef struct { int control, x, y; enum { TL_EVENT_SELECT, TL_EVENT_MOVE, TL_EVENT_NATIVE } action; } TLPreviewEvent;
/* Parse bounded IPC without side effects. A stale scene is rejected. */
int tl_preview_event(const char *text, size_t length, const char *scene_hash, TLPreviewEvent *event);
#endif
