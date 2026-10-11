"""Deterministic, local-only administrative draft prototype. No AI/model calls."""
import argparse
import hashlib
import html
import json
import re
import sqlite3
from datetime import date
from pathlib import Path

LABEL = 'SYNTHETIC DEMONSTRATION. DRAFT. NOT AUTHORIZED FOR MAINTENANCE.'
FIELDS = {'asset_description', 'planned_date', 'coordinator', 'admin_status'}
STATUSES = {'draft_ready', 'deferred'}
TOKEN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')
INSTRUCTION = re.compile(r'ignore\s+all\s+previous|mark\s+this\s+job\s+authorized|send\s+the\s+corpus', re.I)

class DemoError(Exception):
    pass

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode('utf-8')

def envelope(**items):
    return {'label': LABEL, **items}

def token(value):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise DemoError('INVALID_IDENTIFIER')
    return value

def read_within(root, filename):
    path = (root / filename).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise DemoError('SOURCE_PATH_OUTSIDE_FIXTURES')
    return path.read_bytes()

def corpus(root):
    root = Path(root)
    try:
        manifest_bytes = read_within(root, 'manifest.json')
        checklist_bytes = read_within(root, 'checklist.json')
        manifest = json.loads(manifest_bytes)
        checklist = json.loads(checklist_bytes)
        if not isinstance(manifest, dict) or not isinstance(checklist, dict):
            raise DemoError('INVALID_MANIFEST_OR_CHECKLIST')
        if manifest.get('label') != LABEL or checklist.get('label') != LABEL:
            raise DemoError('SYNTHETIC_LABEL_REQUIRED')
        if not checklist.get('required_fields') or not set(checklist['required_fields']) <= FIELDS:
            raise DemoError('INVALID_CHECKLIST')
        token(checklist['id']); token(checklist['revision'])
        entries = manifest['documents']
        if not isinstance(entries, list) or len(entries) > 100:
            raise DemoError('INVALID_MANIFEST')
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise DemoError('MANIFEST_OR_CHECKLIST_UNREADABLE') from error
    sources, issues, hashes, keys, currents = [], [], {}, set(), {}
    for entry in entries:
        if not isinstance(entry, dict): raise DemoError('INVALID_MANIFEST_ENTRY')
        try:
            doc_id, revision = token(entry['doc_id']), token(entry['revision'])
            key = (doc_id, revision)
            if key in keys:
                raise DemoError('DUPLICATE_DOCUMENT_REVISION')
            keys.add(key)
            if type(entry['current']) is not bool:
                raise DemoError('INVALID_CURRENT_FLAG')
            # Currency is a manifest assertion, even when its bytes cannot be ingested.
            if entry['current']: currents.setdefault(doc_id, []).append(revision)
            raw = read_within(root, entry['file'])
            hashes[entry['file']] = digest(raw)
        except DemoError:
            raise
        except (OSError, KeyError, TypeError) as error:
            issues.append({'source': entry.get('file', 'unknown'), 'state': 'SOURCE_MISSING'})
            hashes[str(entry.get('file'))] = 'MISSING'
            continue
        try:
            doc = json.loads(raw.decode('utf-8'))
            if not isinstance(doc, dict): raise DemoError('INVALID_SOURCE_SCHEMA')
            if doc['label'] != LABEL or doc['doc_id'] != doc_id or doc['revision'] != revision:
                raise DemoError('SOURCE_IDENTITY_MISMATCH')
            token(doc['job_id']); token(doc['equipment_id'])
            if not isinstance(doc['passages'], list) or not doc['passages']:
                raise DemoError('INVALID_PASSAGES')
            passage_ids = set()
            for passage in doc['passages']:
                if not isinstance(passage, dict): raise DemoError('INVALID_PASSAGE')
                pid = token(passage['id'])
                if pid in passage_ids:
                    raise DemoError('DUPLICATE_PASSAGE')
                passage_ids.add(pid)
                if not isinstance(passage['text'], str) or not isinstance(passage['fields'], dict):
                    raise DemoError('INVALID_PASSAGE')
                if not set(passage['fields']) <= FIELDS:
                    raise DemoError('UNSUPPORTED_FIELD')
                for field, value in passage['fields'].items():
                    if not isinstance(value, str) or not value.strip() or len(value) > 250:
                        raise DemoError('INVALID_FIELD_VALUE')
                    if field == 'planned_date': date.fromisoformat(value)
                    if field == 'admin_status' and value not in STATUSES:
                        raise DemoError('INVALID_ADMIN_STATUS')
                if INSTRUCTION.search(passage['text']):
                    raise DemoError('UNTRUSTED_EMBEDDED_INSTRUCTION')
            sources.append({**entry, 'sha256': digest(raw), 'document': doc})
        except (UnicodeError, ValueError):
            issues.append({'source': entry['file'], 'state': 'UNREADABLE_OR_INVALID_SOURCE'})
        except (KeyError, TypeError):
            issues.append({'source': entry['file'], 'state': 'INVALID_SOURCE_SCHEMA'})
        except DemoError as error:
            issues.append({'source': entry['file'], 'state': str(error)})
    ambiguous = {k for k, rows in currents.items() if len(rows) != 1}
    for doc_id in sorted(ambiguous):
        issues.append({'source': doc_id, 'state': 'MULTIPLE_CURRENT_REVISIONS'})
    sources = [s for s in sources if s['doc_id'] not in ambiguous]
    fingerprint = digest(encoded({'manifest': digest(manifest_bytes), 'checklist': digest(checklist_bytes), 'sources': hashes}))
    return envelope(fingerprint=fingerprint, checklist=checklist, sources=sources, issues=issues)

