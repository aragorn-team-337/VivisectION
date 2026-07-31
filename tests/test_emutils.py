'''
Tests for vivisection.emutils — pure functions, helper classes, and documented bugs.
'''
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from io import StringIO

from vivisection.emutils import (
    doBytes, compare, tokenizeFmtStr, testPolicy,
    ret0, ret1, retneg1,
    SNAP_NORM, SNAP_CAP, SNAP_DIFF, SNAP_SWAP,
    PEBSZ, TEBSZ, TLSSZ,
    CSTR_FAILURE, CSTR_LESS_THAN, CSTR_EQUAL, CSTR_GREATER_THAN,
    REG_HIVE_HKCU,
    byteprintables,
)


class TestDoBytes(unittest.TestCase):
    def test_str_to_bytes(self):
        self.assertEqual(doBytes('hello'), b'hello')

    def test_bytes_passthrough(self):
        self.assertEqual(doBytes(b'hello'), b'hello')

    def test_empty_str(self):
        self.assertEqual(doBytes(''), b'')

    def test_empty_bytes(self):
        self.assertEqual(doBytes(b''), b'')

    def test_unicode_str(self):
        # doBytes encodes using utf-8, so the latin1 chars get double-encoded
        self.assertEqual(doBytes('caf\xc3\xa9'), 'caf\xc3\xa9'.encode('utf-8'))


class TestCompare(unittest.TestCase):
    '''compare() prints highlighted hex diffs. It has a bug on line 201.'''

    def test_identical_data(self):
        with patch('builtins.print'):
            compare(b'ABCD', b'ABCD')

    def test_different_data(self):
        with patch('builtins.print'):
            compare(b'ABXD', b'ABCD')

    def test_data1_longer(self):
        with patch('builtins.print'):
            compare(b'ABCDE', b'ABCD')

    def test_data2_longer_bug(self):
        '''BUG: line 201 has `elif len(data1) > len(data2)` (duplicate of line 199).
        When data2 is longer, the tail of data2 is NOT appended to out2.
        The function still runs (prints output) but the output is incomplete.'''
        with patch('builtins.print'):
            compare(b'ABCD', b'ABCDE')

    def test_empty_both(self):
        with patch('builtins.print'):
            compare(b'', b'')


class TestTokenizeFmtStr(unittest.TestCase):
    '''tokenizeFmtStr has a bug: cfmt is bytes, but fmt may be str -> TypeError.'''

    def test_bytes_input_works(self):
        result = tokenizeFmtStr(b'Hello %s world %d')
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], b'%s')
        self.assertEqual(result[1][1], b'%d')

    def test_str_input_raises_typeerror_bug(self):
        '''BUG: cfmt is a bytes regex pattern, but fmt is str -> TypeError.'''
        with self.assertRaises(TypeError):
            tokenizeFmtStr('Hello %s world %d')

    def test_no_tokens(self):
        result = tokenizeFmtStr(b'no format strings here')
        self.assertEqual(result, ())

    def test_percent_escape(self):
        result = tokenizeFmtStr(b'100%% done')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], b'%%')

    def test_multiple_tokens(self):
        result = tokenizeFmtStr(b'%d %s %x %c')
        self.assertEqual(len(result), 4)


class TestTestPolicy(unittest.TestCase):
    '''testPolicy checks file mode permissions against fs_policy.'''

    def test_read_allowed(self):
        from envi.const import MM_READ
        self.assertTrue(testPolicy(b'r', MM_READ))

    def test_write_allowed(self):
        from envi.const import MM_WRITE
        self.assertTrue(testPolicy(b'w', MM_WRITE))

    def test_read_write_allowed(self):
        from envi.const import MM_READ, MM_WRITE
        self.assertTrue(testPolicy(b'r+', MM_READ | MM_WRITE))

    def test_append_read_write(self):
        from envi.const import MM_READ, MM_WRITE
        self.assertTrue(testPolicy(b'a', MM_READ | MM_WRITE))

    def test_write_not_read(self):
        from envi.const import MM_READ
        self.assertFalse(testPolicy(b'w', MM_READ))

    def test_read_not_write(self):
        from envi.const import MM_WRITE
        self.assertFalse(testPolicy(b'r', MM_WRITE))


