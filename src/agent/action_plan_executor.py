"""
Universal Action Plan Executor
Executes dynamic action plans with tools, loops, and conditionals.
Completely generic - no hardcoded tool names, server names, or field names.
"""

import json
import asyncio


class ActionPlanExecutor:
    """
    Executes action plans dynamically without hardcoding tool names or server mappings.
    """
    
    def __init__(self, sessions, available_tools_cache=None):
        """
        Initialize executor with MCP sessions.
        
        Args:
            sessions: Dict of {session_name: ClientSession}
            available_tools_cache: Dict of {session_name: set(tool_names)}
        """
        self.sessions = sessions
        self.available_tools_cache = available_tools_cache or {}
        self.results = {}
        self.step_counter = 0
        self.context = {}
        
        # Build tool-to-session mapping dynamically
        self.tool_to_session = self._build_tool_map()
    
    def _build_tool_map(self):
        """Build dynamic mapping of tool_name -> [session_names]"""
        tool_map = {}
        
        if not self.available_tools_cache:
            # No cache provided, will attempt discovery on first tool use
            return tool_map
        
        for session_name, tools in self.available_tools_cache.items():
            for tool_name in tools:
                if tool_name not in tool_map:
                    tool_map[tool_name] = []
                tool_map[tool_name].append(session_name)
        
        return tool_map
    
    async def execute(self, action_plan):
        """
        Execute the action plan.
        
        Args:
            action_plan: Dict with 'analysis' and 'actions' keys
        
        Returns:
            Dict with execution results
        """
        self.context = {}
        self.results = {}
        self.step_counter = 0
        
        print(f"\n--- Starting: {action_plan.get('analysis', 'Workflow')} ---\n")
        
        await self._execute_actions(action_plan.get('actions', []))
        
        print(f"\n--- Execution Complete ---\n")
        return self.results
    
    async def _execute_actions(self, actions, loop_item=None, outer_loop_item=None, indent=0):
        """
        Recursively execute a list of actions.
        Handles: standard tools, loops, and conditionals.
        """
        indent_str = "  " * indent
        
        for action in actions:
            # Identify action type and dispatch
            if action.get('loop_required'):
                await self._handle_loop(action, outer_loop_item, indent)
            elif 'condition' in action:
                await self._handle_conditional(action, loop_item, outer_loop_item, indent)
            else:
                await self._handle_tool_call(action, loop_item, outer_loop_item, indent)
    
    async def _handle_loop(self, action, outer_loop_item, indent):
        """Handle loop blocks"""
        indent_str = "  " * indent
        loop_condition = action.get('loop_condition', 'Loop')
        loop_actions = action.get('actions_loop', [])
        
        print(f"{indent_str}[LOOP] {loop_condition}")
        
        # Extract loop items from context variable reference
        loop_items = self._extract_loop_items(loop_condition)
        
        if not loop_items:
            print(f"{indent_str}  Warning: No items to iterate")
            return
        
        print(f"{indent_str}  Found {len(loop_items)} items")
        
        # Execute loop for each item
        for item in loop_items:
            self.context['loop_item'] = item
            self.context['loop_item_file'] = outer_loop_item or item
            await self._execute_actions(loop_actions, loop_item=item, outer_loop_item=outer_loop_item or item, indent=indent + 1)
    
    async def _handle_conditional(self, action, loop_item, outer_loop_item, indent):
        """Handle conditional blocks"""
        indent_str = "  " * indent
        condition = action.get('condition')
        conditional_actions = action.get('actions', [])
        
        should_execute = self._evaluate_condition(condition)
        
        print(f"{indent_str}[IF] Condition: {condition} -> {should_execute}")
        
        if should_execute:
            await self._execute_actions(conditional_actions, loop_item=loop_item, outer_loop_item=outer_loop_item, indent=indent + 1)
    
    async def _handle_tool_call(self, action, loop_item, outer_loop_item, indent):
        """Handle standard tool calls"""
        indent_str = "  " * indent
        self.step_counter += 1
        
        tool_name = action.get('tool')
        params = action.get('params', {})
        description = action.get('description', tool_name)
        
        if not tool_name:
            print(f"{indent_str}[STEP {self.step_counter}] Warning: No tool specified")
            return
        
        print(f"{indent_str}[STEP {self.step_counter}] {description}")
        print(f"{indent_str}  Tool: {tool_name}")
        
        try:
            # Resolve parameters dynamically
            resolved_params = self._resolve_parameters(params, loop_item, outer_loop_item)
            print(f"{indent_str}  Params: {resolved_params}")
            
            # Execute tool
            result = await self._execute_tool(tool_name, resolved_params)
            
            # Parse result (JSON or string)
            result_data = self._parse_result(result.content[0].text)
            
            # Store results
            self.results[f"step_{self.step_counter}"] = result_data
            self.context[f"result_{self.step_counter}"] = result_data
            self.context['result_last'] = result_data
            
            result_preview = str(result_data)[:100]
            print(f"{indent_str}  Result: {result_preview}...")
            
        except Exception as e:
            print(f"{indent_str}  Error: {str(e)}")
            self.results[f"step_{self.step_counter}"] = f"Error: {str(e)}"
    
    def _extract_loop_items(self, loop_condition):
        """Extract items to loop over from condition string like 'for each item in $result_0'"""
        import re
        
        # Match patterns like $result_0, $result_last, $loop_item
        match = re.search(r'\$(\w+(?:_\w+)?)', loop_condition)
        if not match:
            return []
        
        var_ref = match.group(1)
        result_data = self.context.get(var_ref, '')
        
        if isinstance(result_data, str):
            # Split by lines
            return [line.strip() for line in result_data.split('\n') if line.strip()]
        elif isinstance(result_data, list):
            return result_data
        else:
            return []
    
    def _resolve_parameters(self, params, loop_item, outer_loop_item):
        """Resolve all $ variable references in parameters generically"""
        resolved = {}
        
        for key, value in params.items():
            if not isinstance(value, str):
                resolved[key] = value
                continue
            
            # Handle nested field references: $result_last.field_name, $result_0.any_field
            if '.' in value and value.startswith('$'):
                resolved[key] = self._resolve_nested_reference(value, loop_item, outer_loop_item)
            # Handle simple references: $result_0, $result_last, $loop_item
            elif value.startswith('$'):
                resolved[key] = self._resolve_simple_reference(value, loop_item, outer_loop_item)
            else:
                resolved[key] = value
        
        return resolved
    
    def _resolve_nested_reference(self, ref, loop_item, outer_loop_item):
        """Resolve references like $result_last.field_name"""
        parts = ref[1:].split('.')  # Remove $ and split
        base_var = parts[0]
        field_name = parts[1]
        
        # Get base object
        base_obj = self.context.get(base_var)
        
        # If string, try JSON parse
        if isinstance(base_obj, str):
            try:
                base_obj = json.loads(base_obj)
            except:
                return ref
        
        # Extract field generically
        if isinstance(base_obj, dict) and field_name in base_obj:
            return base_obj[field_name]
        
        return ref
    
    def _resolve_simple_reference(self, ref, loop_item, outer_loop_item):
        """Resolve simple references like $result_0, $result_last, $loop_item"""
        var_name = ref[1:]  # Remove $
        
        # Special variables
        if var_name == 'loop_item':
            return loop_item if loop_item else ref
        elif var_name == 'loop_item_file':
            return outer_loop_item if outer_loop_item else loop_item if loop_item else ref
        
        # Context variables
        if var_name in self.context:
            return self.context[var_name]
        
        return ref
    
    def _evaluate_condition(self, condition):
        """Evaluate condition generically"""
        if isinstance(condition, bool):
            return condition
        
        if isinstance(condition, str):
            # If it's a variable reference
            if condition.startswith('$'):
                if '.' in condition:
                    # Nested reference like $result_last.field
                    value = self._resolve_nested_reference(condition, None, None)
                    return bool(value) if value != condition else False
                else:
                    # Simple reference
                    value = self._resolve_simple_reference(condition, None, None)
                    return bool(value) if value != condition else False
        
        return False
    
    async def _execute_tool(self, tool_name, params):
        """Execute tool on appropriate session"""
        # Check if we have cached tool mapping
        if tool_name not in self.tool_to_session:
            # Try to find it in any session
            for session_name, session in self.sessions.items():
                try:
                    result = await session.call_tool(tool_name, params)
                    print(f"    Server: {session_name}")
                    return result
                except:
                    continue
            raise Exception(f"Tool '{tool_name}' not found in any session")
        
        # Use cached mapping
        for session_name in self.tool_to_session[tool_name]:
            if session_name not in self.sessions:
                continue
            try:
                result = await self.sessions[session_name].call_tool(tool_name, params)
                print(f"    Server: {session_name}")
                return result
            except:
                continue
        
        raise Exception(f"Tool '{tool_name}' failed on all available sessions")
    
    def _parse_result(self, result_text):
        """Parse result as JSON if possible, otherwise return as string"""
        try:
            return json.loads(result_text)
        except:
            return result_text
