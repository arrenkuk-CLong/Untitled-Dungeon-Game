#load & draw assets (dungeon and animations)
#but mostly just loading

import pygame, os
from PIL import Image
from scripts import Dungeongen
#from scripts import config
from scripts.config import ENEMY_SPRITE_MAP, ITEM_SPRITE_MAP, PLAYER_SPRITE_MAP, TILE_SIZE, WIDTH, HEIGHT, MAP_OFF_X, MAP_OFF_Y
from scripts.entities import Enemy, EFFECTS
from scripts.Dungeongen import TILE_MISC

Color ={
    'Black': pygame.Color(0, 0, 0),
    'Green': pygame.Color(0, 128, 0),
    'DGrey': pygame.Color(59, 59, 59),
    'DDGrey': pygame.Color(25, 25, 25),
    'Grey': pygame.Color(70, 70, 70),
    'White': pygame.Color(255, 255, 255),
    'Red': pygame.Color (120, 0, 0),
    'LRed': pygame.Color(200, 0, 0),
    'Blue': pygame.Color(50, 50, 200),
    'Brown': pygame.Color(110, 70, 30),
    'Brown2': pygame.Color(101, 67, 33),
    'Brown3': pygame.Color(61, 43, 31),
    'Gold': pygame.Color(200, 170, 60),
    'DarkPurp': pygame.Color(46, 34, 47)
}

#New fonts
Font_Path = 'assets/Fonts/Minecraft.ttf'
Font = pygame.font.Font(Font_Path, 32)
SmallFont = pygame.font.Font(Font_Path, 16)
SmallestFont = pygame.font.Font(Font_Path, 8)



#Build path to assets, assets can load wherever they are launched from
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
ASSETS = os.path.join(ROOT, 'assets')
def asset(*parts):
    return os.path.join(ASSETS, *parts)
asset('Characters','Backgrounds', 'Anims')

#======================================================================
#Exploration mode Sprites
#----------------------------------------------------------------------
def explore_sprites(name, scale = TILE_SIZE):
    if isinstance(scale, int):
        scale = (scale, scale)

    sprite_name = PLAYER_SPRITE_MAP.get(name) or ENEMY_SPRITE_MAP.get(name)

    if sprite_name is None:
        return None
    if not sprite_name.lower().endswith('.png'):
        sprite_name += '.png'

    cache_key = (name, scale)
    if cache_key not in explore_sprites.cache:
        sprite_path = asset('Characters',  sprite_name)
        sprite = pygame.image.load(sprite_path).convert_alpha()
        explore_sprites.cache[cache_key] = pygame.transform.scale(sprite, scale)
    return explore_sprites.cache[cache_key]

explore_sprites.cache = {}

#=====================================================================
# LOAD ASSETS
#----------------------------------------------------------------------
# load Menu, Battle background
# character Selection cards, battle sprites
# Status Effect Icons
# attack animation, and dungeon.

#Asset loader - purely to make the asset loading process easier
def load_img(png, scale = None):
    img = pygame.image.load(png)
    if scale: # if I apply (WIDTH, HEIGHT)
        img = pygame.transform.scale(img, scale)
    return img

#BGs
BGmenu = load_img(asset('Backgrounds', 'BGselect.png'), (WIDTH, HEIGHT))
BGBattle = load_img(asset('Backgrounds', 'BGBattle.png'), (WIDTH, HEIGHT))

#HUD
Navbar = load_img(asset('hud', 'NavBar.png'), (1080, 55))

#FOV Fog:
Fog = load_img(asset('hud', 'Fogfov.png'), (1080, 720)).convert_alpha()


#Load Class files
character_files = [asset('Characters', 'Sword.png'), asset('Characters', 'Wizard.png'), asset('Characters', 'Archer.png')]
Char_cards = {} 
for file in character_files:
    name = os.path.splitext(os.path.basename(file))[0]
    Char_cards[name] = load_img(file, (260, 260)).convert_alpha()   #[-1] grabs the name that we want 
    print(f"Loaded: {name}")            #print check in terminal 

#Class files (Battle Stage)
Battle_files = {
    "Sword": load_img(asset('Characters', 'SwordBattle.png'), (300, 400)),
    "Wizard": load_img(asset('Characters', 'WizardBattle.png'), (300, 400)),
    "Archer": load_img(asset('Characters', 'ArcherBattle.png'), (300, 400)),
    }
