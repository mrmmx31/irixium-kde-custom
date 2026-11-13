/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "manual_paint.h"
#include <errno.h>
#include <fcntl.h>
#include <json-c/json.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define TL_PAINT_FILE_MAX (32u * 1024u * 1024u)
#define TL_PAINT_HISTORY_BYTES (16u * 1024u * 1024u)
#define TL_PAINT_KIND "theme_lab_manual_paint"
#define TL_PAINT_SCHEMA_VERSION 2

static const char *const part_ids[TL_PAINT_PART_COUNT] = {
    "whole", "arrow", "arrow_button", "trough", "thumb", "fitting"};
static const char *const variant_ids[TL_PAINT_VARIANT_COUNT] = {
    "auto",  "start", "end",  "before", "after",
    "up",    "down",  "left", "right"};

typedef struct {
  int width, height;
  uint32_t *pixels;
} Snapshot;
typedef struct PaintDocument {
  int family, control, state, part, variant, width, height;
  uint32_t *pixels;
  Snapshot history[TL_PAINT_MAX_UNDO + 1];
  int count, position;
  struct PaintDocument *next;
} PaintDocument;
struct TLManualPaint {
  PaintDocument *documents, *current;
  uint32_t color;
};

static size_t pixel_count(int width, int height) {
  return (size_t)width * (size_t)height;
}
static int size_valid(int width, int height) {
  return width >= TL_PAINT_MIN_SIZE && height >= TL_PAINT_MIN_SIZE &&
         width <= TL_PAINT_MAX_WIDTH && height <= TL_PAINT_MAX_HEIGHT;
}
static int identity_valid(int family, int control, int state, int part,
                          int variant) {
  if (family < 0 || family >= 10 || control < 0 || control >= 16 || state < 0 ||
      state >= 5 || part < 0 || part >= TL_PAINT_PART_COUNT || variant < 0 ||
      variant >= TL_PAINT_VARIANT_COUNT)
    return 0;
  if (variant == TL_PAINT_VARIANT_AUTO)
    return 1;
  if (part == TL_PAINT_PART_ARROW || part == TL_PAINT_PART_ARROW_BUTTON)
    return variant == TL_PAINT_VARIANT_START ||
           variant == TL_PAINT_VARIANT_END || variant == TL_PAINT_VARIANT_UP ||
           variant == TL_PAINT_VARIANT_DOWN ||
           variant == TL_PAINT_VARIANT_LEFT ||
           variant == TL_PAINT_VARIANT_RIGHT;
  if (part == TL_PAINT_PART_TROUGH)
    return variant == TL_PAINT_VARIANT_BEFORE ||
           variant == TL_PAINT_VARIANT_AFTER;
  return 0;
}
static int id_from_text(const char *text, const char *const *ids, int count) {
  if (!text)
    return -1;
  for (int i = 0; i < count; ++i)
    if (!strcmp(text, ids[i]))
      return i;
  return -1;
}
static void snapshot_clear(Snapshot *s) {
  free(s->pixels);
  memset(s, 0, sizeof(*s));
}
static int snapshot_set(Snapshot *s, int width, int height,
                        const uint32_t *pixels) {
  size_t n;
  uint32_t *copy;
  if (!size_valid(width, height))
    return -1;
  n = pixel_count(width, height);
  copy = malloc(n * sizeof(*copy));
  if (!copy)
    return -1;
  memcpy(copy, pixels, n * sizeof(*copy));
  snapshot_clear(s);
  s->width = width;
  s->height = height;
  s->pixels = copy;
  return 0;
}
static void doc_history_clear(PaintDocument *d) {
  for (int i = 0; i <= TL_PAINT_MAX_UNDO; ++i)
    snapshot_clear(&d->history[i]);
  d->count = d->position = 0;
}
static void doc_free(PaintDocument *d) {
  if (!d)
    return;
  free(d->pixels);
  doc_history_clear(d);
  free(d);
}
static int history_push(PaintDocument *d) {
  Snapshot candidate = {0};
  size_t bytes = pixel_count(d->width, d->height) * sizeof(uint32_t);
  if (d->count && d->position >= 0 &&
      d->history[d->position].width == d->width &&
      d->history[d->position].height == d->height &&
      memcmp(d->history[d->position].pixels, d->pixels, bytes) == 0)
    return 0;
  if (snapshot_set(&candidate, d->width, d->height, d->pixels))
    return -1;
  for (int i = d->position + 1; i < d->count; ++i)
    snapshot_clear(&d->history[i]);
  d->count = d->position + 1;
  if (d->count > TL_PAINT_MAX_UNDO) {
    snapshot_clear(&d->history[0]);
    memmove(&d->history[0], &d->history[1],
            TL_PAINT_MAX_UNDO * sizeof(d->history[0]));
    memset(&d->history[TL_PAINT_MAX_UNDO], 0, sizeof(d->history[0]));
    --d->count;
    --d->position;
  }
  size_t history_bytes = bytes;
  for (int i = 0; i < d->count; ++i)
    history_bytes += pixel_count(d->history[i].width, d->history[i].height) *
                     sizeof(uint32_t);
  while (d->count > 1 && history_bytes > TL_PAINT_HISTORY_BYTES) {
    history_bytes -= pixel_count(d->history[0].width, d->history[0].height) *
                     sizeof(uint32_t);
    snapshot_clear(&d->history[0]);
    memmove(&d->history[0], &d->history[1],
            (size_t)(d->count - 1) * sizeof(d->history[0]));
    memset(&d->history[d->count - 1], 0, sizeof(d->history[0]));
    --d->count;
    --d->position;
  }
  d->history[d->count] = candidate;
  d->position = d->count++;
  return 0;
}
static PaintDocument *doc_new(int family, int control, int state, int part,
                              int variant, int width, int height) {
  PaintDocument *d = calloc(1, sizeof(*d));
  if (!d)
    return NULL;
  d->pixels = calloc(pixel_count(width, height), sizeof(*d->pixels));
  if (!d->pixels) {
    free(d);
    return NULL;
  }
  d->family = family;
  d->control = control;
  d->state = state;
  d->part = part;
  d->variant = variant;
  d->width = width;
  d->height = height;
  if (history_push(d)) {
    doc_free(d);
    return NULL;
  }
  return d;
}
TLManualPaint *tl_manual_paint_new(void) {
  TLManualPaint *paint = calloc(1, sizeof(*paint));
  if (paint)
    paint->color = 0xff000000u;
  return paint;
}
void tl_manual_paint_free(TLManualPaint *paint) {
  if (!paint)
    return;
  PaintDocument *d = paint->documents;
  while (d) {
    PaintDocument *next = d->next;
    doc_free(d);
    d = next;
  }
  free(paint);
}
int tl_manual_paint_select(TLManualPaint *paint, int family, int control,
                           int state) {
  return tl_manual_paint_select_piece(paint, family, control, state,
                                      TL_PAINT_PART_WHOLE,
                                      TL_PAINT_VARIANT_AUTO);
}
int tl_manual_paint_select_piece(TLManualPaint *paint, int family, int control,
                                 int state, TLManualPaintPart part,
                                 TLManualPaintVariant variant) {
  PaintDocument *d;
  int piece = (int)part, direction = (int)variant;
  if (!paint ||
      !identity_valid(family, control, state, piece, direction))
    return -1;
  for (d = paint->documents; d; d = d->next)
    if (d->family == family && d->control == control && d->state == state &&
        d->part == piece && d->variant == direction) {
      paint->current = d;
      return 0;
    }
  d = doc_new(family, control, state, piece, direction, 96, 32);
  if (!d)
    return -1;
  d->next = paint->documents;
  paint->documents = d;
  paint->current = d;
  return 0;
}
int tl_manual_paint_current_family(const TLManualPaint *p) {
  return p && p->current ? p->current->family : -1;
}
int tl_manual_paint_current_control(const TLManualPaint *p) {
  return p && p->current ? p->current->control : -1;
}
int tl_manual_paint_current_state(const TLManualPaint *p) {
  return p && p->current ? p->current->state : -1;
}
int tl_manual_paint_current_part(const TLManualPaint *p) {
  return p && p->current ? p->current->part : -1;
}
int tl_manual_paint_current_variant(const TLManualPaint *p) {
  return p && p->current ? p->current->variant : -1;
}
int tl_manual_paint_resize(TLManualPaint *paint, int width, int height) {
  PaintDocument *d;
  uint32_t *pixels;
  int copy_w, copy_h;
  if (!paint || !(d = paint->current) || !size_valid(width, height))
    return -1;
  if (d->width == width && d->height == height)
    return 0;
  pixels = calloc(pixel_count(width, height), sizeof(*pixels));
  if (!pixels)
    return -1;
  copy_w = width < d->width ? width : d->width;
  copy_h = height < d->height ? height : d->height;
  for (int y = 0; y < copy_h; ++y)
    memcpy(pixels + (size_t)y * width, d->pixels + (size_t)y * d->width,
           (size_t)copy_w * sizeof(*pixels));
  uint32_t *old_pixels = d->pixels;
  int old_width = d->width, old_height = d->height;
  d->pixels = pixels;
  d->width = width;
  d->height = height;
  if (history_push(d)) {
    d->pixels = old_pixels;
    d->width = old_width;
    d->height = old_height;
    free(pixels);
    return -1;
  }
  free(old_pixels);
  return 0;
}
int tl_manual_paint_replace(TLManualPaint *paint, int width, int height,
                            const uint32_t *pixels) {
  PaintDocument *d;
  uint32_t *replacement, *old_pixels;
  int old_width, old_height;
  size_t count;
  if (!paint || !(d = paint->current) || !pixels ||
      !size_valid(width, height))
    return -1;
  count = pixel_count(width, height);
  replacement = malloc(count * sizeof(*replacement));
  if (!replacement)
    return -1;
  memcpy(replacement, pixels, count * sizeof(*replacement));
  old_pixels = d->pixels;
  old_width = d->width;
  old_height = d->height;
  d->pixels = replacement;
  d->width = width;
  d->height = height;
  if (history_push(d)) {
    d->pixels = old_pixels;
    d->width = old_width;
    d->height = old_height;
    free(replacement);
    return -1;
  }
  free(old_pixels);
  return 0;
}
int tl_manual_paint_width(const TLManualPaint *p) {
  return p && p->current ? p->current->width : 0;
}
int tl_manual_paint_height(const TLManualPaint *p) {
  return p && p->current ? p->current->height : 0;
}
const uint32_t *tl_manual_paint_pixels(const TLManualPaint *p) {
  return p && p->current ? p->current->pixels : NULL;
}
uint32_t tl_manual_paint_pixel(const TLManualPaint *p, int x, int y) {
  if (!p || !p->current || x < 0 || y < 0 || x >= p->current->width ||
      y >= p->current->height)
    return 0;
  return p->current->pixels[(size_t)y * p->current->width + x];
}
void tl_manual_paint_color(TLManualPaint *p, uint32_t rgba) {
  if (p)
    p->color = rgba;
}
uint32_t tl_manual_paint_color_get(const TLManualPaint *p) {
  return p ? p->color : 0;
}
int tl_manual_paint_put(TLManualPaint *p, int x, int y, uint32_t rgba) {
  if (!p || !p->current || x < 0 || y < 0 || x >= p->current->width ||
      y >= p->current->height)
    return -1;
  p->current->pixels[(size_t)y * p->current->width + x] = rgba;
  return 0;
}
static int line_raw(PaintDocument *d, int x0, int y0, int x1, int y1,
                    uint32_t rgba) {
  int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
  int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1, err = dx + dy;
  for (;;) {
    if (x0 >= 0 && y0 >= 0 && x0 < d->width && y0 < d->height)
      d->pixels[(size_t)y0 * d->width + x0] = rgba;
    if (x0 == x1 && y0 == y1)
      break;
    int twice = 2 * err;
    if (twice >= dy) {
      err += dy;
      x0 += sx;
    }
    if (twice <= dx) {
      err += dx;
      y0 += sy;
    }
  }
  return 0;
}
int tl_manual_paint_line(TLManualPaint *p, int x0, int y0, int x1, int y1,
                         uint32_t rgba) {
  return p && p->current ? line_raw(p->current, x0, y0, x1, y1, rgba) : -1;
}
int tl_manual_paint_rect(TLManualPaint *p, int x0, int y0, int x1, int y1,
                         uint32_t rgba) {
  if (!p || !p->current)
    return -1;
  line_raw(p->current, x0, y0, x1, y0, rgba);
  line_raw(p->current, x0, y1, x1, y1, rgba);
  line_raw(p->current, x0, y0, x0, y1, rgba);
  line_raw(p->current, x1, y0, x1, y1, rgba);
  return 0;
}
int tl_manual_paint_fill(TLManualPaint *p, int x, int y, uint32_t rgba) {
  PaintDocument *d;
  uint32_t from;
  size_t n, head = 0, tail = 0;
  size_t *queue;
  if (!p || !(d = p->current) || x < 0 || y < 0 || x >= d->width ||
      y >= d->height)
    return -1;
  n = pixel_count(d->width, d->height);
  from = d->pixels[(size_t)y * d->width + x];
  if (from == rgba)
    return 0;
  queue = malloc(n * sizeof(*queue));
  if (!queue)
    return -1;
  queue[tail++] = (size_t)y * d->width + x;
  d->pixels[queue[0]] = rgba;
  while (head < tail) {
    size_t at = queue[head++];
    int px = (int)(at % d->width), py = (int)(at / d->width);
    size_t neighbors[4];
    int count = 0;
    if (px)
      neighbors[count++] = at - 1;
    if (px + 1 < d->width)
      neighbors[count++] = at + 1;
    if (py)
      neighbors[count++] = at - d->width;
    if (py + 1 < d->height)
      neighbors[count++] = at + d->width;
    for (int i = 0; i < count; ++i)
      if (d->pixels[neighbors[i]] == from) {
        d->pixels[neighbors[i]] = rgba;
        queue[tail++] = neighbors[i];
      }
  }
  free(queue);
  return 0;
}
int tl_manual_paint_checkpoint(TLManualPaint *p) {
  return p && p->current ? history_push(p->current) : -1;
}
int tl_manual_paint_can_undo(const TLManualPaint *p) {
  return p && p->current && p->current->position > 0;
}
int tl_manual_paint_can_redo(const TLManualPaint *p) {
  return p && p->current && p->current->position + 1 < p->current->count;
}
int tl_manual_paint_undo(TLManualPaint *p) {
  PaintDocument *d;
  Snapshot *s;
  if (!tl_manual_paint_can_undo(p) || !(d = p->current))
    return -1;
  s = &d->history[--d->position];
  uint32_t *pixels = malloc(pixel_count(s->width, s->height) * sizeof(*pixels));
  if (!pixels) {
    ++d->position;
    return -1;
  }
  memcpy(pixels, s->pixels, pixel_count(s->width, s->height) * sizeof(*pixels));
  free(d->pixels);
  d->pixels = pixels;
  d->width = s->width;
  d->height = s->height;
  return 0;
}
int tl_manual_paint_redo(TLManualPaint *p) {
  PaintDocument *d;
  Snapshot *s;
  if (!tl_manual_paint_can_redo(p) || !(d = p->current))
    return -1;
  s = &d->history[++d->position];
  uint32_t *pixels = malloc(pixel_count(s->width, s->height) * sizeof(*pixels));
  if (!pixels) {
    --d->position;
    return -1;
  }
  memcpy(pixels, s->pixels, pixel_count(s->width, s->height) * sizeof(*pixels));
  free(d->pixels);
  d->pixels = pixels;
  d->width = s->width;
  d->height = s->height;
  return 0;
}
static int write_all(int fd, const char *data, size_t size) {
  while (size) {
    ssize_t n = write(fd, data, size);
    if (n < 0 && errno == EINTR)
      continue;
    if (n <= 0)
      return -1;
    data += n;
    size -= (size_t)n;
  }
  return 0;
}
static void error_set(char *error, size_t cap, const char *text) {
  if (error && cap)
    snprintf(error, cap, "%s", text);
}
static json_object *document_json_data(int family, int control, int state,
                                       int part, int variant, int width,
                                       int height, const char *hex,
                                       size_t length) {
  json_object *item;
  if (!identity_valid(family, control, state, part, variant) ||
      !size_valid(width, height) || !hex || length != pixel_count(width, height) * 8 ||
      part < 0 || part >= TL_PAINT_PART_COUNT || variant < 0 ||
      variant >= TL_PAINT_VARIANT_COUNT ||
      !(item = json_object_new_object()))
    return NULL;
  json_object_object_add(item, "family", json_object_new_int(family));
  json_object_object_add(item, "control", json_object_new_int(control));
  json_object_object_add(item, "state", json_object_new_int(state));
  json_object_object_add(item, "part", json_object_new_string(part_ids[part]));
  json_object_object_add(item, "variant",
                         json_object_new_string(variant_ids[variant]));
  json_object_object_add(item, "width", json_object_new_int(width));
  json_object_object_add(item, "height", json_object_new_int(height));
  json_object_object_add(item, "rgba_hex",
                         json_object_new_string_len(hex, (int)length));
  return item;
}
static json_object *document_json(const PaintDocument *d) {
  size_t n = pixel_count(d->width, d->height), length = n * 8;
  char *hex = malloc(length + 1);
  json_object *item;
  static const char digits[] = "0123456789abcdef";
  if (!hex) {
    free(hex);
    return NULL;
  }
  for (size_t i = 0; i < n; ++i) {
    uint32_t pixel = d->pixels[i];
    for (int c = 0; c < 8; ++c)
      hex[i * 8 + c] = digits[(pixel >> (28 - c * 4)) & 15u];
  }
  hex[length] = 0;
  item = document_json_data(d->family, d->control, d->state, d->part,
                            d->variant, d->width, d->height, hex, length);
  free(hex);
  return item;
}
int tl_manual_paint_save(const TLManualPaint *p, const char *path, char *error,
                         size_t cap) {
  struct stat st;
  char *tmp, *text;
  json_object *root, *items;
  int fd = -1, result = -1;
  if (!p || !path || path[0] != '/') {
    error_set(error, cap, "O caminho do projeto raster deve ser absoluto.");
    return -1;
  }
  if (lstat(path, &st) == 0 && (!S_ISREG(st.st_mode) || S_ISLNK(st.st_mode))) {
    error_set(error, cap, "O destino raster não é arquivo regular.");
    return -1;
  }
  root = json_object_new_object();
  items = json_object_new_array();
  if (!root || !items) {
    error_set(error, cap, "Sem memória para salvar a camada manual.");
    goto done;
  }
  json_object_object_add(root, "schema_version",
                         json_object_new_int(TL_PAINT_SCHEMA_VERSION));
  json_object_object_add(root, "kind", json_object_new_string(TL_PAINT_KIND));
  for (const PaintDocument *d = p->documents; d; d = d->next) {
    json_object *item = document_json(d);
    if (!item) {
      error_set(error, cap, "Sem memória para codificar a camada manual.");
      goto done;
    }
    json_object_array_add(items, item);
  }
  json_object_object_add(root, "documents", items);
  items = NULL;
  text = strdup(json_object_to_json_string_ext(root, JSON_C_TO_STRING_PRETTY));
  if (!text) {
    error_set(error, cap, "Sem memória para preparar o arquivo raster.");
    goto done;
  }
  size_t n = strlen(text);
  if (n > TL_PAINT_FILE_MAX) {
    free(text);
    error_set(error, cap, "A camada raster excede 32 MiB.");
    goto done;
  }
  tmp = malloc(strlen(path) + 24);
  if (!tmp) {
    free(text);
    error_set(error, cap, "Sem memória para preparar o arquivo raster.");
    goto done;
  }
  sprintf(tmp, "%s.tmp.XXXXXX", path);
  fd = mkstemp(tmp);
  if (fd < 0) {
    free(tmp);
    free(text);
    error_set(error, cap,
              "Não foi possível criar checkpoint temporário da camada.");
    goto done;
  }
  (void)fchmod(fd, 0600);
  if (!write_all(fd, text, n) && !fsync(fd) && !close(fd)) {
    fd = -1;
    if (!rename(tmp, path))
      result = 0;
  }
  if (fd >= 0)
    close(fd);
  if (result)
    unlink(tmp);
  free(tmp);
  free(text);
  if (result)
    error_set(error, cap, "Falha ao confirmar o checkpoint da camada raster.");
  else
    error_set(error, cap,
              "Camada manual salva no arquivo complementar do projeto.");
done:
  if (items)
    json_object_put(items);
  if (root)
    json_object_put(root);
  return result;
}
static int parse_hex(const char *hex, size_t length, uint32_t *pixels,
                     size_t count) {
  if (!hex || length != count * 8)
    return -1;
  for (size_t i = 0; i < count; ++i) {
    uint32_t pixel = 0;
    for (int c = 0; c < 8; ++c) {
      unsigned char ch = (unsigned char)hex[i * 8 + c];
      int digit = ch >= '0' && ch <= '9'   ? ch - '0'
                  : ch >= 'a' && ch <= 'f' ? ch - 'a' + 10
                  : ch >= 'A' && ch <= 'F' ? ch - 'A' + 10
                                           : -1;
      if (digit < 0)
        return -1;
      pixel = (pixel << 4) | (uint32_t)digit;
    }
    pixels[i] = pixel;
  }
  return 0;
}
int tl_manual_paint_load(TLManualPaint *p, const char *path, char *error,
                         size_t cap) {
  struct stat st;
  json_object *root = NULL, *items, *kind;
  char *buffer = NULL;
  int fd = -1, result = -1, schema_version = 0;
  size_t invalid_document = 0;
  char invalid_detail[128] = "estrutura ou pixels inválidos";
  TLManualPaint *loaded = NULL;
  if (!p || !path || path[0] != '/') {
    error_set(error, cap, "O caminho da camada deve ser absoluto.");
    return -1;
  }
  if (lstat(path, &st)) {
    if (errno == ENOENT) {
      error_set(error, cap, "Nenhuma camada manual salva; canvas vazio.");
      return 0;
    }
    error_set(error, cap, "Não foi possível verificar o arquivo da camada.");
    return -1;
  }
  if (!S_ISREG(st.st_mode) || S_ISLNK(st.st_mode) || st.st_size < 0 ||
      (uint64_t)st.st_size > TL_PAINT_FILE_MAX) {
    error_set(error, cap, "O arquivo da camada é inválido ou excede 32 MiB.");
    return -1;
  }
  fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0) {
    error_set(error, cap, "Não foi possível abrir com segurança a camada.");
    return -1;
  }
  buffer = malloc((size_t)st.st_size + 1);
  if (!buffer) {
    error_set(error, cap, "Sem memória para ler a camada manual.");
    goto done;
  }
  size_t used = 0;
  while (used < (size_t)st.st_size) {
    ssize_t n = read(fd, buffer + used, (size_t)st.st_size - used);
    if (n < 0 && errno == EINTR)
      continue;
    if (n <= 0)
      goto done;
    used += (size_t)n;
  }
  close(fd);
  fd = -1;
  buffer[used] = 0;
  root = json_tokener_parse(buffer);
  json_object *version = NULL;
  if (!root || !json_object_is_type(root, json_type_object) ||
      !json_object_object_get_ex(root, "schema_version", &version) ||
      !json_object_is_type(version, json_type_int) ||
      !json_object_object_get_ex(root, "kind", &kind) ||
      !json_object_is_type(kind, json_type_string) ||
      strcmp(json_object_get_string(kind), TL_PAINT_KIND) ||
      !json_object_object_get_ex(root, "documents", &items) ||
      !json_object_is_type(items, json_type_array)) {
    error_set(error, cap,
              "O arquivo não é um projeto válido de camada manual.");
    goto done;
  }
  schema_version = json_object_get_int(version);
  if (schema_version != 1 && schema_version != TL_PAINT_SCHEMA_VERSION) {
    error_set(error, cap,
              "O arquivo não é um projeto válido de camada manual.");
    goto done;
  }
  loaded = tl_manual_paint_new();
  if (!loaded) {
    error_set(error, cap, "Sem memória para abrir a camada manual.");
    goto done;
  }
  for (size_t i = 0; i < json_object_array_length(items); ++i) {
    json_object *item = json_object_array_get_idx(items, i), *v;
    int family, control, state, part = TL_PAINT_PART_WHOLE,
        variant = TL_PAINT_VARIANT_AUTO, width, height,
        legacy_placeholder = 0;
    const char *hex;
    size_t n;
    PaintDocument *d;
    invalid_document = i + 1;
    snprintf(invalid_detail, sizeof(invalid_detail),
             "estrutura ou pixels inválidos");
    if (!item || !json_object_is_type(item, json_type_object) ||
        !json_object_object_get_ex(item, "family", &v) ||
        !json_object_is_type(v, json_type_int))
      goto invalid;
    family = json_object_get_int(v);
    if (!json_object_object_get_ex(item, "control", &v) ||
        !json_object_is_type(v, json_type_int))
      goto invalid;
    control = json_object_get_int(v);
    if (!json_object_object_get_ex(item, "state", &v) ||
        !json_object_is_type(v, json_type_int))
      goto invalid;
    state = json_object_get_int(v);
    if (schema_version == TL_PAINT_SCHEMA_VERSION) {
      const char *id;
      size_t length;
      if (!json_object_object_get_ex(item, "part", &v) ||
          !json_object_is_type(v, json_type_string))
        goto invalid;
      id = json_object_get_string(v);
      length = (size_t)json_object_get_string_len(v);
      if (length != strlen(id) ||
          (part = id_from_text(id, part_ids, TL_PAINT_PART_COUNT)) < 0)
        goto invalid;
      if (!json_object_object_get_ex(item, "variant", &v) ||
          !json_object_is_type(v, json_type_string))
        goto invalid;
      id = json_object_get_string(v);
      length = (size_t)json_object_get_string_len(v);
      if (length != strlen(id) ||
          (variant = id_from_text(id, variant_ids,
                                  TL_PAINT_VARIANT_COUNT)) < 0)
        goto invalid;
    }
    if (!json_object_object_get_ex(item, "width", &v) ||
        !json_object_is_type(v, json_type_int))
      goto invalid;
    width = json_object_get_int(v);
    if (!json_object_object_get_ex(item, "height", &v) ||
        !json_object_is_type(v, json_type_int))
      goto invalid;
    height = json_object_get_int(v);
    if (!json_object_object_get_ex(item, "rgba_hex", &v) ||
        !json_object_is_type(v, json_type_string))
      goto invalid;
    hex = json_object_get_string(v);
    n = json_object_get_string_len(v);
    legacy_placeholder = schema_version == 1 && width == 0 && height == 0 &&
                         n == 0;
    if (legacy_placeholder) {
      width = 96;
      height = 32;
    }
    if (!identity_valid(family, control, state, part, variant)) {
      snprintf(invalid_detail, sizeof(invalid_detail),
               "peça, variante ou contexto inválido");
      goto invalid;
    }
    if (!size_valid(width, height)) {
      snprintf(invalid_detail, sizeof(invalid_detail),
               "dimensões %d x %d fora do intervalo permitido", width,
               height);
      goto invalid;
    }
    for (d = loaded->documents; d; d = d->next)
      if (d->family == family && d->control == control && d->state == state &&
          d->part == part && d->variant == variant) {
        snprintf(invalid_detail, sizeof(invalid_detail),
                 "identidade de camada duplicada");
        goto invalid;
      }
    d = doc_new(family, control, state, part, variant, width, height);
    if (!d || (!legacy_placeholder &&
               parse_hex(hex, n, d->pixels, pixel_count(width, height)))) {
      doc_free(d);
      goto invalid;
    }
    doc_history_clear(d);
    if (history_push(d)) {
      doc_free(d);
      goto invalid;
    }
    d->next = loaded->documents;
    loaded->documents = d;
  }
  if (p->current) {
    if (tl_manual_paint_select_piece(
            loaded, p->current->family, p->current->control, p->current->state,
            (TLManualPaintPart)p->current->part,
            (TLManualPaintVariant)p->current->variant))
      goto done;
  }
  PaintDocument *old = p->documents;
  p->documents = loaded->documents;
  p->current = loaded->current;
  p->color = loaded->color;
  loaded->documents = loaded->current = NULL;
  while (old) {
    PaintDocument *next = old->next;
    doc_free(old);
    old = next;
  }
  result = 0;
  error_set(error, cap, "Camada manual retomada do projeto.");
  goto done;
