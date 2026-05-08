#!/usr/bin/env python3

import importlib.util
import marshal
import opcode
import sys
import types
from pathlib import Path


PYARMOR_FLAG = 0x20000000
NOP = opcode.opmap["NOP"]
RETURN_VALUE = opcode.opmap["RETURN_VALUE"]
PUSH_NULL = opcode.opmap.get("PUSH_NULL")
PUSH_EXC_INFO = opcode.opmap.get("PUSH_EXC_INFO")
EXTENDED_ARG = opcode.opmap["EXTENDED_ARG"]


def load_pyc(src):
    with Path(src).open("rb") as fp:
        header = fp.read(16)
        code = marshal.load(fp)
    return header, code


def write_pyc(code, dst):
    with Path(dst).open("wb") as fp:
        fp.write(importlib.util.MAGIC_NUMBER)
        fp.write((0).to_bytes(4, "little"))
        fp.write((0).to_bytes(4, "little"))
        fp.write((0).to_bytes(4, "little"))
        marshal.dump(code, fp)


def get_crypto_info(code):
    raw = bytes(getattr(code, "_co_code_adaptive", code.co_code))
    for const in code.co_consts:
        if not isinstance(const, bytes) or len(const) < 16:
            continue
        start = const[11]
        size = int.from_bytes(const[12:16], "little")
        if size > 0 and start + size <= len(raw):
            return start, size
    return None


def const_arg(insts, index):
    arg = insts[index].arg or 0
    shift = 8
    cursor = index - 1
    while cursor >= 0 and insts[cursor].opname == "EXTENDED_ARG":
        arg |= (insts[cursor].arg or 0) << shift
        shift += 8
        cursor -= 1
    return arg


def nop_range(buf, start, end):
    start = max(0, start)
    end = min(len(buf), end)
    if start % 2:
        start -= 1
    if end % 2:
        end += 1
    for offset in range(start, end, 2):
        buf[offset] = NOP
        buf[offset + 1] = 0


def patch_exit_blocks(code, buf):
    exit_indexes = {
        index
        for index, const in enumerate(code.co_consts)
        if isinstance(const, str) and const.startswith("__pyarmor_exit_")
    }
    if not exit_indexes:
        return

    import dis

    insts = list(dis.get_instructions(code, show_caches=True))
    by_offset = {inst.offset: i for i, inst in enumerate(insts)}

    for i, inst in enumerate(insts):
        if inst.opname != "LOAD_CONST" or const_arg(insts, i) not in exit_indexes:
            continue

        start_index = i
        if i > 0 and insts[i - 1].opname == "PUSH_NULL":
            start_index = i - 1
        if start_index > 0 and insts[start_index - 1].opname == "PUSH_EXC_INFO":
            end = inst.offset + 2
            j = i + 1
            while j < len(insts) and insts[j].opname not in {"RERAISE", "RETURN_VALUE"}:
                j += 1
            if j < len(insts):
                end = insts[j].offset + 2
            nop_range(buf, insts[start_index - 1].offset, end)
            continue

        start = insts[start_index].offset
        buf[start] = RETURN_VALUE
        buf[start + 1] = 0

        end = start + 2
        j = i + 1
        while j < len(insts) and insts[j].opname not in {"RETURN_VALUE", "RERAISE"}:
            j += 1
        if j < len(insts):
            end = insts[j].offset + 2
        nop_range(buf, start + 2, end)


def remove_dead_fallthrough(code, buf):
    import dis

    insts = list(dis.get_instructions(code, show_caches=True))
    targets = {0, len(buf)}
    for inst in insts:
        if "JUMP" in inst.opname and isinstance(inst.argval, int):
            targets.add(inst.argval)
    sorted_targets = sorted(targets)

    def next_target_after(offset):
        for target in sorted_targets:
            if target > offset:
                return target
        return len(buf)

    for inst in insts:
        if inst.opname in {"RETURN_VALUE", "RERAISE"}:
            nop_range(buf, inst.offset + 2, next_target_after(inst.offset))
            continue
        if inst.opname == "JUMP_FORWARD":
            jump_target = inst.argval if isinstance(inst.argval, int) else None
            next_target = next_target_after(inst.offset + 2)
            if jump_target is not None:
                end = min(next_target, jump_target)
            else:
                end = next_target
            nop_range(buf, inst.offset + 2, end)


def patch_return_jumps(code, buf):
    import dis

    insts = list(dis.get_instructions(code, show_caches=True))
    by_offset = {inst.offset: inst for inst in insts}
    for inst in insts:
        if inst.opname != "JUMP_FORWARD" or not isinstance(inst.argval, int):
            continue
        target = by_offset.get(inst.argval)
        if target and target.opname == "RETURN_VALUE":
            buf[inst.offset] = RETURN_VALUE
            buf[inst.offset + 1] = 0


def clean_code(code):
    consts = tuple(
        clean_code(const) if isinstance(const, types.CodeType) else const
        for const in code.co_consts
    )

    raw = bytearray(bytes(getattr(code, "_co_code_adaptive", code.co_code)))
    info = get_crypto_info(code)
    if info:
        start, _size = info
        nop_range(raw, 0, start)
        patch_exit_blocks(code, raw)
        patched_code = code.replace(co_code=bytes(raw), co_consts=consts)
        patch_return_jumps(patched_code, raw)
        patched_code = code.replace(co_code=bytes(raw), co_consts=consts)
        remove_dead_fallthrough(patched_code, raw)

    return code.replace(
        co_code=bytes(raw),
        co_consts=consts,
        co_flags=code.co_flags & ~PYARMOR_FLAG,
        co_exceptiontable=b"",
    )


def main(src, dst):
    _header, code = load_pyc(src)
    write_pyc(clean_code(code), dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
