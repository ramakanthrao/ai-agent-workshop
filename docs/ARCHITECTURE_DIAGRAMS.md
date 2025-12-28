# System Architecture Diagrams

## 1. Tool Discovery Flow (With Code)

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                    AGENT INITIALIZATION                         │
│                                                                  │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Connect to MCP Servers      │
        │  • llm_mcp.py                │
        │  • code_modifier_mcp.py      │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  list_tools() on llm_mcp     │
        │                              │
        │  Returns:                    │
        │  [Tool(                      │
        │    name="analyze_request",   │
        │    inputSchema={...}         │
        │  ), Tool(...)]               │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  list_tools() on code_mod    │
        │                              │
        │  Returns:                    │
        │  [Tool(                      │
        │    name="get_function...",   │
        │    inputSchema={...}         │
        │  ), Tool(...)]               │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  TOOL FORMATTING             │
        │                              │
        │  For each tool:              │
        │  1. Get schema.properties    │
        │  2. Extract param names      │
        │  3. Get description          │
        │  4. Format string:           │
        │     "- name(p1,p2): desc"    │
        │                              │
        │  Result:                     │
        │  "Available tools:           │
        │   - analyze_request(...): .. │
        │   - ask_llm_to_refactor(...):│
        │   - get_function_source(...) │
        │   - list_files_in_directory..│
        │   - list_functions_in_file..." │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  SEND TO LLM                 │
        │                              │
        │  analyze_request(            │
        │    user_prompt,              │
        │    available_tools=           │
        │      "- analyze_request..." │
        │      "- ask_llm_to_refactor" │
        │      "- get_function..."     │
        │      ...                     │
        │  )                           │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  LLM ANALYZES REQUEST        │
        │  WITH DYNAMIC TOOLS          │
        │                              │
        │  System Prompt:              │
        │  "You are a coordinator.     │
        │   Available tools:           │
        │   - analyze_request(...)     │
        │   - ask_llm_to_refactor(...) │
        │   - get_function_source(...) │
        │   ..."                       │
        │                              │
        │  User Message:               │
        │  "refactor divide function"  │
        │                              │
        │  LLM Response:               │
        │  {                           │
        │    "analysis": "...",        │
        │    "actions": [...]          │
        │  }                           │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  EXECUTE ACTION PLAN         │
        │  (same as before)            │
        └──────────────────────────────┘
```

---

## 2. Code Structure Comparison

### BEFORE (Hardcoded)
```
llm_mcp.py                          agent.py
┌──────────────────────┐            ┌──────────────────────┐
│                      │            │                      │
│ AVAILABLE_TOOLS {    │            │ analyze_request(     │
│   tool1: {...},      │ ◄──────────┤   user_prompt        │
│   tool2: {...},      │  hardcoded │ )                    │
│   ...                │   tools    │                      │
│ }                    │            │ No tool discovery    │
│                      │            │                      │
│ build_tools_section()│            │                      │
│   ├─ loops dict      │            │                      │
│   └─ builds string   │            │                      │
│                      │            │                      │
│ analyze_request(...) │            │                      │
│   ├─ calls function  │            │                      │
│   └─ builds prompt   │            │                      │
│                      │            │                      │
└──────────────────────┘            └──────────────────────┘
        │
        ├─ Tool duplication
        ├─ Sync risk
        └─ Manual updates
```

### AFTER (Dynamic)
```
agent.py                            llm_mcp.py
┌──────────────────────┐            ┌──────────────────────┐
│                      │            │                      │
│ list_tools() {       │            │ FALLBACK_TOOLS {     │
│   llm_session        │            │   # backup only      │
│   code_session       │            │ }                    │
│ }                    │            │                      │
│                      │            │ format_tool_for_(...) │
│ Format discovered    │            │   ├─ schema parsing  │
│ tools as string      │            │   └─ formatting      │
│                      │            │                      │
│ analyze_request(     │ ──────────▶│ analyze_request(     │
│   user_prompt,       │  dynamic   │   user_prompt,       │
│   available_tools    │  tools     │   available_tools    │
│ )                    │            │ )                    │
│                      │            │   ├─ use parameter   │
│                      │            │   └─ fallback if ""   │
│                      │            │                      │
└──────────────────────┘            └──────────────────────┘
        │                                   │
        ├─ Single source of truth          │
        ├─ Zero sync risk                  │
        ├─ Auto-discovers tools            │
        └─ Scales with multiple servers ◀─┘
