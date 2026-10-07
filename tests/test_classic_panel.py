# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise real migration JavaScript against independent native-API ownership rules."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import classic_panel as module


def tree(entries=None, **groups):
    return {'entries': entries or {}, 'groups': groups}


def widget(identifier, type_, **groups):
    return {'id': identifier, 'type': type_, 'config': tree(**groups), 'shortcut': '', 'background': 'DefaultBackground'}


MODEL = r'''
var model = INITIAL;
var captured = [];
function print(text) { captured.push(text); }
function node(object, create) {
    var value = object.raw.config;
    for (var group of object.currentConfigGroup) {
        if (!value.groups[group]) {
            if (!create) return {entries:{},groups:{}};
            value.groups[group] = {entries:{},groups:{}};
        }
        value = value.groups[group];
    }
    return value;
}
function fault(name) {
    if (model.fault === name && !model.faultFired) {
        model.faultFired = true;
        throw new Error("Injected native failure: " + name);
    }
}
class ObjectApi {
    constructor(raw) { this.raw=raw; this.currentConfigGroup=[]; }
    get id() { return this.raw.id; }
    get type() { return this.raw.type; }
    get configKeys() { return Object.keys(node(this,false).entries); }
    get configGroups() { return Object.keys(node(this,false).groups); }
    readConfig(key, fallback) { var value=node(this,false).entries[key]; return value === undefined ? fallback : value; }
    writeConfig(key,value) {
        node(this,true).entries[key]=value;
        if (this.type === 'org.irixclassic.applications') fault('copy');
    }
    reloadConfig() {
        if (model.recreateTrayDefaultOnReload && this.type === 'org.kde.plasma.private.systemtray' &&
            !this.raw.widgets.some(w => !w.destroyed && w.type === 'org.kde.plasma.volume')) {
            this.raw.widgets.push({id:model.nextId++,type:'org.kde.plasma.volume',config:{entries:{},groups:{}},
                                   shortcut:'',background:'DefaultBackground'});
        }
    }
}
function owner(id) {
    return model.panels.concat(Object.values(model.inners)).find(c => c.widgets.some(w => w.id===id));
}
function syncOrder(containment) {
    if (containment.type === 'org.kde.panel') {
        containment.config.groups.General.entries.AppletOrder = containment.widgets.filter(w=>!w.destroyed).map(w=>w.id).join(';');
    }
}
class WidgetApi extends ObjectApi {
    get index() { return -1; }
    set index(value) {} // Native 6.3 setter is a documented implementation stub.
    get geometry() {
        var index=owner(this.id).widgets.findIndex(w=>w.id===this.id);
        return {x:index*100,y:4,width:100,height:56};
    }
    get globalShortcut() { return this.raw.shortcut; }
    set globalShortcut(value) { this.raw.shortcut=value; }
    get userBackgroundHints() { return this.raw.background; }
    set userBackgroundHints(value) { this.raw.background=value; }
    remove() {
        var current=owner(this.id);
        if (!current) return;
        if (model.deferDestruction) this.raw.destroyed=true;
        else current.widgets.splice(current.widgets.findIndex(w=>w.id===this.id),1);
        syncOrder(current);
        // Native SystemTrayContainer QObject ownership destroys its inner
        // containment and every child still inside, independently of config.
        if (!model.deferDestruction && this.type.endsWith('.systemtray')) {
            var innerId=this.raw.config.entries.SystrayContainmentId;
            delete model.inners[innerId];
        }
        if (this.type === 'org.kde.plasma.quicklaunch') fault('remove_after');
    }
}
class ContainmentApi extends ObjectApi {
    // Native applets are a QSet: enumeration is not guaranteed visual order.
    widgets() { return this.raw.widgets.slice().reverse().map(w=>new WidgetApi(w)); }
    widgetById(id) { var raw=this.raw.widgets.find(w=>w.id===id); return raw ? new WidgetApi(raw) : null; }
    addWidget(value,x,y,width,height) {
        if (typeof value !== 'string') {
            model.moves=(model.moves||0)+1;
            if (model.moves===2) fault('move_second');
            var old=owner(value.id);
            old.widgets.splice(old.widgets.findIndex(w=>w.id===value.id),1);
            syncOrder(old);
            this.raw.widgets.push(value.raw);
            syncOrder(this.raw);
            return value;
        }
        var raw={id:model.nextId++,type:value,config:{entries:{},groups:{}},shortcut:'',background:'DefaultBackground'};
        if (x === undefined) this.raw.widgets.push(raw);
        else this.raw.widgets.splice(Math.floor(x/100),0,raw);
        syncOrder(this.raw);
        var instance=new WidgetApi(raw);
        if (value.endsWith('.systemtray')) {
            var innerId=model.nextId++;
            raw.config.entries.SystrayContainmentId=innerId;
            model.inners[innerId]={id:innerId,type:'org.kde.plasma.private.systemtray',config:{entries:{},groups:{}},widgets:[
                {id:model.nextId++,type:'org.kde.plasma.volume',config:{entries:{},groups:{}},shortcut:'',background:'DefaultBackground'}
            ]};
        }
        return instance;
    }
}
function panels() {
    return model.panels.map(raw => {
        var api=new ContainmentApi(raw);
        Object.keys(raw.geometry).forEach(k=>api[k]=raw.geometry[k]);
        return api;
    });
}
function panelById(id) { return panels().find(p=>p.id===id); }
function desktopById(id) { return model.inners[id] ? new ContainmentApi(model.inners[id]) : null; }
var knownWidgetTypes=model.known;
function deferredCleanup() {
    var removedTrays=[];
    for (var containment of model.panels.concat(Object.values(model.inners))) {
        for (var w of containment.widgets) {
            if (w.destroyed && w.type.endsWith('.systemtray')) removedTrays.push(w.config.entries.SystrayContainmentId);
        }
        containment.widgets=containment.widgets.filter(w=>!w.destroyed);
    }
    removedTrays.forEach(id=>delete model.inners[id]);
}
'''