invalid:
  if (error && cap)
    snprintf(error, cap,
             "Documento %zu inválido (%s); original preservado.",
             invalid_document, invalid_detail);
done:
  if (fd >= 0)
    close(fd);
  free(buffer);
  if (root)
    json_object_put(root);
  tl_manual_paint_free(loaded);
  return result;
}

static int paint_document_valid(json_object *item, int schema_version,
                                int *family, int *control, int *state,
                                int *part, int *variant, int *width,
                                int *height, const char **hex,
                                size_t *length, int *legacy_placeholder) {
  json_object *v;
  uint32_t *pixels;
  *part = TL_PAINT_PART_WHOLE;
  *variant = TL_PAINT_VARIANT_AUTO;
  *legacy_placeholder = 0;
  if (!item || !json_object_is_type(item, json_type_object) ||
      !json_object_object_get_ex(item, "family", &v) ||
      !json_object_is_type(v, json_type_int))
    return 0;
  *family = json_object_get_int(v);
  if (!json_object_object_get_ex(item, "control", &v) ||
      !json_object_is_type(v, json_type_int))
    return 0;
  *control = json_object_get_int(v);
  if (!json_object_object_get_ex(item, "state", &v) ||
      !json_object_is_type(v, json_type_int))
    return 0;
  *state = json_object_get_int(v);
  if (schema_version == TL_PAINT_SCHEMA_VERSION) {
    const char *id;
    size_t id_length;
    if (!json_object_object_get_ex(item, "part", &v) ||
        !json_object_is_type(v, json_type_string))
      return 0;
    id = json_object_get_string(v);
    id_length = (size_t)json_object_get_string_len(v);
    if (id_length != strlen(id) ||
        (*part = id_from_text(id, part_ids, TL_PAINT_PART_COUNT)) < 0)
      return 0;
    if (!json_object_object_get_ex(item, "variant", &v) ||
        !json_object_is_type(v, json_type_string))
      return 0;
    id = json_object_get_string(v);
    id_length = (size_t)json_object_get_string_len(v);
    if (id_length != strlen(id) ||
        (*variant = id_from_text(id, variant_ids, TL_PAINT_VARIANT_COUNT)) < 0)
      return 0;
  }
  if (!json_object_object_get_ex(item, "width", &v) ||
      !json_object_is_type(v, json_type_int))
    return 0;
  *width = json_object_get_int(v);
  if (!json_object_object_get_ex(item, "height", &v) ||
      !json_object_is_type(v, json_type_int))
    return 0;
  *height = json_object_get_int(v);
  if (!identity_valid(*family, *control, *state, *part, *variant) ||
      !json_object_object_get_ex(item, "rgba_hex", &v) ||
      !json_object_is_type(v, json_type_string))
    return 0;
  *hex = json_object_get_string(v);
  *length = (size_t)json_object_get_string_len(v);
  *legacy_placeholder = schema_version == 1 && *width == 0 && *height == 0 &&
                        *length == 0;
  if (*legacy_placeholder) {
    *width = 96;
    *height = 32;
    return 1;
  }
  if (!size_valid(*width, *height))
    return 0;
  pixels = malloc(pixel_count(*width, *height) * sizeof(*pixels));
  if (!pixels)
    return -1;
  int valid = parse_hex(*hex, *length, pixels,
                        pixel_count(*width, *height)) == 0;
  free(pixels);
  return valid;
}

