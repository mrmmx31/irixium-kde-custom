/* SPDX-License-Identifier: GPL-3.0-or-later */
/* The Model reads recipes and evidence. It never changes a desktop theme. */
#define _POSIX_C_SOURCE 200809L
#include "theme_lab.h"
#include "control_dimensions.h"
#include <json-c/json.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <math.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define TL_JSON_LIMIT (2U * 1024U * 1024U)

const char *const tl_family_ids[TL_FAMILY_COUNT] = {
    "motif", "gtk1", "gtk2", "gtk3", "gtk4", "gtk5", "qt5", "qt6",
    "kvantum", "plasma"
};
const char *const tl_family_labels[TL_FAMILY_COUNT] = {
    "Motif", "GTK 1", "GTK 2", "GTK 3", "GTK 4", "GTK 5",
    "Qt 5", "Qt 6", "Kvantum", "Plasma"
};
const char *const tl_field_ids[TL_FIELD_COUNT] = {
    "bar_px", "shadow_px", "arrow_px", "thumb_cross_px",
    "arrow_thumb_gap_px", "view_bar_gap_px", "view_inset_px",
    "control_padding_px", "font_px"
};
const char *const tl_field_labels[TL_FIELD_COUNT] = {
    "Barra (px)", "Sombra (px)", "Seta (px)", "Thumb transversal (px)",
    "Seta/Thumb (px)", "Conteúdo/Barra (px)", "Moldura (px)",
    "Espaço do controle (px)", "Fonte (px)"
};
const char *const tl_control_ids[TL_CONTROL_COUNT] = {
    "push", "toggle", "check", "radio", "entry", "combo", "spin", "text",
    "scale_h", "scale_v", "scroll_h", "scroll_v", "arrow", "progress", "list", "frame"
};

static int fail(char *error, size_t capacity, const char *format, ...)
{
    va_list args;
    if (error && capacity) {
        va_start(args, format);
        vsnprintf(error, capacity, format, args);
        va_end(args);
    }
    return 0;
}

static void clear_error(char *error, size_t capacity)
{
    if (error && capacity) error[0] = '\0';
}

int tl_model_geometry_get(const TLGeometry *g, int field)
{
    if (!g) return -1;
    switch (field) {
    case 0: return g->bar_px;
    case 1: return g->shadow_px;
    case 2: return g->arrow_px;
    case 3: return g->thumb_cross_px;
    case 4: return g->arrow_thumb_gap_px;
    case 5: return g->view_bar_gap_px;
    case 6: return g->view_inset_px;
    case 7: return g->control_padding_px;
    case 8: return g->font_px;
    default: return -1;
    }
}

void tl_model_geometry_set(TLGeometry *g, int field, int value)
{
    if (!g) return;
    switch (field) {
    case 0: g->bar_px = value; break;
    case 1: g->shadow_px = value; break;
    case 2: g->arrow_px = value; break;
    case 3: g->thumb_cross_px = value; break;
    case 4: g->arrow_thumb_gap_px = value; break;
    case 5: g->view_bar_gap_px = value; break;
    case 6: g->view_inset_px = value; break;
    case 7: g->control_padding_px = value; break;
    case 8: g->font_px = value; break;
    default: break;
    }
}

void tl_model_init(TLModel *model)
{
    TLGeometry geometry = {15, 2, 11, 11, 1, 4, 2, 4, 13};
    TLPaletteRules palette = {
        "Colors:Button/BackgroundNormal", "Colors:Button/ForegroundNormal",
        "Colors:View/BackgroundNormal", "Colors:Selection/BackgroundNormal",
        .56, .482, .15
    };
    int i, control;
    if (!model) return;
    memset(model, 0, sizeof(*model));
    model->schema_version = 1;
    /* The Motif recipe is the historical reference panel. Start editing the
     * primary adaptation target so a fresh laboratory session compares GTK3
     * against Motif instead of showing a confusing Motif/Motif pair. */
    model->selected = TL_GTK3;
    model->automatic_preview = 0;
    model->separate_preview = 0;
    model->debounce_ms = 600;
    strcpy(model->name, "DomainOS SR10.4 — proposta");
    model->native_measured = geometry;
    for (i = 0; i < TL_FAMILY_COUNT; i++) {
        model->recipes[i].geometry = geometry;
        model->recipes[i].scale_slider_width_px = 8;
        model->recipes[i].scale_slider_length_px = 27;
        model->recipes[i].palette = palette;
        model->recipes[i].visible_categories = (1 << TL_CATEGORY_COUNT) - 1;
        model->recipes[i].visible_controls = (1 << TL_CONTROL_COUNT) - 1;
        for (control = 0; control < TL_CONTROL_COUNT; control++) {
            model->recipes[i].positions[control][0] = 16 + (control % 4) * 160;
            model->recipes[i].positions[control][1] = 16 + (control / 4) * 80;
        }
    }
    strcpy(model->picked.purpose, "evidence_only");
    /* Padding/font and light/shade factors are adaptation/tool defaults.
       Only tl_model_contract imports measured native scrollbar dimensions. */
}

static int terminated(const char *text, size_t capacity)
{
    return memchr(text, '\0', capacity) != NULL;
}

static int semantic_role(const char *role, size_t capacity)
{
    const unsigned char *cursor = (const unsigned char *)role;
    const unsigned char *slash;
    if (!terminated(role, capacity) || strncmp(role, "Colors:", 7)) return 0;
    cursor += 7;
    slash = (const unsigned char *)strchr((const char *)cursor, '/');
    if (!slash || slash == cursor || !slash[1]) return 0;
    for (; *cursor; cursor++)
        if (cursor != slash && !isalnum(*cursor) && *cursor != '_') return 0;
    return 1;
}

static int validate_palette(const TLPaletteRules *p, const char *scope,
                            char *error, size_t capacity)
{
    if (!semantic_role(p->face_role,sizeof(p->face_role)) ||
        !semantic_role(p->text_role,sizeof(p->text_role)) ||
        !semantic_role(p->view_role,sizeof(p->view_role)) ||
        !semantic_role(p->selection_role,sizeof(p->selection_role)))
        return fail(error,capacity,"%s: use papéis semânticos Colors:Grupo/Papel",scope);
    if (!isfinite(p->light) || !isfinite(p->shade) || !isfinite(p->trough) ||
        p->light<0 || p->light>1 || p->shade<0 || p->shade>1 ||
        p->trough<0 || p->trough>1)
        return fail(error,capacity,"%s: fatores de luz/sombra devem ficar entre 0 e 1",scope);
    return 1;
}

