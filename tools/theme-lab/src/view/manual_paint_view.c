/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "manual_paint_view.h"
#include "manual_paint_recovery.h"
#include "ui_hints.h"
#include <X11/Shell.h>
#include <X11/cursorfont.h>
#include <X11/keysym.h>
#include <Xm/ComboBox.h>
#include <Xm/CascadeB.h>
#include <Xm/DrawingA.h>
#include <Xm/Form.h>
#include <Xm/Frame.h>
#include <Xm/Label.h>
#include <Xm/LabelG.h>
#include <Xm/List.h>
#include <Xm/Manager.h>
#include <Xm/MessageB.h>
#include <Xm/Primitive.h>
#include <Xm/Protocols.h>
#include <Xm/PushB.h>
#include <Xm/RowColumn.h>
#include <Xm/Separator.h>
#include <Xm/Scale.h>
#include <Xm/ScrollBar.h>
#include <Xm/ScrolledW.h>
#include <Xm/Text.h>
#include <Xm/TextF.h>
#include <Xm/ToggleB.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

enum {
  ROLE_FACE,
  ROLE_TEXT,
  ROLE_VIEW,
  ROLE_SELECTION,
  ROLE_LIGHT,
  ROLE_SHADOW,
  ROLE_COUNT
};
enum {
  STATE_NORMAL,
  STATE_HOVER,
  STATE_PRESSED,
  STATE_DISABLED,
  STATE_BACKDROP,
  STATE_COUNT
};
enum {
  CONTROL_PUSH = 0,
  CONTROL_TOGGLE = 1,
  CONTROL_CHECK = 2,
  CONTROL_SCROLL_H = 10,
  CONTROL_SCROLL_V = 11
};
enum {
  PALETTE_TEXT,
  PALETTE_FACE,
  PALETTE_VIEW,
  PALETTE_SELECTION,
  PALETTE_LIGHT,
  PALETTE_SHADOW,
  PALETTE_COUNT
};
enum { PAINT_ZOOM = 4, PAINT_ROLE_BUTTONS = 6 };
static const char *const family_names[TL_FAMILY_COUNT] = {
    "Motif", "GTK1", "GTK2", "GTK3",    "GTK4",
    "GTK5",  "Qt5",  "Qt6",  "Kvantum", "Plasma Style"};
static const char *const reference_source_names[TL_PAINT_REFERENCE_COUNT] = {
    "Motif do form principal", "GTK1 atual", "GTK2 atual", "GTK3 atual",
    "GTK4 atual", "GTK5 atual", "Qt5 atual", "Qt6 atual",
    "Kvantum atual", "Plasma Style atual", "GTK2 R584 (assets)"};
static const char *const control_names[TL_CONTROL_COUNT] = {
    "Botão",           "Botão alternável",   "Caixa de seleção",
    "Botão de opção",  "Entrada de texto",   "ComboBox",
    "SpinBox",         "Texto multilinha",   "Escala horizontal",
    "Escala vertical", "Rolagem horizontal", "Rolagem vertical",
    "Botão de seta",   "Progresso / nível",  "Lista",
    "Moldura"};
static const char *const state_names[STATE_COUNT] = {
    "Normal", "Hover", "Pressionado", "Desabilitado", "Backdrop"};
static const char *const part_names[TL_PAINT_PART_COUNT] = {
    "Controle inteiro", "Seta", "Botão da seta", "Trilho",
    "Cursor (thumb)", "Encaixe"};
static const char *const variant_names[TL_PAINT_VARIANT_COUNT] = {
    "Automática",       "Inicial",  "Final",   "Antes do cursor",
    "Depois do cursor", "Cima",     "Baixo",   "Esquerda",
    "Direita"};
static const char *const palette_names[PALETTE_COUNT] = {
    "Texto", "Face", "Conteúdo", "Seleção", "Luz", "Sombra"};
static const int role_map[PALETTE_COUNT] = {
    ROLE_TEXT, ROLE_FACE, ROLE_VIEW, ROLE_SELECTION, ROLE_LIGHT, ROLE_SHADOW};
typedef struct {
  unsigned long pixel;
  uint32_t rgba;
  int used;
} PixelCache;
typedef struct {
  struct TLManualPaintView *view;
  int value;
} PaintBinding;

static int gtk4_control_translated(int control) {
  return control == CONTROL_PUSH || control == CONTROL_TOGGLE ||
         control == CONTROL_CHECK || control == CONTROL_SCROLL_H ||
         control == CONTROL_SCROLL_V;
}
struct TLManualPaintView {
  Widget shell, root, form, menu_bar, header, header_labels[6];
  Widget sidebar, main_panel;
  Widget family, reference_family, control, state, part, variant, canvas,
      scroll, status,
      dimensions, raster_note, recipe_output;
  Widget reference_canvas, native_canvas, reference_label, native_label;
  Widget tools[6], colors[PAINT_ROLE_BUTTONS], width_scale, height_scale;
  Widget probe_length_scale, probe_thickness_scale, probe_value_scale,
      probe_page_scale;
  TLManualPaint *model;
  TLEditorStore *editors;
  XmFontList fallback_font;
  XFontStruct *fallback_core_font;
  char path[TL_PATH_MAX];
  unsigned short rgb[6][3];
  PixelCache *cache;
  size_t cache_capacity, cache_count;
  unsigned long palette_pixels[PALETTE_COUNT + 1];
  int palette_pixel_allocated[PALETTE_COUNT + 1];
  unsigned short header_rgb[6][3];
  unsigned long header_pixels[6];
  int header_pixel_allocated[6], header_palette_valid;
  PaintBinding role_bindings[PALETTE_COUNT], zoom_bindings[2],
      sample_zoom_bindings[2];
  int zoom, grid, tool, family_index, reference_family_index, control_index,
      state_index, part_index, variant_index, brush_role, sample_zoom;
  int variant_values[TL_PAINT_VARIANT_COUNT], variant_count;
  TLManualPaintSampleRequest sample_request;
  int sample_request_ready;
  int updating;
  int combo_map_handlers_installed;
  XtIntervalId combo_selection_timeout;
  Widget pending_combo;
  int pending_combo_selection;
  int drawing, drag_start_x, drag_start_y, last_x, last_y, dirty;
  Cursor tool_cursors[6];
  int cursors_ready;
  uint32_t brush;
  XImage *reference_sample, *native_sample, *reference_display, *native_display;
  Widget copy_reference, copy_native;
  TLManualPaintContextChanged context_changed;
  void *context_changed_context;
  TLManualPaintReferenceChanged reference_changed;
  void *reference_changed_context;
};

static unsigned int cursor_shape_for_tool(int tool) {
  switch (tool) {
  case TL_PAINT_PENCIL:
    return XC_pencil;
  case TL_PAINT_ERASER:
    return XC_X_cursor;
  case TL_PAINT_LINE:
  case TL_PAINT_RECTANGLE:
    return XC_crosshair;
  case TL_PAINT_FILL:
    return XC_spraycan;
  case TL_PAINT_PICKER:
    return XC_draft_small;
  default:
    return XC_left_ptr;
  }
}

static void cursor_palette(TLManualPaintView *v) {
  Display *display;
  Colormap colormap;
  XColor foreground, background;
  if (!v || !v->canvas || !v->cursors_ready)
    return;
  display = XtDisplay(v->canvas);
  XtVaGetValues(v->shell, XtNcolormap, &colormap, NULL);
  foreground.pixel = v->palette_pixels[ROLE_TEXT];
  background.pixel = v->palette_pixels[ROLE_FACE];
  XQueryColor(display, colormap, &foreground);
  XQueryColor(display, colormap, &background);
  for (int i = 0; i < 6; ++i)
    if (v->tool_cursors[i] != None)
      XRecolorCursor(display, v->tool_cursors[i], &foreground, &background);
}

static void cursor_apply(TLManualPaintView *v) {
  if (!v || !v->canvas || !XtIsRealized(v->canvas))
    return;
  if (!v->cursors_ready) {
    for (int i = 0; i < 6; ++i)
      v->tool_cursors[i] =
          XCreateFontCursor(XtDisplay(v->canvas), cursor_shape_for_tool(i));
    v->cursors_ready = 1;
    cursor_palette(v);
  }
  if (v->tool >= 0 && v->tool < 6 && v->tool_cursors[v->tool] != None)
    XDefineCursor(XtDisplay(v->canvas), XtWindow(v->canvas),
                  v->tool_cursors[v->tool]);
}

static XmString text_compound(const char *text) {
  return XmStringGenerate((XtPointer)(text ? text : ""), NULL,
                          XmMULTIBYTE_TEXT, NULL);
}
static void text_content_set(Widget w, const char *text) {
  size_t count = mbstowcs(NULL, text ? text : "", 0);
  if (count == (size_t)-1) {
    XmTextSetString(w, (char *)(text ? text : ""));
    return;
  }
  wchar_t *wide = calloc(count + 1, sizeof(*wide));
  if (!wide || mbstowcs(wide, text ? text : "", count + 1) ==
                   (size_t)-1) {
    free(wide);
    XmTextSetString(w, (char *)(text ? text : ""));
    return;
  }
  XmTextSetStringWcs(w, wide);
  free(wide);
}
static void text_set(Widget w, const char *text) {
  XmString s = text_compound(text);
  XtVaSetValues(w, XmNlabelString, s, NULL);
  XmStringFree(s);
}
static Widget label_new(Widget parent, const char *name, const char *text) {
  Widget w = XtVaCreateManagedWidget(name, xmLabelWidgetClass, parent,
                                     XmNalignment, XmALIGNMENT_BEGINNING, NULL);
  text_set(w, text);
  return w;
}
static XmString combo_item_string(const char *text) {
  XmString result = text_compound(text);
  return result;
}
static Widget combo_new(Widget parent, const char *name,
                        const char *const *items, int count) {
  Widget w;
  XmStringTable values = calloc((size_t)count, sizeof(*values));
  if (!values)
    return NULL;
  for (int i = 0; i < count; i++)
    values[i] = combo_item_string(items[i]);
  w = XtVaCreateManagedWidget(
      name, xmComboBoxWidgetClass, parent, XmNcomboBoxType, XmDROP_DOWN_LIST,
      XmNpositionMode, XmZERO_BASED, XmNitems, values, XmNitemCount, count,
      XmNvisibleItemCount, count < 8 ? count : 8, XmNselectedPosition, 0, NULL);
  for (int i = 0; i < count; i++)
    XmStringFree(values[i]);
  free(values);
  XtManageChild(w);
  return w;
}

static void control_combo_refresh(TLManualPaintView *v) {
  XmStringTable values;
  int old_updating;
  if (!v || !v->control)
    return;
  values = calloc(TL_CONTROL_COUNT, sizeof(*values));
  if (!values)
    return;
  for (int i = 0; i < TL_CONTROL_COUNT; ++i) {
    char label[128];
    if (v->family_index == TL_GTK4)
      snprintf(label, sizeof(label), "%s — %s", control_names[i],
               gtk4_control_translated(i) ? "traduzido"
                                          : "sem tradutor DomainOS");
    else
      snprintf(label, sizeof(label), "%s", control_names[i]);
    values[i] = combo_item_string(label);
  }
  old_updating = v->updating;
  v->updating = 1;
  XtVaSetValues(v->control, XmNitems, values, XmNitemCount, TL_CONTROL_COUNT,
                XmNselectedPosition, v->control_index, NULL);
  v->updating = old_updating;
  for (int i = 0; i < TL_CONTROL_COUNT; ++i)
    XmStringFree(values[i]);
  free(values);
}

static int scrollbar_control(int control) {
  return control == CONTROL_SCROLL_H || control == CONTROL_SCROLL_V;
}

static void variant_combo_refresh(TLManualPaintView *v) {
  XmString values[TL_PAINT_VARIANT_COUNT];
  int candidates[5], count = 0, selected = 0;
  if (!v || !v->variant)
    return;
  candidates[count++] = TL_PAINT_VARIANT_AUTO;
  if (scrollbar_control(v->control_index) &&
      (v->part_index == TL_PAINT_PART_ARROW ||
       v->part_index == TL_PAINT_PART_ARROW_BUTTON)) {
    candidates[count++] = TL_PAINT_VARIANT_START;
    candidates[count++] = TL_PAINT_VARIANT_END;
    candidates[count++] = v->control_index == CONTROL_SCROLL_H
                              ? TL_PAINT_VARIANT_LEFT
                              : TL_PAINT_VARIANT_UP;
    candidates[count++] = v->control_index == CONTROL_SCROLL_H
                              ? TL_PAINT_VARIANT_RIGHT
                              : TL_PAINT_VARIANT_DOWN;
  } else if (scrollbar_control(v->control_index) &&
             v->part_index == TL_PAINT_PART_TROUGH) {
    candidates[count++] = TL_PAINT_VARIANT_BEFORE;
    candidates[count++] = TL_PAINT_VARIANT_AFTER;
  }
  for (int i = 0; i < count; ++i) {
    v->variant_values[i] = candidates[i];
    values[i] = combo_item_string(variant_names[candidates[i]]);
    if (candidates[i] == v->variant_index)
      selected = i;
  }
  v->variant_index = candidates[selected];
  v->variant_count = count;
  int old_updating = v->updating;
  v->updating = 1;
  XtVaSetValues(v->variant, XmNitems, values, XmNitemCount, count,
                XmNselectedPosition, selected, XmNsensitive, count > 1, NULL);
  v->updating = old_updating;
  for (int i = 0; i < count; ++i)
    XmStringFree(values[i]);
}

