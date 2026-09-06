#CapTen
#Untitled dungeon game
#Turn-based combat, procedural generation, game-feel, and save and load files.
#Additional: player inventory, UI, animations, and screen-shake.
#Checklist
#Incorporate the procedural dungeon generation into the game
#Make minifigures of players and enemy for dungeon exploration
#Add camera that follows player
#Make UI for dungeon exploration
#Make inventory
#Add elements (Json, screenshake, animations, etc) to make the game feel more alive


import pygame, random, sys
from pygame.locals import *
pygame.init()

WIDTH = 1080
HEIGHT = 720
DUNGEON_WIDTH = 40
DUNGEON_HEIGHT = 30
ROOM_MIN = 4
ROOM_MAX = 8
MAX_ROOMS = 30
FPS = 60

clrBlack = pygame.Color(0, 0, 0)
clrDGrey = pygame.Color(59, 59, 59)
clrDDGrey = pygame.Color(25, 25, 25) #Dark dark grey
clrGrey = pygame.Color(70, 70, 70)
clrWhite = pygame.Color(255, 255, 255)
clrRed = pygame.Color(120, 0, 0)
clrLRed = pygame.Color(200, 0, 0)
clrBlue = pygame.Color(50, 50, 200)

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

    "corridor_style":    "drunk",         # "L" | "drunk"
    "connect_order":     "nearest",   # "nearest" (tidy, MST) | "sequential" (spaghetti)
    "extra_connections": 2,           # spare links = loops = better exploration
    "wide_corridors":    True,       # 2 tiles wide, for big sprites / party movement

    "place_doors":       True,        # mark corridor tiles that touch a room
    "prune_unreachable": True,        # fill in anything the flood fill can't reach
    "place_stairs":      True,       

}


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

class Dungeon:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.tiles = [[WALL for _ in range(height)] for _ in range (width)] #Build wall for tiles in height/width
        self.rooms = [] #store # of rooms
        self.start = (0, 0)
        self.exit = None
        self.seed = None 

    def is_walkable(self, x, y):
        return self(x, y) and self.tiles[x][y] in WALKABLE
    
    def carve(self, x, y, tile=FLOOR):
        if self(x, y):
            self.tiles[x][y] = tile

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
        if depth <= 0 and too_small:
            rw = min(cfg['room_max'], max(cfg['room_min']), w - pad * 2 ) #room width
            rh = min(cfg['room_max'], max(cfg['room_min']), h - pad * 2 ) #height
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

#Carve corridors (drunk)
#dungeon = instance of Dungeon
#a = starting, b = destination, rng
def drunk_corridor(dungeon, a, b, rng): 
    x, y = a.cx, a.cy
    budget = (abs(a.cx - b.cx) + abs(a.cy - b.cy))   * 6 + 40 #1 per tile
    while (x, y) != (b.cx, b.cy) and budget > 0: 
        budget -= 1 
        dungeon.carve(x + 1, y)
        if rng.random() < 0.7:
            if rng.random() < 0.5 and x != b.cx: #Choose an axis (rng)
                x += 1 if b.cx > x else -1 
            elif y != b.cy:
                y += 1 if b.cy > y else -1
            else:
                x += 1 if b.cx > x else -1
        else:
            x, y = rng.choice(dungeon.neighbours4(x, y))
            x = max(1, min(dungeon.width - 2, x))        # clamp: never leave the map
            y = max(1, min(dungeon.height - 2, y))
        
def connect(dungeon, a, b, rng, cfg):
    if cfg["corridor_style"] == "drunk": #Remove later
        drunk_corridor(dungeon, a, b, rng) #leave this

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
    distance = {start, 0}       
    queue = [start]             #start from beginning cordinations of list
    head = 0
    while head < len(queue):
        x, y = queue[head]
        head += 1
        for nx, ny in dungeon.neighbours4(x, y):
            if (nx, ny) not in distance and dungeon.is_walkable(nx, ny):
                distance[(nx, ny)] = distance[(x, y)] + 1     
                queue.append((nx, ny))  #queue the next set of coordinates to examine
    return distance

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
TILE_COLORS = {
    WALL:  clrDDGrey,
    FLOOR: clrDGrey,
    DOOR:  clrWhite,
    ENTER: clrBlue,
    EXIT:  clrRed,
}

