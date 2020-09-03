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


class RaceServer(object):
    def __init__(self, track):
        self.__track = track
        self.__finish_line = self.__track.finish_line
        self.__cars = []
        self.__time_to_go = 5
        self.__active_bonuses = []
        self.winner = None

    def add_car(self, car):
        r = .2 + .6 * random()
        car.pos[:] = self.__finish_line[0] * r + self.__finish_line[1] * (1 - r)
        car.pos[0] -= 16
        car.start_pos = np.copy(car.pos)
        car.on_finish = -1
        car.lap_start_time = None
        car.lap_time = None
        car.add_time = perf_counter()
        car.best_lap_time = None
        car.laps = -1
        car.laps_to_go = 5
        car.collision = 0.
        car.prev_lap_collision = 0.
        car.bonuses = []
        self.__cars.append(car)

    def get_times_of_cars(self):
        times = np.zeros((len(self.__cars), 5))
        for i in range(len(self.__cars)):
            times[i][0] = self.__cars[i].lap_start_time
            times[i][1] = self.__cars[i].lap_time
            times[i][2] = self.__cars[i].laps
            times[i][3] = self.__cars[i].best_lap_time
            times[i][4] = self.__cars[i].laps_to_go

        return times

    def add_bonus(self):
        bonuses = [
            {"type": "SpeedUP", "color": (0, 200, 0), "time_active": 10.0, "time_show": 6.0},
            {"type": "SlowDOWN", "color": (200, 0, 0), "time_active": 10.0, "time_show": 8.0},
            {"type": "SwapyyyKeys", "color": (255, 51, 255), "time_active": 12.0, "time_show": 7.0},
            {"type": "Freeze", "color": (50, 50, 200), "time_active": 2.0, "time_show": 8.0}
        ]

        bonus = int(random() * len(bonuses))
        tmp = bonuses[bonus]
        position = 0
        while position == 0:
            position = int(random() * len(self.__track.inner_points))
            if position in [x["pos_n"] for x in self.__active_bonuses]:
                position = 0

        tmp["pos"] = (self.__track.inner_points[position] + self.__track.outer_points[position]) / 2
        tmp["pos_n"] = position
        self.__active_bonuses.append(tmp)

    def get_map_bonuses(self):
        return self.__active_bonuses

    def get_car_bonuses(self):
        tmp = []
        for car in self.__cars:
            tmp.append(car.bonuses)
        return tmp

    def hasWinner(self):
        return self.winner is not None

    def remove_car(self, car):
        if car in self.__cars:
            self.__cars.remove(car)
            return True
        return False

    def remove_all_cars(self):
        self.__cars.clear()

    def contain_car(self, car):
        return car in self.__cars

    def handle_event(self, event, my_car):
        for car in self.__cars:
            if car is my_car:
                car.handle_event(event)

    def check_bonuses_intersect(self):
        for bns in self.__active_bonuses:
            for car in self.__cars:
                if math.sqrt(math.pow(float(car.pos[1]) - float(bns["pos"][1]), 2) +
                             math.pow(float(car.pos[0]) - float(bns["pos"][0]), 2)) < 15:

                    print(f'{car.__getattr__("name")} used up bonus {bns["type"]}')
                    if bns["type"] == "SwapyyyKeys":
                        for car_o in self.__cars:
                            if car_o != car:
                                if bns["type"] in [x["type"] for x in car_o.bonuses]:
                                    for car_o_bns in car_o.bonuses:
                                        if car_o_bns["type"] == bns["type"]:
                                            car_o_bns["time_active"] = bns["time_active"]
                                else:
                                    car_o.bonuses.append(
                                        {"type": bns["type"], "time_active": bns["time_active"], "color": bns["color"]})
                    elif bns["type"] in [x["type"] for x in car.bonuses]:
                        for car_bns in car.bonuses:
                            if car_bns["type"] == bns["type"]:
                                car_bns["time_active"] = bns["time_active"]
                    elif (bns["type"] == "SlowDOWN" and "SpeedUP" in [x["type"] for x in car.bonuses]) or\
                            (bns["type"] == "SpeedUP" and "SlowDOWN" in [x["type"] for x in car.bonuses]):
                        for car_bns in car.bonuses:
                            if car_bns["type"] in ("SlowDOWN", "SpeedUP"):
                                bns["time_active"] -= car_bns["time_active"]
                                car.bonuses.append({"type": bns["type"], "time_active": bns["time_active"], "color": bns["color"]})
                                car.bonuses.remove(car_bns)
                                break
                    else:
                        car.bonuses.append({"type": bns["type"], "time_active": bns["time_active"], "color": bns["color"]})
                    self.__active_bonuses.remove(bns)

    def run(self, delta_time):
        delta_time = min(delta_time, .05)

        if self.__time_to_go < 0:
            collisions = self.__track.collision_with_cars(self.__cars)
            for i, car in enumerate(self.__cars):
                if car.lap_start_time is not None:
                    car.lap_time = perf_counter() - car.lap_start_time
                swap = -1 if "SwapyyyKeys" in [x["type"] for x in car.bonuses] else 1
                if "Freeze" in [x["type"] for x in car.bonuses]:
                    car.run(0, collisions[i], self.__track)
                elif "SlowDOWN" in [x["type"] for x in car.bonuses]:
                    car.run(0.3 * delta_time, collisions[i], self.__track, swap)
                elif "SpeedUP" in [x["type"] for x in car.bonuses]:
                    car.run(1.5 * delta_time, collisions[i], self.__track, swap)
                else:
                    car.run(delta_time, collisions[i], self.__track, swap)

                if np.linalg.norm(collisions[i]) > 0:
                    car.collision += delta_time

                finish_unit_vector = self.__finish_line[1] - self.__finish_line[0]
                finish_unit_vector /= np.linalg.norm(finish_unit_vector)
                if 0 < np.dot((car.pos - self.__finish_line[0]) / np.linalg.norm(car.pos - self.__finish_line[0]),
                              finish_unit_vector) < 1:
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
                            if car.lap_time is not None and \
                                    (car.best_lap_time is None or car.best_lap_time > car.lap_time):
                                car.best_lap_time = car.lap_time
                            if car.lap_time is not None:
                                car.laps_to_go -= 1
                                if car.laps_to_go == 0:
                                    # print(i)
                                    self.winner = i
                            car.lap_start_time = perf_counter()

                        car.on_finish = 1
                else:
                    car.on_finish = 0

                for bns in car.bonuses:
                    bns["time_active"] -= delta_time
                    if bns["time_active"] <= 0:
                        car.bonuses.remove(bns)

            self.check_bonuses_intersect()

            # _ decreasing time of the bonuses
            for bonus in self.__active_bonuses:
                bonus["time_show"] -= delta_time
                if bonus["time_show"] < 0:
                    self.__active_bonuses.remove(bonus)

            if random() < 0.00035:
                if len(self.__active_bonuses) < 5:
                    self.add_bonus()
        else:
            self.__time_to_go -= delta_time
