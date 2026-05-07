import pygame
import heapq
import sys
import random

# --- CONFIGURATION ---
BASE_WIDTH, BASE_HEIGHT = 800, 600 # Internal resolution
GRID_SIZE = 25
ROWS, COLS = BASE_HEIGHT // GRID_SIZE, BASE_WIDTH // GRID_SIZE
FPS = 60

# Colors
BG_COLOR = (15, 15, 20)
WALL_COLOR = (45, 45, 55)
PLAYER_COLOR = (0, 210, 255)
AI_COLOR = (255, 60, 60)
GOAL_COLOR = (0, 255, 120)
TEXT_COLOR = (255, 255, 255)

high_score = 0

class Node:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.g = float('inf')
        self.f = float('inf')
        self.parent = None
    def __lt__(self, other): return self.f < other.f

def a_star(start, target, walls):
    open_set = []
    start_node = Node(*start)
    start_node.g = 0
    start_node.f = abs(start[0]-target[0]) + abs(start[1]-target[1])
    heapq.heappush(open_set, start_node)
    visited = {}
    while open_set:
        curr = heapq.heappop(open_set)
        if (curr.x, curr.y) == target:
            path = []
            while curr:
                path.append((curr.x, curr.y)); curr = curr.parent
            return path[::-1]
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = curr.x + dx, curr.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and (nx, ny) not in walls:
                temp_g = curr.g + 1
                if temp_g < visited.get((nx, ny), float('inf')):
                    neighbor = Node(nx, ny)
                    neighbor.parent = curr
                    neighbor.g = temp_g
                    neighbor.f = temp_g + abs(nx-target[0]) + abs(ny-target[1])
                    visited[(nx, ny)] = temp_g
                    heapq.heappush(open_set, neighbor)
    return []

pygame.init()

# --- WINDOW SETUP ---
# Set window to be resizable
screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.RESIZABLE)
# This is our internal 'Canvas' where all drawing happens
canvas = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))

pygame.display.set_caption("Shadow Stalker - Fullscreen Scaling")
font_lg = pygame.font.SysFont("Verdana", 40, bold=True)
font_md = pygame.font.SysFont("Verdana", 24, bold=True)
font_sm = pygame.font.SysFont("Verdana", 18)

def get_random_goal(p_pos, walls):
    while True:
        gx, gy = random.randint(1, COLS-2), random.randint(1, ROWS-2)
        if (gx, gy) not in walls and (gx, gy) != tuple(p_pos): return (gx, gy)

def show_menu():
    while True:
        canvas.fill(BG_COLOR)
        title = font_lg.render("SHADOW STALKER", True, TEXT_COLOR)
        e_btn = font_sm.render("[1] EASY  [2] MEDIUM  [3] HARD  [Q] QUIT", True, (200, 200, 200))
        
        canvas.blit(title, (BASE_WIDTH//2 - 180, 250))
        canvas.blit(e_btn, (BASE_WIDTH//2 - 190, 350))
        
        # Scaling Logic for Menu
        window_size = screen.get_size()
        scaled_canvas = pygame.transform.smoothscale(canvas, window_size)
        screen.blit(scaled_canvas, (0, 0))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE: pass # Handled by screen.get_size()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: return "easy"
                if event.key == pygame.K_2: return "medium"
                if event.key == pygame.K_3: return "hard"
                if event.key == pygame.K_q: pygame.quit(); sys.exit()

def play_game(diff):
    global high_score
    settings = {"easy": (15, 250, 0.8), "medium": (10, 160, 0.4), "hard": (6, 110, 0.2)}
    AI_RATE, VISION, REGEN = settings[diff]

    walls = set()
    for i in range(COLS): walls.update([(i, 0), (i, ROWS-1)])
    for i in range(ROWS): walls.update([(0, i), (COLS-1, i)])
    for x in range(4, COLS-4, 4):
        for y in range(4, ROWS-4, 4): walls.update([(x, y), (x+1, y)])

    player_pos, ai_pos = [1, 1], [COLS-2, ROWS-2]
    goal = get_random_goal(player_pos, walls)
    stamina, score, ai_tick = 100, 0, 0
    clock = pygame.time.Clock()

    while True:
        canvas.fill(BG_COLOR)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return

        # Logic
        keys = pygame.key.get_pressed()
        sprinting = keys[pygame.K_LSHIFT] and stamina > 5
        ai_tick += 1
        if ai_tick % 5 == 0:
            new_p = list(player_pos)
            if keys[pygame.K_UP]: new_p[1] -= 1
            elif keys[pygame.K_DOWN]: new_p[1] += 1
            elif keys[pygame.K_LEFT]: new_p[0] -= 1
            elif keys[pygame.K_RIGHT]: new_p[0] += 1
            if (new_p[0], new_p[1]) not in walls: player_pos = new_p

        stamina = max(0, stamina - 1.8) if sprinting else min(100, stamina + REGEN)
        ai_speed = AI_RATE // 2 if sprinting else AI_RATE
        if ai_tick % ai_speed == 0:
            path = a_star(tuple(ai_pos), tuple(player_pos), walls)
            if len(path) > 1: ai_pos = list(path[1])

        # Render onto CANVAS (not screen)
        pygame.draw.rect(canvas, GOAL_COLOR, (goal[0]*GRID_SIZE, goal[1]*GRID_SIZE, GRID_SIZE, GRID_SIZE), border_radius=4)
        for w in walls: pygame.draw.rect(canvas, WALL_COLOR, (w[0]*GRID_SIZE, w[1]*GRID_SIZE, GRID_SIZE, GRID_SIZE))
        
        # Spotlight Fog
        fog = pygame.Surface((BASE_WIDTH, BASE_HEIGHT)); fog.fill((0, 0, 0))
        pygame.draw.circle(fog, (255, 255, 255), (player_pos[0]*GRID_SIZE+12, player_pos[1]*GRID_SIZE+12), VISION)
        fog.set_colorkey((255, 255, 255))
        
        pygame.draw.circle(canvas, PLAYER_COLOR, (player_pos[0]*GRID_SIZE+12, player_pos[1]*GRID_SIZE+12), 10)
        pygame.draw.circle(canvas, AI_COLOR, (ai_pos[0]*GRID_SIZE+12, ai_pos[1]*GRID_SIZE+12), 10)
        canvas.blit(fog, (0, 0))

        # UI
        pygame.draw.rect(canvas, (40, 40, 40), (20, BASE_HEIGHT-30, 200, 10))
        pygame.draw.rect(canvas, (255, 255, 0), (20, BASE_HEIGHT-30, stamina * 2, 10))
        scr_txt = font_sm.render(f"SCORE: {score}  |  BEST: {high_score}", True, TEXT_COLOR)
        canvas.blit(scr_txt, (BASE_WIDTH - 280, 20))

        # --- FINAL SCALING STEP ---
        # Get current window size and stretch the canvas to fill it
        window_size = screen.get_size()
        scaled_view = pygame.transform.smoothscale(canvas, window_size)
        screen.blit(scaled_view, (0, 0))
        pygame.display.flip()

        if tuple(player_pos) == goal:
            score += 1; goal = get_random_goal(player_pos, walls); pygame.time.wait(100)
        if tuple(player_pos) == tuple(ai_pos):
            if score > high_score: high_score = score
            return # Back to menu

        clock.tick(FPS)

while True:
    difficulty = show_menu()
    play_game(difficulty)