Enemy_img = load_img(asset('Characters', 'Eye.png'), (250, 350))

#The plate every buff badge is drawn on
Icon_base = load_img(asset('Icons', 'Icon Base.png'), (32, 32)).convert_alpha()

#Attack Animation
ATTACK_ANIMATION_FILES = {
    'Sword': [asset('Anims', 'SwordAnim.gif'), asset('Anims', 'GroundSlam.gif'), None, None],
    'Wizard': None,
    'Archer': None,
    'Eye': [asset('Anims', 'EyeAnim.gif'), None, None, asset('Anims', 'kamui.gif')],
}

#Idle Animation
IDLE_ANIMATION_FILES = {
    'Sword': asset('Characters', 'Sword_Idle.gif'),
    'Wizard': asset('Characters', 'Wizard_Idle.gif'),
    'Archer': asset('Characters', 'Archer_Idle.gif'),
    'Eye': asset('Characters', 'Eye_Idle.gif')
}

#Load Effects icons.
Effect_icons = {}
for name in EFFECTS:
    path = asset('Icons', 'effects', name + '.png')
    try:
        Effect_icons[name] = load_img(path, (32, 32)).convert_alpha()
    except FileNotFoundError:
        Effect_icons[name] = None
        print ('no icon for effect:', name)

#Load Item icons.
def item_sprites(name, scale = TILE_SIZE):
    if isinstance(scale, int):
        scale = (scale, scale)

    sprite_name = ITEM_SPRITE_MAP.get(name)

    if sprite_name is None:
        return None
    if not sprite_name.lower().endswith('.png'):
        sprite_name += '.png'

    cache_key = (name, scale)
    if cache_key not in item_sprites.cache:
        sprite_path = asset('Icons', 'items',  sprite_name)
        try:
            sprite = pygame.image.load(sprite_path).convert_alpha()
            item_sprites.cache[cache_key] = pygame.transform.scale(sprite, scale)
        except FileNotFoundError:
            print('no floor sprite for item:', name)
            item_sprites.cache[cache_key] = None

    return item_sprites.cache[cache_key]

item_sprites.cache = {}

#Inventory panel icons. The filename comes from ITEM_SPRITE_MAP, NOT from the
#item name - "Health Potion" is the display name, "health_potion.png" is the file.
Item_icons = {}
for name, filename in ITEM_SPRITE_MAP.items():
    path = asset('Icons', 'items', filename)
    try:
        Item_icons[name] = load_img(path, (32, 32)).convert_alpha()
    except FileNotFoundError:
        Item_icons[name] = None
        print('no icon for item:', name)


#=====================================================================
# Animation
#----------------------------------------------------------------------
# Char_Animation - idle and and maybe attack animations
# 
# AtkAnimation - updates the gif(sprite) and moves it from start pos to
#                end pos
# load the gif (all frames) and create the animation on screen (instance)

class Char_Animation(pygame.sprite.Sprite):
    def __init__(self, gif_path, ms_per_frame=240):
        super().__init__()
        self.frames = load_gif(gif_path) 
        if not self.frames:
            raise ValueError(f'No frames found in {gif_path}')
        self.current_frame = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.active = False
        self.frame_timer = 0
        self.ms_per_frame = ms_per_frame

    def start(self, pos):
        self.active = True
        self.current_frame = 0
        self.frame_timer = pygame.time.get_ticks()
        self.pos = pygame.Vector2(pos)
        self.rect = self.image.get_rect(center=pos)

    def update(self):
        if not self.active:
            return None

        now = pygame.time.get_ticks()
        if now - self.frame_timer >= self.ms_per_frame:
            self.frame_timer = now
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                self.current_frame = 0
            #draw
            self.image = self.frames[self.current_frame]
        return 'RUNNING'


def create_idle_anim(character_name):
    animation_paths = IDLE_ANIMATION_FILES.get(character_name)
    if not animation_paths: #Attack anim?
         return None
     
    if isinstance(animation_paths, str): #if string
        gif_path = animation_paths
    
    return Char_Animation(gif_path)

        
