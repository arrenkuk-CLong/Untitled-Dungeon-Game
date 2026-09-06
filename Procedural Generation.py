#Untitled Dungeon Game
#Developed by CapTen 
#Game Genre: 2D turn-based dungeon crawler
#------------------------------------------
#Learn: Save/load systems (JSON)
#Learn: Procedural generation (dungeon gen)
#Learn: User Experience (game feel particle effect)

import pygame, random, sys
from pygame.locals import *
pygame.init()

WIDTH = 1080
HEIGHT = 720
TILE_SIZE = 32
DUNGEON_WIDTH = 40
DUNGEON_HEIGHT = 30
FPS = 60

#Roomm limits
ROOM_MIN = 4
ROOM_MAX = 8
MAX_ROOMS = 30

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

'''
#Room generation & detect intersection 
class Room: 
    def __init__(self, x, y, w, h):
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + w, y + h
        self.cx, self.cy = (self.x1 + w // 2), (self.y1 + h // 2) 

    def intersects(self, other): #Return if these x/ypos statements are true
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1) 

    def inner (self): #Return inner rect
        return (self.x1 + 1, self.x2 + 1), (self.y1 + 1, self.y2 + 1) #Tuple
'''

# =====================================================================
# PROCEDURAL GENERATION - "the blog"
# ---------------------------------------------------------------------
# READ ME FIRST. Procedural generation (procgen) = the computer builds
# the level instead of me hand-drawing it. Every generator, no matter how
# fancy, is the same four steps:
#
#   1. START FROM SOLID ROCK.
#      The map is a 2D grid where every cell is wall (1). Generating a
#      dungeon means CARVING (setting cells to floor, 0). It is easier to
#      dig holes than to build walls, because a hole can't be "half built".
#
#   2. PLACE ROOMS (the "where do things happen" step).
#      Two ways are implemented below:
#        a) "random"  - throw random rectangles at the map, keep the ones
#                       that don't overlap. Dead simple, slightly messy,
#                       leaves big empty patches. This is how Rogue (1980)
#                       and most beginner roguelikes do it.
#        b) "bsp"     - Binary Space Partitioning: take the whole map,
#                       slice it in two, slice each half in two, keep
#                       slicing until the pieces are room-sized, then put
#                       one room inside each piece. Because the pieces
#                       never overlap, the rooms can never overlap, and
#                       the map gets used evenly. This is how Nethack-ish
#                       and most modern dungeon generators do it.
#
#   3. CONNECT ROOMS (the "can the player actually get there" step).
#      Rooms with no corridors are just floating boxes. Corridor styles:
#        "L"     - go horizontal then vertical. Clean, readable, classic.
#        "drunk" - a random walk that stumbles toward the target
#                  ("drunkard's walk"). Organic, cave-like, wastes space.
#      Connection ORDER matters too:
#        "sequential" - room 0 to room 1 to room 2 ... (long snake, can look
#                       like spaghetti crossing the whole map)
#        "nearest"    - grow a connected blob: always link the closest
#                       room that isn't connected yet. This is a Minimum
#                       Spanning Tree, and it produces short, tidy halls.
#      A pure tree has NO loops, so the player always backtracks the same
#      way. "extra_connections" adds a few spare links on purpose, which
#      turns the level into a graph with cycles - much better to explore.
#
#   4. VALIDATE + DECORATE (the step beginners skip and then wonder why
#      the game is broken).
#      Random data is allowed to be garbage, so never trust it. Below I
#      flood fill (BFS) from the player's start tile:
#        - anything unreachable gets filled back in with rock, so the
#          player can never see a room they cannot enter,
#        - the SAME flood fill gives me the distance to every tile, so the
#          exit stairs get placed in the room that is FARTHEST away from
#          the start. Free level pacing: the exit is never next door.
#
# THE GOLDEN RULE: seed everything.
#   random.Random(seed) is a private dice cup. Same seed => byte-identical
#   dungeon, every single run. That is how you reproduce a bug report, how
#   "daily challenge" levels work, and how a save file can store one small
#   number instead of a whole map.
# =====================================================================


