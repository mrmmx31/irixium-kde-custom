/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_GENERATED_PREVIEW_H
#define TL_GENERATED_PREVIEW_H
#include "theme_lab.h"
#include <json-c/json.h>
/* Returned path belongs to the receipt. GTK2 is explicitly partial, not a
 * declaration that its complete recipe or all controls were applied.
 * GTK4 returns a snapshot directory and admits only the push renderer. */
int tl_generated_preview(json_object *receipt, TLFamily family,
                         const char *scene_hash, const char *generation_dir,
                         const char **path);
#endif
