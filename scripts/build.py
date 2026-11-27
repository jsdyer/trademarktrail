#!/usr/bin/env python3
"""Build the catalogue, paired comparison and permanent numbered trademark histories."""
from datetime import date
from html import escape
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET
from refresh import ATTRIBUTION, TERMS, ROOT, load_roster, source_url
from search_metadata import add_search_metadata

BASE = 'https://coolcode.ca/trademarktrail/'
FEATURE = '2090183'
MILESTONES = {'Filed','Advertised','Registered','Renewed','Opposed','Abandoned','Withdrawn',
              'Expunged','Expunged - Failure to Renew','Proposed Opposition','Change of Title Registered'}


def link(url, label, cls=''):
    css = f' class="{cls}"' if cls else ''
    return f'<a{css} href="{escape(url,quote=True)}">{escape(label)}</a>'


def sub(text):
    return escape(str(text),quote=True)


def display_date(day):
    d=date.fromisoformat(day)
    return f'{d.day} {d:%b %Y}'


def write(path, content):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding='utf-8')


def page(route, title, desc, body, tool):
    prefix='../'*route.count('/') if route else './'
    canonical=BASE+route
    tags=(f'<link rel="canonical" href="{canonical}"><meta property="og:url" content="{canonical}">'
          f'<meta property="og:title" content="{sub(title)}"><meta property="og:description" content="{sub(desc)}">'
          f'<meta property="og:type" content="website">') if route else ''
    content=f'''<!doctype html>
<html lang="en-CA"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{sub(title)} · CoolCode</title><meta name="description" content="{sub(desc)}">{tags}
<link rel="stylesheet" href="{prefix}style.css"><script type="module" src="{prefix}app.mjs"></script>
<script defer src="/assets/tool-metrics.js" referrerpolicy="no-referrer"></script></head>
<body data-tool-id="trademarktrail"><a class="skip" href="#main">Skip to content</a>
<header><div class="wrap mast"><a class="brand" href="{prefix}">Trademark Trail</a><nav aria-label="Site">
<a href="{prefix}records/">Register records</a><a href="https://coolcode.ca/">CoolCode.ca</a></nav></div></header>
<main id="main" class="wrap">{body}</main><footer><div class="wrap">
<p>{link(TERMS,ATTRIBUTION)}</p><p>{link('https://ised-isde.canada.ca/cipo/trademark-search/srch?lang=eng','Search the full Canadian Trademarks Database')} · {link('https://github.com/jsdyer/trademarktrail','Source and collection notes')} · {link('https://coolcode.ca/report/?tool=trademarktrail','Report a correction')}</p></div></footer></body></html>'''
    return content if route else add_search_metadata(content,tool, category='ReferenceApplication')


def first_action(record, label):
    return next((a['date'] for a in record['actions'] if a['label']==label),None)


def fmt(day):
    return display_date(day) if day else 'Unlisted'


def number_label(record):
    return record['name']+' · '+record['number']


def row_link(r,prefix):
    return link(prefix+r['number']+'/',r['name'])


def find_form(topics, statuses):
    def options(items):
        return ''.join(f'<option value="{sub(i)}">{sub(i)}</option>' for i in items)
    return ('<form class="filters" data-filter hidden><label>Find a mark or number<input name="q" type="search" placeholder="Try CANADARM or a filing number"></label>'
            '<label>Topic<select name="topic"><option value="">All topics</option>'+options(topics)+'</select></label>'
            '<label>CIPO status<select name="status"><option value="">All statuses</option>'+options(statuses)+'</select></label>'
            '<button type="reset">Clear</button></form><p data-matches aria-live="polite"></p>')


def catalogue(records,prefix):
    cards=[]
    for r in sorted(records,key=lambda r:(r['name'].casefold(),r['number'])):
        search=' '.join(map(str,[r['name'],r['number'],r.get('registration_number',''),r['topic'],r['scope']]))
        attrs=' '.join(f'data-{k}="{sub(v)}"' for k,v in [('search',search),('status',r['status']),('topic',r['topic'])])
        cards.append(f'<li class="card" data-mark {attrs}><span class="mono">No. {r["number"]} · {sub(r["topic"])}</span>'
                     f'<h3>{row_link(r,prefix)}</h3><p>{sub(r["scope"])}</p>'
                     f'<p class="cardend">{sub(r["status"])} · filed {fmt(r.get("filed"))}</p></li>')
    return find_form(sorted({r['topic'] for r in records}),sorted({r['status'] for r in records}))+ '<ul class="cards">'+''.join(cards)+'</ul>'


