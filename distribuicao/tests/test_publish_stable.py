# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""Publication protocol tests with mocked GitHub; never publish during the suite."""
from pathlib import Path
import copy,json,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'distribuicao/tools'))
import build_kvantum as B
import publish_stable as P


class Publication(unittest.TestCase):
    def test_plan_is_stable_but_not_published(self):
        p,outputs,_=P.local_plan(ROOT)
        self.assertFalse(p['published']);self.assertTrue(p['stable_approved'])
        self.assertEqual(p['tag'],'irixclassic-kvantum-v0.7.1')
        self.assertEqual(set(outputs),set(p['assets']))

    def test_plan_does_not_invoke_git_or_network(self):
        with patch.object(P,'run',side_effect=AssertionError('network')):
            P.local_plan(ROOT)

    def test_known_remote_urls_only(self):
        for x in ('https://github.com/'+P.REPOSITORY+'.git','git@github.com:'+P.REPOSITORY+'.git'):
            P.check_remote_url(x)
        for x in ('https://example.com/x','https://github.com/other/repo','https://token@github.com/'+P.REPOSITORY):
            with self.assertRaises(B.Failure):P.check_remote_url(x)

    def test_parse_exact_ref_response(self):
        self.assertEqual(P.parse_refs('abc\trefs/heads/main\n'),{'refs/heads/main':'abc'})
        with self.assertRaises(B.Failure):P.parse_refs('bad response extra')

    def test_identity_no_clobber(self):
        outputs={'a.zip':b'x'};notes='notes'
        r={'tag_name':P.TAG,'name':P.TITLE,'body':notes,'draft':True,'assets':[]}
        P.check_release_identity(r,notes,outputs)
        for edit in ({'name':'other'},{'body':'different'},{'assets':[{'name':'unexpected'}]},
                     {'assets':[{'name':'a.zip'},{'name':'a.zip'}]}, {'draft':False,'prerelease':True}):
            with self.assertRaises(B.Failure):P.check_release_identity({**r,**edit},notes,outputs)

    def test_auth_or_network_error_not_treated_as_absence(self):
        with patch.object(P,'run',side_effect=B.Failure('network')):
            with self.assertRaises(B.Failure):P.find_release(ROOT)

    def test_release_pages(self):
        responses=[json.dumps([{'tag_name':'other'}]*100),json.dumps([{'tag_name':P.TAG}])]
        with patch.object(P,'run',side_effect=responses):
            self.assertEqual(P.find_release(ROOT)['tag_name'],P.TAG)

    def test_downloaded_bytes_verified(self):
        def fake(argv,cwd):
            (Path(argv[-1])/'a.zip').write_bytes(b'x');return ''
        with patch.object(P,'run',side_effect=fake):P.downloaded(ROOT,{'a.zip':b'x'},{'a.zip'})
        with patch.object(P,'run',side_effect=fake),self.assertRaises(B.Failure):P.downloaded(ROOT,{'a.zip':b'y'},{'a.zip'})

    def test_publish_protocol_order_and_receipt(self):
        head='a'*40;events=[];stored={'release':None}
        outputs={'IrixClassic-0.7.1-kvantum.zip':b'theme','IrixClassic-0.7.1-codigo.zip':b'source','SHA256SUMS':b'sums','DISTRIBUICAO.json':b'{}'}
        plan={'published':False,'signed':False,'tag':P.TAG}
        def fake(argv,cwd):
            events.append(argv)
            if argv[:3]==['git','ls-remote','--heads']:return head+'\trefs/heads/release\n'
            if argv[:3]==['git','ls-remote','--tags']:return ''
            if argv[:3]==['git','tag','--list']:return ''
            if argv[:3]==['gh','release','create']:
                stored['release']={'tag_name':P.TAG,'name':P.TITLE,'body':'notes','draft':True,'prerelease':False,'assets':[],
                                   'html_url':'https://github.com/'+P.REPOSITORY+'/releases/tag/'+P.TAG,'id':1}
            if argv[:3]==['gh','release','upload']:
                stored['release']['assets']=[{'name':n} for n in outputs]
            if argv[:3]==['gh','release','edit']:stored['release']['draft']=False
            return ''
        with tempfile.TemporaryDirectory() as d,patch.object(P.os,'geteuid',return_value=1000),\
             patch.object(P.shutil,'which',return_value='/bin/tool'),patch.object(P,'source_commit',return_value=(head,'release')),\
             patch.object(P,'local_plan',return_value=(plan,outputs,{'notes':'notes'})),patch.object(P,'run',side_effect=fake),\
             patch.object(P,'find_release',side_effect=lambda r:copy.deepcopy(stored['release'])),\
             patch.object(P,'downloaded',side_effect=lambda *a:events.append(['VERIFY',','.join(sorted(a[2]))])):
            folder=Path(d)/'assets';r=P.publish(ROOT,folder)
            self.assertTrue(r['published']);self.assertFalse(r['signed'])
            self.assertTrue((folder/'PUBLICACAO.json').is_file())
        commands=[x[:3] for x in events]
        self.assertLess(commands.index(['gh','release','upload']),commands.index(['gh','release','edit']))
        edit=next(x for x in events if x[:3]==['gh','release','edit'])
        self.assertIn('--draft=false',edit);self.assertIn('--prerelease=false',edit)
        self.assertTrue(any(e[0]=='VERIFY' and 'SHA256SUMS' in e[1] for e in events))
        flat=' '.join(' '.join(x) for x in events)
        for forbidden in ('--force','--clobber','--tags --force','git commit'):
            self.assertNotIn(forbidden,flat)

    def test_no_system_or_automatic_commit(self):
        text=(ROOT/'distribuicao/tools/publish_stable.py').read_text()
        self.assertNotIn("['sudo'",text);self.assertNotIn("['git','commit'",text)
        self.assertNotIn("['git','push','--tags'",text)


if __name__=='__main__':unittest.main()