static void piece_context_refresh(TLManualPaintView *v, int reset) {
  int enabled, old_updating;
  if (!v)
    return;
  enabled = scrollbar_control(v->control_index);
  if (reset || !enabled) {
    v->part_index = TL_PAINT_PART_WHOLE;
    v->variant_index = TL_PAINT_VARIANT_AUTO;
  }
  old_updating = v->updating;
  v->updating = 1;
  if (v->part)
    XtVaSetValues(v->part, XmNselectedPosition, v->part_index,
                  XmNsensitive, enabled, NULL);
  v->updating = old_updating;
  variant_combo_refresh(v);
}
static int combo_callback_index(Widget widget, XtPointer call) {
  XmComboBoxCallbackStruct *selection = call;
  Widget list = NULL;
  XmStringTable items = NULL;
  int *positions = NULL, position_count = 0, count = 0;
  if (!selection || selection->reason != XmCR_SELECT)
    return -1;
  XtVaGetValues(widget, XmNitems, &items, XmNitemCount, &count, XmNlist, &list,
                NULL);
  /* OpenMotif updates the visible callback item before it commits the
   * embedded XmList selection.  The item carried by this callback therefore
   * owns the choice; consulting the list first can return the previous row
   * and leave the editor visually changed but internally on another control. */
  for (int i = 0; selection->item_or_text && items && i < count; i++)
    if (XmStringCompare(selection->item_or_text, items[i]))
      return i;
  if (list && XmListGetSelectedPos(list, &positions, &position_count)) {
    int selected = position_count == 1 ? positions[0] - 1 : -1;
    XtFree((char *)positions);
    if (selected >= 0 && selected < count)
      return selected;
  }
  if (selection->item_position >= 0 && selection->item_position < count)
    return selection->item_position;
  return -1;
}
static int combo_visible_index(Widget combo) {
  Widget text_field = NULL;
  XmStringTable items = NULL;
  XmString visible;
  char *text;
  int count = 0, selected = -1;
  if (!combo)
    return -1;
  XtVaGetValues(combo, XmNtextField, &text_field, XmNitems, &items,
                XmNitemCount, &count, NULL);
  if (!text_field)
    return -1;
  text = XmTextFieldGetString(text_field);
  if (!text)
    return -1;
  visible = text_compound(text);
  for (int i = 0; items && i < count; ++i)
    if (XmStringCompare(visible, items[i])) {
      selected = i;
      break;
    }
  XmStringFree(visible);
  XtFree(text);
  return selected;
}
static void status_set(TLManualPaintView *v, const char *message) {
  if (v && v->status)
    text_set(v->status, message);
}
static void palette_widget(Widget widget,
                           const unsigned long pixels[PALETTE_COUNT + 1]) {
  WidgetList children = NULL;
  Cardinal count = 0;
  Pixel background;
  if (!widget)
    return;
  background = pixels[ROLE_FACE];
  if (XmIsText(widget) || XmIsTextField(widget) || XmIsList(widget))
    background = pixels[ROLE_VIEW];
  XtVaSetValues(widget, XmNbackground, background, NULL);
  if (XmIsPrimitive(widget) || XmIsManager(widget))
    XtVaSetValues(widget, XmNforeground, pixels[ROLE_TEXT], XmNtopShadowColor,
                  pixels[ROLE_LIGHT], XmNbottomShadowColor, pixels[ROLE_SHADOW],
                  NULL);
  if (XmIsPrimitive(widget))
    XtVaSetValues(widget, XmNhighlightColor, pixels[ROLE_SELECTION], NULL);
  if (XmIsToggleButton(widget))
    XtVaSetValues(widget, XmNselectColor, pixels[ROLE_SELECTION],
                  XmNunselectColor, pixels[ROLE_FACE], NULL);
  if (XmIsPushButton(widget))
    XtVaSetValues(widget, XmNarmColor, pixels[PALETTE_COUNT], NULL);
  if (XmIsScrollBar(widget))
    XtVaSetValues(widget, XmNtroughColor, pixels[PALETTE_COUNT], NULL);
  if (XtIsComposite(widget)) {
    XtVaGetValues(widget, XtNchildren, &children, XtNnumChildren, &count, NULL);
    for (Cardinal i = 0; i < count; i++)
      palette_widget(children[i], pixels);
  }
}
static void palette_header_widget(Widget widget,
                                  const unsigned long pixels[6]) {
  if (!widget)
    return;
  XtVaSetValues(widget, XmNbackground, pixels[ROLE_FACE], NULL);
  if (XmIsPrimitive(widget) || XmIsManager(widget))
    XtVaSetValues(widget, XmNforeground, pixels[ROLE_TEXT],
                  XmNtopShadowColor, pixels[ROLE_LIGHT],
                  XmNbottomShadowColor, pixels[ROLE_SHADOW], NULL);
  if (XmIsPrimitive(widget))
    XtVaSetValues(widget, XmNhighlightColor, pixels[ROLE_SELECTION], NULL);
}
static void font_widget(Widget widget, XmFontList fonts) {
  WidgetList children = NULL;
  Cardinal count = 0;
  if (!widget || !fonts)
    return;
  if (XmIsLabel(widget) || XmIsLabelGadget(widget) || XmIsText(widget) ||
      XmIsTextField(widget) || XmIsList(widget) || XmIsScale(widget))
    XtVaSetValues(widget, XmNfontList, fonts, NULL);
  if (XmIsComboBox(widget))
    XtVaSetValues(widget, XmNrenderTable, fonts, NULL);
  if (XtIsComposite(widget)) {
    XtVaGetValues(widget, XtNchildren, &children, XtNnumChildren, &count, NULL);
    for (Cardinal i = 0; i < count; ++i)
      font_widget(children[i], fonts);
  }
}
static void native_role_rgb(TLManualPaintView *v) {
  Pixel pixels[ROLE_COUNT];
  Colormap colormap;
  XtVaGetValues(v->shell, XtNcolormap, &colormap, NULL);
  XtVaGetValues(v->form, XmNbackground, &pixels[ROLE_FACE], XmNforeground,
                &pixels[ROLE_TEXT], XmNtopShadowColor, &pixels[ROLE_LIGHT],
                XmNbottomShadowColor, &pixels[ROLE_SHADOW], NULL);
  XtVaGetValues(v->recipe_output, XmNbackground, &pixels[ROLE_VIEW], NULL);
  XtVaGetValues(v->canvas, XmNhighlightColor, &pixels[ROLE_SELECTION], NULL);
  for (int i = 0; i < ROLE_COUNT; ++i) {
    XColor color = {.pixel = pixels[i]};
    XQueryColor(XtDisplay(v->shell), colormap, &color);
    v->rgb[i][0] = color.red;
    v->rgb[i][1] = color.green;
    v->rgb[i][2] = color.blue;
  }
}
static void combo_list_map_event(Widget list, XtPointer client, XEvent *event,
                                 Boolean *continue_dispatch) {
  TLManualPaintView *v = client;
  Widget combos[] = {v->family, v->control, v->part, v->variant, v->state};
  (void)continue_dispatch;
  if (event->type != MapNotify)
    return;
  for (size_t i = 0; i < sizeof(combos) / sizeof(combos[0]); i++) {
    if (XtNameToWidget(combos[i], "*List") != list)
      continue;
    Widget text = XtNameToWidget(combos[i], "*Text");
    XmFontList font_list = NULL;
    XmRenderTable render_table = NULL;
    if (text)
      XtVaGetValues(text, XmNfontList, &font_list, XmNrenderTable,
                    &render_table, NULL);
    if (font_list)
      XtVaSetValues(list, XmNfontList, font_list, NULL);
    if (render_table)
      XtVaSetValues(list, XmNrenderTable, render_table, NULL);
    palette_widget(list, v->palette_pixels);
    for (Widget ancestor = XtParent(list); ancestor && ancestor != combos[i];
         ancestor = XtParent(ancestor)) {
      if (XtIsShell(ancestor))
        XtVaSetValues(ancestor, XtNbackground,
                      v->palette_pixels[ROLE_FACE], NULL);
      else
        palette_widget(ancestor, v->palette_pixels);
    }
    XFlush(XtDisplay(list));
    break;
  }
}
static int save_layer(TLManualPaintView *v) {
  char error[256];
  if (tl_manual_paint_save(v->model, v->path, error, sizeof(error))) {
    status_set(v, error);
    v->dirty = 1;
    return -1;
  }
  v->dirty = 0;
  status_set(v, error);
  return 0;
}
static void dims_set(TLManualPaintView *v) {
  char label[256];
  snprintf(label, sizeof(label),
           "Arte da peça %s / %s: %d x %d px; zoom %dx (%d:%d)",
           part_names[v->part_index], variant_names[v->variant_index],
           tl_manual_paint_width(v->model), tl_manual_paint_height(v->model),
           v->zoom, v->zoom, v->zoom);
  text_set(v->dimensions, label);
  XtVaSetValues(v->canvas, XmNwidth, tl_manual_paint_width(v->model) * v->zoom,
                XmNheight, tl_manual_paint_height(v->model) * v->zoom, NULL);
  XtVaSetValues(v->width_scale, XmNvalue, tl_manual_paint_width(v->model),
                NULL);
  XtVaSetValues(v->height_scale, XmNvalue, tl_manual_paint_height(v->model),
                NULL);
}
static size_t pixel_hash(uint32_t rgba) {
  uint32_t x = rgba;
  x ^= x >> 16;
  x *= 0x7feb352du;
  x ^= x >> 15;
  x *= 0x846ca68bu;
  x ^= x >> 16;
  return (size_t)x;
}
static int pixel_cache_grow(TLManualPaintView *v) {
  size_t capacity = v->cache_capacity ? v->cache_capacity * 2 : 256;
  if (capacity < 256 || capacity > 1048576)
    return -1;
  PixelCache *next = calloc(capacity, sizeof(*next));
  if (!next)
    return -1;
  for (size_t i = 0; i < v->cache_capacity; i++)
    if (v->cache[i].used) {
      size_t at = pixel_hash(v->cache[i].rgba) & (capacity - 1);
      while (next[at].used)
        at = (at + 1) & (capacity - 1);
      next[at] = v->cache[i];
    }
  free(v->cache);
  v->cache = next;
  v->cache_capacity = capacity;
  return 0;
}
static unsigned long pixel_for(TLManualPaintView *v, uint32_t rgba) {
  Display *dpy = XtDisplay(v->canvas);
  Colormap cmap;
  XColor color;
  if (!v->cache_capacity && pixel_cache_grow(v))
    return v->palette_pixels[ROLE_TEXT];
  if ((v->cache_count + 1) * 10 >= v->cache_capacity * 7 && pixel_cache_grow(v))
    return v->palette_pixels[ROLE_TEXT];
  size_t at = pixel_hash(rgba) & (v->cache_capacity - 1);
  while (v->cache[at].used) {
    if (v->cache[at].rgba == rgba)
      return v->cache[at].pixel;
    at = (at + 1) & (v->cache_capacity - 1);
  }
  color.red = (unsigned short)(((rgba >> 24) & 255u) * 257u);
  color.green = (unsigned short)(((rgba >> 16) & 255u) * 257u);
  color.blue = (unsigned short)(((rgba >> 8) & 255u) * 257u);
  color.flags = DoRed | DoGreen | DoBlue;
  XtVaGetValues(v->shell, XtNcolormap, &cmap, NULL);
  if (!XAllocColor(dpy, cmap, &color))
    return v->palette_pixels[ROLE_TEXT];
  v->cache[at] = (PixelCache){.pixel = color.pixel, .rgba = rgba, .used = 1};
  v->cache_count++;
  return color.pixel;
}
static void canvas_draw(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  XmDrawingAreaCallbackStruct *cb = call;
  Display *dpy = XtDisplay(w);
  Window win = XtWindow(w);
  GC gc;
  const uint32_t *pixels = tl_manual_paint_pixels(v->model);
  int width = tl_manual_paint_width(v->model),
      height = tl_manual_paint_height(v->model), z = v->zoom;
  int image_width = width * z, image_height = height * z;
  XWindowAttributes attributes;
  XImage *image = NULL;
  Pixel background;
  (void)cb;
  if (!XtIsRealized(w) || !pixels || image_width < 1 || image_height < 1 ||
      image_width > 4096 || image_height > 2048 ||
      !XGetWindowAttributes(dpy, win, &attributes))
    return;
  gc = XCreateGC(dpy, win, 0, NULL);
  XtVaGetValues(w, XmNbackground, &background, NULL);
  image = XCreateImage(dpy, attributes.visual, (unsigned)attributes.depth,
                       ZPixmap, 0, NULL, (unsigned)image_width,
                       (unsigned)image_height, 32, 0);
  if (!image) {
    XFreeGC(dpy, gc);
    return;
  }
  size_t image_size = (size_t)image->bytes_per_line * (size_t)image->height;
  if (image_size > 64u * 1024u * 1024u ||
      (image->data = calloc(1, image_size)) == NULL) {
    image->data = NULL;
    XDestroyImage(image);
    XFreeGC(dpy, gc);
    status_set(
        v, "Sem memória para desenhar o canvas; camada e arquivo preservados.");
    return;
  }
  for (int y = 0; y < height; y++)
    for (int x = 0; x < width; x++) {
      uint32_t rgba = pixels[(size_t)y * width + x];
      unsigned long pixel = (rgba & 255u) ? pixel_for(v, rgba) : background;
      for (int dy = 0; dy < z; dy++)
        for (int dx = 0; dx < z; dx++)
          XPutPixel(image, x * z + dx, y * z + dy, pixel);
    }
  XPutImage(dpy, win, gc, image, 0, 0, 0, 0, (unsigned)image_width,
            (unsigned)image_height);
  XDestroyImage(image);
  if (v->grid && z >= 3) {
    Pixel foreground;
    XtVaGetValues(v->canvas, XmNforeground, &foreground, NULL);
    XSetForeground(dpy, gc, foreground);
    for (int x = 1; x < width; x++)
      XDrawLine(dpy, win, gc, x * z, 0, x * z, height * z);
    for (int y = 1; y < height; y++)
      XDrawLine(dpy, win, gc, 0, y * z, width * z, y * z);
  }
  if (v->drawing &&
      (v->tool == TL_PAINT_LINE || v->tool == TL_PAINT_RECTANGLE)) {
    int x0 = v->drag_start_x * z, y0 = v->drag_start_y * z, x1 = v->last_x * z,
        y1 = v->last_y * z;
    XSetForeground(dpy, gc, pixel_for(v, v->brush));
    XSetLineAttributes(dpy, gc, 1, LineOnOffDash, CapButt, JoinMiter);
    if (v->tool == TL_PAINT_LINE)
      XDrawLine(dpy, win, gc, x0, y0, x1, y1);
    else
      XDrawRectangle(dpy, win, gc, x0 < x1 ? x0 : x1, y0 < y1 ? y0 : y1,
                     (unsigned)(abs(x1 - x0)), (unsigned)(abs(y1 - y0)));
  }
  XFreeGC(dpy, gc);
}
static void sample_display_clear(TLManualPaintView *v) {
  if (!v)
    return;
  if (v->reference_display)
    XDestroyImage(v->reference_display);
  if (v->native_display)
    XDestroyImage(v->native_display);
  v->reference_display = NULL;
  v->native_display = NULL;
}
static XImage *sample_scaled_image(Widget canvas, const XImage *source,
                                   int zoom) {
  Display *display;
  XWindowAttributes attributes;
  XImage *scaled;
  size_t bytes;
  int width, height;
  if (!canvas || !source || zoom <= 1 || !XtIsRealized(canvas))
    return NULL;
  width = source->width * zoom;
  height = source->height * zoom;
  if (width < 1 || height < 1 || width > 4096 || height > 2048)
    return NULL;
  display = XtDisplay(canvas);
  if (!XGetWindowAttributes(display, XtWindow(canvas), &attributes))
    return NULL;
  scaled = XCreateImage(display, attributes.visual,
                        (unsigned)attributes.depth, ZPixmap, 0, NULL,
                        (unsigned)width, (unsigned)height, 32, 0);
  if (!scaled)
    return NULL;
  bytes = (size_t)scaled->bytes_per_line * (size_t)scaled->height;
  if (bytes > 64u * 1024u * 1024u ||
      (scaled->data = calloc(1, bytes)) == NULL) {
    scaled->data = NULL;
    XDestroyImage(scaled);
    return NULL;
  }
  for (int y = 0; y < source->height; ++y)
    for (int x = 0; x < source->width; ++x) {
      unsigned long pixel = XGetPixel((XImage *)source, x, y);
      for (int dy = 0; dy < zoom; ++dy)
        for (int dx = 0; dx < zoom; ++dx)
          XPutPixel(scaled, x * zoom + dx, y * zoom + dy, pixel);
    }
  return scaled;
}
static void sample_labels_and_sizes(TLManualPaintView *v) {
  char label[192];
  int zoom;
  if (!v)
    return;
  zoom = v->sample_zoom;
  sample_display_clear(v);
  if (v->reference_sample) {
    XtVaSetValues(v->reference_canvas, XmNwidth,
                  v->reference_sample->width * zoom, XmNheight,
                  v->reference_sample->height * zoom, NULL);
    snprintf(label, sizeof(label), "Referência %s / %s / %d x %d px / %d:1",
             reference_source_names[v->reference_family_index],
             control_names[v->control_index], v->reference_sample->width,
             v->reference_sample->height, zoom);
    text_set(v->reference_label, label);
  } else {
    XtVaSetValues(v->reference_canvas, XmNwidth, 740, XmNheight, 410, NULL);
    snprintf(label, sizeof(label), "Referência %s / captura indisponível",
             reference_source_names[v->reference_family_index]);
    text_set(v->reference_label, label);
  }
  if (v->native_sample) {
    XtVaSetValues(v->native_canvas, XmNwidth, v->native_sample->width * zoom,
                  XmNheight, v->native_sample->height * zoom, NULL);
    snprintf(label, sizeof(label),
             "%s / amostra nativa atual / %d x %d px / %d:1",
             family_names[v->family_index], v->native_sample->width,
             v->native_sample->height, zoom);
    text_set(v->native_label, label);
  } else {
    XtVaSetValues(v->native_canvas, XmNwidth, 740, XmNheight, 410, NULL);
    snprintf(label, sizeof(label), "%s / prévia nativa indisponível",
             family_names[v->family_index]);
    text_set(v->native_label, label);
  }
}
static void samples_redraw(TLManualPaintView *v) {
  if (!v)
    return;
  if (v->reference_canvas && XtIsRealized(v->reference_canvas))
    XClearArea(XtDisplay(v->reference_canvas), XtWindow(v->reference_canvas),
               0, 0, 0, 0, True);
  if (v->native_canvas && XtIsRealized(v->native_canvas))
    XClearArea(XtDisplay(v->native_canvas), XtWindow(v->native_canvas), 0, 0,
               0, 0, True);
}
static void sample_draw(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  XmDrawingAreaCallbackStruct *cb = call;
  XImage *source =
      w == v->reference_canvas ? v->reference_sample : v->native_sample;
  XImage **display = w == v->reference_canvas ? &v->reference_display
                                              : &v->native_display;
  XImage *image = source;
  Display *dpy = XtDisplay(w);
  GC gc;
  XExposeEvent *expose = cb && cb->event && cb->event->type == Expose
                             ? (XExposeEvent *)cb->event
                             : NULL;
  if (!XtIsRealized(w))
    return;
  if (source && v->sample_zoom > 1) {
    if (!*display)
      *display = sample_scaled_image(w, source, v->sample_zoom);
    if (*display)
      image = *display;
  }
  gc = XCreateGC(dpy, XtWindow(w), 0, NULL);
  if (image) {
    int x = expose ? expose->x : 0;
    int y = expose ? expose->y : 0;
    unsigned int width = expose && expose->width > 0
                             ? (unsigned int)expose->width
                             : (unsigned int)image->width;
    unsigned int height = expose && expose->height > 0
                              ? (unsigned int)expose->height
                              : (unsigned int)image->height;
    if (x >= image->width || y >= image->height) {
      XFreeGC(dpy, gc);
      return;
    }
    if (width > (unsigned)(image->width - x))
      width = (unsigned)(image->width - x);
    if (height > (unsigned)(image->height - y))
      height = (unsigned)(image->height - y);
    XPutImage(dpy, XtWindow(w), gc, image, x, y, x, y, width, height);
  } else {
    Pixel foreground;
    XtVaGetValues(w, XmNforeground, &foreground, NULL);
    XSetForeground(dpy, gc, foreground);
    XDrawString(dpy, XtWindow(w), gc, 12, 24, "Amostra nativa indisponivel",
                26);
  }
  XFreeGC(dpy, gc);
}
static void canvas_redraw(TLManualPaintView *v) {
  if (v && v->canvas && XtIsRealized(v->canvas))
    XClearArea(XtDisplay(v->canvas), XtWindow(v->canvas), 0, 0, 0, 0, True);
}
static void select_context(TLManualPaintView *v);
static void canvas_point(TLManualPaintView *v, XButtonEvent *event, int *x,
                         int *y) {
  *x = event->x / v->zoom;
  *y = event->y / v->zoom;
}
static void save_after_edit(TLManualPaintView *v) {
  if (tl_manual_paint_checkpoint(v->model)) {
    status_set(v, "Não foi possível criar o ponto de Undo; edição preservada "
                  "na memória.");
    v->dirty = 1;
  } else {
    v->dirty = 1;
    save_layer(v);
  }
  canvas_redraw(v);
}

