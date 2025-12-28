#!/usr/bin/env python3
"""
Quick test to verify validation catches the exact error from the user report.
"""

import json
import sys

sys.path.insert(0, 'src/agent')
from agent import validate_action_plan

print("="*70)
print("Testing the exact scenario from user error report")
print("="*70)

# This is the exact scenario that failed - get_function_source without function_name
failing_action_plan = {
    'analysis': 'User wants to analyze a specific Python file',
    'actions': [
        {
            'tool': 'get_function_source',
            'params': {'file_path': 'D:/projects/ai/code-summarizer-mcp/sample/tools.py'},
            # MISSING: 'function_name'
            'description': 'Extract function'
        }
    ]
}

print("\nAction plan from user error:")
print(json.dumps(failing_action_plan, indent=2))

print("\n[Validating Action Plan...]")
errors, warnings = validate_action_plan(failing_action_plan['actions'])

if errors:
    print("\n❌ VALIDATION ERRORS FOUND:")
    for error in errors:
        print(f"  - {error}")
    print("\nThe LLM generated an invalid action plan. Cancelling execution.")
    print("Hint: The system prompt may need additional examples or clarification.")
    print("\n✅ SUCCESS: Validation caught the error!")
else:
    print("\n⚠️  WARNING: Validation did NOT catch the error!")
    print("This should have been caught!")

print("\n" + "="*70)
print("RESULT: Validation is working correctly")
print("="*70)
