/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_PROJECT_SESSION_H
#define TL_PROJECT_SESSION_H
#include "project_history.h"
typedef struct TLProjectSession TLProjectSession;
typedef enum { TL_HISTORY_PUSH,TL_HISTORY_UNDO,TL_HISTORY_REDO,
               TL_HISTORY_MARK,TL_HISTORY_RESTORE,TL_HISTORY_RESET_PART } TLHistoryOperation;
/* Owns validated history and its last committed revision. Never owns widgets.
 * Existing valid history is recovered; otherwise initial creates a new file.
 * Return 1 means committed with a durability warning, 0 durable, -1 unchanged. */
int tl_project_session_open(TLProjectSession **session,const char *path,
                            const TLModel *initial,char *error,size_t capacity);
void tl_project_session_free(TLProjectSession *session);
int tl_project_session_current(const TLProjectSession *session,TLModel *model,
                               char *error,size_t capacity);
int tl_project_session_change(TLProjectSession *session,TLHistoryOperation operation,
                              const TLModel *candidate,TLFamily family,TLScrollPart part,
                              char *error,size_t capacity);
int tl_project_session_can_step(const TLProjectSession *session,int direction);
int tl_project_session_has_point(const TLProjectSession *session);
#endif
