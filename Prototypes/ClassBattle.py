#Arren Kuk
#5/31/2026 completed for hand in 6/19/2026
#Your average turn based class game - missing a lot of things
#Game idea: Turn based combat game similar to pokemon 
#Game checklist: Menu (pick class), Battle UI, turn-based fighting code, character design, unique animation
#Use Piskel
#Main gameloop blueprint/tutorial: https://www.youtube.com/watch?v=cM_ocyOrs_k
#Game checklist part 2: Character health bars, battle UI visual upgrades, Character Battle assets(PNGS), Win and Los screen with/without battle stats. 
#Game Checklist part 3: Animations, Stat effects, and add a breathing between moves because the Enemy makes a move a literal frame after I make mine (This is because there should be animation playing but I didnt make any)

import pygame, random, sys
from pygame.locals import *
pygame.init()

WIDTH = 1080
HEIGHT = 720
FPS = 60

clrBlack = pygame.Color(0, 0, 0)
clrDGrey = pygame.Color(59, 59, 59)
clrDDGrey = pygame.Color(25, 25, 25) #Dark dark grey
clrGrey = pygame.Color(70, 70, 70)
clrWhite = pygame.Color(255, 255, 255)
clrRed = pygame.Color(120, 0, 0)
clrLRed = pygame.Color(200, 0, 0)

Font = pygame.font.SysFont('cinzel', 45)
SmallFont = pygame.font.SysFont('cinzel', 25)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('ClassBattle')
clock = pygame.time.Clock()

