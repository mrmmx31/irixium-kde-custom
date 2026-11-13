# SPDX-License-Identifier: GPL-3.0-or-later
"""Input-only EventBox separates Ctrl layout gestures from GTK2 combo input.

The combo owns its native menu, selected item, keyboard and scroll algorithm.
Public focus-child access cannot precede GTK2's own connected input handler.
No private widget pointers or replacement menu are used.
"""
def enclose(Gtk, Gdk, combo):
    box = Gtk.EventBox()
    box.set_visible_window(False)
    box.set_above_child(True)
    box.add(combo)

    def native_event(event, kind, fields):
        # GTK2 GI callbacks expose EventButton/EventScroll; signals require
        # the enclosing public Gdk.Event union rather than those records.
        copied = Gdk.Event.new(event.type)
        record = getattr(copied, kind)
        for field in fields:
            value = getattr(event, field)
            # Gdk2 GIR declares direction as a plain C integer.
            setattr(record, field, int(value) if field == 'direction' else value)
        return copied

    def failure(error):
        message = 'Entrada GTK2 não aplicada: ' + str(error)[:160]
        box.set_tooltip_text(message)
        combo.set_tooltip_text(message)
        return True

    def press(_box, event):
        if int(event.state) & int(Gdk.ModifierType.CONTROL_MASK):
            return False
        if event.button == 1:
            try:
                combo.grab_focus()
                button = combo.get_focus_child()
                if button is None:
                    raise ValueError('botão nativo indisponível')
                # Let GTK2's native handler manage pressed state and the
                # opening release; popup() alone closes on that release.
                copied = native_event(event, 'button',
                    ('window','send_event','time','x','y','x_root','y_root','state','button','device'))
                return bool(button.emit('button-press-event', copied))
            except (ValueError, TypeError, RuntimeError, AttributeError) as error:
                return failure(error)
        return False

    def scroll(_box, event):
        if int(event.state) & int(Gdk.ModifierType.CONTROL_MASK):
            return False
        try:
            copied = native_event(event, 'scroll',
                ('window','send_event','time','x','y','x_root','y_root','state','direction'))
            return bool(combo.emit('scroll-event', copied))
        except (ValueError, TypeError, RuntimeError, AttributeError) as error:
            return failure(error)

    box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.SCROLL_MASK)
    box.connect('button-press-event', press)
    box.connect('scroll-event', scroll)
    return box
