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
    while option != 0:

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


def client_table_menu():
    option = -1
    while option != 0:

        print("\n[Client] Table operations:\n"
              "1- Create table\n"
              "2- List open tables\n"
              "3- Join open table\n"
              "4- Await random table assignment\n"
              "5- Exit")

        option = input("\nOption: ")

        if option == "1":
            return 3, {"type": "CreateTable"}
        elif option == "2":
            return 6, {"type": "RequestOpenTables"}
        elif option == "3":
            return
        elif option == "4":
            return
        elif option == "5":
            return
        else:
            print("[Client] Invalid choice! Try again.")


def connect_to_server(game_socket, host, port):
    print("\n[Client] Connecting to croupier at %s:%d..." % (host, int(port)))

    if game_socket.connect_ex((host, int(port))) != 0:
        print("[Client] Connection failed!")
    else:
        print("[Client] Connection successful!")


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_host, server_port = ("", "")

send_buffer = [{
    "type": "ConnectionRequest"
}]

# Current step in the game
# 0 - Requesting Connection
# 1 - Connection Accepted
# 2 - Acknowledge Prepared to Send
# 3 - No Table Joined
# 4 - Requested Table Creation
# 5 - Table Created (at table menu)
# 6 - Requested Open Table List
# 7 - Awaiting Open Table List
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
game_state = 0

client_init_menu(client_socket, server_host, server_port)

while True:

    if game_state == 3:
        game_state, tmp_message = client_table_menu()
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
                        game_state = 5
                    elif game_state == 7:
                        open_tables = json.loads(received_message.decode("utf-8"))

                        print("\nList of open tables:")
                        for table in open_tables["openTables"]:
                            print("Table ID: %d,\tNumber of Players: %d,\tPlayers: %s" % (table["id"],
                                                                                          table["player_num"],
                                                                                          table["players"]))

                        game_state = 3

client_socket.close()
