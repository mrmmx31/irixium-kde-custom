/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include "theme_lab.h"
#include <json-c/json.h>
#include <assert.h>
#include <fcntl.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

static char directory[TL_PATH_MAX], project[TL_PATH_MAX], malformed[TL_PATH_MAX];
static char error[1024];
static int checks;

#define CHECK(expression) do { if (!(expression)) { \
    fprintf(stderr, "%s:%d: %s; %s\n", __FILE__, __LINE__, #expression, error); \
    exit(1); } checks++; } while (0)

static void file_path(char *target, size_t capacity, const char *name)
{
    int count = snprintf(target, capacity, "%s/%s", directory, name);
    CHECK(count >= 0 && (size_t)count < capacity);
}

static char *read_file(const char *path, size_t *length)
{
    FILE *file = fopen(path, "rb");
    long size;
    char *text;
    CHECK(file != NULL);
    CHECK(!fseek(file, 0, SEEK_END));
    size = ftell(file);
    CHECK(size >= 0);
    rewind(file);
    text = malloc((size_t)size + 1);
    CHECK(text != NULL);
    CHECK(fread(text, 1, (size_t)size, file) == (size_t)size);
    CHECK(!fclose(file));
    text[size] = '\0';
    if (length) *length = (size_t)size;
    return text;
}

static void write_file(const char *path, const char *text)
{
    FILE *file = fopen(path, "wb");
    size_t length = strlen(text);
    CHECK(file != NULL);
    CHECK(fwrite(text, 1, length, file) == length);
    CHECK(!fclose(file));
}

static struct json_object *root_json(void)
{
    char *text = read_file(project, NULL);
    struct json_object *root = json_tokener_parse(text);
    CHECK(root != NULL);
    free(text);
    return root;
}

static struct json_object *field(struct json_object *object, const char *key)
{
    struct json_object *value;
    CHECK(json_object_object_get_ex(object, key, &value));
    return value;
}

static void rejected(TLModel *model, struct json_object *root)
{
    TLModel original = *model;
    write_file(malformed, json_object_to_json_string(root));
    CHECK(tl_model_load(model, malformed, error, sizeof(error)) == -1);
    CHECK(error[0]);
    CHECK(!memcmp(model, &original, sizeof(original)));
    json_object_put(root);
}

static void test_roundtrip(TLModel *model)
{
    TLModel loaded;
    struct stat state;
    int i;
    tl_model_init(model);
    CHECK(tl_model_validate(model, error, sizeof(error)) == 0);
    CHECK(!strcmp(tl_family_ids[TL_GTK3], "gtk3"));
    CHECK(!strcmp(tl_field_ids[8], "font_px"));
    model->selected = TL_GTK4;
    strcpy(model->name, "Outro tema — revisão α 🧪");
    strcpy(model->reference, "/tmp/referência.png");
    strcpy(model->recipes[TL_GTK4].notes, "Proposta exploratória; não é uma medida da VM.");
    model->recipes[TL_GTK4].geometry.bar_px = 22;
    model->recipes[TL_GTK4].geometry.shadow_px = 3;
    model->recipes[TL_GTK4].geometry.thumb_cross_px = 15;
    model->recipes[TL_GTK4].palette.light = .375;
    model->picked.valid = 1;
    model->picked.visual_id = ULONG_MAX;
    model->picked.x = -170;
    model->picked.y = 432;
    strcpy(model->picked.origin, "XQueryColor, amostra original RGB16");
    strcpy(model->picked.purpose, "scheme_input");
    model->picked.rgb16[0] = 65535;
    model->picked.rgb16[1] = 12345;
    model->picked.rgb8[0] = 255;
    model->picked.rgb8[1] = 48;
    CHECK(tl_model_save(model, project, error, sizeof(error)) == 0);
    CHECK(!stat(project, &state));
    CHECK((state.st_mode & 0777) == 0600);
    memset(&loaded, 0xa5, sizeof(loaded));
    CHECK(tl_model_load(&loaded, project, error, sizeof(error)) == 0);
    CHECK(!strcmp(model->name, loaded.name));
    CHECK(!strcmp(model->reference, loaded.reference));
    CHECK(model->selected == loaded.selected);
    CHECK(model->picked.visual_id == loaded.picked.visual_id);
    CHECK(model->picked.rgb16[1] == loaded.picked.rgb16[1]);
    CHECK(model->picked.x == loaded.picked.x);
    CHECK(!strcmp(model->picked.purpose, loaded.picked.purpose));
    CHECK(loaded.native_measured.bar_px == 15);
    for (i = 0; i < TL_FAMILY_COUNT; i++) {
        CHECK(!memcmp(&model->recipes[i].geometry, &loaded.recipes[i].geometry, sizeof(TLGeometry)));
        CHECK(model->recipes[i].palette.light == loaded.recipes[i].palette.light);
        CHECK(!strcmp(model->recipes[i].palette.face_role, loaded.recipes[i].palette.face_role));
        CHECK(!strcmp(model->recipes[i].notes, loaded.recipes[i].notes));
    }
}

