import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('comment_api', ROOT / 'services/comments/server.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class CommentsIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        article = self.root / 'site/posts/example/index.html'
        article.parent.mkdir(parents=True)
        article.write_text('<meta name="robots" content="index, follow">')
        self.database = self.root / 'private/comments.sqlite3'
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), api.Handler)
        self.server.store = api.Comments(self.database, self.root / 'site')
        self.server.allowed_origin = 'https://crossthewall.org'
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = 'http://127.0.0.1:' + str(self.server.server_port) + '/api/comments'

    def request(self, data=None, origin='https://crossthewall.org', suffix=''):
        req = urllib.request.Request(self.url + suffix, data=json.dumps(data).encode() if data is not None else None,
                                     headers={'Origin': origin, 'Content-Type': 'application/json'})
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def payload(self, body='有用的开发实践，谢谢分享。'):
        return {'post': '/posts/example/', 'name': '读者', 'body': body}

    def test_pending_not_public_until_owner_approves(self):
        self.assertEqual(self.request(self.payload())[0], 202)
        self.assertEqual(self.request(suffix='?post=/posts/example/')[1]['comments'], [])
        with sqlite3.connect(self.database) as db:
            identifier, client = db.execute('SELECT id, client FROM comments').fetchone()
            self.assertEqual(len(client), 64)
        subprocess.run([sys.executable, str(ROOT/'scripts/moderate_comments.py'), 'approve', identifier,
                        '--database', str(self.database)], check=True, capture_output=True)
        status, response = self.request(suffix='?post=/posts/example/')
        self.assertEqual(status, 200)
        self.assertEqual(response['comments'][0]['body'], self.payload()['body'])
        self.assertNotIn('client', response['comments'][0])

    def test_cross_origin_and_invalid_article_rejected(self):
        self.assertEqual(self.request(self.payload(), origin='https://other.example')[0], 403)
        data = self.payload(); data['post'] = '/posts/../../private/'
        self.assertEqual(self.request(data)[0], 400)
        data['post'] = '/posts/missing/'
        self.assertEqual(self.request(data)[0], 400)

    def test_duplicate_and_oversized_comments_rejected(self):
        self.assertEqual(self.request(self.payload())[0], 202)
        self.assertEqual(self.request(self.payload())[0], 400)
        self.assertEqual(self.request(self.payload('x' * 3001))[0], 400)

    def test_rate_limit_and_unapproved_markup_is_not_public(self):
        for i in range(20):
            self.assertEqual(self.request(self.payload(f'<script>alert({i})</script>'))[0], 202)
        self.assertEqual(self.request(self.payload('这是超出频率的请求'))[0], 429)
        self.assertEqual(self.request(suffix='?post=/posts/example/')[1]['comments'], [])


if __name__ == '__main__':
    unittest.main()
