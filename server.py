import re
import threading
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pickle
import socket
import time
import pygame
from race_server import *
from threading import Thread
from _thread import start_new_thread

from multiprocessing.connection import Listener

from car_m import Car_m




class Server:

    def __init__(self):
        self.ThreadCount = 0                # * counter of current connected clients
        self.host = ''                      # * Server IP address
        self.port = 0                       # * Port used to connect
        self.players = []                   # * players statistics
        self.cars = []                      # * list of cars on track
        self.players_number = 2             # * number of players in one game
        self.track_name = './tracks/track_2.txt'
        self.track = Track(self.track_name)
        self.race = None
        self.game_not_in_progress = False
        self.winner = None

    def threaded_client(self, client, player):
        global name
        print("New player connect")


        while True:
            if self.ThreadCount == -1:
                client.close()
                return
            try:
                if self.ThreadCount == self.players_number:
                    client.send(player)
                    break
                elif self.ThreadCount == -1:
                    client.close()
                    return
                else:
                    time.sleep(0.002)
                    client.send(-1)
            except ConnectionResetError:
                print("[10054] Client {} disconnected from lobby".format(player))
                self.ThreadCount = -1
                return

        try:
            client.send(self.track_name)  # _ sending information about map
            client.send(self.players_number)  # _ -||- number of players that will play
        except:
            print("Client {} is not responding".format(player))
            return

        try:
            name = client.recv()
        except:
            print("Error when receiving the name")
            return

        self.cars[player].__setattr__('name', name)
        self.players[player] = self.cars[player].get_param()
        while None in self.players:
            time.sleep(0.01)

        # _ send current starting param
        client.send(self.players)

        # _ client game loop (sen/rec)
        while True:
            if self.game_not_in_progress:
                break
            try:
                # _ receive information about event form player
                received = client.recv()  # received[0 - key, 1-type]
                if received != 0:
                    event = Event(received[0], received[1])
                    self.race.handle_event(event, self.cars[player])
                time.sleep(0.005)

                # _ sending data about actual status
                self.players[player] = self.cars[player].get_param()
                client.send(self.winner)
                client.send(self.players)
                client.send(self.race.get_times_of_cars())
                client.send(self.race.get_map_bonuses())
                client.send(self.race.get_car_bonuses())

            except:
                break
        print("Client {} disconnected".format(name))
        self.game_not_in_progress = True
        client.close()

    def clear_game(self):
        self.game_not_in_progress = False
        self.ThreadCount = -1
        self.players = []
        self.cars.clear()
        self.race = RaceServer(self.track)
        for i in range(self.players_number):
            self.cars.append(Car_m())
            self.race.add_car(self.cars[i])
        self.winner = None

    def start(self):
        # _ reading IP address and PORT
        try:
            with open("server.cfg", encoding='utf-8') as f:
                try:
                    line = f.readline()
                    ip_address = r'(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})'
                    self.host = re.findall(ip_address, line)[0]
                    line = f.readline()
                    port = r'([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])'
                    self.port = int(re.findall(port, line)[0])
                    line = f.readline()
                    self.players_number = int(line.split(" = ")[1])
                    print("Configuration: IP:PORT= {}:{}, players nr: {}".format(self.host, self.port, self.players_number))
                except:
                    print("Bad configured server.cfg file.")
                    return
        except:
            print("Can't open file server.cfg")
            return
        server_sock = Listener((self.host, self.port))


        while True:
            # self.race = RaceServer(self.track)
            #
            # for i in range(self.players_number):
            #     self.cars.append(Car())
            #     self.race.add_car(self.cars[i])
            self.clear_game()
            print("Listening for new game started.")
            try:
                while self.ThreadCount < self.players_number:
                    conn = server_sock.accept()
                    if self.ThreadCount == -1:
                        self.clear_game()
                        self.ThreadCount = 0
                    self.players.append(None)

                    # _ creating new handler for new client
                    # start_new_thread(self.threaded_client, (conn, self.ThreadCount, ))
                    Thread(target=self.threaded_client, args=(conn, self.ThreadCount,)).start()
                    self.ThreadCount += 1
                    print('Thread Number: ' + str(self.ThreadCount))



                # _ game loop
                print("Starting new Game")
                time_0 = perf_counter()
                clock = pygame.time.Clock()
                while True:
                    delta_time, time_0 = perf_counter() - time_0, perf_counter()
                    if self.race.hasWinner():
                        self.winner = self.players[self.race.winner][1]
                        time.sleep(1)
                        break
                    self.race.run(delta_time)
                    if self.game_not_in_progress:
                        break

                time.sleep(1)
                print("Game closed")
                # _ clearing for next new game
                # self.clear_game()

            except:
                print("Error in main loop")
                break
        server_sock.close()


if __name__ == "__main__":
    server = Server()
    server.start()