class AtkAnimation(pygame.sprite.Sprite):
    def __init__(self, gif_path, ms_per_frame=80):
        super().__init__()
        self.frames = load_gif(gif_path)
        if not self.frames:
            raise ValueError(f'No frames found in {gif_path}')
        self.current_frame = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.active = False
        self.frame_timer = 0
        self.ms_per_frame = ms_per_frame

    def start(self, start_pos, end_pos):
        self.active = True
        self.current_frame = 0
        self.frame_timer = pygame.time.get_ticks()
        self.start_pos = pygame.Vector2(start_pos)  
        self.end_pos = pygame.Vector2(end_pos)
        self.rect = self.image.get_rect(center=start_pos)

    def update(self):
        if not self.active:
            return None

        now = pygame.time.get_ticks()
        if now - self.frame_timer >= self.ms_per_frame:
            self.frame_timer = now
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                self.active = False
                self.current_frame = 0
                self.image = self.frames[0]
                return 'FINISHED'
            self.image = self.frames[self.current_frame]

        progress = (self.current_frame + 1) / len(self.frames)
        position = self.start_pos.lerp(self.end_pos, progress) #% value of start & End pt.
        self.rect = self.image.get_rect(center=position)
        return 'RUNNING'

def load_gif(file):
    gif = Image.open(file)
    frames = [] # of frames
    try:
        while True:
            rgba_frame = gif.convert('RGBA')
            data = rgba_frame.tobytes()
            size = rgba_frame.size

            pygame_surface = pygame.image.fromstring(data, size, 'RGBA')
            frames.append(pygame_surface)

            gif.seek(len(frames))
    except EOFError:
        pass
    finally:
        gif.close()
    return frames

def create_attack_animation(character_name, move_index=0): 
    animation_paths = ATTACK_ANIMATION_FILES.get(character_name)
    if not animation_paths:
        return None

    if isinstance(animation_paths, str):
        gif_path = animation_paths
    elif move_index < len(animation_paths):
        gif_path = animation_paths[move_index]
    else:
        gif_path = None
    if gif_path is None:
        return None
    return AtkAnimation(gif_path)



#=====================================================================
# Dungeon
#----------------------------------------------------------------------
# tile function, fov
# camera offset, draw_dungeon (main)s


#Dungeon Draw flow (current) generate_dungeon(Dungeongen) --> draw_dungeon (called main.py) 
# --> Tile Assets  --> draw_dungeon (draw_load.py)
TILE_ASSETS = {
    name: load_img(asset('Map', name + '.png'), (TILE_SIZE, TILE_SIZE)).convert_alpha()
    for name in ('Floor', 'Wall_Front', 'Wall_Other', 'Wall_Side', 'Wall_Sidetwo', 'Wall_Bothsides','Door', 'Enter', 'Stairs')
}
TILE_NAMES = {
    Dungeongen.FLOOR: 'Floor',
    Dungeongen.DOOR: 'Door',
    Dungeongen.ENTER: 'Enter',
    Dungeongen.EXIT: 'Stairs',
} #First Change to dungeon 
MISC_IMAGES = {name: load_img(asset('Map', name + '.png')).convert_alpha() for name in TILE_MISC}

#Shadows: Character, items, enemies:
def sprite_shadow(width, height, alpha = 100):
    shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0 ,0, alpha), shadow_surf.get_rect())
    return shadow_surf


#Drawing tiles
def tile_rect(x, y, tile_px = TILE_SIZE, offset_x = MAP_OFF_X, offset_y = MAP_OFF_Y):
    return pygame.Rect(offset_x + x * tile_px, offset_y + y * tile_px,
                       tile_px, tile_px)

#Shades: if light level is 0.8, draw a bright shade, if light level is low (like 0.2), draw a dark shade
#Player FOV, tile lighting
def lighting(dungeon, player_tile, visible, radius = 10):
    light_levels = {}
    px, py = player_tile

    for (x, y) in visible:
        dx = x - px
        dy = y - py    
        distance = (dx * dx + dy * dy) ** 0.5 #Euclidean distance

        if distance <= radius:
            brightness = 1.0 -(distance / radius) #Square the formula to fade faster
            light_levels[(x, y)] = max(0.0, min(1.0, brightness))

    return light_levels

LIGHT_STEPS = []
for i in range(16):
    s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    s.fill((46, 34, 47, int(255 * (1 - i / 15))))   #i=0 pitch black, i=15 clear
    LIGHT_STEPS.append(s)


