import sys
import socket
import select
import json


def set_server_address():
    host = ""
    valid_addr = False
    while not valid_addr:
        host = input("\n[Client] Croupier Address: ")

        addr_split = host.split(".")

        if len(addr_split) != 4:
            print("[Client] Invalid address!")
            continue

        try:
            socket.inet_aton(host)
            valid_addr = True
        except:
            valid_addr = False
            print("[Client] Invalid address!")

    port = 0
    valid_port = False
    while not valid_port:
        port = input("[Client] Croupier Port: ")

        for digit in port:
            if not digit.isdigit():
                valid_port = False
                print("[Client] Invalid port!")
                break
            else:
                valid_port = True

        if valid_port and (int(port) < 1024 or int(port) > 65535):
            print("[Client] Invalid port!")
            valid_port = False

    return host, port


def client_init_menu(game_socket, host, port):
    option = -1
    while 1:

        print("\n[Client] Welcome to the game client!\n"
              "1- Configure croupier address\n"
              "2- Connect to the croupier\n"
              "3- Exit")

        option = input("\nOption: ")

        if option == "1":
            host, port = set_server_address()
        elif option == "2":
            if host != "" and port != "":
                connect_to_server(game_socket, host, port)
                break
            else:
                print("\n[Client] Croupier address not configured!")
        elif option == "3":
            print("\n[Client] Shutting down.")
            game_socket.close()
            sys.exit(20)
        else:
            print("[Client] Invalid choice! Try again.")


def client_table_menu(game_socket):
    option = -1
    while 1:

        print("\n[Client] Game lobby:\n"
              "1- Create table\n"
              "2- List joinable tables\n"
              "3- Join table\n"
              "4- Join random table\n"
              "5- Exit")

        option = input("\nOption: ")

        if option == "1":
            return 3, {"type": "CreateTable"}
        elif option == "2":
            return 6, {"type": "RequestJoinableTables"}
        elif option == "3":
            table_to_join = choose_table_id()
            return 8, {"type": "JoinOpenTable", "table_id": table_to_join}
        elif option == "4":
            return 11, {"type": "JoinRandomTable"}
        elif option == "5":
            print("\n[Client] Shutting down.")
            game_socket.close()
            sys.exit(20)
        else:
            print("[Client] Invalid choice! Try again.")


def in_table_not_leader():

    global ready_to_begin_game
    global tmp_state_saver

    option = -1
    while 1:
        menu_string = "\n[Client] Table operations:\n"\
                      "1- Flag self as "

        if ready_to_begin_game:
            menu_string += "not ready\n"
        else:
            menu_string += "ready\n"

        menu_string += "2- List table information\n"\
                       "3- Leave table"

        print(menu_string)
        option = input("\nOption: ")

        if option == "1":
            ready_to_begin_game = not ready_to_begin_game
            tmp_state_saver = game_state
            return 12, {"type": "ChangeReadyState", "table_id": joined_table_id, "ready": ready_to_begin_game}
        elif option == "2":
            tmp_state_saver = game_state
            return 13, {"type": "RequestTableInfo", "table_id": joined_table_id}
        elif option == "3":
            return 14, {"type": "LeaveTable", "table_id": joined_table_id}
        else:
            print("[Client] Invalid choice! Try again.")


def in_table_leader():

    global ready_to_begin_game
    global tmp_state_saver

    option = -1
    while 1:
        menu_string = "\n[Client] Table operations:\n" \
                      "1- Start the game\n"\
                      "2- Flag self as "

        if ready_to_begin_game:
            menu_string += "not ready\n"
        else:
            menu_string += "ready\n"

        menu_string += "3- List table information\n"\
                       "4- Disband table"

        print(menu_string)
        option = input("\nOption: ")

        if option == "1":
            return 16, {"type": "StartGame", "table_id": joined_table_id}
        elif option == "2":
            ready_to_begin_game = not ready_to_begin_game
            tmp_state_saver = game_state
            return 12, {"type": "ChangeReadyState", "table_id": joined_table_id, "ready": ready_to_begin_game}
        elif option == "3":
            tmp_state_saver = game_state
            return 13, {"type": "RequestTableInfo", "table_id": joined_table_id}
        elif option == "4":
            return 15, {"type": "DisbandTable", "table_id": joined_table_id}
        else:
            print("[Client] Invalid choice! Try again.")


def connect_to_server(game_socket, host, port):
    print("\n[Client] Connecting to croupier at %s:%d..." % (host, int(port)))

    if game_socket.connect_ex((host, int(port))) != 0:
        print("[Client] Connection failed!")
    else:
        print("[Client] Connection successful!")


def choose_table_id():
    tid = -1
    while tid < 0:
        tid = input("\n[Client] Table to join: ")

        try:
            tid = int(tid)
        except:
            tid = -1

    return tid


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_host, server_port = ("", "")

send_buffer = [{
    "type": "ConnectionRequest"
}]