class TestRetHandlers(unittest.TestCase):
    '''ret0, ret1, retneg1 are emulator call handlers. They call getLibcCallConv.'''

    def _make_mock_emu(self):
        emu = MagicMock()
        cconv = MagicMock()
        ccname = 'cdecl'
        emu.getCallingConventions.return_value = {'cdecl': cconv}
        return emu, cconv

    @patch('vivisection.emutils.getLibcCallConv')
    def test_ret0(self, mock_getcc):
        cconv = MagicMock()
        mock_getcc.return_value = ('cdecl', cconv)
        emu = MagicMock()
        ret0(emu, MagicMock())
        cconv.execCallReturn.assert_called_once_with(emu, 0, 0)

    @patch('vivisection.emutils.getLibcCallConv')
    def test_ret1(self, mock_getcc):
        cconv = MagicMock()
        mock_getcc.return_value = ('cdecl', cconv)
        emu = MagicMock()
        ret1(emu, MagicMock())
        cconv.execCallReturn.assert_called_once_with(emu, 1, 0)

    @patch('vivisection.emutils.getLibcCallConv')
    def test_retneg1(self, mock_getcc):
        cconv = MagicMock()
        mock_getcc.return_value = ('cdecl', cconv)
        emu = MagicMock()
        retneg1(emu, MagicMock())
        cconv.execCallReturn.assert_called_once_with(emu, -1, 0)


class TestConstants(unittest.TestCase):
    def test_snap_constants(self):
        self.assertEqual(SNAP_NORM, 0)
        self.assertEqual(SNAP_CAP, 1)
        self.assertEqual(SNAP_DIFF, 2)
        self.assertEqual(SNAP_SWAP, 3)

    def test_page_sizes(self):
        self.assertEqual(PEBSZ, 4096)
        self.assertEqual(TEBSZ, 4096)
        self.assertEqual(TLSSZ, 4096)

    def test_cstr_constants(self):
        self.assertEqual(CSTR_FAILURE, 0)
        self.assertEqual(CSTR_LESS_THAN, 1)
        self.assertEqual(CSTR_EQUAL, 2)
        self.assertEqual(CSTR_GREATER_THAN, 3)

    def test_reg_hive_hkcu_bug(self):
        '''BUG: REG_HIVE_HKCU = 0x80000000, same as HKCR. Should be 0x80000001.'''
        # Document the bug: HKCU should not equal HKCR (0x80000000)
        self.assertEqual(REG_HIVE_HKCU, 0x80000000)

    def test_byteprintables(self):
        self.assertIsInstance(byteprintables, bytes)
        self.assertIn(ord('A'), byteprintables)


class TestTraceMonitor(unittest.TestCase):
    def test_init_no_traces(self):
        from vivisection.emutils import TraceMonitor
        tm = TraceMonitor()
        self.assertEqual(tm.traces, {})

    def test_init_with_traces(self):
        from vivisection.emutils import TraceMonitor
        traces = {0x1000: 'emu.getProgramCounter()'}
        tm = TraceMonitor(traces)
        self.assertEqual(tm.traces, traces)

    def test_prehook_no_trace_data(self):
        from vivisection.emutils import TraceMonitor
        tm = TraceMonitor()
        emu = MagicMock()
        op = MagicMock()
        # Should not raise when trace data doesn't exist
        tm.prehook(emu, op, 0x2000)

    @patch('builtins.print')
    def test_prehook_with_trace_data(self, mock_print):
        from vivisection.emutils import TraceMonitor
        tm = TraceMonitor({0x1000: '42'})
        emu = MagicMock()
        op = MagicMock()
        tm.prehook(emu, op, 0x1000)
        mock_print.assert_called()

    @patch('builtins.print')
    def test_prehook_trace_eval_error(self, mock_print):
        from vivisection.emutils import TraceMonitor
        tm = TraceMonitor({0x1000: 'undefined_var'})
        emu = MagicMock()
        op = MagicMock()
        tm.prehook(emu, op, 0x1000)
        mock_print.assert_called()


class TestImportMap(unittest.TestCase):
    def test_import_map_exists(self):
        from vivisection import emutils
        self.assertTrue(hasattr(emutils, 'import_map'))

    def test_import_map_is_dict(self):
        from vivisection.emutils import import_map
        self.assertIsInstance(import_map, dict)

    def test_import_map_has_entries(self):
        from vivisection.emutils import import_map
        self.assertGreater(len(import_map), 0)


class TestNinjaEmulatorClass(unittest.TestCase):
    '''NinjaEmulator class exists and has expected attributes.'''

    def test_class_exists(self):
        from vivisection.emutils import NinjaEmulator
        self.assertTrue(hasattr(NinjaEmulator, '__init__'))

    def test_class_is_type(self):
        from vivisection.emutils import NinjaEmulator
        self.assertIsInstance(NinjaEmulator, type)


class TestEmuHeap(unittest.TestCase):
    '''EmuHeap basic structure.'''

    def test_emu_heap_class_exists(self):
        from vivisection.emutils import EmuHeap
        self.assertIsInstance(EmuHeap, type)

    def test_emu_heap_init(self):
        from vivisection.emutils import EmuHeap
        emu = MagicMock()
        emu.allocateMemory.return_value = 0x20000000
        # EmuHeap uses `size` not `initial_size`
        heap = EmuHeap(emu, size=1024)
        self.assertIsNotNone(heap)
        self.assertEqual(heap.ptr, 0x20000000)


