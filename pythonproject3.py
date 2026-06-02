

import sys
import pygame
import numpy as np
from enum import Enum
from collections import namedtuple

# ══════════════════════════════════════════════════════════════════════════════
#  GRID LAYOUT & DIMENSIONS (Must be Even Dimensions for Hamiltonian Cycles)
# ══════════════════════════════════════════════════════════════════════════════
BLOCK_SIZE = 20
COLS = 30
ROWS = 30
ARENA_PX = COLS * BLOCK_SIZE  # 600 px
STATS_W = 300
WIN_W = ARENA_PX + STATS_W  # 900 px
WIN_H = ARENA_PX  # 600 px
SPEED = 150  # Press UP-ARROW to turbo charge to 1000 FPS!

# ══════════════════════════════════════════════════════════════════════════════
#  THEME COLOURS (Code Bullet Style Continuous Blocks)
# ══════════════════════════════════════════════════════════════════════════════
BLACK = (3, 3, 8)
WHITE = (235, 235, 255)
DARK_CORE = (8, 8, 18)
PANEL_BG = (12, 12, 24)
NEON_CYAN = (0, 225, 255)
ELEC_GREEN = (40, 255, 100)
WARN_RED = (255, 55, 55)
GOLD = (255, 200, 30)
DIM_GREY = (35, 35, 50)
MID_GREY = (90, 90, 115)
SEPARATOR = (25, 25, 45)
TRACK_BLUE = (15, 35, 65)

pygame.init()
_FS = pygame.font.SysFont('courier', 12, bold=True)
_FM = pygame.font.SysFont('courier', 15, bold=True)
_FL = pygame.font.SysFont('arial', 24, bold=True)
_FH = pygame.font.SysFont('arial', 45, bold=True)
_FCELEB = pygame.font.SysFont('impact', 55, bold=False)


class Direction(Enum):
    RIGHT, LEFT, UP, DOWN = 1, 2, 3, 4


Point = namedtuple('Point', 'x, y')


# ══════════════════════════════════════════════════════════════════════════════
#  HAMILTONIAN TRACK GENERATION
# ══════════════════════════════════════════════════════════════════════════════
def generate_hamiltonian_cycle(cols, rows):
    grid_order = {}
    path = []

    # Row 0 runs entirely right
    for x in range(cols):
        path.append((x, 0))

    # Snake pattern downwards/upwards for remaining rows
    for x in reversed(range(cols)):
        if x % 2 == 1:  # Odd columns slide downwards
            for y in range(1, rows):
                path.append((x, y))
        else:  # Even columns track straight back up to Row 1
            for y in reversed(range(1, rows)):
                path.append((x, y))

    for index, coord in enumerate(path):
        grid_order[Point(coord[0] * BLOCK_SIZE, coord[1] * BLOCK_SIZE)] = index

    return grid_order


