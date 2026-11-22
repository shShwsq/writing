#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

KEY = bytes.fromhex("***REMOVED***")
NONCE_SIZE = 12

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