static void test_rejects(TLModel *model)
{
    struct json_object *root, *value;
    TLModel invalid;
    char oversized[sizeof(model->name) + 1];
    root = root_json();
    json_object_object_add(root, "schema_version", json_object_new_string("1"));
    rejected(model, root);
    root = root_json();
    json_object_object_del(field(root, "recipes"), "gtk5");
    rejected(model, root);
    root = root_json();
    value = field(field(field(root, "recipes"), "gtk2"), "geometry");
    json_object_object_add(value, "bar_px", json_object_new_double(15));
    rejected(model, root);
    root = root_json();
    value = field(field(field(root, "recipes"), "motif"), "geometry");
    json_object_object_add(value, "arrow_px", json_object_new_int(10));
    rejected(model, root);
    root = root_json();
    json_object_object_add(field(root, "picked"), "valid", json_object_new_int(1));
    rejected(model, root);
    root = root_json();
    value = field(field(root, "picked"), "rgb16");
    json_object_array_put_idx(value, 1, json_object_new_int(65536));
    rejected(model, root);
    root = root_json();
    json_object_object_add(field(root, "picked"), "visual_id", json_object_new_int(-1));
    rejected(model, root);
    root = root_json();
    value = field(field(field(root, "recipes"), "plasma"), "palette");
    json_object_object_add(value, "face_role", json_object_new_string("#78a0d5"));
    rejected(model, root);
    root = root_json();
    json_object_object_add(root, "name", json_object_new_string_len("Tema\0oculto", 11));
    rejected(model, root);
    memset(oversized, 'a', sizeof(oversized) - 1);
    oversized[sizeof(oversized) - 1] = '\0';
    root = root_json();
    json_object_object_add(root, "name", json_object_new_string(oversized));
    rejected(model, root);
    root = root_json();
    json_object_object_add(root, "selected_family", json_object_new_string("inventado"));
    rejected(model, root);
    root = root_json();
    json_object_object_add(field(root, "picked"), "purpose", json_object_new_string("final_static_palette"));
    rejected(model, root);
    root = root_json();
    json_object_object_add(field(root, "provenance"), "native_imported", json_object_new_int(1));
    rejected(model, root);
    invalid = *model;
    invalid.recipes[TL_QT5].palette.shade = NAN;
    CHECK(tl_model_validate(&invalid, error, sizeof(error)) == -1);
    CHECK(strstr(error, "qt5") != NULL);
    invalid = *model;
    memset(invalid.name, 'x', sizeof(invalid.name));
    CHECK(tl_model_validate(&invalid, error, sizeof(error)) == -1);
    invalid = *model;
    invalid.recipes[TL_GTK3].geometry.arrow_px = 9;
    CHECK(tl_model_validate(&invalid, error, sizeof(error)) == -1);
    invalid = *model;
    invalid.recipes[TL_GTK3].geometry.view_inset_px = 3;
    CHECK(tl_model_validate(&invalid, error, sizeof(error)) == -1);
}

static double elapsed(struct timespec start, struct timespec end)
{
    return (double)(end.tv_sec - start.tv_sec) +
           (double)(end.tv_nsec - start.tv_nsec) / 1e9;
}

