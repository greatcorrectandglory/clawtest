#!/usr/bin/env python3
"""Small moderated comments API, bound to loopback behind Nginx."""
import argparse
from contextlib import contextmanager
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
import sqlite3
import time
from urllib.parse import parse_qs, unquote, urlsplit


class Comments:
    def __init__(self, database, site_root):
        self.database = Path(database)
        self.root = Path(site_root).resolve()
        self.database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        salt_path = self.database.with_suffix('.salt')
        if not salt_path.exists():
            salt_path.write_bytes(secrets.token_bytes(32))
            salt_path.chmod(0o600)
        self.salt = salt_path.read_bytes()
        with self.connection() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('''CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY, post TEXT NOT NULL, name TEXT NOT NULL,
                body TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
                created INTEGER NOT NULL, client TEXT NOT NULL)''')
            db.execute('CREATE INDEX IF NOT EXISTS comments_post_status ON comments(post, status, created)')
            db.execute('CREATE INDEX IF NOT EXISTS comments_client_created ON comments(client, created)')
        self.database.chmod(0o600)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.database, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def valid_post(self, value):
        if not isinstance(value, str):
            raise ValueError('请选择有效文章')
        post = unquote(value)
        if not re.fullmatch(r'/posts/[^/]+/', post) or any(c in post for c in ['\\', '\x00', '?', '#']):
            raise ValueError('请选择有效文章')
        target = (self.root / post.lstrip('/') / 'index.html').resolve()
        if not target.is_relative_to(self.root / 'posts') or not target.is_file():
            raise ValueError('文章不存在')
        if 'name="robots" content="noindex' in target.read_text(encoding='utf-8'):
            raise ValueError('此页面不开放留言')
        return post

    def public(self, post):
        post = self.valid_post(post)
        with self.connection() as db:
            rows = db.execute("SELECT name, body, created FROM comments WHERE post=? AND status='approved' ORDER BY created DESC LIMIT 100", (post,)).fetchall()
        return [dict(row) for row in reversed(rows)]

    def submit(self, data, client):
        if not isinstance(data, dict):
            raise ValueError('提交格式不正确')
        post = self.valid_post(data.get('post'))
        name, body = data.get('name'), data.get('body')
        if not isinstance(name, str) or not isinstance(body, str):
            raise ValueError('请填写昵称和留言')
        name, body = name.strip(), body.strip()
        if not 1 <= len(name) <= 40 or not 5 <= len(body) <= 3000:
            raise ValueError('昵称需为 1–40 字，留言需为 5–3000 字')
        if any(ord(c) < 32 and c not in '\n\t' for c in name + body) or data.get('website'):
            raise ValueError('提交内容无效')
        now = int(time.time())
        client_hash = hmac.new(self.salt, client.encode(), hashlib.sha256).hexdigest()
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            # No raw IP addresses are stored. Discard expired hashes without deleting comments.
            db.execute("UPDATE comments SET client='' WHERE created < ? AND client != ''", (now - 86400,))
            count = db.execute('SELECT COUNT(*) FROM comments WHERE client=? AND created>?', (client_hash, now - 3600)).fetchone()[0]
            if count >= 20:
                raise OverflowError('提交较频繁，请稍后再试')
            duplicate = db.execute('SELECT id FROM comments WHERE client=? AND post=? AND body=? AND created>?', (client_hash, post, body, now - 300)).fetchone()
            if duplicate:
                raise ValueError('这条留言已收到，请勿重复提交')
            db.execute('INSERT INTO comments(id,post,name,body,created,client) VALUES(?,?,?,?,?,?)',
                       (secrets.token_hex(16), post, name, body, now, client_hash))


class Handler(BaseHTTPRequestHandler):
    server_version = 'Comments'

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def respond(self, code, data):
        payload = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path != '/api/comments':
            return self.respond(404, {'error': '接口不存在'})
        post = parse_qs(parsed.query).get('post', [''])[0]
        try:
            self.respond(200, {'comments': self.server.store.public(post)})
        except ValueError as error:
            self.respond(400, {'error': str(error)})
        except sqlite3.Error:
            self.respond(503, {'error': '留言服务繁忙，请稍后重试'})

    def do_POST(self):
        if self.path != '/api/comments':
            return self.respond(404, {'error': '接口不存在'})
        if self.headers.get('Origin') != self.server.allowed_origin:
            return self.respond(403, {'error': '请从本站文章页提交留言'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.respond(415, {'error': '提交格式不正确'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16384:
                return self.respond(413, {'error': '留言内容过长'})
            data = json.loads(self.rfile.read(size))
            # Only loopback reverse proxy reaches this listener; Nginx replaces this header.
            client = self.headers.get('X-Real-IP', self.client_address[0])
            self.server.store.submit(data, client)
            self.respond(202, {'message': '留言已收到，审核通过后会公开显示。'})
        except OverflowError as error:
            self.respond(429, {'error': str(error)})
        except (ValueError, UnicodeError) as error:
            self.respond(400, {'error': str(error) if not isinstance(error, json.JSONDecodeError) else '提交格式不正确'})
        except sqlite3.Error:
            self.respond(503, {'error': '留言服务繁忙，请稍后重试'})

    def log_message(self, *args):
        pass  # Avoid logging reader addresses or article query strings.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--site-root', type=Path, default=Path('/var/www/crossthewall.org'))
    parser.add_argument('--port', type=int, default=8786)
    parser.add_argument('--origin', default='https://crossthewall.org')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.daemon_threads = True
    server.store = Comments(args.database, args.site_root)
    server.allowed_origin = args.origin
    server.serve_forever()


if __name__ == '__main__':
    main()