def build(root, job, equipment):
    token(job); token(equipment)
    data = corpus(root)
    current = [s for s in data['sources'] if s['current'] and s['document']['job_id'] == job and s['document']['equipment_id'] == equipment]
    if not current:
        raise DemoError('NO_CURRENT_SOURCES_FOR_EXACT_JOB_AND_EQUIPMENT')
    values = {k: {} for k in FIELDS}
    refs = []
    for source in sorted(current, key=lambda s: s['doc_id']):
        for passage in source['document']['passages']:
            ref = {'doc_id': source['doc_id'], 'revision': source['revision'], 'passage_id': passage['id'],
                   'file': source['file'], 'source_sha256': source['sha256'],
                   'passage_sha256': digest(encoded(passage))}
            refs.append(ref)
            for field, value in passage['fields'].items():
                values[field].setdefault(value, []).append(ref)
    fields, missing, conflicts = {}, [], []
    for field in sorted(FIELDS):
        candidates = [{'value': value, 'sources': references} for value, references in sorted(values[field].items())]
        state = 'missing' if not candidates else 'conflict' if len(candidates) > 1 else 'source_asserted'
        fields[field] = {'state': state, 'candidates': candidates}
        if state == 'missing' and field in data['checklist']['required_fields']: missing.append(field)
        if state == 'conflict': conflicts.append(field)
    queue = ([{'reason': 'MISSING_REQUIRED_FIELD', 'field': field} for field in missing]
             + [{'reason': 'CONFLICTING_SOURCE_VALUES', 'field': field} for field in conflicts]
             + [{'reason': 'INGESTION_EXCEPTION', **issue} for issue in data['issues']]
             + [{'reason': 'HUMAN_REVIEW_REQUIRED', 'scope': 'Administrative draft only; cannot authorize maintenance.'}])
    pack = envelope(job_id=job, equipment_id=equipment, fingerprint=data['fingerprint'],
                    checklist={'id': data['checklist']['id'], 'revision': data['checklist']['revision']},
                    fields=fields, missing=missing, conflicts=conflicts, source_manifest=refs,
                    ingestion_issues=data['issues'], human_review_queue=queue,
                    handover={'status': 'draft', 'job_id': job, 'equipment_id': equipment,
                              'unresolved_fields': sorted(set(missing+conflicts)), 'source_references': refs,
                              'authorization': 'NONE. Administrative draft only.'},
                    authorization='NONE', review_state='UNREVIEWED')
    pack['pack_id'] = 'pack-' + digest(encoded(pack))[:24]
    return pack

def connect(db):
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db)
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript('''CREATE TABLE IF NOT EXISTS packs (id TEXT PRIMARY KEY, job TEXT, equipment TEXT, body TEXT);
        CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY, pack_id TEXT REFERENCES packs(id), reviewer TEXT, fingerprint TEXT, note TEXT);''')
    return conn

def save(conn, pack):
    conn.execute('INSERT OR IGNORE INTO packs VALUES (?,?,?,?)', (pack['pack_id'], pack['job_id'], pack['equipment_id'], json.dumps(pack)))
    conn.commit()

def retrieve(conn, root, pack_id):
    row = conn.execute('SELECT body FROM packs WHERE id=?', (pack_id,)).fetchone()
    if not row: raise DemoError('PACK_NOT_FOUND')
    pack = json.loads(row[0])
    fresh = corpus(root)['fingerprint'] == pack['fingerprint']
    reviews = conn.execute('SELECT reviewer,fingerprint,note FROM reviews WHERE pack_id=?', (pack_id,)).fetchall()
    pack['snapshot_state'] = 'CURRENT_SOURCE_SNAPSHOT' if fresh else 'STALE_SOURCE_SNAPSHOT'
    pack['reviews'] = [{'reviewer': r[0], 'note': r[2], 'state': 'DRAFT_REVIEW_RECORDED' if fresh and r[1] == pack['fingerprint'] else 'STALE_REVIEW'} for r in reviews]
    pack['review_state'] = 'DRAFT_REVIEW_RECORDED' if fresh and pack['reviews'] else 'STALE_REVIEW' if reviews else 'UNREVIEWED'
    return pack

