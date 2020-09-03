import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import sys
import pygame
from race import *
from fuzzy_car import FuzzyAlgorithm

track = Track('./tracks/track_7.txt')

window_width = track.size[0] + 128
window_height = track.size[1]

flags = DOUBLEBUF
pygame.init()
window = pygame.display.set_mode((window_width, window_height), flags, 32)

pygame.event.set_allowed([QUIT])

pygame.display.set_caption('')


def terminate():
    pygame.quit()
    sys.exit()


race = Race(track)

genetic_algorithm = FuzzyAlgorithm(race, ray_count=7, additional_front_ray_count=0, population=1)

time_0 = perf_counter()

clock = pygame.time.Clock()
rays_v = True
while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            terminate()
        if event.type == KEYDOWN:
            if event.key == K_r:
                race.remove_all_cars()
                genetic_algorithm = FuzzyAlgorithm(race, ray_count=7, additional_front_ray_count=0, population=3)
            if event.key == K_t:
                genetic_algorithm.getCar().rays_v = False if genetic_algorithm.getCar().rays_v else True
        race.handle_event(event)

    delta_time, time_0 = perf_counter() - time_0, perf_counter()

    race.run(delta_time)

    race.draw(window, 0)

    draw_text(window, (255,) * 3, f'fps: {int(1 / delta_time):4d}', (0, 0), 16, 'topleft')

    pygame.display.update()
