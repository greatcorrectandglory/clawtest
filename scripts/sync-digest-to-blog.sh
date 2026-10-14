#!/usr/bin/env bash
set -euo pipefail
BLOG_DIR="${BLOG_DIR:-/home/ops/clawd/myblog}"
DIGEST_DIR="${DIGEST_DIR:-/opt/knowledge-flow/digests}"
DIGEST_DATE="${DATE:-$(TZ=Asia/Shanghai date +%F)}"
args=("$DIGEST_DIR/$DIGEST_DATE.md" --date "$DIGEST_DATE" --posts "$BLOG_DIR/content/posts")
if [[ "${DRY_RUN:-0}" == "1" ]]; then
  args+=(--dry-run)
fi
exec python3 "$BLOG_DIR/scripts/import_digest.py" "${args[@]}"
