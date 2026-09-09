"""Check all required evidence spans, allowing their union across returned contexts."""
import argparse,json,hashlib
from pathlib import Path
from spec_search.retriever import Retriever,normalize

def run(db,suite):
    r=Retriever(db);rows=[]
    pages=[normalize(x['text']).lower() for x in r.con.execute('select text from pages where page>=?',(int(r.meta['first_body']),))]
    for case in json.loads(Path(suite).read_text())['multispan']:
        required=[normalize(x).lower() for x in case['required']]
        for s in required:
            if not any(s in p for p in pages):raise ValueError('Missing gold span: '+s)
        result=r.search(case['q'],5)
        row={'id':case['id'],'q':case['q'],'top_pages':[x['page'] for x in result['results']]}
        for k in [1,3,5]:
            context=[normalize(p['text']).lower() for hit in result['results'][:k] for p in hit['context']]
            found=[any(s in p for p in context) for s in required]
            row[f'complete@{k}']=all(found);row[f'spans_found@{k}']=found
        rows.append(row)
    out={'n':len(rows),'rows':rows,'suite_sha256':hashlib.sha256(Path(suite).read_bytes()).hexdigest(),**{f'complete@{k}':sum(x[f'complete@{k}'] for x in rows)/len(rows) for k in [1,3,5]}}
    r.close();return out

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--db',required=True);a.add_argument('--suite',required=True);a.add_argument('--out',required=True);args=a.parse_args();result=run(args.db,args.suite);Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
