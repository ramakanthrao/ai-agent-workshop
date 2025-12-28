# Developer Quick Start: Using Dynamic Tool Discovery

## TL;DR

Instead of hardcoding tools in `llm_mcp.py`, the system now **automatically discovers tools from MCP servers at runtime**.

**For you**: Just add `@mcp.tool()` to an MCP server. Done!

---

## What Changed?

### Old Way (❌ Don't Do This)
```python
# Had to edit llm_mcp.py to add tools:
AVAILABLE_TOOLS = {
    "my_new_tool": {
        "params": ["param1", "param2"],
        "description": "..."
    }
}
```

### New Way (✅ Do This)
```python
# Just add to code_modifier_mcp.py or llm_mcp.py:
@mcp.tool()
def my_new_tool(param1: str, param2: int) -> str:
    """Description of what this does."""
    return "result"

# Run agent - tool automatically discovered!
```

---

## How It Works (30-Second Version)

1. **Agent starts** → Connects to both MCP servers
2. **Agent calls** `session.list_tools()` → Gets all available tools
3. **Agent formats** tools as a string
4. **Agent passes** formatted tools to `analyze_request(available_tools=...)`
5. **LLM analyzes** with actual, current tools
6. **LLM creates** action plan using real tools

No hardcoding. No sync issues. Done.

---

## Real Example: Add a New Tool

### Step 1: Add Tool to MCP Server
```python
# In code_modifier_mcp.py
@mcp.tool()
def count_lines_in_file(file_path: str) -> str:
    """Count the number of lines in a file."""
    try:
        with open(file_path, 'r') as f:
            count = len(f.readlines())
        return f"File has {count} lines"
    except Exception as e:
        return f"Error: {str(e)}"
```

### Step 2: Run Agent
```bash
python agent.py
```

### Step 3: Observe
```
[Discovering available tools...]
  Found 2 tools in llm_mcp
  Found 5 tools in code_modifier_mcp  ← NEW TOOL HERE!
```

### Step 4: Use
```
What would you like me to do? count lines in tools.py
[Analyzing Request...]
[Executing Action Plan...]
```

The LLM automatically sees your new tool. **Zero code changes needed** beyond adding the function.

---

## Understanding the Mechanism

### Tool Discovery (What Agent Does)
```python
# In agent.py, run_agent()

# Get tools from llm_mcp
llm_tools = await llm_session.list_tools()
# Returns: [Tool(name="analyze_request", inputSchema={...}), ...]

# Get tools from code_modifier_mcp
code_tools = await code_session.list_tools()
# Returns: [Tool(name="count_lines_in_file", inputSchema={...}), ...]

# Format nicely
discovered_tools_text = """Available tools:
- analyze_request(...): description
- ask_llm_to_refactor(...): description
- count_lines_in_file(...): description
..."""

# Pass to LLM
analyze_request(user_prompt, available_tools=discovered_tools_text)
```

### Tool Processing (What LLM Does)
```
LLM sees system prompt with tools:
"Available tools:
 - analyze_request(...): Analyze user request and return action plan
 - ask_llm_to_refactor(...): Refactor Python code while preserving signature
 - count_lines_in_file(...): Count the number of lines in a file
 ..."

User asks: "count lines in tools.py"

LLM thinks: "I can use count_lines_in_file tool to count lines"

LLM returns plan:
{
  "actions": [
    {
      "tool": "count_lines_in_file",
      "params": {"file_path": "tools.py"},
      "description": "Count lines in tools.py"
    }
  ]
}

Agent executes the plan ✓
```

---

## Common Tasks

### Add a New Tool
```python
@mcp.tool()
def my_function(param1: str) -> str:
    """What this function does."""
    # Your code here
    return "result"
```
✅ Done! Automatically discovered.

### Remove a Tool
```python
# Just delete or comment out the function
# It will no longer be discovered
```
✅ Done! Automatically removed from available tools.

### Change Tool Description
```python
@mcp.tool()
def my_function(param1: str) -> str:
    """Updated description of what this function does."""
    # ...
```
✅ Done! New description automatically used.

### Add Tool Parameters
```python
# Old:
def my_function(param1: str) -> str:

# New:
def my_function(param1: str, param2: int, param3: bool) -> str:
```
✅ Done! New parameters automatically included in tool schema.

---

## Fallback Mechanism

If tool discovery fails for some reason, the system falls back to `FALLBACK_TOOLS` in llm_mcp.py:

```python
# In llm_mcp.py
FALLBACK_TOOLS = {
    "get_function_source": {...},
    "ask_llm_to_refactor": {...},
    # ... etc
}

# This is used if:
# - MCP servers are down
# - Tool discovery fails
# - available_tools parameter is empty
# - etc.
```

**You probably won't need to touch this.**

---

## Troubleshooting

### Tool Not Appearing?

**Check 1**: Is it decorated with `@mcp.tool()`?
```python
@mcp.tool()  # ← Must have this
def my_function(...):
    ...
```

