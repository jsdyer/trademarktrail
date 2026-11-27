# Trademark Trail

[Open Trademark Trail](https://coolcode.ca/trademarktrail/) to follow a Canadian trademark through the action history published by the Canadian Intellectual Property Office (CIPO). Search the reviewed collection by mark, application number, registration number or subject, or open an arbitrary application number on CIPO.

<!-- coolcode:guide -->
Start with TrueNorth.bet to see its filing, advertisement and registration, then open the original Trademarks Journal. Compare the two CANADARM applications to see how the same name can have separate numbers, histories and outcomes. Filing and registration dates come from the register. Each profile dates the status observation.
<!-- /coolcode:guide -->

## Read the source record

The [numbered record directory](https://coolcode.ca/trademarktrail/records/) and every timeline work without JavaScript. JavaScript enables local search, filters, direct CIPO lookup and shareable two-application comparisons. The launch collection includes TrueNorth, CANADARM, BLACKBERRY, BLUENOSE, SUSSEX, BEAVERTAILS and COFFEE CRISP records. Some names appear more than once with different application numbers. This is a curated collection, and the page links to the [national register search](https://ised-isde.canada.ca/cipo/trademark-search/srch?lang=eng).

The page distinguishes the observed CIPO status from dated actions. Class numbers appear where CIPO explicitly lists them alongside goods or services. Filing and registration dates use the biographical fields or, when absent, their first matching entry in the dated action history. Unlisted means neither provided the date. The chronology uses the action date column. Due dates, agents, personal addresses and artwork are excluded. A few related records link to verified journal pages, domain history and separately issued regulatory decisions. A filing or registration alone cannot establish who currently operates a website.

Searches run in the browser, with filters and selected application numbers reflected in the URL for sharing. Using the direct number lookup opens CIPO and sends that number to its website. The site uses the shared CoolCode tool counter and [correction form](https://coolcode.ca/report/?tool=trademarktrail).

## Expand or customize

1. Add a seven-digit CIPO application number, a topic and a brief editorial scope note to `data/roster.json`. Preserve leading zeroes. An optional `compare_with` names a different application already in the collection. For a verified issue, add a journal URL, publication date and page citation. Check any linked history or jurisdiction independently.
2. From a Python 3.12 environment, install `python3 -m pip install -r scripts/collector-requirements.txt` and run `python3 scripts/refresh.py`. It requests only the named public pages, validates the returned numbers, labels and action histories, and replaces the single published edition after the collection succeeds. There is no archive of superseded editions on the site.
3. Run `node --test tests/*.test.mjs`, `python3 -m unittest discover -s tests -v` and `python3 scripts/build.py`. The default build is offline and uses the saved edition. To run the browser QA, install `tests/browser-requirements.txt` and Playwright Chromium, then run `python3 tests/browser_smoke.py`. For a locally installed Chromium, set `CHROMIUM_PATH`. Open `dist/` using a local HTTP server.
4. Commit changed source, roster, edition and documentation. The main Pages workflow tests and deploys. Each profile has a permanent route using its application number. The result directory and profiles appear in the [native sitemap](https://coolcode.ca/trademarktrail/sitemap.xml).

## Refresh and corrections

The `refresh.yml` workflow checks CIPO Fridays at 10:41 UTC and supports manual runs. A failed source check retains the previous published check date and surfaces the workflow failure. `data/status.json` in the built site exposes the last complete check and number of records. CIPO may revise older action history. On notice of a correction, refresh the affected record promptly or withdraw its page until corrected. In a removal, update the roster, remove the old record from the edition, rebuild the directory and sitemap, and notify any downstream users. The hub's independent watchdog monitors the collector.

## Attribution

Contains data licensed by Her Majesty the Queen in right of Canada, as represented by the Minister of Industry, the minister responsible for the administration of the Canadian Intellectual Property Office. [Terms and conditions for use of the Canadian Intellectual Property Data](https://ised-isde.canada.ca/site/canadian-intellectual-property-office/en/terms-and-conditions-use-canadian-intellectual-property-data). Anyone reproducing the IP data must keep that attribution and cease using earlier records when CIPO publishes a modification notice. The separate editorial topic and scope notes help readers navigate the records.
