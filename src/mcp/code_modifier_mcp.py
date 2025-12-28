import os
import ast
import requests
import logging
import sys
from mcp.server.fastmcp import FastMCP

# Configure logging to print to stderr (not stdout, which is used for JSONRPC)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("code_modifier_mcp")

# Initialize FastMCP server
mcp = FastMCP("CodeModifier")

@mcp.tool()
def is_input_a_directory(input_path: str) -> bool:
    """Checks if the given input path is a directory."""
    logger.info(f"is_input_a_directory called: {input_path}")
    try:
        result = os.path.isdir(input_path)
        logger.debug(f"Path '{input_path}' is a directory: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in is_input_a_directory: {str(e)}")
        return False

@mcp.tool()
def is_input_a_file(input_path: str) -> bool:
    """Checks if the given input path is a file."""
    logger.info(f"is_input_a_file called: {input_path}")
    try:
        result = os.path.isfile(input_path)
        logger.debug(f"Path '{input_path}' is a file: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in is_input_a_file: {str(e)}")
        return False

@mcp.tool()
def write_back_to_file(file_path: str, function_name: str, new_code: str) -> str:
    """
    Reads a file, finds a function, and replaces its logic with the provided new code.
    """
    logger.info(f"write_back_to_file called: file={file_path}, function={function_name}")
    try:
        # 1. Read the file
        logger.debug(f"Reading file: {file_path}")
        with open(file_path, "r") as f:
            source = f.read()
        
        # 2. Extract the function using AST
        logger.debug(f"Parsing AST for file: {file_path}")
        tree = ast.parse(source)
        lines = source.splitlines()
        target_node = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                target_node = node
                break
        
        if not target_node:
            logger.warning(f"Function '{function_name}' not found in {file_path}")
            return f"Function '{function_name}' not found."

        # 3. Get the original source lines
        logger.debug(f"Extracting function '{function_name}' from lines {target_node.lineno}-{target_node.end_lineno}")
        original_func_code = "\n".join(lines[target_node.lineno - 1 : target_node.end_lineno])
        
        # 4. Write the new code back to the file
        logger.debug(f"Writing updated function back to {file_path}")
        with open(file_path, "w") as f:
            f.write(source.replace(original_func_code, new_code))
        
        logger.info(f"Successfully updated function '{function_name}' in {file_path}")
        return f"Function '{function_name}' has been updated successfully."

    except Exception as e:
        logger.error(f"Error in write_back_to_file: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def read_directory_for_files(directory_path: str) -> str:
    """Lists all Python files in a given directory."""
    logger.info(f"read_directory_for_files called: {directory_path}")
    try:
        import os
        if not os.path.isdir(directory_path):
            logger.warning(f"Invalid directory: {directory_path}")
            return f"Error: '{directory_path}' is not a valid directory."
        
        python_files = [f for f in os.listdir(directory_path) if f.endswith('.py')]
        if not python_files:
            logger.info(f"No Python files found in {directory_path}")
            return f"No Python files found in {directory_path}"
        
        logger.info(f"Found {len(python_files)} Python files in {directory_path}")
        return "\n".join(python_files)
    except Exception as e:
        logger.error(f"Error in read_directory_for_files: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def list_functions_in_file(file_path: str) -> str:
    """Extracts all function names from a Python file."""
    logger.info(f"list_functions_in_file called: {file_path}")
    try:
        logger.debug(f"Reading file: {file_path}")
        with open(file_path, "r") as f:
            source = f.read()
        
        logger.debug(f"Parsing AST for file: {file_path}")
        tree = ast.parse(source)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        
        if not functions:
            logger.info(f"No functions found in {file_path}")
            return f"No functions found in {file_path}"
        
        logger.info(f"Found {len(functions)} functions in {file_path}")
        return "\n".join(functions)
    except Exception as e:
        logger.error(f"Error in list_functions_in_file: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_function_source(file_path: str, function_name: str) -> str:
    """
    Reads a local Python file and extracts the source code of a specific function.
    """
    logger.info(f"get_function_source called: file={file_path}, function={function_name}")
    try:
        logger.debug(f"Reading file: {file_path}")
        with open(file_path, "r") as f:
            source = f.read()
        logger.debug(f"Parsing AST for file: {file_path}")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Extract the specific lines for the function
                logger.info(f"Found function '{function_name}' at lines {node.lineno}-{node.end_lineno}")
                lines = source.splitlines()
                logger.debug(f"Extracting source code for '{function_name}'")
                return "\n".join(lines[node.lineno - 1 : node.end_lineno])
        
        logger.warning(f"Function '{function_name}' not found in {file_path}")
        return f"Function '{function_name}' not found in {file_path}."
    except Exception as e:
        logger.error(f"Error in get_function_source: {str(e)}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()