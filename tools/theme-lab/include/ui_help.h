/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_UI_HELP_H
#define TL_UI_HELP_H
#include <Xm/Xm.h>
typedef struct TLHelp TLHelp;
TLHelp *tl_help_create(Widget parent,Widget shell);
Widget tl_help_menu(TLHelp *help);
Widget tl_help_dialog(TLHelp *help);
Widget tl_help_popup(TLHelp *help);
void tl_help_destroy(TLHelp *help);
#endif