static int probe_part(const TLManualPaintView *v) {
  switch (v->part_index) {
  case TL_PAINT_PART_ARROW:
    return TL_PAINT_SAMPLE_ARROW;
  case TL_PAINT_PART_ARROW_BUTTON:
    return TL_PAINT_SAMPLE_ARROW_BUTTON;
  case TL_PAINT_PART_TROUGH:
    return TL_PAINT_SAMPLE_TROUGH;
  case TL_PAINT_PART_THUMB:
    return TL_PAINT_SAMPLE_THUMB;
  case TL_PAINT_PART_FITTING:
    return TL_PAINT_SAMPLE_FITTING;
  default:
    return TL_PAINT_SAMPLE_WHOLE;
  }
}

static int probe_direction(const TLManualPaintView *v) {
  switch (v->variant_index) {
  case TL_PAINT_VARIANT_LEFT:
    return TL_PAINT_DIRECTION_LEFT;
  case TL_PAINT_VARIANT_RIGHT:
    return TL_PAINT_DIRECTION_RIGHT;
  case TL_PAINT_VARIANT_UP:
    return TL_PAINT_DIRECTION_UP;
  case TL_PAINT_VARIANT_DOWN:
    return TL_PAINT_DIRECTION_DOWN;
  case TL_PAINT_VARIANT_START:
    return v->control_index == CONTROL_SCROLL_H ? TL_PAINT_DIRECTION_LEFT
                                                 : TL_PAINT_DIRECTION_UP;
  case TL_PAINT_VARIANT_END:
    return v->control_index == CONTROL_SCROLL_H ? TL_PAINT_DIRECTION_RIGHT
                                                 : TL_PAINT_DIRECTION_DOWN;
  default:
    return TL_PAINT_DIRECTION_AUTO;
  }
}

static void probe_request_fill(TLManualPaintView *v) {
  int scrollbar = scrollbar_control(v->control_index);
  v->sample_request.family = v->family_index;
  v->sample_request.control = v->control_index;
  v->sample_request.state = v->state_index;
  if (!scrollbar) {
    v->sample_request.length_px = 0;
    v->sample_request.thickness_px = 0;
    v->sample_request.value = 25;
    v->sample_request.page_size = 25;
    v->sample_request.part = TL_PAINT_SAMPLE_WHOLE;
    v->sample_request.direction = TL_PAINT_DIRECTION_AUTO;
  } else {
    v->sample_request.part = probe_part(v);
    v->sample_request.direction = probe_direction(v);
  }
}

static void probe_send(TLManualPaintView *v) {
  char error[TL_TEXT_MAX];
  if (!v || !v->sample_request_ready || !v->context_changed_context)
    return;
  probe_request_fill(v);
  if (tl_view_manual_paint_sample_request(
          (TLView *)v->context_changed_context, &v->sample_request, error,
          sizeof(error)))
    status_set(v, error[0] ? error
                           : "Não foi possível atualizar a amostra privada.");
}

static void reference_send(TLManualPaintView *v) {
  TLManualPaintSampleRequest request;
  if (!v || !v->sample_request_ready || !v->reference_changed)
    return;
  probe_request_fill(v);
  request = v->sample_request;
  if (v->reference_family_index == TL_PAINT_REFERENCE_R584) {
    request.source = TL_PAINT_SAMPLE_R584;
    request.family = TL_GTK2;
  } else {
    request.source = TL_PAINT_SAMPLE_LIVE;
    request.family = v->reference_family_index;
  }
  v->reference_changed(v->reference_changed_context, &request);
}

static void probe_controls_update(TLManualPaintView *v, int reset) {
  int scrollbar, old_updating;
  if (!v)
    return;
  scrollbar = scrollbar_control(v->control_index);
  if (reset) {
    tl_manual_paint_sample_request_default(
        &v->sample_request, v->family_index, v->control_index, v->state_index);
    if (scrollbar) {
      v->sample_request.length_px = 120;
      v->sample_request.thickness_px = 15;
    }
  }
  old_updating = v->updating;
  v->updating = 1;
  XtVaSetValues(v->probe_length_scale, XmNsensitive, scrollbar, XmNvalue,
                scrollbar ? v->sample_request.length_px : 120, NULL);
  XtVaSetValues(v->probe_thickness_scale, XmNsensitive, scrollbar, XmNvalue,
                scrollbar ? v->sample_request.thickness_px : 15, NULL);
  XtVaSetValues(v->probe_page_scale, XmNsensitive, scrollbar, XmNvalue,
                scrollbar ? v->sample_request.page_size : 25, NULL);
  XtVaSetValues(v->probe_value_scale, XmNsensitive, scrollbar, XmNmaximum,
                scrollbar && 100 - v->sample_request.page_size > 0
                    ? 100 - v->sample_request.page_size
                    : scrollbar ? 1 : 75,
                XmNvalue,
                scrollbar ? v->sample_request.value : 25, NULL);
  v->updating = old_updating;
  probe_request_fill(v);
}

