# SPDX-FileCopyrightText: 2026 mrmmx31
# SPDX-License-Identifier: GPL-3.0-or-later
"""The promotion is explicit and metadata-only, not another desktop acceptance gate."""
import copy, hashlib, json, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'distribuicao/tools'))
import build_kvantum as B
import promotion_contract as P


class StablePromotion(unittest.TestCase):
    def setUp(self):
        self.policy=json.loads((ROOT/'distribuicao/LANCAMENTO.json').read_text())
        self.promotion=json.loads((ROOT/'distribuicao/promocoes/0.7.1.json').read_text())

    def test_explicit_authority(self):
        self.assertEqual(self.promotion['authorized_by'],'mrmmx31')
        self.assertEqual(self.promotion['authorization_date'],'2026-10-06')
        self.assertTrue(P.validate(ROOT,self.policy)['stable_approved'])

    def test_acceptance_preserved_as_candidate_history(self):
        c=json.loads((ROOT/'distribuicao/historico/CANDIDATA-0.7.1-rc1.json').read_text())
        self.assertFalse(c['stable_approved']);self.assertEqual(c['channel'],'candidate')
        self.assertEqual(self.promotion['candidate_acceptance']['status'],'candidate_accepted_locally')

    def test_config_functional_equivalence(self):
        raw=(ROOT/'kvantum/IrixClassic/IrixClassic.kvconfig').read_bytes()
        self.assertEqual(P.config_digest(raw),self.promotion['equivalence']['kvconfig_without_comment_sha256'])
        self.assertNotEqual(P.config_digest(raw.replace(b'scroll_width=18',b'scroll_width=19')),P.config_digest(raw))

    def test_svg_graphics_equivalence(self):
        raw=(ROOT/'kvantum/IrixClassic/IrixClassic.svg').read_bytes()
        self.assertEqual(P.svg_digest(raw),self.promotion['equivalence']['svg_without_title_sha256'])
        self.assertEqual(P.svg_digest(raw.replace(b'controls, 0.7.1',b'controls, 0.7.1-rc1')),P.svg_digest(raw))
        self.assertNotEqual(P.svg_digest(raw.replace(b'#919191',b'#919192',1)),P.svg_digest(raw))

    def test_frozen_art_and_installer_support(self):
        for rel,h in self.promotion['equivalence']['preserved_files'].items():
            self.assertEqual(P.digest((ROOT/rel).read_bytes()),h,rel)

    def test_missing_explicit_policy_is_rejected(self):
        for k,v in (('stable_approved',False),('theme_version','0.7.2'),('promotion_sha256','0'*64),('pending_acceptance',['x'])):
            p=copy.deepcopy(self.policy);p[k]=v
            with self.subTest(key=k),self.assertRaises(B.Failure):P.validate(ROOT,p)

    def test_release_packages_marked_stable(self):
        outputs,info=B.build_plan(ROOT)
        self.assertEqual(info['channel'],'stable');self.assertTrue(info['stable_approved'])
        self.assertEqual(info['pending_acceptance'],[])
        self.assertTrue(any(n=='IrixClassic-0.7.1-kvantum.zip' for n in outputs))
        self.assertNotIn('published',info)

    def test_pristine_history_not_packaged_as_current_policy(self):
        spec=json.loads((ROOT/'distribuicao/ARQUIVOS.json').read_text())
        self.assertIn('distribuicao/LANCAMENTO.json',spec['source_files'])
        self.assertNotIn('distribuicao/CANDIDATA.json',spec['source_files'])

    def test_title_no_rc_and_notes_honest(self):
        readme=(ROOT/'kvantum/IrixClassic/README.md').read_text()
        self.assertIn('# IrixClassic 0.7.1 — Kvantum estável',readme)
        self.assertIn('somente leitura',readme)
        notes=(ROOT/'distribuicao/NOTAS-0.7.1.md').read_text()
        self.assertIn('87 verificações',notes);self.assertIn('não é assinada',notes)

    def test_every_manifest_file_checks(self):
        files={p.name:p.read_bytes() for p in (ROOT/'kvantum/IrixClassic').iterdir() if p.is_file()}
        self.assertEqual(B.check_theme(files),'0.7.1')


if __name__=='__main__':unittest.main()
