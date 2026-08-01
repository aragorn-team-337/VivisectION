# VivisectION Code Review

## Overview

VivisectION is a Vivisect extension/plugin providing emulation-driven reverse engineering capabilities: function emulation (NinjaEmulator), function reconnaissance (FuncRecon), string/pointer scanning, C++ name demangling, a directed graph view, and a fake kernel/filesystem for emulated call handlers.

The codebase is ~9,000 lines across 23 Python files. It's ambitious and feature-rich, but has a significant number of bugs — many of which prevent core functionality from working as shipped.

---

## Architecture Summary

```
vivisection/
├── __init__.py          # VivisectION core class (thin wrapper)
├── analyze.py           # Static analysis: findStrings, findPointers, findStackRets
├── demangle.py          # C++ name demangling via demangler.com web API
├── emulation.py         # DaybreakMonitor/DaybreakEmulator for FuncRecon
├── emutils.py           # 5320 lines: NinjaEmulator, EmuHeap, Kernel/WinKernel/LinuxKernel,
│                        #   Win32Registry, FakeFile, ~100 libc/win32 call handlers, import_map
├── errno.py             # Single constant: EINVAL = 22
├── example_func_setup.py # Template/example file (not importable — references undefined vars)
├── loader.py            # RecursiveLoader for loading library dependencies
├── malware.py           # MalPlayMonitor, WriteTracker_1/2/3 (WIP malware analysis)
├── recon.py             # FuncRecon GUI widgets (PyQt5, IPython dependency at import time)
├── scripts/
│   ├── launchVivisectION.py  # Stub — emuMain() is a pass
│   ├── vivisection_activate.py   # Symlink plugin into VIV_EXT_PATH
│   └── vivisection_deactivate.py  # Remove symlink
├── visualize/
│   └── graph.py         # DirectedGraphView/Canvas (PyQt5, QtWebEngine)
└── viv_plugin/
    ├── __init__.py       # Exports vivExtension
    ├── emuclient.py      # Remote workspace client (HAS SYNTAX ERRORS)
    ├── share.py          # SharedVivWorkspace, shareWorkspace
    └── plugin.py         # IonManager, IonToolbar, ctxMenuHook, vivExtension, dialogs
```

---

## Critical Bugs (Prevent Core Functionality)

### 1. `emuclient.py` — Syntax Error (Import-Time Crash)

**Line 52:** `print("runClient(%r, %r, %r)" % (host, port sessid))` — missing comma between `port` and `sessid`.

This is a **SyntaxError** that prevents the entire module from being imported. The file cannot be loaded at all.

### 2. `__init__.py` — Missing Import of NinjaEmulator

**Line 40:** `self.nemu = NinjaEmulator(emu, vw=self.vw)` — but `NinjaEmulator` is never imported. This causes `NameError` when `VivisectION(vw)` is constructed with a workspace.

**Fix:** Add `from vivisection.emutils import NinjaEmulator` at the top of `__init__.py`.

### 3. `__init__.py` — NoWorkspace() Raised Without Required Argument

**Line 38:** `raise NoWorkspace()` — but `NoWorkspace.__init__` requires `msg`. This raises `TypeError` instead of the intended `NoWorkspace` exception.

**Fix:** `raise NoWorkspace("no workspace loaded")`

### 4. `emulation.py` — Wrong Argument Count in checkIfInteresting

**Lines 51-53:** `self.addString(op.va)` — but `addString` requires `(va, val)`. This is a `TypeError` at runtime.

**Lines 55-59:** `self.addUnicode(item)` — but `addUnicode` requires `(va, val)`. Same issue.

### 5. `emulation.py` — addImport Print Format Bug

**Line 85:** `print("Adding Import: %r" % item)` — when `item` is a tuple, `%r` tries to unpack the tuple as multiple format arguments, causing `TypeError: not all arguments converted during string formatting`.

**Fix:** `print("Adding Import: %r" % (item,))`

### 6. `emulation.py` — vivisect.LOC_IMPORT Not Accessible

**Line 64:** `if ltype == vivisect.LOC_IMPORT` — `LOC_IMPORT` is in `vivisect.const`, not at the top-level `vivisect` module. This causes `AttributeError`.

**Fix:** `import vivisect.const as v_const` and use `v_const.LOC_IMPORT`.

### 7. `emutils.py` — FakeFile Mode Comparison Bug

**Lines 2310, 2339:** `if b'r' not in self.mode` — but `self.mode` is a `str` (e.g. `'rb'`), not `bytes`. This causes `TypeError: 'in <string>' requires string as left operand, not bytes`.

