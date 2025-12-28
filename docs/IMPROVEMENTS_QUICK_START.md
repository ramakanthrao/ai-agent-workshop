# Quick Start Guide - Improved Agent

## What Was Fixed

The agent has been improved to prevent and catch malformed action plans before execution.

### Issue: LLM Generated Invalid Action Plans
- ❌ Using wrong tools for the input type (e.g., `list_files_in_directory` on a `.py` file)
- ❌ Missing required parameters in tool calls
- ❌ Invalid action sequences that didn't make logical sense

### Solution: Two-Part Fix

#### Part 1: Improved System Prompt
Enhanced the LLM's instructions with:
- **Explicit workflow examples** for files vs directories
- **Parameter requirements** clearly documented for each tool
- **Common mistakes** highlighted with "NEVER..." rules
- **Step-by-step sequences** showing correct order of operations

#### Part 2: Action Plan Validation
Added validator that:
- ✅ Checks for required parameters on each tool
- ✅ Detects when wrong tools are used for path types
- ✅ Prevents execution of invalid plans
- ✅ Provides helpful error messages

## How to Use

### Run the Agent
```bash
cd d:\projects\ai\code-summarizer-mcp
python src/agent/agent.py
```

### What to Expect
1. **Tool Discovery**: Agent finds and lists available tools
2. **User Request**: Enter what you want to analyze/fix
3. **Action Plan Generation**: LLM creates an action plan with improved guidance
4. **Validation**: Automatic validation checks the plan for errors:
   - ✅ Shows green checkmark if plan is valid
   - ❌ Shows errors and blocks execution if plan is invalid
5. **Execution**: If valid, plan is executed step by step

### Example Interaction

```
What would you like me to do? Analyze sample/tools.py for bugs in the multiply function

[Analyzing Request...]

Analysis Result:
{
  "analysis": "User wants to analyze a specific Python file for problematic functions",
  "actions": [
    {"tool": "list_functions_in_file", "params": {"file_path": "sample/tools.py"}, ...},
    {"tool": "get_function_source", "params": {"file_path": "sample/tools.py", "function_name": "multiply"}, ...},
    {"tool": "ask_llm_to_analyze_code", "params": {"original_code": "..."}, ...}
  ]
}

[Validating Action Plan...]
✅ Action plan validation passed!

Do you want to proceed with this plan? (yes/no): yes

--- Executing Action Plan ---
[Step 1] List all functions in the file
  Tool: list_functions_in_file
  Result: add, subtract, multiply, divide

[Step 2] Extract the multiply function
  Tool: get_function_source
  Result: def multiply(a, b):
    return a - b  # BUG: Should be a * b

[Step 3] Analyze the function for issues
  Tool: ask_llm_to_analyze_code
  Result: The function has a logic error. It returns a - b instead of a * b.
```

## Test the Validation

Run the validation test suite:
```bash
python test_improved_agent.py
```

Expected output: All 6 tests passing ✅

## Test Different Scenarios

Run the workflow example:
```bash
python test_agent_workflow.py
```

Shows all valid and invalid action plan scenarios.

## Files Modified

| File | Changes |
|------|---------|
| `src/mcp/llm_mcp.py` | Enhanced system prompt in `analyze_request()` function |
| `src/agent/agent.py` | Added `validate_action_plan()` function and integrated validation |
| `test_improved_agent.py` | NEW: Comprehensive validation tests (6 tests, all passing) |
| `test_agent_workflow.py` | NEW: Workflow examples and scenarios |
| `doc/IMPROVEMENTS.md` | Detailed documentation of changes |

## Key Improvements

### System Prompt Changes

**Before:**
```
"If the path ends with .py, it's a FILE - use get_function_source to extract functions"
```

