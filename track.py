# -*- coding: utf-8 -*-
from pygame import draw
import numpy as np
import numba as nb
from time import perf_counter

from car import Car

class Track(object):
    def __init__(self, filename):
        self.__filename = filename
        self.__size = np.zeros(2, dtype=np.int32)
        center_points = []
        outer_points = []
        inner_points = []
        self.__collision_points = np.array([], dtype=np.float64)
        read_points = 0
        with open(filename, 'r') as file:
            for line in file:
                if line == '[size]\n':
                    read_points = 's'
                if line == '[center points]\n':
                    read_points = 'c'
                elif line == '[outer points]\n':
                    read_points = 'o'
                elif line == '[inner points]\n':
                    read_points = 'i'
                elif read_points == 's' and len(line.split()) == 2:
                    self.__size[0], self.__size[1] = map(int, line.split())
                elif read_points == 'c' and len(line.split()) == 3:
                    x, y, r = map(float, line.split())
                    center_points.append((x, y, r))
                elif read_points == 'o' and len(line.split()) == 2:
                    x, y = map(float, line.split())
                    outer_points.append((x, y))
                elif read_points == 'i' and len(line.split()) == 2:
                    x, y = map(float, line.split())
                    inner_points.append((x, y))
        self.__center_points = np.array(center_points, dtype=np.float64)
        self.__outer_points = np.array(outer_points, dtype=np.float64)
        self.__inner_points = np.array(inner_points, dtype=np.float64)
    
    def __getattr__(self, name):
        if name == 'size':
            return self.__size
        if name == 'center_points':
            return self.__center_points
        elif name == 'outer_points':
            return self.__outer_points
        elif name == 'inner_points':
            return self.__inner_points
        elif name == 'finish_line':
            return np.array([self.__inner_points[0], self.__outer_points[0]])
    
    def forward_direction(self, point):
        closest_dist = 0
        closest_idx = None
        for i, p in enumerate(self.__center_points):
            dist = np.linalg.norm(point - p[:2])
            if dist < closest_dist or closest_idx is None:
                closest_dist = dist
                closest_idx = i

        forward = self.__center_points[(closest_idx+1)%self.__center_points.shape[0],:2] - self.__center_points[closest_idx,:2]
        forward /= np.linalg.norm(forward)
        return forward

    @staticmethod
    @nb.guvectorize(['float64[:,:], float64[:,:], float64[:], float64, boolean[:]'],
                    '(n,k),(n,k),(k),()->(n)', nopython=True)
    def __collision_1(chain_prev, chain_next, car_pos, car_radius, can_intersect):
        for i in nb.prange(chain_prev.shape[0]):
            if np.linalg.norm(car_pos - (chain_prev[i,] + chain_next[i,])/2) >\
               car_radius + np.linalg.norm(chain_prev[i,] - chain_next[i,])/2:
                can_intersect[i,] = False
            else:
                can_intersect[i,] = True
                
    @staticmethod
    @nb.guvectorize(['float64[:,:], float64[:,:], float64[:,:], float64[:], boolean[:,:]'],
                    '(n,l),(n,l),(k,l),(k)->(k,n)', nopython=True)
    def __collision_1_2(chain_prev, chain_next, car_pos, car_radius, can_intersect):
        for i in nb.prange(car_pos.shape[0]):
            for j in nb.prange(chain_prev.shape[0]):
                if np.linalg.norm(car_pos[i,] - (chain_prev[j,] + chain_next[j,])/2) >\
                   car_radius[i] + np.linalg.norm(chain_prev[j,] - chain_next[j,])/2:
                    can_intersect[i,j] = False
                else:
                    can_intersect[i,j] = True
    
    @staticmethod
    @nb.guvectorize(['float64[:,:], float64[:,:], float64[:], float64[:], boolean[:]'],
                    '(n,k),(n,k),(k),(k)->(n)', nopython=True)
    def __collision_2(chain_prev, chain_next, car_a, car_b, intersects):
        for i in nb.prange(chain_prev.shape[0]):
            if ((chain_prev[i,0] - chain_next[i,0])*(car_b[1] - chain_next[i,1])-\
                (chain_prev[i,1] - chain_next[i,1])*(car_b[0] - chain_next[i,0]))*\
               ((chain_prev[i,0] - chain_next[i,0])*(car_a[1] - chain_next[i,1])-\
                (chain_prev[i,1] - chain_next[i,1])*(car_a[0] - chain_next[i,0])) < 0 and\
               ((car_a[0] - car_b[0])*(chain_next[i,1] - car_b[1])-\
                (car_a[1] - car_b[1])*(chain_next[i,0] - car_b[0]))*\
               ((car_a[0] - car_b[0])*(chain_prev[i,1] - car_b[1])-\
                (car_a[1] - car_b[1])*(chain_prev[i,0] - car_b[0])) < 0:
                intersects[i,] = True
            else:
                intersects[i,] = False

    @staticmethod
    @nb.guvectorize(['float64[:,:], float64[:,:], float64[:], float64[:], float64[:,:]'],
                    '(n,k),(n,k),(k),(k)->(n,k)', nopython=True)
    def __collision_3(chain_prev, chain_next, car_a, car_b, intersections):
        for i in nb.prange(chain_prev.shape[0]):
            xdiff_1 = chain_prev[i,0] - chain_next[i,0]
            ydiff_1 = chain_prev[i,1] - chain_next[i,1]
            xdiff_2 = car_a[0] - car_b[0]
            ydiff_2 = car_a[1] - car_b[1]
            
            div = xdiff_1*ydiff_2 - xdiff_2*ydiff_1
            
            d_1 = chain_prev[i,0]*chain_next[i,1] - chain_prev[i,1]*chain_next[i,0]
            d_2 = car_a[0]*car_b[1] - car_a[1]*car_b[0]
            
            intersections[i,0] = (d_1*xdiff_2 - d_2*xdiff_1)/div
            intersections[i,1] = (d_1*ydiff_2 - d_2*ydiff_1)/div
            
    def collision_with_cars(self, cars):
        result = []
        all_intersections = np.empty((0, 2), dtype=np.float64)
        
        inner_points_shifted = np.roll(self.__inner_points, -1, axis=0)
        outer_points_shifted = np.roll(self.__outer_points, -1, axis=0)        
        
        car_rect = np.zeros((len(cars), 4, 2), dtype=np.float64)
        car_pos = np.zeros((len(cars), 2), dtype=np.float64)
        car_radius = np.zeros((len(cars)), dtype=np.float64)
        
        for i, car in enumerate(cars):
            car_rect[i,] = car.rect
            car_pos[i,] = car.pos
            car_radius[i,] = np.linalg.norm(car.rect[0] - car.pos)
        
        inner_can_intersect = Track.__collision_1_2(self.__inner_points, inner_points_shifted, car_pos, car_radius)
        outer_can_intersect = Track.__collision_1_2(self.__outer_points, outer_points_shifted, car_pos, car_radius)
        
        for i in range(car_rect.shape[0]):
            collision_force_dir = np.empty((0, 2), dtype=np.float64)
            
            inner_points_can_intersect = self.__inner_points[inner_can_intersect[i,],]
            inner_points_shifted_can_intersect = inner_points_shifted[inner_can_intersect[i,],]
            
            outer_points_can_intersect = self.__outer_points[outer_can_intersect[i,],]
            outer_points_shifted_can_intersect = outer_points_shifted[outer_can_intersect[i,],]
            
            for j in range(car_rect.shape[1]):
                intersects = Track.__collision_2(inner_points_can_intersect, inner_points_shifted_can_intersect, car_rect[i,j-1], car_rect[i,j])
                
                inner_points_intersects = inner_points_can_intersect[intersects,]
                inner_points_shifted_intersects = inner_points_shifted_can_intersect[intersects,]
                intersections = Track.__collision_3(inner_points_intersects, inner_points_shifted_intersects, car_rect[i,j-1], car_rect[i,j])
                
                all_intersections = np.concatenate([all_intersections, intersections], axis=0)
                collision_force_dir = np.concatenate([collision_force_dir, np.column_stack((inner_points_intersects[:,1] - inner_points_shifted_intersects[:,1],
                                                                                            inner_points_shifted_intersects[:,0] - inner_points_intersects[:,0]))], axis=0)

                intersects = Track.__collision_2(outer_points_can_intersect, outer_points_shifted_can_intersect, car_rect[i,j-1], car_rect[i,j])
                
                outer_points_intersects = outer_points_can_intersect[intersects,]
                outer_points_shifted_intersects = outer_points_shifted_can_intersect[intersects,]
                intersections = Track.__collision_3(outer_points_intersects, outer_points_shifted_intersects, car_rect[i,j-1], car_rect[i,j])
                
                all_intersections = np.concatenate([all_intersections, intersections], axis=0)
                collision_force_dir = np.concatenate([collision_force_dir, np.column_stack((outer_points_shifted_intersects[:,1] - outer_points_intersects[:,1],
                                                                                            outer_points_intersects[:,0] - outer_points_shifted_intersects[:,0]))], axis=0)                
                
            
            if collision_force_dir.shape[0] > 0:
                collision_force_dir = collision_force_dir.sum(axis=0)
                collision_force_dir /= np.linalg.norm(collision_force_dir)
            else:
                collision_force_dir = np.zeros(2)
            result.append(collision_force_dir)
        self.__collision_points = np.copy(all_intersections)
            
        return result
    
    def collision_with_segment(self, segment):
        inner_points_shifted = np.roll(self.__inner_points, -1, axis=0)
        outer_points_shifted = np.roll(self.__outer_points, -1, axis=0)
        
        all_points = np.concatenate([self.__inner_points, self.__outer_points], axis=0)
        all_points_shifted = np.concatenate([inner_points_shifted, outer_points_shifted], axis=0)

        can_intersect = Track.__collision_1(all_points, all_points_shifted, (segment[0] + segment[1])/2, np.linalg.norm(segment[0] - segment[1])/2)
        
        all_points_can_intersect = all_points[can_intersect,]
        all_points_shifted_can_intersect = all_points_shifted[can_intersect,]
        
        intersects = Track.__collision_2(all_points_can_intersect, all_points_shifted_can_intersect, segment[0], segment[1])
        
        all_points_intersects = all_points_can_intersect[intersects,]
        all_points_shifted_intersects = all_points_shifted_can_intersect[intersects,]
        
        intersections = Track.__collision_3(all_points_intersects, all_points_shifted_intersects, segment[0], segment[1])
        
        return intersections
    
    def draw(self, surface, pos=(0, 0)):
        updated_rects = []
        pos = np.array(pos)
        # outer black
        updated_rects.append(
            draw.polygon(surface, (127,)*3, (self.__outer_points + pos).astype(np.int32)))
        # inner black
        updated_rects.append(
            draw.polygon(surface, (0,)*3, (self.__inner_points + pos).astype(np.int32)))
        # start line
        updated_rects.append(
            draw.line(surface, (255, 0, 0), (self.__inner_points[0] + pos).astype(np.int32), (self.__outer_points[0] + pos).astype(np.int32)))
        for i in range(self.__collision_points.shape[0]):
            updated_rects.append(
                draw.circle(surface, (255, 0, 0), self.__collision_points[i,].astype(np.int32), 3))
        return updated_rects
    
    def __repr__(self):
        return f'Track(filename={self.__filename})'

