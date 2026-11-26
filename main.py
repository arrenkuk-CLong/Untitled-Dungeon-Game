#CapTen
#Untitled dungeon game 
#Checklist:
#TODO Make minifigures of players and enemy for dungeon exploration #(Made basic)
#TODO Add Moving enemies (within FOV Radius)
#TODO Debug turn-based damage and animation logic 
#TODO Test different attack animations 
#TODO Revamp Global variable soup (gamestate)
#TODO revamp entire codebase architecture
#TODO Full save and load Runs 
#TODO Permadeath implementation
#TODO Intermission screens (loading)
#TODO Add leveling / xp / progression system
#TODO Status and DOT effects
#TODO DETERMINE ART DIRECTION
#TODO Improve Dungeon Map graphics 
#TODO Improve Explore HUD
#TODO Icons (effects, player/enemy)
#TODO More Items and meaningful inventory use  
#TODO Icons (Items)
#TODO Map Shadows & FOV (masking)
#TODO Bresenham line algorihtm (basic raycasting)
#TODO Redraw Battle (character and enemy) assets (96x96 normal sprites, 128 x 128 bosses)
#TODO add Menu/leave game screen
#TODO Four more enemy types and a boss + assets
#---------------------------------------------------------------------------------- Finished
#TODO Improve Battle HUD
#TODO Map lighiting (lamp glows)
#TODO Add win condition & ending: ten floors, too much gems or too many kills + Boss spawn trigger
#TODO add menu/settings
#TODO Make Remaining assets: attack animations mostly
#TODO Implement McGill GameJam's advice
#---------------------------------------------------------------------------------- Due 27th 
#TODO Fix minor bugs: #Set health bar value (on reloading a save) | game message damage without considering multipliers. | Inventory doesn't reset on death | Enemy keeps playing the same move (no cd?) | Quit empties inventory but Rematch doesnt
#TODO Do remaining stat effects (most the cc ones)
#TODO Sound and music (I guess bro)
#TODO Improve visuals and polish (add fallback?)
#TODO Polish UI
#TODO Balancing and playtesting
#TODO Upload to itch.io 

import pygame, sys
from pygame.locals import *
pygame.init()

#Script imports and screen
from scripts.config import DUNGEON_WIDTH, WIDTH, HEIGHT, TILE_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('ClassBattle')
clock = pygame.time.Clock()

from scripts import Dungeongen, draw_load, entities, ui, Inv, exploration, battle, saveload
from scripts.gamestate import State, Game
from scripts.intermission import begin_intermission


MAP_OFF_X = (WIDTH - DUNGEON_WIDTH * TILE_SIZE) // 2    #40 = DUNGEON_WIDTH
MAP_OFF_Y = 0
FPS = 60


INTERMISSION_TIME = 1000  #ms


