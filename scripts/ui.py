#General User Interface
#Button, Cards, MovesUI, HealthBar
import pygame
from scripts.draw_load import Color, Font, SmallFont, SmallestFont, Char_cards, Effect_icons, Item_icons, Icon_base, load_img, asset

#Card button 
#And Card organization/format
class Cards: 
    def __init__(self, name, image, x, y, width = 200, height = 200):
        self.name = name #assets
        self.image = pygame.transform.scale(image, (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.selected = False #Border UX boolean trigger - This doesn't work 
        
    def draw(self, screen):
        border_color = Color['White'] if self.selected else Color['DGrey']  #improve UX - Mouse hover (Doesn't work yet)
        pygame.draw.rect(screen, border_color, self.rect, 10)
        screen.blit(self.image, self.rect)                      #surf and rect in that order
        name_txt = Font.render(self.name, True, Color['White'])
        name_rect = name_txt.get_rect(center=(self.rect.center))#center text
        screen.blit(name_txt, name_rect)                        #Name of class, img of class

    def is_clicked (self, pos):
        return self.rect.collidepoint(pos) #Mousebutton down interaction

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


#First button type for Menu class selection
class button: 
    def __init__(self, x, y, width, height, text, fill_color = Color['Grey'], border_color = Color['DGrey']):
        self.rect = pygame.Rect(x, y, width, height)
        self.fill_color = fill_color
        self.border_color = border_color
        self.text = text
        self.font = Font
    
    def draw(self, screen):
        pygame.draw.rect(screen, Color['Grey'], self.rect)
        pygame.draw.rect(screen, Color['DGrey'], self.rect, 7)
        TxtS = self.font.render(self.text, True, Color['White'])
        TxtR = TxtS.get_rect(center=self.rect.center)
        screen.blit(TxtS, TxtR)

    def is_clicked (self, pos):
        return self.rect.collidepoint(pos) #Collidepoint (on click)

#Slot state slot grid
def slot_grid (slot_labels, start_x, start_y, spacing_x, spacing_y, width = 200, height = 100):
    slots = []
    cols = 3
    for i, txt in enumerate(slot_labels):
        row = i // cols
        col = i % cols
        x = start_x + (col * spacing_x)
        y = start_y + (row * spacing_y)
        #if txt:
        slot = button( x, y, width, height, txt)    
        slots.append(slot)
    return slots

slot_buttons = slot_grid(
    ['Slot 1', 'Slot 2', 'Slot 3'],
    start_x=128,# Starting X position
    start_y=225,# Starting Y position  
    spacing_x=280,# Horizontal spacing
    spacing_y=350,# Vertical spacing
    width=260,#true toggle for size
    height=260,
)

#=====================================================================
#Battle HUD
#----------------------------------------------------------------------
#Semi transparent plates (same fill + border everywhere), laid out on the
#old Box2-Box5 test rectangles:
#   TURN_BOX   - turn counter, top left
#   MSG_BOX    - system message, top centre
#   ENEMY_BOX  - enemy name, HP bar, status effects (top right)
#   PLAYER_BOX - class, level, HP bar + numbers, status effects (bottom left)
#Moves sit in a WASD diamond bottom right, on top of the BattleFog backdrop.
#======================================================================
HUD_FILL = (14, 12, 28, 200)       #near black purple, semi transparent
HUD_EDGE = (150, 142, 186)         #lavender border (same as the fog)
HUD_TEXT = (230, 226, 240)
HUD_DIM = (150, 142, 186)
HUD_GLOW = (124, 221, 187)         #cyan - move is ready
HUD_DULL = (80, 76, 110)           #move is locked / cooling down

TURN_BOX = pygame.Rect(25, 25, 125, 40)
MSG_BOX = pygame.Rect(290, 25, 500, 32)
ENEMY_BOX = pygame.Rect(715, 75, 340, 110)
PLAYER_BOX = pygame.Rect(25, 535, 380, 160)
BOSSES = {'Judgement'}             #gets a BOSS tag instead of the floor number


def draw_panel(screen, rect, fill = HUD_FILL, edge = HUD_EDGE, width = 2):
    plate = pygame.Surface(rect.size, pygame.SRCALPHA)
    plate.fill(fill)
    screen.blit(plate, rect.topleft)
    pygame.draw.rect(screen, edge, rect, width)


def draw_battle_hud(screen, game):
    #Turn counter (turn_num starts at 0)
    draw_panel(screen, TURN_BOX)
    turn = SmallFont.render(f"TURN {game.turn_num + 1}", True, HUD_TEXT)
    screen.blit(turn, turn.get_rect(center = TURN_BOX.center))

    #System message
    draw_panel(screen, MSG_BOX)
    msg = SmallFont.render(game.message, True, HUD_TEXT)
    screen.blit(msg, msg.get_rect(center = MSG_BOX.center))

    #Enemy plate: tag + name, HP bar, effects under the bar (inside the plate)
    if game.enemy and game.enemy_hpbar:
        box = ENEMY_BOX
        draw_panel(screen, box)
        tag = 'BOSS' if game.enemy.name in BOSSES else f'FLOOR {game.dungeon_level}'
        tag_s = SmallFont.render(tag, True, HUD_DIM)
        name_s = SmallFont.render(game.enemy.name.upper(), True, HUD_TEXT)
        screen.blit(tag_s, (box.x + 12, box.y + 8))
        screen.blit(name_s, name_s.get_rect(topright = (box.right - 12, box.y + 8)))
        game.enemy_hpbar.draw_hp(screen, box.x + 12, box.y + 28,
                                 game.enemy.health, game.enemy.health_max, label = False)
        if game.enemy_effects is not None:
            game.enemy_effects.draw(screen, game.enemy)

    #Player plate: class + level, HP bar + numbers, effects under the bar
    if game.player and game.player_hpbar:
        box = PLAYER_BOX
        draw_panel(screen, box)
        name_s = SmallFont.render(game.player.name.upper(), True, HUD_TEXT)
        lv_s = SmallFont.render(f"LV {game.player.power + 1}", True, HUD_DIM)
        screen.blit(name_s, (box.x + 12, box.y + 26))
        screen.blit(lv_s, lv_s.get_rect(topright = (box.right - 12, box.y + 26)))
        game.player_hpbar.draw_hp(screen, box.x + 12, box.y + 50,
                                  game.player.health, game.player.health_max, label = False)
        hp_s = SmallFont.render(f"{int(game.player.health)}/{int(game.player.health_max)}", True, HUD_TEXT)
        screen.blit(hp_s, hp_s.get_rect(midright = (box.right - 12, box.y + 70)))
        if game.player_effects is not None:
            game.player_effects.draw(screen, game.player)


#Moves: one button per move, placed on a diamond and bound to WASD
#(arrow keys work too). Index 0 = top/W, 1 = left/A, 2 = right/D, 3 = bottom/S
MOVE_KEYS = ['W', 'A', 'D', 'S']
KEY_TO_SLOT = {pygame.K_w: 'W', pygame.K_UP: 'W',
               pygame.K_a: 'A', pygame.K_LEFT: 'A',
               pygame.K_d: 'D', pygame.K_RIGHT: 'D',
               pygame.K_s: 'S', pygame.K_DOWN: 'S'}
DIAMOND_CENTRE = (878, 622)
DIAMOND_OFFSETS = [(0, -53), (-92, 0), (92, 0), (0, 53)]
MOVE_W, MOVE_H = 164, 46
KEY_TAB = 22

#Diamond shape
class MovesUI:
    def __init__(self, index, move):
        self.move_index = index
        self.move = move
        self.key = MOVE_KEYS[index]
        dx, dy = DIAMOND_OFFSETS[index]
        self.rect = pygame.Rect(0, 0, MOVE_W, MOVE_H)
        self.rect.center = (DIAMOND_CENTRE[0] + dx, DIAMOND_CENTRE[1] + dy)

    def usable(self, player):
        return player.move_unlocked(self.move_index) and player.move_ready(self.move_index)

    def draw(self, screen, player, my_turn):
        locked = not player.move_unlocked(self.move_index)
        cd = player.move_CDs[self.move_index]
        active = my_turn and not locked and cd == 0

        if active:   #soft pulsing cyan glow around ready moves
            pulse = 60 + int(30 * abs(((pygame.time.get_ticks() // 20) % 100) - 50) / 50)
            glow = pygame.Surface((MOVE_W + 8, MOVE_H + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*HUD_GLOW, pulse), glow.get_rect(), border_radius = 3)
            screen.blit(glow, (self.rect.x - 4, self.rect.y - 4))

        edge = HUD_GLOW if active else HUD_DULL
        draw_panel(screen, self.rect, fill = (40, 36, 64, 235) if active else (24, 22, 40, 200), edge = edge)
        tab = pygame.Rect(self.rect.x, self.rect.y, KEY_TAB, MOVE_H)
        pygame.draw.rect(screen, edge, tab)
        key_s = SmallFont.render(self.key, True, (14, 12, 28))
        screen.blit(key_s, key_s.get_rect(center = tab.center))

        sub = f"LV {self.move.unlock + 1}" if locked else (f"CD {cd}" if cd > 0 else '')
        name_s = SmallFont.render(self.move.name, True, HUD_TEXT if active else HUD_DIM)
        text_x = tab.right + 8
        if sub:
            screen.blit(name_s, name_s.get_rect(midleft = (text_x, self.rect.centery - 8)))
            sub_s = SmallFont.render(sub, True, HUD_DIM)
            screen.blit(sub_s, sub_s.get_rect(midleft = (text_x, self.rect.centery + 10)))
        else:
            screen.blit(name_s, name_s.get_rect(midleft = (text_x, self.rect.centery)))

    def clicked(self, pos): #Return the click bool
        return self.rect.collidepoint(pos)


def move_for_key(buttons, key):
    slot = KEY_TO_SLOT.get(key)
    for btn in buttons:
        if btn.key == slot:
            return btn
    return None


def draw_move_panel(screen, game, fog):
    screen.blit(fog, (0, 0))
    my_turn = game.turn == 'player'
    if not my_turn:
        wait = SmallFont.render("ENEMY TURN", True, HUD_DIM)
        screen.blit(wait, wait.get_rect(center = (DIAMOND_CENTRE[0], DIAMOND_CENTRE[1] - 102)))
    for btn in game.move_buttons:
        btn.draw(screen, game.player, my_turn)


class HPBAR:
    def __init__(self, max_hp, frame = 'HPBar_frame.png'): #Switch player and enemy frames
        self.max_hp = max_hp
        self.hp_frame = load_img(asset('hud', frame)).convert_alpha()
        self.hp_bg = load_img(asset('hud', 'HPBar_bgfill.png')).convert_alpha() 
        self.hp_fill = load_img(asset('hud', 'HPBar_fill.png')).convert_alpha()
        self.char_name = ''
        self.anim_hp = None
        #Save dimensions for stat effects
        self.width = self.hp_frame.get_width() 
        self.height = self.hp_frame.get_height()
        self.x, self.y = 0, 0 #updates


    def set_char(self, name):
        self.char_name = name

    def draw_hp(self, screen, x, y, turn_hp, max_hp, label = True):   #label = HP text inside the bar
        self.x, self.y = x, y
        screen.blit(self.hp_bg, (self.x, self.y)) #Bg

        if self.anim_hp is None:
            self.anim_hp = float(turn_hp)

        diff = turn_hp - self.anim_hp
        if abs(diff) < 0.1:
            self.anim_hp = float(turn_hp)
        else:
            self.anim_hp += diff * 0.1

        ratio = 0.0 if max_hp <= 0 else max(0.0, min(1.0, self.anim_hp / max_hp))#clamp
        fill = int(self.hp_fill.get_width() * ratio) 

        if fill >  0: # xp gain
            visible = pygame.Rect(0, 0, fill, self.hp_fill.get_height())
            screen.blit(self.hp_fill, (self.x, self.y), visible)

        text = SmallFont.render(f"HP: {int(turn_hp)}/{max_hp}", True, Color['White'])
        text_rect = text.get_rect(center = (self.x + 125 , self.y + 20)) #Position text at the center of hp bar
        screen.blit(self.hp_frame, (self.x, self.y)) #frame, should be on top of everything else
        if label:
            screen.blit(text, text_rect)

class TestRect:
    def __init__(self, x, y, width, height, color):
        self.rect = (x, y, width, height)
        self.color = color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)


#Effect Icons
class EffectsUI():
    ICON = 32
    GAP = 4

    def __init__(self, bar):
        self.bar = bar

    def draw(self, surf, character):
        x = self.bar.x
        y = self.bar.y + self.bar.height + 4
        for effect in character.statuses: #statuses []
            icon = Effect_icons.get(effect.name)
            if icon:
                icon.set_alpha(128 if effect.duration == 1 else 255)
                surf.blit(icon, (x, y))
                if effect.duration > 0:
                    duration_txt = SmallestFont.render(f"{str(effect.duration)}", True, Color['White']) #Displays the cooldown turn timer
                    duration_rect = duration_txt.get_rect(topright = (x + self.ICON - 2, y + 2)) #On the top right
                    surf.blit(duration_txt, duration_rect)
            else:   #no icon art yet: a small plate with the first two letters
                slot = pygame.Rect(x, y, self.ICON, self.ICON)
                draw_panel(surf, slot, edge = HUD_DULL)
                abbr = SmallFont.render(effect.name[:2].upper(), True, HUD_DIM)
                surf.blit(abbr, abbr.get_rect(center = slot.center))

            x += self.ICON + self.GAP #runs even if theres no icon


#Explore UI: experimental function
class XPBAR:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.xp_frame = load_img(asset('hud', 'XPBar_frame.png')).convert_alpha() #Frame 
        self.xp_bg = load_img(asset('hud', 'XPBar_bgfill.png')).convert_alpha() #background color
        self.xp_fill = load_img(asset('hud', 'XPBar_fill.png')).convert_alpha() #fill 
        self.anim_xp = None 

    def draw_xp(self, screen, current_xp, max_xp):
        
        screen.blit(self.xp_bg, (self.x, self.y)) #Bg

        if self.anim_xp is None:
            self.anim_xp = float(current_xp)

        diff = current_xp - self.anim_xp
        if abs(diff) < 0.1:
            self.anim_xp = float(current_xp)
        else:
            self.anim_xp += diff * 0.1

        ratio = 0.0 if max_xp <= 0 else max(0.0, min(1.0, self.anim_xp / max_xp))#clamp
        fill = int(self.xp_fill.get_width() * ratio) 

        if fill >  0: # xp gain
            visible = pygame.Rect(0, 0, fill, self.xp_fill.get_height())
            screen.blit(self.xp_fill, (self.x, self.y), visible)
            
        text = SmallFont.render(f'XP: {current_xp}/{max_xp}', True, Color['White'])
        text_rect = text.get_rect(center = (self.x + 112 , self.y + 16)) #Position text at the center of hp bar
        screen.blit(self.xp_frame, (self.x, self.y)) #frame, should be on top of everything else
        screen.blit(text, text_rect)
        


#=====================================================================
#Buff badges: which item is running, and how long is left
#----------------------------------------------------------------------
#Icon Base sits underneath, the item's own icon on top (the item art is
#mostly transparent, so the plate shows around it), then the seconds
#remaining, then a thin bar that drains as the buff runs out.
#======================================================================
class BuffBar:
    ICON = 32
    GAP = 8
    BAR_H = 4

    def __init__(self, x, y):
        self.x, self.y = x, y

    def draw(self, screen, game):
        x = self.x
        for buff in game.active_buffs:
            screen.blit(Icon_base, (x, self.y)) #base

            icon = Item_icons.get(buff['name'])
            if icon:
                screen.blit(icon, (x, self.y)) #icon

            #Seconds remaining, rounded UP so it only shows 0 when it is gone
            seconds = max(0, -(-buff['ms_left'] // 1000))
            label = SmallestFont.render(str(seconds), True, Color['White'])
            screen.blit(label, label.get_rect(bottomright = (x + self.ICON - 2,
                                                             self.y + self.ICON - 1)))

            #Drain bar under the plate
            total = max(1, buff['ms_total'])
            
            fill = int(self.ICON * max(0, buff['ms_left']) / total)
            bar_y = self.y + self.ICON + 1
            pygame.draw.rect(screen, Color['DDGrey'], (x, bar_y, self.ICON, self.BAR_H))
            if fill > 0:
                pygame.draw.rect(screen, Color['Gold'], (x, bar_y, fill, self.BAR_H))

            x += self.ICON + self.GAP
