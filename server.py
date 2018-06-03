"""
This module is implementation of Multi threaded TCP Server.
The Queue is used to share items between the threads.
The class ServerThread extends Thread class that works with one client.

android client (socket+address)
client_pool - queue - stock of resources for ServerThread threads
new_client - tuple of client socket and client address, address - tuple of client ip and client port
one_game_list - list of one game players couple
j - id of client

IP - server IP, '' mean that will using every IP of current computer
PORT_NUMBER - server port
"""
import socket
import Queue
import threading
import random
import time
import json
import sys


androids = []
IP = ''
PORT_NUMBER = 12345

# Create our Queue. The Queue is used to share items between the threads.
client_pool = Queue.Queue(0)


class ServerThread(threading.Thread):
    """
    Extends Thread class that works with one client
    """
    def __init__(self):
        """
        overriding of constructor, initiates the relevant parameters
        """
        threading.Thread.__init__(self)
        self.wait_to_start = True
        self.id = 0
        self.players = None
        self.socket = None

    def run(self):
        """
        overriding Thread run method, Have our thread serve "forever"
        """
        while True:
            # Get a client out of the queue
            data_tuple = client_pool.get()

            # Check if we actually have an actual client in the client variable:
            if data_tuple:
                client = data_tuple[0]

                port = client[1][1]
                ip = client[1][0]

                self.socket = client[0]
                self.players = data_tuple[1]
                self.players.append(self)

                self.id = int(data_tuple[2])

                self.socket.sendall("Wait for start##" + str(self.id) + "\n")
                # starts the game
                if self.id == 1:
                    turn = random.randint(0, 1)
                    for item in self.players:
                        item.socket.sendall("start##" + str(turn) + "\n")
                        item.wait_to_start = False
                    time.sleep(2)

                while self.wait_to_start:
                    time.sleep(2)

                while True:
                    buf = self.socket.recv(1024)
                    buf = buf.strip()
                    print ("Server got:" + buf)

                    if buf == "bye":
                        # ends the connection
                        print ("bye")
                        self.socket.sendall("bye\n")

                        break
                    elif str(buf).startswith("computer"):
                        # The initial data from a java client
                        buf = str(buf)
                        buf = buf[8:]
                        print (buf)
                        for item in self.players:
                            if item.id != self.id:
                                item.socket.sendall(str(buf) + "\n")
                    elif str(buf).startswith("tool") or str(buf).startswith("fight"):
                        # regular movement of the game
                        for item in self.players:
                            if item.id != self.id:
                                print ("server sent " + buf + "\n")
                                item.socket.sendall(buf+"\n")
                    else:
                        # if it is the last message of a turn, sends it to the android
                        if str(buf).startswith("turn"):
                            print ("turn")
                            buf = str(buf)
                            array = buf.split("##")
                            ob_list = []
                            d = {'p1': array[1], 'p2': array[2]}
                            ob_list.append(d)
                            j_str = json.dumps(ob_list)
                            print (str(len(androids)) + " spaces")
                            if len(androids) > 0:
                                print ("sending")
                                try:
                                    androids[0][0].sendall(j_str+"\n")
                                except Exception:
                                    print ("android is dead")
                        for item in self.players:
                            item.socket.sendall(buf+"\n")

                self.socket.close()
                print ('Closed connection from ip=', ip, "port=", port)
                self.players.remove(self)


def kill_android():
    """
    kills the android at the first place
    """
    try:
        if androids[0]:
            androids[0] = None
        if androids[1]:
            androids[0] = androids[1]
    except IndexError:
        print "index error"


def main():
    """
    the function that runs the server
    """
    # Start some threads:
    for x in range(4):
        ServerThread().start()  # ServerThread() - run constructor, start() - run run() method

    # Set up the server:
    # create an INET, STREAMing socket
    # INET socket - IP protocol based sockets which use IP addresses and ports
    # Address Family : AF_INET (this is IP version 4 or IPv4 - 32 bit address - 4 byte address)
    # Type : SOCK_STREAM (this means connection oriented TCP protocol)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Helps to system forget server after 1 second
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:

        # bind socket to any self ip and  PORT_NUMBER
        server.bind((IP, PORT_NUMBER))

        # become a server socket
        server.listen(5)
        print "Server is listening"

        j = 0  # player index in couple

        #  Create list of one couple
        one_game_list = []

        # Have the server serve "forever":
        while True:
            new_client = server.accept()  # Connected point. Server wait for client
            string = new_client[0].recv(1024)
            string = str(string).strip()
            if not string == "android":
                client_pool.put((new_client, one_game_list, j))  # add tuple to  clientPool
                j = j + 1
                if j == 2:  # last player in the current couple
                   
                    j = 0
                    one_game_list = []  # Create new list of one couple
            else:
                print "android"
                if len(androids) > 0:
                    time_t0 = threading.Timer(600, kill_android())
                    time_t0.start()
                    androids[0] = new_client
                else:
                    androids.append(new_client)
    except Exception, e:
        print e
        server.close()
        sys.exit(1)


if __name__ == '__main__':
    main()
