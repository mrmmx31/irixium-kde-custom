/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_CONTROL_CATALOG_H
#define TL_CONTROL_CATALOG_H
#include <Xm/Xm.h>
#include "theme_lab.h"
typedef struct TLControlCatalog TLControlCatalog;
typedef void (*TLCatalogChanged)(void *context, int selected_control);
TLControlCatalog *tl_catalog_create(Widget parent, const char *const *categories,
    const char *const *controls, const int *membership, TLCatalogChanged changed, void *context);
void tl_catalog_update(TLControlCatalog *catalog, int categories, int controls);
void tl_catalog_read(const TLControlCatalog *catalog, int *categories, int *controls);
void tl_catalog_destroy(TLControlCatalog *catalog);
#endif
