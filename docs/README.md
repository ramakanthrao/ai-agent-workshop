# AI Code Summarizer & Refactoring Agent

A sophisticated AI-powered system for analyzing and refactoring Python code using MCP (Model Context Protocol) servers and LM Studio.

## Architecture

The system consists of three main components:

### 1. **LLM MCP Server** (`llm_mcp.py`)
Handles AI-powered code analysis and refactoring:
- **`analyze_request(user_prompt)`**: Analyzes user requests and generates structured action plans
- **`ask_llm_to_refactor(original_code)`**: Uses LLM to fix code logic while preserving function signatures

### 2. **Code Modifier MCP Server** (`code_modifier_mcp.py`)
Handles file system operations for code analysis and modification:
- **`get_function_source(file_path, function_name)`**: Extracts specific function source code
- **`list_files_in_directory(directory_path)`**: Lists all Python files in a directory
- **`list_functions_in_file(file_path)`**: Extracts all function names from a file
- **`write_back_to_file(file_path, function_name, new_code)`**: Writes refactored code back to file

### 3. **Agent** (`agent.py`)
Orchestrates the entire workflow:
- Connects to both MCP servers
- Parses user requests intelligently
- Detects path types (file vs directory)
- Handles typos in function names using fuzzy matching
- Executes sequential action plans
- Maintains context between steps

## Key Features

### 🎯 Path Type Detection
Automatically detects whether a given path is a file or directory:
- **Files (.py)**: Directly extract and refactor specific functions
- **Directories**: List files, explore structure, then refactor

### 🔤 Typo Correction
Automatically finds the closest matching function name when a typo is detected:
```
User input: "devide" → Corrected to: "divide"
```

### 🔄 Intelligent Action Planning
The LLM generates structured JSON action plans that:
- List available functions
- Extract target functions
- Refactor code logic
- Write changes back to files

### 📝 Context Preservation
Maintains execution context across steps:
- Results from each step are stored in context dictionary
- Subsequent steps can reference previous results
- Corrected values are propagated through the workflow

### ⚡ Fallback Logic
When LLM analysis times out:
- Automatically generates a sensible fallback action plan
- Extracts path and function names from user request
- Proceeds with code refactoring workflow

## Usage

### Basic Usage
```bash
python agent.py
```

Then enter your request, e.g.:
```
analyse the code of: D:/projects/ai/code-summarizer-mcp/tools.py and summarize the divide function and fix the code
```

### Supported Request Patterns

1. **Single Function Fix**
   ```
   analyse the code of: /path/to/file.py and fix the function_name
   ```

2. **Directory Analysis**
   ```
   analyse the code of: /path/to/directory and fix all functions
   ```

3. **Specific Function**
   ```
   summarize and fix the divide function in tools.py
   ```

## Example Workflow

### Request
```
analyse the code of: D:/projects/ai/code-summarizer-mcp/tools.py and fix the divide function
```

### Execution Steps

1. **List Functions**
   - Tool: `list_functions_in_file`
   - Output: `add, subtract, multiply, divide`

2. **Extract Function**
   - Tool: `get_function_source`
   - Detects typo if any and finds closest match
   - Extracts the `divide` function code

3. **Refactor Code**
   - Tool: `ask_llm_to_refactor`
   - LLM analyzes and fixes logic errors
   - Returns corrected code

4. **Write Back**
   - Tool: `write_back_to_file`
   - Uses corrected function name
   - Updates the original file

## Configuration

### LM Studio
- **URL**: `http://localhost:1234/v1/chat/completions`
- **Models**: Auto-detects available models from `/v1/models`
- **Timeout**: 180 seconds (can be adjusted)

### Temperature Settings
- **Analysis**: 0.3 (more deterministic)
- **Refactoring**: 0.1 (more deterministic, focused on logic)

## Error Handling

- **400 Bad Request**: Automatically detects and uses correct model ID
- **Read Timeout**: Falls back to manual action plan generation
- **Function Not Found**: Uses fuzzy matching to find similar function names
- **Path Errors**: Validates paths and provides helpful error messages

## Requirements

```
mcp >= 0.1.0
requests >= 2.28.0
openai >= 1.0.0
```

## Testing

Run the connectivity test:
```bash
python test_lm_studio.py
```

This verifies:
- LM Studio is running
- Models are available
- Chat completion endpoint is working

## Performance Notes

- **First Request**: May take 2-3 minutes (model loading)
- **Subsequent Requests**: 30-60 seconds depending on code size
- **Large Code Files**: Consider refactoring smaller functions individually

## Future Enhancements

- [ ] Support for other languages (JavaScript, Java, etc.)
- [ ] Parallel processing of multiple functions
- [ ] Custom refactoring rules
- [ ] Code quality metrics
- [ ] Performance optimization suggestions
- [ ] Web UI for the agent
- [ ] Version control integration

---

Built with ❤️ using MCP, LM Studio, and Python
