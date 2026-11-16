#exploration
#enter dungeon, place enemies & items, player and enemy movement.

from scripts import Dungeongen, Inv
from collections import deque
from scripts.config import GEN_CONFIG
from scripts.gamestate import State

#=====================================================================
#Dungeon exploration functions
#----------------------------------------------------------------------
#enter_dungeon()  - generate a floor, spawn eyeballs, drop the player on '<'
#enemy_at()       - define enemy pos (moves)
#item_at()        - define item pos
#move_player()    - one tile per keypress (turn-based, same as the combat).
#                   Walking into an eyeball starts a battle, walking onto the
#                   stairs generates the next floor
#move_enemy()
#======================================================================

#Fresh seed
def enter_dungeon(game, level = 1):
    game.dungeon_level = level
    game.dungeon = Dungeongen.generate_dungeon(GEN_CONFIG)      
    game.dungeon_enemies = Dungeongen.spawn_enemies(game.dungeon, GEN_CONFIG)
    game.dungeon_items = Dungeongen.spawn_items(game.dungeon, GEN_CONFIG)    

    game.player_tile = game.dungeon.start                 #dungeon.start is room 0's centre

    game.state = State.Explore

    #UI
    game.message = (f'Floor {game.dungeon_level} - {len(game.dungeon_enemies)} eyes, '
                    f'{len(game.dungeon_items)} items. Find the gold stairs.')
    print(f'--- floor {game.dungeon_level}, seed {game.dungeon.seed} ---')
    #ascii_render was left behind in the split - add it back to Dungeongen.py if
    #you want the terminal map check again

#define enemy coordinates
def enemy_at(game, x, y):
    for foe in game.dungeon_enemies:
        if foe['x'] == x and foe['y'] == y:
            return foe
    return None

#Define item coordinates
def item_at(game, x, y):
    for i in game.dungeon_items:
        if i['x'] == x and i['y'] == y:
            return i
    return None

def move_player(game, dx, dy):
    x, y = game.player_tile[0] + dx, game.player_tile[1] + dy

    if not game.dungeon.is_walkable(x, y):   #Walls
        return                          
                                        
    game.player_tile = (x, y)

    foe = enemy_at(game, x, y)
    if foe:
        return foe

    loot = item_at(game, x, y)
    if loot:
        game.dungeon_items.remove(loot)      
        game.message = game.inventory.add_item(loot['name'])

    if game.dungeon.tiles[x][y] == Dungeongen.EXIT:
        enter_dungeon(game, game.dungeon_level + 1)
        return

    move_enemy(game)

def move_enemy(game):
    """Move each exploration enemy one walkable tile toward the player."""
    occupied = {(foe['x'], foe['y']) for foe in game.dungeon_enemies}
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))

    #Shadow Cloak halves it, Invisibility Potion takes it to 0
    fov_radius = int(GEN_CONFIG['enemy_fov_radius'] * Inv.buff_strength(game, 'hide'))

    for foe in game.dungeon_enemies:
        start = (foe['x'], foe['y'])
        occupied.discard(start)

        distance = abs(start[0] - game.player_tile[0]) + abs(start[1] - game.player_tile[1])
        if distance > fov_radius:
            occupied.add(start)
            continue

        queue = deque([start])
        previous = {start: None}

        while queue and game.player_tile not in previous:
            current_x, current_y = queue.popleft()
            for step_x, step_y in directions:
                next_tile = (current_x + step_x, current_y + step_y)
                if next_tile in previous or not game.dungeon.is_walkable(*next_tile):
                    continue
                if next_tile in occupied and next_tile != game.player_tile:
                    continue
                previous[next_tile] = (current_x, current_y)
                queue.append(next_tile)

        if game.player_tile not in previous:
            occupied.add(start)
            continue

        next_tile = game.player_tile
        while previous[next_tile] != start:
            next_tile = previous[next_tile]
        if next_tile != game.player_tile and next_tile not in occupied:
            foe['x'], foe['y'] = next_tile
            occupied.add(next_tile)
        else:
            occupied.add(start)

