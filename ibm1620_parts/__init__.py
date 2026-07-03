"""Compatibility package shim for running `python -m ibm1620_parts.cli` from repo root."""

from pathlib import Path


_PACKAGE_DIR = Path(__file__).resolve().parent
_SRC_PACKAGE_DIR = _PACKAGE_DIR.parent / "src" / "ibm1620_parts"

__path__ = [str(_PACKAGE_DIR)]
if _SRC_PACKAGE_DIR.exists():
    __path__.append(str(_SRC_PACKAGE_DIR))