# TILE CODES - the map is just ints, the renderer decides what they look like
WALL   = 1   # solid rock, blocks movement
FLOOR  = 0   # walkable (0 = floor keeps it consistent with the prototype)
DOOR   = 2   # walkable, drawn differently, hook for locked/secret doors
ENTER  = 3   # up-stairs / player spawn
EXIT   = 4   # down-stairs / next level

WALKABLE = (FLOOR, DOOR, ENTER, EXIT)   # one place to ask "can I step here?"


# ---------------------------------------------------------------------
# THE TOGGLE PANEL - flip these and re-run. Every switch is one concept.
# (In the live demo below you can also flip them with the keyboard.)
# ---------------------------------------------------------------------
GEN_CONFIG = {
    "seed":              None,        # None = new dungeon each run, int = same dungeon forever
    "width":             DUNGEON_WIDTH,
    "height":            DUNGEON_HEIGHT,

    "algorithm":         "bsp",       # "random" | "bsp"
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
    "place_stairs":      True,        # entrance in first room, exit in the farthest room
}


# ---------------------------------------------------------------------
# STEP 2a - THE ROOM
# A room is only 4 numbers. x1,y1 = top-left FLOOR tile, x2,y2 = bottom-right
# FLOOR tile (both inclusive). The walls are simply the rock we never carved,
# which is why rooms are always kept 1 tile away from the map border.
# ---------------------------------------------------------------------
class Room:
    def __init__(self, x, y, w, h):
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + w - 1, y + h - 1     # inclusive, so w tiles wide
        self.cx, self.cy = x + w // 2, y + h // 2   # center = where corridors aim

    @property
    def w(self):
        return self.x2 - self.x1 + 1

    @property
    def h(self):
        return self.y2 - self.y1 + 1

    def intersects(self, other, padding=0):
        # Axis-Aligned Bounding Box test: two rectangles overlap unless one is
        # fully left/right/above/below the other. Padding grows this room by N
        # tiles first, so "no overlap" becomes "at least N rock tiles between us".
        return (self.x1 - padding <= other.x2 and self.x2 + padding >= other.x1 and
                self.y1 - padding <= other.y2 and self.y2 + padding >= other.y1)

    def contains(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def random_spot(self, rng):
        # Where to drop a chest / enemy / trap without it ending up in a wall.
        return rng.randint(self.x1, self.x2), rng.randint(self.y1, self.y2)


# ---------------------------------------------------------------------
# STEP 1 - THE MAP ITSELF
# dungeon.tiles[x][y] (column-major, same as the prototype's dungeon[x][y]).
# Every carving helper lives here so no algorithm below ever touches the
# raw list - that is what stops "index out of range" crashes at 2am.
# ---------------------------------------------------------------------
class Dungeon:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.tiles = [[WALL for _ in range(height)] for _ in range(width)]  # solid rock
        self.rooms = []       #Store room idxs
        self.start = (0, 0)   # where the player spawns
        self.exit = None      # where the stairs down are
        self.seed = None      # remembered so a level can be saved as one number

    def in_bounds(self, x, y):
        # The outer ring is deliberately excluded: a map needs a wall around it,
        # otherwise a corridor can be carved off the edge of the world.
        return 1 <= x < self.width - 1 and 1 <= y < self.height - 1

    def is_walkable(self, x, y):
        return self.in_bounds(x, y) and self.tiles[x][y] in WALKABLE
    
    def carve(self, x, y, tile=FLOOR):
        if self.in_bounds(x, y):
            self.tiles[x][y] = tile

    def carve_room(self, room):
        for x in range(room.x1, room.x2 + 1):
            for y in range(room.y1, room.y2 + 1):
                self.carve(x, y)

    def room_at(self, x, y):
        for room in self.rooms:
            if room.contains(x, y):
                return room
        return None

    def neighbours4(self, x, y):
        # Orthogonal only. Diagonals are excluded on purpose: if the player
        # can't move diagonally, the generator must not think diagonally either,
        # or it will "connect" two rooms through a corner the player can't cross.
        return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) #East, west, North, South


