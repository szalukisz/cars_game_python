import os


os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pickle
import re
import socket
import sys
import threading
import time
import pygame
import mygui
from race_client import *
from track import *

import socket
from multiprocessing.connection import Client

to_send = []
client = None
menu = ''
player_name = ''
connection_lost = False
winner = None


def terminate():
    pygame.quit()
    if client is not None:
        client.close()
    sys.exit()


def set_menu(value):
    global menu
    global player_name
    if value == 'play':
        if gui.get_element('name_textbox').text != '':
            player_name = gui.get_element('name_textbox').text
            menu = value
        else:
            gui.get_element('name_warn').text = 'You have to choose name'
    elif value == 'replay':
        menu = value


def connection_handler():
    flag = False  # for a change send and receive
    global connection_lost
    global winner
    t = time.time()
    f = 0  # _ f - counter to avg ping
    while True:
        if flag:
            # receiving
            try:
                buff = client.recv()
                if buff is not None:
                    winner = buff
                    race.set_winner(winner)
                    client.close()
                    break

                buff = client.recv()  # _ car stats
                for g in range(players_number):
                    cars[g].set_param(buff[g])

                buff = client.recv()  # _ car times
                race.update_times_of_cars(buff)

                buff = client.recv()
                race.update_map_bonuses(buff)

                buff = client.recv()
                race.update_car_bonuses(buff)

                elapsed = time.time() - t
                f += 1
                race.set_ping(elapsed, f % 50)
                t = time.time()

                flag = False
            except (EOFError, ConnectionAbortedError, ConnectionResetError) as e:
                print("Err: An error occurred while receiving information from server")
                connection_lost = True
                break
            except:
                break

        else:
            # sending
            try:
                global to_send

                if len(to_send) != 0:
                    tmp = to_send.pop()
                    package = [tmp.key, tmp.type]
                    client.send(package)
                else:
                    client.send(0)
                flag = True
            except (EOFError, ConnectionAbortedError, ConnectionResetError) as e:
                print("Err: An error occurred while sending information to server")
                connection_lost = True
                break
            except:
                break

        time.sleep(0.005)
    print("Connection with server closed")


host = ''
port = 0

try:
    with open("client.cfg", encoding='utf-8') as f:
        try:
            line = f.readline()
            ip_address = r'(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})'
            host = re.findall(ip_address, line)[0]
            line = f.readline()
            port = r'([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])'
            port = int(re.findall(port, line)[0])
        except:
            print("Bad configured client.cfg file.")
            sys.exit(-1)
except:
    print("Can't open file server.cfg")
    sys.exit(-1)

pygame.init()
welcome_window_size = [485, 725]
window = pygame.display.set_mode((welcome_window_size[0], welcome_window_size[1]), 0, 32)
pygame.display.set_caption('Client Welcome')
bg = pygame.image.load("bg.png")
gui = mygui.GUI(window)

# welcome GUI
gui.clear()
gui.add('button_play', mygui.Button(window, (welcome_window_size[0] / 2 - 120, 300), (240, 40), 'Click to play',
                                    on_action=set_menu, on_action_args=('play',)))
gui.add('name_textbox', mygui.TextBox(window, (welcome_window_size[0] / 2 - 120, 200), (240, 30), 'Name'))
gui.add('name_warn', mygui.Text(window, (welcome_window_size[0] / 2 - 90, 100), (180, 30),
                                'Please choose your name'))

while menu != 'play':
    for event in pygame.event.get():
        if event.type == QUIT:
            terminate()
        gui.handle_event(event)
    window.blit(bg, (0, 0))
    gui.draw()
    pygame.display.update()

while True:
    print('Waiting for connection')
    try:
        client = Client((host, port))
    except (ConnectionRefusedError, TimeoutError) as e:
        connection_lost = True
        print("Err: Server is not online or something is blocking connection!")

    if not connection_lost:
        print("Connected")

        # _ waiting GUI
        gui.clear()
        gui.add('text_wait', mygui.Text(window, (150, 320), (180, 35), 'Please wait for other players to connect...'))

        print("Waiting for other players")
        window.blit(bg, (0, 0))
        gui.draw()
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    terminate()
            pygame.display.update()
            try:
                player_number = client.recv()
            except (EOFError, ConnectionAbortedError, ConnectionResetError) as e:
                print("Err: Probably other player or server disconnect")
                connection_lost = True
                break

            if player_number > -1:
                break

        try:
            # _ map_name that will be used
            track_name = client.recv()
            track = Track(track_name)
            # _ number of players
            players_number = client.recv()
        except (EOFError, ConnectionAbortedError, ConnectionResetError) as e:
            print("Err: Connection lost")
            connection_lost = True

        if not connection_lost:
            window_width = track.size[0] + 256
            window_height = track.size[1]

            pygame.display.set_mode((window_width, window_height), 0, 32)
            pygame.display.set_caption('Client')
            race = Race_Client(track)

            cars = []
            try:
                # sending car name
                client.send(player_name)

                # setting cars
                players = client.recv()
            except (ConnectionResetError, ConnectionAbortedError, EOFError) as e:
                print("Err: Connection lost")
                connection_lost = True
                break
            if not connection_lost:
                for k in range(players_number):
                    cars.append(Car_m())
                    race.add_car(cars[k])
                    cars[k].set_param(players[k])
                    cars[k].change_color()

                # new thread for handling connection with server
                thread = threading.Thread(target=connection_handler)
                thread.start()

                # starting race
                time_0 = perf_counter()
                clock = pygame.time.Clock()

                time.sleep(0.3)
                print("Game started!")
                race.start_count()  # starting counting timer
                winning_freeze = 4
                while True:
                    if connection_lost:
                        break
                    for event in pygame.event.get():
                        if event.type == QUIT:
                            terminate()
                        if event.type in (KEYUP, KEYDOWN) and race.started():
                            to_send.append(event)

                    delta_time, time_0 = perf_counter() - time_0, perf_counter()
                    race.draw(window, delta_time)
                    pygame.display.update()

                    if winner is not None:
                        winning_freeze -= delta_time
                        if winning_freeze < 0:
                            break

    to_send = []
    client = None
    connection_lost = False

    # _ game finished
    # _ replay window
    pygame.display.set_mode((welcome_window_size[0], welcome_window_size[1]), 0, 32)
    pygame.display.set_caption('Replay')
    gui.clear()
    gui.add('button_replay', mygui.Button(window, (welcome_window_size[0] / 2 - 120, 300), (240, 40),
                                          'Click to play again', on_action=set_menu, on_action_args=('replay',)))
    if winner is not None:
        gui.add('winner', mygui.Text(window, (welcome_window_size[0] / 2 - 90, 200), (180, 30),
                                     f'{winner} has won!'))
    else:
        gui.add('cn_lost', mygui.Text(window, (welcome_window_size[0] / 2 - 90, 200), (180, 30),
                                      f'No connection!'))
    window.blit(bg, (0, 0))
    gui.draw()
    while menu != 'replay':
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            gui.handle_event(event)
        pygame.display.update()
    winner = None
    menu = 'play'
