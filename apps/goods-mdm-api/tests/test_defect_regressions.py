"""七项缺陷的真实 API/数据库回归；连接只由 conftest 的隔离配置提供。"""
import asyncio
import csv
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core import auth, audit as audit_module, db
from app.main import app
from app.routers import goods as goods_router, barcodes as barcode_router
from test_contracts import client, hdr

pytestmark = pytest.mark.usefixtures("contract_users")


def codes(n=1):
    base = 3000000000000 + uuid4().int % 1000000000000
    return [str(base+i) for i in range(n)]


def query(sql, args=()):
    with db.conn_app() as c, c.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall() if cur.description else None


def snapshot(barcodes):
    state = {}
    for table in ('mdm_goods','mdm_goods_attrs','mdm_goods_history'):
        state[table] = query(f'SELECT * FROM {table} WHERE barcode=ANY(%s) ORDER BY 1', (barcodes,))
    state['mdm_barcode_alias'] = query('SELECT * FROM mdm_barcode_alias WHERE alias_barcode=ANY(%s) OR master_barcode=ANY(%s) ORDER BY 1', (barcodes,barcodes))
    state['sys_change_log'] = query('SELECT * FROM sys_change_log WHERE entity_key=ANY(%s) ORDER BY 1', (barcodes,))
    return state


def create(barcode=None, **fields):
    barcode = barcode or codes()[0]
    r = client.post('/api/v1/goods', headers=hdr('Operator'),
                    json=dict(barcode=barcode, goods_name=fields.pop('goods_name','独立回归 '+barcode), **fields))
    assert r.json()['code'] == 0, r.text
    return barcode


def move(old, new, api=client):
    return api.post('/api/v1/barcodes/reassign', headers=hdr('Steward'),
                    json=dict(old_barcode=old, new_barcode=new, reason='隔离回归'))


def test_reassign_migrates_all_links_and_history():
    old, new, third, alias = codes(4)
    create(old, attrs={'规格': '大瓶'})
    query("INSERT INTO mdm_barcode_alias(alias_barcode,master_barcode,alias_type) VALUES(%s,%s,'BIG_PACK')", (alias,old))
    assert move(old,new).json()['code'] == 0
    assert move(new,third).json()['code'] == 0
    assert query('SELECT barcode FROM mdm_goods WHERE barcode=ANY(%s)', ([old,new,third],)) == [(third,)]
    assert query('SELECT barcode,attrs_json FROM mdm_goods_attrs WHERE barcode=ANY(%s)', ([old,new,third],)) == [(third,{'规格':'大瓶'})]
    history = query('SELECT barcode,field_name,old_value,new_value FROM mdm_goods_history WHERE barcode=ANY(%s) ORDER BY hist_id', ([old,new,third],))
    assert [h[0] for h in history] == [third]*3
    assert history[-2][1:] == ('barcode',old,new)
    assert history[-1][1:] == ('barcode',new,third)
    links = query('SELECT alias_barcode,master_barcode,alias_type,banned_until FROM mdm_barcode_alias WHERE master_barcode=%s', (third,))
    assert {r[0] for r in links} == {old,new,alias}
    assert all(r[3] is not None for r in links if r[2]=='VOIDED_BAN')
    assert query("SELECT count(*) FROM sys_change_log WHERE action='REASSIGN' AND entity_key=ANY(%s)", ([old,new],)) == [(2,)]


def test_reassign_audit_failure_rolls_back_every_table(monkeypatch):
    old,new,alias = codes(3)
    create(old,attrs={'a':1})
    query("INSERT INTO mdm_barcode_alias(alias_barcode,master_barcode,alias_type) VALUES(%s,%s,'OLD_CODE')",(alias,old))
    before = snapshot([old,new,alias])
    batches = query("SELECT count(*) FROM sys_gov_batch")
    def fail(*args,**kwargs):
        raise RuntimeError('injected audit failure')
    monkeypatch.setattr(barcode_router,'audit',fail)
    with TestClient(app,raise_server_exceptions=False) as api:
        assert move(old,new,api).status_code==500
    assert snapshot([old,new,alias]) == before
    assert query("SELECT count(*) FROM sys_gov_batch") == batches