**After:**
```
"CRITICAL RULES FOR ACTION PLANNING:
1. PATHS: If path ends with .py it's a FILE. If it's a folder, it's a DIRECTORY.
2. FILE ANALYSIS WORKFLOW:
   - FIRST: Use list_functions_in_file(file_path)
   - THEN: Use get_function_source(file_path, function_name)
   - Note: get_function_source REQUIRES BOTH parameters
3. DIRECTORY ANALYSIS WORKFLOW:
   - FIRST: Use list_files_in_directory(directory_path)
   - THEN: For each file, use list_functions_in_file(file_path)
4. REFACTORING WORKFLOW:
   - FIRST: Extract with get_function_source()
   - THEN: Fix with ask_llm_to_refactor()
   - FINALLY: Write with write_back_to_file()
5. NEVER use list_files_in_directory on a .py file
6. NEVER call get_function_source without function_name
7. ALWAYS provide complete file paths"
```

### Validation Added

```python
def validate_action_plan(actions):
    """Validates action plan for common errors"""
    errors = []
    warnings = []
    
    for each action:
        - Check required parameters exist
        - Detect path type mismatches
        - Warn about suspicious configs
    
    return errors, warnings
```

### Integration in Agent

```python
# In run_agent():
errors, warnings = validate_action_plan(action_plan.get('actions', []))

if errors:
    print("\n❌ VALIDATION ERRORS FOUND:")
    for error in errors:
        print(f"  - {error}")
    print("\nAction plan is invalid. Cancelling execution.")
    return

if warnings:
    print("\n⚠️  VALIDATION WARNINGS:")
    for warning in warnings:
        print(f"  - {warning}")

print("✅ Action plan validation passed!")
```

## Validation Examples

### Valid Plan ✅
```json
{
  "tool": "list_functions_in_file",
  "params": {"file_path": "sample/tools.py"}
}
→ "list_functions_in_file" with "file_path" ✅

{
  "tool": "get_function_source",
  "params": {"file_path": "sample/tools.py", "function_name": "multiply"}
}
→ Both required parameters present ✅
```

### Invalid Plan ❌
```json
{
  "tool": "list_files_in_directory",
  "params": {"directory_path": "sample/tools.py"}
}
→ ERROR: Path ends in .py (it's a file, not directory)
→ Suggestion: Use list_functions_in_file instead ❌

{
  "tool": "get_function_source",
  "params": {"file_path": "sample/tools.py"}
}
→ ERROR: Missing required parameter 'function_name' ❌
```

## Troubleshooting

### "VALIDATION ERRORS FOUND"
The LLM generated an invalid action plan. Check the error messages:
- If it says "missing parameter" → LLM forgot a required field
- If it says "called with file path" → LLM used wrong tool for input type
- If it says "missing required parameter" → Add that field to tool call

### Common LLM Mistakes (Now Caught)
1. ❌ Using `list_files_in_directory` on a `.py` file → Use `list_functions_in_file` instead
2. ❌ Calling `get_function_source` without `function_name` → Add the function name
3. ❌ Calling `write_back_to_file` without `new_code` → Add the refactored code
4. ❌ Calling `ask_llm_to_refactor` without `original_code` → Provide the source code

All of these are now caught by validation and prevented from executing.

## Next Steps

1. **Run the agent**: `python src/agent/agent.py`
2. **Try requests like**:
   - "Analyze sample/tools.py for bugs"
   - "Fix the multiply function in sample/tools.py"
   - "Analyze all Python files in the sample directory"
3. **Observe**: Better action plans due to improved system prompt
4. **Trust**: Invalid plans are caught and stopped automatically

## Performance Impact

- **Validation time**: <1ms per action plan
- **Memory overhead**: Minimal (just checking parameters)
- **User experience**: Better (errors caught before execution)

## Future Improvements

Potential enhancements:
- Interactive plan correction (let user fix invalid steps)
- Learning from past successful plans (add to system prompt)
- More specific error messages with auto-fix suggestions
- Retry with refined prompt if initial plan invalid
