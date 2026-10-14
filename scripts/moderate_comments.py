#!/usr/bin/env python3
"""Review site comments over SSH; no public administrative endpoint."""
import argparse
import json
from pathlib import Path
import sqlite3

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('action', choices=['list', 'approve', 'reject'])
parser.add_argument('id', nargs='?')
parser.add_argument('--database', type=Path, default=Path.home() / '.local/state/crossthewall-comments/comments.sqlite3')
args = parser.parse_args()
if not args.database.is_file():
    parser.error('Comment database does not exist')
db = sqlite3.connect(args.database)
db.row_factory = sqlite3.Row
with db:
    if args.action == 'list':
        rows = db.execute("SELECT id, post, name, body, created FROM comments WHERE status='pending' ORDER BY created LIMIT 100").fetchall()
        print(json.dumps([dict(row) for row in rows], ensure_ascii=False, indent=2))
    else:
        if not args.id:
            parser.error('A comment id is required')
        result = db.execute('UPDATE comments SET status=? WHERE id=?', ('approved' if args.action == 'approve' else 'rejected', args.id))
        if result.rowcount != 1:
            parser.error('Comment not found')
        print('Comment ' + ('approved' if args.action == 'approve' else 'rejected'))
db.close()
