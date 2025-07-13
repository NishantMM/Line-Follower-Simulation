import pygame
import math
import random
import sys

pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Robot Simulation with Pause & Obstacle Avoidance")
clock = pygame.time.Clock()

# Colours
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ROBOT_COLOR = (0, 180, 0)
OBSTACLE_COLOR = (130, 130, 130)
TRANSLUCENT_COLOR = (100, 100, 255, 100)
SELECTED_COLOR = (255, 0, 0)
LINE_COLOR = (100, 100, 100)

# Fonts
FONT = pygame.font.SysFont(None, 24)
BIG_FONT = pygame.font.SysFont(None, 30)

# UI Buttons
buttons = {
    "Clear": pygame.Rect(20, 20, 80, 35),
    "Reset": pygame.Rect(120, 20, 80, 35),
    "Go": pygame.Rect(220, 20, 80, 35),
    "Pause": pygame.Rect(320, 20, 80, 35),
    "Exit": pygame.Rect(420, 20, 80, 35)  # Added Exit button
}

speed_values = [1, 2, 3, 4, 5]
selected_speed = 2
speed_dropdown = pygame.Rect(WIDTH - 120, 60, 60, 30)
dropdown_open = False

# Modes
MODE_TARGET = "Target Mode"
MODE_PATH = "Free Path Mode"
current_mode = None

# Robot
robot_pos = [50, HEIGHT - 50]
robot_angle = 0
robot_index = 0
robot_moving = False
robot_paused = False
dot_accumulator = 0
dot_interval = 10
target_index = 0

# Drawing
drawing = False
path_points = []

# Obstacles
obstacles = []
for _ in range(8):
    x = random.randint(100, WIDTH - 100)
    y = random.randint(150, HEIGHT - 100)
    obstacles.append((x, y, 25))  # (x, y, radius)

# Target Mode
translucent_objects = []
selected_targets = []
for _ in range(10):
    x = random.randint(80, WIDTH - 80)
    y = random.randint(120, HEIGHT - 80)
    translucent_objects.append({"pos": (x, y), "selected": False})


