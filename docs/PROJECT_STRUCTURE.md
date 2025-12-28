# Project Structure & File Reference

## Overview
Complete AI-powered code analysis and refactoring system using MCP (Model Context Protocol) servers with improved LLM guidance and validation.

## Directory Structure

```
d:\projects\ai\code-summarizer-mcp/
├── src/
│   ├── agent/
│   │   └── agent.py              # Main agent orchestrator with validation
│   └── mcp/
│       ├── llm_mcp.py            # AI analysis server (LM Studio integration)
│       └── code_modifier_mcp.py  # Code manipulation server
├── sample/
│   └── tools.py                  # Sample Python file with test functions
├── test/
│   ├── test_code_modifier_mcp.py # Unit tests for code_modifier_mcp (24 tests)
│   └── fixtures/
│       └── sample_code.py        # Test fixtures
├── doc/
│   ├── README.md                 # Project overview
│   ├── ARCHITECTURE.md           # System architecture
│   ├── IMPROVEMENTS.md           # Improvements documentation
│   ├── API.md                    # API reference
│   └── [more documentation files]
├── test_improved_agent.py        # Validation test suite (6 tests)
├── test_agent_workflow.py        # Workflow demonstration
├── IMPROVEMENTS_QUICK_START.md   # Quick start guide
└── server.py                     # (Root server file)
```

## Core Files

### 1. Agent System

#### `src/agent/agent.py`
**Purpose**: Orchestrates between MCP servers and executes workflows

**Key Functions**:
- `detect_path_type(path_str)` - Determines if path is file or directory
- `validate_action_plan(actions)` - ✨ NEW: Validates action plans for errors
- `execute_action_plan(sessions, actions, context)` - Executes tool sequences
- `run_agent()` - Main async entry point with tool discovery

**Features**:
- Multi-server MCP client with ClientSession management
- Dynamic tool discovery from both servers
- Typo correction with difflib fuzzy matching
- Context propagation between action steps
- Validation integration with user feedback

**Recent Changes**:
- Added `validate_action_plan()` function
- Integrated validation into `run_agent()`
- Better error messages from validation

### 2. MCP Servers

#### `src/mcp/llm_mcp.py`
**Purpose**: AI-powered code analysis via LM Studio

**Tools Exposed**:
1. `analyze_request(user_prompt, available_tools)` - Generates action plans
2. `ask_llm_to_refactor(original_code)` - Fixes code logic
3. `ask_llm_to_analyze_code(original_code)` - Analyzes code

**Key Functions**:
- `get_model_id()` - Auto-detects model from LM Studio
- LM Studio integration with OpenAI SDK

**Recent Changes**:
- ✨ Enhanced system prompt with explicit workflow examples
- Added parameter requirement documentation
- Added "NEVER..." rules for common mistakes
- Added step-by-step workflow sequences

**Configuration**:
- Endpoint: `http://localhost:1234/v1/chat/completions`
- Temperature: 0.3 (analysis), 0.1 (refactoring)
- Timeout: 180 seconds
- Logging: DEBUG level to stderr

#### `src/mcp/code_modifier_mcp.py`
**Purpose**: File system and code manipulation

**Tools Exposed**:
1. `list_functions_in_file(file_path)` - Lists function names
2. `get_function_source(file_path, function_name)` - Extracts function code
3. `write_back_to_file(file_path, function_name, new_code)` - Updates functions
4. `list_files_in_directory(directory_path)` - Lists Python files

**Features**:
- AST parsing for robust code extraction
- Proper indentation preservation
- Context variable substitution
- Fallback for cases where exact line numbers can't be determined

**Testing**:
- ✅ 24 unit tests, all passing
- Coverage: normal operations, edge cases, integration scenarios

**Logging**: 
- DEBUG level to stderr
- Prevents JSONRPC protocol corruption

## Test Files

### `test/test_code_modifier_mcp.py`
**Status**: ✅ 24/24 tests passing (0.358s execution)

**Test Coverage**:
- `test_list_functions_in_file*` - 4 tests
- `test_get_function_source*` - 6 tests
- `test_write_back_to_file*` - 5 tests
- `test_list_files_in_directory*` - 4 tests
- Integration tests - 2 tests
- Edge cases - 3 tests

### `test_improved_agent.py` ✨ NEW
**Status**: ✅ 6/6 tests passing

**Tests**:
1. Valid action plan (should pass)
2. Invalid: `list_files_in_directory` with .py file (should fail)
3. Invalid: `get_function_source` missing `function_name` (should fail)
4. Invalid: `write_back_to_file` missing parameters (should fail)
5. Invalid: `ask_llm_to_refactor` missing `original_code` (should fail)
6. Warning: `list_functions_in_file` with non-.py file (should warn)

### `test_agent_workflow.py` ✨ NEW
**Purpose**: Demonstrates valid and invalid action plan scenarios

**Scenarios**:
- Valid: Analyze specific file for issues
- Valid: Analyze all files in directory
- Valid: Full refactoring workflow
- Invalid: Using wrong tool for file type
- Invalid: Missing required parameters

## Documentation Files