# Current step in the game
# 0  - Requesting Connection
# 1  - Connection Accepted
# 2  - Acknowledge Prepared to Send
# 3  - No Table Joined (at table menu)
# 4  - Requested Table Creation
# 5  - Table Created (at table leader menu)
# 6  - Requested Joinable Table List
# 7  - Awaiting Joinable Table List
# 8  - Requesting to Join Table
# 9  - Awaiting Response on Table Join
# 10 - Table Joined (not leader)
# 11 - Requested Random Table Assignment
# 12 - Changing ready state
# 13 - Requesting table information
# 14 - Requesting to leave Table
# 15 - Requesting Table Disband
# 16 - Requesting Game Start
# 17 - Game Starting
#
#
#
#
#
game_state = 0
tmp_state_saver = 0

# Id of the currently joined table. Id valued at -1 means no table joined.
joined_table_id = -1

# States whether the client is ready to start the game
ready_to_begin_game = False

client_init_menu(client_socket, server_host, server_port)

while True:

    if game_state == 3:
        game_state, tmp_message = client_table_menu(client_socket)
        send_buffer.append(tmp_message)
    elif game_state == 5:
        game_state, tmp_message = in_table_leader()
        send_buffer.append(tmp_message)
    elif game_state == 10:
        game_state, tmp_message = in_table_not_leader()
        send_buffer.append(tmp_message)

    if send_buffer:
        client_socket.sendall(json.dumps(send_buffer[0]).encode("utf-8"))
        send_buffer = send_buffer[1:]

        if game_state == 0:
            game_state = 1
        elif game_state == 2:
            game_state = 3
        elif game_state == 3:
            game_state = 4
        elif game_state == 6:
            game_state = 7
        elif game_state == 8:
            game_state = 9

    else:

        read_sockets, write_socket, error_socket = select.select([client_socket], [], [])

        for sock in read_sockets:

            if sock == client_socket:
                received_message = sock.recv(1024)

                if received_message:
                    print("\n[Client] %s:%s : %s" % (sock.getpeername()[0], sock.getpeername()[1],
                                                     received_message.decode("utf-8")))

                    if game_state == 1:
                        send_buffer.append({"type": "ConnectionAcknowledge"})
                        game_state = 2
                    elif game_state == 4:
                        decoded_message = json.loads(received_message.decode("utf-8"))
                        joined_table_id = decoded_message["table_id"]
                        game_state = 5
                    elif game_state == 7:
                        decoded_message = json.loads(received_message.decode("utf-8"))

                        print("\nList of joinable tables:")
                        for table in decoded_message["joinableTables"]:
                            print("Table ID: %d,\tNumber of Players: %d,\tPlayers: %s" % (table["id"],
                                                                                          table["player_num"],
                                                                                          table["players"]))

                        game_state = 3
                    elif game_state == 9:
                        decoded_message = json.loads(received_message.decode("utf-8"))
                        if decoded_message["type"] == "TableJoined":
                            joined_table_id = decoded_message["table_id"]
                            game_state = 10
                        elif decoded_message["type"] == "InvalidTable":
                            game_state = 3
                    elif game_state == 11:
                        decoded_message = json.loads(received_message.decode("utf-8"))
                        if decoded_message["type"] == "NoJoinableTable":
                            game_state = 3
                        elif decoded_message["type"] == "RandomTableJoined":
                            game_state = 10
                            joined_table_id = decoded_message["table_id"]
                    elif game_state == 12:
                        decoded_message = json.loads(received_message.decode("utf-8"))

                        if decoded_message["type"] == "ReadyStateChanged":
                            game_state = tmp_state_saver
                        elif decoded_message["type"] == "TableDisbanded":
                            joined_table_id = -1
                            ready_to_begin_game = False
                            game_state = 3
                        elif decoded_message["type"] == "GameAlreadyStarting":
                            game_state = 17

                    elif game_state == 13:
                        decoded_message = json.loads(received_message.decode("utf-8"))

                        if decoded_message["type"] == "ReturnTableInfo":
                            decoded_table = decoded_message["table"]
                            print("\nTable ID: %d,\tNumber of Players: %d,\tPlayers: %s" % (decoded_table["id"],
                                                                                          decoded_table["player_num"],
                                                                                          decoded_table["players"]))

                            game_state = tmp_state_saver
                        elif decoded_message["type"] == "TableDisbanded":
                            joined_table_id = -1
                            ready_to_begin_game = False
                            game_state = 3
                        elif decoded_message["type"] == "GameAlreadyStarting":
                            game_state = 17
                    elif game_state == 14 or game_state == 15:
                        decoded_message = json.loads(received_message.decode("utf-8"))

                        if decoded_message["type"] == "GameAlreadyStarting":
                            print("\n[Client] Round Starting.")
                            game_state = 17
                        else:
                            joined_table_id = -1
                            ready_to_begin_game = False
                            game_state = 3
                    elif game_state == 16:
                        decoded_message = json.loads(received_message.decode("utf-8"))

                        if decoded_message["type"] == "GameStarting":
                            print("\n[Client] Round Starting.")
                            game_state = 17
                        elif decoded_message["type"] == "InsufficientPlayers":
                            print("\n[Client] Insufficient Players: %d" % decoded_message["player_num"])
                            game_state = 5
                        elif decoded_message["type"] == "InsufficientReadyPlayers":
                            print("\n[Client] Insufficient Ready Players: %d" % decoded_message["ready_num"])
                            game_state = 5



client_socket.close()
