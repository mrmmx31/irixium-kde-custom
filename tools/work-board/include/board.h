/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef WORK_BOARD_H
#define WORK_BOARD_H
#include <json-c/json.h>
#include <stddef.h>
#define WB_LIMIT (2 * 1024 * 1024)
typedef struct {
  const char *state, *seed;
  char error[512];
} WBStore;
const char *wb_string(json_object *obj, const char *key);
int wb_number(json_object *obj, const char *key);
int wb_boolean(json_object *obj, const char *key);
json_object *wb_clone(json_object *obj);
json_object *wb_find(json_object *root, const char *id);
json_object *wb_load_file(const char *path, char *error, size_t capacity);
json_object *wb_load_drafts(WBStore *store);
int wb_save_drafts(WBStore *store, json_object *drafts);
json_object *wb_load(WBStore *store);
int wb_sync(WBStore *store);
int wb_save_user(WBStore *store, const char *id, int expected,
                 json_object *user);
int wb_assistant(WBStore *store, const char *id, int expected,
                 const char *reply, const char *status);
int wb_insert(WBStore *store, const char *after, const char *kind,
              const char *title, char *id, size_t capacity);
int wb_run_view(WBStore *store, const char *helper, const char *config,
                int argc, char **argv);
#endif
