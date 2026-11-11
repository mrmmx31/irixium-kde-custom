#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run only on a private Xvfb; never imports or edits personal projects."""
import copy
import json
import os
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
os.environ['GDK_BACKEND'] = 'x11'
os.environ['NO_AT_BRIDGE'] = '1'
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

spec = importlib.util.spec_from_file_location('preview_metrics', Path(__file__).resolve().parents[1] / 'preview_gtk.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)

class Writer:
    def __init__(self):
        self.events = []
    def emit(self, action, index, project_hash, **fields):
        if action == 'metrics':
            self.events.append(dict(index=index, project_hash=project_hash, **fields))

def drain():
    # Allocation/resize notifications may cross several X11 round trips.
    loop = GLib.MainLoop()
    GLib.timeout_add(100, lambda: (loop.quit(), False)[1])
    loop.run()

class NativeMetrics(unittest.TestCase):
    def test_trailing_anchor_real_widget_edges_both_origins(self):
        outcomes=[]
        for coupled in (False,True):
            host=socket=None
            if coupled:
                host=Gtk.Window();socket=Gtk.Socket();host.add(socket)
                host.set_default_size(760,450);host.show_all();drain()
            data={'recipes':{'gtk3':{'visible_categories':31,'visible_controls':(1<<10)|(1<<11),
                  'geometry':{'arrow_px':11,'shadow_px':2},'positions':[[16,16] for _ in range(16)],
                  'sizes':[[0,0] for _ in range(16)],'length_anchor':[0]*16}}}
            recipe=data['recipes']['gtk3'];recipe['length_anchor'][10]=recipe['length_anchor'][11]=1
            recipe['positions'][10]=[400,16];recipe['positions'][11]=[16,400]
            args=SimpleNamespace(family='gtk3',embed_window=socket.get_id() if socket else None,
                                 capture_control=None)
            instance=preview.NativeScene(Gtk,Gdk,GLib,args,data,'b'*64,Writer())
            GLib.source_remove(instance.reload_source);del instance.reload_source
            try:
                for request in (260,1,0,180):
                    recipe['sizes'][10]=[request,0];recipe['sizes'][11]=[0,request]
                    instance.build(data)
                    for _ in range(5):drain()
                    for index in (10,11):
                        widget=instance.widgets[index]
                        x,y=widget.translate_coordinates(instance.fixed,0,0)
                        width,height=widget.get_allocated_width(),widget.get_allocated_height()
                        edge=x+width if index==10 else y+height
                        self.assertEqual(edge,400,(coupled,request,index,x,y,width,height))
                        self.assertGreater(width if index==10 else height,1)
                        outcomes.append({'origin':'coupled' if coupled else 'separate',
                                         'request':request,'control':index,'position':[x,y],
                                         'size':[width,height],'trailing_edge':edge})
            finally:
                instance.window.destroy()
                if host:host.destroy()
                drain()
        destination=os.environ.get('TL_NATIVE_ANCHOR_REPORT')
        if destination:Path(destination).write_text(json.dumps({'passed':True,'measurements':outcomes},indent=2)+'\n')

    def test_native_allocation_both_origins_resize_and_stale_callbacks(self):
        data = {'recipes': {'gtk3': {'visible_categories':31, 'visible_controls':65535,
                                    'geometry':{'arrow_px':11, 'shadow_px':2},
                                    'sizes': [[0,0] for _ in range(16)]}}}
        for coupled in (False, True):
            socket = None
            if coupled:
                host = Gtk.Window()
                socket = Gtk.Socket()
                host.add(socket)
                host.set_default_size(760,450)
                host.show_all()
                drain()
            writer = Writer()
            args = SimpleNamespace(family='gtk3', embed_window=socket.get_id() if socket else None,
                                   capture_control=None)
            instance = preview.NativeScene(Gtk,Gdk,GLib,args,data,'a'*64,writer)
            # Tests supply projects directly; production polling is separately tested.
            GLib.source_remove(instance.reload_source)
            del instance.reload_source
            drain()
            samples = preview.SAMPLES
            self.assertEqual(instance.widgets[0].get_label(), samples['push'])
            self.assertEqual(instance.widgets[1].get_label(), samples['toggle'])
            self.assertEqual(instance.widgets[2].get_label(), samples['check'])
            self.assertTrue(instance.widgets[2].get_active())
            self.assertEqual(instance.widgets[3].get_label(), samples['radio'])
            self.assertTrue(instance.widgets[3].get_active())
            listing=instance.widgets[14].get_child()
            if isinstance(listing,Gtk.Viewport):listing=listing.get_child()
            self.assertEqual([row.get_child().get_text() for row in listing.get_children()],
                             [samples[key] for key in ('list_a','list_b','list_c')])
            self.assertEqual(listing.get_selected_row().get_index(),1)
            self.assertIsNone(instance.widgets[15].get_label_widget())
            self.assertEqual(instance.widgets[15].get_child().get_text(),samples['frame'])
            self.assertEqual(instance.widgets[4].get_text(), samples['entry'])
            self.assertEqual(instance.widgets[5].get_active_text(), samples['combo_a'])
            self.assertEqual(instance.widgets[6].get_value(), samples['spin'])
            for index, key in ((8, 'scale_h'), (9, 'scale_v')):
                self.assertEqual(instance.widgets[index].get_value(), samples[key])
            self.assertEqual(instance.widgets[13].get_fraction(), samples['level'] / 100)
            records = {e['index']:e for e in writer.events}
            self.assertEqual(len(records),16)
            for index, event in records.items():
                widget = instance.widgets[index]
                self.assertEqual((event['width'],event['height']),
                                 (widget.get_allocated_width(),widget.get_allocated_height()))
                self.assertEqual(event['origin'],'coupled' if coupled else 'separate')
                self.assertEqual(event['scale_factor'],widget.get_scale_factor())
                self.assertEqual(event['coordinate_space'],'gtk_logical_px')
                self.assertEqual(event['sensitive'],widget.is_sensitive())
                if index in (10,11):
                    self.assertEqual(widget.get_adjustment().get_value(),35)
                    area=widget.get_range_rect();start,end=widget.get_slider_range()
                    self.assertEqual(event['range_geometry'],{
                        'axis':0 if index==10 else 1,'slider_start':start,'slider_end':end,
                        'area_x':area.x,'area_y':area.y,'area_width':area.width,
                        'area_height':area.height,'coordinate_space':'gtk_widget_window_px'})
                    self.assertTrue(instance.parts_reader.available)
                    self.assertIn('pieces_geometry',event)
                    pieces=event['pieces_geometry']
                    self.assertEqual(pieces['source'],preview.parts_module.SOURCE)
                    self.assertEqual(pieces['coordinate_space'],'gtk_widget_local_px')
                    self.assertEqual(pieces,instance.parts_reader.measure(widget))
                    for name in ('slider','track','arrow_first','arrow_last'):
                        if name not in pieces:continue
                        rect=pieces[name]
                        self.assertGreater(rect['width'],0);self.assertGreater(rect['height'],0)
                        self.assertGreaterEqual(rect['x'],0);self.assertGreaterEqual(rect['y'],0)
                        self.assertLessEqual(rect['x']+rect['width'],widget.get_allocated_width())
                        self.assertLessEqual(rect['y']+rect['height'],widget.get_allocated_height())
                else:
                    self.assertNotIn('range_geometry',event)
                    self.assertNotIn('pieces_geometry',event)
                if index in (10,11,12):
                    self.assertEqual(event['font_kind'],2)
                    self.assertEqual(event['font_description'],'')
                else:
                    self.assertEqual(event['font_kind'],1)
                    target=widget
                    if index in (0,1,2,3,7,15):target=widget.get_child()
                    elif index==14:
                        listing=widget.get_child()
                        if isinstance(listing,Gtk.Viewport):listing=listing.get_child()
                        target=listing.get_row_at_index(0).get_child()
                    context=target.get_pango_context()
                    loaded=context.load_font(context.get_font_description())
                    self.assertEqual(event['font_description'],
                                     'Pango contexto de '+target.__class__.__name__+' carregado: '+loaded.describe().to_string())
                offset=widget.translate_coordinates(instance.boxes[index],0,0)
                if offset is not None:
                    self.assertEqual((event['cell_offset_x'],event['cell_offset_y']),offset)
                else:
                    self.assertNotIn('cell_offset_x',event)
                    self.assertNotIn('cell_offset_y',event)
            for index in (10,11):
                range_widget=instance.widgets[index]
                # Automatic short bars may have no free cursor travel. Give
                # this interaction test a measured long allocation first.
                range_widget.set_size_request(220 if index==10 else 15,
                                              15 if index==10 else 220)
                drain()
                instance.measured(range_widget,range_widget.get_allocation(),index)
                old_event=[e for e in writer.events if e['index']==index][-1]
                old_geometry=old_event['range_geometry']
                range_widget.set_value(70)
                drain()
                latest_event=[e for e in writer.events if e['index']==index][-1]
                latest=latest_event['range_geometry']
                self.assertNotEqual(latest_event['pieces_geometry']['slider'],old_event['pieces_geometry']['slider'])
                self.assertNotEqual((latest['slider_start'],latest['slider_end']),
                                    (old_geometry['slider_start'],old_geometry['slider_end']))
                start,end=range_widget.get_slider_range()
                self.assertEqual((latest['slider_start'],latest['slider_end']),(start,end))
                area_start=latest['area_y'] if index==11 else latest['area_x']
                area_length=latest['area_height'] if index==11 else latest['area_width']
                self.assertGreaterEqual(start,area_start)
                self.assertLessEqual(end,area_start+area_length)
            # Unsupported binary/version disables internal reads but preserves public metrics.
            original_verified=preview.parts_module.verified_runtime
            try:
                preview.parts_module.verified_runtime=lambda _:False
                fallback=preview.parts_module.Reader(Gtk)
                self.assertFalse(fallback.available)
                self.assertIsNone(fallback.measure(instance.widgets[10]))
            finally:preview.parts_module.verified_runtime=original_verified
            self.assertIsNone(instance.parts_reader.measure(instance.widgets[0]))
            # A child may override its parent's font; measure the text child,
            # not an unrelated container's requested font.
            from gi.repository import Pango
            label=instance.widgets[0].get_child()
            label.override_font(Pango.FontDescription.from_string('Monospace 18'))
            drain()
            instance.measured(instance.widgets[0],instance.widgets[0].get_allocation(),0)
            measured=[e for e in writer.events if e['index']==0][-1]
            self.assertIn('Label carregado:',measured['font_description'])
            self.assertIn('18',measured['font_description'])
            widget = instance.widgets[0]
            before = len(writer.events)
            instance.measured(widget,widget.get_allocation(),0)
            self.assertEqual(len(writer.events),before)
            changed = copy.deepcopy(data)
            changed['recipes']['gtk3']['sizes'][0] = [220,80]
            instance.project_hash = 'b'*64
            instance.build(changed)
            # map callbacks can publish valid new-scene metrics synchronously.
            before_stale = len(writer.events)
            instance.measured(widget,widget.get_allocation(),0)
            self.assertEqual(len(writer.events),before_stale)  # old-scene control rejected
            drain()
            event = [e for e in writer.events if e['index']==0][-1]
            self.assertEqual((event['width'],event['height']),(220,80))
            self.assertEqual(event['project_hash'],'b'*64)
            old=instance.widgets[0]
            old_allocation=old.get_allocation()
            old.connect('destroy',lambda current:self.assertIsNone(
                instance.measured(current,old_allocation,0)))
            replacement=copy.deepcopy(changed)
            replacement['recipes']['gtk3']['sizes'][0]=[240,90]
            instance.project_hash='c'*64
            instance.build(replacement)
            drain()
            records=[e for e in writer.events if e['project_hash']=='c'*64 and e['index']==0]
            self.assertTrue(records)
            self.assertFalse(any((e['width'],e['height'])==(220,80) for e in records))
            instance.window.destroy()
            if socket:
                host.destroy()

if __name__ == '__main__':
    unittest.main()
