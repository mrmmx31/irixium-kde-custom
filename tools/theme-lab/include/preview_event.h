/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_PREVIEW_EVENT_H
#define TL_PREVIEW_EVENT_H
#include <stddef.h>
#include "native_metrics.h"
typedef struct {
    int control, x, y, width, height, minimum_width, minimum_height;
    char instance[33];
    TLNativeMetrics metrics;
    int toggle_state_known, toggle_active, toggle_separate;
    int radio_state_known, radio_member, radio_separate;
    enum { TL_EVENT_SELECT, TL_EVENT_MOVE, TL_EVENT_NATIVE, TL_EVENT_METRICS } action;
} TLPreviewEvent;
/* Parse bounded IPC without side effects. A stale scene is rejected. */
int tl_preview_event(const char *text, size_t length, const char *scene_hash, TLPreviewEvent *event);
/* Expected family is supplied by the active controller, never inferred from IPC.
 * The legacy function above remains GTK3-only. */
int tl_preview_event_family(const char *text, size_t length, const char *scene_hash,
                            const char *family, TLPreviewEvent *event);
enum { TL_PREVIEW_EVENT_BATCH=32, TL_PREVIEW_EVENT_FILENAME=256 };
/* Bounded selection of the oldest event filenames; no allocation or I/O. */
size_t tl_preview_event_order(char names[][TL_PREVIEW_EVENT_FILENAME],size_t count,const char *name);
#endif
