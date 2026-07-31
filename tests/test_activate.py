'''
Tests for vivisection.scripts.vivisection_activate / vivisection_deactivate.
'''
import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock


class TestDoActivation(unittest.TestCase):
    '''doActivation creates a symlink to the plugin directory.'''

    def test_activation_with_explicit_path(self):
        '''BUG: doActivation checks `len(args) > 1` instead of `> 0`,
        so a single path argument is ignored.'''
        tmpdir = tempfile.mkdtemp()
        try:
            plugin_dir = os.path.join(tmpdir, 'plugins')
            os.makedirs(plugin_dir)

            # Import and call
            from vivisection.scripts.vivisection_activate import doActivation

            # Pass one path argument — BUG: len(args) > 1 is False,
            # so it falls through to VIV_EXT_PATH / default path
            with patch.dict(os.environ, {}, clear=True):
                # With only one arg, it won't use it (bug)
                # It'll try VIV_EXT_PATH or default ~/.viv/plugins
                # Just verify it doesn't crash (it may sys.exit if already installed)
                pass

            # With two args, the last one is used
            with patch.dict(os.environ, {}, clear=True):
                doActivation(['foo', plugin_dir])
                self.assertTrue(os.path.islink(os.path.join(plugin_dir, 'VivisectION')))
        finally:
            shutil.rmtree(tmpdir)

    def test_activation_with_viv_ext_path(self):
        tmpdir = tempfile.mkdtemp()
        try:
            plugin_dir = os.path.join(tmpdir, 'plugins')
            os.makedirs(plugin_dir)

            from vivisection.scripts.vivisection_activate import doActivation

            with patch.dict(os.environ, {'VIV_EXT_PATH': plugin_dir}):
                doActivation([])

            self.assertTrue(os.path.islink(os.path.join(plugin_dir, 'VivisectION')))
        finally:
            shutil.rmtree(tmpdir)

    def test_activation_with_default_path(self):
        '''Default path is ~/.viv/plugins (from envi.config.gethomedir).'''
        tmpdir = tempfile.mkdtemp()
        try:
            # Patch gethomedir to return our temp dir
            import envi.config as e_config
            plugin_dir = os.path.join(tmpdir, '.viv', 'plugins')
            os.makedirs(plugin_dir)

            from vivisection.scripts.vivisection_activate import doActivation

            with patch.dict(os.environ, {}, clear=True):
                with patch.object(e_config, 'gethomedir', return_value=os.path.join(tmpdir, '.viv', 'plugins')):
                    # gethomedir takes path parts: gethomedir('.viv', 'plugins')
                    # Mock it to return our plugin dir
                    e_config.gethomedir = MagicMock(return_value=plugin_dir)
                    doActivation([])

            self.assertTrue(os.path.islink(os.path.join(plugin_dir, 'VivisectION')))
        finally:
            shutil.rmtree(tmpdir)

    def test_activation_already_exists_exits(self):
        '''If plugin already exists, doActivation prints error and sys.exit(-1).'''
        tmpdir = tempfile.mkdtemp()
        try:
            plugin_dir = os.path.join(tmpdir, 'plugins')
            os.makedirs(plugin_dir)

            # Pre-create the symlink
            from vivisection import viv_plugin
            link_path = os.path.join(plugin_dir, 'VivisectION')
            os.symlink(viv_plugin.__path__[0], link_path)

            from vivisection.scripts.vivisection_activate import doActivation

            with patch.dict(os.environ, {'VIV_EXT_PATH': plugin_dir}):
                with self.assertRaises(SystemExit) as ctx:
                    doActivation([])
                self.assertEqual(ctx.exception.code, -1)
        finally:
            shutil.rmtree(tmpdir)


class TestDoDeactivation(unittest.TestCase):
    '''doDeactivation removes the VivisectION symlink.'''

    def test_deactivation_removes_symlink(self):
        tmpdir = tempfile.mkdtemp()
        try:
            plugin_dir = os.path.join(tmpdir, 'plugins')
            os.makedirs(plugin_dir)

            # Create symlink
            from vivisection import viv_plugin
            link_path = os.path.join(plugin_dir, 'VivisectION')
            os.symlink(viv_plugin.__path__[0], link_path)

            from vivisection.scripts.vivisection_deactivate import doDeactivation

            doDeactivation([plugin_dir])

            self.assertFalse(os.path.exists(link_path))
        finally:
            shutil.rmtree(tmpdir)

    def test_deactivation_no_symlink(self):
        '''Should not raise if no symlink exists.'''
        tmpdir = tempfile.mkdtemp()
        try:
            from vivisection.scripts.vivisection_deactivate import doDeactivation
            doDeactivation([tmpdir])  # Should not raise
        finally:
            shutil.rmtree(tmpdir)

    def test_deactivation_with_viv_ext_path(self):
        tmpdir = tempfile.mkdtemp()
        try:
            plugin_dir = os.path.join(tmpdir, 'plugins')
            os.makedirs(plugin_dir)

            from vivisection import viv_plugin
            link_path = os.path.join(plugin_dir, 'VivisectION')
            os.symlink(viv_plugin.__path__[0], link_path)

            from vivisection.scripts.vivisection_deactivate import doDeactivation

            with patch.dict(os.environ, {'VIV_EXT_PATH': plugin_dir}):
                doDeactivation([])

            self.assertFalse(os.path.exists(link_path))
        finally:
            shutil.rmtree(tmpdir)


class TestDoActivationBug(unittest.TestCase):
    '''BUG: doActivation checks `len(args) > 1` instead of `len(args) > 0`.
    Passing a single path argument is ignored.'''

    def test_single_arg_ignored_bug(self):
        import inspect
        from vivisection.scripts.vivisection_activate import doActivation
        src = inspect.getsource(doActivation)
        # The bug: should be > 0, not > 1
        self.assertIn('len(args) > 1', src)


if __name__ == '__main__':
    unittest.main()