def summary(r):
    filed=r.get('filed')
    registered=r.get('registered')
    if filed and registered:
        span=(date.fromisoformat(registered)-date.fromisoformat(filed)).days
        if span==0:
            return 'CIPO lists filing and registration on the same day, '+display_date(filed)+'.'
        return f'{span:,} days from filing to registration ({display_date(filed)} to {display_date(registered)}).'
    if filed:
        return f'CIPO lists the filing on {display_date(filed)}. Its action history records {len(r["actions"])} dated entries.'
    return f'CIPO publishes {len(r["actions"])} dated actions for this application.'


def comparison(records):
    by_id={r['number']:r for r in records}
    a=by_id.get(FEATURE,records[0])
    b=by_id.get(a.get('compare_with')) or next((r for r in records if r is not a),a)
    def ctrl(name,label,selected):
        options=''.join(f'<option value="{r["number"]}"'+(' selected' if r['number']==selected else '')+f'>{sub(number_label(r))}</option>' for r in records)
        return f'<label>{label}<select name="{name}">{options}</select></label>'
    return ('<section id="compare"><h2>Compare two applications</h2><p>Choose two filings to compare their status and key dates.</p>'
            '<form data-compare hidden>'+ctrl('a','First mark',a['number'])+ctrl('b','Second mark',b['number'])+'</form>'
            '<div class="scroll" tabindex="0" aria-label="Trademark comparison"><table><caption>Dates and status from the register</caption>'
            '<thead><tr><th>Record</th><th data-field="name">'+link('records/'+a['number']+'/',number_label(a))+'</th>'
            '<th data-field="name">'+link('records/'+b['number']+'/',number_label(b))+'</th></tr></thead><tbody>'
            +''.join(f'<tr><th scope="row">{label}</th>'+''.join(f'<td data-field="{field}">{sub(r.get(field) or "Unlisted")}</td>' for r in (a,b))+'</tr>'
                     for field,label in [('status','CIPO status'),('filed','Filed'),('advertised','First advertised'),('registered','Registered'),('registration_number','Registration number')])
            +'</tbody></table></div></section>')


def overview(edition,records):
    feat=next((r for r in records if r['number']==FEATURE),records[0])
    return ('<div class="hero"><div><h1>Follow a Canadian trademark</h1>'
            '<p class="lead">See when a mark was filed, advertised or registered. Pick a record for its timeline or compare two applications side by side.</p>'
            '<p class="actions">'+link('#records','Find a trademark','primary')+' '+link('#compare','Compare marks','secondary')+'</p></div>'
            '<aside><p class="mono">Application '+feat['number']+'</p><h2>'+sub(feat['name'])+'</h2><p>'+sub(summary(feat))+'</p>'
            +link('records/'+feat['number']+'/','Read the timeline →')+'</aside></div>'
            '<section id="records"><h2>Explore the register records</h2><p>'+str(len(records))+' selected applications · CIPO checked '+display_date(edition['checked_at'])+'.</p>'
            +catalogue(records,'records/')+'</section>'+comparison(records)+
            '<section><h2>Have another application number?</h2><form data-lookup hidden><label>CIPO application number<input name="number" placeholder="2090183" inputmode="numeric" required></label>'
            '<button>Open official record</button></form><p class="small">A lookup opens CIPO. Searches and comparisons within this collection stay in your browser.</p>'
            +link('https://ised-isde.canada.ca/cipo/trademark-search/srch?lang=eng','Search all trademarks on CIPO')+'</section>')


