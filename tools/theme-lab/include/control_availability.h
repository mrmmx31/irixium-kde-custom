/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_CONTROL_AVAILABILITY_H
#define TL_CONTROL_AVAILABILITY_H

#include "theme_lab.h"

/*
 * One index space is shared by the model, the Motif catalog and native
 * preview capture.  The identifier is always borrowed from tl_control_ids;
 * this API deliberately owns no second list of control names.
 */
typedef struct {
    int index;
    const char *id;
    int motif_available;
    int gtk2_available;
    const char *gtk2_program;
    const char *gtk2_control_option;
    int gtk2_control_argument;
} TLControlAvailability;

int tl_control_availability(int index, TLControlAvailability *availability);

#endif
