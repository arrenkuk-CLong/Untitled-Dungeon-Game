#gamestate
#Game and State
from enum import Enum, auto
from scripts import Inv

#Game States
class State(Enum):      #val (#), name ('')
    Menu = auto()       #1
    slots = auto()      #2 
    selection = auto()  #3 Once
    intermission = auto() #any order
    Explore = auto()    #4
    Battle = auto()     #5
    Stats = auto()      #6 Once
#game_state = State.Menu 

#Game loop States
class Game:
    def __init__(self):
        #Overall
        self.state = State.Menu #Starts Menu 

        #Slot & permadeath
        self.selected_slot = ''
        self.death_processed = False

        #Intermission
        self.destination = None 
        self.started = 0

        #player & enemy
        self.player = None
        self.enemy = None

        #Battle
        self.turn = 'player' #Turn begins with player
        self.turn_num = 0
        self.enemy_acted = False
        self.move_buttons = []

        #Animations
        self.player_anim = None 
        self.enemy_anim = None
        self.player_idle_anim = None #  NEW
        self.enemy_idle_anim = None  #  NEW
        self.selected_class = None
        self.player_attack_start = None
        self.player_attack_move = None #Instance to prevent spamming
        self.enemy_attack_start = None
        self.enemy_attack_move = None

        #UI
        self.message = ''
        self.player_hpbar = None
        self.enemy_hpbar = None
        self.player_effects = None
        self.enemy_effects = None 
        self.inventory = Inv.Inventory()

        #Item buffs, counted in REAL SECONDS (stored as milliseconds).
        #The clock only advances while exploring - see tick_buffs() below -
        #so a long battle never eats your potion.
        self.active_buffs = []      #[{'name','kind','ms_left','ms_total','strength'}]
        self.item_icons = None

        #Explore State
        self.dungeon = None
        self.dungeon_level = 1
        self.player_tile = (0, 0)
        self.dungeon_enemies = []
        self.dungeon_items = []
        self.current_encounter = None

        #Run Stats
        self.dmg_dealt = 0
        self.dmg_taken = 0
        self.battle_won = False
        self.battles_won = 0
