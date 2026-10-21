import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import statistics
from app.config import settings
from app.retrieval.dense_search import dense_search
from app.retrieval.lexical_search import lexical_search
from app.retrieval.context_builder import context_builder

questions_file = Path('evaluation/questions_v2.jsonl')
questions = [json.loads(line) for line in open(questions_file, encoding='utf-8-sig') if line.strip() and json.loads(line).get('answerable', True)]

cache = []
for q in questions:
    dense_res = dense_search.search(query=q['query'], top_k=20)
    lex_res = lexical_search.search(query=q['query'], top_k=20)
    cache.append({
        'question': q,
        'dense': dense_res,
        'lexical': lex_res
    })

def custom_rrf(dense_results, lexical_results, k=60, w_dense=1.0, w_lex=1.0, top_k=6):
    scores = {}
    doc_map = {}
    for rank, doc in enumerate(dense_results):
        cid = doc['chunk_id']
        scores[cid] = scores.get(cid, 0.0) + w_dense * (1.0 / (k + rank + 1))
        doc_map[cid] = doc
    for rank, doc in enumerate(lexical_results):
        cid = doc['chunk_id']
        scores[cid] = scores.get(cid, 0.0) + w_lex * (1.0 / (k + rank + 1))
        if cid not in doc_map:
            doc_map[cid] = doc
    sorted_cids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)[:top_k]
    res = []
    for cid in sorted_cids:
        d = dict(doc_map[cid])
        d['rrf_score'] = scores[cid]
        res.append(d)
    return res

print(f"{'Configuration':<42} | {'Term Recall':<12} | {'Perfect Rec':<12} | {'Source Acc':<12}")
print("-" * 85)

configs = [
    ('Dense Only (Baseline)', 60, 1.0, 0.0),
    ('BM25 Only', 60, 0.0, 1.0),
    ('Standard RRF (k=10)', 10, 1.0, 1.0),
    ('Standard RRF (k=20)', 20, 1.0, 1.0),
    ('Standard RRF (k=40)', 40, 1.0, 1.0),
    ('Standard RRF (k=60) [Initial]', 60, 1.0, 1.0),
    ('Standard RRF (k=100)', 100, 1.0, 1.0),
    ('Weighted RRF (k=30, w_lex=1.4)', 30, 1.0, 1.4),
    ('Weighted RRF (k=20, w_lex=1.5)', 20, 1.0, 1.5),
    ('Weighted RRF (k=20, w_lex=1.2)', 20, 1.0, 1.2),
    ('Weighted RRF (k=15, w_lex=1.3)', 15, 1.0, 1.3),
]

opt_results = {}
for name, k, wd, wl in configs:
    recalls = []
    perfects = []
    source_hits = 0
    for item in cache:
        q = item['question']
        fused = custom_rrf(item['dense'], item['lexical'], k=k, w_dense=wd, w_lex=wl, top_k=6)
        ctx, _ = context_builder.build_context(fused, max_chunks=6)
        
        ctx_lower = ctx.lower()
        expected = q.get('expected_terms', [])
        found = [t for t in expected if t.lower() in ctx_lower]
        rec = len(found) / len(expected) if expected else 1.0
        recalls.append(rec)
        perfects.append(1.0 if rec >= 1.0 else 0.0)
        
        expected_src = q.get('expected_source')
        if expected_src:
            hit = any(expected_src.lower() in c.get('filename', '').lower() for c in fused)
            if hit: source_hits += 1
            
    m_rec = statistics.mean(recalls)
    m_perf = statistics.mean(perfects)
    src_acc = source_hits / len(cache)
    opt_results[name] = {'term_recall': round(m_rec, 4), 'perfect_recall': round(m_perf, 4), 'source_acc': round(src_acc, 4)}
    print(f"{name:<42} | {m_rec:<12.4f} | {m_perf:<12.4f} | {src_acc:<12.4f}")

with open('evaluation/reports/tuning_experiments.json', 'w', encoding='utf-8') as f:
    json.dump(opt_results, f, indent=2)
print('\nTuning experiment complete and saved to evaluation/reports/tuning_experiments.json')