```

---

## 3. Tool Discovery Mechanism

```
┌─────────────────────────────────────────────────────────────┐
│                  MCP Tool Object                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tool {                                                     │
│    name: "get_function_source"                             │
│                                                             │
│    inputSchema: {                                          │
│      "type": "object",                                     │
│      "properties": {                                       │
│        "file_path": {                                      │
│          "type": "string",                                 │
│          "description": "Path to the Python file"          │
│        },                                                  │
│        "function_name": {                                  │
│          "type": "string",                                 │
│          "description": "Name of function to extract"      │
│        }                                                   │
│      }                                                     │
│    },                                                      │
│                                                             │
│    "description": "Extract specific function source code" │
│  }                                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ EXTRACTION
                         ▼
        ┌────────────────────────────────┐
        │  Extract from inputSchema:     │
        │                                │
        │  params = ["file_path",        │
        │            "function_name"]    │
        │                                │
        │  description = "Extract        │
        │    specific function source    │
        │    code"                       │
        └────────────────────────────────┘
                         │
                         │ FORMATTING
                         ▼
        ┌────────────────────────────────┐
        │  format_tool_for_prompt(       │
        │    "get_function_source",      │
        │    schema                      │
        │  )                             │
        │                                │
        │  Returns:                      │
        │  "- get_function_source(...):  │
        │     Extract specific..."       │
        └────────────────────────────────┘
                         │
                         │ AGGREGATION
                         ▼
        ┌────────────────────────────────┐
        │  Available tools:              │
        │  - analyze_request(...): ...   │
        │  - ask_llm_to_refactor(...):.. │
        │  - get_function_source(...):.. │
        │  - list_files_in_directory(..)│
        │  - list_functions_in_file(..)│
        └────────────────────────────────┘
                         │
                         │ TO LLM
                         ▼
        ┌────────────────────────────────┐
        │  System Prompt includes        │
        │  formatted tools string        │
        └────────────────────────────────┘
```

---

## 4. Request Processing Pipeline

```
USER INPUT
    │
    │ "refactor divide function in tools.py"
    │
    ▼
┌─────────────────────────────────────────┐
│ analyze_request(                        │
│   user_prompt="refactor divide...",     │
│   available_tools="- analyze_request..  │
│                   - ask_llm_to_refactor │
│                   - get_function_source │
│                   ..."                  │
│ )                                       │
└────────────────┬────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ System Prompt:     │
        │                    │
        │ "You are a code    │
        │  coordinator.      │
        │                    │
        │  Available tools:  │
        │  - analyze_request │
        │  - ask_llm_to_     │
        │    refactor        │
        │  - get_function_   │
        │    source          │
        │  ..."              │
        │                    │
        │ User Prompt:       │
        │ "refactor divide   │
        │  function in       │
        │  tools.py"         │
        └────────────┬───────┘
                     │
                     ▼ (Send to LM Studio)
        ┌────────────────────┐
        │ LLM Response:      │
        │                    │
        │ {                  │
        │   "analysis":      │
        │     "User wants    │
        │      to fix the    │
        │      divide fn",   │
        │   "actions": [     │
        │     {              │
        │       "tool":      │
        │         "list_..   │
        │       "params":{..}│
        │     },             │
        │     {              │
        │       "tool":      │
        │         "get_func..│
        │       ...          │
        │     },             │
        │     ...            │
        │   ]                │
        │ }                  │
        └────────────┬───────┘
                     │
                     ▼
        ┌────────────────────┐
        │ execute_action_plan│
        │                    │
        │ For each action:   │
        │ 1. Resolve params  │
        │ 2. Call tool       │
        │ 3. Store result    │
        │ 4. Continue        │
        └────────────┬───────┘
                     │
                     ▼
        ┌────────────────────┐
        │ Execution Complete │
        │                    │
        │ ✓ File modified    │
        │ ✓ Function fixed   │
        └────────────────────┘
