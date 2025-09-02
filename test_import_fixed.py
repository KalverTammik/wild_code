#!/usr/bin/env python3
"""Test script to verify HeaderWidget imports work correctly."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from widgets.HeaderWidget import HeaderWidget, SearchResultsWidget
    print("✓ Import successful - HeaderWidget and SearchResultsWidget imported without errors")
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Other error: {e}")
    import traceback
    traceback.print_exc()
