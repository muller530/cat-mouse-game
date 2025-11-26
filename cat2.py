import pygame
import sys
import random
import math
import os  # 新增：用于检测字体文件路径

# --- 1. 游戏配置参数 (保持不变) ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
BLOCK_SIZE = 30      
MAZE_COLS = SCREEN_WIDTH // BLOCK_SIZE
MAZE_ROWS = SCREEN_HEIGHT // BLOCK_SIZE
FPS = 60

# 狗狗配置
DOG_LIFETIME = 180   # 3秒
DOG_COUNT = 20       

# 颜色定义
BG_COLOR = (44, 62, 80)        
WALL_COLOR = (236, 240, 241)   
GOAL_COLOR = (46, 204, 113)    
SHIELD_COLOR = (0, 255, 255)   
OVERLAY_COLOR = (0, 0, 0, 180)

# --- 初始化 Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("猫鼠迷宫：终极卡通版 (乐乐专属学习放松小游戏)")
clock = pygame.time.Clock()

# --- 2. 字体与图像资源加载 (仅修改此处以修复乱码) ---

def get_chinese_font(size):
    """
    【核心修复】优先使用文件路径加载中文字体，解决SysFont找不到字体导致的乱码
    """
    # 1. Windows 常见中文字体路径 (优先尝试)
    win_paths = [
        "C:\\Windows\\Fonts\\msyh.ttf",    # 微软雅黑 (标准)
        "C:\\Windows\\Fonts\\msyhbd.ttf",  # 微软雅黑 (粗体)
        "C:\\Windows\\Fonts\\simhei.ttf",  # 黑体
        "C:\\Windows\\Fonts\\simkai.ttf",  # 楷体
    ]
    
    # 2. Mac 常见中文字体路径
    mac_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Songti.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc"
    ]
    
    # 尝试加载物理文件
    for path in win_paths + mac_paths:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except:
                continue

    # 3. 如果文件都找不到，回退到系统名称查找 (Linux等)
    sys_names = ["microsoftyahei", "simhei", "pingfangsc", "wqy-microhei"]
    available = pygame.font.get_fonts()
    for name in sys_names:
        if name in available:
            return pygame.font.SysFont(name, size)
            
    # 4. 实在不行，用默认字体 (虽然可能不显示中文，但不会崩)
    return pygame.font.SysFont("arial", size)

def get_emoji_font(size):
    """尝试加载 Emoji 字体用于显示逼真形象"""
    # Windows Emoji
    if os.path.exists("C:\\Windows\\Fonts\\seguiemj.ttf"):
        try: return pygame.font.Font("C:\\Windows\\Fonts\\seguiemj.ttf", size)
        except: pass
    # Mac Emoji
    if os.path.exists("/System/Library/Fonts/Apple Color Emoji.ttc"):
        try: return pygame.font.Font("/System/Library/Fonts/Apple Color Emoji.ttc", size)
        except: pass
    # Fallback
    return get_chinese_font(size)

# 加载字体
font_ui = get_chinese_font(24)      # 用于下方说明文字
font_title = get_chinese_font(60)   # 用于大标题
font_emoji = get_emoji_font(int(BLOCK_SIZE * 0.9)) # 用于游戏内角色

# 预渲染 Emoji 为 Surface
def render_emoji(txt, fallback_color):
    try:
        surf = font_emoji.render(txt, True, (255, 255, 255))
        if surf.get_width() > 0:
            return surf
    except:
        pass
    return None

# 缓存角色图像 (保持上一版设定)
SPRITES = {
    "mouse": render_emoji("🐭", (100, 100, 100)),
    "cat":   render_emoji("🐱", (200, 100, 0)),
    "dog":   render_emoji("🐶", (150, 100, 50)),
    "coin":  render_emoji("🪙", (255, 215, 0)) 
}

