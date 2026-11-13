/* SPDX-License-Identifier: GPL-3.0-or-later */
#define _POSIX_C_SOURCE 200809L
#include "gtk2_r584_catalog.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* Keep this isolated test independent of the mutable application model while
 * providing the same public IDs consumed by the catalog. */
const char *const tl_control_ids[TL_CONTROL_COUNT] = {
    "push",     "toggle",   "check",    "radio",   "entry",  "combo",
    "spin",     "text",     "scale_h",  "scale_v", "scroll_h",
    "scroll_v", "arrow",    "progress", "list",    "frame"};

static int control(const char *id) {
  int i;
  for (i = 0; i < TL_CONTROL_COUNT; ++i)
    if (!strcmp(tl_control_ids[i], id))
      return i;
  assert(!"unknown control fixture id");
  return -1;
}

static void available(const TLGtk2R584Catalog *catalog, const char *control_id,
                      TLGtk2R584Part part, TLGtk2R584State state,
                      TLGtk2R584Direction direction,
                      TLGtk2R584Variant variant, const char *asset_name) {
  TLGtk2R584Query query = {control(control_id), part, state, direction, variant};
  TLGtk2R584Result result;
  char error[256];
  assert(!tl_gtk2_r584_catalog_lookup(catalog, &query, &result, error,
                                      sizeof(error)));
  assert(!error[0] && result.available && !result.reason[0]);
  assert(!strcmp(result.asset_name, asset_name));
  assert(strstr(result.path, "/assets/"));
  assert(strlen(result.sha256) == TL_GTK2_R584_SHA256_LENGTH);
}

static void unavailable(const TLGtk2R584Catalog *catalog,
                        const char *control_id, TLGtk2R584Part part,
                        TLGtk2R584State state,
                        TLGtk2R584Direction direction,
                        TLGtk2R584Variant variant) {
  TLGtk2R584Query query = {control(control_id), part, state, direction, variant};
  TLGtk2R584Result result;
  char error[256];
  assert(!tl_gtk2_r584_catalog_lookup(catalog, &query, &result, error,
                                      sizeof(error)));
  assert(!error[0] && !result.available);
  assert(strstr(result.reason, "não declara asset"));
  assert(!result.asset_name[0] && !result.path[0] && !result.sha256[0]);
}

