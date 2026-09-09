"""Evidence-span evaluation: strict gold, returned-context checks, repeat latency."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import time
from spec_search.retriever import Retriever, normalize


def evaluate(db, suite):
    engine = Retriever(db)
    pages = {row['page']:normalize(row['text']).lower() for row in engine.con.execute('select page,text from pages')}
    first = int(engine.meta['first_body'])
    report = {'source_sha256':engine.meta['sha256'],'suite_sha256':hashlib.sha256(Path(suite).read_bytes()).hexdigest(),'groups':{}}
    for name, tests in json.loads(Path(suite).read_text()).items():
        rows=[]
        for test in tests:
            gold=[]
            if 'e' in test:
                phrase=normalize(test['e']).lower()
                gold=[p for p,s in pages.items() if p>=first and phrase in s]
                if not gold:
                    raise ValueError(f"Full gold phrase missing from body: {test['id']}")
            result=engine.search(test['q'],5)
            top=result['results']
            rank_page=next((i for i,r in enumerate(top,1) if r['page'] in gold),None)
            # Check full literal gold phrase in ACTUAL returned pages, not distance to a page.
            rank_context=next((i for i,r in enumerate(top,1) if 'e' in test and any(phrase in normalize(p['text']).lower() for p in r['context'])),None)
            rows.append({'id':test['id'],'query':test['q'],'gold_pages':gold,'top_pages':[r['page'] for r in top],'context_pages':[r['context_pages'] for r in top], 'page_rank':rank_page,'evidence_rank':rank_context,'status':result['status'], 'answer_status':result.get('answer_status'),'ms':result['latency_ms']})
        positive=[r for r in rows if r['gold_pages']]
        summary={'n':len(rows),'rows':rows}
        if positive:
            summary.update({f'{metric}@{k}':sum(r[field] is not None and r[field]<=k for r in positive)/len(positive) for metric,field in [('page_recall','page_rank'),('returned_evidence','evidence_rank')] for k in (1,3,5)})
        report['groups'][name]=summary
    # 5 passes over the full suite; nearest-rank p95, warmup excluded.
    queries=[r['query'] for g in report['groups'].values() for r in g['rows']]
    lat=[]
    for _ in range(5):
        for q in queries:
            lat.append(engine.search(q,3)['latency_ms'])
    report['latency']={'n':len(lat),'p50_ms':statistics.median(lat),'p95_ms':sorted(lat)[math.ceil(.95*len(lat))-1],'max_ms':max(lat),'definition':'warm index; parsing/answer generation/UI excluded; nearest-rank p95'}
    engine.close()
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--db',required=True);ap.add_argument('--suite',required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
    result=evaluate(args.db,args.suite)
    Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({g:{k:v for k,v in d.items() if k!='rows'} for g,d in result['groups'].items()},indent=2));print(result['latency'])
