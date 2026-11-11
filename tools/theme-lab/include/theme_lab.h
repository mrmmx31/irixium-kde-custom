/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef THEME_LAB_H
#define THEME_LAB_H
#include <stddef.h>
#include "native_metrics.h"
#include "scrollbar_parts.h"
#define TL_FAMILY_COUNT 10
#define TL_FIELD_COUNT 9
#define TL_CONTROL_COUNT 16
#define TL_CATEGORY_COUNT 5
#define TL_PATH_MAX 4096
#define TL_TEXT_MAX 512
typedef enum { TL_MOTIF, TL_GTK1, TL_GTK2, TL_GTK3, TL_GTK4, TL_GTK5,
               TL_QT5, TL_QT6, TL_KVANTUM, TL_PLASMA } TLFamily;
typedef struct {
    int bar_px, shadow_px, arrow_px, thumb_cross_px, arrow_thumb_gap_px;
    int view_bar_gap_px, view_inset_px, control_padding_px, font_px;
} TLGeometry;
typedef struct {
    char face_role[96], text_role[96], view_role[96], selection_role[96];
    double light, shade, trough;
} TLPaletteRules;
typedef struct {
    unsigned short rgb16[3]; unsigned char rgb8[3];
    int x, y, valid; unsigned long visual_id;
    char origin[TL_TEXT_MAX], purpose[32];
} TLPick;
typedef struct {
    TLGeometry geometry; TLPaletteRules palette;
    /* GTK2 GtkScale only; independent of Motif and scrollbar dimensions. */
    int scale_slider_width_px, scale_slider_length_px;
    /* Optional semantic role/factor override for one catalog control. */
    TLPaletteRules control_palettes[TL_CONTROL_COUNT];
    unsigned char control_palette_custom[TL_CONTROL_COUNT];
    TLScrollbarParts scrollbar_parts;
    char notes[2048];
    int visible_categories, visible_controls, selected_control, edit_state;
    int selected_scroll_part;
    int positions[TL_CONTROL_COUNT][2];
    int length_anchor[TL_CONTROL_COUNT]; /* 0 leading edge, 1 trailing edge; bars only. */
    int sizes[TL_CONTROL_COUNT][2]; /* 0 delegates that axis to the native toolkit. */
} TLRecipe;
typedef struct {
    int schema_version; TLFamily selected;
    char name[256], reference[TL_PATH_MAX];
    char contract_source[TL_PATH_MAX]; int native_imported;
    TLGeometry native_measured;
    TLRecipe recipes[TL_FAMILY_COUNT]; TLPick picked;
    char color_scheme[128]; int automatic_preview, debounce_ms, separate_preview;
} TLModel;
extern const char *const tl_family_ids[TL_FAMILY_COUNT];
extern const char *const tl_family_labels[TL_FAMILY_COUNT];
extern const char *const tl_control_ids[TL_CONTROL_COUNT];
extern const char *const tl_field_ids[TL_FIELD_COUNT];
extern const char *const tl_field_labels[TL_FIELD_COUNT];
void tl_model_init(TLModel *model);
/* Public model operations return 0 on success, -1 on failure. */
int tl_model_validate(const TLModel *model, char *error, size_t capacity);
int tl_model_load(TLModel *model, const char *path, char *error, size_t capacity);
int tl_model_save(const TLModel *model, const char *path, char *error, size_t capacity);
/* Canonical project codec shared by history; exported_at omitted on encode. */
struct json_object *tl_model_encode(const TLModel *model,char *error,size_t capacity);
int tl_model_decode(TLModel *model,struct json_object *object,char *error,size_t capacity);
int tl_model_geometry_get(const TLGeometry *geometry, int field);
void tl_model_geometry_set(TLGeometry *geometry, int field, int value);
int tl_model_contract(TLModel *model, const char *path, char *error, size_t capacity);
/* The View owns Motif/Xt widgets; callbacks only dispatch controller actions. */
#include <X11/Intrinsic.h>
typedef enum { TL_SELECT_FAMILY, TL_APPLY, TL_SAVE, TL_LOAD, TL_PICK,
               TL_PREVIEW, TL_EXPORT, TL_REFERENCE, TL_RESET, TL_QUIT,
               TL_MANUAL_PAINT, TL_CHANGED, TL_SELECT_CONTROL, TL_MOVE_CONTROL, TL_SEPARATE_TOGGLE, TL_SELECT_SCROLL_PART,
               TL_PAINT_SAMPLE, TL_PAINT_REFERENCE_SAMPLE,
               TL_SELECT_ANCHOR, TL_SELECT_PART_STATE, TL_PART_RELIEF_CHANGED,
               TL_PROJECT_UNDO,TL_PROJECT_REDO,TL_PROJECT_MARK,TL_PROJECT_RESTORE,
               TL_PROJECT_RESET_PART, TL_IMPORT_DELTA, TL_RECONSTRUCT_FILES } TLAction;
