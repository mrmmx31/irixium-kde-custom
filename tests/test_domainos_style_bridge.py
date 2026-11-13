#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bridge authorization, installation and Qt file events in disposable profiles."""
from __future__ import annotations
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import domainos_style_bridge as bridge
from theme_transaction import Failure, atomic


class BridgeTests(unittest.TestCase):
    def setUp(self):
        # This workspace filesystem has room for fixtures; /tmp is intentionally
        # not used for the dozens of private profile files.
        self.temp=tempfile.TemporaryDirectory(prefix='.domainos-bridge-test-',dir=ROOT)
        self.base=Path(self.temp.name)
        self.data=self.base/'data'; self.config=self.base/'config'; self.state=self.base/'state'
        for path in (self.data,self.config,self.state): path.mkdir(mode=0o700)
        self.locations=bridge.paths(self.data,self.config,self.state)
        self.source=self.base/'source'; (self.source/'tools').mkdir(parents=True)
        for name in bridge.MODULES: shutil.copyfile(ROOT/'tools'/name,self.source/'tools'/name)
        self.token='a'*32
        self.receipt=self.locations['activation']/'backups'/self.token/'receipt.json'
        self.record={'format':1,'uid':os.getuid(),'token':self.token,'plugin':'org.irixclassic.domainos.panel','status':'active'}
        atomic(self.receipt,(json.dumps(self.record)+'\n').encode())
        atomic(self.locations['activation']/'latest',(self.token+'\n').encode())
        atomic(self.config/'other-app.conf',b'unchanged\n')
        atomic(self.config/'plasmarc',b'[Theme]\nname=IrixClassicDomainOS\n')
        self.environment=patch.dict(os.environ,{'XDG_DATA_HOME':str(self.data),
            'XDG_CONFIG_HOME':str(self.config),'XDG_STATE_HOME':str(self.state)},clear=False)
        self.environment.start()

    def tearDown(self):
        self.environment.stop(); self.temp.cleanup()

    def install(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return bridge.install_bridge(self.data,self.config,self.state,self.source)

    def test_transition_scope_and_pending_receipts(self):
        for state in ('active','restored','prepared','committing','recovery_needed','invalid'):
            for style in ('IrixClassicDomainOS','IrixClassic','Breeze','Irixium',None):
                expected = None
                if state=='active' and style=='IrixClassic': expected=['--ponte','--restaurar']
                if state=='restored' and style=='IrixClassicDomainOS': expected=['--ponte']
                self.assertEqual(bridge.action_for(style,{'status':state}),expected)

    def test_global_install_has_no_activation_or_desktop_side_effects(self):
        self.receipt.unlink(); (self.locations['activation']/'latest').unlink()
        atomic(self.config/'kdeglobals', ('[KDE]\nLookAndFeelPackage='+bridge.GLOBAL_THEME+'\n').encode())
        protected={path:path.read_bytes() for path in (self.config/'kdeglobals',self.config/'plasmarc',self.config/'other-app.conf')}
        with patch.object(bridge,'session_owner',side_effect=AssertionError('desktop queried while installing')), \
                patch.object(bridge,'service_command',side_effect=AssertionError('service started while installing')), \
                contextlib.redirect_stdout(io.StringIO()):
            bridge.install_bridge(self.data,self.config,self.state,self.source,global_choices=True)
        control=bridge.read_control(self.locations)
        self.assertTrue(control['global_enabled']);self.assertFalse(control['style_enabled'])
        self.assertEqual(control['global_baseline'],bridge.GLOBAL_THEME)
        self.assertIsNone(bridge.panel_action(bridge.GLOBAL_THEME,'IrixClassicDomainOS',None,control))
        self.assertFalse((self.locations['activation']/'latest').exists())
        for path,contents in protected.items():self.assertEqual(path.read_bytes(),contents)

    def test_global_dry_install_does_not_create_runtime_state_or_receipt(self):
        self.receipt.unlink(); (self.locations['activation']/'latest').unlink()
        with patch.object(bridge,'effective_preference',return_value='org.kde.breeze.desktop'):
            bridge.install_bridge(self.data,self.config,self.state,self.source,global_choices=True,dry=True)
        self.assertFalse(self.locations['state'].exists());self.assertFalse(self.locations['runtime'].exists())

    def test_global_choices_preserve_manual_activations_and_pending_transactions(self):
        control={'global_enabled':True,'style_enabled':False,
                 'global_baseline':'org.kde.breeze.desktop','panel_id':42}
        self.assertEqual(bridge.panel_action(bridge.GLOBAL_THEME,'IrixClassicDomainOS',None,control),
                         ['--global','--painel','42'])
        self.assertIsNone(bridge.panel_action(bridge.GLOBAL_THEME,'IrixClassic',None,control))
        for status in ('prepared','committing','recovery_needed','active'):
            self.assertIsNone(bridge.panel_action(bridge.GLOBAL_THEME,'IrixClassicDomainOS',
                {'status':status,'origin':'manual'},control))
        for theme in bridge.IRIX_GLOBAL_THEMES:
            self.assertIsNone(bridge.panel_action(theme,'IrixClassic',{'status':'active','origin':'manual'},control))
            self.assertEqual(bridge.panel_action(theme,'IrixClassic',{'status':'active','origin':'global'},control),
                             ['--global','--ponte','--restaurar'])
        self.assertIsNone(bridge.panel_action('org.kde.breeze.desktop','breeze',
            {'status':'active','origin':'global'},control))
        self.assertEqual(bridge.panel_action(bridge.GLOBAL_THEME,'IrixClassicDomainOS',
            {'status':'restored','origin':'global'},control),['--global','--ponte'])

    def test_updating_panel_id_preserves_unfinished_global_choice(self):
        self.receipt.unlink(); (self.locations['activation']/'latest').unlink()
        with patch.object(bridge,'effective_preference',return_value=bridge.IRIX_GLOBAL_THEMES[0]), \
                contextlib.redirect_stdout(io.StringIO()):
            bridge.install_bridge(self.data,self.config,self.state,self.source,global_choices=True)
        with patch.object(bridge,'effective_preference',return_value=bridge.GLOBAL_THEME), \
                contextlib.redirect_stdout(io.StringIO()):
            bridge.install_bridge(self.data,self.config,self.state,self.source,global_choices=True,panel=99)
        control=bridge.read_control(self.locations)
        self.assertEqual(control['global_baseline'],bridge.IRIX_GLOBAL_THEMES[0])
        self.assertEqual(bridge.panel_action(bridge.GLOBAL_THEME,'IrixClassicDomainOS',None,control),
                         ['--global','--painel','99'])

    def test_native_defaults_are_read_when_override_key_or_file_is_absent(self):
        fallback=self.config/'kdedefaults/plasmarc'
        atomic(fallback,b'[Theme]\nname=IrixClassic\n')
        for override in (b'[Theme]\nother=preserved\n',b'[Unrelated]\nkey=value\n',None):
            with self.subTest(override=override):
                if override is None: (self.config/'plasmarc').unlink()
                else: atomic(self.config/'plasmarc',override)
                self.assertEqual(bridge.selected_style(self.config/'plasmarc'),'IrixClassic')
                self.assertEqual(bridge.action_for(bridge.selected_style(self.config/'plasmarc'),
                    self.record),['--ponte','--restaurar'])
        self.assertEqual(fallback.read_bytes(),b'[Theme]\nname=IrixClassic\n')
        self.assertEqual(json.loads(self.receipt.read_text()),self.record)

    def test_explicit_style_and_empty_override_precede_native_defaults(self):
        atomic(self.config/'kdedefaults/plasmarc',b'[Theme]\nname=IrixClassic\n')
        for style in ('IrixClassicDomainOS','Breeze','Irixium',''):
            with self.subTest(style=style):
                atomic(self.config/'plasmarc',('[Theme]\nname='+style+'\n').encode())
                self.assertEqual(bridge.selected_style(self.config/'plasmarc'),style)
                self.assertIsNone(bridge.action_for(style,self.record))

    def test_malformed_or_masked_override_does_not_authorize_fallback(self):
        atomic(self.config/'kdedefaults/plasmarc',b'[Theme]\nname=IrixClassic\n')
        for override in (b'not an INI file\n',b'[Theme]\nname[$d]\n',
                b'[Theme]\nname[$d]=\n',b'[Theme][$i]\nname=IrixClassic\n',
                b'[Theme]\nname[$e]=IrixClassic\n'):
            with self.subTest(override=override):
                atomic(self.config/'plasmarc',override)
                self.assertIsNone(bridge.selected_style(self.config/'plasmarc'))
                self.assertIsNone(bridge.action_for(bridge.selected_style(self.config/'plasmarc'),self.record))

    def test_fallback_keeps_existing_link_and_owner_guards(self):
        atomic(self.config/'plasmarc',b'[Theme]\nother=value\n')
        fallback=self.config/'kdedefaults/plasmarc'
        atomic(fallback,b'[Theme]\nname=IrixClassic\n')
        original=fallback.read_bytes(); fallback.unlink(); fallback.symlink_to(self.receipt)
        with self.assertRaisesRegex(Failure,'Link simbólico'):
            bridge.selected_style(self.config/'plasmarc')
        fallback.unlink(); atomic(fallback,original)
        real=bridge.own_file
        with patch.object(bridge,'own_file',side_effect=lambda candidate,private=False:
                (_ for _ in ()).throw(Failure('fixture foreign owner')) if candidate==fallback
                else real(candidate,private)):
            with self.assertRaisesRegex(Failure,'foreign owner'):
                bridge.selected_style(self.config/'plasmarc')
        self.assertEqual(fallback.read_bytes(),original)

    def test_selected_style_matches_native_kconfig_precedence(self):
        if not shutil.which('kreadconfig6'): self.skipTest('kreadconfig6 unavailable')
        fallback=self.config/'kdedefaults/plasmarc'
        atomic(fallback,b'[Theme]\nname=IrixClassic\n')
        home=self.base/'native-home'; home.mkdir(mode=0o700)
        environment={**os.environ,'HOME':str(home),'XDG_CONFIG_HOME':str(self.config),
            'XDG_CONFIG_DIRS':str(fallback.parent)}
        for key in ('DISPLAY','WAYLAND_DISPLAY','DBUS_SESSION_BUS_ADDRESS','DBUS_SYSTEM_BUS_ADDRESS'):
            environment.pop(key,None)
        for override in (b'[Theme]\nother=value\n',b'[Theme]\nname=\n',
                b'[Theme]\nname=Breeze\n',b'[Theme]\nname[$i]=IrixClassicDomainOS\n',
                b'[Theme]\nname[$d]\n',b'[Theme]\nname[$d]=\n'):
            with self.subTest(override=override):
                atomic(self.config/'plasmarc',override)
                result=subprocess.run(['kreadconfig6','--file','plasmarc','--group','Theme',
                    '--key','name','--default','absent'],cwd=self.base,env=environment,
                    capture_output=True,text=True,timeout=5)
                self.assertEqual(result.returncode,0,result.stderr)
                native=result.stdout.removesuffix('\n')
                self.assertEqual(bridge.selected_style(self.config/'plasmarc'),
                    None if native=='absent' else native)

    def test_fallback_does_not_bypass_receipt_authorization(self):
        atomic(self.config/'kdedefaults/plasmarc',b'[Theme]\nname=IrixClassic\n')
        atomic(self.config/'plasmarc',b'[Theme]\nother=value\n')
        style=bridge.selected_style(self.config/'plasmarc')
        for status in ('prepared','committing','recovery_needed','invalid'):
            self.assertIsNone(bridge.action_for(style,{'status':status}))
        self.record['status']='prepared'; atomic(self.receipt,json.dumps(self.record).encode())
        with self.assertRaisesRegex(Failure,'pendente'): self.install()
        self.assertFalse(self.locations['runtime'].exists())

    def test_install_is_private_complete_and_idempotent(self):
        with patch.object(bridge,'service_command',side_effect=AssertionError('service start without --iniciar')):
            self.install()
            controls=list((self.locations['state']/'control-backups').glob('*/receipt.json'))
            installs=list((self.locations['state']/'installations/backups').glob('*/receipt.json'))
            self.assertEqual(len(controls),1); self.assertEqual(len(installs),1)
            self.install()
            self.assertEqual(list((self.locations['state']/'control-backups').glob('*/receipt.json')),controls)
            self.assertEqual(list((self.locations['state']/'installations/backups').glob('*/receipt.json')),installs)
        control=bridge.read_control(self.locations)
        self.assertTrue(control['enabled'])
        copied={p.name for p in (self.locations['runtime']/'tools').iterdir()}
        self.assertEqual(copied,set(bridge.MODULES))
        self.assertNotIn(str(self.source),self.locations['unit'].read_text())
        self.assertIn(str(self.locations['runtime']),self.locations['unit'].read_text())

    def test_previous_complete_runtime_can_upgrade_without_bypassing_edit_guards(self):
        previous_modules = tuple(name for name in bridge.MODULES
            if name not in ('domainos_color_migration.py', 'domainos_native_menu.py'))
        with patch.object(bridge, 'MODULES', previous_modules):
            self.install()
        self.assertFalse((self.locations['runtime']/'tools/domainos_color_migration.py').exists())
        with self.assertRaises(Failure):
            bridge.read_control(self.locations)
        guarded = self.locations['runtime']/'tools/activate_domainos.py'
        original = guarded.read_bytes()
        guarded.write_bytes(original + b'\n# edited after installation\n')
        with self.assertRaises(Failure):
            self.install()
        self.assertFalse((self.locations['runtime']/'tools/domainos_color_migration.py').exists())
        guarded.write_bytes(original)
        self.install()
        self.assertEqual({p.name for p in (self.locations['runtime']/'tools').iterdir()}, set(bridge.MODULES))
        bridge.read_control(self.locations)
        self.assertEqual((self.config/'other-app.conf').read_bytes(),b'unchanged\n')
        self.assertEqual((self.config/'plasmarc').read_bytes(),b'[Theme]\nname=IrixClassicDomainOS\n')
        self.assertEqual(json.loads(self.receipt.read_text()),self.record)
        copied_runtime=self.locations['runtime']/'tools'
        result=subprocess.run(['/usr/bin/python3','-B','-c',
            'import sys;sys.path.insert(0,sys.argv[1]);import domainos_style_bridge,activate_domainos;'
            'assert hasattr(activate_domainos,"restore");'
            'assert hasattr(domainos_style_bridge,"watch");print("closure-ok")',str(copied_runtime)],
            cwd=self.base,env={**os.environ,'PYTHONPATH':'','PYTHONDONTWRITEBYTECODE':'1'},
            text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'closure-ok')

    def test_ten_module_runtime_upgrades_with_complete_native_import_dependency(self):
        previous = tuple(name for name in bridge.MODULES if name != 'domainos_native_menu.py')
        with patch.object(bridge, 'MODULES', previous):
            self.install()
        self.assertFalse((self.locations['runtime']/'tools/domainos_native_menu.py').exists())
        with self.assertRaises(Failure):
            bridge.read_control(self.locations)
        self.install()
        bridge.read_control(self.locations)
        result=subprocess.run(['/usr/bin/python3','-B','-c',
            'import sys;sys.path.insert(0,sys.argv[1]);'
            'import domainos_style_bridge,install_suite,domainos_native_menu;'
            'assert hasattr(domainos_native_menu,"prepared_source_pairs");'
            'print("native-closure-ok")', str(self.locations['runtime']/'tools')],
            cwd=self.base, env={**os.environ, 'PYTHONPATH':'', 'PYTHONDONTWRITEBYTECODE':'1'},
            text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'native-closure-ok')
        self.assertEqual((self.config/'other-app.conf').read_bytes(),b'unchanged\n')

    def test_upgrade_has_script_unit_control_backups_and_guards_edits(self):
        self.install()
        original=(self.locations['runtime']/'tools/domainos_style_bridge.py').read_bytes()
        with (self.source/'tools/domainos_style_bridge.py').open('ab') as stream: stream.write(b'\n# next private fixture revision\n')
        self.install()
        current=(self.locations['runtime']/'tools/domainos_style_bridge.py').read_bytes()
        self.assertNotEqual(original,current)
        bundle=bridge.Bundle(self.locations['state']/'installations',(self.locations['runtime'],self.locations['unit']))
        receipt,record=bundle.latest()
        self.assertEqual(record['status'],'installed')
        runtime_entry=next(entry for entry in record['entries'] if entry['destination']==str(self.locations['runtime']))
        self.assertEqual((receipt.parent/runtime_entry['saved']/'tools/domainos_style_bridge.py').read_bytes(),original)
        self.assertEqual(len(list((self.locations['state']/'control-backups').glob('*/receipt.json'))),2)
        atomic(self.locations['unit'],self.locations['unit'].read_bytes()+b'# user edit\n')
        before=self.locations['unit'].read_bytes()
        with self.assertRaisesRegex(Failure,'Edição posterior'): self.install()
        self.assertEqual(self.locations['unit'].read_bytes(),before)

    def test_refuses_unopted_and_pending_profiles(self):
        atomic(self.locations['unit'],b'[Service]\nExecStart=/bin/true\n')
        with self.assertRaisesRegex(Failure,'sem recibo'): self.install()
        self.locations['unit'].unlink()
        self.record['status']='prepared'; atomic(self.receipt,json.dumps(self.record).encode())
        with self.assertRaisesRegex(Failure,'pendente'): self.install()
        self.record['status']='active'; atomic(self.receipt,json.dumps(self.record).encode())
        (self.locations['activation']/'latest').unlink()
        with self.assertRaises(Failure): self.install()
        self.assertFalse(self.locations['runtime'].exists())

    def test_control_permissions_links_and_owner_guard(self):
        self.install(); control=self.locations['state']/'control.json'
        os.chmod(control,0o644)
        with self.assertRaisesRegex(Failure,'0600'): bridge.read_control(self.locations)
        os.chmod(control,0o600)
        value=json.loads(control.read_text()); value['uid']=os.getuid()+1
        atomic(control,json.dumps(value).encode())
        with self.assertRaisesRegex(Failure,'usuário'): bridge.read_control(self.locations)
        control.unlink(); control.symlink_to(self.receipt)
        with self.assertRaisesRegex(Failure,'Link simbólico'): bridge.read_control(self.locations)

    def test_systemd_escaping_and_explicit_start(self):
        path='/a/"b"/%/$name/c\\d'
        self.assertEqual(bridge.quoted(path),'"/a/\\"b\\"/%%/$name/c\\\\d"')
        self.assertEqual(bridge.quoted(path, command=True),'"/a/\\"b\\"/%%/$$name/c\\\\d"')
        for command in (False, True):
            for control in ('\n', '\r', '\t', '\0', '\x1f', '\x7f'):
                with self.subTest(command=command, control=repr(control)):
                    with self.assertRaises(Failure):
                        bridge.quoted('/a'+control+'/b', command=command)
        self.install()
        with patch.object(bridge,'session_owner') as owner, patch.object(bridge,'service_command') as run:
            bridge.start_bridge(self.locations)
            owner.assert_called_once()
            self.assertEqual([call.args[0] for call in run.call_args_list],
                [['daemon-reload'],['enable',bridge.UNIT],['restart',bridge.UNIT]])

    def test_special_xdg_unit_runtime_closure_idempotence_and_restore(self):
        special=self.base/'profile space % $BRIDGE_TEST_CANARY " \\ tail'
        data,config,state=(special/name for name in ('data', 'config', 'state'))
        for directory in (data,config,state): directory.mkdir(parents=True, mode=0o700)
        locations=bridge.paths(data,config,state)
        receipt=locations['activation']/'backups'/self.token/'receipt.json'
        atomic(receipt,(json.dumps(self.record)+'\n').encode())
        atomic(locations['activation']/'latest',(self.token+'\n').encode())
        protected={config/'plasmarc':b'[Theme]\nname=IrixClassicDomainOS\n',
            config/'other-app.conf':b'unchanged\n',receipt:receipt.read_bytes(),
            locations['activation']/'latest':(self.token+'\n').encode()}
        for path,content in protected.items(): atomic(path,content)
        environment={**os.environ,'HOME':str(special/'home'),
            'XDG_DATA_HOME':str(data),'XDG_CONFIG_HOME':str(config),
            'XDG_STATE_HOME':str(state),'XDG_CACHE_HOME':str(special/'cache'),
            'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':'',
            'BRIDGE_TEST_CANARY':'must-not-be-expanded'}
        for key in ('DISPLAY','WAYLAND_DISPLAY','XAUTHORITY','DBUS_SESSION_BUS_ADDRESS',
                'DBUS_SYSTEM_BUS_ADDRESS'):
            environment.pop(key,None)
        with contextlib.redirect_stdout(io.StringIO()), \
                patch.object(bridge,'service_command',side_effect=AssertionError('unexpected systemctl')):
            bridge.install_bridge(data,config,state,self.source)
            bundle=bridge.Bundle(locations['state']/'installations',
                (locations['runtime'],locations['unit']))
            first=bundle.latest()
            fingerprints={key:bridge.fingerprint(locations[key]) for key in ('runtime','unit')}
            control=(locations['state']/'control.json').read_bytes()
            bridge.install_bridge(data,config,state,self.source)
            self.assertEqual(bundle.latest(),first)
            self.assertEqual((locations['state']/'control.json').read_bytes(),control)
            self.assertEqual({key:bridge.fingerprint(locations[key]) for key in ('runtime','unit')},fingerprints)

        lines=locations['unit'].read_text().splitlines()
        command=next(line.removeprefix('ExecStart=') for line in lines if line.startswith('ExecStart='))
        variables=[line.removeprefix('Environment=') for line in lines if line.startswith('Environment=')]
        self.assertIn('$$BRIDGE_TEST_CANARY',command)
        self.assertNotIn('must-not-be-expanded',command)
        self.assertTrue(all('$$BRIDGE_TEST_CANARY' not in value for value in variables))
        # Decode only the documented literal escapes used by this unit, not a
        # general systemd parser. Actual service startup remains outside the test.
        argv=[word.replace('%%','%').replace('$$','$') for word in shlex.split(command)]
        self.assertEqual(argv,['/usr/bin/python3',
            str(locations['runtime']/'tools/domainos_style_bridge.py'),'--observar'])
        parsed_environment={}
        for assignment in variables:
            decoded=shlex.split(assignment)
            self.assertEqual(len(decoded),1)
            key,value=decoded[0].replace('%%','%').split('=',1)
            parsed_environment[key]=value
        self.assertEqual({key:parsed_environment[key] for key in
            ('XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_STATE_HOME')},
            {'XDG_DATA_HOME':str(data),'XDG_CONFIG_HOME':str(config),'XDG_STATE_HOME':str(state)})
        environment.update(parsed_environment)
        shutil.rmtree(self.source)
        checked=subprocess.run([*argv[:-1],'--verificar'],cwd=self.base,env=environment,
            text=True,capture_output=True,timeout=10)
        self.assertEqual(checked.returncode,0,checked.stderr)
        self.assertEqual(json.loads(checked.stdout),{'uid':os.getuid(),'panel_status':'active',
            'bridge_installed':True,'enabled':True,'selected_style':'IrixClassicDomainOS'})
        self.assertEqual({key:bridge.fingerprint(locations[key]) for key in ('runtime','unit')},fingerprints)
        self.assertEqual((locations['state']/'control.json').read_bytes(),control)
        with bundle.locked(), contextlib.redirect_stdout(io.StringIO()): bundle.restore()
        self.assertFalse(locations['runtime'].exists())
        self.assertFalse(locations['unit'].exists())
        self.assertEqual(bundle.latest()[1]['status'],'restored')
        for path,content in protected.items(): self.assertEqual(path.read_bytes(),content)

    def test_suite_detach_disables_only_new_global_worker_and_keeps_runtime_for_recovery(self):
        self.receipt.unlink();(self.locations['activation']/'latest').unlink()
        with contextlib.redirect_stdout(io.StringIO()),patch.object(bridge,'effective_preference',return_value='org.kde.breeze.desktop'):
            bridge.install_bridge(self.data,self.config,self.state,self.source,global_choices=True)
        before=(self.locations['state']/'control.json').read_bytes()
        runtime=bridge.fingerprint(self.locations['runtime'])
        self.assertEqual(bridge.detach_global_choices(self.data,self.config,self.state,dry=True)['status'],'ready')
        self.assertEqual((self.locations['state']/'control.json').read_bytes(),before)
        with contextlib.redirect_stdout(io.StringIO()):
            result=bridge.detach_global_choices(self.data,self.config,self.state)
        self.assertEqual(result['status'],'detached')
        control=bridge.read_control(self.locations)
        self.assertFalse(control['enabled']);self.assertFalse(control['global_enabled'])
        self.assertFalse(control['style_enabled'])
        self.assertEqual(bridge.fingerprint(self.locations['runtime']),runtime)
        self.assertFalse((self.locations['activation']/'latest').exists())

    def test_suite_detach_preserves_prior_style_opt_in_and_rejects_runtime_edits(self):
        self.install()
        with contextlib.redirect_stdout(io.StringIO()),patch.object(bridge,'effective_preference',return_value=bridge.IRIX_GLOBAL_THEMES[0]):
            bridge.install_bridge(self.data,self.config,self.state,self.source,global_choices=True)
        source=self.locations['runtime']/'tools/activate_domainos.py'
        original=source.read_bytes();source.write_bytes(original+b'# personal edit\n')
        before=(self.locations['state']/'control.json').read_bytes()
        with self.assertRaisesRegex(Failure,'Edição posterior'):
            bridge.detach_global_choices(self.data,self.config,self.state,dry=True)
        self.assertEqual((self.locations['state']/'control.json').read_bytes(),before)
        source.write_bytes(original)
        with contextlib.redirect_stdout(io.StringIO()):
            result=bridge.detach_global_choices(self.data,self.config,self.state)
        self.assertTrue(result['style_enabled']);self.assertTrue(result['enabled'])
        control=bridge.read_control(self.locations)
        self.assertFalse(control['global_enabled']);self.assertTrue(control['style_enabled'])
        self.assertEqual(self.receipt.read_bytes(),(json.dumps(self.record)+'\n').encode())

    def test_real_qt_global_choices_wait_for_style_and_restore_only_owned_activation(self):
        from PyQt6.QtCore import QCoreApplication
        application=QCoreApplication.instance() or QCoreApplication([])
        self.receipt.unlink();(self.locations['activation']/'latest').unlink()
        initial=bridge.IRIX_GLOBAL_THEMES[0]
        atomic(self.config/'kdeglobals',('[KDE]\nLookAndFeelPackage='+initial+'\n').encode())
        atomic(self.config/'plasmarc',b'[Theme]\nname=IrixClassic\n')
        marker=self.base/'global-executed.json'
        fake='''import json,os,pathlib,sys
state=pathlib.Path(os.environ['XDG_STATE_HOME'])/'irixium-domainos-panel'
pointer=state/'latest'
token=pointer.read_text().strip() if pointer.exists() else 'b'*32
receipt=state/'backups'/token/'receipt.json';receipt.parent.mkdir(parents=True,exist_ok=True)
value=json.loads(receipt.read_text()) if receipt.exists() else {'format':1,'uid':os.getuid(),'token':token,'plugin':'org.irixclassic.domainos.panel'}
value['status']='restored' if '--restaurar' in sys.argv else 'active'
value['origin']='global' if '--global' in sys.argv else 'manual'
receipt.write_text(json.dumps(value));pointer.write_text(token+'\\n')
marker=pathlib.Path(os.environ['DOMAINOS_BRIDGE_TEST_MARKER'])
rows=json.loads(marker.read_text()) if marker.exists() else []
rows.append(sys.argv[1:]);marker.write_text(json.dumps(rows))
'''
        atomic(self.source/'tools/activate_domainos.py',fake.encode())
        with contextlib.redirect_stdout(io.StringIO()):
            bridge.install_bridge(self.data,self.config,self.state,self.source,global_choices=True,panel=42)
        def calls():return json.loads(marker.read_text()) if marker.exists() else []
        def pump(predicate,timeout=5):
            end=time.monotonic()+timeout
            while time.monotonic()<end:
                application.processEvents()
                if predicate():return True
                time.sleep(.005)
            return False
        with patch.dict(os.environ,{'DOMAINOS_BRIDGE_TEST_MARKER':str(marker)}), \
                patch.object(bridge,'session_owner'),contextlib.redirect_stdout(io.StringIO()):
            observer=bridge.watch(self.locations,application)
            self.assertEqual(calls(),[])
            atomic(self.config/'kdeglobals',('[KDE]\nLookAndFeelPackage='+bridge.GLOBAL_THEME+'\n').encode())
            observer.changed() # Observe the real KConfig value before the asynchronous style commit.
            self.assertIsNone(observer.process);self.assertEqual(calls(),[])
            atomic(self.config/'plasmarc',b'[Theme]\nname=IrixClassicDomainOS\n')
            self.assertTrue(pump(lambda:len(calls())==1 and observer.process is None))
            self.assertEqual(calls(),[['--global','--painel','42']])
            atomic(self.config/'kdeglobals',('[KDE]\nLookAndFeelPackage='+bridge.IRIX_GLOBAL_THEMES[1]+'\n').encode())
            self.assertTrue(pump(lambda:len(calls())==2 and observer.process is None))
            self.assertEqual(calls()[1],['--global','--ponte','--restaurar'])
            # A manual Style change is independent when this installed mode is Global-only.
            atomic(self.config/'plasmarc',b'[Theme]\nname=IrixClassicDomainOS\n')
            end=time.monotonic()+.15
            while time.monotonic()<end:application.processEvents();time.sleep(.005)
            self.assertEqual(len(calls()),2)
            value=bridge.read_control(self.locations);value['enabled']=False
            bridge.write_control(self.locations,value,'private-test-disable');application.processEvents()
            observer.watcher.removePaths(observer.watcher.files()+observer.watcher.directories())
            observer.deleteLater();application.processEvents()

    def test_failed_activation_rollback_receipt_does_not_create_a_retry_loop(self):
        from PyQt6.QtCore import QCoreApplication
        application=QCoreApplication.instance() or QCoreApplication([])
        self.receipt.unlink();(self.locations['activation']/'latest').unlink()
        initial=bridge.IRIX_GLOBAL_THEMES[0]
        atomic(self.config/'kdeglobals',('[KDE]\nLookAndFeelPackage='+initial+'\n').encode())
        atomic(self.config/'plasmarc',b'[Theme]\nname=IrixClassic\n')
        marker=self.base/'failed-global-executed.json'
        fake='''import json,os,pathlib,sys,uuid
state=pathlib.Path(os.environ['XDG_STATE_HOME'])/'irixium-domainos-panel'
token=uuid.uuid4().hex
receipt=state/'backups'/token/'receipt.json';receipt.parent.mkdir(parents=True,exist_ok=True)
value={'format':1,'uid':os.getuid(),'token':token,'plugin':'org.irixclassic.domainos.panel','status':'restored','origin':'global'}
receipt.write_text(json.dumps(value));(state/'latest').write_text(token+'\\n')
marker=pathlib.Path(os.environ['DOMAINOS_BRIDGE_TEST_MARKER'])
rows=json.loads(marker.read_text()) if marker.exists() else []
rows.append(sys.argv[1:]);marker.write_text(json.dumps(rows))
sys.exit(1)
'''
        atomic(self.source/'tools/activate_domainos.py',fake.encode())
        with contextlib.redirect_stdout(io.StringIO()):
            bridge.install_bridge(self.data,self.config,self.state,self.source,global_choices=True)
        def calls():return json.loads(marker.read_text()) if marker.exists() else []
        def pump(timeout=.3):
            end=time.monotonic()+timeout
            while time.monotonic()<end:application.processEvents();time.sleep(.005)
        with patch.dict(os.environ,{'DOMAINOS_BRIDGE_TEST_MARKER':str(marker)}), \
                patch.object(bridge,'session_owner'),contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            observer=bridge.watch(self.locations,application)
            atomic(self.config/'plasmarc',b'[Theme]\nname=IrixClassicDomainOS\n')
            atomic(self.config/'kdeglobals',('[KDE]\nLookAndFeelPackage='+bridge.GLOBAL_THEME+'\n').encode())
            pump(1)
            self.assertEqual(calls(),[['--global']])
            self.assertIsNone(observer.process)
            self.assertEqual(bridge.activation_record(self.locations)[1]['status'],'restored')
            # Receipt replacement and an atomic rewrite of the unchanged
            # preference are not new choices and cannot repeat the failure.
            atomic(self.config/'kdeglobals',('[KDE]\nLookAndFeelPackage='+bridge.GLOBAL_THEME+'\n').encode())
            observer.changed();pump()
            self.assertEqual(len(calls()),1)
            atomic(self.config/'kdeglobals',('[KDE]\nLookAndFeelPackage='+initial+'\n').encode())
            pump()
            atomic(self.config/'kdeglobals',('[KDE]\nLookAndFeelPackage='+bridge.GLOBAL_THEME+'\n').encode())
            pump(1)
            self.assertEqual(calls(),[['--global'],['--global','--ponte']])
            value=bridge.read_control(self.locations);value['enabled']=False
            bridge.write_control(self.locations,value,'private-test-disable');application.processEvents()
            observer.watcher.removePaths(observer.watcher.files()+observer.watcher.directories())
            observer.deleteLater();application.processEvents()

    def test_real_qt_file_changes_dispatch_only_two_authorized_styles(self):
        from PyQt6.QtCore import QCoreApplication
        application=QCoreApplication.instance() or QCoreApplication([])
        marker=self.base/'executed.json'
        # An isolated child only logs arguments and updates its own fixture
        # receipt. It never owns a Plasma bus or touches desktop configuration.
        fake='''import json,os,pathlib,sys
state=pathlib.Path(os.environ['XDG_STATE_HOME'])/'irixium-domainos-panel'
token=(state/'latest').read_text().strip()
receipt=state/'backups'/token/'receipt.json'
value=json.loads(receipt.read_text());value['status']='restored' if '--restaurar' in sys.argv else 'active'
receipt.write_text(json.dumps(value))
marker=pathlib.Path(os.environ['DOMAINOS_BRIDGE_TEST_MARKER'])
rows=json.loads(marker.read_text()) if marker.exists() else []
rows.append(sys.argv[1:]);marker.write_text(json.dumps(rows))
'''
        atomic(self.source/'tools/activate_domainos.py',fake.encode())
        self.install()

        def pump(predicate,timeout=5):
            end=time.monotonic()+timeout
            while time.monotonic()<end:
                application.processEvents()
                if predicate(): return True
                time.sleep(.005)
            return False

        def calls(): return json.loads(marker.read_text()) if marker.exists() else []

        with patch.dict(os.environ,{'DOMAINOS_BRIDGE_TEST_MARKER':str(marker)}), \
                patch.object(bridge,'session_owner'), contextlib.redirect_stdout(io.StringIO()):
            observer=bridge.watch(self.locations,application)
            self.assertIsNone(observer.process); self.assertEqual(calls(),[])
            atomic(self.config/'plasmarc',b'[Theme]\nname=IrixClassic\n')
            self.assertTrue(pump(lambda:len(calls())==1 and observer.process is None))
            self.assertEqual(calls(),[['--ponte','--restaurar']])
            # Atomic replacement must re-arm the plasmarc watch.
            atomic(self.config/'plasmarc',b'[Theme]\nname=Breeze\n')
            self.assertTrue(pump(lambda:bridge.selected_style(self.config/'plasmarc')=='Breeze',.2))
            atomic(self.config/'plasmarc',b'[Theme]\nname=IrixClassicDomainOS\n')
            self.assertTrue(pump(lambda:len(calls())==2 and observer.process is None))
            self.assertEqual(calls()[1],['--ponte'])
            atomic(self.config/'plasmarc',b'[Theme]\nname=IrixClassicDomainOS\n')
            end=time.monotonic()+.15
            while time.monotonic()<end: application.processEvents(); time.sleep(.005)
            self.assertEqual(len(calls()),2)
            # Native Global Theme application can remove the override and then
            # change only kdedefaults on the next roundtrip. Both the file and
            # its directory must be re-armed after atomic replacement.
            fallback=self.config/'kdedefaults/plasmarc'
            atomic(fallback,b'[Theme]\nname=IrixClassic\n')
            atomic(self.config/'plasmarc',b'[Theme]\nother=preserved\n')
            self.assertTrue(pump(lambda:len(calls())==3 and observer.process is None))
            self.assertEqual(calls()[2],['--ponte','--restaurar'])
            override=(self.config/'plasmarc').read_bytes()
            atomic(fallback,b'[Theme]\nname=IrixClassicDomainOS\n')
            self.assertTrue(pump(lambda:len(calls())==4 and observer.process is None))
            self.assertEqual(calls()[3],['--ponte'])
            self.assertEqual((self.config/'plasmarc').read_bytes(),override)
            # A literal empty override masks the fallback and performs no
            # action, even when the watched fallback changes to Classic.
            atomic(self.config/'plasmarc',b'[Theme]\nname=\n')
            atomic(fallback,b'[Theme]\nname=IrixClassic\n')
            end=time.monotonic()+.15
            while time.monotonic()<end: application.processEvents(); time.sleep(.005)
            self.assertEqual(len(calls()),4)
            value=bridge.read_control(self.locations);value['enabled']=False
            bridge.write_control(self.locations,value,'private-test-disable')
            atomic(self.config/'plasmarc',b'[Theme]\nname=IrixClassic\n')
            end=time.monotonic()+.15
            while time.monotonic()<end: application.processEvents(); time.sleep(.005)
            self.assertEqual(len(calls()),4)
            observer.watcher.removePaths(observer.watcher.files()+observer.watcher.directories())
            observer.deleteLater(); application.processEvents()
        self.assertEqual((self.config/'other-app.conf').read_bytes(),b'unchanged\n')


if __name__=='__main__': unittest.main()