static int portable_scheme(const char *scheme, size_t capacity)
{
    const unsigned char *cursor = (const unsigned char *)scheme;
    if (!terminated(scheme, capacity)) return 0;
    if (!scheme[0]) return 1; /* Empty ID selects current KDE roles. */
    if (scheme[0] == '.' || scheme[0] == ' ' || strstr(scheme, "..")) return 0;
    for (; *cursor; cursor++)
        if (!((*cursor >= 'A' && *cursor <= 'Z') ||
              (*cursor >= 'a' && *cursor <= 'z') ||
              (*cursor >= '0' && *cursor <= '9') || *cursor == ' ' ||
              *cursor == '-' || *cursor == '_' || *cursor == '.')) return 0;
    return cursor[-1] != ' ';
}

static int validate_geometry(const TLGeometry *g, int constrained,
                             const char *scope, char *error, size_t capacity)
{
    int field, value;
    for (field = 0; field < TL_FIELD_COUNT; field++) {
        value = tl_model_geometry_get(g, field);
        if (field == 8) {
            if (value < 6 || value > 48)
                return fail(error, capacity, "%s: fonte deve ficar entre 6 e 48 px", scope);
        } else if (value < 0 || value > 128) {
            return fail(error, capacity, "%s: %s deve ficar entre 0 e 128 px",
                        scope, tl_field_ids[field]);
        }
    }
    if (g->bar_px < 1 || g->arrow_px < 1 || g->thumb_cross_px < 1 ||
        g->bar_px < g->arrow_px || g->bar_px < g->thumb_cross_px ||
        2 * g->shadow_px >= g->bar_px)
        return fail(error, capacity, "%s: barra deve acomodar seta, thumb e sombras", scope);
    if (constrained && (g->bar_px != g->arrow_px + 2 * g->shadow_px ||
                        g->thumb_cross_px != g->arrow_px))
        return fail(error, capacity,
                    "%s: barra = seta + 2 × sombra; thumb transversal = seta", scope);
    return 1;
}

static int validate_model(const TLModel *model, char *error, size_t capacity)
{
    int i, control, axis;
    clear_error(error, capacity);
    if (!model) return fail(error, capacity, "Projeto ausente");
    if (model->schema_version < 1 || model->schema_version > 4)
        return fail(error, capacity, "Versão de projeto não suportada");
    if ((int)model->selected < 0 || (int)model->selected >= TL_FAMILY_COUNT)
        return fail(error, capacity, "Família selecionada inválida");
    if (!portable_scheme(model->color_scheme, sizeof(model->color_scheme)))
        return fail(error, capacity, "Use um ID portátil de esquema, sem caminhos");
    if (model->separate_preview != 0 && model->separate_preview != 1)
        return fail(error, capacity, "Prévia separada requer estado booleano");
    if ((model->automatic_preview != 0 && model->automatic_preview != 1) ||
        model->debounce_ms < 100 || model->debounce_ms > 10000)
        return fail(error, capacity, "Prévia automática requer estado booleano e intervalo de 100 a 10000 ms");
    if (!terminated(model->name, sizeof(model->name)) || !model->name[0] ||
        !terminated(model->reference, sizeof(model->reference)))
        return fail(error, capacity, "Nome ou referência inválidos");
    if (!terminated(model->contract_source, sizeof(model->contract_source)) ||
        (model->native_imported != 0 && model->native_imported != 1) ||
        (model->native_imported && !model->contract_source[0]) ||
        (!model->native_imported && model->contract_source[0]))
        return fail(error, capacity, "Origem das medidas nativas inválida");
    if (!validate_geometry(&model->native_measured, 0, "Medidas nativas", error, capacity))
        return 0;
    for (i = 0; i < TL_FAMILY_COUNT; i++) {
        const TLRecipe *recipe = &model->recipes[i];
        const TLPaletteRules *p = &recipe->palette;
        if (tl_scroll_parts_validate(&recipe->scrollbar_parts,error,capacity)) return 0;
        if (i == TL_GTK3 && recipe->scrollbar_parts.parts[TL_SCROLL_ARROW].present) {
            const TLPartRecipe *arrow=&recipe->scrollbar_parts.parts[TL_SCROLL_ARROW];
            int size=(arrow->present & 1U)?arrow->values[0]:recipe->geometry.arrow_px;
            int shadow=(arrow->present & 2U)?arrow->values[1]:recipe->geometry.shadow_px;
            if(size<3 || !(size&1) || size>recipe->geometry.arrow_px || 2*shadow>=size)
                return fail(error,capacity,"Seta: tamanho ímpar de 3 até o espaço reservado; relevo menor que metade");
        }
        if (i == TL_GTK3 && recipe->scrollbar_parts.parts[TL_SCROLL_ARROW_BUTTON].present) {
            const TLPartRecipe *arrow=&recipe->scrollbar_parts.parts[TL_SCROLL_ARROW];
            const TLPartRecipe *button=&recipe->scrollbar_parts.parts[TL_SCROLL_ARROW_BUTTON];
            int glyph=(arrow->present & 1U)?arrow->values[0]:recipe->geometry.arrow_px;
            int padding=(button->present & 1U)?button->values[0]:0;
            int shadow=(button->present & 2U)?button->values[1]:recipe->geometry.shadow_px;
            int outer=recipe->geometry.arrow_px+2*recipe->geometry.shadow_px;
            if(glyph+2*(padding+shadow)>outer)
                return fail(error,capacity,"Botão isolado: moldura/espaço devem caber sem cobrir a seta nem aumentar o botão");
        }
        if (i == TL_GTK3 && recipe->scrollbar_parts.parts[TL_SCROLL_TROUGH].present) {
            const TLPartRecipe *trough=&recipe->scrollbar_parts.parts[TL_SCROLL_TROUGH];
            int thickness=(trough->present & 1U)?trough->values[0]:recipe->geometry.bar_px;
            int shadow=(trough->present & 2U)?trough->values[1]:recipe->geometry.shadow_px;
            int reserved=recipe->geometry.arrow_px>recipe->geometry.thumb_cross_px?
                         recipe->geometry.arrow_px:recipe->geometry.thumb_cross_px;
            if(thickness<reserved+2*shadow)
                return fail(error,capacity,"Trilho: espessura deve acomodar seta e cursor sem cortar suas alocações");
        }
        if (i == TL_GTK3 && recipe->scrollbar_parts.parts[TL_SCROLL_THUMB].present) {
            const TLPartRecipe *thumb=&recipe->scrollbar_parts.parts[TL_SCROLL_THUMB];
            const TLPartRecipe *trough=&recipe->scrollbar_parts.parts[TL_SCROLL_TROUGH];
            int cross=(thumb->present & 1U)?thumb->values[0]:recipe->geometry.thumb_cross_px;
            int shadow=(thumb->present & 2U)?thumb->values[1]:recipe->geometry.shadow_px;
            int thickness=(trough->present & 1U)?trough->values[0]:recipe->geometry.bar_px;
            int trough_shadow=(trough->present & 2U)?trough->values[1]:recipe->geometry.shadow_px;
            int available=thickness-2*trough_shadow;
            if(cross<=2*shadow || cross>available || (available-cross)%2)
                return fail(error,capacity,"Cursor: largura deve caber no trilho com margens inteiras simétricas e relevo menor que metade");
        }
        if (recipe->visible_categories < 0 ||
            recipe->visible_categories >= (1 << TL_CATEGORY_COUNT) ||
            recipe->visible_controls < 0 ||
            recipe->visible_controls >= (1 << TL_CONTROL_COUNT) ||
            recipe->selected_control < 0 || recipe->selected_control >= TL_CONTROL_COUNT ||
            recipe->edit_state < 0 || recipe->edit_state > 3 ||
            recipe->selected_scroll_part < 0 || recipe->selected_scroll_part >= TL_SCROLL_PART_COUNT)
            return fail(error, capacity, "%s: categoria, controle ou estado de edição inválido",
                        tl_family_ids[i]);
        for(control=0;control<TL_CONTROL_COUNT;control++)
            if(recipe->length_anchor[control]<0 || recipe->length_anchor[control]>1 ||
               (recipe->length_anchor[control] && tl_control_long_axis(control)<0))
                return fail(error,capacity,"Âncora inválida; somente barras têm extremidade longitudinal");
        for (control = 0; control < TL_CONTROL_COUNT; control++)
            for (axis = 0; axis < 2; axis++)
                if (recipe->positions[control][axis] < 0 || recipe->positions[control][axis] > 2048)
                    return fail(error, capacity, "%s: posições devem ficar entre 0 e 2048 px",
                                tl_family_ids[i]);
        for (control = 0; control < TL_CONTROL_COUNT; control++)
            for (axis = 0; axis < 2; axis++)
                if (recipe->sizes[control][axis] < 0 || recipe->sizes[control][axis] > 2048)
                    return fail(error, capacity, "%s: dimensões devem ficar entre 0 e 2048 px (0 = automático)",
                                tl_family_ids[i]);
        if (!validate_geometry(&recipe->geometry, i == TL_MOTIF || i == TL_GTK3,
                               tl_family_ids[i], error, capacity)) return 0;
        if (i == TL_GTK2 &&
            (recipe->scale_slider_width_px < 1 || recipe->scale_slider_width_px > 128 ||
             recipe->scale_slider_length_px < 1 || recipe->scale_slider_length_px > 128))
            return fail(error, capacity, "gtk2: largura e comprimento do cursor de escala devem ficar entre 1 e 128 px");
        if (i == TL_GTK3 &&
            (!(recipe->geometry.bar_px & 1) ||
             recipe->geometry.arrow_px <= 2 * recipe->geometry.shadow_px ||
             recipe->geometry.view_inset_px != recipe->geometry.shadow_px))
            return fail(error, capacity,
                        "gtk3: barra ímpar, seta > 2 × sombra e moldura = sombra");
        if (!validate_palette(p,tl_family_ids[i],error,capacity)) return 0;
        for(control=0;control<TL_CONTROL_COUNT;control++) {
            char scope[128];
            if(recipe->control_palette_custom[control]>1)
                return fail(error,capacity,"%s: estado de papel por controle inválido",tl_family_ids[i]);
            if(recipe->control_palette_custom[control]) {
                (void)snprintf(scope,sizeof(scope),"%s/%s",tl_family_ids[i],tl_control_ids[control]);
                if(!validate_palette(&recipe->control_palettes[control],scope,error,capacity)) return 0;
            }
        }
        if (!terminated(recipe->notes, sizeof(recipe->notes)))
            return fail(error, capacity, "%s: anotação sem terminação", tl_family_ids[i]);
    }
    if ((model->picked.valid != 0 && model->picked.valid != 1) ||
        !terminated(model->picked.origin, sizeof(model->picked.origin)) ||
        !terminated(model->picked.purpose, sizeof(model->picked.purpose)) ||
        (strcmp(model->picked.purpose, "evidence_only") &&
         strcmp(model->picked.purpose, "scheme_input")))
        return fail(error, capacity, "Evidência da pipeta inválida");
    return 1;
}

