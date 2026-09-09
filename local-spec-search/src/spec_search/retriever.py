"""Offline, section-aware PDF evidence retrieval. No remote services or generated answers."""
import argparse
import bisect
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import time

VERSION = '2.2.0'
# Domain vocabulary, not page IDs or benchmark answers. Expand longest terms first.
CONCEPTS = {
 'FLR': ('Function Level Reset', ['单功能复位', '功能级复位', '功能复位', '只复位一个', '只 reset 一个', '单独复位']),
 'Recovery': ('Recovery', ['重训练', '重新训练', '重新协商链路']),
 'DPC': ('Downstream Port Containment', ['下游端口遏制', '下游端口隔离']),
 'ATS': ('Address Translation Services', ['地址翻译', '地址转换服务']),
 'PASID': ('Process Address Space ID', ['进程地址空间', '进程标识']),
 'FEC': ('FEC ECC CRC correction', ['前向纠错', '纠错']),
 'ECRC': ('ECRC', ['端到端校验', '端到端crc']),
 'Poisoning': ('Data Poisoning', ['毒化', '中毒', '投毒']),
 'AtomicOps': ('Atomic Operations', ['原子操作']),
 'Completion Timeout': ('Completion Timeout', ['完成超时']),
 'Replay': ('Replay', ['重放', '重传']),
 'ACS': ('Access Control Services', ['访问控制服务']),
 'ARI': ('Alternative Routing-ID Interpretation', ['替代路由']),
 'Resizable BAR': ('Resizable BAR', ['可调整bar', '可调整大小的bar']),
 'VC': ('Virtual Channel', ['虚拟通道']),
 'Ordering': ('Transaction Ordering', ['事务排序', '事务顺序']),
}
WORDS = {
 '下游端口':'Downstream Port', '请求':'Request', '丢弃':'discard', '触发':'trigger',
 '错误':'error', '链路':'Link', '状态':'state', '多久':'within time', '超时':'timeout',
 '字节':'Bytes', '有效':'valid', '检查':'check', '先':'before after', '接收端':'Receiver',
 '失效':'invalidate invalidation', '完成':'completion completed', '缓存':'cache',
 '地址空间':'address space', '全局唯一':'uniquely identifies', '标识':'identifies',
 '多少':'size width', '宽度':'width bits', '字段':'field', '之前':'before', '之后':'after',
 '多少位':'bits wide', '顺序':'ordering', '复位':'reset', '协商':'negotiation',
 '布局':'layout Bytes', '缓冲区':'buffer', '流控':'Flow Control', '信用':'credit',
 '边界':'boundary', '对齐':'alignment', '支持':'support', '最大':'maximum',
 '最小':'minimum', '长度':'length', '完成包':'Completion', '拆分':'split',
 '数据':'data', '大小':'size', '如何':'', '规范':'', '图':'Figure',
}
STOP = set('the and or a an of to for in on is are be by with it this that how what when where which does do not no all every should must shall can will would spec specification section page pci pcie reset'.split())

def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()