# ---------------------------------------------------------------------
# STEP 2b - ROOM PLACEMENT, ALGORITHM 1: "random" (throw darts)
# Try max_rooms times: roll a random size, roll a random position, and keep
# the room only if it doesn't touch anything already placed. Rejected rolls
# are simply thrown away - this is called REJECTION SAMPLING, and it is the
# cheapest procgen tool there is. Cost: the map ends up patchy, and asking
# for more rooms than fit just wastes rolls (it never loops forever).
# ---------------------------------------------------------------------
def place_rooms_random(dungeon, rng, cfg):
    for _ in range(cfg["max_rooms"]): # 4 to 8 rooms
        w = rng.randint(cfg["room_min"], cfg["room_max"]) 
        h = rng.randint(cfg["room_min"], cfg["room_max"])
        x = rng.randint(1, dungeon.width - w - 1)    # -1 keeps the border wall intact
        y = rng.randint(1, dungeon.height - h - 1)
        new_room = Room(x, y, w, h)

        if any(new_room.intersects(r, cfg["room_padding"]) for r in dungeon.rooms):
            continue                                 # rejected, roll again
        dungeon.rooms.append(new_room)
        dungeon.carve_room(new_room)


# ---------------------------------------------------------------------
# STEP 2c - ROOM PLACEMENT, ALGORITHM 2: "bsp" (slice the map up)
# Binary Space Partitioning. Recursion in three lines of English:
#   - if this rectangle is still big enough and I have splits left,
#     cut it into two children (along its longer axis so rooms stay squarish)
#     and recurse into both;
#   - otherwise this rectangle is a leaf, so shrink it a bit and call it a room.
# Because sibling rectangles never overlap, neither can the rooms inside them.
# That is the whole trick, and it's why BSP maps feel evenly used.
# ---------------------------------------------------------------------
def place_rooms_bsp(dungeon, rng, cfg): #Dungeon, seed, config
    pad = cfg["room_padding"]
    min_side = cfg["room_min"] + pad * 2 + 1   # a slice must fit a room + its rock

    def split(x, y, w, h, depth):
        # --- base case: this slice becomes one room -------------------
        too_small = (w < min_side * 2 and h < min_side * 2)
        if depth <= 0 or too_small:
            rw = min(cfg["room_max"], max(cfg["room_min"], w - pad * 2))
            rh = min(cfg["room_max"], max(cfg["room_min"], h - pad * 2))
            if rw < 1 or rh < 1 or rw > w or rh > h:
                return                                   # slice too thin, skip it
            rx = rng.randint(x, x + w - rw)              # jitter inside the slice
            ry = rng.randint(y, y + h - rh)              # so rooms aren't all centered
            dungeon.rooms.append(Room(rx, ry, rw, rh))
            return

        # --- recursive case: cut along the longer axis ----------------
        can_h = h >= min_side * 2      # is there room to cut top/bottom?
        can_v = w >= min_side * 2      # ...or left/right?
        if can_h and can_v:
            # both cuts legal: prefer the long axis, coin-flip when it's square-ish
            horizontal = h > w if abs(w - h) > 2 else rng.random() < 0.5
        else:
            horizontal = can_h         # only one legal cut left, take it
        if horizontal:
            cut = rng.randint(min_side, h - min_side)     # never cut off a sliver
            split(x, y, w, cut, depth - 1)
            split(x, y + cut, w, h - cut, depth - 1)
        else:
            cut = rng.randint(min_side, w - min_side)
            split(x, y, cut, h, depth - 1)
            split(x + cut, y, w - cut, h, depth - 1)

    split(1, 1, dungeon.width - 2, dungeon.height - 2, cfg["bsp_depth"])
    for room in dungeon.rooms:
        dungeon.carve_room(room)


# ---------------------------------------------------------------------
# STEP 3a - CORRIDORS
# A corridor is just "carve every tile along a path". The path is the only
# thing that changes between styles.
# ---------------------------------------------------------------------
def carve_h_corridor(dungeon, x1, x2, y, wide):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        dungeon.carve(x, y)
        if wide:
            dungeon.carve(x, y + 1)      # second lane, for chunky sprites


def carve_v_corridor(dungeon, y1, y2, x, wide): 
    for y in range(min(y1, y2), max(y1, y2) + 1):
        dungeon.carve(x, y)
        if wide:
            dungeon.carve(x + 1, y)


