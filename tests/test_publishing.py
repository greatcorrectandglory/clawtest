import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deploy = load('deploy_site')
imports = load('import_digest')


class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'live'
        self.build = Path(self.temporary.name) / 'build'
        self.archive = Path(self.temporary.name) / 'archive'
        for path in [self.root, self.build, self.archive]:
            path.mkdir()
        self.write(self.root, 'index.html', 'old home')
        self.write(self.root, 'posts/obsolete/index.html', 'old article')
        self.write(self.root, 'test-platform/index.html', 'independent product')
        self.write(self.root, 'ota/manifest.json', 'independent OTA')
        self.write(self.root, 'muyu/index.html', 'independent app')
        self.write(self.build, 'index.html', 'new home')
        self.write(self.build, 'js/comments.js', 'comment script')
        self.write(self.build, 'posts/new/index.html', 'new article')
        self.write(self.build, 'test-platform/index.html', 'must not overwrite')
        self.write(self.build, 'muyu/index.html', 'must not overwrite')

    def write(self, root, name, text):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_publish_preserves_independent_apps_and_removes_stale_owned_pages(self):
        plan = deploy.plan_release(self.build, self.root)
        self.assertEqual(plan['remove'], ['posts/obsolete/index.html'])
        deploy.apply_release(self.build, self.root, self.archive, plan, lambda: None)
        self.assertEqual((self.root / 'index.html').read_text(), 'new home')
        self.assertEqual((self.root / 'js/comments.js').read_text(), 'comment script')
        self.assertFalse((self.root / 'posts/obsolete').exists())
        self.assertTrue((self.root / 'posts').is_dir())
        for name, expected in [('test-platform/index.html', 'independent product'),
                               ('ota/manifest.json', 'independent OTA'),
                               ('muyu/index.html', 'independent app')]:
            self.assertEqual((self.root / name).read_text(), expected)
        self.assertEqual(deploy.plan_release(self.build, self.root), {'write': [], 'remove': []})

    def test_failed_verification_rolls_back_changed_deleted_and_new_files(self):
        before = {name: path.read_bytes() for name, path in deploy.files(self.root).items()}
        def fail():
            raise RuntimeError('verification failed')
        with self.assertRaisesRegex(RuntimeError, 'verification failed'):
            deploy.apply_release(self.build, self.root, self.archive,
                                 deploy.plan_release(self.build, self.root), fail)
        after = {name: path.read_bytes() for name, path in deploy.files(self.root).items()}
        self.assertEqual(before, after)
        self.assertEqual((self.archive / 'status.txt').read_text(), 'rolled back\n')

    def test_symlink_cannot_escape_site_root(self):
        (self.root / 'images').symlink_to(self.archive, target_is_directory=True)
        self.write(self.build, 'images/avatar.png', 'image')
        with self.assertRaises(ValueError):
            deploy.plan_release(self.build, self.root)


class DigestTests(unittest.TestCase):
    def body(self, published):
        return (f'# 每日科技简报\n\n## 1. Example release\n- 时间：{published}T00:00:00Z\n'
                '- 链接：https://example.com/release\n- 摘要：示例\n')

    def test_recent_digest_requires_editorial_review(self):
        result = imports.render_digest(self.body('2026-09-28'), date(2026, 9, 29))
        self.assertIn('draft = true', result)
        self.assertIn('description = ', result)

    def test_stale_future_and_undated_entries_are_rejected(self):
        for value in ['2026-03-23', '2026-09-30', 'unknown']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                imports.render_digest(self.body(value), date(2026, 9, 29))

    def test_one_fresh_entry_does_not_hide_stale_entries(self):
        body = self.body('2026-09-29') + self.body('2026-03-23').replace('## 1.', '## 2.')
        with self.assertRaises(ValueError):
            imports.render_digest(body, date(2026, 9, 29))


if __name__ == '__main__':
    unittest.main()
