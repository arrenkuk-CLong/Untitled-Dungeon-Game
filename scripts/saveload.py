#An empty slot has no run data.
#The player chooses that slot, then chooses a class.
#The game creates the player and dungeon.
#Save the live game into that slot.
#Save again whenever relevant gameplay changes, such as moving, collecting an item, defeating an enemy, or reaching another floor.

import json, os, tempfile, time
from scripts.gamestate import State, Game

SAVE_VERSION = 1
SLOTS = ("1", "2", "3")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #absolute path

APP_NAME = "UntitledDungeonGame"
if os.name == "nt":                                                                       #nt = new technology
    SAVE_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME) #looks for the folder in user directory
else:                                                                                     #Fallback (expanduser) home
    SAVE_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", APP_NAME)
os.makedirs(SAVE_DIR, exist_ok=True)
SAVE_FILE = os.path.join(SAVE_DIR, "savegame.json")                                       #glue all files


#Start if file is empty
def empty_save():
    return {"save_version": SAVE_VERSION, "slots": {s: None for s in SLOTS}}

#check file (cheat, missing, etc)
def read_save():
    try: 
        with open(SAVE_FILE, "r") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return empty_save()
    
    if not isinstance(data, dict) or not isinstance(data.get("slots"), dict):
        return empty_save()
    for s in SLOTS:
        data["slots"].setdefault(s, None)
    return data #1, 2, 3


#Save data
def save_game(game, slot):
    #add level/xp later
    slot = str(slot)
    if slot not in SLOTS:
        raise ValueError ("save slot must be one of %s, got %r" % (SLOTS, slot))
    data = read_save()
    data["save_version"] = SAVE_VERSION
    data["slots"][slot] = {
        "player" : {
            "class": game.player.name,  #game is checking for class but class doesn't exist on an empty file.
            "position": list(game.player_tile),     
            "health": game.player.health,          
            "health_max": game.player.health_max,      
            "exp": game.player.xp,
            "expcap": game.player.xpcap,
            "power": game.player.power,
        },
        "dungeon" : {
            "seed": game.dungeon.seed,
            "level": game.dungeon_level,       
            "enemies": [dict(enemy) for enemy in game.dungeon_enemies],
            "items": [dict(item) for item in game.dungeon_items]
        },
        "inventory" : {
            name: dict(item_data)
            for name, item_data in game.inventory.items.items()
        },
        "stats" : {
            "battles_won": game.battles_won,
            "dmg_dealt": game.dmg_dealt,
            "dmg_taken": game.dmg_taken,
            "buffs": game.active_buffs
        }
        }

    write_json(data)
def write_json(data):
    fd, temp = tempfile.mkstemp(dir=os.path.dirname(SAVE_FILE) or '.', suffix='tmp')
    try:
        with os.fdopen(fd, 'w') as file: # w = Overwrite
            json.dump(data, file, indent=4)
        for attempt in range(10):
            try:
                os.replace(temp, SAVE_FILE)
                return
            except PermissionError:
                if attempt == 9:
                    raise
                time.sleep(0.05)
    except BaseException:
        if os.path.exists(temp):
            os.remove(temp)
        raise

def load_game(slot):
    return read_save()["slots"].get(str(slot))


def death_slot(slot): #permadeath
    slot = str(slot)
    data = read_save()
    data["slots"][str(slot)] = None
    write_json(data)
    '''
    #overwrite to Null/None
    fd, temp = tempfile.mkstemp(dir=os.path.dirname(SAVE_FILE) or '.', suffix='tmp')
    try:
        with os.fdopen(fd, 'w') as file: 
            json.dump(data, file, indent=4)
        os.replace(temp, SAVE_FILE)

    except BaseException: 
        if os.path.exists(temp):
            os.replace(temp, SAVE_FILE)'''
