#!/usr/bin/env python3
"""Test script to check LM Studio connectivity and available models."""

import requests
import json

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODELS_URL = "http://localhost:1234/v1/models"

print("=" * 60)
print("Testing LM Studio Connection")
print("=" * 60)

# Test 1: Check if LM Studio is running
print("\n[Test 1] Checking LM Studio availability...")
try:
    response = requests.get("http://localhost:1234/v1/models", timeout=120)
    print(f"✓ LM Studio is running (Status: {response.status_code})")
except Exception as e:
    print(f"✗ LM Studio is NOT running: {e}")
    exit(1)

# Test 2: List available models
print("\n[Test 2] Listing available models...")
try:
    response = requests.get(MODELS_URL, timeout=10)
    response.raise_for_status()
    models = response.json()
    print(f"✓ Available models:")
    for model in models.get('data', []):
        print(f"  - {model['id']}")
    
    if not models.get('data'):
        print("✗ No models available in LM Studio!")
        exit(1)
        
except Exception as e:
    print(f"✗ Failed to list models: {e}")
    exit(1)

# Test 3: Try a simple completion request
print("\n[Test 3] Testing chat completion...")
model_id = models['data'][0]['id']
payload = {
    "model": model_id,
    "messages": [
        {"role": "user", "content": "Say 'hello'"}
    ],
    "temperature": 0.7
}

print(f"  Model: {model_id}")
print(f"  Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(LM_STUDIO_URL, json=payload, timeout=120)
    print(f"  Response status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"✗ Error: {response.text}")
    else:
        content = response.json()['choices'][0]['message']['content']
        print(f"✓ Chat completion works!")
        print(f"  Response: {content}")
        
except Exception as e:
    print(f"✗ Chat completion failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)
