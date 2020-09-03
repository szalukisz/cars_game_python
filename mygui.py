import pygame, sys, os, time, string
import numpy as np
from pygame.locals import *


colors = {'white':          (255, 255, 255),
          'black':          (  0,   0,   0),
          'lightgray':      ( 63,  63,  63),
          'gray':           (127, 127, 127),
          'darkgray':       (191, 191, 191),
          'red':            (255, 127, 127),
          'green':          (127, 255, 127),
          'blue':           (127, 127, 255)}


def draw_text(text, size, color, surface, position, align=''):
    # function for drawing text on screen
    font = pygame.font.SysFont("consolasms", size)
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect()
    if align == 'bottomleft':
        textrect.bottomleft = position
    elif align == 'topleft':
        textrect.topleft = position
    elif align == 'bottomright':
        textrect.bottomright = position
    elif align == 'topright':
        textrect.topright = position
    else:
        textrect.center = position
    surface.blit(textobj, textrect)

class GUI:
    def __init__(self, window):
        self.__window = window
        self.__elements = dict([])

    def draw(self):
        for element in self.__elements.values():
            if not element.hide:
                element.draw()

    def handle_event(self, event):
        for element in self.__elements.values():
            if not element.hide:
                element.handle_event(event)

    def add(self, element_id, element):
        if isinstance(element, GUIElement):
            self.__elements[element_id] = element
        else:
            raise TypeError

    def id_exists(self, element_id):
        return element_id in self.__elements.keys()

    def get_element(self, element_id):
        return self.__elements[element_id]

    def clear(self):
        self.__elements = dict([])

class GUIElement:
    def __init__(self, window, pos, size):
        self.__window = window
        self.__pos = pos
        self.__size = size
        self.__border = 2
        self.__hide = False

    @property
    def window(self):
        return self.__window

    @window.setter
    def window(self, value):
        self.__window = value

    @property
    def pos(self):
        return self.__pos

    @pos.setter
    def pos(self, value):
        self.__pos = value

    @property
    def size(self):
        return self.__size

    @size.setter
    def size(self, value):
        self.__size = value

    @property
    def border(self):
        return self.__border
    
    @border.setter
    def border(self, value):
        self.__border = value

    @property
    def hide(self):
        return self.__hide
    
    @hide.setter
    def hide(self, value):
        self.__hide = value
        
    def draw(self):
        pass

    def handle_event(self, event):
        pass

class Text(GUIElement):
    def __init__(self, window, pos, size, text=''):
        GUIElement.__init__(self, window, pos, size)
        self.__text = text

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value):
        self.__text = value

    def draw(self):
        text_size = self.size[1]*4//5
        draw_text(self.__text, text_size, colors['white'], self.window,\
                  (self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1]/2))

class TextList(GUIElement):
    def __init__(self, window, pos, size, text_list=[]):
        GUIElement.__init__(self, window, pos, size)
        self.__text_list = text_list

    @property
    def text_list(self):
        return self.__text_list

    @text_list.setter
    def text_list(self, value):
        self.__text_list = value

    def draw(self):
        text_size = self.size[1]*4//5
        for i, text in enumerate(self.__text_list):
            draw_text(text, text_size, colors['black'], self.window,\
                      (self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1]/2 + self.size[1]*i))
class Button(GUIElement):
    def __init__(self, window, pos, size, text='', on_action=None, on_action_args=()):
        GUIElement.__init__(self, window, pos, size)
        self.__text = text
        self.__on_action = on_action
        self.__on_action_args = on_action_args

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value):
        self.__text = value

    def draw(self):
        pygame.draw.rect(self.window, colors['black'], pygame.Rect(self.pos, self.size))
        pygame.draw.rect(self.window, colors['white'],\
                         pygame.Rect((self.pos[0] + self.border, self.pos[1] + self.border),\
                                     (self.size[0] - 2*self.border, self.size[1] - 2*self.border)))
        text_size = self.size[1]*4//5
        draw_text(self.__text, text_size, colors['black'], self.window,\
                  (self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1]/2))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            borders = (self.pos[0], self.pos[1], self.pos[0] + self.size[0], self.pos[1] + self.size[1])
            if borders[0] <= event.pos[0] <= borders[2] and borders[1] <= event.pos[1] <= borders[3]:
                if self.__on_action is not None:
                    self.__on_action(*self.__on_action_args)
        if event.type == KEYDOWN:
            if event.key in (K_KP_ENTER, K_RETURN):
                if self.__on_action is not None:
                    self.__on_action(*self.__on_action_args)


