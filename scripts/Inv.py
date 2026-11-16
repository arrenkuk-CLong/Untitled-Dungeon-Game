#Inventory
#Inv Class and UI

import pygame, random
from scripts.draw_load import Color, Font, load_img, asset, SmallFont, Item_icons


#What each item DOES.
ITEM_EFFECTS = {
    "Health Potion":        {"kind": "heal", "heal": 20, "where": "any"},
    "Greater Health Potion":{"kind": "heal", "heal": 40, "where": "any"},
    #strength 0.5 = enemies notice you from half as far
    "Shadow Cloak":         {"kind": "hide", "seconds": 20, "strength": 0.5,
                             "where": "explore"},
    #strength 0.0 = enemies cannot see you at all
    "Invisibility Potion":  {"kind": "hide", "seconds": 10, "strength": 0.0,
                             "where": "explore"},
    "XP Scroll":            {"kind": "xp", "seconds": 120, "where": "any"},
    "Teleportation Scroll": {"kind": "teleport", "where": "explore"},
}


#=====================================================================
#Item buffs
#----------------------------------------------------------------------
#Durations are real seconds, but on OUR clock, not the wall clock:
#tick_buffs() is only called while the player is exploring, so the
#countdown freezes during a battle and resumes when the fight ends.
#======================================================================

def add_buff(game, name, kind, seconds, strength = 1.0):
    for buff in game.active_buffs:
        if buff['name'] == name:                    #same item again: refresh
            buff['ms_left'] = max(buff['ms_left'], int(seconds * 1000))
            buff['ms_total'] = max(buff['ms_total'], buff['ms_left'])
            return
    game.active_buffs.append({'name': name, 'kind': kind,
                              'ms_left': int(seconds * 1000),
                              'ms_total': int(seconds * 1000),
                              'strength': strength})


def tick_buffs(game, dt_ms):
    #dt_ms is what clock.tick() returned, so this is real time
    for buff in game.active_buffs:
        buff['ms_left'] -= dt_ms
    expired = [b['name'] for b in game.active_buffs if b['ms_left'] <= 0]
    if expired:
        game.active_buffs = [b for b in game.active_buffs if b['ms_left'] > 0]
        game.message = '%s wore off' % expired[0]


def has_buff(game, kind):
    return any(b['kind'] == kind for b in game.active_buffs)


def buff_strength(game, kind, default = 1.0):
    #Strongest wins: invisibility (0.0) beats the cloak (0.5)
    values = [b['strength'] for b in game.active_buffs if b['kind'] == kind]
    return min(values) if values else default

def random_walkable_tile(game):
    #A floor tile with nothing standing on it - avoid teleporting onto enemy tile
    taken = {(f['x'], f['y']) for f in game.dungeon_enemies}
    spots = [(x, y)
             for x in range(game.dungeon.width)
             for y in range(game.dungeon.height)
             if game.dungeon.is_walkable(x, y)
             and (x, y) not in taken
             and (x, y) != game.player_tile]
    return random.choice(spots) if spots else None


