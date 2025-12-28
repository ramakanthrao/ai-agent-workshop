from mcp.server.fastmcp import FastMCP
import ast
import requests
import json
import logging
import sys

# Configure logging to print to stderr (not stdout, which is used for JSONRPC)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("llm_mcp")

# Initialize FastMCP server
mcp = FastMCP("CodeSummarizer")

# LM Studio Configuration
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODELS_URL = "http://localhost:1234/v1/models"

# Cache for available tools from all MCP servers
_cached_model_id = 'phi4-mini-model-quantized-to'
_available_tools_cache = None

def get_model_id():
    """Get the first available model from LM Studio."""
    global _cached_model_id
    if _cached_model_id:
        return _cached_model_id
    
    try:
        response = requests.get(MODELS_URL, timeout=10)
        response.raise_for_status()
        models = response.json().get('data', [])
        if models:
            _cached_model_id = models[0].get('id', 'phi4-mini-model-quantized-to')
            return _cached_model_id
    except Exception:
        pass
    
    return 'phi4-mini-model-quantized-to'  # Fallback

def format_tool_for_prompt(tool_name: str, tool_input_schema: dict) -> str:
    """Format a single tool with its parameters for the LLM prompt."""
    # Extract parameter names from JSON schema
    schema_properties = tool_input_schema.get("properties", {})
    params = list(schema_properties.keys())
    
    # Try to get description
    description = tool_input_schema.get("description", "No description available")
    
    params_str = ", ".join(params) if params else "no parameters"
    return f"- {tool_name}({params_str}): {description}"

def build_tools_section_from_schema(tools_by_server: dict) -> str:
    """
    Build the tools section from the actual tool schemas returned by MCP servers.
    tools_by_server: dict with server names as keys and lists of (tool_name, schema) tuples
    """
    tools_text = "Available tools:\n"
    
    all_tools = []
    for server_name, tools in tools_by_server.items():
        for tool_name, tool_schema in tools:
            formatted = format_tool_for_prompt(tool_name, tool_schema)
            all_tools.append(formatted)
    
    # Sort for consistent output
    all_tools.sort()
    tools_text += "\n".join(all_tools)
    return tools_text.strip()

