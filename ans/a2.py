import tkinter as tk

class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculator")
        
        self.expression = ""
        self.text_input = tk.StringVar()

        # Display screen for input/output
        self.display = tk.Entry(root, font=('Arial', 20), textvariable=self.text_input, bd=10, insertwidth=4, width=14, borderwidth=4)
        self.display.grid(row=0, column=0, columnspan=4)

        # Buttons
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            'C', '0', '=', '+'
        ]
        
        # Place buttons on the grid
        row_val = 1
        col_val = 0
        for button in buttons:
            self.create_button(button, row_val, col_val)
            col_val += 1
            if col_val > 3:
                col_val = 0
                row_val += 1

    def create_button(self, value, row, column):
        if value == "=":
            button = tk.Button(self.root, text=value, padx=20, pady=20, font=('Arial', 18), bg="lightgreen", command=self.equal)
        elif value == "C":
            button = tk.Button(self.root, text=value, padx=20, pady=20, font=('Arial', 18), bg="lightcoral", command=self.clear)
        else:
            button = tk.Button(self.root, text=value, padx=20, pady=20, font=('Arial', 18), command=lambda: self.press(value))
        
        button.grid(row=row, column=column)

    def press(self, value):
        self.expression += str(value)
        self.text_input.set(self.expression)

    def clear(self):
        self.expression = ""
        self.text_input.set("")

    def equal(self):
        try:
            result = str(eval(self.expression))
            self.text_input.set(result)
            self.expression = result
        except Exception as e:
            self.text_input.set("Error")
            self.expression = ""

if __name__ == "__main__":
    root = tk.Tk()
    calc = Calculator(root)
    root.mainloop()
