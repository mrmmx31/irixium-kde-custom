/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "manual_paint.h"
#include <assert.h>
#include <json-c/json.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static char *read_text(const char *path) {
  FILE *f = fopen(path, "rb");
  long length;
  char *text;
  assert(f && fseek(f, 0, SEEK_END) == 0 && (length = ftell(f)) >= 0 &&
         fseek(f, 0, SEEK_SET) == 0);
  text = malloc((size_t)length + 1);
  assert(text && fread(text, 1, (size_t)length, f) == (size_t)length);
  text[length] = '\0';
  assert(fclose(f) == 0);
  return text;
}

static void write_json(json_object *root, const char *path) {
  const char *serialized =
      json_object_to_json_string_ext(root, JSON_C_TO_STRING_PRETTY);
  FILE *f;
  assert(serialized && (f = fopen(path, "wb")) != NULL);
  assert(fwrite(serialized, 1, strlen(serialized), f) == strlen(serialized));
  assert(fclose(f) == 0);
}

static json_object *find_document(json_object *root, int family, int control,
                                  int state, const char *part,
                                  const char *variant) {
  json_object *documents = NULL;
  assert(root && json_object_object_get_ex(root, "documents", &documents));
  for (size_t i = 0; i < json_object_array_length(documents); ++i) {
    json_object *item = json_object_array_get_idx(documents, i), *v;
    if (!json_object_object_get_ex(item, "family", &v) ||
        json_object_get_int(v) != family ||
        !json_object_object_get_ex(item, "control", &v) ||
        json_object_get_int(v) != control ||
        !json_object_object_get_ex(item, "state", &v) ||
        json_object_get_int(v) != state ||
        !json_object_object_get_ex(item, "part", &v) ||
        strcmp(json_object_get_string(v), part) ||
        !json_object_object_get_ex(item, "variant", &v) ||
        strcmp(json_object_get_string(v), variant))
      continue;
    return item;
  }
  return NULL;
}

static size_t write_bad_document(const char *valid, const char *bad) {
  json_object *root = json_object_from_file(valid);
  json_object *documents = NULL, *item = json_object_new_object();
  size_t index;
  assert(root && item &&
         json_object_object_get_ex(root, "documents", &documents));
  index = json_object_array_length(documents) + 1;
  json_object_object_add(item, "family", json_object_new_int(0));
  json_object_object_add(item, "control", json_object_new_int(0));
  json_object_object_add(item, "state", json_object_new_int(0));
  json_object_object_add(item, "part", json_object_new_string("whole"));
  json_object_object_add(item, "variant", json_object_new_string("auto"));
  json_object_object_add(item, "width", json_object_new_int(0));
  json_object_object_add(item, "height", json_object_new_int(0));
  json_object_object_add(item, "rgba_hex", json_object_new_string(""));
  assert(json_object_array_add(documents, item) == 0);
  write_json(root, bad);
  json_object_put(root);
  return index;
}

static void copy_member(json_object *to, json_object *from, const char *name) {
  json_object *value = NULL;
  assert(json_object_object_get_ex(from, name, &value));
  json_object_object_add(to, name, json_object_get(value));
}

static void write_schema1_project(const char *valid, const char *legacy) {
  json_object *source = json_object_from_file(valid);
  json_object *whole = find_document(source, 0, 0, 0, "whole", "auto");
  json_object *root = json_object_new_object(), *documents = json_object_new_array();
  json_object *item = json_object_new_object(), *placeholder = json_object_new_object();
  assert(source && whole && root && documents && item && placeholder);
  json_object_object_add(root, "schema_version", json_object_new_int(1));
  json_object_object_add(root, "kind",
                         json_object_new_string("theme_lab_manual_paint"));
  copy_member(item, whole, "family");
  copy_member(item, whole, "control");
  copy_member(item, whole, "state");
  copy_member(item, whole, "width");
  copy_member(item, whole, "height");
  copy_member(item, whole, "rgba_hex");
  assert(json_object_array_add(documents, item) == 0);
  json_object_object_add(placeholder, "family", json_object_new_int(2));
  json_object_object_add(placeholder, "control", json_object_new_int(11));
  json_object_object_add(placeholder, "state", json_object_new_int(0));
  json_object_object_add(placeholder, "width", json_object_new_int(0));
  json_object_object_add(placeholder, "height", json_object_new_int(0));
  json_object_object_add(placeholder, "rgba_hex", json_object_new_string(""));
  assert(json_object_array_add(documents, placeholder) == 0);
  json_object_object_add(root, "documents", documents);
  write_json(root, legacy);
  json_object_put(root);
  json_object_put(source);
}

