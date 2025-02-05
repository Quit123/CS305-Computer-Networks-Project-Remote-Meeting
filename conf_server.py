import asyncio
import time

from util import *
import string
from asyncio import StreamReader, StreamWriter
from log_register_func import *

users = load_users(user_inf_txt)
print(users)


class ConferenceServer:
    def __init__(self, conference_id, title, port):
        # async server
        self.conference_id = conference_id  # conference_id for distinguish difference conference
        self.title = title
        self.data_serve_ports = [port, port + 1, port + 2, port + 3]  # self.data_serve_ports=[]
        self.data_types = ['audio', 'screen', 'camera', 'text']  # example data types in a video conference
        self.conns = []
        self.mode = 'Client-Server'  # or 'P2P' if you want to support peer-to-peer conference mode
        self.run = True
        self.tasks = []
        self.owner = None
        self.screen = False
        self.loops = {}
        self.sockets = {}

    async def handle_client(self, reader: StreamReader, writer: StreamWriter, message):
        message = message
        parts = message.strip().split(" ")
        address = writer.get_extra_info('peername')
        address = address[0]
        if parts[0].startswith('[COMMAND]'):
            if parts[1] == "JOIN":
                if address not in self.conns:
                    print(address)
                    self.conns.append(address)
                    print(f"SUCCESS join confernece {self.title}")
                    writer.write(f"SUCCESS join confernece {self.title} {self.data_serve_ports[0]}".encode())
                else:
                    print(self.conns)
                    writer.write("FAILURE already join".encode())
                await writer.drain()
            elif parts[1] == "QUIT":
                # print(message+"QQQQQQQQQQQQQQQQQQQQQQQQQQ")
                if address in self.conns:
                    self.conns.remove(address)
                    # print(address+"66666666666666666666666666666666666666")
                    writer.write("QUIT".encode())
                    time.sleep(0.5)
                    for i in range(5):
                        await self.loops[1].sock_sendto(self.sockets[1], "QUIT".encode(), (address, self.data_serve_ports[0]))
                        await self.loops[2].sock_sendto(self.sockets[2], "QUIT".encode(), (address, self.data_serve_ports[2]))
                        await self.loops[3].sock_sendto(self.sockets[3], "QUIT".encode(), (address, self.data_serve_ports[3]))
                        await self.loops[4].sock_sendto(self.sockets[4], "QUIT".encode(), (address, self.data_serve_ports[1]))
                    # 会议创始人点击发QUIT
                else:
                    writer.write("FAILURE user not in meeting".encode())
                print(self.conns)
                await writer.drain()
            elif parts[1] == "CANCEL":
                # print("0000000000000000000000000000000000000")
                #writer.write("SUCCESS QUIT confernece".encode())
                time.sleep(0.5)
                for conn in self.conns:
                    for i in range(5):
                        await self.loops[1].sock_sendto(self.sockets[1], "QUIT".encode(), (conn, self.data_serve_ports[0]))
                        await self.loops[2].sock_sendto(self.sockets[2], "QUIT".encode(), (conn, self.data_serve_ports[2]))
                        await self.loops[3].sock_sendto(self.sockets[3], "QUIT".encode(), (conn, self.data_serve_ports[3]))
                        await self.loops[4].sock_sendto(self.sockets[4], "QUIT".encode(), (conn, self.data_serve_ports[1]))
                self.run = False
                self.conns = []
                await writer.drain()
            elif (parts[1] == "OPEN"):
                if (self.screen):
                    writer.write("FAIL SCREEN already share".encode())
                else:
                    writer.write("SUCCESS SCREEN open screen".encode())
                    self.screen = True
                await writer.drain()
            elif (parts[1] == "CLOSE"):
                self.screen = False
            else:
                writer.write("FAILURE invalid command".encode())
                await writer.drain()
        else:
            print("invalid message")
            writer.write("FAILURE invalid message".encode())
            await writer.drain()

    async def log(self):
        while self.run:
            print('Something about server status')
            await asyncio.sleep(LOG_INTERVAL)

    async def cancel_conference(self):
        """
        handle cancel conference request: disconnect all connections to cancel the conference
        """
        self.run = False

    async def build(self):
        await asyncio.gather(
            self.udp_server1(),
            self.udp_server2(),
            self.udp_server3(),
            self.udp_server4()
        )

    async def udp_server1(self):
        loop = asyncio.get_running_loop()
        udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        buffer_size = 65536  # 设置为较大的值，例如 65535 字节
        udp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
        server_address = (SERVER_IP, self.data_serve_ports[0])
        udp_server_socket.bind(server_address)
        udp_server_socket.setblocking(False)

        print("UDP server1 is running...")
        self.loops[1] = loop
        self.sockets[1] = udp_server_socket
        conns = self.conns
        while self.run:
            data, client_address = await loop.sock_recvfrom(udp_server_socket, buffer_size)
            # print(data.decode())
            for w in conns:
                if w != client_address[0]:
                    await loop.sock_sendto(udp_server_socket, data, (w, self.data_serve_ports[0]))

    async def udp_server2(self):
        loop = asyncio.get_running_loop()
        udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        buffer_size = 65536  # 设置为较大的值，例如 65535 字节
        udp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
        server_address = (SERVER_IP, self.data_serve_ports[2])
        udp_server_socket.bind(server_address)
        udp_server_socket.setblocking(False)

        print("UDP server2 is running...")
        self.loops[2] = loop
        self.sockets[2] = udp_server_socket
        conns = self.conns
        while self.run:
            data, client_address = await loop.sock_recvfrom(udp_server_socket, buffer_size)
            for w in conns:
                if w != client_address[0]:
                    await loop.sock_sendto(udp_server_socket, data, (w, self.data_serve_ports[2]))

    async def udp_server3(self):
        loop = asyncio.get_running_loop()
        udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        buffer_size = 65536  # 设置为较大的值，例如 65535 字节
        udp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
        server_address = (SERVER_IP, self.data_serve_ports[3])
        udp_server_socket.bind(server_address)
        udp_server_socket.setblocking(False)

        print("UDP server3 is running...")
        self.loops[3] = loop
        self.sockets[3] = udp_server_socket
        conns = self.conns
        while self.run:
            data, client_address = await loop.sock_recvfrom(udp_server_socket, buffer_size)
            print(data.decode())
            print(conns)
            for w in conns:
                if w != client_address[0]:
                    await loop.sock_sendto(udp_server_socket, data, (w, self.data_serve_ports[3]))

    async def udp_server4(self):  # screen
        loop = asyncio.get_running_loop()
        udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        buffer_size = 65536  # 设置为较大的值，例如 65535 字节
        udp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
        server_address = (SERVER_IP, self.data_serve_ports[1])
        udp_server_socket.bind(server_address)
        udp_server_socket.setblocking(False)

        print("UDP server4 is running...")
        self.loops[4] = loop
        self.sockets[4] = udp_server_socket
        conns = self.conns
        while self.run:
            data, client_address = await loop.sock_recvfrom(udp_server_socket, buffer_size)
            # if (client_address[0] not in conns):
            #     print(client_address)
            #     conns.append(client_address[0])
            for w in conns:
                await loop.sock_sendto(udp_server_socket, data, (w, self.data_serve_ports[1]))

    async def start(self):
        '''
        start the ConferenceServer and necessary running tasks to handle clients in this conference
        '''
        await self.build()


