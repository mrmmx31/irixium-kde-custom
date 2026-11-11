/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_NATIVE_METRICS_H
#define TL_NATIVE_METRICS_H
#include <stddef.h>
enum { TL_FONT_UNKNOWN, TL_FONT_MEASURED, TL_FONT_NONE };
typedef struct {
    int kind;
    char description[384];
} TLNativeFont;
typedef struct {
    int valid, axis, slider_start, slider_end;
    int area_x, area_y, area_width, area_height;
} TLNativeRange;
typedef struct { int x,y,width,height; } TLNativeRect;
typedef struct {
    int source; /* 1 Motif 2.3.8 rectangles, 2 verified GTK3 margin boxes */
    unsigned mask; /* 1 slider, 2 slider area, 4 first arrow, 8 second arrow */
    TLNativeRect slider, track, arrows[2];
} TLNativePieces;
typedef struct {
    int width, height, minimum_width, minimum_height;
    int natural_width, natural_height, scale_factor, separate;
    int cell_offset_x, cell_offset_y, cell_offset_valid;
    int position_x, position_y, position_valid;
    TLNativeFont font;
    int sensitivity_known, sensitive;
    TLNativeRange range;
    TLNativePieces pieces;
} TLNativeMetrics;
/* Measurements are ephemeral allocations, never historical defaults. */
void tl_metrics_format(char *text, size_t capacity, const char *origin,
                       const TLNativeMetrics *metrics);
/* Physical size comparison only; positions belong to separate local canvases.
 * Returns -1 when allocation or scale is unknown, never invents equality. */
int tl_metrics_size_delta(const TLNativeMetrics *reference,
                         const TLNativeMetrics *sample, int *width, int *height);
#endif
