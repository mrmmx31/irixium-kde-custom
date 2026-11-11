/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_PROJECT_HISTORY_STORE_H
#define TL_PROJECT_HISTORY_STORE_H
#include "project_history.h"
/* Load: 0 valid, 1 missing, -1 error. Outputs untouched on error.
 * Commit: 0 durable, 1 committed but directory durability uncertain, -1 unchanged.
 * expected=NULL means the file must not yet exist. Compare under a shared lock.
 * A candidate remains separate from the live history until commit succeeds. */
int tl_history_store_load(const char *path,TLProjectHistory **history,
                          json_object **revision,char *error,size_t capacity);
int tl_history_store_commit(const char *path,const TLProjectHistory *candidate,
                            json_object *expected,json_object **revision,
                            char *error,size_t capacity);
#endif
