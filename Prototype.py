#7/24/26
# Rogue Like Dungeon Crawler Game
# Notes
# 1. self.dungeon[nx][ny] == 0 - 0 means empty space/walking ground, 1 means walls or borders
# 2. diagonal 646
# 3. Revamp turn based fighting
# Movement: arrow keys
# Bug fixes: Camera movement
# Bug fixes: Look into combat system
# Bug fixes: ZERO USER INTERFACE
# Goals: Demonstrate two skills: Pokemon combat system and User Interface
# Come back and all levels later

import pygame
import random
import math
import sys


# GLOBAL CONSTANTS 
# ------------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 32
FPS = 60

# Color Palette
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (100, 100, 100)
DARK_GREY = (40, 40, 40)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
YELLOW = (200, 200, 50)
PURPLE = (150, 50, 200)
ORANGE = (200, 100, 50)
BROWN = (130, 80, 30)
LIGHT_BLUE = (100, 150, 255)

# Dungeon dimensions (in tiles)
DUNGEON_WIDTH = 40
DUNGEON_HEIGHT = 30
ROOM_MIN = 4
ROOM_MAX = 8
MAX_ROOMS = 30


# PIXEL ART GENERATORS - Create assets
# ------------------------------
#Sprite dimensions - 32px by 32px dimensions - base for each character
def create_sprite(color, shape, size=TILE_SIZE): #color (dictionary), shape (name), size (32 by 32 px)
    """Return a pygame surface with a simple pixel-art sprite."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA) 
    surf.fill((0, 0, 0, 0))  # transparent (Last zero)
    pixels = pygame.PixelArray(surf) #Allows modification to pygame.surface objects

    #Player
    if shape == "player":
        # A small knight with helmet
        for x in range(size): #One pixel each - up to 32px
            for y in range(size):
                if (x == 0 or x == size-1 or y == 0 or y == size-1):
                    continue
                #Manipulatung ranges of px (in 32/32 dimension) to fill colors
                # Body
                if 6 <= x <= 25 and 16 <= y <= 30:
                    pixels[x, y] = color 
                # Head
                if 10 <= x <= 21 and 8 <= y <= 18:
                    pixels[x, y] = (200, 180, 140)  # skin
                # Helmet
                if 9 <= x <= 22 and 6 <= y <= 12: 
                    pixels[x, y] = (150, 150, 150)
                # Eyes
                if x == 13 and y == 12:
                    pixels[x, y] = BLACK
                if x == 18 and y == 12:
                    pixels[x, y] = BLACK
                # Sword
                if 24 <= x <= 26 and 18 <= y <= 28:
                    pixels[x, y] = (200, 200, 200)

    #Enemy type 1                 
    elif shape == "skeleton":
        # Skeleton: white bony figure
        for x in range(size):
            for y in range(size):
                if (x == 0 or x == size-1 or y == 0 or y == size-1):
                    continue
                if 10 <= x <= 21 and 12 <= y <= 29:
                    pixels[x, y] = color
                # Skull
                if 12 <= x <= 19 and 6 <= y <= 13:
                    pixels[x, y] = color
                # Eye holes
                if x == 14 and y == 10:
                    pixels[x, y] = BLACK
                if x == 17 and y == 10:
                    pixels[x, y] = BLACK
    #Enemy type 2
    elif shape == "zombie":
        # Greenish zombie
        for x in range(size):
            for y in range(size):
                if (x == 0 or x == size-1 or y == 0 or y == size-1):
                    continue
                if 10 <= x <= 21 and 14 <= y <= 29:
                    pixels[x, y] = color
                # Head
                if 12 <= x <= 19 and 8 <= y <= 15:
                    pixels[x, y] = color
                # Eye
                if x == 14 and y == 11:
                    pixels[x, y] = RED
                if x == 17 and y == 11:
                    pixels[x, y] = RED
    #Enemy type 3
    elif shape == "bat":
        # Bat (purple)
        for x in range(size):
            for y in range(size):
                if (x == 0 or x == size-1 or y == 0 or y == size-1):
                    continue
                # Body
                if 8 <= x <= 23 and 14 <= y <= 25:
                    pixels[x, y] = color
                # Wings
                if (x < 8 or x > 23) and 12 <= y <= 28:
                    if (x % 2 == 0):  # ragged edges
                        pixels[x, y] = color
                # Eyes
                if x == 13 and y == 15:
                    pixels[x, y] = YELLOW
                if x == 18 and y == 15:
                    pixels[x, y] = YELLOW
    #Enemy type 4
    elif shape == "slime":
        # Slime (green blob)
        for x in range(size):
            for y in range(size):
                if (x == 0 or x == size-1 or y == 0 or y == size-1):
                    continue
                # Blob circle-ish - Inner Color
                dx = x - size//2 
                dy = y - size//2
                if dx*dx + dy*dy < (size//2 - 4)**2: #makes sure the inner color isn't outside the sprite
                    pixels[x, y] = color
                # Eye
                if x == 12 and y == 15:
                    pixels[x, y] = BLACK
                if x == 19 and y == 15:
                    pixels[x, y] = BLACK
    #Enemy type 5
    elif shape == "wraith":
        # Wraith (ghostly blue)
        for x in range(size):
            for y in range(size):
                if (x == 0 or x == size-1 or y == 0 or y == size-1):
                    continue
                # Body shape with transparency
                if 10 <= x <= 21 and 12 <= y <= 28:
                    alpha = 180 if (y > 20) else 255
                    if alpha == 255:
                        pixels[x, y] = color
                    else:
                        pixels[x, y] = (*color, alpha)
                # Faint face
                if 13 <= x <= 18 and 14 <= y <= 18:
                    pixels[x, y] = (200, 200, 255)

    #Consumables / Items
    elif shape == "health_potion": #1
        # Red potion
        for x in range(size):
            for y in range(size):
                if (x == 0 or x == size-1 or y == 0 or y == size-1):#One Pixel smaller than base sprite size
                    continue
                if 8 <= x <= 23 and 12 <= y <= 27: # Upper part of the pot
                    pixels[x, y] = color
                # Cork
                if 12 <= x <= 19 and 9 <= y <= 13:
                    pixels[x, y] = (150, 100, 50)
    elif shape == "strength_scroll": #2
        # Scroll with yellow glow
        for x in range(size):
            for y in range(size):
                if (x == 0 or x == size-1 or y == 0 or y == size-1):
                    continue
                if 8 <= x <= 23 and 12 <= y <= 27:
                    pixels[x, y] = color
                # Runes - Small Details
                if (x == 12 or x == 19) and y == 18: #Brackets consider the or parameter first
                    pixels[x, y] = YELLOW #Al pixels within the list (#12 to 19) become yellow
                if (x == 15) and y == 15:
                    pixels[x, y] = YELLOW
    elif shape == "armor":
        # Chainmail
        for x in range(size):
            for y in range(size):
                if (x == 0 or x == size-1 or y == 0 or y == size-1):
                    continue
                if 6 <= x <= 25 and 12 <= y <= 28:
                    pixels[x, y] = color
                # Draw a row/column every 4 pixels (4 % 4 = 0)
                if (x % 4 == 0 or y % 4 == 0) and 10 <= x <= 24 and 14 <= y <= 26: # Draws a cross pattern within the horz and vert range
                    pixels[x, y] = (180, 180, 180) #all pixels on each col/row = light grey
    else:
        # fallback: colored square
        surf.fill(color)
    del pixels
    return surf

# Item sprites dictionary
# Categorizations: Pots, Scrolls, and Armor
ITEM_SPRITE_MAP = {
    "Health Potion": "health_potion",
    "Greater Health Potion": "health_potion",
    "Strength Scroll": "strength_scroll",
    "Defense Scroll": "strength_scroll",
    "Speed Boots": "armor",
    "Cloak of Shadows": "armor",
    "Ring of Regeneration": "armor",
    "Amulet of Health": "armor",
    "Potion of Invisibility": "health_potion",
    "Scroll of Teleportation": "strength_scroll"
}

ITEM_COLORS = {
    "Health Potion": RED,
    "Greater Health Potion": (255, 50, 50),
    "Strength Scroll": ORANGE,
    "Defense Scroll": BLUE,
    "Speed Boots": BROWN,
    "Cloak of Shadows": PURPLE,
    "Ring of Regeneration": GREEN,
    "Amulet of Health": YELLOW,
    "Potion of Invisibility": LIGHT_BLUE,
    "Scroll of Teleportation": (200, 100, 200)
}

# Enemy sprite map - lowercase
ENEMY_SPRITE_MAP = {
    "Skeleton": "skeleton",
    "Zombie": "zombie",
    "Bat": "bat",
    "Slime": "slime",
    "Wraith": "wraith"
}
ENEMY_COLORS = {
    "Skeleton": (220, 220, 220),
    "Zombie": (80, 160, 80),
    "Bat": (150, 50, 200),
    "Slime": (50, 200, 50),
    "Wraith": (100, 150, 255)
}


# DUNGEON GENERATION (rooms + corridors)
# ------------------------------
class Room:
    def __init__(self, x, y, w, h): #state objects
        self.x1 = x #Start x pos
        self.y1 = y
        self.x2 = x + w #End x pos
        self.y2 = y + h
        self.cx = x + w//2 #Center x of the room
        self.cy = y + h//2 #Center y of the room
    
    def intersects(self, other): #Return if these x/ypos statements are true
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1) 

def generate_dungeon(): # Returns dungeon, player_x, player_y, enemies, items 
    dungeon = [[1 for _ in range(DUNGEON_HEIGHT)] for _ in range(DUNGEON_WIDTH)]  # 1=wall 40 width walls 30 length walls
    rooms = [] #List - stores sprites
    for _ in range(MAX_ROOMS): #30 
        w = random.randint(ROOM_MIN, ROOM_MAX) #random (0-4, 0-8)
        h = random.randint(ROOM_MIN, ROOM_MAX) 
        x = random.randint(1, DUNGEON_WIDTH - w - 1) #32px - random width - 1 
        y = random.randint(1, DUNGEON_HEIGHT - h - 1)
        new_room = Room(x, y, w, h) #Random coordinates and random dimensions
        if not any(new_room.intersects(r) for r in rooms): #If rooms don't intersect, add it to the list
            rooms.append(new_room)
            # Carve room
            for i in range(x, x+w): #Each px in the width 
                for j in range(y, y+h): #Each px in the height
                    dungeon[i][j] = 0  #floor
    
    # Connect rooms with corridors (simple L-shaped)
    for i in range(1, len(rooms)): #Start at first index, because the first room [0], is the base
        prev = rooms[i-1] #Previous index
        curr = rooms[i]
        # Previous room x, Previous room y (center)
        # Current room x, current room y (center)
        x1, y1 = prev.cx, prev.cy 
        x2, y2 = curr.cx, curr.cy
        # Horizontal - creating the corridor to connect horizontal pathways
        # Use while loop to fill the corridor with 0's (dungeon[x][y] = 0) and iterate the range (x1, x2) as walls.
        for x in range(min(x1, x2), max(x1, x2)+1): 
            dungeon[x][y1] = 0
        # Vertical - create up/down corridor that goes to the current room's center
        for y in range(min(y1, y2), max(y1, y2)+1):
            dungeon[x2][y] = 0 #why x2?
    
    # Ensure player start in first room and in the center
    start_room = rooms[0] #Starting room = First index room 
    player_x = start_room.cx # cx = x // 2
    player_y = start_room.cy
    
    # Place enemies and items in rooms (excluding first)
    # Random Placement - based on the random.random chances 
    # take a random sprite from the dictionary 
    # And turns it and it's contents/data (keys) into a list. 
    enemies = []
    items = []
    for idx, room in enumerate(rooms):
        if idx == 0: # Nothing will spawn If index is zero
            continue #pass/skips the code
        # Chance for enemy
        if random.random() < 0.5:
            enemy_type = random.choice(list(ENEMY_SPRITE_MAP.keys()))
            #Random Spawn
            ex = random.randint(room.x1+1, room.x2-1) 
            ey = random.randint(room.y1+1, room.y2-1)
            enemies.append((ex, ey, enemy_type)) #add to list
        # Chance for item
        if random.random() < 0.4:
            item_type = random.choice(list(ITEM_SPRITE_MAP.keys()))
            ix = random.randint(room.x1+1, room.x2-1)
            iy = random.randint(room.y1+1, room.y2-1)
            items.append((ix, iy, item_type))
    
    return dungeon, player_x, player_y, enemies, items 


# ENTITY CLASSES
# ------------------------------
class Entity:
    def __init__(self, x, y, name, sprite, color): #Sprite parameter = player
        self.x = x
        self.y = y
        self.name = name
        self.sprite = sprite  # surface
        self.color = color
    
class Player(Entity): #Player is Parent class
    #Define all player variables - hp, max_hp, str, def, lvl, xp, inv, alive status, fov
    #Call create_sprite function for the 'sprite' parameter for the child class Entity
    def __init__(self, x, y):
        #super: can be used when there is a parent & child class
        #super: can give the child class methods and parameters from the parent class
        super().__init__(x, y, "Player", create_sprite((200,200,200), "player"), WHITE)
        self.hp = 30
        self.max_hp = 30
        self.strength = 5
        self.defense = 2
        self.level = 1
        self.xp = 0
        self.xp_to_next = 10
        self.inventory = []
        self.alive = True
        self.fov_radius = 6
    #lvl up function - permanently add stats and increase xp meter bar
    #Should be displayed on screen
    def level_up(self):
        self.level += 1
        self.max_hp += 10
        self.hp = self.max_hp 
        self.strength += 2
        self.defense += 1
        self.xp_to_next = int(self.xp_to_next * 1.5) #increase the xp requirement to level up
        print(f"Level up! Now level {self.level}") #Termina=l only - can delete
    #use self and dmg parameters - self.hp and assign dmg to five enemy entities
    #consider True damage after calculating defense
    #Check player status after damage code runs
    def take_damage(self, dmg):
        actual = max(1, dmg - self.defense) 
        self.hp -= actual
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
    #call heal function - use for health pots, amount = heal, self.hp to use +
    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
    #xp function will be called on enemy defeat/room clear 
    #add amount parameter to self.xp and use a while loop to check if it meets the lvlup requirement
    #if lvlup requirement is met, call lvlup function
    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.level_up()

class Enemy(Entity): 
    #same parameters as player, x, y, and type
    #use same Entity child class for parameters: name, sprite, color
    #define enemy_type, color and sprite in advance
    def __init__(self, x, y, enemy_type):
        self.enemy_type = enemy_type
        color = ENEMY_COLORS[enemy_type] 
        sprite = create_sprite(color, ENEMY_SPRITE_MAP[enemy_type]) #Define sprite parameter - more organized
        super().__init__(x, y, enemy_type, sprite, color) 
        # stats: hp, maxhp, str, def, xp_val, speed
        if enemy_type == "Skeleton":
            self.hp = 8
            self.max_hp = 8
            self.strength = 4
            self.defense = 1
            self.xp_value = 5
            self.speed = 1
        elif enemy_type == "Zombie":
            self.hp = 12
            self.max_hp = 12
            self.strength = 5
            self.defense = 0
            self.xp_value = 6
            self.speed = 1
        elif enemy_type == "Bat":
            self.hp = 5
            self.max_hp = 5
            self.strength = 3
            self.defense = 0
            self.xp_value = 4
            self.speed = 2
        elif enemy_type == "Slime":
            self.hp = 10
            self.max_hp = 10
            self.strength = 3
            self.defense = 3
            self.xp_value = 5
            self.speed = 1
        elif enemy_type == "Wraith":
            self.hp = 15
            self.max_hp = 15
            self.strength = 6
            self.defense = 2
            self.xp_value = 8
            self.speed = 1
        self.alive = True #boolean to check status of entity while function runs
        self.fov_radius = 5 #Enemy Detection range
    #health function same as player - works on all entities
    def take_damage(self, dmg):
        actual = max(1, dmg - self.defense)
        self.hp -= actual
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

# Item definition
# define name from Item dictionary by turning it into a list
# run through create_sprite function to define self.sprite as the color and item type
class Item:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.type = item_type
        self.sprite = create_sprite(ITEM_COLORS[item_type], ITEM_SPRITE_MAP[item_type])
        self.pickup_message = f"Picked up {item_type}!" #extra parameter, pickup status

    #use Function - each item - based on dictionary
    #refer to heal function and strength, defense, & fov parameter in player (__init__)
    #cloak of shadows, ring of regen, pot of invis, and scroll of tele will be implemented in game loop since they don't give simple stat buffs
    def use(self, player):
        if self.type == "Health Potion":
            player.heal(10)
            return "You drink the health potion and heal 10 HP."
        elif self.type == "Greater Health Potion":
            player.heal(25)
            return "You drink the greater health potion and heal 25 HP."
        elif self.type == "Strength Scroll":
            player.strength += 2
            return "You feel stronger! Strength +2."
        elif self.type == "Defense Scroll":
            player.defense += 1
            return "You feel tougher! Defense +1."
        elif self.type == "Speed Boots":
            player.fov_radius += 1
            return "Your vision expands! FOV +1."
        elif self.type == "Cloak of Shadows":
            # Stealth: maybe increase dodge chance (simplified as +defense)
            player.defense += 2
            return "You become harder to hit! Defense +2."
        elif self.type == "Ring of Regeneration":
            player.heal(5)
            return "You feel a warm pulse, healing 5 HP."
        elif self.type == "Amulet of Health":
            player.max_hp += 10
            player.heal(10)
            return "Your vitality increases! Max HP +10."
        elif self.type == "Potion of Invisibility":
            # For simplicity: gain +3 defense for a turn (we'll implement as instant +2 def for now)
            player.defense += 2
            return "You turn slightly transparent, gaining +2 defense."
        elif self.type == "Scroll of Teleportation":
            # Teleport to a random room (we'll just teleport to a random tile)
            # We'll implement in game loop
            return "Teleportation scroll used."
        else:
            return "Nothing happens."


# GAME STATE/ GAME LOOP
# ------------------------------
class Game:
    # Initialize with __init__(self) - assign lists and self definitions
    # define player, enemy, items, game loop bools, turns, messages, and generate_dungeon class
    def __init__(self):
        self.dungeon, px, py, enemy_data, item_data = generate_dungeon() #dungeon, player_x, player_y, enemies, items 
        self.player = Player(px, py) #Starting Cords - updates on movement
        self.enemies = []
        self.items = []
        for ex, ey, etype in enemy_data: #fetch the x pos, y pos, and type for each enemy spawned
            self.enemies.append(Enemy(ex, ey, etype)) #adds to list in this class
        for ix, iy, itype in item_data: #same as enmey
            self.items.append(Item(ix, iy, itype))
        self.turn = "player"  # "player" or "enemy" - turn based combat
        self.messages = [] #list for non-terminal game msg
        #Bools
        self.game_over = False
        self.player_turn_done = False
    #message function 
    #if the # of messages goes over ten (1 msg per idx) - list will pop/remove the oldest one
    def add_message(self, msg):
        self.messages.append(msg) #messages is a list
        if len(self.messages) > 10:
            self.messages.pop(0) #pop first and oldest idx of the 10
    #FOV 
    def get_visible_tiles(self): #Set() - Circle uses Pythagoream theorem
        # Simple FOV: all tiles within radius (no occlusion)
        visible = set() #Instance variable
        #in  a constructor, set() becomes an independent instance variable (explain), 
        #and will have effect on one individual entity among a list of entities
        #depending if that specific entity met the requires or not.
        px, py = self.player.x, self.player.y #fetch current grid cords
        r = self.player.fov_radius #6
        for dx in range(-r, r+1):  #-6, 6 #West, East
            for dy in range(-r, r+1): #-6, 6 #South North
                if dx*dx + dy*dy <= r*r: #Pythag x^2 + y^2 <= radius^2
                    #total x & y
                    tx = px + dx 
                    ty = py + dy
                    if 0 <= tx < DUNGEON_WIDTH and 0 <= ty < DUNGEON_HEIGHT:
                        visible.add((tx, ty))
        return visible
    #Velocity, player turn, border, global messages, pick up items
    def move_player(self, dx, dy): #fetch x and y cords (given its a range)
        if not self.player.alive or self.game_over: 
            return
        if self.turn != "player":
            return
        #self (Game) player (Entity) x(pos) + dx/dy(move velocity)
        new_x = self.player.x + dx #Horizontal 
        new_y = self.player.y + dy #Vertical 
        if 0 <= new_x < DUNGEON_WIDTH and 0 <= new_y < DUNGEON_HEIGHT: #Borders
            # walkable area - listed new_x and new_y variables are different every room
            # Edges are bordered
            if self.dungeon[new_x][new_y] == 0:  
                # check if enemy there
                enemy = self.get_enemy_at(new_x, new_y) #define enemy with function - has x / y movement
                if enemy: #If enemy is there
                    # attack (take_damage)
                    # Global messages
                    # add xp to player and remove enemy from list
                    dmg = self.player.strength
                    enemy.take_damage(dmg) #Call dmg for function
                    self.add_message(f"You hit {enemy.name} for {dmg} damage.")
                    if not enemy.alive:
                        self.add_message(f"{enemy.name} is destroyed!")
                        self.player.add_xp(enemy.xp_value)
                        self.enemies.remove(enemy)
                    self.player_turn_done = True
                else:
                    self.player.x = new_x
                    self.player.y = new_y
                    # check for items
                    item = self.get_item_at(new_x, new_y) #assign call function to cords
                    if item:
                        msg = item.use(self.player) #Auto use on pickup
                        self.add_message(msg)
                        self.items.remove(item) #Remove item from items list
                    self.player_turn_done = True
            else:
                self.add_message("You bump into a wall.")
        else:
            self.add_message("You can't go there.")

    def get_enemy_at(self, x, y):
        for e in self.enemies:
            if e.x == x and e.y == y and e.alive: 
                return e #If all are true. return x, y, and status
        return None #Return an empty result early

    def get_item_at(self, x, y):
        for it in self.items: #it refer to list of items in gm loop
            if it.x == x and it.y == y: #Cords
                return it
        return None

    def enemy_turn(self):
        # Enemies move toward player if in FOV, else wander 
        # 0 for walkable path
        # step in the direction the player is at
        # Random wander - 4 tuples in a list
        # avoid stepping on another entity
        for enemy in self.enemies: 
            if not enemy.alive: #For every enemy in the list, if the enemy isn't alive, continue
                continue #skip all code below
            # Check if player is within that enemy's FOV
            dx = self.player.x - enemy.x
            dy = self.player.y - enemy.y
            dist = math.hypot(dx, dy) #calculate the hypotenuse
            if dist <= enemy.fov_radius: 
                # Move toward player
                step_x = 1 if dx > 0 else (-1 if dx < 0 else 0) #direction (1 = right. -1 = left) 
                step_y = 1 if dy > 0 else (-1 if dy < 0 else 0) #same as step_x but up & down
                #one turn move
                moved = False 
                # Prefer axis with larger distance
                if abs(dx) >= abs(dy): #abs = absolute value
                    # try horizontal
                    if step_x != 0: 
                        #newx/y +1 or -1
                        nx = enemy.x + step_x 
                        ny = enemy.y
                        # [0]-----[nx]-----[border width]
                        # if newx is between 0 and the end of the room width/height
                        # and if the ground in the column/row is walkable (0)
                        if 0 <= nx < DUNGEON_WIDTH and 0 <= ny < DUNGEON_HEIGHT and self.dungeon[nx][ny] == 0: #nx = row, ny = column
                            # check if player is there
                            if nx == self.player.x and ny == self.player.y:
                                # attack player
                                self.player.take_damage(enemy.strength)
                                self.add_message(f"{enemy.name} hits you for {enemy.strength} damage.")
                                if not self.player.alive: #Game, Entity, bool Status
                                    self.add_message("You have been slain...")
                                    self.game_over = True
                            else:
                                enemy.x = nx #If not in combat, move one tile
                                moved = True #once true, it's player's turn
                #Vertical - same code as step_x           
                if not moved and step_y != 0:
                    nx = enemy.x #x stays where it's at
                    ny = enemy.y + step_y
                    if 0 <= nx < DUNGEON_WIDTH and 0 <= ny < DUNGEON_HEIGHT and self.dungeon[nx][ny] == 0:
                        if nx == self.player.x and ny == self.player.y:
                            self.player.take_damage(enemy.strength)
                            self.add_message(f"{enemy.name} hits you for {enemy.strength} damage.")
                            if not self.player.alive:
                                self.add_message("You have been slain...")
                                self.game_over = True
                        else:
                            enemy.x = nx
                            moved = True
                # if still not moved, try diagonal? We'll skip for simplicity.
            else:
                # Random wander
                dirs = [(0,1),(0,-1),(1,0),(-1,0)] #tuples - up, down, right, left by 1 
                random.shuffle(dirs) #shuffles/changes index order
                for dx, dy in dirs: 
                    nx = enemy.x + dx #-1/1/0
                    ny = enemy.y + dy #-1/1/0
                    if 0 <= nx < DUNGEON_WIDTH and 0 <= ny < DUNGEON_HEIGHT and self.dungeon[nx][ny] == 0:
                        # don't step on another enemy
                        if not self.get_enemy_at(nx, ny):
                            enemy.x = nx
                            enemy.y = ny
                            break
        self.player_turn_done = False  # reset for next player turn
    #if Game (turn) = player - else Game (turn) = enemy 
    def process_turn(self):
        if self.game_over:
            return
        if self.turn == "player":
            # player turn already handled by input, just check if done
            if self.player_turn_done:
                self.turn = "enemy"
        else:
            self.enemy_turn()
            self.turn = "player"
            # After enemy turn, check if player dead
            if not self.player.alive:
                self.game_over = True

    #DRAWIWNG
    #----------------------
    def render(self, screen, font):
        screen.fill(BLACK)
        visible = self.get_visible_tiles() #tiles that appear in FOV range 
        
        # Draw dungeon tiles
        # Filter down to tiles that are in range of FOV and the dungeon area
        for x in range(DUNGEON_WIDTH):
            for y in range(DUNGEON_HEIGHT):
                if (x, y) in visible:
                    color = (30, 30, 30) if self.dungeon[x][y] == 0 else (80, 80, 80) #Set floor color to 30, everyting else is 80
                    pygame.draw.rect(screen, color, (x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)) #x cord, y cord, square dimension
        
        # Draw items
        for it in self.items:
            if (it.x, it.y) in visible:
                screen.blit(it.sprite, (it.x*TILE_SIZE, it.y*TILE_SIZE)) #has name and shape, needs size & cords
                #Game (sprite parameter) = create_sprite function 
        
        # Draw enemies
        for e in self.enemies:
            if e.alive and (e.x, e.y) in visible:
                screen.blit(e.sprite, (e.x*TILE_SIZE, e.y*TILE_SIZE))
        
        # Draw player
        screen.blit(self.player.sprite, (self.player.x*TILE_SIZE, self.player.y*TILE_SIZE))
        
        # HUD
        hud_y = DUNGEON_HEIGHT * TILE_SIZE + 5
        # Background for HUD
        pygame.draw.rect(screen, (20,20,20), (0, hud_y, SCREEN_WIDTH, SCREEN_HEIGHT - hud_y)) #x, y, screen dimensions
        font_small = pygame.font.Font(None, 18)
        #Huge f string
        text = f"HP: {self.player.hp}/{self.player.max_hp}  Lv:{self.player.level}  XP:{self.player.xp}/{self.player.xp_to_next}  Str:{self.player.strength}  Def:{self.player.defense}"
        label = font_small.render(text, True, WHITE) #render text
        screen.blit(label, (10, hud_y + 5)) #blit text
        
        # Messages
        msg_y = hud_y + 30
        for msg in self.messages[-5:]:
            msg_surf = font_small.render(msg, True, (200,200,200))
            screen.blit(msg_surf, (10, msg_y))
            msg_y += 20
        
        # Game over overlay
        # Screen text - input code is in main
        if self.game_over:
            go_font = pygame.font.Font(None, 60)
            go_text = go_font.render("GAME OVER", True, RED)
            screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
            restart_font = pygame.font.Font(None, 30)
            restart_text = restart_font.render("Press R to restart", True, WHITE)
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 20))

# ------------------------------
# MAIN - Movement is OK
# ------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("NecroCrypt - Roguelike Dungeon Crawler")
    clock = pygame.time.Clock()
    game = Game()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            #True gameloop
            if event.type == pygame.KEYDOWN:
                #gameover
                if game.game_over:
                    if event.key == pygame.K_r:
                        game = Game()  # restart
                    continue
                if game.turn == "player":
                    dx, dy = 0, 0
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        dy = -1
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        dy = 1
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        dx = -1
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        dx = 1
                    elif event.key == pygame.K_SPACE:
                        # Wait / skip turn
                        game.player_turn_done = True
                    if dx != 0 or dy != 0:
                        game.move_player(dx, dy)
                    if game.player_turn_done:
                        game.turn = "enemy"
                        game.process_turn()
        # Continuous enemy processing if needed (already done after each player action)
        game.render(screen, pygame.font.Font(None, 24))
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()