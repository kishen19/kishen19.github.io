import assert from 'node:assert/strict';
import { newsMonth, partitionNews, refreshNews } from '../assets/js/news.mjs';

const record = (id, year, month, order = 0) => ({ id, year, month, order });
const ids = items => items.map(item => item.id);
const today = { year: 2026, month: 11 };
const records = [record('old', 2024, 1), record('one', 2026, 9), record('new', 2026, 11), record('two', 2026, 10), record('overflow', 2026, 8)];
assert.deepEqual(ids(partitionNews(records, {}, today).recent), ['new', 'two', 'one']);
assert.deepEqual(ids(partitionNews(records, {}, today).archive), ['overflow', 'old']);
const boundary = [record('jan', 2027, 1), record('dec', 2026, 12), record('nov', 2026, 11), record('oct', 2026, 10)];
assert.deepEqual(ids(partitionNews(boundary, { maxAgeMonths: 3 }, { year: 2027, month: 1 }).archive), ['oct']);
assert.deepEqual(ids(partitionNews([record('future', 2027, 2)], {}, today).recent), ['future']);
assert.equal(partitionNews([record('old', 2020, 1)], {}, today).recent.length, 0);
assert.equal(partitionNews([record('old', 2020, 1)], { maxAgeMonths: null }, today).recent.length, 1);
assert.equal(partitionNews([record('unknown-month', 2026, null)], { maxAgeMonths: null }, today).recent.length, 0);
assert.deepEqual(ids(partitionNews([record('later-tie', 2026, 11, 2), record('first-tie', 2026, 11, 1)], {}, today).recent), ['first-tie', 'later-tie']);
assert.deepEqual(newsMonth(new Date('2026-11-01T03:30:00Z')), { year: 2026, month: 10 });
assert.deepEqual(newsMonth(new Date('2026-11-01T05:30:00Z')), { year: 2026, month: 11 });

// A tiny DOM double: stale generated news must move into history without fetching JSON.
const node = (year, month, order) => ({ dataset: { newsYear: String(year), newsMonth: String(month), newsOrder: String(order) } });
const first = node(2026, 10, 0), second = node(2026, 9, 1);
const list = children => ({ children, hidden: false, replaceChildren(...nodes) { this.children = nodes; } });
const recentList = list([first, second]), archiveList = list([]);
const history = { hidden: true, open: true };
const root = {
  dataset: { newsLimit: '3', newsMaxAgeMonths: '3' },
  querySelector: selector => ({ '.news-recent': recentList, '.news-history': history, '.news-archive ul': archiveList })[selector],
  querySelectorAll: () => [...recentList.children, ...archiveList.children],
};
refreshNews(root, { year: 2027, month: 1 });
assert.equal(recentList.hidden, true);
assert.deepEqual(archiveList.children, [first, second]);
assert.equal(history.hidden, false);
assert.equal(history.open, true, 'Refreshing must preserve the disclosure state');
refreshNews(root, { year: 2026, month: 11 });
assert.deepEqual(recentList.children, [first, second]);
assert.equal(history.hidden, true);
console.log('News sorting, calendar cutoff, timezone, static-data refresh, and disclosure-state checks passed.');
