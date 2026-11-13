/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_MANUAL_PAINT_VIEW_H
#define TL_MANUAL_PAINT_VIEW_H
#include "manual_paint.h"
#include "text_editor.h"
#include "theme_lab.h"
#include <X11/Xutil.h>
#include <Xm/Xm.h>
typedef struct TLManualPaintView TLManualPaintView;
/* Private native sample geometry.  This request is deliberately separate from
 * TLModel/TLRecipe: changing a Paint probe must never promote those temporary
 * dimensions or range values into scene.json.  A zero length/thickness keeps
 * the toolkit's natural request.  The range is normalized to 0..100. */
typedef enum {
    TL_PAINT_SAMPLE_WHOLE = -1,
    TL_PAINT_SAMPLE_ARROW = TL_SCROLL_ARROW,
    TL_PAINT_SAMPLE_ARROW_BUTTON = TL_SCROLL_ARROW_BUTTON,
    TL_PAINT_SAMPLE_TROUGH = TL_SCROLL_TROUGH,
    TL_PAINT_SAMPLE_THUMB = TL_SCROLL_THUMB,
    TL_PAINT_SAMPLE_FITTING = TL_SCROLL_FITTING
} TLManualPaintSamplePart;
typedef enum {
    TL_PAINT_DIRECTION_AUTO,
    TL_PAINT_DIRECTION_LEFT,
    TL_PAINT_DIRECTION_RIGHT,
    TL_PAINT_DIRECTION_UP,
    TL_PAINT_DIRECTION_DOWN
} TLManualPaintSampleDirection;
typedef enum {
    TL_PAINT_SAMPLE_LIVE,
    TL_PAINT_SAMPLE_R584
} TLManualPaintSampleSource;
enum {
    TL_PAINT_REFERENCE_R584 = TL_FAMILY_COUNT,
    TL_PAINT_REFERENCE_COUNT = TL_FAMILY_COUNT + 1
};
typedef struct {
    int source, family, control, state;
    int length_px, thickness_px;
    int value, page_size;
    int part, direction;
} TLManualPaintSampleRequest;
typedef void (*TLManualPaintContextChanged)(void *context, int family,
                                            int control, int state);
typedef void (*TLManualPaintReferenceChanged)(
    void *context, const TLManualPaintSampleRequest *request);
void tl_manual_paint_sample_request_default(TLManualPaintSampleRequest *request,
                                            int family, int control, int state);
int tl_manual_paint_sample_request_validate(
    const TLManualPaintSampleRequest *request, char *error, size_t capacity);
/* View-side hand-off used by the Paint controls.  It dispatches a private
 * sample only; it does not edit the project model or applied scene. */
int tl_view_manual_paint_sample_request(
    TLView *view, const TLManualPaintSampleRequest *request,
    char *error, size_t capacity);
int tl_view_manual_paint_sample_current(
    const TLView *view, TLManualPaintSampleRequest *request);
int tl_view_manual_paint_reference_current(
    const TLView *view, TLManualPaintSampleRequest *request);
TLManualPaintView *tl_manual_paint_view_open(
    Widget parent, const char *path, int family, int control, int state,
    const unsigned short rgb[6][3], XmFontList inherited_font,
    TLEditorStore *editors,
    TLManualPaintContextChanged changed, void *changed_context,
    TLManualPaintReferenceChanged reference_changed,
    void *reference_changed_context);
void tl_manual_paint_view_samples(TLManualPaintView *view,
                                  int reference_source, XImage *reference,
                                  XImage *native);
void tl_manual_paint_view_notice(TLManualPaintView *view,
                                 const char *message);
void tl_manual_paint_view_present(TLManualPaintView *view);
int tl_manual_paint_view_is_visible(const TLManualPaintView *view);
int tl_manual_paint_view_checkpoint(TLManualPaintView *view);
void tl_manual_paint_view_context(TLManualPaintView *view, int family,
                                  int control, int state);
void tl_manual_paint_view_palette(TLManualPaintView *view,
                                  const unsigned short rgb[6][3]);
void tl_manual_paint_view_header_palette(TLManualPaintView *view,
                                         const unsigned short rgb[6][3]);
void tl_manual_paint_view_palettes(TLManualPaintView *view,
                                   const unsigned short body[6][3],
                                   const unsigned short header[6][3]);
void tl_manual_paint_view_close(TLManualPaintView *view);
#endif
