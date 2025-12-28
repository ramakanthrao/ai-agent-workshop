def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    # Multiplication function which returns the product of two numbers a*b
    return a * b

def divide(a, b):
    try:
        return a / b
    except ZeroDivisionError as e:
        raise ValueError('division by zero is not allowed') from None

# Example usage
if __name__ == "__main__":
    print("Addition:", add(10, 5))
    print("Subtraction:", subtract(10, 5))
    print("Multiplication:", multiply(10, 5))
    print("Division:", divide(10, 5))