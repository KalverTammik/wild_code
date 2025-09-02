#!/usr/bin/env python3
"""Test script to debug search functionality."""

import sys
import os
import json

# Add current directory to path for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def load_graphql_query():
    """Load the search GraphQL query directly."""
    query_path = os.path.join(current_dir, "queries", "graphql", "user", "search.graphql")
    if os.path.exists(query_path):
        with open(query_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def load_session_token():
    """Load session token from config or use environment variable."""
    # Try environment variable first
    token = os.environ.get("KAVITRO_API_TOKEN")
    if token:
        return token

    # Try config file
    config_path = os.path.join(current_dir, "config", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("api_token")
        except:
            pass

    return None

def load_api_endpoint():
    """Load API endpoint from config."""
    config_path = os.path.join(current_dir, "config", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("graphql_endpoint", "https://kiisu.kavitro.io/graphql")
        except:
            pass
    return "https://kiisu.kavitro.io/graphql"

try:
    print("=== Testing Search Functionality ===")

    # Load GraphQL query directly
    query = load_graphql_query()
    if not query:
        print("✗ Could not load GraphQL query file")
        sys.exit(1)
    print("✓ GraphQL query loaded successfully")

    # Load API endpoint
    url = load_api_endpoint()
    print(f"✓ Using API endpoint: {url}")

    # Load session token
    token = load_session_token()
    if not token:
        print("✗ No API token found. Please set KAVITRO_API_TOKEN environment variable or add 'api_token' to config.json")
        print("Example: set KAVITRO_API_TOKEN=your_token_here")
        sys.exit(1)
    # Test API call directly
    import requests
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Test different search terms
    test_terms = ["kat", "kah", "uus", "pakk"]

    for test_term in test_terms:
        if len(test_term) >= 3:
            print(f"\n[DEBUG] Testing search term: '{test_term}'")
            variables = {
                "input": {
                    "term": test_term,
                    "types": [
                        "TASKS", "PROJECTS", "PROPERTIES", "CONTACTS",
                        "METERS", "LETTERS", "SUBMISSIONS", "EASEMENTS",
                        "COORDINATIONS", "SPECIFICATIONS", "ORDINANCES",
                        "CONTRACTS", "PRODUCTS", "INVOICES", "EXPENSES", "QUOTES"
                    ],
                    "limit": 5
                }
            }

            payload = {
                "query": query,
                "variables": variables
            }

            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                print(f"[DEBUG] HTTP Status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    if "data" in result and "search" in result["data"]:
                        search_data = result["data"]["search"]
                        total_results = sum(module.get("total", 0) for module in search_data)
                        print(f"[DEBUG] Total results for '{test_term}': {total_results}")

                        # Show detailed results for each module
                        for module in search_data:
                            if module.get("total", 0) > 0:
                                print(f"[DEBUG] '{test_term}' found {module['total']} results in {module['type']}:")
                                for hit in module.get("hits", []):
                                    print(f"[DEBUG]   - {hit.get('title', 'Unknown')} (ID: {hit.get('id', 'N/A')})")

                        if total_results > 0:
                            print(f"✓ Found results with term '{test_term}'!")
                        else:
                            print(f"✗ No results for '{test_term}'")
                    else:
                        print(f"✗ Unexpected response structure for '{test_term}'")
                        print(f"Response: {result}")
                else:
                    print(f"✗ HTTP Error {response.status_code} for '{test_term}'")
                    print(f"Response: {response.text}")

            except Exception as e:
                print(f"✗ Request failed for '{test_term}': {e}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
