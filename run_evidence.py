"""Run local tests and emit actual evidence pinned to Git HEAD, without network."""
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import demo

ROOT=Path(__file__).parent.resolve()
OUT=ROOT/'output'/'evidence'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    dirty=subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain'],text=True).strip()
    if dirty:
        print(json.dumps(demo.envelope(state='EXPLICIT_FAILURE',error='Commit source and fixtures before generating pinned evidence.',git_status=dirty),indent=2))
        return 2
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    with (OUT/'test-results.txt').open('w',encoding='utf-8') as log:
        log.write(demo.LABEL+'\nCommit: '+commit+'\nPython: '+platform.python_version()+'\n\n')
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    data=demo.corpus(ROOT/'fixtures')
    primary=demo.build(ROOT/'fixtures','J-SYN-100','P-SYN-101')
    demo.render(primary,OUT/'primary-draft',ROOT/'fixtures')
    with tempfile.TemporaryDirectory() as tmp:
        temp=Path(tmp); fixtures=temp/'fixtures'; shutil.copytree(ROOT/'fixtures',fixtures)
        conn=demo.connect(temp/'scenario.sqlite')
        try:
            demo.save(conn,primary)
            reviewed=demo.review(conn,fixtures,primary['pack_id'],primary['fingerprint'],'fictional-reviewer','Draft examined. Missing coordinator and conflicts remain unresolved.')
            (OUT/'reviewed-draft.json').write_text(json.dumps(reviewed,indent=2)+'\n',encoding='utf-8')
            original_search=demo.search(conn,fixtures,'J-SYN-100','P-SYN-101','2026-11-03')
            path=fixtures/'job-register-r2.json'; doc=json.loads(path.read_text(encoding='utf-8'))
            doc['passages'][0]['fields']['planned_date']='2026-11-05'
            path.write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
            stale=demo.retrieve(conn,fixtures,primary['pack_id'])
            (OUT/'stale-review.json').write_text(json.dumps(stale,indent=2)+'\n',encoding='utf-8')
            stale_query=demo.answer(stale,'planned_date')
            fresh=demo.build(fixtures,'J-SYN-100','P-SYN-101')
            (OUT/'replacement-unreviewed-draft.json').write_text(json.dumps(fresh,indent=2)+'\n',encoding='utf-8')
            rejection=None
            try: demo.review(conn,fixtures,primary['pack_id'],primary['fingerprint'],'fictional-reviewer','Attempt stale draft review.')
            except demo.DemoError as error: rejection=str(error)
            scenarios=demo.envelope(original_review_state=reviewed['review_state'],unchanged_authorization=reviewed['authorization'],
                original_search=original_search,stale_snapshot=stale['snapshot_state'],stale_review=stale['reviews'][0]['state'],
                stale_query=stale_query,stale_review_rejection=rejection,new_review_state=fresh['review_state'],
                unsupported_question=demo.answer(fresh,'safe_to_operate'))
            (OUT/'scenarios.json').write_text(json.dumps(scenarios,indent=2)+'\n',encoding='utf-8')
        finally: conn.close()
    report=demo.envelope(commit=commit,branch='codex/synthetic-admin-demo',python=platform.python_version(),
        tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),successful=result.wasSuccessful(),
        fixture_fingerprint=data['fingerprint'],primary_pack_id=primary['pack_id'],
        expected_document_failures={'missing':primary['missing'],'conflicts':primary['conflicts'],'ingestion_issues':primary['ingestion_issues']},
        scenario_result=scenarios,limitations='Small structured fictional fixtures only; no LLM, RAG, OCR, operational validation, reliability or savings proof.')
    (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if result.wasSuccessful() else 1

if __name__=='__main__': raise SystemExit(main())
