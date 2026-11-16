#CapTen
#Untitled dungeon game 
#Checklist:
#TODO Make minifigures of players and enemy for dungeon exploration #(Made basic)
#TODO Add Moving enemies (within FOV Radius)
#TODO Debug turn-based damage and animation logic (thigs play too fast)
#TODO Test different attack animations (line 1294 (enemy), 1239(enemy))
#TODO Test Enum game states
#TODO Revampe Global variable soup
#TODO revamp entire codebase architecture
#----------------------------------------------------------------------------------
#TODO Full save and load Runs 
#TODO Permadeath implementation
#TODO Add leveling / xp / progression system (e.g. player can unlock moves as he levels up)
#TODO levels and floor scaling 
# Cut off for posting a new log
#TODO More enemy types and a boss
#TODO More Items and meaningful inventory use
#TODO Add win condition (Average Campaign)
#----------------------------------------------------------------------------------
#TODO Make Remaining assets (make public access)
#TODO Sound and music 
#TODO Improve visuals and polish (add fallback?)
#TODO Balancing and playtesting
#TODO Upload to itch.io

#Built in imports
import os
import pygame, random, sys, json
import gif_pygame
from pygame.locals import *
from PIL import Image
from collections import deque
from enum import Enum, auto
pygame.init()

#Script imports
from scripts.config import DUNGEON_WIDTH
from scripts import Dungeongen, draw_load, entities, ui, Inv, exploration, battle, saveload
from scripts.gamestate import State, Game

WIDTH = 1080
HEIGHT = 720
TILE_SIZE = 24          #Pixels per tile. 40*24 = 960 wide, 30*24 = 720 tall, so
                        #a whole floor fits on screen and no camera is needed YET
MAP_OFF_X = (WIDTH - DUNGEON_WIDTH * TILE_SIZE) // 2    #40 = DUNGEON_WIDTH
MAP_OFF_Y = 0
FPS = 60

#Import Color form draw_load to replace this
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


#Actual JSON (saving data)
INVENTORY_PERSISTS = True           #True  = potions survive death and even closing the game (a real save file)
                                    #False = every run starts with an empty bag
LOAD_SAVE = True

