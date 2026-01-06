"""
Test OpenAI API Connection
Simple script to verify that the OpenAI API is accessible.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables - try multiple locations
env_paths = [
    Path(__file__).parent.parent / ".env",
    Path(__file__).parent.parent / ".env.local",
    Path.home() / ".openai" / ".env",
]

env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[INFO] Loaded .env from: {env_path}")
        env_loaded = True
        break

if not env_loaded:
    # Try loading from current directory
    load_dotenv()
    print("[INFO] Attempting to load .env from current directory")

# Get API key - try multiple sources
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    # Try alternative environment variable names
    api_key = os.getenv("OPENAI_KEY") or os.getenv("API_KEY")

# Try loading from config.json (like test_single_scenario_quick.py does)
if not api_key:
    config_path = Path(__file__).parent.parent / "config.json"
    if config_path.exists():
        try:
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            api_key = config.get("openai_api_key")
            if api_key:
                print(f"[INFO] Loaded API key from config.json")
        except Exception as e:
            print(f"[WARN] Failed to load config.json: {e}")
    
if not api_key:
    print("[ERROR] OPENAI_API_KEY not found in environment variables or config.json")
    print("Please set OPENAI_API_KEY in:")
    print("  1. .env file")
    print("  2. Environment variables")
    print("  3. config.json (with 'openai_api_key' field)")
    print("\nTried locations:")
    for env_path in env_paths:
        print(f"  - {env_path}")
    config_path = Path(__file__).parent.parent / "config.json"
    print(f"  - {config_path}")
    sys.exit(1)

print("=" * 80)
print("Testing OpenAI API Connection")
print("=" * 80)
print(f"API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
print()

# Test 1: Initialize ChatOpenAI
print("[Test 1] Initializing ChatOpenAI client...")
try:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key,
        temperature=0.7,
        timeout=30.0
    )
    print("[OK] ChatOpenAI client initialized successfully")
except Exception as e:
    print(f"[ERROR] Failed to initialize ChatOpenAI: {e}")
    sys.exit(1)

# Test 2: Simple API call
print()
print("[Test 2] Making a simple API call...")
try:
    response = llm.invoke("Say 'Hello, API connection test successful!' in one sentence.")
    print(f"[OK] API call successful!")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"[ERROR] API call failed: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test with timeout
print()
print("[Test 3] Testing with timeout settings...")
try:
    llm_with_timeout = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key,
        temperature=0.7,
        timeout=60.0
    )
    response = llm_with_timeout.invoke("Count from 1 to 3.")
    print(f"[OK] API call with timeout successful!")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"[ERROR] API call with timeout failed: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("[SUCCESS] All API connection tests passed!")
print("=" * 80)