int tl_model_validate(const TLModel *model, char *error, size_t capacity)
{
    return validate_model(model, error, capacity) ? 0 : -1;
}

static int member(struct json_object *object, const char *key, enum json_type type,
                  struct json_object **value, char *error, size_t capacity)
{
    if (!object || !json_object_is_type(object, json_type_object) ||
        !json_object_object_get_ex(object, key, value) ||
        !json_object_is_type(*value, type))
        return fail(error, capacity, "Campo %s ausente ou com tipo inválido", key);
    return 1;
}

static int string_member(struct json_object *object, const char *key, char *target,
                         size_t limit, char *error, size_t capacity)
{
    struct json_object *value;
    const char *text;
    size_t length;
    if (!member(object, key, json_type_string, &value, error, capacity)) return 0;
    length = (size_t)json_object_get_string_len(value);
    text = json_object_get_string(value);
    if (length >= limit || strlen(text) != length)
        return fail(error, capacity, "Campo %s excede o limite ou contém NUL", key);
    memcpy(target, text, length + 1);
    return 1;
}

static int int_member(struct json_object *object, const char *key, int minimum,
                      int maximum, int *target, char *error, size_t capacity)
{
    struct json_object *value;
    int64_t number;
    if (!member(object, key, json_type_int, &value, error, capacity)) return 0;
    number = json_object_get_int64(value);
    if (number < minimum || number > maximum)
        return fail(error, capacity, "Campo %s fora do intervalo permitido", key);
    *target = (int)number;
    return 1;
}

static int optional_int(struct json_object *object, const char *key, int minimum,
                        int maximum, int *target, char *error, size_t capacity)
{
    struct json_object *value;
    if (!json_object_object_get_ex(object, key, &value)) return 1;
    return int_member(object, key, minimum, maximum, target, error, capacity);
}

static int decode_pairs(struct json_object *object, const char *key,
                        int target[TL_CONTROL_COUNT][2], char *error, size_t capacity)
{
    struct json_object *positions, *pair, *value;
    int control, axis;
    int64_t coordinate;
    if (!json_object_object_get_ex(object, key, &positions)) return 1;
    if (!json_object_is_type(positions, json_type_array) ||
        json_object_array_length(positions) != TL_CONTROL_COUNT)
        return fail(error, capacity, "%s deve conter os 16 pares", key);
    for (control = 0; control < TL_CONTROL_COUNT; control++) {
        pair = json_object_array_get_idx(positions, (size_t)control);
        if (!json_object_is_type(pair, json_type_array) || json_object_array_length(pair) != 2)
            return fail(error, capacity, "Cada posição deve conter exatamente x e y");
        for (axis = 0; axis < 2; axis++) {
            value = json_object_array_get_idx(pair, (size_t)axis);
            if (!json_object_is_type(value, json_type_int))
                return fail(error, capacity, "Coordenadas de posição devem ser inteiras");
            coordinate = json_object_get_int64(value);
            if (coordinate < 0 || coordinate > 2048)
                return fail(error, capacity, "Coordenadas devem ficar entre 0 e 2048 px");
            target[control][axis] = (int)coordinate;
        }
    }
    return 1;
}

