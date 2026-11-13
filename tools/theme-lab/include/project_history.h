/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_PROJECT_HISTORY_H
#define TL_PROJECT_HISTORY_H
#include "theme_lab.h"
#include <json-c/json.h>
#define TL_HISTORY_LIMIT 128
#define TL_HISTORY_JSON_LIMIT (32*1024*1024)
typedef struct TLProjectHistory TLProjectHistory;
TLProjectHistory *tl_history_new(const TLModel *initial,char *error,size_t capacity);
void tl_history_free(TLProjectHistory *history);
TLProjectHistory *tl_history_decode(json_object *root,char *error,size_t capacity);
json_object *tl_history_encode(const TLProjectHistory *history);
int tl_history_current(const TLProjectHistory *history,TLModel *model,char *error,size_t capacity);
int tl_history_push(TLProjectHistory *history,const TLModel *model,char *error,size_t capacity);
int tl_history_step(TLProjectHistory *history,int direction,char *error,size_t capacity);
int tl_history_mark(TLProjectHistory *history);
int tl_history_restore(TLProjectHistory *history,char *error,size_t capacity);
int tl_history_reset_part(TLProjectHistory *history,TLFamily family,TLScrollPart part,char *error,size_t capacity);
int tl_history_can_step(const TLProjectHistory *history,int direction);
int tl_history_has_point(const TLProjectHistory *history);
#endif
