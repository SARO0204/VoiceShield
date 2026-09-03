"""
PyTest configuration for VoiceShield.
Ensures workspace root is in sys.path.
"""

import os
import sys

# Insert repository root directory to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