**Fix:** `if 'r' not in self.mode` (use str, not bytes)

### 8. `emutils.py` — Kernel.getSnapshot() Pops Non-Existent Keys

**Lines 3098-3100:** `snap.pop('win32k')`, `snap.pop('ntdll')`, `snap.pop('ntoskrnl')` — these attributes only exist on `WinKernel`, not the base `Kernel` class. Calling `getSnapshot()` on a base `Kernel` or `LinuxKernel` raises `KeyError`.

**Fix:** Use `snap.pop('win32k', None)` etc. with default values.

### 9. `analyze.py` — findStrings/findPointers Skip All Maps When memranges=()

**Line 21 (findStrings), Line 128 (findPointers):** `skip = True` is initialized and only set to `False` inside the `if memranges:` block. When `memranges=()` (the default, meaning "search all maps"), all maps are skipped and nothing is found.

**Fix:** Initialize `skip = not memranges` (True only when memranges is non-empty), or restructure the logic.

### 10. `emutils.py` — strcat() TypeError

**Line 765:** `emu.writeMemory(start + len(initial) + b'\0', data)` — adds `int` (`len(initial)`) to `bytes` (`b'\0'`), which is a `TypeError`.

**Fix:** `emu.writeMemory(start + len(initial) + 1, data)`

### 11. `vivisection_activate.py` — doActivation len(args) > 1 Bug

**Line 13:** `if len(args) > 1:` — should be `len(args) > 0` (or `len(args) >= 1`). Passing a single path argument falls through to the default `~/.viv/plugins` path instead of using the provided argument.

### 12. `recon.py` — globals.get() Typo

**Line 227:** `if globals().get('vw') and globals.get('args'):` — second call is `globals.get` (missing parentheses), which is `dict.get` method reference (always truthy). Should be `globals().get('args')`.

### 13. `graph.py` — Class Name Typo

**Line 35:** `class DirecedGraphCanvas` — should be `DirectedGraphCanvas`. The `reset()` function at line 184 references `DirectedGraphView.viewidx`, but line 35 is the canvas class. This is cosmetic but confusing.

### 14. `emutils.py` — compare() Copy-Paste Bug

**Line 201:** `elif len(data1) > len(data2):` — identical to line 199 condition. Should be `elif len(data2) > len(data1):` to handle the case where data2 is longer.

### 15. `emutils.py` — REG_HIVE_HKCU Wrong Value

**Line 2818:** `REG_HIVE_HKCU = 0x80000000` — same as HKCR. Should be `0x80000001`.

### 16. `emutils.py` — CompareStringA Wrong charsize

**Line 1667:** `charsize=2` for an ANSI function. Should be `charsize=1`.

---

## Significant Bugs (Functional Issues)

### 17. `emutils.py` — findExtPath Type Confusion

**findExtPath** expects `libFileName` as bytes, but `os.listdir` returns str filenames. When comparing str to bytes, the comparison always fails. The function is fundamentally broken with bytes `libFileName`.

### 18. `emutils.py` — doWin32StringCompare Forward Reference

**Line 2467:** `val2[0]` is referenced before `val2` is read from memory. `val2` is only read on line 2478. The check on line 2467 would raise `NameError`.

### 19. `emutils.py` — RegQueryValue Uses `type` Instead of `rtype`

**Lines 3001-3004:** `if type == REG_MULTI_SZ:` — `type` is the Python builtin, not the registry type variable `rtype`. These conditions are always False.

### 20. `emutils.py` — getUserNameA Typo

**Line 2736:** `"DummUser"` — should be `"DummyUser"`.

### 21. `emutils.py` — GetTickCount Not Available

**Line 3530:** `psutil.boot_time()` — `psutil` is imported at the top but may not be installed. The pyproject.toml doesn't list `psutil` as a dependency.

### 22. `emutils.py` — GetProcAddress Logger F-String Missing

**Line 3261:** `logger.info("Attempting to open external file: %r")` — missing the value argument. This will raise `TypeError` at runtime.

---

## Security Concerns

### 23. `demangle.py` — HTTP (Not HTTPS) to External Service

**Line 21:** `requests.post('http://demangler.com/raw', ...)` — uses plain HTTP, sending potentially sensitive symbol names to an external service in cleartext. Consider using HTTPS or a local demangler.

### 24. `plugin.py` — exec() of User-Supplied Setup Code

**Line 694:** `exec(setup_code, gbls, lcls)` — executes arbitrary Python code from the setup code dialog. While this is by design (interactive emulation), it should be clearly documented as a code execution risk.