"""
MainServer 类的主要功能
管理多个会议：维护一个字典 conference_servers，其中每个键值对包含一个会议ID和对应的 ConferenceServer 实例。

处理客户端请求：负责接收来自客户端的请求，如创建会议、加入会议和退出会议，并根据请求类型将请求转发给相应的 ConferenceServer。

启动和停止会议：可以启动新的会议（通过创建 ConferenceServer 实例）和关闭会议（通过调用 ConferenceServer 的 cancel_conference 方法）。
"""


class MainServer:
    def __init__(self, server_ip, main_port):
        # async server
        self.server_ip = server_ip
        self.server_port = main_port
        self.main_server = None
        self.running = True

        # self.conference_conns = None (貌似没有用)
        self.conference_servers = {}  # 每个键值对包含一个会议ID和对应的 ConferenceServer 实例
        self.conference_manager = {}  # 管理创建会议的客户端(根据会议号找主持人)
        self.reverse_conference_manager = {}  # conference_manager的反向映射
        self.clients_info = {}  # 管理客户端加入的会议（记录该会议的）value是会议号
        self.manage_task = {}  # 管理每个会议协程
        self.user_name_conference = {}  # P2P模式下管理（主持人名字:会议号)
        self.conf_name = {}  # P2P模式下管理（会议号:会议名）
        self.P2P_conference = {}  # P2P模式管理会议号和(主持人IP,writer)
        self.P2P_limit = {}  # P2P会议人数不超过2
        self.P2P_screen = {}  # P2P的screen开关情况
        self.ports = 8005

    async def handle_creat_conference(self, writer, reader, title, user_name, type):
        """
        create conference: create and start the corresponding ConferenceServer, and reply necessary info to client

        """
        characters = string.ascii_letters + string.digits
        # 生成随机密码
        conference_id = ''.join(random.choice(characters) for i in range(6))  # 会议唯一标识
        print(conference_id)
        if type == 'P2P':
            print("create P2P")
            client_address = writer.get_extra_info('peername')
            self.user_name_conference[user_name] = conference_id
            self.P2P_conference[conference_id] = (client_address[0], writer)
            self.conf_name[conference_id] = title
            self.P2P_limit[conference_id] = 0
            self.P2P_screen[conference_id] = 0
        else:
            print("create Conference")
            new_conference = ConferenceServer(conference_id, title, self.ports)  # 创建新会议服务器
            new_conference.owner = writer
            self.conference_servers[conference_id] = new_conference  # 用会议id管理会议，便于加入等操作
            self.conference_manager[conference_id] = writer  # 用writer唯一标识会议创建者（注：有时间的话去换成ip?）
            self.conf_name[conference_id] = title
            self.user_name_conference[user_name] = conference_id
            self.reverse_conference_manager[writer] = conference_id
            task = asyncio.create_task(new_conference.start())
            self.manage_task[conference_id] = task
            writer.write(f'SUCCESS {conference_id} {self.ports}'.encode())
            print(self.ports)
            if self.ports == 8993:
                self.ports = 8005
            else:
                self.ports = self.ports + 4
            await writer.drain()

    async def handle_join_conference(self, reader, writer, conference_id, message):
        """
        join conference: search corresponding conference_info and ConferenceServer, and reply necessary info to client
        """
        if conference_id in self.conference_servers:  # 如果可以通过会议id找到会议
            # print("11111111111111111111111111111111111111111111111111111")
            if (writer, reader) in self.clients_info:  # 如果已经加入某个会议
                cid = self.clients_info[(writer, reader)]
                writer.write(f'FAIL: You have already joined the conference {cid}'.encode())
                await writer.drain()
            else:
                conference = self.conference_servers[conference_id]
                # print("5555555555555555555555555555555555")
                await conference.handle_client(reader, writer, message)  # 将message交给会议服务器，由会议服务器添加？
                self.clients_info[(writer, reader)] = conference_id  # 标识每个客户端加入的会议
        elif conference_id in self.P2P_conference:  # 如果是P2P会议的id
            print("P2P")
            if (writer, reader) in self.clients_info:  #
                cid = self.clients_info[(writer, reader)]
                writer.write(f'FAIL: You have already joined the conference {cid}'.encode())
                await writer.drain()
            else:
                if self.P2P_limit[conference_id] == 2:
                    writer.write(f'FAIL: Conference full!'.encode())
                    await writer.drain()
                else:
                    self.P2P_limit[conference_id] += 1
                    ip, owner = self.P2P_conference[conference_id]  # 找到该会议的主持人和其writer
                    title = self.conf_name[conference_id]  # 找到会议名字
                    client_address = writer.get_extra_info('peername')
                    writer.write(f'SUCCESS join P2P confernece {title} {ip}'.encode())  # 给当前用户发送会议名字和ip
                    print(f'{client_address[0]} join {ip} conference')
                    if ip != client_address[0]:
                        owner.write(f'SUCCESS {conference_id} {client_address[0]}'.encode())  # 给主持人发送加入会议的ip
                        print('send ip to owner')
                    self.clients_info[(writer, reader)] = conference_id
                    await writer.drain()
        else:
            writer.write('FAIL: Conference not found'.encode())
            await writer.drain()

    async def handle_quit_conference(self, reader, writer, message):
        """
        quit conference (in-meeting request & or no need to request)
        """
        if (writer, reader) in self.clients_info:  # 如果该用户加入了某个会议
            cid = self.clients_info[(writer, reader)]
            if cid in self.P2P_conference:  # 如果是P2P
                print("quit P2P conference")
                self.P2P_screen.pop(cid)
                self.P2P_conference.pop(cid)
                self.P2P_limit.pop(cid)
                ktd = [k for k, v in self.user_name_conference.items() if v == cid]
                for k in ktd:
                    self.user_name_conference.pop(k)
                keys_to_delete = [k for k, v in self.clients_info.items() if v == cid]
                for k in keys_to_delete:
                    w, r = k
                    w.write(f'QUIT'.encode())
                    self.clients_info.pop(k)
                await writer.drain()
            else:
                cid = self.clients_info[(writer, reader)]  # 用户加入的会议id
                print(cid)
                await self.conference_servers[cid].handle_client(reader, writer, message)  # 向该会议发送message
                print("quit conference server")
                flag = 0
                self.clients_info.pop((writer, reader))
                if writer == self.conference_manager[cid]:  # 如果是主持人退出
                    # print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
                    self.reverse_conference_manager.pop(writer)  # 删除主持人！！！
                    for k, v in self.clients_info.items():
                        if v == cid:
                            # print("change")
                            w, r = k
                            self.conference_manager[cid] = w  # 改变MainServer记录的主持人
                            self.conference_servers[cid].owner = w  # 改变ConferenceServer的主持人
                            self.reverse_conference_manager[w] = cid
                            w.write(f'HOST'.encode())
                            flag = 1
                            break
                    if flag == 0:
                        # print("no conference")
                        self.conference_manager.pop(cid)
                        self.conference_servers.pop(cid)
                        task = self.manage_task.pop(cid)  # Get the task associated with the conference
                        task.cancel()  # Cancel the task
                        owner_name = [k for k, v in self.user_name_conference.items() if v == cid]
                        for k in owner_name:
                            self.user_name_conference.pop(k)
        else:
            writer.write('FAIL: You do not have a meeting now'.encode())
            await writer.drain()
        pass


    async def handle_cancel_conference(self, reader, writer, message):
        """
        cancel conference (in-meeting request, a ConferenceServer should be closed by the MainServer)
        """
        if writer in self.conference_manager.values():  # 如果该用户是会议主持人
            # print("555555555555555555555555555555555555555")
            conference_id = self.reverse_conference_manager[writer]  # 从反向映射表中找会议号
            self.conference_manager.pop(conference_id)  # 删除（主持人，会议）记录
            self.reverse_conference_manager.pop(writer)
            keys_to_delete = [k for k, v in self.clients_info.items() if v == conference_id]
            for k in keys_to_delete:
                w, r = k
                # print("send quit to")
                w.write(f'QUIT'.encode())
                self.clients_info.pop(k)
            await self.conference_servers[conference_id].handle_client(reader, writer, message)
            task = self.manage_task.pop(conference_id)  # Get the task associated with the conference
            task.cancel()  # Cancel the task
            self.conference_servers.pop(conference_id)  # 删除该会议
            # print("555555555555555555555555555555555555555")
            owner_name = [k for k, v in self.user_name_conference.items() if v == conference_id]
            for k in owner_name:
                self.user_name_conference.pop(k)
            client_address = writer.get_extra_info('peername')
            print(f'{client_address[0]} cancel conference: {conference_id}')
            await writer.drain()
        else:
            writer.write('CANCEL FAIL'.encode())
            await writer.drain()

    async def request_handler(self, reader, writer):
        """
        running task: handle out-meeting (or also in-meeting) requests from clients
        """

        with open("command.txt", "a") as f:
            while self.running:
                try:
                    client_address = writer.get_extra_info('peername')
                    print(f'{client_address[0]}: {client_address[1]}')
                    receive_data = await reader.read(1024)
                    message = receive_data.decode()
                    f.write(f'{client_address}' + message + '\n')
                    print(f'{client_address}:{message}')
                    if message.startswith('[COMMAND]:'):
                        opera = message.split(' ')[1]
                        # print("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
                        if opera.startswith('Create'):
                            # print("ininininininininininininininCREATE")
                            type = message.split(' ')[2]
                            title = message.split(' ')[-2]
                            user_name = message.split(' ')[-1]
                            await self.handle_creat_conference(writer, reader, title, user_name, type)
                        elif opera.startswith('JOIN'):
                            conference_id = message.split()[2]
                            if conference_id == ' ':
                                writer.write('Too few parameters to join conference'.encode())
                            else:
                                await self.handle_join_conference(reader, writer, conference_id, message)
                        elif opera.startswith('QUIT'):
                            print("enter quit branch")
                            await self.handle_quit_conference(reader, writer, message)
                        elif opera.startswith('CHECK'):
                            list = ""
                            for k, v in self.user_name_conference.items():
                                user_name = k
                                conference_id = v
                                title = self.conf_name[v]
                                list = list + title + " " + user_name + " " + conference_id + " "
                            print(list)
                            if list == "":
                                writer.write('None'.encode())
                            else:
                                writer.write(f'{list}'.encode())
                        elif opera.startswith('CANCEL'):
                            if "P2P" in message:
                                print("P2P")
                                await self.handle_quit_conference(reader, writer, message)
                            else:
                                await self.handle_cancel_conference(reader, writer, message)
                        elif "SCREEN" in message:
                            cid = self.clients_info[(writer, reader)]
                            # print(message+"5555555555555555555555555")
                            if cid in self.P2P_conference:
                                if "OPEN" in message:
                                    if self.P2P_screen[cid] == 1:
                                        writer.write("FAIL SCREEN already share".encode())
                                        await writer.drain()
                                    else:
                                        writer.write("SUCCESS SCREEN open screen".encode())
                                        self.P2P_screen[cid] = 1
                                        await writer.drain()
                                elif "CLOSE" in message:
                                    self.P2P_screen[cid] = 0
                            else:
                                # print("5555555555555444444444444444444444444")
                                await self.conference_servers[cid].handle_client(reader, writer, message)
                    else:
                        cmd = message.split(' ')
                        if cmd[0] == 'login':
                            if len(cmd) < 3:
                                feedback_data = 'Please re-enter the login commend with your username and password'
                                feedback_data = FAILURE(feedback_data)
                            elif len(cmd) == 3:
                                feedback_data, login_user = await login_authentication(writer, reader, cmd, users)
                            else:
                                feedback_data = "Password shouldn't include spaces"
                                feedback_data = FAILURE(feedback_data)
                        elif cmd[0] == 'register':
                            if len(cmd) < 3:
                                feedback_data = 'Please re-enter the command with username and password'
                                feedback_data = FAILURE(feedback_data)
                            elif len(cmd) > 3:
                                feedback_data = "Username or password shouldn't include spaces"
                                feedback_data = FAILURE(feedback_data)
                            else:
                                feedback_data = user_register(cmd, users)
                        writer.write(feedback_data.encode())
                        await writer.drain()
                        if feedback_data == '200:disconnected':
                            print(f'Client {client_address} disconnected')
                            writer.close()
                except Exception as e:
                    client_address = writer.get_extra_info('peername')
                    print(f"Client {client_address[0]} disconnected unexpectedly.")
                    break

    async def start(self):
        """
        start MainServer
        """
        server = await asyncio.start_server(self.request_handler, self.server_ip, self.server_port)
        print(f'Serving on {self.server_ip}:{self.server_port}')

        await server.serve_forever()

    async def stop(self):
        for conference_id, conference in self.conference_servers.items():
            await conference.cancel_conference()
        self.running = False


if __name__ == '__main__':
    server = MainServer(SERVER_IP, MAIN_SERVER_PORT)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("Server is shutting down.")
        asyncio.run(server.stop())
