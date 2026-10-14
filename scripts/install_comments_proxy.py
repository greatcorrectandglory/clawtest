#!/usr/bin/env python3
"""Run once as root to attach the already-running loopback comments API to Nginx."""
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

if os.geteuid() != 0:
    raise SystemExit('Run with sudo: sudo python3 /home/ops/clawd/myblog/scripts/install_comments_proxy.py')
config = Path('/etc/nginx/sites-available/crossthewall-blog')
original = config.read_text()
marker = '    # BEGIN moderated-comments\n'
if marker in original:
    subprocess.run(['nginx', '-t'], check=True)
    subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
    raise SystemExit('Comments proxy already installed; Nginx checked and reloaded')
needle = '    listen 443 ssl http2;'
if original.count(needle) != 1:
    raise SystemExit('Unexpected Nginx configuration; no changes made')
location = '''
    # BEGIN moderated-comments
    location = /api/comments {
        client_max_body_size 16k;
        client_body_timeout 10s;
        limit_except GET POST { deny all; }
        proxy_pass http://127.0.0.1:8786;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Origin $http_origin;
        proxy_connect_timeout 3s;
        proxy_read_timeout 15s;
        add_header Cache-Control "no-store" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Strict-Transport-Security "max-age=15552000" always;
    }
    # END moderated-comments
'''
backup = config.with_name(config.name + '.before-comments-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
shutil.copy2(config, backup)
try:
    config.write_text(original.replace(needle, needle + '\n' + location))
    subprocess.run(['nginx', '-t'], check=True)
    subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
except BaseException:
    shutil.copy2(backup, config)
    subprocess.run(['nginx', '-t'], check=False)
    subprocess.run(['systemctl', 'reload', 'nginx'], check=False)
    raise
print(f'Comments proxy installed. Previous configuration: {backup}')
