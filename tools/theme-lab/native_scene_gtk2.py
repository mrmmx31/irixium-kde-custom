# SPDX-License-Identifier: GPL-3.0-or-later
"""Partial GTK2 scene for controls admitted by the current recipe.

The caller owns private-display guards and palette loading. This module does
not import GTK3, modify a project or silently replace an unsupported control.
It does not claim a complete GTK2 theme or historical visual fidelity.
"""
from scene_contract import scene, integer
import re
from sample_contract import SAMPLES
from gtk2_canvas import canvas_sensitivity
from control_hints import bind_control_hint


def scene_records(model, allow_button_pressed=False):
    records = scene(model, 'gtk2')
    unsupported=[item['id'] for item in records
                 if item['id'] not in ('push', 'toggle', 'check', 'radio', 'entry', 'text', 'combo', 'spin', 'scale_h', 'scale_v', 'arrow', 'progress', 'scroll_h', 'scroll_v', 'list', 'frame')]
    if unsupported:
        raise ValueError('GTK2: cena parcial; controles ainda pendentes: '+', '.join(unsupported)+'.')
    if any(item['forced_state'] == 1 and
           (not allow_button_pressed or item['id'] not in ('push', 'arrow')) for item in records):
        raise ValueError('GTK2: demonstração forçada de pressão pendente; use interação nativa.')
    return records


