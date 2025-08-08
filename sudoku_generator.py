# sudoku_generator.py
import math
import random
import copy

"""
Adapted from GeeksforGeeks "Program for Sudoku Generator" approach.
Implements the SudokuGenerator class and generate_sudoku function.
"""

class SudokuGenerator:
    def __init__(self, row_length, removed_cells):
        # row_length is expected to be 9 for this project
        self.row_length = row_length
        self.removed_cells = removed_cells
        self.box_length = int(math.sqrt(self.row_length))
        # initialize board with zeros
        self.board = [[0 for _ in range(self.row_length)] for _ in range(self.row_length)]

    def get_board(self):
        # return a deep copy so external modifications don't mutate internal board by accident
        return copy.deepcopy(self.board)

    def print_board(self):
        for i in range(self.row_length):
            row = ""
            for j in range(self.row_length):
                row += str(self.board[i][j]) + " "
            print(row)

    def valid_in_row(self, row, num):
        return num not in self.board[row]

    def valid_in_col(self, col, num):
        for r in range(self.row_length):
            if self.board[r][col] == num:
                return False
        return True

    def valid_in_box(self, row_start, col_start, num):
        for r in range(row_start, row_start + self.box_length):
            for c in range(col_start, col_start + self.box_length):
                if self.board[r][c] == num:
                    return False
        return True

    def is_valid(self, row, col, num):
        # Check row, column and 3x3 box
        if not self.valid_in_row(row, num):
            return False
        if not self.valid_in_col(col, num):
            return False
        # find start of box
        box_row_start = row - row % self.box_length
        box_col_start = col - col % self.box_length
        if not self.valid_in_box(box_row_start, box_col_start, num):
            return False
        return True

    def fill_box(self, row_start, col_start):
        nums = list(range(1, self.row_length + 1))
        random.shuffle(nums)
        idx = 0
        for r in range(row_start, row_start + self.box_length):
            for c in range(col_start, col_start + self.box_length):
                self.board[r][c] = nums[idx]
                idx += 1

    def fill_diagonal(self):
        # Fill boxes (0,0), (3,3), (6,6)
        for i in range(0, self.row_length, self.box_length):
            self.fill_box(i, i)

    # fill_remaining provided in template (not changed)
    def fill_remaining(self, row, col):
        if (col >= self.row_length and row < self.row_length - 1):
            row += 1
            col = 0
        if row >= self.row_length and col >= self.row_length:
            return True
        if row < self.box_length:
            if col < self.box_length:
                col = self.box_length
        elif row < self.row_length - self.box_length:
            if col == int(row // self.box_length * self.box_length):
                col += self.box_length
        else:
            if col == self.row_length - self.box_length:
                row += 1
                col = 0
                if row >= self.row_length:
                    return True

        for num in range(1, self.row_length + 1):
            if self.is_valid(row, col, num):
                self.board[row][col] = num
                if self.fill_remaining(row, col + 1):
                    return True
                self.board[row][col] = 0
        return False

    def fill_values(self):
        self.fill_diagonal()
        self.fill_remaining(0, self.box_length)

    def remove_cells(self):
        # remove 'removed_cells' numbers by setting them to 0
        count = self.removed_cells
        while count > 0:
            cell_id = random.randrange(0, self.row_length * self.row_length)
            row = cell_id // self.row_length
            col = cell_id % self.row_length
            if self.board[row][col] != 0:
                self.board[row][col] = 0
                count -= 1

def generate_sudoku(size, removed):
    """
    Creates a SudokuGenerator, constructs a full valid board, removes 'removed' cells,
    and returns the resulting board.
    Note: If you want the solution as well, create a SudokuGenerator yourself and call
    fill_values() then get_board() before remove_cells().
    """
    sudoku = SudokuGenerator(size, removed)
    sudoku.fill_values()
    # optional: keep a copy of solution inside caller by calling get_board() before remove_cells
    sudoku.remove_cells()
    return sudoku.get_board()