@mcp.tool()
def analyze_request(user_prompt: str, available_tools: str = "") -> str:
    """
    Analyzes the user's request and returns structured instructions on what tools to call.
    
    Args:
        user_prompt: The user's request
        available_tools: (Optional) Pre-formatted string of available tools. If not provided,
                        uses fallback tools.
    
    Returns:
        A JSON-like string with the sequence of actions needed.
    """
    # Use provided tools or fallback
    if not available_tools or available_tools.strip() == "":
        # Build tools section from fallback
        tools_text = "Available tools:\n"
        available_tools = tools_text.strip()
    
    system_prompt = (
        "You are an intelligent code analysis coordinator. Analyze the user's request and return "
        "a structured plan of actions with optional nested loops and conditional execution. "
        "Return ONLY valid JSON (no markdown, no extra text, NO COMMENTS).\n\n"
        "ACTION STRUCTURE - You can use:\n"
        "1. REGULAR ACTIONS: {\"tool\": \"name\", \"params\": {...}, \"description\": \"what this does\"}\n"
        "2. LOOP ACTIONS: {\"loop_required\": true, \"loop_condition\": \"description\", \"actions_loop\": [...]}\n"
        "3. CONDITIONAL ACTIONS: {\"condition\": \"string or boolean\", \"actions\": [...]}\n"
        "4. REFERENCE RESULTS: Use $result_0, $result_1, $result_last, $loop_item to reference previous outputs\n\n"
        "BASIC STRUCTURE:\n"
        "{\n"
        "  \"analysis\": \"brief summary of what the user wants\",\n"
        "  \"actions\": [\n"
        "    {\"tool\": \"...\", \"params\": {...}, \"description\": \"...\"},\n"
        "    {\"loop_required\": true, \"loop_condition\": \"...\", \"actions_loop\": [...]},\n"
        "    {\"condition\": \"...\", \"actions\": [...]}\n"
        "  ]\n"
        "}\n\n"
        "LOOP ITERATION CRITICAL RULES:\n"
        "- Inside actions_loop, ALWAYS use $loop_item to reference the current item\n"
        "- NEVER use $result_0 or other indices inside a loop as they refer to initial results\n"
        "- $loop_item is automatically set to each function name (or other item) in the loop\n"
        "- Example: {\"function_name\": \"$loop_item\"} gets the current function name in the loop\n"
        "- Use $result_last to reference the result of the most recent step in the loop\n"
        "- Each loop iteration has its own context with fresh $result_last\n\n"
        "ABSOLUTELY CRITICAL - FOLLOW THESE RULES EXACTLY:\n"
        "1. Return ONLY valid JSON - NO comments like // or /* */\n"
        "2. ALL string values must be quoted with double quotes\n"
        "3. ALL parameter values must be quoted: \"key\": \"value\" (even for variables like $result_0)\n"
        "4. Return REAL VALUES, NEVER [brackets], <angles>, or placeholders\n"
        "5. Use actual values: 'multiply', 'divide', complete file paths\n"
        "6. Use $result_0, $result_1, $result_last to reference previous step results\n"
        "7. For loops: set \"loop_required\": true and nest actions in \"actions_loop\"\n"
        "8. For conditionals: set \"condition\" as a string description or boolean true/false\n"
        "9. Agent will automatically iterate loops and evaluate conditions\n"
        "10. DO NOT nest conditionals inside conditionals - only nest conditionals inside loops\n"
        "11. Do NOT include comments or explanatory text in JSON\n"
        "12. Do NOT include actions_loop if loop_required is false\n"
        "13. EVERY variable reference MUST be quoted as a string\n\n"
        "CONDITIONAL RULES:\n"
        "- condition can be a STRING like \"if analysis indicates critical issues found\"\n"
        "- condition can be a BOOLEAN like true or false\n"
        "- condition can reference a field from LLM response like \"$result_last.condition\"\n"
        "- When using $result_last.condition, the agent will extract the 'condition' field from JSON responses\n"
        "- LLM tools (ask_llm_to_analyze_code, ask_llm_to_refactor) return JSON with 'condition' field\n"
        "- String conditions are evaluated by checking if recent results contain issue keywords\n"
        "- Boolean true/false conditions are executed directly\n"
        "- Field reference conditions ($result_X.fieldname) extract and use that field value\n"
        "- All actions inside a conditional MUST be at the same nesting level\n\n"
        "RECOMMENDED APPROACH FOR LLM-BASED CONDITIONS:\n"
        "Use $result_last.condition to let the LLM decide if next step is needed:\n"
        "{\"condition\": \"$result_last.condition\", \"actions\": [...]}\n"
        "This way, the LLM that analyzed the code also decides if refactoring is needed.\n\n"
        "EXAMPLE 1 - Simple file analysis with LOOP and CONDITIONAL inside loop using LLM response condition:\n"
        "{\n"
        "  \"analysis\": \"Analyze all functions for issues and fix critical ones\",\n"
        "  \"actions\": [\n"
        "    {\"tool\": \"list_functions_in_file\", \"params\": {\"file_path\": \"D:/path/tools.py\"}, \"description\": \"List all functions\"},\n"
        "    {\n"
        "      \"loop_required\": true,\n"
        "      \"loop_condition\": \"for each function returned in $result_0\",\n"
        "      \"actions_loop\": [\n"
        "        {\"tool\": \"get_function_source\", \"params\": {\"file_path\": \"D:/path/tools.py\", \"function_name\": \"$loop_item\"}, \"description\": \"Get function source\"},\n"
        "        {\"tool\": \"ask_llm_to_analyze_code\", \"params\": {\"original_code\": \"$result_last\"}, \"description\": \"Analyze for issues\"},\n"
        "        {\"condition\": \"$result_last.condition\", \"actions\": [\n"
        "          {\"tool\": \"ask_llm_to_refactor\", \"params\": {\"original_code\": \"$result_-2\"}, \"description\": \"Fix code\"},\n"
        "          {\"tool\": \"write_back_to_file\", \"params\": {\"file_path\": \"D:/path/tools.py\", \"function_name\": \"$loop_item\", \"new_code\": \"$result_last\"}, \"description\": \"Save fixed code\"}\n"
        "        ]}\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "EXAMPLE 2 - With condition referencing specific result index:\n"
        "{\n"
        "  \"analysis\": \"Analyze and conditionally fix each function\",\n"
        "  \"actions\": [\n"
        "    {\"tool\": \"list_functions_in_file\", \"params\": {\"file_path\": \"D:/path/file.py\"}, \"description\": \"List functions\"},\n"
        "    {\n"
        "      \"loop_required\": true,\n"
        "      \"loop_condition\": \"for each function in result 0\",\n"
        "      \"actions_loop\": [\n"
        "        {\"tool\": \"get_function_source\", \"params\": {\"file_path\": \"D:/path/file.py\", \"function_name\": \"$loop_item\"}, \"description\": \"Get function\"},\n"
        "        {\"tool\": \"ask_llm_to_analyze_code\", \"params\": {\"original_code\": \"$result_last\"}, \"description\": \"Analyze\"},\n"
        "        {\"condition\": \"$result_last.condition\", \"actions\": [\n"
        "          {\"tool\": \"ask_llm_to_refactor\", \"params\": {\"original_code\": \"$result_-2\"}, \"description\": \"Refactor\"},\n"
        "          {\"tool\": \"write_back_to_file\", \"params\": {\"file_path\": \"D:/path/file.py\", \"function_name\": \"$loop_item\", \"new_code\": \"$result_last\"}, \"description\": \"Write fixed code\"}\n"
        "        ]}\n"
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        "REFERENCE VARIABLE RULES:\n"
        "1. $loop_item = current item in loop iteration - use this in actions_loop for the current item\n"
        "2. $result_0, $result_1, $result_2... = output from step at that absolute index (OUTSIDE loops)\n"
        "3. $result_last = output from the most recent executed step\n"
        "4. $result_-1, $result_-2 = relative references (1 or 2 steps back)\n"
        "5. IMPORTANT: Inside a loop, use $loop_item, NOT $result_0 or other indices\n"
        "6. Example: In loop actions, use {\"function_name\": \"$loop_item\"} to reference the current function\n"
        "7. Example: To reference analyzed code: {\"original_code\": \"$result_last\"}\n"
        "8. NESTED FIELDS: Use {\"field\": \"$variable.fieldname\"} to extract specific fields from JSON responses\n"
        "9. Example: {\"original_code\": \"$result_last.refactored_code\"} to extract refactored_code field\n"
        "10. ALL values must be quoted as strings in JSON: \"key\": \"$variable\" (with quotes around variable)\n\n"
        "4. $result_-1, $result_-2 = relative references (1 or 2 steps back) - MUST be quoted\n"
        "5. Example: \"original_code\": \"$result_-2\" (with quotes)\n"
        "6. Example: \"function_name\": \"$loop_item\" (with quotes)\n\n"
        "WORKFLOW GUIDANCE:\n"
        "1. PATHS: If ends with .py it's FILE, else it's DIRECTORY\n"
        "2. FILE ANALYSIS: list_functions_in_file -> LOOP -> get_function_source -> analyze -> CONDITIONAL fix\n"
        "3. Use LOOP for processing multiple items (functions, files, etc.)\n"
        "4. Use CONDITIONAL inside LOOP for if-then logic (fix only if issues found)\n"
        "5. NEVER use list_files_in_directory on .py files - use list_functions_in_file\n"
        "6. ALWAYS include function_name in get_function_source\n"
        "7. ALWAYS use complete file paths\n"
        "8. NEVER include extra fields like actions_loop when loop_required is false\n"
        "9. Keep action structure simple and clean\n\n"
        f"{available_tools}"
    )

    payload = {
        "model": get_model_id(),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3
    }

    try:
        logger.info(f"Sending analyze_request to LM Studio using model: {get_model_id()}")
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=300)
        logger.info(f"Received response from analyze_request: {response.status_code}")
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        logger.info(f"Successfully analyzed request, returning action plan")
        return content.strip()
    except Exception as e:
        logger.error(f"Error in analyze_request: {str(e)}")
        return f"Analysis Error: {str(e)}"


