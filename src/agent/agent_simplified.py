"""
Simplified AI Code Agent using Template-Based Action Plan Execution
- Clean separation of concerns: planning vs execution
- Fully dynamic tool discovery and execution
- Configuration-driven template management
- Templates loaded from registry configuration
"""

import os
import asyncio
import json
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.agent.template_manager import TemplateManager

# Setup Local LLM
client_llm = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")


def clean_json_response(text: str) -> str:
    """Remove comments and syntax errors from LLM JSON response."""
    import re
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    text = re.sub(r':\s*(\$[\w._-]+)([,}\]])', r': "\1"\2', text)
    return text.strip()


def load_schema(schema_path):
    """Load JSON schema for validation"""
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            return json.load(f)
    return None


async def run_agent(mcp_servers_config=None):
    """
    Run the AI agent with template-based action planning.
    
    Args:
        mcp_servers_config: Optional dict with server configurations
    """
    if mcp_servers_config is None:
        # Default configuration
        mcp_servers_config = {
            'llm_mcp': {
                'command': 'python',
                'args': ['src/mcp/llm_mcp.py']
            },
            'code_modifier_mcp': {
                'command': 'python',
                'args': ['src/mcp/code_modifier_mcp.py']
            }
        }
    
    sessions = {}
    available_tools_cache = {}
    
    # Connect to all configured MCP servers
    print("Connecting to MCP servers...")
    for server_name, server_config in mcp_servers_config.items():
        print(f"  Connecting to {server_name}...")
        try:
            params = StdioServerParameters(
                command=server_config['command'],
                args=server_config['args']
            )
            
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    sessions[server_name] = session
                    
                    # Discover tools from this server
                    try:
                        tools_list = await session.list_tools()
                        available_tools_cache[server_name] = {tool.name for tool in tools_list.tools}
                        print(f"    Found {len(tools_list.tools)} tools")
                    except Exception as e:
                        print(f"    Warning: Could not list tools: {e}")
                    
                    # ===== CRITICAL: Keep session alive for action execution =====
                    # Instead of exiting the context, we need to keep the connection open
                    # This is where the agent runs and uses the tools
                    
                    print("--- Interactive AI Code Agent ---")
                    print(f"Connected to {len(sessions)} MCP servers\n")
                    
                    # Get user request
                    user_request = input("What would you like me to do? ").strip()
                    if not user_request:
                        user_request = "Analyze the code in D:/projects/ai/code-summarizer-mcp/sample/ and fix functions with issues"
                        print(f"[Using default: {user_request}]\n")
                    
                    # Build tools description for LLM
                    tools_desc = "Available tools:\n"
                    for server_name, tools in available_tools_cache.items():
                        for tool_name in sorted(tools):
                            tools_desc += f"  - {tool_name}\n"
                    
                    # Step 1: Ask LLM to analyze request and generate action plan
                    print("[Analyzing request with LLM...]\n")
                    
                    llm_prompt = f"""You are an AI assistant that creates action plans for code analysis and refactoring.

{tools_desc}

USER REQUEST: {user_request}

RESPOND WITH ONLY VALID JSON (no markdown, no comments) following this structure:
{{
  "analysis": "brief description of what will be done",
  "actions": [
    {{"tool": "tool_name", "params": {{}}, "description": "what this does"}},
    {{"loop_required": true, "loop_condition": "for each item in $result_0", "actions_loop": [...]}},
    {{"condition": "$result_last.field_name", "actions": [...]}}
  ]
}}

Rules:
1. Use ONLY the available tools listed above
2. NO comments in JSON
3. ALL parameter values must be quoted strings
4. Use $result_0, $result_last, $loop_item for variable references
5. Nested field refs: $result_last.any_field_name
6. Return ONLY the JSON object, nothing else"""

                    response = client_llm.chat.completions.create(
                        model="phi4-mini-model-quantized-to",
                        messages=[{"role": "user", "content": llm_prompt}],
                        temperature=0.1,
                        max_tokens=2000
                    )
                    
                    response_text = response.choices[0].message.content
                    
                    # Clean and parse JSON
                    try:
                        clean_text = clean_json_response(response_text)
                        action_plan = json.loads(clean_text)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing LLM response: {e}")
                        print(f"Response: {response_text[:500]}")
                        return
                    
                    print(f"Analysis: {action_plan.get('analysis')}")
                    print(f"Actions: {len(action_plan.get('actions', []))}\n")
                    
                    # Confirm execution
                    confirm = input("Execute this plan? (yes/no): ").strip().lower()
                    if confirm not in ['yes', 'y']:
                        print("Plan cancelled.")
                        return
                    
                    # Step 2: Execute action plan using template manager
                    print("\n--- Executing Action Plan ---\n")
                    
                    try:
                        # Initialize template manager
                        registry_path = os.path.join(os.path.dirname(__file__), '..', '..', 'schema', 'template_registry.json')
                        template_mgr = TemplateManager(registry_path)
                        
                        # Execute using template manager (handles executor instantiation)
                        results = await template_mgr.execute_action_plan(action_plan, sessions)
                        
                        print("--- Execution Results ---")
                        for step, result in list(results.items())[:5]:  # Show first 5 results
                            print(f"\n{step}:")
                            print(str(result)[:200])
                    except Exception as e:
                        print(f"Execution error: {e}")
        
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    asyncio.run(run_agent())