static void test_files(TLModel *model)
{
    char link[TL_PATH_MAX], fifo[TL_PATH_MAX], huge[TL_PATH_MAX], folder[TL_PATH_MAX];
    char *before, *after;
    TLModel original = *model, invalid = *model;
    struct timespec start, end;
    struct stat old_state, new_state;
    int fd;
    file_path(link, sizeof(link), "project-link.json");
    file_path(fifo, sizeof(fifo), "pipe.json");
    file_path(huge, sizeof(huge), "huge.json");
    file_path(folder, sizeof(folder), "not-a-file");
    CHECK(!symlink(project, link));
    before = read_file(project, NULL);
    CHECK(tl_model_save(model, link, error, sizeof(error)) == -1);
    CHECK(tl_model_load(model, link, error, sizeof(error)) == -1);
    CHECK(!memcmp(model, &original, sizeof(original)));
    after = read_file(project, NULL);
    CHECK(!strcmp(before, after));
    free(after);
    CHECK(!mkfifo(fifo, 0600));
    CHECK(!clock_gettime(CLOCK_MONOTONIC, &start));
    CHECK(tl_model_load(model, fifo, error, sizeof(error)) == -1);
    CHECK(tl_model_save(model, fifo, error, sizeof(error)) == -1);
    CHECK(!clock_gettime(CLOCK_MONOTONIC, &end));
    CHECK(elapsed(start, end) < 1.0);
    CHECK(!memcmp(model, &original, sizeof(original)));
    fd = open(huge, O_WRONLY | O_CREAT | O_EXCL, 0600);
    CHECK(fd >= 0);
    CHECK(!ftruncate(fd, 2 * 1024 * 1024 + 1));
    CHECK(!close(fd));
    CHECK(tl_model_load(model, huge, error, sizeof(error)) == -1);
    CHECK(strstr(error, "2 MiB") != NULL);
    CHECK(tl_model_save(model, huge, error, sizeof(error)) == -1);
    CHECK(!mkdir(folder, 0700));
    CHECK(tl_model_save(model, folder, error, sizeof(error)) == -1);
    invalid.recipes[TL_PLASMA].geometry.font_px = 49;
    CHECK(tl_model_save(&invalid, project, error, sizeof(error)) == -1);
    after = read_file(project, NULL);
    CHECK(!strcmp(before, after));
    free(after);
    free(before);
    CHECK(!stat(project, &old_state));
    CHECK(!chmod(project, 0644));
    strcpy(model->recipes[TL_QT6].notes, "Segunda gravação atômica");
    CHECK(tl_model_save(model, project, error, sizeof(error)) == 0);
    CHECK(!stat(project, &new_state));
    CHECK(old_state.st_ino != new_state.st_ino);
    CHECK((new_state.st_mode & 0777) == 0600);
    write_file(malformed, "{} trailing-json");
    original = *model;
    CHECK(tl_model_load(model, malformed, error, sizeof(error)) == -1);
    CHECK(!memcmp(model, &original, sizeof(original)));
    write_file(malformed, "{\"name\":\"\300\257\"}");
    CHECK(tl_model_load(model, malformed, error, sizeof(error)) == -1);
    CHECK(strstr(error, "UTF-8") != NULL);
    CHECK(!memcmp(model, &original, sizeof(original)));
    write_file(malformed, "{/* comment */\"name\":\"test\"}");
    CHECK(tl_model_load(model, malformed, error, sizeof(error)) == -1);
    CHECK(!unlink(link));
    CHECK(!unlink(fifo));
    CHECK(!unlink(huge));
    CHECK(!rmdir(folder));
}

