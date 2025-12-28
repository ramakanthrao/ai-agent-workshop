"""
Module 4: Integration and Practical Applications
This module integrates functionality from module1_data_structures and module2_graph_algorithms.
Depends on: module1_data_structures (Stack, Queue, validate_balanced_parentheses)
            module2_graph_algorithms (Graph, depth_first_search, breadth_first_search, find_shortest_path)
"""

from module1_data_structures import Stack, Queue, validate_balanced_parentheses
from module2_graph_algorithms import (
    Graph, depth_first_search, breadth_first_search, find_shortest_path
)


class ExpressionParser:
    """
    Parse and evaluate mathematical expressions using Stack and Queue from module1.
    This implementation is CORRECT.
    """
    def __init__(self):
        self.stack = Stack()
        self.operators = {'+', '-', '*', '/', '^'}
    
    def is_valid_syntax(self, expression):
        """Check if expression has valid syntax using validate_balanced_parentheses."""
        return validate_balanced_parentheses(expression)
    
    def evaluate_simple(self, num1, num2, operator):
        """Evaluate simple arithmetic operation."""
        if operator == '+':
            return num1 + num2
        elif operator == '-':
            return num1 - num2
        elif operator == '*':
            return num1 * num2
        elif operator == '/':
            if num2 == 0:
                raise ValueError("Division by zero")
            return num1 / num2
        elif operator == '^':
            return num1 ** num2
        else:
            raise ValueError(f"Unknown operator: {operator}")


class RouteOptimizer:
    """
    Find optimal routes in a transportation network using Graph algorithms.
    This implementation is INCORRECT - incorrectly uses find_shortest_path.
    """
    def __init__(self):
        self.network = Graph()
    
    def add_route(self, city1, city2):
        """Add a bidirectional route between two cities."""
        self.network.add_edge(city1, city2)
    
    def find_route(self, start, end):
        """Find route from start to end city."""
        # BUG: find_shortest_path is broken (uses Stack instead of Queue)
        # This will not find shortest path correctly
        return find_shortest_path(self.network, start, end)
    
    def check_connectivity(self, city1, city2):
        """Check if two cities are connected using DFS from module2."""
        return depth_first_search(self.network, city1, city2)
    
    def get_all_cities(self):
        """Get list of all cities in the network."""
        return list(self.network.adjacency_list.keys())


class SystemCallStack:
    """
    Track system function calls using Stack from module1.
    This implementation is CORRECT.
    """
    def __init__(self):
        self.call_stack = Stack()
        self.call_history = []
    
    def push_call(self, function_name, parameters):
        """Push a function call onto the stack."""
        call_info = {'function': function_name, 'params': parameters}
        self.call_stack.push(call_info)
        self.call_history.append(call_info)
    
    def pop_call(self):
        """Pop the last function call from the stack."""
        if not self.call_stack.is_empty():
            return self.call_stack.pop()
        return None
    
    def get_current_call(self):
        """Get the current function call without removing it."""
        if not self.call_stack.is_empty():
            return self.call_stack.peek()
        return None
    
    def get_call_depth(self):
        """Get the current call stack depth."""
        return self.call_stack.size()
    
    def get_history(self):
        """Get the complete call history."""
        return self.call_history


class TaskQueue:
    """
    Manage task execution queue using Queue from module1.
    This implementation is INCORRECT - wrong comparison operator in priority logic.
    """
    def __init__(self):
        self.task_queue = Queue()
        self.completed_tasks = []
    
    def add_task(self, task_name, priority):
        """Add a task to the queue."""
        task = {'name': task_name, 'priority': priority}
        self.task_queue.enqueue(task)
    
    def execute_next_task(self):
        """Execute the next task in the queue."""
        if not self.task_queue.is_empty():
            task = self.task_queue.dequeue()
            self.completed_tasks.append(task)
            return task
        return None
    
    def get_high_priority_tasks(self):
        """Get all high priority tasks (priority > 7)."""
        high_priority = []
        # BUG: Should iterate through actual queue, but Queue doesn't expose items
        # This implementation is fundamentally broken for this use case
        for task in self.task_queue.items:
            # BUG: Wrong comparison - should be >= not <=
            if task['priority'] <= 7:
                high_priority.append(task)
        return high_priority
    
    def pending_task_count(self):
        """Get count of pending tasks."""
        return self.task_queue.size()