def carve_L_corridor(dungeon, a, b, rng, wide):
    # Classic L: all the way across, then all the way down (or the mirror
    # image). Flipping a coin on the order is what stops every hallway in the
    # dungeon from bending the same direction, which is an instant "this was
    # generated by a computer" tell.
    # CapTen Note: accomodating neighbor room space
    if rng.random() < 0.5:
        carve_h_corridor(dungeon, a.cx, b.cx, a.cy, wide) 
        carve_v_corridor(dungeon, a.cy, b.cy, b.cx, wide)
    else:
        carve_v_corridor(dungeon, a.cy, b.cy, a.cx, wide) 
        carve_h_corridor(dungeon, a.cx, b.cx, b.cy, wide)


def carve_drunk_corridor(dungeon, a, b, rng, wide):
    # Drunkard's walk: step toward the target MOST of the time, and stumble
    # sideways the rest of the time. The bias (0.7) is the whole design knob:
    #   1.0 = a boring straight L,  0.5 = it may never arrive.
    # Kept honest with a step budget, because "random" and "terminates" are
    # not the same promise. If it runs out, we finish with a straight line so
    # the two rooms are guaranteed connected either way.
    # a room center to b room center is the start and end of drunk walk.
    x, y = a.cx, a.cy
    budget = (abs(a.cx - b.cx) + abs(a.cy - b.cy)) * 6 + 40
    while (x, y) != (b.cx, b.cy) and budget > 0: 
        budget -= 1 #Total budget - 1 tile spent per iteration
        dungeon.carve(x, y) #carve/build corridor tile
        if wide:
            dungeon.carve(x + 1, y)
        if rng.random() < 0.7:                       # sober step: close the gap
            if rng.random() < 0.5 and x != b.cx:     # Randomly choose which axis to pave first, under padding restrictions
                x += 1 if b.cx > x else -1
            elif y != b.cy:
                y += 1 if b.cy > y else -1
            else:
                x += 1 if b.cx > x else -1
        else:                                        # drunk step: wander
            x, y = rng.choice(dungeon.neighbours4(x, y))
        x = max(1, min(dungeon.width - 2, x))        # clamp: never leave the map
        y = max(1, min(dungeon.height - 2, y))
    if (x, y) != (b.cx, b.cy):                       #run out of budget, finish with straight line
        carve_L_corridor(dungeon, Room(x, y, 1, 1), b, rng, wide)


def connect(dungeon, a, b, rng, cfg):
    if cfg["corridor_style"] == "drunk":
        carve_drunk_corridor(dungeon, a, b, rng, cfg["wide_corridors"])
    else:
        carve_L_corridor(dungeon, a, b, rng, cfg["wide_corridors"])


# ---------------------------------------------------------------------
# STEP 3b - CONNECTION ORDER (this is graph theory wearing a hat)
# "sequential": link room i to room i-1. One long snake. Cheap, and on a
#               random layout the halls cross the whole map like spaghetti.
# "nearest":    start with one room "connected", then repeatedly link the
#               closest still-unconnected room to the blob. That is Prim's
#               algorithm building a Minimum Spanning Tree: every room is
#               reachable, using the shortest total corridor length, and with
#               exactly (rooms - 1) corridors and zero loops.
# Then "extra_connections" deliberately adds loops back in, because a perfect
# tree means every dead end must be walked twice. Loops are good level design.
# ---------------------------------------------------------------------
def connect_rooms(dungeon, rng, cfg):
    rooms = dungeon.rooms   #copy list of rooms to local func var
    if len(rooms) < 2: 
        return              #Return func if no rooms nearby

    if cfg["connect_order"] == "sequential":    #sapghetti style, room 0 to room 1 to room 2...
        for i in range(1, len(rooms)):          #Skip room 0
            connect(dungeon, rooms[i - 1], rooms[i], rng, cfg) 
    else:
        def dist(a, b):
            # Manhattan distance: corridors only move in straight lines, so
            # |dx| + |dy| is the REAL cost. Using straight-line distance here
            # would be measuring a path the digger cannot dig.
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