static void test_contract(TLModel *model, const char *contract)
{
    char *before, *after;
    TLModel original;
    struct json_object *root, *geometry;
    int i;
    before = read_file(contract, NULL);
    model->recipes[TL_GTK2].geometry.control_padding_px = 7;
    model->recipes[TL_GTK2].geometry.font_px = 16;
    CHECK(tl_model_contract(model, contract, error, sizeof(error)) == 0);
    CHECK(model->native_measured.bar_px == 15);
    CHECK(model->native_measured.shadow_px == 2);
    CHECK(model->native_measured.arrow_px == 11);
    CHECK(model->native_measured.thumb_cross_px == 11);
    CHECK(model->native_measured.arrow_thumb_gap_px == 1);
    CHECK(model->native_measured.view_bar_gap_px == 4);
    CHECK(model->native_measured.view_inset_px == 2);
    CHECK(model->recipes[TL_GTK2].geometry.control_padding_px == 7);
    CHECK(model->recipes[TL_GTK2].geometry.font_px == 16);
    CHECK(!strcmp(model->name, "Outro tema — revisão α 🧪"));
    CHECK(model->recipes[TL_GTK4].palette.light == .375);
    CHECK(model->native_imported == 1);
    CHECK(!strcmp(model->contract_source, contract));
    for (i = 0; i < TL_FAMILY_COUNT; i++)
        CHECK(model->recipes[i].geometry.bar_px == model->native_measured.bar_px);
    after = read_file(contract, NULL);
    CHECK(!strcmp(before, after));
    free(after);
    CHECK(tl_model_save(model, contract, error, sizeof(error)) == -1);
    CHECK(strstr(error, "originais") != NULL);
    after = read_file(contract, NULL);
    CHECK(!strcmp(before, after));
    free(after);
    CHECK(tl_model_save(model, project, error, sizeof(error)) == 0);
    {
        TLModel loaded;
        CHECK(tl_model_load(&loaded, project, error, sizeof(error)) == 0);
        CHECK(loaded.native_imported == 1);
        CHECK(!strcmp(loaded.contract_source, contract));
    }
    root = json_tokener_parse(before);
    free(before);
    CHECK(root != NULL);
    geometry = field(root, "geometry");
    json_object_object_add(geometry, "shadow_px", json_object_new_string("2"));
    write_file(malformed, json_object_to_json_string(root));
    json_object_put(root);
    original = *model;
    CHECK(tl_model_contract(model, malformed, error, sizeof(error)) == -1);
    CHECK(!memcmp(model, &original, sizeof(original)));
}

