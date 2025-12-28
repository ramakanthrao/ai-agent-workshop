# Quick Start Guide

## 1. Prerequisites

Make sure you have:
- Python 3.8+
- LM Studio running on `localhost:1234`
- A language model loaded in LM Studio

## 2. Check LM Studio

First, verify LM Studio is running and has a model loaded:
```bash
python test_lm_studio.py
```

If successful, you'll see:
```
✓ LM Studio is running (Status: 200)
✓ Available models:
  - quantized_phi3_v1
  - phi4-mini-model-quantized-to
```

## 3. Run the Agent

Start the interactive agent:
```bash
python agent.py
```

You'll see:
```
Connecting to llm_mcp.py...
Connecting to code_modifier_mcp.py...
--- Interactive AI Code Agent ---
Connected to 2 MCP servers

What would you like me to do?
```

## 4. Example Commands

### Fix a specific function
```
analyse the code of: D:/projects/ai/code-summarizer-mcp/tools.py and fix the divide function
```

### Fix all functions in a file
```
analyse the code of: D:/projects/ai/code-summarizer-mcp/tools.py and fix all functions
```

### Analyze a directory
```
analyse the code of: D:/projects/ai/code-summarizer-mcp and fix all functions
```

## 5. What Happens Next

The agent will:

1. **Parse your request** - Extract file path and function names
2. **List available functions** - Show what's in the target file
3. **Find best matches** - Correct any typos in function names
4. **Extract code** - Get the source code of the target function
5. **Analyze & Refactor** - Use the LLM to fix logic errors
6. **Write back** - Update the file with corrected code

## 6. Expected Output

You'll see a detailed breakdown of each step:

```
[Step 1] List all functions in D:/projects/ai/code-summarizer-mcp/tools.py
  Tool: list_functions_in_file
  Server: code_modifier_mcp
  Result: add
subtract
multiply
divide...

[Step 2] Extract function 'divide' from D:/projects/ai/code-summarizer-mcp/tools.py
  Tool: get_function_source
  Server: code_modifier_mcp
  Result: def divide(a, b):
    if b == 0:
        ...

[Step 3] Refactor and fix the function
  Tool: ask_llm_to_refactor
  Server: llm_mcp
  Result: def divide(a, b):
    if b == 0:
        raise ZeroDivisionError...

[Step 4] Write fixed function back to file
  Tool: write_back_to_file
  Server: code_modifier_mcp
  Result: Function 'divide' has been updated successfully.
```

## 7. Troubleshooting

### "Analysis Error: 400 Client Error"
- Check that LM Studio is running
- Verify a model is loaded
- Run `python test_lm_studio.py` to debug

### "Function not found"
- The agent will try to find similar function names
- Check the listed functions carefully
- Make sure you're using the correct file path

### Timeouts (> 3 minutes)
- LM Studio models are large and slow on first use
- Subsequent requests will be faster
- Check LM Studio's GPU/CPU usage

## 8. File Modifications

The agent modifies code directly in your files. Changes include:

**Before:**
```python
def divide(a, b):
    if b == 0:
        return a / b
    else:
        return "Division by zero is not allowed"
```

**After:**
```python
def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("division by zero")
    else:
        return a / b
```

## 9. Tips & Tricks

- **Parallel Processing**: Run multiple agent instances for different files
- **Batch Operations**: Refactor one function at a time for best results
- **Custom Prompts**: Modify the system prompts in `llm_mcp.py` for different behavior
- **Model Selection**: The agent auto-selects the first available model

## 10. System Architecture

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
    ┌────▼─────────────────────────────┐
    │  Agent (agent.py)                │
    │  - Parses requests               │
    │  - Detects path types            │
    │  - Manages workflow              │
    └────┬──────────┬──────────────────┘
         │          │
    ┌────▼────┐ ┌──▼─────────┐
    │ LLM MCP │ │ Code Mod   │
    │         │ │ MCP        │
    │- analyze├─┤- extract   │
    │- refactor┤ ├- list      │
    └────┬────┘ ├- write     │
         │      └──┬─────────┘
         │         │
         └────┬────┘
              │
    ┌─────────▼──────────┐
    │  LM Studio Server  │
    │  (localhost:1234)  │
    └────────────────────┘
```

---

Ready to refactor some code! 🚀