static void probe_changed(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  int length, thickness, value, page, scale_max;
  (void)w;
  (void)call;
  if (!v || v->updating || !scrollbar_control(v->control_index))
    return;
  XtVaGetValues(v->probe_length_scale, XmNvalue, &length, NULL);
  XtVaGetValues(v->probe_thickness_scale, XmNvalue, &thickness, NULL);
  XtVaGetValues(v->probe_page_scale, XmNvalue, &page, NULL);
  XtVaGetValues(v->probe_value_scale, XmNvalue, &value, NULL);
  if (value > 100 - page) {
    value = 100 - page;
    XtVaSetValues(v->probe_value_scale, XmNvalue, value, NULL);
  }
  scale_max = 100 - page;
  XtVaSetValues(v->probe_value_scale, XmNmaximum,
                scale_max > 0 ? scale_max : 1, NULL);
  v->sample_request.length_px = length;
  v->sample_request.thickness_px = thickness;
  v->sample_request.value = value;
  v->sample_request.page_size = page;
  probe_send(v);
  reference_send(v);
}
static void combo_selection_apply(TLManualPaintView *v, Widget combo,
                                  int selected) {
  int count = combo == v->family    ? TL_FAMILY_COUNT
              : combo == v->reference_family ? TL_PAINT_REFERENCE_COUNT
              : combo == v->control ? TL_CONTROL_COUNT
              : combo == v->part    ? TL_PAINT_PART_COUNT
              : combo == v->variant ? v->variant_count
                                    : STATE_COUNT;
  if (selected < 0 || selected >= count) {
    status_set(v, "O ComboBox retornou um índice inválido; contexto "
                  "anterior preservado.");
    return;
  }
  int *current = combo == v->family    ? &v->family_index
                 : combo == v->reference_family ? &v->reference_family_index
                 : combo == v->control ? &v->control_index
                 : combo == v->part    ? &v->part_index
                 : combo == v->variant ? &v->variant_index
                                       : &v->state_index;
  int value = combo == v->variant ? v->variant_values[selected] : selected;
  if (*current == value)
    return;
  *current = value;
  if (combo == v->reference_family) {
    reference_send(v);
    sample_labels_and_sizes(v);
    samples_redraw(v);
    status_set(v, "Fonte da referência alterada; a família e a arte editada "
                  "foram preservadas.");
    return;
  }
  if (combo == v->family)
    control_combo_refresh(v);
  if (combo == v->control) {
    piece_context_refresh(v, 1);
    probe_controls_update(v, 1);
  } else if (combo == v->part) {
    v->variant_index = TL_PAINT_VARIANT_AUTO;
    variant_combo_refresh(v);
  } else
    probe_controls_update(v, 0);
  select_context(v);
  if (v->context_changed)
    v->context_changed(v->context_changed_context, v->family_index,
                       v->control_index, v->state_index);
  probe_send(v);
  reference_send(v);
}

