import getpass
from pygame import surfarray, transform, draw, image
from pygame.locals import *
import cv2
import numpy as np
from math import cos, sin, pi, ceil

from util import *

class Car_m(object):
    def __init__(self, pos=(100., 100.), name=getpass.getuser()):
        self.__pos = np.array(pos, dtype=np.float32)
        self.__name = name
        self.__start_pos = np.zeros(2)
        self.__angle = 0.0
        self.__velocity = np.zeros(2, dtype=np.float32)
        self.__acceleration = np.zeros(2, dtype=np.float32)
        self._move = 0
        self._turn = 0
        self.__color = np.random.randint(0, 255, size=3)
        texture_cv2 = cv2.imread('textures/car1_a.png', cv2.IMREAD_UNCHANGED)
        texture_cv2 = cv2.cvtColor(texture_cv2, cv2.COLOR_BGR2RGB)
        texture_cv2[(texture_cv2[:, :, 0] == 0) &\
                (texture_cv2[:, :, 1] == 255) &\
                (texture_cv2[:, :, 2] == 0)] = self.__color
        self.__texture = surfarray.make_surface(texture_cv2)
        self.__texture.set_colorkey((255,)*3)
        self.__turn_keys = []
        self.__move_keys = []

    def change_color(self):
        texture_cv2 = cv2.imread('textures/car1_a.png', cv2.IMREAD_UNCHANGED)
        texture_cv2 = cv2.cvtColor(texture_cv2, cv2.COLOR_BGR2RGB)
        texture_cv2[(texture_cv2[:, :, 0] == 0) & \
                    (texture_cv2[:, :, 1] == 255) & \
                    (texture_cv2[:, :, 2] == 0)] = self.__color
        self.__texture = surfarray.make_surface(texture_cv2)
        self.__texture.set_colorkey((255,) * 3)

    def __setattr__(self, name, value):
        if name == 'pos':
            self.__pos = np.array(value, dtype=np.float32)
        elif name == 'start_pos':
            self.__start_pos = np.array(value, dtype=np.float32)
        elif name == 'name':
            self.__name = value
        super(Car_m, self).__setattr__(name, value)

    def __getattr__(self, name):
        if name == 'pos':
            return self.__pos
        elif name == 'angle':
            return self.__angle
        elif name == 'name':
            return self.__name
        elif name == 'color':
            return self.__color
        elif name == 'rect':
            width, height = self.__texture.get_size()
            front_dir = np.array([np.cos(self.__angle), np.sin(self.__angle)])
            left_dir = np.array([-front_dir[1], front_dir[0]])
            return np.array([self.__pos + front_dir*width/2 + left_dir*height/2,
                             self.__pos - front_dir*width/2 + left_dir*height/2,
                             self.__pos - front_dir*width/2 - left_dir*height/2,
                             self.__pos + front_dir*width/2 - left_dir*height/2])


    def handle_event(self, event):
        if event.type == JOYAXISMOTION:
            if event.axis == 0:
                self._turn = event.value
            if event.axis == 2:
                self._move = - event.value
        else:
            if event.type == KEYDOWN:
                if event.key in (K_UP, K_w):
                    self.__move_keys.insert(0, 1)
                elif event.key in (K_DOWN, K_s):
                    self.__move_keys.insert(0, -1)
                elif event.key in (K_LEFT, K_a):
                    self.__turn_keys.insert(0, -1)
                elif event.key in (K_RIGHT, K_d):
                    self.__turn_keys.insert(0, 1)
            elif event.type == KEYUP:
                if event.key in (K_UP, K_w):
                    while 1 in self.__move_keys:
                        self.__move_keys.remove(1)
                elif event.key in (K_DOWN, K_s):
                    while -1 in self.__move_keys:
                        self.__move_keys.remove(-1)
                elif event.key in (K_LEFT, K_a):
                    while -1 in self.__turn_keys:
                        self.__turn_keys.remove(-1)
                elif event.key in (K_RIGHT, K_d):
                    while 1 in self.__turn_keys:
                        self.__turn_keys.remove(1)
            if len(self.__move_keys) > 0:
                self._move = self.__move_keys[0]
            else:
                self._move = 0
            if len(self.__turn_keys) > 0:
                self._turn = self.__turn_keys[0]
            else:
                self._turn = 0

    def run(self, delta_time, collision_force_dir, track, swap=1):
        self.__acceleration = 512 * np.array([cos(self.__angle), sin(self.__angle)], dtype=np.float32) * self._move
        if self._turn != 0:
            if np.dot(np.array([np.cos(self.angle), np.sin(self.angle)]), self.__velocity) > 0:
                self.__angle += (5 * swap * self._turn * delta_time)*np.linalg.norm(self.__velocity)/256
            else:
                self.__angle -= (5 * swap * self._turn * delta_time)*np.linalg.norm(self.__velocity)/256

        self.__pos += self.__velocity * delta_time
        self.__velocity += (self.__acceleration - 0.02 * np.sign(self.__velocity) * np.power(self.__velocity, 2)) * delta_time

        if collision_force_dir.dot(self.__velocity) > 0:
            self.__velocity -= 1.5*collision_force_dir*collision_force_dir.dot(self.__velocity)
            self.__velocity /= 2
        else:
            self.__velocity += 0.3*collision_force_dir*collision_force_dir.dot(self.__velocity)
        self.__velocity[0] = clamp(self.__velocity[0], -500, 500)
        self.__velocity[1] = clamp(self.__velocity[1], -500, 500)

    def draw(self, surface, bonuses=None):
        if bonuses is None:
            bonuses = []
        updated_rects = []
        texture = transform.rotate(self.__texture, -self.__angle*180/pi - 180)
        width, height = texture.get_size()
        pos = (self.__pos[0] - width/2, self.__pos[1] - height/2)
        try:
            updated_rects.append(
                surface.blit(texture, pos))
            updated_rects.append(
                draw_text(surface, self.__color, self.__name, (pos[0], pos[1] - 32), 16))
            for j, bns in enumerate(bonuses):  # _ bonuses
                updated_rects.append(
                    draw_text(surface, bns["color"], f"{ceil(bns['time_active'])}",
                              (pos[0] + 16 * j, pos[1] - 20), 16, 'topleft'))
        except:
            self.go_to_start()

        return updated_rects

    def go_to_start(self):
        self.__pos = np.copy(self.__start_pos)
        self.__angle = .0
        self.__velocity = np.zeros(2, dtype=np.float32)
        self.__acceleration = np.zeros(2, dtype=np.float32)

    def get_param(self):
        return [self.__pos,
                self.__name,
                self.__angle,
                self.__color]

    def set_param(self, params):
        self.__pos = params[0]
        self.__name = params[1]
        self.__angle = params[2]
        self.__color = params[3]



