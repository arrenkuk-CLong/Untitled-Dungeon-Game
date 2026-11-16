#entities
#player, enemy, move lists

import copy #Duplicate
#store name, damage, and CD from move list
class Move: 
    def __init__(self, name, damage, effect: str, cooldown = 0, unlock = 0):
        self.name = name 
        self.damage = damage 
        self.cooldown = cooldown
        self.unlock = unlock
        self.effect = effect


class Status_Effects:
    def __init__(self, name, duration, category, intensity, target): #dot, hot, cc
        self.name = name
        self.duration = duration #turns
        self.category = category
        self.intensity = intensity
        self.target = target

    def tick(self, target):
        if self.duration <= 0: #effect run out
            return ''
        #if Character has_status()
        if self.category == 'dot':
            target.health -= self.intensity
        elif self.category == 'hot':
            target.health += self.intensity


#Player class and enemy 
class Character: #Health, damage, move list
    def __init__(self, name: str, health: int, moves, xp = 0, xpcap = 10, power = 0) -> None: 
        self.name = name 
        self.health = health 
        self.health_max = health 
        self.moves = moves #list
        self.move_CDs = [0] * len(moves) 
        self.statuses = [] #Battle usage only
        self.xp = xp
        self.xpcap = xpcap
        self.power = power
    
    def alive(self):
        return self.health > 0 #Return Val of hp - reference this for health bar

    def take_dmg(self, dmg):
        #Reduce dmg
        if self.has_status('Superblock'):
            dmg = int(dmg * 0.1)
        if self.has_status('Block'):
            dmg = int(dmg * 0.5)
        #Increase dmg
        if self.has_status('Vulnerable'):
            dmg = int(dmg * 1.25)
        self.health = max(0, self.health - dmg)
        return dmg
    
    #Reset cooldown per battle
    def reset_CD(self):
        self.move_CDs = [0] * len(self.moves) 

    #Decrease cooldown per turn
    def dec_CDs(self): 
        for cd in range(len(self.move_CDs)):
            if self.move_CDs[cd] > 0: 
                self.move_CDs[cd] -= 1

    #Status effects
    def add_status (self, effect):
        existing = self.get_status(effect.name)
        if existing:
            existing.duration = max(existing.duration, effect.duration) 
        else:
            self.statuses.append(effect) 

    def get_status(self, name):
        for s in self.statuses: 
            if s.name == name:
                return s
        return None
    
    def has_status(self, name):
        return self.get_status(name) is not None
    
    def tick_statuses(self):
        for s in self.statuses:
            s.tick(self) #?
            s.duration -= 1
        self.statuses = [s for s in self.statuses if s.duration > 0]

    def can_act(self):
        return not(self.has_status('Freeze') or self.has_status('Stagger') or self.has_status('Disoriented'))
    
    def clear_status(self): #Run after battle ends
        self.statuses = []

    #Moves
    def use_move(self, index): #1-4 
        if index < len(self.move_CDs):
            move = self.moves[index]
            self.move_CDs[index] = move.cooldown 
            return move
        return None 
    
    #unlock movesets
    def move_unlocked(self, index):
        return self.power >= self.moves[index].unlock
    def move_ready(self, index):
        return self.move_CDs[index] == 0

    #level up - increase max hp, xp gain/retain, top up hp
    def power_up(self):
        while self.xp >= self.xpcap:
            self.xp -= self.xpcap 
            self.xpcap = int(self.xpcap * 1.5)
            self.power += 1
            print('you have powered up') #print check
            self.health_max *= 1.2 
            self.health = int(self.health_max) 



#Enemy class (explore stage drawing only)
class Enemy:
    def __init__(self, x, y, enemy_type): # 5 enemies
        self.x, self.y = x, y 
        self.enemy_type = enemy_type
        self.speed = 1 #Move speed


#=====================================================================
# Move Arsenal
#----------------------------------------------------------------------
# 4 moves per class, 1 basic attack, 1 heal, 2 special moves with CD
# Moves are stored in lists (name, dmg, cooldown)
# Combat Data
Sword_moves = [ 
    Move('Slash', 15, None, 0, unlock = 0), 
    Move('Ground Slam', 30, 'Stagger', 2, unlock = 3), 
    Move('Guard', 0, 'Block', 0, unlock = 0), 
    Move('180 Pound', 35, None, 3, unlock = 5) 
]

Wizard_moves = [ 
    Move('Magic Missile', 20, None, 0, unlock = 0), 
    Move('Frost Beam', 25, 'Freeze', 2, unlock = 2), 
    Move('Light Cure', -15, None, 2, unlock = 0),
    Move('FIREBALL', 30, 'Burn', 3, unlock = 4) 
]

