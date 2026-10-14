(() => {
  const section = document.querySelector('#comments[data-post]');
  const form = document.getElementById('comment-form');
  if (!section || !form) return;
  const status = document.getElementById('comment-status');
  const button = form.querySelector('button');
  const list = document.getElementById('comment-list');
  const post = section.dataset.post;
  fetch(`/api/comments?post=${encodeURIComponent(post)}`, {cache: 'no-store'})
    .then(response => { if (!response.ok) throw new Error(); return response.json(); })
    .then(data => {
      if (!Array.isArray(data.comments)) throw new Error();
      if (!data.comments.length) list.textContent = '还没有公开留言，欢迎留下第一条。';
      for (const comment of data.comments) {
        const item = document.createElement('article');
        item.className = 'reader-comment';
        const heading = document.createElement('strong');
        heading.textContent = comment.name;
        const date = document.createElement('time');
        date.dateTime = new Date(comment.created * 1000).toISOString();
        date.textContent = new Date(comment.created * 1000).toLocaleDateString('zh-CN');
        const body = document.createElement('p');
        body.textContent = comment.body;
        item.append(heading, date, body); list.append(item);
      }
      status.textContent = '昵称和留言在审核通过后公开展示。';
      button.disabled = false;
    }).catch(() => { status.textContent = '留言服务暂时无法连接，请稍后刷新再试。内容不会在未提交成功时清空。'; });
  form.addEventListener('submit', async event => {
    event.preventDefault(); button.disabled = true;
    status.textContent = '正在提交…';
    try {
      const data = new FormData(form);
      const response = await fetch('/api/comments', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({post, name: data.get('name'), body: data.get('body'), website: data.get('website')})
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || '暂时无法提交，请稍后重试。');
      status.textContent = result.message; form.reset();
    } catch (error) { status.textContent = error.message || '网络连接失败，请稍后重试。'; }
    finally { button.disabled = false; }
  });
})();
