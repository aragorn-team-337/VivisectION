'''
test_vivisection_core.py - tests for vivisection/__init__.py

This exercises the ``NoWorkspace`` exception and the ``VivisectION`` class,
including several documented bugs:

* BUG #3: ``NoWorkspace()`` with no args raises ``TypeError`` because
  ``__init__`` requires a ``msg`` argument (line 38 calls ``NoWorkspace()``
  without one).
* BUG #2: ``VivisectION(vw)`` raises ``NameError`` because ``NinjaEmulator``
  is referenced in ``resetEmu`` but never imported (line 40).
* BUG #1 (follow-on): ``resetEmu`` calls ``NoWorkspace()`` without a ``msg``
  argument, triggering the ``TypeError`` above.
'''
import unittest

from vivisection import NoWorkspace, VivisectION


class TestNoWorkspace(unittest.TestCase):
    def test_is_exception_subclass(self):
        '''NoWorkspace must be an Exception subclass.'''
        self.assertTrue(issubclass(NoWorkspace, Exception))

    def test_msg_attribute(self):
        '''NoWorkspace('msg').msg == 'msg'.'''
        e = NoWorkspace('msg')
        self.assertEqual(e.msg, 'msg')

    def test_repr(self):
        '''repr(NoWorkspace('msg')) == "NoWorkspace: 'msg'".'''
        self.assertEqual(repr(NoWorkspace('msg')), "NoWorkspace: 'msg'")

    def test_no_args_raises_typeerror(self):
        '''
        BUG #3: NoWorkspace() without args raises TypeError because the
        __init__ signature requires ``msg``.
        '''
        with self.assertRaises(TypeError):
            NoWorkspace()


class TestVivisectION(unittest.TestCase):
    def test_no_vw_sets_none(self):
        '''VivisectION() with no vw should set vw=None and nemu=None.'''
        vion = VivisectION()
        self.assertIsNone(vion.vw)
        self.assertIsNone(vion.nemu)

    def test_with_vw_raises_nameerror(self):
        '''
        With BUG #2 fixed, NinjaEmulator is imported, so VivisectION(vw)
        no longer raises NameError.  (It may raise other errors due to the
        mock vw, but NameError should not occur.)
        '''
        from unittest.mock import MagicMock
        vw = MagicMock()
        try:
            VivisectION(vw)
        except NameError:
            self.fail('NameError should not be raised now that NinjaEmulator is imported')
        except Exception:
            # Other exceptions are acceptable since vw is a mock and
            # NinjaEmulator may require a real workspace.
            pass

    def test_setemuopts_stores_all_opts(self):
        '''setEmuOpts should store all the opts in emuopts.'''
        vion = VivisectION()
        vion.setEmuOpts(start=0x1000, verbose=True, fakePEB=True,
                        hookfuncsbyname=True, extra='x')
        self.assertEqual(vion.emuopts['start'], 0x1000)
        self.assertTrue(vion.emuopts['verbose'])
        self.assertTrue(vion.emuopts['fakePEB'])
        self.assertTrue(vion.emuopts['hookfuncsbyname'])
        self.assertEqual(vion.emuopts['extra'], 'x')

    def test_setemuopt_sets_individual(self):
        '''setEmuOpt should set an individual opt in emuopts.'''
        vion = VivisectION()
        vion.setEmuOpts()
        vion.setEmuOpt('foo', 'bar')
        self.assertEqual(vion.emuopts['foo'], 'bar')

    def test_setvw_sets_vw(self):
        '''setVw should set the vw attribute.'''
        from unittest.mock import MagicMock
        vion = VivisectION()
        vw = MagicMock()
        vion.setVw(vw)
        self.assertIs(vion.vw, vw)

    def test_resetemu_without_vw_raises_typeerror(self):
        '''
        With BUG #1/#3 fixed, resetEmu without a vw raises NoWorkspace
        (with a msg argument) instead of TypeError.
        '''
        vion = VivisectION()
        with self.assertRaises(NoWorkspace):
            vion.resetEmu()


if __name__ == '__main__':
    unittest.main()