/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "board.h"
#include <errno.h>
#include <fcntl.h>
#include <openssl/sha.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

const char *wb_string(json_object *o, const char *key) {
  json_object *v = NULL;
  return o && json_object_object_get_ex(o, key, &v) &&
                 json_object_is_type(v, json_type_string)
             ? json_object_get_string(v)
             : "";
}
int wb_number(json_object *o, const char *key) {
  json_object *v = NULL;
  return o && json_object_object_get_ex(o, key, &v) ? json_object_get_int(v)
                                                    : 0;
}
int wb_boolean(json_object *o, const char *key) {
  json_object *v = NULL;
  return o && json_object_object_get_ex(o, key, &v) &&
         json_object_get_boolean(v);
}
json_object *wb_clone(json_object *o) {
  return o ? json_tokener_parse(
                 json_object_to_json_string_ext(o, JSON_C_TO_STRING_PLAIN))
           : NULL;
}
static void str(json_object *o, const char *key, const char *v) {
  json_object_object_add(o, key, json_object_new_string(v));
}
static void timestamp(char *buf, size_t n) {
  struct timespec t;
  struct tm utc;
  char date[32];
  clock_gettime(CLOCK_REALTIME, &t);
  gmtime_r(&t.tv_sec, &utc);
  strftime(date, sizeof(date), "%Y-%m-%dT%H:%M:%S", &utc);
  snprintf(buf, n, "%s.%03ldZ", date, t.tv_nsec / 1000000);
}
static int fail(WBStore *s, const char *msg) {
  snprintf(s->error, sizeof(s->error), "%s", msg);
  return -1;
}
static json_object *load_file(const char *path, char *error, size_t cap,
                              size_t limit) {
  int fd = open(path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK);
  struct stat st;
  char *buf;
  ssize_t n;
  size_t done = 0;
  json_object *obj = NULL;
  json_tokener *tok;
  if (fd < 0) {
    snprintf(error, cap, "Não foi possível abrir: %s", strerror(errno));
    return NULL;
  }
  if (fstat(fd, &st) || !S_ISREG(st.st_mode) || (size_t)st.st_size > limit) {
    close(fd);
    snprintf(error, cap, "JSON deve ser arquivo regular dentro do limite.");
    return NULL;
  }
  buf = malloc(limit + 1);
  if (!buf) {
    close(fd);
    return NULL;
  }
  while (done < limit && (n = read(fd, buf + done, limit - done)) != 0) {
    if (n < 0) {
      if (errno == EINTR)
        continue;
      goto end;
    }
    done += (size_t)n;
  }
  if (done == limit)
    goto end;
  buf[done] = 0;
  tok = json_tokener_new();
  obj = json_tokener_parse_ex(tok, buf, (int)done);
  if (json_tokener_get_error(tok) != json_tokener_success ||
      !json_object_is_type(obj, json_type_object)) {
    json_object_put(obj);
    obj = NULL;
  } else {
    size_t used = json_tokener_get_parse_end(tok);
    while (used < done && (buf[used] == ' ' || buf[used] == '\n' ||
                           buf[used] == '\r' || buf[used] == '\t'))
      ++used;
    if (used != done) {
      json_object_put(obj);
      obj = NULL;
    }
  }
  json_tokener_free(tok);
end:
  close(fd);
  free(buf);
  if (!obj)
    snprintf(error, cap,
             "JSON inválido ou leitura incompleta; o arquivo foi preservado.");
  return obj;
}
json_object *wb_load_file(const char *path, char *error, size_t cap) {
  return load_file(path, error, cap, WB_LIMIT);
}
json_object *wb_load_drafts(WBStore *s) {
  char path[4096];
  struct stat st;
  if (snprintf(path, sizeof(path), "%s.drafts.json", s->state) >= (int)sizeof(path))
    return NULL;
  if (lstat(path, &st)) {
    if (errno == ENOENT)
      return json_object_new_object();
    snprintf(s->error, sizeof(s->error), "Não foi possível consultar a recuperação.");
    return NULL;
  }
  if (!S_ISREG(st.st_mode) || st.st_uid != getuid()) {
    snprintf(s->error, sizeof(s->error), "Arquivo de recuperação inseguro; preservado.");
    return NULL;
  }
  return load_file(path, s->error, sizeof(s->error), 32 * 1024 * 1024);
}
json_object *wb_find(json_object *root, const char *id) {
  json_object *items = NULL;
  size_t i;
  if (!json_object_object_get_ex(root, "items", &items) ||
      !json_object_is_type(items, json_type_array))
    return NULL;
  for (i = 0; i < json_object_array_length(items); i++) {
    json_object *o = json_object_array_get_idx(items, i);
    if (!strcmp(wb_string(o, "id"), id))
      return o;
  }
  return NULL;
}
static json_object *user_default(void) {
  json_object *u = json_object_new_object();
  str(u, "verdict", "pending");
  str(u, "note", "");
  str(u, "level", "intermediate");
  json_object_object_add(u, "authorized", json_object_new_boolean(0));
  json_object_object_add(u, "revision", json_object_new_int(0));
  str(u, "responded_at", "");
  return u;
}
static json_object *assistant_default(void) {
  json_object *a = json_object_new_object();
  str(a, "reply", "");
  str(a, "status", "queued");
  str(a, "read_at", "");
  str(a, "replied_at", "");
  json_object_object_add(a, "ack_revision", json_object_new_int(0));
  return a;
}
static json_object *field(json_object *o, const char *key) {
  json_object *v = NULL;
  json_object_object_get_ex(o, key, &v);
  return v;
}
static int valid(json_object *root) {
  json_object *items = field(root, "items");
  size_t i, j;
  if (wb_number(root, "schema_version") != 1 ||
      strcmp(wb_string(root, "kind"), "motif_work_board") ||
      !json_object_is_type(items, json_type_array) ||
      json_object_array_length(items) > 200)
    return 0;
  for (i = 0; i < json_object_array_length(items); i++) {
    json_object *o = json_object_array_get_idx(items, i), *u = field(o, "user"),
                *a = field(o, "assistant");
    const char *id = wb_string(o, "id"), *kind = wb_string(o, "type");
    if (!*id || strlen(id) > 63 || strlen(wb_string(o, "title")) > 1024 ||
        (!strcmp(kind, "task") && !u) ||
        (strcmp(kind, "task") && strcmp(kind, "question") &&
         strcmp(kind, "instruction")))
      return 0;
    for (j = 0; j < i; j++)
      if (!strcmp(id, wb_string(json_object_array_get_idx(items, j), "id")))
        return 0;
    if (u) {
      const char *level = wb_string(u, "level"),
                 *verdict = wb_string(u, "verdict");
      if (!json_object_is_type(field(u, "authorized"), json_type_boolean) ||
          !json_object_is_type(field(u, "revision"), json_type_int) ||
          !json_object_is_type(field(u, "note"), json_type_string))
        return 0;
      if (!json_object_is_type(u, json_type_object) ||
          strlen(wb_string(u, "note")) > 64000 ||
          wb_number(u, "revision") < 0 ||
          (!strcmp(kind, "question") && wb_boolean(u, "authorized")))
        return 0;
      if (strcmp(level, "novice") && strcmp(level, "intermediate") &&
          strcmp(level, "expert"))
        return 0;
      if (strcmp(verdict, "pending") && strcmp(verdict, "approve") &&
          strcmp(verdict, "refuse") && strcmp(verdict, "doubt"))
        return 0;
    }
    if (a && (!json_object_is_type(a, json_type_object) ||
              wb_number(a, "ack_revision") > wb_number(u, "revision")))
      return 0;
  }
  return 1;
}
json_object *wb_load(WBStore *s) {
  json_object *root = wb_load_file(s->state, s->error, sizeof(s->error));
  if (root && !valid(root)) {
    json_object_put(root);
    fail(s, "Formato da prancheta inválido. Nenhuma resposta foi substituída.");
    return NULL;
  }
  return root;
}
static int lock_store(WBStore *s) {
  char path[4096];
  int fd;
  struct stat st;
  if (snprintf(path, sizeof(path), "%s.lock", s->state) >= (int)sizeof(path))
    return fail(s, "Caminho muito longo.");
  fd = open(path, O_RDWR | O_CREAT | O_NOFOLLOW, 0600);
  if (fd < 0 || fstat(fd, &st) || !S_ISREG(st.st_mode) ||
      st.st_uid != getuid()) {
    if (fd >= 0)
      close(fd);
    return fail(s, "Não foi possível bloquear o arquivo privado.");
  }
  if (flock(fd, LOCK_EX | LOCK_NB)) {
    close(fd);
    return fail(s,
                "Arquivo em uso; tente salvar novamente. Rascunho preservado.");
  }
  return fd;
}
static int write_all(int fd, const char *data, size_t n) {
  size_t done = 0;
  while (done < n) {
    ssize_t c = write(fd, data + done, n - done);
    if (c < 0 && errno == EINTR)
      continue;
    if (c <= 0)
      return -1;
    done += (size_t)c;
  }
  return 0;
}
int wb_save_drafts(WBStore *s, json_object *drafts) {
  char path[4096], temp[4096];
  const char *data = json_object_to_json_string_ext(drafts, JSON_C_TO_STRING_PLAIN);
  struct stat st;
  int fd;
  size_t n = strlen(data);
  if (n > 32 * 1024 * 1024)
    return fail(s, "Recuperação excede 32 MiB; rascunho continua na memória.");
  if (snprintf(path, sizeof(path), "%s.drafts.json", s->state) >= (int)sizeof(path) ||
      snprintf(temp, sizeof(temp), "%s.drafts.new.XXXXXX", s->state) >= (int)sizeof(temp))
    return fail(s, "Caminho da recuperação muito longo.");
  if (lstat(path, &st) == 0 && (!S_ISREG(st.st_mode) || st.st_uid != getuid()))
    return fail(s, "Arquivo de recuperação inseguro; rascunho continua na memória.");
  fd = mkstemp(temp);
  if (fd < 0)
    return fail(s, "Não foi possível salvar recuperação; rascunho continua na memória.");
  if (write_all(fd, data, n) || fsync(fd)) {
    close(fd);
    unlink(temp);
    return fail(s, "Falha ao gravar recuperação; rascunho continua na memória.");
  }
  if (close(fd) || rename(temp, path)) {
    unlink(temp);
    return fail(s, "Falha na troca da recuperação; rascunho continua na memória.");
  }
  char *slash = strrchr(path, '/');
  if (slash) {
    *slash = 0;
    fd = open(*path ? path : "/", O_RDONLY | O_DIRECTORY);
    if (fd < 0 || fsync(fd)) {
      if (fd >= 0) close(fd);
      return fail(s, "Recuperação gravada, mas sincronização do diretório falhou.");
    }
    close(fd);
  }
  return 0;
}
static int persist(WBStore *s, json_object *root) {
  char temp[4096], history[4096], date[64];
  struct stat st;
  int fd, old, ok = 0;
  const char *data;
  size_t n;
  char *slash;
  timestamp(date, sizeof(date));
  str(root, "saved_at", date);
  if (!valid(root))
    return fail(s, "Operação recusada: dados inconsistentes.");
  if (lstat(s->state, &st) == 0 &&
      (!S_ISREG(st.st_mode) || st.st_uid != getuid()))
    return fail(s, "Estado deve ser arquivo regular pertencente ao usuário.");
  data = json_object_to_json_string_ext(root, JSON_C_TO_STRING_PRETTY);
  n = strlen(data);
  if (n > WB_LIMIT)
    return fail(s, "Prancheta excede 2 MiB.");
  if (snprintf(temp, sizeof(temp), "%s.new.XXXXXX", s->state) >=
      (int)sizeof(temp))
    return fail(s, "Caminho muito longo.");
  fd = mkstemp(temp);
  if (fd < 0)
    return fail(s, "Falha ao criar arquivo temporário.");
  if (write_all(fd, data, n) || write_all(fd, "\n", 1) || fsync(fd)) {
    close(fd);
    unlink(temp);
    return fail(s, "Falha ao gravar; estado anterior preservado.");
  }
  close(fd);
  old = open(s->state, O_RDONLY | O_NOFOLLOW | O_NONBLOCK);
  if (old >= 0) {
    snprintf(history, sizeof(history), "%s.history.XXXXXX", s->state);
    fd = mkstemp(history);
    if (fd >= 0) {
      char buf[8192];
      ssize_t c;
      ok = 1;
      while ((c = read(old, buf, sizeof(buf))) > 0)
        if (write_all(fd, buf, (size_t)c)) {
          ok = 0;
          break;
        }
      if (c < 0 || fsync(fd))
        ok = 0;
      close(fd);
      if (!ok)
        unlink(history);
    }
    close(old);
    if (fd < 0 || !ok) {
      unlink(temp);
      return fail(s, "Histórico não pôde ser preservado; gravação cancelada.");
    }
  }
  if (rename(temp, s->state)) {
    unlink(temp);
    return fail(s, "Falha na troca atômica do JSON.");
  }
  snprintf(temp, sizeof(temp), "%s", s->state);
  slash = strrchr(temp, '/');
  if (slash) {
    *slash = 0;
    fd = open(*temp ? temp : "/", O_RDONLY | O_DIRECTORY);
    if (fd >= 0) {
      fsync(fd);
      close(fd);
    }
  }
  return 0;
}
static void hash_definition(json_object *o, char out[65]) {
  unsigned char digest[SHA256_DIGEST_LENGTH];
  json_object *def = json_object_new_object();
  const char *keys[] = {"type", "title", "group", "scope", "criteria"};
  size_t i;
  for (i = 0; i < sizeof(keys) / sizeof(*keys); i++) {
    json_object *v = field(o, keys[i]);
    if (v)
      json_object_object_add(def, keys[i], wb_clone(v));
  }
  SHA256((const unsigned char *)json_object_to_json_string_ext(
             def, JSON_C_TO_STRING_PLAIN),
         strlen(json_object_to_json_string_ext(def, JSON_C_TO_STRING_PLAIN)),
         digest);
  for (i = 0; i < sizeof(digest); i++)
    sprintf(out + i * 2, "%02x", digest[i]);
  out[64] = 0;
  json_object_put(def);
}
int wb_sync(WBStore *s) {
  int lock = lock_store(s), result = -1, changed = 0;
  json_object *seed = NULL, *root = NULL, *items, *src;
  size_t i;
  if (lock < 0)
    return -1;
  seed = wb_load_file(s->seed, s->error, sizeof(s->error));
  if (!seed || !valid(seed)) {
    fail(s, "Dataset inválido; estado anterior preservado.");
    goto done;
  }
  if (access(s->state, F_OK) == 0) {
    root = wb_load(s);
    if (!root)
      goto done;
  } else {
    root = json_object_new_object();
    json_object_object_add(root, "schema_version", json_object_new_int(1));
    str(root, "kind", "motif_work_board");
    json_object_object_add(root, "items", json_object_new_array());
    changed = 1;
  }
  items = field(root, "items");
  src = field(seed, "items");
  for (i = 0; i < json_object_array_length(src); i++) {
    json_object *def = json_object_array_get_idx(src, i),
                *existing = wb_find(root, wb_string(def, "id"));
    char hash[65];
    hash_definition(def, hash);
    if (!existing) {
      existing = wb_clone(def);
      json_object_object_add(existing, "user", user_default());
      json_object_object_add(existing, "assistant", assistant_default());
      str(existing, "definition_sha256", hash);
    }
    if (!wb_find(root, wb_string(def, "id"))) {
      json_object_array_add(items, existing);
      changed = 1;
    } else {
      int definition_changed =
          strcmp(hash, wb_string(existing, "definition_sha256"));
      json_object_object_foreach(def, key, value) {
        if (strcmp(key, "user") && strcmp(key, "assistant") &&
            strcmp(key, "definition_sha256")) {
          json_object *prior = field(existing, key);
          if (!prior || !json_object_equal(prior, value)) {
            json_object_object_add(existing, key, wb_clone(value));
            changed = 1;
          }
        }
      }
      if (definition_changed) {
        json_object *u = field(existing, "user");
        char date[64];
        timestamp(date, sizeof(date));
        json_object_object_add(u, "authorized", json_object_new_boolean(0));
        str(u, "authorized_definition", "");
        json_object_object_add(
            u, "revision", json_object_new_int(wb_number(u, "revision") + 1));
        str(existing, "definition_sha256", hash);
        str(existing, "scope_changed_at", date);
        changed = 1;
      }
    }
  }
  result = changed ? persist(s, root) : 0;
done:
  json_object_put(root);
  json_object_put(seed);
  close(lock);
  return result;
}
int wb_save_user(WBStore *s, const char *id, int expected, json_object *input) {
  int lock = lock_store(s), result = -1;
  json_object *root = NULL, *o, *u, *next;
  const char *keys[] = {"verdict", "note", "level", "authorized"};
  size_t i;
  char date[64];
  int changed = 0;
  if (lock < 0)
    return -1;
  root = wb_load(s);
  if (!root)
    goto done;
  o = wb_find(root, id);
  if (!o) {
    fail(s, "Item não encontrado.");
    goto done;
  }
  u = field(o, "user");
  if (wb_number(u, "revision") != expected) {
    fail(s, "Resposta mudou no arquivo. Rascunho preservado: recarregue e "
            "compare antes de salvar.");
    goto done;
  }
  next = wb_clone(u);
  for (i = 0; i < 4; i++) {
    json_object *v = field(input, keys[i]);
    if (!v) {
      json_object_put(next);
      fail(s, "Resposta incompleta.");
      goto done;
    }
    if (!json_object_equal(field(u, keys[i]), v)) {
      changed = 1;
      json_object_object_add(next, keys[i], wb_clone(v));
    }
  }
  if (!strcmp(wb_string(o, "type"), "question") &&
      wb_boolean(next, "authorized")) {
    json_object_put(next);
    fail(s, "Perguntas não autorizam execução.");
    goto done;
  }
  if (!changed) {
    json_object_put(next);
    result = 0;
    goto done;
  }
  timestamp(date, sizeof(date));
  str(next, "responded_at", date);
  json_object_object_add(next, "revision", json_object_new_int(expected + 1));
  str(next, "authorized_definition",
      wb_boolean(next, "authorized") ? wb_string(o, "definition_sha256") : "");
  json_object_object_add(o, "user", next);
  result = persist(s, root);
done:
  json_object_put(root);
  close(lock);
  return result;
}
int wb_assistant(WBStore *s, const char *id, int expected, const char *reply,
                 const char *status) {
  int lock = lock_store(s), result = -1;
  json_object *root = NULL, *o, *u, *a;
  char date[64];
  if (lock < 0)
    return -1;
  root = wb_load(s);
  if (!root)
    goto done;
  o = wb_find(root, id);
  if (!o) {
    fail(s, "Item não encontrado.");
    goto done;
  }
  u = field(o, "user");
  a = field(o, "assistant");
  if (wb_number(u, "revision") != expected) {
    fail(s, "Nova resposta chegou; leitura antiga não pode desmarcá-la.");
    goto done;
  }
  if (status && (!strcmp(status, "running") || !strcmp(status, "done")) &&
      (!wb_boolean(u, "authorized") ||
       strcmp(wb_string(u, "authorized_definition"),
              wb_string(o, "definition_sha256")))) {
    fail(s, "Execução sem autorização válida para este escopo foi recusada.");
    goto done;
  }
  timestamp(date, sizeof(date));
  json_object_object_add(a, "ack_revision", json_object_new_int(expected));
  str(a, "read_at", date);
  if (reply) {
    str(a, "reply", reply);
    str(a, "replied_at", date);
  }
  if (status)
    str(a, "status", status);
  result = persist(s, root);
done:
  json_object_put(root);
  close(lock);
  return result;
}
int wb_insert(WBStore *s, const char *after, const char *kind,
              const char *title, char *id, size_t cap) {
  int lock = lock_store(s), result = -1;
  json_object *root = NULL, *o, *items, *anchor;
  size_t count;
  char hash[65], date[64];
  if (lock < 0)
    return -1;
  root = wb_load(s);
  if (!root)
    goto done;
  anchor = wb_find(root, after);
  if (!anchor || (strcmp(kind, "instruction") && strcmp(kind, "question")) ||
      !*title) {
    fail(s, "Escolha um intervalo e escreva a proposta/pergunta.");
    goto done;
  }
  items = field(root, "items");
  count = json_object_array_length(items);
  if (count >= 200) {
    fail(s, "Limite de 200 itens atingido.");
    goto done;
  }
  snprintf(id, cap, "%c%03zu", !strcmp(kind, "question") ? 'Q' : 'I',
           count + 1);
  while (wb_find(root, id))
    snprintf(id, cap, "%c%03zu", !strcmp(kind, "question") ? 'Q' : 'I',
             ++count + 1);
  o = json_object_new_object();
  str(o, "id", id);
  str(o, "type", kind);
  str(o, "title", title);
  str(o, "group", !strcmp(kind, "question") ? "Perguntas" : "Instruções");
  str(o, "after", after);
  str(o, "scope", title);
  str(o, "technical_status", "Proposta nova; não executada.");
  timestamp(date, sizeof(date));
  str(o, "created_at", date);
  hash_definition(o, hash);
  str(o, "definition_sha256", hash);
  json_object_object_add(o, "user", user_default());
  json_object_object_add(o, "assistant", assistant_default());
  json_object_array_add(items, o);
  result = persist(s, root);
done:
  json_object_put(root);
  close(lock);
  return result;
}