@mcp.tool()
def ask_llm_to_refactor(original_code: str) -> str:
    """Sends code to LM Studio to fix its logic and returns JSON with condition."""
    logger.info(f"ask_llm_to_refactor called with code of length: {len(original_code)}")
    prompt = (
        "You are a code refactoring assistant. Your task is to analyze and correct Python code.\n\n"
        f"Original Code:\n{original_code}\n\n"
        "Return ONLY valid JSON (no markdown, no extra text) with this structure:\n"
        "{\n"
        "  \"refactored_code\": \"<the corrected Python code>\",\n"
        "  \"condition\": true or false,\n"
        "  \"reason\": \"<brief explanation of changes or why no changes needed>\"\n"
        "}\n\n"
        "Set condition to true if you made improvements to the code, false if code is already correct.\n"
        "The refactored_code should be the complete corrected code or the original if no changes needed."
    )

    payload = {
        "model": get_model_id(),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    try:
        logger.info(f"Sending refactor request to LM Studio")
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=180)
        logger.info(f"Received refactor response: {response.status_code}")
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        logger.info(f"Successfully refactored code")
        # Parse and clean JSON response
        cleaned = content.replace("```json", "").replace("```", "").strip()
        try:
            return json.dumps(json.loads(cleaned))
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse refactor response as JSON, returning as-is")
            return cleaned
    except Exception as e:
        logger.error(f"Error in ask_llm_to_refactor: {str(e)}")
        return json.dumps({"error": str(e), "condition": False, "refactored_code": original_code})

