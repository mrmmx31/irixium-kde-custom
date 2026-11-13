/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "control_availability.h"
#include <stdio.h>

int main(void)
{
    TLControlAvailability item;
    for (int index = 0; index < TL_CONTROL_COUNT; ++index) {
        if (tl_control_availability(index, &item) != 0 ||
            item.id != tl_control_ids[index] || item.index != index ||
            item.gtk2_control_argument != index)
            return 2;
        printf("%d\t%s\t%d\t%d\t%s\t%s\t%d\n", item.index, item.id,
               item.motif_available, item.gtk2_available, item.gtk2_program,
               item.gtk2_control_option, item.gtk2_control_argument);
    }
    if (tl_control_availability(-1, &item) == 0 ||
        tl_control_availability(TL_CONTROL_COUNT, &item) == 0 ||
        tl_control_availability(0, NULL) == 0)
        return 3;
    return 0;
}
