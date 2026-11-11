/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#define _XOPEN_SOURCE 700
#include "gtk2_r584_catalog.h"
#include <errno.h>
#include <fcntl.h>
#include <json-c/json.h>
#include <openssl/evp.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

enum { JSON_LIMIT = 2 * 1024 * 1024, ASSET_LIMIT = 8 * 1024 * 1024 };

const TLGtk2R584Identity tl_gtk2_r584_canonical_identity = {
    "0f11d4aa6cb38c97f93f8035ac4ef7cab3101c944ae9d5925bd5bc5ac3de2c6b",
    "565e5c9095e5ae86df516b819c55a502dcc74af8b5412e42af9e6c4a49d4b0ee",
    "fe95ddd38ef6f61a941d420f6d3d33f376b4d34032c3fc2cf9cad77834710755",
    "ef34a032ddb76017ff15e92524d1964eb28b0cf71414312030456b3348c79b70"};

typedef struct {
  char name[160];
  char sha256[TL_GTK2_R584_SHA256_LENGTH + 1];
  unsigned int control_mask;
  TLGtk2R584Part part;
  TLGtk2R584State state;
  TLGtk2R584Direction direction;
  TLGtk2R584Variant variant;
  int mapped;
} CatalogAsset;

struct TLGtk2R584Catalog {
  char bundle_id[TL_GTK2_R584_SHA256_LENGTH + 1];
  char bundle_root[TL_PATH_MAX];
  char receipt_sha256[TL_GTK2_R584_SHA256_LENGTH + 1];
  char manifest_sha256[TL_GTK2_R584_SHA256_LENGTH + 1];
  CatalogAsset *assets;
  size_t asset_count;
};

static int fail(char *error, size_t capacity, const char *format, ...) {
  va_list args;
  if (error && capacity) {
    va_start(args, format);
    vsnprintf(error, capacity, format, args);
    va_end(args);
  }
  return -1;
}

static void clear_error(char *error, size_t capacity) {
  if (error && capacity)
    error[0] = '\0';
}

static int sha256_valid(const char *text) {
  size_t i;
  if (!text || strlen(text) != TL_GTK2_R584_SHA256_LENGTH)
    return 0;
  for (i = 0; i < TL_GTK2_R584_SHA256_LENGTH; ++i)
    if (!((text[i] >= '0' && text[i] <= '9') ||
          (text[i] >= 'a' && text[i] <= 'f')))
      return 0;
  return 1;
}

static void digest_hex(const unsigned char digest[32], char output[65]) {
  static const char hex[] = "0123456789abcdef";
  size_t i;
  for (i = 0; i < 32; ++i) {
    output[i * 2] = hex[digest[i] >> 4];
    output[i * 2 + 1] = hex[digest[i] & 15];
  }
  output[64] = '\0';
}

static int digest_fd(int fd, size_t limit, char output[65], char **contents,
                     size_t *contents_size, char *error, size_t capacity) {
  EVP_MD_CTX *context = NULL;
  unsigned char digest[EVP_MAX_MD_SIZE], buffer[8192];
  unsigned int digest_size = 0;
  struct stat info;
  char *data = NULL;
  size_t used = 0;
  ssize_t got;
  if (fstat(fd, &info) || !S_ISREG(info.st_mode) || info.st_size < 0 ||
      (uintmax_t)info.st_size > limit)
    return fail(error, capacity, "Arquivo R584 não é regular ou excede o limite.");
  if (contents) {
    data = malloc((size_t)info.st_size + 1);
    if (!data)
      return fail(error, capacity, "Memória insuficiente para ler evidência R584.");
  }
  context = EVP_MD_CTX_new();
  if (!context || EVP_DigestInit_ex(context, EVP_sha256(), NULL) != 1)
    goto crypto_error;
  while ((got = read(fd, buffer, sizeof(buffer))) > 0) {
    if (EVP_DigestUpdate(context, buffer, (size_t)got) != 1)
      goto crypto_error;
    if (data) {
      if (used > (size_t)info.st_size ||
          (size_t)got > (size_t)info.st_size - used)
        goto crypto_error;
      memcpy(data + used, buffer, (size_t)got);
      used += (size_t)got;
    }
  }
  if (got < 0 || EVP_DigestFinal_ex(context, digest, &digest_size) != 1 ||
      digest_size != 32)
    goto crypto_error;
  EVP_MD_CTX_free(context);
  digest_hex(digest, output);
  if (data) {
    data[used] = '\0';
    *contents = data;
    if (contents_size)
      *contents_size = used;
  }
  return 0;
crypto_error:
  EVP_MD_CTX_free(context);
  free(data);
  return fail(error, capacity, "Falha ao calcular SHA-256 de evidência R584.");
}

