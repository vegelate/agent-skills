#!/usr/bin/env python3
"""Decrypt PyArmor AES-GCM blobs with an explicit runtime key."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Optional

from Crypto.Cipher import AES


def get_third_argument(filepath: Path) -> Optional[bytes]:
    tree = ast.parse(filepath.read_text(encoding="utf-8", errors="replace"))

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.args = None

        def visit_Call(self, node):
            if self.args is None and isinstance(node.func, ast.Name):
                self.args = node.args
                return
            self.generic_visit(node)

    visitor = Visitor()
    visitor.visit(tree)
    if visitor.args and len(visitor.args) >= 3:
        value = visitor.args[2]
        if isinstance(value, ast.Constant) and isinstance(value.value, bytes):
            return value.value
    return None


def get_bytes_from_pyc(filepath: Path) -> bytes:
    module = filepath.read_bytes()
    marker = b"__pyarmor__\x73"
    pos = module.find(marker)
    if pos == -1:
        raise RuntimeError("Unable to locate pyarmor data in compiled module")
    pos += len(marker)
    armor_len = int.from_bytes(module[pos : pos + 4], "little")
    if armor_len < 0x200 or armor_len > 10 * 1024 * 1024:
        raise RuntimeError(f"String length implausible: {armor_len}")
    return module[pos + 4 : pos + 4 + armor_len]


def decrypt_gcm_without_tag(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    return AES.new(key, AES.MODE_GCM, nonce=nonce).decrypt(ciphertext)


def decrypt_outer(filepath: Path, key: bytes) -> Path:
    if filepath.suffix == ".py":
        armor_bytes = get_third_argument(filepath)
        if armor_bytes is None:
            raise RuntimeError("Unable to find third __pyarmor__ argument")
    elif filepath.suffix == ".pyc":
        armor_bytes = get_bytes_from_pyc(filepath)
    else:
        raise RuntimeError("Outer decrypt expects .py or .pyc")

    if armor_bytes[20] == 9:
        nonce = armor_bytes[36:40] + armor_bytes[44:52]
        bcc_start = int.from_bytes(armor_bytes[28:32], "little")
        bcc_end = int.from_bytes(armor_bytes[56:60], "little")
        plaintext = decrypt_gcm_without_tag(key, nonce, armor_bytes[bcc_start:bcc_end])
        filepath.with_suffix(filepath.suffix + ".dec.elf").write_bytes(plaintext[16:])
        armor_bytes = armor_bytes[bcc_end:]

    nonce = armor_bytes[36:40] + armor_bytes[44:52]
    ciphertext = armor_bytes[int.from_bytes(armor_bytes[28:32], "little") :]
    out = filepath.with_suffix(filepath.suffix + ".dec")
    out.write_bytes(decrypt_gcm_without_tag(key, nonce, ciphertext))
    return out


def decrypt_inner(filepath: Path, key: bytes) -> Path:
    module = bytearray(filepath.read_bytes())
    regions = json.loads(filepath.with_suffix(filepath.suffix + ".json").read_text())
    skip = int.from_bytes(module[0:4], "little") + int.from_bytes(module[4:8], "little")
    for region in regions:
        start = skip + region["ciphertext_offset"]
        size = region["ciphertext_size"]
        nonce = bytes.fromhex(region["nonce"])
        module[start : start + size] = decrypt_gcm_without_tag(key, nonce, module[start : start + size])
    out = filepath.with_suffix(filepath.suffix + "2")
    out.write_bytes(module)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--key", required=True, help="16-byte AES key as hex")
    args = parser.parse_args()
    key = bytes.fromhex(args.key)
    if len(key) != 16:
        raise SystemExit("--key must decode to 16 bytes")

    name = args.input.name
    if name.endswith(".py.dec") or name.endswith(".pyc.dec"):
        out = decrypt_inner(args.input, key)
    else:
        out = decrypt_outer(args.input, key)
    print(out)


if __name__ == "__main__":
    main()