static int decode_anchors(struct json_object *object, TLRecipe *recipe, char *error, size_t capacity)
{
    struct json_object *array;
    if(!json_object_object_get_ex(object,"length_anchor",&array))return 1;
    if(!json_object_is_type(array,json_type_array) || json_object_array_length(array)!=TL_CONTROL_COUNT)
        return fail(error,capacity,"length_anchor deve conter 16 inteiros");
    for(int i=0;i<TL_CONTROL_COUNT;i++) {
        struct json_object *value=json_object_array_get_idx(array,(size_t)i);
        if(!json_object_is_type(value,json_type_int) || json_object_get_int64(value)<0 || json_object_get_int64(value)>1)
            return fail(error,capacity,"Âncora deve ser inteiro 0 ou 1");
        recipe->length_anchor[i]=json_object_get_int(value);
    }
    return 1;
}

static int decode_layout(struct json_object *object, TLRecipe *recipe,
                         char *error, size_t capacity)
{
    return optional_int(object, "visible_categories", 0, (1 << TL_CATEGORY_COUNT) - 1,
                        &recipe->visible_categories, error, capacity) &&
           optional_int(object, "visible_controls", 0, (1 << TL_CONTROL_COUNT) - 1,
                        &recipe->visible_controls, error, capacity) &&
           optional_int(object, "selected_control", 0, TL_CONTROL_COUNT - 1,
                        &recipe->selected_control, error, capacity) &&
           optional_int(object, "edit_state", 0, 3, &recipe->edit_state, error, capacity) &&
           optional_int(object, "selected_scroll_part", 0, TL_SCROLL_PART_COUNT-1, &recipe->selected_scroll_part, error, capacity) &&
           decode_pairs(object, "positions", recipe->positions, error, capacity) &&
           decode_pairs(object, "sizes", recipe->sizes, error, capacity) &&
           decode_anchors(object,recipe,error,capacity);
}

static int fraction_member(struct json_object *object, const char *key, double *target,
                           char *error, size_t capacity)
{
    struct json_object *value;
    double number;
    if (!json_object_object_get_ex(object, key, &value) ||
        (!json_object_is_type(value, json_type_double) &&
         !json_object_is_type(value, json_type_int)))
        return fail(error, capacity, "Campo %s deve ser numérico", key);
    number = json_object_get_double(value);
    if (!isfinite(number) || number < 0 || number > 1)
        return fail(error, capacity, "Campo %s deve ficar entre 0 e 1", key);
    *target = number;
    return 1;
}

static int decode_geometry(struct json_object *object, TLGeometry *g, int count,
                           char *error, size_t capacity)
{
    int i, value;
    for (i = 0; i < count; i++) {
        if (!int_member(object, tl_field_ids[i], 0, 128, &value, error, capacity)) return 0;
        tl_model_geometry_set(g, i, value);
    }
    return 1;
}

static int decode_palette(struct json_object *object, TLPaletteRules *p,
                          char *error, size_t capacity)
{
    return string_member(object, "face_role", p->face_role, sizeof(p->face_role), error, capacity) &&
           string_member(object, "text_role", p->text_role, sizeof(p->text_role), error, capacity) &&
           string_member(object, "view_role", p->view_role, sizeof(p->view_role), error, capacity) &&
           string_member(object, "selection_role", p->selection_role, sizeof(p->selection_role), error, capacity) &&
           fraction_member(object, "light", &p->light, error, capacity) &&
           fraction_member(object, "shade", &p->shade, error, capacity) &&
           fraction_member(object, "trough", &p->trough, error, capacity);
}

static int decode_control_palettes(struct json_object *object, TLRecipe *recipe,
                                   char *error, size_t capacity)
{
    int i, found=0;
    struct json_object *value;
    if(!json_object_is_type(object,json_type_object))
        return fail(error,capacity,"control_palettes deve ser objeto");
    for(i=0;i<TL_CONTROL_COUNT;i++) {
        if(json_object_object_get_ex(object,tl_control_ids[i],&value)) {
            if(!decode_palette(value,&recipe->control_palettes[i],error,capacity)) return 0;
            recipe->control_palette_custom[i]=1;
            found++;
        }
    }
    if(found!=json_object_object_length(object))
        return fail(error,capacity,"control_palettes contém um controle desconhecido");
    return 1;
}

static int decode_rgb(struct json_object *object, const char *key, unsigned int maximum,
                      unsigned int rgb[3], char *error, size_t capacity)
{
    struct json_object *array, *value;
    int i;
    int64_t number;
    if (!member(object, key, json_type_array, &array, error, capacity)) return 0;
    if (json_object_array_length(array) != 3)
        return fail(error, capacity, "%s deve ter três componentes", key);
    for (i = 0; i < 3; i++) {
        value = json_object_array_get_idx(array, (size_t)i);
        if (!json_object_is_type(value, json_type_int))
            return fail(error, capacity, "%s deve conter inteiros", key);
        number = json_object_get_int64(value);
        if (number < 0 || number > maximum)
            return fail(error, capacity, "%s fora do intervalo permitido", key);
        rgb[i] = (unsigned int)number;
    }
    return 1;
}

