/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef THEME_LAB_GTK2_PRESS_H
#define THEME_LAB_GTK2_PRESS_H
#include <gtk/gtk.h>
int theme_lab_gtk2_press_abi(void);
int theme_lab_gtk2_press_set(GtkWidget *widget, int enabled);
int theme_lab_gtk2_press_input_flags(GtkWidget *widget);
#endif
