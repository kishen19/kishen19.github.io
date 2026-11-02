// Keep static news readable without JS; refresh its age grouping once per page load.
export function newsMonth(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', year: 'numeric', month: 'numeric' }).formatToParts(now);
  return { year: Number(parts.find(part => part.type === 'year').value), month: Number(parts.find(part => part.type === 'month').value) };
}

export function partitionNews(records, { maxVisible = 3, maxAgeMonths = 18 } = {}, today = newsMonth()) {
  const sorted = [...records].sort((a, b) => b.year - a.year || (b.month || 0) - (a.month || 0) || a.order - b.order);
  const recent = [], archive = [];
  for (const record of sorted) {
    const age = today.year * 12 + today.month - (record.year * 12 + (record.month || 0));
    const eligible = Boolean(record.month) && (maxAgeMonths === null || age < maxAgeMonths);
    (eligible && recent.length < maxVisible ? recent : archive).push(record);
  }
  return { recent, archive };
}

export function refreshNews(root, today = newsMonth()) {
  const recentList = root.querySelector('.news-recent');
  const history = root.querySelector('.news-history');
  const archiveList = root.querySelector('.news-archive ul');
  if (!recentList || !history || !archiveList) return;
  const records = [...root.querySelectorAll('li[data-news-year]')].map(node => ({
    node, year: Number(node.dataset.newsYear), month: Number(node.dataset.newsMonth) || null, order: Number(node.dataset.newsOrder),
  }));
  const groups = partitionNews(records, {
    maxVisible: Number(root.dataset.newsLimit),
    maxAgeMonths: root.dataset.newsMaxAgeMonths === '' ? null : Number(root.dataset.newsMaxAgeMonths),
  }, today);
  function replaceIfChanged(list, records) {
    const nodes = records.map(record => record.node);
    if (nodes.length !== list.children.length || nodes.some((node, index) => node !== list.children[index])) list.replaceChildren(...nodes);
  }
  replaceIfChanged(recentList, groups.recent);
  replaceIfChanged(archiveList, groups.archive);
  recentList.hidden = groups.recent.length === 0;
  history.hidden = groups.archive.length === 0;
}

if (typeof document !== 'undefined') {
  document.querySelectorAll('[data-news-limit]').forEach(root => refreshNews(root));
}