### `doc/IMPROVEMENTS.md` ✨ NEW
**Contents**:
- Summary of changes
- Issues addressed and solutions
- Detailed changes to system prompt
- New `validate_action_plan()` function details
- Integration into agent
- Test results
- Impact analysis
- Future improvements

### `IMPROVEMENTS_QUICK_START.md` ✨ NEW
**Contents**:
- What was fixed and why
- How to use the improved agent
- Example interactions
- Test instructions
- File modification summary
- Key improvements side-by-side
- Validation examples
- Troubleshooting guide

### `doc/README.md`
**Contents**:
- Project overview
- Architecture description
- Features list
- Setup instructions
- Usage examples
- Dependencies

### `doc/ARCHITECTURE.md`
**Contents**:
- System architecture diagram
- MCP server overview
- Agent workflow
- Tool interaction patterns
- Error handling strategy

### `doc/API.md`
**Contents**:
- Tool specifications
- Parameter documentation
- Return value descriptions
- Error codes and messages
- Examples for each tool

### Other Documentation
- `doc/TESTING.md` - Testing approach and guidelines
- `doc/SETUP.md` - Detailed setup instructions
- `doc/WORKFLOW.md` - Step-by-step workflow examples
- `doc/TROUBLESHOOTING.md` - Common issues and fixes
- And more...

## Sample Code

### `sample/tools.py`
**Purpose**: Test file with intentional bugs

**Functions**:
```python
def add(a, b)
    return a + b

def subtract(a, b)
    return a - b

def multiply(a, b)
    return a - b  # BUG: should be a * b

def divide(a, b)
    # Raises ZeroDivisionError instead of returning error message
    if b != 0:
        return a / b
    else:
        raise ZeroDivisionError("division by zero is not allowed")
```

**Purpose**: Demonstrates agent's ability to:
- Identify multiple functions in a file
- Extract specific function source code
- Detect logic errors (multiply using - instead of *)
- Suggest fixes

## Configuration & Environment

### Requirements
- Python 3.8+
- LM Studio running locally on `http://localhost:1234`
- MCP-compatible Python environment

### Dependencies
- `mcp` - Model Context Protocol
- `fastmcp` - FastMCP framework
- `openai` - OpenAI SDK for LM Studio
- `pydantic` - Data validation

### Logging Configuration
- **Output**: stderr (not stdout, to preserve JSONRPC)
- **Format**: `YYYY-MM-DD HH:MM:SS,mmm - server_name - LEVEL - message`
- **Level**: DEBUG
- **Applies to**: All MCP servers

## Key Statistics

| Metric | Count |
|--------|-------|
| Python files in src/ | 3 |
| MCP tools exposed | 7 (3 in llm_mcp, 4 in code_modifier_mcp) |
| Unit tests | 24 (all passing) |
| Validation tests | 6 (all passing) |
| Documentation files | 12+ |
| Test fixtures | 1+ |

## Architecture Highlights

### Tool Discovery
- Automatic discovery from MCP servers at runtime
- No hardcoded tool lists
- Fallback dictionary for backward compatibility

### Workflow Execution
```
User Request
    ↓
[Analyze with LLM] → Generate action plan
    ↓
[Validate Plan] → Check for errors/warnings
    ↓
[Get Approval] → User confirms execution
    ↓
[Execute Tools] → Run each action sequentially
    ↓
Results to User
```

### Error Handling
- Tool parameter validation before execution
- Typo correction with fuzzy matching
- Fallback for missing line numbers
- User-friendly error messages
- Pre-execution plan validation

## Recent Improvements

### ✨ System Prompt Enhancements
- Explicit workflow examples for different scenarios
- Parameter requirements clearly documented
- Common mistakes highlighted ("NEVER..." rules)
- Step-by-step correct execution sequences

### ✨ Action Plan Validation
- `validate_action_plan()` function
- Checks required parameters
- Detects path type mismatches
- Prevents invalid plan execution
- Helpful error messages

### ✨ Better User Feedback
- Validation results displayed before execution
- Clear error messages showing what's wrong
- Helpful suggestions for fixes
- Ability to refine prompts based on failures

## Usage Quick Reference

### Run the Agent
```bash
cd d:\projects\ai\code-summarizer-mcp
python src/agent/agent.py
```

### Run Tests
```bash
# Unit tests
python -m pytest test/test_code_modifier_mcp.py -v

# Validation tests
python test_improved_agent.py

# Workflow demonstration
python test_agent_workflow.py
```

### Example Commands
```
What would you like me to do? Analyze sample/tools.py for bugs
What would you like me to do? Fix the multiply function in sample/tools.py
What would you like me to do? Analyze all Python files in sample/
```

## Next Steps

1. **Run the Agent**: Execute `python src/agent/agent.py`
2. **Try Requests**: Use example commands above
3. **Observe Improvements**: See better action plan generation
4. **Trust Validation**: See invalid plans caught and stopped
5. **Review Documentation**: Read doc/IMPROVEMENTS.md for details

## Contact & Support

For issues or improvements:
- Check `doc/TROUBLESHOOTING.md`
- Review error messages from validation
- Check logging output (stderr)
- Consult system prompt in `llm_mcp.py` for tool expectations
