import unittest
import os
import tempfile
import shutil
from code_modifier_mcp import (
    write_back_to_file,
    list_files_in_directory,
    list_functions_in_file,
    get_function_source
)


class TestCodeModifierMCP(unittest.TestCase):
    """Test suite for code_modifier_mcp functions."""
    
    def setUp(self):
        """Create a temporary directory and test files."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_module.py")
        
        # Create a test Python file with sample functions
        self.test_code = '''def add(a, b):
    """Add two numbers."""
    return a + b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def greet(name):
    """Greet a person."""
    return f"Hello, {name}!"

def divide(a, b):
    """Divide two numbers - has a bug!"""
    return a / b  # Bug: doesn't check for zero
'''
        
        with open(self.test_file, "w") as f:
            f.write(self.test_code)
    
    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)
    
    # ===== Tests for list_functions_in_file =====
    
    def test_list_functions_in_file_success(self):
        """Test listing functions in an existing file."""
        result = list_functions_in_file(self.test_file)
        expected_functions = ["add", "multiply", "greet", "divide"]
        
        # Result should contain all functions
        for func in expected_functions:
            self.assertIn(func, result)
    
    def test_list_functions_in_file_format(self):
        """Test that functions are returned as newline-separated list."""
        result = list_functions_in_file(self.test_file)
        functions = result.split("\n")
        
        self.assertEqual(len(functions), 4)
        self.assertEqual(functions[0], "add")
        self.assertEqual(functions[1], "multiply")
    
    def test_list_functions_in_file_not_found(self):
        """Test listing functions in a non-existent file."""
        result = list_functions_in_file("/nonexistent/file.py")
        self.assertIn("Error", result)
    
    def test_list_functions_empty_file(self):
        """Test listing functions in a file with no functions."""
        empty_file = os.path.join(self.test_dir, "empty.py")
        with open(empty_file, "w") as f:
            f.write("# This is just a comment\nx = 5")
        
        result = list_functions_in_file(empty_file)
        self.assertIn("No functions found", result)
    
    # ===== Tests for get_function_source =====
    
    def test_get_function_source_success(self):
        """Test extracting a function's source code."""
        result = get_function_source(self.test_file, "add")
        self.assertIn("def add(a, b):", result)
        self.assertIn("return a + b", result)
    
    def test_get_function_source_multiple_functions(self):
        """Test extracting different functions."""
        # Test greet function
        result = get_function_source(self.test_file, "greet")
        self.assertIn("def greet(name):", result)
        self.assertIn("Hello", result)
        
        # Test divide function
        result = get_function_source(self.test_file, "divide")
        self.assertIn("def divide(a, b):", result)
        self.assertIn("return a / b", result)
    
    def test_get_function_source_not_found(self):
        """Test extracting a non-existent function."""
        result = get_function_source(self.test_file, "nonexistent")
        self.assertIn("not found", result)
    
    def test_get_function_source_invalid_file(self):
        """Test extracting from a non-existent file."""
        result = get_function_source("/nonexistent/file.py", "add")
        self.assertIn("Error", result)
    
    def test_get_function_source_with_docstring(self):
        """Test that docstring is included in extracted source."""
        result = get_function_source(self.test_file, "add")
        self.assertIn('"""Add two numbers."""', result)
    
    # ===== Tests for write_back_to_file =====
    
    def test_write_back_to_file_success(self):
        """Test replacing a function in a file."""
        new_code = '''def add(a, b):
    """Add two numbers."""
    result = a + b
    return result'''
        
        result = write_back_to_file(self.test_file, "add", new_code)
        self.assertIn("updated successfully", result)
        
        # Verify the file was actually updated
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertIn("result = a + b", content)
    
    def test_write_back_to_file_function_not_found(self):
        """Test writing back to a non-existent function."""
        new_code = "def test(): return True"
        result = write_back_to_file(self.test_file, "nonexistent", new_code)
        self.assertIn("not found", result)
    
    def test_write_back_to_file_invalid_file(self):
        """Test writing to a non-existent file."""
        new_code = "def test(): return True"
        result = write_back_to_file("/nonexistent/file.py", "test", new_code)
        self.assertIn("Error", result)
    
    def test_write_back_to_file_preserves_other_functions(self):
        """Test that updating one function doesn't affect others."""
        new_add_code = '''def add(a, b):
    """Add two numbers - improved."""
    return a + b'''
        
        write_back_to_file(self.test_file, "add", new_add_code)
        
        # Check that other functions are still present
        with open(self.test_file, "r") as f:
            content = f.read()
        
        self.assertIn("def multiply(a, b):", content)
        self.assertIn("def greet(name):", content)
        self.assertIn("def divide(a, b):", content)
    
    def test_write_back_to_file_multiple_updates(self):
        """Test updating multiple functions in sequence."""
        new_add = '''def add(a, b):
    """Add two numbers."""
    return a + b'''
        
        new_multiply = '''def multiply(a, b):
    """Multiply two numbers."""
    return a * b'''
        
        write_back_to_file(self.test_file, "add", new_add)
        write_back_to_file(self.test_file, "multiply", new_multiply)
        
        # Verify both updates
        result_add = get_function_source(self.test_file, "add")
        result_multiply = get_function_source(self.test_file, "multiply")
        
        self.assertIn("def add(a, b):", result_add)
        self.assertIn("def multiply(a, b):", result_multiply)
    
    def test_write_back_with_multiline_function(self):
        """Test updating a function with multiple lines."""
        new_divide = '''def divide(a, b):
    """Divide two numbers safely."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b'''
        
        write_back_to_file(self.test_file, "divide", new_divide)
        
        result = get_function_source(self.test_file, "divide")
        self.assertIn("if b == 0:", result)
        self.assertIn("raise ValueError", result)
    
    # ===== Tests for list_files_in_directory =====
    
    def test_list_files_in_directory_success(self):
        """Test listing Python files in a directory."""
        # Create some test files
        open(os.path.join(self.test_dir, "file1.py"), "w").close()
        open(os.path.join(self.test_dir, "file2.py"), "w").close()
        open(os.path.join(self.test_dir, "readme.txt"), "w").close()
        
        result = list_files_in_directory(self.test_dir)
        
        # Should include .py files
        self.assertIn("test_module.py", result)
        self.assertIn("file1.py", result)
        self.assertIn("file2.py", result)
        # Should NOT include non-.py files
        self.assertNotIn("readme.txt", result)
    
    def test_list_files_in_directory_empty(self):
        """Test listing files in a directory with no Python files."""
        new_dir = os.path.join(self.test_dir, "empty_dir")
        os.makedirs(new_dir)
        open(os.path.join(new_dir, "readme.txt"), "w").close()
        
        result = list_files_in_directory(new_dir)
        self.assertIn("No Python files found", result)
    
    def test_list_files_in_directory_invalid_path(self):
        """Test listing files in a non-existent directory."""
        result = list_files_in_directory("/nonexistent/directory")
        self.assertIn("not a valid directory", result)
    
    def test_list_files_returns_only_py_files(self):
        """Test that only .py files are returned."""
        # Create various file types
        open(os.path.join(self.test_dir, "script.py"), "w").close()
        open(os.path.join(self.test_dir, "data.json"), "w").close()
        open(os.path.join(self.test_dir, "config.yaml"), "w").close()
        
        result = list_files_in_directory(self.test_dir)
        lines = result.split("\n")
        
        # All returned lines should be .py files
        for line in lines:
            if line.strip():
                self.assertTrue(line.endswith(".py"))
    
    # ===== Integration Tests =====
    
    def test_integration_list_get_modify(self):
        """Test the full workflow: list -> get -> modify."""
        # Step 1: List functions
        functions = list_functions_in_file(self.test_file)
        self.assertIn("divide", functions)
        
        # Step 2: Get the function source
        source = get_function_source(self.test_file, "divide")
        self.assertIn("def divide(a, b):", source)
        
        # Step 3: Modify the function
        new_divide = '''def divide(a, b):
    """Divide two numbers safely."""
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b'''
        
        result = write_back_to_file(self.test_file, "divide", new_divide)
        self.assertIn("updated successfully", result)
        
        # Verify the modification
        modified_source = get_function_source(self.test_file, "divide")
        self.assertIn("ZeroDivisionError", modified_source)
    
    def test_integration_work_with_multiple_functions(self):
        """Test working with multiple functions in sequence."""
        functions = list_functions_in_file(self.test_file)
        function_list = [f for f in functions.split("\n") if f.strip()]
        
        # Should have at least 4 functions
        self.assertGreaterEqual(len(function_list), 4)
        
        # Get source for each function
        for func_name in function_list:
            source = get_function_source(self.test_file, func_name)
            self.assertIn(f"def {func_name}", source)
            self.assertNotIn("Error", source)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Create a temporary directory for edge case tests."""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def test_function_with_special_characters(self):
        """Test handling functions with special names."""
        test_file = os.path.join(self.test_dir, "special.py")
        code = '''def _private_function(x):
    """Private function."""
    return x * 2

def __dunder_function__(y):
    """Dunder function."""
    return y
'''
        with open(test_file, "w") as f:
            f.write(code)
        
        # Test getting private function
        result = get_function_source(test_file, "_private_function")
        self.assertIn("def _private_function", result)
        
        # Test getting dunder function
        result = get_function_source(test_file, "__dunder_function__")
        self.assertIn("def __dunder_function__", result)
    
    def test_function_with_decorators(self):
        """Test handling functions with decorators."""
        test_file = os.path.join(self.test_dir, "decorated.py")
        code = '''def decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@decorator
def decorated_function(x):
    """A decorated function."""
    return x + 1
'''
        with open(test_file, "w") as f:
            f.write(code)
        
        functions = list_functions_in_file(test_file)
        self.assertIn("decorated_function", functions)
        self.assertIn("decorator", functions)
    
    def test_function_with_nested_functions(self):
        """Test handling functions with nested functions."""
        test_file = os.path.join(self.test_dir, "nested.py")
        code = '''def outer_function(x):
    """Outer function with nested function."""
    def inner_function(y):
        return y * 2
    return inner_function(x)
'''
        with open(test_file, "w") as f:
            f.write(code)
        
        functions = list_functions_in_file(test_file)
        # Both functions should be listed (ast.walk gets all FunctionDef nodes)
        self.assertIn("outer_function", functions)
        self.assertIn("inner_function", functions)


if __name__ == "__main__":
    unittest.main()
