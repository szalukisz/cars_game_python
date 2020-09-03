from pygame import surfarray
from pygame.locals import *
from time import perf_counter
import cv2
import numpy as np
from random import random

from util import *
from car import *
from track import *

class Race(object):
    def __init__(self, track):
        self.__track = track
        self.__finish_line = self.__track.finish_line
        self.__cars = []
        self.__time_to_go = 1
        
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
    
    def handle_event(self, event):
        for car in self.__cars:
            car.handle_event(event)
    
    def run(self, delta_time):
        delta_time = min(delta_time, .05)
        
        if self.__time_to_go < 0:
            collisions = self.__track.collision_with_cars(self.__cars)
            for i, car in enumerate(self.__cars):
                if car.lap_start_time is not None:
                    car.lap_time = perf_counter() - car.lap_start_time
                    if car.best_lap_time is None or car.best_lap_time > 1e3:
                        tmp = self.__track.inner_points - car.pos
                        car.best_lap_time = 1e4 - np.argmin(np.sum(tmp*tmp, axis=1))
                car.run(delta_time, collisions[i], self.__track)
                if np.linalg.norm(collisions[i]) > 0:
                    car.collision += delta_time
                
                finish_unit_vector = self.__finish_line[1] - self.__finish_line[0]
                finish_unit_vector /= np.linalg.norm(finish_unit_vector)
                if -0.3 < np.dot((car.pos - self.__finish_line[0])/np.linalg.norm(car.pos - self.__finish_line[0]), finish_unit_vector) < 1.3:
                    finish_unit_normal = np.zeros(2)
                    finish_unit_normal[0] = finish_unit_vector[1]
                    finish_unit_normal[1] = -finish_unit_vector[0]
                    
                    dot_prod = np.dot(car.pos - self.__finish_line[0], finish_unit_normal)
                    if 0 < dot_prod < 32:
                        if car.on_finish == 1:
                            car.laps -= 1
                            car.prev_lap_collision = car.collision
                            car.collision = 0
                            car.lap_start_time = None
                            car.lap_time = None
                        car.on_finish = -1
                    elif -32 < dot_prod < 0:
                        if car.on_finish == -1:
                            car.laps += 1
                            car.prev_lap_collision = car.collision
                            car.collision = 0
                            if car.lap_time is not None and\
                               (car.best_lap_time is None or car.best_lap_time > car.lap_time):
                                car.best_lap_time = car.lap_time
                            car.lap_start_time = perf_counter()
                        car.on_finish = 1
                else:
                    car.on_finish = 0
        else:
            self.__time_to_go -= delta_time


    def draw(self, surface, best_car_idx=None, no_scores=False):
        surface.fill((0, 0, 0))
        updated_rects = []
        updated_rects.extend(
            self.__track.draw(surface))
        
        for i, car in enumerate(self.__cars):
            if best_car_idx is None or best_car_idx == i:
                updated_rects.extend(
                    car.draw(surface))
            else:
                try:
                    updated_rects.append(
                        draw.circle(surface, (0, 0, 255), car.pos, 2))
                except:
                    pass
            if not no_scores:
                updated_rects.append(
                    draw_text(surface, car.color, car.name, (self.__track.size[0], i*32), 16, 'topleft'))
                if car.lap_time is not None:
                    updated_rects.append(
                        draw_text(surface, (255,)*3, f'{car.lap_time:8.2f}', (self.__track.size[0], i*32 + 16), 16, 'topleft'))
                if car.best_lap_time is not None:
                    updated_rects.append(
                        draw_text(surface, (255,)*3, f'{car.best_lap_time:8.2f}', (self.__track.size[0] + 64, i*32 + 16), 16, 'topleft'))
                
        if self.__time_to_go >= 0:
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                updated_rects.append(draw_text(surface, (0,)*3, f'{int(self.__time_to_go)}', (self.__track.size[0]/2 + dx*2, self.__track.size[1]/2 + dy*2), 256))
            updated_rects.append(draw_text(surface, (255,)*3, f'{int(self.__time_to_go)}', (self.__track.size[0]/2, self.__track.size[1]/2), 256))
        
        return updated_rects
