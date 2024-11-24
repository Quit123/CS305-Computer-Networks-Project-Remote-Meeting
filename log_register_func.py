import hmac
import os
import socket
import hashlib
import re
import random
import ast
import fileinput

user_inf_txt = 'users.txt'
login_commands = [
    '?',
    'help',
    'exit',
    'logout',
    'changepwd {newpassword}',
]


def SUCCESS(message):
    """
    This function is designed to be easy to test, so do not modify it
    """
    return '200:' + message


def FAILURE(message):
    """
    This function is designed to be easy to test, so do not modify it
    """
    return '400:' + message


def ntlm_hash_func(password):
    """
    This function is used to encrypt passwords by the MD5 algorithm
    """
    # 1. Convert password to hexadecimal format
    hex_password = ''.join(format(ord(char), '02x') for char in password)

    # 2. Unicode encoding of hexadecimal passwords
    unicode_password = hex_password.encode('utf-16le')

    # 3. The MD5 digest algorithm is used to Hash the Unicode encoded data
    md5_hasher = hashlib.md5()
    md5_hasher.update(unicode_password)

    # Returns the MD5 Hash
    return md5_hasher.hexdigest()


def connection_establish(ip_p):
    """
    Task 1.1 Correctly separate the IP address from the port number in the string
    Returns the socket object of the connected server when the socket server address pointed to by IP:port is available
    Otherwise, an error message is given
    :param ip_p: str 'IP:port'
    :return socket_client: socket.socket() or None
    :return information: str 'success' or error information
    """
    try:
        ip, port_s = ip_p[0], ip_p[1]
        port = int(port_s)

        socket_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        socket_client.connect((ip, port))

        return socket_client, 'success\n'
    except ValueError as e:
        return None, ('ValueError:' + str(e) + '\n' +
                      'Value Error: Invalid IP Address or Port format, check use "IP:port" format')
    except socket.error as e:
        error_m = 'Please check your IP Address or Port format.'
        return None, (error_m + 'Socket Error: ' + str(e))
    except Exception as e:
        return None, ('Error: An unexpected error occurred:' + str(e))

    # TODO: finish the codes


