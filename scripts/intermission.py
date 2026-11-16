#intermission / transition handler

import pygame
from scripts.gamestate import State, Game 

#Intermission
def begin_intermission(game, destination):
    game.destination = destination
    game.started = pygame.time.get_ticks()
    game.state = State.intermission