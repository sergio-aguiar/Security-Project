import sys
import socket
import select
import json


def set_server_address():

    host = ""
    valid_addr = False
    while not valid_addr:
        host = input("\n[Client] Server Address: ")

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
        port = input("[Client] Server Port: ")

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
        print("\n[Client] Welcome to the game client!\n1- Configure server address\n2- Connect to the server\n3- Exit")
        option = input("\nOption: ")

        if option == "1":
            host, port = set_server_address()
        elif option == "2":
            if host != "" and port != "":
                connect_to_server(game_socket, host, port)
                break
            else:
                print("\n[Client] Server address not configured!")
        elif option == "3":
            print("\n[Client] Shutting down.")
            game_socket.close()
            sys.exit(20)
        else:
            print("[Client] Invalid choice! Try again.")


def connect_to_server(game_socket, host, port):
    print("\n[Client] Connecting to server at %s:%d..." % (host, int(port)))

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
#
#
#
#
#
game_state = 0

client_init_menu(client_socket, server_host, server_port)

while True:

    if send_buffer:
        client_socket.sendall(json.dumps(send_buffer[0]).encode("utf-8"))
        send_buffer = send_buffer[1:]
    else:

        read_sockets, write_socket, error_socket = select.select([client_socket], [], [])

        for sock in read_sockets:

            if sock == client_socket:
                received_message = sock.recv(1024)

                if received_message:
                    print("[Client] %s:%s : %s" % (sock.getpeername()[0], sock.getpeername()[1],
                                                   received_message.decode("utf-8")))

                    if game_state == 0:
                        game_state = 1
                        send_buffer.append({"type": "ConnectionAcknowledge"})
                    if game_state == 1:
                        game_state = 2

        # else:
        #
        #     tmp_message = sys.stdin.readline()
        #
        #     if game_state == 0:
        #         client_message = {
        #             "type": "ConnectionRequest"
        #         }
        #     elif game_state == 1:
        #         client_message = {
        #             "type": "ConnectionAcknowledge"
        #         }
        #
        #     client_socket.sendall(json.dumps(client_message).encode("utf-8"))
        #
        #     sys.stdout.flush()

client_socket.close()