static int decode_model(struct json_object *root, TLModel *model, char *error, size_t capacity)
{
    struct json_object *native, *recipes, *recipe, *geometry, *palette, *pick, *value, *provenance;
    char kind[64], family[64];
    unsigned int rgb16[3], rgb8[3];
    uint64_t visual;
    int i, selected = -1;
    if (!int_member(root, "schema_version", 1, 4, &model->schema_version, error, capacity) ||
        !string_member(root, "kind", kind, sizeof(kind), error, capacity) ||
        !string_member(root, "selected_family", family, sizeof(family), error, capacity)) return 0;
    if (strcmp(kind, "theme_lab_project")) return fail(error, capacity, "Tipo de projeto não suportado");
    for (i = 0; i < TL_FAMILY_COUNT; i++) if (!strcmp(family, tl_family_ids[i])) selected = i;
    if (selected < 0) return fail(error, capacity, "Família selecionada desconhecida");
    model->selected = (TLFamily)selected;
    if (json_object_object_get_ex(root, "color_scheme", &value) &&
        !string_member(root, "color_scheme", model->color_scheme,
                       sizeof(model->color_scheme), error, capacity)) return 0;
    if (json_object_object_get_ex(root, "separate_preview", &value)) {
        if (!json_object_is_type(value, json_type_boolean))
            return fail(error, capacity, "separate_preview deve ser booleano");
        model->separate_preview = json_object_get_boolean(value);
    }
    if (json_object_object_get_ex(root, "automatic_preview", &value)) {
        if (!json_object_is_type(value, json_type_boolean))
            return fail(error, capacity, "automatic_preview deve ser booleano");
        model->automatic_preview = json_object_get_boolean(value);
    }
    if (!optional_int(root, "debounce_ms", 100, 10000, &model->debounce_ms, error, capacity)) return 0;
    if (!string_member(root, "name", model->name, sizeof(model->name), error, capacity) ||
        !string_member(root, "reference", model->reference, sizeof(model->reference), error, capacity) ||
        !member(root, "provenance", json_type_object, &provenance, error, capacity) ||
        !string_member(provenance, "contract_source", model->contract_source,
                       sizeof(model->contract_source), error, capacity) ||
        !member(provenance, "native_imported", json_type_boolean, &value, error, capacity)) return 0;
    model->native_imported = json_object_get_boolean(value);
    if (
        !member(root, "native_measured", json_type_object, &native, error, capacity) ||
        !decode_geometry(native, &model->native_measured, TL_FIELD_COUNT, error, capacity) ||
        !member(root, "recipes", json_type_object, &recipes, error, capacity)) return 0;
    if (json_object_object_length(recipes) != TL_FAMILY_COUNT)
        return fail(error, capacity, "Projeto deve conter as dez famílias de receitas");
    for (i = 0; i < TL_FAMILY_COUNT; i++) {
        TLRecipe *r = &model->recipes[i];
        if (!member(recipes, tl_family_ids[i], json_type_object, &recipe, error, capacity) ||
            !member(recipe, "geometry", json_type_object, &geometry, error, capacity) ||
            !decode_geometry(geometry, &r->geometry, TL_FIELD_COUNT, error, capacity) ||
            !member(recipe, "palette", json_type_object, &palette, error, capacity) ||
            !decode_palette(palette, &r->palette, error, capacity) ||
            !string_member(recipe, "notes", r->notes, sizeof(r->notes), error, capacity) ||
            !decode_layout(recipe, r, error, capacity)) return 0;
        if (i == TL_GTK2 && model->schema_version >= 4 &&
            (!optional_int(geometry, "scale_slider_width_px", 1, 128,
                           &r->scale_slider_width_px, error, capacity) ||
             !optional_int(geometry, "scale_slider_length_px", 1, 128,
                           &r->scale_slider_length_px, error, capacity))) return 0;
        if (i != TL_GTK2 &&
            (json_object_object_get_ex(geometry, "scale_slider_width_px", &value) ||
             json_object_object_get_ex(geometry, "scale_slider_length_px", &value)))
            return fail(error, capacity, "%s: dimensões GtkScale só pertencem à receita GTK2", tl_family_ids[i]);
        if(model->schema_version<2 && json_object_object_get_ex(recipe,"length_anchor",&value))
            return fail(error,capacity,"Âncoras exigem schema_version=2");
        if (json_object_object_get_ex(recipe,"scrollbar_parts",&value)) {
            if (model->schema_version < 2)
                return fail(error,capacity,"Receitas por peça exigem schema_version=2");
            if (tl_scroll_parts_decode(&r->scrollbar_parts,value,error,capacity)) return 0;
        }
        if(json_object_object_get_ex(recipe,"control_palettes",&value)) {
            if(model->schema_version<3)
                return fail(error,capacity,"Papéis por controle exigem schema_version=3");
            if(!decode_control_palettes(value,r,error,capacity)) return 0;
        }
    }
    if (!member(root, "picked", json_type_object, &pick, error, capacity) ||
        !member(pick, "valid", json_type_boolean, &value, error, capacity)) return 0;
    model->picked.valid = json_object_get_boolean(value);
    if (!decode_rgb(pick, "rgb16", 65535, rgb16, error, capacity) ||
        !decode_rgb(pick, "rgb8", 255, rgb8, error, capacity) ||
        !int_member(pick, "x", INT_MIN, INT_MAX, &model->picked.x, error, capacity) ||
        !int_member(pick, "y", INT_MIN, INT_MAX, &model->picked.y, error, capacity) ||
        !member(pick, "visual_id", json_type_int, &value, error, capacity)) return 0;
    visual = json_object_get_uint64(value);
    if (json_object_get_string(value)[0] == '-' || visual > ULONG_MAX)
        return fail(error, capacity, "Identificador visual inválido");
    model->picked.visual_id = (unsigned long)visual;
    for (i = 0; i < 3; i++) {
        model->picked.rgb16[i] = (unsigned short)rgb16[i];
        model->picked.rgb8[i] = (unsigned char)rgb8[i];
    }
    return string_member(pick, "origin", model->picked.origin, sizeof(model->picked.origin), error, capacity) &&
           string_member(pick, "purpose", model->picked.purpose, sizeof(model->picked.purpose), error, capacity) &&
           validate_model(model, error, capacity);
}

/* json-c 0.18 in the fixture rejects literal non-ASCII strings with STRICT.
   Normalize valid UTF-8 to JSON escapes, keeping strict syntax and bounded input.
   This changes only the parser buffer; original evidence files are never written. */
static char *ascii_json(const char *input, size_t length, size_t *output_length,
                        char *error, size_t capacity)
{
    char *output = malloc(length * 6U + 1U);
    size_t i = 0, used = 0;
    if (!output) { fail(error, capacity, "Memória insuficiente"); return NULL; }
    while (i < length) {
        unsigned int first = (unsigned char)input[i++], codepoint, count, k, minimum;
        if (first < 0x80) { output[used++] = (char)first; continue; }
        if (first >= 0xc2 && first <= 0xdf) { count = 1; codepoint = first & 0x1f; minimum = 0x80; }
        else if (first >= 0xe0 && first <= 0xef) { count = 2; codepoint = first & 0x0f; minimum = 0x800; }
        else if (first >= 0xf0 && first <= 0xf4) { count = 3; codepoint = first & 0x07; minimum = 0x10000; }
        else goto invalid_utf8;
        if (length - i < count) goto invalid_utf8;
        for (k = 0; k < count; k++) {
            unsigned int continuation = (unsigned char)input[i++];
            if ((continuation & 0xc0) != 0x80) goto invalid_utf8;
            codepoint = (codepoint << 6) | (continuation & 0x3f);
        }
        if (codepoint < minimum || codepoint > 0x10ffff ||
            (codepoint >= 0xd800 && codepoint <= 0xdfff)) goto invalid_utf8;
        if (codepoint <= 0xffff) {
            snprintf(output + used, 7, "\\u%04x", codepoint);
            used += 6;
        } else {
            codepoint -= 0x10000;
            snprintf(output + used, 13, "\\u%04x\\u%04x",
                     0xd800 + (codepoint >> 10), 0xdc00 + (codepoint & 0x3ff));
            used += 12;
        }
    }
    output[used] = '\0';
    *output_length = used;
    return output;
invalid_utf8:
    free(output);
    fail(error, capacity, "JSON contém UTF-8 inválido");
    return NULL;
}

