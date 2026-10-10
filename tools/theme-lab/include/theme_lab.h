/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef THEME_LAB_H
#define THEME_LAB_H
#include <stddef.h>
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
    char notes[2048];
    int visible_categories, visible_controls, selected_control, edit_state;
    int positions[TL_CONTROL_COUNT][2];
    int sizes[TL_CONTROL_COUNT][2]; /* 0 delegates that axis to the native toolkit. */
} TLRecipe;
typedef struct {
    int schema_version; TLFamily selected;
    char name[256], reference[TL_PATH_MAX];
    char contract_source[TL_PATH_MAX]; int native_imported;
    TLGeometry native_measured;
    TLRecipe recipes[TL_FAMILY_COUNT]; TLPick picked;
    char color_scheme[128]; int automatic_preview, debounce_ms;
} TLModel;
extern const char *const tl_family_ids[TL_FAMILY_COUNT];
extern const char *const tl_family_labels[TL_FAMILY_COUNT];
extern const char *const tl_field_ids[TL_FIELD_COUNT];
extern const char *const tl_field_labels[TL_FIELD_COUNT];
void tl_model_init(TLModel *model);
/* Public model operations return 0 on success, -1 on failure. */
int tl_model_validate(const TLModel *model, char *error, size_t capacity);
int tl_model_load(TLModel *model, const char *path, char *error, size_t capacity);
int tl_model_save(const TLModel *model, const char *path, char *error, size_t capacity);
int tl_model_geometry_get(const TLGeometry *geometry, int field);
void tl_model_geometry_set(TLGeometry *geometry, int field, int value);
int tl_model_contract(TLModel *model, const char *path, char *error, size_t capacity);
/* The View owns Motif/Xt widgets; callbacks only dispatch controller actions. */
#include <X11/Intrinsic.h>
typedef enum { TL_SELECT_FAMILY, TL_APPLY, TL_SAVE, TL_LOAD, TL_PICK,
               TL_PREVIEW, TL_EXPORT, TL_REFERENCE, TL_RESET, TL_QUIT,
               TL_CHANGED, TL_SELECT_CONTROL, TL_MOVE_CONTROL, TL_SEPARATE_TOGGLE } TLAction;
typedef void (*TLDispatch)(void *context, TLAction action, int argument);
typedef void (*TLFileChosen)(void *context, const char *path);
typedef struct TLView TLView;
TLView *tl_view_create(Widget shell, TLDispatch dispatch, void *context);
void tl_view_update(TLView *view, const TLModel *model);
void tl_view_scene(TLView *view, const TLModel *applied);
int tl_view_read(TLView *view, TLModel *candidate, char *error, size_t capacity);
void tl_view_status(TLView *view, const char *message);
void tl_view_capability(TLView *view, TLFamily family, const char *message);
Widget tl_view_shell(TLView *view);
void tl_view_palette(TLView *view, const unsigned short rgb[6][3]);
void tl_view_preview_palette(TLView *view, const unsigned short rgb[6][3]);
void tl_view_reference_palette(TLView *view, const unsigned short rgb[6][3]);
void tl_view_show_reference_image(TLView *view);
void tl_view_preview_settings(TLView *view, int *automatic, int *delay_ms);
void tl_view_separate_preview(TLView *view, int visible);
int tl_view_reference(TLView *view, const char *path, char *error, size_t capacity);
void tl_view_choose_file(TLView *view, const char *title, const char *initial,
                         TLFileChosen chosen, void *context);
void tl_view_code(TLView *view, const char *text);
unsigned long tl_view_canvas(TLView *view);
void tl_view_schemes(TLView *view, const char *const *ids, int count);
void tl_view_destroy(TLView *view);
#endif
