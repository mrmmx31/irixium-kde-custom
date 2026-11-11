# SPDX-License-Identifier: GPL-3.0-or-later
"""Private GTK4 worker lifecycle. Entry point establishes guards before init."""
import ctypes as C
import json
import os
from pathlib import Path
import signal
import sys
import time
import uuid
import backend
from gtk4_generation import verify_initial_snapshot, verify_snapshot
from gtk4_push_api import PushAPI, bind
from gtk4_push_session import PushSession
from gtk4_scene_contract import push_records
from gtk4_host import HostBridge
from gtk4_focus import FocusKeys
from preview_event_writer import EventWriter
from gtk4_snapshot_job import SnapshotJob
from scene_contract import scene


class Bounds(C.Structure):
    _fields_=[('x',C.c_float),('y',C.c_float),('width',C.c_float),('height',C.c_float)]


def configure_display_backend(embed_window):
    """An embedded GTK4 surface must belong to the X11 server of its canvas."""
    if embed_window:
        os.environ['GDK_BACKEND']='x11'


def wait_window_xid(window, native_surface, surface_xid, context_iteration,
                    timeout=1.0, clock=time.monotonic, sleeper=time.sleep):
    """Wait for GTK4 to publish its X11 surface before the host attaches it."""
    deadline=clock()+timeout
    while True:
        surface=native_surface(window)
        window_id=surface_xid(surface) if surface else 0
        if type(window_id) is int and 1<=window_id<=0xffffffff:
            return window_id
        if clock()>=deadline:
            raise RuntimeError('GTK4 X11 surface did not become ready for embedding')
        for _pending in range(64):
            if not context_iteration(None,0):break
        sleeper(0.005)


def publish_pending_x11_state(context_iteration, display_flush, display):
    """Dispatch GTK work and make its X11 requests visible to the host connection."""
    for _pending in range(64):
        if not context_iteration(None,0):
            break
    display_flush(display)


def capture_capabilities(control):
    """Select the one native renderer that owns a manual-paint capture."""
    if control is None:
        return None
    if type(control) is not int or control not in (0, 1, 2, 10, 11):
        raise ValueError('GTK4 sample unavailable: control is not translated')
    return {
        'renderer': 'scrollbar' if control in (10, 11) else 'buttons',
        'allow_toggle': control == 1,
        'allow_check': control == 2,
        'allow_scrollbar': control in (10, 11),
    }


def capture_scrollbar_probe(args, control):
    """Normalize private scrollbar dimensions/range without editing the project."""
    if control not in (10, 11):
        return None
    length = getattr(args, 'capture_length', 0)
    thickness = getattr(args, 'capture_thickness', 0)
    value = getattr(args, 'capture_value', 25)
    page_size = getattr(args, 'capture_page_size', 25)
    part = getattr(args, 'capture_part', 'whole')
    direction = getattr(args, 'capture_direction', 'auto')
    if (type(length) is not int or type(thickness) is not int or
            type(value) is not int or type(page_size) is not int):
        raise ValueError('GTK4 scrollbar capture geometry and range must be integers')
    if (length and not 15 <= length <= 2048) or (
            thickness and not 1 <= thickness <= 512):
        raise ValueError('GTK4 scrollbar capture size is outside the private limits')
    if not 1 <= page_size <= 100 or not 0 <= value <= 100 - page_size:
        raise ValueError('GTK4 scrollbar capture value must fit its 0..100 page range')
    if part != 'whole' or direction != 'auto':
        raise backend.Unavailable(
            'GTK4 GtkScrollbar captures only whole/auto; it has no native arrows '
            'and this worker does not simulate or crop a scrollbar part.')
    size = ([length, thickness] if control == 10
            else [thickness, length])
    return {'size': size, 'value': value, 'page_size': page_size,
            'part': part, 'direction': direction}