class CheckBox(GUIElement):
    def __init__(self, window, pos, size, text = '', checked = True):
        GUIElement.__init__(self, window, pos, size)
        self.__text = text
        self.__checked = checked

    @property
    def checked(self):
        return self.__checked

    @checked.setter
    def checked(self, value):
        self.__checked = value

    def draw(self):
        pygame.draw.rect(self.window, colors['black'], pygame.Rect(self.pos, self.size))
        pygame.draw.rect(self.window, colors['white'],\
                         pygame.Rect((self.pos[0] + self.border, self.pos[1] + self.border),\
                                     (self.size[0] - 2*self.border, self.size[1] - 2*self.border)))
        text_size = self.size[1]*4//5
        draw_text(self.__text, text_size, colors['black'], self.window,\
                  (self.pos[0] + self.size[0], self.pos[1] + self.size[1]), 'lb')
        if self.value:
            pygame.draw.line(self.window, colors['black'], (self.pos[0] + 5, self.pos[1] + 5),
                             (self.pos[0] + self.size[0] - 5, self.pos[1] + self.size[1] - 5), 5)
            pygame.draw.line(self.window, colors['black'], (self.pos[0] + self.size[0] - 5, self.pos[1] + 5),
                             (self.pos[0] + 5, self.pos[1] + self.size[1] - 5), 5)

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            borders = (self.pos[0], self.pos[1], self.pos[0] + self.size[0], self.pos[1] + self.size[1])
            if borders[0] <= event.pos[0] <= borders[2] and borders[1] <= event.pos[1] <= borders[3]:
                self.__checked = not self.__checked


class TextBox(GUIElement):
    def __init__(self, window, pos, size, prompt_text=''):
        GUIElement.__init__(self, window, pos, size)
        self.__prompt_text = prompt_text
        self.__text = ''
        self.__is_active = False
        self.__max_text_len = 8

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value):
        self.__text = value

    @property
    def is_active(self):
        return self.__is_active

    @is_active.setter
    def is_active(self, value):
        self.__is_active = value

    @property
    def max_text_len(self):
        return self.__max_text_len

    @max_text_len.setter
    def max_text_lnen(self, value):
        self.__max_text_len = value

    def draw(self):
        if self.__is_active:
            pygame.draw.rect(self.window, colors['blue'], pygame.Rect(self.pos, self.size))
        else:
            pygame.draw.rect(self.window, colors['black'], pygame.Rect(self.pos, self.size))
        pygame.draw.rect(self.window, colors['white'],\
                         pygame.Rect((self.pos[0] + self.border, self.pos[1] + self.border),\
                                     (self.size[0] - 2*self.border, self.size[1] - 2*self.border)))
        text_size = self.size[1]*4//5
        if len(self.__text) != 0:
            draw_text(self.__text, text_size, colors['black'], self.window,\
                      (self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1]/2))
        else:
            draw_text(self.__prompt_text, text_size, colors['gray'], self.window,\
                      (self.pos[0] + self.size[0]/2, self.pos[1] + self.size[1]/2))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN:
            borders = (self.pos[0], self.pos[1], self.pos[0] + self.size[0], self.pos[1] + self.size[1])
            if borders[0] <= event.pos[0] <= borders[2] and borders[1] <= event.pos[1] <= borders[3]:
                self.__is_active = True
            else:
                self.__is_active = False
        if self.__is_active and event.type == KEYDOWN:
            if event.unicode in string.ascii_letters + string.digits and len(self.__text) < self.__max_text_len:
                self.__text += event.unicode
            if event.key == K_BACKSPACE and len(self.__text) > 0:
                self.__text = self.__text[:-1]

















