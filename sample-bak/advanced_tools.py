"""
Advanced sample file with complex functions for testing the AI code agent.
Contains a mix of correct and incorrect implementations with longer logic.
"""

def calculate_factorial(n):
    """
    Calculate the factorial of a number using recursion.
    This implementation is CORRECT.
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def find_largest_prime(numbers):
    """
    Find the largest prime number in a list.
    This implementation is CORRECT.
    """
    def is_prime(num):
        if num < 2:
            return False
        if num == 2:
            return True
        if num % 2 == 0:
            return False
        for i in range(3, int(num ** 0.5) + 1, 2):
            if num % i == 0:
                return False
        return True
    
    primes = [num for num in numbers if is_prime(num)]
    if not primes:
        return None
    return max(primes)


def merge_sorted_arrays(arr1, arr2):
    """
    Merge two sorted arrays into one sorted array.
    This implementation is INCORRECT - uses addition instead of proper merging.
    """
    # BUG: This just concatenates, doesn't merge properly
    result = arr1 + arr2
    return result


def calculate_average(numbers):
    """
    Calculate the average of a list of numbers.
    This implementation is CORRECT with proper error handling.
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    
    return average


def remove_duplicates_maintain_order(items):
    """
    Remove duplicate items from a list while maintaining order.
    This implementation is CORRECT.
    """
    seen = set()
    result = []
    
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    
    return result


def find_missing_number(numbers):
    """
    Find the missing number in a sequence from 1 to n.
    Expected: [1,2,3,5] should return 4
    This implementation is INCORRECT - uses wrong operator.
    """
    n = len(numbers) + 1
    expected_sum = n * (n + 1) // 2
    actual_sum = sum(numbers)
    # BUG: Should subtract, not add
    missing = expected_sum + actual_sum
    return missing


def rotate_array(arr, k):
    """
    Rotate array to the right by k steps.
    Example: [1,2,3,4,5] rotated by 2 becomes [4,5,1,2,3]
    This implementation is CORRECT.
    """
    if not arr:
        return arr
    
    k = k % len(arr)  # Handle k larger than array length
    
    # Rotate using slicing
    rotated = arr[-k:] + arr[:-k]
    return rotated


def find_peak_element(arr):
    """
    Find a peak element in an unsorted array.
    A peak is an element greater than its neighbors.
    This implementation is INCORRECT - uses wrong comparison.
    """
    if len(arr) < 1:
        return None
    
    for i in range(len(arr)):
        is_peak = True
        
        # BUG: Should check if current element is GREATER than neighbors
        # This checks if it's LESS than neighbors (incorrect logic)
        if i > 0 and arr[i] < arr[i - 1]:
            is_peak = False
        if i < len(arr) - 1 and arr[i] < arr[i + 1]:
            is_peak = False
        
        if is_peak:
            return arr[i]
    
    return None


def count_word_frequency(text):
    """
    Count the frequency of each word in a text.
    This implementation is CORRECT.
    """
    if not text:
        return {}
    
    words = text.lower().split()
    frequency = {}
    
    for word in words:
        # Remove punctuation from word
        clean_word = ''.join(c for c in word if c.isalnum())
        
        if clean_word:
            frequency[clean_word] = frequency.get(clean_word, 0) + 1
    
    return frequency


def is_valid_palindrome(s):
    """
    Check if a string is a valid palindrome (ignoring spaces and punctuation).
    This implementation is INCORRECT - doesn't ignore special characters.
    """
    # BUG: Should filter out non-alphanumeric characters first
    # This checks with all characters including spaces and punctuation
    cleaned = s.lower()
    return cleaned == cleaned[::-1]


def binary_search(arr, target):
    """
    Perform binary search on a sorted array.
    This implementation is CORRECT.
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1  # Element not found


def calculate_compound_interest(principal, rate, time, compounds_per_year):
    """
    Calculate compound interest.
    Formula: A = P(1 + r/n)^(nt)
    This implementation is INCORRECT - wrong formula application.
    """
    # BUG: Should use ** (power) not * (multiplication) for exponent
    # A = P(1 + r/n)^(nt)
    amount = principal * (1 + rate / compounds_per_year) * (compounds_per_year * time)
    interest = amount - principal
    return interest


def get_nth_fibonacci(n):
    """
    Get the nth number in the Fibonacci sequence.
    This implementation is CORRECT using dynamic programming.
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")
    if n == 1 or n == 2:
        return 1
    
    # Use DP approach for efficiency
    fib = [0] * (n + 1)
    fib[1] = 1
    fib[2] = 1
    
    for i in range(3, n + 1):
        fib[i] = fib[i - 1] + fib[i - 2]
    
    return fib[n]


def validate_email(email):
    """
    Validate email format.
    This implementation is CORRECT with basic validation rules.
    """
    if not email or '@' not in email:
        return False
    
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    local, domain = parts
    
    # Check local part
    if not local or len(local) > 64:
        return False
    
    # Check domain part
    if not domain or '.' not in domain:
        return False
    
    if domain.startswith('.') or domain.endswith('.'):
        return False
    
    return True


def find_longest_common_substring(str1, str2):
    """
    Find the longest common substring between two strings.
    This implementation is INCORRECT - uses wrong comparison logic.
    """
    if not str1 or not str2:
        return ""
    
    max_length = 0
    max_substring = ""
    
    for i in range(len(str1)):
        for j in range(len(str2)):
            # BUG: Should check if characters match, not compare indices
            length = 0
            while (i + length < len(str1) and j + length < len(str2) and
                   str1[i + length] != str2[j + length]):  # Should be == not !=
                length += 1
            
            if length > max_length:
                max_length = length
                max_substring = str1[i:i + length]
    
    return max_substring


def quicksort(arr):
    """
    Sort an array using quicksort algorithm.
    This implementation is CORRECT.
    """
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quicksort(left) + middle + quicksort(right)


if __name__ == "__main__":
    # Test examples
    print("Testing factorial:", calculate_factorial(5))
    print("Testing largest prime:", find_largest_prime([10, 15, 20, 23, 17]))
    print("Testing average:", calculate_average([1, 2, 3, 4, 5]))
    print("Testing remove duplicates:", remove_duplicates_maintain_order([1, 2, 2, 3, 3, 3]))
    print("Testing rotate array:", rotate_array([1, 2, 3, 4, 5], 2))
    print("Testing word frequency:", count_word_frequency("Hello world hello"))
    print("Testing binary search:", binary_search([1, 3, 5, 7, 9], 5))
    print("Testing nth fibonacci:", get_nth_fibonacci(10))
    print("Testing email validation:", validate_email("test@example.com"))
    print("Testing quicksort:", quicksort([64, 34, 25, 12, 22, 11, 90]))
