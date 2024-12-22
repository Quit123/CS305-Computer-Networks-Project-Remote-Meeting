import asyncio
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
        self.user_name = []
        self.conns = []
        self.servers = []
        self.online_users = 0
        self.last_online_users = 0
        self.last_join_user = "NULL"
        self.mode = 'Client-Server'  # or 'P2P' if you want to support peer-to-peer conference mode
        self.run = True
        self.tasks = []
        self.owner = None

    async def handle_data(self, reader: StreamReader, writer: StreamWriter, type):
        """
        running task: receive sharing stream data from a client and decide how to forward them to the rest clients
        """
        if type == 'audio':
            conns = self.audio_conns
        elif type == 'screen':
            conns = self.screen_conns
        elif type == 'camera':
            conns = self.camera_conns
        else:
            conns = self.text_conns
        if (writer not in conns):
            conns.append(writer)
        try:
            while self.run:
                data = await reader.read(1024)
                if type == 'text':
                    print(data.decode())
                for w in self.audio_conns:  # 假设这是处理音频的连接列表
                    if w != writer:
                        w.write(data)
                        await w.drain()
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            client_address = writer.get_extra_info('peername')
            print(f"Client {client_address[0]} disconnected unexpectedly.")
            if client_address[0] == self.owner:
                for server in self.servers:
                    server.close()
                    await server.wait_closed()

    async def handle_client(self, reader: StreamReader, writer: StreamWriter, message):
        """
        running task: handle the in-meeting requests or messages from clients
        """
        message = message
        parts = message.strip().split(" ")
        if (parts[0].startswith('[COMMAND]')):
            if (parts[1] == "JOIN"):
                if (parts[-1] not in self.user_name):
                    self.user_name.append(parts[-1])
                    self.online_users += 1
                    self.last_join_user = parts[-1]
                    print(f"SUCCESS join confernece {self.title}")
                    writer.write(f"SUCCESS join confernece {self.title} {self.data_serve_ports[0]}".encode())
                    print(writer)
                    await writer.drain()
                else:
                    writer.write("FAILURE wrong user".encode())
                    await writer.drain()
            elif (parts[1] == "QUIT"):
                if parts[-1] in self.client_conns:
                    self.user_name.remove(parts[-1])
                    self.last_online_users -= 1
                    self.online_users -= 1
                    writer.write("SUCCESS quit confernece".encode())
                    await writer.drain()
                else:
                    writer.write("FAILURE wrong user".encode())
                    await writer.drain()
            else:
                writer.write("FAILURE invalid command".encode())
                await writer.drain()
        elif parts[0].startswith('[ASK]'):
            if self.online_users > self.last_online_users:
                writer.write(f"[ANS]: YES {self.last_join_user} True".encode())
                await writer.drain()
            else:
                writer.write("[ANS]: No False".encode())
                await writer.drain()
            self.last_online_users = self.online_users
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
            self.udp_server3()
        )

    async def udp_server1(self):
        loop = asyncio.get_running_loop()
        udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        buffer_size = 65535  # 设置为较大的值，例如 65535 字节
        udp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
        server_address = (SERVER_IP, self.data_serve_ports[0])
        udp_server_socket.bind(server_address)
        udp_server_socket.setblocking(False)

        print("UDP server1 is running...")
        conns = self.conns
        while self.run:
            data, client_address = await loop.sock_recvfrom(udp_server_socket, buffer_size)
            if (client_address[0] not in conns):
                print(client_address)
                conns.append(client_address[0])
            # print(data.decode())
            for w in conns:
                if w != client_address[0]:
                    await loop.sock_sendto(udp_server_socket, data, (w, self.data_serve_ports[0]))

    async def udp_server2(self):
        loop = asyncio.get_running_loop()
        udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        buffer_size = 400000  # 设置为较大的值，例如 65535 字节
        udp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
        server_address = (SERVER_IP, self.data_serve_ports[2])
        udp_server_socket.bind(server_address)
        udp_server_socket.setblocking(False)

        print("UDP server2 is running...")
        conns = self.conns
        while self.run:
            data, client_address = await loop.sock_recvfrom(udp_server_socket, buffer_size)
            if (client_address[0] not in conns):
                # print(client_address)
                conns.append(client_address[0])
            # print(data.decode())
            for w in conns:
                # if w != client_address[0]:
                await loop.sock_sendto(udp_server_socket, data, (w, self.data_serve_ports[2]))

    async def udp_server3(self):
        loop = asyncio.get_running_loop()
        udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        buffer_size = 65535  # 设置为较大的值，例如 65535 字节
        udp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
        server_address = (SERVER_IP, self.data_serve_ports[3])
        udp_server_socket.bind(server_address)
        udp_server_socket.setblocking(False)

        print("UDP server3 is running...")
        conns = self.conns
        while self.run:
            data, client_address = await loop.sock_recvfrom(udp_server_socket, buffer_size)
            if (client_address[0] not in conns):
                # print(client_address)
                conns.append(client_address[0])
            # print(data.decode())
            for w in conns:
                if w != client_address[0]:
                    await loop.sock_sendto(udp_server_socket, data, (w, self.data_serve_ports[3]))

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
        self.conference_manager = {}  # 管理创建会议的客户端
        self.reverse_conference_manager = {}  # conference_manager的反向映射
        self.clients_info = {}  # 管理客户端加入的会议（记录该会议的）
        self.manage_task = {}  # 管理每个会议协程
        self.user_conference = {}  # P2P模式下管理（主持人:会议号)
        self.P2P_conf_name = {}  # P2P模式下管理（会议号:会议名）
        self.P2P_conference = {}  # P2P模式管理会议号和(主持人IP,writer)
        self.ports = 8001

    async def handle_creat_conference(self, writer, reader, title, user_name, type):
        """
        create conference: create and start the corresponding ConferenceServer, and reply necessary info to client

        """
        characters = string.ascii_letters + string.digits
        # 生成随机密码
        conference_id = ''.join(random.choice(characters) for i in range(6))  # 会议唯一标识
        print(conference_id)
        if type == 'P2P':
            client_address = writer.get_extra_info('peername')
            self.user_conference[user_name] = conference_id
            self.P2P_conference[conference_id] = (client_address[0], writer)
            self.P2P_conf_name[conference_id] = title
        else:
            new_conference = ConferenceServer(conference_id, title, self.ports)  # 创建新会议服务器
            client_address = writer.get_extra_info('peername')
            new_conference.owner = client_address[0]
            self.conference_servers[conference_id] = new_conference  # 用会议id管理会议，便于加入等操作
            self.conference_manager[conference_id] = (writer, reader)  # 用（writer, reader）唯一标识会议创建者（注：有时间的话去换成ip?）
            self.reverse_conference_manager[(writer, reader)] = conference_id
            task = asyncio.create_task(new_conference.start())
            self.manage_task[conference_id] = task
            writer.write(f'SUCCESS {conference_id} {self.ports}'.encode())
            print(self.ports)
            if self.ports == 8993:
                self.ports=8000
            else:
                self.ports = self.ports + 4
            await writer.drain()

    async def handle_join_conference(self, reader, writer, conference_id, message):
        """
        join conference: search corresponding conference_info and ConferenceServer, and reply necessary info to client
        """
        if conference_id in self.conference_servers:  # 如果可以通过会议id找到会议
            if (writer, reader) in self.clients_info:  # 如果已经加入某个会议
                cid = self.clients_info[(writer, reader)]
                writer.write(f'Fail:You have already joined the conference {cid}'.encode())
                await writer.drain()
            else:
                conference = self.conference_servers[conference_id]
                await conference.handle_client(reader, writer, message)  # 将message交给会议服务器，由会议服务器添加？
                self.clients_info[(writer, reader)] = conference_id  # 标识每个客户端加入的会议
                print(conference_id)
        elif conference_id in self.P2P_conference:  # 如果是P2P会议的id
            if (writer, reader) in self.clients_info:  #
                cid = self.clients_info[(writer, reader)]
                writer.write(f'Fail:You have already joined the conference {cid}'.encode())
                await writer.drain()
            else:
                ip, owner = self.P2P_conference[conference_id]
                title = self.P2P_conf_name[conference_id]
                client_address = writer.get_extra_info('peername')
                writer.write(f'SUCCESS join confernece {title} {ip}'.encode())
                if ip != client_address[0]:
                    owner.write(f'SUCCESS {conference_id} {client_address[0]}'.encode())
                self.clients_info[(writer, reader)] = conference_id
                await writer.drain()
        else:
            writer.write('Fail: Conference not found'.encode())
            await writer.drain()

    async def handle_quit_conference(self, reader, writer, message):
        """
        quit conference (in-meeting request & or no need to request)
        """
        if (writer, reader) in self.clients_info:  # 如果该用户加入了某个会议
            cid = self.clients_info[(writer, reader)]
            if cid in self.P2P_conference:
                client_address = writer.get_extra_info('peername')
                if client_address[0] == self.P2P_conference[cid][0]:
                    self.P2P_conference.pop(cid)
                    self.user_conference.pop(client_address[0])
                    self.clients_info.pop((writer, reader))
                    writer.write(f'SUCCESS: Cancel Conference: {cid}'.encode())
                    await writer.drain()
                else:
                    self.clients_info.pop((writer, reader))
                    writer.write(f'SUCCESS: Cancel Conference: {cid}'.encode())
                    await writer.drain()
            else:
                if (writer, reader) in self.conference_manager.values():  # 如果该用户是会议主持人
                    conference_id = self.reverse_conference_manager[(writer, reader)]  # 从反向映射表中找会议号
                    await self.conference_servers[conference_id].cancel_conference()  # 有的话发送给conference_server
                    task = self.manage_task.pop(conference_id)  # Get the task associated with the conference
                    task.cancel()  # Cancel the task
                    self.conference_manager.pop(conference_id)  # 删除（主持人，会议）记录
                    self.reverse_conference_manager.pop((writer, reader))
                    keys_to_delete = [k for k, v in self.clients_info.items() if v == conference_id]
                    for k in keys_to_delete:
                        self.clients_info.pop(k)
                    self.conference_servers.pop(conference_id)  # 删除该会议
                    writer.write(f'SUCCESS: Cancel Conference: {conference_id}'.encode())
                    client_address = writer.get_extra_info('peername')
                    print(f'{client_address[0]} cancel conference: {conference_id}')
                    await writer.drain()
                else:
                    cid = self.clients_info[(writer, reader)]  # 用户加入的会议id
                    await self.conference_servers[cid].handle_client(reader, writer, message)  # 向该会议发送message
                    self.clients_info.pop((writer, reader))  # 该用户状态改为未加入任何会议
                    writer.write(f'SUCCESS: Quit Conference: {cid}'.encode())
                    client_address = writer.get_extra_info('peername')
                    print(f"{client_address[0]} quit conference {cid}")
                    await writer.drain()
        else:
            writer.write('Fail: You do not have a meeting now'.encode())
            await writer.drain()
        pass

    # async def handle_cancel_conference(self, reader, writer, conference_id, message):
    #     """
    #     cancel conference (in-meeting request, a ConferenceServer should be closed by the MainServer)
    #     """
    #     if self.conference_manager[conference_id] == (writer, reader):  # 确认该用户是否有管理权限
    #         self.conference_servers[conference_id].cancel_conference()  # 有的话发送给conference_server
    #         task = self.manage_task.pop(conference_id)  # Get the task associated with the conference
    #         task.cancel()  # Cancel the task
    #         self.conference_manager.pop((writer, reader))
    #         for (w, r) in self.conference_servers[conference_id].clients_info:  # 删除所有参加该会议的人
    #             self.clients_info.pop((w, r))
    #         self.conference_servers.pop(conference_id)  # 删除该会议
    #         writer.write(f'SUCCESS: Cancel Conference: {conference_id}'.encode())
    #         await writer.drain()
    #     else:
    #         writer.write('Fail: Permission deny'.encode())
    #         await writer.drain()

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

                        if opera.startswith('Create'):
                            type = message.split(' ')[1]
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
                            await self.handle_quit_conference(reader, writer, message)
                        elif opera.startswith('CHECKLIST'):
                            list = ""
                            for k, v in self.user_conference.items():
                                user_name = k
                                conference_id = v
                                list = list + user_name + " " + conference_id + " "
                            print(list)
                            writer.write(f'{list}'.encode())
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