static struct json_object *read_json(const char *path, char *error, size_t capacity)
{
    struct stat st;
    struct json_tokener *tokener;
    struct json_object *object = NULL;
    enum json_tokener_error parsing;
    char *data, *normalized = NULL;
    size_t used = 0, normalized_length, end;
    ssize_t count;
    int fd;
    if (!path || !path[0]) { fail(error, capacity, "Caminho ausente"); return NULL; }
    fd = open(path, O_RDONLY | O_NONBLOCK | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) { fail(error, capacity, "Não foi possível abrir %s: %s", path, strerror(errno)); return NULL; }
    if (fstat(fd, &st) || !S_ISREG(st.st_mode) || st.st_size < 0 ||
        (uintmax_t)st.st_size > TL_JSON_LIMIT) {
        close(fd);
        fail(error, capacity, "Use um arquivo regular de até 2 MiB, sem link simbólico");
        return NULL;
    }
    data = malloc(TL_JSON_LIMIT + 2U);
    if (!data) { close(fd); fail(error, capacity, "Memória insuficiente"); return NULL; }
    while (used <= TL_JSON_LIMIT) {
        count = read(fd, data + used, TL_JSON_LIMIT + 1U - used);
        if (count < 0 && errno == EINTR) continue;
        if (count < 0) { fail(error, capacity, "Erro ao ler projeto: %s", strerror(errno)); goto finished; }
        if (!count) break;
        used += (size_t)count;
    }
    if (used > TL_JSON_LIMIT) { fail(error, capacity, "Arquivo excede 2 MiB"); goto finished; }
    data[used] = '\0';
    normalized = ascii_json(data, used, &normalized_length, error, capacity);
    if (!normalized) goto finished;
    tokener = json_tokener_new_ex(32);
    if (!tokener) { fail(error, capacity, "Memória insuficiente"); goto finished; }
    json_tokener_set_flags(tokener, JSON_TOKENER_STRICT | JSON_TOKENER_VALIDATE_UTF8);
    object = json_tokener_parse_ex(tokener, normalized, (int)normalized_length);
    parsing = json_tokener_get_error(tokener);
    end = json_tokener_get_parse_end(tokener);
    while (end < normalized_length && isspace((unsigned char)normalized[end])) end++;
    if (parsing != json_tokener_success || end != normalized_length ||
        !json_object_is_type(object, json_type_object)) {
        if (object) json_object_put(object);
        object = NULL;
        fail(error, capacity, "JSON inválido: %s", json_tokener_error_desc(parsing));
    }
    json_tokener_free(tokener);
finished:
    free(normalized);
    free(data);
    close(fd);
    return object;
}

int tl_model_load(TLModel *model, const char *path, char *error, size_t capacity)
{
    TLModel candidate;
    struct json_object *root;
    int result;
    clear_error(error, capacity);
    if (!model) return fail(error, capacity, "Projeto ausente"), -1;
    root = read_json(path, error, capacity);
    if (!root) return -1;
    tl_model_init(&candidate);
    result = decode_model(root, &candidate, error, capacity);
    json_object_put(root);
    if (result) *model = candidate;
    return result ? 0 : -1;
}

int tl_model_contract(TLModel *model, const char *path, char *error, size_t capacity)
{
    TLModel candidate;
    TLGeometry native;
    struct json_object *root, *geometry;
    int version, i, result = 0;
    char unit[64];
    clear_error(error, capacity);
    if (!model) return fail(error, capacity, "Projeto ausente"), -1;
    if (!path || strlen(path) >= sizeof(model->contract_source))
        return fail(error, capacity, "Caminho do contrato inválido"), -1;
    root = read_json(path, error, capacity);
    if (!root) return -1;
    candidate = *model;
    native = candidate.native_measured;
    if (!int_member(root, "schema_version", 1, 1, &version, error, capacity) ||
        !member(root, "geometry", json_type_object, &geometry, error, capacity) ||
        !string_member(geometry, "unit", unit, sizeof(unit), error, capacity) ||
        !decode_geometry(geometry, &native, 7, error, capacity) ||
        !validate_geometry(&native, 1, "Contrato nativo", error, capacity)) goto finished;
    if (strcmp(unit, "native_pixel")) { fail(error, capacity, "Contrato deve usar pixels nativos"); goto finished; }
    candidate.native_measured = native;
    candidate.native_imported = 1;
    strcpy(candidate.contract_source, path);
    for (i = 0; i < TL_FAMILY_COUNT; i++) {
        int field;
        /* Seven imported measures; preserve tool font/padding and palette roles. */
        for (field = 0; field < 7; field++)
            tl_model_geometry_set(&candidate.recipes[i].geometry, field,
                                  tl_model_geometry_get(&native, field));
    }
    result = validate_model(&candidate, error, capacity);
    if (result) *model = candidate;
finished:
    json_object_put(root);
    return result ? 0 : -1;
}

static struct json_object *encode_geometry(const TLGeometry *geometry)
{
    struct json_object *object = json_object_new_object();
    int i;
    for (i = 0; i < TL_FIELD_COUNT; i++)
        json_object_object_add(object, tl_field_ids[i],
                               json_object_new_int(tl_model_geometry_get(geometry, i)));
    return object;
}

static struct json_object *encode_palette(const TLPaletteRules *p)
{
    struct json_object *object = json_object_new_object();
    json_object_object_add(object, "face_role", json_object_new_string(p->face_role));
    json_object_object_add(object, "text_role", json_object_new_string(p->text_role));
    json_object_object_add(object, "view_role", json_object_new_string(p->view_role));
    json_object_object_add(object, "selection_role", json_object_new_string(p->selection_role));
    json_object_object_add(object, "light", json_object_new_double(p->light));
    json_object_object_add(object, "shade", json_object_new_double(p->shade));
    json_object_object_add(object, "trough", json_object_new_double(p->trough));
    return object;
}

static struct json_object *encode_control_palettes(const TLRecipe *recipe)
{
    struct json_object *object=json_object_new_object();
    int control;
    if(!object) return NULL;
    for(control=0;control<TL_CONTROL_COUNT;control++)
        if(recipe->control_palette_custom[control])
            json_object_object_add(object,tl_control_ids[control],
                                   encode_palette(&recipe->control_palettes[control]));
    return object;
}