class TestWin32Registry(unittest.TestCase):
    '''Win32Registry basic structure.'''

    def test_class_exists(self):
        from vivisection.emutils import Win32Registry
        self.assertIsInstance(Win32Registry, type)


class TestKernelGetSnapshotBug(unittest.TestCase):
    '''BUG: Kernel.getSnapshot() pops win32k/ntdll/ntoskrnl that don't exist
    on base Kernel or LinuxKernel -> KeyError.'''

    def test_kernel_class_exists(self):
        from vivisection.emutils import Kernel
        self.assertIsInstance(Kernel, type)

    def test_get_snapshot_keyerror_bug(self):
        '''getSnapshot on base Kernel should raise KeyError for win32k/ntdll/ntoskrnl.'''
        from vivisection.emutils import Kernel
        # Creating a Kernel requires a lot of setup; just verify the bug
        # by checking the source has .pop() without defaults
        import inspect
        src = inspect.getsource(Kernel.getSnapshot)
        # The bug: .pop('win32k') without a default
        self.assertIn(".pop('win32k')", src)
        self.assertIn(".pop('ntdll')", src)
        self.assertIn(".pop('ntoskrnl')", src)


class TestFakeFileModeBug(unittest.TestCase):
    '''BUG: FakeFile.read() uses `b'r' not in self.mode` where mode is str -> TypeError.'''

    def test_fakefile_class_exists(self):
        from vivisection.emutils import FakeFile
        self.assertIsInstance(FakeFile, type)

    def test_mode_comparison_bug(self):
        '''Verify the bug exists by checking source code.'''
        import inspect
        from vivisection.emutils import FakeFile
        src = inspect.getsource(FakeFile)
        # The bug: comparing bytes b'r' with string mode
        self.assertIn("b'r' not in self.mode", src)


class TestCompareStringACharsizeBug(unittest.TestCase):
    '''BUG: CompareStringA uses charsize=2 (wide), should be 1 (ANSI).'''

    def test_comparestringa_charsize_bug(self):
        import inspect
        from vivisection.emutils import CompareStringA
        src = inspect.getsource(CompareStringA)
        # Should be charsize=1 for ANSI, but is 2
        # Look for the call to doWin32StringCompare
        self.assertIn('charsize=2', src)


class TestFindExtPath(unittest.TestCase):
    '''findExtPath searches directory paths for a file.

    BUG: findExtPath has a type confusion: libFileName is expected as bytes,
    but os.listdir returns str filenames. When comparing str to bytes,
    the comparison always fails. The function only works if libFileName
    is a str AND fakepart is also a str (or if kernel.sep is str).'''

    def test_file_not_found_raises(self):
        import tempfile, os, shutil
        from vivisection.emutils import findExtPath
        tmpdir = tempfile.mkdtemp()
        try:
            with self.assertRaises(FileNotFoundError):
                findExtPath([(tmpdir, b'C:\\fake')], b'nonexistent.dll', kernel=None)
        finally:
            shutil.rmtree(tmpdir)

    def test_bytes_libfilename_type_confusion_bug(self):
        '''BUG: bytes libFileName compared with str os.listdir result -> never matches.'''
        import tempfile, os, shutil
        from vivisection.emutils import findExtPath
        tmpdir = tempfile.mkdtemp()
        try:
            with open(os.path.join(tmpdir, 'testlib.dll'), 'w') as f:
                f.write('test')
            # bytes libFileName never matches str fname from os.listdir
            with self.assertRaises(FileNotFoundError):
                findExtPath([(tmpdir, b'C:\\fake')], b'testlib.dll', kernel=None)
        finally:
            shutil.rmtree(tmpdir)


class TestCallHandlersExist(unittest.TestCase):
    '''Verify key call handlers are defined in emutils.'''

    def test_win32_handlers_exist(self):
        from vivisection import emutils
        for name in ['CreateFileA', 'CreateFileW', 'HeapAlloc', 'HeapFree',
                     'Sleep', 'GetCurrentProcessId', 'GetTickCount',
                     'IsDebuggerPresent', 'LoadLibraryExA', 'GetProcAddress',
                     'GetLastError', 'SetLastError']:
            self.assertTrue(hasattr(emutils, name), f'Missing handler: {name}')

    def test_libc_handlers_exist(self):
        from vivisection import emutils
        for name in ['ret0', 'ret1', 'retneg1']:
            self.assertTrue(hasattr(emutils, name), f'Missing handler: {name}')


class TestRunStep(unittest.TestCase):
    '''runStep is a module-level function that creates/uses NinjaEmulator.'''

    def test_runstep_exists(self):
        from vivisection.emutils import runStep
        self.assertTrue(callable(runStep))


if __name__ == '__main__':
    unittest.main()