#Buttons
begin = ui.button(440, 500, 200, 60, "Begin") 
Rematch = ui.button(WIDTH//2 - 150, 500, 150, 60, "Rematch")
Quit = ui.button(WIDTH//2 + 20,  500, 150, 60, "Quit")

#User Interface
Bag = Inv.inventory_UI(0, HEIGHT // 6,  300, 500, 'INVENTORY')
game = Game() #Literally the entire game loop


#Explain this
def cycle(cfg, field, values):
    # Move to the next value in the list, wrapping around at the end.
    # (index + 1) % len is the whole "cycle through options" pattern.
    current = cfg[field]
    i = values.index(current) if current in values else -1
    cfg[field] = values[(i + 1) % len(values)]

#save/load callback
def load_slot():
    data = saveload.load_game()
    #parent dictionaries
    player_data = data["player"] 
    dungeon_data = data["dungeon"]

    create_player(player_data["class"])
    game.player.health = player_data["health"]

    game.dungeon_level = dungeon_data["level"]
    game.dungeon = Dungeongen.generate_dungeon(seed=dungeon_data["seed"])

    #Pos
    game.player_tile = tuple(player_data["position"])
    game.dungeon_enemies = dungeon_data["enemies"]
    game.dungeon_items = dungeon_data["items"]

    #Change this later when slot screen is added.
    game.state = State.Explore

def create_player(class_name):
    game.dmg_dealt = 0
    game.dmg_taken = 0
    game.battles_won = 0
    game.battle_won = False
    game.selected_class = class_name

    #If False - Every run starts with an empty bag
    if INVENTORY_PERSISTS:
        print(game.inventory.load())
    else:
        game.inventory.clear()

    #Name, maxhealth, move list (index)
    if class_name == 'Sword':
        game.player = entities.Character("Sword", 110, entities.Sword_moves)
        game.player_hpbar = ui.HealthBar(150, 150, 200, 40, 110)
    elif class_name == 'Wizard':
        game.player = entities.Character("Wizard", 100, entities.Wizard_moves)
        game.player_hpbar = ui.HealthBar(150, 150, 200, 40, 100)
    elif class_name == 'Archer': 
        game.player = entities.Character("Archer", 95, entities.Archer_moves)
        game.player_hpbar = ui.HealthBar(150, 150, 200, 40, 95)
    game.player_anim = None
    game.player_hpbar.set_char(game.player.name)

#Reset the game for a brand new run on rematch or Run
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
    #Throw the whole floor away: a new run has to roll a new dungeon
    game.dungeon = None
    game.dungeon_enemies = []
    game.dungeon_items = []
    game.dungeon_level = 1
    game.current_encounter = None


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

        if game.state == State.Menu:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if begin.is_clicked(pos):
                    game.state = State.slots                    

        elif game.state == State.slots:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                #if runslot.is_clicked(pos):
                for slot in ui.slot_buttons:
                    if slot.is_clicked(pos):
                        game.state = State.selection
        
        elif game.state == State.selection:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for card in ui.class_cards:
                    if card.is_clicked(pos):
                        create_player(card.name)    
                        #exploration.enter_dungeon(1)            #Drop player on floor 1 - will change with JSON save files when implemented
                        exploration.enter_dungeon(game, 1)
                        game.state = State.Explore
                        break

        #Trigger after selection screen. Return to this screen after every
        #Battle assuming the player is still alive.
        #One keypress = one tile = one turn, same rhythm as the combat.
        elif game.state == State.Explore:
            if event.type == pygame.KEYDOWN:
                '''
                if event.key in (K_UP, K_w):
                    exploration.move_player(0, -1)
                elif event.key in (K_DOWN, K_s):
                    exploration.move_player(0, 1)
                elif event.key in (K_LEFT, K_a):
                    exploration.move_player(-1, 0)
                elif event.key in (K_RIGHT, K_d):
                    exploration.move_player(1, 0)
                #Two generator debug keys. Keep them while tuning GEN_CONFIG:
                elif event.key == K_r:              #Re-roll THIS floor
                    exploration.enter_dungeon(game.dungeon_level)
                #elif event.key == K_TAB:            #Print the floor as text
                #    print(ascii_render(game.dungeon))'''
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
                        game.state = State.Battle

            #Clicking USE next to a row drinks that potion. Only the buttons
            #the panel actually drew this frame can be hit, so a click while
            #the bag is shut can never use anything.
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                chosen = Bag.use_button_at(pos)
                if chosen:
                    game.message = game.inventory.use_item(chosen, game.player)
                    print(game.message)


        #breaks every turn after the player has chosen a move.
        elif game.state == State.Battle:
            if game.turn == 'player' and event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for i, btn in enumerate(game.move_buttons): #Moves with CD = 0
                    if btn.clicked(pos) and game.player.move_ready(i):
                        battle.player_atk(game, i) #With that specific index move
                        break
        elif game.state == State.Stats:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if Rematch.is_clicked(pos):
                    reset()
                elif Quit.is_clicked(pos):
                    Rungame = False

    #Enemy attack logic (following 3 second duration)
    if game.state == State.Battle:
        battle.player_move_update(game)
    
    if game.state == State.Battle and game.turn == 'enemy' and not game.enemy_acted and game.enemy.alive():
        battle.enemy_atk(game)
    
    if game.state == State.Battle:
        battle.enemy_move_update(game)

    if game.player_anim is not None:
        game.player_anim.update()
    if game.enemy_anim is not None:
        game.enemy_anim.update()

    #Decrease cooldown at the start of every player's turn
    #if Battle and turn == 'player' and not enemy_acted:
    if game.state == State.Battle and game.turn == 'player' and not game.enemy_acted:
        game.player.dec_CDs()
        game.enemy.dec_CDs()

    #Drawing
    if game.state == State.Menu:
        screen.blit(draw_load.BGmenu, (0, 0))
        begin.draw(screen)
        title_text = Font.render("CLASS BATTLE", True, clrWhite)
        screen.blit(title_text, (430, 150))

    elif game.state == State.slots:
        screen.fill(clrBlack)
        #runslot.draw(screen)
        HeadTxt = Font.render("RUN SLOTS", True, clrWhite)
        screen.blit(HeadTxt, (450, 150))
        for slot in ui.slot_buttons:
            slot.draw(screen)

    elif game.state == State.selection:
        screen.blit(draw_load.BGmenu, (0, 0)) #originally had a second background, voided
        HeadTxt = Font.render("SELECT YOUR CLASS", True, clrWhite)
        screen.blit(HeadTxt, (380, 80))
        #Cards of the 3 classes/chars
        for card in ui.class_cards:
            card.draw(screen)

    elif game.state == State.Explore:
        screen.fill(clrBlack)               #Wipe FIRST. Drawing the icon before
        draw_load.draw_dungeon(screen, game, game.dungeon, TILE_SIZE)    #the fill just erased it
        if Bag.is_open:
            Bag.draw(screen, game.inventory)     #Inv Panel with a USE button per row
        Bag.drawicon(screen)                #Icon last, so it sits on top

    #elif Battle:
    elif game.state == State.Battle:
        #Draw battle background
        screen.blit(draw_load.BGBattle, (0, 0))

        #Draw player and enemy
        if game.player and game.player.name in draw_load.Battle_files:
            pimg = draw_load.Battle_files[game.player.name]
            prect = pimg.get_rect(midbottom = (WIDTH//2 - 250, HEIGHT - 125)) #Better to reference and adjust it from the center 
            screen.blit(pimg, prect)
        if game.enemy:
            eimg = draw_load.Enemy_img
            e_rect = eimg.get_rect(midbottom = (WIDTH//2 + 250, HEIGHT - 325))
            screen.blit(eimg, e_rect)

        if game.player_anim is not None and game.player_anim.active:
            screen.blit(game.player_anim.image, game.player_anim.rect)
        if game.enemy_anim is not None and game.enemy_anim.active:
            screen.blit(game.enemy_anim.image, game.enemy_anim.rect)

        #Draw health bars
        if game.player_hpbar:
            game.player_hpbar.draw(screen, game.player.health)
        if game.enemy_hpbar:
            game.enemy_hpbar.draw(screen, game.enemy.health)

        #Draw Message
        message_surf = Font.render(game.message, True, clrDDGrey)
        screen.blit(message_surf, (WIDTH//2 - message_surf.get_width()//2, 50)) #x, y

        #Draw move buttons only on player's turn
        if game.turn == 'player':
            pygame.draw.rect(screen, clrDDGrey, (100, 500, 900, 400))
            for i, btn in enumerate(game.move_buttons):
                btn.draw(screen, game.player.move_CDs[i]) #Passes the Button drawing and the Cooldown # text
    
    #Stats screen, post battle
    elif game.state == State.Stats:
        screen.fill(clrDGrey)
        #title text
        title = Font.render("BATTLE STATS", True, clrWhite)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100)) #Ensures it centeres correctly given the length of the sentence
        #Draw win or lose text
        result_txt = 'VICTORY' if game.battle_won else "DEFEAT"
        result_surf = Font.render(result_txt, True, clrWhite)
        screen.blit(result_surf, (WIDTH//2 - result_surf.get_width()//2, 180))
        #damage dealt and damage taken
        dealt = SmallFont.render(f'Damage Dealt: {game.dmg_dealt}', True, clrWhite)
        taken = SmallFont.render(f'Damage Taken: {game.dmg_taken}', True, clrWhite)
        screen.blit(dealt, (WIDTH//2 - dealt.get_width()//2, 280))
        screen.blit(taken, (WIDTH//2 - taken.get_width()//2, 320))
        #Run summary - how deep the dungeon got before it killed you
        floors = SmallFont.render(f'Floor Reached: {game.dungeon_level}', True, clrWhite)
        kills = SmallFont.render(f'Eyes Killed: {game.battles_won}', True, clrWhite)
        screen.blit(floors, (WIDTH//2 - floors.get_width()//2, 360))
        screen.blit(kills, (WIDTH//2 - kills.get_width()//2, 400))

        #Rematch / quit 
        Rematch.draw(screen)
        Quit.draw(screen)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
sys.exit()