static void combo_selection_after_commit(XtPointer client, XtIntervalId *id) {
  TLManualPaintView *v = client;
  Widget combo;
  int selected = -1;
  (void)id;
  if (!v)
    return;
  combo = v->pending_combo;
  v->pending_combo = NULL;
  v->combo_selection_timeout = 0;
  selected = v->pending_combo_selection;
  v->pending_combo_selection = -1;
  if (!combo || v->updating)
    return;
  /* OpenMotif commits XmNselectedPosition after XmNselectionCallback returns.
   * Keep an explicit callback/list item when one was reported: the visible
   * field can still contain the previous row on this event-loop turn.  Only a
   * callback-free keyboard/pointer commit falls back to the visible field. */
  if (selected < 0)
    selected = combo_visible_index(combo);
  if (selected < 0)
    XtVaGetValues(combo, XmNselectedPosition, &selected, NULL);
  combo_selection_apply(v, combo, selected);
}
static void canvas_event(Widget w, XtPointer client, XEvent *event,
                         Boolean *cont) {
  TLManualPaintView *v = client;
  int x, y;
  uint32_t color;
  (void)w;
  (void)cont;
  if (event->type == ButtonPress && event->xbutton.button == Button1) {
    canvas_point(v, &event->xbutton, &x, &y);
    if (v->tool == TL_PAINT_PICKER) {
      v->brush_role = -1;
      v->brush = tl_manual_paint_pixel(v->model, x, y);
      tl_manual_paint_color(v->model, v->brush);
      status_set(v, "Cor copiada apenas para a camada raster; a receita nativa "
                    "não foi alterada.");
      return;
    }
    if (v->tool == TL_PAINT_FILL) {
      color = tl_manual_paint_color_get(v->model);
      if (!tl_manual_paint_fill(v->model, x, y, color))
        save_after_edit(v);
      return;
    }
    XtSetKeyboardFocus(v->shell, w);
    (void)XtGrabPointer(w, False, ButtonReleaseMask | ButtonMotionMask,
                        GrabModeAsync, GrabModeAsync, None, None,
                        event->xbutton.time);
    v->drawing = 1;
    v->drag_start_x = v->last_x = x;
    v->drag_start_y = v->last_y = y;
    if (v->tool == TL_PAINT_PENCIL || v->tool == TL_PAINT_ERASER) {
      color = v->tool == TL_PAINT_ERASER ? 0 : v->brush;
      tl_manual_paint_put(v->model, x, y, color);
      canvas_redraw(v);
    }
    return;
  }
  if (event->type == MotionNotify && v->drawing) {
    x = event->xmotion.x / v->zoom;
    y = event->xmotion.y / v->zoom;
    if (v->tool == TL_PAINT_PENCIL || v->tool == TL_PAINT_ERASER) {
      color = v->tool == TL_PAINT_ERASER ? 0 : v->brush;
      tl_manual_paint_line(v->model, v->last_x, v->last_y, x, y, color);
      canvas_redraw(v);
    } else
      canvas_redraw(v);
    v->last_x = x;
    v->last_y = y;
    return;
  }
  if (event->type == ButtonRelease && event->xbutton.button == Button1 &&
      v->drawing) {
    canvas_point(v, &event->xbutton, &x, &y);
    v->drawing = 0;
    XtUngrabPointer(w, event->xbutton.time);
    color = v->tool == TL_PAINT_ERASER ? 0 : v->brush;
    if (v->tool == TL_PAINT_LINE)
      tl_manual_paint_line(v->model, v->drag_start_x, v->drag_start_y, x, y,
                           color);
    else if (v->tool == TL_PAINT_RECTANGLE)
      tl_manual_paint_rect(v->model, v->drag_start_x, v->drag_start_y, x, y,
                           color);
    save_after_edit(v);
    return;
  }
  if (event->type == KeyPress) {
    KeySym key = XLookupKeysym(&event->xkey, 0);
    if ((event->xkey.state & ControlMask) && !(event->xkey.state & ShiftMask) &&
        (key == XK_z || key == XK_Z)) {
      if (tl_manual_paint_undo(v->model) == 0) {
        save_layer(v);
        canvas_redraw(v);
        status_set(v, "Undo da camada raster.");
      }
    } else if (((event->xkey.state & ControlMask) &&
                (key == XK_y || key == XK_Y)) ||
               ((event->xkey.state & (ControlMask | ShiftMask)) ==
                    (ControlMask | ShiftMask) &&
                (key == XK_z || key == XK_Z))) {
      if (tl_manual_paint_redo(v->model) == 0) {
        save_layer(v);
        canvas_redraw(v);
        status_set(v, "Redo da camada raster.");
      }
    }
  }
}
static void select_context(TLManualPaintView *v) {
  if (tl_manual_paint_select_piece(
          v->model, v->family_index, v->control_index, v->state_index,
          (TLManualPaintPart)v->part_index,
          (TLManualPaintVariant)v->variant_index)) {
    status_set(v, "Plataforma, controle, peça, variante ou estado inválido; "
                  "conteúdo anterior preservado.");
    return;
  }
  dims_set(v);
  canvas_redraw(v);
  char message[320];
  snprintf(
      message, sizeof(message),
      "Editando raster: %s / %s / %s / %s / %s. Prévia nativa separada.",
      family_names[v->family_index], control_names[v->control_index],
      part_names[v->part_index], variant_names[v->variant_index],
      state_names[v->state_index]);
  status_set(v, message);
  if (v->recipe_output) {
    char recipe[512];
    if (v->family_index == TL_GTK4 &&
        !gtk4_control_translated(v->control_index))
      snprintf(recipe, sizeof(recipe),
               "%s / %s / %s / %s / %s: sem tradutor DomainOS (5/16).\n"
               "A arte manual pode ser editada; não há prévia temática nativa.",
               family_names[v->family_index], control_names[v->control_index],
               part_names[v->part_index], variant_names[v->variant_index],
               state_names[v->state_index]);
    else if (v->family_index == TL_GTK4 &&
             scrollbar_control(v->control_index) &&
             (v->part_index == TL_PAINT_PART_ARROW ||
              v->part_index == TL_PAINT_PART_ARROW_BUTTON))
      snprintf(recipe, sizeof(recipe),
               "%s / %s / %s / %s / %s: arte manual editável.\n"
               "GtkScrollbar não possui setas nativas; nenhuma seta é simulada.",
               family_names[v->family_index], control_names[v->control_index],
               part_names[v->part_index], variant_names[v->variant_index],
               state_names[v->state_index]);
    else if (v->family_index == TL_GTK4)
      snprintf(recipe, sizeof(recipe),
               "%s / %s / %s / %s / %s: tradutor DomainOS disponível (5/16).\n"
               "A captura nativa é somente leitura; o raster permanece separado.",
               family_names[v->family_index], control_names[v->control_index],
               part_names[v->part_index], variant_names[v->variant_index],
               state_names[v->state_index]);
    else
      snprintf(recipe, sizeof(recipe),
               "%s / %s / %s / %s / %s: raster separado da receita.\n"
               "A captura nativa, quando disponível, permanece somente leitura.",
               family_names[v->family_index], control_names[v->control_index],
               part_names[v->part_index], variant_names[v->variant_index],
               state_names[v->state_index]);
    text_content_set(v->recipe_output, recipe);
  }
}
static void combo_changed(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  int selected = combo_callback_index(w, call);
  if (v->updating || !call)
    return;
  /* Resolve the actual callback item against the widget's item table. Motif
   * variants can report the previous selectedPosition/item_position during
   * XmNselectionCallback; the compound item itself is unambiguous. */
  if (selected >= 0)
    combo_selection_apply(v, w, selected);
  v->pending_combo = w;
  v->pending_combo_selection = selected;
  if (v->combo_selection_timeout)
    XtRemoveTimeOut(v->combo_selection_timeout);
  v->combo_selection_timeout = XtAppAddTimeOut(
      XtWidgetToApplicationContext(v->shell), 0,
      combo_selection_after_commit, v);
}
static Widget combo_for_list(TLManualPaintView *v, Widget list) {
  Widget combos[6];
  if (!v || !list)
    return NULL;
  combos[0] = v->family;
  combos[1] = v->reference_family;
  combos[2] = v->control;
  combos[3] = v->part;
  combos[4] = v->variant;
  combos[5] = v->state;
  for (int i = 0; i < 6; ++i) {
    Widget internal = NULL;
    if (combos[i])
      XtVaGetValues(combos[i], XmNlist, &internal, NULL);
    if (internal == list)
      return combos[i];
  }
  return NULL;
}
static Widget combo_for_text_field(TLManualPaintView *v, Widget text_field) {
  Widget combos[6];
  if (!v || !text_field)
    return NULL;
  combos[0] = v->family;
  combos[1] = v->reference_family;
  combos[2] = v->control;
  combos[3] = v->part;
  combos[4] = v->variant;
  combos[5] = v->state;
  for (int i = 0; i < 6; ++i) {
    Widget internal = NULL;
    if (combos[i])
      XtVaGetValues(combos[i], XmNtextField, &internal, NULL);
    if (internal == text_field)
      return combos[i];
  }
  return NULL;
}
static void combo_list_changed(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  XmListCallbackStruct *selection = call;
  Widget combo;
  int selected;
  if (!v || v->updating || !selection)
    return;
  combo = combo_for_list(v, w);
  selected = selection->item_position - 1;
  if (combo) {
    combo_selection_apply(v, combo, selected);
    v->pending_combo = combo;
    v->pending_combo_selection = selected;
  }
}
static void combo_text_changed(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  Widget combo;
  int selected;
  (void)call;
  if (!v || v->updating)
    return;
  combo = combo_for_text_field(v, w);
  if (!combo)
    return;
  selected = combo_visible_index(combo);
  if (selected >= 0) {
    combo_selection_apply(v, combo, selected);
    v->pending_combo = combo;
    v->pending_combo_selection = selected;
  }
}
static Widget combo_for_interaction(TLManualPaintView *v, Widget widget) {
  Widget combos[6];
  if (!v || !widget)
    return NULL;
  combos[0] = v->family;
  combos[1] = v->reference_family;
  combos[2] = v->control;
  combos[3] = v->part;
  combos[4] = v->variant;
  combos[5] = v->state;
  for (int i = 0; i < 6; ++i) {
    Widget list = NULL, text_field = NULL;
    if (!combos[i])
      continue;
    XtVaGetValues(combos[i], XmNlist, &list, XmNtextField, &text_field, NULL);
    if (widget == combos[i] || widget == list || widget == text_field)
      return combos[i];
  }
  return NULL;
}
static void combo_interaction_event(Widget w, XtPointer client, XEvent *event,
                                    Boolean *cont) {
  TLManualPaintView *v = client;
  Widget combo;
  KeySym key;
  (void)cont;
  if (!v || v->updating || !event ||
      (event->type != ButtonRelease && event->type != KeyRelease))
    return;
  if (event->type == KeyRelease) {
    key = XLookupKeysym(&event->xkey, 0);
    if (key != XK_Return && key != XK_KP_Enter)
      return;
  }
  combo = combo_for_interaction(v, w);
  if (!combo)
    return;
  if (v->pending_combo != combo)
    v->pending_combo_selection = -1;
  v->pending_combo = combo;
  if (v->combo_selection_timeout)
    XtRemoveTimeOut(v->combo_selection_timeout);
  v->combo_selection_timeout = XtAppAddTimeOut(
      XtWidgetToApplicationContext(v->shell), 0,
      combo_selection_after_commit, v);
}
static void combo_list_callback_install(TLManualPaintView *v, Widget combo) {
  Widget list = NULL, text_field = NULL;
  if (!v || !combo)
    return;
  XtVaGetValues(combo, XmNlist, &list, XmNtextField, &text_field, NULL);
  if (list) {
    XtAddCallback(list, XmNsingleSelectionCallback, combo_list_changed, v);
    XtAddCallback(list, XmNbrowseSelectionCallback, combo_list_changed, v);
    XtAddCallback(list, XmNmultipleSelectionCallback, combo_list_changed, v);
    XtAddCallback(list, XmNextendedSelectionCallback, combo_list_changed, v);
    XtAddCallback(list, XmNdefaultActionCallback, combo_list_changed, v);
  }
  if (text_field)
    XtAddCallback(text_field, XmNvalueChangedCallback, combo_text_changed, v);
  XtAddEventHandler(combo, ButtonReleaseMask | KeyReleaseMask, False,
                    combo_interaction_event, v);
  if (list)
    XtAddEventHandler(list, ButtonReleaseMask | KeyReleaseMask, False,
                      combo_interaction_event, v);
  if (text_field)
    XtAddEventHandler(text_field, ButtonReleaseMask | KeyReleaseMask, False,
                      combo_interaction_event, v);
}
static void tool_selected(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  XmToggleButtonCallbackStruct *toggle = call;
  if (toggle && !toggle->set)
    return;
  for (int i = 0; i < 6; i++)
    if (w == v->tools[i]) {
      v->tool = i;
      break;
    }
  cursor_apply(v);
  char msg[128];
  snprintf(msg, sizeof(msg),
           "Ferramenta ativa: %s. A pintura modifica somente a camada raster.",
           v->tool == TL_PAINT_PENCIL      ? "lápis"
           : v->tool == TL_PAINT_ERASER    ? "borracha"
           : v->tool == TL_PAINT_LINE      ? "linha"
           : v->tool == TL_PAINT_RECTANGLE ? "retângulo"
           : v->tool == TL_PAINT_FILL      ? "preenchimento"
                                           : "pipeta");
  status_set(v, msg);
}
static void brush_role(Widget w, XtPointer client, XtPointer call) {
  PaintBinding *binding = client;
  TLManualPaintView *v = binding->view;
  int i = binding->value;
  (void)w;
  (void)call;
  v->brush_role = i;
  v->brush = ((uint32_t)(v->rgb[role_map[i]][0] / 257u) << 24) |
             ((uint32_t)(v->rgb[role_map[i]][1] / 257u) << 16) |
             ((uint32_t)(v->rgb[role_map[i]][2] / 257u) << 8) | 255u;
  tl_manual_paint_color(v->model, v->brush);
  status_set(v, "Pincel usa um papel dinâmico do esquema atual; raster não "
                "vira RGB final do tema.");
}
static void palette_apply(TLManualPaintView *v) {
  Display *dpy = XtDisplay(v->shell);
  Colormap cmap;
  XtVaGetValues(v->shell, XtNcolormap, &cmap, NULL);
  Pixel inherited;
  XtVaGetValues(v->shell, XtNbackground, &inherited, NULL);
  if (v->palette_pixel_allocated[PALETTE_COUNT]) {
    XFreeColors(dpy, cmap, &v->palette_pixels[PALETTE_COUNT], 1, 0);
    v->palette_pixel_allocated[PALETTE_COUNT] = 0;
  }
  for (int i = 0; i < ROLE_COUNT; i++) {
    if (v->palette_pixel_allocated[i]) {
      XFreeColors(dpy, cmap, &v->palette_pixels[i], 1, 0);
      v->palette_pixel_allocated[i] = 0;
    }
    XColor color = {.red = v->rgb[i][0],
                    .green = v->rgb[i][1],
                    .blue = v->rgb[i][2],
                    .flags = DoRed | DoGreen | DoBlue};
    if (XAllocColor(dpy, cmap, &color)) {
      v->palette_pixels[i] = color.pixel;
      v->palette_pixel_allocated[i] = 1;
    } else
      v->palette_pixels[i] =
          i == ROLE_FACE ? inherited : v->palette_pixels[ROLE_FACE];
  }
  if (v->palette_pixel_allocated[ROLE_FACE] &&
      v->palette_pixel_allocated[ROLE_SHADOW]) {
    XColor face, shadow, trough;
    face.pixel = v->palette_pixels[ROLE_FACE];
    shadow.pixel = v->palette_pixels[ROLE_SHADOW];
    XQueryColor(dpy, cmap, &face);
    XQueryColor(dpy, cmap, &shadow);
    trough.red = (unsigned short)(face.red * .85 + shadow.red * .15 + .5);
    trough.green = (unsigned short)(face.green * .85 + shadow.green * .15 + .5);
    trough.blue = (unsigned short)(face.blue * .85 + shadow.blue * .15 + .5);
    trough.flags = DoRed | DoGreen | DoBlue;
    if (XAllocColor(dpy, cmap, &trough)) {
      v->palette_pixels[PALETTE_COUNT] = trough.pixel;
      v->palette_pixel_allocated[PALETTE_COUNT] = 1;
    }
  }
  if (!v->palette_pixel_allocated[PALETTE_COUNT])
    v->palette_pixels[PALETTE_COUNT] = v->palette_pixels[ROLE_FACE];
  Pixel bg = v->palette_pixels[ROLE_FACE];
  XtVaSetValues(v->shell, XtNbackground, bg, NULL);
  XtVaSetValues(v->root, XmNbackground, bg, NULL);
  palette_widget(v->form, v->palette_pixels);
  cursor_palette(v);
  /* Selectors remain ordinary controls in the tools sidebar. Their chrome
   * follows Button/View roles; only the real menu band follows Header. */
  Widget header_combos[] = {v->family, v->reference_family, v->control,
                            v->part, v->variant, v->state};
  for (size_t i = 0; i < sizeof(header_combos) / sizeof(header_combos[0]); ++i)
    palette_widget(header_combos[i], v->palette_pixels);
  if (v->header_palette_valid) {
    for (int i = 0; i < 6; ++i) {
      if (v->header_pixel_allocated[i]) {
        XFreeColors(dpy, cmap, &v->header_pixels[i], 1, 0);
        v->header_pixel_allocated[i] = 0;
      }
      XColor color = {.red = v->header_rgb[i][0],
                      .green = v->header_rgb[i][1],
                      .blue = v->header_rgb[i][2],
                      .flags = DoRed | DoGreen | DoBlue};
      if (XAllocColor(dpy, cmap, &color)) {
        v->header_pixels[i] = color.pixel;
        v->header_pixel_allocated[i] = 1;
      } else
        v->header_pixels[i] = i == ROLE_TEXT
                                  ? v->palette_pixels[ROLE_TEXT]
                                  : v->palette_pixels[ROLE_FACE];
    }
    palette_header_widget(v->menu_bar, v->header_pixels);
  }
  XtVaSetValues(v->canvas, XmNbackground, v->palette_pixels[ROLE_VIEW], NULL);
  XtVaSetValues(v->reference_canvas, XmNbackground,
                v->palette_pixels[ROLE_VIEW],
                NULL);
  XtVaSetValues(v->native_canvas, XmNbackground, v->palette_pixels[ROLE_VIEW],
                NULL);
  for (int i = 0; i < PALETTE_COUNT; i++)
    XtVaSetValues(v->colors[i], XmNbackground, v->palette_pixels[role_map[i]],
                  NULL);
  Widget combos[] = {v->family, v->reference_family, v->control, v->part,
                     v->variant, v->state};
  for (size_t i = 0; i < sizeof(combos) / sizeof(combos[0]); i++) {
    Widget list = XtNameToWidget(combos[i], "*List");
    Widget text = XtNameToWidget(combos[i], "*Text");
    XmFontList font_list = NULL;
    XmRenderTable render_table = NULL;
    if (text)
      XtVaGetValues(text, XmNfontList, &font_list, XmNrenderTable,
                    &render_table, NULL);
    if (list) {
      if (font_list)
        XtVaSetValues(list, XmNfontList, font_list, NULL);
      if (render_table)
        XtVaSetValues(list, XmNrenderTable, render_table, NULL);
      palette_widget(list, v->palette_pixels);
      if (!v->combo_map_handlers_installed)
        XtAddEventHandler(list, StructureNotifyMask, False,
                          combo_list_map_event, v);
    }
  }
  v->combo_map_handlers_installed = 1;
  if (v->brush_role >= 0) {
    int role = role_map[v->brush_role];
    v->brush = ((uint32_t)(v->rgb[role][0] / 257u) << 24) |
               ((uint32_t)(v->rgb[role][1] / 257u) << 16) |
               ((uint32_t)(v->rgb[role][2] / 257u) << 8) | 255u;
    tl_manual_paint_color(v->model, v->brush);
  }
}
static void save_button(Widget w, XtPointer client, XtPointer call) {
  (void)w;
  (void)call;
  save_layer(client);
}
static void undo_button(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  (void)w;
  (void)call;
  if (tl_manual_paint_undo(v->model) == 0) {
    save_layer(v);
    canvas_redraw(v);
    status_set(v, "Undo da camada raster.");
  }
}
static void redo_button(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  (void)w;
  (void)call;
  if (tl_manual_paint_redo(v->model) == 0) {
    save_layer(v);
    canvas_redraw(v);
    status_set(v, "Redo da camada raster.");
  }
}
static void grid_button(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  (void)w;
  (void)call;
  v->grid = !v->grid;
  canvas_redraw(v);
  status_set(
      v,
      v->grid
          ? "Grade de edição ligada; coordenadas continuam em pixels de arte."
          : "Grade de edição desligada.");
}
static void zoom_button(Widget w, XtPointer client, XtPointer call) {
  PaintBinding *binding = client;
  TLManualPaintView *v = binding->view;
  int z = v->zoom + binding->value;
  (void)w;
  (void)call;
  if (z < 1)
    z = 1;
  if (z > 8)
    z = 8;
  v->zoom = z;
  dims_set(v);
  canvas_redraw(v);
}
static int sample_zoom_fits(const TLManualPaintView *v, int zoom) {
  const XImage *images[2] = {v->reference_sample, v->native_sample};
  for (size_t i = 0; i < sizeof(images) / sizeof(images[0]); ++i)
    if (images[i] && (images[i]->width * zoom > 4096 ||
                      images[i]->height * zoom > 2048))
      return 0;
  return 1;
}
static void sample_zoom_button(Widget w, XtPointer client, XtPointer call) {
  PaintBinding *binding = client;
  TLManualPaintView *v = binding->view;
  int zoom = v->sample_zoom + binding->value;
  (void)w;
  (void)call;
  if (zoom < 1)
    zoom = 1;
  if (zoom > 8)
    zoom = 8;
  if (!sample_zoom_fits(v, zoom)) {
    status_set(v, "Zoom das amostras limitado para preservar o canvas; "
                  "medidas nativas não foram alteradas.");
    return;
  }
  v->sample_zoom = zoom;
  sample_labels_and_sizes(v);
  samples_redraw(v);
  status_set(v, "Referência e prévia nativa usam o mesmo zoom visual; dimensões "
                "originais continuam indicadas nos títulos.");
}
typedef struct {
  unsigned long pixel;
  uint32_t rgba;
} SampleColor;
static int sample_pixels_rgba(TLManualPaintView *v, const XImage *sample,
                              uint32_t **result) {
  enum { SAMPLE_COLOR_CACHE = 256 };
  SampleColor cache[SAMPLE_COLOR_CACHE];
  size_t cache_count = 0, count;
  Colormap colormap;
  uint32_t *pixels;
  if (!v || !sample || !result)
    return -1;
  count = (size_t)sample->width * (size_t)sample->height;
  pixels = malloc(count * sizeof(*pixels));
  if (!pixels)
    return -1;
  XtVaGetValues(v->shell, XtNcolormap, &colormap, NULL);
  for (int y = 0; y < sample->height; ++y)
    for (int x = 0; x < sample->width; ++x) {
      unsigned long pixel = XGetPixel((XImage *)sample, x, y);
      uint32_t rgba = 0;
      size_t i;
      for (i = 0; i < cache_count; ++i)
        if (cache[i].pixel == pixel) {
          rgba = cache[i].rgba;
          break;
        }
      if (i == cache_count) {
        XColor color = {.pixel = pixel};
        if (!XQueryColor(XtDisplay(v->shell), colormap, &color)) {
          free(pixels);
          return -1;
        }
        rgba = ((uint32_t)(color.red / 257u) << 24) |
               ((uint32_t)(color.green / 257u) << 16) |
               ((uint32_t)(color.blue / 257u) << 8) | 255u;
        if (cache_count < SAMPLE_COLOR_CACHE)
          cache[cache_count++] = (SampleColor){pixel, rgba};
      }
      pixels[(size_t)y * (size_t)sample->width + (size_t)x] = rgba;
    }
  *result = pixels;
  return 0;
}
static void copy_sample_to_art(TLManualPaintView *v, const XImage *sample,
                               const char *source, int piece_specific) {
  uint32_t *pixels = NULL;
  int width, height;
  char message[320];
  if (!sample) {
    snprintf(message, sizeof(message),
             "%s indisponível; camada manual preservada.", source);
    status_set(v, message);
    return;
  }
  if (v->part_index != TL_PAINT_PART_WHOLE && !piece_specific) {
    snprintf(message, sizeof(message),
             "%s contém o controle inteiro, não a peça selecionada; "
             "nenhum recorte foi presumido.", source);
    status_set(v, message);
    return;
  }
  width = sample->width;
  height = sample->height;
  if (width < TL_PAINT_MIN_SIZE || width > TL_PAINT_MAX_WIDTH ||
      height < TL_PAINT_MIN_SIZE || height > TL_PAINT_MAX_HEIGHT) {
    snprintf(message, sizeof(message),
             "%s excede os limites editáveis; nenhuma camada foi "
             "substituída.", source);
    status_set(v, message);
    return;
  }
  if (sample_pixels_rgba(v, sample, &pixels) ||
      tl_manual_paint_replace(v->model, width, height, pixels)) {
    free(pixels);
    snprintf(message, sizeof(message),
             "Não foi possível copiar %s; camada e histórico anteriores "
             "foram preservados.", source);
    status_set(v, message);
    return;
  }
  free(pixels);
  v->dirty = 1;
  dims_set(v);
  canvas_redraw(v);
  if (save_layer(v))
    return;
  snprintf(message, sizeof(message),
           "%s copiada para a arte editável em um único passo de Undo; "
           "referências e receita não foram alteradas.", source);
  status_set(v, message);
}
static void copy_reference_button(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  char source[96];
  (void)w;
  (void)call;
  snprintf(source, sizeof(source), "a referência %s",
           reference_source_names[v->reference_family_index]);
  copy_sample_to_art(v, v->reference_sample, source,
                     v->reference_family_index == TL_PAINT_REFERENCE_R584 ||
                     v->reference_family_index == TL_GTK2 ||
                     v->reference_family_index == TL_GTK3 ||
                     v->reference_family_index == TL_GTK4);
}
static void copy_native_button(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  char source[96];
  (void)w;
  (void)call;
  snprintf(source, sizeof(source), "a prévia nativa %s",
           family_names[v->family_index]);
  copy_sample_to_art(v, v->native_sample, source,
                     v->family_index == TL_GTK2 ||
                     v->family_index == TL_GTK3 ||
                     v->family_index == TL_GTK4);
}
static void size_changed(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  XmScaleCallbackStruct *cb = call;
  int width = tl_manual_paint_width(v->model),
      height = tl_manual_paint_height(v->model);
  (void)w;
  if (cb && w == v->width_scale)
    width = cb->value;
  else if (cb)
    height = cb->value;
  if (tl_manual_paint_resize(v->model, width, height)) {
    status_set(
        v, "Dimensão inválida (8-512 x 8-256 px); tela anterior preservada.");
    dims_set(v);
    return;
  }
  save_layer(v);
  dims_set(v);
  canvas_redraw(v);
}
static void close_protocol(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  (void)w;
  (void)call;
  if (v->drawing) {
    v->drawing = 0;
    save_after_edit(v);
  } else if (v->dirty && save_layer(v))
    return;
  XtPopdown(v->shell);
}
static void resize_event(Widget w, XtPointer client, XEvent *event,
                         Boolean *cont) {
  TLManualPaintView *v = client;
  (void)w;
  (void)cont;
  if (event->type == MapNotify)
    cursor_apply(v);
  if (event->type == ConfigureNotify)
    canvas_redraw(v);
}

