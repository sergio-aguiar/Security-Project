import sys
import socket
import select
import json
from _thread import *


def client_thread(socket_object, socket_address):

    global global_table_id

    while True:
        try:
            received_data = socket_object.recv(1024)

            if received_data:

                received_message = json.loads(received_data.decode("utf-8"))

                print("[Server] %s:%s : %s" % (socket_object.getpeername()[0], socket_object.getpeername()[1] ,
                                               received_message))

                for sock in game_states:
                    if sock["socket"] == socket_object:
                        if sock["state"] == 0:
                            reply_to_client(socket_object, received_message, sock["state"])
                            sock["state"] = 1
                        elif sock["state"] == 1:
                            reply_to_client(socket_object, received_message, sock["state"])
                            sock["state"] = 2
                        elif sock["state"] == 2:

                            if received_message["type"] == "CreateTable":
                                tables.append({"id": global_table_id, "leader": socket_object.getpeername(),
                                               "player_num": 1, "players": [socket_object.getpeername()], "open": False,
                                               "in-game": False})

                                print("[Server] Tables: %s" % str(tables))

                                global_table_id += 1
                                sock["state"] = 3

                            reply_to_client(socket_object, received_message, sock["state"])

                            if sock["state"] == 3:
                                sock["state"] = 2

            else:
                disconnect_from_client(socket_object)
        except:
            continue


def reply_to_client(client_sock, received_message, state):
    try:
        if state == 0:
            reply = {
                "type": "ConnectionSuccessful"
            }
            client_sock.sendall(json.dumps(reply).encode("utf-8"))
        elif state == 2:
            if received_message["type"] == "RequestOpenTables":
                reply = {"type": "ReturnOpenTables", "openTables": get_open_tables()}
                client_sock.sendall(json.dumps(reply).encode("utf-8"))
        elif state == 3:
            reply = {
                "type": "TableCreated"
            }
            client_sock.sendall(json.dumps(reply).encode("utf-8"))
    except:
        client_sock.close()
        disconnect_from_client(client_sock)


def disconnect_from_client(client_sock):

    if client_socket in client_list:
        client_list.remove(client_sock)

    for sock in game_states:
        if sock["socket"] == client_socket:
            game_states.remove(sock)


def get_open_tables():

    global tables

    open_tables = []
    for table in tables:
        if table["open"]:
            open_tables.append(table)

    return open_tables


print("[Server] Initializing.")

server_host, server_port = ("127.0.0.1", 1024)
client_list = []

# Current step in the game
# 0 - Connected
# 1 - Awaiting Acknowledge
# 2 - Awaiting Menu Option
# 3 - Table Created
#
#
#
#
#
#
game_states = []

global_table_id = 0
tables = []

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((server_host, server_port))
server_socket.listen(16)

print("[Server] Initialization successful on %s:%s." % (server_host, str(server_port)))

while True:

    client_socket, client_address = server_socket.accept()
    client_list.append(client_socket)
    game_states.append({"socket": client_socket, "state": 0})

    print("[Server] Connected to %s:%d" % (client_address[0], int(client_address[1])))
    start_new_thread(client_thread, (client_socket, client_address))

server_socket.close()
