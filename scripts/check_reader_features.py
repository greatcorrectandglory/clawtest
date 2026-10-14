#!/usr/bin/env python3
"""Check rendered reader features, draft exclusions and document search entries."""
import json
from pathlib import Path
import sys
from urllib.parse import unquote
import xml.etree.ElementTree as ET

root = Path(sys.argv[1])
home = (root / 'index.html').read_text()
assert '更新说明' in home and 'RSS' in home
assert (root / 'search/index.html').is_file()
assert (root / 'updates/index.html').is_file()
index = json.loads((root / 'index.json').read_text())
assert len([item for item in index if '/test-platform/docs/' in item['permalink']]) == 17
hidden = ['测试', '测试自动化', '推特测试', '测试文章-hello-world', 'hello-world']
for slug in hidden:
    assert not any(unquote(item['permalink']).endswith(f'/posts/{slug}/') for item in index), slug
assert not any('/2026-05-' in item['permalink'] or '/2026-06-' in item['permalink'] for item in index)
article = (root / 'posts/2026-09-29-test-platform-reproducible-runs/index.html').read_text()
for marker in ['author-card', 'related-posts', 'id="comments"', 'RSS']:
    assert marker in article, marker
projects = (root / 'projects/index.html').read_text()
assert '暂停自动发布' in projects
feed = ET.parse(root / 'index.xml')
assert any('2026-09-29-test-platform-reproducible-runs' in (item.findtext('link') or '') for item in feed.findall('.//item'))
print(f'Reader feature checks passed: {len(index)} search entries, 17 document guides, RSS, author/related/comments blocks')
