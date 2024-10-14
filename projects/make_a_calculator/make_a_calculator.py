# ```python
def get_number_input(prompt):
    while True:
        try:
            num = float(input(prompt))
            return num
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def get_operator_input():
    while True:
        operator = input("Enter the operator (+, -, *, /): ")
        if operator in ['+', '-', '*', '/']:
            return operator
        else:
            print("Invalid operator. Please enter one of +, -, *, or /.")

def add(x, y):
    return x + y

def subtract(x, y):
    return x - y

def multiply(x, y):
    return x * y

def divide(x, y):
    if y != 0:
        return x / y
    else:
        raise ZeroDivisionError("Cannot divide by zero!")

operations = {
    '+': add,
    '-': subtract,
    '*': multiply,
    '/': divide
}

num1 = get_number_input("Enter the first number: ")
operator = get_operator_input()
num2 = get_number_input("Enter the second number: ")

try:
    result = operations[operator](num1, num2)
except ZeroDivisionError as e:
    print(f"Error: {e}")
else:
    print("Result:", result)

# ```