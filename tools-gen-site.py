#!/usr/bin/env python3
"""Generate the exploration-log site from test-results*.json files.

Site structure (fully static, no dependencies):
  index.html   — landing: latest run summary + stats
  log.html     — execution log: one entry per test run
  catalog.html — catalog of unique tests across all runs

Usage: python3 gen-site.py <site-dir> <results.json ...>
Each results file may carry optional sidecar metadata: <file>.meta.json
with {"run": "name", "timestamp": "ISO", "battery": "desc"}.
"""
import json, sys, html, os, datetime

def e(s): return html.escape(str(s))

def load_runs(paths):
    runs = []
    for p in paths:
        results = json.load(open(p))
        meta_p = p + '.meta.json'
        meta = {}
        if os.path.exists(meta_p):
            meta = json.load(open(meta_p))
        passed = sum(1 for r in results if r.get('ok'))
        runs.append({
            'file': os.path.basename(p),
            'run': meta.get('run', os.path.basename(p).replace('.json','')),
            'timestamp': meta.get('timestamp', ''),
            'battery': meta.get('battery', ''),
            'results': results,
            'passed': passed,
            'total': len(results),
        })
    return runs

def build_catalog(runs):
    catalog = {}
    for run in runs:
        for r in run['results']:
            tid = r['id']
            if tid not in catalog:
                catalog[tid] = {'id': tid, 'title': r['title'], 'desc': r['desc'],
                                'history': [], 'first': run['timestamp'] or run['run'],
                                'last': run['timestamp'] or run['run']}
            catalog[tid]['history'].append({
                'run': run['run'], 'timestamp': run['timestamp'],
                'ok': r.get('ok'), 'detail': r.get('detail','')})
            catalog[tid]['last'] = run['timestamp'] or run['run']
    return catalog

CSS = '''
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,'Segoe UI',Roboto,sans-serif; background:#faf9f6; color:#1a1d23; line-height:1.6; max-width:980px; margin:0 auto; padding:2rem 1.25rem 4rem; }
header { background:linear-gradient(135deg,#1f2430,#3d3a1f); color:#fff; border-radius:16px; padding:2rem 2rem; margin-bottom:1.6rem; position:relative; }
header .kicker { text-transform:uppercase; letter-spacing:.18em; font-size:.72rem; color:#f5c518; font-weight:700; }
header h1 { font-size:1.7rem; margin:.4rem 0 .3rem; }
header .sub { color:#c9cedd; font-size:.92rem; }
nav { display:flex; gap:.6rem; margin:0 0 1.6rem; flex-wrap:wrap; }
nav a { background:#fff; border:1px solid #e8e5de; border-radius:999px; padding:.4rem 1rem; text-decoration:none; color:#1a1d23; font-size:.88rem; font-weight:600; }
nav a:hover { border-color:#b8860b; }
nav a.active { background:#1a1d23; color:#f5c518; border-color:#1a1d23; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.7rem; margin-bottom:1.8rem; }
.stat { background:#fff; border:1px solid #e8e5de; border-radius:12px; padding:.9rem 1rem; }
.stat b { font-size:1.4rem; display:block; }
.stat span { font-size:.72rem; color:#8a90a2; text-transform:uppercase; letter-spacing:.07em; }
section { margin-bottom:2.2rem; }
h2 { font-size:1.2rem; margin-bottom:.8rem; }
.run { background:#fff; border:1px solid #e8e5de; border-left:4px solid #1a8f4a; border-radius:12px; padding:1rem 1.2rem; margin-bottom:.9rem; }
.run.fail-major { border-left-color:#c62828; }
.run-head { display:flex; align-items:baseline; gap:.8rem; flex-wrap:wrap; }
.run-date { font-family:monospace; font-size:.75rem; color:#8a90a2; }
.run-name { font-weight:700; }
.run-score { margin-left:auto; font-weight:800; font-size:.9rem; }
.run-score.ok { color:#1a8f4a; } .run-score.bad { color:#c62828; }
.run-battery { color:#4a5060; font-size:.88rem; margin:.25rem 0 .5rem; }
.tests { display:grid; gap:.4rem; }
.t { display:flex; gap:.6rem; align-items:baseline; font-size:.86rem; padding:.35rem .6rem; background:#f7f5f0; border-radius:8px; }
.t .tid { font-family:monospace; font-weight:700; color:#b8860b; font-size:.74rem; flex:none; }
.t .mark { flex:none; font-weight:800; }
.t .mark.ok { color:#1a8f4a; } .t .mark.bad { color:#c62828; }
.t .detail { color:#6a7080; font-size:.78rem; font-family:monospace; overflow-wrap:anywhere; }
.cat { background:#fff; border:1px solid #e8e5de; border-radius:12px; padding:.95rem 1.1rem; margin-bottom:.7rem; }
.cat-head { display:flex; gap:.6rem; align-items:baseline; flex-wrap:wrap; }
.cat-id { font-family:monospace; font-weight:700; color:#b8860b; font-size:.78rem; background:#fdf6d8; border-radius:6px; padding:.1rem .45rem; }
.cat-title { font-weight:700; font-size:.95rem; }
.cat-passrate { margin-left:auto; font-weight:800; font-size:.85rem; }
.cat-passrate.ok { color:#1a8f4a; } .cat-passrate.bad { color:#c62828; } .cat-passrate.mixed { color:#b26a00; }
.cat-desc { color:#4a5060; font-size:.87rem; margin:.3rem 0 .4rem; }
.cat-hist { font-size:.76rem; color:#8a90a2; font-family:monospace; }
.cat-hist .h-ok { color:#1a8f4a; } .cat-hist .h-bad { color:#c62828; }
footer { margin-top:2.5rem; padding-top:1rem; border-top:1px solid #e8e5de; color:#8a90a2; font-size:.78rem; }
'''

