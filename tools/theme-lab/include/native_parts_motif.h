/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_NATIVE_PARTS_MOTIF_H
#define TL_NATIVE_PARTS_MOTIF_H
#include <X11/Intrinsic.h>
#include "native_metrics.h"
/* Read-only, version-specific diagnostic; unavailable is explicit. Never
 * treats installed Motif geometry as SR10.4 defaults or painted silhouettes. */
void tl_motif_parts_measure(Widget widget, TLNativePieces *pieces);
#endif