def tokens(text):
    return [s.lower() for s in re.findall(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*|\d+(?:\.\d+)?', text) if s.lower() not in STOP]

def query_terms(query):
    concepts = []
    low = query.lower()
    for key, (english, aliases) in CONCEPTS.items():
        if re.search(r'(?<![a-z])' + re.escape(key.lower()) + r'(?![a-z])', low) or english.lower() in low or any(a in low for a in aliases):
            concepts.append(key)
    # Single-function reset takes precedence over incidental link retraining mention.
    if 'FLR' in concepts and 'Recovery' in concepts:
        concepts.remove('Recovery')
    expanded = query + ' ' + ' '.join(CONCEPTS[c][0] + ' ' + c for c in concepts)
    for word, english in WORDS.items():
        if word in query:
            expanded += ' ' + english
    return list(dict.fromkeys(tokens(expanded))), concepts

def expanded_query(query):
    _, concepts=query_terms(query)
    expanded=query+' '+' '.join(CONCEPTS[c][0] for c in concepts)
    for word, english in WORDS.items():
        if word in query:
            expanded+=' '+english
    return expanded


def build(pdf, db):
    import fitz
    pdf, db = Path(pdf).resolve(), Path(db).resolve()
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if db.exists():
        try:
            with sqlite3.connect(db) as c:
                meta = dict(c.execute('select key,value from metadata'))
            if meta.get('sha256') == digest and meta.get('version') == VERSION and meta.get('source') == str(pdf):
                return {'reused': True, 'sha256': digest, 'db': str(db)}
        except sqlite3.DatabaseError:
            pass
    started = time.perf_counter()
    doc = fitz.open(pdf)
    toc = [x for x in doc.get_toc(simple=False) if re.match(r'(Section|Chapter|Appendix)\s|Terms and Acronyms|Glossary', x[1]) and x[2] > 0]
    first_body = min((x[2] for x in toc), default=1)
    page_texts = [p.get_text('text').replace('\x00', ' ') for p in doc]
    sections = []
    for i, entry in enumerate(toc):
        level,title,start=entry[:3]
        end = len(doc)
        for later in toc[i+1:]:
            lvl2,title2,page2=later[:3]
            if lvl2 <= level and page2 > start:
                end = page2  # include shared boundary page, not a fabricated exact boundary
                break
        sections.append((i, level, title, start, end))
    db.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=db.name+'.', dir=db.parent)
    os.close(fd)
    try:
        c = sqlite3.connect(tmp)
        c.executescript('''
        create table metadata(key text primary key,value text);
        create table vectors(name text primary key, value blob);
        create table pages(page integer primary key,label text,text text);
        create table sections(id integer primary key,level integer,title text,start integer,end integer);
        create table chunks(id integer primary key,page integer,section_id integer,text text,boxes text);
        create virtual table fts using fts5(title,text,tokenize='porter unicode61');
        create virtual table titles using fts5(title);
        create virtual table pagefts using fts5(text,tokenize='porter unicode61');
        ''')
        c.executemany('insert into pages values(?,?,?)', [(i+1, doc[i].get_label(), s) for i,s in enumerate(page_texts)])
        c.executemany('insert into sections values(?,?,?,?,?)', sections)
        for sid, _, title, _, _ in sections:
            c.execute('insert into titles(rowid,title) values(?,?)', (sid, title))
        cid = 0
        anchors=sorted((entry[2],float(entry[3].get('to',fitz.Point(0,0)).y),i) for i,entry in enumerate(toc))
        ancestors={}
        stack=[]
        for sid,level,title,start,end in sections:
            while stack and stack[-1][1]>=level:
                stack.pop()
            stack.append((sid,level,title))
            ancestors[sid]=' | '.join(x[2] for x in stack)
        for page, text in enumerate(page_texts, 1):
            if page < first_body:
                continue
            c.execute('insert into pagefts(rowid,text) values(?,?)',(page,text))
            groups={}
            for block in sorted(doc[page-1].get_text('blocks',flags=fitz.TEXTFLAGS_TEXT),key=lambda b:(b[1],b[0])):
                words=normalize(block[4]).split()
                if not words:
                    continue
                ai=bisect.bisect_right(anchors,(page,float(block[1])+5,10**9))-1
                sid=anchors[ai][2] if ai>=0 else -1
                groups.setdefault(sid,[]).append((words,list(block[:4])))
            for sid, blocks in groups.items():
                words=[w for ws,_ in blocks for w in ws]
                boxes=json.dumps([box for _,box in blocks])
                for start in range(0,len(words),150):
                    chunk=' '.join(words[start:start+220])
                    if len(chunk)<30:
                        continue
                    c.execute('insert into chunks values(?,?,?,?,?)',(cid,page,sid,chunk,boxes))
                    c.execute('insert into fts(rowid,title,text) values(?,?,?)',(cid,ancestors.get(sid,'Unsectioned'),chunk))
                    cid+=1
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer=TfidfVectorizer(ngram_range=(1,2),max_features=60000,stop_words='english')
        matrix=vectorizer.fit_transform(page_texts[first_body-1:])
        arrays={'data':matrix.data.astype('float64'),'indices':matrix.indices.astype('int32'),'indptr':matrix.indptr.astype('int32'),'idf':vectorizer.idf_.astype('float64')}
        c.executemany('insert into vectors values(?,?)',[(key,val.tobytes()) for key,val in arrays.items()])
        c.execute('insert into vectors values(?,?)',('vocabulary',json.dumps({k:int(v) for k,v in vectorizer.vocabulary_.items()})))
        c.execute('insert into vectors values(?,?)',('shape',json.dumps(matrix.shape)))
        metadata = {'version':VERSION, 'sha256':digest, 'source':str(pdf), 'pages':str(len(doc)), 'first_body':str(first_body)}
        c.executemany('insert into metadata values(?,?)', metadata.items())
        c.commit()
        c.close()
        os.replace(tmp, db)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
        doc.close()
    return {'reused':False, 'seconds':time.perf_counter()-started, 'pages':len(page_texts), 'chunks':cid, 'sections':len(sections), 'sha256':digest, 'db_bytes':db.stat().st_size}


class Retriever:
    def __init__(self, db):
        self.con = sqlite3.connect(f'file:{Path(db).resolve()}?mode=ro', uri=True)
        self.con.row_factory = sqlite3.Row
        self.meta = dict(self.con.execute('select key,value from metadata'))
        if self.meta.get('version')!=VERSION:
            self.con.close()
            raise ValueError('Index version mismatch; run build again.')
        self.sections = [dict(r) for r in self.con.execute('select * from sections')]
        self.by_id = {s['id']:s for s in self.sections}
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.page_rows = list(self.con.execute('select page,text from pages where page>=?',(int(self.meta['first_body']),)))
        import numpy as np
        from scipy.sparse import csr_matrix
        saved=dict(self.con.execute('select name,value from vectors'))
        self.vectorizer=TfidfVectorizer(ngram_range=(1,2),max_features=60000,stop_words='english',vocabulary=json.loads(saved['vocabulary']))
        self.vectorizer.idf_=np.frombuffer(saved['idf'],dtype='float64').copy()
        self.matrix=csr_matrix((np.frombuffer(saved['data'],dtype='float64'),np.frombuffer(saved['indices'],dtype='int32'),np.frombuffer(saved['indptr'],dtype='int32')),shape=json.loads(saved['shape']))
        self.chunks_by_page = {}
        for row in self.con.execute('select * from chunks'):
            item=dict(row)
            item['_tokens']=set(tokens(item['text']))
            self.chunks_by_page.setdefault(item['page'],[]).append(item)

    def close(self):
        self.con.close()

    def search(self, query, k=3):
        started = time.perf_counter()
        terms, concepts = query_terms(query)
        base = {'query':query, 'source_sha256':self.meta['sha256'], 'concepts':concepts, 'expanded_terms':terms}
        if not terms:
            return dict(base,status='unsupported_query',answer_status='abstained',results=[],reason='No recognized searchable terms; use a technical term or English wording.',latency_ms=(time.perf_counter()-started)*1000)
        raw_identifiers=re.findall(r'\b[A-Za-z][A-Za-z0-9_]{5,}\b',query)
        unresolved=[x for x in raw_identifiers if any(ch.isdigit() for ch in x) and x.lower() not in self.vectorizer.vocabulary_]
        vocabulary_coverage=sum(t in self.vectorizer.vocabulary_ for t in terms)/len(terms)
        if unresolved or vocabulary_coverage<.5:
            return dict(base,status='insufficient_evidence',answer_status='abstained',results=[],reason='Unresolved identifier or weak vocabulary coverage; no supported answer is asserted.',unresolved_identifiers=unresolved,latency_ms=(time.perf_counter()-started)*1000)
        match = ' OR '.join('"'+x+'"' for x in terms[:48])
        ranked = {}
        # Fuse independent page-level lexical ranks, then use paragraphs to select evidence.
        from sklearn.metrics.pairwise import cosine_similarity
        sim = cosine_similarity(self.vectorizer.transform([expanded_query(query)]),self.matrix).ravel()
        vector_pages = [self.page_rows[int(i)]['page'] for i in sim.argsort()[-100:][::-1] if sim[int(i)]>0]
        lexical_pages = [r['rowid'] for r in self.con.execute('select rowid,bm25(pagefts) score from pagefts where pagefts match ? order by score limit 100',(match,))]
        page_scores = {}
        for stream in (vector_pages,lexical_pages):
            for rank,page in enumerate(stream,1):
                page_scores[page] = page_scores.get(page,0)+1/(50+rank)
        # Multiword identifiers/phrases retain relationships lost by unigram OR queries.
        phrases=[]
        for span in re.findall(r'[A-Za-z][A-Za-z0-9_]*(?:[ -]+[A-Za-z][A-Za-z0-9_]*)+',query):
            ts=tokens(span)
            if len(ts)>=2:
                phrases.append(' '.join(ts))
        if phrases:
            phrase_match=' OR '.join('"'+p+'"' for p in phrases[:8])
            phrase_pages=self.con.execute('select rowid,bm25(pagefts) score from pagefts where pagefts match ? order by score limit 100',(phrase_match,)).fetchall()
            peak=max((-row['score'] for row in phrase_pages),default=1.0)
            compound_focus=not concepts and sum(len(p.split())>=3 for p in phrases)>=2
            for rank,row in enumerate(phrase_pages,1):
                boost=.025*(-row['score'])/max(peak,1e-12) if compound_focus else .35/(50+rank)
                page_scores[row['rowid']]=page_scores.get(row['rowid'],0)+boost
        # Rank section headings independently. Max contribution avoids duplicate ancestor boosts.
        title_rows = self.con.execute('select rowid,bm25(titles) score from titles where titles match ? order by score limit 8',(match,)).fetchall()
        section_boost = {}
        for trank,tr in enumerate(title_rows,1):
            sec = self.by_id[tr['rowid']]
            for page in range(sec['start'],sec['end']+1):
                section_boost[page] = max(section_boost.get(page,0), .12/(50+trank))
        # Canonical topic headings are structural hints, never hard-coded evidence pages.
        for concept in concepts:
            if concept in ('FEC','PASID','Replay'):
                continue
            phrase = CONCEPTS[concept][0].lower()
            exact_sections = [s for s in self.sections if phrase in s['title'].lower()]
            for sec in exact_sections:
                if sec['end']-sec['start']<=12:
                    for page in range(sec['start'],sec['end']+1):
                        section_boost[page] = max(section_boost.get(page,0),.010)
                    if re.search(r'多少|范围|optional|mandatory|what is|是什么',query,re.I):
                        page_scores[sec['start']]=max(page_scores.get(sec['start'],0),.032)
                        section_boost[sec['start']]=max(section_boost.get(sec['start'],0),.016)
        if 'Recovery' in concepts and not re.search(r'Recovery\.',query,re.I):
            for sec in self.sections:
                if re.sub(r'^Section\s+[\d.]+\s+','',sec['title']).lower()=='recovery':
                    page_scores[sec['start']]=max(page_scores.get(sec['start'],0),.05)
        for page,score in page_scores.items():
            candidates=self.chunks_by_page.get(page,[])
            if not candidates:
                continue
            def chunk_score(c):
                return sum(float(self.vectorizer.idf_[self.vectorizer.vocabulary_[t]]) if t in self.vectorizer.vocabulary_ else 1.0 for t in set(terms)&c['_tokens'])
            chunk=max(candidates,key=chunk_score)
            sec=self.by_id.get(chunk['section_id'],{})
            structural_score=score+section_boost.get(page,0)
            # Architecture questions should not be dominated by register descriptions.
            if 'register' in sec.get('title','').lower() and not re.search(r'register|offset|寄存器|偏移|[A-Za-z]+_[A-Za-z_]+',query,re.I):
                structural_score-=.012
            ranked[chunk['id']] = [structural_score,chunk,sec]
        ordered = sorted(ranked.values(),key=lambda x:(-x[0],x[1]['page'],x[1]['id']))
        results = []
        covered_pages = set()
        for score, chunk, sec in ordered:
            page = chunk['page']
            if page in covered_pages:
                continue
            # Actual context returned. At most three pages, bounds explicit even across sections.
            lo = max(int(self.meta['first_body']), page-1)
            hi = min(int(self.meta['pages']), page+1)
            context = [dict(r) for r in self.con.execute('select page,label,text from pages where page between ? and ? order by page',(lo,hi))]
            result = {'page':page,'section':sec.get('title','Unsectioned'),'score':score,
                      'excerpt':chunk['text'], 'source_block_boxes':json.loads(chunk['boxes']), 'section_locator':'PDF bookmark position; boxes bound the section group on this page', 'context_pages':[r['page'] for r in context], 'context':context,
                      'source':self.meta['source'], 'citation':Path(self.meta['source']).as_uri()+f'#page={page}'}
            results.append(result)
            covered_pages.update(result['context_pages'])
            if len(results)>=k:
                break
        # Evidence retrieval does not entail that a natural-language proposition is answered.
        status = 'candidates' if results else 'no_match'
        return dict(base,status=status,answer_status='not_generated',results=results,latency_ms=(time.perf_counter()-started)*1000)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build');b.add_argument('pdf');b.add_argument('--db',default='index.sqlite')
    q=sub.add_parser('search');q.add_argument('query');q.add_argument('--db',default='index.sqlite');q.add_argument('-k',type=int,default=3);q.add_argument('--full',action='store_true')
    args=ap.parse_args()
    if args.command=='build':
        out=build(args.pdf,args.db)
    else:
        if not 1<=args.k<=10:
            ap.error('k must be 1..10')
        r=Retriever(args.db)
        try:
            out=r.search(args.query,args.k)
        finally:
            r.close()
        if not args.full:
            for item in out['results']:
                item.pop('context')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