### 25. `emutils.py` — input() Prompts During Emulation

Several call handlers (`fopen`, `LoadLibraryExA`, `WaitForSingleObject`, `GetModuleFileNameA`) call `input()` during emulation, which blocks automated/headless use. These should be configurable or mockable.

---

## Style / Maintainability Issues

### 26. Version Mismatch
- `VERSION` file: `1.0.1`
- `pyproject.toml`: `1.1.0`
- `requirements.txt`: only lists `vivisect>=1.0.8`, missing `requests` and `ipython`

### 27. PyQt5 vs PyQt6
The code imports PyQt5, but the vivisect ecosystem is migrating to PyQt6 (the `pyqt6_unittests` branch).

### 28. `emutils.py` is 5320 Lines
This is a monolith. It should be broken into separate modules (ninja_emulator, emu_heap, kernels, win32_registry, call_handlers, import_map).

### 29. Excessive `print()` Usage
Many functions use `print()` for debugging instead of `logger`. The `DaybreakMonitor` especially has dozens of print statements that should be log calls.

### 30. Bare `except:` Clauses
Multiple bare `except:` clauses swallow all exceptions including `KeyboardInterrupt`:
- `analyze.py` lines 235, 258
- `emulation.py` line 190
- `emutils.py` line 1751

### 31. `example_func_setup.py` Is Not Importable
References `vemu`, `nemu`, `unhexlify`, `br` (raw string prefix misuse) without imports. It's a template file, not a module, but lives in the package tree.

### 32. Leftover Debug Code
- `emutils.py` line 3769: `import envi.interactive as ei; ei.dbg_interact(locals(), globals())` — drops into interactive debugger during `sys_win_NtQueryAttributesFile`
- Same in `sys_win_NtOpenFile`, `sys_win_NtCreateSection`, `sys_win_MapViewOfSection`

---

## Test Suite

**128 tests, 17 skipped, 0 failures.** Tests are in `tests/` and cover:

- `test_analyze.py` — findStrings, findPointers, isGoodTarget, analyzeStackMap, findStackRets
- `test_demangle.py` — demangle() with mocked HTTP, DemangleException
- `test_emulation.py` — DaybreakMonitor init, checkIfInteresting, addImport/String/Unicode/Function/DynBranch
- `test_emutils.py` — doBytes, EmuHeap, makeArgs, TraceMonitor, tokenizeFmtStr, Win32Registry, Kernel, FakeFile, import_map, ret0/ret1/retneg1, compare, testPolicy, findExtPath, constants
- `test_errno.py` — EINVAL constant
- `test_vivisection_core.py` — NoWorkspace, VivisectION class
- `test_loader.py` — RecursiveLoader, getLibFileExt, findLibDep
- `test_plugin.py` — vprint, IonManager, demangleNameAtVa, renameFullString, ctxMenuHook, IonToolbar
- `test_activate.py` — doActivation/doDeactivation with symlinks, env vars
- `test_emuclient.py` — Documents syntax errors in emuclient.py
- `test_recon.py` — FuncReconView/Widget (skipped: requires IPython + full GUI)
- `test_graph.py` — DirectedGraphView (skipped: requires QtWebEngine)

Tests use the headless PyQt6 pattern from vivisect's `pyqt6_unittests` branch: `QT_QPA_PLATFORM=offscreen`, shared QApplication singleton, processEvents in setUp/tearDown. A `conftest.py` shim aliases PyQt6 as PyQt5 so VivisectION's PyQt5 imports work against the installed PyQt6.

The tests document the source bugs — tests for broken functionality assert the appropriate `TypeError`/`NameError`/`AttributeError`/`KeyError` is raised, so when you fix a bug you'll need to update the corresponding test to assert correct behavior.

Run with:
```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ -v
```

The 17 skipped tests are GUI tests requiring QtWebEngine or full IPython+PyQt GUI stack.

---

## Recommendations

1. **Fix the critical bugs first** — the syntax error in emuclient.py and the missing import in __init__.py prevent the plugin from working at all.
2. **Migrate to PyQt6** — the vivisect ecosystem is moving to PyQt6.
3. **Break up emutils.py** — 5320 lines is unmaintainable.
4. **Replace print() with logging** — especially in DaybreakMonitor and call handlers.
5. **Use HTTPS for demangle.com** or implement a local demangler.
6. **Make input() prompts configurable** — allow headless/automated use.
7. **Add type hints** — at least to public APIs.
8. **Remove debug interactive breakpoints** from syscall handlers.