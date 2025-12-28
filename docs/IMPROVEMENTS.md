# Agent Improvements - Validation & Prompt Refinement

## Summary of Changes

This document describes the improvements made to fix issues with LLM action plan generation and add validation to prevent malformed plans from executing.

## Issues Addressed

### Problem 1: LLM Generating Incorrect Action Plans
**Symptom**: LLM was generating action plans that violated its own stated rules:
- Using `list_files_in_directory` on a .py file path
- Missing required parameters like `function_name` in `get_function_source` calls
- Incorrect workflow sequences

**Root Cause**: System prompt rules were too vague and lacked concrete examples. The LLM needed:
1. Explicit workflow examples for different scenarios
2. Clear parameter requirements for each tool
3. Common mistakes highlighted to avoid

**Solution**: Enhanced system prompt with:
- Detailed workflow examples for file vs directory analysis
- Explicit parameter requirements per tool
- Critical rules and pitfalls to avoid
- Step-by-step correct action sequences

### Problem 2: Invalid Action Plans Were Executed
**Symptom**: Agent would attempt to execute malformed action plans, causing cascading failures

**Root Cause**: No validation before execution

**Solution**: Added `validate_action_plan()` function that:
- Checks for required parameters on each tool
- Detects when directory tools are used on files
- Warns when file paths don't match expected extensions
- Prevents execution if critical errors found
- Provides helpful error messages

## Changes Made

### 1. Enhanced System Prompt (`src/mcp/llm_mcp.py`)

**Changed in `analyze_request()` function:**

```python
system_prompt = (
    "... [JSON structure requirements] ...\n\n"
    "CRITICAL RULES FOR ACTION PLANNING:\n"
    "1. PATHS: If path ends with .py it's a FILE. If it's a folder, it's a DIRECTORY.\n"
    "2. FILE ANALYSIS WORKFLOW:\n"
    "   - FIRST: Use list_functions_in_file(file_path) to list all function names\n"
    "   - THEN: Use get_function_source(file_path, function_name) for EACH function\n"
    "   - Note: get_function_source REQUIRES BOTH file_path AND function_name parameters\n"
    "3. DIRECTORY ANALYSIS WORKFLOW:\n"
    "   - FIRST: Use list_files_in_directory(directory_path) to list Python files\n"
    "   - THEN: For each file, use list_functions_in_file(file_path)\n"
    "   - THEN: Extract specific functions as needed\n"
    "4. REFACTORING WORKFLOW:\n"
    "   - FIRST: Extract code with get_function_source()\n"
    "   - THEN: Fix with ask_llm_to_refactor(original_code)\n"
    "   - FINALLY: Write back with write_back_to_file(file_path, function_name, new_code)\n"
    "5. NEVER use list_files_in_directory on a .py file - it's a file, not a directory\n"
    "6. NEVER call get_function_source without function_name parameter\n"
    "7. ALWAYS provide complete file paths in parameters\n\n"
    f"{available_tools}"
)
```

**Key Improvements:**
- Explicit workflow examples for different input types
- Parameter requirements clearly documented
- Common mistakes highlighted ("NEVER...")
- Step-by-step execution order specified
- Emphasis on required parameters

### 2. Added Action Plan Validation (`src/agent/agent.py`)

**New Function: `validate_action_plan(actions)`**

Validates each action in the plan for:
- **Required Parameters**: Checks each tool has all required fields
  - `get_function_source`: requires `file_path` AND `function_name`
  - `write_back_to_file`: requires `file_path`, `function_name`, AND `new_code`
  - `list_files_in_directory`: requires `directory_path`
  - `ask_llm_to_refactor`: requires `original_code`

- **Path Type Mismatches**: Detects when wrong tool is used for path type
  - Warns if `list_files_in_directory` is used with a `.py` file
  - Suggests using `list_functions_in_file` instead

- **File Extension Warnings**: Alerts when file paths don't match expected types
  - Warns if `list_functions_in_file` is used with non-`.py` file

**Returns**: `(errors: list, warnings: list)`
- **Errors**: Critical issues that prevent execution
- **Warnings**: Issues that should be reviewed but don't block execution

### 3. Integrated Validation into Agent (`src/agent/agent.py`)

**Changes to `run_agent()` function:**

Added validation step after action plan generation:

```python
# Validate the action plan
print("\n[Validating Action Plan...]")
errors, warnings = validate_action_plan(action_plan.get('actions', []))

if errors:
    print("\n❌ VALIDATION ERRORS FOUND:")
    for error in errors:
        print(f"  - {error}")
    print("\nThe LLM generated an invalid action plan. Cancelling execution.")
    print("Hint: The system prompt may need additional examples or clarification.")
    return

if warnings:
    print("\n⚠️  VALIDATION WARNINGS:")
    for warning in warnings:
        print(f"  - {warning}")

if not errors:
    print("✅ Action plan validation passed!")
```

**Behavior:**
1. Validates plan immediately after LLM generation
2. Shows validation results to user before execution
3. **Blocks execution** if critical errors found
4. **Warns** for non-critical issues
5. Provides helpful guidance to user about prompt improvements

## Test Results

Created `test_improved_agent.py` with comprehensive validation tests:

```
✅ TEST 1: Valid action plan (should pass) - PASSED
✅ TEST 2: Invalid - list_files_in_directory with .py file (should fail) - PASSED
✅ TEST 3: Invalid - get_function_source missing function_name (should fail) - PASSED
✅ TEST 4: Invalid - write_back_to_file missing parameters (should fail) - PASSED
✅ TEST 5: Invalid - ask_llm_to_refactor missing original_code (should fail) - PASSED
✅ TEST 6: Warning - list_functions_in_file with non-.py file (should warn) - PASSED

ALL TESTS PASSED! ✅
```

## Impact

### Before Improvements
- ❌ LLM generated invalid action plans
- ❌ Invalid plans were executed, causing cascading failures
- ❌ User had no warning about malformed plans
- ❌ Required manual investigation of errors

### After Improvements
- ✅ Enhanced system prompt with explicit workflow examples
- ✅ Validation prevents invalid plans from executing
- ✅ User sees clear error messages before execution
- ✅ Better LLM guidance through detailed rules and examples
- ✅ Validation tests ensure correctness

## Files Modified

1. **`src/mcp/llm_mcp.py`**
   - Enhanced system prompt in `analyze_request()` function
   - Added workflow examples and rules
   - Added parameter requirement documentation

2. **`src/agent/agent.py`**
   - Added `validate_action_plan()` function
   - Integrated validation into `run_agent()`
   - Added user-facing validation feedback

3. **`test_improved_agent.py`** (NEW)
   - Comprehensive validation tests
   - 6 test cases covering various scenarios
   - All tests passing

## Future Improvements

1. **Fallback Prompt Refinement**: If validation fails, could offer refined prompt examples to LLM
2. **Interactive Correction**: Allow user to approve/modify invalid action plans
3. **Tool Usage Analytics**: Track which validation errors occur most frequently
4. **Example Learning**: Use past successful action plans as examples in system prompt
