from pygame import surfarray
from pygame.locals import *
from time import perf_counter
import cv2
import numpy as np
from random import random
import math

from util import *
from car_m import *
from track import *

class Race_Client(object):
    def __init__(self, track):
        self.winner = None
        self.__track = track
        self.__finish_line = self.__track.finish_line
        self.__cars = []
        self.__time_to_go = 5
        self.__waiting = 1
        self.__active_bonuses = []
        self.ping = [0]*50

    def start_count(self):
        self.__waiting = 0

    def set_ping(self, ping, pos):
        self.ping[pos] = ping

    def set_winner(self, winner):
        self.winner = winner

    def started(self):
        return self.__time_to_go < 0

    def add_car(self, car):
        r = .2 + .6*random()
        car.pos[:] = self.__finish_line[0]*r + self.__finish_line[1]*(1-r)
        car.pos[0] -= 16
        car.start_pos = np.copy(car.pos)
        car.on_finish = -1
        car.lap_start_time = None
        car.lap_time = None
        car.add_time = perf_counter()
        car.best_lap_time = None
        car.laps = -1
        car.collision = 0.
        car.prev_lap_collision = 0.
        car.bonuses = []
        car.laps_to_go = 5
        self.__cars.append(car)
    
    def remove_car(self, car):
        if car in self.__cars:
            self.__cars.remove(car)
            return True
        return False
    
    def remove_all_cars(self):
        self.__cars.clear()
    
    def contain_car(self, car):
        return car in self.__cars

    def update_times_of_cars(self, times):
        for i in range(len(self.__cars)):
            self.__cars[i].lap_start_time = times[i][0]
            self.__cars[i].lap_time = times[i][1]
            self.__cars[i].laps = times[i][2]
            self.__cars[i].best_lap_time = times[i][3]
            self.__cars[i].laps_to_go = times[i][4]

    def update_car_bonuses(self, bonuses):
        for i, car in enumerate(self.__cars):
            car.bonuses = bonuses[i]

    def update_map_bonuses(self, buff):
        self.__active_bonuses = buff

    def draw(self, surface, delta_time, best_car_idx=None, no_scores=False):
        surface.fill((0, 0, 0))
        updated_rects = []
        updated_rects.extend(
            self.__track.draw(surface))

        # _ drawing bonuses on map
        for bonus in self.__active_bonuses:
            if bonus["type"] in ("SpeedUP", "SwapyyyKeys"):
                updated_rects.append(
                     draw.circle(surface, bonus["color"], (bonus["pos"]).astype(np.int32), 8))
            elif bonus["type"] in ("SlowDOWN", "Freeze"):
                triangle = [x + bonus["pos"] for x in [[0, 0], [7, -12], [14, 0]]]
                updated_rects.append(
                    draw.polygon(surface, bonus["color"], triangle))

        # _ First Row of Scores
        # _ name
        updated_rects.append(draw_text(surface, (255,) * 3, 'Player name', (self.__track.size[0]-96, 16), 16, 'topleft'))
        # _ laps number
        updated_rects.append(draw_text(surface, (255,) * 3, f'Laps', (self.__track.size[0] + 16, 16), 16, 'topleft'))
        # _ current lap time
        updated_rects.append(draw_text(surface, (255,) * 3, 'This LapTime', (self.__track.size[0]+64, 16), 16, 'topleft'))
        # _ best lap time
        updated_rects.append(draw_text(surface, (255,) * 3, 'Best LapTime', (self.__track.size[0] + 160, 16), 16, 'topleft'))
        # _ ping
        updated_rects.append(
            draw_text(surface, (255,) * 3, f'{int(sum(self.ping)/len(self.ping)*1000)}ms', (16, 16), 16, 'topleft'))
        # _ drawing cars
        for i, car in enumerate(self.__cars):
            if best_car_idx is None or best_car_idx == i:
                updated_rects.extend(car.draw(surface, car.bonuses))
            else:
                updated_rects.append(draw.circle(surface, (0, 0, 255), car.pos, 2))
            if not no_scores:
                updated_rects.append(   # _ name
                    draw_text(surface, car.color, car.name, (self.__track.size[0]-104, i*32+48), 16, 'topleft'))
                for j, bns in enumerate(car.bonuses):   # _ bonuses
                    updated_rects.append(
                        draw_text(surface, bns["color"], f"{math.ceil(bns['time_active'])}",
                                  (self.__track.size[0] - 48+16*j, i * 32 + 48), 16, 'topleft'))

                updated_rects.append(   # _ laps number
                    draw_text(surface, (255,) * 3, f'{abs(int(car.laps_to_go)-5)}/5',
                                                            (self.__track.size[0] + 16, i * 32 + 48), 16, 'topleft'))
                if car.lap_time is not None:
                    updated_rects.append(   # _  current lap time
                        draw_text(surface, (255,)*3, f'{(0.0 if math.isnan(car.lap_time) else car.lap_time):8.2f}',
                                  (self.__track.size[0]+64, i*32 + 48), 16, 'topleft'))
                if car.best_lap_time is not None:
                    updated_rects.append(   # _ best lap time
                        draw_text(surface, (255,)*3, f'{(0.0 if math.isnan(car.best_lap_time) else car.best_lap_time):8.2f}',
                                  (self.__track.size[0] + 160, i*32 + 48), 16, 'topleft'))
        # _ drawing legend
        bonuses = [
            {"type": "Freeze", "color": (50, 50, 200)},
            {"type": "SlowDOWN", "color": (200, 0, 0)},
            {"type": "SwapyyyKeys", "color": (255, 51, 255)},
            {"type": "SpeedUP", "color": (0, 200, 0)}
        ]
        updated_rects.append(
            draw_text(surface, (255,)*3, 'Bonuses legend (color = bonus)',
                      (self.__track.size[0] + 32, self.__track.size[1] - 112), 16, 'bottomleft'))
        for i,bonus in enumerate(bonuses):
            updated_rects.append(
                draw_text(surface, bonus["color"], bonus["type"], (self.__track.size[0]+64, self.__track.size[1]-96+i*16), 16, 'bottomleft'))

        if self.winner is not None:
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                updated_rects.append(draw_text(surface, (0,)*3, f'{self.winner} has won!', (self.__track.size[0]/2 + dx*2, self.__track.size[1]/2 + dy*2), 64))
            updated_rects.append(draw_text(surface, (255,)*3, f'{self.winner} has won!', (self.__track.size[0]/2, self.__track.size[1]/2), 64))

        if 0.3 > self.__time_to_go > 0.0 and self.__waiting == 0:     # _ if time is less than 0.3 sec display start
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                updated_rects.append(draw_text(surface, (0,)*3, 'START', (self.__track.size[0]/2 + dx*2, self.__track.size[1]/2 + dy*2), 128))
            updated_rects.append(draw_text(surface, (255,)*3, 'START', (self.__track.size[0]/2, self.__track.size[1]/2), 128))

        if self.__time_to_go >= 0.3 and self.__waiting == 0:
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                updated_rects.append(draw_text(surface, (0,)*3, f'{int(self.__time_to_go)}', (self.__track.size[0]/2 + dx*2, self.__track.size[1]/2 + dy*2), 256))
            updated_rects.append(draw_text(surface, (255,)*3, f'{int(self.__time_to_go)}', (self.__track.size[0]/2, self.__track.size[1]/2), 256))
        if self.__time_to_go >= 0 and self.__waiting == 1:
            updated_rects.append(
                draw_text(surface, (225, 200, 0), "Waiting for other players", (self.__track.size[0]/2 + 30, 30), 25))
        delta_time = min(delta_time, .05)
        self.__time_to_go -= delta_time
        return updated_rects


