import os
import asyncio
import json
from openai import OpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 1. Setup Local LLM (LM Studio)
client_llm = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

def clean_json_response(text: str) -> str:
    """Remove comments and invalid syntax from LLM JSON response."""
    import re
    
    # Remove JavaScript-style comments (// ...)
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    
    # Remove CSS-style comments (/* ... */)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    # Remove trailing commas before } or ]
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    
    # Fix unquoted string values that are variable references (e.g., $result_last)
    # Match pattern like: "key": $variable_reference
    text = re.sub(r':\s*(\$[\w._-]+)([,}\]])', r': "\1"\2', text)
    
    # Fix unquoted boolean/null at end or before comma/bracket
    # But be careful not to match numbers or true/false in the right context
    text = re.sub(r':\s*(true|false|null)([,}\]])', r': \1\2', text)
    
    return text.strip()

def detect_path_type(path_str):
    """Detect if a path is a file or directory and return the type."""
    path = path_str.strip()
    
    # Check if it exists
    if os.path.exists(path):
        if os.path.isdir(path):
            return 'directory', path
        elif os.path.isfile(path):
            return 'file', path
    
    # If doesn't exist, infer from extension
    if path.endswith('.py'):
        return 'file', path
    else:
        return 'directory', path

def validate_action_plan(actions):
    """Validates an action plan for common errors before execution."""
    errors = []
    warnings = []
    
    for i, action in enumerate(actions):
        tool_name = action.get('tool', '')
        params = action.get('params', {})
        
        # Check for required parameters
        if tool_name == 'get_function_source':
            if 'file_path' not in params:
                errors.append(f"Step {i+1}: {tool_name} missing required parameter 'file_path'")
            if 'function_name' not in params:
                errors.append(f"Step {i+1}: {tool_name} missing required parameter 'function_name'")
        
        elif tool_name == 'write_back_to_file':
            if 'file_path' not in params:
                errors.append(f"Step {i+1}: {tool_name} missing required parameter 'file_path'")
            if 'function_name' not in params:
                errors.append(f"Step {i+1}: {tool_name} missing required parameter 'function_name'")
            if 'new_code' not in params:
                errors.append(f"Step {i+1}: {tool_name} missing required parameter 'new_code'")
        
        elif tool_name == 'list_files_in_directory':
            if 'directory_path' not in params:
                errors.append(f"Step {i+1}: {tool_name} missing required parameter 'directory_path'")
            else:
                # Check if directory_path looks like a file (ends in .py)
                dir_path = params['directory_path']
                if isinstance(dir_path, str) and dir_path.endswith('.py'):
                    errors.append(f"Step {i+1}: {tool_name} called with file path '{dir_path}' - should use 'list_functions_in_file' instead")
        
        elif tool_name == 'list_functions_in_file':
            if 'file_path' not in params:
                errors.append(f"Step {i+1}: {tool_name} missing required parameter 'file_path'")
            else:
                # Warn if path doesn't end in .py
                file_path = params['file_path']
                if isinstance(file_path, str) and not file_path.endswith('.py'):
                    warnings.append(f"Step {i+1}: {tool_name} called with path '{file_path}' - may not be a Python file")
        
        elif tool_name == 'ask_llm_to_refactor':
            if 'original_code' not in params:
                errors.append(f"Step {i+1}: {tool_name} missing required parameter 'original_code'")
        
        elif tool_name == 'ask_llm_to_analyze_code':
            if 'original_code' not in params:
                errors.append(f"Step {i+1}: {tool_name} missing required parameter 'original_code'")
    
    return errors, warnings

