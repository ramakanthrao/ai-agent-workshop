# Quick Reference: Dynamic Tool Discovery

## What Changed?

The system now **discovers available tools from MCP servers at runtime** instead of hardcoding them.

## For Users

Nothing changes! The agent works exactly the same way:
```bash
python agent.py
# What would you like me to do? refactor the divide function in tools.py
```

You'll just see an extra output:
```
[Discovering available tools...]
  Found 2 tools in llm_mcp
  Found 4 tools in code_modifier_mcp
```

## For Developers

### Adding a New Tool

**Old Way** (❌ 3 steps, error-prone):
1. Add `@mcp.tool()` to MCP server
2. Edit `AVAILABLE_TOOLS` dict in llm_mcp.py
3. Update any other tool lists
4. Run agent and hope tools sync correctly

**New Way** (✅ 1 step, foolproof):
1. Add `@mcp.tool()` to MCP server
2. Run agent → tools auto-discovered

### Example: Add `my_new_tool`

```python
# In code_modifier_mcp.py
@mcp.tool()
def my_new_tool(input_path: str) -> str:
    """Read and analyze the input file."""
    # Your implementation here
    return result

# Run agent
python agent.py
# ✅ Tool automatically available to LLM
```

### Troubleshooting

**Q: Tool not appearing in agent?**
- Check tool is properly decorated with `@mcp.tool()`
- Verify MCP server is running
- Check tool name (case-sensitive)

**Q: What if MCP server is down?**
- Agent falls back to `FALLBACK_TOOLS`
- Workflows with built-in tools still work
- Messages show warnings but continue

**Q: How to see discovered tools?**
- Run: `python agent.py`
- Look for: `[Discovering available tools...]` section

## Architecture Overview

```
┌─────────────────────────────────────────┐
│ agent.py                                │
│ ├─ Connect to MCP servers              │
│ ├─ Call session.list_tools()           │
│ ├─ Format tool schemas as string       │
│ └─ Pass to llm_mcp.analyze_request()   │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
    ┌─────────────┐      ┌──────────────┐
    │ llm_mcp.py  │      │ code_modifier│
    │             │      │ _mcp.py      │
    │ • analyze   │      │ • get_func   │
    │ • refactor  │      │ • write_back │
    └─────────────┘      │ • list_files │
                         │ • list_funcs │
                         └──────────────┘
         Tools discovered & formatted
         by agent, sent to LLM
```

## Files Modified

| File | What Changed | Why |
|------|-------------|-----|
| `agent.py` | Added tool discovery + formatting | Discover tools at runtime |
| `llm_mcp.py` | Added fallback, updated analyze_request | Accept tools as parameter |

## Key Concepts

### Tool Discovery
- Happens at agent startup
- Uses MCP's `session.list_tools()` method
- Extracts name, parameters, description from schema

### Tool Formatting
- Extracts parameters from JSON schema
- Creates: `"- tool_name(param1, param2): description"`
- Passes formatted string to LLM

### Fallback
- If discovery fails, uses hardcoded `FALLBACK_TOOLS`
- Ensures robustness
- Printed as warning in logs

## Performance

- **Startup**: +1-2 seconds for discovery (one-time per run)
- **Runtime**: No impact
- **Overall**: Negligible

## Testing Checklist

```bash
# 1. Start the agent
python agent.py

# 2. Check output
[Discovering available tools...]
  Found 2 tools in llm_mcp
  Found 4 tools in code_modifier_mcp
✅ Both servers found

# 3. Try a request
What would you like me to do? refactor the divide function in tools.py

# 4. Verify execution
[Analyzing Request...]
[Executing Action Plan...]
---Execution Complete---
✅ Should complete successfully
```

## Migration Notes

- **Backward Compatible**: Old FALLBACK_TOOLS still work
- **No Breaking Changes**: Same tool names and signatures
- **New Features**: Can now support multiple servers easily

## FAQ

**Q: Do tools still work?**
A: Yes, exactly the same. Only how they're discovered changed.

**Q: Why this change?**
A: Eliminates sync bugs when adding new tools. Scales better with multiple servers.

**Q: Can I revert to hardcoded tools?**
A: Yes, just populate AVAILABLE_TOOLS again (not recommended).

**Q: What if a tool is broken?**
A: Same as before - error is returned to LLM, workflow handles it.

## Next Steps

Try adding a new tool to code_modifier_mcp.py:

```python
@mcp.tool()
def my_test_tool() -> str:
    """Just a test."""
    return "Hello from my new tool!"
```

Run agent and see if it's auto-discovered!
