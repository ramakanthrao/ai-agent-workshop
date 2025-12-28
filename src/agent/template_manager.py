"""
Template Registry and Loader
Manages template discovery, loading, and executor instantiation.
Allows dynamic addition of new templates without code changes.
"""

import json
import os
import importlib
from typing import Dict, Any, Optional


class TemplateRegistry:
    """
    Loads and manages action plan templates from configuration.
    Dynamically instantiates executors based on registry.
    """
    
    def __init__(self, registry_path: str):
        """
        Initialize registry from configuration file.
        
        Args:
            registry_path: Path to template_registry.json
        """
        self.registry_path = registry_path
        self.registry = {}
        self.executor_config = {}
        self.loaded_executors = {}
        
        self._load_registry()
    
    def _load_registry(self):
        """Load registry from JSON file"""
        if not os.path.exists(self.registry_path):
            raise FileNotFoundError(f"Registry not found: {self.registry_path}")
        
        with open(self.registry_path, 'r') as f:
            config = json.load(f)
        
        # Extract templates (handle both array and object formats)
        templates_data = config.get('templates', {})
        
        if isinstance(templates_data, list):
            # Array format: convert to object keyed by template_id
            for template in templates_data:
                template_id = template.get('template_id')
                if template_id:
                    self.registry[template_id] = template
        elif isinstance(templates_data, dict):
            # Object format: already keyed
            self.registry = templates_data
        
        self.executor_config = config.get('executor_config', {})
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID"""
        return self.registry.get(template_id)
    
    def list_templates(self) -> Dict[str, str]:
        """List all available templates with descriptions"""
        return {
            template_id: template.get('template_desc', 'No description')
            for template_id, template in self.registry.items()
            if template.get('enabled', True)
        }
    
    def get_executor_class(self, template_id: str):
        """
        Dynamically load and return executor class for a template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            Executor class ready to instantiate
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")
        
        if not template.get('enabled', True):
            raise ValueError(f"Template '{template_id}' is disabled")
        
        # Check if already loaded
        if template_id in self.loaded_executors:
            return self.loaded_executors[template_id]
        
        # Dynamically import executor module and class
        executor_module_name = template.get('executor_module')
        executor_class_name = template.get('executor_class')
        
        if not executor_module_name or not executor_class_name:
            raise ValueError(f"Template '{template_id}' missing executor_module or executor_class")
        
        try:
            # Import module (e.g., 'src.agent.action_plan_executor')
            module = importlib.import_module(executor_module_name)
            executor_class = getattr(module, executor_class_name)
            
            # Cache the loaded class
            self.loaded_executors[template_id] = executor_class
            
            return executor_class
        except (ImportError, AttributeError) as e:
            raise RuntimeError(f"Failed to load executor for template '{template_id}': {e}")
    
    def get_schema(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Load JSON schema for a template.
        
        Args:
            template_id: ID of the template
            
        Returns:
            JSON schema dictionary or None if not found
        """
        template = self.get_template(template_id)
        if not template:
            return None
        
        schema_file = template.get('template_schema_file')
        schema_dir = template.get('template_dir')
        
        if not schema_file or not schema_dir:
            return None
        
        schema_path = os.path.join(schema_dir, schema_file)
        
        if not os.path.exists(schema_path):
            return None
        
        with open(schema_path, 'r') as f:
            return json.load(f)
    
    def validate_action_plan(self, template_id: str, action_plan: Dict[str, Any]) -> tuple:
        """
        Validate action plan against template schema.
        
        Args:
            template_id: Template ID to validate against
            action_plan: Action plan to validate
            
        Returns:
            (is_valid, errors) tuple
        """
        try:
            import jsonschema
        except ImportError:
            # If jsonschema not available, do basic validation
            return self._basic_validation(action_plan)
        
        schema = self.get_schema(template_id)
        if not schema:
            return True, []  # No schema available, assume valid
        
        try:
            jsonschema.validate(instance=action_plan, schema=schema)
            return True, []
        except jsonschema.ValidationError as e:
            return False, [str(e)]
        except jsonschema.SchemaError as e:
            return False, [f"Schema error: {str(e)}"]
    
    def _basic_validation(self, action_plan: Dict[str, Any]) -> tuple:
        """Basic validation without jsonschema"""
        errors = []
        
        # Check required fields
        if 'analysis' not in action_plan:
            errors.append("Missing required field: 'analysis'")
        
        if 'actions' not in action_plan:
            errors.append("Missing required field: 'actions'")
        elif not isinstance(action_plan['actions'], list):
            errors.append("Field 'actions' must be an array")
        
        return len(errors) == 0, errors


class TemplateManager:
    """
    High-level manager that handles template operations.
    Integrates with executor instantiation and execution.
    """
    
    def __init__(self, registry_path: str):
        """Initialize template manager"""
        self.registry = TemplateRegistry(registry_path)
    
    async def execute_action_plan(self, action_plan: Dict[str, Any], sessions: Dict, 
                                   template_id: str = 'universal-action-plan') -> Dict:
        """
        Execute an action plan using the specified template executor.
        
        Args:
            action_plan: Action plan to execute
            sessions: Dict of MCP sessions
            template_id: ID of template/executor to use
            
        Returns:
            Execution results
        """
        # Get executor class
        ExecutorClass = self.registry.get_executor_class(template_id)
        
        # Discover available tools
        available_tools_cache = {}
        for session_name, session in sessions.items():
            try:
                tools_list = await session.list_tools()
                available_tools_cache[session_name] = {tool.name for tool in tools_list.tools}
            except Exception as e:
                print(f"Warning: Could not list tools from {session_name}: {e}")
        
        # Instantiate executor
        executor = ExecutorClass(sessions, available_tools_cache)
        
        # Validate action plan
        is_valid, errors = self.registry.validate_action_plan(template_id, action_plan)
        if not is_valid:
            print("Action plan validation errors:")
            for error in errors:
                print(f"  - {error}")
            raise ValueError("Action plan validation failed")
        
        # Execute
        results = await executor.execute(action_plan)
        return results
    
    def describe_templates(self) -> str:
        """Get human-readable template descriptions"""
        templates = self.registry.list_templates()
        if not templates:
            return "No templates available"
        
        desc = "Available Templates:\n"
        for template_id, description in templates.items():
            desc += f"  - {template_id}: {description}\n"
        return desc