# ---------------------------------------------------------------------
# STEP 4a - DOORS (decoration, but it teaches "find the interesting tiles")
# A door belongs on a corridor tile that touches a room. So: look at every
# floor tile that is NOT in a room, and if it has a room tile next to it,
# it is a doorway. The extra check stops a 2-wide corridor from producing a
# clump of five doors in a row.
# ---------------------------------------------------------------------
def place_doors(dungeon):
    for x in range(1, dungeon.width - 1):
        for y in range(1, dungeon.height - 1):
            if dungeon.tiles[x][y] != FLOOR or dungeon.room_at(x, y):   #ignore if not floor tile or already in room
                continue
            touches_room = any(dungeon.room_at(nx, ny)
                               for nx, ny in dungeon.neighbours4(x, y)) #check qualified neighbors for door
            already_doored = any(dungeon.tiles[nx][ny] == DOOR
                                 for nx, ny in dungeon.neighbours4(x, y))
            if touches_room and not already_doored:
                dungeon.tiles[x][y] = DOOR


# ---------------------------------------------------------------------
# STEP 4b - FLOOD FILL / BFS (the most useful 15 lines in this file)
# Breadth-First Search from the start tile. Walk outward one ring at a time,
# writing down how many steps each tile took. Because every ring is one step
# further than the last, the number you write down IS the shortest path length.
# It answers three questions at once:
#   "is the level fully connected?"  -> did BFS reach every floor tile?
#   "what do I fill back in?"        -> everything it did NOT reach
#   "where should the exit go?"      -> the tile with the biggest number
# The same routine drives enemy pathfinding later on.
# ---------------------------------------------------------------------
def flood_fill(dungeon, start):
    distances = {start: 0} #dist of starting tile = 0
    queue = [start]
    head = 0
    while head < len(queue):                 # index instead of pop(0): pop(0) - euns while there are still unexamined cords
        x, y = queue[head]                   # is O(n) and turns BFS into O(n^2)
        head += 1
        for nx, ny in dungeon.neighbours4(x, y):    #Loops through the four neighbors of the current tile
            if (nx, ny) not in distances and dungeon.is_walkable(nx, ny):
                distances[(nx, ny)] = distances[(x, y)] + 1     #Record distance
                queue.append((nx, ny))  #next set of coordinates to examine
    return distances


# ---------------------------------------------------------------------
# THE CONDUCTOR - runs the four steps in order and hands back a finished map.
#   dungeon = generate_dungeon()                       # use GEN_CONFIG as-is
#   dungeon = generate_dungeon({"algorithm": "random"})# override just one switch
#   dungeon = generate_dungeon(seed=1234)              # same map every time
# ---------------------------------------------------------------------
def generate_dungeon(config=None, seed=None):
    cfg = dict(GEN_CONFIG)                 # copy, so a caller's override is
    if config:                             # never allowed to leak into the
        cfg.update(config)                 # global defaults

    # One dice cup for the whole level. Nothing below is allowed to call
    # random.* directly - if it did, the seed would stop reproducing the map.
    if seed is None:
        seed = cfg["seed"] if cfg["seed"] is not None else random.randrange(2**31)
    rng = random.Random(seed) 

    dungeon = Dungeon(cfg["width"], cfg["height"])
    dungeon.seed = seed

    # 1 + 2 - solid rock, then rooms
    if cfg["algorithm"] == "random":
        place_rooms_random(dungeon, rng, cfg)
    else:
        place_rooms_bsp(dungeon, rng, cfg)

    if not dungeon.rooms:                  # paranoia: a config with huge rooms on
        room = Room(1, 1, min(cfg["room_min"], cfg["width"] - 2),   # a tiny map can
                    min(cfg["room_min"], cfg["height"] - 2))        # place nothing.
        dungeon.rooms.append(room)         # A game must never get a mapless level.
        dungeon.carve_room(room)           #Reduce width and height accordingly for room size

    # 3 - corridors
    connect_rooms(dungeon, rng, cfg)

    # 4 - validate and decorate
    if cfg["place_doors"] and not cfg["wide_corridors"]:    #No doors on 2-tile wide corridors
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

    return dungeon


# ---------------------------------------------------------------------
# DEBUG VIEW - print the map as text. Do this BEFORE writing any rendering
# code: if the ASCII looks wrong, the bug is in the generator, not the art.
# ---------------------------------------------------------------------
ASCII_TILES = {WALL: '#', FLOOR: '.', DOOR: '+', ENTER: '<', EXIT: '>'}


def ascii_render(dungeon):
    lines = []
    for y in range(dungeon.height):                       # rows are y...
        lines.append(''.join(ASCII_TILES[dungeon.tiles[x][y]]
                             for x in range(dungeon.width)))   # ...columns are x
    return '\n'.join(lines)


