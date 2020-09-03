import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import sys
import pygame
from pygame.locals import *
from time import perf_counter
import cv2
import numpy as np

from util import *
from car import *
from race import *
from track import *

track = Track('./tracks/track_2.txt')

window_width = track.size[0] + 128
window_height = track.size[1]

pygame.init()
window = pygame.display.set_mode((window_width, window_height), 0, 32)

pygame.display.set_caption('')

def terminate():
    pygame.quit()
    sys.exit()

race = Race(track)

race.add_car(Car())

time_0 = perf_counter()

clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            terminate()
        race.handle_event(event)
            
    delta_time, time_0 = perf_counter() - time_0, perf_counter()
    
    race.run(delta_time)
    
    race.draw(window)
    
    print(end=f'\r{1/delta_time:.2f}')
    pygame.display.update()