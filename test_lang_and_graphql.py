#!/usr/bin/env python3
"""Test script to verify LanguageManager and GraphQLQueryLoader work together."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from languages.language_manager import LanguageManager
    print("✓ LanguageManager import successful")

    # Test instantiation
    lang_manager = LanguageManager()
    print("✓ LanguageManager instantiation successful")

    from utils.GraphQLQueryLoader import GraphQLQueryLoader
    print("✓ GraphQLQueryLoader import successful")

    # Test instantiation with language manager
    loader = GraphQLQueryLoader(lang_manager)
    print("✓ GraphQLQueryLoader instantiation successful")

    # Test loading search query
    query = loader.load_query("user", "search.graphql")
    print(f"✓ Search query loaded: {bool(query)}")
    if query:
        print(f"Query length: {len(query)} characters")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
