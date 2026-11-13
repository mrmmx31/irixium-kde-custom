/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef TL_UI_HINTS_H
#define TL_UI_HINTS_H
#include <Xm/Xm.h>
/* Primitive tips use Motif ownership; scoped bridges cover painted arrows
   and editor menus. Input translations and editable history are preserved. */
void tl_ui_hint(Widget widget, const char *text);
void tl_ui_numeric_hint(Widget field, const char *text);
/* Local bridge for arrows painted by the SpinBox manager. */
void tl_ui_spin_hints(Widget spin);
void tl_ui_spin_hints_refresh(Widget tree);
void tl_ui_disabled_hint(Widget owner);
void tl_ui_disabled_spin_hint(Widget spin,Widget source);
/* Hover bridge for interactive drawing surfaces without Motif's primitive tooltip resource. */
void tl_ui_surface_hint(Widget owner,Widget source);
void tl_ui_hints_shell(Widget shell);
void tl_ui_file_dialog_hints(Widget dialog);
void tl_ui_scroll_hints(Widget tree);
/* Attach once, after creating this application's editor menu commands. */
void tl_ui_menu_hints(Widget menu);
void tl_ui_menu_hint_refresh(Widget menu);
const char *tl_ui_action_hint(int index);
const char *tl_ui_geometry_hint(int index);
const char *tl_ui_motif_control_hint(int index);
const char *tl_ui_editor_command_hint(int index);
#endif
