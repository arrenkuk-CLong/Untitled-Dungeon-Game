#CapTen
#Untitled dungeon game
#Turn-based combat, procedural generation, game-feel, and save and load files.
#Additional: player inventory, UI, animations, and screen-shake.
#Checklist
#Incorporate the procedural dungeon generation into the game
#Make minifigures of players and enemy for dungeon exploration #(not necessary yet)
#Make UI for dungeon exploration
#Make inventory
#Add elements (Json (inventory), screenshake, animations, etc) to make the game feel more alive


import pygame, random, sys, json
import gif_pygame
from pygame.locals import *
from PIL import Image
pygame.init()

WIDTH = 1080
HEIGHT = 720
DUNGEON_WIDTH = 40      #Map size in TILES, not pixels
DUNGEON_HEIGHT = 30
TILE_SIZE = 24          #Pixels per tile. 40*24 = 960 wide, 30*24 = 720 tall, so
                        #a whole floor fits on screen and no camera is needed YET
MAP_OFF_X = (WIDTH - DUNGEON_WIDTH * TILE_SIZE) // 2    #Centre the map
MAP_OFF_Y = 0
ROOM_MIN = 4
ROOM_MAX = 8
MAX_ROOMS = 30
FPS = 60

clrBlack = pygame.Color(0, 0, 0)
clrGreen = pygame.Color(0, 128, 0)
clrDGrey = pygame.Color(59, 59, 59)
clrDDGrey = pygame.Color(25, 25, 25) #Dark dark grey
clrGrey = pygame.Color(70, 70, 70)
clrWhite = pygame.Color(255, 255, 255)
clrRed = pygame.Color(120, 0, 0)
clrLRed = pygame.Color(200, 0, 0)
clrBlue = pygame.Color(50, 50, 200)
clrBrown = pygame.Color(110, 70, 30)    #Doors
clrBrown2 = pygame.Color(101, 67, 33)   #Inventory
clrBrown3 = pygame.Color(61, 43, 31)    #Inv border
clrGold = pygame.Color(200, 170, 60)    #Exit stairs

Font = pygame.font.SysFont('cinzel', 45)
SmallFont = pygame.font.SysFont('cinzel', 25)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('ClassBattle')
clock = pygame.time.Clock()

WALL = 1 
FLOOR = 0  
DOOR = 2
ENTER = 3 #Player spawn
EXIT = 4
WALKABLE = (FLOOR, DOOR, ENTER, EXIT)   

#General configuration
GEN_CONFIG = {
    "seed":              None,        # None = new dungeon each run, int = same dungeon forever
    "width":             DUNGEON_WIDTH,
    "height":            DUNGEON_HEIGHT,

    #"algorithm":         "bsp",       # "random" | "bsp"
    "max_rooms":         MAX_ROOMS,   # ("random" only) how many times we try to drop a room
    "room_min":          ROOM_MIN,    # smallest room side, in tiles
    "room_max":          ROOM_MAX,    # largest room side, in tiles
    "room_padding":      1,           # tiles of rock kept between rooms (0 = rooms may touch)
    "bsp_depth":         4,           # ("bsp" only) how many times we slice; rooms = up to 2**depth

    "corridor_style":    "L",         # "L" | "drunk"
    "connect_order":     "sequential",   # "nearest" (tidy, MST) | "sequential" (spaghetti)
    "extra_connections": 2,           # spare links = loops = better exploration
    "wide_corridors":    None,       # 2 tiles wide, for big sprites / party movement

    "place_doors":       True,        # mark corridor tiles that touch a room
    "prune_unreachable": True,        # fill in anything the flood fill can't reach
    "place_stairs":      True,        # entrance in room 0, exit in the farthest room

    "enemy_chance":      0.6,         # chance an eyeball spawns in a room (start room excluded)
    "item_chance":       0.4,
}

#Items (Explore mode) - JSON
#ITEM_SPRITE_MAP says what an item LOOKS like. ITEM_EFFECTS (below) says what
#it DOES. Keeping them apart means adding an item is two small edits instead of
#one big one, and the inventory never has to know anything about sprites.
ITEM_SPRITE_MAP = {
    "Health Potion": "health_potion",
    #"Greater Health Potion": "health_potion",
    #"Strength Scroll": "strength_scroll",
    #"Defense Scroll": "strength_scroll",
    #"Speed Boots": "armor",
    #"Cloak of Shadows": "armor",
    #"Ring of Regeneration": "armor",
    #"Amulet of Health": "armor",
    #"Potion of Invisibility": "health_potion",
    #"Scroll of Teleportation": "strength_scroll"
}

#What each item does when used. Health potions only for now, so this is the one
#entry that matters; the commented items above each need a line here too.
#These values are what gets written into the JSON alongside the quantity.
ITEM_EFFECTS = {
    "Health Potion": {"heal": 30},
}

INVENTORY_FILE = 'inventory.json'   #Written next to the game file
INVENTORY_PERSISTS = True           #True  = potions survive death and even
                                    #        closing the game (a real save file)
                                    #False = every run starts with an empty bag

#=====================================================================
#Classes 
#----------------------------------------------------------------------
#Cards, button, MovesUI, Move, Character, HealthBar
#Cards - covers the img.generation of the 3 classes on the selection screen
# and blits (draw function) the name & img of classes - connected to the 
# card_grid function
# 
#button - create a simple rectangle button type
#
#MovesUI - covers the img.generation of the 4 move types for each class
# blits the name of the move, rect, and CD text if move has an active CD
# clicking returns a bool to trigger the player_atk() function through the
# Move_Buttons list
#
#Moves - stores name, damage, and cooldown for each move. Attached to
# the Character class move list
#
#Character - stores, name, hp, and movesets for the selected class and enemy
# handles CD, alive status, and damage taken functions of the character
#
#HealthBar - draws the healthbar for player and enemy, blits the current hp
# using ratio of turn_hp/max_hp
#
#Room - Store room specific data and prevent overlap
#
#Dungeon - Stores the entire map (tiles, rooms, width, height)
#======================================================================

