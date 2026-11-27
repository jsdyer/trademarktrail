#!/usr/bin/env python3
"""Check only the reviewed application numbers and replace the saved register edition."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REGISTER = "https://ised-isde.canada.ca/cipo/trademark-search/"
TERMS = "https://ised-isde.canada.ca/site/canadian-intellectual-property-office/en/terms-and-conditions-use-canadian-intellectual-property-data"
ATTRIBUTION = ("Contains data licensed by Her Majesty the Queen in right of Canada, as represented by the "
               "Minister of Industry, the minister responsible for the administration of the Canadian Intellectual Property Office.")


def norm(text):
    return " ".join(text.split())


def date_day(text):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        raise ValueError(f"Invalid action date {text!r}")
    datetime.strptime(text, "%Y-%m-%d")
    return text


def source_url(number):
    return REGISTER + str(int(number)) + "?lang=eng"


def load_roster(path):
    roster = json.loads(path.read_text())
    ids = {r['number'] for r in roster}
    if not roster or len(ids) != len(roster):
        raise ValueError("Expected a nonempty list of distinct CIPO records")
    for r in roster:
        if not re.fullmatch(r"\d{7}", r["number"]) or not r['topic'].strip() or not r['scope'].strip():
            raise ValueError("Expected an application number, topic and short scope note")
        if 'compare_with' in r and (r['compare_with'] not in ids or r['compare_with'] == r['number']):
            raise ValueError("Compare records must be distinct members of this roster")
        if 'journal' in r:
            j = r['journal']
            if not j['url'].startswith('https://publications.gc.ca/') or not j['label']:
                raise ValueError("Expected an official journal citation")
            date_day(j['published'])
    return roster


def parse_record(raw, number):
    from lxml import html
    doc = html.fromstring(raw, parser=html.HTMLParser(encoding="utf-8"))
    heading = norm(doc.xpath("string(//h1[@id='wb-cont'])"))
    name, sep, source_number = heading.rpartition(" — ")
    if not sep or not name or source_number != number:
        raise ValueError(f"Register page does not identify application {number}")
    labels = {}
    for heading in doc.xpath("//*[@id='details-bio-info']//h3"):
        key = norm(heading.text_content())
        next_cols = heading.xpath("../following-sibling::div[1]")
        if next_cols and key in {'Application number','Registration number','Filed','Registered','Type(s)','Category','CIPO Status'}:
            labels[key] = norm(next_cols[0].text_content())
    if labels.get("Application number") != number or not labels.get("CIPO Status"):
        raise ValueError(f"Missing identity or status for {number}")
    actions = []
    for row in doc.xpath("//*[@id='details-act-hist']//tbody/tr"):
        cols = row.xpath("./td")
        if len(cols) != 4:
            raise ValueError(f"Unexpected register action columns for {number}")
        label = norm(cols[0].text_content())
        day = date_day(norm(cols[1].text_content()))
        if not label or len(label) > 180:
            raise ValueError(f"Expected an action label in {number}")
        actions.append({"date":day,"label":label})
    if not actions:
        raise ValueError(f"No source actions returned for {number}")
    classes = sorted({int(norm(v.text_content())) for v in doc.xpath("//h3[contains(.,'Nice class')]/following-sibling::div[1]//dt")
                      if norm(v.text_content()).isdecimal() and 1 <= int(norm(v.text_content())) <= 45})
    result = dict(number=number, name=name, status=labels['CIPO Status'], classes=classes,
                  actions=sorted(actions, key=lambda a:a['date']), source=source_url(number))
    for key, output in (('Filed', 'filed'), ('Registered', 'registered')):
        # Some older records list these dates only in the dated action history.
        observed = labels.get(key) or next(
            (action['date'] for action in result['actions'] if action['label'] == key), None
        )
        if observed:
            result[output] = date_day(observed)
    if labels.get('Registration number'):
        result['registration_number'] = labels['Registration number']
    return result


def fetch(number):
    req = Request(source_url(number), headers={"User-Agent":"CoolCode Trademark Trail (+https://coolcode.ca/trademarktrail/)"})
    with urlopen(req, timeout=45) as response:
        raw = response.read(3_000_001)
    if not 0 < len(raw) <= 3_000_000:
        raise ValueError(f"Unexpected CIPO response size for {number}")
    return raw


def refresh(roster, dest, read=fetch):
    records = [parse_record(read(item['number']), item['number']) for item in roster]
    edition = dict(checked_at=datetime.now(timezone.utc).date().isoformat(), attribution=ATTRIBUTION, licence=TERMS, records=records)
    with NamedTemporaryFile('w', dir=dest.parent, delete=False, encoding='utf-8') as temp:
        json.dump(edition,temp,ensure_ascii=False,indent=2)
        temp.write('\n')
    Path(temp.name).replace(dest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-directory', type=Path, help='Replay official HTML just downloaded on this check, named by application number without leading zeroes')
    args = parser.parse_args()
    roster = load_roster(ROOT/'data/roster.json')
    read = (lambda n: (args.source_directory/(str(int(n))+'.html')).read_bytes()) if args.source_directory else fetch
    refresh(roster,ROOT/'data/register.json',read)
    print(f"Validated {len(roster)} official register pages")
