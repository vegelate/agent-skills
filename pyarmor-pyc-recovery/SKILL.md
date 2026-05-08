---
name: pyarmor-pyc-recovery
description: Recover readable Python source from PyArmor v8/v9 protected .py/.pyc files, especially Python 3.11+ Maya/tooling packages. Use when Codex needs to unpack PyArmor runtime-protected bytecode, decrypt PyArmor code objects using a pyarmor_runtime key, produce runtime-free .py source instead of .pyc loaders, or migrate a repeatable PyArmor deobfuscation workflow to another Codex/agent environment.
---

# PyArmor PYC Recovery

Recover PyArmor-protected Python into readable, importable `.py` files. Prefer source reconstruction over loader wrappers when the user asks to stop depending on `*.pyc`.

## Safety And Scope

- Work only on files the user owns or is authorized to inspect.
- Preserve original `.pyc`, `.dec`, `.dec2`, `.dis`, and generated pyc artifacts until the recovered `.py` imports successfully.
- Do not upload protected code to online decompilers. Use local tools only.
- For project files, write final `.py` changes directly and validate them. Keep external tool clones and scratch output under a separate workspace such as `D:\CodeX\tools` or `/tmp/codex-tools`.

## Workflow

1. Identify the Python version from the `.pyc` magic or by importing with the target interpreter. Use the same major/minor interpreter for `marshal` work.
2. Locate `pyarmor_runtime_*` and derive the AES-GCM key. GDATA Pyarmor-Tooling expects this key; see `references/gdata-pyarmor-tooling.md`.
3. Clone/build GDATA Pyarmor-Tooling for the matching Python version. For 3.11, build its `py311` Docker image or equivalent patched interpreter.
4. Outer decrypt each protected `.py`/`.pyc` with `scripts/decrypt_gcm_keyed.py --key <hex> file.pyc`, producing `file.pyc.dec`.
5. Analyze encrypted code-object regions with `scripts/analyze_crypted_code_py311.py` under the patched interpreter, producing `file.pyc.dec.json`.
6. Inner decrypt with `scripts/decrypt_gcm_keyed.py --key <hex> file.pyc.dec`, producing `file.pyc.dec2`.
7. Generate bytecode artifacts:
   - `scripts/export_sliced_pyc.py file.pyc.dec2 file.recovered.pyc` for runtime-free executable code object tests.
   - `scripts/export_clean_full_pyc.py file.decrypted.pyc file.cleanfull.pyc` when decompilers need PyArmor enter/exit wrappers removed but original control flow kept.
   - `scripts/disassemble_safe.py file.pyc.dec2 > file.py.dis` for readable bytecode fallback.
8. Reconstruct `.py` source. Prefer `depyf` for individual functions/methods, use latest `pycdc` as a fallback for failed functions, and manually compose module-level imports/classes/config lists. See `references/source-reconstruction.md`.
9. Validate with the target interpreter:
   - `mayapy -m py_compile *.py` or `python -m py_compile *.py`
   - import every module by package path
   - search final `.py` for `marshal`, `exec_recovered`, `.recovered.pyc`, `_recovered_loader`, and `__pyarmor__`

## Bundled Scripts

- `scripts/decrypt_gcm_keyed.py`: PyArmor AES-GCM outer/inner decrypt with `--key`.
- `scripts/analyze_crypted_code_py311.py`: patched GDATA analyzer for Python 3.11+ code-object regions.
- `scripts/export_sliced_pyc.py`: create executable runtime-free `*.recovered.pyc` from `.dec2`.
- `scripts/export_clean_full_pyc.py`: remove PyArmor enter/exit bytecode for better source decompilation.
- `scripts/disassemble_safe.py`: recursively disassemble decrypted code objects without stopping on failures.
- `scripts/source_fragments.py`: dump `depyf`/`pycdc` candidate source for every code object.

## Decision Rules

- If the user only needs executable recovery, a short `.py` wrapper around `*.recovered.pyc` may be acceptable.
- If the user asks for readable code or no `.pyc` dependency, do not stop at wrappers. Generate real `.py` source and remove loader references.
- If a decompiler emits `None(None)`, `None.attr`, broken lambdas, or `# WARNING: Decompyle incomplete`, treat that fragment as suspect and cross-check with disassembly or another decompiler.
- If module-level data is easier to obtain by importing the recovered module, serialize runtime objects back to source instead of reverse-engineering a giant literal from bytecode.
