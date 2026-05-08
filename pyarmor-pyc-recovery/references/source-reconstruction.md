# Source Reconstruction Notes

No current local decompiler is fully reliable for PyArmor-stripped Python 3.11 modules. Compose source from multiple views.

## Recommended Local Tools

- `depyf`: best for individual Python 3.11 functions/methods.
- latest `pycdc` built from source: useful fallback for failed functions and simple module fragments.
- `dis` output: final authority for control-flow questions.
- `source_fragments.py`: creates side-by-side candidate fragments for every nested code object.

Install `depyf` into the target interpreter when needed:

```powershell
python -m pip install git+https://github.com/thuml/depyf.git
```

Build latest `pycdc` when the bundled binary is stale:

```powershell
git clone https://github.com/zrax/pycdc.git D:\CodeX\tools\pycdc-src
cmake -S D:\CodeX\tools\pycdc-src -B D:\CodeX\tools\pycdc-src\build -G "Visual Studio 17 2022" -A x64
cmake --build D:\CodeX\tools\pycdc-src\build --config Release --target pycdc pycdas
```

## Fragment Generation

```powershell
python scripts\source_fragments.py module.cleanfull.pyc --out-dir D:\CodeX\fragments\module --pycdc D:\CodeX\tools\pycdc-src\build\Release\pycdc.exe
```

Use `depyf` fragments first. Use `pycdc` fragments when `depyf` fails on loops or jumps. If both fail, reconstruct from `dis.dis(code, show_caches=False)`.

## Composition Rules

- Recreate top-level imports manually from module names and disassembly. Keep relative imports matching the original package.
- Class bodies are usually not decompiled directly. Emit `class Name(object):` and insert decompiled method functions indented inside.
- Preserve function names, argument names, constants, and public symbols from `co_names`, `co_varnames`, and runtime imports.
- For large module-level literal/config data, import the recovered module in an isolated package path and serialize the runtime object back to source.
- Fix obvious decompiler artifacts:
  - `__temp_N` loop variables can become descriptive names, but do not over-refactor.
  - Remove unreachable statements after `continue`/`return`.
  - Replace broken `None(None)`/`None.attr` with the intended receiver by checking bytecode stack or neighboring fragments.
  - Broken list comprehensions/lambdas should be reconstructed from nested code objects.

## Validation Checklist

Run all checks before replacing project files:

```powershell
python -m py_compile recovered_package\*.py
```

Then import modules by their real package names. Finally:

```powershell
Select-String -Path recovered_package\*.py -Pattern 'marshal','exec_recovered','.pyc','__pyarmor__','_recovered_loader'
```

The final `.py` files should not depend on recovered pyc loaders. Keep `.pyc`, `.dec2`, `.dis`, and fragments as audit artifacts until the user approves cleanup.
