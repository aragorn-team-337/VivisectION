'''
Tests for vivisection.loader — RecursiveLoader.
'''
import os
import tempfile
import shutil
import unittest
from unittest.mock import MagicMock

from vivisection.loader import RecursiveLoader, FT_PE, FT_ELF


class TestRecursiveLoaderInit(unittest.TestCase):
    def test_init_default_paths(self):
        vw = MagicMock()
        loader = RecursiveLoader(vw)
        self.assertEqual(loader.vw, vw)
        self.assertEqual(loader.paths, ['.'])

    def test_init_custom_paths(self):
        vw = MagicMock()
        loader = RecursiveLoader(vw, paths=['/usr/lib', '/lib'])
        self.assertEqual(loader.paths, ['/usr/lib', '/lib'])

    def test_ft_constants(self):
        self.assertEqual(FT_PE, 1)
        self.assertEqual(FT_ELF, 2)


class TestGetLibFileExt(unittest.TestCase):
    def test_elf_with_got(self):
        vw = MagicMock()
        vw.getFiles.return_value = ['libtest.so']
        vw.getFileMeta.return_value = True  # GOT exists
        loader = RecursiveLoader(vw)
        self.assertEqual(loader.getLibFileExt(), '.so')

    def test_pe_without_got(self):
        vw = MagicMock()
        vw.getFiles.return_value = ['test.dll']
        vw.getFileMeta.return_value = None  # No GOT
        loader = RecursiveLoader(vw)
        self.assertEqual(loader.getLibFileExt(), '.dll')

    def test_multiple_files_with_got(self):
        vw = MagicMock()
        vw.getFiles.return_value = ['libtest.so', 'libother.so']
        # getFileMeta called for each file; first returns True
        vw.getFileMeta.return_value = True
        loader = RecursiveLoader(vw)
        self.assertEqual(loader.getLibFileExt(), '.so')


class TestFindLibDep(unittest.TestCase):
    def test_exact_match(self):
        tmpdir = tempfile.mkdtemp()
        try:
            libpath = os.path.join(tmpdir, 'libtest.so')
            with open(libpath, 'w') as f:
                f.write('test')
            vw = MagicMock()
            loader = RecursiveLoader(vw, paths=[tmpdir])
            result = loader.findLibDep('libtest.so', filetype=FT_ELF)
            self.assertEqual(result, os.path.join(tmpdir, 'libtest.so'))
        finally:
            shutil.rmtree(tmpdir)

    def test_versioned_so(self):
        tmpdir = tempfile.mkdtemp()
        try:
            # Create libtest.so.1
            libpath = os.path.join(tmpdir, 'libtest.so.1')
            with open(libpath, 'w') as f:
                f.write('test')
            vw = MagicMock()
            loader = RecursiveLoader(vw, paths=[tmpdir])
            result = loader.findLibDep('libtest.so', filetype=FT_ELF)
            self.assertEqual(result, os.path.join(tmpdir, 'libtest.so.1'))
        finally:
            shutil.rmtree(tmpdir)

    def test_not_found_returns_none(self):
        tmpdir = tempfile.mkdtemp()
        try:
            vw = MagicMock()
            loader = RecursiveLoader(vw, paths=[tmpdir])
            result = loader.findLibDep('nonexistent.so', filetype=FT_ELF)
            self.assertIsNone(result)
        finally:
            shutil.rmtree(tmpdir)

    def test_nonexistent_path_handled(self):
        vw = MagicMock()
        loader = RecursiveLoader(vw, paths=['/nonexistent/path'])
        # Should not raise, returns None
        result = loader.findLibDep('libtest.so', filetype=FT_ELF)
        self.assertIsNone(result)

    def test_multiple_versioned_numbers(self):
        tmpdir = tempfile.mkdtemp()
        try:
            libpath = os.path.join(tmpdir, 'libtest.so.5')
            with open(libpath, 'w') as f:
                f.write('test')
            vw = MagicMock()
            loader = RecursiveLoader(vw, paths=[tmpdir])
            result = loader.findLibDep('libtest.so', filetype=FT_ELF)
            self.assertEqual(result, os.path.join(tmpdir, 'libtest.so.5'))
        finally:
            shutil.rmtree(tmpdir)


class TestLoad(unittest.TestCase):
    def test_load_no_dependencies(self):
        vw = MagicMock()
        vw.getLibraryDependancies.return_value = []
        vw.getFiles.return_value = []
        loader = RecursiveLoader(vw)
        loader.load()  # Should not raise

    def test_load_with_existing_dependency(self):
        vw = MagicMock()
        vw.getLibraryDependancies.return_value = ['libtest']
        vw.getFiles.return_value = ['libtest']  # Already loaded
        loader = RecursiveLoader(vw)
        loader.load()
        # Should not call loadFromFile since lib is already in files
        vw.loadFromFile.assert_not_called()

    def test_load_finds_and_loads_dependency(self):
        tmpdir = tempfile.mkdtemp()
        try:
            # getLibFileExt returns '.dll' when getFiles() is empty
            # (no GOT meta found), so the file must be 'libtest.dll'
            libpath = os.path.join(tmpdir, 'libtest.dll')
            with open(libpath, 'w') as f:
                f.write('test')

            vw = MagicMock()
            vw.getLibraryDependancies.return_value = ['libtest']
            vw.getFiles.return_value = []  # Not loaded yet
            vw.loadFromFile.return_value = 'libtest'

            loader = RecursiveLoader(vw, paths=[tmpdir])
            loader.load()
            vw.loadFromFile.assert_called_once()
        finally:
            shutil.rmtree(tmpdir)

    def test_load_missing_dependency_continues(self):
        vw = MagicMock()
        vw.getLibraryDependancies.return_value = ['libmissing']
        vw.getFiles.return_value = []
        vw.getFileMeta.return_value = True

        loader = RecursiveLoader(vw, paths=['/nonexistent'])
        loader.load()  # Should not raise even if dep not found


if __name__ == '__main__':
    unittest.main()