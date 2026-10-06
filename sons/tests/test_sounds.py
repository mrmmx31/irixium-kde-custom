# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Deterministic tests with private synthetic AIFF fixtures, not SGI replacement audio."""
from __future__ import annotations
import copy
import io
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import irix_sounds as S
import sound_transaction as TX


def aiff(channels=1, rate=44100, frames=441):
    # 80-bit extended encoding with an explicit integer bit.
    exponent = rate.bit_length() - 1
    ext = struct.pack('>HQ', 16383 + exponent, rate << (63-exponent))
    pcm = b''.join(struct.pack('>h', ((i % 33)-16)*400) for i in range(frames*channels))
    comm = struct.pack('>hIh', channels, frames, 16) + ext
    ssnd = b'\0'*8 + pcm
    body = b'AIFF' + b'COMM' + struct.pack('>I', len(comm)) + comm + b'SSND' + struct.pack('>I', len(ssnd)) + ssnd
    return b'FORM' + struct.pack('>I', len(body)) + body, pcm


def source_spec(data, filename='fixture.aiff'):
    return {'original_filename':filename, 'source_size':len(data), 'git_blob_sha1':S.git_blob(data)}


class CatalogTests(unittest.TestCase):
    def setUp(self): self.c = S.catalog()
    def test_nineteen_sources(self): self.assertEqual(len(self.c['sounds']),19)
    def test_eight_selected_sources(self): self.assertEqual(sum(bool(s['events']) for s in self.c['sounds']),8)
    def test_twentyfour_unique_events(self):
        ev=[e for s in self.c['sounds'] for e in s['events']]
        self.assertEqual(len(ev),24); self.assertEqual(len(set(ev)),24)
    def test_source_bytes(self): self.assertEqual(sum(s['source_size'] for s in self.c['sounds'] if s['events']),668084)
    def test_no_dolphin_aliases(self):
        for s in self.c['sounds']:
            for e in s['events']: self.assertFalse(e.startswith(('file-','item-','trash-','window-')))
    def test_historical_unused(self):
        for s in self.c['sounds']:
            if s['id'] in ('deskswitch','dropignore','putaway','folder','remote-folder','move','copy','trash','remove','launch','shift'):
                self.assertEqual(s['events'],[])
    def test_kcm_previews_available(self):
        events={e for s in self.c['sounds'] for e in s['events']}
        self.assertTrue({'theme-demo','bell-window-system','dialog-warning','message-new-instant','battery-caution','device-added'}<=events)
    def test_warning_is_not_filearrival(self):
        for s in self.c['sounds']:
            if s['id']=='arrival':self.assertNotIn('dialog-warning',s['events'])
    def test_boot_not_faked(self):
        self.assertIn('desktop-login',self.c['disabled_events'])
        self.assertIn('system-shutdown',self.c['disabled_events'])
    def test_no_alarm_disabled(self):
        self.assertFalse(any(e.startswith(('dialog','battery','device')) for e in self.c['disabled_events']))
    def test_urls_pinned_https(self):
        for s in self.c['sounds']:
            urls=S.source_urls(self.c,s)
            self.assertIn(self.c['source_mirror']['commit'],urls[0][0])
            self.assertTrue(all(u.startswith('https://') for u,_ in urls))
    def test_template_not_empty(self):
        text=(ROOT/'modelo/index.theme').read_text()
        self.assertTrue(text.startswith('[Sound Theme]'))
        self.assertIn('OutputProfile=stereo',text)
        self.assertIn('Inherits=freedesktop',text)
    def test_no_audio_in_package(self):
        self.assertFalse(any(p.suffix.lower() in ('.wav','.aif','.aiff','.aifc','.oga','.ogg') for p in ROOT.rglob('*')))
    def test_only_read_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'kdeglobals'; data=b'[KDE]\nwidgetStyle=kvantum\n[Sounds]\nTheme=ocean\nEnable=false\n'
            p.write_bytes(data)
            self.assertEqual(S.installed_selection(Path(tmp)),{'Theme':'ocean','Enable':'false'})
            self.assertEqual(p.read_bytes(),data)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
        self.data,_=aiff(); self.spec=source_spec(self.data)
    def tearDown(self):self.t.cleanup()
    def test_valid_aiff(self): S.check_source(self.data,self.spec)
    def test_bad_hash(self):
        with self.assertRaises(S.Failure):S.check_source(self.data[:-1]+b'x',self.spec)
    def test_wrong_size(self):
        with self.assertRaises(S.Failure):S.check_source(self.data+b'\0',self.spec)
    def test_html_not_audio(self):
        x=b'<html>'*20
        with self.assertRaises(S.Failure):S.check_source(x,source_spec(x))
    def test_truncated_form(self):
        x=self.data[:4]+struct.pack('>I',len(self.data)+300)+self.data[8:]
        with self.assertRaises(S.Failure):S.check_source(x,source_spec(x))
    def test_network_requires_optin(self):
        with patch.object(S,'fetch_bytes',side_effect=AssertionError('network')):
            with self.assertRaises(S.Failure):S.obtain_source(S.catalog(),self.spec,self.root,None,False)
        self.assertEqual(list(self.root.iterdir()),[])
    def test_local_source_used(self):
        (self.root/self.spec['original_filename']).write_bytes(self.data)
        got,label=S.obtain_source(S.catalog(),self.spec,self.root/'cache',self.root,False)
        self.assertEqual(got,self.data); self.assertEqual(label,'local-pinned-source')
    def test_local_source_mismatch_not_hidden(self):
        (self.root/self.spec['original_filename']).write_bytes(b'corrupt')
        with patch.object(S,'fetch_bytes',side_effect=AssertionError('network')):
            with self.assertRaises(S.Failure):S.obtain_source(S.catalog(),self.spec,self.root/'cache',self.root,True)
    def test_cached_source_checked(self):
        f=self.root/'originais'/self.spec['original_filename'];f.parent.mkdir();f.write_bytes(self.data)
        with patch.object(S,'fetch_bytes',side_effect=AssertionError('network')):
            got,label=S.obtain_source(S.catalog(),self.spec,self.root,None,True)
        self.assertEqual(got,self.data);self.assertEqual(label,'verified-cache')
    def test_corrupted_cache_refused(self):
        f=self.root/'originais'/self.spec['original_filename'];f.parent.mkdir();f.write_bytes(b'corrupt')
        with self.assertRaises(S.Failure):S.obtain_source(S.catalog(),self.spec,self.root,None,False)
    def test_download_identity_and_cache(self):
        with patch.object(S,'fetch_bytes',return_value=self.data):
            got,_=S.obtain_source(S.catalog(),self.spec,self.root,None,True)
        f=self.root/'originais'/self.spec['original_filename']
        self.assertEqual(got,f.read_bytes());self.assertEqual(f.stat().st_mode&0o777,0o600)
    def test_download_fallback(self):
        with patch.object(S,'fetch_bytes',side_effect=[OSError('unavailable'),self.data]) as f:
            got,_=S.obtain_source(S.catalog(),self.spec,self.root,None,True)
            self.assertEqual(f.call_count,2);self.assertEqual(got,self.data)
    def test_all_sources_failed_no_file(self):
        with patch.object(S,'fetch_bytes',return_value=b'<html>'):
            with self.assertRaises(S.Failure):S.obtain_source(S.catalog(),self.spec,self.root,None,True)
        self.assertEqual(list(self.root.iterdir()),[])
    def test_http_refused(self):
        with self.assertRaises(S.Failure):S.fetch_bytes('http://example.invalid/test','raw')
    def test_insecure_redirect_refused(self):
        with self.assertRaises(S.Failure):S.HttpsOnly().redirect_request(None,None,302,'',{},'http://ftp.jurassic.nl/test')
    def test_symlink_source_refused(self):
        real=self.root/'real';real.write_bytes(self.data)
        (self.root/self.spec['original_filename']).symlink_to(real)
        with self.assertRaises(S.Failure):S.obtain_source(S.catalog(),self.spec,self.root/'cache',self.root,False)
    def test_relative_xdg_refused(self):
        with patch.dict(os.environ,{'XDG_DATA_HOME':'relative'}):
            with self.assertRaises(S.Failure):S.locations()
    def test_wav_silent_refused(self):
        p=self.root/'test.wav'
        with wave.open(str(p),'wb') as w:w.setparams((1,2,44100,441,'NONE',''));w.writeframes(b'\0'*882)
        with self.assertRaises(S.Failure):S.wav_info(p)
    def test_root_write_refused(self):
        with patch.object(os,'geteuid',return_value=0):
            with self.assertRaises(S.Failure):S.user_only()


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg indisponível')
class ConversionTests(unittest.TestCase):
    def test_real_aiff_decoder_preserves_pcm(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);data,pcm=aiff(2,44100);(r/'in.aiff').write_bytes(data)
            info=S.convert(r/'in.aiff',r/'out.wav')
            with wave.open(str(r/'out.wav'),'rb') as w:out=w.readframes(w.getnframes())
            expected=b''.join(struct.pack('<h',v[0]) for v in struct.iter_unpack('>h',pcm))
            self.assertEqual(out,expected);self.assertEqual(info['rate'],44100);self.assertEqual(info['channels'],2)
    def test_deterministic_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);(r/'in.aifc').write_bytes(aiff()[0])
            S.convert(r/'in.aifc',r/'a.wav');S.convert(r/'in.aifc',r/'b.wav')
            self.assertEqual((r/'a.wav').read_bytes(),(r/'b.wav').read_bytes())
    def test_rate_outside_profile_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp);(r/'in.aiff').write_bytes(aiff(rate=96000)[0])
            with self.assertRaises(S.Failure):S.convert(r/'in.aiff',r/'out.wav')


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg indisponível')
class ThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t=tempfile.TemporaryDirectory();cls.base=Path(cls.t.name);cls.origin=cls.base/'sources';cls.origin.mkdir()
        cls.c=copy.deepcopy(S.catalog())
        data,_=aiff()
        for s in cls.c['sounds']:
            if s['events']:
                s.update(source_spec(data,s['original_filename']))
                (cls.origin/s['original_filename']).write_bytes(data)
        cls.ready=S.prepare(cls.c,cls.base/'cache',cls.origin,False)
    @classmethod
    def tearDownClass(cls):cls.t.cleanup()
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
    def tearDown(self):self.t.cleanup()
    def test_manifest_complete(self):self.assertEqual(len(S.validate_theme(self.ready,self.c)['sources']),8)
    def test_all_aliases_generated(self):self.assertEqual(len(list((self.ready/'stereo').glob('*.wav'))),24)
    def test_disabled_zero_bytes(self):
        p=list((self.ready/'stereo').glob('*.disabled'));self.assertEqual(len(p),8)
        self.assertTrue(all(f.read_bytes()==b'' for f in p))
    def test_alias_pcm_equal(self):
        for s in self.c['sounds']:
            if s['events']:
                data={(self.ready/'stereo'/(e+'.wav')).read_bytes() for e in s['events']}
                self.assertEqual(len(data),1)
    def test_local_html_all_sources(self):
        text=(self.ready/'OUVIR.html').read_text()
        self.assertEqual(text.count('<audio'),8);self.assertNotIn('http',text)
    def test_no_global_files_generated(self):
        files=S.tree_files(self.ready)
        self.assertNotIn('kdeglobals',files);self.assertFalse(any(f.endswith('.sh') for f in files))
    def test_tamper_detected(self):
        p=self.root/'theme';shutil.copytree(self.ready,p)
        (p/'stereo/dialog-error.wav').write_bytes(b'corrupt')
        with self.assertRaises(S.Failure):S.validate_theme(p,self.c)
    def test_extra_file_refused(self):
        p=self.root/'theme';shutil.copytree(self.ready,p);(p/'extra').write_text('x')
        with self.assertRaises(S.Failure):S.validate_theme(p,self.c)
    def test_install_and_restore_real_files(self):
        dest=self.root/'data/sounds/IrixClassic';state=self.root/'state'
        S.install(self.ready,dest,state,self.c)
        self.assertEqual(S.tree_files(dest),S.tree_files(self.ready))
        tx=S.transaction(dest,state)
        with tx.locked():tx.restore()
        self.assertFalse(S.tree_files(dest))
    def test_repeat_install_is_idempotent(self):
        dest=self.root/'theme';state=self.root/'state'
        S.install(self.ready,dest,state,self.c);pointer=(state/'latest').read_bytes()
        S.install(self.ready,dest,state,self.c)
        self.assertEqual(pointer,(state/'latest').read_bytes())
    def test_unknown_install_refused(self):
        dest=self.root/'theme';dest.mkdir();(dest/'index.theme').write_text('private')
        with self.assertRaises(S.Failure):S.install(self.ready,dest,self.root/'state',self.c)
        self.assertEqual((dest/'index.theme').read_text(),'private')
    def test_restore_postedit_refused(self):
        dest=self.root/'theme';state=self.root/'state';S.install(self.ready,dest,state,self.c)
        (dest/'index.theme').write_text('private')
        with self.assertRaises(S.Failure):S.transaction(dest,state).restore()
        self.assertEqual((dest/'index.theme').read_text(),'private')
    def test_dry_install_no_write(self):
        dest=self.root/'theme';state=self.root/'state'
        S.install(self.ready,dest,state,self.c,True)
        self.assertFalse(dest.exists());self.assertFalse(state.exists())
    def test_symlink_destination_refused(self):
        dest=self.root/'theme';real=self.root/'real';real.mkdir();dest.symlink_to(real)
        with self.assertRaises(S.Failure):S.install(self.ready,dest,self.root/'state',self.c)
    def test_atomic_file_failure_rolls_back(self):
        dest=self.root/'theme';state=self.root/'state';tx=S.transaction(dest,state);count=0
        def writer(path,before,after):
            nonlocal count
            count+=1
            if count==2:raise OSError('injected interruption')
            TX.replace_checked(path,before,after)
        tx.writer=writer
        with self.assertRaises(S.Failure):tx.install([TX.Change(dest/'a',b'a'),TX.Change(dest/'b',b'b')])
        self.assertFalse((dest/'a').exists());self.assertFalse((dest/'b').exists())
        self.assertEqual(tx.latest()[1]['status'],'restored')
    def test_read_only_inventory_no_changes(self):
        cache=self.root/'cache';dest=self.root/'dest';cfg=self.root/'config'
        info=S.verify(self.c,cache,dest,cfg)
        self.assertFalse(info['network_used']);self.assertFalse(info['installed'])
        self.assertFalse(cache.exists());self.assertFalse(dest.exists());self.assertFalse(cfg.exists())


if __name__=='__main__':unittest.main()
