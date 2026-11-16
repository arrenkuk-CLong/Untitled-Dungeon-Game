#battle
#Attack anims
import pygame, random
from scripts.config import WIDTH, HEIGHT
from scripts import entities, draw_load, ui, saveload, Inv
from scripts.gamestate import State
from scripts.intermission import begin_intermission

ATTACK_ANIMATION_POSITION = {
    "Sword": {
        "Slash": {
            "start": (WIDTH // 2 - 250, HEIGHT - 400), #Player to enemy
            "end": (WIDTH // 2 + 300, HEIGHT - 450),
        },
        "Ground Slam": {
            "start": (WIDTH // 2 + 300, HEIGHT - 400),
            "end": (WIDTH // 2 + 300, HEIGHT - 700), 
        },
    },
    "Eye": {
        "Bloodshot Gaze": {
            "start": (WIDTH // 2 + 300, HEIGHT - 500),
            "end": (WIDTH // 2 - 250, HEIGHT - 225),
            
        },
        "Kamui": {
            "start": (WIDTH // 2 - 250, HEIGHT - 225),
            "end": (WIDTH // 2 - 250, HEIGHT - 225),
        },
    },
}


#=====================================================================
#Battle Functions
#---------------------------------------------------------------------
#
#Start_Battle: Initialize enemy and reset CDs
#
#player_atk: [fill out]
#
#enemy_atk: [fill out]
#======================================================================
def start_battle(game, encounter):
    #encounter = the {'x','y','name'} dict of the eyeball we walked into, kept
    #so the right one can be deleted from the floor once it dies
    game.current_encounter = encounter

    #Enemy data
    enemy_type = encounter['name']
    enemy_data = entities.ENEMY_BATTLE_DATA[enemy_type]
    game.enemy = entities.Character(enemy_type, enemy_data['health'], enemy_data['moves'], enemy_data['XP'])
    game.enemy_anim = None
    #game.enemy_hpbar = ui.HealthBar(WIDTH - 365, 75, 200, 40, enemy_data['health'])
    game.enemy_hpbar = ui.HPBAR(enemy_data['health'])
    game.enemy_hpbar.set_char(enemy_type)    
    game.enemy_effects = ui.EffectsUI(game.enemy_hpbar)

    #player idle
    game.player_idle_anim = draw_load.create_idle_anim(game.player.name)
    if game.player_idle_anim:
        game.player_idle_anim.start((WIDTH//2 - 250, HEIGHT - 350))

    #Enemy idle
    game.enemy_idle_anim = draw_load.create_idle_anim(game.enemy.name)
    if game.enemy_idle_anim:
        game.enemy_idle_anim.start((WIDTH//2 + 250, HEIGHT - 325))

    #Create move buttons
    game.move_buttons = [] #Reset
    for i, move in enumerate(game.player.moves):
        if not game.player.move_unlocked(i): #if power < index.unlock
            continue
        x = 200 + (i % 2) * 500 
        y = 550 + (i // 2) * 70
        move_button = ui.MovesUI(x, y, 220, 50, move)
        move_button.move_index = i
        game.move_buttons.append(move_button)

    game.player.reset_CD()

    game.state = State.Battle

    game.turn = 'player'
    game.turn_num = 0
    game.enemy_acted = False
    game.message = (f"{game.player.name} vs {game.enemy.name}")
    print(game.message)

def player_atk(game, move_index): #Function for player attack ONLY
    game.player.dec_CDs()
    game.player.tick_statuses()
    game.player.can_act()
    #Check for death here with if statement, break after sending player to intermission scree.
    move = game.player.use_move(move_index) #i
    if move is None:
        return
    
    game.player_attack_move = move
    game.player_attack_start = pygame.time.get_ticks()
    game.player_anim = draw_load.create_attack_animation(game.player.name, move_index)

    if game.player_anim is not None:
        position = ATTACK_ANIMATION_POSITION[game.player.name][move.name]
        game.player_anim.start(
            position["start"],
            position["end"],
        )

    game.turn = 'player_anim'

def player_move_update(game):
    if game.player_attack_start is None:
        return
    #move = player_attack_move
    
    if game.player_anim is None or game.player_anim.current_frame == len(game.player_anim.frames) - 1: #Ensures the dmg shows on last frame of anim
        move = game.player_attack_move
        dmg = move.damage
        if dmg > 0: 
            game.enemy.take_dmg(dmg)
            game.dmg_dealt += dmg
            game.message = (f'{move.name} dealt {dmg} damage!') #Change message display (take_dmg)
        elif dmg < 0: #Player Heal 
                game.player.health = min(game.player.health_max, game.player.health - dmg)
                game.message = (f'{move.name} healed {dmg} HP!')

        #Status effects - Player
        if move.effect:
            effect = entities.make_effect(move.effect) 
            if effect.target == 'player':
                game.player.add_status(effect)
            else:
                game.enemy.add_status(effect)
            
        #Reset attack state
        game.player_attack_move = None
        game.player_attack_start = None
        #Enemy death check
        if game.enemy.health <= 0:
            game.battle_won = True
            game.battles_won += 1

            gained = game.enemy.xp * (2 if Inv.has_buff(game, 'xp') else 1)
            game.player.xp += gained
            game.player.power_up()
            print('gained 5 xp!') #Check xp gain

            if game.current_encounter in game.dungeon_enemies:
                game.dungeon_enemies.remove(game.current_encounter)
            game.current_encounter = None
            game.message = (f"{game.enemy.name} got cooked. HP {game.player.health}/{game.player.health_max}")
            begin_intermission(game, State.Explore)
        else:
            game.turn = 'enemy'
            game.enemy_acted = False



def enemy_atk(game):
    ready_moves = [i for i, cd in enumerate(game.enemy.move_CDs) if cd == 0]

    game.enemy.tick_statuses()
    #Check for death here with if statement, break after sending player to intermission screen
    game.enemy.can_act() #cc
    if not ready_moves:
        game.enemy.dec_CDs()
        game.turn = 'player'
        game.enemy_acted = True
        game.message = 'Enemy is waiting...'
        return

    idx = random.choice(ready_moves)
    enemove = game.enemy.use_move(idx)
    game.enemy_attack_move = enemove
    game.enemy_attack_start = pygame.time.get_ticks()
    game.enemy_anim = draw_load.create_attack_animation(game.enemy.name, idx)

    game.turn = 'enemy_anim'

def enemy_move_update(game): 
    if game.enemy_attack_start is None:
        return
    passed = pygame.time.get_ticks() - game.enemy_attack_start
    if passed < 1000:
        return

    if game.enemy_anim is not None and not game.enemy_anim.active:
        position = ATTACK_ANIMATION_POSITION[game.enemy.name][game.enemy_attack_move.name]
        game.enemy_anim.start(
            position["start"],
            position["end"],
        )
        return
    if game.enemy_anim is not None and game.enemy_anim.current_frame != len(game.enemy_anim.frames) - 1:
        return

    move = game.enemy_attack_move
    dmg = move.damage
    if dmg > 0:
        game.player.take_dmg(dmg)
        game.dmg_taken += dmg
        game.message = (f'{move.name} dealt {dmg} damage!') #Change message display (take_dmg)
    elif dmg < 0:
        game.enemy.health = min(game.enemy.health_max, game.enemy.health - dmg)
        game.message = (f'{move.name} healed {dmg} HP!')
    else:
        game.message = 'Enemy heal failed!'

    #Status effects - Enemy
    if move.effect:
        effect = entities.make_effect(move.effect)
        if effect.target == 'enemy':
            game.enemy.add_status(effect)
        else:
            game.player.add_status(effect)

    game.enemy_attack_move = None
    game.enemy_attack_start = None
    if game.player.health <= 0:
        game.battle_won = False
        game.message = (f"{game.player.name} got cooked, you lose")
        begin_intermission(game, State.Stats)
    else:
        game.turn = 'player'
        game.turn_num += 1
        game.enemy_acted = True

