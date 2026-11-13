/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Private experiment, not a shipped adapter. GtkButton's exposed GTK2
 * depressed bit affects both shadow and child allocation; set_state alone
 * does not. Never change in_button/button_down or emit an activation. */
#include <gtk/gtk.h>

int t04_gtk2_demo_depressed(GtkWidget *widget, int enabled);
int t04_gtk2_demo_input_flags(GtkWidget *widget);
int t04_gtk2_demo_input_flags(GtkWidget *widget)
{
    if (!widget || G_OBJECT_TYPE(widget) != GTK_TYPE_BUTTON)
        return -1;
    return (GTK_BUTTON(widget)->in_button ? 1 : 0) |
           (GTK_BUTTON(widget)->button_down ? 2 : 0);
}
int t04_gtk2_demo_depressed(GtkWidget *widget, int enabled)
{
    if (gtk_major_version != GTK_MAJOR_VERSION ||
        gtk_minor_version != GTK_MINOR_VERSION ||
        gtk_micro_version != GTK_MICRO_VERSION ||
        GTK_MAJOR_VERSION != 2 || GTK_MINOR_VERSION != 24 ||
        GTK_MICRO_VERSION != 33)
        return -1;
    if (!widget || G_OBJECT_TYPE(widget) != GTK_TYPE_BUTTON ||
        (enabled != 0 && enabled != 1))
        return -2;
    GTK_BUTTON(widget)->depressed = enabled != 0;
    gtk_widget_set_state(widget, enabled ? GTK_STATE_ACTIVE : GTK_STATE_NORMAL);
    gtk_widget_queue_resize(widget);
    gtk_widget_queue_draw(widget);
    return 0;
}