static int read_path(const char *path, size_t limit, const char *expected,
                     char **contents, size_t *contents_size, char actual[65],
                     char *error, size_t capacity) {
  int fd, status;
  if (!path || !*path || !expected || !sha256_valid(expected))
    return fail(error, capacity, "Identidade SHA-256 R584 inválida.");
  fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK);
  if (fd < 0)
    return fail(error, capacity, "Não foi possível abrir evidência R584: %s.",
                strerror(errno));
  status = digest_fd(fd, limit, actual, contents, contents_size, error, capacity);
  close(fd);
  if (status)
    return status;
  if (strcmp(actual, expected)) {
    free(contents ? *contents : NULL);
    if (contents)
      *contents = NULL;
    return fail(error, capacity, "SHA-256 da evidência R584 não confere.");
  }
  return 0;
}

static json_object *parse_json(const char *text, size_t length, char *error,
                               size_t capacity) {
  json_tokener *tokener;
  json_object *object;
  enum json_tokener_error code;
  size_t parsed;
  tokener = json_tokener_new();
  if (!tokener) {
    fail(error, capacity, "Memória insuficiente para JSON R584.");
    return NULL;
  }
  object = json_tokener_parse_ex(tokener, text, (int)length);
  code = json_tokener_get_error(tokener);
  parsed = json_tokener_get_parse_end(tokener);
  while (parsed < length && (text[parsed] == ' ' || text[parsed] == '\t' ||
                             text[parsed] == '\r' || text[parsed] == '\n'))
    ++parsed;
  if (code != json_tokener_success || !object || parsed != length ||
      !json_object_is_type(object, json_type_object)) {
    if (object)
      json_object_put(object);
    object = NULL;
    fail(error, capacity, "JSON R584 inválido ou com conteúdo residual.");
  }
  json_tokener_free(tokener);
  return object;
}

static json_object *member(json_object *object, const char *name,
                           enum json_type type) {
  json_object *value = NULL;
  return object && json_object_object_get_ex(object, name, &value) && value &&
                 json_object_is_type(value, type)
             ? value
             : NULL;
}

static int text_is(json_object *object, const char *name, const char *expected) {
  json_object *value = member(object, name, json_type_string);
  return value && !strcmp(json_object_get_string(value), expected);
}

static int int_is(json_object *object, const char *name, int expected) {
  json_object *value = member(object, name, json_type_int);
  return value && json_object_get_int(value) == expected;
}

static int bool_is(json_object *object, const char *name, int expected) {
  json_object *value = member(object, name, json_type_boolean);
  return value && json_object_get_boolean(value) == expected;
}

static const char *path_basename(const char *path) {
  const char *slash = path ? strrchr(path, '/') : NULL;
  return slash ? slash + 1 : path;
}

static int asset_name_safe(const char *name) {
  size_t i, length;
  if (!name || !(length = strlen(name)) || length >= 160 || name[0] == '.')
    return 0;
  for (i = 0; i < length; ++i)
    if (!((name[i] >= 'a' && name[i] <= 'z') ||
          (name[i] >= '0' && name[i] <= '9') || name[i] == '-' ||
          name[i] == '_' || name[i] == '.'))
      return 0;
  return !strstr(name, "..") && length > 4 && !strcmp(name + length - 4, ".png");
}

static int control_index(const char *id) {
  int i;
  for (i = 0; i < TL_CONTROL_COUNT; ++i)
    if (!strcmp(tl_control_ids[i], id))
      return i;
  return -1;
}

