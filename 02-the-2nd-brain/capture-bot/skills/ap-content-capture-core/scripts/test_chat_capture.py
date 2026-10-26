"""Regression tests: open sessions, delta bounds, crash recovery, moved notes, legacy seed."""
import importlib.util
import json
import pathlib
import sqlite3
import tempfile
import time
import unittest

HELPER = pathlib.Path(__file__).with_name('chat_capture.py')

class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(HELPER.exists(), 'Missing deterministic open-session capture helper')
        spec = importlib.util.spec_from_file_location('capture', HELPER)
        self.h = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.h)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.brain = self.root / 'brain'; self.brain.mkdir()
        self.db = self.root / 'state.db'
        c = sqlite3.connect(self.db)
        c.executescript('CREATE TABLE sessions(id TEXT PRIMARY KEY, source TEXT, title TEXT, started_at REAL, ended_at REAL, last_activity_at REAL); CREATE TABLE messages(id INTEGER PRIMARY KEY, session_id TEXT, role TEXT, content TEXT, timestamp REAL);')
        c.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)', ('chat1','telegram','Garden plan',time.time()-864000,None,time.time()))
        c.executemany('INSERT INTO messages VALUES(?,?,?,?,?)', [(1,'chat1','user','OLD question',time.time()-20),(2,'chat1','assistant','OLD answer',time.time()-19)])
        c.commit(); c.close()

    def exporter(self, snapshot, sid, directory, hermes):
        c = sqlite3.connect(snapshot)
        rows = c.execute('SELECT id,content FROM messages WHERE session_id=? ORDER BY id',(sid,)).fetchall(); c.close()
        directory.mkdir(parents=True, exist_ok=True)
        p = directory / 'export.md'
        p.write_text('---\nsession_id: "chat1"\n---\n## Messages\n\n'+'\n'.join(text for _,text in rows))
        return p

    def prepare(self, **kw):
        return self.h.prepare(self.brain, [('main', self.db)], hours=24, exporter=self.exporter, **kw)

    def commit(self, item):
        draft=self.root/'draft.md'; draft.write_text('A conversation about the garden.\n\n'+pathlib.Path(item['export']).read_text())
        return self.h.commit(self.brain,item['token'],draft,'Garden plan')

    def add(self):
        c=sqlite3.connect(self.db)
        c.executemany('INSERT INTO messages VALUES(?,?,?,?,?)',[(3,'chat1','user','NEW question',time.time()),(4,'chat1','assistant','NEW answer',time.time())])
        c.commit(); c.close()

    def test_open_session_delta_and_rerun(self):
        first=self.prepare()['items']; self.assertEqual(len(first),1)
        self.assertTrue(first[0]['open'])
        note=self.commit(first[0]); original=pathlib.Path(note['note']).read_bytes()
        self.add()
        later=self.prepare()['items']; self.assertEqual(len(later),1)
        text=pathlib.Path(later[0]['export']).read_text()
        self.assertIn('NEW question',text); self.assertNotIn('OLD question',text)
        continued=self.commit(later[0]); content=pathlib.Path(continued['note']).read_text()
        self.assertIn('# Garden plan (continued)',content)
        self.assertIn('[[',content)
        self.assertEqual(pathlib.Path(note['note']).read_bytes(),original)
        self.assertEqual(self.prepare()['items'],[])
        self.assertEqual(len(list((self.brain/'01. Inbox/agent-drops').glob('*.md'))),2)

    def test_no_advance_on_missing_draft_and_recover_after_note_written(self):
        item=self.prepare()['items'][0]
        with self.assertRaises(FileNotFoundError): self.h.commit(self.brain,item['token'],self.root/'missing','Garden plan')
        self.assertFalse((self.brain/'_System/state/chat-capture-watermarks.json').exists())
        note=self.commit(item)
        (self.brain/'_System/state/chat-capture-watermarks.json').write_text('{}')
        self.assertEqual(self.prepare()['items'],[])
        self.assertEqual(len(list((self.brain/'01. Inbox/agent-drops').glob('*.md'))),1)

    def test_moved_note_and_stale_commit(self):
        item=self.prepare()['items'][0]; result=self.commit(item)
        moved=self.brain/'02. Projects'; moved.mkdir()
        pathlib.Path(result['note']).rename(moved/pathlib.Path(result['note']).name)
        self.add(); later=self.prepare()['items'][0]
        self.assertIn('02. Projects/',later['previous_note'])
        self.commit(later)
        self.assertEqual(self.commit(item)['status'],'already_committed')

    def test_seed_from_legacy_export_uses_historical_boundary(self):
        old=self.brain/'08. Sources/hermes-chats/2026-10-01/main'; old.mkdir(parents=True)
        (old/'chat1.md').write_text('---\nsession_id: "chat1"\nexported_at: "'+self.h.iso(time.time()-10)+'"\n---\n## Messages\n\nOLD question\nOLD answer')
        inbox=self.brain/'01. Inbox/agent-drops'; inbox.mkdir(parents=True)
        (inbox/'Garden.md').write_text('# Garden plan\nsource: main, telegram chat\noriginal: [[08. Sources/hermes-chats/2026-10-01/main/chat1]]\nOLD question\nOLD answer\n')
        self.add()
        seeded=self.h.seed(self.brain,[('main',self.db)],exporter=self.exporter)
        self.assertEqual(seeded['seeded'],1)
        state=json.loads((self.brain/'_System/state/chat-capture-watermarks.json').read_text())
        self.assertEqual(state['main/chat1']['last_message_id'],2)
        later=self.prepare(only_open=True, continued_only=True)['items']
        self.assertEqual(len(later),1)
        self.assertNotIn('OLD question',pathlib.Path(later[0]['export']).read_text())
        self.commit(later[0]); self.assertEqual(self.prepare()['items'],[])

    def test_compaction_clone_does_not_repeat_captured_turn(self):
        self.commit(self.prepare()['items'][0])
        c=sqlite3.connect(self.db)
        c.execute("INSERT INTO messages SELECT 3,session_id,role,content,timestamp FROM messages WHERE id=2")
        c.execute("INSERT INTO messages VALUES(4,'chat1','user','ACTUALLY NEW',?)",(time.time(),))
        c.commit(); c.close()
        item=self.prepare()['items'][0]
        text=pathlib.Path(item['export']).read_text()
        self.assertNotIn('OLD answer',text)
        self.assertIn('ACTUALLY NEW',text)

    def test_compaction_between_selection_and_snapshot_keeps_old_turn(self):
        c=sqlite3.connect(self.db)
        c.execute('ALTER TABLE messages ADD COLUMN active INTEGER DEFAULT 1')
        c.execute('ALTER TABLE messages ADD COLUMN compacted INTEGER DEFAULT 0')
        c.execute('UPDATE messages SET active=0 WHERE id=2')
        c.execute("INSERT INTO messages SELECT 3,session_id,role,content,timestamp,1,0 FROM messages WHERE id=2")
        c.commit(); c.close()
        snap=self.root/'snapshot.db'
        self.h.snapshot(self.db,'chat1',0,2,snap)
        c=sqlite3.connect(snap)
        visible=c.execute('SELECT content FROM messages WHERE active=1 OR compacted=1').fetchall(); c.close()
        self.assertIn(('OLD answer',),visible)

    def test_seed_refuses_timestamp_race(self):
        old=self.brain/'08. Sources/hermes-chats/2026-10-01/main'; old.mkdir(parents=True)
        (old/'chat1.md').write_text('---\nsession_id: "chat1"\nexported_at: "'+self.h.iso(time.time()+60)+'"\n---\n## Messages\n\nOLD question\nOLD answer')
        inbox=self.brain/'01. Inbox/agent-drops'; inbox.mkdir(parents=True)
        (inbox/'Garden.md').write_text('# Garden plan\noriginal: [[08. Sources/hermes-chats/2026-10-01/main/chat1]]')
        self.add()
        result=self.h.seed(self.brain,[('main',self.db)],exporter=self.exporter)
        self.assertEqual(result['seeded'],0)
        self.assertEqual(len(result['unresolved']),1)
        self.assertFalse((self.brain/'_System/state/chat-capture-watermarks.json').exists())

    def test_historical_verification_heading_inside_chat_is_preserved(self):
        text='---\nx: 1\n---\n## Messages\n\nOld words\n## Export verification\nQuoted example\nNEW words\n## Export verification\n- actual footer'
        self.assertIn('NEW words', self.h.transcript(text))

    def test_unresolved_seed_is_not_recaptured_on_normal_night(self):
        old=self.brain/'08. Sources/hermes-chats/2026-10-01/main'; old.mkdir(parents=True)
        (old/'chat1.md').write_text('---\nsession_id: "chat1"\nexported_at: "'+self.h.iso(time.time()+60)+'"\n---\n## Messages\n\nAn export that cannot be matched')
        inbox=self.brain/'01. Inbox/agent-drops'; inbox.mkdir(parents=True)
        (inbox/'Garden.md').write_text('# Garden plan\noriginal: [[08. Sources/hermes-chats/2026-10-01/main/chat1]]')
        self.h.seed(self.brain,[('main',self.db)],exporter=self.exporter)
        result=self.prepare()
        self.assertEqual(result['items'],[])
        self.assertTrue(result['errors'])

    def test_merged_note_seeds_and_blocks_each_link_independently(self):
        c=sqlite3.connect(self.db)
        c.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)',('chat2','telegram','Second plan',time.time(),None,time.time()))
        c.execute('INSERT INTO messages VALUES(?,?,?,?,?)',(3,'chat2','user','Second words',time.time()-20)); c.commit(); c.close()
        old=self.brain/'08. Sources/hermes-chats/2026-10-01/main'; old.mkdir(parents=True)
        stamp=self.h.iso(time.time())
        for sid,body in [('chat1','OLD question\nOLD answer'),('chat2','Unmatched words')]:
            (old/(sid+'.md')).write_text('---\nsession_id: "'+sid+'"\nexported_at: "'+stamp+'"\n---\n## Messages\n\n'+body)
        inbox=self.brain/'01. Inbox/agent-drops'; inbox.mkdir(parents=True)
        (inbox/'Merged.md').write_text('# Plans\n[[08. Sources/hermes-chats/2026-10-01/main/chat1]]\n[[08. Sources/hermes-chats/2026-10-01/main/chat2]]')
        seeded=self.h.seed(self.brain,[('main',self.db)],exporter=self.exporter)
        self.assertEqual(seeded['seeded'],1)
        result=self.prepare(); self.assertEqual(result['items'],[])
        self.assertTrue(any(e.get('key')=='main/chat2' for e in result['errors']))
        (old/'chat2.md').write_text('---\nsession_id: "chat2"\nexported_at: "'+stamp+'"\n---\n## Messages\n\nSecond words')
        seeded=self.h.seed(self.brain,[('main',self.db)],exporter=self.exporter)
        self.assertEqual(seeded['seeded'],1)
        self.assertEqual(self.prepare()['errors'],[])

    def test_dry_run_writes_nothing(self):
        result=self.prepare(dry_run=True)
        self.assertEqual(len(result['items']),1)
        self.assertEqual(list(self.brain.iterdir()),[])

if __name__=='__main__': unittest.main(verbosity=2)
