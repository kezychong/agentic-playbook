#!/usr/bin/env python3
"""Hermes chat capture 2.4.0. Python stdlib only; invoke with python3 -I.

Live stores are opened mode=ro, query_only=ON. Only a private, minimal session
snapshot is handed to Hermes. The model receives redacted, bounded exports.
prepare -> write draft -> commit. commit owns the note+watermark transaction;
embedded receipts recover a crash between the two durable writes.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
from datetime import datetime, timezone

STATE = '_System/state/chat-capture-watermarks.json'
WORK = '_System/state/chat-capture'
EXCLUDED = {'08. Restricted', '.git', '.obsidian', '.trash', '_System', 'node_modules'}


def iso(value=None):
    return datetime.fromtimestamp(time.time() if value is None else value, timezone.utc).isoformat()


def load(path, default=None):
    return json.loads(path.read_text()) if path.exists() else ({} if default is None else default)


def atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.capture-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(name): os.unlink(name)


def save(path, data):
    atomic(path, json.dumps(data, ensure_ascii=False, indent=2)+'\n')


@contextlib.contextmanager
def locked(brain):
    directory = brain / WORK
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'lock').open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


@contextlib.contextmanager
def readonly(path):
    c = sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    try: yield c
    finally: c.close()


def profiles(root, explicit):
    if explicit:
        result=[]
        for entry in explicit:
            name, path = entry.split('=',1)
            if not re.fullmatch(r'[A-Za-z0-9_.-]+',name): raise ValueError('Invalid profile name')
            result.append((name,Path(path).expanduser().resolve()))
        return result
    root=Path(root).expanduser().resolve()
    result=[('default',root/'state.db')] if (root/'state.db').is_file() else []
    result += [(p.parent.name,p) for p in sorted((root/'profiles').glob('*/state.db'))]
    return result


def select(db, hours, only_open=False):
    with readonly(db) as c:
        columns={r['name'] for r in c.execute('PRAGMA table_info(sessions)')}
        activity='s.last_activity_at' if 'last_activity_at' in columns else 'NULL'
        sql=f'''SELECT s.id,s.source,s.ended_at,
          MAX(COALESCE({activity},0),COALESCE(s.started_at,0),COALESCE(m.ts,0)) AS last_active,
          COALESCE(m.upper_id,0) AS upper_id,COALESCE(m.n,0) AS message_count
          FROM sessions s LEFT JOIN
          (SELECT session_id,MAX(timestamp) ts,MAX(id) upper_id,COUNT(*) n FROM messages GROUP BY session_id) m
          ON m.session_id=s.id
          WHERE MAX(COALESCE({activity},0),COALESCE(s.started_at,0),COALESCE(m.ts,0)) >= ?
          {'AND s.ended_at IS NULL' if only_open else ''}
          ORDER BY last_active,s.id'''
        return [dict(r) for r in c.execute(sql,(time.time()-hours*3600,))]


def note_files(brain):
    for base, dirs, files in os.walk(brain, followlinks=False):
        dirs[:] = [d for d in dirs if d not in EXCLUDED and 'finance' not in d.lower()
                   and not (Path(base)/d).is_symlink()]
        for name in files:
            if name.endswith('.md') and 'finance' not in name.lower():
                p=Path(base)/name
                if not p.is_symlink(): yield p


def metadata(text):
    result={}
    if not text.startswith('---\n'): return result
    for line in text.split('\n---',1)[0].splitlines()[1:]:
        k,sep,v=line.partition(':')
        if not sep: continue
        try: result[k]=json.loads(v.strip())
        except ValueError: result[k]=v.strip().strip("'\"")
    return result


def resolve_note(brain, note):
    if not note: return ''
    p=Path(note)
    if p.is_absolute():
        try: p=p.relative_to(brain)
        except ValueError: return Path(note).stem
    if (brain/p).is_file(): return str(p)
    matches=[f for f in note_files(brain) if f.name==p.name]
    return str(matches[0].relative_to(brain)) if len(matches)==1 else p.stem


def recover(brain, state):
    # A note is the durable receipt; never require its original folder to survive Organise.
    changed=False
    for p in note_files(brain):
        with p.open() as f: head=f.read(8192)
        m=metadata(head)
        if not all(k in m for k in ('capture_key','capture_through_id','capture_token')): continue
        key=m['capture_key']; upper=int(m['capture_through_id'])
        if upper>int(state.get(key,{}).get('last_message_id',0)):
            state[key]={'last_message_id':upper,'note':str(p.relative_to(brain)),
                        'original_title':m.get('capture_original_title',p.stem),
                        'captured_at':m.get('captured',iso()),'token':m['capture_token']}
            changed=True
    return changed


def snapshot(db, sid, lower, upper, path):
    # Copy only this session's bounded rows; never copy a multi-GB live DB or its WAL files.
    # Schema is copied from the installed version, with no triggers to mutate display identities.
    with readonly(db) as src, contextlib.closing(sqlite3.connect(path)) as dst:
        src.execute('BEGIN')
        for row in src.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"):
            if row['name'].startswith('sqlite_') or 'VIRTUAL TABLE' in row['sql'].upper(): continue
            dst.execute(row['sql'])
        rows=[dict(r) for r in src.execute('SELECT * FROM messages WHERE session_id=? ORDER BY id',(sid,))]
        groups={}
        for row in rows:
            identity=row.get('display_identity') or tuple(row.get(k) for k in
                ('role','content','timestamp','tool_call_id','tool_calls','tool_name'))
            group=groups.setdefault(identity,{'first':row['id'],'best':None})
            visible=bool(row.get('active',1) or row.get('compacted',0))
            best=group['best']
            if visible and (best is None or (row.get('active',1),row['id'])>(best.get('active',1),best['id'])):
                group['best']=row
        chosen=[]
        for group in groups.values():
            row=group['best']
            if row and lower<group['first']<=upper:
                if 'display_order' in row: row['display_order']=group['first']
                chosen.append(row)
        sessions=[dict(r) for r in src.execute('SELECT * FROM sessions WHERE id=?',(sid,))]
        for table, records in [('sessions',sessions),('messages',chosen)]:
            if not records: continue
            names=list(records[0])
            insert='INSERT INTO '+table+' ('+','.join('"'+n+'"' for n in names)+') VALUES ('+','.join('?' for _ in names)+')'
            dst.executemany(insert,[[r[n] for n in names] for r in records])
        # Redact arbitrary metadata by omission; title is chosen from the redacted conversation.
        cols={r[1] for r in dst.execute('PRAGMA table_info(sessions)')}
        for col in ('title','display_name','cwd','system_prompt'):
            if col in cols: dst.execute('UPDATE sessions SET "'+col+'"=NULL')
        if 'message_count' in cols:
            dst.execute('UPDATE sessions SET message_count=(SELECT COUNT(*) FROM messages)')
        version=src.execute('PRAGMA user_version').fetchone()[0]
        dst.execute('PRAGMA user_version='+str(version))
        dst.commit()


def export_session(db, sid, directory, hermes):
    directory.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    # parent named profiles keeps both older/newer Hermes from selecting the sticky active profile.
    env['HERMES_HOME']=str(db.parent)
    for key in ('HERMES_PROFILE','HERMES_CONFIG','HERMES_ENV','PYTHONPATH','PYTHONHOME'):
        env.pop(key,None)
    run=subprocess.run([hermes,'sessions','export','--format','md','--redact','--session-id',sid,str(directory)],
                       env=env,cwd=db.parent,capture_output=True,text=True,timeout=180)
    files=list(directory.glob('*.md'))
    if run.returncode or len(files)!=1:
        # Never echo Hermes output: some failures include config or conversation content.
        raise RuntimeError('Single-session export failed (exit '+str(run.returncode)+'); no watermark advanced')
    text=files[0].read_text()
    if metadata(text).get('session_id')!=sid: raise RuntimeError('Export session mismatch')
    return files[0]


def prepare(brain, sources, hours=24, only_open=False, continued_only=False, dry_run=False,
            hermes='hermes', exporter=export_session, source_root='08. Sources/hermes-chats', export_brain=None):
    brain=Path(brain).resolve()
    if not brain.is_dir(): raise ValueError('Brain folder is missing')
    if Path(source_root).is_absolute() or '..' in Path(source_root).parts: raise ValueError('Invalid source folder')
    result={'items':[],'errors':[],'unseeded':[],'selected':0,'dry_run':dry_run}
    guard=contextlib.nullcontext() if dry_run else locked(brain)
    with guard:
        state=load(brain/STATE)
        blocks=load(brain/'_System/state/chat-capture-seed-blocks.json')
        if not dry_run and recover(brain,state): save(brain/STATE,state)
        for profile,db in sources:
            try: rows=select(db,hours,only_open)
            except (sqlite3.Error,OSError):
                result['errors'].append({'profile':profile,'error':'Cannot read session database'}); continue
            for row in rows:
                result['selected']+=1
                key=profile+'/'+row['id']; previous=state.get(key,{})
                if 'last_message_count' in previous and 'last_message_id' not in previous:
                    result['errors'].append({'key':key,'error':'Count watermark requires explicit ID migration'}); continue
                if not previous.get('note') and (key in blocks or '*' in blocks):
                    result['errors'].append({'key':key,'error':'Historical capture needs a source match; refusing duplicate first capture'}); continue
                lower=int(previous.get('last_message_id',0)); upper=int(row['upper_id'])
                if upper<=lower: continue
                if continued_only and not previous.get('note'):
                    result['unseeded'].append(key); continue
                token=hashlib.sha256((key+':'+str(lower)+':'+str(upper)).encode()).hexdigest()[:24]
                item={'token':token,'key':key,'profile':profile,'session_id':row['id'],
                      'source':row['source'],'open':row['ended_at'] is None,'last_active':iso(row['last_active']),
                      'after_id':lower,'through_id':upper,'message_count':row['message_count'],
                      'previous_note':resolve_note(brain,previous.get('note','')),
                      'original_title':previous.get('original_title',''),'continued':bool(previous.get('note'))}
                if not dry_run:
                    try:
                        with tempfile.TemporaryDirectory(prefix='chat-capture-') as temp:
                            private=Path(temp)/'profiles'/'capture-export'; private.mkdir(parents=True)
                            snap=private/'state.db'; snapshot(db,row['id'],lower,upper,snap)
                            out=exporter(snap,row['id'],Path(temp)/'export',hermes)
                            destination=(Path(export_brain).resolve() if export_brain else brain)/source_root/time.strftime('%Y-%m-%d')/profile/(token+'.md')
                            atomic(destination,out.read_text())
                            item['export']=str(destination)
                            save(brain/WORK/'pending'/(token+'.json'),item)
                    except (OSError,sqlite3.Error,RuntimeError,subprocess.TimeoutExpired):
                        result['errors'].append({'key':key,'error':'Export failed; watermark unchanged'}); continue
                result['items'].append(item)
        if not dry_run: save(brain/WORK/'batch.json',result)
    return result


def commit(brain, token, draft, title, inbox='01. Inbox/agent-drops'):
    brain=Path(brain).resolve()
    if not re.fullmatch(r'[a-f0-9]{24}',token): raise ValueError('Invalid batch token')
    if Path(inbox).is_absolute() or '..' in Path(inbox).parts: raise ValueError('Invalid inbox')
    with locked(brain):
        state=load(brain/STATE)
        if recover(brain,state): save(brain/STATE,state)
        item=load(brain/WORK/'pending'/(token+'.json'))
        if not item: raise ValueError('Unknown batch token')
        current=state.get(item['key'],{})
        if int(current.get('last_message_id',0))>=item['through_id']:
            return {'status':'already_committed','note':str(brain/current['note'])}
        if int(current.get('last_message_id',0))!=item['after_id']:
            raise ValueError('Stale batch; prepare again before writing')
        body=Path(draft).read_text().strip()
        if not body: raise ValueError('Empty draft; watermark unchanged')
        title=(item['original_title'] or title).strip()
        title=re.sub(r'[\r\n\[\]#]',' ',title).strip()
        if not title: raise ValueError('A title is required')
        display=title+(' (continued)' if item['continued'] else '')
        slug=re.sub(r'[^\w .()-]','-',display)[:100].strip(' .') or 'Conversation'
        note=brain/inbox/(time.strftime('%Y-%m-%d')+' '+slug+' '+token+'.md')
        previous=resolve_note(brain,current.get('note',''))
        link=('Previous: [['+str(Path(previous).with_suffix('') if previous.endswith('.md') else previous)+']]\n\n') if previous else ''
        fields={'title':display,'source':item['profile']+', '+str(item['source'])+' chat '+item['session_id'],
                'captured':iso(),'epistemic':'researched','capture_key':item['key'],
                'capture_after_id':item['after_id'],'capture_through_id':item['through_id'],
                'capture_original_title':title,'capture_token':token}
        header='---\n'+'\n'.join(k+': '+json.dumps(v,ensure_ascii=False) for k,v in fields.items())+'\n---\n\n'
        try:
            export_link='[['+str(Path(item['export']).relative_to(brain).with_suffix(''))+']]'
        except ValueError:
            export_link='[Private source export]('+Path(item['export']).as_uri()+')'
        content=header+'# '+display+'\n\n'+link+'Original: '+export_link+'\n\n'+body+'\n'
        # No original note is opened for writing. Atomic install refuses filename collisions.
        note.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix='.capture-note-',dir=note.parent)
        try:
            with os.fdopen(fd,'w') as f: f.write(content); f.flush(); os.fsync(f.fileno())
            os.link(tmp,note)
            directory=os.open(note.parent,os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
        finally: os.unlink(tmp)
        state[item['key']]={'last_message_id':item['through_id'],'note':str(note.relative_to(brain)),
                            'original_title':title,'captured_at':fields['captured'],'token':token}
        save(brain/STATE,state)
        return {'status':'written','note':str(note)}


def transcript(text):
    if '\n## Messages\n' not in text: return None
    return text.split('\n## Messages\n',1)[1].rsplit('\n## Export verification\n',1)[0].strip()


def seed(brain,sources,hermes='hermes',exporter=export_session):
    """Seed only evidenced boundaries, never file mtime or today's message count."""
    brain=Path(brain).resolve(); stores=dict(sources); count=0; unresolved=[]
    with locked(brain):
        state=load(brain/STATE); recovered=recover(brain,state); blocks={}
        for note in note_files(brain):
            # Only notes, not the export originals themselves, establish prior capture.
            if not any(part.startswith(('01.','02.','03.','04.','05.')) for part in note.relative_to(brain).parts): continue
            text=note.read_text(); meta=metadata(text)
            if meta.get('capture_key'): continue
            links=re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]',text)
            candidates=[]; known_keys=set(); unknown_links=False
            for link in links:
                if '/hermes-chats/' not in link: continue
                linked=Path(link if link.endswith('.md') else link+'.md')
                if linked.is_absolute() or '..' in linked.parts:
                    unknown_links=True; continue
                full=brain/linked
                if not full.is_file():
                    matches=[p for p in note_files(brain) if p.name==linked.name]
                    if len(matches)!=1:
                        unknown_links=True; continue
                    full=matches[0]
                historical=full.read_text(); data=metadata(historical)
                sid=data.get('session_id'); stamp=data.get('exported_at')
                parts=linked.parts; profile=parts[-2]
                if sid and profile in stores: known_keys.add(profile+'/'+sid)
                if not sid or profile not in stores:
                    unknown_links=True; continue
                if not stamp: continue
                try:
                    cutoff=datetime.fromisoformat(str(stamp).replace('Z','+00:00')).timestamp()
                    with readonly(stores[profile]) as c:
                        upper=c.execute('SELECT MAX(id) FROM messages WHERE session_id=? AND timestamp<=?',(sid,cutoff)).fetchone()[0]
                    if upper and transcript(historical) is not None:
                        # exported_at is only a candidate bound. Prove it against the immutable
                        # exported words, including timestamps/tool blocks. Never seed from time alone.
                        with tempfile.TemporaryDirectory(prefix='capture-seed-') as temp:
                            private=Path(temp)/'profiles'/'capture-export'; private.mkdir(parents=True)
                            snap=private/'state.db'; snapshot(stores[profile],sid,0,int(upper),snap)
                            exported=exporter(snap,sid,Path(temp)/'export',hermes)
                            if transcript(exported.read_text())==transcript(historical):
                                candidates.append((profile+'/'+sid,int(upper),stamp))
                except (ValueError,sqlite3.Error,OSError,RuntimeError,subprocess.TimeoutExpired): continue
            proven={}
            for key,upper,stamp in candidates:
                if upper>proven.get(key,(0,''))[0]: proven[key]=(upper,stamp)
            heading=re.search(r'^# (.+)$',text,re.M)
            title=(heading.group(1) if heading else note.stem).removesuffix(' (continued)')
            for key,(upper,stamp) in proven.items():
                if upper>int(state.get(key,{}).get('last_message_id',0)):
                    state[key]={'last_message_id':upper,'note':str(note.relative_to(brain)),
                                'original_title':title,'captured_at':stamp,'seeded_from':'linked historical export'}
                    count+=1
            missing=known_keys-set(proven)-set(state)
            looks_captured='/hermes-chats/' in text or re.search(r'(?im)^source:.*(?:hermes|telegram|desktop).*chat',text)
            if unknown_links or (looks_captured and not known_keys): missing.add('*')
            if missing:
                unresolved.append(str(note.relative_to(brain)))
                for key in missing: blocks.setdefault(key,[]).append(str(note.relative_to(brain)))
        if count or recovered: save(brain/STATE,state)
        block_path=brain/'_System/state/chat-capture-seed-blocks.json'
        if blocks or block_path.exists(): save(block_path,blocks)
    return {'seeded':count,'unresolved':unresolved}


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['prepare','commit','seed'])
    parser.add_argument('--brain',required=True,type=Path)
    parser.add_argument('--root',default=str(Path.home()/'.hermes'))
    parser.add_argument('--profile',action='append',default=[],help='name=/absolute/profile/state.db; repeatable')
    parser.add_argument('--hours',type=float,default=24)
    parser.add_argument('--only-open',action='store_true')
    parser.add_argument('--continued-only',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--hermes',default=shutil.which('hermes') or str(Path.home()/'.local/bin/hermes'))
    parser.add_argument('--source-root',default='08. Sources/hermes-chats')
    parser.add_argument('--export-brain',type=Path,help='Optional private export store for a routed brain')
    parser.add_argument('--inbox',default='01. Inbox/agent-drops')
    parser.add_argument('--token'); parser.add_argument('--draft',type=Path); parser.add_argument('--title')
    args=parser.parse_args()
    if args.command=='commit':
        if not all((args.token,args.draft,args.title)): parser.error('commit requires --token --draft --title')
        result=commit(args.brain,args.token,args.draft,args.title,args.inbox)
    else:
        sources=profiles(args.root,args.profile)
        if not sources: parser.error('No session databases found; supply --root or --profile')
        if args.command=='seed': result=seed(args.brain,sources,args.hermes)
        else:
            if args.hours<=0: parser.error('--hours must be positive')
            result=prepare(args.brain,sources,args.hours,args.only_open,args.continued_only,args.dry_run,args.hermes,source_root=args.source_root,export_brain=args.export_brain)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result.get('errors'): return 1
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,OSError,sqlite3.Error) as exc:
        # Error types are safe to print; paths/content from arbitrary exceptions are not.
        print(json.dumps({'error':type(exc).__name__,'message':'Capture stopped; check inputs. No source profile was changed.'}))
        raise SystemExit(1)