static unsigned int control_bit(const char *id) {
  int index = control_index(id);
  return index >= 0 ? 1u << (unsigned int)index : 0u;
}

static const char *const state_names[] = {"normal", "focused", "pressed",
                                          "disabled", "toggled"};
static const char *const direction_names[] = {
    "", "up", "down", "left", "right", "horizontal", "vertical"};
static const char *const variant_names[] = {"", "off", "on", "mixed"};

static int name_equals(char *buffer, size_t size, const char *format,
                       const char *a, const char *b, const char *c) {
  int length = snprintf(buffer, size, format, a, b, c);
  return length > 0 && (size_t)length < size;
}

static void map_asset(CatalogAsset *asset) {
  char expected[160];
  int state, direction, variant;
  asset->mapped = 0;
  asset->direction = TL_GTK2_R584_DIRECTION_NONE;
  asset->variant = TL_GTK2_R584_VARIANT_NONE;
  for (state = 0; state < 5; ++state) {
    if (name_equals(expected, sizeof(expected), "command-%s.png",
                    state_names[state], "", "") &&
        !strcmp(asset->name, expected)) {
      asset->control_mask = control_bit("push");
      asset->part = TL_GTK2_R584_PART_WHOLE;
      asset->state = (TLGtk2R584State)state;
      asset->mapped = asset->control_mask != 0;
      return;
    }
    if (name_equals(expected, sizeof(expected), "input-%s.png",
                    state_names[state], "", "") &&
        !strcmp(asset->name, expected)) {
      asset->control_mask = control_bit("entry");
      asset->part = TL_GTK2_R584_PART_WHOLE;
      asset->state = (TLGtk2R584State)state;
      asset->mapped = asset->control_mask != 0;
      return;
    }
    for (variant = TL_GTK2_R584_VARIANT_OFF;
         variant <= TL_GTK2_R584_VARIANT_MIXED; ++variant) {
      if (name_equals(expected, sizeof(expected), "check-%s-%s.png",
                      variant_names[variant], state_names[state], "") &&
          !strcmp(asset->name, expected)) {
        asset->control_mask = control_bit("check");
        asset->part = TL_GTK2_R584_PART_WHOLE;
        asset->state = (TLGtk2R584State)state;
        asset->variant = (TLGtk2R584Variant)variant;
        asset->mapped = asset->control_mask != 0;
        return;
      }
      if (variant != TL_GTK2_R584_VARIANT_MIXED &&
          name_equals(expected, sizeof(expected), "radio-%s-%s.png",
                      variant_names[variant], state_names[state], "") &&
          !strcmp(asset->name, expected)) {
        asset->control_mask = control_bit("radio");
        asset->part = TL_GTK2_R584_PART_WHOLE;
        asset->state = (TLGtk2R584State)state;
        asset->variant = (TLGtk2R584Variant)variant;
        asset->mapped = asset->control_mask != 0;
        return;
      }
    }
    if (name_equals(expected, sizeof(expected), "scroll-thumb-%s.png",
                    state_names[state], "", "") &&
        !strcmp(asset->name, expected)) {
      asset->control_mask = control_bit("scroll_h") | control_bit("scroll_v");
      asset->part = TL_GTK2_R584_PART_THUMB;
      asset->state = (TLGtk2R584State)state;
      asset->mapped = asset->control_mask != 0;
      return;
    }
    for (direction = TL_GTK2_R584_DIRECTION_UP;
         direction <= TL_GTK2_R584_DIRECTION_RIGHT; ++direction) {
      unsigned int scrollbar = direction == TL_GTK2_R584_DIRECTION_LEFT ||
                                       direction == TL_GTK2_R584_DIRECTION_RIGHT
                                   ? control_bit("scroll_h")
                                   : control_bit("scroll_v");
      if (name_equals(expected, sizeof(expected),
                      "scrollbar-arrow-%s-%s.png", direction_names[direction],
                      state_names[state], "") &&
          !strcmp(asset->name, expected)) {
        asset->control_mask = scrollbar;
        asset->part = TL_GTK2_R584_PART_ARROW;
        asset->state = (TLGtk2R584State)state;
        asset->direction = (TLGtk2R584Direction)direction;
        asset->mapped = scrollbar != 0;
        return;
      }
      if (name_equals(expected, sizeof(expected),
                      "scrollbar-stepper-%s-%s.png",
                      direction_names[direction], state_names[state], "") &&
          !strcmp(asset->name, expected)) {
        asset->control_mask = scrollbar;
        asset->part = TL_GTK2_R584_PART_ARROW_BUTTON;
        asset->state = (TLGtk2R584State)state;
        asset->direction = (TLGtk2R584Direction)direction;
        asset->mapped = scrollbar != 0;
        return;
      }
    }
    for (direction = TL_GTK2_R584_DIRECTION_HORIZONTAL;
         direction <= TL_GTK2_R584_DIRECTION_VERTICAL; ++direction) {
      unsigned int scrollbar = direction == TL_GTK2_R584_DIRECTION_HORIZONTAL
                                   ? control_bit("scroll_h")
                                   : control_bit("scroll_v");
      if (name_equals(expected, sizeof(expected),
                      "scroll-trough-%s-%s.png", state_names[state],
                      direction_names[direction], "") &&
          !strcmp(asset->name, expected)) {
        asset->control_mask = scrollbar;
        asset->part = TL_GTK2_R584_PART_TROUGH;
        asset->state = (TLGtk2R584State)state;
        asset->direction = (TLGtk2R584Direction)direction;
        asset->mapped = scrollbar != 0;
        return;
      }
    }
  }
}

