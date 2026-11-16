#config
DUNGEON_WIDTH = 40      #Map size in TILES, not pixels
DUNGEON_HEIGHT = 30
TILE_SIZE = 32
#Side effect:
#Side effect worth knowing: at 32px your 40×30 map is 1280×960, larger than the 1080×720 window. 
# That’s fine — your camera already follows the player and FOV only draws a radius — but MAP_OFF_X 
# on config.py:11 is computed from the full map width and will go negative. 
# It’s unused in the camera path, so check whether anything still reads it.

MAX_ROOMS = 30
ROOM_MIN = 4
ROOM_MAX = 8
WIDTH = 1080
HEIGHT = 720
#Camera
MAP_OFF_X = (WIDTH - 40 * TILE_SIZE) // 2    #40 = DUNGEON_WIDTH
MAP_OFF_Y = 0

#Items (Explore mode) - JSON
#Icon sprites only, see ITEM_EFFECTS in inv.py for their actual usage.
ITEM_SPRITE_MAP = {
    "Health Potion": "health_potion.png",
    "Greater Health Potion": "greater_health_potion.png",
    "Shadow Cloak" : "shadow_cloak.png",
    "Invisibility Potion" : "invis_potion.png",
    "XP Scroll" : "xp_scroll.png",
    "Teleportation Scroll" : "teleportation_scroll.png"
    #"Strength Scroll": "strength_scroll",
    #"Defense Scroll": "strength_scroll",
    #"Speed Boots": "armor",
    #"Ring of Regeneration": "armor",
}

#Enemies (Explore State)
ENEMY_SPRITE_MAP = {
    "Eye": "Mini_Eye.png",          #Wolf level
    "Skeleton": "Mini_Skele.png",   #Tiger level
    "Ghoul": "Mini_Ghoul.png",      #Demon level - resistant against Physical attacks
    "Fallen": "Mini_Fallen.png",    #Demon level - resistant against magic attacks
    "Wraith": "Mini_Wraith.png"     #Dragon level - resistant against both, spawns on the tenth floor. Larger size (maybe 64 x 64) 
}

PLAYER_SPRITE_MAP = {
    "Sword" : "Mini_Sword.png",
    "Wizard" : "Mini_Wizard.png",
    "Archer" : "Mini_Archer.png"
}


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
    "enemy_fov_radius":  6,           # enemies only chase when this close to the player
    "item_chance":       0.4,
}