def load_users(user_records_txt):
    """
    Task 2.1 Load saved user information (username and password)
    :param user_records_txt: a txt file containing username and password records
    :return users: dict {'username':'password'}
    """
    # TODO: finish the codes
    user_infos = {}
    try:
        with open(user_records_txt, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                username, password = line.split(':', 1)
                user_infos[username] = password
    except FileNotFoundError:
        print("user_records_txt is not found. Creating a new file.")
        with open(user_records_txt, 'w', encoding='utf-8'):
            pass
    except Exception as e:
        print(f"Something went wrong: {e}")
    return user_infos


def user_register(cmd, users):
    """
    Task 2.2 Register command processing
    :param cmd: Instruction string
    :param users: The dict to hold information about all users
    :return feedback message: str
    """
    # TODO: finish the codes

    username, password = cmd[1], cmd[2]

    username = str(username)

    if username in users:
        return FAILURE('Username already registered')

    users[username] = password

    try:
        with open('users.txt', 'a', encoding='utf-8') as f:
            f.write(f"{username}:{password}\n")
    except FileNotFoundError:
        return FAILURE('User file not found')

    return SUCCESS(f"User: {username} : Registering successfully")


async def login_authentication(writer, reader, cmd, users):
    """
    Task 2.3 Login authentication
        You can simply use password comparison for authentication (Task 2.3 basic score)
        It can also be implemented according to the NTLM certification process to obtain Task 3.2 and 3.5 scores
    :param conn: socket connection to the client
    :param cmd: Instruction string
    :param users: The dict to hold information about all users
    :return: feedback message: str, login_user: str
    """
    # TODO: finish the codes

    username, password = cmd[1], cmd[2]

    if username not in users:
        return FAILURE("Username not registered"), None

    if password not in users[username]:
        return FAILURE("Password is incorrect"), None
    else:
        challenge = generate_challenge()
        await writer.write(challenge)

        client_response = await reader.read(1024)

        expected_response = calculate_response(password, challenge)

        if hmac.compare_digest(client_response, expected_response):
            return SUCCESS(f"User: {username} : Login successfully"), username
        else:
            return FAILURE("Failed to login"), None


def server_message_encrypt(message, client_instance):
    """
    Task 3.1 Determine whether the command is "login", "register", or "changepwd",
    If so, it encrypts the password in the command and returns the encrypted message and Password
    Otherwise, the original message and None are returned
    :param message: str message sent to server:
    :return encrypted message: str, encrypted password: str
    """

    # TODO: finish the codes
    global established_client
    def encrypt(type, cmd):
        unencrypted_message = cmd[type - 1]
        if len(cmd) > type:
            for i in cmd[type]:
                unencrypted_message += f" {i}"
        encrypted_password = ntlm_hash_func(unencrypted_message)
        encrypted_message = None
        if type == 3:
            encrypted_message = f"{cmd[0]} {cmd[1]} {encrypted_password}"
        elif type == 2:
            encrypted_message = f"{cmd[0]} {encrypted_password}"

        return encrypted_message, encrypted_password

    cmd = message.split()
    if cmd[0] in ['login', 'register']:
        if len(cmd) < 3:
            client_instance.established_client.send(message.encode("utf-8"))
            recv_data = server_response(client_instance.established_client, None).decode("utf-8")
            return recv_data
        else:
            print("conf_client.established_client:", client_instance.established_client)
            encrypted_message, encrypted_password = encrypt(3, cmd)
            client_instance.established_client.send(encrypted_message.encode("utf-8"))
            recv_data = server_response(client_instance.established_client, encrypted_password).decode("utf-8")
            return recv_data
    elif cmd[0] == 'changepwd':
        if len(cmd) < 2:
            client_instance.established_client.send(message.encode("utf-8"))
            recv_data = server_response(client_instance.established_client, None).decode("utf-8")
            return recv_data
        else:
            encrypted_message, encrypted_password = encrypt(2, cmd)
            client_instance.established_client.send(encrypted_message.encode("utf-8"))
            recv_data = server_response(client_instance.established_client, encrypted_password).decode("utf-8")
            return recv_data
    else:
        return message, None


def generate_challenge():
    """
    Task 3.2
    :return information: bytes random bytes as challenge message
    """
    # TODO: finish the codes
    return os.urandom(8)


def calculate_response(ntlm_hash, challenge):
    """
    Task 3.3
    :param ntlm_hash: str encrypted password
    :param challenge: bytes random bytes as challenge message
    :return expected response
    """
    # TODO: finish the codes
    key = ntlm_hash.encode('utf-8')
    return hmac.new(key, challenge, hashlib.sha256).digest()


def server_response(server, password_hash):
    """
    Task 3.4 Receives the server response and determines whether the message returned by the server is an authentication challenge.
    If it is, the challenge will be authenticated with the encrypted password, and the authentication information will be returned to the server to obtain the login result
    Otherwise, the original message is returned
    :param server: socket server
    :param password_hash: encrypted password
    :return server response: str
    """
    # TODO: finish the codes
    response = server.recv(1024)

    fail_sign = "400".encode('utf-8')
    register_sign = "Registering successfully".encode('utf-8')
    change_sign = "changed password".encode('utf-8')

    if password_hash is not None and fail_sign not in response and register_sign not in response and change_sign not in response:
        response = calculate_response(password_hash, response)
        server.sendall(response)
        return server.recv(1024)
    else:
        return response


def login_cmds(receive_data, users, login_user):
    """
    Task 4 Command processing after login
    :param receive_data: Received user commands
    :param users: The dict to hold information about all users
    :param login_user: The logged-in user
    :return feedback message: str, login user: str
    """

    # TODO: finish the codes
    def is_number(s):
        return re.match(r'^-?\d+(\.\d+)?$', s)
    cmd = receive_data.split(' ')
    type = cmd[0]
    if type == 'changepwd':
        if len(cmd) > 2:
            return (f"USER:{login_user}:\n" + FAILURE("Space is not allowed in password")), login_user
        elif len(cmd) < 2:
            return (f"USER:{login_user}:\n" + FAILURE("Wrong changepwd format")), login_user
        else:
            new_password = cmd[1]
            try:
                temp_file_path = user_inf_txt + '.tmp'
                with open(user_inf_txt, mode='r') as file, open(temp_file_path, mode='w') as temp_file:
                    for line in file:
                        user, password = line.strip().split(':')
                        if user == login_user:
                            temp_file.write(f"{login_user}:{new_password}\n")
                        else:
                            temp_file.write(line)
                os.replace(temp_file_path, user_inf_txt)
                return (f"USER:{login_user}:\n" + SUCCESS("Successfully changed password")), login_user
            except FileNotFoundError:
                return (f"USER:{login_user}:\n" + FAILURE("File not found")), login_user
            except Exception as e:
                return (f"USER:{login_user}:\n" + FAILURE("Exception error:" + str(e))), login_user

    elif type == '?' or type == 'help' or type == 'ls':
        feedback_data = 'Available commends: \n\t' + '\n\t'.join(login_commands)
        return (f"USER:{login_user}:\n" + SUCCESS(feedback_data)), login_user

    elif type == 'exit':
        feedback_data = 'disconnected'
        return (f"USER:{login_user}:\n" + SUCCESS(feedback_data)), None

    elif type == 'logout':
        return (f"USER:{login_user}:\n" + SUCCESS(f"{login_user} logout successfully")), None

    else:
        return (f"USER:{login_user}:\n" + FAILURE("Invalid command")), login_user
