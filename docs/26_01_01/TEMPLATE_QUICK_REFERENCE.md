# Template System Quick Reference

## Files and Responsibilities

| File | Purpose | Type |
|------|---------|------|
| `schema/template_registry.json` | Configuration of all templates | Config |
| `schema/action_plan_schema.json` | JSON schema for action plans | Config |
| `src/agent/template_manager.py` | Registry loader & executor manager | Code |
| `src/agent/action_plan_executor.py` | Generic action plan executor | Code |
| `src/agent/agent_simplified.py` | Main agent entry point | Code |

## Common Operations

### 1. Run Agent

```bash
cd d:\projects\ai\code-summarizer-mcp
python src/agent/agent_simplified.py
```

### 2. Add New MCP Server

Edit `agent_simplified.py` > `run_agent()`:

```python
mcp_servers_config = {
    'existing_server': {...},
    'new_server': {
        'command': 'python',
        'args': ['path/to/new_server.py']
    }
}
await run_agent(mcp_servers_config)
```

No other changes needed - executor discovers tools automatically.

### 3. Create New Executor Type

1. Create executor class:
```python
# src/agent/my_executor.py
class MyExecutor:
    def __init__(self, sessions, available_tools_cache=None):
        self.sessions = sessions
        
    async def execute(self, action_plan):
        # Implementation here
        pass
```

2. Register in `schema/template_registry.json`:
```json
{
  "templates": {
    "my-template": {
      "template_id": "my-template",
      "executor_module": "my_executor",
      "executor_class": "MyExecutor",
      "template_schema_file": "my_schema.json",
      "enabled": true
    }
  }
}
```

3. Use it:
```python
await template_mgr.execute_action_plan(plan, sessions, template_id='my-template')
```

### 4. Validate Action Plan

```python
template_mgr = TemplateManager('schema/template_registry.json')
is_valid, errors = template_mgr.registry.validate_action_plan(
    'universal-action-plan',
    action_plan
)
```

### 5. List Available Templates

```python
templates = template_mgr.registry.list_templates()
print(template_mgr.describe_templates())
```

## Action Plan Format

Minimal valid action plan:

```json
{
  "analysis": "What you want to do",
  "actions": [
    {
      "tool": "tool_name",
      "params": {"param": "value"},
      "description": "What this step does"
    }
  ]
}
```

With loop:

```json
{
  "analysis": "Process files",
  "actions": [
    {
      "tool": "list_files",
      "params": {"dir": "/path"},
      "description": "Get files"
    },
    {
      "loop_required": true,
      "loop_condition": "for each file in $result_0",
      "actions_loop": [
        {
          "tool": "process_file",
          "params": {"file": "$loop_item"}
        }
      ]
    }
  ]
}
```

With conditional:

```json
{
  "analysis": "Conditional processing",
  "actions": [
    {
      "tool": "analyze",
      "params": {"code": "..."},
      "description": "Analyze code"
    },
    {
      "condition": "$result_last.has_issues",
      "actions": [
        {
          "tool": "fix",
          "params": {"code": "$result_last.refactored_code"}
        }
      ]
    }
  ]
}
```

## Variable References in Parameters

| Reference | Meaning | Example |
|-----------|---------|---------|
| `$result_0` | First tool's output | `"code": "$result_0"` |
| `$result_last` | Last tool's output | `"code": "$result_last"` |
| `$result_last.field` | Field from last result | `"code": "$result_last.refactored_code"` |
| `$loop_item` | Current loop item | `"file": "$loop_item"` |
| `$loop_item_file` | Outer loop item | `"file": "$loop_item_file"` |

## Executor Config Settings

In `template_registry.json` > `executor_config`:

```json
{
  "timeout_seconds": 300,
  "max_nested_loops": 5,
  "max_steps": 1000,
  "enable_caching": true
}
```

| Setting | Purpose | Default |
|---------|---------|---------|
| `timeout_seconds` | Max execution time | 300 |
| `max_nested_loops` | Max loop nesting level | 5 |
| `max_steps` | Max action steps allowed | 1000 |
| `enable_caching` | Cache discovered tools | true |

## Troubleshooting

### "Template not found"
Check `template_registry.json` has the template_id with `"enabled": true`

### "Executor module not found"
Check `executor_module` path is correct, relative to Python path

### "Tool not found"
- Check tool exists in one of the connected MCP servers
- Run agent and check "Found X tools" message
- Verify server is actually running

### "Validation error"
- Check action plan matches schema in `schema/action_plan_schema.json`
- Ensure required fields present: `analysis`, `actions`
- Check JSON is valid

## Performance Tips

1. **Reuse sessions** - Keep MCP sessions open across executions
2. **Cache tools** - Tool discovery happens once, cached automatically
3. **Limit steps** - Set reasonable `max_steps` in config
4. **Async execution** - All operations are async, can run many in parallel

## Best Practices

1. **Use descriptive analysis** - LLM uses this to understand workflow
2. **Add descriptions to steps** - Makes debugging easier
3. **Use variable references** - Connect steps together with `$result_X`
4. **Validate before executing** - Use `validate_action_plan()`
5. **Keep loops simple** - Nested loops beyond 2 levels are hard to debug
6. **Test with small plans first** - Start simple, add complexity gradually
