export function fold(value) {
  return (value || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
}
export function matches(row, query, status, topic) {
  return fold(row.search).includes(fold(query)) && (!status || row.status === status) && (!topic || row.topic === topic);
}
export function sourceURL(raw) {
  const number = raw.trim().replaceAll(',', '');
  if (!/^\d{1,7}$/.test(number) || Number(number) < 1) return null;
  return 'https://ised-isde.canada.ca/cipo/trademark-search/' + Number(number) + '?lang=eng';
}
