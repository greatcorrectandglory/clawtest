#!/usr/bin/env bash
set -euo pipefail
BLOG_DIR="${BLOG_DIR:-/home/ops/clawd/myblog}"
if [[ "${DRY_RUN:-0}" == "1" ]]; then
  exec python3 "$BLOG_DIR/scripts/deploy_site.py" "$@"
fi
exec python3 "$BLOG_DIR/scripts/deploy_site.py" --apply "$@"