class Cards: #get it?
    def __init__(self, name, image, x, y, width = 200, height = 200):
        self.name = name #assets
        self.image = pygame.transform.scale(image, (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.selected = False #Border UX boolean trigger
        
    def draw(self, screen):
        border_color = clrWhite if self.selected else clrDGrey #improve UX
        pygame.draw.rect(screen, border_color, self.rect, 10)
        screen.blit(self.image, self.rect) #surf and rect in that order
        name_txt = Font.render(self.name, True, clrWhite)
        name_rect = name_txt.get_rect(center=(self.rect.center)) #center text
        screen.blit(name_txt, name_rect)

    def is_clicked (self, pos):
        return self.rect.collidepoint(pos) #Mousebutton down interaction

class button: #First button type for Menu class selection
    def __init__(self, x, y, width, height, text, fill_color = clrGrey, border_color = clrDGrey):
        self.rect = pygame.Rect(x, y, width, height)
        self.fill_color = fill_color
        self.border_color = border_color
        self.text = text
        self.font = Font
    
    def draw(self, screen):
        pygame.draw.rect(screen, clrGrey, self.rect)
        pygame.draw.rect(screen, clrDGrey, self.rect, 7)
        TxtS = self.font.render(self.text, True, clrWhite)
        TxtR = TxtS.get_rect(center=self.rect.center)
        screen.blit(TxtS, TxtR)

    def is_clicked (self, pos):
        return self.rect.collidepoint(pos) #Collidepoint (on click)

class MovesUI: #Second button type for battle UI
    def __init__(self, x, y, width, height, move): #Class that sorts out unique moves for  Sword, Wizard, and Archer, trigger from click/button
        self.rect = pygame.Rect(x, y, width, height)
        self.move = move
        #self.CDfont = SmallFont #Cooldown will be shown on SOME move buttons 

    #Bordless, looks better this way
    def draw(self, screen, CD = 0): 
        color = clrDGrey if CD == 0 else clrDGrey
        pygame.draw.rect(screen, color, self.rect)
        #draw moves
        Textscreen = Font.render(self.move.name, True, clrWhite)
        Textrender = Textscreen.get_rect(center = self.rect.center)
        screen.blit(Textscreen, Textrender)
        #If CD > 0 - on cooldown 
        if CD > 0:
            cd_text = SmallFont.render(f"CD:{CD}", True, clrLRed) #Displays the cooldown turn timer
            cd_rect = cd_text.get_rect(topright = (self.rect.right-5, self.rect.top+5)) #On the top right
            screen.blit (cd_text, cd_rect)
    
    def clicked (self, pos): #Return the click bool
        return self.rect.collidepoint(pos) 

class Move: #store name, damage, and move name for the movesets below
    def __init__(self, name, damage, cooldown = 0): #Planned third parameter: Move Cooldown
        self.name = name 
        self.damage = damage 
        self.cooldown = cooldown

class Character: #Health, damage, and other variables needed for battle
    def __init__(self, name: str, health: int, moves) -> None: #realization: very similar to what I did in Unity (C-Sharp)
        self.name = name #Wizard, Sword, Archer, Eye
        self.health = health #Current health after every turn
        self.health_max = health #100 for each char, 80 for the enemy
        self.moves = moves #list of moves
        self.move_CDs = [0] * len(moves) #Each move starts of with no cooldown
    
    def alive(self):
        return self.health > 0 #Return Val of hp - reference this for health bar

    def take_dmg(self, dmg):
        self.health -= dmg
        if self.health < 0: #Defeat detection
            self.health = 0 
    
    #handling cooldowns
    def reset_CD(self):
        self.move_CDs = [0] * len(self.moves) #same
    
    def dec_CDs(self): #Automatically decreases every turn, dont need to intialize it in the gameloop or a func
        for cd in range(len(self.move_CDs)):
            if self.move_CDs[cd] > 0: #If cooldown is larger than zero
                self.move_CDs[cd] -= 1 #then dec cd by 1 (every turn but that isn't coded in this function)
    
    def use_move(self, index): #Pick an index# (1 to 4) each representing a move from the move list by clicking
        if index < len(self.move_CDs):
            move = self.moves[index]
            self.move_CDs[index] = move.cooldown #From Move Class
            return move
        return None #If still on cooldown, return nothing
    
    def move_ready(self, index):
        return self.move_CDs[index] == 0

class HealthBar: #Same class, work on player and enemy
    def __init__(self, x, y, width, height, max_hp):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_hp = max_hp
        self.char_name = ''

    def set_char(self, name):
        self.char_name = name #Identify player (swd, Wiz, Arc) and Enemy

    def draw(self, surf, turn_hp): #turn_hp will be assigned to the current health of a character every turn
        ratio = turn_hp / self.max_hp #always gives the right percentage
        pygame.draw.rect(surf, clrRed, (self.x, self.y, self.width, self.height)) #Healthbar background
        pygame.draw.rect(surf, clrLRed, (self.x, self.y, self.width * ratio, self.height)) #Multiply width by ratio (basically 1 times anything < 1 but > 0)
        pygame.draw.rect(surf, clrRed, (self.x, self.y, self.width, self.height), 5)
        #Health txt
        text = SmallFont.render(f"{int(turn_hp)}/{self.max_hp}", True, clrWhite) 
        text_rect = text.get_rect(center = (self.x + self.width//2 , self.y + self.height//2)) #Position text at the center of hp bar
        surf.blit(text, text_rect)


#Asset loader - purely to make the asset loading process easier
def load_img(png, scale = None):
    img = pygame.image.load(png)
    if scale: # if I apply (WIDTH, HEIGHT)
        img = pygame.transform.scale(img, scale)
    return img

#BGs
BGmenu = load_img('BGselect.png', (WIDTH, HEIGHT))
BGBattle = load_img('BGBattle.png', (WIDTH, HEIGHT))


#Class files (select stage) | Char cards = Character files + asset_dict --> card_grid = Char_cards + Cards (class) --> class_cards (destination)--------------------------------------------------------------------------------------------
character_files = ["Sword.png", "Wizard.png", "Archer.png"]
Char_cards = {} #Set up as dictionary
for file in character_files:
    name = file.split('.')[0] #Removes everything after '.', including the dot itself, still remains in a list
    Char_cards[name] = load_img(file, (260, 260))
    print(f"Loaded: {name}") #print check in terminal 

#Class files (Battle stage) each loaded asset defined as a str
Battle_files = {
    "Sword": load_img("SwordBattle.png", (300, 400)), 
    "Wizard": load_img("WizardBattle.png", (300, 400)),
    "Archer": load_img("ArcherBattle.png", (300, 400))}
Enemy_img = load_img('Eye.png', (250, 350))

def card_grid (names, start_x, start_y, spacing_x, spacing_y, width = 260, height = 260):  
    cards = []
    cols = 3 #2 is very ugly
    for i, name in enumerate(names): #Index and name (index 0: Sword, etc)
        row = i // cols #all three on the same row
        col = i % cols 
        x = start_x + (col * spacing_x) #Spacing by 280 pxls
        y = start_y + (row * spacing_y) #Not really necessary now but Incase I want to come back and add more classes
        #clean_name = name.split('.')[0]
        if name in Char_cards:
            card = Cards(name, Char_cards[name], x, y, width, height) #Name, img, rect 
            cards.append(card)
    return cards

class_cards = card_grid(
    ['Sword', 'Wizard', 'Archer'],
    start_x=128,# Starting X position
    start_y=225,# Starting Y position  
    spacing_x=280,# Horizontal spacing
    spacing_y=350,# Vertical spacing
    width=260,#true toggle for size
    height=260
)


#Sword moves
Sword_moves = [ 
    Move('Slash', 15, 0), #Basic Attack
    Move('Ground Slam', 30, 2), #Planned stat effect and CD
    Move('Guard', 0, 0), #Planned stat effect, USE THIS TO TEST THE DEFEAT SCREEN CAUSE YOU'RE BASICALLY GURANTEED TO WIN IF YOU DONT USE THIS MOVE
    Move('180 Pound', 35, 3) #CD
]

#Wizard moves
Wizard_moves = [ 
    Move('Magic Missile', 20, 0), #Basic Attack
    Move('Frost Beam', 25, 2), #Planned stat effect Short CD
    Move('Light Cure', -15, 2),
    Move('FIREBALL', 30, 3) #Planned stat effect and CD
]

#Archer moves
Archer_moves = [ 
    Move('Quick Fire', 20, 0), #Basic Attack
    Move('Rain of Arrows', 30, 2), #Short CD
    Move('Ranger Stance', 0, 0), #Planned stat effect, USE THIS TO TEST THE DEFEAT SCREEN CAUSE YOU'RE BASICALLY GURANTEED TO WIN IF YOU DONT USE THIS MOVE
    Move('Thunder Snipe', 40, 3) #Planned stat effect and CD
]

#Boss/EnEemy moves,  too many stat effects planned but im lazy to design them
Eye_moves = [ 
    Move('Bloodshot Gaze', 30, 0), #High base attack
    Move('illusory Realm', -20, 2), #Planned stat effect
    Move('Confusion', 0, 0), #Planned stat effect
    Move('Amaterasu', 10, 3) #Planned stat effect and CD
]


#Buttons
classes = button(440, 500, 200, 60, "classes") 
Rematch = button(WIDTH//2 - 150, 500, 150, 60, "Rematch")
Quit = button(WIDTH//2 + 20,  500, 150, 60, "Quit")

#Global Boolean values, basically pages
Menu = True
selection = False
Battle = False
Stats = False 

player = None #Selected class
enemy = None # Eye dude
Move_Buttons = [] #Store moveset of chosen char
turn = 'player' #Turn based combat - turn starts with player
enemy_acted = False #prevents enemy from attacking every frame
Message = '' #Basically terminal but on the actual pygame screen
Selected_class = None #player

#Stats 
dmg_dealt = 0 #Player damage dealt
dmg_taken = 0 
Battle_won = False 


def start_battle(class_name): #Fucntion to Initialize everything
    #globalize all variables first
    global player, enemy, player_hpbar, enemy_hpbar, Move_Buttons
    global turn, enemy_acted, Message, Battle, selection, Menu
    global dmg_dealt, dmg_taken 

    dmg_dealt = 0 #start as 0
    dmg_taken = 0 

    #class_name means the selected class from selection screen
    #Initializes the Character the HealthBar Class depending on which Class u clicked on (No take backs)
    if class_name == 'Sword':
        player = Character("Sword", 110, Sword_moves) #Name, maxhealth, move list - movelist can be reference using index
        player_hpbar = HealthBar(150, 150, 200, 40, 110)
    elif class_name == 'Wizard':
        player = Character("Wizard", 100, Wizard_moves)
        player_hpbar = HealthBar(150, 150, 200, 40, 100)    
    elif class_name == 'Archer':
        player = Character("Archer", 95, Archer_moves)
        player_hpbar = HealthBar(150, 150, 200, 40, 95)
    player_hpbar.set_char(player.name)

    #Initilize the enemy
    enemy = Character('Eye', 80, Eye_moves)
    enemy_hpbar = HealthBar(WIDTH - 365, 75, 200, 40, 80)
    enemy_hpbar.set_char('Eye')
    #Generate MovesUI - one moveset - four moves, four buttons
    #Horizontal spacing by 250 px and vertical spacing by 70
    #two moves per row, two rows
    Move_Buttons = [] #Reset the list
    for i, move in enumerate(player.moves):
        x = 200 + (i % 2) * 500 
        y = 550 + (i // 2) * 70
         #New list that contains the moves from either Sword, wizard, or archer
        Move_Buttons.append(MovesUI(x, y, 220, 50, move)) 

    Battle = True
    selection = False
    Menu = False
    turn = 'player'
    enemy_acted = False    
    #Print check
    Message = (f"{player.name} vs {enemy.name}")#, player's turn!") 
    print(Message) # terminal
    
def player_atk(move_index): #Function for player attack ONLY
    global Message, Battle, turn, enemy_acted, Stats, Battle_won, dmg_dealt
    move = player.use_move(move_index)
    if move is None:
        return

    dmg = move.damage
    if dmg > 0: #Player Attack
        enemy.health -= dmg
        dmg_dealt += dmg
        Message = (f'{move.name} dealt {dmg} damage!')
    elif dmg < 0: #Player Heal (Negative damage -dmg)
            player.health = min(player.health_max, player.health - dmg) #Max health becomes the ceiling, cant heal more than 100 hp
            Message = (f'{move.name} healed {dmg} HP!')

    #Enemy death check
    if enemy.health <= 0:
        Message = (f"{enemy.name} got cooked, winner winner chicken dinner")
        Battle_won = True
        Stats = True #Initiate stats screen (win)
        Battle = False #End battle
    else:
        turn = 'enemy'
        enemy_acted = False #Enemy can act next frame

def enemy_atk():
    global Message, turn, Battle, dmg_taken,Battle_won, Stats, enemy_acted, dmg_taken
    #Finding which moves the enemy can currently use, since enemy also has some moves with CD
    Ready_or_not = [i for i, cd in enumerate(enemy.move_CDs) if cd == 0] #HERE I COME
    if not Ready_or_not: #Incase the enemy randomly chooses a move that is in CD, cause choosing from an empty list will crash
        enemy.dec_CDs()
        turn = 'player'
        Message = 'Enemy is waiting...'
        return

    idx = random.choice(Ready_or_not)
    enemove = enemy.use_move(idx)
    dmg = enemove.damage

    if dmg > 0: #Player Attack
        player.health -= dmg
        dmg_taken += dmg
        Message = (f'{enemove.name} dealt {dmg} damage!')
    elif dmg < 0: #Ememy Heal (Negative damage -dmg)
        enemy.health = min(enemy.health_max, enemy.health - dmg) 
        Message = (f'{enemove.name} healed {dmg} HP!')
    else:
        Message = (f'Eye thought it would be getting shieldHP, sorry this is not fortnite!') #IF the eye tries to use the heal move while having full hp. and if the eye tries to use this move on CD
    #Player death check
    if player.health <= 0:
        Message = (f"{player.name} got cooked, you lose")
        Battle_won = False
        Stats = True #Initiate stats screen (win)
        Battle = False #End battle
    else:
        turn = 'player'
        enemy_acted = True #Enemy can act next frame

def reset(): #Reset game for the same playthrough (rematch)
    global Menu, selection, Battle, Stats, player, enemy, turn, enemy_acted, Message, dmg_dealt, dmg_taken
    Menu = True
    selection = False
    Battle = False
    Stats = False
    player = None 
    enemy = None 
    turn = 'player' 
    enemy_acted = False 
    Message = '' 
    dmg_dealt = 0
    dmg_taken = 0


Rungame = True
while Rungame: 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            Rungame = False

        if Menu:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if classes.is_clicked(pos):
                    Menu = False
                    selection = True
        
        elif selection:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for card in class_cards:
                    if card.is_clicked(pos):
                        start_battle(card.name) #Intialize first func with name of class
                        break

        #breaks every turn after the player has chosen a move. 
        elif Battle:
            if turn == 'player' and event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                for i, btn in enumerate(Move_Buttons): #Moves with CD = 0
                    if btn.clicked(pos) and player.move_ready(i):
                        player_atk(i) #With that specific index move
                        break
        elif Stats:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if Rematch.is_clicked(pos):
                    reset()
                elif Quit.is_clicked(pos):
                    Rungame = False

    #Enemy attack logic
    if Battle and turn == 'enemy' and not enemy_acted and enemy.alive():
        enemy_atk()
    #Decrease cooldown at the start of every player's turn
    if Battle and turn == 'player' and not enemy_acted:
        player.dec_CDs()
        enemy.dec_CDs()

    #Drawing
    if Menu:
        screen.blit(BGmenu, (0, 0))
        classes.draw(screen)
        title_text = Font.render("CLASS BATTLE", True, clrWhite)
        screen.blit(title_text, (430, 150))

    elif selection:
        screen.blit(BGmenu, (0, 0)) #originally had a second background, voided
        HeadTxt = Font.render("SELECT YOUR CLASS", True, clrWhite)
        screen.blit(HeadTxt, (380, 80))
        #Cards of the 3 classes/chars
        for card in class_cards:
            card.draw(screen)
    
    elif Battle:
        #Draw battle background
        screen.blit(BGBattle, (0, 0))

        #Draw player and enemy
        if player and player.name in Battle_files:
            pimg = Battle_files[player.name]
            prect = pimg.get_rect(midbottom = (WIDTH//2 - 250, HEIGHT - 125)) #Better to reference and adjust it from the center 
            screen.blit(pimg, prect)
        if enemy:
            e_img = Enemy_img
            e_rect = pimg.get_rect(midbottom = (WIDTH//2 + 300, HEIGHT - 300))
            screen.blit(e_img, e_rect)

        #Draw health bars
        if player_hpbar:
            player_hpbar.draw(screen, player.health)
        if enemy_hpbar:
            enemy_hpbar.draw(screen, enemy.health)

        #Draw Message
        message_surf = Font.render(Message, True, clrDDGrey)
        screen.blit(message_surf, (WIDTH//2 - message_surf.get_width()//2, 50)) #x, y

        #Draw move buttons only on player's turn
        if turn == 'player':
            pygame.draw.rect(screen, clrDDGrey, (100, 500, 900, 400))
            for i, btn in enumerate(Move_Buttons):
                btn.draw(screen, player.move_CDs[i]) #Passes the Button drawing and the Cooldown # text
    
    #Stats screen, post battle
    elif Stats:
        screen.fill(clrDGrey)
        #title text
        title = Font.render("BATTLE STATS", True, clrWhite)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 100)) #Ensures it centeres correctly given the length of the sentence
        #Draw win or lose text
        result_txt = 'VICTORY' if Battle_won else "DEFEAT"
        result_surf = Font.render(result_txt, True, clrWhite)
        screen.blit(result_surf, (WIDTH//2 - result_surf.get_width()//2, 180))
        #damage dealt and damage taken
        dealt = SmallFont.render(f'Damage Dealt: {dmg_dealt}', True, clrWhite)
        taken = SmallFont.render(f'Damage Taken: {dmg_taken}', True, clrWhite)
        screen.blit(dealt, (WIDTH//2 - dealt.get_width()//2, 280))
        screen.blit(taken, (WIDTH//2 - taken.get_width()//2, 320))

        #Rematch / quit 
        Rematch.draw(screen)
        Quit.draw(screen)

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
sys.exit()

