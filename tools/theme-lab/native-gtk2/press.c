/* SPDX-License-Identifier: GPL-3.0-or-later */
/* GTK2 exposes GtkButton's layout bit in its installed headers. No private
 * symbol or guessed offset is used. This bridge is intentionally restricted
 * to the exact inspected runtime; other versions remain unsupported.
 * Color, activation and native input flags are not modified here. */
#include "press.h"

int theme_lab_gtk2_press_abi(void)
{
    return GTK_MAJOR_VERSION == 2 && GTK_MINOR_VERSION == 24 &&
           GTK_MICRO_VERSION == 33 && gtk_major_version == GTK_MAJOR_VERSION &&
           gtk_minor_version == GTK_MINOR_VERSION &&
           gtk_micro_version == GTK_MICRO_VERSION ? 1 : 0;
}

static int check_widget(GtkWidget *widget)
{
    if (!theme_lab_gtk2_press_abi())
        return -1;
    if (!widget || G_OBJECT_TYPE(widget) != GTK_TYPE_BUTTON)
        return -2;
    if (GTK_OBJECT_FLAGS(widget) & GTK_IN_DESTRUCTION)
        return -3;
    return 0;
}

int theme_lab_gtk2_press_input_flags(GtkWidget *widget)
{
    int error = check_widget(widget);
    if (error)
        return error;
    return (GTK_BUTTON(widget)->in_button ? 1 : 0) |
           (GTK_BUTTON(widget)->button_down ? 2 : 0);
}

int theme_lab_gtk2_press_set(GtkWidget *widget, int enabled)
{
    GtkButton *button;
    GtkStateType state;
    gboolean depressed, touchscreen = FALSE;
    int error = check_widget(widget);
    if (error)
        return error;
    if (enabled != 0 && enabled != 1)
        return -4;
    if (enabled && !gtk_widget_get_sensitive(widget))
        return -5;
    button = GTK_BUTTON(widget);
    /* Keyboard activation owns a native timer; do not interfere with it. */
    if (button->activate_timeout)
        return -6;
    depressed = enabled || (button->in_button && button->button_down);
    g_object_get(gtk_widget_get_settings(widget), "gtk-touchscreen-mode",
                 &touchscreen, NULL);
    state = enabled ? GTK_STATE_ACTIVE :
            !gtk_widget_get_sensitive(widget) ? GTK_STATE_INSENSITIVE :
            (!touchscreen && button->in_button &&
             (!button->button_down || !depressed)) ? GTK_STATE_PRELIGHT :
            depressed ? GTK_STATE_ACTIVE : GTK_STATE_NORMAL;
    button->depressed = depressed;
    gtk_widget_set_state(widget, state);
    gtk_widget_queue_resize(widget);
    gtk_widget_queue_draw(widget);
    return 0;
}