def page(title, active, body, extra_head=''):
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title><style>{CSS}</style>{extra_head}</head>
<body>
<header>
  <div class="kicker">Hypershell / OpenShell exploration log</div>
  <h1>Agent exploration journal 🍋</h1>
  <div class="sub">Every test execution, logged as it happened — by Lemon, an OpenClaw agent acting as a real platform user on hyp2.</div>
</header>
<nav>
  <a href="index.html" class="{'active' if active=='index' else ''}">Overview</a>
  <a href="log.html" class="{'active' if active=='log' else ''}">Run log</a>
  <a href="catalog.html" class="{'active' if active=='catalog' else ''}">Test catalog</a>
</nav>
{body}
<footer>Generated by gen-site.py from structured test results · {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · maintained by the Lemon agent</footer>
</body></html>'''

def render_run(run, expanded=False):
    cls = '' if run['passed'] == run['total'] else 'fail-major'
    score_cls = 'ok' if run['passed'] == run['total'] else 'bad'
    tests = ''.join(
        f'<div class="t"><span class="tid">{e(t["id"])}</span>'
        f'<span class="mark {"ok" if t.get("ok") else "bad"}">{"✓" if t.get("ok") else "✗"}</span>'
        f'<span>{e(t["title"])}</span>'
        f'<span class="detail">{e(t.get("detail","")[:140])}</span></div>'
        for t in run['results'])
    return f'''<div class="run {cls}">
  <div class="run-head"><span class="run-name">{e(run['run'])}</span>
    <span class="run-date">{e(run['timestamp'])}</span>
    <span class="run-score {score_cls}">{run['passed']}/{run['total']} passed</span></div>
  <div class="run-battery">{e(run['battery'])}</div>
  <div class="tests">{tests}</div>
</div>'''

def gen_site(outdir, paths):
    runs = load_runs(paths)
    catalog = build_catalog(runs)
    total_tests = sum(r['total'] for r in runs)
    total_passed = sum(r['passed'] for r in runs)
    unique = len(catalog)
    always_pass = sum(1 for c in catalog.values() if all(h['ok'] for h in c['history']))
    os.makedirs(outdir, exist_ok=True)

    # index.html — overview
    latest = runs[-1] if runs else None
    idx_body = f'''
<div class="stats">
  <div class="stat"><b style="color:#1a8f4a">{total_passed}</b><span>tests passed</span></div>
  <div class="stat"><b style="color:#c62828">{total_tests-total_passed}</b><span>failed / findings</span></div>
  <div class="stat"><b>{len(runs)}</b><span>runs executed</span></div>
  <div class="stat"><b style="color:#1565c0">{unique}</b><span>unique tests</span></div>
</div>
<section><h2>Latest run</h2>{render_run(latest) if latest else '<p>No runs yet.</p>'}</section>
<section><h2>What this is</h2>
<p style="color:#4a5060;font-size:.92rem;max-width:44rem">A real-user simulation of the <b>openshift-online/hypershell</b> platform and its <b>OpenShell</b> gateways: an AI agent was given a gateway service account and told to behave like a platform user — connecting, creating sandboxes with different configurations, testing policies, lifecycle, templates, service exposure, concurrency and error paths. Every execution is logged below; the catalog deduplicates the unique test cases across runs.</p></section>
'''
    open(f'{outdir}/index.html','w').write(page('Exploration log — overview','index',idx_body))

    # log.html — all runs
    log_body = f'''<section><h2>Execution log</h2>
<p style="color:#4a5060;font-size:.9rem;margin-bottom:1rem">One entry per test execution, newest last. Expand details in the raw results files.</p>
{''.join(render_run(r) for r in runs)}</section>'''
    open(f'{outdir}/log.html','w').write(page('Exploration log — runs','log',log_body))

    # catalog.html — unique tests
    cats = []
    for c in sorted(catalog.values(), key=lambda x: x['id']):
        passes = sum(1 for h in c['history'] if h['ok'])
        rate = passes / len(c['history'])
        cls = 'ok' if rate == 1 else ('bad' if rate == 0 else 'mixed')
        hist = ' · '.join(f'<span class="{"h-ok" if h["ok"] else "h-bad"}">{e(h["run"])}:{"✓" if h["ok"] else "✗"}</span>' for h in c['history'])
        cats.append(f'''<div class="cat">
  <div class="cat-head"><span class="cat-id">{e(c['id'])}</span><span class="cat-title">{e(c['title'])}</span>
    <span class="cat-passrate {cls}">{passes}/{len(c['history'])} · {int(rate*100)}%</span></div>
  <div class="cat-desc">{e(c['desc'])}</div>
  <div class="cat-hist">{hist}</div>
</div>''')
    cat_body = f'''<section><h2>Test catalog — {unique} unique tests</h2>
<p style="color:#4a5060;font-size:.9rem;margin-bottom:1rem">Every distinct test case ever executed, with its all-time pass rate and per-run history.</p>
{''.join(cats)}</section>'''
    open(f'{outdir}/catalog.html','w').write(page('Exploration log — catalog','catalog',cat_body))

    print(f'site generated in {outdir}: {len(runs)} runs, {total_passed}/{total_tests} passed, {unique} unique tests')

if __name__ == '__main__':
    gen_site(sys.argv[1], sys.argv[2:])