class CarAI(Car_m):
    def __init__(self, ray_count=7, additional_front_ray_count=0, rays_params=None, *args, **kwargs):
        # define ai params
        if rays_params is None:
            rays_params = CarAI.create_rays_params(self, ray_count, additional_front_ray_count)

        self._ray_count = ray_count
        self._additional_front_ray_count = additional_front_ray_count
        self._dists = np.zeros(rays_params['origin'].shape[0])
        self._ray_origin = np.copy(rays_params['origin'])
        self._ray_angle = np.copy(rays_params['angle'])
        self._ray_length= np.copy(rays_params['length'])
        self._points = np.zeros((self._ray_origin.shape[0], 2))

        if self.__class__ == CarAI:
            super(CarAI, self).__init__(*args, **kwargs)

    def __getattr__(self, name):
        if name == 'dists':
            return self._dists
        if name == 'move':
            return self._move
        if name == 'turn':
            return self._turn
        if name == 'turn':
            return {'origin': self._ray_origin, 'angle': self._ray_angle, 'length': self._ray_max_dist}
        return super(CarAI, self).__getattr__(name)

    def create_rays_params(self, ray_count=7, additional_front_ray_count=0):
        origin = np.zeros((ray_count + additional_front_ray_count, 2))
        for i in range(additional_front_ray_count):
            origin[ray_count + i, 1] = (self.rect[0,1] - self.pos[1])*(i*2/(additional_front_ray_count - 1) - 1)
        angle = np.zeros(ray_count + additional_front_ray_count)
        angle[:ray_count] = np.array([(i - ray_count//2)/(ray_count - 2)*np.pi for i in range(ray_count)])
        length = np.ones(ray_count + additional_front_ray_count)*255

        return {'origin': origin, 'angle': angle, 'length': length}

    def draw(self, surface, draw_rays=False):
        updated_rects = []
        updated_rects.extend(
            super(CarAI, self).draw(surface))
        for i in range(self._dists.shape[0]):
            angle = self._ray_angle[i]
            start_pos = np.copy(self.pos)
            start_pos[0] += np.cos(self.angle)*self._ray_origin[i,0] - np.sin(self.angle)*self._ray_origin[i,1]
            start_pos[1] += np.sin(self.angle)*self._ray_origin[i,0] + np.cos(self.angle)*self._ray_origin[i,1]
            direction = np.array([np.cos(self.angle + angle),
                                  np.sin(self.angle + angle)])
            if draw_rays:
                updated_rects.append(
                    draw.aaline(surface, (0, 127, 0), start_pos.astype(np.int32), (start_pos + self._ray_length[i]*direction).astype(np.int32)))
            updated_rects.append(
                draw.circle(surface, (0, 255, 0), self._points[i].astype(np.int32), 2))
        return updated_rects

    def run(self, delta_time, collision_force_dir, track, swap=1):
        self._points = []
        for i in range(self._dists.shape[0]):
            max_dist = self._ray_length[i]
            angle = self._ray_angle[i]
            start_pos = np.copy(self.pos)
            start_pos[0] += np.cos(self.angle)*self._ray_origin[i,0] - np.sin(self.angle)*self._ray_origin[i,1]
            start_pos[1] += np.sin(self.angle)*self._ray_origin[i,0] + np.cos(self.angle)*self._ray_origin[i,1]
            direction = np.array([np.cos(self.angle + angle),
                                  np.sin(self.angle + angle)])
            intersections = track.collision_with_segment(np.array([start_pos - 4*direction, start_pos + max_dist*direction]))
            if intersections.shape[0] > 0:
                min_d = max_dist
                for j in range(intersections.shape[0]):
                    d = np.linalg.norm(start_pos - intersections[j])
                    min_d = min(d, min_d)
                dist = min_d
            else:
                dist = max_dist
            self._dists[i] = dist/max_dist
            self._points.append(start_pos + direction*dist)

        if self.__class__ == CarAI:
            super(CarAI, self).run(delta_time, collision_force_dir, track)

class Event:
    def __init__(self, _key, _type):
        self.key = _key
        self.type = _type
