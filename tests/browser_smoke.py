"""Verify navigation, comparison, saved link state and the native records at phone widths."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]

def run():
    records = {r['number']: r for r in json.loads((ROOT / 'data/register.json').read_text())['records']}
    arm_records = [r for r in records.values() if 'CANADARM' in r['name']]
    selected_status = records['2060180']['status']
    with TemporaryDirectory() as tmp:
        (Path(tmp)/'trademarktrail').symlink_to(ROOT/'dist',target_is_directory=True)
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=tmp))
        thread=Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}/trademarktrail/'
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH'),args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1280,'height':900})
                page.goto(base)
                expect(page.get_by_role('heading',name='Follow a Canadian trademark')).to_be_visible()
                page.get_by_label('Find a mark or number').fill('CANADARM')
                expect(page.locator('[data-mark]:visible')).to_have_count(len(arm_records))
                page.get_by_label('CIPO status').select_option(selected_status)
                expect(page.locator('[data-mark]:visible')).to_have_count(sum(r['status'] == selected_status for r in arm_records))
                page.reload()
                expect(page.locator('[data-mark]:visible')).to_have_count(sum(r['status'] == selected_status for r in arm_records))
                page.get_by_label('First mark').select_option('0607708')
                page.get_by_label('Second mark').select_option('0871883')
                expect(page.locator('[data-field="status"]').nth(0)).to_have_text(records['0607708']['status'])
                expect(page.locator('[data-field="status"]').nth(1)).to_have_text(records['0871883']['status'])
                page.reload()
                expect(page.get_by_label('First mark')).to_have_value('0607708')
                page.goto(base)
                shots=ROOT/'browser-checks';shots.mkdir(exist_ok=True)
                page.screenshot(path=str(shots/'desktop.png'))
                page.set_viewport_size({'width':390,'height':844})
                for width in [390,320]:
                    page.set_viewport_size({'width':width,'height':844})
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    assert page.get_by_role('link',name='Find a trademark').bounding_box()['y']<650
                page.screenshot(path=str(shots/'mobile.png'))
                page.get_by_role('link',name='Read the timeline').click()
                expect(page.locator('h1')).to_have_text('TrueNorth.bet')
                expect(page.get_by_text('Registration TMA1171288.')).to_be_visible()
                page.locator('details summary').click()
                context=browser.new_context(java_script_enabled=False,viewport={'width':320,'height':720})
                native=context.new_page()
                native.goto(base+'records/')
                native.get_by_role('link',name='BLUENOSE',exact=True).click()
                expect(native.locator('h1')).to_have_text('BLUENOSE')
                expect(native.locator('.state')).to_have_text(records['0170580']['status'])
                assert native.evaluate('document.documentElement.scrollWidth <= innerWidth')
                browser.close()
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
if __name__=='__main__':
    run()