@mcp.tool()
def ask_llm_to_analyze_code(original_code: str) -> str:
    """Sends code to LM Studio to analyze and returns JSON with condition."""
    prompt = (
        "You are a code analysis assistant. Analyze the provided Python function for ACTUAL BUGS or LOGICAL ERRORS.\n\n"
        f"Code to analyze:\n{original_code}\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Focus ONLY on actual bugs, logic errors, and incorrect behavior\n"
        "2. Do NOT report issues for style, formatting, or cosmetic reasons\n"
        "3. Do NOT report issues for missing comments, type hints, or documentation\n"
        "4. Raising exceptions is CORRECT behavior - do NOT report it as an issue\n"
        "5. Your has_issues and condition values MUST be IDENTICAL (both true or both false)\n\n"
        "Return ONLY valid JSON (no markdown, no extra text):\n"
        "{\n"
        "  \"analysis\": \"<what the code does and if it has logic errors>\",\n"
        "  \"has_issues\": true or false,\n"
        "  \"condition\": true or false,\n"
        "  \"issues\": \"<description of actual logic errors, or 'None'>\"\n"
        "}\n\n"
        "EXAMPLES:\n"
        "- Code: 'def add(a, b): return a + b' → has_issues: false, condition: false (CORRECT)\n"
        "- Code: 'def multiply(a, b): return a - b' → has_issues: true, condition: true (WRONG OPERATOR)\n"
        "- Code with error handling → has_issues: false, condition: false (CORRECT, not an issue)\n"
        "- Incomplete/empty code → has_issues: false, condition: false"
    )

    payload = {
        "model": get_model_id(),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    try:
        logger.info(f"Sending request to LM Studio for code analysis...")
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=180)
        logger.info(f"Received response from ask_llm_to_analyze_code model: {response.status_code}")
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        logger.info(f"Successfully analyzed code")
        # Parse and clean JSON response
        cleaned = content.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(cleaned)
            # CRITICAL: Ensure has_issues and condition are identical
            if 'has_issues' in parsed and 'condition' in parsed:
                if parsed['has_issues'] != parsed['condition']:
                    # They should match - prioritize has_issues as it's more direct
                    parsed['condition'] = parsed['has_issues']
                    logger.info(f"Corrected mismatched condition values to match has_issues")
            return json.dumps(parsed)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse analysis response as JSON, returning as-is")
            return cleaned
    except Exception as e:
        logger.error(f"Error in ask_llm_to_analyze_code: {str(e)}")
        return json.dumps({"error": str(e), "condition": False, "analysis": "Error during analysis", "has_issues": False})

if __name__ == "__main__":
    mcp.run()