@pytest.mark.parametrize('kind,expected', [('missing',3001),('occupied',3001),('alias',3001),('ban',3003),('isbn',3004),('same',3001),('voided',3007),('orphan',3001)])
def test_reassign_rejects_invalid_destinations_without_writes(kind,expected):
    old,new = codes(2)
    if kind!='missing': create(old)
    if kind=='occupied': create(new)
    if kind in ('alias','ban'):
        query("INSERT INTO mdm_barcode_alias(alias_barcode,master_barcode,alias_type,banned_until) VALUES(%s,%s,%s,current_date+90)", (new,old,'VOIDED_BAN' if kind=='ban' else 'OLD_CODE'))
    if kind=='isbn': new='978'+new[3:]
    if kind=='same': new=old
    if kind=='voided': query("UPDATE mdm_goods SET status='VOIDED' WHERE barcode=%s",(old,))
    if kind=='orphan': query("INSERT INTO mdm_goods_attrs(barcode) VALUES(%s)",(new,))
    before = snapshot([old,new])
    assert move(old,new).json()['code']==expected
    assert snapshot([old,new]) == before


@pytest.fixture
def tree():
    prefix='T'+uuid4().hex[:8]
    ids=[prefix+str(i) for i in range(6)]
    rows=[(ids[0],None,1,'根',0,'ACTIVE'),(ids[1],ids[0],2,'中',0,'ACTIVE'),
          (ids[2],ids[1],3,'叶',1,'ACTIVE'),(ids[3],ids[0],2,'停',1,'DEPRECATED'),
          (ids[4],'missing',2,'断',1,'ACTIVE'),(ids[5],ids[5],2,'环',1,'ACTIVE')]
    with db.conn_app() as c,c.cursor() as cur:
        cur.executemany('INSERT INTO mdm_category(category_id,parent_id,category_level,category_path,category_name,is_leaf,status) VALUES(%s,%s,%s,\'/stale/\',%s,%s,%s)',rows)
    return ids


def test_category_create_import_change_paths_and_lineage(tree):
    root,middle,leaf,*_=tree
    barcode=create(category_id=leaf)
    expected=f'/{root}/{middle}/{leaf}/'
    assert query('SELECT category_path,category_source FROM mdm_goods WHERE barcode=%s',(barcode,))==[(expected,'MANUAL')]
    detail=client.get('/api/v1/goods/'+barcode,headers=hdr('Viewer')).json()['data']
    listing=client.get('/api/v1/goods',params={'q':barcode},headers=hdr('Viewer')).json()['data']['items'][0]
    for item in (detail,listing): assert (item['category_path'],item['category_code_path'])==('根 / 中 / 叶',expected)
    imported=codes()[0]
    result=client.post('/api/v1/goods/import',headers=hdr('Operator'),files={'file':('g.csv',f'barcode,goods_name,category_id\n{imported},导入,{leaf}\n'.encode(),'text/csv')}).json()['data']
    assert result['success']==1
    assert query('SELECT category_path FROM mdm_goods WHERE barcode=%s',(imported,))==[(expected,)]
    other=create()
    query("UPDATE mdm_goods SET category_source='AI_FILLBACK',category_confidence=.8,decision_trace='original lineage',governance_batch='original batch' WHERE barcode=%s",(other,))
    assert client.post(f'/api/v1/goods/{other}/category',headers=hdr('Operator'),json={'category_id':leaf}).json()['code']==0
    assert query('SELECT category_path,category_source,category_confidence,decision_trace,governance_batch FROM mdm_goods WHERE barcode=%s',(other,))==[(expected,'MANUAL',None,'original lineage','original batch')]


def test_category_rejects_bad_trees_and_read_is_bounded(tree):
    barcode=create()
    for cid in [tree[0],*tree[3:],'absent']:
        r=client.post('/api/v1/goods',headers=hdr('Operator'),json={'barcode':codes()[0],'goods_name':'拒绝','category_id':cid})
        assert r.json()['code']==3005
        assert client.post(f'/api/v1/goods/{barcode}/category',headers=hdr('Operator'),json={'category_id':cid}).json()['code']==3005
    for cid in tree[4:]:
        query('UPDATE mdm_goods SET category_id=%s,category_path=%s WHERE barcode=%s',(cid,'/stale/',barcode))
        data=client.get('/api/v1/goods/'+barcode,headers=hdr('Viewer')).json()['data']
        assert data['category_path'] is None and data['category_code_path']=='/stale/'