static size_t duplicate_document(const char *valid, const char *duplicate) {
  json_object *root = json_object_from_file(valid), *documents = NULL;
  assert(root && json_object_object_get_ex(root, "documents", &documents));
  size_t index = json_object_array_length(documents) + 1;
  json_object *item = json_object_array_get_idx(documents, 0);
  assert(item && json_object_array_add(documents, json_object_get(item)) == 0);
  write_json(root, duplicate);
  json_object_put(root);
  return index;
}

static void write_invalid_identity(const char *valid, const char *invalid) {
  json_object *root = json_object_from_file(valid), *documents = NULL;
  assert(root && json_object_object_get_ex(root, "documents", &documents));
  json_object *item = json_object_array_get_idx(documents, 0);
  assert(item);
  json_object_object_add(item, "part", json_object_new_string("unknown"));
  write_json(root, invalid);
  json_object_put(root);
}

int main(int argc, char **argv) {
  char error[256];
  TLManualPaint *p, *loaded;
  char invalid_path[1024], recovered_path[1024], legacy_path[1024];
  char migrated_path[1024], legacy_recovered_path[1024];
  char duplicate_path[1024], invalid_identity_path[1024];
  const uint32_t ink = 0xff13a2c4u, ink2 = 0xffd05040u;
  assert(argc == 2);
  p = tl_manual_paint_new();
  assert(p && tl_manual_paint_current_family(p) == -1 &&
         tl_manual_paint_current_control(p) == -1 &&
         tl_manual_paint_current_state(p) == -1 &&
         tl_manual_paint_current_part(p) == -1 &&
         tl_manual_paint_current_variant(p) == -1);
  assert(tl_manual_paint_select(p, 0, 0, 0) == 0);
  assert(tl_manual_paint_current_family(p) == 0 &&
         tl_manual_paint_current_control(p) == 0 &&
         tl_manual_paint_current_state(p) == 0 &&
         tl_manual_paint_current_part(p) == TL_PAINT_PART_WHOLE &&
         tl_manual_paint_current_variant(p) == TL_PAINT_VARIANT_AUTO);
  assert(tl_manual_paint_width(p) == 96 && tl_manual_paint_height(p) == 32);
  assert(tl_manual_paint_line(p, 1, 1, 9, 1, ink) == 0);
  assert(tl_manual_paint_checkpoint(p) == 0);
  assert(tl_manual_paint_rect(p, 2, 2, 10, 8, ink) == 0);
  assert(tl_manual_paint_checkpoint(p) == 0);
  assert(tl_manual_paint_fill(p, 5, 5, ink2) == 0);
  assert(tl_manual_paint_checkpoint(p) == 0);
  assert(tl_manual_paint_pixel(p, 5, 5) == ink2);
  assert(tl_manual_paint_pixel(p, 2, 2) == ink);
  assert(tl_manual_paint_can_undo(p));
  assert(tl_manual_paint_undo(p) == 0 && tl_manual_paint_pixel(p, 5, 5) == 0);
  assert(tl_manual_paint_redo(p) == 0 &&
         tl_manual_paint_pixel(p, 5, 5) == ink2);
  assert(tl_manual_paint_select(p, 0, 0, 1) == 0);
  assert(tl_manual_paint_pixel(p, 5, 5) == 0);
  assert(tl_manual_paint_put(p, 3, 4, ink) == 0);
  assert(tl_manual_paint_checkpoint(p) == 0);
  assert(tl_manual_paint_resize(p, 120, 40) == 0);
  assert(tl_manual_paint_width(p) == 120 && tl_manual_paint_height(p) == 40);
  assert(tl_manual_paint_pixel(p, 3, 4) == ink);

  /* A reference import is one atomic, reversible operation even when both
   * dimensions change. */
  uint32_t imported[15 * 65];
  for (size_t i = 0; i < sizeof(imported) / sizeof(imported[0]); ++i)
    imported[i] = i & 1u ? ink : ink2;
  assert(tl_manual_paint_replace(p, 15, 65, imported) == 0);
  assert(tl_manual_paint_width(p) == 15 && tl_manual_paint_height(p) == 65);
  assert(tl_manual_paint_pixel(p, 0, 0) == ink2 &&
         tl_manual_paint_pixel(p, 1, 0) == ink);
  assert(tl_manual_paint_undo(p) == 0);
  assert(tl_manual_paint_width(p) == 120 && tl_manual_paint_height(p) == 40 &&
         tl_manual_paint_pixel(p, 3, 4) == ink);
  assert(tl_manual_paint_redo(p) == 0);
  assert(tl_manual_paint_width(p) == 15 && tl_manual_paint_height(p) == 65 &&
         tl_manual_paint_pixel(p, 1, 0) == ink);
  assert(tl_manual_paint_replace(p, 2, 2, imported) < 0);
  assert(tl_manual_paint_replace(p, 15, 65, NULL) < 0);
  assert(tl_manual_paint_width(p) == 15 && tl_manual_paint_height(p) == 65 &&
         tl_manual_paint_pixel(p, 1, 0) == ink);
  assert(tl_manual_paint_undo(p) == 0);
  assert(tl_manual_paint_width(p) == 120 && tl_manual_paint_height(p) == 40 &&
         tl_manual_paint_pixel(p, 3, 4) == ink);

  /* Piece identities own independent pixels and undo/redo histories. */
  assert(tl_manual_paint_select_piece(p, 0, 0, 0, TL_PAINT_PART_ARROW,
                                      TL_PAINT_VARIANT_START) == 0);
  assert(tl_manual_paint_put(p, 1, 1, ink) == 0);
  assert(tl_manual_paint_checkpoint(p) == 0);
  assert(tl_manual_paint_put(p, 2, 2, ink2) == 0);
  assert(tl_manual_paint_checkpoint(p) == 0);
  assert(tl_manual_paint_undo(p) == 0 && tl_manual_paint_pixel(p, 1, 1) == ink &&
         tl_manual_paint_pixel(p, 2, 2) == 0);
  assert(tl_manual_paint_select_piece(p, 0, 0, 0, TL_PAINT_PART_ARROW,
                                      TL_PAINT_VARIANT_END) == 0);
  assert(tl_manual_paint_pixel(p, 1, 1) == 0);
  assert(tl_manual_paint_put(p, 1, 1, ink2) == 0);
  assert(tl_manual_paint_checkpoint(p) == 0);
  assert(tl_manual_paint_select_piece(p, 0, 0, 0, TL_PAINT_PART_ARROW,
                                      TL_PAINT_VARIANT_START) == 0);
  assert(tl_manual_paint_can_redo(p) && tl_manual_paint_redo(p) == 0);
  assert(tl_manual_paint_pixel(p, 2, 2) == ink2);
  assert(tl_manual_paint_select_piece(p, 0, 0, 0, TL_PAINT_PART_TROUGH,
                                      TL_PAINT_VARIANT_BEFORE) == 0);
  assert(tl_manual_paint_pixel(p, 1, 1) == 0);
  assert(tl_manual_paint_select_piece(p, 0, 0, 0, TL_PAINT_PART_WHOLE,
                                      TL_PAINT_VARIANT_START) < 0);
  assert(tl_manual_paint_select_piece(p, 0, 0, 0, TL_PAINT_PART_THUMB,
                                      TL_PAINT_VARIANT_BEFORE) < 0);
  assert(tl_manual_paint_select_piece(
             p, 0, 0, 0, (TLManualPaintPart)TL_PAINT_PART_COUNT,
             TL_PAINT_VARIANT_AUTO) < 0);
  assert(tl_manual_paint_select_piece(
             p, 0, 0, 0, TL_PAINT_PART_ARROW,
             (TLManualPaintVariant)TL_PAINT_VARIANT_COUNT) < 0);
  assert(tl_manual_paint_current_part(p) == TL_PAINT_PART_TROUGH &&
         tl_manual_paint_current_variant(p) == TL_PAINT_VARIANT_BEFORE);
  assert(tl_manual_paint_select(p, 0, 0, 0) == 0);
  assert(tl_manual_paint_pixel(p, 5, 5) == ink2);
  assert(tl_manual_paint_save(p, argv[1], error, sizeof(error)) == 0);

  json_object *saved = json_object_from_file(argv[1]), *v = NULL,
              *documents = NULL;
  assert(saved && json_object_object_get_ex(saved, "schema_version", &v) &&
         json_object_get_int(v) == 2 &&
         json_object_object_get_ex(saved, "documents", &documents));
  size_t saved_documents = json_object_array_length(documents);
  assert(saved_documents == 5);
  assert(find_document(saved, 0, 0, 0, "whole", "auto") != NULL);
  assert(find_document(saved, 0, 0, 0, "arrow", "start") != NULL);
  assert(find_document(saved, 0, 0, 0, "arrow", "end") != NULL);
  assert(find_document(saved, 0, 0, 0, "trough", "before") != NULL);
  json_object_put(saved);

  loaded = tl_manual_paint_new();
  assert(loaded && tl_manual_paint_select(loaded, 0, 0, 0) == 0);
  assert(tl_manual_paint_load(loaded, argv[1], error, sizeof(error)) == 0);
  assert(tl_manual_paint_width(loaded) == 96);
  assert(tl_manual_paint_pixel(loaded, 5, 5) == ink2);
  assert(tl_manual_paint_select(loaded, 0, 0, 1) == 0);
  assert(tl_manual_paint_width(loaded) == 120);
  assert(tl_manual_paint_pixel(loaded, 3, 4) == ink);
  assert(tl_manual_paint_select_piece(loaded, 0, 0, 0, TL_PAINT_PART_ARROW,
                                      TL_PAINT_VARIANT_START) == 0);
  assert(tl_manual_paint_pixel(loaded, 1, 1) == ink &&
         tl_manual_paint_pixel(loaded, 2, 2) == ink2);
  assert(tl_manual_paint_select_piece(loaded, 0, 0, 0, TL_PAINT_PART_ARROW,
                                      TL_PAINT_VARIANT_END) == 0);
  assert(tl_manual_paint_pixel(loaded, 1, 1) == ink2 &&
         tl_manual_paint_pixel(loaded, 2, 2) == 0);

  assert(snprintf(invalid_path, sizeof(invalid_path), "%s.invalid", argv[1]) >
         0);
  assert(snprintf(recovered_path, sizeof(recovered_path), "%s.recovered", argv[1]) >
         0);
  assert(snprintf(legacy_path, sizeof(legacy_path), "%s.legacy", argv[1]) > 0);
  assert(snprintf(migrated_path, sizeof(migrated_path), "%s.migrated", argv[1]) >
         0);
  assert(snprintf(legacy_recovered_path, sizeof(legacy_recovered_path),
                  "%s.legacy-recovered", argv[1]) > 0);
  assert(snprintf(duplicate_path, sizeof(duplicate_path), "%s.duplicate",
                  argv[1]) > 0);
  assert(snprintf(invalid_identity_path, sizeof(invalid_identity_path),
                  "%s.invalid-identity", argv[1]) > 0);
  (void)unlink(recovered_path);
  (void)unlink(legacy_recovered_path);
  size_t bad_document = write_bad_document(argv[1], invalid_path);
  char *invalid_before = read_text(invalid_path);
  assert(tl_manual_paint_load(loaded, invalid_path, error, sizeof(error)) < 0);
  char expected_document[64];
  assert(snprintf(expected_document, sizeof(expected_document), "Documento %zu",
                  bad_document) > 0);
  assert(strstr(error, expected_document) != NULL);
  assert(strstr(error, "dimensões 0 x 0") != NULL);
  assert(strstr(error, "original preservado") != NULL);
  char *invalid_after = read_text(invalid_path);
  assert(strcmp(invalid_before, invalid_after) == 0);
  char recovery_message[256];
  assert(tl_manual_paint_recover(invalid_path, recovered_path, recovery_message,
                                 sizeof(recovery_message)) ==
         (int)saved_documents);
  char expected_recovered[64];
  assert(snprintf(expected_recovered, sizeof(expected_recovered),
                  "%zu camadas recuperadas", saved_documents) > 0);
  assert(strstr(recovery_message, expected_recovered) != NULL);
  assert(strstr(recovery_message, "1 inválidas ignoradas") != NULL);
  TLManualPaint *recovered = tl_manual_paint_new();
  assert(recovered && tl_manual_paint_select(recovered, 0, 0, 0) == 0);
  assert(tl_manual_paint_load(recovered, recovered_path, error, sizeof(error)) ==
         0);
  assert(tl_manual_paint_select(recovered, 0, 0, 0) == 0);
  assert(tl_manual_paint_pixel(recovered, 5, 5) == ink2);
  assert(tl_manual_paint_select(recovered, 0, 0, 1) == 0);
  assert(tl_manual_paint_pixel(recovered, 3, 4) == ink);
  assert(tl_manual_paint_select_piece(recovered, 0, 0, 0,
                                      TL_PAINT_PART_ARROW,
                                      TL_PAINT_VARIANT_START) == 0);
  assert(tl_manual_paint_pixel(recovered, 2, 2) == ink2);
  assert(tl_manual_paint_recover(invalid_path, recovered_path, recovery_message,
                                 sizeof(recovery_message)) < 0);
  assert(strstr(recovery_message, "destino já existe") != NULL);
  free(invalid_before);
  free(invalid_after);

  /* A real schema-1 zero-sized placeholder becomes transparent 96x32. */
  write_schema1_project(argv[1], legacy_path);
  TLManualPaint *legacy = tl_manual_paint_new();
  assert(legacy && tl_manual_paint_select(legacy, 2, 11, 0) == 0);
  assert(tl_manual_paint_load(legacy, legacy_path, error, sizeof(error)) == 0);
  assert(tl_manual_paint_current_family(legacy) == 2 &&
         tl_manual_paint_current_control(legacy) == 11 &&
         tl_manual_paint_current_state(legacy) == 0 &&
         tl_manual_paint_current_part(legacy) == TL_PAINT_PART_WHOLE &&
         tl_manual_paint_current_variant(legacy) == TL_PAINT_VARIANT_AUTO);
  assert(tl_manual_paint_width(legacy) == 96 &&
         tl_manual_paint_height(legacy) == 32 &&
         tl_manual_paint_pixel(legacy, 0, 0) == 0);
  assert(tl_manual_paint_select(legacy, 0, 0, 0) == 0 &&
         tl_manual_paint_pixel(legacy, 5, 5) == ink2);
  assert(tl_manual_paint_save(legacy, migrated_path, error, sizeof(error)) == 0);
  json_object *migrated = json_object_from_file(migrated_path);
  assert(migrated && json_object_object_get_ex(migrated, "schema_version", &v) &&
         json_object_get_int(v) == 2);
  json_object *placeholder =
      find_document(migrated, 2, 11, 0, "whole", "auto");
  assert(placeholder && json_object_object_get_ex(placeholder, "width", &v) &&
         json_object_get_int(v) == 96 &&
         json_object_object_get_ex(placeholder, "height", &v) &&
         json_object_get_int(v) == 32 &&
         json_object_object_get_ex(placeholder, "rgba_hex", &v) &&
         json_object_get_string_len(v) == 96 * 32 * 8);
  json_object_put(migrated);
  assert(tl_manual_paint_recover(legacy_path, legacy_recovered_path,
                                 recovery_message,
                                 sizeof(recovery_message)) == 2);
  migrated = json_object_from_file(legacy_recovered_path);
  assert(migrated && json_object_object_get_ex(migrated, "schema_version", &v) &&
         json_object_get_int(v) == 2 &&
         find_document(migrated, 2, 11, 0, "whole", "auto") != NULL);
  json_object_put(migrated);

  size_t duplicate_index = duplicate_document(argv[1], duplicate_path);
  assert(tl_manual_paint_load(loaded, duplicate_path, error, sizeof(error)) < 0);
  assert(snprintf(expected_document, sizeof(expected_document), "Documento %zu",
                  duplicate_index) > 0);
  assert(strstr(error, expected_document) != NULL &&
         strstr(error, "duplicada") != NULL);
  write_invalid_identity(argv[1], invalid_identity_path);
  assert(tl_manual_paint_load(loaded, invalid_identity_path, error,
                              sizeof(error)) < 0);
  assert(strstr(error, "Documento") != NULL &&
         strstr(error, "original preservado") != NULL);

  assert(tl_manual_paint_select(loaded, 0, 0, 0) == 0);
  assert(tl_manual_paint_pixel(loaded, 5, 5) == ink2);
  assert(unlink(invalid_path) == 0);
  assert(unlink(recovered_path) == 0);
  assert(unlink(legacy_path) == 0);
  assert(unlink(migrated_path) == 0);
  assert(unlink(legacy_recovered_path) == 0);
  assert(unlink(duplicate_path) == 0);
  assert(unlink(invalid_identity_path) == 0);
  tl_manual_paint_free(legacy);
  tl_manual_paint_free(recovered);
  assert(tl_manual_paint_select(loaded, 9, 15, 4) == 0);
  assert(tl_manual_paint_width(loaded) == 96);
  assert(tl_manual_paint_pixel(loaded, 3, 4) == 0);
  assert(tl_manual_paint_resize(loaded, 2, 2) < 0);
  tl_manual_paint_free(loaded);
  tl_manual_paint_free(p);
  puts("manual paint model: 1 passed; schema1 migration, piece identities, "
       "per-document undo/redo, validation, recovery, save/resume");
  return 0;
}
