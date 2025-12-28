# Before and After: Dynamic Tool Discovery

## Architecture Comparison

### BEFORE (Hardcoded Tools)
```
┌──────────────────────┐
│  llm_mcp.py          │
│                      │
│  AVAILABLE_TOOLS = { │
│    "tool1": {...},   │◄── Hardcoded, static
│    "tool2": {...},   │
│    ...               │
│  }                   │
│                      │
│  build_tools_section()
│  ├─ loops over dict  │
│  └─ formats string   │
│                      │
│  analyze_request()   │
│  ├─ calls function   │
│  └─ builds prompt    │
└──────────────────────┘
         ▲
         │ (static tools)
         │
    ┌────┴─────────────┐
    │  Agent asks      │
    │  llm_mcp for     │
    │  analysis        │
    └──────────────────┘
```

**Problem**: Tools must be manually updated in code every time a new tool is added

---

### AFTER (Dynamic Discovery)
```
┌──────────────────────┐         ┌──────────────────────┐
│  llm_mcp.py          │         │  Agent               │
│                      │         │                      │
│  FALLBACK_TOOLS = {  │         │  session.list_tools()│
│    # fallback only   │         │  ├─ llm_mcp tools   │
│  }                   │         │  └─ code_modifier   │
│                      │         │                      │
│  format_tool_for     │         │  Format discovered  │
│  _prompt()           │         │  tools as string    │
│                      │         │                      │
│  analyze_request(    │◄────────┤  analyze_request(   │
│    user_prompt,      │  pass    │    user_prompt,     │
│    available_tools   │  tools   │    available_tools) │
│  )                   │          │                     │
└──────────────────────┘         └──────────────────────┘
                                          ▲
                                          │
                        ┌─────────────────┤
                        │                 │
                    ┌───┴───┐         ┌───┴───┐
                    │llm_mcp│         │code_  │
                    │       │         │modifier│
                    └───┬───┘         └───┬───┘
                        │                 │
                        └─────────┬───────┘
                                  │
                          Real tools discovered
                          at runtime
```

**Benefit**: New tools are automatically available - no code changes needed!

---

## Code Comparison

### Tool Definition

#### BEFORE (llm_mcp.py)
```python
# Hardcoded in llm_mcp.py
AVAILABLE_TOOLS = {
    "get_function_source": {
        "params": ["file_path", "function_name"],
        "description": "Extract specific function source code from a Python file"
    },
    "ask_llm_to_refactor": {
        "params": ["original_code"],
        "description": "Refactor/fix Python code logic while preserving function signatures"
    },
    # ... more tools hardcoded
}

def build_tools_section():
    """Build from hardcoded dict"""
    tools_text = "Available tools:\n"
    for tool_name, tool_info in AVAILABLE_TOOLS.items():
        params = ", ".join(tool_info["params"])
        description = tool_info["description"]
        tools_text += f"- {tool_name}({params}): {description}\n"
    return tools_text.strip()
```

**Issues**:
- ❌ Requires manual updates
- ❌ Duplicates tool definitions
- ❌ No schema validation
- ❌ Easy to get out of sync

---

#### AFTER (llm_mcp.py)
```python
# No hardcoded tools - only fallback
FALLBACK_TOOLS = {
    # Only used if discovery fails
}

def format_tool_for_prompt(tool_name: str, tool_input_schema: dict) -> str:
    """Format a tool from its actual JSON schema"""
    schema_properties = tool_input_schema.get("properties", {})
    params = list(schema_properties.keys())
    description = tool_input_schema.get("description", "No description available")
    params_str = ", ".join(params) if params else "no parameters"
    return f"- {tool_name}({params_str}): {description}"
```

**Advantages**:
- ✅ Uses real tool schemas from servers
- ✅ No manual updates needed
- ✅ Always in sync
- ✅ Single source of truth

---

### Tool Discovery

#### BEFORE (agent.py)
```python
# No tool discovery - just send request
analysis_result = await llm_session.call_tool("analyze_request", {
    "user_prompt": user_request
    # ❌ No tools passed - they're hardcoded in llm_mcp.py
})
```