#Buttons
classes = button(440, 500, 200, 60, "classes") 
Rematch = button(WIDTH//2 - 150, 500, 150, 60, "Rematch")
Quit = button(WIDTH//2 + 20,  500, 150, 60, "Quit")

#Global Boolean values - flip through game states (menu screen, Selection screen, battle screen, stats screen)
Menu = True
selection = False
dungeon = False         #Dungeon exploration, not implemented
Battle = False
Stats = False           #Must change in gameloop as player has a new objective

player = None           #Sword, Wizard, or Archer 
enemy = None            #Eye dude
Move_Buttons = []       #Store moveset of chosen char
turn = 'player'         #Turn based combat - turn starts with player
enemy_acted = False     #prevents enemy from attacking every frame
Message = ''            #Screen terminal
Selected_class = None   #player

#Stats 
dmg_dealt = 0
dmg_taken = 0           
Battle_won = False 


#=====================================================================
#Main Gameloop Functions
#----------------------------------------------------------------------
#Start_battle() - Intialize battle with selected class (Class_name) and 
#the enemy (Eye) and generates the moveset buttons for player.
#
#Player_atk() - player attack logic, when turn is = player and move button
#is_clicked. Updates Enemy health and player health (heal) and checks for
#enemy death. If enemy dies, Stats = True (Win screen)
#
#enemy_atk() -  enemy attack logic, when turn is = enemy. Enemy move choice
#is random, but only chooses moves that are not on CD. does the same thing
#
#reset() - call this function to reset the game if player wants a rematch
#======================================================================

def cycle(cfg, field, values):
    # Move to the next value in the list, wrapping around at the end.
    # (index + 1) % len is the whole "cycle through options" pattern.
    current = cfg[field]
    i = values.index(current) if current in values else -1
    cfg[field] = values[(i + 1) % len(values)]


def draw_dungeon(screen, dungeon, tile_px):
    for x in range(dungeon.width):
        for y in range(dungeon.height):
            rect = pygame.Rect(x * tile_px, y * tile_px, tile_px, tile_px)
            pygame.draw.rect(screen, TILE_COLORS[dungeon.tiles[x][y]], rect)

def start_battle(class_name): 
    #globalize all variables
    global player, enemy, player_hpbar, enemy_hpbar, Move_Buttons
    global turn, enemy_acted, Message, Battle, selection, Menu
    global dmg_dealt, dmg_taken 

    dmg_dealt = 0 #start as 0
    dmg_taken = 0 

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
    player_hpbar.set_char(player.name)

    #Initilize the enemy
    enemy = Character('Eye', 80, Eye_moves)
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

    Battle = True
    selection = False
    Menu = False
    turn = 'player'
    enemy_acted = False    
    #Print check
    Message = (f"{player.name} vs {enemy.name}")#, player's turn!") 
    print(Message) # terminal
    
def player_atk(move_index): #Function for player attack ONLY
    global Message, Battle, turn, enemy_acted, Stats, Battle_won, dmg_dealt
    move = player.use_move(move_index) #i
    #if move is None:
    #    return

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
        Message = (f"{enemy.name} got cooked, winner winner chicken dinner")
        Battle_won = True
        Stats = True #Initiate stats screen (win)
        Battle = False #End battle
    else:
        turn = 'enemy'
        enemy_acted = False #Enemy can act next frame

def enemy_atk():
    global Message, turn, Battle, dmg_taken,Battle_won, Stats, enemy_acted, dmg_taken
    #Finding which moves the enemy can currently use, since enemy also has some moves with CD
    Ready_or_not = [i for i, cd in enumerate(enemy.move_CDs) if cd == 0] #HERE I COME
    if not Ready_or_not: #Incase the enemy randomly chooses a move that is in CD, cause choosing from an empty list will crash
        enemy.dec_CDs()
        turn = 'player'
        Message = 'Enemy is waiting...'
        return

    idx = random.choice(Ready_or_not)
    enemove = enemy.use_move(idx)
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
        Stats = True #Initiate stats screen (win)
        Battle = False #End battle
    else:
        turn = 'player'
        enemy_acted = True #Enemy can act next frame

def reset(): #Reset game for the same playthrough (rematch)
    global Menu, selection, Battle, Stats, player, enemy, turn, enemy_acted, Message, dmg_dealt, dmg_taken
    Menu = True
    selection = False
    Battle = False
    Stats = False
    player = None 
    enemy = None 
    turn = 'player' 
    enemy_acted = False 
    Message = '' 
    dmg_dealt = 0
    dmg_taken = 0


#=====================================================================
#Gameloop
#----------------------------------------------------------------------
#Constantly checks for events (Menu, selection, Battle, Stats) and draws
#the appropriate screen based on game state. 
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
                        start_battle(card.name) #intialize dungeon instead - in progress
                        break

        elif dungeon: #Trigger after selection screen. Return to this screen after every Battle assuming the player is still alive.
            
        
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

    elif dungeon:
    
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

        #Rematch / quit 
        Rematch.draw(screen)
        Quit.draw(screen)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
sys.exit()