static struct json_object *encode_model(const TLModel *model)
{
    struct json_object *root = json_object_new_object();
    struct json_object *recipes = json_object_new_object();
    struct json_object *pick = json_object_new_object();
    struct json_object *rgb16 = json_object_new_array(), *rgb8 = json_object_new_array();
    struct json_object *provenance = json_object_new_object();
    struct json_object *measured = json_object_new_array(), *defaults = json_object_new_array();
    char exported_at[32] = "unavailable";
    time_t now = time(NULL);
    struct tm utc;
    int i;
    int version=model->schema_version;
    for(int family=0;family<TL_FAMILY_COUNT;family++)
        if(tl_scroll_parts_any(&model->recipes[family].scrollbar_parts) || model->recipes[family].selected_scroll_part)version=2;
    for(int family=0;family<TL_FAMILY_COUNT;family++)
        for(int control=0;control<TL_CONTROL_COUNT;control++)
            if(model->recipes[family].length_anchor[control])version=2;
    for(int family=0;family<TL_FAMILY_COUNT;family++)
        for(int control=0;control<TL_CONTROL_COUNT;control++)
            if(model->recipes[family].control_palette_custom[control])version=3;
    if(model->recipes[TL_GTK2].scale_slider_width_px!=8 ||
       model->recipes[TL_GTK2].scale_slider_length_px!=27)version=4;
    json_object_object_add(root, "schema_version", json_object_new_int(version));
    json_object_object_add(root, "kind", json_object_new_string("theme_lab_project"));
    json_object_object_add(root, "name", json_object_new_string(model->name));
    json_object_object_add(root, "reference", json_object_new_string(model->reference));
    json_object_object_add(root, "selected_family", json_object_new_string(tl_family_ids[model->selected]));
    json_object_object_add(root, "color_scheme", json_object_new_string(model->color_scheme));
    json_object_object_add(root, "separate_preview", json_object_new_boolean(model->separate_preview));
    json_object_object_add(root, "automatic_preview", json_object_new_boolean(model->automatic_preview));
    json_object_object_add(root, "debounce_ms", json_object_new_int(model->debounce_ms));
    json_object_object_add(root, "native_measured", encode_geometry(&model->native_measured));
    if (gmtime_r(&now, &utc)) strftime(exported_at, sizeof(exported_at), "%Y-%m-%dT%H:%M:%SZ", &utc);
    json_object_object_add(root, "exported_at", json_object_new_string(exported_at));
    for (i = 0; i < TL_FIELD_COUNT; i++)
        json_object_array_add(i < 7 ? measured : defaults, json_object_new_string(tl_field_ids[i]));
    json_object_object_add(provenance, "contract_source", json_object_new_string(model->contract_source));
    json_object_object_add(provenance, "native_imported", json_object_new_boolean(model->native_imported));
    json_object_object_add(provenance, "geometry_origin",
        json_object_new_string(model->native_imported ? "imported_contract" : "initial_adaptation_baseline"));
    json_object_object_add(provenance, "native_measurement_fields", measured);
    json_object_object_add(provenance, "tool_default_fields", defaults);
    json_object_object_add(provenance, "palette_factor_origin", json_object_new_string("adaptation"));
    json_object_object_add(provenance, "picked_policy", json_object_new_string("evidence_or_scheme_input_never_final_static_palette"));
    json_object_object_add(root, "provenance", provenance);
    for (i = 0; i < TL_FAMILY_COUNT; i++) {
        const TLRecipe *r = &model->recipes[i];
        struct json_object *recipe = json_object_new_object();
        struct json_object *positions = json_object_new_array();
        struct json_object *sizes = json_object_new_array();
        int control;
        json_object_object_add(recipe, "geometry", encode_geometry(&r->geometry));
        if (i == TL_GTK2 && version >= 4) {
            struct json_object *gtk2_geometry;
            json_object_object_get_ex(recipe, "geometry", &gtk2_geometry);
            json_object_object_add(gtk2_geometry, "scale_slider_width_px",
                                   json_object_new_int(r->scale_slider_width_px));
            json_object_object_add(gtk2_geometry, "scale_slider_length_px",
                                   json_object_new_int(r->scale_slider_length_px));
        }
        if (version >= 2)
            json_object_object_add(recipe,"scrollbar_parts",tl_scroll_parts_encode(&r->scrollbar_parts));
        json_object_object_add(recipe,"selected_scroll_part",json_object_new_int(r->selected_scroll_part));
        json_object_object_add(recipe, "palette", encode_palette(&r->palette));
        if(version>=3)
            json_object_object_add(recipe,"control_palettes",encode_control_palettes(r));
        json_object_object_add(recipe, "notes", json_object_new_string(r->notes));
        json_object_object_add(recipe, "visible_categories", json_object_new_int(r->visible_categories));
        json_object_object_add(recipe, "visible_controls", json_object_new_int(r->visible_controls));
        json_object_object_add(recipe, "selected_control", json_object_new_int(r->selected_control));
        json_object_object_add(recipe, "edit_state", json_object_new_int(r->edit_state));
        for (control = 0; control < TL_CONTROL_COUNT; control++) {
            struct json_object *pair = json_object_new_array();
            json_object_array_add(pair, json_object_new_int(r->positions[control][0]));
            json_object_array_add(pair, json_object_new_int(r->positions[control][1]));
            json_object_array_add(positions, pair);
            pair = json_object_new_array();
            json_object_array_add(pair, json_object_new_int(r->sizes[control][0]));
            json_object_array_add(pair, json_object_new_int(r->sizes[control][1]));
            json_object_array_add(sizes, pair);
        }
        json_object_object_add(recipe, "positions", positions);
        json_object_object_add(recipe, "sizes", sizes);
        if(version>=2) {
            json_object *anchors=json_object_new_array();
            for(control=0;control<TL_CONTROL_COUNT;control++)
                json_object_array_add(anchors,json_object_new_int(r->length_anchor[control]));
            json_object_object_add(recipe,"length_anchor",anchors);
        }
        json_object_object_add(recipes, tl_family_ids[i], recipe);
        if (i < 3) {
            json_object_array_add(rgb16, json_object_new_int(model->picked.rgb16[i]));
            json_object_array_add(rgb8, json_object_new_int(model->picked.rgb8[i]));
        }
    }
    json_object_object_add(root, "recipes", recipes);
    json_object_object_add(pick, "valid", json_object_new_boolean(model->picked.valid));
    json_object_object_add(pick, "rgb16", rgb16);
    json_object_object_add(pick, "rgb8", rgb8);
    json_object_object_add(pick, "x", json_object_new_int(model->picked.x));
    json_object_object_add(pick, "y", json_object_new_int(model->picked.y));
    json_object_object_add(pick, "visual_id", json_object_new_uint64(model->picked.visual_id));
    json_object_object_add(pick, "origin", json_object_new_string(model->picked.origin));
    json_object_object_add(pick, "purpose", json_object_new_string(model->picked.purpose));
    json_object_object_add(root, "picked", pick);
    return root;
}