def validate_preview_renderer(model, allow_toggle, allow_check, allow_scrollbar):
    """Keep every worker entry path consistent with the explicit route."""
    if any(type(value) is not bool for value in
           (allow_toggle, allow_check, allow_scrollbar)):
        raise ValueError('GTK4 worker capabilities must be explicit booleans')
    if allow_scrollbar and (allow_toggle or allow_check):
        raise ValueError('GTK4 scrollbar and button preview capabilities are mutually exclusive')
    from gtk4_route import renderer
    mode = renderer(model)
    visible = {record['id'] for record in scene(model, 'gtk4')}
    expected = {
        'toggle': mode == 'buttons' and 'toggle' in visible,
        'check': mode == 'buttons' and 'check' in visible,
        'scrollbar': mode == 'scrollbar',
    }
    actual = {'toggle': allow_toggle, 'check': allow_check,
              'scrollbar': allow_scrollbar}
    if actual != expected:
        raise backend.Unavailable(
            'GTK4 worker capability mismatch; relaunch through gtk4_route '
            f'(expected {expected}, received {actual}).')
    return mode


class Worker:
    def __init__(self, args, guards):
        self.args, self.guards = args, guards
        self.root = args.root.resolve()
        self.allow_toggle = bool(getattr(args,'private_toggle_session',False))
        self.allow_check = bool(getattr(args,'private_check_session',False))
        self.allow_scrollbar = bool(getattr(args,'private_scrollbar_session',False))
        self.capture_control = getattr(args, 'capture_control', None)
        self.capture_state = getattr(args, 'capture_state', 0)
        self.capture_output = getattr(args, 'capture_output', None)
        capture = capture_capabilities(self.capture_control)
        self.capture_probe = capture_scrollbar_probe(args, self.capture_control)
        self.capture_probe_effective = None
        if capture is not None:
            # Capture owns an isolated one-control scene. Derive its renderer
            # here as well as in the CLI so direct Worker use cannot render a
            # scrollbar request through the three-button fallback.
            self.allow_toggle = capture['allow_toggle']
            self.allow_check = capture['allow_check']
            self.allow_scrollbar = capture['allow_scrollbar']
        if self.allow_scrollbar and (self.allow_toggle or self.allow_check):
            raise ValueError('GTK4 scrollbar and button preview capabilities are mutually exclusive')
        self.folder = backend.private_output(args.events_dir,self.root)
        self.model, self.digest = backend.project(args.project)
        if self.capture_control is not None:
            from scene_contract import CATEGORIES, CONTROLS
            control = self.capture_control
            recipe = self.model['recipes']['gtk4']
            recipe['visible_controls'] = 1 << control
            recipe['visible_categories'] = 1 << CATEGORIES[control]
            recipe['selected_control'] = control
            if self.capture_probe is not None:
                recipe['sizes'][control] = list(self.capture_probe['size'])
            project_path = self.folder / ('paint-project-' + uuid.uuid4().hex + '.json')
            backend.write_json(project_path, self.model)
            self.model, self.digest = backend.project(project_path)
            args.project = project_path
            args.snapshot = self.folder / ('paint-snapshot-' + uuid.uuid4().hex)
            kdeglobals = args.kdeglobals or backend.kdeglobals_path()
            if self.allow_scrollbar:
                from gtk4_scrollbar_snapshot import generate_snapshot
                generate_snapshot(self.root,args.snapshot,self.model,self.digest,kdeglobals)
            else:
                from gtk4_generation import generate_snapshot
                generate_snapshot(self.root,args.snapshot,self.model,self.digest,kdeglobals,
                                  allow_toggle=self.allow_toggle,allow_check=self.allow_check)
        validate_preview_renderer(self.model, self.allow_toggle, self.allow_check,
                                  self.allow_scrollbar)
        if self.allow_scrollbar:
            from gtk4_scrollbar_session import scrollbar_records, ScrollbarSession
            self.records_for, session_type = scrollbar_records, ScrollbarSession
        elif self.allow_toggle or self.allow_check:
            from gtk4_toggle_session import button_records, ToggleSession
            self.records_for, session_type = button_records, ToggleSession
        else:
            self.records_for, session_type = push_records, PushSession
        self.records_for(self.model)
        self.receipt, colors = verify_initial_snapshot(
            self.root, args.snapshot, self.model, self.digest,
            allow_toggle=self.allow_toggle, allow_scrollbar=self.allow_scrollbar,
            allow_check=self.allow_check)
        self.writer = EventWriter(self.folder,self.root,family='gtk4',
                                  instance_id=args.preview_instance or uuid.uuid4().hex)
        # The private X11 preview cannot rely on an automatic GPU renderer:
        # both standalone and reparented surfaces were observed black despite
        # correct allocations. Scope the default to this preview process and
        # preserve an explicitly selected renderer.
        os.environ.setdefault('GSK_RENDERER','cairo')
        configure_display_backend(args.embed_window)
        self.renderer_requested=os.environ.get('GSK_RENDERER','automatic')
        self.gtk = C.CDLL('libgtk-4.so.1');self.glib = C.CDLL('libglib-2.0.so.0')
        p, i, u = C.c_void_p, C.c_int, C.c_uint
        bind(self.gtk,'gtk_init',None)()
        self.api = PushAPI()
        self.window = bind(self.gtk,'gtk_window_new',p)()
        self.title = bind(self.gtk,'gtk_window_set_title',None,p,C.c_char_p)
        bind(self.gtk,'gtk_window_set_default_size',None,p,i,i)(self.window,640,420)
        if args.embed_window:
            bind(self.gtk,'gtk_window_set_decorated',None,p,i)(self.window,0)
        self.loop = bind(self.glib,'g_main_loop_new',p,p,i)(None,0)
        self.quit_loop = bind(self.glib,'g_main_loop_quit',None,p)
        self.run_loop = bind(self.glib,'g_main_loop_run',None,p)
        self.loop_unref = bind(self.glib,'g_main_loop_unref',None,p)
        self.remove_source = bind(self.glib,'g_source_remove',i,u)
        self.width = bind(self.gtk,'gtk_widget_get_allocated_width',i,p)
        self.height = bind(self.gtk,'gtk_widget_get_allocated_height',i,p)
        self.scale = bind(self.gtk,'gtk_widget_get_scale_factor',i,p)
        self.bounds = bind(self.gtk,'gtk_widget_compute_bounds',i,p,p,C.POINTER(Bounds))
        change_callback = self.scrollbar_changed if self.allow_scrollbar else self.clicked
        self.session = session_type(self.api,self.window,backend.load_builder(self.root),
                                    change_callback,self.layout_event)
        active=getattr(args,'runtime_toggle_active',None)
        if self.allow_toggle and active is not None:
            self.session.selection={1:bool(active)}
        check_active=getattr(args,'runtime_check_active',None)
        if self.allow_check and check_active is not None:
            self.session.selection[2]=bool(check_active)
        self.session.replace(self.model,colors,None,prepared=self.receipt)
        if self.capture_probe is not None:
            adjustment = self.session.scene.adjustments.get(self.capture_control)
            if adjustment is None:
                raise ValueError('GTK4 scrollbar capture adjustment was not allocated')
            configure = bind(self.gtk, 'gtk_adjustment_configure', None, p,
                             C.c_double, C.c_double, C.c_double, C.c_double,
                             C.c_double, C.c_double)
            configure(adjustment, self.capture_probe['value'], 0.0, 100.0,
                      1.0, 10.0, self.capture_probe['page_size'])
            page_size = bind(self.gtk, 'gtk_adjustment_get_page_size', C.c_double, p)
            self.capture_probe_effective = {
                'value': float(self.api.adjustment_value(adjustment)),
                'page_size': float(page_size(adjustment)),
            }
        self.bridge = self.keys = None
        self.stop_requested = self.host_lost = False
        self.last_error = self.event_error = None
        self.metric_signature = None
        self.defer_metrics = False
        self.job = None
        self.failed_signature = None
        self.status = 'running'
        self.capture_result = None
        self.capture_prepared = False
        self.title(self.window,'Theme Lab — GTK4 nativo'.encode())
        bind(self.gtk,'gtk_window_present',None,p)(self.window)
        context_iteration = bind(self.glib,'g_main_context_iteration',i,p,i)
        display = bind(self.gtk,'gtk_widget_get_display',p,p)(self.window)
        display_flush = bind(self.gtk,'gdk_display_flush',None,p)

        def publish_window():
            publish_pending_x11_state(context_iteration,display_flush,display)

        publish_window()
        self.window_id = wait_window_xid(
            self.window,
            bind(self.gtk,'gtk_native_get_surface',p,p),
            bind(self.gtk,'gdk_x11_surface_get_xid',C.c_ulong,p),
            context_iteration)
        if args.embed_window:
            self.bridge = HostBridge(args.host_bridge,args.embed_window,args.host_pid)
            self.bridge.attach(self.window_id,progress=publish_window)
            self.keys = FocusKeys(self.window,self.bridge)
        self.close_callback = C.CFUNCTYPE(i,p,p)(self.close_requested)
        self.close_handler = self.api.connect(self.window,b'close-request',
                            C.cast(self.close_callback,p),None,None,0)
        self.tick_callback = C.CFUNCTYPE(i,p)(self.tick)
        self.source = bind(self.glib,'g_timeout_add_full',u,i,u,p,p,p)(
            0,150,C.cast(self.tick_callback,p),None,None)
        self.previous_signals = {s:signal.signal(s,self.signal_stop) for s in (signal.SIGTERM,signal.SIGINT)}

    def state(self):
        scene = getattr(getattr(self, 'session', None), 'scene', None)
        selected = scene.selected_values() if scene is not None and (
            getattr(self, 'allow_toggle', False) or getattr(self, 'allow_check', False)) else {}
        return {'status':self.status,'family':'gtk4','pid':__import__('os').getpid(),
                'window':self.window_id,'project_sha256':self.digest,
                'preview_instance':self.writer.instance_id,'error':self.last_error,
                'event_error':self.event_error,'embedded':self.bridge is not None,
                'renderer_requested':self.renderer_requested,
                'generation_pid':self.job.process.pid if self.job and self.job.poll() is None else None,
                'toggle_selection':{str(index):value for index,value in selected.items()
                    if getattr(self,'allow_toggle',False) and scene.records[index]['id']=='toggle'},
                'check_selection':{str(index):value for index,value in selected.items()
                    if getattr(self,'allow_check',False) and scene.records[index]['id']=='check'},
                'scrollbar_values':self.session.values()
                    if getattr(self,'allow_scrollbar',False) and self.session.scene is not None else {}}

    def checkpoint(self):
        backend.write_json(self.folder/'WORKER.json',self.state())

    def report(self,error):
        message=str(error)
        if message!=self.last_error:
            self.last_error=message
            print('GTK4 previous scene preserved: '+message,file=sys.stderr,flush=True)
        self.title(self.window,('Prévia GTK4 anterior preservada: '+message[:120]).encode())

    def clicked(self,index):
        try:
            state={'clicked':True}
            fields={}
            control=self.session.scene.records[index]['id']
            if control=='toggle' and getattr(self,'allow_toggle',False):
                state['selected']=bool(self.api.toggle_active(self.session.scene.widgets[index]))
                state['active']=state['selected']
                fields['origin']='coupled' if self.bridge else 'separate'
            elif control=='check' and getattr(self,'allow_check',False):
                state['selected']=bool(self.api.check_active(self.session.scene.widgets[index]))
                state['active']=state['selected']
                fields['origin']='coupled' if self.bridge else 'separate'
            self.writer.emit('native',index,self.digest,state=state,**fields)
            self.event_error=None
        except (OSError,ValueError,RuntimeError) as error:
            self.event_error=str(error)
            print('GTK4 event not saved: '+str(error),file=sys.stderr,flush=True)
            self.title(self.window,('Evento GTK4 não salvo: '+str(error)[:120]).encode())

    def scrollbar_changed(self,index,value):
        try:
            self.writer.emit('native',index,self.digest,
                             state={'value':round(value,3)},
                             origin='coupled' if self.bridge else 'separate')
            self.event_error=None
        except (OSError,ValueError,RuntimeError) as error:
            self.event_error=str(error)
            print('GTK4 scrollbar event not saved: '+str(error),file=sys.stderr,flush=True)
            self.title(self.window,('Evento GTK4 não salvo: '+str(error)[:120]).encode())

    def layout_event(self,action,index,fields):
        try:
            self.writer.emit(action,index,self.digest,**fields)
            self.event_error=None
        except (OSError,ValueError,RuntimeError) as error:
            self.event_error=str(error)
            self.title(self.window,('Evento GTK4 não salvo: '+str(error)[:120]).encode())
            raise

    def metrics(self):
        rows=[]
        for index,widget in self.session.scene.widgets.items():
            box=Bounds()
            if not self.bounds(widget,self.session.scene.fixed,C.byref(box)):continue
            rows.append({'index':index,'allocation':[round(box.x),round(box.y),
                          round(box.width),round(box.height)],'scale_factor':self.scale(widget),
                          **self.session.scene.native_requests[index]})
        return rows

    def tick(self,_data):
        if self.stop_requested:
            if self.capture_result is None:self.status='closed'
            self.source=0;self.quit_loop(self.loop);return 0
        try:
            if self.bridge and self.bridge.poll() is None:
                self.host_lost=True;self.status='host_lost';self.source=0;self.quit_loop(self.loop);return 0
            model,digest=backend.project(self.args.project)
            signature=(digest,self.palette_stamp())
            if self.job and self.job.poll() is not None:
                job=self.job;self.job=None
                try:
                    if job.poll()!=0:
                        self.failed_signature=(job.digest,signature[1])
                        raise ValueError('GTK4 generation failed; see '+str(job.folder/'generation.log'))
                    if job.digest==digest:
                        receipt,colors=verify_snapshot(
                            self.root, job.folder/'generated', model, digest,
                            allow_toggle=self.allow_toggle,
                            allow_scrollbar=self.allow_scrollbar,
                            allow_check=self.allow_check)
                        self.session.replace(model,colors,None,prepared=receipt)
                        self.model,self.digest,self.receipt=model,digest,receipt
                        self.metric_signature=None;self.last_error=None;self.failed_signature=None
                        self.defer_metrics=True
                        self.title(self.window,'Theme Lab — GTK4 nativo'.encode())
                finally:job.close()
            if (self.job is None and signature!=self.failed_signature and
                    (digest!=self.digest or not backend.palette_inputs_current(self.receipt))):
                validate_preview_renderer(model, self.allow_toggle,
                                          self.allow_check,
                                          self.allow_scrollbar)
                self.records_for(model)
                self.job=SnapshotJob(
                    self.root, self.folder, model, digest, self.args.kdeglobals,
                    allow_toggle=self.allow_toggle,
                    allow_scrollbar=self.allow_scrollbar,
                    allow_check=self.allow_check)
            rows=[] if self.defer_metrics else self.metrics()
            self.defer_metrics=False
            if self.capture_control is not None and self.capture_result is None:
                try:
                    widget=self.session.scene.widgets.get(self.capture_control)
                    if widget is None:raise ValueError('GTK4 selected control was not allocated')
                    from gtk4_paint_capture import capture
                    if not self.capture_prepared:
                        from gtk4_paint_capture import prepare
                        prepare(self.gtk,widget,self.capture_state)
                        self.capture_prepared=True
                        return 1
                    self.capture_result=capture(self.gtk,widget,self.window,self.window_id,
                                                self.capture_output,self.folder,self.capture_control,
                                                self.capture_state)
                    if self.capture_probe is not None:
                        self.capture_result['scrollbar_probe'] = dict(
                            self.capture_probe,
                            effective=dict(self.capture_probe_effective or {}))
                    self.status='captured'
                except (OSError,ValueError,RuntimeError,TypeError,KeyError,AttributeError) as error:
                    self.capture_result={'status':'unavailable','reason':str(error)}
                    self.status='capture_unavailable'
                self.stop_requested=True
                self.source=0;self.quit_loop(self.loop);return 0
            signature=(self.digest,json.dumps(rows,sort_keys=True))
            ready = rows and all(
                all(actual >= minimum > 0 for actual, minimum in zip(
                    row['allocation'][2:], row['native_minimum_before_custom_size']))
                for row in rows)
            if ready and signature!=self.metric_signature:
                for row in rows:
                    x,y,width,height=row['allocation']
                    minimum=row['native_minimum_before_custom_size']
                    natural=row['native_natural_before_custom_size']
                    self.writer.emit('metrics',row['index'],self.digest,metrics=rows,
                                     origin='coupled' if self.bridge else 'separate',
                                     width=width,height=height,
                                     minimum_width=minimum[0],minimum_height=minimum[1],
                                     natural_width=natural[0],natural_height=natural[1],
                                     scale_factor=row['scale_factor'],coordinate_space='gtk_logical_px',
                                     position_x=x,position_y=y,font_kind=row['font_kind'],
                                     font_description=row['font_description'])
                self.metric_signature=signature
            if self.keys and self.keys.last_error:
                self.report(self.keys.last_error)
            if self.session.scene.gestures and self.session.scene.gestures.last_error:
                self.report(self.session.scene.gestures.last_error)
            self.checkpoint()
        except (OSError,ValueError,RuntimeError,TypeError,KeyError) as error:
            self.report(error)
            try:self.checkpoint()
            except (OSError,ValueError) as storage_error:
                print('GTK4 status not saved: '+str(storage_error),file=sys.stderr,flush=True)
        return 1

    def palette_stamp(self):
        result=[]
        for item in self.receipt.get('palette_inputs',[]):
            try:
                info=Path(item['path']).stat();result.append((item['path'],info.st_size,info.st_mtime_ns))
            except OSError:result.append((item['path'],None,None))
        return tuple(result)

    def signal_stop(self,_number,_frame):self.stop_requested=True

    def close_requested(self,_window,_data):
        self.stop_requested=True
        return 1  # Cleanup belongs to the worker, not a duplicate Gtk destroy.

    def run(self):
        self.checkpoint()
        if self.capture_control is None:
            print(json.dumps(self.state(),ensure_ascii=False),flush=True)
        try:self.run_loop(self.loop)
        finally:
            if self.source:self.remove_source(self.source)
            for number,previous in self.previous_signals.items():signal.signal(number,previous)
            self.api.disconnect(self.window,self.close_handler)
            if self.job:self.job.close();self.job=None
            def close_scene():
                if self.keys:self.keys.close()
                self.session.close()
                if self.bridge:self.bridge.close()
            if self.host_lost:self.api.close_after_host_loss(self.window,close_scene)
            else:
                close_scene();self.api.destroy_window(self.window)
            self.loop_unref(self.loop)
            self.checkpoint()
        if self.capture_control is not None:
            print(json.dumps(self.capture_result or {
                'status':'unavailable','reason':'GTK4 sample ended without a capture result'},
                ensure_ascii=False),flush=True)
        return 1 if self.host_lost else 0
