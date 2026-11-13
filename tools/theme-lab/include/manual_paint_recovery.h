/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_MANUAL_PAINT_RECOVERY_H
#define TL_MANUAL_PAINT_RECOVERY_H

#include <Xm/Xm.h>
#include "text_editor.h"

/* Present the validation error and an explicit, non-destructive recovery path.
 * Valid documents are copied to a new user-selected file; source is untouched. */
void tl_manual_paint_recovery_error(Widget parent, const char *message,
                                   const char *source,
                                   TLEditorStore *editors);

#endif