def draw_mode_selection():
    screen.fill(WHITE)
    title = BIG_FONT.render("Choose Mode", True, BLACK)
    screen.blit(title, (WIDTH // 2 - 80, HEIGHT // 2 - 100))

    target_btn = pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 - 30, 120, 50)
    path_btn = pygame.Rect(WIDTH // 2 + 10, HEIGHT // 2 - 30, 120, 50)

    pygame.draw.rect(screen, (200, 200, 200), target_btn)
    pygame.draw.rect(screen, (200, 200, 200), path_btn)
    pygame.draw.rect(screen, BLACK, target_btn, 2)
    pygame.draw.rect(screen, BLACK, path_btn, 2)

    screen.blit(FONT.render("Target Mode", True, BLACK), (target_btn.x + 10, target_btn.y + 15))
    screen.blit(FONT.render("Free Path", True, BLACK), (path_btn.x + 20, path_btn.y + 15))
    pygame.display.update()
    return target_btn, path_btn


def draw_robot(pos, angle):
    x, y = pos
    size = 15
    points = [
        (x + size, y),
        (x - size, y - size // 2),
        (x - size, y + size // 2)
    ]
    sin_a, cos_a = math.sin(angle), math.cos(angle)
    rotated = []
    for px, py in points:
        dx, dy = px - x, py - y
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        rotated.append((x + rx, y + ry))
    pygame.draw.polygon(screen, ROBOT_COLOR, rotated)


def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def draw_buttons():
    for name, rect in buttons.items():
        if robot_moving and not robot_paused and name != "Pause":
            pygame.draw.rect(screen, (180, 180, 180), rect)
        elif name == "Pause" and not robot_moving:
            pygame.draw.rect(screen, (180, 180, 180), rect)
        else:
            pygame.draw.rect(screen, (220, 220, 220), rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        label = BIG_FONT.render(name, True, BLACK)
        screen.blit(label, (rect.x + 10, rect.y + 5))


def draw_speed_dropdown():
    pygame.draw.rect(screen, (230, 230, 230), speed_dropdown)
    pygame.draw.rect(screen, BLACK, speed_dropdown, 2)
    label = FONT.render(f"Speed: {selected_speed}", True, BLACK)
    screen.blit(label, (speed_dropdown.x + 5, speed_dropdown.y + 5))

    if dropdown_open:
        for i, val in enumerate(speed_values):
            opt_rect = pygame.Rect(speed_dropdown.x, speed_dropdown.y + (i + 1) * 30, 60, 30)
            pygame.draw.rect(screen, (240, 240, 240), opt_rect)
            pygame.draw.rect(screen, BLACK, opt_rect, 1)
            opt_label = FONT.render(str(val), True, BLACK)
            screen.blit(opt_label, (opt_rect.x + 20, opt_rect.y + 5))


def draw_obstacles():
    for ox, oy, r in obstacles:
        pygame.draw.circle(screen, OBSTACLE_COLOR, (ox, oy), r)
    for (tx, ty) in selected_targets:  # treat targets as obstacles
        pygame.draw.circle(screen, SELECTED_COLOR, (tx, ty), 20, 2)


def avoid_obstacles(pos, angle):
    ahead_x = pos[0] + math.cos(angle) * 25
    ahead_y = pos[1] + math.sin(angle) * 25
    avoid = False
    all_obstacles = obstacles.copy() + [(tx, ty, 20) for tx, ty in selected_targets]
    for ox, oy, r in all_obstacles:
        if distance((ahead_x, ahead_y), (ox, oy)) < r + 10:
            avoid = True
            break
    if avoid:
        left = angle + 1.2
        right = angle - 1.2
        dist_left = min([distance((pos[0] + math.cos(left) * 25, pos[1] + math.sin(left) * 25), (ox, oy)) for (ox, oy, r) in all_obstacles])
        dist_right = min([distance((pos[0] + math.cos(right) * 25, pos[1] + math.sin(right) * 25), (ox, oy)) for (ox, oy, r) in all_obstacles])
        return left if dist_left > dist_right else right
    return angle

# Mode selection
def mode_selection_loop():
    target_btn, path_btn = draw_mode_selection()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if target_btn.collidepoint(event.pos):
                    return MODE_TARGET
                elif path_btn.collidepoint(event.pos):
                    return MODE_PATH

# Start screen - mode selection
current_mode = mode_selection_loop()

# Main
running = True
while running:
    screen.fill(WHITE)
    mx, my = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and not robot_moving:
                if current_mode == MODE_TARGET and selected_targets:
                    robot_moving = True
                    robot_paused = False
                    target_index = 0
                elif current_mode == MODE_PATH and path_points:
                    robot_moving = True
                    robot_paused = False
                    robot_index = 0
                    dot_accumulator = 0

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if speed_dropdown.collidepoint(event.pos):
                dropdown_open = not dropdown_open
            elif dropdown_open:
                for i, val in enumerate(speed_values):
                    opt_rect = pygame.Rect(speed_dropdown.x, speed_dropdown.y + (i + 1) * 30, 60, 30)
                    if opt_rect.collidepoint(event.pos):
                        selected_speed = val
                        dropdown_open = False
                        break
            else:
                for name, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if name == "Pause" and robot_moving:
                            robot_paused = not robot_paused
                        elif not robot_moving or robot_paused:
                            if name == "Clear":
                                selected_targets.clear()
                                path_points.clear()
                                for obj in translucent_objects:
                                    obj["selected"] = False
                                robot_pos = [50, HEIGHT - 50]
                                robot_moving = False
                            elif name == "Reset":
                                robot_pos = [50, HEIGHT - 50]
                                robot_index = 0
                                target_index = 0
                                robot_moving = False
                                dot_accumulator = 0
                            elif name == "Go":
                                if current_mode == MODE_TARGET and selected_targets:
                                    robot_moving = True
                                    robot_paused = False
                                    target_index = 0
                                elif current_mode == MODE_PATH and path_points:
                                    robot_moving = True
                                    robot_paused = False
                                    robot_index = 0
                                    dot_accumulator = 0
                        break
                else:
                    if current_mode == MODE_TARGET:
                        for obj in translucent_objects:
                            if distance((mx, my), obj["pos"]) < 20 and not obj["selected"]:
                                obj["selected"] = True
                                selected_targets.append(obj["pos"])
                                break
                    elif current_mode == MODE_PATH:
                        drawing = True
                        path_points.clear()

        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False

        elif event.type == pygame.MOUSEMOTION and drawing and current_mode == MODE_PATH:
            path_points.append((mx, my))

    draw_buttons()
    draw_speed_dropdown()
    draw_obstacles()
    robot_speed = selected_speed

    for obj in translucent_objects:
        x, y = obj["pos"]
        surface = pygame.Surface((40, 40), pygame.SRCALPHA)
        color = SELECTED_COLOR if obj["selected"] else TRANSLUCENT_COLOR
        pygame.draw.circle(surface, color, (20, 20), 20)
        screen.blit(surface, (x - 20, y - 20))
        if obj["selected"]:
            label = FONT.render(f"{selected_targets.index(obj['pos'])+1}", True, WHITE)
            screen.blit(label, (x - 6, y - 8))

    if current_mode == MODE_PATH and len(path_points) > 1:
        pygame.draw.lines(screen, LINE_COLOR, False, path_points, 3)

    if robot_moving and not robot_paused:
        if current_mode == MODE_TARGET and target_index < len(selected_targets):
            target = selected_targets[target_index]
            dx, dy = target[0] - robot_pos[0], target[1] - robot_pos[1]
            dist = math.hypot(dx, dy)
            if dist < 5:
                target_index += 1
            else:
                angle = math.atan2(dy, dx)
                robot_angle = avoid_obstacles(robot_pos, angle)
                robot_pos[0] += robot_speed * math.cos(robot_angle)
                robot_pos[1] += robot_speed * math.sin(robot_angle)
                draw_robot(robot_pos, robot_angle)
        elif current_mode == MODE_PATH and robot_index < len(path_points):
            if dot_accumulator <= 0:
                pos = path_points[robot_index]
                if robot_index + 1 < len(path_points):
                    next_pos = path_points[robot_index + 1]
                    angle = math.atan2(next_pos[1] - pos[1], next_pos[0] - pos[0])
                    robot_angle = avoid_obstacles(pos, angle)
                draw_robot(pos, robot_angle)
                pygame.draw.circle(screen, BLACK, pos, 2)
                dot_accumulator = dot_interval
            dot_accumulator -= robot_speed
            robot_index += 1
        else:
            draw_robot(robot_pos, robot_angle)
    else:
        draw_robot(robot_pos, robot_angle)

    pygame.display.update()
    clock.tick(60)

pygame.quit()
sys.exit()