async def execute_action_plan(sessions, actions, context):
    """Executes a sequence of actions returned by analyze_request, with support for loops and conditionals."""
    import difflib
    results = {}
    step_counter = 0
    step_history = {}  # Track steps for better reference resolution
    
    async def execute_actions_recursive(action_list, indent_level=0, loop_item=None):
        """Recursively execute actions, handling nested loops and conditionals."""
        nonlocal step_counter
        
        for action in action_list:
            # Handle loop actions
            if action.get('loop_required'):
                loop_condition = action.get('loop_condition', '')
                loop_actions = action.get('actions_loop', [])
                
                print(f"\n[Loop: {loop_condition}]")
                
                # Extract items to loop over from context
                loop_items = []
                loop_condition_str = str(loop_condition)
                
                # Parse the loop condition to find the data source (e.g., "$result_0")
                for i in range(step_counter + 1):
                    var_name = f'result_{i}'
                    if f'${var_name}' in loop_condition_str:
                        result_data = context.get(var_name, '').strip()
                        # Split by newlines to get individual items
                        loop_items = [item.strip() for item in result_data.split('\n') if item.strip()]
                        print(f"  Found {len(loop_items)} items to process: {loop_items[:3]}...")
                        break
                
                # If no items found, try to get from most recent result
                if not loop_items and 'result_last' in context:
                    result_data = context.get('result_last', '').strip()
                    loop_items = [item.strip() for item in result_data.split('\n') if item.strip()]
                
                # Execute loop actions for each item
                for item in loop_items:
                    print(f"\n  [Loop iteration: {item}]")
                    # Update context with loop item
                    context['loop_item'] = item
                    await execute_actions_recursive(loop_actions, indent_level + 1, loop_item=item)
                    
            # Handle conditional actions
            elif action.get('condition') is not None:
                condition = action.get('condition')
                conditional_actions = action.get('actions', [])
                
                print(f"\n[Conditional: {condition}]")
                
                # Simple condition evaluation
                should_execute = False
                
                # If condition is boolean, use it directly
                if isinstance(condition, bool):
                    should_execute = condition
                # If condition is a reference like $result_last.condition, extract it
                elif isinstance(condition, str) and condition.startswith('$'):
                    # Extract the reference (e.g., $result_last -> result_last)
                    var_ref = condition[1:]  # Remove $
                    
                    # Check if it's asking for a nested field (e.g., $result_last.condition)
                    if '.' in var_ref:
                        parts = var_ref.split('.')
                        result_key = parts[0]
                        field_name = parts[1]
                        
                        # Get the result object
                        result_obj = context.get(result_key)
                        
                        # If it's a JSON string, parse it
                        if isinstance(result_obj, str):
                            try:
                                result_obj = json.loads(result_obj)
                            except json.JSONDecodeError:
                                result_obj = {}
                        
                        # Extract the field value
                        if isinstance(result_obj, dict) and field_name in result_obj:
                            should_execute = result_obj[field_name]
                            print(f"  Extracted condition from {result_key}.{field_name}: {should_execute}")
                        else:
                            print(f"  Warning: Could not extract {field_name} from {result_key}")
                    else:
                        # Just reference the variable
                        result_obj = context.get(var_ref)
                        should_execute = result_obj if isinstance(result_obj, bool) else bool(result_obj)
                else:
                    # String condition evaluation: check if keywords appear in recent results
                    condition_lower = str(condition).lower()
                    
                    # Check last few results for condition keywords
                    for i in range(max(0, step_counter - 3), step_counter + 1):
                        result_key = f'result_{i}'
                        if result_key in context:
                            result_obj = context[result_key]
                            
                            # If it's a JSON object with 'condition' field, use that
                            if isinstance(result_obj, str):
                                try:
                                    result_obj = json.loads(result_obj)
                                except json.JSONDecodeError:
                                    pass
                            
                            if isinstance(result_obj, dict) and 'condition' in result_obj:
                                should_execute = result_obj['condition']
                                print(f"  Found condition field in {result_key}: {should_execute}")
                                break
                            
                            # Fallback to keyword matching
                            result_text = str(result_obj).lower()
                            if any(keyword in result_text for keyword in ['issue', 'error', 'bug', 'problem', 'critical', 'severe', 'fix', 'refactor']):
                                should_execute = True
                                break
                
                if should_execute:
                    print(f"  Condition met, executing conditional actions...")
                    await execute_actions_recursive(conditional_actions, indent_level + 1)
                else:
                    print(f"  Condition not met, skipping...")
            else:
                # Regular action - execute it
                step_counter += 1
                tool_name = action.get('tool')
                params = action.get('params', {})
                description = action.get('description', '')
                
                # Skip if tool is None or empty
                if not tool_name:
                    print(f"\n[Step {step_counter}] {description}")
                    print(f"  Warning: No tool specified, skipping this action")
                    continue
                
                print(f"\n[Step {step_counter}] {description}")
                print(f"  Tool: {tool_name}")
                print(f"  Original Params: {params}")
                
                try:
                    # Resolve context variables in params
                    resolved_params = {}
                    for key, value in params.items():
                        if isinstance(value, str):
                            # Handle nested field references like $loop_item.function_name or $result_last.field
                            if '.' in value and value.startswith('$'):
                                var_ref = value[1:]  # Remove $
                                parts = var_ref.split('.')
                                base_var = parts[0]
                                field_name = parts[1]
                                
                                # Get the base variable
                                if base_var == 'loop_item':
                                    # loop_item is a simple string value
                                    if loop_item:
                                        # For simple strings like loop_item, just use the value itself
                                        resolved_params[key] = loop_item
                                    else:
                                        resolved_params[key] = value
                                else:
                                    # Try to get from context (e.g., result_0, result_last)
                                    base_obj = context.get(base_var)
                                    if isinstance(base_obj, dict) and field_name in base_obj:
                                        resolved_params[key] = base_obj[field_name]
                                    elif isinstance(base_obj, str):
                                        # If base_obj is already a string (plain text result), use it
                                        # The field_name request is likely a mistake by the LLM
                                        print(f"  Note: {base_var} is plain text, using full result instead of {field_name}")
                                        resolved_params[key] = base_obj
                                    else:
                                        print(f"  Warning: Could not resolve {value}")
                                        # Fallback: if it looks like they want the last result, just use it
                                        if base_var == 'result_last' or base_var.startswith('result_'):
                                            resolved_params[key] = base_obj if base_obj else value
                                        else:
                                            resolved_params[key] = value
                            # Handle $loop_item reference
                            elif value == '$loop_item' and loop_item:
                                resolved_params[key] = loop_item
                            # Handle $result_last reference
                            elif value == '$result_last' and 'result_last' in context:
                                result_value = context['result_last']
                                # If it's a JSON object with refactored_code (from ask_llm_to_refactor), extract it
                                if isinstance(result_value, dict) and 'refactored_code' in result_value:
                                    resolved_params[key] = result_value['refactored_code']
                                else:
                                    resolved_params[key] = result_value
                            # Handle negative indexing like $result_-1, $result_-2
                            elif value.startswith('$result_-'):
                                try:
                                    offset = int(value.split('_')[1])
                                    ref_step = step_counter + offset
                                    if ref_step >= 0 and ref_step < step_counter:
                                        ref_value = context.get(f'result_{ref_step}', value)
                                        # If it's a JSON object with refactored_code, extract it
                                        if isinstance(ref_value, dict) and 'refactored_code' in ref_value:
                                            resolved_params[key] = ref_value['refactored_code']
                                        else:
                                            resolved_params[key] = ref_value
                                        if ref_value == value:
                                            print(f"  Warning: Could not resolve {value} (step {ref_step} not found)")
                                    else:
                                        print(f"  Warning: Invalid reference {value} (step {ref_step} out of range)")
                                        resolved_params[key] = value
                                except Exception as e:
                                    print(f"  Warning: Error parsing reference {value}: {e}")
                                    resolved_params[key] = value
                            # Handle context references like '$result_0'
                            elif value.startswith('$'):
                                var_name = value[1:]
                                resolved_value = context.get(var_name, value)
                                # If it's a JSON object with refactored_code, extract it
                                if isinstance(resolved_value, dict) and 'refactored_code' in resolved_value:
                                    resolved_params[key] = resolved_value['refactored_code']
                                else:
                                    resolved_params[key] = resolved_value
                                if resolved_value == value and var_name.startswith('result_'):
                                    print(f"  Warning: Reference {value} not found in context")
                            # Handle placeholders like '<extracted code>'
                            elif value.startswith('<') and value.endswith('>'):
                                if f'result_{step_counter-1}' in context:
                                    resolved_params[key] = context[f'result_{step_counter-1}']
                                else:
                                    resolved_params[key] = value
                            else:
                                resolved_params[key] = value
                        else:
                            resolved_params[key] = value
                    
                    # Use corrected function name if available
                    if 'corrected_function_name' in context and 'function_name' in resolved_params:
                        resolved_params['function_name'] = context['corrected_function_name']
                    
                    print(f"  Resolved Params: {resolved_params}")
                    
                    # Try tool in both sessions
                    result = None
                    session_used = None
                    
                    # Define which tools belong to which server
                    code_tools = {'get_function_source', 'write_back_to_file', 'list_files_in_directory', 'list_functions_in_file', 'is_input_a_directory', 'is_input_a_file', 'read_directory_for_files'}
                    llm_tools = {'analyze_request', 'ask_llm_to_refactor', 'ask_llm_to_analyze_code'}
                    
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
                    
                    # Special handling: if function not found, try to find closest match
                    if tool_name == 'get_function_source' and 'not found' in result_text.lower():
                        print(f"  Function not found: {resolved_params.get('function_name')}")
                        print(f"  Attempting to find closest match...")
                        
                        # Get list of available functions
                        file_path = resolved_params.get('file_path')
                        if file_path and 'result_0' in context:
                            functions_list = context['result_0'].strip().split('\n')
                            func_name = resolved_params.get('function_name')
                            
                            # Find closest match using difflib
                            close_matches = difflib.get_close_matches(func_name, functions_list, n=1, cutoff=0.6)
                            if close_matches:
                                corrected_func = close_matches[0]
                                print(f"  Found closest match: '{corrected_func}'")
                                
                                # Retry with corrected name
                                resolved_params['function_name'] = corrected_func
                                result = await sessions[session_used].call_tool(tool_name, resolved_params)
                                result_text = result.content[0].text
                                
                                # Update context for future steps
                                context['corrected_function_name'] = corrected_func
                    
                    # Parse result as JSON if possible, otherwise keep as string
                    result_data = None
                    try:
                        result_data = json.loads(result_text)
                    except json.JSONDecodeError:
                        result_data = result_text
                    
                    # For ask_llm_to_refactor, extract the refactored_code if available
                    if tool_name == 'ask_llm_to_refactor' and isinstance(result_data, dict) and 'refactored_code' in result_data:
                        # Store the entire JSON object, but also make refactored_code easily accessible
                        actual_code = result_data['refactored_code']
                        results[f"step_{step_counter}"] = result_data
                        context[f"result_{step_counter}"] = result_data
                        context['result_last'] = result_data
                        # Also store the code separately for backwards compatibility
                        context[f"result_{step_counter}_code"] = actual_code
                        print(f"  Result: {str(result_data)[:200]}...")
                    else:
                        # Store normally
                        results[f"step_{step_counter}"] = result_data if isinstance(result_data, dict) else result_text
                        context[f"result_{step_counter}"] = result_data if isinstance(result_data, dict) else result_text
                        context['result_last'] = result_data if isinstance(result_data, dict) else result_text
                        print(f"  Result: {result_text[:200]}...")
                    
                except Exception as e:
                    print(f"  Error: {str(e)}")
                    results[f"step_{step_counter}"] = f"Error: {str(e)}"
                    
                except Exception as e:
                    print(f"  Error: {str(e)}")
                    results[f"step_{step_counter}"] = f"Error: {str(e)}"
    
    # Execute all actions
    await execute_actions_recursive(actions)
    
    return results

