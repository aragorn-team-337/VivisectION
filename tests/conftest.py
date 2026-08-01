'''
conftest.py for the VivisectION test suite.

VivisectION imports ``PyQt5`` but only ``PyQt6`` is installed in this
environment.  This shim aliases the PyQt6 submodules under the ``PyQt5``
name *before* any VivisectION module is imported, so that the rest of the
test-suite can ``import vivisection.<mod>`` normally.

It also forces the Qt platform to ``offscreen`` so that GUI dependent
imports do not try to talk to a real display server.
'''
import os
import sys

# Force the offscreen Qt platform *before* any Qt/QPA code runs.
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


def _install_pyqt5_shim():
    '''Alias PyQt6 sub-modules under the PyQt5 names VivisectION expects.'''
    try:
        import PyQt6
    except ImportError:
        # If PyQt6 is not installed there is nothing to alias; the GUI
        # dependent tests are expected to skip on their own.
        return

    # Top-level alias:  ``import PyQt5`` -> PyQt6
    sys.modules.setdefault('PyQt5', PyQt6)

    for sub in ('QtCore', 'QtGui', 'QtWidgets', 'QtNetwork', 'QtSvg', 'QtTest'):
        try:
            real = __import__('PyQt6.' + sub)
            modname = 'PyQt6.' + sub
            sys.modules.setdefault('PyQt5.' + sub, sys.modules[modname])
        except ImportError:
            continue


_install_pyqt5_shim()