static void test_layout(void)
{
    TLModel model, loaded, defaults;
    struct json_object *root, *recipes, *recipe, *positions, *pair;
    int i, control;
    const char *optional[] = {"visible_categories", "visible_controls",
                             "selected_control", "edit_state", "positions"};
    tl_model_init(&model);
    defaults = model;
    CHECK(model.automatic_preview == 0);
    CHECK(model.debounce_ms == 600);
    CHECK(!model.color_scheme[0]);
    strcpy(model.name, "Layout reutilizável");
    strcpy(model.color_scheme, "DomainOS-SR10.4");
    model.automatic_preview = 1;
    model.debounce_ms = 1700;
    for (i = 0; i < TL_FAMILY_COUNT; i++) {
        TLRecipe *recipe_model = &model.recipes[i];
        recipe_model->visible_categories = (i + 1) & 31;
        recipe_model->visible_controls = 65535 ^ (1 << i);
        recipe_model->selected_control = i;
        recipe_model->edit_state = i % 4;
        for (control = 0; control < TL_CONTROL_COUNT; control++) {
            recipe_model->positions[control][0] = i * 7 + control * 17;
            recipe_model->positions[control][1] = i * 11 + control * 23;
        }
    }
    model.recipes[TL_GTK1].positions[15][0] = 2048;
    model.recipes[TL_GTK1].positions[15][1] = 0;
    CHECK(tl_model_save(&model, project, error, sizeof(error)) == 0);
    CHECK(tl_model_load(&loaded, project, error, sizeof(error)) == 0);
    CHECK(!strcmp(loaded.color_scheme, model.color_scheme));
    CHECK(loaded.automatic_preview == 1);
    CHECK(loaded.debounce_ms == 1700);
    for (i = 0; i < TL_FAMILY_COUNT; i++) {
        CHECK(loaded.recipes[i].visible_categories == model.recipes[i].visible_categories);
        CHECK(loaded.recipes[i].visible_controls == model.recipes[i].visible_controls);
        CHECK(loaded.recipes[i].selected_control == model.recipes[i].selected_control);
        CHECK(loaded.recipes[i].edit_state == model.recipes[i].edit_state);
        CHECK(!memcmp(loaded.recipes[i].positions, model.recipes[i].positions,
                      sizeof(model.recipes[i].positions)));
    }
    /* Old schema-1 projects receive tool defaults, not the currently open layout. */
    root = root_json();
    json_object_object_del(root, "color_scheme");
    json_object_object_del(root, "automatic_preview");
    json_object_object_del(root, "debounce_ms");
    recipes = field(root, "recipes");
    for (i = 0; i < TL_FAMILY_COUNT; i++) {
        recipe = field(recipes, tl_family_ids[i]);
        for (control = 0; control < 5; control++)
            json_object_object_del(recipe, optional[control]);
    }
    write_file(malformed, json_object_to_json_string(root));
    json_object_put(root);
    CHECK(tl_model_load(&loaded, malformed, error, sizeof(error)) == 0);
    CHECK(!strcmp(loaded.name, model.name));
    CHECK(!loaded.color_scheme[0]);
    CHECK(loaded.automatic_preview == defaults.automatic_preview);
    CHECK(loaded.debounce_ms == defaults.debounce_ms);
    for (i = 0; i < TL_FAMILY_COUNT; i++) {
        CHECK(loaded.recipes[i].visible_categories == defaults.recipes[i].visible_categories);
        CHECK(loaded.recipes[i].visible_controls == defaults.recipes[i].visible_controls);
        CHECK(loaded.recipes[i].selected_control == defaults.recipes[i].selected_control);
        CHECK(loaded.recipes[i].edit_state == defaults.recipes[i].edit_state);
        CHECK(!memcmp(loaded.recipes[i].positions, defaults.recipes[i].positions,
                      sizeof(defaults.recipes[i].positions)));
    }
    root = root_json();
    json_object_object_add(root, "automatic_preview", json_object_new_int(1));
    rejected(&loaded, root);
    root = root_json();
    json_object_object_add(root, "debounce_ms", json_object_new_int(99));
    rejected(&loaded, root);
    root = root_json();
    json_object_object_add(root, "debounce_ms", json_object_new_int(10001));
    rejected(&loaded, root);
    root = root_json();
    json_object_object_add(root, "color_scheme", json_object_new_string("../other.colors"));
    rejected(&loaded, root);
    root = root_json();
    recipe = field(field(root, "recipes"), "gtk5");
    json_object_object_add(recipe, "selected_control", json_object_new_int(16));
    rejected(&loaded, root);
    root = root_json();
    recipe = field(field(root, "recipes"), "qt6");
    json_object_object_add(recipe, "visible_categories", json_object_new_int(32));
    rejected(&loaded, root);
    root = root_json();
    recipe = field(field(root, "recipes"), "gtk1");
    json_object_object_add(recipe, "visible_controls", json_object_new_int(-1));
    rejected(&loaded, root);
    root = root_json();
    recipe = field(field(root, "recipes"), "plasma");
    json_object_object_add(recipe, "edit_state", json_object_new_int(4));
    rejected(&loaded, root);
    root = root_json();
    recipe = field(field(root, "recipes"), "motif");
    json_object_object_add(recipe, "positions", json_object_new_array());
    rejected(&loaded, root);
    root = root_json();
    positions = field(field(field(root, "recipes"), "gtk3"), "positions");
    pair = json_object_array_get_idx(positions, 1);
    json_object_array_add(pair, json_object_new_int(1));
    rejected(&loaded, root);
    root = root_json();
    positions = field(field(field(root, "recipes"), "qt5"), "positions");
    pair = json_object_array_get_idx(positions, 1);
    json_object_array_put_idx(pair, 0, json_object_new_double(12.5));
    rejected(&loaded, root);
    root = root_json();
    positions = field(field(field(root, "recipes"), "kvantum"), "positions");
    pair = json_object_array_get_idx(positions, 1);
    json_object_array_put_idx(pair, 1, json_object_new_int(2049));
    rejected(&loaded, root);
    model.recipes[TL_GTK5].positions[4][1] = -1;
    CHECK(tl_model_validate(&model, error, sizeof(error)) == -1);
    CHECK(strstr(error, "gtk5") != NULL);
}

int main(int argc, char **argv)
{
    TLModel model;
    char template[] = "/tmp/theme-lab-model-XXXXXX";
    const char *contract = argc > 1 ? argv[1] : "tools/domainos_scrollbar_rules.json";
    char *created = mkdtemp(template);
    CHECK(created != NULL);
    CHECK(strlen(created) < sizeof(directory));
    strcpy(directory, created);
    file_path(project, sizeof(project), "project.json");
    file_path(malformed, sizeof(malformed), "malformed.json");
    if (argc > 1 && !strcmp(argv[1], "--layout-only")) {
        test_layout();
    } else {
        test_roundtrip(&model);
        test_rejects(&model);
        test_files(&model);
        test_contract(&model, contract);
        test_layout();
    }
    CHECK(!unlink(project));
    CHECK(!unlink(malformed));
    CHECK(!rmdir(directory));
    printf("Model: %d verificações offline passaram; nenhuma GUI ou tema foi alterado.\n", checks);
    return 0;
}
