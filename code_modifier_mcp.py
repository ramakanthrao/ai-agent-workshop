import os
import ast
import requests
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("CodeModifier")

# LM Studio Configuration
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

@mcp.tool()
def write_back_to_file(file_path: str, function_name: str, new_code: str) -> str:
    """
    Reads a file, finds a function, and replaces its logic with the provided new code.
    """
    try:
        # 1. Read the file
        with open(file_path, "r") as f:
            source = f.read()
        
        # 2. Extract the function using AST
        tree = ast.parse(source)
        lines = source.splitlines()
        target_node = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                target_node = node
                break
        
        if not target_node:
            return f"Function '{function_name}' not found."

        # 3. Get the original source lines
        original_func_code = "\n".join(lines[target_node.lineno - 1 : target_node.end_lineno])
        
        # 4. Write the new code back to the file
        with open(file_path, "w") as f:
            f.write(source.replace(original_func_code, new_code))
        
        return f"Function '{function_name}' has been updated successfully."

    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def list_files_in_directory(directory_path: str) -> str:
    """Lists all Python files in a given directory."""
    try:
        import os
        if not os.path.isdir(directory_path):
            return f"Error: '{directory_path}' is not a valid directory."
        
        python_files = [f for f in os.listdir(directory_path) if f.endswith('.py')]
        if not python_files:
            return f"No Python files found in {directory_path}"
        
        return "\n".join(python_files)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def list_functions_in_file(file_path: str) -> str:
    """Extracts all function names from a Python file."""
    try:
        with open(file_path, "r") as f:
            source = f.read()
        
        tree = ast.parse(source)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        
        if not functions:
            return f"No functions found in {file_path}"
        
        return "\n".join(functions)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def get_function_source(file_path: str, function_name: str) -> str:
    """
    Reads a local Python file and extracts the source code of a specific function.
    """
    print(f"Reading file: {file_path} to find function: {function_name}")

    try:
        print(f"Attempting to open file: {file_path}")
        with open(file_path, "r") as f:
            source = f.read()
        print(f"File {file_path} read successfully. Parsing AST.")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            print(f"Visiting node: {type(node).__name__}")
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Extract the specific lines for the function
                print(f"Function '{function_name}' found. Extracting source code.")
                lines = source.splitlines()
                print(f"Function '{function_name}' spans lines {node.lineno} to {node.end_lineno}.")
                return "\n".join(lines[node.lineno - 1 : node.end_lineno])
        
        return f"Function '{function_name}' not found in {file_path}."
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()