static int open_output_parent(const char *path, char basename[TL_PATH_MAX],
                              char *error, size_t capacity)
{
    char parent[TL_PATH_MAX], *slash;
    struct stat st;
    int fd;
    if (!path || !path[0] || strlen(path) >= sizeof(parent))
        return fail(error, capacity, "Caminho de saída inválido"), -1;
    strcpy(parent, path);
    slash = strrchr(parent, '/');
    if (slash) {
        strcpy(basename, slash + 1);
        if (slash == parent) slash[1] = '\0'; else *slash = '\0';
    } else {
        strcpy(basename, parent);
        strcpy(parent, ".");
    }
    if (!basename[0] || !strcmp(basename, ".") || !strcmp(basename, ".."))
        return fail(error, capacity, "Nome de saída inválido"), -1;
    fd = open(parent, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) return fail(error, capacity, "Pasta de saída indisponível: %s", strerror(errno)), -1;
    if (fstat(fd, &st) || st.st_uid != geteuid() || (st.st_mode & (S_IWGRP | S_IWOTH))) {
        close(fd);
        return fail(error, capacity, "Use uma pasta própria sem permissão de escrita para terceiros"), -1;
    }
    return fd;
}

static int output_state(int directory, const char *name, struct stat *state,
                        int *exists, char *error, size_t capacity)
{
    if (fstatat(directory, name, state, AT_SYMLINK_NOFOLLOW)) {
        if (errno == ENOENT) { *exists = 0; return 1; }
        return fail(error, capacity, "Não foi possível verificar a saída: %s", strerror(errno));
    }
    *exists = 1;
    if (!S_ISREG(state->st_mode) || state->st_uid != geteuid() || state->st_size < 0 ||
        (uintmax_t)state->st_size > TL_JSON_LIMIT)
        return fail(error, capacity, "Saída existente deve ser regular, própria e de até 2 MiB; links/FIFOs recusados");
    return 1;
}

static int is_original(const TLModel *model, const char *path,
                       const struct stat *output, int exists)
{
    const char *originals[2] = {model->contract_source, model->reference};
    struct stat source;
    int i;
    for (i = 0; i < 2; i++) {
        if (!originals[i][0]) continue;
        if (!strcmp(originals[i], path)) return 1;
        if (exists && !stat(originals[i], &source) &&
            source.st_dev == output->st_dev && source.st_ino == output->st_ino)
            return 1;
    }
    return 0;
}

int tl_model_save(const TLModel *model, const char *path, char *error, size_t capacity)
{
    static unsigned int serial;
    struct json_object *root;
    const char *data;
    char basename[TL_PATH_MAX], temporary[128];
    struct stat initial, current;
    size_t length, written = 0;
    ssize_t count;
    int directory = -1, fd = -1, existed, exists_now, attempt, result = 0, temporary_created = 0;
    if (!validate_model(model, error, capacity)) return -1;
    if (path && is_original(model, path, NULL, 0))
        return fail(error, capacity, "Use outra saída; contrato e referência originais são preservados"), -1;
    root = encode_model(model);
    if (!root) return fail(error, capacity, "Memória insuficiente"), -1;
    data = json_object_to_json_string_ext(root, JSON_C_TO_STRING_PRETTY | JSON_C_TO_STRING_NOSLASHESCAPE);
    if (!data) { fail(error, capacity, "Falha ao serializar projeto"); goto finished; }
    length = strlen(data);
    if (length + 1U > TL_JSON_LIMIT) { fail(error, capacity, "Projeto excede 2 MiB; saída preservada"); goto finished; }
    directory = open_output_parent(path, basename, error, capacity);
    if (directory < 0 || !output_state(directory, basename, &initial, &existed, error, capacity)) goto finished;
    if (is_original(model, path, &initial, existed)) {
        fail(error, capacity, "Use outra saída; contrato e referência originais são preservados");
        goto finished;
    }
    for (attempt = 0; attempt < 100; attempt++) {
        snprintf(temporary, sizeof(temporary), ".theme-lab-%ld-%u.tmp", (long)getpid(), ++serial);
        fd = openat(directory, temporary, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
        if (fd >= 0) break;
        if (errno != EEXIST) { fail(error, capacity, "Falha ao criar saída temporária: %s", strerror(errno)); goto finished; }
    }
    if (fd < 0) { fail(error, capacity, "Nomes de saída temporária ocupados"); goto finished; }
    temporary_created = 1;
    while (written < length) {
        count = write(fd, data + written, length - written);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) { fail(error, capacity, "Falha ao gravar projeto: %s", strerror(errno)); goto finished; }
        written += (size_t)count;
    }
    if (write(fd, "\n", 1) != 1 || fchmod(fd, 0600) || fsync(fd)) {
        fail(error, capacity, "Falha ao concluir gravação: %s", strerror(errno)); goto finished;
    }
    if (close(fd)) { fd = -1; fail(error, capacity, "Falha ao fechar gravação: %s", strerror(errno)); goto finished; }
    fd = -1;
    if (!output_state(directory, basename, &current, &exists_now, error, capacity)) goto finished;
    if (existed != exists_now || (existed &&
        (initial.st_dev != current.st_dev || initial.st_ino != current.st_ino ||
         initial.st_size != current.st_size || initial.st_mtim.tv_sec != current.st_mtim.tv_sec ||
         initial.st_mtim.tv_nsec != current.st_mtim.tv_nsec))) {
        fail(error, capacity, "A saída mudou durante a gravação; alteração externa preservada"); goto finished;
    }
    if (renameat(directory, temporary, directory, basename)) {
        fail(error, capacity, "Falha ao substituir projeto: %s", strerror(errno)); goto finished;
    }
    temporary_created = 0;
    /* A successful rename already committed the regular 0600 file. */
    (void)fsync(directory);
    clear_error(error, capacity);
    result = 1;
finished:
    if (fd >= 0) close(fd);
    if (temporary_created) unlinkat(directory, temporary, 0);
    if (directory >= 0) close(directory);
    json_object_put(root);
    return result ? 0 : -1;
}

struct json_object *tl_model_encode(const TLModel *model,char *error,size_t capacity)
{
    if(tl_model_validate(model,error,capacity))return NULL;
    struct json_object *root=encode_model(model);
    if(!root) {fail(error,capacity,"Memória insuficiente");return NULL;}
    json_object_object_del(root,"exported_at");return root;
}
int tl_model_decode(TLModel *model,struct json_object *object,char *error,size_t capacity)
{
    TLModel candidate;
    if(!model)return fail(error,capacity,"Projeto ausente"),-1;
    tl_model_init(&candidate);
    if(!decode_model(object,&candidate,error,capacity))return -1;
    *model=candidate;return 0;
}
