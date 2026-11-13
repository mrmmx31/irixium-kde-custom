/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_CONTROL_DIMENSIONS_H
#define TL_CONTROL_DIMENSIONS_H
#include "theme_lab.h"
/* Catalog identities, not historical Motif defaults. */
enum { TL_CONTROL_SCROLL_HORIZONTAL = 10, TL_CONTROL_SCROLL_VERTICAL = 11 };
/* -1: two editable axes; 0/1: longitudinal axis, opposite axis locked. */
int tl_control_long_axis(int control);
/* Transactional editor operation. Import preserves older explicit dimensions.
   Editing length must retain the existing transverse request, including 0
   (native automatic). Native minimum/allocation remain separately measured. */
int tl_control_edit_dimensions(TLRecipe *recipe, int control, int width, int height);
/* Positions store the chosen boundary, not a guessed native length. Switching
   anchor preserves current native origin; resizing retains that boundary. */
int tl_control_anchor_origin(const TLRecipe *recipe, int control,
                             int native_width, int native_height, int origin[2]);
int tl_control_set_anchor(TLRecipe *recipe, int control, int anchor, int native_length);
#endif