async def run_agent():
    # Connect to both MCP servers
    sessions = {}
    
    # Connect to llm_mcp.py
    print("Connecting to llm_mcp.py...")
    llm_params = StdioServerParameters(
        command="python",
        args=["src/mcp/llm_mcp.py"],
    )
    
    # Connect to code_modifier_mcp.py
    print("Connecting to code_modifier_mcp.py...")
    code_params = StdioServerParameters(
        command="python",
        args=["src/mcp/code_modifier_mcp.py"],
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
                    
                    # Discover available tools from both servers
                    print("\n[Discovering available tools...]")
                    tools_by_server = {}
                    
                    try:
                        # List tools from llm_mcp
                        llm_tools = await llm_session.list_tools()
                        tools_by_server['llm_mcp'] = [(tool.name, tool.inputSchema) for tool in llm_tools.tools]
                        print(f"  Found {len(llm_tools.tools)} tools in llm_mcp")
                    except Exception as e:
                        print(f"  Warning: Could not list tools from llm_mcp: {e}")
                    
                    try:
                        # List tools from code_modifier_mcp
                        code_tools = await code_session.list_tools()
                        tools_by_server['code_modifier_mcp'] = [(tool.name, tool.inputSchema) for tool in code_tools.tools]
                        print(f"  Found {len(code_tools.tools)} tools in code_modifier_mcp")
                    except Exception as e:
                        print(f"  Warning: Could not list tools from code_modifier_mcp: {e}")
                    
                    # Build formatted tools section from discovered tools
                    discovered_tools_text = ""
                    if tools_by_server:
                        discovered_tools_text = "Available tools:\n"
                        all_formatted_tools = []
                        
                        for server_name, tools in tools_by_server.items():
                            for tool_name, tool_schema in tools:
                                # Extract parameters from JSON schema
                                params = list(tool_schema.get("properties", {}).keys()) if tool_schema else []
                                description = tool_schema.get("description", "No description") if tool_schema else "No description"
                                params_str = ", ".join(params) if params else "no parameters"
                                all_formatted_tools.append(f"- {tool_name}({params_str}): {description}")
                        
                        all_formatted_tools.sort()
                        discovered_tools_text += "\n".join(all_formatted_tools)
                    
                    # Get user request (with default if empty)
                    default_input = "analyse the code of : D:/projects/ai/code-summarizer-mcp/sample/ and fix the function which has issues"
                    user_request = input("\nWhat would you like me to do? ").strip()
                    if not user_request:
                        user_request = default_input
                        print(f"[Using default input: {user_request}]")
                    
                    # Step 1: Analyze the request with discovered tools
                    print("\n[Analyzing Request...]")
                    analysis_result = await llm_session.call_tool("analyze_request", {
                        "user_prompt": user_request,
                        "available_tools": discovered_tools_text
                    })
                    print("\n[Analysis complete...]")
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
                        # Clean JSON before parsing (remove comments and invalid syntax)
                        clean_text = clean_json_response(analysis_text)
                        action_plan = json.loads(clean_text)
                    except json.JSONDecodeError as e:
                        # Parsing failed even after cleaning
                        print("Error parsing JSON from analysis result.")
                        print(f"Parse error: {e}")
                        print("\nAttempted to parse:")
                        print(analysis_text[:500])  # Show first 500 chars
                        action_plan = {}
                    print(f"\nAnalysis: {action_plan.get('analysis')}")
                    print(f"Number of actions: {len(action_plan.get('actions', []))}")
                    
                    # Validate the action plan
                    print("\n[Validating Action Plan...]")
                    errors, warnings = validate_action_plan(action_plan.get('actions', []))
                    
                    if errors:
                        print("\n❌ VALIDATION ERRORS FOUND:")
                        for error in errors:
                            print(f"  - {error}")
                        print("\nThe LLM generated an invalid action plan. Cancelling execution.")
                        print("Hint: The system prompt may need additional examples or clarification.")
                        return
                    
                    if warnings:
                        print("\n[VALIDATION WARNINGS]")
                        for warning in warnings:
                            print(f"  - {warning}")
                    
                    if not errors:
                        print("[OK] Action plan validation passed!")
                    
                    # Confirm with user (auto-confirm for fallback)
                    if "Analysis Error" in analysis_text or "could not parse" in analysis_text.lower():
                        print("\nUsing fallback plan (auto-confirmed)")
                        confirm = 'y'
                    else:
                        confirm = input("\nDo you want to proceed with this plan? (Yes/no): ").lower()
                    
                    if confirm in ['No','no', 'N', 'n']:
                        print("Plan cancelled.")
                        return
                    
                    # Step 2: Execute the action plan
                    print("\n--- Executing Action Plan ---")
                    context = {"user_request": user_request}
                    results = await execute_action_plan(sessions, action_plan.get('actions', []), context)
                    
                    print("\n--- Execution Complete ---")
                    for step, result in results.items():
                        print(f"\n{step}:")
                        # Handle both string and dict results
                        if isinstance(result, str):
                            print(result[:500])
                        else:
                            print(str(result)[:500])

if __name__ == "__main__":
    asyncio.run(run_agent())