int tl_manual_paint_recover(const char *source, const char *destination,
                            char *error, size_t cap) {
  struct stat st;
  json_object *root = NULL, *items = NULL, *kind = NULL, *version = NULL;
  json_object *recovered = NULL, *output = NULL;
  char *buffer = NULL, *text = NULL, *temporary = NULL;
  int fd = -1, result = -1, valid_count = 0, schema_version = 0;
  size_t invalid_count = 0;
  unsigned char seen[10][16][5][TL_PAINT_PART_COUNT]
                    [TL_PAINT_VARIANT_COUNT] = {{{{{0}}}}};
  if (!source || source[0] != '/' || !destination || destination[0] != '/' ||
      strcmp(source, destination) == 0) {
    error_set(error, cap, "Origem e destino devem ser caminhos absolutos diferentes.");
    return -1;
  }
  if (lstat(source, &st) || !S_ISREG(st.st_mode) || S_ISLNK(st.st_mode) ||
      st.st_size < 0 || (uint64_t)st.st_size > TL_PAINT_FILE_MAX) {
    error_set(error, cap, "O arquivo original é inválido ou excede 32 MiB.");
    return -1;
  }
  fd = open(source, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0) {
    error_set(error, cap, "Não foi possível abrir o original para recuperação.");
    goto done;
  }
  buffer = malloc((size_t)st.st_size + 1);
  if (!buffer) {
    error_set(error, cap, "Sem memória para ler o arquivo original.");
    goto done;
  }
  size_t used = 0;
  while (used < (size_t)st.st_size) {
    ssize_t n = read(fd, buffer + used, (size_t)st.st_size - used);
    if (n < 0 && errno == EINTR)
      continue;
    if (n <= 0) {
      error_set(error, cap, "Falha ao ler o arquivo original completo.");
      goto done;
    }
    used += (size_t)n;
  }
  buffer[used] = 0;
  root = json_tokener_parse(buffer);
  if (!root || !json_object_is_type(root, json_type_object) ||
      !json_object_object_get_ex(root, "schema_version", &version) ||
      !json_object_is_type(version, json_type_int) ||
      !json_object_object_get_ex(root, "kind", &kind) ||
      !json_object_is_type(kind, json_type_string) ||
      strcmp(json_object_get_string(kind), TL_PAINT_KIND) ||
      !json_object_object_get_ex(root, "documents", &items) ||
      !json_object_is_type(items, json_type_array)) {
    error_set(error, cap, "O original não é um projeto de pintura recuperável.");
    goto done;
  }
  schema_version = json_object_get_int(version);
  if (schema_version != 1 && schema_version != TL_PAINT_SCHEMA_VERSION) {
    error_set(error, cap, "O original não é um projeto de pintura recuperável.");
    goto done;
  }
  recovered = json_object_new_array();
  output = json_object_new_object();
  if (!recovered || !output) {
    error_set(error, cap, "Sem memória para preparar as camadas recuperadas.");
    goto done;
  }
  for (size_t i = 0; i < json_object_array_length(items); ++i) {
    json_object *item = json_object_array_get_idx(items, i);
    int family = 0, control = 0, state = 0, part = 0, variant = 0,
        width = 0, height = 0, legacy_placeholder = 0;
    const char *hex = NULL;
    size_t length = 0;
    int valid = paint_document_valid(item, schema_version, &family, &control,
                                     &state, &part, &variant, &width, &height,
                                     &hex, &length, &legacy_placeholder);
    if (valid < 0) {
      error_set(error, cap, "Sem memória para validar uma camada raster.");
      goto done;
    }
    if (!valid || seen[family][control][state][part][variant]) {
      ++invalid_count;
      continue;
    }
    seen[family][control][state][part][variant] = 1;
    json_object *copy = NULL;
    if (legacy_placeholder) {
      PaintDocument *blank = doc_new(family, control, state, part, variant,
                                     width, height);
      if (blank) {
        copy = document_json(blank);
        doc_free(blank);
      }
    } else
      copy = document_json_data(family, control, state, part, variant, width,
                                height, hex, length);
    if (!copy || json_object_array_add(recovered, copy)) {
      if (copy)
        json_object_put(copy);
      error_set(error, cap, "Sem memória para reunir as camadas válidas.");
      goto done;
    }
    ++valid_count;
  }
  if (valid_count == 0) {
    error_set(error, cap, "Nenhuma camada íntegra encontrada; original preservado.");
    goto done;
  }
  json_object_object_add(output, "schema_version",
                         json_object_new_int(TL_PAINT_SCHEMA_VERSION));
  json_object_object_add(output, "kind", json_object_new_string(TL_PAINT_KIND));
  json_object_object_add(output, "documents", recovered);
  recovered = NULL;
  text = strdup(json_object_to_json_string_ext(output, JSON_C_TO_STRING_PRETTY));
  if (!text || strlen(text) > TL_PAINT_FILE_MAX) {
    error_set(error, cap, "Não foi possível preparar o arquivo recuperado.");
    goto done;
  }
  temporary = malloc(strlen(destination) + 24);
  if (!temporary) {
    error_set(error, cap, "Sem memória para reservar o arquivo recuperado.");
    goto done;
  }
  sprintf(temporary, "%s.tmp.XXXXXX", destination);
  fd = mkstemp(temporary);
  if (fd < 0) {
    error_set(error, cap,
              "Não foi possível criar o arquivo temporário no destino escolhido.");
    goto done;
  }
  (void)fchmod(fd, 0600);
  if (write_all(fd, text, strlen(text)) || fsync(fd) || close(fd)) {
    fd = -1;
    error_set(error, cap, "Falha ao gravar as camadas recuperadas.");
    goto done;
  }
  fd = -1;
  if (link(temporary, destination)) {
    error_set(error, cap, errno == EEXIST
                            ? "O destino já existe; nenhum arquivo foi substituído."
                            : "Não foi possível publicar o arquivo recuperado.");
    goto done;
  }
  result = valid_count;
  if (error && cap)
    snprintf(error, cap, "%d camadas recuperadas; %zu inválidas ignoradas%s",
             valid_count, invalid_count,
             invalid_count ? ". Original preservado." : ".");
done:
  if (fd >= 0)
    close(fd);
  if (temporary) {
    unlink(temporary);
    free(temporary);
  }
  free(text);
  free(buffer);
  if (recovered)
    json_object_put(recovered);
  if (output)
    json_object_put(output);
  if (root)
    json_object_put(root);
  return result;
}