Archer_moves = [ 
    Move('Quick Fire', 20, None, 0, unlock = 0),
    Move('Rain of Arrows', 30, None, 2, unlock = 3), 
    Move('Ethereal Arrows', 0, 'Ethereal', 0, unlock = 1), 
    Move('Thunder Snipe', 40, 'Vulnerable', 3, unlock = 5) 
]

Eye_moves = [ 
    Move('Bloodshot Gaze', 15, None, 0), 
    Move('illusory Realm', -10, None, 2), 
    Move('Confusion', 5, 'Disoriented', 3), 
    Move('Kamui', 10, 'Corruption', 3) 
]

Skele_moves = [ 
    Move('Bone throw', 15, None, 0), #base attack
    Move('High Calcium', 0, 'HighCalcium', 4), 
    Move('Bone Bat', 30, 'Disoriented', 3) 
]


Wraith_moves = [ 
    Move('Phase Claw', 25, None, 0), #base attack
    Move('Shadowcast', 15, 'Shadowed', 2), 
    Move('Conceal', 0, 'Conceal', 3), 
    Move('Siphon', 0, 'Siphon', 3) 
]

Fallen_moves = [ 
    Move('Strike', 25, None, 0), #base attack
    Move('Damnation', 0, 'Damnation', 4) 
]

Judgement_moves = [ 
    Move('Monopoly', 0, None, 10), #Damage should be the amount of coins the player earned during the entire run
    Move('Slaughter', 0, None, 1),  #Damage should be the amount of enemies the player kileld duringt the entire run
    Move('Greed', 0, 'Greed', 10),
    Move('Monologue', 0, None, 0) #Trash talk the player lol
]

ENEMY_BATTLE_DATA = {
    'Eye': {'health': 40, 'moves': Eye_moves, 'XP' : 5},
    'Skeleton': {'health': 60, 'moves': Skele_moves, 'XP' : 8},
    'Wraith': {'health': 100, 'moves': Wraith_moves, 'XP' : 15},
    'Fallen': {'health': 150, 'moves': Fallen_moves, 'XP' : 20},
    'Judgement': {'health': 250, 'moves': Judgement_moves, 'XP' : 30},
}

#Effects map
#Move --> pass effect if effect exists --> set target (enemy/player) --> 
#add_status(effect) to target --> tick_statuses from each entity every turn --> 
#duration runs out --> repeat if hit

#!!!!!!!!!!!!!!!!!! means newly added effects and without icon.
EFFECTS = {
    'Superblock' : Status_Effects('Superblock', 1, 'cc', 0, 'player'),
    'Block': Status_Effects('Block', 1, 'cc', 0, 'player'), #Lower dmg
    'Stagger': Status_Effects('Stagger', 2, 'cc', 0, 'enemy'), #stun 1 turn
    'Freeze': Status_Effects('Freeze', 2, 'cc', 0, 'enemy'), #stun 2 turns
    'Burn': Status_Effects('Burn', 2, 'dot', 4, 'enemy'), #burn 
    'Ethereal': Status_Effects('Ethereal', 3, 'cc', 0, 'player'), #Reset all cooldowns. !!!!!!!!!!!!!!!!!
    'Vulnerable': Status_Effects('Vulnerable', 2, 'cc', 0, 'enemy'), #Increase dmg
    'Corruption': Status_Effects('Corruption', 2, 'dot', 3, 'player'), #Burn damage but lower
    'Disoriented': Status_Effects('Disoriented', 1, 'cc', 0, 'player'), #Hit yourself
    'HighCalcium': Status_Effects('HighCalcium', 2, 'cc', 0, 'enemy'), #increase damage and defense (a.k.a damage reduction) only for skeleton !!!!!!!!!!!!!!!
    'Shadowed': Status_Effects('Shadowed', 2, 'cc', 0, 'player'), #Hides Cooldown for each move and player hp !!!!!!!!!!!!!!!!!!
    'Conceal': Status_Effects('Conceal', 1, 'cc', 0, 'enemy'), #Completely Immune to all physical damage !!!!!!!!!!!!!!!!!!
    'Siphon': Status_Effects('Siphon', 3, 'cc', 5, 'player'), #Lifesteal 5 hp for 3 turns !!!!!!!!!!!!!!!!!!
    'Damnation': Status_Effects('Damnation', 4, 'cc', 0, 'player'), #Once Status effect wears off, player will immediately suffer 67 damage. !!!!!!!!!!!!!!!!!!
    'Greed': Status_Effects('Greed', 10, 'cc', 10, 'player') #!!!!!!!!!!!!!!!!!!
} 

#Copy effect from dictionary per inflict/proc
def make_effect(name):
    return copy.deepcopy(EFFECTS[name])