static int validate_receipt(json_object *receipt,
                            const TLGtk2R584Identity *identity,
                            int *asset_entries, char *error, size_t capacity) {
  json_object *authority, *p10, *i167, *transaction, *classes, *value;
  int total = 0;
  if (!int_is(receipt, "schema_version", 1) || !text_is(receipt, "id", "R584") ||
      !text_is(receipt, "item", "I167") ||
      !text_is(receipt, "related_parent", "P10"))
    return fail(error, capacity, "Recibo não identifica a revisão canônica R584/I167.");
  authority = member(receipt, "authority", json_type_object);
  p10 = member(authority, "P10", json_type_object);
  i167 = member(authority, "I167", json_type_object);
  if (!bool_is(p10, "authorized", 1) || !bool_is(i167, "authorized", 1) ||
      !text_is(p10, "definition_sha256",
               "939e9ae8d36a4d38b0c11654d263523b8460190c84ed70ef9a9f7c86b4eb91d4") ||
      !text_is(i167, "definition_sha256",
               "5e128e4eca5cabd7a949ab11b3b480ce1c433d1446615e10ec8313bf273885ea"))
    return fail(error, capacity, "Autoridade ou definição do recibo R584 não confere.");
  transaction = member(receipt, "transaction", json_type_object);
  classes = member(transaction, "entry_classes", json_type_object);
  if (!text_is(transaction, "status", "installed") || !classes ||
      !text_is(transaction, "palette_source_colors_sha256",
               identity->palette_source_sha256))
    return fail(error, capacity, "Transação ou paleta de origem R584 não confere.");
  value = member(transaction, "generated_bundle", json_type_string);
  if (!value || strcmp(path_basename(json_object_get_string(value)),
                       identity->bundle_id))
    return fail(error, capacity, "Recibo R584 aponta para outro bundle.");
  value = member(classes, "immutable GTK2 palette assets", json_type_int);
  if (!value || json_object_get_int(value) < 0)
    return fail(error, capacity, "Contagem de assets R584 ausente.");
  *asset_entries = json_object_get_int(value);
  json_object_object_foreach(classes, key, entry) {
    (void)key;
    if (!json_object_is_type(entry, json_type_int) ||
        json_object_get_int(entry) < 0)
      return fail(error, capacity, "Classe de entradas R584 inválida.");
    total += json_object_get_int(entry);
  }
  if (!int_is(transaction, "entries", total) ||
      !int_is(transaction, "changed_entries", total))
    return fail(error, capacity, "Totais da transação R584 não conferem.");
  return 0;
}

