/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_GTK2_R584_CATALOG_H
#define TL_GTK2_R584_CATALOG_H

#include "theme_lab.h"
#include <stddef.h>

#define TL_GTK2_R584_SHA256_LENGTH 64

typedef struct TLGtk2R584Catalog TLGtk2R584Catalog;

typedef struct {
  const char *receipt_sha256;
  const char *manifest_sha256;
  const char *bundle_id;
  const char *palette_source_sha256;
} TLGtk2R584Identity;

/* Byte identities of the evidence selected by the user as the R584 baseline.
 * The loader still verifies every file declared by the manifest. */
extern const TLGtk2R584Identity tl_gtk2_r584_canonical_identity;

typedef enum {
  TL_GTK2_R584_PART_WHOLE,
  TL_GTK2_R584_PART_ARROW,
  TL_GTK2_R584_PART_ARROW_BUTTON,
  TL_GTK2_R584_PART_TROUGH,
  TL_GTK2_R584_PART_THUMB
} TLGtk2R584Part;

/* These are the states actually named by the R584 bundle. Focused is not
 * silently treated as hover, and toggled is not silently treated as pressed. */
typedef enum {
  TL_GTK2_R584_STATE_NORMAL,
  TL_GTK2_R584_STATE_FOCUSED,
  TL_GTK2_R584_STATE_PRESSED,
  TL_GTK2_R584_STATE_DISABLED,
  TL_GTK2_R584_STATE_TOGGLED
} TLGtk2R584State;

typedef enum {
  TL_GTK2_R584_DIRECTION_NONE,
  TL_GTK2_R584_DIRECTION_UP,
  TL_GTK2_R584_DIRECTION_DOWN,
  TL_GTK2_R584_DIRECTION_LEFT,
  TL_GTK2_R584_DIRECTION_RIGHT,
  TL_GTK2_R584_DIRECTION_HORIZONTAL,
  TL_GTK2_R584_DIRECTION_VERTICAL
} TLGtk2R584Direction;

typedef enum {
  TL_GTK2_R584_VARIANT_NONE,
  TL_GTK2_R584_VARIANT_OFF,
  TL_GTK2_R584_VARIANT_ON,
  TL_GTK2_R584_VARIANT_MIXED
} TLGtk2R584Variant;

typedef struct {
  int control; /* TL_CONTROL_COUNT index; resolved through tl_control_ids. */
  TLGtk2R584Part part;
  TLGtk2R584State state;
  TLGtk2R584Direction direction;
  TLGtk2R584Variant variant;
} TLGtk2R584Query;

typedef struct {
  int available;
  char reason[192];
  char asset_name[160];
  char path[TL_PATH_MAX];
  char sha256[TL_GTK2_R584_SHA256_LENGTH + 1];
} TLGtk2R584Result;

/* The verified loader is public so hermetic fixtures can carry their own
 * trusted byte identity. Production callers should use load_canonical. */
int tl_gtk2_r584_catalog_load_verified(
    TLGtk2R584Catalog **result, const char *receipt_path,
    const char *manifest_path, const TLGtk2R584Identity *identity, char *error,
    size_t capacity);
int tl_gtk2_r584_catalog_load_canonical(TLGtk2R584Catalog **result,
                                        const char *receipt_path,
                                        const char *manifest_path, char *error,
                                        size_t capacity);
void tl_gtk2_r584_catalog_free(TLGtk2R584Catalog *catalog);

const char *tl_gtk2_r584_catalog_bundle_id(const TLGtk2R584Catalog *catalog);
const char *tl_gtk2_r584_catalog_bundle_root(const TLGtk2R584Catalog *catalog);
size_t tl_gtk2_r584_catalog_asset_count(const TLGtk2R584Catalog *catalog);

/* Returns 0 for a valid query, including explicit unavailability. Returns -1
 * only for an invalid API request. No fallback between state, direction,
 * control or piece is performed. */
int tl_gtk2_r584_catalog_lookup(const TLGtk2R584Catalog *catalog,
                                const TLGtk2R584Query *query,
                                TLGtk2R584Result *result, char *error,
                                size_t capacity);

#endif
