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

#Second button type for player battle UI 
# blits the name of the move, rect, and CD text if move has an active CD
# clicking returns a bool to trigger the player_atk() function through the
# Move_Buttons list
class MovesUI: 
    def __init__(self, x, y, width, height, move):
        self.rect = pygame.Rect(x, y, width, height)
        self.move = move

    def draw(self, screen, CD = 0): 
        color = Color['DGrey'] if CD == 0 else Color['DGrey'] #UI change Doesn't work - debug
        pygame.draw.rect(screen, color, self.rect)
        Textscreen = Font.render(self.move.name, True, Color['White'])
        Textrender = Textscreen.get_rect(center = self.rect.center)
        screen.blit(Textscreen, Textrender)

        if CD > 0:
            cd_text = SmallFont.render(f"CD:{CD}", True, Color['LRed']) #Displays the cooldown turn timer
            cd_rect = cd_text.get_rect(topright = (self.rect.right-5, self.rect.top+5)) #On the top right
            screen.blit (cd_text, cd_rect)
    
    def clicked (self, pos): #Return the click bool
        return self.rect.collidepoint(pos) 


class HPBAR:
    def __init__(self, max_hp):
        self.max_hp = max_hp
        self.hp_frame = load_img(asset('hud', 'HPBar_frame.png')).convert_alpha() 
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

    def draw_hp(self, screen, x, y, turn_hp, max_hp):   
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