def review(conn, root, pack_id, expected, reviewer, note):
    token(reviewer)
    pack = retrieve(conn, root, pack_id)
    if expected != pack['fingerprint'] or pack['snapshot_state'] != 'CURRENT_SOURCE_SNAPSHOT':
        raise DemoError('SOURCE_CHANGED_REVIEW_REJECTED')
    if not note.strip() or len(note) > 1000: raise DemoError('REVIEW_NOTE_REQUIRED')
    conn.execute('INSERT INTO reviews(pack_id,reviewer,fingerprint,note) VALUES(?,?,?,?)', (pack_id,reviewer,expected,note))
    conn.commit()
    return retrieve(conn, root, pack_id)

def search(conn, root, job=None, equipment=None, planned_date=None):
    if planned_date:
        try: date.fromisoformat(planned_date)
        except ValueError as error: raise DemoError('INVALID_SEARCH_DATE') from error
    if job: token(job)
    if equipment: token(equipment)
    rows = conn.execute('SELECT id FROM packs WHERE (? IS NULL OR job=?) AND (? IS NULL OR equipment=?) ORDER BY id', (job,job,equipment,equipment)).fetchall()
    matches = []
    for row in rows:
        pack = retrieve(conn,root,row[0])
        dates = [c['value'] for c in pack['fields']['planned_date']['candidates']]
        if not planned_date or planned_date in dates:
            matches.append({'pack_id':pack['pack_id'], 'job_id':pack['job_id'], 'equipment_id':pack['equipment_id'],
                            'observed_dates':dates, 'date_is_conflicted':len(dates)>1,
                            'snapshot_state':pack['snapshot_state'], 'review_state':pack['review_state']})
    return envelope(matches=matches, date_semantics='Matches any source-asserted planned date, including unresolved conflicting dates; not an approved date.')

def answer(pack, field):
    if field not in FIELDS:
        return envelope(state='ABSTAIN_UNSUPPORTED_QUESTION', reason='Only the four administrative fixture fields are supported. No safety, isolation or work authorization answer is provided.', sources=[])
    if pack.get('snapshot_state') == 'STALE_SOURCE_SNAPSHOT':
        return envelope(state='ABSTAIN_STALE_SNAPSHOT', sources=[])
    item = pack['fields'][field]
    return envelope(field=field, state=item['state'], candidates=item['candidates'],
                    interpretation='Source assertions only. Conflicts are not resolved; missing facts are not invented.')

def source_basename(ref):
    """Structured identity encoding avoids delimiter ambiguity; full hash bounds length."""
    return 'source-'+digest(encoded([ref['doc_id'],ref['revision']]))

def render(pack, target, root):
    """Write escaped static HTML and JSON locally; source links use filename plus passage ID."""
    # Check all output identities before writing any files, including hash collision defense.
    names={}
    for ref in pack['source_manifest']:
        name=source_basename(ref)
        name_key=name.casefold()
        identity=(ref['doc_id'],ref['revision'],ref['file'],ref['source_sha256'])
        if name_key in names and names[name_key]!=identity: raise DemoError('DUPLICATE_EXPORT_NAME')
        names[name_key]=identity
    target=Path(target); target.mkdir(parents=True,exist_ok=True)
    source_dir=target/'sources'; source_dir.mkdir(exist_ok=True)
    for ref in pack['source_manifest']:
        raw=read_within(Path(root),ref['file'])
        if digest(raw)!=ref['source_sha256']: raise DemoError('SOURCE_CHANGED_EXPORT_REJECTED')
        doc=json.loads(raw.decode('utf-8'))
        name=source_basename(ref)+'.html'
        contents=[]
        for passage in doc['passages']:
            contents.append(f'<section id="{html.escape(passage["id"])}"><h2>Passage {html.escape(passage["id"])}</h2><p>{html.escape(passage["text"])}</p><pre>{html.escape(json.dumps(passage["fields"],indent=2))}</pre></section>')
        (source_dir/name).write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><title>Synthetic source</title><h1>{html.escape(doc["doc_id"])} revision {html.escape(doc["revision"])}</h1><p><strong>{LABEL}</strong></p><p>SHA256 {digest(raw)}</p>'+''.join(contents)+'</html>',encoding='utf-8')
        (source_dir/(source_basename(ref)+'.json')).write_bytes(raw)
    (target/'draft-pack.json').write_text(json.dumps(pack,indent=2)+'\n',encoding='utf-8')
    esc=html.escape
    rows=[]
    for field,item in pack['fields'].items():
        candidates=[]
        for candidate in item['candidates']:
            citations=[]
            for ref in candidate['sources']:
                link='sources/'+source_basename(ref)+'.html#'+ref['passage_id']
                citations.append(f'<a href="{esc(link)}">{esc(ref["doc_id"])} r{esc(ref["revision"])} / {esc(ref["passage_id"])}</a> (file {esc(ref["file"])}, SHA256 {ref["source_sha256"]})')
            candidates.append(esc(candidate['value'])+'<br>'+ '<br>'.join(citations))
        rows.append(f'<tr><th>{esc(field)}</th><td>{esc(item["state"])}</td><td>'+ '<hr>'.join(candidates)+'</td></tr>')
    sources=[]
    for ref in pack['source_manifest']:
        sources.append(f'<li>{esc(ref["doc_id"])} r{esc(ref["revision"])} / {esc(ref["passage_id"])}: file {esc(ref["file"])}. Source SHA256 {ref["source_sha256"]}. Passage SHA256 {ref["passage_sha256"]}.</li>')
    body=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic administrative draft</title>
