import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import demo

class AdminDemoTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.fixtures=self.root/'fixtures'
        shutil.copytree(ROOT/'fixtures',self.fixtures)
        self.db=self.root/'demo.sqlite'
        self.conn=demo.connect(self.db)
        self.addCleanup(self.conn.close)
    def build(self): return demo.build(self.fixtures,'J-SYN-100','P-SYN-101')
    def edit(self,file,change):
        path=self.fixtures/file; data=json.loads(path.read_text(encoding='utf-8')); change(data)
        path.write_text(json.dumps(data),encoding='utf-8')
    def test_fixture_answer_key_and_source_refs(self):
        pack=self.build(); key=json.loads((ROOT/'fixture-answer-key.json').read_text())
        self.assertEqual(pack['missing'],key['target']['missing'])
        self.assertEqual(pack['conflicts'],key['target']['conflicts'])
        self.assertEqual({r['doc_id']+':'+r['revision']+':'+r['passage_id'] for r in pack['source_manifest']},set(key['target']['source_refs']))
        for field,item in pack['fields'].items():
            self.assertEqual([c['value'] for c in item['candidates']],key['target']['values'][field])
            for candidate in item['candidates']:
                for ref in candidate['sources']:
                    raw=(self.fixtures/ref['file']).read_bytes(); doc=json.loads(raw)
                    passage=next(p for p in doc['passages'] if p['id']==ref['passage_id'])
                    self.assertEqual(doc['doc_id'],ref['doc_id']); self.assertEqual(doc['revision'],ref['revision'])
                    self.assertEqual(hashlib.sha256(raw).hexdigest(),ref['source_sha256'])
                    self.assertEqual(demo.digest(demo.encoded(passage)),ref['passage_sha256'])
                    self.assertEqual(passage['fields'][field],candidate['value'])
    def test_superseded_values_excluded(self):
        text=json.dumps(self.build()); self.assertNotIn('2026-11-01',text)
        self.assertNotIn('Fictional Reviewer A',text); self.assertNotIn('retired description',text)
    def test_exact_asset_separation(self):
        text=json.dumps(self.build()); self.assertNotIn('P-SYN-101A',text); self.assertNotIn('Reviewer B',text)
        other=demo.build(self.fixtures,'J-SYN-101','P-SYN-101A')
        self.assertEqual(other['missing'],[]); self.assertEqual(other['conflicts'],[])
        with self.assertRaisesRegex(demo.DemoError,'NO_CURRENT'): demo.build(self.fixtures,'J-SYN-100','P-SYN-101A')
    def test_irrelevant_material_excluded(self): self.assertNotIn('stationery',json.dumps(self.build()))
    def test_missing_abstention(self):
        result=demo.answer(self.build(),'coordinator'); self.assertEqual(result['state'],'missing'); self.assertEqual(result['candidates'],[])
    def test_conflicts_visible_without_winner(self):
        pack=self.build()
        for field in ['planned_date','admin_status']:
            self.assertEqual(pack['fields'][field]['state'],'conflict'); self.assertEqual(len(pack['fields'][field]['candidates']),2)
            self.assertNotIn('selected_value',pack['fields'][field])
    def test_human_queue_and_draft_handover(self):
        pack=self.build(); reasons=[q['reason'] for q in pack['human_review_queue']]
        self.assertIn('MISSING_REQUIRED_FIELD',reasons); self.assertIn('CONFLICTING_SOURCE_VALUES',reasons); self.assertIn('HUMAN_REVIEW_REQUIRED',reasons)
        self.assertEqual(pack['handover']['status'],'draft'); self.assertEqual(pack['authorization'],'NONE')
        self.assertEqual(pack['handover']['unresolved_fields'],['admin_status','coordinator','planned_date'])
    def test_unreadable_input_explicit(self):
        self.assertIn({'source':'unreadable-r1.bin','state':'UNREADABLE_OR_INVALID_SOURCE'},self.build()['ingestion_issues'])
    def test_malicious_instruction_quarantined(self):
        pack=self.build(); self.assertIn({'source':'embedded-instruction-r1.json','state':'UNTRUSTED_EMBEDDED_INSTRUCTION'},pack['ingestion_issues'])
        self.assertNotIn('Untrusted invented coordinator',json.dumps(pack)); self.assertEqual(pack['authorization'],'NONE')
    def test_unsupported_questions_abstain(self):
        for question in ['safe_to_operate','isolation_points','authorize_work','expected_savings','invented_field']:
            result=demo.answer(self.build(),question); self.assertEqual(result['state'],'ABSTAIN_UNSUPPORTED_QUESTION'); self.assertEqual(result['sources'],[])
    def test_review_is_revision_bound_and_never_authorizes(self):
        pack=self.build(); demo.save(self.conn,pack)
        reviewed=demo.review(self.conn,self.fixtures,pack['pack_id'],pack['fingerprint'],'fictional-reviewer','Reviewed the draft; unresolved issues remain.')
        self.assertEqual(reviewed['review_state'],'DRAFT_REVIEW_RECORDED'); self.assertEqual(reviewed['authorization'],'NONE')
        self.assertEqual(reviewed['missing'],['coordinator'])
    def test_source_change_invalidates_review_and_query(self):
        pack=self.build(); demo.save(self.conn,pack); demo.review(self.conn,self.fixtures,pack['pack_id'],pack['fingerprint'],'fixture-reviewer','Draft checked.')
        self.edit('job-register-r2.json',lambda d:d['passages'][0]['fields'].update(planned_date='2026-11-05'))
        old=demo.retrieve(self.conn,self.fixtures,pack['pack_id']); self.assertEqual(old['snapshot_state'],'STALE_SOURCE_SNAPSHOT'); self.assertEqual(old['reviews'][0]['state'],'STALE_REVIEW')
        self.assertEqual(demo.answer(old,'planned_date')['state'],'ABSTAIN_STALE_SNAPSHOT')
        with self.assertRaisesRegex(demo.DemoError,'SOURCE_CHANGED'): demo.review(self.conn,self.fixtures,pack['pack_id'],pack['fingerprint'],'fixture-reviewer','Do not accept stale source.')
        new=self.build(); self.assertNotEqual(new['pack_id'],pack['pack_id']); self.assertEqual(new['review_state'],'UNREVIEWED')
    def test_checklist_change_invalidates_review(self):
        pack=self.build(); demo.save(self.conn,pack)
        self.edit('checklist.json',lambda d:d.update(revision='2'))
        self.assertEqual(demo.retrieve(self.conn,self.fixtures,pack['pack_id'])['snapshot_state'],'STALE_SOURCE_SNAPSHOT')
    def test_wrong_snapshot_review_rejected(self):
        pack=self.build(); demo.save(self.conn,pack)
        with self.assertRaisesRegex(demo.DemoError,'SOURCE_CHANGED'): demo.review(self.conn,self.fixtures,pack['pack_id'],'wrong','fixture-reviewer','Draft note.')
    def test_persistence_across_cli_processes(self):
        command=[sys.executable,str(ROOT/'demo.py'),'--fixtures',str(self.fixtures),'--db',str(self.root/'process.sqlite')]
        built=json.loads(subprocess.check_output(command+['build','--job','J-SYN-100','--equipment','P-SYN-101'],text=True))
        loaded=json.loads(subprocess.check_output(command+['get','--pack',built['pack_id']],text=True))
        self.assertEqual(loaded['pack_id'],built['pack_id']); self.assertEqual(loaded['fields'],built['fields'])
    def test_retrieval_by_job_equipment_and_conflicting_date(self):
        pack=self.build(); demo.save(self.conn,pack); demo.save(self.conn,demo.build(self.fixtures,'J-SYN-101','P-SYN-101A'))
        for d in ['2026-11-03','2026-11-04']:
            rows=demo.search(self.conn,self.fixtures,'J-SYN-100','P-SYN-101',d)['matches']
            self.assertEqual(len(rows),1); self.assertTrue(rows[0]['date_is_conflicted'])
        self.assertEqual(demo.search(self.conn,self.fixtures,equipment='P-SYN-101')['matches'][0]['job_id'],'J-SYN-100')
        self.assertEqual(demo.search(self.conn,self.fixtures,planned_date='2026-12-31')['matches'],[])
    def test_current_revision_ambiguity_excludes_document(self):
        self.edit('manifest.json',lambda d:d['documents'][0].update(current=True))
        pack=self.build(); self.assertIn({'source':'job-register','state':'MULTIPLE_CURRENT_REVISIONS'},pack['ingestion_issues'])
        self.assertNotIn('job-register',json.dumps(pack['source_manifest']))
    def test_manifest_duplicate_is_explicit_failure(self):
        self.edit('manifest.json',lambda d:d['documents'].append(d['documents'][0]))
        with self.assertRaisesRegex(demo.DemoError,'DUPLICATE_DOCUMENT'): self.build()
    def test_path_escape_rejected(self):
        self.edit('manifest.json',lambda d:d['documents'][0].update(file='../outside.json'))
        with self.assertRaisesRegex(demo.DemoError,'SOURCE_PATH_OUTSIDE'): self.build()
    def test_missing_source_recorded(self):
        (self.fixtures/'asset-register-r2.json').unlink()
        pack=self.build(); self.assertIn('asset_description',pack['missing']); self.assertIn({'source':'asset-register-r2.json','state':'SOURCE_MISSING'},pack['ingestion_issues'])
    def test_source_identity_and_bad_field_rejected(self):
        self.edit('asset-register-r2.json',lambda d:d.update(revision='wrong'))
        self.assertIn({'source':'asset-register-r2.json','state':'SOURCE_IDENTITY_MISMATCH'},self.build()['ingestion_issues'])
        self.edit('handover-note-r1.json',lambda d:d['passages'][0]['fields'].update(planned_date='not-a-date'))
        self.assertIn({'source':'handover-note-r1.json','state':'UNREADABLE_OR_INVALID_SOURCE'},self.build()['ingestion_issues'])
    def test_unknown_pack_and_invalid_search_date(self):
        with self.assertRaisesRegex(demo.DemoError,'PACK_NOT_FOUND'): demo.retrieve(self.conn,self.fixtures,'not-found')
        with self.assertRaisesRegex(demo.DemoError,'INVALID_SEARCH_DATE'): demo.search(self.conn,self.fixtures,planned_date='tomorrow')
    def test_render_source_links_hashes_and_html_escaping(self):
        self.edit('asset-register-r2.json',lambda d:d['passages'][0]['fields'].update(asset_description='<script>fake()</script>'))
        pack=self.build(); target=self.root/'export'; demo.render(pack,target,self.fixtures)
        view=(target/'draft-pack.html').read_text(encoding='utf-8'); self.assertIn('&lt;script&gt;',view); self.assertNotIn('<script>fake',view)
        for filename,pid in re.findall(r'href="sources/([^"#]+)#([^"]+)"',view):
            source=(target/'sources'/filename).read_text(encoding='utf-8'); self.assertIn(f'id="{pid}"',source); self.assertIn(demo.LABEL,source)
        self.assertIn(demo.LABEL,view)
    def test_export_rejects_changed_source(self):
        pack=self.build(); self.edit('asset-register-r2.json',lambda d:d['passages'][0].update(text='Changed text.'))
        with self.assertRaisesRegex(demo.DemoError,'SOURCE_CHANGED_EXPORT'): demo.render(pack,self.root/'export',self.fixtures)
    def test_deterministic_repeated_build(self): self.assertEqual(self.build(),self.build())
    def test_no_external_side_effect_surface_and_all_labels(self):
        tree=ast.parse((ROOT/'demo.py').read_text(encoding='utf-8'))
        imports={n.names[0].name.split('.')[0] for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) and isinstance(n,ast.Import)}
        self.assertFalse(imports & {'socket','urllib','requests','http','subprocess','smtplib'})
        self.assertEqual(self.build()['label'],demo.LABEL); self.assertEqual(demo.answer(self.build(),'coordinator')['label'],demo.LABEL)
    def test_runtime_does_not_attempt_network_connection(self):
        with patch('socket.socket.connect', side_effect=AssertionError('NETWORK_ATTEMPT')) as connect_mock, patch('socket.create_connection', side_effect=AssertionError('NETWORK_ATTEMPT')) as create_mock:
            pack=self.build(); demo.save(self.conn,pack)
            demo.review(self.conn,self.fixtures,pack['pack_id'],pack['fingerprint'],'fixture-reviewer','Draft review.')
            demo.retrieve(self.conn,self.fixtures,pack['pack_id']); demo.search(self.conn,self.fixtures,planned_date='2026-11-03')
            demo.answer(pack,'safe_to_operate'); demo.render(pack,self.root/'export',self.fixtures)
            connect_mock.assert_not_called(); create_mock.assert_not_called()
    def test_malformed_manifest_fails_explicitly(self):
        (self.fixtures/'manifest.json').write_text('[]',encoding='utf-8')
        with self.assertRaisesRegex(demo.DemoError,'INVALID_MANIFEST'): self.build()
    def test_export_uses_unique_identity_names_for_nested_sources(self):
        nested=self.fixtures/'nested'; nested.mkdir()
        shutil.move(self.fixtures/'asset-register-r2.json',nested/'record.json')
        self.edit('manifest.json',lambda d:[e.update(file='nested/record.json') for e in d['documents'] if e['doc_id']=='asset-register' and e['revision']=='2'])
        pack=self.build(); target=self.root/'export'; demo.render(pack,target,self.fixtures)
        self.assertTrue((target/'sources'/'asset-register-r2.html').exists())
        self.assertTrue((target/'sources'/'asset-register-r2.json').exists())

if __name__=='__main__': unittest.main(verbosity=2)
