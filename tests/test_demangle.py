'''
test_demangle.py - tests for vivisection.demangle

demangle() talks to demangler.com over HTTP.  We mock ``requests.post`` so
the tests run offline.  Also exercises :class:`DemangleException`.
'''
import unittest
from unittest.mock import patch, MagicMock

import vivisection.demangle as ion_demangle
from vivisection.demangle import demangle, DemangleException


class TestDemangle(unittest.TestCase):
    def test_plain_name_returned_as_is(self):
        '''demangle('plain_name') returns 'plain_name' (no _Z or @).'''
        self.assertEqual(demangle('plain_name'), 'plain_name')

    @patch('vivisection.demangle.requests.post')
    def test_z_prefix_calls_post(self, mock_post):
        '''demangle with _Z prefix should call requests.post.'''
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'demangled_name'
        mock_post.return_value = mock_resp

        result = demangle('_ZN3foo3barEv')
        self.assertEqual(result, 'demangled_name')
        self.assertTrue(mock_post.called)

    @patch('vivisection.demangle.requests.post')
    def test_at_sign_calls_post(self, mock_post):
        '''demangle with @ should call requests.post.'''
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'demangled_at'
        mock_post.return_value = mock_resp

        result = demangle('?func@yacc@@')
        self.assertEqual(result, 'demangled_at')
        self.assertTrue(mock_post.called)

    @patch('vivisection.demangle.requests.post')
    def test_non_200_raises_demangle_exception(self, mock_post):
        '''DemangleException when status != 200.'''
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_post.return_value = mock_resp

        with self.assertRaises(DemangleException):
            demangle('_Zname')


class TestDemangleException(unittest.TestCase):
    def test_repr(self):
        '''DemangleException repr contains the response.'''
        resp = MagicMock()
        resp.status_code = 500
        e = DemangleException(resp)
        self.assertIs(e.resp, resp)
        r = repr(e)
        self.assertIn('Failed access to demangler.com', r)

    def test_is_exception_subclass(self):
        self.assertTrue(issubclass(DemangleException, Exception))


if __name__ == '__main__':
    unittest.main()