<style>body{{max-width:1100px;margin:2rem auto;padding:1rem;font:16px system-ui}}strong{{color:#8b0000}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #bbb;padding:.7rem;text-align:left;overflow-wrap:anywhere}}pre,li{{white-space:pre-wrap;overflow-wrap:anywhere}}</style>
<h1>Synthetic pump-job administrative pack</h1><p><strong>{LABEL}</strong></p><p>Job {esc(pack['job_id'])}, equipment {esc(pack['equipment_id'])}. No operating procedures, safety decisions or work authorization.</p>
<h2>Source-asserted fields</h2><table><tr><th>Field</th><th>State</th><th>Values and exact references</th></tr>{''.join(rows)}</table>
<h2>Human-review queue</h2><pre>{esc(json.dumps(pack['human_review_queue'],indent=2))}</pre>
<h2>Draft handover</h2><pre>{esc(json.dumps(pack['handover'],indent=2))}</pre>
<h2>Source manifest</h2><ul>{''.join(sources)}</ul><p>Snapshot fingerprint: {pack['fingerprint']}. This exported view is a snapshot; retrieve through the CLI to check source freshness.</p><p><strong>{LABEL}</strong></p></html>'''
    (target/'draft-pack.html').write_text(body,encoding='utf-8')

def main(argv=None):
    p=argparse.ArgumentParser(description=LABEL)
    p.add_argument('--fixtures',default=str(Path(__file__).parent/'fixtures'))
    p.add_argument('--db',default=str(Path(__file__).parent/'output'/'demo.sqlite'))
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('ingest')
    b=sub.add_parser('build'); b.add_argument('--job',required=True); b.add_argument('--equipment',required=True); b.add_argument('--export')
    g=sub.add_parser('get'); g.add_argument('--pack',required=True)
    s=sub.add_parser('search'); s.add_argument('--job'); s.add_argument('--equipment'); s.add_argument('--date')
    r=sub.add_parser('review'); r.add_argument('--pack',required=True); r.add_argument('--fingerprint',required=True); r.add_argument('--reviewer',required=True); r.add_argument('--note',required=True)
    q=sub.add_parser('query'); q.add_argument('--pack',required=True); q.add_argument('--field',required=True)
    args=p.parse_args(argv)
    try:
        if args.command=='ingest':
            data=corpus(args.fixtures)
            result=envelope(fingerprint=data['fingerprint'], issues=data['issues'],
                manifest=[{k:v for k,v in s.items() if k!='document'} for s in data['sources']],checklist=data['checklist'])
        else:
            with connect(args.db) as conn:
                if args.command=='build':
                    result=build(args.fixtures,args.job,args.equipment); save(conn,result)
                    if args.export: render(result,args.export,args.fixtures)
                elif args.command=='get': result=retrieve(conn,args.fixtures,args.pack)
                elif args.command=='search': result=search(conn,args.fixtures,args.job,args.equipment,args.date)
                elif args.command=='review': result=review(conn,args.fixtures,args.pack,args.fingerprint,args.reviewer,args.note)
                else: result=answer(retrieve(conn,args.fixtures,args.pack),args.field)
        print(json.dumps(result,indent=2)); return 0
    except (DemoError,OSError,sqlite3.Error) as error:
        print(json.dumps(envelope(state='EXPLICIT_FAILURE',error=str(error)),indent=2)); return 2

if __name__=='__main__':
    raise SystemExit(main())