static int validate_hash_object(json_object *object, int require_png,
                                char *error, size_t capacity) {
  if (!object || !json_object_is_type(object, json_type_object))
    return fail(error, capacity, "Tabela de hashes R584 ausente.");
  json_object_object_foreach(object, name, value) {
    const char *hash;
    if ((require_png && !asset_name_safe(name)) ||
        !json_object_is_type(value, json_type_string) ||
        !sha256_valid(hash = json_object_get_string(value)))
      return fail(error, capacity, "Nome ou SHA-256 de asset R584 inválido.");
  }
  return 0;
}

static int validate_file_at(int directory, const char *name,
                            const char *expected, char *error,
                            size_t capacity) {
  int fd, status;
  char actual[65];
  fd = openat(directory, name, O_RDONLY | O_CLOEXEC | O_NOFOLLOW | O_NONBLOCK);
  if (fd < 0)
    return fail(error, capacity, "Asset R584 declarado não pôde ser aberto: %s.",
                name);
  status = digest_fd(fd, ASSET_LIMIT, actual, NULL, NULL, error, capacity);
  close(fd);
  if (!status && strcmp(actual, expected))
    return fail(error, capacity, "SHA-256 do asset R584 não confere: %s.", name);
  return status;
}

static int validate_manifest(TLGtk2R584Catalog *catalog, json_object *manifest,
                             const TLGtk2R584Identity *identity,
                             int receipt_assets, char *error,
                             size_t capacity) {
  json_object *generated, *rendered, *source, *value;
  int bundle_fd = -1, assets_fd = -1, asset_count, status = -1;
  size_t index = 0;
  if (!int_is(manifest, "format", 1) ||
      !text_is(manifest, "theme", "DomainOS-SR10-4") ||
      !text_is(manifest, "id", identity->bundle_id))
    return fail(error, capacity, "Manifesto não identifica o bundle GTK2 R584.");
  generated = member(manifest, "generated", json_type_object);
  rendered = member(manifest, "rendered_assets", json_type_object);
  source = member(manifest, "source_assets", json_type_object);
  value = member(manifest, "asset_count", json_type_int);
  if (!generated || !rendered || !source || !value ||
      (asset_count = json_object_get_int(value)) < 0 ||
      asset_count != receipt_assets ||
      asset_count != json_object_object_length(rendered) ||
      json_object_object_length(generated) != asset_count + 1 ||
      validate_hash_object(rendered, 1, error, capacity) ||
      validate_hash_object(source, 1, error, capacity))
    return fail(error, capacity, "Cobertura declarada pelo manifesto R584 não confere.");
  value = NULL;
  if (!json_object_object_get_ex(generated, "gtkrc", &value) || !value ||
      !json_object_is_type(value, json_type_string) ||
      !text_is(manifest, "rendered_rc_sha256", json_object_get_string(value)) ||
      !sha256_valid(json_object_get_string(value)))
    return fail(error, capacity, "Hash do gtkrc R584 não confere no manifesto.");
  {
    json_object_object_foreach(rendered, name, hash_value) {
      char generated_name[192];
      json_object *generated_value = NULL;
      if (snprintf(generated_name, sizeof(generated_name), "assets/%s", name) >=
              (int)sizeof(generated_name) ||
          !json_object_object_get_ex(generated, generated_name,
                                     &generated_value) ||
          !generated_value ||
          !json_object_is_type(generated_value, json_type_string) ||
          strcmp(json_object_get_string(hash_value),
                 json_object_get_string(generated_value)))
        return fail(error, capacity,
                    "Asset renderizado R584 sem hash gerado correspondente.");
    }
  }
  {
    json_object_object_foreach(generated, generated_name, generated_hash) {
      json_object *rendered_value = NULL;
      if (!strcmp(generated_name, "gtkrc"))
        continue;
      if (strncmp(generated_name, "assets/", 7) ||
          !asset_name_safe(generated_name + 7) ||
          !json_object_object_get_ex(rendered, generated_name + 7,
                                     &rendered_value) ||
          !rendered_value || strcmp(json_object_get_string(generated_hash),
                                    json_object_get_string(rendered_value)))
        return fail(error, capacity,
                    "Caminho gerado R584 não é seguro ou não é declarado.");
    }
  }
  bundle_fd = open(catalog->bundle_root,
                   O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
  if (bundle_fd < 0)
    return fail(error, capacity, "Diretório do bundle R584 não pôde ser aberto.");
  assets_fd = openat(bundle_fd, "assets",
                     O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
  if (assets_fd < 0) {
    fail(error, capacity, "Diretório de assets R584 não pôde ser aberto.");
    goto done;
  }
  value = NULL;
  json_object_object_get_ex(generated, "gtkrc", &value);
  if (validate_file_at(bundle_fd, "gtkrc", json_object_get_string(value), error,
                       capacity))
    goto done;
  catalog->assets = calloc((size_t)asset_count, sizeof(*catalog->assets));
  if (asset_count && !catalog->assets) {
    fail(error, capacity, "Memória insuficiente para catálogo R584.");
    goto done;
  }
  {
    json_object_object_foreach(rendered, name, hash_value) {
      CatalogAsset *asset = &catalog->assets[index++];
      if (validate_file_at(assets_fd, name, json_object_get_string(hash_value),
                           error, capacity))
        goto done;
      snprintf(asset->name, sizeof(asset->name), "%s", name);
      snprintf(asset->sha256, sizeof(asset->sha256), "%s",
               json_object_get_string(hash_value));
      map_asset(asset);
    }
  }
  catalog->asset_count = (size_t)asset_count;
  status = 0;
done:
  if (assets_fd >= 0)
    close(assets_fd);
  if (bundle_fd >= 0)
    close(bundle_fd);
  return status;
}

int tl_gtk2_r584_catalog_load_verified(
    TLGtk2R584Catalog **result, const char *receipt_path,
    const char *manifest_path, const TLGtk2R584Identity *identity, char *error,
    size_t capacity) {
  TLGtk2R584Catalog *catalog = NULL;
  char *receipt_text = NULL, *manifest_text = NULL, resolved[TL_PATH_MAX];
  char receipt_sha[65], manifest_sha[65], parent[TL_PATH_MAX], *slash;
  size_t receipt_size = 0, manifest_size = 0;
  json_object *receipt = NULL, *manifest = NULL;
  int receipt_assets = 0, status = -1;
  clear_error(error, capacity);
  if (!result || *result || !receipt_path || !manifest_path || !identity ||
      !sha256_valid(identity->receipt_sha256) ||
      !sha256_valid(identity->manifest_sha256) ||
      !sha256_valid(identity->palette_source_sha256) || !identity->bundle_id ||
      !sha256_valid(identity->bundle_id))
    return fail(error, capacity, "Parâmetros do catálogo R584 são inválidos.");
  if (read_path(receipt_path, JSON_LIMIT, identity->receipt_sha256, &receipt_text,
                &receipt_size, receipt_sha, error, capacity) ||
      read_path(manifest_path, JSON_LIMIT, identity->manifest_sha256,
                &manifest_text, &manifest_size, manifest_sha, error, capacity))
    goto done;
  receipt = parse_json(receipt_text, receipt_size, error, capacity);
  manifest = parse_json(manifest_text, manifest_size, error, capacity);
  if (!receipt || !manifest ||
      validate_receipt(receipt, identity, &receipt_assets, error, capacity))
    goto done;
  if (!realpath(manifest_path, resolved) ||
      strcmp(path_basename(resolved), "manifest.json")) {
    fail(error, capacity, "Caminho do manifesto R584 não é canônico.");
    goto done;
  }
  snprintf(parent, sizeof(parent), "%s", resolved);
  slash = strrchr(parent, '/');
  if (!slash) {
    fail(error, capacity, "Diretório do manifesto R584 é inválido.");
    goto done;
  }
  *slash = '\0';
  if (strcmp(path_basename(parent), identity->bundle_id)) {
    fail(error, capacity, "Diretório do manifesto não corresponde ao bundle R584.");
    goto done;
  }
  catalog = calloc(1, sizeof(*catalog));
  if (!catalog) {
    fail(error, capacity, "Memória insuficiente para catálogo R584.");
    goto done;
  }
  snprintf(catalog->bundle_id, sizeof(catalog->bundle_id), "%s",
           identity->bundle_id);
  snprintf(catalog->bundle_root, sizeof(catalog->bundle_root), "%s", parent);
  snprintf(catalog->receipt_sha256, sizeof(catalog->receipt_sha256), "%s",
           receipt_sha);
  snprintf(catalog->manifest_sha256, sizeof(catalog->manifest_sha256), "%s",
           manifest_sha);
  if (validate_manifest(catalog, manifest, identity, receipt_assets, error,
                        capacity))
    goto done;
  *result = catalog;
  catalog = NULL;
  status = 0;
done:
  tl_gtk2_r584_catalog_free(catalog);
  if (receipt)
    json_object_put(receipt);
  if (manifest)
    json_object_put(manifest);
  free(receipt_text);
  free(manifest_text);
  return status;
}

int tl_gtk2_r584_catalog_load_canonical(TLGtk2R584Catalog **result,
                                        const char *receipt_path,
                                        const char *manifest_path, char *error,
                                        size_t capacity) {
  return tl_gtk2_r584_catalog_load_verified(
      result, receipt_path, manifest_path, &tl_gtk2_r584_canonical_identity,
      error, capacity);
}

void tl_gtk2_r584_catalog_free(TLGtk2R584Catalog *catalog) {
  if (!catalog)
    return;
  free(catalog->assets);
  free(catalog);
}

const char *tl_gtk2_r584_catalog_bundle_id(const TLGtk2R584Catalog *catalog) {
  return catalog ? catalog->bundle_id : NULL;
}

const char *tl_gtk2_r584_catalog_bundle_root(const TLGtk2R584Catalog *catalog) {
  return catalog ? catalog->bundle_root : NULL;
}

size_t tl_gtk2_r584_catalog_asset_count(const TLGtk2R584Catalog *catalog) {
  return catalog ? catalog->asset_count : 0;
}

int tl_gtk2_r584_catalog_lookup(const TLGtk2R584Catalog *catalog,
                                const TLGtk2R584Query *query,
                                TLGtk2R584Result *result, char *error,
                                size_t capacity) {
  size_t i;
  clear_error(error, capacity);
  if (!catalog || !query || !result || query->control < 0 ||
      query->control >= TL_CONTROL_COUNT || query->part < 0 ||
      query->part > TL_GTK2_R584_PART_THUMB || query->state < 0 ||
      query->state > TL_GTK2_R584_STATE_TOGGLED || query->direction < 0 ||
      query->direction > TL_GTK2_R584_DIRECTION_VERTICAL || query->variant < 0 ||
      query->variant > TL_GTK2_R584_VARIANT_MIXED)
    return fail(error, capacity, "Consulta ao catálogo R584 é inválida.");
  memset(result, 0, sizeof(*result));
  snprintf(result->reason, sizeof(result->reason),
           "R584 não declara asset para %s/peça=%d/estado=%d/direção=%d/variante=%d.",
           tl_control_ids[query->control], query->part, query->state,
           query->direction, query->variant);
  for (i = 0; i < catalog->asset_count; ++i) {
    const CatalogAsset *asset = &catalog->assets[i];
    if (asset->mapped &&
        (asset->control_mask & (1u << (unsigned int)query->control)) &&
        asset->part == query->part && asset->state == query->state &&
        asset->direction == query->direction && asset->variant == query->variant) {
      size_t root_length = strlen(catalog->bundle_root);
      size_t name_length = strlen(asset->name);
      if (root_length + sizeof("/assets/") - 1 + name_length + 1 >
          sizeof(result->path))
        return fail(error, capacity, "Caminho do asset R584 excede o limite.");
      result->available = 1;
      result->reason[0] = '\0';
      snprintf(result->asset_name, sizeof(result->asset_name), "%s", asset->name);
      memcpy(result->path, catalog->bundle_root, root_length);
      memcpy(result->path + root_length, "/assets/", sizeof("/assets/") - 1);
      memcpy(result->path + root_length + sizeof("/assets/") - 1, asset->name,
             name_length + 1);
      snprintf(result->sha256, sizeof(result->sha256), "%s", asset->sha256);
      return 0;
    }
  }
  return 0;
}
