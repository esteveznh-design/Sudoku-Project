# sudoku.py
import pygame
import sys
from sudoku_generator import SudokuGenerator
import copy

pygame.init()
pygame.font.init()

# Constants
WIDTH = 540
HEIGHT = 700
BOARD_SIZE = 9
CELL_SIZE = WIDTH // BOARD_SIZE
MARGIN_TOP = 40
MARGIN_BOTTOM = 120
WINDOW_HEIGHT = HEIGHT + MARGIN_BOTTOM

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)
BLUE = (50, 100, 200)
RED = (220, 50, 50)
GREEN = (50, 180, 80)

FONT = pygame.font.SysFont("consolas", 32)
SMALL_FONT = pygame.font.SysFont("consolas", 18)

# Helper UI button class
class Button:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text

    def draw(self, screen):
        pygame.draw.rect(screen, LIGHT_GRAY, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        text_surf = FONT.render(self.text, True, BLACK)
        tx = self.rect.x + (self.rect.width - text_surf.get_width()) // 2
        ty = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
        screen.blit(text_surf, (tx, ty))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)

# Cell class
class Cell:
    def __init__(self, value, row, col, fixed=False):
        self.value = value            # placed value (0 means empty)
        self.sketched = 0             # sketched temporary value
        self.row = row
        self.col = col
        self.fixed = fixed            # True if initial clue (cannot be edited)
        self.selected = False

    def set_cell_value(self, value):
        self.value = value

    def set_sketched_value(self, value):
        self.sketched = value

    def draw(self, screen, x, y, w, h):
        # background
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, WHITE, rect)

        # draw number
        if self.value != 0:
            # fixed numbers in blue, user placed in black
            color = BLUE if self.fixed else BLACK
            txt = FONT.render(str(self.value), True, color)
            tx = x + (w - txt.get_width()) // 2
            ty = y + (h - txt.get_height()) // 2
            screen.blit(txt, (tx, ty))
        elif self.sketched != 0:
            # small sketch in top-left
            sk = SMALL_FONT.render(str(self.sketched), True, GRAY)
            screen.blit(sk, (x + 6, y + 4))

        # outline if selected
        if self.selected:
            pygame.draw.rect(screen, RED, rect, 3)
        else:
            pygame.draw.rect(screen, BLACK, rect, 1)