#Bresenham's line algorithm
def line_of_sight(dungeon, x0, y0, x1, y1): #player (0) and Map tiles (1)
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1 
    sy = 1 if y0 < y1 else -1 
    error = dx - dy
    cx, cy = x0, y0
    
    while (cx, cy) != (x1, y1):
        e2 = 2 * error
        if e2 > -dy:
            error -= dy; cx += sx
        if e2 < dx:
            error += dx ; cy += sy
        if (cx, cy) == (x1, y1):
            return True                     #Hit wall
        if dungeon.tiles[cx][cy] == Dungeongen.WALL: #1
            return False                    #Cant go past wall
        
    return True

#Player FOV, draw tiles
def fov_tiles(dungeon, player_tile, radius = 10):
    visible = set() #Store all visible tiles per Fov
    px, py = player_tile
    radius_squared = radius * radius

    for x in range(px - radius, px + radius + 1): #Left & Right
        for y in range (py - radius, py + radius + 1): #Top & Bot
            if not dungeon.in_bounds(x, y): #past the map
                continue

            #Euclidean distance
            dx = x - px
            dy = y - py
            if (dx * dx) + (dy * dy) <= radius_squared:
                if line_of_sight(dungeon, px, py, x, y):
                    visible.add((x, y))

    return (visible)


#Camera track player & offset to center of screen - disabled.
def camera_offset(player_tile, tile_px):
    px, py = player_tile

    cam_x = WIDTH // 2 - (px * tile_px + tile_px // 2)
    cam_y = HEIGHT // 2 - (py * tile_px + tile_px // 2)
    return cam_x, cam_y


def draw_dungeon(screen, game, dungeon, tile_px):

    visible = fov_tiles(dungeon, game.player_tile)
    offset_x, offset_y = camera_offset(game.player_tile, tile_px)

    for x, y in visible:
        rect = pygame.Rect(             
            x * tile_px + offset_x,     
            y * tile_px + offset_y,
            tile_px,
            tile_px
        )
        #pygame.draw.rect(screen, TILE_COLORS[dungeon.tiles[x][y]], rect) #disable for now
        tile = dungeon.tiles[x][y]
        if tile == Dungeongen.WALL:
            name = dungeon.wall_sprite(x, y)      #Wall_Front or Wall_Other
        else:
            name = TILE_NAMES[tile]
        screen.blit(TILE_ASSETS[name], rect)

        decoration = dungeon.decor.get((x, y))    #Decoration or misc
        if decoration and MISC_IMAGES.get(decoration):
            screen.blit(MISC_IMAGES[decoration], rect)

        light_levels = lighting(dungeon, game.player_tile, visible)
        step = int(light_levels.get((x,y), 0)*15)
        screen.blit(LIGHT_STEPS[step], rect)


    for foe in game.dungeon_enemies:
        if (foe['x'], foe['y']) in visible:
            sprite = explore_sprites(foe['name'], tile_px) #enemy sprite
            shadow = sprite_shadow(tile_px - 8, max(4, tile_px // 4), alpha = 100)             
            if sprite:
                rect = tile_rect(foe['x'], foe['y'], tile_px, offset_x, offset_y)

                foe_shadow_rect = shadow.get_rect(midbottom = (rect.centerx, rect.bottom - 2))
                screen.blit(shadow, foe_shadow_rect)

                screen.blit(sprite, sprite.get_rect(center=rect.center))

    for i in game.dungeon_items:
        if (i['x'], i['y']) in visible:
            sprite = item_sprites(i['name'], tile_px)
            shadow = sprite_shadow(tile_px - 8, max(4, tile_px // 4), alpha = 100)             
            if sprite:
                rect = tile_rect(i['x'], i['y'], tile_px, offset_x, offset_y)

                item_shadow_rect = shadow.get_rect(midbottom = (rect.centerx, rect.bottom - 2))
                screen.blit(shadow, item_shadow_rect)

                screen.blit(sprite, sprite.get_rect(center=rect.center))

    
    player_sprite = explore_sprites(game.player.name, tile_px) #player sprite
    player_rect = tile_rect(game.player_tile[0], game.player_tile[1], tile_px, offset_x, offset_y)

    shadow = sprite_shadow(tile_px - 8, max(4, tile_px // 4), alpha = 100)             
    player_shadow_rect = shadow.get_rect(midbottom = (player_rect.centerx, player_rect.bottom))

    screen.blit(shadow, player_shadow_rect)
    screen.blit(player_sprite, player_sprite.get_rect(center=player_rect.center))

    #Global message
    note = SmallFont.render(game.message, True, Color['White'])
    screen.blit(note, (WIDTH//2, 60))


