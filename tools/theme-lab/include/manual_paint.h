/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_MANUAL_PAINT_H
#define TL_MANUAL_PAINT_H

#include <stddef.h>
#include <stdint.h>

typedef struct TLManualPaint TLManualPaint;

/* Persistent artwork identity.  WHOLE/AUTO is the compatibility identity used
 * by schema 1 and by tl_manual_paint_select(). */
typedef enum {
  TL_PAINT_PART_WHOLE,
  TL_PAINT_PART_ARROW,
  TL_PAINT_PART_ARROW_BUTTON,
  TL_PAINT_PART_TROUGH,
  TL_PAINT_PART_THUMB,
  TL_PAINT_PART_FITTING,
  TL_PAINT_PART_COUNT
} TLManualPaintPart;

/* AUTO is valid for every part.  START/END and the four directions identify
 * arrow or arrow-button variants; BEFORE/AFTER split a trough around a thumb. */
typedef enum {
  TL_PAINT_VARIANT_AUTO,
  TL_PAINT_VARIANT_START,
  TL_PAINT_VARIANT_END,
  TL_PAINT_VARIANT_BEFORE,
  TL_PAINT_VARIANT_AFTER,
  TL_PAINT_VARIANT_UP,
  TL_PAINT_VARIANT_DOWN,
  TL_PAINT_VARIANT_LEFT,
  TL_PAINT_VARIANT_RIGHT,
  TL_PAINT_VARIANT_COUNT
} TLManualPaintVariant;

typedef enum {
  TL_PAINT_PENCIL,
  TL_PAINT_ERASER,
  TL_PAINT_LINE,
  TL_PAINT_RECTANGLE,
  TL_PAINT_FILL,
  TL_PAINT_PICKER
} TLPaintTool;

enum {
  TL_PAINT_MIN_SIZE = 8,
  TL_PAINT_MAX_WIDTH = 512,
  TL_PAINT_MAX_HEIGHT = 256,
  TL_PAINT_MAX_UNDO = 64
};

/* Pixels are RGBA; alpha zero means transparent paper, not a fixed theme color.
 */
TLManualPaint *tl_manual_paint_new(void);
void tl_manual_paint_free(TLManualPaint *paint);
/* Compatibility wrapper: selects WHOLE/AUTO. */
int tl_manual_paint_select(TLManualPaint *paint, int family, int control,
                           int state);
int tl_manual_paint_select_piece(TLManualPaint *paint, int family, int control,
                                 int state, TLManualPaintPart part,
                                 TLManualPaintVariant variant);
/* Current identity getters return -1 when no document is selected. */
int tl_manual_paint_current_family(const TLManualPaint *paint);
int tl_manual_paint_current_control(const TLManualPaint *paint);
int tl_manual_paint_current_state(const TLManualPaint *paint);
int tl_manual_paint_current_part(const TLManualPaint *paint);
int tl_manual_paint_current_variant(const TLManualPaint *paint);
int tl_manual_paint_resize(TLManualPaint *paint, int width, int height);
/* Atomically replaces the current editable raster and records exactly one
 * Undo step.  This is used for explicit reference imports; the caller still
 * owns pixels and the operation never changes a theme recipe. */
int tl_manual_paint_replace(TLManualPaint *paint, int width, int height,
                            const uint32_t *pixels);
int tl_manual_paint_width(const TLManualPaint *paint);
int tl_manual_paint_height(const TLManualPaint *paint);
const uint32_t *tl_manual_paint_pixels(const TLManualPaint *paint);
uint32_t tl_manual_paint_pixel(const TLManualPaint *paint, int x, int y);
void tl_manual_paint_color(TLManualPaint *paint, uint32_t rgba);
uint32_t tl_manual_paint_color_get(const TLManualPaint *paint);
int tl_manual_paint_put(TLManualPaint *paint, int x, int y, uint32_t rgba);
int tl_manual_paint_line(TLManualPaint *paint, int x0, int y0, int x1, int y1,
                         uint32_t rgba);
int tl_manual_paint_rect(TLManualPaint *paint, int x0, int y0, int x1, int y1,
                         uint32_t rgba);
int tl_manual_paint_fill(TLManualPaint *paint, int x, int y, uint32_t rgba);
/* Call once at the end of a logical stroke/tool operation. */
int tl_manual_paint_checkpoint(TLManualPaint *paint);
int tl_manual_paint_undo(TLManualPaint *paint);
int tl_manual_paint_redo(TLManualPaint *paint);
int tl_manual_paint_can_undo(const TLManualPaint *paint);
int tl_manual_paint_can_redo(const TLManualPaint *paint);
/* Save/load a companion document, independent of the Board's JSON/state. */
int tl_manual_paint_save(const TLManualPaint *paint, const char *path,
                         char *error, size_t capacity);
int tl_manual_paint_load(TLManualPaint *paint, const char *path, char *error,
                         size_t capacity);
/* Salvage valid documents to a new destination without replacing either file.
 * Returns the number of recovered documents, or -1 on failure. */
int tl_manual_paint_recover(const char *source, const char *destination,
                            char *error, size_t capacity);

#endif
