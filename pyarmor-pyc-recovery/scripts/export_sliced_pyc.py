#!/usr/bin/env python3

import importlib.util
import marshal
import opcode
import sys
import types
from io import BytesIO
from pathlib import Path


PYARMOR_FLAG = 0x20000000
LOAD_CONST = opcode.opmap["LOAD_CONST"]
RETURN_VALUE = opcode.opmap["RETURN_VALUE"]
EXTENDED_ARG = opcode.opmap["EXTENDED_ARG"]


def instr(op, arg=0):
    data = bytearray()
    value = arg >> 8
    ext = []
    while value:
        ext.append(value & 0xFF)
        value >>= 8
    for part in reversed(ext):
        data.extend((EXTENDED_ARG, part))
    data.extend((op, arg & 0xFF))
    return bytes(data)


def get_crypto_info(code):
    raw = getattr(code, "_co_code_adaptive", code.co_code)
    for const in code.co_consts:
        if not isinstance(const, bytes) or len(const) < 16:
            continue
        start = const[11]
        size = int.from_bytes(const[12:16], "little")
        if size > 0 and start + size <= len(raw):
            return start, size
    return None


def clean_code(code):
    cleaned_consts = tuple(
        clean_code(const) if isinstance(const, types.CodeType) else const
        for const in code.co_consts
    )

    raw = bytes(getattr(code, "_co_code_adaptive", code.co_code))
    consts = list(cleaned_consts)
    if info := get_crypto_info(code):
        start, size = info
        raw = raw[start:start + size]
        try:
            none_index = consts.index(None)
        except ValueError:
            none_index = len(consts)
            consts.append(None)
        raw += instr(LOAD_CONST, none_index) + instr(RETURN_VALUE)

    return code.replace(
        co_code=raw,
        co_consts=tuple(consts),
        co_flags=code.co_flags & ~PYARMOR_FLAG,
        co_exceptiontable=b"",
    )


def load_pyarmor_code(src):
    with Path(src).open("rb") as fp:
        skip = int.from_bytes(fp.read(4), "little") + int.from_bytes(fp.read(4), "little")
        fp.seek(skip)
        data = fp.read()
    return marshal.load(BytesIO(data))


def write_pyc(code, dst):
    with Path(dst).open("wb") as fp:
        fp.write(importlib.util.MAGIC_NUMBER)
        fp.write((0).to_bytes(4, "little"))
        fp.write((0).to_bytes(4, "little"))
        fp.write((0).to_bytes(4, "little"))
        marshal.dump(code, fp)


def main(src, dst):
    write_pyc(clean_code(load_pyarmor_code(src)), dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
