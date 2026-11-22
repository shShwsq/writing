#!/usr/bin/env bash
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"

SCRIPT="tools/crypt.py"
PLAIN="diary.docx"
ENC="${PLAIN}.enc"

if [ ! -f "$PLAIN" ]; then
    echo "未找到 $PLAIN" >&2
    exit 1
fi

# 内容级判断：解密 ENC 与 PLAIN 逐字节比较，一致才跳过
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
if [ -f "$ENC" ] && python "$SCRIPT" dec "$ENC" "$TMP" && cmp -s "$PLAIN" "$TMP"; then
    echo "$PLAIN 无改动，跳过。"
    exit 0
fi

echo "加密 $PLAIN -> $ENC"
python "$SCRIPT" enc "$PLAIN" "$ENC"

git add -- "$ENC"

if git diff --cached --quiet -- "$ENC"; then
    echo "$ENC 内容无变化，无需提交。"
    exit 0
fi

git commit -m "$(date '+%Y-%m-%d %H:%M')" -- "$ENC"
echo "已提交 $ENC"