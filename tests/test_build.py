from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import sys
import unittest
from xml.etree import ElementTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build import ROOT, build
from refresh import ATTRIBUTION, parse_record, refresh

SAMPLE = b"""<h1 id="wb-cont">FRESH MARK &mdash; 9990001</h1><div id="details-bio-info">
<div><div><h3>Application number</h3></div><div>9990001</div></div>
<div><div><h3>CIPO Status</h3></div><div>OPPOSED</div></div>
<div><div><h3>Agent</h3></div><div>Private Street</div></div></div>
<div id="details-act-hist"><table><tbody><tr><td>Filed</td><td>2022-01-01</td><td>2030-01-01</td><td>Private Street</td></tr></tbody></table></div>"""

class TestRecords(unittest.TestCase):
    def test_parse_exact_identity_and_action_column(self):
        r=parse_record(SAMPLE,'9990001')
        self.assertEqual(r['actions'],[dict(date='2022-01-01',label='Filed')])
        self.assertEqual(r['filed'], '2022-01-01')
        self.assertNotIn('Private Street',json.dumps(r))
        with self.assertRaises(ValueError):
            parse_record(SAMPLE,'9990002')

    def test_validation_retains_previous_complete_edition(self):
        with TemporaryDirectory() as folder:
            p=Path(folder)/'register.json'
            p.write_text('unchanged')
            with self.assertRaises(ValueError):
                refresh([dict(number='9990001'),dict(number='9990002')],p,lambda _: SAMPLE)
            self.assertEqual(p.read_text(),'unchanged')

    def test_new_number_builds_its_own_canonical_page_and_sitemap_entry(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            for name in ('data','web'):
                shutil.copytree(ROOT/name,root/name)
            shutil.copy(ROOT/'tool.json',root)
            roster=root/'data/roster.json'
            rows=json.loads(roster.read_text())+[dict(number='9990001',topic='Test',scope='New test mark.')]
            roster.write_text(json.dumps(rows))
            reg=root/'data/register.json'
            edition=json.loads(reg.read_text());edition['records'].append(parse_record(SAMPLE,'9990001'));reg.write_text(json.dumps(edition))
            build(root)
            xml=ElementTree.parse(root/'dist/sitemap.xml')
            urls=[e.text for e in xml.findall('.//{*}loc')]
            self.assertEqual(len(urls),len(rows)+1)
            url='https://coolcode.ca/trademarktrail/records/9990001/'
            self.assertIn(url,urls)
            text=(root/'dist/records/9990001/index.html').read_text()
            self.assertIn('rel="canonical" href="'+url+'"',text)
            self.assertIn(ATTRIBUTION,text)
            self.assertIn('New test mark.',text)