#Buttons
begin = ui.button(440, 500, 200, 60, "Begin") 
Rematch = ui.button(WIDTH//2 - 150, 500, 150, 60, "Rematch")
Quit = ui.button(WIDTH//2 + 20,  500, 150, 60, "Quit")

#User Interface
Bag = Inv.inventory_UI(712, 55, 300, 300, 'INVENTORY')
exp_bar = ui.XPBAR(50, 650)
game = Game() #Literally the entire game loop


#Battle HUD layout lives in ui.py (TURN_BOX, MSG_BOX, ENEMY_BOX, PLAYER_BOX
#use the old Box2-Box5 test rectangles)




#Explain this
def cycle(cfg, field, values):
    # Move to the next value in the list, wrapping around at the end.
    # (index + 1) % len is the whole "cycle through options" pattern.
    current = cfg[field]
    i = values.index(current) if current in values else -1
    cfg[field] = values[(i + 1) % len(values)]

#save/load callback
def load_slot(slot_num):
    #saveload.save_game(game, slot_num)
    data = saveload.load_game(slot_num)
    if data is None:
        return
    
    #parent dictionaries
    player_data = data["player"] 
    dungeon_data = data["dungeon"]
    game.selected_slot = slot_num 

    create_player(player_data["class"])
    game.player.health = player_data["health"]
    game.player.xp = player_data.get("exp", 0) #Default values
    game.player.xpcap = player_data.get("expcap", 10)
    game.player.power = player_data.get("power", 0)

    game.dungeon_level = dungeon_data["level"]
    game.dungeon = Dungeongen.generate_dungeon(seed=dungeon_data["seed"]) 
    game.player_tile = tuple(player_data["position"])
    game.dungeon_enemies = dungeon_data["enemies"] 
    game.dungeon_items = dungeon_data["items"]
    game.inventory.items = data.get("inventory", {})
    game.active_buffs = [dict(buff) for buff in data.get("stats", {}).get("buffs", [])] 
    begin_intermission(game, State.Explore)


def create_player(class_name):
    game.dmg_dealt = 0
    game.dmg_taken = 0
    game.battles_won = 0
    game.battle_won = False
    game.selected_class = class_name

    #Name, maxhealth, move list (index)
    if class_name == 'Sword':
        game.player = entities.Character("Sword", 110, entities.Sword_moves) 
        game.player_hpbar = ui.HPBAR(110) #VISUAL Bug
    elif class_name == 'Wizard':
        game.player = entities.Character("Wizard", 100, entities.Wizard_moves)
        game.player_hpbar = ui.HPBAR(100)
    elif class_name == 'Archer': 
        game.player = entities.Character("Archer", 95, entities.Archer_moves)
        game.player_hpbar = ui.HPBAR(95)
    game.player_anim = None
    game.player_idle_anim = None
    game.player_hpbar.set_char(game.player.name)
    game.item_icons = ui.BuffBar(50, 550)
    game.player_effects = ui.EffectsUI(game.player_hpbar)


#Reset the game for a brand new run on rematch or Run - change
def reset():
    game.state = State.Menu
    game.player = None
    game.enemy = None
    game.turn = 'player'
    game.enemy_acted = False
    game.message = ''
    game.dmg_dealt = 0
    game.dmg_taken = 0
    game.battle_won = False
    game.battles_won = 0
    #game.item_icons = None
    #Throw the whole floor away: a new run has to roll a new dungeon
    game.dungeon = None
    game.dungeon_enemies = []
    game.dungeon_items = []
    game.dungeon_level = 1
    game.current_encounter = None
    game.death_processed = False


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
last_save = None
Rungame = True
while Rungame: 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            Rungame = False

        if game.state == State.Menu:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if begin.is_clicked(pos):
                    game.state = State.slots                    

        elif game.state == State.slots: #Save/load application
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for slot_num, slot in enumerate(ui.slot_buttons, start = 1): #define slot_num as 1st index
                    if slot.is_clicked(pos): #return slot num-
                        data = saveload.load_game(slot_num)
                        if data is None: 
                            game.selected_slot = slot_num
                            game.state = State.selection
                        else:
                            load_slot(slot_num)
                        break
        
        elif game.state == State.selection:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for card in ui.class_cards:
                    if card.is_clicked(pos):
                        create_player(card.name)    
                        #exploration.enter_dungeon(1)            #Drop player on floor 1 - will change with JSON save files when implemented
                        exploration.enter_dungeon(game, 1)
                        begin_intermission(game, State.Explore)       #Intermission screen - Explore
                        break

        #Trigger after selection screen. Return to this screen after every
        #Battle assuming the player is still alive.
        #One keypress = one tile = one turn, same rhythm as the combat.
        elif game.state == State.Explore:
            if event.type == pygame.KEYDOWN:
                if event.key in (K_UP, K_w):
                    dx, dy = 0, -1
                elif event.key in (K_DOWN, K_s):
                    dx, dy = 0, 1
                elif event.key in (K_LEFT, K_a):
                    dx, dy = -1, 0
                elif event.key in (K_RIGHT, K_d):
                    dx, dy = 1, 0
                elif event.key == K_e:              #Open/shut the bag
                    Bag.toggle()                    #Flips Inv.is_open
                    dx, dy = 0, 0                   #E is not a step. Without this
                                                    #dx/dy keep the LAST arrow key,
                                                    #so opening the bag walks you
                elif event.key == K_r:              #Debug: re-roll THIS floor
                    exploration.enter_dungeon(game, game.dungeon_level)
                    dx, dy = 0, 0
                else:
                    dx, dy = 0, 0

                if dx or dy:
                    encounter = exploration.move_player(game, dx, dy)
                    if encounter:
                        battle.start_battle(game, encounter)
                        begin_intermission(game, State.Battle) #Intermission screen - battle

            #Clicking USE next to a row drinks that potion. Only the buttons
            #the panel actually drew this frame can be hit, so a click while
            #the bag is shut can never use anything.
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                chosen = Bag.use_button_at(pos)
                if chosen:
                    #game.message = game.inventory.use_item(chosen, game.player)
                    game.message = game.inventory.use_item(chosen, game)
                    print(game.message)


        #breaks every turn after the player has chosen a move.
        elif game.state == State.Battle:
            if game.turn == 'player':
                chosen = None
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    chosen = next((btn for btn in game.move_buttons if btn.clicked(pos)), None)
                elif event.type == pygame.KEYDOWN:              #WASD / arrow keys
                    chosen = ui.move_for_key(game.move_buttons, event.key)
                if chosen and chosen.usable(game.player):       #unlocked and CD = 0
                    battle.player_atk(game, chosen.move_index)

        elif game.state == State.Stats:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if Rematch.is_clicked(pos):
                    reset()
                elif Quit.is_clicked(pos):
                    reset()
                    Rungame = False


    #Save snapshot
    if game.selected_slot and game.state in (State.Explore, State.Battle):
        snapshot = (game.state, game.player_tile, game.dungeon_level,                       #Snapshot contents
                    game.player.health, len(game.dungeon_enemies), len(game.dungeon_items), game.inventory.items)
        if snapshot != last_save:
            last_save = snapshot
            saveload.save_game(game, game.selected_slot)

    #Enemy attack logic (following 3 second duration)
    if game.state == State.Battle:
        battle.player_move_update(game)
    
    if game.state == State.Battle and game.turn == 'enemy' and not game.enemy_acted and game.enemy.alive():
        battle.enemy_atk(game)
    
    if game.state == State.Battle:
        battle.enemy_move_update(game)
        
    #Permadeath implement
    wipe = game.state == State.Stats or game.state == State.intermission and game.destination == State.Stats
    if wipe and not game.battle_won and not game.death_processed:
        if game.selected_slot not in (None, ''):
            saveload.death_slot(game.selected_slot)
        game.death_processed = True

    #Tick animations
    if game.player_anim is not None:
        game.player_anim.update()
    if game.player_idle_anim is not None:
        game.player_idle_anim.update()
    if game.enemy_anim is not None:
        game.enemy_anim.update()
    if game.enemy_idle_anim is not None:
        game.enemy_idle_anim.update()

    #Decrease cooldown at the start of every player's turn
    if game.state == State.Battle and game.turn == 'player' and not game.enemy_acted:
        game.player.dec_CDs()
        game.enemy.dec_CDs()


    #Drawing
    if game.state == State.Menu:
        screen.blit(draw_load.BGmenu, (0, 0))
        begin.draw(screen)
        title_text = draw_load.Font.render("CLASS BATTLE", True, draw_load.Color['White'])
        screen.blit(title_text, (430, 150))

    elif game.state == State.slots:
        #screen.fill(draw_load.Color['Black'])
        screen.blit(draw_load.BGselect, (0, 0))
        HeadTxt = draw_load.Font.render("RUN SLOTS", True, draw_load.Color['White'])
        screen.blit(HeadTxt, (450, 150))
        for slot in ui.slot_buttons:
            slot.draw(screen)

    elif game.state == State.selection:
        screen.blit(draw_load.BGmenu, (0, 0)) #originally had a second background, voided
        HeadTxt = draw_load.Font.render("SELECT YOUR CLASS", True, draw_load.Color['White'])
        screen.blit(HeadTxt, (380, 80))

        #Cards of the 3 classes/chars
        for card in ui.class_cards:
            card.draw(screen)

    elif game.state == State.intermission:
        elapsed_t = pygame.time.get_ticks() - game.started
        screen.fill(draw_load.Color['Black'])
        HeadTxt = draw_load.Font.render("Loading", True, draw_load.Color['DDGrey'])
        screen.blit(HeadTxt, (380, 80))
        if elapsed_t >= INTERMISSION_TIME:
            game.state = game.destination
            game.destination = None

    elif game.state == State.Explore:
        screen.fill(draw_load.Color['DarkPurp'])               
        draw_load.draw_dungeon(screen, game, game.dungeon, TILE_SIZE)    
        screen.blit(draw_load.Navbar, (0, 0))
        exp_bar.draw_xp(screen, game.player.xp, game.player.xpcap)
        game.player_hpbar.draw_hp(screen, 50, 600, game.player.health, game.player.health_max)

        if game.item_icons:
            game.item_icons.draw(screen, game)
        
        hud_nav = draw_load.SmallFont.render(
            f'Floor {game.dungeon_level}   {game.player.name}  Power {game.player.power}  Enemies left: {len(game.dungeon_enemies)}   [E] bag', True, draw_load.Color['White'])
        screen.blit(hud_nav, (200, 15))

        if Bag.is_open:
            Bag.draw(screen, game.inventory)     #Inv Panel with a USE button per row
        Bag.drawicon(screen)                #Icon last, so it sits on top

    elif game.state == State.Battle:
        #Draw battle background
        screen.blit(draw_load.BGBattle, (0, 0))

        #player idle
        if game.player_idle_anim:
            screen.blit(game.player_idle_anim.image, game.player_idle_anim.rect)

        if game.enemy_idle_anim:
            screen.blit(game.enemy_idle_anim.image, game.enemy_idle_anim.rect)
        
        #Attack anims
        if game.player_anim is not None and game.player_anim.active:
            screen.blit(game.player_anim.image, game.player_anim.rect)
        if game.enemy_anim is not None and game.enemy_anim.active:
            screen.blit(game.enemy_anim.image, game.enemy_anim.rect)

        #HUD: fog backdrop + WASD move diamond, then the plates
        #(turn, message, enemy, player - HP bars and status effects inside)
        ui.draw_move_panel(screen, game, draw_load.BattleFog)
        ui.draw_battle_hud(screen, game)

    #Stats screen, post battle
    elif game.state == State.Stats:
        screen.fill(draw_load.Color['DGrey'])

        #title text
        title = draw_load.Font.render("BATTLE STATS", True, draw_load.Color['DDGrey'])
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100))

        #Draw win or lose text
        result_txt = 'VICTORY' if game.battle_won else "DEFEAT"
        result_surf = draw_load.Font.render(result_txt, True, draw_load.Color['DDGrey'])
        screen.blit(result_surf, (WIDTH//2 - result_surf.get_width()//2, 180))

        #damage dealt and damage taken
        dealt = draw_load.SmallFont.render(f'Damage Dealt: {game.dmg_dealt}', True, draw_load.Color['DDGrey'])
        taken = draw_load.SmallFont.render(f'Damage Taken: {game.dmg_taken}', True, draw_load.Color['DDGrey'])
        screen.blit(dealt, (WIDTH//2 - dealt.get_width()//2, 280))
        screen.blit(taken, (WIDTH//2 - taken.get_width()//2, 320))

        #Run summary 
        floors = draw_load.SmallFont.render(f'Floor Reached: {game.dungeon_level}', True, draw_load.Color['DDGrey'])
        kills = draw_load.SmallFont.render(f'Eyes Killed: {game.battles_won}', True, draw_load.Color['DDGrey'])
        screen.blit(floors, (WIDTH//2 - floors.get_width()//2, 360))
        screen.blit(kills, (WIDTH//2 - kills.get_width()//2, 400))

        #Rematch / quit 
        Rematch.draw(screen)
        Quit.draw(screen)

    pygame.display.update()
    dt_ms = clock.tick(FPS)
    if game.state == State.Explore:
        Inv.tick_buffs(game, dt_ms)

pygame.quit()
sys.exit()