static Widget paint_menu_create(Widget menu_bar, const char *name,
                                const char *label, char mnemonic,
                                int position, const char *hint) {
  Widget popup = XmCreatePulldownMenu(menu_bar, (char *)name, NULL, 0);
  XmString title = text_compound(label);
  char cascade_name[96];
  (void)snprintf(cascade_name, sizeof(cascade_name), "%sCascade", name);
  Widget cascade = XtVaCreateManagedWidget(
      cascade_name, xmCascadeButtonWidgetClass, menu_bar, XmNlabelString, title,
      XmNsubMenuId, popup, XmNmnemonic, mnemonic, XmNpositionIndex, position,
      NULL);
  XmStringFree(title);
  tl_ui_hint(cascade, hint);
  return popup;
}

static Widget paint_menu_item(Widget menu, const char *name,
                              const char *label, const char *hint,
                              XtCallbackProc callback, XtPointer data) {
  XmString title = text_compound(label);
  Widget item = XtVaCreateManagedWidget(name, xmPushButtonWidgetClass, menu,
                                        XmNlabelString, title, NULL);
  XmStringFree(title);
  tl_ui_hint(item, hint);
  XtAddCallback(item, XmNactivateCallback, callback, data);
  return item;
}

static void paint_menu_separator(Widget menu, const char *name) {
  (void)XtVaCreateManagedWidget(name, xmSeparatorWidgetClass, menu, NULL);
}

static void paint_help_button(Widget w, XtPointer client, XtPointer call) {
  TLManualPaintView *v = client;
  (void)w;
  (void)call;
  status_set(v,
             "Fluxo: escolha alvo e referência, copie uma amostra se quiser, "
             "desenhe no canvas e salve. Dicas detalham unidade e limite.");
}

static void paint_menus_create(TLManualPaintView *v) {
  Widget file = paint_menu_create(
      v->menu_bar, "paintFileMenu", "Arquivo", 'A', 0,
      "Salva a camada raster ou fecha somente o editor de pintura manual.");
  Widget edit = paint_menu_create(
      v->menu_bar, "paintEditMenu", "Editar", 'E', 1,
      "Desfaz ou refaz operações raster inteiras sem alterar a receita do tema.");
  Widget display = paint_menu_create(
      v->menu_bar, "paintDisplayMenu", "Exibir", 'x', 2,
      "Alterna recursos de visualização que não mudam os pixels da arte.");
  Widget help = paint_menu_create(
      v->menu_bar, "paintHelpMenu", "Ajuda", 'j', 3,
      "Mostra o fluxo do editor; cada controle também possui uma dica detalhada.");
  Widget help_cascade = XtNameToWidget(v->menu_bar, "*paintHelpMenuCascade");
  if (help_cascade)
    XtVaSetValues(v->menu_bar, XmNmenuHelpWidget, help_cascade, NULL);
  paint_menu_item(file, "paintMenuSave", "Salvar",
                  "Grava atomicamente a camada raster complementar do projeto.",
                  save_button, v);
  paint_menu_separator(file, "paintFileSeparator");
  paint_menu_item(file, "paintMenuClose", "Fechar",
                  "Fecha somente este editor depois de preservar a camada.",
                  close_protocol, v);
  paint_menu_item(edit, "paintMenuUndo", "Desfazer",
                  "Desfaz uma operação raster inteira; atalho Ctrl+Z no canvas.",
                  undo_button, v);
  paint_menu_item(edit, "paintMenuRedo", "Refazer",
                  "Refaz uma operação raster; atalhos Ctrl+Y e Ctrl+Shift+Z no canvas.",
                  redo_button, v);
  paint_menu_item(display, "paintMenuGrid", "Alternar grade",
                  "Alterna somente a grade visual; pixels e escala 1:1 não mudam.",
                  grid_button, v);
  paint_menu_item(help, "paintMenuHelp", "Ajuda do editor",
                  "Resume o fluxo seguro no rodapé sem alterar a camada.",
                  paint_help_button, v);
}

