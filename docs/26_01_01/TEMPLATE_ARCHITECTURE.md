# Template-Based Agent Architecture

## System Overview

The refactored agent uses a **template-registry pattern** for complete modularity and extensibility.

```
┌─────────────────────────────────────────────────────────┐
│  Agent (agent_simplified.py)                            │
│  - Gets user request                                    │
│  - Calls LLM to generate action plan                    │
│  - Uses TemplateManager to execute                      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  TemplateManager (template_manager.py)                  │
│  - Loads registry configuration                         │
│  - Validates action plans against schema                │
│  - Dynamically instantiates executor                    │
│  - Orchestrates execution                               │
└────────────────┬────────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    ▼                         ▼
┌──────────────┐      ┌──────────────────┐
│ Registry     │      │ ActionPlanExecutor
│ Config       │      │ - Executes plan  │
│ (JSON)       │      │ - Dynamic tool   │
│              │      │ - No hardcoding  │
└──────────────┘      └──────────────────┘
```

## Component Details

### 1. Template Registry (`schema/template_registry.json`)

Configuration file that defines all available templates and executor settings:

```json
{
  "templates": {
    "universal-action-plan": {
      "template_id": "universal-action-plan",
      "template_desc": "Universal template for executing dynamic action plans",
      "template_schema_file": "action_plan_schema.json",
      "template_dir": "d:\\projects\\ai\\code-summarizer-mcp\\schema",
      "executor_module": "action_plan_executor",
      "executor_class": "ActionPlanExecutor",
      "version": "1.0",
      "enabled": true
    }
  },
  "executor_config": {
    "timeout_seconds": 300,
    "max_nested_loops": 5,
    "max_steps": 1000,
    "enable_caching": true
  }
}
```

**Key Features:**
- **Multiple templates supported** - Easy to add new executor types
- **Dynamic module loading** - Executor class loaded at runtime
- **Schema mapping** - Each template has a JSON schema for validation
- **Configuration centralized** - All executor settings in one place

### 2. Action Plan Schema (`schema/action_plan_schema.json`)

JSON Schema that defines the structure of valid action plans:

```json
{
  "title": "Universal Action Plan Schema",
  "required": ["analysis", "actions"],
  "properties": {
    "actions": {
      "items": {
        "oneOf": [
          { "title": "Standard Tool Call" },
          { "title": "Loop Block" },
          { "title": "Conditional Block" }
        ]
      }
    }
  }
}
```

**Benefits:**
- **Validation** - Action plans validated before execution
- **LLM guidance** - Schema shared with LLM for consistency
- **Documentation** - Schema documents the action plan format

### 3. Template Manager (`src/agent/template_manager.py`)

Manages template loading, validation, and executor instantiation:

```python
# Usage
registry_path = "schema/template_registry.json"
template_mgr = TemplateManager(registry_path)

# Execute action plan
results = await template_mgr.execute_action_plan(
    action_plan=plan,
    sessions=sessions,
    template_id='universal-action-plan'
)
```

**Responsibilities:**
- Load registry configuration
- List available templates
- Validate action plans
- Dynamically instantiate executors
- Handle execution orchestration

### 4. Action Plan Executor (`src/agent/action_plan_executor.py`)

Generic executor that runs action plans without hardcoding:

```python
# No hardcoding of:
# - Tool names
# - Server names
# - Field names in responses
# - Conditional logic
# - Parameter resolution patterns
```

**Generic Methods:**
- `_resolve_parameters()` - Works with ANY parameter type
- `_evaluate_condition()` - Works with ANY field reference
- `_execute_tool()` - Dynamic tool lookup from registry
- `_parse_result()` - JSON or string handling

### 5. Simplified Agent (`src/agent/agent_simplified.py`)

Clean agent that focuses on planning and orchestration:

```python
# Only ~120 lines
# Responsibilities:
# 1. Connect to MCP servers
# 2. Get user request
# 3. Call LLM for action plan
# 4. Use TemplateManager to execute
```

## Data Flow

### Execution Flow

```
User Request
    ↓
Agent: Connect MCP servers
    ↓
Agent: Get user input
    ↓
Agent: Call LLM with tools list
    ↓
LLM: Generate action plan (JSON)
    ↓
TemplateManager: Validate plan
    ↓
TemplateManager: Load executor from registry
    ↓
Executor: Execute action plan
    ├─ Dynamic tool discovery
    ├─ Parameter resolution
    ├─ Condition evaluation
    ├─ Loop handling
    └─ Results storage
    ↓
Agent: Display results
```

## Extensibility Scenarios

### Scenario 1: Add New MCP Server

No code changes needed:

```python
# In agent, just add to config
new_server_config = {
    'my_analyzer': {
        'command': 'python',
        'args': ['my_analyzer_mcp.py']
    }
}
await run_agent(new_server_config)

# Executor automatically discovers tools
# No hardcoded tool lists to update
```

### Scenario 2: Add New Executor Type

Create new executor class:

```python
# my_custom_executor.py
class MyCustomExecutor:
    async def execute(self, action_plan):
        # Custom execution logic
        pass

# Register in template_registry.json
{
  "templates": {
    "my-custom-template": {
      "executor_module": "my_custom_executor",
      "executor_class": "MyCustomExecutor",
      ...
    }
  }
}

# Use it
await template_mgr.execute_action_plan(
    plan, 
    sessions, 
    template_id='my-custom-template'
)
```

### Scenario 3: Change LLM Response Format

Update schema and executor handles it:

```json
// In template_registry.json, change schema
"template_schema_file": "my_new_schema.json"

// Create my_new_schema.json with new structure
// Executor's generic methods handle any structure
// No code changes needed in executor
```

## Configuration-Driven Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Adding tool** | Hardcoded tool list | Auto-discovered |
| **New MCP server** | Code change required | Config only |
| **Change response format** | Executor code change | Schema change |
| **Different execution logic** | Not possible | New template config |
| **Tool name changes** | Update everywhere | Auto-discovered |

## Validation

Action plans are validated before execution:

```python
# In TemplateManager
is_valid, errors = registry.validate_action_plan(
    template_id='universal-action-plan',
    action_plan=plan
)

if not is_valid:
    for error in errors:
        print(f"Validation error: {error}")
```

Validation includes:
- Schema validation (if jsonschema installed)
- Required field checks
- Array/object structure validation
- Type checking

## Performance Considerations

- **Tool discovery cached** - Happens once per session
- **Executors cached** - Loaded once from module
- **Schema cached** - Loaded once from file
- **Template registry cached** - Loaded once from JSON

## Migration Path

Existing action plans still work:

```python
# Old code still works
results = await executor.execute(action_plan)

# New code with templates
results = await template_mgr.execute_action_plan(action_plan, sessions)
```

Both approaches use the same executor internally.

## Summary

The template-based architecture provides:

✅ **Zero Hardcoding** - Fully runtime configurable
✅ **Modular Design** - Clear separation of concerns  
✅ **Extensible** - New templates via config
✅ **Maintainable** - Single source of truth for configuration
✅ **Scalable** - Supports any number of MCP servers/templates
✅ **Validated** - Action plans validated against schema
✅ **LLM-Friendly** - Schema shared with LLM

Total code: ~400 lines, zero hardcoded values.