#### AFTER (agent.py)
```python
# Discover tools from both servers
llm_tools = await llm_session.list_tools()
tools_by_server['llm_mcp'] = [
    (tool.name, tool.inputSchema) 
    for tool in llm_tools.tools
]

code_tools = await code_session.list_tools()
tools_by_server['code_modifier_mcp'] = [
    (tool.name, tool.inputSchema) 
    for tool in code_tools.tools
]

# Format and pass to analyze_request
discovered_tools_text = "Available tools:\n"
for server_name, tools in tools_by_server.items():
    for tool_name, tool_schema in tools:
        # Use actual schema to extract params and description
        params = list(tool_schema.get("properties", {}).keys())
        description = tool_schema.get("description", "No description")
        # Format tool

analysis_result = await llm_session.call_tool("analyze_request", {
    "user_prompt": user_request,
    "available_tools": discovered_tools_text  # ✅ Dynamic!
})
```

---

### analyze_request Signature

#### BEFORE
```python
@mcp.tool()
def analyze_request(user_prompt: str) -> str:
    """Analyze user request - tools are hardcoded inside"""
    tools_section = build_tools_section()  # Static
    system_prompt = f"...{tools_section}..."
    # Send to LLM
```

#### AFTER
```python
@mcp.tool()
def analyze_request(user_prompt: str, available_tools: str = "") -> str:
    """Analyze user request - tools come as parameter"""
    # Use provided tools or fallback
    if not available_tools or available_tools.strip() == "":
        # Build from FALLBACK_TOOLS
        available_tools = build_fallback_tools()
    
    system_prompt = f"...{available_tools}..."  # Dynamic!
    # Send to LLM
```

---

## Adding a New Tool Example

### BEFORE (Hardcoded Approach)
To add a new tool `list_tests_in_directory`:

1. **Add tool to code_modifier_mcp.py**:
   ```python
   @mcp.tool()
   def list_tests_in_directory(directory_path: str) -> str:
       # Implementation
   ```

2. **Update AVAILABLE_TOOLS in llm_mcp.py** ⚠️ **MUST DO THIS**:
   ```python
   AVAILABLE_TOOLS = {
       # ... existing tools ...
       "list_tests_in_directory": {
           "params": ["directory_path"],
           "description": "List all test files in a directory"
       }
   }
   ```

3. **Update any other hardcoded tool lists** ⚠️ **EASY TO FORGET**

**Risk**: Forget step 2 or 3 → Tool exists but LLM doesn't know about it

---

### AFTER (Dynamic Discovery)
To add a new tool `list_tests_in_directory`:

1. **Add tool to code_modifier_mcp.py**:
   ```python
   @mcp.tool()
   def list_tests_in_directory(directory_path: str) -> str:
       """List all test files in a directory"""
       # Implementation
   ```

2. **Done!** 🎉

The agent automatically discovers it on next run:
```
[Discovering available tools...]
  Found 2 tools in llm_mcp
  Found 5 tools in code_modifier_mcp  ◄── New tool included automatically
```

**Benefit**: One step instead of three, zero risk of sync issues

---

## Summary Table

| Aspect | Before | After |
|--------|--------|-------|
| **Tool Definition** | llm_mcp.py (hardcoded) | MCP servers (source of truth) |
| **Tool Discovery** | None (static) | Runtime (via list_tools()) |
| **Adding Tools** | Edit llm_mcp.py | Just add @mcp.tool() |
| **Sync Risk** | High | None |
| **LLM Awareness** | Static list | Real, live tools |
| **Fallback** | None | FALLBACK_TOOLS |
| **Lines of Code** | More (hardcoded dicts) | Less (use real schemas) |
| **Maintainability** | Low | High |

---

## Key Insight

**Before**: Tools defined in 3 places (mcp servers + hardcoded dict + prompts)
**After**: Tools defined in 1 place (mcp servers) + discovered dynamically

This eliminates the biggest source of bugs: **definition synchronization**