class NativeModel:
    def __init__(self, value):
        self.value = value
        self.payloads = []

    def __call__(self, payload):
        self.payloads.append(copy.deepcopy(payload))
        source = MODEL.replace('INITIAL', json.dumps(self.value)) + '\n' + module.script(payload)
        source += '\ndeferredCleanup(); process.stdout.write(JSON.stringify({result:JSON.parse(captured[captured.length-1]),model:model}));'
        response = subprocess.run(['node', '-e', source], capture_output=True, text=True, check=True)
        output = json.loads(response.stdout)
        self.value = output['model']
        return output['result']


@unittest.skipUnless(shutil.which('node'), 'Node required to exercise the actual Plasma migration JavaScript')
class PanelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root/'config'; self.config.mkdir()
        self.state = self.root/'state'
        (self.config/'plasmarc').write_text('[Theme]\nname=IrixClassic\n')
        self.rc = self.config/'plasma-org.kde.plasma.desktop-appletsrc'
        self.rc.write_bytes(b'[Containments][13]\nplugin=org.kde.panel\n[Other user preference]\nkeep=this\n')
        self.rc.chmod(0o640)
        originals = [
            widget(20, 'org.kde.plasma.kickoff', General=tree({'icon':'start-here','favorites':['kate.desktop','org.kde.dolphin.desktop']}, Nested=tree({'value':'preserve'}))),
            widget(21, 'org.kde.plasma.quicklaunch', General=tree({'launcherUrls':['file:///home/example/Desktop/Terminal.desktop'],'maxRows':1})),
            widget(22, 'org.kde.plasma.taskmanager', General=tree({'maxStripes':'2','forceStripes':'true','groupingStrategy':1})),
            widget(23, 'org.kde.plasma.pager', General=tree({'showWindowIcons':True})),
            widget(24, 'org.kde.plasma.systemtray'),
            widget(25, 'org.kde.plasma.analogclock', General=tree({'showSecondHand':False})),
        ]
        originals[0]['shortcut'] = 'Alt+F1'
        originals[4]['config']['entries']['SystrayContainmentId'] = 30
        originals[3]['background'] = 'NoBackground'
        geometry = dict(screen=0,location='bottom',alignment='center',offset=0,lengthMode='custom',length=1440,
                        minimumLength=1440,maximumLength=1440,height=64,hiding='none',floating=False,opacity='opaque')
        inner = dict(id=30,type='org.kde.plasma.private.systemtray',config=tree(General=tree({'extraItems':['org.kde.plasma.networkmanagement'],'hiddenItems':['org.kde.plasma.volume']})),widgets=[
            widget(31,'org.kde.plasma.networkmanagement',General=tree({'wifiEnabled':True})),
            widget(32,'org.kde.plasma.volume',General=tree({'showVirtualDevices':False}, Nested=tree({'keep':42})))
        ])
        self.native = NativeModel({'nextId':1000,'panels':[dict(id=13,type='org.kde.panel',config=tree(General=tree({'AppletOrder':'20;21;22;23;24;25','customSetting':'keep'})),geometry=geometry,widgets=originals)],
                                   'inners':{'30':inner},'known':list(module.MAPPING)+list(module.MAPPING.values()),'fault':None})
        self.before = module.diagnose(self.native)['panels'][0]

    def apply(self, **kwargs):
        return module.apply(self.config,self.state,call=self.native,**kwargs)

    def restore(self, **kwargs):
        return module.restore(self.config,self.state,call=self.native,**kwargs)

    def current(self):
        return module.diagnose(self.native)['panels'][0]

    def test_dry_run_is_read_only_including_files_and_widgets(self):
        initial=copy.deepcopy(self.native.value); original=self.rc.read_bytes()
        self.apply(dry=True)
        self.assertEqual(self.native.value,initial); self.assertEqual(self.rc.read_bytes(),original)
        self.assertFalse(self.state.exists())
        self.assertTrue(all(p['action']=='inspect' for p in self.native.payloads))

    def test_replacement_preserves_panel_geometry_order_shortcuts_and_recursive_config(self):
        receipt=self.apply(); record=json.loads(receipt.read_text()); after=self.current()
        self.assertEqual(after['id'],13); self.assertEqual(after['geometry'],self.before['geometry'])
        self.assertEqual([w['type'] for w in after['widgets']],[module.MAPPING.get(w['type'],w['type']) for w in self.before['widgets']])
        self.assertEqual(after['widgets'][0]['shortcut'],'Alt+F1')
        self.assertEqual(after['widgets'][0]['config'],self.before['widgets'][0]['config'])
        self.assertEqual(after['widgets'][1]['config'],self.before['widgets'][1]['config'])
        self.assertEqual(after['widgets'][3],self.before['widgets'][3])
        self.assertEqual(after['widgets'][2]['config']['groups']['General']['entries']['maxStripes'],'1')
        self.assertEqual(record['status'],'applied')
        self.assertEqual(module.decode(record['config_before']),self.rc.read_bytes())
        self.assertEqual(record['config_before']['mode'],0o640)

    def test_tray_children_move_before_wrapper_deletion_with_ids_preferences_and_order_preserved(self):
        self.apply(); tray=self.current()['widgets'][4]['tray']; expected=self.before['widgets'][4]['tray']
        self.assertNotEqual(tray['id'],expected['id'])
        self.assertEqual(tray['widgets'],expected['widgets']); self.assertEqual(tray['config'],expected['config'])
        self.assertNotIn('30',self.native.value['inners'])

    def test_restore_recreates_original_widgets_and_preserves_inner_child_ids(self):
        receipt=self.apply(); self.restore(); restored=self.current()
        self.assertEqual(module.semantic(restored),module.semantic(self.before))
        self.assertEqual(restored['widgets'][4]['tray']['widgets'],self.before['widgets'][4]['tray']['widgets'])
        self.assertEqual(json.loads(receipt.read_text())['status'],'restored')

    def test_native_deferred_destruction_and_tray_reload_preserve_original_children(self):
        self.native.value.update(deferDestruction=True,recreateTrayDefaultOnReload=True)
        receipt=self.apply()
        self.assertEqual(module.stable(self.current())['widgets'][4]['tray']['widgets'],
                         module.stable(self.before)['widgets'][4]['tray']['widgets'])
        self.restore()
        self.assertEqual(module.semantic(self.current()),module.semantic(self.before))
        self.assertEqual(json.loads(receipt.read_text())['status'],'restored')

    def test_containment_applet_records_are_not_copied_as_widget_configuration(self):
        panel=self.native.value['panels'][0]
        panel['config']['groups']['Applets']=tree(**{'20':tree({'plugin':'org.kde.plasma.kickoff'})})
        self.native.value['inners']['30']['config']['groups']['Applets']=tree(**{'31':tree({'plugin':'org.kde.plasma.networkmanagement'})})
        panel['widgets'][1]['config']['groups']['Applets']=tree({'AppletOrder':'custom-widget-setting'})
        before=self.current()
        self.assertNotIn('Applets',before['config']['groups'])
        self.assertNotIn('Applets',before['widgets'][4]['tray']['config']['groups'])
        self.apply(); after=self.current()
        self.assertEqual(after['widgets'][1]['config']['groups']['Applets']['entries']['AppletOrder'],'custom-widget-setting')
        self.restore(); self.assertEqual(module.semantic(self.current()),module.semantic(before))

    def test_receipt_is_durable_before_any_widget_mutation(self):
        def check(payload):
            if payload['action']=='replace':
                receipt=module.latest(self.state); record=json.loads(receipt.read_text())
                self.assertEqual(record['status'],'prepared')
                self.assertEqual(record['before'],self.before)
                self.assertEqual(record['planned_after']['widgets'][0]['type'],'org.irixclassic.applications')
                self.assertEqual(module.decode(record['config_before']),self.rc.read_bytes())
            return self.native(payload)
        module.apply(self.config,self.state,call=check)

    def test_recursive_copy_failure_rolls_back_before_source_deletion(self):
        self.native.value['fault']='copy'
        with self.assertRaises(module.Failure): self.apply()
        self.assertEqual(module.semantic(self.current()),module.semantic(self.before))
        record=json.loads(module.latest(self.state).read_text())
        self.assertEqual(record['status'],'rolled_back')

    def test_partial_tray_transfer_reunites_children_without_losing_either_half(self):
        self.native.value['fault']='move_second'
        with self.assertRaises(module.Failure): self.apply()
        self.assertEqual(module.semantic(self.current()),module.semantic(self.before))
        self.assertEqual(module.stable(self.current())['widgets'][4]['tray']['widgets'],
                         module.stable(self.before)['widgets'][4]['tray']['widgets'])
        self.assertEqual(json.loads(module.latest(self.state).read_text())['status'],'rolled_back')

    def test_failure_after_source_deletion_recreates_originals_and_restores_order(self):
        self.native.value['fault']='remove_after'
        with self.assertRaises(module.Failure): self.apply()
        self.assertEqual(module.semantic(self.current()),module.semantic(self.before))
        self.assertEqual(json.loads(module.latest(self.state).read_text())['status'],'rolled_back')

    def test_failed_postcondition_automatically_restores_original_configuration(self):
        damaged = False
        def damage(payload):
            nonlocal damaged
            result = self.native(payload)
            if payload['action']=='replace' and not damaged and result.get('ok'):
                damaged = True
                self.native.value['panels'][0]['widgets'][2]['config']['groups']['General']['entries']['groupingStrategy']=7
                result = self.native({'action':'inspect'})
                result['replacements']=[{'oldId':spec['from']['id'],'newId':self.native.value['panels'][0]['widgets'][index]['id'],
                                         'oldType':spec['from']['type'],'newType':spec['type']}
                                        for index,spec in enumerate(payload['specs'])]
                # Pager is preserved between taskmanager and tray.
                for item in result['replacements']:
                    item['newId']=next(w['id'] for w in self.native.value['panels'][0]['widgets'] if w['type']==item['newType'])
            return result
        with self.assertRaises(module.Failure): module.apply(self.config,self.state,call=damage)
        self.assertEqual(module.semantic(self.current()),module.semantic(self.before))
        self.assertEqual(json.loads(module.latest(self.state).read_text())['status'],'rolled_back')

    def test_lost_reply_can_restore_only_a_fully_proven_result(self):
        def lost(payload):
            result=self.native(payload)
            if payload['action']=='replace': raise subprocess.TimeoutExpired(['gdbus'],30)
            return result
        with self.assertRaises(subprocess.TimeoutExpired): module.apply(self.config,self.state,call=lost)
        receipt=module.latest(self.state); record=json.loads(receipt.read_text())
        self.assertEqual(record['status'],'recovery_needed'); self.assertNotIn('after',record)
        self.restore()
        self.assertEqual(module.semantic(self.current()),module.semantic(self.before))
        self.assertEqual(json.loads(receipt.read_text())['status'],'restored')

    def test_lost_reply_with_intact_original_panel_needs_no_mutation(self):
        def lost(payload):
            if payload['action']=='replace': raise subprocess.TimeoutExpired(['gdbus'],30)
            return self.native(payload)
        with self.assertRaises(subprocess.TimeoutExpired): module.apply(self.config,self.state,call=lost)
        before=copy.deepcopy(self.native.value); self.restore()
        self.assertEqual(self.native.value,before)
        self.assertEqual(json.loads(module.latest(self.state).read_text())['status'],'rolled_back')

    def test_concurrent_change_before_transaction_is_refused_without_losing_edit(self):
        def change(payload):
            if payload['action']=='replace':
                self.native.value['panels'][0]['widgets'][3]['config']['groups']['General']['entries']['showWindowIcons']=False
            return self.native(payload)
        with self.assertRaises(module.Failure): module.apply(self.config,self.state,call=change)
        self.assertEqual(self.current()['widgets'][3]['config']['groups']['General']['entries']['showWindowIcons'],False)
        self.assertEqual([w['type'] for w in self.current()['widgets']],[w['type'] for w in self.before['widgets']])
        self.assertEqual(json.loads(module.latest(self.state).read_text())['status'],'not_applied')

    def test_restore_refuses_unrelated_edits_instead_of_replaying_full_file_backup(self):
        self.apply()
        self.native.value['panels'][0]['widgets'][3]['config']['groups']['General']['entries']['showWindowIcons']=False
        self.rc.write_bytes(self.rc.read_bytes()+b'external=keep\n')
        before=copy.deepcopy(self.native.value)
        with self.assertRaises(module.Failure): self.restore()
        self.assertEqual(self.native.value,before); self.assertIn(b'external=keep',self.rc.read_bytes())

    def test_missing_destination_is_detected_before_preparing_receipt(self):
        self.native.value['known'].remove('org.irixclassic.analogclock')
        with self.assertRaises(module.Failure): self.apply()
        self.assertFalse(self.state.exists())
        self.assertTrue(all(p['action']=='inspect' for p in self.native.payloads))

    def test_missing_source_id_is_rechecked_before_first_creation(self):
        def missing(payload):
            if payload['action']=='replace': self.native.value['panels'][0]['widgets'].pop(0)
            return self.native(payload)
        with self.assertRaises(module.Failure): module.apply(self.config,self.state,call=missing)
        self.assertEqual(self.native.value['nextId'],1000)

    def test_multi_panel_profile_is_not_reset_or_guessed(self):
        self.native.value['panels'].append(copy.deepcopy(self.native.value['panels'][0]))
        with self.assertRaises(module.Failure): self.apply()
        self.assertFalse(self.state.exists())

    def test_modern_theme_is_refused_without_dbus_mutations(self):
        (self.config/'plasmarc').write_text('[Theme]\nname=Irixium\n')
        self.native.payloads.clear()
        with self.assertRaises(module.Failure): self.apply()
        self.assertEqual(self.native.payloads,[])

    def test_per_user_kdedefaults_theme_is_respected(self):
        (self.config/'plasmarc').unlink(); (self.config/'kdedefaults').mkdir()
        (self.config/'kdedefaults/plasmarc').write_text('[Theme]\nname=IrixClassic\n')
        self.apply(dry=True); self.assertFalse(self.state.exists())

    def test_existing_classic_panel_is_idempotent(self):
        receipt=self.apply(); call_count=len([p for p in self.native.payloads if p['action']=='replace'])
        self.assertIsNone(self.apply())
        self.assertEqual(module.latest(self.state),receipt)
        self.assertEqual(len([p for p in self.native.payloads if p['action']=='replace']),call_count)

    def test_foreign_receipt_and_symlink_are_refused(self):
        receipt=self.apply(); record=json.loads(receipt.read_text()); record['uid']=-1; module.save(receipt,record)
        with self.assertRaises(module.Failure): self.restore()
        (self.state/'latest').unlink(); (self.state/'latest').symlink_to('/tmp/not-our-receipt')
        with self.assertRaises(module.Failure): module.latest(self.state)

    def test_modified_replacement_id_is_rejected_before_restore(self):
        receipt=self.apply(); record=json.loads(receipt.read_text())
        record['replacements'][0]['newId']=record['after']['widgets'][3]['id']; module.save(receipt,record)
        before=copy.deepcopy(self.native.value)
        with self.assertRaises(module.Failure): self.restore()
        self.assertEqual(self.native.value,before)

    def test_restore_verification_does_not_rewrite_receipt_or_widgets(self):
        receipt=self.apply(); data=receipt.read_bytes(); before=copy.deepcopy(self.native.value)
        self.restore(dry=True)
        self.assertEqual(receipt.read_bytes(),data); self.assertEqual(self.native.value,before)

    def test_no_desktop_action_occurs_on_import_and_main_checks_own_session(self):
        import reload_decoration
        with patch.object(reload_decoration,'check_session',side_effect=module.Failure('foreign bus')),patch.object(sys,'argv',['classic_panel.py','--verificar']),patch.object(module,'plasma') as call:
            with self.assertRaises(module.Failure): module.main()
        call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
