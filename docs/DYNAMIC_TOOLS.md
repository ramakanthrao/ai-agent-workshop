# Dynamic Tool Discovery Implementation

## Overview
The system has been updated to **dynamically discover available tools from MCP servers** instead of hardcoding them. This provides better maintainability and ensures the LLM always has access to the latest tools.

## Architecture Changes

### 1. **agent.py** - Tool Discovery
The agent now performs dynamic tool discovery when it connects to MCP servers:

```python
# Discover available tools from both servers
print("\n[Discovering available tools...]")
tools_by_server = {}

try:
    # List tools from llm_mcp
    llm_tools = await llm_session.list_tools()
    tools_by_server['llm_mcp'] = [(tool.name, tool.inputSchema) for tool in llm_tools.tools]
except Exception as e:
    print(f"  Warning: Could not list tools from llm_mcp: {e}")

try:
    # List tools from code_modifier_mcp
    code_tools = await code_session.list_tools()
    tools_by_server['code_modifier_mcp'] = [(tool.name, tool.inputSchema) for tool in code_tools.tools]
except Exception as e:
    print(f"  Warning: Could not list tools from code_modifier_mcp: {e}")
```

**Process:**
1. Call `session.list_tools()` on each MCP server
2. Extract tool name and input schema from each tool
3. Format tools as a string for the LLM
4. Pass the formatted tools to `analyze_request()`

### 2. **llm_mcp.py** - Dynamic Tool Handling

#### New Functions:
- **`format_tool_for_prompt()`**: Formats a single tool with its parameters from JSON schema
  ```python
  # Extracts: tool_name(param1, param2): description
  ```

- **`build_tools_section_from_schema()`**: Builds tools section from server responses
  - Used as a reference but primarily for documentation
  - Agent now passes pre-formatted tools to analyze_request

#### Updated `analyze_request()`:
- Now accepts an optional `available_tools` parameter
- If tools not provided, uses `FALLBACK_TOOLS` dictionary
- Fallback ensures the system works even if tool discovery fails

```python
def analyze_request(user_prompt: str, available_tools: str = "") -> str:
    # Use provided tools or fallback
    if not available_tools or available_tools.strip() == "":
        # Build from fallback...
```

#### Fallback Tools Dictionary:
```python
FALLBACK_TOOLS = {
    "get_function_source": {...},
    "ask_llm_to_refactor": {...},
    "write_back_to_file": {...},
    "list_files_in_directory": {...},
    "list_functions_in_file": {...}
}
```

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Agent starts and connects to both MCP servers                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ Call session.list_tools()    │
        │ on each server               │
        └──────────────┬───────────────┘
                       │
         ┌─────────────┴──────────────┐
         │                            │
         ▼                            ▼
    ┌─────────────┐            ┌──────────────┐
    │ llm_mcp     │            │ code_modifier│
    │ tools:      │            │ tools:       │
    │ - analyze   │            │ - get_func   │
    │ - refactor  │            │ - write_back │
    └─────┬───────┘            └──────┬───────┘
          │                           │
          └───────────┬───────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │ Format tools as string:    │
         │ "- tool1(...): desc"       │
         │ "- tool2(...): desc"       │
         └────────────┬───────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │ Call analyze_request()     │
         │ with available_tools param │
         └────────────┬───────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │ LLM receives current tool  │
         │ list and generates plan    │
         └────────────────────────────┘
```

## Benefits

1. **No Hardcoding Required**: Tool lists are discovered from actual MCP servers
2. **Easy Extension**: Add new tools to MCP servers without updating llm_mcp.py
3. **Graceful Fallback**: If discovery fails, uses FALLBACK_TOOLS
4. **Always Up-to-Date**: LLM always sees the current tools available
5. **Multiple Servers**: Works seamlessly with multiple MCP servers

## Migration Path

### Before (Hardcoded):
```python
AVAILABLE_TOOLS = {
    "get_function_source": {
        "params": ["file_path", "function_name"],
        "description": "..."
    },
    # ... hardcoded tool definitions
}

tools_section = build_tools_section()  # Static, never changes
```

### After (Dynamic):
```python
# No AVAILABLE_TOOLS hardcoded in llm_mcp.py

# Agent discovers at runtime:
llm_tools = await llm_session.list_tools()
code_tools = await code_session.list_tools()

# Format and pass to analyze_request:
analysis_result = await llm_session.call_tool(
    "analyze_request",
    {
        "user_prompt": user_request,
        "available_tools": discovered_tools_text  # Dynamic!
    }
)
```

## Adding New Tools

To add a new tool to the system:

1. **Define in MCP server** (e.g., code_modifier_mcp.py):
   ```python
   @mcp.tool()
   def my_new_tool(param1: str, param2: int) -> str:
       """Description of what this tool does."""
       # Implementation
       pass
   ```

2. **That's it!** The agent will automatically discover it via `list_tools()`

The tool will immediately be available to the LLM without any changes to llm_mcp.py or the configuration.

## Error Handling

- **Tool Discovery Fails**: Agent prints warning and continues
- **LLM Gets Empty Tools**: Uses FALLBACK_TOOLS as backup
- **analyze_request() Called Without Tools**: Uses FALLBACK_TOOLS

All three fallback mechanisms ensure robustness.

## Testing

To verify the dynamic discovery works:

```bash
# Run the agent
python agent.py

# Check the output:
# [Discovering available tools...]
#   Found 2 tools in llm_mcp
#   Found 4 tools in code_modifier_mcp
```

The tools should be listed dynamically from the actual servers, not from hardcoded definitions.
