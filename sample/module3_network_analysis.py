"""
Module 3: Advanced Network Analysis
This module builds upon module2_graph_algorithms for complex network operations.
Depends on: module2_graph_algorithms (Graph, depth_first_search, breadth_first_search, find_shortest_path)
            module1_data_structures (Stack, Queue)
"""

from module2_graph_algorithms import (
    Graph, depth_first_search, breadth_first_search, find_shortest_path
)
from module1_data_structures import Stack, Queue


class WeightedGraph(Graph):
    """
    Weighted graph extending the Graph class from module2.
    This implementation is CORRECT.
    """
    def __init__(self):
        super().__init__()
        self.weights = {}
    
    def add_weighted_edge(self, vertex1, vertex2, weight):
        """Add a weighted undirected edge between two vertices."""
        self.add_edge(vertex1, vertex2)
        self.weights[(vertex1, vertex2)] = weight
        self.weights[(vertex2, vertex1)] = weight
    
    def get_weight(self, vertex1, vertex2):
        """Get the weight of an edge."""
        return self.weights.get((vertex1, vertex2), float('inf'))


def dijkstra_shortest_path(graph, start, end):
    """
    Find shortest path using Dijkstra's algorithm with weighted graph.
    This implementation is INCORRECT - uses wrong comparison operator.
    """
    distances = {vertex: float('inf') for vertex in graph.adjacency_list}
    distances[start] = 0
    visited = set()
    parent = {start: None}
    
    while len(visited) < len(graph.adjacency_list):
        # Find unvisited vertex with minimum distance
        min_vertex = None
        min_distance = float('inf')
        
        for vertex in graph.adjacency_list:
            if vertex not in visited and distances[vertex] < min_distance:
                min_vertex = vertex
                min_distance = distances[vertex]
        
        if min_vertex is None:
            break
        
        visited.add(min_vertex)
        
        for neighbor in graph.get_neighbors(min_vertex):
            if neighbor not in visited:
                weight = graph.get_weight(min_vertex, neighbor)
                new_distance = distances[min_vertex] + weight
                
                # BUG: Should use < (less than), not > (greater than)
                if new_distance > distances[neighbor]:
                    distances[neighbor] = new_distance
                    parent[neighbor] = min_vertex
    
    # Reconstruct path
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = parent.get(current)
    
    return path[::-1] if distances[end] != float('inf') else []


def find_all_paths_using_dfs(graph, start, end):
    """
    Find all paths between two vertices using DFS from module2.
    This implementation is CORRECT.
    """
    def dfs_helper(current, target, visited, path, all_paths):
        if current == target:
            all_paths.append(path[:])
            return
        
        for neighbor in graph.get_neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                dfs_helper(neighbor, target, visited, path, all_paths)
                path.pop()
                visited.remove(neighbor)
    
    all_paths = []
    visited = {start}
    dfs_helper(start, end, visited, [start], all_paths)
    return all_paths


def has_cycle_undirected(graph):
    """
    Detect if an undirected graph has a cycle.
    This implementation is INCORRECT - doesn't properly track parent vertex.
    """
    visited = set()
    
    def dfs_cycle(vertex, parent):
        visited.add(vertex)
        
        for neighbor in graph.get_neighbors(vertex):
            if neighbor not in visited:
                # BUG: Should pass vertex as parent, but passes None
                if dfs_cycle(neighbor, None):
                    return True
            elif neighbor != parent:
                return True
        
        return False
    
    for vertex in graph.adjacency_list:
        if vertex not in visited:
            if dfs_cycle(vertex, None):
                return True
    
    return False


def topological_sort(graph):
    """
    Perform topological sort on a directed acyclic graph (DAG).
    Uses Stack from module1_data_structures.
    This implementation is INCORRECT - wrong order of operations.
    """
    in_degree = {vertex: 0 for vertex in graph.adjacency_list}
    
    for vertex in graph.adjacency_list:
        for neighbor in graph.get_neighbors(vertex):
            in_degree[neighbor] += 1
    
    queue = Queue()
    for vertex in graph.adjacency_list:
        if in_degree[vertex] == 0:
            queue.enqueue(vertex)
    
    result = []
    
    while not queue.is_empty():
        vertex = queue.dequeue()
        # BUG: Should append vertex to result, not to in_degree
        in_degree[vertex] = vertex
        
        for neighbor in graph.get_neighbors(vertex):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.enqueue(neighbor)
    
    return result


def network_flow_reachability(graph, source, targets):
    """
    Check which target nodes are reachable from source using BFS from module2.
    This implementation is CORRECT.
    """
    reachable = []
    
    for target in targets:
        if breadth_first_search(graph, source, target):
            reachable.append(target)
    
    return reachable


def analyze_graph_connectivity(graph):
    """
    Analyze graph connectivity metrics using both DFS and BFS.
    This implementation is CORRECT.
    """
    if not graph.adjacency_list:
        return {
            'vertices': 0,
            'edges': 0,
            'is_connected': False,
            'avg_degree': 0
        }
    
    num_vertices = len(graph.adjacency_list)
    num_edges = sum(len(neighbors) for neighbors in graph.adjacency_list.values()) // 2
    
    # Check connectivity by seeing if all vertices are reachable from first vertex
    first_vertex = list(graph.adjacency_list.keys())[0]
    is_connected = True
    
    for vertex in graph.adjacency_list:
        if vertex != first_vertex:
            if not depth_first_search(graph, first_vertex, vertex):
                is_connected = False
                break
    
    avg_degree = (2 * num_edges) / num_vertices if num_vertices > 0 else 0
    
    return {
        'vertices': num_vertices,
        'edges': num_edges,
        'is_connected': is_connected,
        'avg_degree': avg_degree
    }


if __name__ == "__main__":
    # Test examples
    print("Creating weighted graph...")
    g = WeightedGraph()
    g.add_weighted_edge('A', 'B', 4)
    g.add_weighted_edge('A', 'C', 2)
    g.add_weighted_edge('B', 'C', 1)
    g.add_weighted_edge('B', 'D', 5)
    g.add_weighted_edge('C', 'D', 8)
    
    print("Dijkstra shortest path A to D:", dijkstra_shortest_path(g, 'A', 'D'))
    print("All paths from A to D:", find_all_paths_using_dfs(g, 'A', 'D'))
    print("Has cycle:", has_cycle_undirected(g))
    
    print("\nGraph connectivity analysis:")
    analysis = analyze_graph_connectivity(g)
    for key, value in analysis.items():
        print(f"  {key}: {value}")
    
    print("\nNetwork reachability from A:")
    targets = ['B', 'C', 'D']
    reachable = network_flow_reachability(g, 'A', targets)
    print(f"  Reachable targets: {reachable}")
