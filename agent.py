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
        print(f"  Params: {params}")
        
        try:
            # Replace context variables in params
            resolved_params = {}
            for key, value in params.items():
                if isinstance(value, str) and value.startswith('$'):
                    # Reference to previous result
                    resolved_params[key] = context.get(value[1:], value)
                else:
                    resolved_params[key] = value
            
            # Try tool in both sessions
            result = None
            for session_name, session in sessions.items():
                try:
                    result = await session.call_tool(tool_name, resolved_params)
                    print(f"  Server: {session_name}")
                    break
                except Exception:
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
                        print("Raw response:", analysis_text)
                        return
                    
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