TLManualPaintView *tl_manual_paint_view_open(
    Widget parent, const char *path, int family, int control, int state,
    const unsigned short rgb[6][3], XmFontList inherited_font,
    TLEditorStore *editors,
    TLManualPaintContextChanged changed, void *changed_context,
    TLManualPaintReferenceChanged reference_changed,
    void *reference_changed_context) {
  static const char *const tool_names[6] = {"Lápis",     "Borracha",  "Linha",
                                            "Retângulo", "Preencher", "Pipeta"};
  static const char *const tool_hints[6] = {
      "Desenha com o pincel atual. Um arrasto forma uma única ação para Undo.",
      "Apaga para transparência da camada raster; não pinta com cor fixa.",
      "Desenha uma linha entre o início e o fim do arrasto, em pixels de arte.",
      "Desenha o contorno de um retângulo em pixels de arte.",
      "Preenche a região contígua sob o clique com a cor do pincel.",
      "Copia a cor de um pixel do canvas para o pincel; não a grava como papel "
      "do KDE."};
  static const char *const color_hints[PALETTE_COUNT] = {
      "Seleciona o papel Texto atual do esquema para pintar somente a "
      "referência raster.",
      "Seleciona o papel Face atual do esquema para pintar somente a "
      "referência raster.",
      "Seleciona o papel Conteúdo atual do esquema para pintar somente a "
      "referência raster.",
      "Seleciona o papel Seleção atual do esquema para pintar somente a "
      "referência raster.",
      "Seleciona o papel Luz atual do esquema para pintar somente a referência "
      "raster.",
      "Seleciona o papel Sombra atual do esquema para pintar somente a "
      "referência raster."};
  TLManualPaintView *v = calloc(1, sizeof(*v));
  if (!v)
    return NULL;
  v->model = tl_manual_paint_new();
  v->zoom = PAINT_ZOOM;
  v->sample_zoom = PAINT_ZOOM;
  v->grid = 1;
  v->tool = TL_PAINT_PENCIL;
  v->brush_role = ROLE_TEXT;
  v->context_changed = changed;
  v->context_changed_context = changed_context;
  v->reference_changed = reference_changed;
  v->reference_changed_context = reference_changed_context;
  v->reference_family_index = TL_MOTIF;
  v->pending_combo_selection = -1;
  v->editors = editors;
  if (!v->model || !path || strlen(path) >= sizeof(v->path)) {
    tl_manual_paint_free(v->model);
    free(v);
    return NULL;
  }
  strcpy(v->path, path);
  char load_error[256] = "Não foi possível validar o arquivo da camada.";
  if (tl_manual_paint_load(v->model, path, load_error, sizeof(load_error))) {
    tl_manual_paint_recovery_error(parent, load_error, path, editors);
    tl_manual_paint_free(v->model);
    free(v);
    return NULL;
  }
  Pixel parent_background;
  XtVaGetValues(parent, XmNbackground, &parent_background, NULL);
  v->shell = XtVaCreatePopupShell(
      "manualPaintEditor", topLevelShellWidgetClass, parent, XmNtitle,
      "Theme Lab - Editor de pintura manual", XtNbackground, parent_background,
      XtNwidth, 1500, XtNheight, 850, XtNminWidth, 1100, XtNminHeight, 650,
      XmNdeleteResponse, XmDO_NOTHING, NULL);
  v->root = XtVaCreateManagedWidget(
      "manualPaintRoot", xmFormWidgetClass, v->shell, XmNfractionBase, 100,
      XmNmarginWidth, 0, XmNmarginHeight, 0, NULL);
  v->menu_bar = XmCreateMenuBar(v->root, "manualPaintMenuBar", NULL, 0);
  XtVaSetValues(v->menu_bar, XmNleftAttachment, XmATTACH_FORM,
                XmNrightAttachment, XmATTACH_FORM,
                XmNtopAttachment, XmATTACH_FORM, NULL);
  XtManageChild(v->menu_bar);
  paint_menus_create(v);
  v->form = XtVaCreateManagedWidget(
      "manualPaintForm", xmFormWidgetClass, v->root, XmNfractionBase, 100,
      XmNmarginWidth, 8, XmNmarginHeight, 8,
      XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM,
      XmNtopAttachment, XmATTACH_WIDGET, XmNtopWidget, v->menu_bar,
      XmNbottomAttachment, XmATTACH_FORM, NULL);
  Widget sidebar_scroll = XtVaCreateManagedWidget(
      "manualPaintSidebarScroll", xmScrolledWindowWidgetClass, v->form,
      XmNscrollingPolicy, XmAUTOMATIC,
      XmNscrollBarDisplayPolicy, XmAS_NEEDED,
      XmNleftAttachment, XmATTACH_FORM,
      XmNrightAttachment, XmATTACH_POSITION, XmNrightPosition, 26,
      XmNtopAttachment, XmATTACH_FORM, XmNbottomAttachment, XmATTACH_FORM,
      NULL);
  v->sidebar = XtVaCreateManagedWidget(
      "manualPaintSidebar", xmRowColumnWidgetClass, sidebar_scroll,
      XmNorientation, XmVERTICAL, XmNpacking, XmPACK_TIGHT,
      XmNspacing, 7, XmNmarginWidth, 5, XmNmarginHeight, 5,
      XmNwidth, 380, NULL);
  v->main_panel = XtVaCreateManagedWidget(
      "manualPaintMain", xmFormWidgetClass, v->form, XmNfractionBase, 100,
      XmNleftAttachment, XmATTACH_POSITION, XmNleftPosition, 26,
      XmNleftOffset, 7, XmNrightAttachment, XmATTACH_FORM,
      XmNtopAttachment, XmATTACH_FORM, XmNbottomAttachment, XmATTACH_FORM,
      NULL);
  v->header = XtVaCreateManagedWidget(
      "manualPaintSelectors", xmRowColumnWidgetClass, v->sidebar, XmNorientation,
      XmVERTICAL, XmNpacking, XmPACK_TIGHT, XmNspacing, 3, NULL);
  v->header_labels[0] =
      label_new(v->header, "familyLabel", "Plataforma da arte");
  v->family = combo_new(v->header, "paintFamily", family_names, TL_FAMILY_COUNT);
  v->header_labels[1] =
      label_new(v->header, "referenceFamilyLabel", "Fonte da referência");
  v->reference_family = combo_new(v->header, "paintReferenceFamily",
                                  reference_source_names,
                                  TL_PAINT_REFERENCE_COUNT);
  v->header_labels[2] = label_new(v->header, "controlLabel", "Controle");
  v->control = combo_new(v->header, "paintControl", control_names, TL_CONTROL_COUNT);
  v->header_labels[3] = label_new(v->header, "partLabel", "Peça");
  v->part = combo_new(v->header, "paintPart", part_names, TL_PAINT_PART_COUNT);
  v->header_labels[4] = label_new(v->header, "variantLabel", "Variante");
  v->variant = combo_new(v->header, "paintVariant", variant_names,
                         TL_PAINT_VARIANT_COUNT);
  v->header_labels[5] = label_new(v->header, "stateLabel", "Estado");
  v->state = combo_new(v->header, "paintState", state_names, STATE_COUNT);
  tl_ui_hint(v->family,
             "Família dona da camada raster. A pintura não transforma sozinha "
             "o bitmap em receita GTK/Qt/Plasma.");
  tl_ui_hint(v->reference_family,
             "Escolhe independentemente a família mostrada à esquerda como "
             "referência. Não muda a plataforma nem a camada que está sendo "
             "editada; famílias sem rota nativa aparecem como indisponíveis. "
             "GTK2 R584 mostra somente assets comprovados pelo manifesto da "
             "revisão, nunca uma renderização histórica ou nativa inventada.");
  tl_ui_hint(v->control, "Componente que identifica esta camada. Cada família, "
                         "controle e estado mantém sua própria imagem.");
  tl_ui_hint(v->part,
             "Escolhe o controle inteiro ou uma peça independente da barra. "
             "Seta, trilho e cursor mantêm desenhos e Undo separados.");
  tl_ui_hint(v->variant,
             "Distingue extremidade ou segmento da peça: inicial/final, "
             "direção e antes/depois do cursor conforme a orientação.");
  tl_ui_hint(v->state, "Estado visual da camada: normal, hover, pressionado, "
                       "desabilitado ou backdrop.");
  Widget form = v->main_panel;
  Widget sidebar = v->sidebar;
  Widget toolrow = XtVaCreateManagedWidget(
      "manualPaintTools", xmRowColumnWidgetClass, sidebar, XmNorientation,
      XmHORIZONTAL, XmNpacking, XmPACK_COLUMN, XmNnumColumns, 5,
      XmNspacing, 4, XmNradioBehavior, True,
      XmNradioAlwaysOne, True, NULL);
  for (int i = 0; i < 6; i++) {
    v->tools[i] = XtVaCreateManagedWidget(
        "paintTool", xmToggleButtonWidgetClass, toolrow, XmNindicatorOn, False,
        XmNfillOnSelect, True, XmNset, i == TL_PAINT_PENCIL, NULL);
    text_set(v->tools[i], tool_names[i]);
    tl_ui_hint(v->tools[i], tool_hints[i]);
    XtAddCallback(v->tools[i], XmNvalueChangedCallback, tool_selected, v);
  }
  for (int i = 0; i < PALETTE_COUNT; i++) {
    v->colors[i] = XtVaCreateManagedWidget("paintRole", xmPushButtonWidgetClass,
                                           toolrow, NULL);
    text_set(v->colors[i], palette_names[i]);
    tl_ui_hint(v->colors[i], color_hints[i]);
  }
  Widget grid = XtVaCreateManagedWidget("paintGrid", xmPushButtonWidgetClass,
                                        toolrow, NULL);
  text_set(grid, "Grade");
  tl_ui_hint(grid, "Alterna a grade visual. A grade não altera pixels, escala "
                   "nem o valor 1:1.");
  XtAddCallback(grid, XmNactivateCallback, grid_button, v);
  Widget minus = XtVaCreateManagedWidget(
      "paintZoomOut", xmPushButtonWidgetClass, toolrow, NULL);
  text_set(minus, "-");
  tl_ui_hint(minus, "Reduz o zoom de trabalho entre 1x e 8x. Não redimensiona "
                    "a arte nem sua medida em pixels.");
  v->zoom_bindings[0] = (PaintBinding){v, -1};
  XtAddCallback(minus, XmNactivateCallback, zoom_button, &v->zoom_bindings[0]);
  Widget plus = XtVaCreateManagedWidget("paintZoomIn", xmPushButtonWidgetClass,
                                        toolrow, NULL);
  text_set(plus, "+");
  tl_ui_hint(plus, "Aumenta o zoom de trabalho entre 1x e 8x. Não redimensiona "
                   "a arte nem sua medida em pixels.");
  v->zoom_bindings[1] = (PaintBinding){v, 1};
  XtAddCallback(plus, XmNactivateCallback, zoom_button, &v->zoom_bindings[1]);
  Widget flow_hint = label_new(
      form, "paintFlowHint",
      "1. Escolha a referência   2. Copie a referência ou a prévia nativa   "
      "3. Escolha ferramenta e desenhe na arte à direita");
  XtVaSetValues(flow_hint, XmNleftAttachment, XmATTACH_FORM,
                XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment,
                XmATTACH_FORM, NULL);
  Widget probe_sizes = XtVaCreateManagedWidget(
      "paintNativeProbeDimensions", xmRowColumnWidgetClass, sidebar,
      XmNorientation, XmVERTICAL, XmNpacking, XmPACK_TIGHT,
      XmNspacing, 5, NULL);
  XmString probe_length_title =
      text_compound("Ensaio nativo: comprimento (px)");
  v->probe_length_scale = XtVaCreateManagedWidget(
      "paintProbeLength", xmScaleWidgetClass, probe_sizes, XmNorientation,
      XmHORIZONTAL, XmNminimum, 15, XmNmaximum, 512, XmNvalue, 120,
      XmNshowValue, True, XmNtitleString, probe_length_title, XmNwidth, 350,
      NULL);
  XmStringFree(probe_length_title);
  XmString probe_thickness_title = text_compound("Espessura solicitada (px)");
  v->probe_thickness_scale = XtVaCreateManagedWidget(
      "paintProbeThickness", xmScaleWidgetClass, probe_sizes, XmNorientation,
      XmHORIZONTAL, XmNminimum, 1, XmNmaximum, 64, XmNvalue, 15,
      XmNshowValue, True, XmNtitleString, probe_thickness_title, XmNwidth, 350,
      NULL);
  XmStringFree(probe_thickness_title);
  XmString probe_value_title = text_compound("Posição do cursor (0–100)");
  v->probe_value_scale = XtVaCreateManagedWidget(
      "paintProbeValue", xmScaleWidgetClass, probe_sizes, XmNorientation,
      XmHORIZONTAL, XmNminimum, 0, XmNmaximum, 75, XmNvalue, 25,
      XmNshowValue, True, XmNtitleString, probe_value_title, XmNwidth, 350,
      NULL);
  XmStringFree(probe_value_title);
  XmString probe_page_title = text_compound("Página visível / thumb (1–100)");
  v->probe_page_scale = XtVaCreateManagedWidget(
      "paintProbePage", xmScaleWidgetClass, probe_sizes, XmNorientation,
      XmHORIZONTAL, XmNminimum, 1, XmNmaximum, 100, XmNvalue, 25,
      XmNshowValue, True, XmNtitleString, probe_page_title, XmNwidth, 350, NULL);
  XmStringFree(probe_page_title);
  tl_ui_numeric_hint(
      v->probe_length_scale,
      "Comprimento privado da barra nativa em pixels. Altera somente a amostra; "
      "não redimensiona a arte nem modifica scene.json.");
  tl_ui_numeric_hint(
      v->probe_thickness_scale,
      "Espessura solicitada ao toolkit em pixels. A medida efetiva aparece na "
      "captura e pode obedecer ao mínimo nativo.");
  tl_ui_numeric_hint(
      v->probe_value_scale,
      "Posição no intervalo privado 0–100; o máximo acompanha a página visível.");
  tl_ui_numeric_hint(
      v->probe_page_scale,
      "Página visível no intervalo privado 0–100. O toolkit calcula o tamanho "
      "do thumb a partir deste valor.");
  Widget sizes = XtVaCreateManagedWidget(
      "paintDimensions", xmRowColumnWidgetClass, sidebar, XmNorientation,
      XmVERTICAL, XmNpacking, XmPACK_TIGHT, XmNspacing, 8,
      XmNmarginHeight, 6, NULL);
  v->dimensions = label_new(sizes, "paintDimensionLabel",
                            "Camada raster em pixels de arte; zoom separado.");
  XmString width_title = text_compound("Largura da arte (px)");
  v->width_scale = XtVaCreateManagedWidget(
      "paintWidth", xmScaleWidgetClass, sizes, XmNorientation, XmHORIZONTAL,
      XmNminimum, 8, XmNmaximum, 512, XmNshowValue, True, XmNtitleString,
      width_title, NULL);
  XmStringFree(width_title);
  XmString height_title = text_compound("Altura da arte (px)");
  v->height_scale = XtVaCreateManagedWidget(
      "paintHeight", xmScaleWidgetClass, sizes, XmNorientation, XmHORIZONTAL,
      XmNminimum, 8, XmNmaximum, 256, XmNshowValue, True, XmNtitleString,
      height_title, NULL);
  XmStringFree(height_title);
  tl_ui_numeric_hint(v->width_scale,
                     "Largura da arte: 8-512 px; reduzir recorta, ampliar "
                     "cria área vazia.");
  tl_ui_numeric_hint(v->height_scale,
                     "Altura da arte: 8-256 px; reduzir recorta, ampliar "
                     "cria área vazia.");
  v->reference_label = label_new(sidebar, "referenceSampleLabel",
                                 "Referência: escala 4:1");
  Widget reference_scroll = XtVaCreateManagedWidget(
      "referenceSampleScroll", xmScrolledWindowWidgetClass, sidebar,
      XmNscrollingPolicy, XmAUTOMATIC, XmNscrollBarDisplayPolicy, XmAS_NEEDED,
      XmNwidth, 350, XmNheight, 150, NULL);
  v->reference_canvas = XtVaCreateManagedWidget(
      "referenceSampleCanvas", xmDrawingAreaWidgetClass, reference_scroll,
      XmNwidth, 320, XmNheight, 130, XmNresizePolicy, XmRESIZE_NONE, NULL);
  tl_ui_hint(v->reference_label,
             "Referência selecionável, somente leitura; compare forma e "
             "medidas no zoom compartilhado. Use Copiar referência somente "
             "quando quiser editar uma cópia.");
  tl_ui_surface_hint(v->reference_canvas, v->reference_label);
  v->copy_reference = XtVaCreateManagedWidget(
      "paintCopyReference", xmPushButtonWidgetClass, sidebar,
      XmNsensitive, False, NULL);
  text_set(v->copy_reference, "Copiar referência");
  tl_ui_hint(v->copy_reference,
             "Substitui explicitamente a peça selecionada pela imagem exibida "
             "na referência, como um único passo de Undo. Fontes sem captura "
             "de peça exigem Controle inteiro. Não altera a prévia nativa nem "
             "a receita do tema.");
  XtAddCallback(v->copy_reference, XmNactivateCallback,
                copy_reference_button, v);
  v->native_label = label_new(sidebar, "nativeSampleLabel",
                              "Prévia nativa: escala 4:1");
  Widget native_scroll = XtVaCreateManagedWidget(
      "nativeSampleScroll", xmScrolledWindowWidgetClass, sidebar,
      XmNscrollingPolicy, XmAUTOMATIC, XmNscrollBarDisplayPolicy, XmAS_NEEDED,
      XmNwidth, 350, XmNheight, 150, NULL);
  v->native_canvas = XtVaCreateManagedWidget(
      "nativeSampleCanvas", xmDrawingAreaWidgetClass, native_scroll,
      XmNwidth, 320, XmNheight, 130, XmNresizePolicy, XmRESIZE_NONE, NULL);
  tl_ui_hint(v->native_label,
             "Prévia nativa atual, somente leitura; compare com a referência "
             "no mesmo zoom explícito.");
  tl_ui_surface_hint(v->native_canvas, v->native_label);
  v->copy_native = XtVaCreateManagedWidget(
      "paintCopyNative", xmPushButtonWidgetClass, sidebar,
      XmNsensitive, False, NULL);
  text_set(v->copy_native, "Copiar prévia nativa");
  tl_ui_hint(v->copy_native,
             "Substitui a peça selecionada pela captura nativa, como um único "
             "passo de Undo; a captura deve corresponder à peça. Não altera a "
             "fonte da referência nem a receita do tema.");
  XtAddCallback(v->copy_native, XmNactivateCallback, copy_native_button, v);
  XtAddCallback(v->reference_canvas, XmNexposeCallback, sample_draw, v);
  XtAddCallback(v->native_canvas, XmNexposeCallback, sample_draw, v);
  Widget actions = XtVaCreateManagedWidget(
      "paintActions", xmRowColumnWidgetClass, form, XmNorientation,
      XmHORIZONTAL, XmNpacking, XmPACK_TIGHT, XmNleftAttachment, XmATTACH_FORM,
      XmNrightAttachment, XmATTACH_FORM, XmNbottomAttachment, XmATTACH_FORM,
      XmNspacing, 5, NULL);
  Widget undo = XtVaCreateManagedWidget("paintUndo", xmPushButtonWidgetClass,
                                        actions, NULL);
  text_set(undo, "Desfazer");
  tl_ui_hint(undo, "Desfaz uma operação raster inteira (Ctrl+Z); não desfaz "
                   "alterações na receita do Theme Lab.");
  XtAddCallback(undo, XmNactivateCallback, undo_button, v);
  Widget redo = XtVaCreateManagedWidget("paintRedo", xmPushButtonWidgetClass,
                                        actions, NULL);
  text_set(redo, "Refazer");
  tl_ui_hint(redo, "Refaz uma operação raster desfeita (Ctrl+Y); o histórico é "
                   "independente da receita.");
  XtAddCallback(redo, XmNactivateCallback, redo_button, v);
  Widget sample_minus = XtVaCreateManagedWidget(
      "paintSampleZoomOut", xmPushButtonWidgetClass, actions, NULL);
  text_set(sample_minus, "Amostras -");
  tl_ui_hint(sample_minus,
             "Reduz somente o zoom visual compartilhado por referência e prévia "
             "nativa. As dimensões originais não mudam.");
  v->sample_zoom_bindings[0] = (PaintBinding){v, -1};
  XtAddCallback(sample_minus, XmNactivateCallback, sample_zoom_button,
                &v->sample_zoom_bindings[0]);
  Widget sample_plus = XtVaCreateManagedWidget(
      "paintSampleZoomIn", xmPushButtonWidgetClass, actions, NULL);
  text_set(sample_plus, "Amostras +");
  tl_ui_hint(sample_plus,
             "Amplia igualmente referência e prévia nativa até 8:1, mantendo "
             "coordenadas correspondentes.");
  v->sample_zoom_bindings[1] = (PaintBinding){v, 1};
  XtAddCallback(sample_plus, XmNactivateCallback, sample_zoom_button,
                &v->sample_zoom_bindings[1]);
  Widget save = XtVaCreateManagedWidget("paintSave", xmPushButtonWidgetClass,
                                        actions, NULL);
  text_set(save, "Salvar");
  tl_ui_hint(save, "Grava atomicamente a camada raster no arquivo complementar "
                   "do projeto, separado do JSON da Prancheta.");
  XtAddCallback(save, XmNactivateCallback, save_button, v);
  Widget close = XtVaCreateManagedWidget("paintClose", xmPushButtonWidgetClass,
                                         actions, NULL);
  text_set(close, "Fechar");
  tl_ui_hint(close, "Fecha o editor depois de salvar a camada raster.");
  XtAddCallback(close, XmNactivateCallback, close_protocol, v);
  v->status = label_new(form, "paintStatus",
                        "Camada raster independente; receita não alterada.");
  XtVaSetValues(v->status, XmNleftAttachment, XmATTACH_FORM,
                XmNrightAttachment, XmATTACH_FORM, XmNbottomAttachment,
                XmATTACH_WIDGET, XmNbottomWidget, actions, XmNbottomOffset, 3,
                NULL);
  v->raster_note = label_new(
      form, "paintRasterBoundary",
      "Camada raster é arte separada, não render do toolkit. O estado vale para "
      "ela; a amostra nativa mostra a captura atual.");
  XtVaSetValues(v->raster_note, XmNleftAttachment, XmATTACH_FORM,
                XmNrightAttachment, XmATTACH_FORM, XmNbottomAttachment,
                XmATTACH_WIDGET, XmNbottomWidget, v->status, XmNbottomOffset, 3,
                NULL);
  Widget paint_label =
      label_new(form, "manualSampleLabel", "Camada manual: pixels de arte");
  XtVaSetValues(paint_label, XmNleftAttachment, XmATTACH_FORM,
                XmNrightAttachment, XmATTACH_FORM,
                XmNtopAttachment, XmATTACH_WIDGET, XmNtopWidget, flow_hint,
                XmNtopOffset, 5, NULL);
  v->recipe_output = XtVaCreateManagedWidget(
      "paintRecipeOutput", xmTextWidgetClass, form, XmNeditMode,
      XmMULTI_LINE_EDIT, XmNeditable, False, XmNcursorPositionVisible, False,
      XmNrows, 2, XmNwordWrap, True, XmNscrollHorizontal, False,
      XmNscrollVertical, False, XmNleftAttachment, XmATTACH_FORM,
      XmNrightAttachment, XmATTACH_FORM, XmNtopAttachment,
      XmATTACH_WIDGET, XmNtopWidget, paint_label, XmNheight, 44, NULL);
  tl_ui_hint(
      v->recipe_output,
      "Saída somente leitura para o controle e estado escolhidos. A pintura "
      "raster só será convertida quando houver mapeamento nativo verificável.");
  v->scroll = XtVaCreateManagedWidget(
      "paintCanvasScroll", xmScrolledWindowWidgetClass, form,
      XmNscrollingPolicy, XmAUTOMATIC, XmNscrollBarDisplayPolicy, XmAS_NEEDED,
      XmNleftAttachment, XmATTACH_FORM, XmNrightAttachment, XmATTACH_FORM,
      XmNtopAttachment, XmATTACH_WIDGET,
      XmNtopWidget, v->recipe_output, XmNbottomAttachment, XmATTACH_WIDGET,
      XmNbottomWidget, v->raster_note, XmNbottomOffset, 3, NULL);
  v->canvas = XtVaCreateManagedWidget(
      "manualPaintCanvas", xmDrawingAreaWidgetClass, v->scroll, XmNwidth, 96,
      XmNheight, 32, XmNresizePolicy, XmRESIZE_NONE, NULL);
  tl_ui_hint(paint_label,
             "Camada raster: clique ou arraste conforme a ferramenta; pixels "
             "de arte e zoom separado.");
  tl_ui_surface_hint(v->canvas, paint_label);
  XtVaSetValues(v->canvas, XmNtraversalOn, True, XmNnavigationType, XmTAB_GROUP,
                NULL);
  XtAddCallback(v->canvas, XmNexposeCallback, canvas_draw, v);
  XtAddEventHandler(v->canvas,
                    ButtonPressMask | ButtonReleaseMask | ButtonMotionMask |
                        KeyPressMask,
                    False, canvas_event, v);
  XtAddEventHandler(v->canvas, StructureNotifyMask, False, resize_event, v);
  XtAddCallback(v->family, XmNselectionCallback, combo_changed, v);
  XtAddCallback(v->reference_family, XmNselectionCallback, combo_changed, v);
  XtAddCallback(v->control, XmNselectionCallback, combo_changed, v);
  XtAddCallback(v->part, XmNselectionCallback, combo_changed, v);
  XtAddCallback(v->variant, XmNselectionCallback, combo_changed, v);
  XtAddCallback(v->state, XmNselectionCallback, combo_changed, v);
  combo_list_callback_install(v, v->family);
  combo_list_callback_install(v, v->reference_family);
  combo_list_callback_install(v, v->control);
  combo_list_callback_install(v, v->part);
  combo_list_callback_install(v, v->variant);
  combo_list_callback_install(v, v->state);
  XtAddCallback(v->width_scale, XmNvalueChangedCallback, size_changed, v);
  XtAddCallback(v->height_scale, XmNvalueChangedCallback, size_changed, v);
  XtAddCallback(v->probe_length_scale, XmNvalueChangedCallback, probe_changed,
                v);
  XtAddCallback(v->probe_thickness_scale, XmNvalueChangedCallback,
                probe_changed, v);
  XtAddCallback(v->probe_value_scale, XmNvalueChangedCallback, probe_changed,
                v);
  XtAddCallback(v->probe_page_scale, XmNvalueChangedCallback, probe_changed,
                v);
  v->family_index = family;
  v->control_index = control;
  v->state_index = state;
  v->part_index = TL_PAINT_PART_WHOLE;
  v->variant_index = TL_PAINT_VARIANT_AUTO;
  control_combo_refresh(v);
  piece_context_refresh(v, 1);
  probe_controls_update(v, 1);
  tl_manual_paint_select_piece(v->model, family, control, state,
                               TL_PAINT_PART_WHOLE,
                               TL_PAINT_VARIANT_AUTO);
  tl_manual_paint_color(v->model, 0u);
  v->brush = 0u;
  if (rgb)
    memcpy(v->rgb, rgb, sizeof(v->rgb));
  else
    native_role_rgb(v);
  for (int i = 0; i < PALETTE_COUNT; i++) {
    v->role_bindings[i] = (PaintBinding){v, i};
    XtAddCallback(v->colors[i], XmNactivateCallback, brush_role,
                  &v->role_bindings[i]);
  }
  palette_apply(v);
  if (!inherited_font) {
    v->fallback_core_font = XLoadQueryFont(XtDisplay(v->shell), "fixed");
    if (v->fallback_core_font) {
      v->fallback_font = XmFontListCreate(v->fallback_core_font,
                                          XmFONTLIST_DEFAULT_TAG);
      inherited_font = v->fallback_font;
    }
  }
  font_widget(v->root, inherited_font);
  select_context(v);
  v->updating = 1;
  XtVaSetValues(v->family, XmNselectedPosition, family, NULL);
  XtVaSetValues(v->reference_family, XmNselectedPosition,
                v->reference_family_index, NULL);
  XtVaSetValues(v->control, XmNselectedPosition, control, NULL);
  XtVaSetValues(v->part, XmNselectedPosition, v->part_index, NULL);
  XtVaSetValues(v->state, XmNselectedPosition, state, NULL);
  v->updating = 0;
  tl_ui_hints_shell(v->shell);
  tl_ui_scroll_hints(v->shell);
  Atom wm_delete = XmInternAtom(XtDisplay(v->shell), "WM_DELETE_WINDOW", False);
  XmAddWMProtocolCallback(v->shell, wm_delete, close_protocol, v);
  return v;
}
void tl_manual_paint_view_context(TLManualPaintView *v, int family, int control,
                                  int state) {
  if (!v || family < 0 || family >= TL_FAMILY_COUNT || control < 0 ||
      control >= TL_CONTROL_COUNT || state < 0 || state >= STATE_COUNT)
    return;
  if (v->family_index == family && v->control_index == control &&
      v->state_index == state)
    return;
  v->family_index = family;
  v->control_index = control;
  v->state_index = state;
  v->part_index = TL_PAINT_PART_WHOLE;
  v->variant_index = TL_PAINT_VARIANT_AUTO;
  control_combo_refresh(v);
  piece_context_refresh(v, 1);
  probe_controls_update(v, 1);
  v->updating = 1;
  XtVaSetValues(v->family, XmNselectedPosition, family, NULL);
  XtVaSetValues(v->control, XmNselectedPosition, control, NULL);
  XtVaSetValues(v->part, XmNselectedPosition, v->part_index, NULL);
  XtVaSetValues(v->state, XmNselectedPosition, state, NULL);
  v->updating = 0;
  select_context(v);
  if (v->context_changed)
    v->context_changed(v->context_changed_context, family, control, state);
  probe_send(v);
  reference_send(v);
  canvas_redraw(v);
}
void tl_manual_paint_view_present(TLManualPaintView *v) {
  if (v && v->shell) {
    XtPopup(v->shell, XtGrabNone);
    v->sample_request_ready = 1;
    probe_send(v);
    reference_send(v);
    cursor_apply(v);
    canvas_redraw(v);
  }
}
int tl_manual_paint_view_is_visible(const TLManualPaintView *v) {
  XWindowAttributes attributes;
  if (!v || !v->shell || !XtIsRealized(v->shell))
    return 0;
  if (!XGetWindowAttributes(XtDisplay(v->shell), XtWindow(v->shell),
                            &attributes))
    return 0;
  return attributes.map_state == IsViewable;
}
void tl_manual_paint_view_palette(TLManualPaintView *v,
                                  const unsigned short rgb[6][3]) {
  if (!v || !rgb)
    return;
  memcpy(v->rgb, rgb, sizeof(v->rgb));
  palette_apply(v);
}
void tl_manual_paint_view_header_palette(TLManualPaintView *v,
                                         const unsigned short rgb[6][3]) {
  if (!v || !rgb)
    return;
  memcpy(v->header_rgb, rgb, sizeof(v->header_rgb));
  v->header_palette_valid = 1;
  palette_apply(v);
}
void tl_manual_paint_view_palettes(TLManualPaintView *v,
                                   const unsigned short body[6][3],
                                   const unsigned short header[6][3]) {
  if (!v || !body || !header)
    return;
  memcpy(v->rgb, body, sizeof(v->rgb));
  memcpy(v->header_rgb, header, sizeof(v->header_rgb));
  v->header_palette_valid = 1;
  palette_apply(v);
}
void tl_manual_paint_view_samples(TLManualPaintView *v, int reference_source,
                                  XImage *reference, XImage *native) {
  if (!v) {
    if (reference)
      XDestroyImage(reference);
    if (native)
      XDestroyImage(native);
    return;
  }
  if (v->reference_sample)
    XDestroyImage(v->reference_sample);
  if (v->native_sample)
    XDestroyImage(v->native_sample);
  v->reference_sample = reference;
  v->native_sample = native;
  if (reference_source >= 0 &&
      reference_source < TL_PAINT_REFERENCE_COUNT) {
    v->reference_family_index = reference_source;
    v->updating = 1;
    XtVaSetValues(v->reference_family, XmNselectedPosition, reference_source,
                  NULL);
    v->updating = 0;
  }
  if (v->copy_reference)
    XtSetSensitive(v->copy_reference, reference != NULL);
  if (v->copy_native)
    XtSetSensitive(v->copy_native, native != NULL);
  sample_labels_and_sizes(v);
  samples_redraw(v);
}
void tl_manual_paint_view_notice(TLManualPaintView *v, const char *message) {
  status_set(v, message ? message : "");
}
int tl_manual_paint_view_checkpoint(TLManualPaintView *v) {
  return v && v->dirty ? save_layer(v) : 0;
}
void tl_manual_paint_view_close(TLManualPaintView *v) {
  if (!v)
    return;
  if (v->dirty && save_layer(v))
    return;
  if (v->combo_selection_timeout) {
    XtRemoveTimeOut(v->combo_selection_timeout);
    v->combo_selection_timeout = 0;
  }
  Display *dpy = XtDisplay(v->shell);
  Colormap cmap;
  XtVaGetValues(v->shell, XtNcolormap, &cmap, NULL);
  for (size_t i = 0; i < v->cache_capacity; i++)
    if (v->cache[i].used)
      XFreeColors(dpy, cmap, &v->cache[i].pixel, 1, 0);
  for (int i = 0; i < PALETTE_COUNT + 1; i++)
    if (v->palette_pixel_allocated[i])
      XFreeColors(dpy, cmap, &v->palette_pixels[i], 1, 0);
  for (int i = 0; i < 6; ++i)
    if (v->header_pixel_allocated[i])
      XFreeColors(dpy, cmap, &v->header_pixels[i], 1, 0);
  if (v->cursors_ready)
    for (int i = 0; i < 6; ++i)
      if (v->tool_cursors[i] != None)
        XFreeCursor(dpy, v->tool_cursors[i]);
  free(v->cache);
  sample_display_clear(v);
  if (v->reference_sample)
    XDestroyImage(v->reference_sample);
  if (v->native_sample)
    XDestroyImage(v->native_sample);
  tl_manual_paint_free(v->model);
  XtDestroyWidget(v->shell);
  if (v->fallback_font)
    XmFontListFree(v->fallback_font);
  if (v->fallback_core_font)
    XFreeFont(dpy, v->fallback_core_font);
  free(v);
}
