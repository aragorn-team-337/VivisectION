'''
test_emulation.py - tests for vivisection.emulation

Covers DaybreakMonitor init and the checkIfInteresting / addImport /
addString / addUnicode helpers, including several documented bugs:

* BUG #4: checkIfInteresting calls ``self.addString(op.va)`` with the
  wrong argument count (addString requires ``(va, val)``).
* BUG #5: addImport uses a ``print`` with a format string bug
  (``"Adding Import: %r" % item`` is fine, but the documented bug is the
  print format in the ``addImport`` tuple handling path).
* BUG #6: emulation.py references ``vivisect.LOC_IMPORT`` which does not
  exist at the top level of the vivisect package (it lives in
  ``vivisect.const``), so the ``ltype == vivisect.LOC_IMPORT`` branch
  raises ``AttributeError``.
'''
import unittest
from unittest.mock import MagicMock

import vivisect
import vivisection.emulation as ion_emulation  # noqa: F401
from vivisection.emulation import DaybreakMonitor


class TestDaybreakMonitorInit(unittest.TestCase):
    def _make_monitor(self):
        vw = MagicMock()
        fva = 0x401000
        m = DaybreakMonitor(vw, fva)
        return m, vw, fva

    def test_init_attributes(self):
        '''DaybreakMonitor init sets all the documented attributes.'''
        m, vw, fva = self._make_monitor()
        self.assertEqual(m.trackPointers, False)
        self.assertEqual(m.valist, [])
        self.assertEqual(m.strings, [])
        self.assertEqual(m.imports, [])
        self.assertEqual(m.functions, [])
        self.assertEqual(m.dynbranches, {})
        self.assertEqual(m.stack, [(fva, fva)])
        self.assertTrue(m.stopAtModuleBreak)

    def test_init_immediates_is_defaultdict(self):
        m, vw, fva = self._make_monitor()
        import collections
        self.assertIsInstance(m.immediates, collections.defaultdict)

    def test_init_graph_exists(self):
        m, vw, fva = self._make_monitor()
        self.assertIsNotNone(m.graph)


class TestCheckIfInteresting(unittest.TestCase):
    def _make_monitor(self):
        vw = MagicMock()
        fva = 0x401000
        return DaybreakMonitor(vw, fva), vw, fva

    def test_none_vals_returns_false(self):
        '''checkIfInteresting with None vals returns False.'''
        m, vw, fva = self._make_monitor()
        op = MagicMock()
        self.assertFalse(m.checkIfInteresting(MagicMock(), op, None))

    def test_valid_pointer_to_string_calls_addstring_buggy(self):
        '''
        BUG #4: when val is a valid pointer to a probable string and there
        is no Location, checkIfInteresting calls ``self.addString(op.va)``
        with only ONE argument.  addString requires ``(va, val)`` so this
        raises TypeError.
        '''
        m, vw, fva = self._make_monitor()
        op = MagicMock()
        op.va = 0x401000

        vw.isValidPointer.return_value = True
        vw.getLocation.return_value = None
        vw.isProbablyString.return_value = True

        # addString(va) is called with the wrong arg count -> TypeError
        with self.assertRaises(TypeError):
            m.checkIfInteresting(MagicMock(), op, [0x402000])

    def test_loc_import_branch_raises_attributeerror(self):
        '''
        BUG #6: the ``ltype == vivisect.LOC_IMPORT`` branch references
        ``vivisect.LOC_IMPORT`` which does not exist at the top level of
        the vivisect package -> AttributeError.
        '''
        m, vw, fva = self._make_monitor()
        op = MagicMock()
        op.va = 0x401000

        vw.isValidPointer.return_value = True
        # a Location tuple with ltype that would hit the LOC_IMPORT branch
        vw.getLocation.return_value = (0x402000, 4, 9, ('imp', 'foo'))
        # vivisect.LOC_IMPORT does not exist at top level
        self.assertFalse(hasattr(vivisect, 'LOC_IMPORT'))
        with self.assertRaises(AttributeError):
            m.checkIfInteresting(MagicMock(), op, [0x402000])


class TestAddImport(unittest.TestCase):
    def test_addimport_tuple_item(self):
        '''
        BUG #5: addImport does ``print("Adding Import: %r" % item)`` where
        ``item`` is a 3-tuple.  Because ``%`` with a tuple unpacks it as the
        format arguments, the single ``%r`` receives too many args and
        raises ``TypeError: not all arguments converted during string
        formatting``.
        '''
        vw = MagicMock()
        vw.getFunction.return_value = 0x401000
        m = DaybreakMonitor(vw, 0x401000)
        m.starteip = 0x401000
        item = (0x1000, 0x2000, ('kernel32.dll', 'CreateFileW'))
        with self.assertRaises(TypeError):
            m.addImport(item)


class TestAddStringBuggy(unittest.TestCase):
    def test_addstring_wrong_arg_count(self):
        '''
        BUG #4: addString requires two arguments ``(va, val)``.  Calling
        it with one argument raises TypeError.
        '''
        m = DaybreakMonitor(MagicMock(), 0x401000)
        with self.assertRaises(TypeError):
            m.addString(0x1000)

    def test_addstring_two_args_works(self):
        '''addString with the correct (va, val) signature works.'''
        vw = MagicMock()
        vw.readMemString.return_value = b'hello'
        vw.getFunction.return_value = 0x401000
        m = DaybreakMonitor(vw, 0x401000)
        m.starteip = 0x401000
        ret = m.addString(0x1000, 0x2000)
        # returns True on first add
        self.assertTrue(ret)
        self.assertEqual(len(m.strings), 1)


class TestAddUnicodeBuggy(unittest.TestCase):
    def test_addunicode_wrong_arg_count(self):
        '''
        BUG (companion to #4): addUnicode requires two arguments
        ``(va, val)``.  Calling it with one argument raises TypeError.
        '''
        m = DaybreakMonitor(MagicMock(), 0x401000)
        with self.assertRaises(TypeError):
            m.addUnicode(0x1000)

    def test_addunicode_two_args_works(self):
        '''addUnicode with the correct (va, val) signature works.'''
        vw = MagicMock()
        vw.readMemString.return_value = b'h\x00e\x00l\x00l\x00o\x00'
        vw.getFunction.return_value = 0x401000
        m = DaybreakMonitor(vw, 0x401000)
        m.starteip = 0x401000
        ret = m.addUnicode(0x1000, 0x2000)
        self.assertTrue(ret)
        self.assertEqual(len(m.strings), 1)


if __name__ == '__main__':
    unittest.main()