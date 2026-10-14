#!/usr/bin/env python3
"""Preview or install a www-to-primary-host redirect, preserving apps and comments."""
import argparse
from datetime import datetime, timezone
import difflib
import os
from pathlib import Path
import shutil
import subprocess

CONFIG = Path('/etc/nginx/sites-available/crossthewall-blog')
MARKER = '    # BEGIN canonical-www\n'
RULE = '''    # BEGIN canonical-www
    if ($host = www.crossthewall.org) {
        return 301 https://crossthewall.org$request_uri;
    }
    # END canonical-www
'''


def candidate(original):
    if MARKER in original:
        if original.count(RULE) != 2:
            raise ValueError('Unexpected existing redirect; no changes made')
        return original
    needle = '    server_name crossthewall.org www.crossthewall.org test1.crossthewall.org;\n'
    if original.count(needle) != 2:
        raise ValueError('Expected exactly two known HTTP/HTTPS servers; no changes made')
    return original.replace(needle, needle + '\n' + RULE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    original = CONFIG.read_text()
    changed = candidate(original)
    if not args.apply:
        print(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True), fromfile=str(CONFIG), tofile=str(CONFIG) + ' (proposed)')))
        return
    if os.geteuid() != 0:
        parser.error('--apply requires sudo')
    if changed == original:
        subprocess.run(['nginx', '-t'], check=True)
        print('Redirect already installed')
        return
    backup = CONFIG.with_name(CONFIG.name + '.before-seo-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    shutil.copy2(CONFIG, backup)
    try:
        CONFIG.write_text(changed)
        subprocess.run(['nginx', '-t'], check=True)
        subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
    except BaseException:
        shutil.copy2(backup, CONFIG)
        subprocess.run(['nginx', '-t'], check=False)
        subprocess.run(['systemctl', 'reload', 'nginx'], check=False)
        raise
    print(f'Installed www redirect. Backup: {backup}')


if __name__ == '__main__':
    main()
