# **Improved Game Board Generation Code**

# Based on the provided code snippet, I'll improve it by including a full game board generation and display. We will also use Object-Oriented Programming (OOP) principles to create a `GameBoard` class.

# ```python
# Import necessary modules
import random

# Constants
GRID_SIZE = 10
CELL_SIZE = 1
NUM_MINES = 10

class GameBoard:
    def __init__(self, grid_size):
        """
        Initialize the game board with a specified size.
        
        Args:
            grid_size (int): The size of the game board.
        """
        self.grid_size = grid_size
        self.board = [[0] * grid_size for _ in range(grid_size)]
        self.num_mines = NUM_MINES

    def generate_board(self):
        """
        Generate a random game board with mines and hidden numbers.
        """
        # Randomly place mines on the board
        mine_locations = set()
        while len(mine_locations) < self.num_mines:
            x, y = random.randint(0, self.grid_size - 1), random.randint(0, self.grid_size - 1)
            if (x, y) not in mine_locations:
                mine_locations.add((x, y))

        # Assign numbers to non-mine cells
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                if (x, y) not in mine_locations:
                    self.board[x][y] = random.randint(0, 10)

    def print_board(self):
        """
        Print the game board.
        """
        for row in self.board:
            print(' '.join(str(cell).ljust(2) for cell in row))

# Create a new game board
game_board = GameBoard(GRID_SIZE)
game_board.generate_board()
print("Game Board:")
game_board.print_board()
# ```

# **Example Use Cases**

# 1. Run the code to generate and display a random 10x10 game board.
# 2. Modify the `NUM_MINES` constant to change the number of mines on the board.

# Note: The above code uses a simple and inefficient method for generating numbers on non-mine cells. For a more realistic game, you may want to consider using a more complex algorithm or incorporating user input to generate numbers.