# =====================================================================
# LIVE DEMO - see every toggle change the dungeon, instantly.
# Run this file directly:  python "Untitled Dungeon Game.py"
# Nothing below is needed by the game itself; it is a teaching harness.
# The point of it: procgen is tuned by LOOKING at hundreds of maps, so the
# fastest way to understand a knob is to hold it and watch the map react.
# =====================================================================
TILE_COLORS = {
    WALL:  DARK_GREY,
    FLOOR: GREY,
    DOOR:  BROWN,
    ENTER: LIGHT_BLUE,
    EXIT:  YELLOW,
}

# key -> (config field, list of values to cycle through)
TOGGLE_KEYS = {
    K_1: ("algorithm",         ["bsp", "random"]),
    K_2: ("corridor_style",    ["L", "drunk"]),
    K_3: ("connect_order",     ["nearest", "sequential"]),
    K_4: ("extra_connections", [0, 1, 2, 4, 8]),
    K_5: ("wide_corridors",    [False, True]),
    K_6: ("place_doors",       [True, False]),
    K_7: ("prune_unreachable", [True, False]),
    K_8: ("bsp_depth",         [2, 3, 4, 5]),
    K_9: ("max_rooms",         [10, 20, 30, 60]),
    K_0: ("room_max",          [5, 6, 8, 10]),
}

HELP_LINES = [
    "SPACE  new dungeon (new seed)",
    "R      re-roll SAME seed",
    "TAB    print ASCII map to console",
    "ESC    quit",
    "",
    "1 algorithm          2 corridors",
    "3 connect order      4 extra links",
    "5 wide halls         6 doors",
    "7 prune islands      8 bsp depth",
    "9 max rooms          0 room size",
]


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
    # Outline each room so the room-vs-corridor split is obvious at a glance.
    for room in dungeon.rooms:
        pygame.draw.rect(screen, GREEN,
                         pygame.Rect(room.x1 * tile_px, room.y1 * tile_px,
                                     room.w * tile_px, room.h * tile_px), 1)


def draw_panel(screen, font, cfg, dungeon, x0):
    pygame.draw.rect(screen, BLACK, pygame.Rect(x0, 0, WIDTH - x0, HEIGHT))
    y = 10

    def line(text, color=WHITE):
        nonlocal y
        screen.blit(font.render(text, True, color), (x0 + 12, y))
        y += 20

    line("PROC-GEN SANDBOX", YELLOW)
    line("seed %d" % dungeon.seed, LIGHT_BLUE)
    line("rooms %d" % len(dungeon.rooms), LIGHT_BLUE)
    y += 8
    for key in sorted(TOGGLE_KEYS):
        field, _ = TOGGLE_KEYS[key]
        line("%-18s %s" % (field, cfg[field]), GREEN)
    y += 10
    for text in HELP_LINES:
        line(text, GREY)


def run_demo():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Untitled Dungeon Game - procedural generation sandbox")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 15)

    cfg = dict(GEN_CONFIG)
    panel_x = WIDTH - 320
    tile_px = min(panel_x // cfg["width"], HEIGHT // cfg["height"])
    dungeon = generate_dungeon(cfg)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key in (K_ESCAPE, K_q):
                    running = False
                elif event.key == K_SPACE:
                    dungeon = generate_dungeon(cfg)                 # fresh seed
                elif event.key == K_r:
                    dungeon = generate_dungeon(cfg, seed=dungeon.seed)  # same map,
                elif event.key == K_TAB:                            # proves seeding
                    print("seed %d\n%s" % (dungeon.seed, ascii_render(dungeon)))
                elif event.key in TOGGLE_KEYS:
                    field, values = TOGGLE_KEYS[event.key]
                    cycle(cfg, field, values)
                    # Same seed, one switch flipped: now the change you see on
                    # screen is caused by the TOGGLE and nothing else. Changing
                    # two variables at once teaches you nothing.
                    dungeon = generate_dungeon(cfg, seed=dungeon.seed)

        screen.fill(BLACK)
        draw_dungeon(screen, dungeon, tile_px)
        draw_panel(screen, font, cfg, dungeon, panel_x)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_demo()