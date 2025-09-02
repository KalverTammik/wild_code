#!/usr/bin/env python3
"""Test script to verify search functionality works."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from utils.GraphQLQueryLoader import GraphQLQueryLoader
    print("✓ GraphQLQueryLoader import successful")

    # Test instantiation
    loader = GraphQLQueryLoader()
    print("✓ GraphQLQueryLoader instantiation successful")

    # Test loading search query
    query = loader.load_query("user", "search.graphql")
    print(f"✓ Search query loaded: {bool(query)}")
    if query:
        print(f"Query length: {len(query)} characters")

    from utils.api_client import APIClient
    print("✓ APIClient import successful")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