# Board class
class Board:
    def __init__(self, width, height, screen, difficulty_removed):
        self.width = width
        self.height = height
        self.screen = screen
        self.difficulty_removed = difficulty_removed

        # Generate sudoku and keep solution
        generator = SudokuGenerator(BOARD_SIZE, 0)
        generator.fill_values()
        self.solution = generator.get_board()  # solved board
        # generate initial board with removals
        generator = SudokuGenerator(BOARD_SIZE, difficulty_removed)
        generator.fill_values()
        generator.remove_cells()
        starting = generator.get_board()

        # Build cells
        self.cells = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.original = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                val = starting[r][c]
                fixed = val != 0
                self.cells[r][c] = Cell(val, r, c, fixed=fixed)
                self.original[r][c] = val

        self.selected_row = None
        self.selected_col = None
        self.last_move = None  # (row,col,value) optional
        self.update_board()

    def draw(self):
        # Draw board background
        board_rect = pygame.Rect(0, MARGIN_TOP, WIDTH, WIDTH)
        pygame.draw.rect(self.screen, BLACK, board_rect, 2)

        # Draw cells
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x = c * CELL_SIZE
                y = MARGIN_TOP + r * CELL_SIZE
                self.cells[r][c].draw(self.screen, x, y, CELL_SIZE, CELL_SIZE)

        # draw thick lines for 3x3 boxes
        for i in range(10):
            line_width = 1
            if i % 3 == 0:
                line_width = 4
            # vertical
            pygame.draw.line(self.screen, BLACK, (i * CELL_SIZE, MARGIN_TOP),
                             (i * CELL_SIZE, MARGIN_TOP + 9 * CELL_SIZE), line_width)
            # horizontal
            pygame.draw.line(self.screen, BLACK, (0, MARGIN_TOP + i * CELL_SIZE),
                             (WIDTH, MARGIN_TOP + i * CELL_SIZE), line_width)

    def select(self, row, col):
        if self.selected_row is not None and self.selected_col is not None:
            self.cells[self.selected_row][self.selected_col].selected = False
        self.selected_row = row
        self.selected_col = col
        self.cells[row][col].selected = True

    def click(self, x, y):
        if x < 0 or x > WIDTH or y < MARGIN_TOP or y > MARGIN_TOP + WIDTH:
            return None
        col = x // CELL_SIZE
        row = (y - MARGIN_TOP) // CELL_SIZE
        return (row, col)

    def clear(self):
        if self.selected_row is None:
            return
        cell = self.cells[self.selected_row][self.selected_col]
        if not cell.fixed:
            cell.set_cell_value(0)
            cell.set_sketched_value(0)
            self.update_board()

    def sketch(self, value):
        if self.selected_row is None:
            return
        cell = self.cells[self.selected_row][self.selected_col]
        if not cell.fixed:
            cell.set_sketched_value(value)

    def place_number(self, value):
        # place sketched value as final value in selected cell
        if self.selected_row is None:
            return False
        r, c = self.selected_row, self.selected_col
        cell = self.cells[r][c]
        if cell.fixed:
            return False
        if value < 0 or value > 9:
            return False
        cell.set_cell_value(value)
        cell.set_sketched_value(0)
        self.update_board()
        return True

    def reset_to_original(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                v = self.original[r][c]
                self.cells[r][c].value = v
                self.cells[r][c].sketched = 0
        self.update_board()

    def is_full(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.cells[r][c].value == 0:
                    return False
        return True

    def update_board(self):
        self.board = [[self.cells[r][c].value for c in range(BOARD_SIZE)] for r in range(BOARD_SIZE)]

    def find_empty(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == 0:
                    return (r, c)
        return None

    def check_board(self):
        # Check if full and matches the solution
        if not self.is_full():
            return False
        # Compare with solution
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] != self.solution[r][c]:
                    return False
        return True

# Screens and main game loop
def start_screen(screen):
    screen.fill(WHITE)
    title = FONT.render("Sudoku - Choose Difficulty", True, BLACK)
    screen.blit(title, ((WIDTH - title.get_width()) // 2, 10))

    easy_btn = Button((60, 120, 140, 60), "Easy")
    med_btn = Button((200, 120, 140, 60), "Medium")
    hard_btn = Button((340, 120, 140, 60), "Hard")
    easy_btn.draw(screen)
    med_btn.draw(screen)
    hard_btn.draw(screen)

    info1 = SMALL_FONT.render("Easy: 30 removed cells", True, BLACK)
    info2 = SMALL_FONT.render("Medium: 40 removed | Hard: 50 removed", True, BLACK)
    screen.blit(info1, ((WIDTH - info1.get_width()) // 2, 200))
    screen.blit(info2, ((WIDTH - info2.get_width()) // 2, 220))

    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if easy_btn.clicked(event.pos):
                    return 30
                if med_btn.clicked(event.pos):
                    return 40
                if hard_btn.clicked(event.pos):
                    return 50

        pygame.time.wait(10)

def draw_buttons(screen, reset_btn, restart_btn, exit_btn):
    reset_btn.draw(screen)
    restart_btn.draw(screen)
    exit_btn.draw(screen)

def game_loop(screen, removed_cells):
    board = Board(WIDTH, WIDTH, screen, removed_cells)

    # Buttons below the board
    reset_btn = Button((40, WIDTH + 60, 140, 50), "Reset")
    restart_btn = Button((200, WIDTH + 60, 140, 50), "Restart")
    exit_btn = Button((360, WIDTH + 60, 140, 50), "Exit")

    running = True
    clock = pygame.time.Clock()
    message = ""

    while running:
        screen.fill(WHITE)
        board.draw()

        # Draw control buttons
        draw_buttons(screen, reset_btn, restart_btn, exit_btn)

        # Display message
        msg_surf = SMALL_FONT.render(message, True, RED if "over" in message.lower() else BLACK)
        screen.blit(msg_surf, (10, WIDTH + 20))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                # check if clicked one of the buttons
                if reset_btn.clicked(pos):
                    board.reset_to_original()
                    message = "Board reset to initial state."
                    continue
                if restart_btn.clicked(pos):
                    return "restart"
                if exit_btn.clicked(pos):
                    pygame.quit()
                    sys.exit()

                clicked = board.click(*pos)
                if clicked:
                    r, c = clicked
                    board.select(r, c)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if board.selected_row is None:
                        board.select(0, 0)
                    else:
                        r = max(0, board.selected_row - 1)
                        c = board.selected_col
                        board.select(r, c)
                elif event.key == pygame.K_DOWN:
                    if board.selected_row is None:
                        board.select(0, 0)
                    else:
                        r = min(8, board.selected_row + 1)
                        c = board.selected_col
                        board.select(r, c)
                elif event.key == pygame.K_LEFT:
                    if board.selected_row is None:
                        board.select(0, 0)
                    else:
                        r = board.selected_row
                        c = max(0, board.selected_col - 1)
                        board.select(r, c)
                elif event.key == pygame.K_RIGHT:
                    if board.selected_row is None:
                        board.select(0, 0)
                    else:
                        r = board.selected_row
                        c = min(8, board.selected_col + 1)
                        board.select(r, c)

                # digits 1-9 sketch
                elif event.unicode and event.unicode.isdigit():
                    d = int(event.unicode)
                    if 1 <= d <= 9:
                        board.sketch(d)

                elif event.key == pygame.K_BACKSPACE:
                    # clear sketched value
                    if board.selected_row is not None:
                        cell = board.cells[board.selected_row][board.selected_col]
                        if not cell.fixed:
                            cell.sketched = 0

                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # submit guess: use the sketched value if present
                    if board.selected_row is not None:
                        cell = board.cells[board.selected_row][board.selected_col]
                        if cell.sketched != 0:
                            placed = board.place_number(cell.sketched)
                            if not placed:
                                message = "Can't place number here."
                            else:
                                # after placement, check full/solved
                                if board.is_full():
                                    if board.check_board():
                                        return "win"
                                    else:
                                        return "lose"

        clock.tick(30)

def win_screen(screen):
    screen.fill(WHITE)
    title = FONT.render("You Win!", True, GREEN)
    screen.blit(title, ((WIDTH - title.get_width()) // 2, 200))

    info1 = SMALL_FONT.render("Congratulations, you solved the puzzle!", True, BLACK)
    info2 = SMALL_FONT.render("Press any key to return to the start menu.", True, BLACK)
    screen.blit(info1, ((WIDTH - info1.get_width()) // 2, 260))
    screen.blit(info2, ((WIDTH - info2.get_width()) // 2, 280))

    pygame.display.update()
    wait_for_key()

def lose_screen(screen):
    screen.fill(WHITE)
    title = FONT.render("Game Over", True, RED)
    screen.blit(title, ((WIDTH - title.get_width()) // 2, 200))

    info1 = SMALL_FONT.render("Board full but incorrect.", True, BLACK)
    info2 = SMALL_FONT.render("Press any key to return to the start menu.", True, BLACK)
    screen.blit(info1, ((WIDTH - info1.get_width()) // 2, 260))
    screen.blit(info2, ((WIDTH - info2.get_width()) // 2, 280))

    pygame.display.update()
    wait_for_key()

def wait_for_key():
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN:
                return

def main():
    screen = pygame.display.set_mode((WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Sudoku")

    while True:
        removed = start_screen(screen)
        result = game_loop(screen, removed)
        if result == "restart":
            continue
        elif result == "win":
            win_screen(screen)
            # AFTER displaying win, return to start
            continue
        elif result == "lose":
            lose_screen(screen)
            continue
        else:
            # start over
            continue

if __name__ == "__main__":
    main()
