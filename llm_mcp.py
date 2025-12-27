from mcp.server.fastmcp import FastMCP
import ast
import requests

# Initialize FastMCP server
mcp = FastMCP("CodeSummarizer")

# LM Studio Configuration
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"


@mcp.tool()
def analyze_request(user_prompt: str) -> str:
    """
    Analyzes the user's request and returns structured instructions on what tools to call.
    Returns a JSON-like string with the sequence of actions needed.
    """
    system_prompt = (
        "You are an intelligent code analysis coordinator. Analyze the user's request and return "
        "a structured plan of actions. Return ONLY valid JSON (no markdown, no extra text) with this structure:\n"
        "{\n"
        "  'analysis': 'brief summary of what the user wants',\n"
        "  'actions': [\n"
        "    {'tool': 'tool_name', 'params': {'param1': 'value1', ...}, 'description': 'what this does'},\n"
        "    ...\n"
        "  ],\n"
        "  'loop_required': false,\n"
        "  'loop_condition': 'description of loop condition if needed'\n"
        "}\n\n"
        "IMPORTANT RULES:\n"
        "1. If the path ends with .py, it's a FILE - use get_function_source to extract functions\n"
        "2. If the path is a DIRECTORY - use list_files_in_directory first to list Python files\n"
        "3. If user asks to analyze ALL functions in a file or directory, use list_functions_in_file\n"
        "4. ALWAYS use get_function_source with actual file paths when extracting specific functions\n"
        "5. For refactoring, use ask_llm_to_refactor on extracted code\n"
        "6. For writing back, use write_back_to_file with the refactored code\n\n"
        "Available tools:\n"
        "- get_function_source(file_path, function_name): Extract specific function from a file\n"
        "- ask_llm_to_refactor(original_code): Refactor/fix code logic\n"
        "- write_back_to_file(file_path, function_name, new_code): Write refactored code back to file\n"
        "- list_files_in_directory(directory_path): List all Python files in a directory\n"
        "- list_functions_in_file(file_path): Extract all function names from a file"
    )

    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=120)
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        return content.strip()
    except Exception as e:
        return f"Analysis Error: {str(e)}"


@mcp.tool()
def ask_llm_to_refactor(original_code: str) -> str:
    """Sends code to LM Studio to fix its logic."""
    prompt = (
        "You are a code refactoring assistant. Your task is to correct the logic "
        "of the provided Python function while keeping the signature exactly the same.\n\n"
        f"Original Code:\n{original_code}\n\n"
        "Return ONLY the corrected Python code. Do not include explanations or markdown blocks."
    )

    payload = {
        "model": "local-model", # LM Studio usually ignores this and uses the loaded model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=120)
        response.raise_for_status()
        # Extract content and remove markdown code fences if the LLM added them
        content = response.json()['choices'][0]['message']['content']
        return content.replace("```python", "").replace("```", "").strip()
    except Exception as e:
        return f"LLM Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()