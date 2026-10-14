#!/usr/bin/env python3
"""Import only dated, recent digest entries. Publishing remains an explicit action."""
import argparse
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import re
import sys


def render_digest(body, day):
    entries = re.split(r'(?m)^## \d+\. ', body)[1:]
    if not entries:
        raise ValueError('No dated digest entries found')
    titles = []
    for entry in entries:
        match = re.search(r'(?m)^- 时间：(\d{4}-\d{2}-\d{2})(?:T|\s|$)', entry)
        if not match:
            raise ValueError('Every digest entry must have a source publication date')
        published = date.fromisoformat(match.group(1))
        if not day - timedelta(days=7) <= published <= day:
            raise ValueError(f'Source date {published} outside the 7-day window for {day}')
        if not re.search(r'(?m)^- 链接：https?://\S+', entry):
            raise ValueError('Every digest entry must link to its source')
        titles.append(entry.splitlines()[0].strip())
    description = f'{day} 技术资讯整理：' + '；'.join(titles[:3])
    if len(description) > 150:
        description = description[:149] + '…'
    return (f'+++\ntitle = "{day} 技术资讯整理"\ndate = {day}T08:00:00+08:00\n'
            f'description = {json.dumps(description, ensure_ascii=False)}\n'
            'tags = ["技术资讯"]\ncategories = ["资讯整理"]\ndraft = true\n+++\n\n' + body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('digest', type=Path)
    parser.add_argument('--date', type=date.fromisoformat, required=True)
    parser.add_argument('--posts', type=Path, required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        rendered = render_digest(args.digest.read_text(), args.date)
        target = args.posts / f'{args.date}-ai-digest.md'
        if args.dry_run:
            print(f'Validated draft; no file written: {target}')
            return
        args.posts.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_text() == rendered:
                print(f'Draft unchanged: {target}')
                return
            raise ValueError(f'Refusing to overwrite an existing article: {target}')
        with target.open('x') as stream:
            stream.write(rendered)
        print(f'Draft imported for editorial review: {target}')
    except (OSError, ValueError) as error:
        sys.exit(str(error))


if __name__ == '__main__':
    main()
