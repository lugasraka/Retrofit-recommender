#!/usr/bin/env python3
"""Test script to verify .env file is loaded correctly"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the token
token = os.getenv("HUGGINGFACE_API_TOKEN", "")

print("=" * 50)
print("Environment Variable Test")
print("=" * 50)

if token:
    if token == "your_token_here":
        print("❌ Token found but still has placeholder value")
        print("   Please replace 'your_token_here' with your actual token in .env file")
    else:
        # Mask the token for security
        masked_token = token[:7] + "..." + token[-4:] if len(token) > 11 else "***"
        print(f"✓ Token successfully loaded: {masked_token}")
        print(f"✓ Token length: {len(token)} characters")
        print(f"✓ Token starts with 'hf_': {token.startswith('hf_')}")
else:
    print("❌ No token found in environment variables")
    print("   Make sure HUGGINGFACE_API_TOKEN is set in your .env file")

print("=" * 50)
