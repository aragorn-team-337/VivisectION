'''
test_errno.py - tests for vivisection.errno

errno.py is intentionally tiny: it just defines ``EINVAL = 22``.  These
tests pin that contract and exercise the module-level constant.
'''
import unittest

from vivisection.errno import EINVAL


class TestErrno(unittest.TestCase):
    def test_einval_value(self):
        '''EINVAL should be exactly 22.'''
        self.assertEqual(EINVAL, 22)

    def test_einval_is_int(self):
        '''EINVAL should be an int (not a str or anything else).'''
        self.assertIsInstance(EINVAL, int)


if __name__ == '__main__':
    unittest.main()