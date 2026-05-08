#!/usr/bin/env python3
"""Dump readable source fragments for every code object in a pyc."""

from __future__ import annotations

import argparse
import marshal
import re
import subprocess
import textwrap
import types
from pathlib import Path


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def decompile_with_depyf(code) -> str | None:
    try:
        import depyf

        return depyf.decompile(code).rstrip() + "\n"
    except Exception as exc:
        return f"# depyf failed: {type(exc).__name__}: {exc}\n"


def decompile_with_pycdc(pycdc: Path | None, header: bytes, code, out_pyc: Path) -> str | None:
    if pycdc is None:
        return None
    out_pyc.write_bytes(header + marshal.dumps(code))
    proc = subprocess.run([str(pycdc), str(out_pyc)], text=True, capture_output=True, check=False)
    text = proc.stdout.strip()
    if not text:
        return f"# pycdc produced no output\n# stderr:\n{textwrap.indent(proc.stderr, '# ')}\n"
    return text + "\n"


def walk(code, path):
    yield path + [code.co_name], code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            yield from walk(const, path + [code.co_name])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pyc", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--pycdc", type=Path)
    args = parser.parse_args()

    with args.pyc.open("rb") as fp:
        header = fp.read(16)
        root = marshal.load(fp)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for index, (path, code) in enumerate(walk(root, []), 1):
        stem = f"{index:03d}_{safe_name('.'.join(path))}_line{code.co_firstlineno}"
        pyc_path = args.out_dir / f"{stem}.pyc"
        src_path = args.out_dir / f"{stem}.py"
        pyc_path.write_bytes(header + marshal.dumps(code))
        depyf_text = decompile_with_depyf(code)
        pycdc_text = decompile_with_pycdc(args.pycdc, header, code, args.out_dir / f"{stem}.pycdc.pyc")
        src = "# Source fragment candidates\n\n"
        src += "# --- depyf ---\n" + depyf_text
        if pycdc_text is not None:
            src += "\n# --- pycdc ---\n" + pycdc_text
        src_path.write_text(src, encoding="utf-8")


if __name__ == "__main__":
    main()
