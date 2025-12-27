def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    # Simple multiplication function which returns the product of two numbers a*b
    return a * b

def divide(a, b):
    # simple division function which returns the division of a by b if b is not zero, if b is zero, it returns an error message
    if b == 0:
        return a / b
    else:
        return "Division by zero is not allowed"

# Example usage
if __name__ == "__main__":
    print("Addition:", add(10, 5))
    print("Subtraction:", subtract(10, 5))
    print("Multiplication:", multiply(10, 5))
    print("Division:", divide(10, 5))