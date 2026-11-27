import { matches, sourceURL } from './model.mjs';

const $ = selector => document.querySelector(selector);
const url = new URL(location.href);
const filters = $('[data-filter]');
if (filters) {
  const cards = [...document.querySelectorAll('[data-mark]')];
  const fields = filters.elements;
  function filter() {
    let count = 0;
    for (const card of cards) {
      card.hidden = !matches(card.dataset,fields.q.value,fields.status.value,fields.topic.value);
      if (!card.hidden) count++;
    }
    $('[data-matches]').textContent = count ? count + (count === 1 ? ' matching application' : ' matching applications') : 'No matching applications. Clear the filters to see all records.';
    for (const key of ['q','topic','status']) {
      if (fields[key].value) url.searchParams.set(key,fields[key].value);
      else url.searchParams.delete(key);
    }
    history.replaceState(null,'',url);
  }
  for (const key of ['q','topic','status']) fields[key].value = url.searchParams.get(key) || '';
  filters.hidden = false;
  filters.addEventListener('input',filter);
  filters.addEventListener('submit',e=>{e.preventDefault();filter();});
  filters.addEventListener('reset',()=>setTimeout(filter,0));
  filter();
}

const form = $('[data-compare]');
if (form) {
  const response = await fetch(new URL('./data/compare.json',import.meta.url)).catch(()=>null);
  if (response?.ok) {
    const { records: rows } = await response.json();
    const records = new Map(rows.map(r=>[r.number,r]));
    const fields = form.elements;
    for (const k of ['a','b']) if (records.has(url.searchParams.get(k))) fields[k].value=url.searchParams.get(k);
    if (fields.a.value===fields.b.value && records.size>1) fields.b.value=rows.find(r=>r.number!==fields.a.value).number;
    function compare(update) {
      const selections = [fields.a.value,fields.b.value];
      for (const [index, num] of selections.entries()) {
        const r=records.get(num);
        for (const tr of document.querySelectorAll('#compare tr')) {
          const cell=tr.querySelectorAll('[data-field]')[index];
          const key=cell.dataset.field;
          if (key==='name') {
            const a=document.createElement('a');
            a.href='records/'+r.number+'/';
            a.textContent=r.name+' · '+r.number;
            cell.replaceChildren(a);
          } else cell.textContent=r[key] || 'Unlisted';
        }
      }
      if (update) {
        url.searchParams.set('a',fields.a.value);url.searchParams.set('b',fields.b.value);
        url.hash='compare';history.replaceState(null,'',url);
      }
    }
    form.hidden=false;
    form.addEventListener('change',event=>{
      if (fields.a.value===fields.b.value && records.size>1) {
        const other=event.target===fields.a ? fields.b : fields.a;
        other.value=rows.find(r=>r.number!==event.target.value).number;
      }
      compare(true);
    });
    compare(false);
  }
}
const official=$('[data-lookup]');
if (official) {
  official.hidden=false;
  official.addEventListener('submit',e=>{
    e.preventDefault();
    const field=official.elements.number;
    const href=sourceURL(field.value);
    if (href) location.assign(href);
    else { field.setCustomValidity('Enter a CIPO application number of up to seven digits.');field.reportValidity(); }
  });
  official.elements.number.addEventListener('input',()=>official.elements.number.setCustomValidity(''));
}