**Check 2**: Is the MCP server running?
```bash
# Agent connects to both servers at startup
# Both must be accessible
```

**Check 3**: Is it in the right file?
```python
# Tools in code_modifier_mcp.py and llm_mcp.py are discovered
# Tools in other files won't be discovered
```

**Check 4**: Run agent in verbose mode
```bash
python agent.py
# Look for: "Found X tools in [server_name]"
# Your tool should be listed
```

### Tool Listed But Not Working?

Check the error in the agent output. Usually:
- Wrong parameter names
- Function implementation error
- Type mismatches

Fix the function and re-run agent. It's auto-discovered!

---

## Architecture Overview

```
YOU ADD TOOL:                agent.py                    llm_mcp.py
┌─────────────┐             ┌─────────────┐            ┌─────────────┐
│ @mcp.tool() │             │ list_tools()│            │ analyze_req │
│ def my_func │──────────▶│ from servers │────────▶│ with dynamic │
│   (...)     │             │             │            │ tools param │
└─────────────┘             └─────────────┘            └─────────────┘
                                  │
                                  ▼
                            Format as string
                            "- my_func(...):
                              description"
                                  │
                                  └─────────────────────▶ LLM sees tool
```

---

## Tips & Tricks

### Tip 1: Write Good Docstrings
The docstring becomes the tool description the LLM sees:
```python
@mcp.tool()
def analyze_code(code: str) -> str:
    """
    Analyze Python code for syntax errors and suggest improvements.
    Returns a formatted report with issues and fixes.
    """
    # Implementation
```

**Good docstring** = LLM understands tool better

### Tip 2: Use Descriptive Parameter Names
```python
# Good:
def process_file(file_path: str, options: dict) -> str:

# Confusing:
def process_file(a: str, b: dict) -> str:
```

**Clear names** = LLM uses tool correctly

### Tip 3: Return Helpful Messages
```python
# Good:
return f"Successfully processed {file_path}. Found 5 functions."

# Confusing:
return "done"
```

**Helpful messages** = LLM knows what happened

### Tip 4: Handle Errors Gracefully
```python
try:
    # Do something
except Exception as e:
    return f"Error: {str(e)}"
```

**Error messages** = Agent can recover or retry

---

## Advanced Usage

### Custom Tool Schemas (Advanced)
If you need more control over the tool schema, you can:
```python
@mcp.tool()
def my_advanced_tool(
    required_param: str,
    optional_param: str = "default"
) -> str:
    """Does something advanced."""
    return "result"
```

The schema is auto-generated from type hints. Works great!

### Tool with Multiple Returns (Advanced)
```python
@mcp.tool()
def analyze_and_report(file_path: str) -> str:
    """Analyze file and return detailed report."""
    analysis = do_analysis(file_path)
    
    # Return rich information as string
    report = f"""
    Analysis Results:
    - Files processed: {analysis['count']}
    - Issues found: {analysis['issues']}
    - Suggestions: {analysis['suggestions']}
    """
    return report
```

---

## Comparison Table

| Action | Old Way | New Way | Saves? |
|--------|---------|---------|--------|
| Add tool | Add to AVAILABLE_TOOLS dict | Add @mcp.tool() | Fewer files |
| Remove tool | Remove from dict | Remove function | Fewer files |
| Update description | Edit dict entry | Edit docstring | More natural |
| Add parameter | Edit dict entry | Add function param | Self-documenting |
| Test tool | Run agent | Run agent | Same |
| Verify in LLM | Check llm_mcp.py | Run agent, check output | Clearer |

---

## Quick Reference

### Create Tool
```python
@mcp.tool()
def my_tool(param: str) -> str:
    """Description."""
    return result
```

### Test Tool
```bash
python agent.py
# Observe: "Found X tools in..."
# Try asking agent to use it
```

### Debug Tool
```bash
python agent.py
# Check output for tool discovery
# Check error messages if tool fails
```

### Documentation
- See: QUICK_REFERENCE.md
- See: DYNAMIC_TOOLS.md
- See: ARCHITECTURE_DIAGRAMS.md

---

## FAQ

**Q: Do I have to use dynamic discovery?**
A: No, FALLBACK_TOOLS are still there. But dynamic is better!

**Q: Can I have tools in multiple servers?**
A: Yes! Agent discovers from all servers and combines them.

**Q: What if I make a tool with bad code?**
A: Error is returned to LLM. Agent handles it gracefully.

**Q: Can tools call other tools?**
A: Not directly, but LLM can create action plans that chain tools.

**Q: How many tools can I add?**
A: Unlimited! Discovery works with any number.

**Q: Is this backward compatible?**
A: Yes, 100%. Old code still works.

---

## Summary

**Before**: Hardcode tools in llm_mcp.py (3 steps, error-prone)
**After**: Add @mcp.tool() to MCP server (1 step, foolproof)

**New tools are discovered automatically at runtime.**

That's it! 🎉

Start with QUICK_REFERENCE.md for more details.
