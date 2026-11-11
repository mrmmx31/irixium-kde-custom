/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "control_availability.h"

int tl_control_availability(int index, TLControlAvailability *availability)
{
    if (availability == NULL || index < 0 || index >= TL_CONTROL_COUNT)
        return -1;
    *availability = (TLControlAvailability) {
        .index = index,
        .id = tl_control_ids[index],
        .motif_available = 1,
        .gtk2_available = 1,
        .gtk2_program = "preview_gtk2.py",
        .gtk2_control_option = "--capture-control",
        .gtk2_control_argument = index
    };
    return 0;
}
