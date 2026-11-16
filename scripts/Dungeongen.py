#dungeon
#dungeon
import random
from scripts.config import GEN_CONFIG, ITEM_SPRITE_MAP, ENEMY_SPRITE_MAP

WALL = 1 
FLOOR = 0  
DOOR = 2
ENTER = 3 #Player spawn
EXIT = 4
WALKABLE = (FLOOR, DOOR, ENTER, EXIT)   

#Add decoration, separate by roof, floor, and Wall_Front
TILE_MISC = {
   'Bones' : {'surface': 'Floor', 'chance' : 0.02},
   'Candles' : {'surface': 'Floor', 'chance' : 0.04},
   'Crack' : {'surface' : 'Wall_Front', 'chance': 0.10},
   'Vines' : {'surface': 'Wall_Front', 'chance': 0.10},
   'Vent' : {'surface': 'Wall_Other', 'chance': 0.025}
}

#Room - Store room specific data and prevent overlap
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

#Dungeon - Stores the entire map (tiles, rooms, width, height)
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
    
    def is_solid(self, x, y):
            #off-map counts as solid, so the map border draws as roof, not as a face
            if not (0 <= x < self.width and 0 <= y < self.height):
                return True
            return self.tiles[x][y] == WALL

    def wall_sprite(self, x, y):
        if not self.is_solid(x, y + 1): #If the tile above floor is a wall
            return 'Wall_Front'
        if not self.is_solid(x - 1, y) and not self.is_solid(x + 1, y):  #Both sides, return if there are two separate rooms/corridors one tile-apart.
            return 'Wall_Bothsides'
        if not self.is_solid(x + 1, y): #left side
            return 'Wall_Side'
        if not self.is_solid(x - 1, y):  #Right side
            return 'Wall_Sidetwo'
        else:
            return 'Wall_Other'


#=====================================================================
#Procedural Generation functions & Methods 
#----------------------------------------------------------------------
#Bsp place rooms
#Drunk corridor style
#Room connection algorithm (nearest)
#Flood Fill (BFS)
#Generate dungeon - main func

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
    if rng.random() < 0.5: #hallway bends different ways by chance
        h_corridor(dungeon, a.cx, b.cx, a.cy, wide)
        v_corridor(dungeon, a.cy, b.cy, b.cx, wide)
    else:
        v_corridor(dungeon, a.cy, b.cy, a.cx, wide)
        h_corridor(dungeon, a.cx, b.cx, b.cy, wide)

def drunk_corridor(dungeon, a, b, rng, wide):
    #room a --> room b
    x, y = a.cx, a.cy
    budget = (abs(a.cx - b.cx) + abs(a.cy - b.cy)) * 6 + 40 #Step budget
    while (x, y) != (b.cx, b.cy) and budget > 0:
        budget -= 1
        dungeon.carve(x, y)         #Carve where we ARE
        if wide:                    
            dungeon.carve(x + 1, y) 
        if rng.random() < 0.7:      
            if rng.random() < 0.5 and x != b.cx: 
                x += 1 if b.cx > x else -1
            elif y != b.cy:
                y += 1 if b.cy > y else -1
            else:
                x += 1 if b.cx > x else -1
        else:                       
            x, y = rng.choice(dungeon.neighbours4(x, y))
        #Clamp EVERY step
        x = max(1, min(dungeon.width - 2, x))
        y = max(1, min(dungeon.height - 2, y))
    #Out of budget
    if (x, y) != (b.cx, b.cy):
        L_corridor(dungeon, Room(x, y, 1, 1), b, rng, wide)

def connect(dungeon, a, b, rng, cfg):
    if cfg["corridor_style"] == "drunk":
        drunk_corridor(dungeon, a, b, rng, cfg["wide_corridors"])
    else:
        L_corridor(dungeon, a, b, rng, cfg["wide_corridors"])

#Nearest connection
def connect_rooms(dungeon, rng, cfg):
    rooms = dungeon.rooms   
    if len(rooms) < 2:      #If no rooms nearby
        return              
    # Manhattan distance:
    else:
        def dist(a, b):
            return abs(a.cx - b.cx) + abs(a.cy - b.cy) 

        #Iterate and connect all rooms by finding the closest room to the linked list
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

    for _ in range(cfg["extra_connections"]):# extra hallways
        a, b = rng.sample(rooms, 2)         
        connect(dungeon, a, b, rng, cfg)

def flood_fill(dungeon, start):
    distance = {start: 0}       #starting Tile, distance
    queue = [start]             
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

#every floor tile that is NOT inside a room but 
#has a room tile next to it is a doorway
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

    place_rooms_bsp(dungeon, rng, cfg)

    if not dungeon.rooms:                  
        room = Room(1, 1, min(cfg["room_min"], cfg["width"] - 2),   
                    min(cfg["room_min"], cfg["height"] - 2))        
        dungeon.rooms.append(room)         
        dungeon.carve_room(room)           

    #corridors
    connect_rooms(dungeon, rng, cfg)

    #decorate
    if cfg["place_doors"]:
        place_doors(dungeon)    
                                
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
    
    dungeon.decor = {}          #(x, y) -> decoration name
    for x in range(dungeon.width):
        for y in range(dungeon.height):
            if dungeon.tiles[x][y] in WALKABLE: #floor
                surface = 'Floor'
            else:
                surface = dungeon.wall_sprite(x, y)
            for name, spec in TILE_MISC.items():
                if spec['surface'] == surface and dungeon.rng.random() < spec['chance']:
                    dungeon.decor[(x, y)] = name
                    break
    return dungeon


#Placing Enemies and items
#spawn_enemies()  - one roll per room, using the floor's OWN seeded rng so the
#                   same seed gives the same monsters as well as the same map
#(Special events & bosses soon)
def spawn_enemies(dungeon, cfg):
    enemies = []
    enemy_type = next(iter(ENEMY_SPRITE_MAP))
    for room in dungeon.rooms[1:]: #Skip room 0
        if dungeon.rng.random() < cfg['enemy_chance']:
            x, y = room.random_spot(dungeon.rng)
            if (x, y) != dungeon.start and (x, y) != dungeon.exit:
                enemies.append({'x': x, 'y': y, 'name': enemy_type})
    return enemies #Return # of enemies 

def spawn_items(dungeon, cfg):
    items = []
    for room in dungeon.rooms[1:]:
        if dungeon.rng.random() < cfg['item_chance']:
            item_type = dungeon.rng.choice(list(ITEM_SPRITE_MAP.keys()))
            x, y = room.random_spot(dungeon.rng)
            if (x, y) != dungeon.start and (x, y) != dungeon.exit:
                items.append({'x' : x, 'y' : y, 'name' : item_type})
    return items


