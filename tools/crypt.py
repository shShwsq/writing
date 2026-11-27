#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

NONCE_SIZE = 12

def _load_key() -> bytes:
    """从环境变量 GUARD_SECRET 或仓库根目录 .env 读取密钥"""
    hexkey = os.environ.get("GUARD_SECRET", "").strip()
    if not hexkey:
        env_file = Path(__file__).resolve().parents[1] / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GUARD_SECRET="):
                    hexkey = line.split("=", 1)[1].strip()
                    break
    if not hexkey:
        print("未找到密钥：请在环境变量 GUARD_SECRET 或仓库根目录 .env 中配置", file=sys.stderr)
        sys.exit(1)
    try:
        return bytes.fromhex(hexkey)
    except ValueError:
        print("密钥格式错误：需要 64 位十六进制字符串", file=sys.stderr)
        sys.exit(1)

KEY = _load_key()

def encrypt(src: Path, dst: Path) -> None:
    data = src.read_bytes()
    nonce = os.urandom(NONCE_SIZE)
    ct = ChaCha20Poly1305(KEY).encrypt(nonce, data, None)
    dst.write_bytes(nonce + ct)

def decrypt(src: Path, dst: Path) -> None:
    data = src.read_bytes()
    nonce, ct = data[:NONCE_SIZE], data[NONCE_SIZE:]
    pt = ChaCha20Poly1305(KEY).decrypt(nonce, ct, None)
    dst.write_bytes(pt)

def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] not in ("enc", "dec"):
        print("用法: crypt.py enc|dec <src> <dst>", file=sys.stderr)
        sys.exit(1)
    cmd, src, dst = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    (encrypt if cmd == "enc" else decrypt)(src, dst)

if __name__ == "__main__":
    main()
