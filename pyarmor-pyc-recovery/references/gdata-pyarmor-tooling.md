# GDATA Pyarmor-Tooling Notes

Use the GDATA workflow as the bytecode extraction foundation:

```powershell
git clone https://github.com/GDATAAdvancedAnalytics/Pyarmor-Tooling D:\CodeX\tools\Pyarmor-Tooling
docker build -t pyarmor311 D:\CodeX\tools\Pyarmor-Tooling\py311
```

Pick `py39`, `py311`, `py312`, or `py313` based on the protected file's Python magic.

## Key Extraction

GDATA's original repo expects the AES-GCM key to be recovered from `pyarmor_runtime` using IDA/Binary Ninja scripts. In a migration environment:

1. Find the exact runtime loaded by the protected package, for example `runtime/pyarmor_runtime_*/pyarmor_runtime.pyd`.
2. Use GDATA's `ida_getkey.py` or `bn_getkey.py` against that runtime.
3. Pass the resulting 16-byte key to this skill's `decrypt_gcm_keyed.py` as `--key <hex>`. Do not hardcode the key in scripts.

If the runtime differs, the key differs. Never reuse a key from another project unless the runtime binary hash matches.

## Commands

Outer decrypt:

```powershell
D:\Autodesk\Maya2026\bin\mayapy.exe scripts\decrypt_gcm_keyed.py --key <hex> module.pyc
```

Analyze code-object crypto regions with the patched interpreter:

```powershell
docker run --rm -v "D:/CodeX/.codex/skills/pyarmor-pyc-recovery/scripts:/skill:ro" -v "${PWD}:/data" pyarmor311 /skill/analyze_crypted_code_py311.py /data/module.pyc.dec
```

Inner decrypt:

```powershell
D:\Autodesk\Maya2026\bin\mayapy.exe scripts\decrypt_gcm_keyed.py --key <hex> module.pyc.dec
```

Export runtime-free pyc:

```powershell
docker run --rm -v "D:/CodeX/.codex/skills/pyarmor-pyc-recovery/scripts:/skill:ro" -v "${PWD}:/data" pyarmor311 /skill/export_sliced_pyc.py /data/module.pyc.dec2 /data/module.recovered.pyc
```

Export cleanfull pyc for decompilation:

```powershell
D:\Autodesk\Maya2026\bin\mayapy.exe scripts\export_clean_full_pyc.py module.decrypted.pyc module.cleanfull.pyc
```

The `cleanfull` path assumes a standard `.pyc` created from decrypted code. If only `.dec2` exists, first export a standard decrypted `.pyc` or adjust the script to load the PyArmor marshal container.
