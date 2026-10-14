const input = document.getElementById('searchInput');
const results = document.getElementById('searchResults');
const status = document.getElementById('searchStatus');
let engine;
function search() {
  const query = input.value.trim();
  results.replaceChildren();
  if (!query) { status.textContent = '输入关键词，搜索文章和公开文档。'; return; }
  const matches = engine.search(query, {limit: 30});
  status.textContent = matches.length ? `找到 ${matches.length} 条相关结果` : '没有找到相关内容，请尝试其他关键词。';
  for (const {item} of matches) {
    const li = document.createElement('li'); li.className = 'search-result';
    const link = document.createElement('a'); link.href = item.permalink; link.textContent = item.title;
    const summary = document.createElement('p'); summary.textContent = item.summary;
    li.append(link, summary); results.append(li);
  }
}
fetch('../index.json').then(response => { if (!response.ok) throw new Error(); return response.json(); }).then(data => {
  engine = new Fuse(data, {threshold: 0.3, ignoreLocation: true, keys: [{name: 'title', weight: 2}, {name: 'content', weight: 1}]});
  input.disabled = false;
  input.value = (new URLSearchParams(location.search).get('q') || '').slice(0, 80);
  search();
  input.addEventListener('input', event => { if (!event.isComposing) search(); });
  input.addEventListener('compositionend', search);
}).catch(() => { status.textContent = '搜索索引暂时加载失败，请刷新页面重试，或通过导航浏览博客。'; });