# --- 3. 辅助绘图 (Fallback) ---
def draw_vector_character(surface, role, x, y, size):
    cx, cy = x + size // 2, y + size // 2
    r = size // 2 - 2
    
    if role == "mouse":
        pygame.draw.circle(surface, (150, 150, 150), (cx, cy), r)
        pygame.draw.circle(surface, (255, 180, 200), (cx-r+4, cy-r+4), r//2)
        pygame.draw.circle(surface, (255, 180, 200), (cx+r-4, cy-r+4), r//2)
        pygame.draw.circle(surface, (0,0,0), (cx, cy+2), 3)
    elif role == "cat":
        pygame.draw.circle(surface, (255, 165, 0), (cx, cy), r)
        pygame.draw.polygon(surface, (255, 165, 0), [(cx-8, cy-10), (cx, cy-r-2), (cx+8, cy-10)])
        pygame.draw.circle(surface, (255,255,255), (cx-5, cy-2), 4)
        pygame.draw.circle(surface, (255,255,255), (cx+5, cy-2), 4)
        pygame.draw.circle(surface, (0,0,0), (cx-5, cy-2), 2)
        pygame.draw.circle(surface, (0,0,0), (cx+5, cy-2), 2)
    elif role == "dog":
        pygame.draw.circle(surface, (139, 69, 19), (cx, cy), r)
        pygame.draw.ellipse(surface, (80, 40, 10), (cx-r-2, cy-4, 12, 16))
        pygame.draw.ellipse(surface, (80, 40, 10), (cx+r-10, cy-4, 12, 16))
        pygame.draw.circle(surface, (0,0,0), (cx-4, cy-2), 2)
        pygame.draw.circle(surface, (0,0,0), (cx+4, cy-2), 2)

def draw_sprite(surface, role, x, y, size, shield_active=False):
    # 护盾光效
    if shield_active:
        glow = 4 + int(math.sin(pygame.time.get_ticks() * 0.15) * 4)
        center = (int(x + size/2), int(y + size/2))
        pygame.draw.circle(surface, SHIELD_COLOR, center, size//2 + 4, 2)
        
    img = SPRITES.get(role)
    if img:
        offset_x = (size - img.get_width()) // 2
        offset_y = (size - img.get_height()) // 2
        surface.blit(img, (x + offset_x, y + offset_y))
    else:
        draw_vector_character(surface, role, x, y, size)

# --- 4. 迷宫生成: Growing Tree (保持分叉和诱导特性) ---
class Maze:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.grid = [[1 for _ in range(cols)] for _ in range(rows)]
        self.generate_growing_tree()
        
        self.grid[rows-1][cols-1] = 0
        self.grid[rows-1][cols-2] = 0
        self.grid[rows-2][cols-1] = 0
        
        self.empty_cells = []
        for r in range(rows):
            for c in range(cols):
                if self.grid[r][c] == 0:
                    self.empty_cells.append((c, r))

    def generate_growing_tree(self):
        start_x, start_y = 0, 0
        self.grid[start_y][start_x] = 0
        active_cells = [(start_x, start_y)]
        
        while active_cells:
            # 50%概率选最新，50%概率选随机
            if random.random() < 0.5:
                index = len(active_cells) - 1
            else:
                index = random.randint(0, len(active_cells) - 1)
            
            cx, cy = active_cells[index]
            neighbors = []
            for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] == 1:
                    neighbors.append((nx, ny, dx, dy))
            
            if neighbors:
                nx, ny, dx, dy = random.choice(neighbors)
                self.grid[cy + dy//2][cx + dx//2] = 0 
                self.grid[ny][nx] = 0                 
                active_cells.append((nx, ny))
            else:
                active_cells.pop(index)

    def draw(self, surface):
        surface.fill(BG_COLOR)
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 1:
                    rect = (c*BLOCK_SIZE, r*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
                    pygame.draw.rect(surface, (189, 195, 199), rect) # 侧面
                    pygame.draw.rect(surface, WALL_COLOR, (rect[0], rect[1], rect[2], rect[3]-4)) # 顶面
        pygame.draw.rect(surface, WALL_COLOR, (0,0,SCREEN_WIDTH, SCREEN_HEIGHT), 5)

# --- 5. 玩家与物体 (保持物理特性) ---
class Player:
    def __init__(self, role, controls):
        self.role = role
        self.controls = controls
        self.grid_x, self.grid_y = 0, 0
        self.draw_x, self.draw_y = 0, 0
        self.is_dead = False
        self.velocity_y = 0
        self.shield_timer = 0
        self.move_cd = 0

    def reset(self):
        self.grid_x, self.grid_y = 0, 0
        self.draw_x, self.draw_y = 0, 0
        self.is_dead = False
        self.velocity_y = 0
        self.shield_timer = 0

    def trigger_death(self):
        if not self.is_dead:
            self.is_dead = True
            self.velocity_y = -15 

    def update(self, maze, keys):
        if self.is_dead:
            self.draw_y += self.velocity_y
            self.velocity_y += 0.8
            if self.draw_y > SCREEN_HEIGHT + 100: self.reset()
            return

        if self.shield_timer > 0: self.shield_timer -= 1
        if self.move_cd > 0: self.move_cd -= 1; return

        dx, dy = 0, 0
        if keys[self.controls['up']]: dy = -1
        elif keys[self.controls['down']]: dy = 1
        elif keys[self.controls['left']]: dx = -1
        elif keys[self.controls['right']]: dx = 1

        if dx or dy:
            nx, ny = self.grid_x + dx, self.grid_y + dy
            if 0 <= nx < maze.cols and 0 <= ny < maze.rows:
                if maze.grid[ny][nx] == 0:
                    self.grid_x, self.grid_y = nx, ny
                    self.move_cd = 6 

    def update_pos(self):
        if not self.is_dead:
            tx, ty = self.grid_x * BLOCK_SIZE, self.grid_y * BLOCK_SIZE
            self.draw_x += (tx - self.draw_x) * 0.4
            self.draw_y += (ty - self.draw_y) * 0.4

class CoinManager:
    def __init__(self): self.coins = []
    def spawn(self, maze):
        dead_ends = []
        for r in range(1, maze.rows-1):
            for c in range(1, maze.cols-1):
                if maze.grid[r][c] == 0:
                    walls = 0
                    if maze.grid[r+1][c]==1: walls+=1
                    if maze.grid[r-1][c]==1: walls+=1
                    if maze.grid[r][c+1]==1: walls+=1
                    if maze.grid[r][c-1]==1: walls+=1
                    if walls >= 3:
                        dead_ends.append((c,r))
        if len(dead_ends) > 10:
            self.coins = random.sample(dead_ends, 10)
        else:
            self.coins = dead_ends

    def draw(self, surf):
        for cx, cy in self.coins:
            x, y = cx*BLOCK_SIZE, cy*BLOCK_SIZE
            if SPRITES["coin"]:
                 draw_sprite(surf, "coin", x, y, BLOCK_SIZE)
            else:
                center = (x + BLOCK_SIZE//2, y + BLOCK_SIZE//2)
                coin_size = int(BLOCK_SIZE * 0.8)
                w = coin_size * math.fabs(math.sin(pygame.time.get_ticks() * 0.005))
                pygame.draw.ellipse(surf, (255, 215, 0), (center[0]-w/2, center[1]-coin_size/2, w, coin_size))
                pygame.draw.ellipse(surf, (255, 255, 200), (center[0]-w/2+2, center[1]-coin_size/2+2, w-4, coin_size-4), 1)

class DogManager:
    def __init__(self): self.dogs = []
    def init(self, maze):
        self.dogs = []
        for _ in range(DOG_COUNT): self.spawn(maze, True)
    
    def spawn(self, maze, start=False):
        for _ in range(50):
            rx, ry = random.randint(0, maze.cols-1), random.randint(0, maze.rows-1)
            dist = (rx + ry) / (maze.cols + maze.rows)
            if random.random() < dist + 0.1:
                if maze.grid[ry][rx] == 0:
                    if (rx<3 and ry<3) or (rx>maze.cols-3 and ry>maze.rows-3): continue
                    life = random.randint(30, DOG_LIFETIME) if start else DOG_LIFETIME
                    self.dogs.append({'x':rx, 'y':ry, 'life':life})
                    return
    def update(self, maze):
        for d in self.dogs:
            d['life'] -= 1
            if d['life'] <= 0:
                self.dogs.remove(d)
                self.spawn(maze)
    def draw(self, surf):
        for d in self.dogs:
            if d['life'] < 60 and (d['life']//5)%2==0: continue
            draw_sprite(surf, "dog", d['x']*BLOCK_SIZE, d['y']*BLOCK_SIZE, BLOCK_SIZE)
            ratio = d['life'] / DOG_LIFETIME
            rect = (d['x']*BLOCK_SIZE, d['y']*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.arc(surf, (255, 50, 50), rect, 0, 6.28*ratio, 2)

# --- 主逻辑 ---
def main():
    maze = Maze(MAZE_COLS, MAZE_ROWS)
    mouse = Player("mouse", {'up':pygame.K_w, 'down':pygame.K_s, 'left':pygame.K_a, 'right':pygame.K_d})
    cat = Player("cat", {'up':pygame.K_UP, 'down':pygame.K_DOWN, 'left':pygame.K_LEFT, 'right':pygame.K_RIGHT})
    dogs = DogManager()
    coins = CoinManager()
    
    running, active, winner = True, False, None

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if not active and e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                maze = Maze(MAZE_COLS, MAZE_ROWS)
                mouse.reset(); cat.reset()
                dogs.init(maze); coins.spawn(maze)
                winner = None; active = True

        if active and not winner:
            keys = pygame.key.get_pressed()
            mouse.update(maze, keys); cat.update(maze, keys)
            dogs.update(maze)
            
            for p in [mouse, cat]:
                if not p.is_dead:
                    if (p.grid_x, p.grid_y) in coins.coins:
                        coins.coins.remove((p.grid_x, p.grid_y))
                        p.shield_timer = 3 * FPS
                    if p.shield_timer == 0:
                        for d in dogs.dogs:
                            if d['x']==p.grid_x and d['y']==p.grid_y:
                                p.trigger_death()
            
            if mouse.grid_x==MAZE_COLS-1 and mouse.grid_y==MAZE_ROWS-1: winner = "老鼠 (Mouse)"
            elif cat.grid_x==MAZE_COLS-1 and cat.grid_y==MAZE_ROWS-1: winner = "猫 (Cat)"

        mouse.update_pos(); cat.update_pos()

        # 绘图
        maze.draw(screen)
        
        goal_rect = ((MAZE_COLS-1)*BLOCK_SIZE, (MAZE_ROWS-1)*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
        pygame.draw.rect(screen, GOAL_COLOR, goal_rect)
        pygame.draw.rect(screen, (30, 150, 80), (goal_rect[0], goal_rect[1]+BLOCK_SIZE-4, BLOCK_SIZE, 4))

        coins.draw(screen)
        dogs.draw(screen)
        draw_sprite(screen, "mouse", mouse.draw_x, mouse.draw_y, BLOCK_SIZE, mouse.shield_timer>0)
        draw_sprite(screen, "cat", cat.draw_x, cat.draw_y, BLOCK_SIZE, cat.shield_timer>0)

        # UI Overlay (中文字体修复生效区域)
        if not active or winner:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill(OVERLAY_COLOR)
            screen.blit(overlay, (0,0))
            cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
            
            if winner:
                c = (52, 152, 219) if "老鼠" in winner else (231, 76, 60)
                t = font_title.render(f"🏆 {winner} 获胜!", True, c)
                if t: screen.blit(t, t.get_rect(center=(cx, cy-80)))
            
            if not active and not winner:
                t = font_title.render("终极卡通迷宫", True, (255,255,255))
                if t: screen.blit(t, t.get_rect(center=(cx, cy-120)))
                
                # 大图标展示
                draw_sprite(screen, "mouse", cx-150, cy-50, 80)
                draw_sprite(screen, "cat", cx+70, cy-50, 80)
                
                # 说明文字
                info1 = font_ui.render("老鼠: W A S D", True, (200,200,255))
                info2 = font_ui.render("猫咪: ↑ ↓ ← →", True, (255,200,200))
                info3 = font_ui.render("玩法: 躲避小狗 🐶，拾取金币 🪙", True, (255,215,0))

                if info1: screen.blit(info1, (cx-180, cy+40))
                if info2: screen.blit(info2, (cx+60, cy+40))
                if info3: screen.blit(info3, info3.get_rect(center=(cx, cy+90)))

            s = font_ui.render("按 [空格 SPACE] 开始", True, (255,255,255))
            if s and pygame.time.get_ticks() % 1000 < 600:
                screen.blit(s, s.get_rect(center=(cx, cy+150)))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit(); sys.exit()

if __name__ == "__main__":
    main()