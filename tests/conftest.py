"""Pytest configuration: make the project root importable so tests can do
`from utility.vault import ...` and `from tests import nist_sp800_22`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