```

---

## 5. Error Handling Flow

```
┌─────────────────────────────────────────┐
│ Discovery Attempts                      │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
Try list_tools()         Try list_tools()
on llm_mcp               on code_mod
    │                         │
    ├─ Success                ├─ Success
    │   │                     │   │
    │   ▼                     │   ▼
    │  Extract tools      Extract tools
    │                         │
    └────────────┬────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ Format Tools    │
        │ Success?        │
        └────────┬────────┘
                 │
    ┌────────────┴────────────┐
    │ YES                 NO  │
    │                         │
    ▼                         ▼
Pass to           Use FALLBACK
analyze_request   _TOOLS
    │                  │
    └────────────┬─────┘
                 │
                 ▼
        ┌─────────────────┐
        │ LLM Analyzes    │
        │ Request         │
        │ Success?        │
        └────────┬────────┘
                 │
    ┌────────────┴────────────┐
    │ YES                 NO  │
    │                         │
    ▼                         ▼
Execute Action  Print Error,
Plan            Continue
    │           with fallback
    ▼
┌─────────────────┐
│ Return Results  │
└─────────────────┘
```

---

## 6. Tool Schema Structure

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  InputSchema (from MCP Tool object)                     │
│                                                         │
│  {                                                      │
│    "type": "object",                                   │
│    "properties": {                     ◄─ Extract keys  │
│      "file_path": {                    │ as parameters  │
│        "type": "string",               │                │
│        "description": "..."            │                │
│      },                                │                │
│      "function_name": {                │                │
│        "type": "string",               │                │
│        "description": "..."            │                │
│      }                                 │                │
│    },                                  │                │
│    "required": ["file_path", ...]      │                │
│  }                                     ▼                │
│                                                         │
│  ────────────────────────────────────────────           │
│                                                         │
│  Tool Description (from Tool object)                    │
│                                                         │
│  "Extract specific function source code from a Python  │
│   file"                                ◄─ Use as desc  │
│                                                         │
│  ────────────────────────────────────────────           │
│                                                         │
│  FORMATTED OUTPUT:                                      │
│                                                         │
│  "- get_function_source(file_path, function_name):    │
│     Extract specific function source code from a       │
│     Python file"                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 7. Multi-Server Orchestration

```
                    AGENT.PY
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐
   │Initialize  │ │Discover │ │ Format  │
   │Sessions    │ │Tools    │ │ Tools   │
   └─────┬─────┘ └────┬────┘ └────┬────┘
         │            │            │
         ▼            ▼            ▼
    ┌─────────────────────────────────┐
    │  Tool Discovery from Both:      │
    │                                 │
    │  Server 1: llm_mcp              │
    │  ├─ Tools: ["analyze_request",  │
    │  │          "ask_llm_to_refactor"]
    │  │ Schemas: {...}               │
    │  │                              │
    │  Server 2: code_modifier_mcp    │
    │  ├─ Tools: ["get_function...",  │
    │  │          "write_back...",    │
    │  │          "list_files...",    │
    │  │          "list_functions..."]│
    │  └─ Schemas: {...}              │
    │                                 │
    └─────────┬───────────────────────┘
              │
              ▼
    ┌─────────────────────────────────┐
    │  Unified Tools List:            │
    │                                 │
    │  - analyze_request(...)         │
    │  - ask_llm_to_refactor(...)     │
    │  - get_function_source(...)     │
    │  - list_files_in_directory(...) │
    │  - list_functions_in_file(...)  │
    │  - write_back_to_file(...)      │
    │                                 │
    └─────────┬───────────────────────┘
              │
              ▼ Pass to LLM
    ┌─────────────────────────────────┐
    │  LLM Sees All Tools             │
    │  (from both servers)            │
    │                                 │
    │  Coordinate between servers:    │
    │  1. Use llm_mcp for analysis    │
    │  2. Use code_modifier for files │
    │  3. Fallback between if needed  │
    │                                 │
    └─────────────────────────────────┘
```

---

## Key Insights

1. **Schema Extraction**: Tool parameters come from inputSchema.properties
2. **Formatting**: Parameters extracted automatically from schema
3. **Aggregation**: All servers' tools combined into single list
4. **Fallback**: FALLBACK_TOOLS used only if discovery/analysis fails
5. **Scalability**: Works seamlessly with any number of servers

This architecture ensures **zero manual tool management** while maintaining flexibility and robustness.
