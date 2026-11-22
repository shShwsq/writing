#!/bin/bash
set -e
cd "$(git rev-parse --show-toplevel)"

if [ -z "$1" ]; then
    echo "用法: bash decrypt.sh <文件名>"
    exit 1
fi

NAME="$1"
ENC_FILE="${NAME}.enc"

if [ ! -f "$ENC_FILE" ]; then
    echo "找不到密文: $ENC_FILE"
    exit 1
fi

if [ -f "$NAME" ]; then
    read -r -p "$NAME 已存在，覆盖? [y/N] " ans
    case "$ans" in
        y|Y|yes|YES) ;;
        *) echo "已取消。"; exit 1 ;;
    esac
fi

python tools/crypt.py dec "$ENC_FILE" "$NAME"
echo "已解密到: $NAME"