#Inventory Icon UI
class inventory_UI():
    ICON = 32   #Icon is drawn at 64x64 (the pngs are 256x256)
    #CHANGE to 32

    def __init__(self, x, y, width, height, text, fill_color = Color['Brown2'], border_color = Color['Brown3']):
        #Inv box
        self.rect = pygame.Rect(x, y, width, height)
        self.fill_color = fill_color
        self.border_color = border_color
        self.text = text
        self.font = Font

        self.is_open = False
        self.bag_closed = load_img(asset('Icons', 'Sack_closed.png'), (self.ICON, self.ICON))
        self.bag_open = load_img(asset('Icons', 'Sack_open.png'), (self.ICON, self.ICON))
        self.icon_rect = pygame.Rect(980, 8, self.ICON, self.ICON)
        self.use_buttons = []   

    def draw(self, screen, inventory):
        pygame.draw.rect(screen, Color['Brown2'], self.rect)
        pygame.draw.rect(screen, Color['Brown3'], self.rect, 7)
        TxtS = self.font.render(self.text, True, Color['Brown3'])
        TxtR = TxtS.get_rect(topleft=(730, 75))
        screen.blit(TxtS, TxtR)

        self.use_buttons = []
        rows = inventory.rows()
        if not rows:
            empty = SmallFont.render('(empty)', True, Color['Brown3'])
            screen.blit(empty, (self.rect.left + 20, self.rect.top + 90))
            return

        y = self.rect.top + 85
        for name, qty in rows:

            icon = Item_icons.get(name)
            if icon:
                screen.blit(icon, (self.rect.left + 14, y))
            label = SmallFont.render(f'{name} x{qty}', True, Color['White'])
            screen.blit(label, (self.rect.left + 14 + self.ICON + 6, y + 6))

            btn = pygame.Rect(self.rect.right - 78, y, 60, 32)
            pygame.draw.rect(screen, Color['Brown3'], btn)
            pygame.draw.rect(screen, Color['Brown2'], btn, 3)
            use_txt = SmallFont.render('USE', True, Color['White'])
            screen.blit(use_txt, use_txt.get_rect(center = btn.center))
            self.use_buttons.append((btn, name))

            y += 46      #Next row

    def toggle(self):
        self.is_open = not self.is_open  #T/F of bag icon

    def use_button_at(self, pos):
        #Which item's USE button was clicked (
        if not self.is_open:
            return None
        for btn, name in self.use_buttons:
            if btn.collidepoint(pos):
                return name
        return None

    def drawicon (self, screen):
        if self.is_open:
            screen.blit(self.bag_open, self.icon_rect)
        else:
            screen.blit(self.bag_closed, self.icon_rect)

#JSON inventory management
class Inventory():
    def __init__(self):
        self.items = {}     #name -> {"quantity": n, plus whatever ITEM_EFFECTS says}

    def add_item(self, name, quantity = 1):
        if name in self.items:
            self.items[name]["quantity"] += quantity    #Stack, don't duplicate
        else:
            entry = dict(ITEM_EFFECTS.get(name, {}))    #Copy, so editing one
            entry["quantity"] = quantity                #potion's data later
            self.items[name] = entry                    #can't edit every potion
        return f'Picked up {name} (x{self.items[name]["quantity"]})'

    def use_item(self, name, game):
        entry = self.items.get(name)
        if not entry or entry["quantity"] <= 0:
            return f'No {name} left'

        player = game.player
        kind = entry.get("kind")

        #Explore state only items 
        if entry.get("where") == "explore" and game.dungeon is None:
            return f'{name} can only be used in the dungeon'

        if kind == "heal":
            heal = entry.get("heal", 0)
            if player.health >= player.health_max:
                return 'Already at full HP'     #don't waste it
            player.health = min(player.health_max, player.health + heal)
            message = f'Used {name}, healed {heal} HP ({player.health}/{player.health_max})'

        elif kind == "hide":
            seconds = entry.get("seconds", 0)
            strength = entry.get("strength", 1.0)
            add_buff(game, name, "hide", seconds, strength)
            if strength <= 0:
                message = f'Used {name}, invisible for {seconds}s'
            else:
                message = f'Used {name}, harder to spot for {seconds}s'

        elif kind == "xp":
            seconds = entry.get("seconds", 0)
            add_buff(game, name, "xp", seconds)
            message = f'Used {name}, double XP for {seconds}s'

        elif kind == "teleport":
            spot = random_walkable_tile(game)
            if spot is None:
                return 'Nowhere to teleport to'
            game.player_tile = spot
            message = f'Used {name}, blinked to {spot}'

        else:
            return f'{name} does nothing yet'

        entry["quantity"] -= 1
        if entry["quantity"] <= 0:
            del self.items[name]
        return message

    def rows(self):
        #What the UI draws: [(name, quantity)], sorted so the list never
        #reshuffles under the player's cursor between frames
        return sorted((name, data["quantity"]) for name, data in self.items.items())

    def clear(self):
        self.items = {}