typedef void (*TLDispatch)(void *context, TLAction action, int argument);
typedef void (*TLFileChosen)(void *context, const char *path);
typedef struct TLView TLView;
TLView *tl_view_create(Widget shell, TLDispatch dispatch, void *context);
int tl_view_editor_open(TLView *view,const char *path,char *error,size_t capacity);
int tl_view_editor_checkpoint(TLView *view,char *error,size_t capacity);
void tl_view_update(TLView *view, const TLModel *model);
void tl_view_scene(TLView *view, const TLModel *applied);
int tl_view_read(TLView *view, TLModel *candidate, char *error, size_t capacity);
int tl_view_part_state(const TLView *view);
void tl_view_status(TLView *view, const char *message);
void tl_view_history_state(TLView *view,int undo,int redo,int point);
void tl_view_capability(TLView *view, TLFamily family, const char *message);
Widget tl_view_shell(TLView *view);
void tl_view_palette(TLView *view, const unsigned short rgb[6][3]);
void tl_view_header_palette(TLView *view, const unsigned short rgb[6][3]);
void tl_view_shell_palettes(TLView *view,
                            const unsigned short body[6][3],
                            const unsigned short header[6][3]);
void tl_view_preview_palette(TLView *view, const unsigned short rgb[6][3]);
void tl_view_reference_palette(TLView *view, const unsigned short rgb[6][3]);
void tl_view_show_reference_image(TLView *view);
void tl_view_preview_settings(TLView *view, int *automatic, int *delay_ms);
void tl_view_separate_preview(TLView *view, int visible);
void tl_view_native_metrics(TLView *view, int control, const TLNativeMetrics *metrics);
int tl_view_set_anchor(TLView *view, TLModel *model, int anchor, char *error, size_t capacity);
int tl_view_get_native_metrics(TLView *view,int control,int separate,TLNativeMetrics *metrics);
void tl_view_metrics_reset(TLView *view);
void tl_view_metrics_clear_origin(TLView *view,int separate);
int tl_view_reference(TLView *view, const char *path, char *error, size_t capacity);
int tl_view_manual_paint_open(TLView *view, const char *path, int family, int control, int state);
int tl_view_manual_paint_checkpoint(TLView *view);
int tl_view_manual_paint_native_png(TLView *view, const char *path,
                                    int family, int control, int state);
int tl_view_manual_paint_reference_png(TLView *view, const char *path,
                                       int family, int control, int state);
int tl_view_manual_paint_r584_catalog(TLView *view, const char *receipt_path,
                                      const char *manifest_path, char *error,
                                      size_t capacity);
void tl_view_manual_paint_refresh_sample(TLView *view);
void tl_view_choose_file(TLView *view, const char *title, const char *initial,
                         TLFileChosen chosen, void *context);
void tl_view_choose_directory(TLView *view, const char *title, const char *initial,
                             TLFileChosen chosen, void *context);
void tl_view_code(TLView *view, const char *text);
void tl_view_export_review(TLView *view,const char *text);
unsigned long tl_view_canvas(TLView *view);
void tl_view_schemes(TLView *view, const char *const *ids, int count);
void tl_view_destroy(TLView *view);
#endif
