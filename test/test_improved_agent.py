#!/usr/bin/env python3
"""
Test script to verify improved agent with better system prompt and validation.
Tests that the agent correctly validates action plans before execution.
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'agent'))

from agent import validate_action_plan

def test_validate_action_plan():
    """Test the validate_action_plan function."""
    
    print("=" * 70)
    print("TEST 1: Valid action plan (should pass)")
    print("=" * 70)
    
    valid_plan = [
        {
            'tool': 'list_functions_in_file',
            'params': {'file_path': 'sample/tools.py'},
            'description': 'List all functions in tools.py'
        },
        {
            'tool': 'get_function_source',
            'params': {'file_path': 'sample/tools.py', 'function_name': 'multiply'},
            'description': 'Extract the multiply function'
        },
        {
            'tool': 'ask_llm_to_analyze_code',
            'params': {'original_code': 'def multiply(a, b):\n    return a - b'},
            'description': 'Analyze the function'
        }
    ]
    
    errors, warnings = validate_action_plan(valid_plan)
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    assert len(errors) == 0, f"Expected no errors, got {errors}"
    print("✅ PASSED\n")
    
    print("=" * 70)
    print("TEST 2: Invalid - list_files_in_directory with .py file (should fail)")
    print("=" * 70)
    
    invalid_plan_1 = [
        {
            'tool': 'list_files_in_directory',
            'params': {'directory_path': 'sample/tools.py'},
            'description': 'This is wrong - tools.py is a file, not a directory'
        }
    ]
    
    errors, warnings = validate_action_plan(invalid_plan_1)
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    assert len(errors) > 0, "Expected validation error for .py file to list_files_in_directory"
    assert 'list_functions_in_file' in errors[0], "Error should suggest list_functions_in_file"
    print("✅ PASSED\n")
    
    print("=" * 70)
    print("TEST 3: Invalid - get_function_source missing function_name (should fail)")
    print("=" * 70)
    
    invalid_plan_2 = [
        {
            'tool': 'get_function_source',
            'params': {'file_path': 'sample/tools.py'},
            'description': 'Extract function - but missing function_name!'
        }
    ]
    
    errors, warnings = validate_action_plan(invalid_plan_2)
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    assert len(errors) > 0, "Expected validation error for missing function_name"
    assert 'function_name' in errors[0], "Error should mention missing function_name"
    print("✅ PASSED\n")
    
    print("=" * 70)
    print("TEST 4: Invalid - write_back_to_file missing parameters (should fail)")
    print("=" * 70)
    
    invalid_plan_3 = [
        {
            'tool': 'write_back_to_file',
            'params': {'file_path': 'sample/tools.py'},
            'description': 'Write back - but missing function_name and new_code!'
        }
    ]
    
    errors, warnings = validate_action_plan(invalid_plan_3)
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    assert len(errors) >= 2, "Expected multiple validation errors"
    assert any('function_name' in e for e in errors), "Error should mention function_name"
    assert any('new_code' in e for e in errors), "Error should mention new_code"
    print("✅ PASSED\n")
    
    print("=" * 70)
    print("TEST 5: Invalid - ask_llm_to_refactor missing original_code (should fail)")
    print("=" * 70)
    
    invalid_plan_4 = [
        {
            'tool': 'ask_llm_to_refactor',
            'params': {},
            'description': 'Refactor - but missing original_code!'
        }
    ]
    
    errors, warnings = validate_action_plan(invalid_plan_4)
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    assert len(errors) > 0, "Expected validation error for missing original_code"
    assert 'original_code' in errors[0], "Error should mention missing original_code"
    print("✅ PASSED\n")
    
    print("=" * 70)
    print("TEST 6: Warning - list_functions_in_file with non-.py file (should warn)")
    print("=" * 70)
    
    warning_plan = [
        {
            'tool': 'list_functions_in_file',
            'params': {'file_path': 'sample/data.txt'},
            'description': 'List functions in a text file'
        }
    ]
    
    errors, warnings = validate_action_plan(warning_plan)
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    assert len(errors) == 0, "Should have no errors"
    assert len(warnings) > 0, "Expected a warning for non-.py file"
    print("✅ PASSED\n")
    
    print("=" * 70)
    print("ALL TESTS PASSED! ✅")
    print("=" * 70)

if __name__ == '__main__':
    test_validate_action_plan()
