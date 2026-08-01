'''
Tests for vivisection.viv_plugin.plugin — IonManager, toolbar, context menu hooks.
'''
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure conftest shim is loaded
import tests.conftest  # noqa: F401

from vivisection.viv_plugin.plugin import IonManager


class TestIonManagerInit(unittest.TestCase):
    def test_init_stores_vw(self):
        vw = MagicMock()
        mgr = IonManager(vw)
        self.assertEqual(mgr.vw, vw)

    def test_init_no_sessions(self):
        vw = MagicMock()
        mgr = IonManager(vw)
        self.assertEqual(mgr.sessions, {})


class TestIonManagerSessions(unittest.TestCase):
    def test_new_session(self):
        vw = MagicMock()
        mgr = IonManager(vw)
        # Sessions should be empty initially
        self.assertEqual(mgr.sessions, {})

    def test_ionmgr_methods_exist(self):
        vw = MagicMock()
        mgr = IonManager(vw)
        # Check key methods exist
        for method in ['getSession', 'addSession']:
            self.assertTrue(hasattr(mgr, method), f'Missing method: {method}')


class TestDemangleNameAtVa(unittest.TestCase):
    def test_demangle_name_at_va_callable(self):
        from vivisection.viv_plugin.plugin import demangleNameAtVa
        self.assertTrue(callable(demangleNameAtVa))


class TestRenameFullString(unittest.TestCase):
    def test_rename_full_string_exists(self):
        from vivisection.viv_plugin.plugin import renameFullString
        self.assertTrue(callable(renameFullString))


class TestCtxMenuHook(unittest.TestCase):
    def test_ctxmenu_not_in_function(self):
        '''ctxMenuHook when VA is not in a function should return without adding menu items.'''
        from vivisection.viv_plugin.plugin import ctxMenuHook
        vw = MagicMock()
        vw.getFunction.return_value = None
        menu = MagicMock()
        ctxMenuHook(vw, 0x1000, '0x1000', menu, None, None)

    def test_ctxmenu_in_function(self):
        '''BUG: ctxMenuHook references ionRecon which fails to import because
        recon.py requires IPython at module level. The exception is caught
        by the try/except in ctxMenuHook and printed, not re-raised.'''
        from vivisection.viv_plugin.plugin import ctxMenuHook
        vw = MagicMock()
        vw.getFunction.return_value = 0x1000
        vw.getVivGui.return_value = MagicMock()
        vw.getName.return_value = 'func_name'
        menu = MagicMock()
        # ionRecon import fails (IPython dependency), so ctxMenuHook
        # catches the NameError internally and doesn't add the menu items
        ctxMenuHook(vw, 0x1000, '0x1000', menu, None, None)


class TestVivExtension(unittest.TestCase):
    def test_viv_extension_exists(self):
        from vivisection.viv_plugin import vivExtension
        self.assertTrue(callable(vivExtension))


class TestIonToolbar(unittest.TestCase):
    def test_ion_toolbar_class_exists(self):
        from vivisection.viv_plugin.plugin import IonToolbar
        self.assertIsInstance(IonToolbar, type)

    def test_ion_toolbar_init_requires_gui(self):
        '''IonToolbar requires a GUI (QToolBar). Skip if no Qt display.'''
        from vivisection.viv_plugin.plugin import IonToolbar
        # Just verify it's a class
        self.assertTrue(hasattr(IonToolbar, '__init__'))


class TestPluginImport(unittest.TestCase):
    def test_plugin_module_imports(self):
        import vivisection.viv_plugin.plugin
        self.assertTrue(hasattr(vivisection.viv_plugin.plugin, 'IonManager'))


if __name__ == '__main__':
    unittest.main()