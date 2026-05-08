#!/usr/bin/env python3

import dis
import marshal
import sys
import types
from io import BytesIO


def iter_code_objects(code):
    yield code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            yield from iter_code_objects(const)


def main(filename):
    with open(filename, "rb") as fp:
        skip = int.from_bytes(fp.read(4), "little") + int.from_bytes(fp.read(4), "little")
        fp.seek(skip)
        data = fp.read()

    root = marshal.load(BytesIO(data))
    for code in iter_code_objects(root):
        print("=" * 100)
        print(f"{code.co_qualname}  line={code.co_firstlineno}  file={code.co_filename}")
        print(f"args={code.co_argcount} locals={code.co_varnames}")
        print(f"names={code.co_names}")
        print(f"consts={[c if not isinstance(c, types.CodeType) else '<code ' + c.co_qualname + '>' for c in code.co_consts]}")
        try:
            dis.dis(code)
        except Exception as exc:
            print(f"[disassembly failed: {type(exc).__name__}: {exc}]")


if __name__ == "__main__":
    main(sys.argv[1])
