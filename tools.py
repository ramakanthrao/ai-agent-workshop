def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    # Simple multiplication function which returns the product of two numbers a*b
    return a * b

def divide(a, b):
    # simple division function which raises ZeroDivisionError instead of returning an error message when dividing by zero.
    if b == 0:
        raise ZeroDivisionError("division by zero")
    else:
        return a / b

# Example usage
if __name__ == "__main__":
    print("Addition:", add(10, 5))
    print("Subtraction:", subtract(10, 5))
    print("Multiplication:", multiply(10, 5))
    print("Division:", divide(10, 5))