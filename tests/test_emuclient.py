'''
test_emuclient.py - documents the syntax errors in emuclient.py

emuclient.py has a syntax error on line 52::

    print("runClient(%r, %r, %r)" % (host, port sessid))
                                              ^ missing comma

The module therefore cannot be imported normally; attempting to execute
it raises ``SyntaxError``.  These tests document that bug.

Because ``emuclient.py`` lives inside the ``viv_plugin`` package whose
``__init__.py`` itself fails to import (PyQt5 / QToolBar), we load the file
directly via :mod:`importlib.util` so we isolate the *syntax* error from
the package-level import problems.
'''
import importlib.util
import os
import unittest

_EMUCLIENT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'vivisection', 'viv_plugin', 'emuclient.py',
)


def _load_emuclient():
    '''
    Load emuclient.py from disk as an isolated module (bypassing the
    viv_plugin package __init__) and return the loaded module or raise.
    '''
    spec = importlib.util.spec_from_file_location(
        'emuclient_under_test', _EMUCLIENT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestEmuclientSyntax(unittest.TestCase):
    def test_import_raises_syntaxerror(self):
        '''
        BUG: emuclient.py line 52 has a syntax error (missing comma
        between ``port`` and ``sessid``) so importing/execing the module
        raises SyntaxError.
        '''
        with self.assertRaises(SyntaxError):
            _load_emuclient()

    def test_syntax_error_mentions_line_52(self):
        '''
        The SyntaxError should point at line 52 (the runClient print
        statement).
        '''
        try:
            _load_emuclient()
        except SyntaxError as e:
            self.assertIsNotNone(e.lineno)
            self.assertEqual(e.lineno, 52)
        else:
            self.fail('expected SyntaxError')


if __name__ == '__main__':
    unittest.main()