int main(int argc, char **argv) {
  static const TLGtk2R584Identity fixture_identity = {
      "10161c0d6e36f2af66f1bb8ed2e180cfc42877a5d67f0e65a999456c8e43b080",
      "7c303e99ea3ed0738f2363264ffd28ec6b592ec867c49c60b5c8489426102f84",
      "1111111111111111111111111111111111111111111111111111111111111111",
      "ef34a032ddb76017ff15e92524d1964eb28b0cf71414312030456b3348c79b70"};
  TLGtk2R584Identity wrong_identity = fixture_identity;
  TLGtk2R584Catalog *catalog = NULL;
  TLGtk2R584Result result;
  TLGtk2R584Query bad_query;
  char receipt[TL_PATH_MAX], manifest[TL_PATH_MAX], error[256];
  assert(argc == 2 || argc == 4);
  assert(snprintf(receipt, sizeof(receipt), "%s/receipt.json", argv[1]) > 0);
  assert(snprintf(manifest, sizeof(manifest), "%s/%s/manifest.json", argv[1],
                  fixture_identity.bundle_id) > 0);
  assert(!tl_gtk2_r584_catalog_load_verified(
      &catalog, receipt, manifest, &fixture_identity, error, sizeof(error)));
  assert(catalog && !error[0]);
  assert(tl_gtk2_r584_catalog_asset_count(catalog) == 6);
  assert(!strcmp(tl_gtk2_r584_catalog_bundle_id(catalog),
                 fixture_identity.bundle_id));
  assert(strstr(tl_gtk2_r584_catalog_bundle_root(catalog),
                "/tests/fixtures/gtk2-r584/111111111111111111111111111111111"));

  available(catalog, "push", TL_GTK2_R584_PART_WHOLE,
            TL_GTK2_R584_STATE_NORMAL, TL_GTK2_R584_DIRECTION_NONE,
            TL_GTK2_R584_VARIANT_NONE, "command-normal.png");
  available(catalog, "check", TL_GTK2_R584_PART_WHOLE,
            TL_GTK2_R584_STATE_PRESSED, TL_GTK2_R584_DIRECTION_NONE,
            TL_GTK2_R584_VARIANT_ON, "check-on-pressed.png");
  available(catalog, "scroll_h", TL_GTK2_R584_PART_TROUGH,
            TL_GTK2_R584_STATE_NORMAL, TL_GTK2_R584_DIRECTION_HORIZONTAL,
            TL_GTK2_R584_VARIANT_NONE,
            "scroll-trough-normal-horizontal.png");
  available(catalog, "scroll_v", TL_GTK2_R584_PART_ARROW_BUTTON,
            TL_GTK2_R584_STATE_PRESSED, TL_GTK2_R584_DIRECTION_UP,
            TL_GTK2_R584_VARIANT_NONE, "scrollbar-stepper-up-pressed.png");
  available(catalog, "scroll_h", TL_GTK2_R584_PART_THUMB,
            TL_GTK2_R584_STATE_DISABLED, TL_GTK2_R584_DIRECTION_NONE,
            TL_GTK2_R584_VARIANT_NONE, "scroll-thumb-disabled.png");
  available(catalog, "scroll_v", TL_GTK2_R584_PART_THUMB,
            TL_GTK2_R584_STATE_DISABLED, TL_GTK2_R584_DIRECTION_NONE,
            TL_GTK2_R584_VARIANT_NONE, "scroll-thumb-disabled.png");

  /* No inferred mapping: tab has no tl_control_ids peer, toggle is not push,
   * focused is not normal, missing orientation and check variant stay absent. */
  unavailable(catalog, "toggle", TL_GTK2_R584_PART_WHOLE,
              TL_GTK2_R584_STATE_NORMAL, TL_GTK2_R584_DIRECTION_NONE,
              TL_GTK2_R584_VARIANT_NONE);
  unavailable(catalog, "push", TL_GTK2_R584_PART_WHOLE,
              TL_GTK2_R584_STATE_FOCUSED, TL_GTK2_R584_DIRECTION_NONE,
              TL_GTK2_R584_VARIANT_NONE);
  unavailable(catalog, "scroll_v", TL_GTK2_R584_PART_TROUGH,
              TL_GTK2_R584_STATE_NORMAL, TL_GTK2_R584_DIRECTION_VERTICAL,
              TL_GTK2_R584_VARIANT_NONE);
  unavailable(catalog, "check", TL_GTK2_R584_PART_WHOLE,
              TL_GTK2_R584_STATE_PRESSED, TL_GTK2_R584_DIRECTION_NONE,
              TL_GTK2_R584_VARIANT_NONE);

  bad_query = (TLGtk2R584Query){TL_CONTROL_COUNT, TL_GTK2_R584_PART_WHOLE,
                                TL_GTK2_R584_STATE_NORMAL,
                                TL_GTK2_R584_DIRECTION_NONE,
                                TL_GTK2_R584_VARIANT_NONE};
  assert(tl_gtk2_r584_catalog_lookup(catalog, &bad_query, &result, error,
                                     sizeof(error)) == -1);
  assert(strstr(error, "inválida"));
  tl_gtk2_r584_catalog_free(catalog);
  catalog = NULL;

  wrong_identity.receipt_sha256 =
      "00161c0d6e36f2af66f1bb8ed2e180cfc42877a5d67f0e65a999456c8e43b080";
  assert(tl_gtk2_r584_catalog_load_verified(
             &catalog, receipt, manifest, &wrong_identity, error,
             sizeof(error)) == -1);
  assert(!catalog && strstr(error, "SHA-256"));

  assert(!strcmp(tl_gtk2_r584_canonical_identity.bundle_id,
                 "fe95ddd38ef6f61a941d420f6d3d33f376b4d34032c3fc2cf9cad77834710755"));
  if (argc == 4) {
    assert(!tl_gtk2_r584_catalog_load_canonical(
        &catalog, argv[2], argv[3], error, sizeof(error)));
    assert(catalog && !error[0]);
    assert(tl_gtk2_r584_catalog_asset_count(catalog) == 112);
    available(catalog, "scroll_h", TL_GTK2_R584_PART_TROUGH,
              TL_GTK2_R584_STATE_NORMAL, TL_GTK2_R584_DIRECTION_HORIZONTAL,
              TL_GTK2_R584_VARIANT_NONE,
              "scroll-trough-normal-horizontal.png");
    available(catalog, "scroll_v", TL_GTK2_R584_PART_ARROW,
              TL_GTK2_R584_STATE_PRESSED, TL_GTK2_R584_DIRECTION_DOWN,
              TL_GTK2_R584_VARIANT_NONE,
              "scrollbar-arrow-down-pressed.png");
    tl_gtk2_r584_catalog_free(catalog);
    catalog = NULL;
  }
  puts("R584 GTK2 catalog: provenance, hashes, paths, semantic mapping and explicit unavailability passed.");
  return 0;
}
