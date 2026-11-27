import test from 'node:test';
import assert from 'node:assert/strict';
import { matches, sourceURL } from '../web/model.mjs';

test('searches apply all filters and fold accents', () => {
  const row={search:'Étoile 2090183',topic:'Space',status:'OPPOSED'};
  assert.ok(matches(row,'etoile','OPPOSED','Space'));
  assert.ok(matches(row,'2090183','',''));
  assert.equal(matches(row,'','REGISTERED','Space'),false);
});
test('arbitrary application number opens the fixed official host', () => {
  assert.equal(sourceURL('0,170,580'),'https://ised-isde.canada.ca/cipo/trademark-search/170580?lang=eng');
  assert.equal(sourceURL('2660012'),'https://ised-isde.canada.ca/cipo/trademark-search/2660012?lang=eng');
  for (const invalid of ['','.','0','-1','foo.ca','1?lang=fra','12345678']) assert.equal(sourceURL(invalid),null);
});
