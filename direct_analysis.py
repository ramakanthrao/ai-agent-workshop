#!/usr/bin/env python3
"""
Direct code analysis and fixing script using MCP tools
"""

import asyncio
import json
import os
from pathlib import Path
from mcp.client.stdio import stdio_client
from mcp.shared.session import ClientSession

async def run_analysis():
    # Paths
    sample_dir = r"d:\projects\ai\code-summarizer-mcp\sample"
    
    # Define MCP server commands
    llm_mcp_cmd = [r"d:\projects\ai\code-summarizer-mcp\src\mcp\llm_mcp.py"]
    code_mcp_cmd = [r"d:\projects\ai\code-summarizer-mcp\src\mcp\code_modifier_mcp.py"]
    
    print("=" * 80)
    print("DIRECT CODE ANALYSIS AND FIXING")
    print("=" * 80)
    print(f"\nAnalyzing Python files in: {sample_dir}")
    print("\nConnecting to MCP servers...\n")
    
    # Connect to both MCP servers
    async with stdio_client(("python", str(llm_mcp_cmd[0]))) as (llm_read, llm_write):
        async with ClientSession(llm_read, llm_write) as llm_session:
            async with stdio_client(("python", str(code_mcp_cmd[0]))) as (code_read, code_write):
                async with ClientSession(code_read, code_write) as code_session:
                    
                    # Step 1: List all Python files
                    print("[Step 1] Listing Python files...")
                    try:
                        result = await code_session.call_tool("read_directory_for_files", {
                            "directory_path": sample_dir
                        })
                        files_text = result.content[0].text
                        files = [f.strip() for f in files_text.strip().split('\n') if f.strip().endswith('.py')]
                        print(f"Found {len(files)} Python files:\n")
                        for f in files:
                            print(f"  - {f}")
                    except Exception as e:
                        print(f"Error listing files: {e}")
                        return
                    
                    # Step 2: Process each file
                    for file_path in files:
                        print(f"\n{'='*80}")
                        print(f"Processing: {Path(file_path).name}")
                        print('='*80)
                        
                        # Get all functions in the file
                        try:
                            result = await code_session.call_tool("list_functions_in_file", {
                                "file_path": file_path
                            })
                            functions_text = result.content[0].text
                            functions = [f.strip() for f in functions_text.strip().split('\n') if f.strip()]
                            print(f"\nFound {len(functions)} functions")
                        except Exception as e:
                            print(f"Error listing functions: {e}")
                            continue
                        
                        # Process each function
                        for func_name in functions:
                            try:
                                # Get function source
                                result = await code_session.call_tool("get_function_source", {
                                    "file_path": file_path,
                                    "function_name": func_name
                                })
                                source_code = result.content[0].text
                                
                                # Analyze with LLM
                                print(f"\n  [Function: {func_name}]")
                                result = await llm_session.call_tool("ask_llm_to_analyze_code", {
                                    "code": source_code
                                })
                                analysis_text = result.content[0].text
                                
                                # Parse analysis result
                                try:
                                    analysis = json.loads(analysis_text)
                                    has_issues = analysis.get("condition", analysis.get("has_issues", False))
                                    
                                    if has_issues:
                                        print(f"    Status: [BUGGY] - Issues found")
                                        print(f"    Analysis: {analysis.get('analysis', 'N/A')[:100]}...")
                                        
                                        # Ask LLM to fix it
                                        result = await llm_session.call_tool("ask_llm_to_refactor", {
                                            "code": source_code
                                        })
                                        fix_text = result.content[0].text
                                        
                                        try:
                                            fix_data = json.loads(fix_text)
                                            fixed_code = fix_data.get("refactored_code", fix_text)
                                        except:
                                            fixed_code = fix_text
                                        
                                        # Write back to file
                                        result = await code_session.call_tool("write_back_to_file", {
                                            "file_path": file_path,
                                            "function_name": func_name,
                                            "new_code": fixed_code
                                        })
                                        fix_result = result.content[0].text
                                        print(f"    Status: [FIXED] - {fix_result[:80]}")
                                    else:
                                        print(f"    Status: [OK] - No issues found")
                                        
                                except json.JSONDecodeError:
                                    print(f"    Status: [SKIPPED] - Could not parse analysis")
                                    
                            except Exception as e:
                                print(f"  Error processing {func_name}: {e}")
                    
                    print(f"\n{'='*80}")
                    print("ANALYSIS COMPLETE")
                    print('='*80)

if __name__ == "__main__":
    asyncio.run(run_analysis())
