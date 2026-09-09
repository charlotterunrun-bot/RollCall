"""Make the PySide6 wheel's sibling Qt DLLs visible before QtGui imports."""
import os
import sys

if sys.platform.startswith("win"):
    _pyside = os.path.join(sys._MEIPASS, "PySide6")
    _shiboken = os.path.join(sys._MEIPASS, "shiboken6")
    sys.path.insert(0, _pyside)
    _dll_handles = getattr(sys, "_rollcall_dll_handles", [])
    for _directory in (_pyside, _shiboken, sys._MEIPASS):
        if hasattr(os, "add_dll_directory"):
            _dll_handles.append(os.add_dll_directory(_directory))
    sys._rollcall_dll_handles = _dll_handles
    os.environ["PATH"] = os.pathsep.join((_pyside, _shiboken, sys._MEIPASS, os.environ.get("PATH", "")))