@pytest.mark.parametrize('prefix',['978','979'])
def test_isbn_policy_consistent_across_three_entries(prefix):
    barcode=prefix+codes()[0][3:]
    assert not client.post('/api/v1/barcodes/validate',headers=hdr('Operator'),json={'barcode':barcode}).json()['data']['allowed']
    assert client.post('/api/v1/goods',headers=hdr('Operator'),json={'barcode':barcode,'goods_name':'图书'}).json()['code']==3004
    data=client.post('/api/v1/goods/import',headers=hdr('Operator'),files={'file':('g.csv',f'barcode,goods_name\n{barcode},图书\n'.encode(),'text/csv')}).json()['data']
    assert (data['success'],data['failed'])==(0,1)
    assert query('SELECT barcode FROM mdm_goods WHERE barcode=%s',(barcode,))==[]


def test_real_authentication_serializes_failures_and_reset():
    account='auth_'+uuid4().hex[:12]
    query("INSERT INTO sys_user(account,display_name,role,status,password_hash) VALUES(%s,%s,'Viewer','ACTIVE',%s)",(account,account,auth.hash_password('correct')))
    barrier=Barrier(8)
    def wrong(_):
        barrier.wait()
        try: auth.authenticate(account,'wrong')
        except HTTPException as exc: return exc.status_code
    with ThreadPoolExecutor(max_workers=8) as pool: assert list(pool.map(wrong,range(8)))==[401]*8
    failed,locked=query('SELECT failed_attempts,locked_until FROM sys_user WHERE account=%s',(account,))[0]
    assert failed==5 and locked>datetime.now(timezone.utc)
    with pytest.raises(HTTPException): auth.authenticate(account,'correct')
    query("UPDATE sys_user SET locked_until=now()-interval '1 minute' WHERE account=%s",(account,))
    assert auth.authenticate(account,'correct')==(account,'Viewer',0)
    assert query('SELECT failed_attempts,locked_until FROM sys_user WHERE account=%s',(account,))==[(0,None)]
    # A success racing a failure must be one of the two serial outcomes.
    barrier=Barrier(2)
    def attempt(password):
        barrier.wait()
        try: return auth.authenticate(account,password)
        except HTTPException: return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(attempt,['correct','wrong']))
    assert results==[(account,'Viewer',0),None]
    assert query('SELECT failed_attempts FROM sys_user WHERE account=%s',(account,))[0][0] in (0,1)


def test_same_second_imports_have_unique_batch_and_multiple_logs(monkeypatch):
    class Frozen:
        @staticmethod
        def now(): return datetime(2026,11,27,12,0,0)
    monkeypatch.setattr(audit_module,'datetime',Frozen)
    def import_one(barcode):
        return client.post('/api/v1/goods/import',headers=hdr('Operator'),files={'file':('g.csv',f'barcode,goods_name\n{barcode},并发导入\n'.encode(),'text/csv')}).json()['data']
    with ThreadPoolExecutor(max_workers=2) as pool: jobs=list(pool.map(import_one,codes(2)))
    assert all(j['success']==1 for j in jobs)
    assert len({j['batch_id'] for j in jobs})==2
    with db.conn_app() as c,c.cursor() as cur:
        for _ in range(2): audit_module.audit(cur,entity_type='TEST',entity_key='batch',action='TEST',operator='ct_operator',batch_id=jobs[0]['batch_id'])
    assert query('SELECT count(*) FROM sys_change_log WHERE batch_id=%s',(jobs[0]['batch_id'],))==[(2,)]


def test_export_real_named_cursor_multiple_batches_and_audit():
    marker='export_'+uuid4().hex
    with db.conn_app() as c,c.cursor() as cur:
        cur.execute("INSERT INTO mdm_goods(barcode,goods_name,quality_grade,governance_batch) SELECT %s||lpad(i::text,8,'0'),%s,'C','TEST' FROM generate_series(1,4101) i",(marker,marker))
    r=client.get('/api/v1/goods/export',params={'q':marker},headers=hdr('Viewer'))
    rows=list(csv.reader(io.StringIO(r.content.decode('utf-8-sig'))))
    assert len(rows)==4102 and len(rows[0])==9
    assert r.headers['x-export-limit']=='200000'
    assert query("SELECT after_data->>'rows',after_data->>'state' FROM sys_change_log WHERE action='EXPORT_RESULT' AND after_data->'filters'->>'q'=%s",(marker,))==[('4101','COMPLETED')]
    assert not db._pool('app')._used
    query('DELETE FROM mdm_goods WHERE goods_name=%s',(marker,))


