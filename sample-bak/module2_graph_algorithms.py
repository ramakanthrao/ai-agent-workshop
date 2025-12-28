"""
Module 2: Graph Algorithms and Data Structures
This module builds upon module1_data_structures and provides graph operations.
Depends on: module1_data_structures (Stack, Queue, validate_balanced_parentheses)
"""

from module1_data_structures import Stack, Queue, validate_balanced_parentheses


class Graph:
    """
    Undirected graph representation using adjacency list.
    This implementation is CORRECT.
    """
    def __init__(self):
        self.adjacency_list = {}
    
    def add_vertex(self, vertex):
        """Add a vertex to the graph."""
        if vertex not in self.adjacency_list:
            self.adjacency_list[vertex] = []
    
    def add_edge(self, vertex1, vertex2):
        """Add an undirected edge between two vertices."""
        self.add_vertex(vertex1)
        self.add_vertex(vertex2)
        self.adjacency_list[vertex1].append(vertex2)
        self.adjacency_list[vertex2].append(vertex1)
    
    def get_neighbors(self, vertex):
        """Get all neighbors of a vertex."""
        return self.adjacency_list.get(vertex, [])


def depth_first_search(graph, start, target):
    """
    Perform DFS traversal using Stack from module1_data_structures.
    This implementation is CORRECT.
    """
    stack = Stack()
    visited = set()
    stack.push(start)
    visited.add(start)
    
    while not stack.is_empty():
        vertex = stack.pop()
        
        if vertex == target:
            return True
        
        for neighbor in graph.get_neighbors(vertex):
            if neighbor not in visited:
                visited.add(neighbor)
                stack.push(neighbor)
    
    return False


def breadth_first_search(graph, start, target):
    """
    Perform BFS traversal using Queue from module1_data_structures.
    This implementation is INCORRECT - doesn't mark neighbors as visited when adding to queue.
    """
    queue = Queue()
    visited = set()
    queue.enqueue(start)
    visited.add(start)
    
    while not queue.is_empty():
        vertex = queue.dequeue()
        
        if vertex == target:
            return True
        
        for neighbor in graph.get_neighbors(vertex):
            # BUG: Should check if neighbor is visited before enqueuing
            # This causes infinite loops and revisiting vertices
            queue.enqueue(neighbor)
            visited.add(neighbor)
    
    return False


def find_shortest_path(graph, start, end):
    """
    Find the shortest path between two vertices using BFS concepts.
    This implementation is INCORRECT - uses wrong data structure (Stack instead of Queue).
    """
    stack = Stack()  # BUG: Should be Queue for BFS
    visited = set()
    parent = {start: None}
    
    stack.push(start)
    visited.add(start)
    
    while not stack.is_empty():
        vertex = stack.pop()
        
        if vertex == end:
            path = []
            current = end
            while current is not None:
                path.append(current)
                current = parent.get(current)
            return path[::-1]
        
        for neighbor in graph.get_neighbors(vertex):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = vertex
                stack.push(neighbor)
    
    return []


def is_valid_expression_with_stack(expression):
    """
    Check if an expression has valid balanced operators.
    Reuses validate_balanced_parentheses from module1_data_structures.
    This implementation is CORRECT.
    """
    return validate_balanced_parentheses(expression)


def count_connected_components(graph):
    """
    Count the number of connected components in an undirected graph.
    This implementation is INCORRECT - uses DFS wrong by not checking vertex equality.
    """
    visited = set()
    components = 0
    
    for vertex in graph.adjacency_list:
        if vertex not in visited:
            # BUG: depth_first_search returns boolean, not visited set
            # This approach is fundamentally wrong
            stack = Stack()
            stack.push(vertex)
            visited.add(vertex)
            
            while not stack.is_empty():
                current = stack.pop()
                # BUG: Missing logic to add unvisited neighbors to stack
                for neighbor in graph.get_neighbors(current):
                    if neighbor not in visited:
                        pass  # BUG: Should push neighbor to stack
            
            components += 1
    
    return components


if __name__ == "__main__":
    # Test examples
    print("Creating graph...")
    g = Graph()
    g.add_edge(1, 2)
    g.add_edge(1, 3)
    g.add_edge(2, 4)
    
    print("DFS search for 4:", depth_first_search(g, 1, 4))
    print("BFS search for 4:", breadth_first_search(g, 1, 4))
    print("Shortest path 1 to 4:", find_shortest_path(g, 1, 4))
    
    print("\nExpression validation:")
    print(is_valid_expression_with_stack("{ [ ( ) ] }"))
    
    print("\nConnected components:")
    print(count_connected_components(g))
