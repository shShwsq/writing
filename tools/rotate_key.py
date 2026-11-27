#!/usr/bin/env python3
"""轮换日记加密密钥：重写 git 历史，把所有用旧密钥加密的 blob 重新用新密钥加密。

依赖: pip install git-filter-repo cryptography

用法:
  python tools/rotate_key.py                  # 自动生成新密钥
  python tools/rotate_key.py --new-key <hex>  # 指定新密钥(64位hex)

完成后历史已改写，需手动: git push --force origin main
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from git_filter_repo import FilteringOptions, RepoFilter

NONCE_SIZE = 12


def sh(*args, check=True) -> str:
    r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        sys.exit(f"命令失败: {' '.join(args)}\n{r.stderr}")
    return r.stdout.strip()


def load_old_key() -> bytes:
    hexkey = os.environ.get("GUARD_SECRET", "").strip()
    if not hexkey:
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GUARD_SECRET="):
                    hexkey = line.split("=", 1)[1].strip()
                    break
    if not hexkey:
        sys.exit("未找到旧密钥：请配置环境变量 GUARD_SECRET 或仓库根目录 .env")
    try:
        return bytes.fromhex(hexkey)
    except ValueError:
        sys.exit("旧密钥格式错误：需要 64 位十六进制字符串")


def write_env_key(new_hex: str) -> None:
    env_file = Path.cwd() / ".env"
    lines = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []
    for i, line in enumerate(lines):
        if line.strip().startswith("GUARD_SECRET="):
            lines[i] = f"GUARD_SECRET={new_hex}"
            break
    else:
        lines.append(f"GUARD_SECRET={new_hex}")
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


class Rotator(RepoFilter):
    def __init__(self, args, old_key: bytes, new_key: bytes):
        # blob_callback 必须经构造函数传入，覆盖同名方法无效
        super().__init__(args, blob_callback=self.rotate_blob)
        self.old_key = old_key
        self.new_key = new_key
        self.rotated = 0

    def rotate_blob(self, blob, metadata):
        # 只有旧密钥能通过 Poly1305 校验的 blob 才是加密文件，误伤概率为零
        if len(blob.data) <= NONCE_SIZE:
            return
        nonce, ct = blob.data[:NONCE_SIZE], blob.data[NONCE_SIZE:]
        try:
            pt = ChaCha20Poly1305(self.old_key).decrypt(nonce, ct, None)
        except Exception:
            return
        new_nonce = os.urandom(NONCE_SIZE)
        blob.data = new_nonce + ChaCha20Poly1305(self.new_key).encrypt(new_nonce, pt, None)
        self.rotated += 1


def main() -> None:
    parser = argparse.ArgumentParser(description="轮换日记加密密钥并重写 git 历史")
    parser.add_argument("--new-key", help="新密钥(64位hex)，默认自动生成")
    opts = parser.parse_args()

    os.chdir(sh("git", "rev-parse", "--show-toplevel"))

    dirty = sh("git", "status", "--porcelain")
    if any(l for l in dirty.splitlines() if l and not l.startswith("??")):
        sys.exit("工作区有未提交改动，请先提交再轮换密钥")

    old_key = load_old_key()
    new_hex = (opts.new_key or os.urandom(32).hex()).strip()
    new_key = bytes.fromhex(new_hex)
    if new_key == old_key:
        sys.exit("新密钥与旧密钥相同")

    # 重写前备份完整历史
    backup = Path(tempfile.gettempdir()) / f"writing-backup-{time.strftime('%Y%m%d-%H%M%S')}.bundle"
    sh("git", "bundle", "create", str(backup), "--all")
    print(f"已备份当前历史: {backup}")

    origin = sh("git", "remote", "get-url", "origin", check=False)

    # 先持久化新密钥，再重写历史
    write_env_key(new_hex)

    rotator = Rotator(FilteringOptions.parse_args(["--force"]), old_key, new_key)
    rotator.run()

    if origin and "origin" not in sh("git", "remote", check=False).split():
        sh("git", "remote", "add", "origin", origin)

    print(f"\n轮换完成：{rotator.rotated} 个历史 blob 已用新密钥重新加密")
    print("新密钥已写入 .env")
    print("下一步：git push --force origin main")


if __name__ == "__main__":
    main()