@pytest.mark.parametrize('failure',['disconnect','send_error'])
def test_export_asgi_exit_releases_cursor_and_connection(failure):
    response=goods_router.export_goods({}, {'account':'ct_viewer'})
    scope={'type':'http','asgi':{'spec_version':'2.3'},'method':'GET','path':'/','headers':[]}
    async def run():
        sent=asyncio.Event()
        async def receive():
            await sent.wait()
            return {'type':'http.disconnect'}
        async def send(message):
            if message['type']=='http.response.body':
                assert db._pool('app')._used  # Cursor/connection active after header.
                sent.set()
                if failure=='send_error': raise OSError('closed transport')
        try: await response(scope,receive,send)
        except OSError:
            assert failure=='send_error'
    asyncio.run(run())
    assert not db._pool('app')._used
    with db.conn_app() as c,c.cursor() as cur:
        cur.execute('SELECT name FROM pg_cursors')
        assert cur.fetchall()==[]
        cur.execute('SELECT 1')
        assert cur.fetchone()==(1,)


def test_export_limit_and_explicit_truncation():
    marker='cap_'+uuid4().hex
    query("INSERT INTO mdm_goods(barcode,goods_name,quality_grade,governance_batch) SELECT %s||i::text,%s,'C','TEST' FROM generate_series(1,200001) i",(marker,marker))
    r=client.get('/api/v1/goods/export',params={'q':marker},headers=hdr('Viewer'))
    rows=list(csv.reader(io.StringIO(r.content.decode('utf-8-sig'))))
    assert len(rows)==200002
    assert rows[-1][0]=='#' and '截断' in rows[-1][1]
    assert all(row[1]==marker for row in rows[1:-1])
    assert query("SELECT after_data->>'rows',after_data->>'truncated' FROM sys_change_log WHERE action='EXPORT_RESULT' AND after_data->'filters'->>'q'=%s",(marker,))==[('200000','true')]
    query('DELETE FROM mdm_goods WHERE goods_name=%s',(marker,))


def test_export_database_failure_releases_connection(monkeypatch):
    monkeypatch.setattr(goods_router.dg,'export_query',lambda *a: ('SELECT 1/0', []))
    response=goods_router.export_goods({}, {'account':'ct_viewer'})
    with pytest.raises(Exception): next(response.producer)
    assert not db._pool('app')._used
    assert query('SELECT 1')==[(1,)]


def test_quarantine_stream_retains_readonly_role_and_closes():
    from app.routers.admin import quarantine_export
    response=quarantine_export(None,None,{'account':'ct_viewer'})
    header=next(response.producer)
    assert '条码' in header
    assert db._pool('ro')._used
    response.producer.close()
    assert not db._pool('ro')._used
    with db.conn_ro() as c,c.cursor() as cur:
        cur.execute('SELECT current_user')
        assert cur.fetchone()==('goods_test_ro',)
        cur.execute('SELECT name FROM pg_cursors')
        assert cur.fetchall()==[]


def test_competing_reassigns_have_one_winner():
    first,second,dest=codes(3)
    create(first,attrs={'owner':first})
    create(second,attrs={'owner':second})
    barrier=Barrier(2)
    def attempt(source):
        barrier.wait()
        return move(source,dest).json()['code']
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(attempt,[first,second]))
    assert sorted(outcomes)==[0,3001]
    winner,loser=(first,second) if outcomes[0]==0 else (second,first)
    assert query('SELECT attrs_json FROM mdm_goods_attrs WHERE barcode=%s',(dest,))==[({'owner':winner},)]
    assert query('SELECT attrs_json FROM mdm_goods_attrs WHERE barcode=%s',(loser,))==[({'owner':loser},)]
    assert query('SELECT master_barcode FROM mdm_barcode_alias WHERE alias_barcode=%s',(winner,))==[(dest,)]


def test_category_list_reads_catalog_once(tree):
    from app.daos import goods
    marker='paths_'+uuid4().hex
    for _ in range(3): create(category_id=tree[2],goods_name=marker)
    with db.conn_app() as c,c.cursor() as raw:
        class CountCursor:
            queries=[]
            def execute(self,sql,args=None):
                self.queries.append(sql)
                return raw.execute(sql,args)
            def __getattr__(self,name): return getattr(raw,name)
        cur=CountCursor()
        data=goods.list_goods(cur,{'q':marker})
    assert len(data['items'])==3
    assert len(cur.queries)==4  # count, estimate, page, and ONE catalog read.
    assert all(item['category_path']=='根 / 中 / 叶' for item in data['items'])
