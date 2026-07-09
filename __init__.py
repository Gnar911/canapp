"""canapp package

Editable-install marker. The real package code lives under ``src/canapp``; we
extend ``__path__`` so ``canapp`` and its subpackages (vm, screens, pyqt, ...)
resolve to the src layout, mirroring the pattern used by ``file_service``.
"""

import os

_here = os.path.dirname(__file__)
_src_pkg = os.path.join(_here, "src", "canapp")

if os.path.isdir(_src_pkg) and _src_pkg not in __path__:
    __path__.insert(0, _src_pkg)

__all__ = []
