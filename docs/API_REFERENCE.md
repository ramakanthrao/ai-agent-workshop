# API Reference & Configuration Guide

## MCP Tools Overview

### LLM MCP Server Tools

#### `analyze_request(user_prompt: str) -> str`
Analyzes a user's request and returns a structured action plan.

**Parameters:**
- `user_prompt` (str): The user's request describing what code work needs to be done

**Returns:**
- JSON string containing:
  - `analysis`: Brief summary of what the user wants
  - `actions`: List of tools to call with parameters
  - `loop_required`: Boolean indicating if iterations are needed
  - `loop_condition`: Description of loop conditions

**Example:**
```python
response = await session.call_tool("analyze_request", {
    "user_prompt": "fix the divide function in tools.py"
})
# Returns:
# {
#   "analysis": "User wants to fix the divide function",
#   "actions": [
#     {"tool": "list_functions_in_file", ...},
#     {"tool": "get_function_source", ...},
#     {"tool": "ask_llm_to_refactor", ...},
#     {"tool": "write_back_to_file", ...}
#   ]
# }
```

---

#### `ask_llm_to_refactor(original_code: str) -> str`
Uses LLM to fix and improve Python code logic.

**Parameters:**
- `original_code` (str): The Python function code to refactor

**Returns:**
- str: The refactored Python code (without markdown fences)

**Rules:**
- Preserves function signature exactly
- Fixes logic errors and improves code quality
- Returns only code, no explanations

**Example:**
```python
response = await session.call_tool("ask_llm_to_refactor", {
    "original_code": "def divide(a, b):\n    if b == 0:\n        return a / b"
})
# Returns refactored code
```

---

### Code Modifier MCP Server Tools

#### `get_function_source(file_path: str, function_name: str) -> str`
Extracts specific function source code from a Python file.

**Parameters:**
- `file_path` (str): Path to the Python file
- `function_name` (str): Name of the function to extract

**Returns:**
- str: Source code of the function, or error message if not found

**Example:**
```python
response = await session.call_tool("get_function_source", {
    "file_path": "D:/projects/tools.py",
    "function_name": "divide"
})
```

---

#### `list_functions_in_file(file_path: str) -> str`
Lists all function names in a Python file.

**Parameters:**
- `file_path` (str): Path to the Python file

**Returns:**
- str: Newline-separated list of function names

**Example:**
```python
response = await session.call_tool("list_functions_in_file", {
    "file_path": "D:/projects/tools.py"
})
# Returns:
# add
# subtract
# multiply
# divide
```

---

#### `list_files_in_directory(directory_path: str) -> str`
Lists all Python files in a directory.

**Parameters:**
- `directory_path` (str): Path to the directory

**Returns:**
- str: Newline-separated list of Python file names

**Example:**
```python
response = await session.call_tool("list_files_in_directory", {
    "directory_path": "D:/projects/ai/code-summarizer-mcp"
})
# Returns:
# agent.py
# llm_mcp.py
# code_modifier_mcp.py
# tools.py
```

---

#### `write_back_to_file(file_path: str, function_name: str, new_code: str) -> str`
Replaces a function in a file with new code.

**Parameters:**
- `file_path` (str): Path to the Python file
- `function_name` (str): Name of the function to replace
- `new_code` (str): New function code

**Returns:**
- str: Success message or error

**Important:**
- Finds the function by AST parsing (exact match on function name)
- Replaces the entire function definition
- Preserves file structure and other functions

**Example:**
```python
response = await session.call_tool("write_back_to_file", {
    "file_path": "D:/projects/tools.py",
    "function_name": "divide",
    "new_code": "def divide(a, b):\n    if b == 0:\n        raise ZeroDivisionError()"
})
```

---

## Configuration

### Environment Variables
None required - all configuration is hardcoded or auto-detected.

### LM Studio Configuration

**Endpoint URL:**
```python
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
```

**Model Detection:**
The system automatically detects available models from:
```python
MODELS_URL = "http://localhost:1234/v1/models"
```

**Timeout Settings:**
```python
LM_STUDIO_TIMEOUT = 180  # seconds
```

### Temperature Settings

Used to control LLM behavior:

```python
# Analysis phase - more deterministic
"temperature": 0.3

# Refactoring phase - very deterministic
"temperature": 0.1
```

Lower temperature = more predictable, consistent results

---

## Action Plan Format

The agent executes action plans with the following structure:

```json
{
  "analysis": "Brief description of what will be done",
  "actions": [
    {
      "tool": "tool_name",
      "params": {
        "param1": "value1",
        "param2": "$result_0"
      },
      "description": "What this step does"
    }
  ],
  "loop_required": false,
  "loop_condition": ""
}
```

### Context Variables
- `$result_0`: Result from first action
- `$result_1`: Result from second action
- etc.

### Special Handling
- If a function is not found, the agent uses fuzzy matching
- Results are automatically propagated to subsequent steps
- Corrected function names are applied throughout

---

## Error Handling

### HTTP Errors

```python
try:
    response = requests.post(LM_STUDIO_URL, json=payload)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    # Handle 4xx/5xx errors
    return f"LLM Error: {str(e)}"
except requests.exceptions.Timeout:
    # Handle timeouts
    return "LLM Error: Request timed out"
except Exception as e:
    # Handle other errors
    return f"LLM Error: {str(e)}"
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 400 Bad Request | Invalid model name | Agent auto-detects model |
| 404 Not Found | LM Studio not running | Start LM Studio |
| Connection timeout | Model is slow/busy | Wait and retry |
| Function not found | Typo in function name | Agent uses fuzzy matching |
| Permission denied | File access issue | Check file permissions |

---

## Performance Metrics

### Expected Times
- **Model Loading**: 1-2 minutes (first request only)
- **Analysis**: 30-60 seconds
- **Refactoring**: 30-120 seconds per function
- **Total**: 2-5 minutes for typical workflow

### Optimization Tips
1. Use smaller functions for faster processing
2. Batch similar refactoring tasks
3. Keep models loaded between requests
4. Use GPU if available in LM Studio

---

## Extending the System

### Adding New Tools

1. Create tool in appropriate MCP server:
```python
@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"
```

2. Update `analyze_request` system prompt with tool info

3. Update agent's tool mapping if needed

### Custom Prompts

Edit system prompts in `llm_mcp.py`:

```python
system_prompt = (
    "Your custom system prompt here...\n"
    "Available tools:\n"
    "- tool1: description\n"
    "- tool2: description"
)
```

---

## Debugging

### Enable Debug Logging

Add to MCP servers:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Individual Tools

```bash
# Test LM Studio connectivity
python test_lm_studio.py

# Test agent workflow
python agent.py
```

### Check MCP Server Status

```python
# In agent.py, after initialization:
print(f"LLM Session available: {llm_session}")
print(f"Code Modifier Session available: {code_session}")
```

---

## Security Considerations

⚠️ **Important Notes:**

- **File Access**: The agent modifies files directly. Use version control.
- **Model Prompts**: System prompts are visible in code. Don't include secrets.
- **LM Studio**: Runs locally. No external API calls except to localhost.
- **User Input**: All user input is passed to the LLM. Be aware of prompt injection.

### Recommended Practices

1. Use Git to track changes:
   ```bash
   git commit -am "Before refactoring"
   ```

2. Test refactored code:
   ```bash
   python -m pytest
   ```

3. Review changes before committing:
   ```bash
   git diff
   ```

---

For more information, see:
- [README.md](./README.md) - Overview and features
- [QUICKSTART.md](./QUICKSTART.md) - Getting started guide
