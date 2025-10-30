"""
Sistema Auditor Fiscal - Módulo Principal
"""
import sys
from pathlib import Path

# Garantir que src está no path do Python
_current_file = Path(__file__)
_src_dir = _current_file.parent

if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