# ══════════════════════════════════════════════════════════════════════════════
#  PERFECT SNAKE GAME CORE ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class PerfectSnakeGame:
    def __init__(self):
        self.display = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption('HAMILTONIAN CYBER-CORE v9.5 — Perfect Screen Fill')
        self.clock = pygame.time.Clock()

        self.track_indices = generate_hamiltonian_cycle(COLS, ROWS)
        self.total_cells = COLS * ROWS

        self.record = 0
        self.shortcut_count = 0
        self.shortcut_mode_active = True
        self.game_won = False
        self.reset()

    def reset(self):
        self.head = Point(0, 0)
        self.snake = [self.head, Point(0, BLOCK_SIZE), Point(0, BLOCK_SIZE * 2)]
        self.direction = Direction.RIGHT
        self.score = 0
        self.moves_taken = 0
        self.game_won = False
        self._place_food()

    def _place_food(self):
        if len(self.snake) >= self.total_cells:
            self.game_won = True
            return

        while True:
            x = np.random.randint(0, COLS) * BLOCK_SIZE
            y = np.random.randint(0, ROWS) * BLOCK_SIZE
            self.food = Point(x, y)
            if self.food not in self.snake:
                break

    def get_track_distance(self, p1: Point, p2: Point) -> int:
        i1 = self.track_indices[p1]
        i2 = self.track_indices[p2]
        if i2 >= i1:
            return i2 - i1
        return (self.total_cells - i1) + i2

    def calculate_perfect_move(self):
        head = self.head
        neighbors = {
            Direction.RIGHT: Point(head.x + BLOCK_SIZE, head.y),
            Direction.LEFT: Point(head.x - BLOCK_SIZE, head.y),
            Direction.DOWN: Point(head.x, head.y + BLOCK_SIZE),
            Direction.UP: Point(head.x, head.y - BLOCK_SIZE)
        }

        valid_moves = {}
        for d, pt in neighbors.items():
            if 0 <= pt.x < ARENA_PX and 0 <= pt.y < ARENA_PX and pt not in self.snake:
                valid_moves[d] = pt

        track_next_idx = (self.track_indices[head] + 1) % self.total_cells
        best_direction = self.direction

        for d, pt in valid_moves.items():
            if self.track_indices[pt] == track_next_idx:
                best_direction = d
                break

        if not self.shortcut_mode_active:
            return best_direction

        # Shortcut Matrix Math
        best_dist_to_food = self.get_track_distance(head, self.food)
        tail_end = self.snake[-1]
        max_safe_track_skip = self.get_track_distance(head, tail_end) - 3

        for d, pt in valid_moves.items():
            dist_from_this_node_to_food = self.get_track_distance(pt, self.food)
            shortcut_jump_length = self.get_track_distance(head, pt)

            if dist_from_this_node_to_food < best_dist_to_food:
                if shortcut_jump_length < max_safe_track_skip:
                    best_dist_to_food = dist_from_this_node_to_food
                    best_direction = d
                    self.shortcut_count += 1

        return best_direction

    def step(self):
        self.moves_taken += 1
        global SPEED

        # Event Polling Interceptor
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.game_won:
                        self.reset()  # Reset manually after a perfect score win
                    else:
                        self.shortcut_mode_active = not self.shortcut_mode_active
                elif event.key == pygame.K_UP:
                    SPEED = min(1000, SPEED + 50)
                elif event.key == pygame.K_DOWN:
                    SPEED = max(5, SPEED - 50)

        # Freeze movement ticks if game win banner is deployed
        if self.game_won:
            self._render()
            self.clock.tick(15)
            return

        self.direction = self.calculate_perfect_move()

        if self.direction == Direction.RIGHT:
            self.head = Point(self.head.x + BLOCK_SIZE, self.head.y)
        elif self.direction == Direction.LEFT:
            self.head = Point(self.head.x - BLOCK_SIZE, self.head.y)
        elif self.direction == Direction.DOWN:
            self.head = Point(self.head.x, self.head.y + BLOCK_SIZE)
        elif self.direction == Direction.UP:
            self.head = Point(self.head.x, self.head.y - BLOCK_SIZE)

        self.snake.insert(0, self.head)

        if self.head == self.food:
            self.score += 1
            if self.score > self.record:
                self.record = self.score
            self._place_food()
        else:
            self.snake.pop()

        if self.head in self.snake[1:] or not (0 <= self.head.x < ARENA_PX and 0 <= self.head.y < ARENA_PX):
            print("[CRASH ERROR] Safety path breached!")
            self.reset()

        self._render()
        self.clock.tick(SPEED)

    def _render(self):
        self.display.fill(BLACK)

        # 1. Math Canvas Map
        pygame.draw.rect(self.display, DARK_CORE, (0, 0, ARENA_PX, ARENA_PX))

        # Draw background coordinates tracking map
        for pt in self.track_indices.keys():
            pygame.draw.rect(self.display, TRACK_BLUE, (pt.x + 9, pt.y + 9, 2, 2))

        # Seamless Code Bullet Fill Matrix Rendering Loop
        for i, pt in enumerate(self.snake):
            col = NEON_CYAN if i == 0 else ELEC_GREEN
            # Drawn at full block dimensions (No padding gap) to achieve maxed solid block aesthetic
            pygame.draw.rect(self.display, col, (pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))

        # Draw Goal Objective Node (Hide if game is won and grid is packed solid)
        if not self.game_won:
            pygame.draw.rect(self.display, WARN_RED, (self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(self.display, GOLD, (self.food.x + 4, self.food.y + 4, BLOCK_SIZE - 8, BLOCK_SIZE - 8))

        # 2. OVERLAY: PERFECT SCORE BANNER CELEBRATION
        if self.game_won:
            # Drop a darkened translucent veil across the entire grid
            overlay = pygame.Surface((ARENA_PX, ARENA_PX), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.display.blit(overlay, (0, 0))

            # Render a stylized Neon-Border Box
            pygame.draw.rect(self.display, GOLD, (50, 200, 500, 180), 4)
            pygame.draw.rect(self.display, BLACK, (54, 204, 492, 172))

            # Text Blits
            t1 = _FCELEB.render("PERFECT SCORE", True, GOLD)
            t2 = _FL.render(f"GAME COMPLETED IN {self.moves_taken:,} STEPS", True, WHITE)
            t3 = _FS.render("[PRESS SPACEBAR TO RESTART RUN]", True, NEON_CYAN)

            self.display.blit(t1, (ARENA_PX // 2 - t1.get_width() // 2, 220))
            self.display.blit(t2, (ARENA_PX // 2 - t2.get_width() // 2, 295))
            self.display.blit(t3, (ARENA_PX // 2 - t3.get_width() // 2, 345))

        # 3. Dynamic Technical Diagnostic Data Column
        x0 = ARENA_PX + 4
        pygame.draw.rect(self.display, PANEL_BG, (x0, 0, STATS_W, WIN_H))
        pygame.draw.rect(self.display, SEPARATOR, (ARENA_PX, 0, 4, WIN_H))

        self.display.blit(_FM.render('━━Perfect Core v9.5━━', True, NEON_CYAN), (x0 + 12, 15))

        self.display.blit(_FS.render('CURRENT SCORE', True, MID_GREY), (x0 + 15, 55))
        self.display.blit(_FH.render(f"{self.score:03d}", True, ELEC_GREEN), (x0 + 12, 70))

        self.display.blit(_FS.render('MAX RECORD', True, MID_GREY), (x0 + 15, 135))
        self.display.blit(_FH.render(f"{self.record:03d}/{self.total_cells}", True, GOLD), (x0 + 12, 150))

        fill_pct = (len(self.snake) / self.total_cells) * 100
        self.display.blit(_FS.render(f"BOARD SATURATION: {fill_pct:.1f}%", True, WHITE), (x0 + 15, 225))
        pygame.draw.rect(self.display, DIM_GREY, (x0 + 15, 245, STATS_W - 30, 12))
        pygame.draw.rect(self.display, NEON_CYAN, (x0 + 15, 245, int((STATS_W - 30) * (fill_pct / 100)), 12))

        pygame.draw.line(self.display, SEPARATOR, (x0 + 10, 280), (WIN_W - 10, 280), 1)

        self.display.blit(_FS.render(f"SIMULATION ENGINE SPEEDS: {SPEED} FPS", True, MID_GREY), (x0 + 15, 305))
        self.display.blit(_FS.render(f"ENGINE STEPS RUN:  {self.moves_taken:,}", True, MID_GREY), (x0 + 15, 330))
        self.display.blit(_FS.render(f"SHORTCUT JUMPS:    {self.shortcut_count:,}", True, MID_GREY), (x0 + 15, 355))

        mode_txt, mode_col = ("SHORTCUTS ACTIVATED", ELEC_GREEN) if self.shortcut_mode_active else (
            "PURE FIXED CYCLE TRACK", WARN_RED)
        if self.game_won: mode_txt, mode_col = ("SIMULATION COMPLETE", GOLD)
        pygame.draw.rect(self.display, DIM_GREY, (x0 + 15, 395, STATS_W - 30, 30))
        self.display.blit(_FS.render(mode_txt, True, mode_col), (x0 + 28, 403))

        pygame.draw.line(self.display, SEPARATOR, (x0 + 10, 455), (WIN_W - 10, 455), 1)

        self.display.blit(_FS.render("MANUAL CONTROL OVERRIDES:", True, GOLD), (x0 + 15, 475))
        self.display.blit(_FS.render("[SPACE]  Toggle AI / Reset Win", True, WHITE), (x0 + 15, 505))
        self.display.blit(_FS.render("[ARROW UP]   Speed Up Clock", True, WHITE), (x0 + 15, 530))
        self.display.blit(_FS.render("[ARROW DOWN] Slow Down Clock", True, WHITE), (x0 + 15, 555))

        pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
#  RUNTIME MASTER DISPATCH LOOP ENTRY
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    perfect_engine = PerfectSnakeGame()
    while True:
        perfect_engine.step()