def history(r,records,checked):
    name,number=r['name'],r['number']
    title=f'{name} Canadian trademark history · {number}'
    desc=f'Canadian application {number} for {name}. {summary(r)} CIPO status observed {checked}: {r["status"]}.'
    lead=(f'<p>{link("../","‹ All trademark records")}</p><h1>{sub(name)}</h1>'
          f'<p class="lead">{sub(r["scope"])}</p><p class="mono">Application {number} · {sub(r["topic"])}</p>'
          f'<div class="panel"><p class="state">{sub(r["status"])}</p><p>Status observed {display_date(checked)}. {sub(summary(r))}</p>'
          f'<p>{link(r["source"],"Open the official CIPO record →")}</p></div>')
    if r.get('registration_number'):
        lead+=f'<p>Registration {sub(r["registration_number"])}.</p>'
    if r['classes']:
        lead+=' <p>Nice classes published in the register: '+', '.join(map(str,r['classes']))+'.</p>'
    body=lead+'<section><h2>Key dates</h2><ol class="timeline">'
    important=[a for a in r['actions'] if a['label'] in MILESTONES]
    for a in important or r['actions']:
        body+=f'<li><time datetime="{a["date"]}">{display_date(a["date"])}</time><strong>{sub(a["label"])}</strong></li>'
    body+='</ol>'
    if j:=r.get('journal'):
        body+='<p>Published '+display_date(j['published'])+' in the '+link(j['url'],j['label'])+' (PDF).</p>'
    body+=f'<details><summary>All {len(r["actions"])} dated register actions</summary><ol class="timeline">'
    for a in r['actions']:
        body+=f'<li><time datetime="{a["date"]}">{display_date(a["date"])}</time>{sub(a["label"])}</li>'
    body+='</ol></details></section><section><h2>Explore related records</h2>'
    by_id={x['number']:x for x in records}
    if other:=by_id.get(r.get('compare_with')):
        body+='<p>'+link('../'+other['number']+'/',number_label(other))+' · '+link('../../?a='+number+'&b='+other['number']+'#compare','Compare these two applications')+'</p>'
    else:
        body+='<p>'+link('../../?a='+number+'#compare','Compare this application with another mark')+'</p>'
    if number==FEATURE:
        body+='<p>Follow the dates on the website and licensing notices in '+link('https://coolcode.ca/domain-biography/records/truenorth-bet/','Domain Biography')+' and '+link('https://coolcode.ca/gamblingregulatorwatch/records/true-north-88b4e0aad9/','Gambling Regulator Watch')+'. The mark and gaming authorization have separate records.</p>'
    if r['topic']=='Food and drink':
        body+='<p>'+link('https://coolcode.ca/maplelabel/','Check Canadian origin claims for named products in Maple Label')+'. Product origin is a separate question from trademark registration.</p>'
    if r['topic']=='Space and robotics':
        body+='<p>'+link('https://coolcode.ca/patentattic/','Explore Canadian invention publications in Patent Attic')+'.</p>'
    return title,desc,body+'</section>'


def build(root=ROOT):
    tool=json.loads((root/'tool.json').read_text())
    edition=json.loads((root/'data/register.json').read_text())
    roster=load_roster(root/'data/roster.json')
    records_map={r['number']:r for r in edition['records']}
    if set(records_map)!={r['number'] for r in roster} or len(records_map)!=len(edition['records']):
        raise ValueError("Saved source edition must cover the complete current roster")
    checked=date.fromisoformat(edition['checked_at']).isoformat()
    records=[]
    for meta in roster:
        r=records_map[meta['number']] | meta
        if r.get('source')!=source_url(r['number']) or not r['actions']:
            raise ValueError("Expected a source-linked action history")
        r['advertised']=first_action(r,'Advertised')
        records.append(r)
    with TemporaryDirectory(dir=root) as tmp:
        stage=Path(tmp)/'site'
        shutil.copytree(root/'web',stage)
        write(stage/'index.html',page('','Canadian trademark search and registration timelines',tool['description'],overview(edition,records),tool))
        routes=['records/']
        directory=('''<h1>Canadian trademark histories</h1><p class="lead">Choose an application number to read its dates and official sources. Two applications can share a name and have different outcomes.</p>'''
                   +'<p>'+str(len(records))+' records · checked '+display_date(checked)+'</p>'+catalogue(records,'./'))
        write(stage/'records/index.html',page('records/','Canadian trademark records by name and application number','Browse selected Canadian trademark applications, dated actions and observed registration status.',directory,tool))
        for rec in records:
            route='records/'+rec['number']+'/'
            write(stage/route/'index.html',page(route,*history(rec,records,checked),tool))
            routes.append(route)
        compact=[{k:r.get(k) for k in ('number','name','status','filed','advertised','registered','registration_number')} for r in records]
        write(stage/'data/compare.json',json.dumps({'checked_at':checked,'attribution':ATTRIBUTION,'licence':TERMS,'records':compact},ensure_ascii=False)+'\n')
        write(stage/'data/status.json',json.dumps({'checked_at':checked,'record_count':len(records),'actions':sum(len(r['actions']) for r in records)},indent=2)+'\n')
        sitemap=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
        for route in sorted(routes):
            ET.SubElement(ET.SubElement(sitemap,'url'),'loc').text=BASE+route
        (stage/'sitemap.xml').write_bytes(ET.tostring(sitemap,encoding='utf-8',xml_declaration=True))
        write(stage/'.nojekyll','')
        if (root/'dist').exists():
            shutil.rmtree(root/'dist')
        stage.rename(root/'dist')
    print(f'Built {len(records)} record timelines and {len(routes)} sitemap entries.')


if __name__=='__main__':
    build()
