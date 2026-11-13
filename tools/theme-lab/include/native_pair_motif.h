/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_NATIVE_PAIR_MOTIF_H
#define TL_NATIVE_PAIR_MOTIF_H
#include "theme_lab.h"
/* Ephemeral pairing: never writes a recipe. Coordinate spaces are local,
 * GTK logical pixels converted into X11 pixels for the Motif reference. */
int tl_pair_physical_origin(const TLNativeMetrics *sample, int origin[2]);
/* Restores non-selected bars to their independent baseline. Returns 1 when
 * position is paired, 2 when sensitivity also measured, otherwise 0. */
int tl_motif_pair_bars(Widget widgets[TL_CONTROL_COUNT], const TLRecipe *baseline,
                       int selected, const TLNativeMetrics samples[TL_CONTROL_COUNT]);
#endif