class ScrollbarScene:
    def __init__(self, Gtk, model, embed_window=None, writer=None, project_hash=None, Gdk=None, show=True, progress_style_id=None, entry_style_id=None, text_histories=None, text_style_id=None, combo_style_id=None, combo_popup_color=None, spin_style_id=None, scale_style_id=None, arrow_style_id=None, list_style_id=None, frame_style_id=None, press_bridge=None, trace_input=False, capture_mode=False, capture_probe=None):
        self.Gtk = Gtk
        self.writer, self.project_hash = writer, project_hash
        records = scene_records(model, allow_button_pressed=press_bridge is not None)
        if any(r['id']=='progress' for r in records) and (not isinstance(progress_style_id,str) or not re.fullmatch('[0-9a-f]{16}',progress_style_id)):
            raise ValueError('GTK2: identidade do estilo gerado de progresso ausente ou inválida.')
        if any(r['id']=='entry' for r in records) and (Gdk is None or not isinstance(entry_style_id,str) or not re.fullmatch('[0-9a-f]{16}',entry_style_id)):
            raise ValueError('GTK2: identidade do estilo de entrada ou Gdk ausente ou inválida.')
        if any(r['id']=='text' for r in records) and (Gdk is None or not isinstance(text_style_id,str) or not re.fullmatch('[0-9a-f]{16}',text_style_id)):
            raise ValueError('GTK2: identidade do estilo multilinha ou Gdk ausente ou inválida.')
        if any(r['id']=='combo' for r in records) and (Gdk is None or not isinstance(combo_style_id,str) or not re.fullmatch('[0-9a-f]{16}',combo_style_id) or not isinstance(combo_popup_color,str) or not re.fullmatch('#[0-9a-fA-F]{6}',combo_popup_color)):
            raise ValueError('GTK2: identidade do estilo combobox/papel Header ou Gdk ausente ou inválido.')
        if any(r['id']=='spin' for r in records) and (Gdk is None or not isinstance(spin_style_id,str) or not re.fullmatch('[0-9a-f]{16}',spin_style_id)):
            raise ValueError('GTK2: identidade do estilo spin ausente ou inválida.')
        if any(r['id'] in ('scale_h','scale_v') for r in records) and (Gdk is None or not isinstance(scale_style_id,str) or not re.fullmatch('[0-9a-f]{16}',scale_style_id)):
            raise ValueError('GTK2: identidade do estilo escala ausente ou inválida.')
        if any(r['id']=='arrow' for r in records) and (Gdk is None or not isinstance(arrow_style_id,str) or not re.fullmatch('[0-9a-f]{16}',arrow_style_id)):
            raise ValueError('GTK2: identidade do estilo seta isolada ausente ou inválida.')
        if any(r['id']=='list' for r in records) and (Gdk is None or not isinstance(list_style_id,str) or not re.fullmatch('[0-9a-f]{16}',list_style_id)):
            raise ValueError('GTK2: identidade do estilo lista ausente ou inválida.')
        if any(r['id']=='frame' for r in records) and (Gdk is None or not isinstance(frame_style_id,str) or not re.fullmatch('[0-9a-f]{16}',frame_style_id)):
            raise ValueError('GTK2: identidade do estilo moldura ausente ou inválida.')
        self.frame_controls = {}
        self.list_controls = {}
        self.text_histories = text_histories if text_histories is not None else {}
        self.text_editors = {}
        self.capture_mode = capture_mode
        self.window = (Gtk.OffscreenWindow() if capture_mode else
                       Gtk.Plug.new(embed_window) if embed_window is not None else Gtk.Window())
        self.window.set_name('themeLabCanvasWindow')
        self.window.set_title('Theme Lab — GTK2 nativo')
        if capture_mode:
            self.window.set_default_size(1, 1)
        else:
            self.window.set_default_size(640, 420)
        self.fixed = Gtk.Fixed()
        self.fixed.set_name('themeLabCanvas')
        self.window.add(self.fixed)
        canvas_sensitivity(self.window)
        self.window.connect('notify::sensitive', canvas_sensitivity)
        self.widgets, self.records, self.natural = {}, {}, {}
        self.input_trace = None
        self.radio_groups = {}
        self.combo_widgets = {}
        self.progress_widgets = {}
        self.progress_values = {}
        for record in records:
            if record['id'] in ('push','toggle'):
                toggle = record['id'] == 'toggle'
                widget = (Gtk.ToggleButton if toggle else Gtk.Button)(label=SAMPLES[record['id']])
                widget.set_name('themeLabToggle' if toggle else 'themeLabPush')
                widget.connect('toggled' if toggle else 'clicked',
                               self.toggle_changed if toggle else self.button_clicked, record['index'])
            elif record['id']=='radio':
                from radio_group_gtk2 import RadioGroup
                group=RadioGroup(Gtk,record['forced_state']==3)
                self.radio_groups[record['index']]=group
                widget=group.widget
                for member in group.members:
                    member.connect('toggled',self.radio_changed,record['index'])
            elif record['id']=='entry':
                from gi.repository import GLib
                from preview_text_editing import bind
                widget=Gtk.Entry()
                widget.set_name('themeLabEntry_'+entry_style_id)
                widget.set_text(SAMPLES['entry'])
                editor=bind(widget,Gtk,Gdk,GLib,self.text_histories.get(record['index']))
                self.text_editors[record['index']]=editor
                self.text_histories[record['index']]=editor.history
            elif record['id']=='spin':
                from gi.repository import GLib
                from preview_text_editing import bind
                prefix='themeLabInsensitiveSpin' if record['forced_state']==2 else 'themeLabBackdropSpin' if record['forced_state']==3 else 'themeLabSpin'
                widget=Gtk.SpinButton.new_with_range(0,100,1)
                widget.set_name(prefix+'_'+spin_style_id)
                widget.set_value(SAMPLES['spin'])
                editor=bind(widget,Gtk,Gdk,GLib,self.text_histories.get(record['index']))
                self.text_editors[record['index']]=editor
                self.text_histories[record['index']]=editor.history
                widget.connect('value-changed',self.native_changed,record['index'])
            elif record['id']=='text':
                from gi.repository import GLib
                from preview_text_editing import bind
                from gtk2_buttons import geometry
                prefix='themeLabInsensitiveText' if record['forced_state']==2 else 'themeLabBackdropText' if record['forced_state']==3 else 'themeLabText'
                widget=Gtk.ScrolledWindow()
                widget.set_name(prefix+'Viewport_'+text_style_id)
                widget.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)
                widget.set_shadow_type(Gtk.ShadowType.IN)
                text=Gtk.TextView()
                text.set_name(prefix+'Editor_'+text_style_id)
                # The Motif reference configures XmText with XmNwordWrap=True.
                # Apply GTK wrapping before inserting text so its initial layout
                # and the scrolled-window adjustments use the same behavior.
                text.set_wrap_mode(Gtk.WrapMode.WORD)
                text.set_sensitive(record['forced_state']!=2)
                # GtkTextView margins are instance properties, not GTK2 RC
                # theme properties. Keep the real GTK2 defaults in the native
                # theme preview instead of simulating an application setting.
                text.get_buffer().set_text(SAMPLES['text'])
                editor=bind(text,Gtk,Gdk,GLib,self.text_histories.get(record['index']))
                self.text_editors[record['index']]=editor
                self.text_histories[record['index']]=editor.history
                bind_control_hint(text,'text','gtk2')
                widget.add(text)
            elif record['id']=='frame':
                from frame_control_gtk2 import FrameControl
                prefix='themeLabInsensitiveFrame' if record['forced_state']==2 else 'themeLabBackdropFrame' if record['forced_state']==3 else 'themeLabFrame'
                frame=FrameControl(Gtk,model['recipes']['gtk2'],prefix,frame_style_id,record['forced_state']!=2)
                self.frame_controls[record['index']]=frame
                widget=frame.widget
            elif record['id']=='list':
                from list_control_gtk2 import ListControl
                prefix='themeLabInsensitiveList' if record['forced_state']==2 else 'themeLabBackdropList' if record['forced_state']==3 else 'themeLabList'
                listing=ListControl(Gtk,prefix,list_style_id,record['forced_state']!=2)
                self.list_controls[record['index']]=listing
                widget=listing.widget
                listing.view.get_selection().connect('changed',self.list_changed,record['index'])
                bind_control_hint(listing.view,'list','gtk2')
            elif record['id']=='combo':
                from combo_popup_gtk2 import bind_popup
                prefix='themeLabInsensitiveCombo' if record['forced_state']==2 else 'themeLabBackdropCombo' if record['forced_state']==3 else 'themeLabCombo'
                widget=Gtk.ComboBoxText.new()
                widget.set_name(prefix+'_'+combo_style_id)
                for item in (SAMPLES['combo_a'],SAMPLES['combo_b'],SAMPLES['combo_c']):
                    widget.append_text(item)
                widget.set_active(0)
                bind_popup(Gtk,Gdk,widget,prefix,combo_style_id,combo_popup_color)
                widget.connect('changed',self.combo_changed,record['index'])
                from combo_input_gtk2 import enclose
                self.combo_widgets[record['index']]=widget
                widget=enclose(Gtk,Gdk,widget)
                widget.set_name(prefix+'_'+combo_style_id)
            elif record['id'] in ('scale_h','scale_v'):
                prefix='themeLabInsensitiveScale' if record['forced_state']==2 else 'themeLabBackdropScale' if record['forced_state']==3 else 'themeLabScale'
                widget=(Gtk.HScale if record['id']=='scale_h' else Gtk.VScale).new_with_range(0,100,1)
                # XmScale in the paired Motif reference shows its current value.
                # Keep the comparison scene semantically equivalent.
                widget.set_draw_value(True)
                widget.set_name(prefix+'_'+scale_style_id)
                widget.set_value(SAMPLES[record['id']])
                widget.get_adjustment().connect('value-changed',self.native_changed,record['index'])
            elif record['id']=='arrow':
                from gtk2_arrows import glyph_geometry
                prefix='themeLabInsensitiveArrow' if record['forced_state']==2 else 'themeLabBackdropArrow' if record['forced_state']==3 else 'themeLabArrow'
                widget=Gtk.Button()
                widget.set_name(prefix+'_'+arrow_style_id)
                child=Gtk.Arrow(arrow_type=Gtk.ArrowType.DOWN,shadow_type=Gtk.ShadowType.OUT)
                glyph=glyph_geometry(model['recipes']['gtk2'])['arrow_px']
                child.set_size_request(glyph,glyph)
                widget.add(child)
                child.show()  # Include the native glyph in the pre-custom requisition.
                widget.connect('clicked',self.button_clicked,record['index'])
            elif record['id']=='progress':
                # Motif's local level sample puts its value above the scale.
                # Keep GTK's native ProgressBar, but place the sample value in
                # a sibling label instead of painting it inside the trough.
                widget=Gtk.VBox()
                widget.set_homogeneous(False)
                widget.set_spacing(0)
                value=Gtk.Label()
                value.set_text(str(SAMPLES['level'])+'%')
                value_prefix='themeLabInsensitiveProgressValue' if record['forced_state']==2 else 'themeLabBackdropProgressValue' if record['forced_state']==3 else 'themeLabProgressValue'
                bar_prefix='themeLabInsensitiveProgress' if record['forced_state']==2 else 'themeLabBackdropProgress' if record['forced_state']==3 else 'themeLabProgress'
                value.set_name(value_prefix+'_'+progress_style_id)
                value.set_alignment(0.5,0.5)
                value.show()
                progress=Gtk.ProgressBar()
                progress.set_name(bar_prefix+'_'+progress_style_id)
                progress.set_fraction(SAMPLES['level']/100.0)
                progress.set_show_text(False)
                progress.show()
                widget.pack_start(value,False,False,0)
                widget.pack_start(progress,True,True,0)
                self.progress_widgets[record['index']]=progress
                self.progress_values[record['index']]=value
            elif record['id']=='check':
                widget=Gtk.CheckButton(label=SAMPLES['check'])
                widget.set_name('themeLabCheck')
                widget.connect('toggled',self.toggle_changed,record['index'])
            else:
                probe = capture_probe if capture_mode and record['id'] in ('scroll_h', 'scroll_v') else None
                value = probe['value'] if probe is not None else SAMPLES['scroll']
                page_size = probe['page_size'] if probe is not None else SAMPLES['page_size']
                adjustment = Gtk.Adjustment(value=value, lower=0, upper=100,
                                           step_increment=1, page_increment=10,
                                           page_size=page_size)
                widget = (Gtk.HScrollbar if record['id'] == 'scroll_h' else Gtk.VScrollbar)(adjustment=adjustment)
            state = record['forced_state']
            if state == 2:
                if record['id']=='progress': widget.set_name('themeLabInsensitiveProgress_'+progress_style_id)
                if record['id']=='entry': widget.set_name('themeLabInsensitiveEntry_'+entry_style_id)
                if record['id'] in ('scroll_h','scroll_v'): widget.set_name('themeLabInsensitiveScroll')
                widget.set_sensitive(False)
            elif state == 3:
                if record['id'] not in ('radio','text','combo','spin','scale_h','scale_v','arrow','list','frame'):
                    widget.set_name(({'push':'themeLabBackdropPush','toggle':'themeLabBackdropToggle','check':'themeLabBackdropCheck','entry':'themeLabBackdropEntry','progress':'themeLabBackdropProgress'}.get(record['id'],'themeLabBackdropScroll'))+('_'+progress_style_id if record['id']=='progress' else '_'+entry_style_id if record['id']=='entry' else ''))
            bind_control_hint(widget,record['id'],'gtk2')
            self.fixed.put(widget, record['x'], record['y'])
            widget.ensure_style()
            natural = Gtk.Requisition()
            widget.size_request(natural)
            self.natural[record['index']] = [natural.width, natural.height]
            widget.set_size_request(record['width'] or -1, record['height'] or -1)
            if record['length_anchor']:
                from gtk2_anchor_geometry import requested_origin
                try:
                    self.fixed.move(widget, *requested_origin(record, self.natural[record['index']]))
                except (ValueError, TypeError):
                    self.window.destroy()
                    raise
            self.widgets[record['index']] = widget
            self.records[record['index']] = record
            if record['id'] in ('scroll_h','scroll_v'): adjustment.connect('value-changed', self.native_changed, record['index'])
        if trace_input:
            from gtk2_input_trace import Gtk2InputTrace
            self.input_trace = Gtk2InputTrace(self.widgets, self.records, writer.directory)
        self.press_demos = {}
        try:
            for index, record in self.records.items():
                if record['forced_state'] == 1:
                    from gtk2_pressed_state import PressedButtonDemo
                    self.press_demos[index] = PressedButtonDemo(
                        self.widgets[index], press_bridge.bind(self.widgets[index]))
        except Exception:
            self.window.destroy()
            raise
        from gi.repository import GLib
        if capture_mode:
            if len(records) != 1:
                self.window.destroy()
                raise ValueError('Captura GTK2 requer exatamente um controle visível.')
            record = records[0]
            natural = Gtk.Requisition()
            self.widgets[record['index']].size_request(natural)
            width = record['width'] or natural.width
            height = record['height'] or natural.height
            if width < 1 or height < 1:
                self.window.destroy()
                raise ValueError('GTK2 não mediu uma dimensão válida para a captura.')
            self.fixed.set_size_request(width, height)
            self.window.set_default_size(width, height)
        from gtk2_placement import Placement
        self.placement = Placement(self, GLib)
        if Gdk is not None:
            from gestures_gtk2 import LayoutGestures
            self.gestures = LayoutGestures(self, Gdk)
        if show:
            self.window.show_all()
            self.restore_spin_fields()

    def restore_spin_fields(self):
        # GTK2 realizes SpinButton with formatted committed value. Restore the
        # separately saved partial field after mapping, before idle recording.
        for editor in self.text_editors.values():
            if isinstance(editor.widget, self.Gtk.SpinButton):
                editor.restore(editor.history.states[editor.history.position])

    def emit(self, action, index, **fields):
        if self.writer is not None:
            self.writer.emit(action, index, self.project_hash, **fields)

    def native_changed(self, adjustment, index):
        try:
            self.emit('native', index, state={'value': adjustment.get_value()})
        except (OSError, ValueError) as error:
            self.last_error = str(error)
            self.window.set_title('Evento GTK2 não salvo: ' + self.last_error[:160])

    def button_clicked(self, widget, index):
        try:
            self.emit('native', index, state={'clicked': True})
        except (OSError, ValueError) as error:
            self.last_error = str(error)
            self.window.set_title('Evento GTK2 não salvo: ' + self.last_error[:160])

    def list_changed(self, selection, index):
        try:
            _model,paths=selection.get_selected_rows()
            self.emit('native',index,state={'selected_rows':[p.to_string() for p in paths]})
        except (OSError,ValueError) as error:
            self.last_error=str(error)
            self.window.set_title('Evento GTK2 não salvo: '+self.last_error[:160])

    def combo_changed(self, widget, index):
        try:
            self.emit('native',index,state={'active_index':widget.get_active()},
                      origin='coupled' if isinstance(self.window,self.Gtk.Plug) else 'separate')
        except (OSError,ValueError) as error:
            self.last_error=str(error)
            self.window.set_title('Evento GTK2 não salvo: '+self.last_error[:160])

    def toggle_changed(self, widget, index):
        try:
            self.emit('native',index,state={'active':bool(widget.get_active())},
                      origin='coupled' if isinstance(self.window,self.Gtk.Plug) else 'separate')
        except (OSError,ValueError) as error:
            self.last_error=str(error)
            self.window.set_title('Evento GTK2 não salvo: '+self.last_error[:160])

    def select_control(self, index):
        if index not in self.widgets:
            raise ValueError('Controle não montado na cena GTK2.')
        self.emit('select', index)

    def radio_changed(self, widget, index):
        # During GTK's group transition the old member emits first. Publish
        # only the newly selected member, when exclusivity has settled.
        if not widget.get_active(): return
        try:
            self.emit('native',index,state={'selected_member':self.radio_groups[index].selected()},
                      origin='coupled' if isinstance(self.window,self.Gtk.Plug) else 'separate')
        except (OSError,ValueError) as error:
            self.last_error=str(error)
            self.window.set_title('Evento GTK2 não salvo: '+self.last_error[:160])

    def move_control(self, index, x, y):
        if index not in self.widgets:
            raise ValueError('Controle não montado na cena GTK2.')
        integer(x, 0, 2048, 'x')
        integer(y, 0, 2048, 'y')
        self.placement.origin(index, (x, y))
        # Persist the proposed event before moving the private scene; a failed
        # write must not leave the controller unaware of an applied movement.
        self.emit('move', index, x=x, y=y, coordinate_space='gtk_logical_px')
        self.records[index] = dict(self.records[index], x=x, y=y)
        self.placement.reset(index)

    def emit_metrics(self):
        for item in self.metrics():
            x, y, width, height = item['allocation']
            natural_width, natural_height = item['native_request_before_custom_size']
            if width < 1 or height < 1 or not self.widgets[item['index']].get_realized():
                continue
            widget = self.widgets[item['index']]
            extra = {}
            if item['id'] in ('scroll_h','scroll_v'):
                area = widget.get_range_rect()
                start, end = item['slider_range']
                measured = {'axis':item['index']-10,'slider_start':start,'slider_end':end,
                    'area_x':area.x,'area_y':area.y,'area_width':area.width,'area_height':area.height,
                    'coordinate_space':'gtk_widget_window_px'}
                area_start = area.x if item['index']==10 else area.y
                area_length = area.width if item['index']==10 else area.height
                if (area.x >= 0 and area.y >= 0 and area.width > 0 and area.height > 0
                        and area_start <= start < end <= area_start + area_length):
                    extra['range_geometry'] = measured
                else:
                    # Below natural requisition GtkRange can report a thumb
                    # outside its area. Preserve that measurement separately;
                    # it must not invalidate the real allocation/position or
                    # masquerade as a usable range rectangle in the C parser.
                    extra['range_geometry_unavailable'] = measured
            self.emit('metrics', item['index'], width=width, height=height,
                      minimum_width=natural_width, minimum_height=natural_height,
                      natural_width=natural_width, natural_height=natural_height,
                      scale_factor=1, origin=item['origin'], coordinate_space='gtk_logical_px',
                      position_x=x, position_y=y, cell_offset_x=0, cell_offset_y=0,
                      sensitive=item['sensitive'], font_kind=2 if item['font_not_applicable'] else 1,
                      font_description=item['font_description'], **extra)

    def metrics(self):
        result = []
        for index, widget in self.widgets.items():
            allocation = widget.get_allocation()
            record = self.records[index]
            result.append({'id': record['id'], 'index': index,
                           'allocation': [allocation.x, allocation.y, allocation.width, allocation.height],
                           'requested_size': [record['width'], record['height']],
                           'native_request_before_custom_size': self.natural[index],
                           'slider_range': list(widget.get_slider_range()) if index in (8,9,10,11) else None,
                           'sensitive': widget.get_sensitive(), 'widget_name': widget.get_name(),
                           'value': widget.get_adjustment().get_value() if index in (8,9,10,11) else None,
                           'active':bool(widget.get_active()) if index in (1,2) else None,
                           'fraction':self.progress_widgets[index].get_fraction() if index==13 else None, 'scale_factor': 1,
                           'origin': 'coupled' if isinstance(self.window, self.Gtk.Plug) else 'separate',
                           'coordinate_space': 'gtk_logical_px', 'font_not_applicable': index not in (0,1,2,3,4,5,6,7,8,9,13,14,15),
                           'font_description': (self.radio_groups[index].members[0] if index==3 else self.list_controls[index].view if index==14 else self.frame_controls[index].label if index==15 else self.progress_widgets[index] if index==13 else widget).get_pango_context().get_font_description().to_string() if index in (0,1,2,3,4,5,6,7,8,9,13,14,15) else '',
                           'group_members':self.radio_groups[index].metrics() if index==3 else None,
                           'selected_member':self.radio_groups[index].selected() if index==3 else None})
        return result