class NetworkPathFinder:
    """
    Complex network path finding using both Graph from module2 and algorithms.
    This implementation is CORRECT.
    """
    def __init__(self):
        self.graph = Graph()
        self.cached_paths = {}
    
    def add_connection(self, node1, node2):
        """Add a connection between two network nodes."""
        self.graph.add_edge(node1, node2)
    
    def find_dfs_path(self, start, target):
        """Find a path using DFS from module2."""
        if (start, target) in self.cached_paths:
            return self.cached_paths[(start, target)]
        
        path = [start] if depth_first_search(self.graph, start, target) else []
        self.cached_paths[(start, target)] = path
        return path
    
    def find_bfs_path(self, start, target):
        """Find a path using BFS from module2."""
        if (start, target) in self.cached_paths:
            return self.cached_paths[(start, target)]
        
        path = [start] if breadth_first_search(self.graph, start, target) else []
        self.cached_paths[(start, target)] = path
        return path
    
    def get_network_nodes(self):
        """Get all nodes in the network."""
        return list(self.graph.adjacency_list.keys())
    
    def clear_cache(self):
        """Clear the path cache."""
        self.cached_paths.clear()


class DataStreamProcessor:
    """
    Process incoming data streams using Queue from module1.
    This implementation is INCORRECT - processes data in wrong order (uses stack behavior).
    """
    def __init__(self, max_buffer=100):
        self.buffer = Queue()
        self.max_buffer = max_buffer
        self.processed = []
    
    def add_data(self, data_item):
        """Add data to the stream."""
        if self.buffer.size() < self.max_buffer:
            self.buffer.enqueue(data_item)
            return True
        return False
    
    def process_next(self):
        """Process the next item in the stream."""
        if not self.buffer.is_empty():
            item = self.buffer.dequeue()
            # BUG: Queue.dequeue() pops from back instead of front
            # This causes LIFO behavior instead of FIFO
            self.processed.append(item)
            return item
        return None
    
    def buffer_size(self):
        """Get current buffer size."""
        return self.buffer.size()
    
    def flush_buffer(self):
        """Process all remaining items in buffer."""
        results = []
        while not self.buffer.is_empty():
            results.append(self.process_next())
        return results


if __name__ == "__main__":
    # Test expression parser
    print("=== Expression Parser Test ===")
    parser = ExpressionParser()
    print("Is '(a + b)' valid:", parser.is_valid_syntax("(a + b)"))
    print("Is '(a + b' valid:", parser.is_valid_syntax("(a + b"))
    print("Evaluate 5 + 3:", parser.evaluate_simple(5, 3, '+'))
    
    # Test route optimizer
    print("\n=== Route Optimizer Test ===")
    optimizer = RouteOptimizer()
    optimizer.add_route('NYC', 'Boston')
    optimizer.add_route('NYC', 'DC')
    optimizer.add_route('Boston', 'DC')
    print("Is NYC connected to DC:", optimizer.check_connectivity('NYC', 'DC'))
    print("All cities:", optimizer.get_all_cities())
    
    # Test system call stack
    print("\n=== System Call Stack Test ===")
    call_stack = SystemCallStack()
    call_stack.push_call('main', [])
    call_stack.push_call('process', ['data'])
    call_stack.push_call('validate', ['input'])
    print("Call depth:", call_stack.get_call_depth())
    print("Current call:", call_stack.get_current_call())
    print("Pop call:", call_stack.pop_call())
    
    # Test task queue
    print("\n=== Task Queue Test ===")
    task_queue = TaskQueue()
    task_queue.add_task('Backup', 9)
    task_queue.add_task('Cleanup', 3)
    task_queue.add_task('Update', 8)
    print("Pending tasks:", task_queue.pending_task_count())
    print("Next task:", task_queue.execute_next_task())
    
    # Test network path finder
    print("\n=== Network Path Finder Test ===")
    finder = NetworkPathFinder()
    finder.add_connection('A', 'B')
    finder.add_connection('B', 'C')
    finder.add_connection('A', 'C')
    print("Network nodes:", finder.get_network_nodes())
    print("DFS from A to C:", finder.find_dfs_path('A', 'C'))
    
    # Test data stream processor
    print("\n=== Data Stream Processor Test ===")
    processor = DataStreamProcessor()
    processor.add_data('item1')
    processor.add_data('item2')
    processor.add_data('item3')
    print("Buffer size:", processor.buffer_size())
    print("Process next:", processor.process_next())
    print("Remaining:", processor.flush_buffer())
