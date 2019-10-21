import sys
import socket
import select
import json
import random
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
                                               "player_num": 1, "players": [[socket_object.getpeername(), False ]],
                                               "in-game": False})

                                print("[Server] Tables: %s" % str(tables))

                                global_table_id += 1
                                sock["state"] = 3
                            elif received_message["type"] == "JoinOpenTable":
                                sock["state"] = 4
                            elif received_message["type"] == "JoinRandomTable":
                                sock["state"] = 6

                            reply_to_client(socket_object, received_message, sock["state"])

                            if sock["state"] == 3:
                                sock["state"] = 2
                        elif sock["state"] == 5:
                            if received_message["type"] == "ChangeReadyState":
                                change_ready_state(socket_object, received_message["table_id"], received_message["ready"])
                                sock["state"] = 7
                            elif received_message["type"] == "RequestTableInfo":
                                sock["state"] = 8

                            reply_to_client(socket_object, received_message, sock["state"])

                            if sock["state"] == 7 or sock["state"] == 8:
                                sock["state"] = 5
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

            if received_message["type"] == "RequestJoinableTables":
                reply = {
                    "type": "ReturnJoinableTables",
                    "joinableTables": get_joinable_tables()
                }
                client_sock.sendall(json.dumps(reply).encode("utf-8"))

        elif state == 3:
            reply = {
                "type": "TableCreated"
            }
            client_sock.sendall(json.dumps(reply).encode("utf-8"))

        elif state == 4:
            join_table_by_id(client_sock, received_message["table_id"])

            if is_joinable_table(received_message["table_id"]):
                reply = {
                    "type": "TableJoined",
                    "table_id": received_message["table_id"]
                }
                update_game_state_by_sock(client_sock, 5)
            else:
                reply = {
                    "type": "InvalidTable"
                }
                update_game_state_by_sock(client_sock, 2)

            client_sock.sendall(json.dumps(reply).encode("utf-8"))
            print("[Server] Tables: %s" % str(tables))

        elif state == 6:
            joinable_tables = get_joinable_tables()

            if len(joinable_tables) == 0:
                reply = {
                    "type": "NoJoinableTable"
                }
                update_game_state_by_sock(client_sock, 2)
            else:
                table_id_to_join = joinable_tables[random.randint(0, len(joinable_tables) - 1)]["id"]
                join_table_by_id(client_sock, table_id_to_join)

                reply = {
                    "type": "RandomTableJoined",
                    "table_id": table_id_to_join
                }
                update_game_state_by_sock(client_sock, 5)

            client_sock.sendall(json.dumps(reply).encode("utf-8"))
            print("[Server] Tables: %s" % str(tables))

        elif state == 7:
            reply = {
                "type": "ReadyStateChanged"
            }
            print("[Server] Tables: %s" % str(tables))
            client_sock.sendall(json.dumps(reply).encode("utf-8"))

        elif state == 8:
            requested_table = get_table_by_id(received_message["table_id"])

            reply = {
                "type": "ReturnTableInfo",
                "table": requested_table
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


def get_joinable_tables():

    joinable_tables = []
    for table in tables:
        if not table["in-game"]:
            joinable_tables.append(table)

    return joinable_tables


def is_joinable_table(tid):

    for table in tables:
        if table["id"] == tid:
            if not table["in-game"]:
                return True

    return False


def join_table_by_id(client_sock, tid):

    for table in tables:
        if table["id"] == tid and table["player_num"] <= 4:
            table["players"].append([client_sock.getpeername(), False])
            table["player_num"] += 1


def update_game_state_by_sock(sock, new_state):

    for state in game_states:
        if state["socket"] == sock:
            state["state"] = new_state


def change_ready_state(sock, tid, ready):

    for table in tables:
        if table["id"] == tid:
            for player in table["players"]:
                if player[0] == sock.getpeername():
                    player[1] = ready


def get_table_by_id(tid):

    for table in tables:
        if table["id"] == tid:
            return table


print("[Server] Initializing.")

server_host, server_port = ("127.0.0.1", 1024)
client_list = []

# Current step in the game
# 0 - Connected
# 1 - Awaiting Acknowledge
# 2 - Awaiting Menu Option
# 3 - Table Created
# 4 - Checking Open Table
# 5 - Table Joined (not leader)
# 6 - Attempting Random Table Assignment
# 7 - Ready State Changed
# 8 - Requesting Table Info
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
