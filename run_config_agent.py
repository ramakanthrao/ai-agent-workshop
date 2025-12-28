#!/usr/bin/env python3
"""
Script to run the agent with a configuration file for directory analysis and bug fixing.
"""

import json
import sys
import subprocess
import os

def main():
    config_path = r"d:\projects\ai\code-summarizer-mcp\configs\directory_analysis_config.json"
    
    # Load the configuration
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print("=" * 80)
    print("CONFIGURATION-DRIVEN CODE ANALYSIS AND FIX")
    print("=" * 80)
    print(f"\nLoaded configuration from: {config_path}")
    print(f"User request: {config.get('user_request')}")
    print(f"Analysis scope: {config.get('analysis_scope')}")
    print(f"File pattern: {config.get('file_pattern')}")
    print(f"Total actions: {len(config.get('actions', []))}")
    
    # Create a temporary request string that tells the agent to load this config
    request = f"""
    Load and execute the following action plan:
    {json.dumps(config.get('actions', []), indent=2)}
    
    Analysis scope: {config.get('analysis_scope')}
    File pattern: {config.get('file_pattern')}
    User request: {config.get('user_request')}
    
    Follow this exact action plan to analyze and fix code issues in Python files.
    """
    
    print("\n" + "=" * 80)
    print("Starting Agent with Configuration...")
    print("=" * 80 + "\n")
    
    # Run the agent with the request
    agent_script = r"d:\projects\ai\code-summarizer-mcp\src\agent\agent.py"
    
    # Use a subprocess with echo to provide input
    process = subprocess.Popen(
        [sys.executable, agent_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=r"d:\projects\ai\code-summarizer-mcp"
    )
    
    # Provide the request and yes confirmation
    stdout, stderr = process.communicate(input=f"{request}\ny\n")
    
    print(stdout)
    if stderr:
        print("STDERR:", stderr)
    
    sys.exit(process.returncode)

if __name__ == "__main__":
    main()
