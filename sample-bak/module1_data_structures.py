"""
Module 1: Basic Data Structures and Utilities
This module provides foundational data structures and helper functions.
"""

class Stack:
    """
    Stack implementation using a list.
    This implementation is CORRECT.
    """
    def __init__(self):
        self.items = []
    
    def push(self, item):
        """Add an item to the top of the stack."""
        self.items.append(item)
    
    def pop(self):
        """Remove and return the top item from the stack."""
        if self.is_empty():
            raise IndexError("Cannot pop from empty stack")
        return self.items.pop()
    
    def peek(self):
        """Return the top item without removing it."""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items[-1]
    
    def is_empty(self):
        """Check if the stack is empty."""
        return len(self.items) == 0
    
    def size(self):
        """Return the number of items in the stack."""
        return len(self.items)


class Queue:
    """
    Queue implementation using a list.
    This implementation is INCORRECT - uses wrong index for dequeue.
    """
    def __init__(self):
        self.items = []
    
    def enqueue(self, item):
        """Add an item to the back of the queue."""
        self.items.append(item)
    
    def dequeue(self):
        """Remove and return the front item from the queue."""
        if self.is_empty():
            raise IndexError("Cannot dequeue from empty queue")
        # BUG: Should pop from index 0 (front), not -1 (back)
        return self.items.pop(-1)
    
    def front(self):
        """Return the front item without removing it."""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items[0]
    
    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.items) == 0
    
    def size(self):
        """Return the number of items in the queue."""
        return len(self.items)


def validate_balanced_parentheses(expression):
    """
    Check if parentheses, brackets, and braces are balanced.
    Uses Stack for validation.
    This implementation is CORRECT.
    """
    stack = Stack()
    pairs = {'(': ')', '[': ']', '{': '}'}
    
    for char in expression:
        if char in pairs:
            stack.push(char)
        elif char in pairs.values():
            if stack.is_empty() or pairs[stack.pop()] != char:
                return False
    
    return stack.is_empty()


def convert_infix_to_postfix(expression):
    """
    Convert infix expression to postfix notation.
    Example: "3 + 4 * 2" → "3 4 2 * +"
    This implementation is INCORRECT - wrong operator precedence handling.
    """
    stack = Stack()
    postfix = []
    precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
    
    tokens = expression.split()
    
    for token in tokens:
        if token.isdigit():
            postfix.append(token)
        elif token in precedence:
            # BUG: Should pop operators with >= precedence, not just >
            while (not stack.is_empty() and stack.peek() in precedence and
                   precedence[stack.peek()] > precedence[token]):
                postfix.append(stack.pop())
            stack.push(token)
        elif token == '(':
            stack.push(token)
        elif token == ')':
            while not stack.is_empty() and stack.peek() != '(':
                postfix.append(stack.pop())
            if not stack.is_empty():
                stack.pop()  # Remove '('
    
    while not stack.is_empty():
        postfix.append(stack.pop())
    
    return ' '.join(postfix)


def find_duplicate_in_array(arr):
    """
    Find a duplicate element in array containing n+1 integers where 1 to n appear exactly once.
    This implementation is CORRECT.
    """
    if not arr:
        return None
    
    # Floyd's cycle detection algorithm
    slow = fast = arr[0]
    
    # Find intersection point in the cycle
    while True:
        slow = arr[slow]
        fast = arr[arr[fast]]
        if slow == fast:
            break
    
    # Find the entrance to the cycle
    slow = arr[0]
    while slow != fast:
        slow = arr[slow]
        fast = arr[fast]
    
    return slow


if __name__ == "__main__":
    # Test examples
    print("Stack test:")
    stack = Stack()
    stack.push(1)
    stack.push(2)
    print("Popped:", stack.pop())
    
    print("\nQueue test:")
    queue = Queue()
    queue.enqueue(1)
    queue.enqueue(2)
    print("Dequeued:", queue.dequeue())
    
    print("\nBalanced parentheses test:")
    print(validate_balanced_parentheses("( [ { } ] )"))
    
    print("\nInfix to postfix test:")
    print(convert_infix_to_postfix("3 + 4 * 2"))
