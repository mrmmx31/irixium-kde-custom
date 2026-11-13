/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "board.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) {
  WBStore store = {0};
  const char *command = "gui", *id = NULL, *file = NULL, *reply = NULL,
             *status = NULL, *after = NULL, *kind = "instruction",
             *title = NULL, *helper = NULL, *config = NULL;
  int expected = -1, i, result = -1;
  char inserted[64];
  json_object *root = NULL, *input = NULL;
  for (i = 1; i < argc; i++) {
    const char *arg = argv[i];
    if (i + 1 >= argc) {
      fprintf(stderr, "Argumento sem valor: %s\n", arg);
      return 2;
    }
    if (!strcmp(arg, "--state"))
      store.state = argv[++i];
    else if (!strcmp(arg, "--seed"))
      store.seed = argv[++i];
    else if (!strcmp(arg, "--command"))
      command = argv[++i];
    else if (!strcmp(arg, "--id"))
      id = argv[++i];
    else if (!strcmp(arg, "--revision")) {
      char *end;
      long n = strtol(argv[++i], &end, 10);
      if (*end || n < 0 || n > 1000000000)
        return 2;
      expected = (int)n;
    } else if (!strcmp(arg, "--input"))
      file = argv[++i];
    else if (!strcmp(arg, "--reply"))
      reply = argv[++i];
    else if (!strcmp(arg, "--status"))
      status = argv[++i];
    else if (!strcmp(arg, "--after"))
      after = argv[++i];
    else if (!strcmp(arg, "--kind"))
      kind = argv[++i];
    else if (!strcmp(arg, "--title"))
      title = argv[++i];
    else if (!strcmp(arg, "--colors-helper"))
      helper = argv[++i];
    else if (!strcmp(arg, "--kde-config"))
      config = argv[++i];
    else {
      fprintf(stderr, "Opção desconhecida: %s\n", arg);
      return 2;
    }
  }
  if (!store.state || !store.seed) {
    fprintf(stderr, "Use --state arquivo.json --seed checklist.json [--command "
                    "gui|sync|read|user|ack|reply|insert]\n");
    return 2;
  }
  if (!strcmp(command, "sync") || !strcmp(command, "gui")) {
    if (wb_sync(&store)) {
      fprintf(stderr, "%s\n", store.error);
      return 1;
    }
    if (!strcmp(command, "sync"))
      return 0;
    int xtargc = 1;
    char *xtargv[] = {argv[0], NULL};
    return wb_run_view(&store, helper, config, xtargc, xtargv);
  }
  if (!strcmp(command, "read")) {
    root = wb_load(&store);
    if (root) {
      puts(json_object_to_json_string_ext(root, JSON_C_TO_STRING_PRETTY));
      json_object_put(root);
      return 0;
    }
  } else if (!strcmp(command, "user") && id && file && expected >= 0) {
    input = wb_load_file(file, store.error, sizeof(store.error));
    if (input)
      result = wb_save_user(&store, id, expected, input);
  } else if ((!strcmp(command, "ack") || !strcmp(command, "reply")) && id &&
             expected >= 0) {
    if (file) {
      input = wb_load_file(file, store.error, sizeof(store.error));
      if (!input)
        goto done;
      reply = wb_string(input, "reply");
      if (!status && *wb_string(input, "status"))
        status = wb_string(input, "status");
    }
    if (!strcmp(command, "ack") || reply)
      result = wb_assistant(&store, id, expected, reply, status);
  } else if (!strcmp(command, "insert") && after && title) {
    result = wb_insert(&store, after, kind, title, inserted, sizeof(inserted));
    if (!result)
      puts(inserted);
  } else
    snprintf(store.error, sizeof(store.error),
             "Comando incompleto ou inválido.");
done:
  json_object_put(input);
  if (result)
    fprintf(stderr, "%s\n",
            *store.error ? store.error : "Operação não realizada.");
  return result ? 1 : 0;
}