class Cards: 
    def __init__(self, name, image, x, y, width = 200, height = 200):
        self.name = name #assets
        self.image = pygame.transform.scale(image, (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.selected = False #Border UX boolean trigger - This doesn't work 
        
    def draw(self, screen):
        border_color = clrWhite if self.selected else clrDGrey  #improve UX - Mouse hover (Doesn't work yet)
        pygame.draw.rect(screen, border_color, self.rect, 10)
        screen.blit(self.image, self.rect)                      #surf and rect in that order
        name_txt = Font.render(self.name, True, clrWhite)
        name_rect = name_txt.get_rect(center=(self.rect.center))#center text
        screen.blit(name_txt, name_rect)                        #Name of class, img of class

    def is_clicked (self, pos):
        return self.rect.collidepoint(pos) #Mousebutton down interaction

class button: #First button type for Menu class selection
    def __init__(self, x, y, width, height, text, fill_color = clrGrey, border_color = clrDGrey):
        self.rect = pygame.Rect(x, y, width, height)
        self.fill_color = fill_color
        self.border_color = border_color
        self.text = text
        self.font = Font
    
    def draw(self, screen):
        pygame.draw.rect(screen, clrGrey, self.rect)
        pygame.draw.rect(screen, clrDGrey, self.rect, 7)
        TxtS = self.font.render(self.text, True, clrWhite)
        TxtR = TxtS.get_rect(center=self.rect.center)
        screen.blit(TxtS, TxtR)

    def is_clicked (self, pos):
        return self.rect.collidepoint(pos) #Collidepoint (on click)

class MovesUI: #Second button type for battle UI
    def __init__(self, x, y, width, height, move): #Class that sorts out unique moves for Sword, Wizard, and Archer, trigger from click/button
        self.rect = pygame.Rect(x, y, width, height)
        self.move = move
        #self.CDfont = SmallFont #Cooldown will be shown on SOME move buttons 

    def draw(self, screen, CD = 0): 
        color = clrDGrey if CD == 0 else clrDGrey #UI change Doesn't work
        pygame.draw.rect(screen, color, self.rect)
        #draw moves
        Textscreen = Font.render(self.move.name, True, clrWhite)
        Textrender = Textscreen.get_rect(center = self.rect.center)
        screen.blit(Textscreen, Textrender)
        #If CD > 0 - on cooldown 
        if CD > 0:
            cd_text = SmallFont.render(f"CD:{CD}", True, clrLRed) #Displays the cooldown turn timer
            cd_rect = cd_text.get_rect(topright = (self.rect.right-5, self.rect.top+5)) #On the top right
            screen.blit (cd_text, cd_rect)
    
    def clicked (self, pos): #Return the click bool
        return self.rect.collidepoint(pos) 

class Move: #store name, damage, and move name for the movesets below
    def __init__(self, name, damage, cooldown = 0): #Planned third parameter: Move Cooldown
        self.name = name 
        self.damage = damage 
        self.cooldown = cooldown

class Character: #Health, damage, and other variables needed for battle
    def __init__(self, name: str, health: int, moves) -> None: #realization: very similar to what I did in Unity (C-Sharp)
        self.name = name #Wizard, Sword, Archer, Eye
        self.health = health #Current health after every turn
        self.health_max = health #100 for each char, 80 for the enemy
        self.moves = moves #list of moves
        self.move_CDs = [0] * len(moves) #Each move starts of with no cooldown
    
    def alive(self):
        return self.health > 0 #Return Val of hp - reference this for health bar

    def take_dmg(self, dmg):
        self.health -= dmg
        if self.health < 0: #Defeat detection
            self.health = 0 
    
    #handling cooldowns
    def reset_CD(self):
        self.move_CDs = [0] * len(self.moves) #same
    
    def dec_CDs(self): #Automatically decreases every turn, dont need to intialize it in the gameloop or a func
        for cd in range(len(self.move_CDs)):
            if self.move_CDs[cd] > 0: #If cooldown is larger than zero
                self.move_CDs[cd] -= 1 #then dec cd by 1 (every turn but that isn't coded in this function)
    
    def use_move(self, index): #Pick an index# (1 to 4) each representing a move from the move list by clicking
        if index < len(self.move_CDs):
            move = self.moves[index]
            self.move_CDs[index] = move.cooldown #From Move Class
            return move
        return None #If still on cooldown, return nothing
    
    def move_ready(self, index):
        return self.move_CDs[index] == 0

class HealthBar: #Same class, work on player and enemy
    def __init__(self, x, y, width, height, max_hp):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_hp = max_hp
        self.char_name = ''

    def set_char(self, name):
        self.char_name = name #Identify player (swd, Wiz, Arc) and Enemy

    def draw(self, surf, turn_hp): #turn_hp will be assigned to the current health of a character every turn
        ratio = turn_hp / self.max_hp #always gives the right percentage
        pygame.draw.rect(surf, clrRed, (self.x, self.y, self.width, self.height)) #Healthbar background
        pygame.draw.rect(surf, clrLRed, (self.x, self.y, self.width * ratio, self.height)) #Multiply width by ratio (basically 1 times anything < 1 but > 0)
        pygame.draw.rect(surf, clrRed, (self.x, self.y, self.width, self.height), 5)
        #Health txt
        text = SmallFont.render(f"{int(turn_hp)}/{self.max_hp}", True, clrWhite) 
        text_rect = text.get_rect(center = (self.x + self.width//2 , self.y + self.height//2)) #Position text at the center of hp bar
        surf.blit(text, text_rect)

class Room: 
    def __init__(self, x, y, w, h):
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + w - 1, y + h - 1
        self.cx, self.cy = self.x1 + w // 2, self.y1 + h // 2

    @property #access as a normal variable
    def w(self):
        return self.x2 - self.x1 + 1

    @property 
    def h(self):
        return self.y2 - self.y1 + 1 

    def intersects(self, other, padding = 0):
        #Padding prevents overlap btwn x1(self) and x2(other)
        return (self.x1 - padding <= other.x2 and self.x2 + padding >= other.x1 and
                self.y1 - padding <= other.y2 and self.y2 + padding >= other.y1)
    
    def contains(self, x, y): #Return bool if player is in room
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def random_spot(self, rng): #Somewhere inside this room, never in a wall
        return rng.randint(self.x1, self.x2), rng.randint(self.y1, self.y2)

class Dungeon:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.tiles = [[WALL for _ in range(height)] for _ in range (width)] #Build wall for tiles in height/width
        self.rooms = [] #store # of rooms
        self.start = (0, 0)
        self.exit = None
        self.seed = None
        self.rng = None #The dice cup that built this floor, kept so the enemy
                        #spawns come out of the SAME seeded stream as the map

    def in_bounds(self, x, y):
        #The outer ring is excluded on purpose: the map needs a solid border,
        #or a corridor can be carved off the edge of the world
        return 1 <= x < self.width - 1 and 1 <= y < self.height - 1

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and self.tiles[x][y] in WALKABLE

    def carve(self, x, y, tile=FLOOR):
        if self.in_bounds(x, y):    #self(x, y) tried to CALL the dungeon
            self.tiles[x][y] = tile #object, which is not callable

    def carve_room(self, room):
        for x in range(room.x1, room.x2 + 1): #Horz can_h
            for y in range(room.y1, room.y2 + 1): #vert can_v
                self.carve(x, y)

    def room_at(self, x, y):
        for room in self.rooms:
            if room.contains(x, y):
                return room
        return None

    def neighbours4(self, x, y):
        # Connect rooms only on East, west, North, South
        return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) 

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

class inventory_UI():
    ICON = 64   #Icon is drawn at 64x64 (the pngs are 256x256)

    def __init__(self, x, y, width, height, text, fill_color = clrBrown2, border_color = clrBrown3):
        #Inv box
        self.rect = pygame.Rect(x, y, width, height)
        self.fill_color = fill_color
        self.border_color = border_color
        self.text = text
        self.font = Font

        #None of these existed before, so toggle() and drawicon() were reading
        #attributes that were never created -> AttributeError the moment the
        #dungeon tried to draw itself
        self.is_open = False
        self.bag_closed = load_img('invclosed.png', (self.ICON, self.ICON))
        self.bag_open = load_img('invopen.png', (self.ICON, self.ICON))
        #The icon sits ON TOP of the panel, hugging its left edge, so it stays
        #in the same place whether the panel is open or shut
        self.icon_rect = pygame.Rect(self.rect.left + 6,
                                     self.rect.top - self.ICON - 6,
                                     self.ICON, self.ICON)
        self.use_buttons = []   #[(rect, item name)] rebuilt every draw

    def draw(self, screen, inventory):
        pygame.draw.rect(screen, clrBrown2, self.rect)
        pygame.draw.rect(screen, clrBrown3, self.rect, 7)
        TxtS = self.font.render(self.text, True, clrBrown3)
        TxtR = TxtS.get_rect(midtop=(self.rect.centerx, self.rect.top + 15))
        screen.blit(TxtS, TxtR)

        #One row per item: name + quantity on the left, a USE button on the
        #right. The button rects are REMEMBERED in self.use_buttons so the
        #click test later hits exactly what was drawn - no second layout maths
        #that can drift out of sync with this one.
        self.use_buttons = []
        rows = inventory.rows()
        if not rows:
            empty = SmallFont.render('(empty)', True, clrBrown3)
            screen.blit(empty, (self.rect.left + 20, self.rect.top + 90))
            return

        y = self.rect.top + 85
        for name, qty in rows:
            label = SmallFont.render(f'{name} x{qty}', True, clrWhite)
            screen.blit(label, (self.rect.left + 18, y + 6))

            btn = pygame.Rect(self.rect.right - 78, y, 60, 32)
            pygame.draw.rect(screen, clrBrown3, btn)
            pygame.draw.rect(screen, clrBrown2, btn, 3)
            use_txt = SmallFont.render('USE', True, clrWhite)
            screen.blit(use_txt, use_txt.get_rect(center = btn.center))
            self.use_buttons.append((btn, name))

            y += 46      #Next row

    def toggle(self):
        self.is_open = not self.is_open  #T/F

    def use_button_at(self, pos):
        #Which item's USE button was clicked (None = the click missed them all)
        if not self.is_open:
            return None
        for btn, name in self.use_buttons:
            if btn.collidepoint(pos):
                return name
        return None

    def drawicon (self, screen):
        if self.is_open:
            screen.blit(self.bag_open, self.icon_rect)
        else:
            screen.blit(self.bag_closed, self.icon_rect)

#JSON inventory management
#----------------------------------------------------------------------
#The whole inventory is ONE dict, and that is deliberate: a dict of dicts is
#already valid JSON, so saving is a single json.dump with no conversion step.
#
#   {"Health Potion": {"heal": 30, "quantity": 2}}
#
#Three rules that JSON forces on you, and that this class respects:
#  1. JSON object keys are always strings. Item names are strings, fine - but
#     never key a save file by an int and expect an int back.
#  2. JSON has no tuples, no sets and no pygame objects. Only dict, list, str,
#     int, float, bool and None survive the round trip. That is exactly why the
#     item's SPRITE lives in ITEM_SPRITE_MAP and not in here.
#  3. The file is written by you but read from a disk you do not control. It
#     can be missing, empty, or half-written if the game was killed mid-save,
#     so load() has to survive all three instead of crashing the game.
class Inventory():
    def __init__(self, filename = INVENTORY_FILE):
        self.filename = filename
        self.items = {}     #name -> {"quantity": n, plus whatever ITEM_EFFECTS says}

    #--- contents ------------------------------------------------------
    def add_item(self, name, quantity = 1):
        if name in self.items:
            self.items[name]["quantity"] += quantity    #Stack, don't duplicate
        else:
            entry = dict(ITEM_EFFECTS.get(name, {}))    #Copy, so editing one
            entry["quantity"] = quantity                #potion's data later
            self.items[name] = entry                    #can't edit every potion
        self.save()
        return f'Picked up {name} (x{self.items[name]["quantity"]})'

    def use_item(self, name, target):
        #target = whoever drinks it, i.e. the player Character
        entry = self.items.get(name)
        if not entry or entry["quantity"] <= 0:
            return f'No {name} left'

        heal = entry.get("heal", 0)
        if heal and target.health >= target.health_max:
            return 'Already at full HP'     #Don't burn a potion for nothing

        target.health = min(target.health_max, target.health + heal)

        entry["quantity"] -= 1              #Consume one...
        if entry["quantity"] <= 0:
            del self.items[name]            #...and drop the row when it empties
        self.save()
        return f'Used {name}, healed {heal} HP ({target.health}/{target.health_max})'

    def rows(self):
        #What the UI draws: [(name, quantity)], sorted so the list never
        #reshuffles under the player's cursor between frames
        return sorted((name, data["quantity"]) for name, data in self.items.items())

    def clear(self):
        self.items = {}
        self.save()

    #--- disk ----------------------------------------------------------
    def save(self):
        #indent=2 keeps inventory.json readable, so you can open it and see
        #exactly what the game thinks you are carrying
        with open(self.filename, 'w') as f:
            json.dump(self.items, f, indent = 2)

    def load(self):
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.items = {}         #First ever run: no save file yet
            return 'No inventory file yet'
        except json.JSONDecodeError:
            self.items = {}         #Empty or corrupted file: start clean rather
            return 'Inventory file was corrupt, starting empty'  #than crash

        #Never trust a file you did not just write. Someone can hand-edit this,
        #and a bad row should cost one item, not the whole run.
        self.items = {}
        if isinstance(data, dict):
            for name, entry in data.items():
                if isinstance(entry, dict) and isinstance(entry.get("quantity"), int):
                    if entry["quantity"] > 0:
                        self.items[name] = entry
        return f'Loaded {len(self.items)} item type(s)'


#=====================================================================
#Dungeon Generation functions & Methods 
#----------------------------------------------------------------------
#Bsp place rooms
#Drunk corridor style
#Room connection algorithm (nearest)
#Flood Fill
#Generate dungeon

#Carve rooms (BSP)
def place_rooms_bsp(dungeon, rng, cfg):
    pad = cfg['room_padding']
    min_side = cfg['room_min'] + pad * 2 + 1 #Slice must a room & padding

    def split(x, y, w, h, depth):
        too_small = (w < min_side * 2 and h < min_side * 2)
        if depth <= 0 or too_small: #OR: stop when we run out of depth OR of space
            rw = min(cfg['room_max'], max(cfg['room_min'], w - pad * 2)) #room width
            rh = min(cfg['room_max'], max(cfg['room_min'], h - pad * 2)) #height
            if rw < 1 or rh < 1 or rw > w or rh > h:
                return                             #Skip if slice is too thin
            rx = rng.randint(x, x + w - rw)       
            ry = rng.randint(y, y + h - rh)
            dungeon.rooms.append(Room(rx, ry, rw, rh))
            return

        #cutting along the longer axis
        can_h = h >= min_side * 2  #T/F is there room to cut
        can_v = w >= min_side * 2  #only if h/w is greater than room sides * 2 
        if can_h and can_v: 
            horizontal = h > w if abs(w - h) > 2 else rng.random() < 0.5
        else:
            horizontal = can_h #(T)
        if horizontal:
            cut = rng.randint(min_side, h - min_side)
            split(x, y, w, cut, depth - 1)
            split(x, y + cut, w, h - cut, depth - 1)
        else:#if can_v - cut vertical 
            cut = rng.randint(min_side, w - min_side)
            split(x, y, cut, h, depth - 1)
            split(x + cut, y, w - cut, h, depth - 1)

    split(1, 1, dungeon.width - 2, dungeon.height - 2, cfg['bsp_depth'])
    for room in dungeon.rooms:
        dungeon.carve_room(room)

#Carve corridors (straight)
#The two halves of an L (Horizontal and vertical)
def h_corridor(dungeon, x1, x2, y, wide):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        dungeon.carve(x, y)
        if wide:
            dungeon.carve(x, y + 1)

def v_corridor(dungeon, y1, y2, x, wide):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        dungeon.carve(x, y)
        if wide:
            dungeon.carve(x + 1, y)

def L_corridor(dungeon, a, b, rng, wide):
    #Across then down, or down then across. Flipping a coin on the order stops
    #every hallway bending the same way, which is an instant "a computer made
    #this" tell. Also the fallback when a drunk walk gets lost.
    if rng.random() < 0.5:
        h_corridor(dungeon, a.cx, b.cx, a.cy, wide)
        v_corridor(dungeon, a.cy, b.cy, b.cx, wide)
    else:
        v_corridor(dungeon, a.cy, b.cy, a.cx, wide)
        h_corridor(dungeon, a.cx, b.cx, b.cy, wide)

#Carve corridors (drunk)
#dungeon = instance of Dungeon
#a = starting, b = destination, rng
#Step toward the target MOST of the time and stumble sideways the rest. The
#bias (0.7) is the design knob: 1.0 = a boring straight line, 0.5 = it may
#never arrive at all.
def drunk_corridor(dungeon, a, b, rng, wide):
    x, y = a.cx, a.cy
    budget = (abs(a.cx - b.cx) + abs(a.cy - b.cy)) * 6 + 40 #Step budget
    while (x, y) != (b.cx, b.cy) and budget > 0:
        budget -= 1
        dungeon.carve(x, y)         #Carve where we ARE. Carving x + 1 instead
        if wide:                    #left the tile we stand on solid, so the
            dungeon.carve(x + 1, y) #"corridor" had a wall running down it
        if rng.random() < 0.7:      #Sober step: close the gap
            if rng.random() < 0.5 and x != b.cx: #Choose an axis (rng)
                x += 1 if b.cx > x else -1
            elif y != b.cy:
                y += 1 if b.cy > y else -1
            else:
                x += 1 if b.cx > x else -1
        else:                       #Drunk step: wander
            x, y = rng.choice(dungeon.neighbours4(x, y))
        #Clamp EVERY step
        x = max(1, min(dungeon.width - 2, x))
        y = max(1, min(dungeon.height - 2, y))
    #Out of budget means the walk got lost. Finish with a straight L
    #To guarantee connection
    if (x, y) != (b.cx, b.cy):
        L_corridor(dungeon, Room(x, y, 1, 1), b, rng, wide)

def connect(dungeon, a, b, rng, cfg):
    if cfg["corridor_style"] == "drunk":
        drunk_corridor(dungeon, a, b, rng, cfg["wide_corridors"])
    else:
        L_corridor(dungeon, a, b, rng, cfg["wide_corridors"])

#Nearest Room Connection
def connect_rooms(dungeon, rng, cfg):
    rooms = dungeon.rooms   #copy list of rooms to local func var
    if len(rooms) < 2: 
        return              #Return func if no rooms nearby
    
    else:
        def dist(a, b):
            # Manhattan distance: corridors only move in straight lines, so
            return abs(a.cx - b.cx) + abs(a.cy - b.cy) #Distance x + distance y = manhattan distance (2D)

        #Iterate through all rooms, find the closest room to the linked list, connect, and repeat till all rooms are connected
        linked, pending = [rooms[0]], rooms[1:] #room 0 (starter room) is linked, the rest pending
        while pending:
            best_a, best_b, best_d = None, None, None   #best_d = most optimal distance
            for a in linked:
                for b in pending:
                    d = dist(a, b)
                    if best_d is None or d < best_d:
                        best_a, best_b, best_d = a, b, d
            connect(dungeon, best_a, best_b, rng, cfg)
            pending.remove(best_b)
            linked.append(best_b)

    for _ in range(cfg["extra_connections"]):# spare links for better exploration, at most 2
        a, b = rng.sample(rooms, 2)          # sample = two DIFFERENT rooms
        connect(dungeon, a, b, rng, cfg)

#BFS - search for shortest path to exit by ring
#(and it's nodes) and checks if all rooms are connected
def flood_fill(dungeon, start):
    distance = {start: 0}       #DICT (tile -> steps), not a set. {start, 0} is
                                #a set literal, and a set cannot be indexed, so
                                #the first distance[(nx, ny)] = ... blew up
    queue = [start]             #start from beginning cordinations of list
    head = 0
    while head < len(queue):
        x, y = queue[head]
        head += 1               #Index instead of pop(0): pop(0) is O(n) and
                                #would turn this BFS into O(n^2)
        for nx, ny in dungeon.neighbours4(x, y):
            if (nx, ny) not in distance and dungeon.is_walkable(nx, ny):
                distance[(nx, ny)] = distance[(x, y)] + 1     
                queue.append((nx, ny))  #queue the next set of coordinates to examine
    return distance

#Doors
#A door belongs on a corridor tile that touches a room. So: every floor tile
#that is NOT inside a room but has a room tile next to it is a doorway. The
#already_doored check stops a clump of five doors appearing in a row.
def place_doors(dungeon):
    for x in range(1, dungeon.width - 1):
        for y in range(1, dungeon.height - 1):
            if dungeon.tiles[x][y] != FLOOR or dungeon.room_at(x, y):
                continue
            touches_room = any(dungeon.room_at(nx, ny)
                               for nx, ny in dungeon.neighbours4(x, y))
            already_doored = any(dungeon.tiles[nx][ny] == DOOR
                                 for nx, ny in dungeon.neighbours4(x, y))
            if touches_room and not already_doored:
                dungeon.tiles[x][y] = DOOR



#Generate dungeon
def generate_dungeon(config = None, seed = None):
    cfg = dict(GEN_CONFIG)                 # Define cfg | copy, so a caller's override is
    if config:                             # never allowed to leak into the
        cfg.update(config)                 # global defaults

    # One dice cup for the whole level. Nothing below is allowed to call
    # random.* directly - if it did, the seed would stop reproducing the map.
    if seed is None:
        seed = cfg["seed"] if cfg["seed"] is not None else random.randrange(2**31) #2^31
    rng = random.Random(seed) 

    dungeon = Dungeon(cfg["width"], cfg["height"])
    dungeon.seed = seed
    dungeon.rng = rng   #Kept on the floor so enemy spawns share this stream

    # 1 + 2 - solid rock, then rooms
    #if cfg["algorithm"] == "random":
    #    place_rooms_random(dungeon, rng, cfg)
    #else:
    place_rooms_bsp(dungeon, rng, cfg)

    if not dungeon.rooms:                  # paranoia: a config with huge rooms on
        room = Room(1, 1, min(cfg["room_min"], cfg["width"] - 2),   # a tiny map can
                    min(cfg["room_min"], cfg["height"] - 2))        # place nothing.
        dungeon.rooms.append(room)         # A game must never get a mapless level.
        dungeon.carve_room(room)           #Reduce width and height based on map size

    # 3 - corridors
    connect_rooms(dungeon, rng, cfg)

    # 4 - validate and decorate
    if cfg["place_doors"]:
        place_doors(dungeon)    #With wide_corridors on you get the odd double
                                #door at a room mouth, which is fine

    dungeon.start = (dungeon.rooms[0].cx, dungeon.rooms[0].cy)
    distances = flood_fill(dungeon, dungeon.start)

    if cfg["prune_unreachable"]:
        # Anything BFS never touched is an island. Fill it back in with rock:
        # a room the player can see but can't enter reads as a bug, not mystery.
        for x in range(dungeon.width):
            for y in range(dungeon.height):
                if dungeon.tiles[x][y] in WALKABLE and (x, y) not in distances:
                    dungeon.tiles[x][y] = WALL              #turn tiles not examined to Wall (1)
        dungeon.rooms = [r for r in dungeon.rooms if (r.cx, r.cy) in distances]

    if cfg["place_stairs"]:
        # Pacing for free: the exit goes in whichever room's center scored the
        # highest BFS distance, i.e. the room that is the longest walk away.
        reachable = [r for r in dungeon.rooms if (r.cx, r.cy) in distances]
        if len(reachable) > 1:
            far = max(reachable, key=lambda r: distances[(r.cx, r.cy)])
            dungeon.exit = (far.cx, far.cy)
        elif distances:
            dungeon.exit = max(distances, key=distances.get)
        if dungeon.exit and dungeon.exit != dungeon.start:
            dungeon.tiles[dungeon.exit[0]][dungeon.exit[1]] = EXIT
        dungeon.tiles[dungeon.start[0]][dungeon.start[1]] = ENTER

    return dungeon


#Debug view - print the floor as text. Check this BEFORE trusting the renderer:
#if the ASCII looks wrong then the bug is in the generator, not in the drawing
ASCII_TILES = {WALL: '#', FLOOR: '.', DOOR: '+', ENTER: '<', EXIT: '>'}

def ascii_render(dungeon):
    lines = []
    for y in range(dungeon.height):     #Rows are y...
        lines.append(''.join(ASCII_TILES[dungeon.tiles[x][y]]
                             for x in range(dungeon.width)))  #...columns are x
    return '\n'.join(lines)


#=====================================================================
# LOAD ASSETS
#----------------------------------------------------------------------
# load Menu, Battle background
# Load character cards and battle sprites


#Asset loader - purely to make the asset loading process easier
def load_img(png, scale = None):
    img = pygame.image.load(png)
    if scale: # if I apply (WIDTH, HEIGHT)
        img = pygame.transform.scale(img, scale)
    return img

#BGs
BGmenu = load_img('BGselect.png', (WIDTH, HEIGHT))
BGBattle = load_img('BGBattle.png', (WIDTH, HEIGHT))

#Class files (select stage) | Char cards = Character files + asset_dict --> card_grid = Char_cards + Cards (class) --> class_cards (destination)
character_files = ["Sword.png", "Wizard.png", "Archer.png"]
Char_cards = {} 
for file in character_files:
    name = file.split('.')[0]           #Removes '.' and everything after from file string 
    Char_cards[name] = load_img(file, (260, 260))
    print(f"Loaded: {name}")            #print check in terminal 

#Class files (Battle Stage)
Battle_files = {
    "Sword": load_img("SwordBattle.png", (300, 400)), 
    "Wizard": load_img("WizardBattle.png", (300, 400)),
    "Archer": load_img("ArcherBattle.png", (300, 400))}
Enemy_img = load_img('Eye.png', (250, 350))

def card_grid (names, start_x, start_y, spacing_x, spacing_y, width = 260, height = 260):  
    cards = []
    cols = 3 #2 is very ugly
    for i, name in enumerate(names): #Index and name (index 0: Sword, etc)
        row = i // cols #all three on the same row
        col = i % cols 
        x = start_x + (col * spacing_x) #Spacing by 280 pxls
        y = start_y + (row * spacing_y) #Not really necessary now but Incase I want to come back and add more classes
        #clean_name = name.split('.')[0]
        if name in Char_cards:
            card = Cards(name, Char_cards[name], x, y, width, height) #Name, img, rect 
            cards.append(card)
    return cards

class_cards = card_grid(
    ['Sword', 'Wizard', 'Archer'],
    start_x=128,# Starting X position
    start_y=225,# Starting Y position  
    spacing_x=280,# Horizontal spacing
    spacing_y=350,# Vertical spacing
    width=260,#true toggle for size
    height=260
)


#=====================================================================
# Move Arsenal
#----------------------------------------------------------------------
# 4 moves per class, 1 basic attack, 1 heal, 2 special moves with CD
# Moves are stored in lists (name, dmg, cooldown)
# One animation per class (reduce time spent animating but each class will still have unique animations)

#Sword moves
Sword_moves = [ 
    Move('Slash', 15, 0), #Basic Attack
    Move('Ground Slam', 30, 2), #Planned stat effect and CD
    Move('Guard', 0, 0), #Planned stat effect, USE THIS TO TEST THE DEFEAT SCREEN CAUSE YOU'RE BASICALLY GURANTEED TO WIN IF YOU DONT USE THIS MOVE
    Move('180 Pound', 35, 3) #CD
]

#Wizard moves
Wizard_moves = [ 
    Move('Magic Missile', 20, 0), #Basic Attack
    Move('Frost Beam', 25, 2), #Planned stat effect Short CD
    Move('Light Cure', -15, 2),
    Move('FIREBALL', 30, 3) #Planned stat effect and CD
]

#Archer moves
Archer_moves = [ 
    Move('Quick Fire', 20, 0), #Basic Attack
    Move('Rain of Arrows', 30, 2), #Short CD
    Move('Ranger Stance', 0, 0), #Planned stat effect, USE THIS TO TEST THE DEFEAT SCREEN CAUSE YOU'RE BASICALLY GURANTEED TO WIN IF YOU DONT USE THIS MOVE
    Move('Thunder Snipe', 40, 3) #Planned stat effect and CD
]

#Boss/EnEemy moves,  too many stat effects planned but im lazy to design them
Eye_moves = [ 
    Move('Bloodshot Gaze', 30, 0), #High base attack
    Move('illusory Realm', -20, 2), #Planned stat effect
    Move('Confusion', 0, 0), #Planned stat effect
    Move('Amaterasu', 10, 3) #Planned stat effect and CD
]
#=====================================================================
# Pre-gameloop variables
#----------------------------------------------------------------------
#======================================================================

#Dungeon colors
#Doors were white and the exit was red, but the player marker is white and the
#eyeballs are red, so a door read as the player and the stairs read as a monster
TILE_COLORS = {
    WALL:  clrDDGrey,   #Solid rock
    FLOOR: clrDGrey,    #Walkable
    DOOR:  clrBrown,    #Room/corridor seam
    ENTER: clrBlue,     #Where you spawned
    EXIT:  clrGold,     #Stairs to the next floor
}

#Buttons
classes = button(440, 500, 200, 60, "classes") 
Rematch = button(WIDTH//2 - 150, 500, 150, 60, "Rematch")
Quit = button(WIDTH//2 + 20,  500, 150, 60, "Quit")

#User Interface
Inv = inventory_UI(0, HEIGHT // 6,  300, 500, 'INVENTORY')

#Global Boolean values - flip through game states
#Menu screen -> Selection screen -> Dungeon -> Battle -> Dungeon (win) / Stats (lose)
Menu = True
selection = False
Explore = False         #Dungeon exploration
Battle = False
Stats = False           #Must change in gameloop as player has a new objective

player = None           #Sword, Wizard, or Archer 
enemy = None            #Eye dude
player_anim = None
enemy_anim = None
Move_Buttons = []       #Store moveset of chosen char
turn = 'player'         #Turn based combat - turn starts with player
enemy_acted = False     #prevents enemy from attacking every frame
Message = ''            #Screen terminal
Selected_class = None   #player
#The bag. Inv (above) is the PANEL that draws it; this is the DATA that gets
#written to inventory.json. Inv.is_open is the single open/closed flag - a
#separate inv_open global was a second source of truth waiting to disagree.
inventory = Inventory()

#Stats - these cover the whole RUN now, not one fight, so they survive from
#battle to battle and only get wiped when a new run starts
dmg_dealt = 0
dmg_taken = 0
Battle_won = False
battles_won = 0

#Dungeon exploration state
dungeon = None          #The current Dungeon instance (generate_dungeon() output)
dungeon_level = 1       #Floor number, goes up every time the stairs are used
player_tile = (0, 0)    #Player position in TILES (not pixels)
dungeon_enemies = []    #[{'x':.., 'y':.., 'name':'Eye'}, ...] eyeballs on this floor
dungeon_items = []
current_encounter = None#The enemy dict that started the fight we are in 


#=====================================================================
#Main Gameloop Functions
#----------------------------------------------------------------------


def cycle(cfg, field, values):
    # Move to the next value in the list, wrapping around at the end.
    # (index + 1) % len is the whole "cycle through options" pattern.
    current = cfg[field]
    i = values.index(current) if current in values else -1
    cfg[field] = values[(i + 1) % len(values)]


#=====================================================================
#Dungeon exploration
#----------------------------------------------------------------------
#spawn_enemies()  - one roll per room, using the floor's OWN seeded rng so the
#                   same seed gives the same monsters as well as the same map
#enter_dungeon()  - generate a floor, spawn eyeballs, drop the player on '<'
#enemy_at()       - is something standing on this tile
#move_player()    - one tile per keypress (turn-based, same as the combat).
#                   Walking into an eyeball starts a battle, walking onto the
#                   stairs generates the next floor
#draw_dungeon()   - PLACEHOLDER renderer: one rect per tile, one rect per
#                   creature. This is the hook for the checklist items
#                   (minifigures, camera, dungeon UI, inventory)
#======================================================================

def spawn_enemies(dungeon, cfg):
    #Room 0 is skipped: spawning an eyeball on top of the player is not a fight,
    #it is an ambush the player never agreed to
    enemies = []
    for room in dungeon.rooms[1:]:
        if dungeon.rng.random() < cfg['enemy_chance']:
            x, y = room.random_spot(dungeon.rng)
            if (x, y) != dungeon.start and (x, y) != dungeon.exit:
                enemies.append({'x': x, 'y': y, 'name': 'Eye'})
    return enemies

def spawn_items(dungeon, cfg):
    items = []
    for room in dungeon.rooms[1:]:
        if dungeon.rng.random() < cfg['item_chance']:
            #dungeon.rng, NOT random: the floor's own seeded stream, so one
            #seed reproduces the loot as well as the map and the monsters
            item_type = dungeon.rng.choice(list(ITEM_SPRITE_MAP.keys()))
            x, y = room.random_spot(dungeon.rng)
            if (x, y) != dungeon.start and (x, y) != dungeon.exit:
                items.append({'x' : x, 'y' : y, 'name' : item_type})
    return items


def enter_dungeon(level = 1):
    global dungeon, dungeon_enemies, dungeon_items, dungeon_level, player_tile
    global Menu, selection, Explore, Battle, Stats, Message

    dungeon_level = level
    dungeon = generate_dungeon(GEN_CONFIG)      #Fresh seed
    dungeon_enemies = spawn_enemies(dungeon, GEN_CONFIG)
    dungeon_items = spawn_items(dungeon, GEN_CONFIG)    #Needs the global above,
                                #or this only fills a local list and the floor
                                #ends up with no green tiles on it    
    player_tile = dungeon.start                 #dungeon.start is room 0's centre

    Menu = False
    selection = False
    Explore = True
    Battle = False
    Stats = False
    Message = (f'Floor {dungeon_level} - {len(dungeon_enemies)} eyes, '
               f'{len(dungeon_items)} items. Find the gold stairs.')
    print(f'--- floor {dungeon_level}, seed {dungeon.seed} ---')
    print(ascii_render(dungeon))                #Terminal check, same as always

def enemy_at(x, y):
    for foe in dungeon_enemies:
        if foe['x'] == x and foe['y'] == y:
            return foe
    return None

def item_at(x, y):
    for i in dungeon_items:
        if i['x'] == x and i['y'] == y:
            return i
    return None

def move_player(dx, dy):
    global player_tile, Message
    x, y = player_tile[0] + dx, player_tile[1] + dy

    if not dungeon.is_walkable(x, y):   #Walls stop you. The generator promised
        return                          #every floor tile is reachable, so this
                                        #is the ONLY movement rule needed here
    player_tile = (x, y)

    foe = enemy_at(x, y)
    if foe:
        start_battle(foe)               #Dungeon -> Battle
        return

    #Green tile -> straight into the bag, and straight into inventory.json.
    #Picking up is the only place items ENTER the inventory, so it is the only
    #place that has to remove them from the floor.
    loot = item_at(x, y)
    if loot:
        dungeon_items.remove(loot)      #Off the floor...
        Message = inventory.add_item(loot['name'])  #...and into the JSON

    if dungeon.tiles[x][y] == EXIT:     #Stairs -> next floor, deeper and fresh
        enter_dungeon(dungeon_level + 1)

#Define offset for camera func
def tile_rect(x, y, tile_px = TILE_SIZE, offset_x = MAP_OFF_X, offset_y = MAP_OFF_Y):
    return pygame.Rect(offset_x + x * tile_px, offset_y + y * tile_px,
                       tile_px, tile_px)


#FOV view only 8 tile radius of the player
def fov_tiles(dungeon, player_tile, radius = 8):
    visible = set()
    px, py = player_tile

    for x in range(px - radius, px + radius + 1):
        for y in range (py - radius, py + radius + 1):
            if not dungeon.in_bounds(x, y): #past the map
                continue

            distance = abs(x - px) + abs(y - py)
            if distance <= radius:
                visible.add((x, y)) #set

    return (visible)

#Camera track player & offset to center of screen - disabled.
def camera_offset(player_tile, tile_px):
    px, py = player_tile

    cam_x = WIDTH // 2 - (px * tile_px + tile_px // 2)
    cam_y = HEIGHT // 2 - (py * tile_px + tile_px // 2)
    return cam_x, cam_y


def draw_dungeon(screen, dungeon, tile_px):
    #PLACEHOLDER ART. Every tile is a flat rect, so the generator can be judged
    #on its own before any sprite work happens.
    #TODO(you): minifigure sprites instead of the two rects below
    #TODO(you): camera - draw only the tiles around player_tile and offset them,
    #           instead of blitting the whole 40x30 floor every frame

    visible = fov_tiles(dungeon, player_tile)
    offset_x, offset_y = camera_offset(player_tile, tile_px)

    for x, y in visible:
        rect = pygame.Rect(             #Draw tiles in 8 radius FOV range
            x * tile_px + offset_x,     #Offset to scale the tiles
            y * tile_px + offset_y,
            tile_px,
            tile_px
        )
        pygame.draw.rect(screen, TILE_COLORS[dungeon.tiles[x][y]], rect)

    for foe in dungeon_enemies:             #Eyeballs
        if (foe['x'], foe['y']) in visible:
            pygame.draw.rect(screen, clrLRed,
                tile_rect(foe['x'], foe['y'], tile_px, offset_x, offset_y).inflate(-6, -6))

    for i in dungeon_items:
        if (i['x'], i['y']) in visible:
            pygame.draw.rect(screen, clrGreen, 
                tile_rect(i['x'], i['y'], tile_px, offset_x, offset_y).inflate(-6, -6))

    pygame.draw.rect(screen, clrWhite,
        tile_rect(player_tile[0], player_tile[1], tile_px, offset_x, offset_y).inflate(-8, -8))

    #for x in range(dungeon.width):
    #    for y in range(dungeon.height):
    #       if (x, y) in visible:
    #        pygame.draw.rect(screen, TILE_COLORS[dungeon.tiles[x][y]],
    #                            tile_rect(x, y, tile_px))

    #for foe in dungeon_enemies:             #Eyeballs
    #    if (foe['x'], foe['y']) in visible:
    #        pygame.draw.rect(screen, clrLRed,
    #                        tile_rect(foe['x'], foe['y'], tile_px).inflate(-6, -6))

    #pygame.draw.rect(screen, clrWhite,      #The player
    #                 tile_rect(player_tile[0], player_tile[1], tile_px).inflate(-8, -8))

    #Bare-minimum HUD so the floor is playable
    #TODO(you): this is where the real dungeon UI and the inventory go
    hud = SmallFont.render(
        f'Floor {dungeon_level}   {player.name}  HP {player.health}/{player.health_max}   '
        f'Eyes left: {len(dungeon_enemies)}   [E] bag', True, clrWhite)
    screen.blit(hud, (MAP_OFF_X + 8, 8))
    note = SmallFont.render(Message, True, clrWhite)
    screen.blit(note, (MAP_OFF_X + 8, HEIGHT - 32))

def create_player(class_name):
    #Runs once, when a card is clicked on the selection screen
    global player, player_anim, player_hpbar, Selected_class
    global dmg_dealt, dmg_taken, battles_won, Battle_won

    dmg_dealt = 0 #start as 0
    dmg_taken = 0
    battles_won = 0
    Battle_won = False
    Selected_class = class_name

    #One switch decides whether the save file is a real save file
    if INVENTORY_PERSISTS:
        print(inventory.load())     #Carry potions in from the last session
    else:
        inventory.clear()           #Every run starts with an empty bag

    #class_name means the selected class from selection screen
    #No take backs or confirmation screen
    if class_name == 'Sword':
        player = Character("Sword", 110, Sword_moves) #Name, maxhealth, move list - movelist is referenced using index
        player_hpbar = HealthBar(150, 150, 200, 40, 110)
    elif class_name == 'Wizard':
        player = Character("Wizard", 100, Wizard_moves)
        player_hpbar = HealthBar(150, 150, 200, 40, 100)    
    elif class_name == 'Archer':
        player = Character("Archer", 95, Archer_moves)
        player_hpbar = HealthBar(150, 150, 200, 40, 95)
    player_anim = create_attack_animation(class_name)
    player_hpbar.set_char(player.name)


#=====================================================================
#Battle Functions
#----------------------------------------------------------------------
#load_gif: for attack animations
#
# Start_Battle: Called on encounter (White player = Red enemy)
#Initialize enemy and reset CDs
#
#player_atk: damage/health update and death check
#
#enemy_atk: Same as player_atk
#======================================================================

def load_gif(file):
    gif = Image.open(file)
    frames = [] #6
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


ATTACK_ANIMATION_FILES = {
    'Sword': 'SwordAnim.gif',
    'Wizard': None,
    'Archer': None,
    'Eye': 'EyeAnim.gif',
}


def create_attack_animation(character_name):
    gif_path = ATTACK_ANIMATION_FILES.get(character_name)
    if gif_path is None:
        return None
    return AtkAnimation(gif_path)

def start_battle(encounter):
    #encounter = the {'x','y','name'} dict of the eyeball we walked into, kept
    #so the right one can be deleted from the floor once it dies
    global enemy, enemy_anim, enemy_hpbar, Move_Buttons, current_encounter
    global turn, enemy_acted, Message, Battle, Explore, selection, Menu

    current_encounter = encounter

    #Initilize the enemy
    enemy = Character('Eye', 80, Eye_moves)
    enemy_anim = create_attack_animation('Eye')
    enemy_hpbar = HealthBar(WIDTH - 365, 75, 200, 40, 80)
    enemy_hpbar.set_char('Eye')
    #Generate MovesUI - one moveset - four moves, four buttons
    #Horizontal spacing by 250 px and vertical spacing by 70
    #two moves per row, two rows
    Move_Buttons = [] #Reset the list (Rematch)
    for i, move in enumerate(player.moves):
        x = 200 + (i % 2) * 500 
        y = 550 + (i // 2) * 70
         #New list that contains the moves from either Sword, wizard, or archer
        Move_Buttons.append(MovesUI(x, y, 220, 50, move)) 

    #Fresh cooldowns every fight, but NOT fresh health: damage carries between
    #rooms, and that is what makes exploring a risk
    player.reset_CD()

    Battle = True
    Explore = False
    selection = False
    Menu = False
    turn = 'player'
    enemy_acted = False
    #Print check
    Message = (f"{player.name} vs {enemy.name}")#, player's turn!") 
    print(Message) # terminal
    
def player_atk(move_index): #Function for player attack ONLY
    global Message, Battle, turn, enemy_acted, Stats, Battle_won, dmg_dealt
    global Explore, battles_won, current_encounter
    global player_anim
    move = player.use_move(move_index) #i
    if move is None:
        return

    if player_anim is not None:
        if Selected_class == "Sword" and move_index != 2: #Guard does not have anim
            player_anim.start(
                (WIDTH // 2 - 250, HEIGHT - 400), #Player to enemy
                (WIDTH // 2 + 300, HEIGHT - 400),
            )


    dmg = move.damage
    if dmg > 0: #Player Attack
        enemy.health -= dmg
        dmg_dealt += dmg
        Message = (f'{move.name} dealt {dmg} damage!')
    elif dmg < 0: #Player Heal (Negative damage -dmg)
            player.health = min(player.health_max, player.health - dmg) #Max health becomes the ceiling, cant heal more than 100 hp
            Message = (f'{move.name} healed {dmg} HP!')

    #Enemy death check
    if enemy.health <= 0:
        Battle_won = True
        battles_won += 1
        if current_encounter in dungeon_enemies:
            dungeon_enemies.remove(current_encounter)  #It stays dead when we
        current_encounter = None                       #walk over that tile again
        Message = (f"{enemy.name} got cooked. HP {player.health}/{player.health_max}")
        Battle = False   #Win -> straight back to the floor, wounds and all
        Explore = True
    else:
        turn = 'enemy'
        enemy_acted = False #Enemy can act next frame

def enemy_atk():
    global Message, turn, Battle, Battle_won, Stats, enemy_acted, dmg_taken, Explore
    global enemy_anim
    #Finding which moves the enemy can currently use, since enemy also has some moves with CD
    Ready_or_not = [i for i, cd in enumerate(enemy.move_CDs) if cd == 0] #HERE I COME
    if not Ready_or_not: #Incase the enemy randomly chooses a move that is in CD, cause choosing from an empty list will crash
        enemy.dec_CDs()
        turn = 'player'
        Message = 'Enemy is waiting...'
        return
    
    idx = random.choice(Ready_or_not)
    enemove = enemy.use_move(idx)
    if idx == 0 and enemy_anim is not None: #Only bloodshot gaze should have a projectile
        enemy_anim.start(
            (WIDTH // 2 + 300, HEIGHT - 500),   #Enemy pos to player
            (WIDTH // 2 - 250, HEIGHT - 225),
        )
    dmg = enemove.damage

    if dmg > 0: #Player Attack
        player.health -= dmg
        dmg_taken += dmg
        Message = (f'{enemove.name} dealt {dmg} damage!')
    elif dmg < 0: #Ememy Heal (Negative damage -dmg)
        enemy.health = min(enemy.health_max, enemy.health - dmg) 
        Message = (f'{enemove.name} healed {dmg} HP!')
    else:
        Message = (f'Eye thought it would be getting shieldHP, sorry this is not fortnite!') #IF the eye tries to use the heal move while having full hp. and if the eye tries to use this move on CD
    #Player death check
    if player.health <= 0:
        Message = (f"{player.name} got cooked, you lose")
        Battle_won = False
        Stats = True    #Dying is the only way into the stats screen now
        Battle = False  #End battle, end run
        Explore = False
    else:
        turn = 'player'
        enemy_acted = True #Enemy can act next frame

#Reset the game for a brand new run on rematch or Run
def reset():
    global Menu, selection, Explore, Battle, Stats, player, enemy, turn, enemy_acted
    global Message, dmg_dealt, dmg_taken, Battle_won, battles_won
    global dungeon, dungeon_enemies, dungeon_items, dungeon_level, current_encounter
    Menu = True
    selection = False
    Explore = False
    Battle = False
    Stats = False
    player = None
    enemy = None
    turn = 'player'
    enemy_acted = False
    Message = ''
    dmg_dealt = 0
    dmg_taken = 0
    Battle_won = False
    battles_won = 0
    #Throw the whole floor away: a new run has to roll a new dungeon
    dungeon = None
    dungeon_enemies = []
    dungeon_items = []
    dungeon_level = 1
    current_encounter = None


#=====================================================================
#Gameloop
#----------------------------------------------------------------------
#Constantly checks for events (Menu, selection, Explore, Battle, Stats) and
#draws the appropriate screen based on game state.
#Flow: Menu -> selection -> Explore -> Battle -> Explore (win) / Stats (lose) 
#Battle turn logic handled outside the event loop, enemy attack logic is
#handled on boolean and turn = 'enemy'/'player' and CDs are decreased at
#the start of every player turn
#Finally, draws the appropriate screen based on game state and updates 
#the display and clock tick.
#======================================================================

Rungame = True
while Rungame: 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            Rungame = False

        if Menu:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if classes.is_clicked(pos):
                    Menu = False
                    selection = True
        
        elif selection:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for card in class_cards:
                    if card.is_clicked(pos):
                        create_player(card.name)    #Build the class...
                        enter_dungeon(1)            #...then drop it on floor 1
                        break

        #Trigger after selection screen. Return to this screen after every
        #Battle assuming the player is still alive.
        #One keypress = one tile = one turn, same rhythm as the combat.
        elif Explore:
            if event.type == pygame.KEYDOWN:
                if event.key in (K_UP, K_w):
                    move_player(0, -1)
                elif event.key in (K_DOWN, K_s):
                    move_player(0, 1)
                elif event.key in (K_LEFT, K_a):
                    move_player(-1, 0)
                elif event.key in (K_RIGHT, K_d):
                    move_player(1, 0)
                #Two generator debug keys. Keep them while tuning GEN_CONFIG:
                elif event.key == K_r:              #Re-roll THIS floor
                    enter_dungeon(dungeon_level)
                elif event.key == K_TAB:            #Print the floor as text
                    print(ascii_render(dungeon))
                elif event.key == K_e:              #Open/shut the bag
                    Inv.toggle()                    #Flips Inv.is_open

            #Clicking USE next to a row drinks that potion. Only the buttons
            #the panel actually drew this frame can be hit, so a click while
            #the bag is shut can never use anything.
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                chosen = Inv.use_button_at(pos)
                if chosen:
                    Message = inventory.use_item(chosen, player)
                    print(Message) 


        #breaks every turn after the player has chosen a move.
        elif Battle:
            if turn == 'player' and event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for i, btn in enumerate(Move_Buttons): #Moves with CD = 0
                    if btn.clicked(pos) and player.move_ready(i):
                        player_atk(i) #With that specific index move
                        break
        elif Stats:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if Rematch.is_clicked(pos):
                    reset()
                elif Quit.is_clicked(pos):
                    Rungame = False

    #Enemy attack logic
    if Battle and turn == 'enemy' and not enemy_acted and enemy.alive():
            enemy_atk()

    if player_anim is not None:
        player_anim.update()
    if enemy_anim is not None:
        enemy_anim.update()

    #Decrease cooldown at the start of every player's turn
    if Battle and turn == 'player' and not enemy_acted:
        player.dec_CDs()
        enemy.dec_CDs()

    #Drawing
    if Menu:
        screen.blit(BGmenu, (0, 0))
        classes.draw(screen)
        title_text = Font.render("CLASS BATTLE", True, clrWhite)
        screen.blit(title_text, (430, 150))

    elif selection:
        screen.blit(BGmenu, (0, 0)) #originally had a second background, voided
        HeadTxt = Font.render("SELECT YOUR CLASS", True, clrWhite)
        screen.blit(HeadTxt, (380, 80))
        #Cards of the 3 classes/chars
        for card in class_cards:
            card.draw(screen)

    elif Explore:
        screen.fill(clrBlack)               #Wipe FIRST. Drawing the icon before
        draw_dungeon(screen, dungeon, TILE_SIZE)    #the fill just erased it
        if Inv.is_open:
            Inv.draw(screen, inventory)     #Panel with a USE button per row
        Inv.drawicon(screen)                #Icon last, so it sits on top

    elif Battle:
        #Draw battle background
        screen.blit(BGBattle, (0, 0))

        #Draw player and enemy
        if player and player.name in Battle_files:
            pimg = Battle_files[player.name]
            prect = pimg.get_rect(midbottom = (WIDTH//2 - 250, HEIGHT - 125)) #Better to reference and adjust it from the center 
            screen.blit(pimg, prect)
        if enemy:
            e_img = Enemy_img
            e_rect = pimg.get_rect(midbottom = (WIDTH//2 + 300, HEIGHT - 300))
            screen.blit(e_img, e_rect)

        if player_anim is not None and player_anim.active:
            screen.blit(player_anim.image, player_anim.rect)
        if enemy_anim is not None and enemy_anim.active:
            screen.blit(enemy_anim.image, enemy_anim.rect)

        #Draw health bars
        if player_hpbar:
            player_hpbar.draw(screen, player.health)
        if enemy_hpbar:
            enemy_hpbar.draw(screen, enemy.health)

        #Draw Message
        message_surf = Font.render(Message, True, clrDDGrey)
        screen.blit(message_surf, (WIDTH//2 - message_surf.get_width()//2, 50)) #x, y

        #Draw move buttons only on player's turn
        if turn == 'player':
            pygame.draw.rect(screen, clrDDGrey, (100, 500, 900, 400))
            for i, btn in enumerate(Move_Buttons):
                btn.draw(screen, player.move_CDs[i]) #Passes the Button drawing and the Cooldown # text
    
    #Stats screen, post battle
    elif Stats:
        screen.fill(clrDGrey)
        #title text
        title = Font.render("BATTLE STATS", True, clrWhite)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100)) #Ensures it centeres correctly given the length of the sentence
        #Draw win or lose text
        result_txt = 'VICTORY' if Battle_won else "DEFEAT"
        result_surf = Font.render(result_txt, True, clrWhite)
        screen.blit(result_surf, (WIDTH//2 - result_surf.get_width()//2, 180))
        #damage dealt and damage taken
        dealt = SmallFont.render(f'Damage Dealt: {dmg_dealt}', True, clrWhite)
        taken = SmallFont.render(f'Damage Taken: {dmg_taken}', True, clrWhite)
        screen.blit(dealt, (WIDTH//2 - dealt.get_width()//2, 280))
        screen.blit(taken, (WIDTH//2 - taken.get_width()//2, 320))
        #Run summary - how deep the dungeon got before it killed you
        floors = SmallFont.render(f'Floor Reached: {dungeon_level}', True, clrWhite)
        kills = SmallFont.render(f'Eyes Killed: {battles_won}', True, clrWhite)
        screen.blit(floors, (WIDTH//2 - floors.get_width()//2, 360))
        screen.blit(kills, (WIDTH//2 - kills.get_width()//2, 400))

        #Rematch / quit 
        Rematch.draw(screen)
        Quit.draw(screen)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
sys.exit()
