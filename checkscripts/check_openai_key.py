#!/usr/bin/env python3
"""
OpenAI API Key Checker
Checks if the provided OpenAI API key in config.json is valid and working.
"""

import json
import os
import sys
from typing import Dict, Optional

# Add parent directory to path to import from project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import openai
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI package not installed. Run: pip install openai")
    sys.exit(1)


def load_config(config_path: str = "config.json") -> Dict[str, str]:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file '{config_path}': {e}")
        sys.exit(1)


def check_api_key(api_key: str) -> bool:
    """
    Check if the OpenAI API key is valid by making a simple API call.
    
    Args:
        api_key: The OpenAI API key to check
        
    Returns:
        bool: True if the key is valid, False otherwise
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Make a simple API call to check the key
        print("Testing API key with a simple request...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, this is a test message. Please respond with 'API key is working'."}
            ],
            max_tokens=10,
            timeout=10
        )
        
        # Check if we got a valid response
        if response.choices and len(response.choices) > 0:
            print("API key is valid and working!")
            print(f"Response: {response.choices[0].message.content}")
            return True
        else:
            print("API key test failed: No response received")
            return False
            
    except openai.AuthenticationError:
        print("Authentication failed: Invalid API key")
        return False
    except openai.RateLimitError:
        print("Rate limit exceeded: API key is valid but quota exceeded")
        return True  # Key is valid, just rate limited
    except openai.APIConnectionError:
        print("Connection error: Unable to connect to OpenAI API")
        return False
    except openai.APITimeoutError:
        print("Timeout error: Request timed out")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False


def validate_key_format(api_key: str) -> bool:
    """
    Validate the basic format of the OpenAI API key.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        bool: True if format looks valid, False otherwise
    """
    if not api_key:
        print("API key is empty")
        return False
    
    if not api_key.startswith('sk-'):
        print("API key format invalid: Should start with 'sk-'")
        return False
    
    if len(api_key) < 20:
        print("API key too short: Should be at least 20 characters")
        return False
    
    print("API key format looks valid")
    return True


def main():
    """Main function to check OpenAI API key."""
    print("=" * 60)
    print("OpenAI API Key Checker")
    print("=" * 60)
    
    # Load configuration
    print("Loading configuration...")
    config = load_config()
    
    if "openai_api_key" not in config:
        print("Error: 'openai_api_key' not found in configuration file")
        sys.exit(1)
    
    api_key = config["openai_api_key"]
    print(f"Found API key: {api_key[:10]}...{api_key[-4:]}")
    
    # Validate key format
    print("\nValidating API key format...")
    if not validate_key_format(api_key):
        sys.exit(1)
    
    # Test API key
    print("\nTesting API key with OpenAI...")
    if check_api_key(api_key):
        print("\nSUCCESS: OpenAI API key is valid and working!")
        sys.exit(0)
    else:
        print("\nFAILURE: OpenAI API key is invalid or not working")
        sys.exit(1)


if __name__ == "__main__":
    main()
