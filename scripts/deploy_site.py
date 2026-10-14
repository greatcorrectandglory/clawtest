#!/usr/bin/env python3
"""Build, validate and publish the Hugo-owned files; preserve independent apps."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
DIRECTORIES = {'posts', 'tags', 'categories', 'about', 'projects', 'assets', 'js', 'images', 'work', 'search', 'updates'}
ROOT_FILES = {'index.html', 'index.xml', '404.html', 'sitemap.xml', 'robots.txt', 'index.json'}
# Only these complete Hugo-generated trees may have obsolete pages removed.
PRUNE_DIRECTORIES = {'posts', 'tags', 'categories', 'about', 'projects', 'search', 'updates'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root):
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}


def managed(name):
    parts = Path(name).parts
    return name in ROOT_FILES or (len(parts) > 1 and parts[0] in DIRECTORIES)


def validate_target(root, name):
    target = root / name
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Path outside site root: {name}')
    for part in [target, *target.parents]:
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f'Symlink in managed path: {name}')
    return target


def plan_release(build, root):
    incoming = {name: path for name, path in files(build).items() if managed(name)}
    existing = files(root)
    write = [name for name, path in incoming.items()
             if name not in existing or digest(path) != digest(existing[name])]
    remove = [name for name in existing if Path(name).parts[0] in PRUNE_DIRECTORIES
              and name not in incoming]
    for name in write + remove:
        validate_target(root, name)
    return {'write': sorted(write), 'remove': sorted(remove)}


def atomic_copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.blog-deploy-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(source.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def apply_release(build, root, archive, plan, verify):
    """Backup all affected files before writes; restore them if verification fails."""
    previous = archive / 'previous'
    absent = []
    touched = plan['write'] + plan['remove']
    for name in touched:
        target = validate_target(root, name)
        if target.exists():
            saved = previous / name
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        else:
            absent.append(name)
    (archive / 'rollback.json').write_text(json.dumps({'touched': touched, 'absent': absent}, indent=2))
    try:
        # Install assets/content before switching the top-level index and sitemap.
        for name in sorted(plan['write'], key=lambda name: (name in ROOT_FILES, name)):
            atomic_copy(build / name, root / name)
        for name in plan['remove']:
            (root / name).unlink()
            # An empty leftover directory makes Nginx answer 403 instead of 404.
            parent = (root / name).parent
            while parent.parent != root and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
        for name in plan['write']:
            if digest(build / name) != digest(root / name):
                raise RuntimeError(f'Published file hash mismatch: {name}')
        verify()
    except BaseException:
        for name in touched:
            if name in absent:
                (root / name).unlink(missing_ok=True)
            else:
                atomic_copy(previous / name, root / name)
        (archive / 'status.txt').write_text('rolled back\n')
        raise
    (archive / 'status.txt').write_text('published and validated\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site-root', type=Path, default=Path('/var/www/crossthewall.org'))
    parser.add_argument('--backup-root', type=Path,
                        default=Path.home() / '.local/state/crossthewall-deployments')
    parser.add_argument('--hugo', default=str(Path.home() / '.local/bin/hugo'))
    parser.add_argument('--apply', action='store_true', help='Publish; otherwise only build and show the plan')
    args = parser.parse_args()
    root = args.site_root.resolve()
    if not root.is_dir():
        parser.error('site-root must already exist')
    args.backup_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (args.backup_root / '.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
        archive = args.backup_root / stamp
        archive.mkdir(mode=0o700)
        build = archive / 'build'
        subprocess.run([args.hugo, '--environment', 'production', '--baseURL',
                        'https://crossthewall.org/', '--destination', str(build)], cwd=REPO, check=True)
        def check(path):
            subprocess.run([sys.executable, str(REPO / 'scripts/check_seo.py'), str(path)], check=True)
            subprocess.run([sys.executable, str(REPO / 'scripts/check_reader_features.py'), str(path)], check=True)
        check(build)
        plan = plan_release(build, root)
        (archive / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2))
        (archive / 'source-state.txt').write_text(subprocess.check_output(
            ['git', 'status', '--short'], cwd=REPO, text=True))
        print(f"Plan: {len(plan['write'])} writes, {len(plan['remove'])} removals; archive: {archive}", flush=True)
        if not args.apply:
            return
        apply_release(build, root, archive, plan, lambda: check(root))
        print(f'Published and validated: {root}; rollback files: {archive / "previous"}')


if __name__ == '__main__':
    main()
