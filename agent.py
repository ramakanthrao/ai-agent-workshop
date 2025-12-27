import os
import asyncio
import json
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 1. Setup Local LLM (LM Studio)
client_llm = OpenAI(base_url="http://localhost:1234", api_key="lm-studio")

async def execute_action_plan(sessions, actions, context):
    """Executes a sequence of actions returned by analyze_request."""
    results = {}
    
    for i, action in enumerate(actions):
        tool_name = action.get('tool')
        params = action.get('params', {})
        description = action.get('description', '')
        
        print(f"\n[Step {i+1}] {description}")
        print(f"  Tool: {tool_name}")
        print(f"  Original Params: {params}")
        
        try:
            # Replace context variables and placeholder text in params
            resolved_params = {}
            for key, value in params.items():
                if isinstance(value, str):
                    # Handle placeholders like '<extracted code of devide>'
                    if value.startswith('<') and value.endswith('>'):
                        # This is a placeholder, try to replace with last result
                        if 'result_' + str(i-1) in context:
                            resolved_params[key] = context[f'result_{i-1}']
                        else:
                            resolved_params[key] = value
                    # Handle context references like '$result_0'
                    elif value.startswith('$'):
                        var_name = value[1:]
                        resolved_params[key] = context.get(var_name, value)
                    else:
                        resolved_params[key] = value
                else:
                    resolved_params[key] = value
            
            print(f"  Resolved Params: {resolved_params}")
            
            # Try tool in both sessions - try code_modifier_mcp first for code tools
            result = None
            session_used = None
            
            # Define which tools belong to which server
            code_tools = {'get_function_source', 'write_back_to_file', 'list_files_in_directory', 'list_functions_in_file'}
            llm_tools = {'analyze_request', 'ask_llm_to_refactor'}
            
            # Prefer the correct server
            if tool_name in code_tools:
                preferred_order = ['code_modifier_mcp', 'llm_mcp']
            elif tool_name in llm_tools:
                preferred_order = ['llm_mcp', 'code_modifier_mcp']
            else:
                preferred_order = list(sessions.keys())
            
            for session_name in preferred_order:
                if session_name not in sessions:
                    continue
                try:
                    result = await sessions[session_name].call_tool(tool_name, resolved_params)
                    session_used = session_name
                    print(f"  Server: {session_name}")
                    break
                except Exception as e:
                    continue
            
            if result is None:
                raise Exception(f"Tool '{tool_name}' not found in any MCP server")
            
            result_text = result.content[0].text
            results[f"step_{i}"] = result_text
            context[f"result_{i}"] = result_text
            
            print(f"  Result: {result_text[:200]}...")
            
        except Exception as e:
            print(f"  Error: {str(e)}")
            results[f"step_{i}"] = f"Error: {str(e)}"
    
    return results

async def run_agent():
    # Connect to both MCP servers
    sessions = {}
    
    # Connect to llm_mcp.py
    print("Connecting to llm_mcp.py...")
    llm_params = StdioServerParameters(
        command="python",
        args=["llm_mcp.py"],
    )
    
    # Connect to code_modifier_mcp.py
    print("Connecting to code_modifier_mcp.py...")
    code_params = StdioServerParameters(
        command="python",
        args=["code_modifier_mcp.py"],
    )
    
    async with stdio_client(llm_params) as (llm_read, llm_write):
        async with ClientSession(llm_read, llm_write) as llm_session:
            await llm_session.initialize()
            sessions['llm_mcp'] = llm_session
            
            async with stdio_client(code_params) as (code_read, code_write):
                async with ClientSession(code_read, code_write) as code_session:
                    await code_session.initialize()
                    sessions['code_modifier_mcp'] = code_session
                    
                    print("--- Interactive AI Code Agent ---")
                    print(f"Connected to {len(sessions)} MCP servers")
                    
                    # Get user request
                    user_request = input("\nWhat would you like me to do? ").strip()
                    
                    # Step 1: Analyze the request
                    print("\n[Analyzing Request...]")
                    analysis_result = await llm_session.call_tool("analyze_request", {
                        "user_prompt": user_request
                    })
                    
                    # Extract text content from result
                    analysis_text = analysis_result.content[0].text if hasattr(analysis_result.content[0], 'text') else str(analysis_result.content[0])
                    print(f"\nAnalysis Result:\n{analysis_text}\n")
                    
                    # Remove markdown code fences if present
                    analysis_text = analysis_text.strip()
                    if analysis_text.startswith("```"):
                        analysis_text = analysis_text.split("```")[1]
                        if analysis_text.startswith("json"):
                            analysis_text = analysis_text[4:]
                        analysis_text = analysis_text.strip()
                    
                    # Parse the JSON response
                    try:
                        action_plan = json.loads(analysis_text)
                    except json.JSONDecodeError:
                        print("Error: Could not parse LLM response as JSON")
                        print("Creating fallback action plan...\n")
                        
                        # Extract file path and function name from user request
                        import re
                        file_match = re.search(r'[D:][/\\].*?\.py', user_request, re.IGNORECASE)
                        file_path = file_match.group(0) if file_match else "tools.py"
                        
                        func_match = re.search(r'(function|func)\s+(\w+)', user_request, re.IGNORECASE)
                        func_name = func_match.group(2) if func_match else "divide" if "divide" in user_request.lower() or "devide" in user_request.lower() else "add"
                        
                        # Fallback action plan
                        action_plan = {
                            "analysis": "User wants to analyze and fix a specific function",
                            "actions": [
                                {
                                    "tool": "get_function_source",
                                    "params": {"file_path": file_path, "function_name": func_name},
                                    "description": f"Extract function '{func_name}' from file"
                                },
                                {
                                    "tool": "ask_llm_to_refactor",
                                    "params": {"original_code": "$result_0"},
                                    "description": "Refactor and fix the function"
                                },
                                {
                                    "tool": "write_back_to_file",
                                    "params": {"file_path": file_path, "function_name": func_name, "new_code": "$result_1"},
                                    "description": "Write fixed function back to file"
                                }
                            ]
                        }
                    
                    print(f"\nAnalysis: {action_plan.get('analysis')}")
                    print(f"Number of actions: {len(action_plan.get('actions', []))}")
                    
                    # Confirm with user
                    confirm = input("\nDo you want to proceed with this plan? (yes/no): ").lower()
                    if confirm not in ['yes', 'y']:
                        print("Plan cancelled.")
                        return
                    
                    # Step 2: Execute the action plan
                    print("\n--- Executing Action Plan ---")
                    context = {"user_request": user_request}
                    results = await execute_action_plan(sessions, action_plan.get('actions', []), context)
                    
                    print("\n--- Execution Complete ---")
                    for step, result in results.items():
                        print(f"\n{step}:")
                        print(result[:500])

if __name__ == "__main__":
    asyncio.run(run_agent())